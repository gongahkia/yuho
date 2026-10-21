{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Presumption.Run
  ( encodePresumptionDocument, decodePresumptionDocument, validatePresumptionAnalysis
  , PresumptionCompilation, compilePresumptionAnalysis, presumptionCompiledRequest
  , presumptionCompiledSnapshot, presumptionCompiledMappings, presumptionCompiledSources
  , presumptionProofCompilation
  , PresumptionEvaluation, evaluatePresumptionAnalysis, presumptionEvaluationReport
  , presumptionEvaluationSnapshot, presumptionEvaluationResponse, presumptionEvaluationCompilation
  , presumptionSnapshotFor ) where

import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import Data.List (find, nub)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Compile
import Yuho.Authoring.Presumption.Types
import Yuho.Authoring.Presumption.Validate
import Yuho.Authoring.Projection (projectionIdentity)
import Yuho.Authoring.Report
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (findAnalysis, issue)
import qualified Yuho.Core.Types as C
import qualified Yuho.Presumption.Types as K
import Yuho.Presumption.Decode (decodePresumptionRequest)
import Yuho.Presumption.Validate (validatePresumptionRequest)
import Yuho.Presumption.Evaluate (evaluatePresumptions)
import Yuho.Presumption.Encode (encodePresumptionResult)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField)
import Yuho.Protocol.Decode (inputDigest, sha256Text)
import Yuho.Protocol.Encode (spanJson)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProofWith)
import Yuho.SuppliedProofStatus.Select (selectProofPenalties)
import qualified Yuho.SuppliedProofStatus.Types as P

encodePresumptionDocument :: PresumptionDocument -> BS.ByteString
encodePresumptionDocument = encodeRecord

