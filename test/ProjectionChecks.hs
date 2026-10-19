{-# LANGUAGE OverloadedStrings #-}
module ProjectionChecks (runProjectionChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.Char (isAsciiLower, isAsciiUpper, isDigit)
import Data.List (find, nub, sort)
import qualified Data.Map.Strict as Map
import Data.Maybe (isNothing)
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Calendar (fromGregorian)
import Cheating
import Yuho.Authoring

runProjectionChecks :: IO ()
runProjectionChecks = do
  drafts
  meaning
  identityAndProvenance
  comparisons
  putStrLn "projection: drafts without execution, snapshot attachment, identity/connectivity, provenance, encoders and comparison audit passed"

evaluateDoc :: AuthoringDocument -> IO Evaluation
evaluateDoc doc = require (compileAnalysis doc "analysis:cheating" >>= evaluateAnalysis)

occurrence :: Projection -> Text -> IO ProjectionNode
occurrence projection key = maybe (fail ("occurrence missing: " <> Text.unpack key)) pure
  (find (\n -> projectedNodeKind n == "occurrence" && maybe False ((== key) . occurrenceAuthoredNode)
    (projectedNodeOccurrence n)) (projectionNodes (projectionData projection)))

drafts :: IO ()
drafts = do
  let draft = pendingDocument { documentAnalyses = [a {analysisAssessments=
        filter (/= "assessment:property-fault-pending") (analysisAssessments a)}
        | a <- documentAnalyses pendingDocument] }
  projected <- require (projectAuthored draft "analysis:cheating")
  missing <- occurrence projected "f:property-fraudulent-or-dishonest"
  check "missing binding has no invented computed value" (projectedNodeComputed missing == Nothing
    && (bindingState <$> projectedNodeBinding missing) == Just "missing"
    && projectedNodeEvaluation missing == "not_requested")
  check "draft diagnostics and context retained" (any ((== "AMISSING") . diagnosticCode)
    (projectionDiagnostics (projectionData projected))
    && snapshotDocument (projectionSnapshot (projectionData projected)) == draft)
  -- This structurally valid, completely bound tree exceeds the backend node
  -- budget. Projection succeeding proves the authored path does not compile.
  let scope = Scope "actor:test" "context:test"
      label i = "leaf-" <> Text.pack (show (i :: Int))
      node key kind = LawNode key kind key Nothing Nothing []
      leaves = map label [1..600]
      big = AuthoringDocument authoringFormat "doc:large" (LawDefinition "law:large" "1"
        (node "rule" "rule" : node "root" "all" : [node key "input" | key <- leaves])
        (LawEdge "requires" "rule" "root" "requires" : [LawEdge ("member-" <> key) "root" key "member" | key <- leaves]) [])
        [] [] [Assessment ("assessment-" <> key) key scope (Classification Proved) "assumption" "caller"
          "synthetic_fixture" "assumption" [] [] | key <- leaves]
        [Analysis "large-analysis" "rule" scope ["assessment-" <> key | key <- leaves] (fromGregorian 2026 10 19)] [] [] []
  large <- require (projectAuthored big "large-analysis")
  check "authored projection never requires backend compilation" (case compileAnalysis big "large-analysis" of
    Left _ -> projectionApplication (projectionData large) == Nothing
      && all (isNothing . projectedNodeComputed) (projectionNodes (projectionData large))
    Right _ -> False)
  let bad = cheatingDocument {documentLaw=(documentLaw cheatingDocument) {lawEdges=
        LawEdge "edge:dangling" "o:cheating" "absent" "requires" : lawEdges (documentLaw cheatingDocument)}}
  check "structural errors not repaired for projection" (case projectAuthored bad "analysis:cheating" of
    Left diagnostics -> any (elem "edge:dangling" . diagnosticObjects) diagnostics; Right _ -> False)
  base <- evaluateDoc cheatingDocument
  own <- require (projectEvaluation base)
  same <- require (projectEvaluationOn cheatingDocument base)
  check "own snapshot reused exactly" (projectionSnapshot (projectionData own) == evaluationSnapshot base
    && projectionId (projectionData same) == projectionId (projectionData own))
  let editedReason = modifyAssessment (assessmentFor "f:deception") (\a -> a {assessmentReason="new reason"}) cheatingDocument
      editedPresentation = cheatingDocument {documentPresentation=[Presentation "o:cheating" (Map.singleton "x" "999")]}
  forM_ [pendingDocument,editedReason,editedPresentation] $ \doc ->
    check "stale overlay rejected, including metadata-only edits" (case projectEvaluationOn doc base of
      Left diagnostics -> any ((== "PSTALE") . diagnosticCode) diagnostics; Right _ -> False)

meaning :: IO ()
meaning = do
  authored <- require (projectAuthored pendingDocument "analysis:cheating")
  pending <- evaluateDoc pendingDocument >>= require . projectEvaluation
  satisfied <- evaluateDoc cheatingDocument >>= require . projectEvaluation
  let defeatedDoc = foldl (\doc key -> withStatus key Proved doc) cheatingDocument
        ["f:unsoundness-time","f:nature-causation","f:nature-incapacity"]
  defeated <- evaluateDoc defeatedDoc >>= require . projectEvaluation
  guardInput <- occurrence pending "f:unsoundness-time"
  check "skipped guard keeps selected not_proved and absent computation"
    (projectedNodeEvaluation guardInput == "not_evaluated" && projectedNodeComputed guardInput == Nothing
      && (projectedNodeBinding guardInput >>= bindingSupplied) == Just (Classification NotProved)
      && maybe False (Text.isInfixOf "requirements_unresolved") (projectedNodeSkipReason guardInput))
  before <- occurrence authored "f:unsoundness-time"
  check "authored state is not a skipped evaluation" (projectedNodeEvaluation before == "not_requested"
    && projectedNodeComputed before == Nothing && projectedNodeSkipReason before == Nothing)
  fault <- occurrence pending "f:property-fraudulent-or-dishonest"
  check "supplied uncertainty distinct from computed uncertainty"
    ((projectedNodeBinding fault >>= bindingSupplied) == Just (Classification (Unresolved NotDetermined))
     && projectedNodeComputed fault == Just "unresolved" && projectedNodeEvaluation fault == "evaluated")
  falseInput <- occurrence satisfied "f:unsoundness-time"
  check "not_proved kept beside evaluated not_satisfied"
    ((projectedNodeBinding falseInput >>= bindingSupplied) == Just (Classification NotProved)
      && projectedNodeComputed falseInput == Just "not_satisfied" && projectedNodeEvaluation falseInput == "evaluated")
  root <- occurrence defeated "o:cheating"
  check "evaluated exception defeat visible" (projectedNodeComputed root == Just "not_satisfied"
    && projectedNodeBranchReason root == Just "defeated")
  check "groups have no supplied assessment" (all (isNothing . projectedNodeBinding)
    [n | n <- projectionNodes (projectionData pending), projectedNodeKind n == "occurrence", projectedNodeRole n `elem` ["all","any"]])
  let selected = find ((== objectProjectionId "assessment:property-fault-pending") . projectedNodeId)
        (projectionNodes (projectionData pending))
      retained = find ((== objectProjectionId (assessmentFor "f:property-fraudulent-or-dishonest")) . projectedNodeId)
        (projectionNodes (projectionData pending))
  check "selected and retained assessments distinct" ((selected >>= projectedNodeSelected) == Just True
    && (retained >>= projectedNodeSelected) == Just False)
  forM_ [authored,pending,satisfied,defeated] $ \p -> do
    check "all projection endpoints and origins valid" (null (validateProjection (projectionData p)))
    _ <- require (encodeProjection p)
    _ <- require (encodeProjectionLegacyJson p)
    _ <- require (encodeProjectionLegacyXml p)
    svg <- require (encodeProjectionSvg p)
    check "SVG has explicit state column headings" (all (`BS.isInfixOf` svg)
      ["SUPPLIED CLASSIFICATION","COMPUTED RESULT","EVALUATION STATE"])

identityAndProvenance :: IO ()
identityAndProvenance = do
  scope <- case documentAnalyses cheatingDocument of
    analysis:_ -> pure (analysisScope analysis)
    [] -> fail "cheating fixture has no analysis"
  let
      collisionDoc = cheatingDocument {documentLaw=(documentLaw cheatingDocument) {
          lawNodes=LawNode "f/deception" "input" "second distinct input" Nothing Nothing [] : lawNodes (documentLaw cheatingDocument),
          lawEdges=LawEdge "edge:collision" "g:cheating-requirements" "f/deception" "member" : lawEdges (documentLaw cheatingDocument)},
        documentAssessments=Assessment "assessment:collision" "f/deception" scope (Classification Proved)
          "explicit assumption" "caller" "external_assertion" "assumption" [] [] : documentAssessments cheatingDocument,
        documentAnalyses=[a {analysisAssessments="assessment:collision":analysisAssessments a} | a <- documentAnalyses cheatingDocument],
        documentRelationships=[Relationship key "support" "assertion:description" "assertion:message" "same label"
          | key <- ["relation:one","relation/two"]] ++ documentRelationships cheatingDocument}
      naive = Text.map (\c -> if isAsciiLower c || isAsciiUpper c || isDigit c || c `elem` ['-','_','.'] then c else '-')
  projection <- require (projectAuthored collisionDoc "analysis:cheating")
  a <- occurrence projection "f:deception"
  b <- occurrence projection "f/deception"
  check "naive sanitization collision fixture is real" (naive "f:deception" == naive "f/deception")
  check "collision-safe occurrence/render identities" (projectedNodeId a /= projectedNodeId b)
  view <- require (lawOccurrenceView projection)
  check "SVG IDs remain unique" (let ids = map viewBindingRenderedId (viewNodeBindings view) in length ids == length (nub ids))
  svg <- require (encodeProjectionSvg projection)
  check "both collision-prone originals remain addressable in SVG"
    ("data-authored-id=\"f:deception\"" `BS.isInfixOf` svg && "data-authored-id=\"f/deception\"" `BS.isInfixOf` svg)
  let value = projectionData projection
      retainedEdges = [e | e <- projectionEdges value, projectedEdgeKind e == "support",
        projectedEdgeSemantics e == "descriptive"]
  check "parallel descriptive relationships not deduplicated" (length retainedEdges == 2
    && length (nub (map projectedEdgeId retainedEdges)) == 2
    && length (nub [(projectedEdgeFrom e,projectedEdgeTo e) | e <- retainedEdges]) == 1)
  (firstEdge, remainingEdges) <- case projectionEdges value of
    edge:edges -> pure (edge, edges)
    [] -> fail "projection has no edges"
  firstNode <- case projectionNodes value of
    node:_ -> pure node
    [] -> fail "projection has no nodes"
  let invalid = value {projectionEdges=firstEdge {projectedEdgeTo="missing-emitted-node"}:remainingEdges}
  check "missing emitted endpoints diagnosed before rendering" (any ((== "PENDPOINT") . diagnosticCode) (validateProjection invalid))
  check "duplicate projected identities diagnosed" (any ((== "PDUPLICATE") . diagnosticCode)
    (validateProjection value {projectionNodes=firstNode:projectionNodes value}))
  let anchor = SourceRef "source:anchor" (Just (TextSpan 2 5 1 3 1 6))
      sourced = modifyAssessment (assessmentFor "f:deception") (\x -> x {assessmentSources=[anchor]})
        cheatingDocument {documentSources=SourceRecord "source:anchor" "case" Nothing (Just "é猫") : documentSources cheatingDocument}
  evaluated <- evaluateDoc sourced
  p <- require (projectEvaluation evaluated)
  n <- occurrence p "f:deception"
  resolution <- maybe (fail "resolver unavailable") pure (resolveProjectedObject p (projectedNodeId n))
  check "one assessment resolves several assertions and original anchor"
    (length (resolvedAssessments resolution) == 1 && length (resolvedAssertions resolution) == 2
      && anchor `elem` resolvedOriginalReferences resolution)
  check "original and generated anchors never conflated" (all (\e -> projectedEdgeOriginalSource e == Nothing)
    [e | e <- projectionEdges (projectionData p), projectedEdgeSemantics e == "generated_provenance"]
      && not (null (resolvedGeneratedSpans resolution)))
  lawResolution <- maybe (fail "law resolver unavailable") pure (resolveProjectedObject p (objectProjectionId "o:cheating"))
  check "unfinished annotations recoverable" (any ((== "draft") . annotationState) (resolvedAnnotations lawResolution))
  let changedNumbering = [observationOriginalKernelId i | node <- projectionNodes (projectionData p),
        Just i <- [projectedNodeObservation node]]
  check "run observation kernel identities retained" (not (null changedNumbering) && any (/= Nothing) changedNumbering)

comparisons :: IO ()
comparisons = do
  original <- evaluateDoc cheatingDocument
  pending <- evaluateDoc pendingDocument
  a <- require (projectEvaluation original)
  b <- require (projectEvaluation pending)
  diff <- require (projectComparison original pending)
  let changed = projectedChangedObservations diff
      unchanged = projectedUnchangedObservations diff
      count f = length (filter f changed)
  check "original comparison row count preserved" (length (projectedAssessmentChanges diff) == 1
    && length changed == 20 && length unchanged == 6)
  check "20 rows explained without metadata inflation" (count observationComputedFieldChanged == 20
    && count observationComputedValueChanged == 5 && count observationEvaluationChanged == 15
    && count observationBranchReasonChanged == 2 && count observationReasonChanged == 16)
  check "new run identities do not force computed changes" (all (\row ->
    observationChangeOldIdentity row /= observationChangeNewIdentity row
      && not (observationComputedFieldChanged row) && not (observationEvaluationChanged row)) unchanged)
  let ids projection = sort [projectedNodeId node | node <- projectionNodes (projectionData projection), projectedNodeKind node == "occurrence"]
  check "compatible law occurrences align across scenario runs" (ids a == ids b)
  let bothRoutes = foldl (\doc key -> withStatus key Proved doc) cheatingDocument
        ["f:intentional-inducement","f:induced-act-or-omission","f:damage-or-harm"]
  before <- evaluateDoc bothRoutes
  after <- evaluateDoc (withStatus "f:property-fraudulent-or-dishonest" NotProved bothRoutes)
  alternative <- require (projectComparison before after)
  check "changed input with unchanged selected conclusion" (not (projectedConclusionChanged alternative)
    && not (null (projectedChangedObservations alternative)) && any ((== "o:cheating") . changeObject . observationChange)
      (projectedUnchangedObservations alternative))
  metadata <- evaluateDoc (modifyAssessment (assessmentFor "f:deception") (\x -> x {assessmentReason="new reason",assessmentIssuer="new caller"}) cheatingDocument)
  metadataDiff <- require (projectComparison original metadata)
  check "authorship-only changes do not become computed changes" (null (projectedChangedObservations metadataDiff)
    && not (projectedConclusionChanged metadataDiff)
    && any (changeAuthorship . assessmentChange) (projectedAssessmentChanges metadataDiff))

modifyAssessment :: Text -> (Assessment -> Assessment) -> AuthoringDocument -> AuthoringDocument
modifyAssessment key change doc = doc {documentAssessments=[if assessmentId a == key then change a else a | a <- documentAssessments doc]}

require :: Show a => Either a b -> IO b
require = either (fail . show) pure
check :: String -> Bool -> IO ()
check label condition = unless condition (fail ("projection: " <> label))
