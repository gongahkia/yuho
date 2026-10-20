{-# LANGUAGE OverloadedStrings #-}
-- Independent review inputs are retained byte-for-byte in fixtures/typed-boundary.
module TypedBoundaryChecks (runTypedBoundaryChecks) where

import Control.Monad (forM, unless)
import qualified Data.Aeson as A
import qualified Data.Aeson.Key as Key
import qualified Data.Aeson.KeyMap as KM
import qualified Data.ByteString as BS
import Data.List (find, nub)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as T
import System.Directory (createDirectoryIfMissing)
import System.Environment (lookupEnv)
import System.FilePath ((</>))
import Text.Read (readMaybe)
import TypedExamples (permissionDocument, thresholdDocument)
import Yuho.Authoring

require :: Show e => Either e a -> IO a
require = either (fail . show) pure
check :: String -> Bool -> IO ()
check name ok = unless ok (fail ("typed boundary: " <> name))

runTypedBoundaryChecks :: FilePath -> IO ()
runTypedBoundaryChecks root = do
  let fixture name = BS.readFile (root </> "test/fixtures/typed-boundary" </> name)
      reviewerUnknown = ["application-form-extra-key","application-form-hidden-negation","nullary-form-extra-contents",
        "nullary-form-extra-key","classification-extra-contents","classification-extra-key"]
  -- Collect every failure before asserting, so the pre-fix execution exposes
  -- both independent defect categories instead of stopping at the first one.
  originals <- forM reviewerUnknown $ \name -> do
    bytes <- fixture (name <> ".json")
    let result = decodeTypedDocument bytes
    emit (name <> ".result.json") (A.object ["decoded" A..= either (const False) (const True) result,
      "diagnostic" A..= either Just (const Nothing) result])
    pure (name,either (const True) (const False) result)
  duplicates <- forM [("repeated-provenance","assessment_assertion"),("repeated-annotation","annotation_about")] $ \(name,kind) -> do
    bytes <- fixture (name <> ".document.json")
    d <- require (decodeTypedDocument bytes)
    let validation = validateTypedAnalysis d "analysis-a"
    check "reviewer's repeated-reference input is otherwise valid" (null (validateTypedDocument d) && typedAnalysisReady validation)
    evaluated <- require (compileTypedAnalysis d "analysis-a" >>= evaluateTypedAnalysis)
    let authored = projectTypedAuthored d "analysis-a"
        projected = projectTypedEvaluation evaluated
    emit (name <> ".result.json") (A.object ["validation" A..= validation,
      "authoredProjection" A..= either A.toJSON (A.toJSON . typedProjectionData) authored,
      "evaluatedProjection" A..= either A.toJSON (A.toJSON . typedProjectionData) projected])
    case (authored,projected) of
      (Right ap,Right ep) -> do
        repeatChecks kind d evaluated ap ep
        pure (name,True)
      _ -> pure (name,False)
  let failed = [name | (name,False) <- originals ++ duplicates]
  check ("independent reviewer regressions failed: " <> show failed) (null failed)
  negation <- fixture "application-form-hidden-negation.json"
  check "constructor diagnostic identifies exact nested property" (case decodeTypedDocument negation of
    Left e -> "$.typedExpressions[0].expressionForm.negated" `T.isInfixOf` diagnosticMessage e
    _ -> False)
  seedBytes <- fixture "valid-reviewer.document.json"
  seed <- require (decodeTypedDocument seedBytes)
  permission <- require permissionDocument
  let complete = permission {typedPresentation=[Presentation "q:ada" (Map.fromList [("unexpected","retained open property"),("negated","presentation only")])]}
      numeric = thresholdDocument (ExactInteger 36) 35
      unknown = numeric {typedValues=[v {valueExact=UnknownInteger "integer" "not_determined"} | v <- typedValues numeric]}
      alternate = complete {typedAssessments=[a {typedClassification=TechnicalUnresolved "pending"} | a <- typedAssessments complete]}
      negative = complete {typedAssessments=[a {typedClassification=TechnicalFalse} | a <- typedAssessments complete]}
      anyGroup = seed {typedExpressions=[if expressionForm e == TypedAll then e {expressionForm=TypedAny} else e | e <- typedExpressions seed]}
      scalarComparison = ["typedExpressions","0","expressionForm"]
      matrix = [("document",complete,[]),("entity-type",complete,["typedEntityTypes","0"]),
        ("entity",complete,["typedEntities","0"]),("predicate",complete,["typedPredicates","0"]),
        ("argument-role",complete,["typedPredicates","0","predicateRoles","0"]),
        ("ground-application",complete,["typedApplications","0"]),("ground-tuple",complete,["typedApplications","0","applicationTuple"]),
        ("metadata",complete,["typedApplications","0","applicationMeta"]),
        ("assessment",complete,["typedAssessments","0"]),("assessment-tuple",complete,["typedAssessments","0","assessedTuple"]),
        ("scope",complete,["typedAssessments","0","typedAssessmentScope"]),
        ("true-classification",complete,["typedAssessments","0","typedClassification"]),
        ("false-classification",negative,["typedAssessments","0","typedClassification"]),
        ("unresolved-classification",alternate,["typedAssessments","0","typedClassification"]),
        ("scalar",numeric,["typedScalars","0"]),("value-record",numeric,["typedValues","0"]),
        ("integer-value",numeric,["typedValues","0","valueExact"]),
        ("unresolved-integer",unknown,["typedValues","0","valueExact"]),
        ("expression",numeric,["typedExpressions","0"]),("comparison",numeric,scalarComparison),
        ("ground-form",complete,["typedExpressions","0","expressionForm"]),
        ("all-form",seed,["typedExpressions","2","expressionForm"]),
        ("any-form",anyGroup,["typedExpressions","2","expressionForm"]),
        ("link",complete,["typedLinks","0"]),("rule",complete,["typedRules","0"]),
        ("proposition",complete,["typedPropositions","0"]),("analysis",complete,["typedAnalyses","0"]),
        ("source",complete,["typedOriginalSources","0"]),("assertion",complete,["typedCaseAssertions","0"]),
        ("source-ref",complete,["typedCaseAssertions","0","assertionSources","0"]),
        ("source-span",complete,["typedCaseAssertions","0","assertionSources","0","referenceSpan"]),
        ("annotation",complete,["typedAnnotations","0"]),("presentation-record",complete,["typedPresentation","0"])]
  _ <- forM matrix $ \(name,d,path) -> do
    malformed <- require (modifyJson path (insert "unexpected" (A.Bool True)) (A.toJSON d))
    let result = decodeTypedDocument (encodeRecord malformed)
    emit (name <> ".unknown.json") malformed
    emit (name <> ".unknown-result.json") (either A.toJSON (const A.Null) result)
    check (name <> " rejects unknown closed member") (case result of Left e -> "unexpected" `T.isInfixOf` diagnosticMessage e; _ -> False)
    -- The direct public FromJSON instance must not be a permissive bypass.
    check (name <> " FromJSON is closed") (case A.fromJSON malformed :: A.Result TypedDocument of A.Error _ -> True; _ -> False)
    pure ()
  _ <- forM [("missing-contents",numeric,scalarComparison,"contents"),("missing-tag",numeric,scalarComparison,"tag")] $ \(name,d,path,field) -> do
    malformed <- require (modifyJson path (remove field) (A.toJSON d))
    check name (case decodeTypedDocument (encodeRecord malformed) of Left e -> field `T.isInfixOf` diagnosticMessage e && not ("unexpected field" `T.isInfixOf` diagnosticMessage e); _ -> False)
    pure ()
  let unknownConstructor = modifyJson scalarComparison (insert "tag" (A.String "Not")) (A.toJSON numeric)
  malformed <- require unknownConstructor
  check "unsupported constructor remains rejected" (case decodeTypedDocument (encodeRecord malformed) of Left _ -> True; _ -> False)
  _ <- forM [(complete,"analysis:ada"),(numeric,"analysis:threshold"),(seed,"analysis-a")] $ \(d,key) -> do
    decoded <- require (decodeTypedDocument (encodeTypedDocument d))
    check "valid round trip and open presentation map" (decoded == d)
    original <- require (compileTypedAnalysis d key >>= evaluateTypedAnalysis)
    replay <- require (compileTypedAnalysis decoded key >>= evaluateTypedAnalysis)
    p <- require (projectTypedEvaluation original)
    q <- require (projectTypedEvaluation replay)
    check "unchanged snapshot/report/mappings on replay" (typedEvaluationSnapshot original == typedEvaluationSnapshot replay && typedEvaluationReport original == typedEvaluationReport replay && typedEvaluationMappings original == typedEvaluationMappings replay)
    first <- require (encodeTypedProjection p); second <- require (encodeTypedProjection q)
    check "stable complete projection replay" (first == second)
    pure ()
  sourceControls complete
  putStrLn ("typed boundary regressions: 6 original constructor adversaries, 2 original repeated-reference inputs, " <> show (length matrix) <> " closed-record/constructor injections, open maps, projection/replay/source controls passed")

-- No duplicate object nodes: repeated references are separate relationships.
repeatChecks :: Text -> TypedDocument -> TypedEvaluation -> TypedProjection -> TypedProjection -> IO ()
repeatChecks kind d evaluated ap ep = do
  let dataValue = typedProjectionData ep
      matches = filter ((== kind) . typedEdgeKind) (typedProjectionEdges dataValue)
      repeated = [e | e <- matches, length [x | x <- matches, typedEdgeFrom x == typedEdgeFrom e, typedEdgeTo x == typedEdgeTo e] == 2]
      edges = typedProjectionEdges dataValue
  check "two distinct repeated-reference edges preserved" (length repeated == 2 && length (nub (map typedEdgeId repeated)) == 2)
  check "authored/evaluated projection integrity" (null (validateTypedProjection (typedProjectionData ap)) && null (validateTypedProjection dataValue))
  second <- require (projectTypedEvaluation evaluated >>= encodeTypedProjection)
  first <- require (encodeTypedProjection ep)
  check "deterministic repeated-reference projection" (first == second)
  reloaded <- require (decodeTypedDocument (encodeTypedDocument d))
  replay <- require (compileTypedAnalysis reloaded "analysis-a" >>= evaluateTypedAnalysis >>= projectTypedEvaluation >>= encodeTypedProjection)
  check "repeated-reference saved replay" (first == replay)
  _ <- forM [TypedExpressionFocus "expr-a",TypedRuleFocus] $ \focus -> do
    view <- require (typedReferenceView ep focus [])
    check "view partitions and endpoints" (null (validateTypedView ep view))
    check "all repeated edges included or explicitly omitted" (all (\e -> typedEdgeId e `elem` viewIncludedEdges view || typedEdgeId e `elem` viewOmittedEdges view) repeated)
    if kind == "assessment_assertion" then check "focused view retains both provenance connections" (all ((`elem` viewIncludedEdges view) . typedEdgeId) repeated) else pure ()
    _ <- require (encodeTypedViewJson ep view); _ <- require (encodeTypedViewXml ep view); _ <- require (encodeTypedViewSvg ep view)
    check "view does not drop endpoints" (all (\e -> typedEdgeId e `notElem` viewIncludedEdges view || (typedEdgeFrom e `elem` viewIncludedNodes view && typedEdgeTo e `elem` viewIncludedNodes view)) edges)
    pure ()
  -- The first occurrence keeps its pre-hardening identity for compatibility.
  let unique = d {typedAssessments=[a {typedAssertionRefs=nub (typedAssertionRefs a)} | a <- typedAssessments d],
        typedAnnotations=[a {annotationAbout=nub (annotationAbout a)} | a <- typedAnnotations d]}
  canonical <- require (compileTypedAnalysis unique "analysis-a" >>= evaluateTypedAnalysis >>= projectTypedEvaluation)
  check "existing first edge identity retained" (case repeated of e:_ -> typedEdgeId e `elem` map typedEdgeId (typedProjectionEdges (typedProjectionData canonical)); _ -> False)

sourceControls :: TypedDocument -> IO ()
sourceControls d = do
  source <- maybe (fail "missing retained fixture source") pure (find ((== "source:synthetic") . sourceId) (typedOriginalSources d))
  a <- require (sourceAnchorCodePoints source 0 3)
  b <- require (sourceAnchorCodePoints source 4 11)
  let changed = d {typedAssessments=[x {typedAssessmentMeta=(typedAssessmentMeta x) {typedSources=[a,a,b]}} | x <- typedAssessments d]}
  check "shared/repeated source controls valid" (null (validateTypedDocument changed) && typedAnalysisReady (validateTypedAnalysis changed "analysis:ada"))
  p <- require (compileTypedAnalysis changed "analysis:ada" >>= evaluateTypedAnalysis >>= projectTypedEvaluation)
  let originals = filter ((== "original_source") . typedEdgeKind) (typedProjectionEdges (typedProjectionData p))
      own = filter (elem "assessment:ada" . typedEdgeOrigins) originals
  check "same source different anchors and repeated entries preserved" (length own == 3 && length (nub (map typedEdgeId own)) == 3 && map typedEdgeOriginal own == map Just [a,a,b])
  check "shared source across separate assessments supported" (any (elem "assessment:ben" . typedEdgeOrigins) originals)
  check "single original source node" (length [n | n <- typedProjectionNodes (typedProjectionData p), typedNodeKind n == "source", typedNodeAuthoredId n == "source:synthetic"] == 1)
  recovered <- require (recoverTypedSource p a)
  check "UTF8 anchored recovery unchanged" (excerptText recovered == Just "Zoë")

modifyJson :: [Text] -> (A.Value -> Either String A.Value) -> A.Value -> Either String A.Value
modifyJson [] f value = f value
modifyJson (key:rest) f (A.Object object) = do
  child <- maybe (Left ("unknown test object path " <> T.unpack key)) Right (KM.lookup (Key.fromText key) object)
  value <- modifyJson rest f child
  pure (A.Object (KM.insert (Key.fromText key) value object))
modifyJson (index:rest) f array@(A.Array _) = do
  values <- case A.fromJSON array :: A.Result [A.Value] of A.Success xs -> Right xs; A.Error e -> Left e
  offset <- maybe (Left "invalid test array index") Right (readMaybe (T.unpack index))
  if offset < 0 || offset >= length values then Left "missing test array element" else
    A.toJSON <$> traverse (\(i,value) -> if i == offset then modifyJson rest f value else Right value) (zip [0::Int ..] values)
modifyJson _ _ _ = Left "test path is not a container"

insert :: Text -> A.Value -> A.Value -> Either String A.Value
insert key value (A.Object object) = Right (A.Object (KM.insert (Key.fromText key) value object))
insert _ _ _ = Left "injection target must be an object"
remove :: Text -> A.Value -> Either String A.Value
remove key (A.Object object) = Right (A.Object (KM.delete (Key.fromText key) object))
remove _ _ = Left "removal target must be an object"

emit :: A.ToJSON a => FilePath -> a -> IO ()
emit name value = do
  output <- lookupEnv "YUHO_TYPED_BOUNDARY_EVIDENCE"
  case output of Nothing -> pure (); Just folder -> createDirectoryIfMissing True folder >> BS.writeFile (folder </> name) (encodeRecord value)