decodePresumptionDocument :: BS.ByteString -> Either AuthoringDiagnostic PresumptionDocument
decodePresumptionDocument bytes = do
  wire <- either (Left . issue "PAJSON" "/" []) Right (decodeJson bytes)
  case lookupField "presumptionDocumentFormat" wire of
    Just (JStr version) | version == presumptionAuthoringFormat -> pure ()
    _ -> Left (issue "PAVERSION" "/presumptionDocumentFormat" [] "expected explicit v0.4 presumption document")
  either (Left . issue "PAJSON" "/" [] . T.pack) Right (A.eitherDecodeStrict' bytes)

data PresumptionCompilation = PresumptionCompilation BS.ByteString PresumptionSnapshot
  CompiledAnalysis [PresumptionMapping] [GeneratedSource] K.ValidatedPresumption
presumptionCompiledRequest :: PresumptionCompilation -> BS.ByteString
presumptionCompiledRequest (PresumptionCompilation x _ _ _ _ _) = x
presumptionCompiledSnapshot :: PresumptionCompilation -> PresumptionSnapshot
presumptionCompiledSnapshot (PresumptionCompilation _ x _ _ _ _) = x
presumptionProofCompilation :: PresumptionCompilation -> CompiledAnalysis
presumptionProofCompilation (PresumptionCompilation _ _ x _ _ _) = x
presumptionCompiledMappings :: PresumptionCompilation -> [PresumptionMapping]
presumptionCompiledMappings (PresumptionCompilation _ _ _ x _ _) = x
presumptionCompiledSources :: PresumptionCompilation -> [GeneratedSource]
presumptionCompiledSources (PresumptionCompilation _ _ _ _ x _) = x

data PresumptionEvaluation = PresumptionEvaluation PresumptionReport PresumptionCompilation BS.ByteString
presumptionEvaluationReport :: PresumptionEvaluation -> PresumptionReport
presumptionEvaluationReport (PresumptionEvaluation x _ _) = x
presumptionEvaluationCompilation :: PresumptionEvaluation -> PresumptionCompilation
presumptionEvaluationCompilation (PresumptionEvaluation _ x _) = x
presumptionEvaluationSnapshot :: PresumptionEvaluation -> PresumptionSnapshot
presumptionEvaluationSnapshot = presumptionCompiledSnapshot . presumptionEvaluationCompilation
presumptionEvaluationResponse :: PresumptionEvaluation -> BS.ByteString
presumptionEvaluationResponse (PresumptionEvaluation _ _ x) = x

presumptionSnapshotFor :: PresumptionDocument -> Analysis -> PresumptionSnapshot
presumptionSnapshotFor d a = PresumptionSnapshot (sha256Text (encodeRecord (d,a,presumptionProfile))) presumptionProfile a d

compilePresumptionAnalysis :: PresumptionDocument -> Text -> Either [AuthoringDiagnostic] PresumptionCompilation
compilePresumptionAnalysis d key = do
  let validation = validatePresumptionBindings d key
      base = presumptionProofDocument d
      failure code ids message = Left [issue code "/presumptionRegistrations" (key:ids) message]
  if presumptionAnalysisReady validation then pure () else Left (presumptionDiagnostics validation)
  a <- maybe (failure "PAANALYSIS" [] "analysis not found") Right (findAnalysis base key)
  compiled <- compileAnalysis (proofSliceDocument d key) key
  wire <- either (failure "PAJSON" []) Right (decodeJson (compiledRequest compiled))
  let snapshot = presumptionSnapshotFor d a
      regs = registrationsFor d key
      required = requiredPresumptionInputs d a
      ordinary = compiledRequirements compiled
      extras = [input | input <- required, input `notElem` map mappedNode ordinary]
      leafId input = maybe (generated "leaf" input) mappedKernelRequirement (find ((== input) . mappedNode) ordinary)
      generated role input = "pa-" <> role <> ":" <> sha256Text (encodeRecord input)
      selected input = find (\x -> assessmentInput x == input && assessmentId x `elem` analysisAssessments a) (documentAssessments base)
      material owner text = GeneratedSource (generated "source" owner) "generated_presumption_compilation" text [owner]
      regSources = [material (registeredId r) (UTF8.decodeUtf8 (encodeRecord r)) | r <- regs]
      extraSources = [material input (input <> "\n" <> maybe "" (UTF8.decodeUtf8 . encodeRecord) (selected input)) | input <- extras]
      sources = regSources ++ extraSources
      whole s = byteSpan (generatedSourceText s) 0 (BS.length (UTF8.encodeUtf8 (generatedSourceText s)))
      coreSpan s = let x = whole s in C.Span (start x) (end x) (startLine x) (startColumn x) (endLine x) (endColumn x)
      textSpan s = spanJson (coreSpan s)
      sourceValue s = JObj [("id",JStr (generatedSourceId s)),("path",JStr "generated/presumption.txt"),
        ("text",JStr (generatedSourceText s)),("sha256",JStr (sha256Text (UTF8.encodeUtf8 (generatedSourceText s))))]
      condition s c = JObj ([("kind",JStr (registeredConditionKind c)),("span",textSpan s)] ++ case registeredConditionLeaf c of
        Just input -> [("leaf_id",JStr (leafId input))]
        Nothing -> [("members",JArr (map (condition s) (registeredConditionMembers c)))])
      registrations = [JObj [("presumption_id",JStr (generated "registration" (registeredId r))),
          ("target_leaf_id",JStr (leafId (registeredTarget r))),("source_id",JStr (generatedSourceId s)),
          ("span",textSpan s),("trigger",condition s (registeredTrigger r)),("rebuttal",condition s (registeredRebuttal r))]
        | (r,s) <- zip regs regSources]
      -- Condition-only leaves need registry declarations because the unchanged
      -- proof protocol forbids unreferenced facts. These generated storage
      -- branches are NOT authored rules or downstream execution observations.
      extraRules = [JObj [("id",JStr (generated "storage" input)),("source_id",JStr (generatedSourceId s)),
        ("program",JObj [("id",JStr (generated "branch" input)),("path",JArr [JStr (generated "branch" input)]),
          ("span",textSpan s),("definitions",JBool False),("children",JArr []),("penalties",JArr []),
          ("requirements",JArr [JObj [("id",JStr (leafId input)),("kind",JStr "leaf"),
            ("path",JArr [JStr (generated "branch" input)]),("span",textSpan s)]])]),("exceptions",JArr [])]
        | (input,s) <- zip extras extraSources]
      extraFacts = [(leafId input,JObj [("proof_status",P.suppliedStatusJson (classificationStatus (assessmentClassification x))),
        ("status_source",JObj [("assignment_id",JStr (generated "assignment" input)),("issuer_label",JStr (assessmentIssuer x)),
          ("origin",JStr (assessmentOrigin x)),("source_id",JStr (generatedSourceId s)),("span",textSpan s)])])
        | (input,s) <- zip extras extraSources, Just x <- [selected input]]
      extend name value = case (name,value) of
        ("fragment",_) -> JStr presumptionProfile
        ("sources",JArr xs) -> JArr (xs ++ map sourceValue sources)
        ("registry",JArr xs) -> JArr (xs ++ extraRules)
        ("facts",JObj xs) -> JObj (xs ++ extraFacts)
        _ -> value
      request = case wire of
        JObj xs -> JObj ([(name,extend name value) | (name,value) <- xs] ++ [("presumptions",JArr registrations)])
        _ -> wire
      mappings = [PresumptionMapping "registration" (registeredId r) (generated "registration" (registeredId r)) []
          (generatedSourceId s) (whole s) (registeredSources r) | (r,s) <- zip regs regSources]
        ++ [PresumptionMapping "condition" (registeredConditionId c) (generated "registration" (registeredId r)) path
          (generatedSourceId s) (whole s) (registeredConditionSources c)
          | (r,s) <- zip regs regSources, (role,root) <- [("trigger",registeredTrigger r),("rebuttal",registeredRebuttal r)],
            (c,path) <- conditionPaths [role] root]
        ++ concat [[PresumptionMapping "condition_input" input (leafId input) [] (generatedSourceId s) (whole s)
              (maybe [] nodeSources (find ((== input) . nodeId) (lawNodes (documentLaw base)))),
            PresumptionMapping "assignment" (assessmentId x) (generated "assignment" input) [] (generatedSourceId s) (whole s) (assessmentSources x)]
          | (input,s) <- zip extras extraSources, Just x <- [selected input]]
      scaffolding = concat [[PresumptionMapping category input (generated role input) [] (generatedSourceId s) (whole s) []
        | (category,role) <- [("condition_storage_rule","storage"),("condition_storage_branch","branch")]] | (input,s) <- zip extras extraSources]
        ++ [PresumptionMapping "generated_source" owner (generatedSourceId s) [] (generatedSourceId s) (whole s) []
          | s <- sources, owner <- generatedSourceObjects s]
      bytes = encodeJson request
      backend e = failure ("PABACKEND/" <> C.diagCode e) (nub (concatMap (\m -> [presumptionMappingAuthored m | presumptionMappingKernel m `elem` map snd (C.diagParameters e)]) mappings)) (T.pack (show e))
  json <- either (failure "PABACKEND/JSON" []) Right (decodeJson bytes)
  decoded <- either backend Right (decodePresumptionRequest json)
  checked <- either backend Right (validatePresumptionRequest decoded)
  pure (PresumptionCompilation bytes snapshot compiled (mappings ++ scaffolding) sources checked)
  where
    conditionPaths path c = (c,path) : concat [conditionPaths (path ++ [T.pack (show i)]) child | (i,child) <- zip [0 :: Int ..] (registeredConditionMembers c)]

validatePresumptionAnalysis :: PresumptionDocument -> Text -> PresumptionValidation
validatePresumptionAnalysis d key = let report = validatePresumptionBindings d key in
  if not (presumptionAnalysisReady report) then report else case compilePresumptionAnalysis d key of
    Left errors -> report {presumptionAnalysisReady=False,presumptionDiagnostics=errors}
    Right _ -> report

evaluatePresumptionAnalysis :: PresumptionCompilation -> Either [AuthoringDiagnostic] PresumptionEvaluation
evaluatePresumptionAnalysis compiled@(PresumptionCompilation bytes snapshot base mappings _ validated) = do
  let d = presumptionSnapshotDocument snapshot
      doc = presumptionProofDocument d
      a = presumptionSnapshotAnalysis snapshot
      sid = presumptionSnapshotId snapshot
      kernel = either (\e -> Left [issue ("PABACKEND/" <> C.diagCode e) (C.diagPath e) [analysisId a] (T.pack (show e))]) Right
  derived <- kernel (evaluatePresumptions validated)
  proof <- kernel (evaluateProofWith (K.presumptionValidatedBase validated) (K.presumptionEffective derived))
  selection <- kernel (selectProofPenalties (K.presumptionValidatedBase validated) proof)
  response <- kernel (encodePresumptionResult validated derived proof selection)
  wire <- either (\reason -> Left [issue "PAJSON" "/" [] reason]) Right (decodeJson bytes)
  let downstream = (applicationReportFromResult base proof (inputDigest wire))
        {reportSnapshot=sid,reportProfile=presumptionProfile}
      leafKernel input = maybe (maybe "" presumptionMappingKernel (find (\m -> presumptionMappingKind m == "condition_input" && presumptionMappingAuthored m == input) mappings))
        mappedKernelRequirement (find ((== input) . mappedNode) (compiledRequirements base))
      regFor kernelId = find (\r -> any (\m -> presumptionMappingKind m == "registration" && presumptionMappingAuthored m == registeredId r && presumptionMappingKernel m == kernelId) mappings) (registrationsFor d (analysisId a))
      trace authored actual = ResolvedCondition authored (P.satisfactionText (K.conditionTraceValue actual))
        (zipWith trace (registeredConditionMembers authored) (K.conditionTraceChildren actual))
      routes = [RegistrationObservation (projectionIdentity "derivation" (sid,registeredId r)) r "evaluated" (K.stateText (K.derivationState route))
        (trace (registeredTrigger r) (K.derivationTrigger route)) (trace (registeredRebuttal r) (K.derivationRebuttal route))
        | route <- K.presumptionDerivations derived, Just r <- [regFor (K.registrationId (K.derivationRegistration route))]]
      leaves = [EffectiveLeafObservation (projectionIdentity "effective-leaf" (sid,input)) input (analysisScope a) selected
        (P.satisfactionText (K.leafDirect resolution)) (P.satisfactionText (K.leafEffective resolution))
        [registeredId r | route <- K.leafRoutes resolution, Just r <- [regFor (K.registrationId (K.derivationRegistration route))]]
        [o | o <- reportRequirements downstream, observationNode o == input]
        | input <- requiredPresumptionInputs d a, Just resolution <- [Map.lookup (leafKernel input) (K.presumptionResolutions derived)],
          selected <- documentAssessments doc, assessmentInput selected == input, assessmentId selected `elem` analysisAssessments a]
      report = PresumptionReport sid a leaves routes downstream
        "Registered technical support, not evidence weighing, factual falsity, burden transfer or independently determined legal rebuttal sufficiency. Derivations resolve globally; downstream proof guards may be skipped."
  if length routes == length (registrationsFor d (analysisId a)) && length leaves == length (requiredPresumptionInputs d a)
    then pure (PresumptionEvaluation report compiled response)
    else Left [issue "PAINTERNAL" "/presumptionReport" [analysisId a] "validated mapping coverage incomplete"]
