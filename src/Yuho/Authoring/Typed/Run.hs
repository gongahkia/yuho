{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Typed.Run
  ( encodeTypedDocument, decodeTypedDocument, validateTypedAnalysis, typedSnapshotFor
  , TypedCompilation, compileTypedAnalysis, typedCompiledRequest, typedCompiledSnapshot, typedCompiledMappings
  , TypedEvaluation, evaluateTypedAnalysis, typedEvaluationReport, typedEvaluationSnapshot
  , typedEvaluationResponse, typedEvaluationMappings ) where

import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as KeyMap
import qualified Data.Aeson.Key as Key
import qualified Data.ByteString as BS
import Data.List (find, nub)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as T
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Types
import Yuho.Authoring.Typed.Types
import Yuho.Authoring.Typed.Validate
import Yuho.Authoring.Validate (issue)
import qualified Yuho.CoreYuho.TypedFinite as K
import Yuho.Exception.Types (Truth(..))
import Yuho.Protocol.Decode (inputDigest, sha256Text)
import Yuho.Protocol.Json (J(..), decodeJson, lookupField)
import Yuho.Surface.TypedFinite (encodeTypedFiniteRequest)
import Yuho.TypedFiniteRules.Run (decodeTypedFiniteRequest, encodeTypedFiniteResult)

encodeTypedDocument :: TypedDocument -> BS.ByteString
encodeTypedDocument = encodeRecord

decodeTypedDocument :: BS.ByteString -> Either AuthoringDiagnostic TypedDocument
decodeTypedDocument bytes = do
  value <- either (Left . issue "TJSON" "/" []) Right (decodeJson bytes)
  case lookupField "typedDocumentFormat" value of
    Just (JStr version) | version == typedAuthoringFormat -> pure ()
    _ -> Left (issue "TVERSION" "/typedDocumentFormat" [] "expected the v0.3 typed document; mixed proof-profile objects are unsupported")
  either (Left . issue "TJSON" "/" [] . T.pack) Right (A.eitherDecodeStrict' bytes)

data TypedCompilation = TypedCompilation BS.ByteString TypedSnapshot [TypedKernelMapping] K.TypedFiniteProgram

typedCompiledRequest :: TypedCompilation -> BS.ByteString
typedCompiledRequest (TypedCompilation x _ _ _) = x
typedCompiledSnapshot :: TypedCompilation -> TypedSnapshot
typedCompiledSnapshot (TypedCompilation _ x _ _) = x
typedCompiledMappings :: TypedCompilation -> [TypedKernelMapping]
typedCompiledMappings (TypedCompilation _ _ x _) = x

data TypedEvaluation = TypedEvaluation TypedReport TypedCompilation BS.ByteString

typedEvaluationReport :: TypedEvaluation -> TypedReport
typedEvaluationReport (TypedEvaluation x _ _) = x
typedEvaluationSnapshot :: TypedEvaluation -> TypedSnapshot
typedEvaluationSnapshot (TypedEvaluation _ x _) = typedCompiledSnapshot x
typedEvaluationResponse :: TypedEvaluation -> BS.ByteString
typedEvaluationResponse (TypedEvaluation _ _ x) = x
typedEvaluationMappings :: TypedEvaluation -> [TypedKernelMapping]
typedEvaluationMappings (TypedEvaluation _ x _) = typedCompiledMappings x

typedSnapshotFor :: TypedDocument -> TypedAnalysis -> TypedSnapshot
typedSnapshotFor d a = TypedSnapshot (sha256Text (encodeRecord (d,a,typedEvaluatorProfile)))
  (sha256Text (encodeRecord (lawObjects,typedLinks d,originals))) typedEvaluatorProfile a d
  where
    lawObjects = [(role,meta) | (role,meta) <- typedObjects d, role `notElem` ["assessment","value"]]
    -- Hash actual declaration/form/tuple/role contents, not just their labels.
    originals = (typedLawId d,typedLawRevision d,typedEntityTypes d,typedEntities d,typedPredicates d,
      typedApplications d,typedScalars d,typedExpressions d,typedRules d,typedPropositions d,
      [s | s <- typedOriginalSources d, sourceId s `elem` map referenceSource (concatMap (typedSources . snd) lawObjects)])

compileTypedAnalysis :: TypedDocument -> Text -> Either [AuthoringDiagnostic] TypedCompilation
compileTypedAnalysis d key = do
  let report = validateTypedBindings d key
      failure code ids message = Left [issue code "/typedAnalyses" (key:ids) message]
  if typedAnalysisReady report then pure () else Left (typedDiagnostics report)
  a <- maybe (failure "TTARGET" [] "analysis not found") Right (typedAnalysisById d key)
  rule <- maybe (failure "TTARGET" [] "selected rule not found") Right
    (find ((== typedAnalysisRule a) . typedId . typedRuleMeta) (typedRules d))
  root <- case [typedLinkTo e | e <- typedLinks d, typedLinkFrom e == typedAnalysisRule a, typedLinkKind e == "typed_body"] of
    [x] -> Right x
    _ -> failure "TSHAPE" [typedAnalysisRule a] "ground rule must have exactly one body"
  let occurrences = typedOccurrences d a
      expressions = map fst occurrences
      appIds = nub [app | x <- expressions, GroundApplication app <- [expressionForm x]]
      operands = nub (concat [[l,r] | x <- expressions, IntegerComparison _ l r <- [expressionForm x]])
      assessments = [x | ref <- selectedTypedAssessments a, x <- typedAssessments d, typedId (typedAssessmentMeta x) == ref]
      values = [x | ref <- selectedTypedValues a, x <- typedValues d, typedId (valueMeta x) == ref]
      generatedReason x = "generated SDK assessment " <> sha256Text (encodeRecord (typedId (typedAssessmentMeta x)))
      classification TechnicalTrue = TrueValue
      classification TechnicalFalse = FalseValue
      classification (TechnicalUnresolved _) = UnresolvedValue
      scalarValue (ExactInteger n) = K.IntegerValue n
      scalarValue (UnknownInteger _ reason) = K.ScalarUnresolved reason K.IntegerType
      form x = case expressionForm x of
        GroundApplication app -> case find ((== app) . typedId . applicationMeta) (typedApplications d) of
          Nothing -> failure "TAPPLICATION" [app] "application not found"
          Just value -> Right (K.PredicateExpr (tuplePredicate (applicationTuple value)) (map K.EntityTerm (tupleArguments (applicationTuple value))))
        IntegerComparison op left right -> case op of
          "gt" -> Right (K.ComparisonExpr K.GreaterThan left right Nothing)
          "eq" -> Right (K.ComparisonExpr K.Equal left right Nothing)
          _ -> failure "TOPERATOR" [typedId (expressionMeta x)] "unsupported integer comparator"
        kind -> let members = [K.ReferenceExpr (typedLinkTo e) | e <- typedLinks d,
                      typedLinkFrom e == typedId (expressionMeta x), typedLinkKind e == "typed_member"]
                in Right (if kind == TypedAll then K.AllExpr members else K.AnyExpr members)
  bodies <- traverse (\x -> do body <- form x; pure (typedId (expressionMeta x),body)) expressions
  let program = K.TypedFiniteProgram (typedLawId d)
        [K.EntityTypeDecl (typedId (entityTypeMeta t)) | t <- typedEntityTypes d]
        [K.EntityDecl (typedId (entityMeta e)) (entityNominalType e) | e <- typedEntities d]
        [K.PredicateDecl (typedId (predicateMeta p)) (map argumentType (predicateRoles p)) K.PredicateRelationship | p <- typedPredicates d]
        [K.ScalarDecl (typedId (scalarMeta s)) K.IntegerType | s <- typedScalars d, typedId (scalarMeta s) `elem` operands]
        [typedAnalysisProposition a] bodies
        [K.RuleDecl (typedAnalysisRule a) [] K.Establish (typedAnalysisProposition a) (K.ReferenceExpr root) (typedCitation (typedRuleMeta rule))]
        [] [] [] [K.GroundFact (tuplePredicate (assessedTuple x)) (tupleArguments (assessedTuple x))
          (classification (typedClassification x)) (generatedReason x) | x <- assessments]
        (Map.fromList [(valueScalar x,scalarValue (valueExact x)) | x <- values]) [] (typedLimitations d)
      refs keyObject = maybe [] (typedSources . snd) (find ((== keyObject) . typedId . snd) (typedObjects d))
      mappings = [TypedKernelMapping "expression" (typedId (expressionMeta x)) (typedId (expressionMeta x)) path
          (typedSources (expressionMeta x)) Nothing | (x,path) <- occurrences]
        ++ [TypedKernelMapping "ground_application" (K.groundKey (tuplePredicate (applicationTuple x)) (tupleArguments (applicationTuple x)))
          (typedId (applicationMeta x)) [] (typedSources (applicationMeta x)) Nothing | x <- typedApplications d, typedId (applicationMeta x) `elem` appIds]
        ++ [TypedKernelMapping "assessment" (K.groundKey (tuplePredicate (assessedTuple x)) (tupleArguments (assessedTuple x)))
          (typedId (typedAssessmentMeta x)) [] (typedSources (typedAssessmentMeta x)) (Just (generatedReason x)) | x <- assessments]
        ++ [TypedKernelMapping "scalar" v v [] (refs v) Nothing | v <- operands]
        ++ [TypedKernelMapping "value" (valueScalar x) (typedId (valueMeta x)) [] (typedSources (valueMeta x)) Nothing | x <- values]
        ++ [TypedKernelMapping "rule" (typedAnalysisRule a) (typedAnalysisRule a) [] (typedSources (typedRuleMeta rule)) Nothing,
            TypedKernelMapping "proposition" (typedAnalysisProposition a) (typedAnalysisProposition a) [] (refs (typedAnalysisProposition a)) Nothing]
        ++ [TypedKernelMapping category (typedId meta) (typedId meta) [] (typedSources meta) Nothing
          | (category,meta) <- typedObjects d, category `elem` ["entity_type","entity","predicate"]]
      bytes = encodeTypedFiniteRequest "SDK-TYPED" program
  wire <- either (failure "TBACKEND/JSON" [root]) Right (decodeJson bytes)
  -- Exactly the production protocol's decoder, type/grounding/resource checks;
  -- validation never runs the evaluator.
  validated <- either (failure "TBACKEND" [root]) Right (decodeTypedFiniteRequest wire)
  pure (TypedCompilation bytes (typedSnapshotFor d a) mappings validated)

validateTypedAnalysis :: TypedDocument -> Text -> TypedValidation
validateTypedAnalysis d key = let report = validateTypedBindings d key in
  if not (typedAnalysisReady report) then report else case compileTypedAnalysis d key of
    Left errors -> report {typedAnalysisReady=False,typedDiagnostics=errors}
    Right _ -> report

evaluateTypedAnalysis :: TypedCompilation -> Either [AuthoringDiagnostic] TypedEvaluation
evaluateTypedAnalysis compiled@(TypedCompilation bytes snapshot mappings program) = do
  let a = typedSnapshotAnalysis snapshot
      d = typedSnapshotDocument snapshot
      failure message = Left [issue "TBACKEND" "/typedEvaluation" [typedAnalysisId a] message]
      occurrences = typedOccurrences d a
      occurrence key = case [path | (x,path) <- occurrences, typedId (expressionMeta x) == key] of
        [path] -> Just (TypedOccurrence (typedLawDigest snapshot) (typedAnalysisRule a) (typedAnalysisScope a) key path)
        _ -> Nothing
  result <- either failure Right (K.evaluateTypedFinite program)
  request <- either failure Right (decodeJson bytes)
  let response = encodeTypedFiniteResult "SDK-TYPED" (inputDigest request) result
  encoded <- either (failure . T.pack) Right (A.eitherDecodeStrict' response :: Either String A.Value)
  -- Keep actual structured backend rows. No parsing of free-text detail and no
  -- invented child traces; every row corresponds to a named returned category.
  let row category key status resolution backend = TypedObservation
        ("p-typed-observation-" <> sha256Text (encodeRecord (typedSnapshotId snapshot,category,key)))
        category key key status "evaluated" resolution
        (if category == "expression" then occurrence key else Nothing) backend
      backendRows name = case encoded of
        A.Object object -> case maybe (A.Error "missing category") A.fromJSON (KeyMap.lookup (Key.fromText name) object) of
          A.Success values -> values
          A.Error _ -> []
        _ -> []
  expressionRows <- traverse (attach row "expression" backendRows)
    [(K.expressionLabel x,K.truthName (K.expressionStatus x),Nothing) | x <- K.finiteResultExpressions result]
  ruleRows <- traverse (attach row "rule" backendRows)
    [(K.observedRule x,K.truthName (K.observedStatus x),Nothing) | x <- K.finiteResultRules result]
  propositionRows <- traverse (attach row "proposition" backendRows)
    [(K.observedPropositionId x,K.truthName (K.propositionStatus x),Just (K.propositionState x)) | x <- K.finiteResultPropositions result]
  let report = TypedReport (typedSnapshotId snapshot) (typedAnalysisId a) (typedAnalysisScope a)
        (typedAnalysisRule a) (typedAnalysisProposition a) typedEvaluatorProfile expressionRows ruleRows propositionRows mappings
        "Technical grounded typed evaluation of authored expressions and explicit supplied tuples/integers; no absence-as-false policy, evidence weighing, unauthorised-access finding, quantity conversion or guilt determination."
  if length expressionRows == length occurrences then Right (TypedEvaluation report compiled response)
    else failure "backend expression observation coverage differs from authored selected closure"
  where
    attach row category rows (key,status,resolution) = case [v | v@(A.Object o) <- rows (category <> "s"), KeyMap.lookup "id" o == Just (A.String key)] of
      [backend] -> Right (row category key status resolution backend)
      _ -> Left [issue "TOBSERVATION" "/typedEvaluation" [key] "returned backend observation is absent or ambiguous"]
