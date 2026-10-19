{-# LANGUAGE OverloadedStrings #-}
module CaseViewChecks (runCaseViewChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.List (nub)
import Data.Maybe (isNothing)
import CaseApplication
import Cheating (assessmentFor)
import Yuho.Authoring

runCaseViewChecks :: IO ()
runCaseViewChecks = do
  draft <- require (projectAuthored caseDraft "analysis:cheating")
  view <- require (caseView draft)
  let includes key = elem (objectProjectionId key) (viewIncludedNodes view)
  check "case view includes unmapped material and relevant draft"
    (includes "assertion:weather" && includes "annotation:case-draft"
      && all (includes . assertionId) (documentAssertions caseDraft)
      && any ((== "AMISSING") . diagnosticCode) (projectionDiagnostics (projectionData draft)))
  unmapped <- require (caseAssertionLinks draft "assertion:weather")
  linked <- require (caseAssertionLinks draft "assertion:description")
  check "no link distinct from unselected links" (null (linkedAssessments unmapped)
    && length (linkedAssessments linked) == 2 && null (linkedSelectedAssessments linked))
  check "case-only state has no computation" (projectionApplication (projectionData draft) == Nothing
    && all (isNothing . projectedNodeComputed) (projectionNodes (projectionData draft)))
  let descriptive = [e | e <- projectionEdges (projectionData draft),
        projectedEdgeSemantics e == "descriptive", elem (projectedEdgeKind e) ["chronology","support","challenge"]]
  check "descriptive relationships preserved without execution" (length descriptive == 3
    && all (\e -> elem (projectedEdgeId e) (viewIncludedEdges view)) descriptive)
  forM_ [encodeViewJson draft view,encodeViewXml draft view,encodeViewSvg draft view] $ \encoded -> do
    bytes <- require encoded
    check "case reference encoder emits output" (not (BS.null bytes))
  missing <- require (applicationView draft (FocusInput "f:deception"))
  check "application view also accepts missing binding" (not (null (viewIncludedNodes missing))
    && null [n | n <- includedNodes draft missing, projectedNodeKind n == "observation"])
  base <- evaluateDoc caseDocument
  projection <- require (projectEvaluation base)
  focused <- require (applicationView projection (FocusInput "f:deception"))
  sameOccurrence <- case [n | n <- includedNodes projection focused, projectedNodeKind n == "occurrence"] of
    [n] -> require (applicationView projection (FocusOccurrence (projectedNodeId n)))
    _ -> fail "one deception occurrence expected"
  check "input and occurrence focus have same inclusion" (viewIncludedNodes focused == viewIncludedNodes sameOccurrence
    && viewIncludedEdges focused == viewIncludedEdges sameOccurrence)
  selected <- require (inspectAssessment projection (assessmentFor "f:deception"))
  alternative <- require (inspectAssessment projection "assessment:deception-alternative")
  check "alternative supplied proved never inherits computation"
    (inspectionSelected selected && not (inspectionSelected alternative)
      && assessmentClassification (inspectionAssessment alternative) == Classification Proved
      && all (\a -> not (applicationSelected a) && applicationComputed a == Nothing
        && applicationObservation a == Nothing && applicationEvaluation a == "not_applicable") (inspectionApplications alternative)
      && not (null (inspectionApplications alternative)))
  check "selected multi-assertion and cross-context references remain explicit"
    (length (resolvedAssertions (inspectionResolution selected)) == 2
      && any ((== Scope "actor:buyer" "context:message-exchange") . assertionScope)
        (resolvedAssertions (inspectionResolution selected)))
  let sourceNodes = [n | n <- includedNodes projection focused, projectedNodeRole n == "original_source"]
      edges = [e | e <- projectionEdges (projectionData projection), elem (projectedEdgeId e) (viewIncludedEdges focused)]
  check "shared original source has one handle and multiple references"
    (length (filter ((== objectProjectionId "source:case-note") . projectedNodeId) sourceNodes) == 1
      && length (filter ((== objectProjectionId "source:case-note") . projectedEdgeTo) edges) == 3)
  check "out of scope alternative intentionally omitted" (elem (objectProjectionId "assessment:deception-other-context")
    (viewOmittedNodes focused))
  other <- require (applicationView projection (FocusAssessments ["assessment:deception-other-context"]))
  otherDetail <- require (inspectAssessment projection "assessment:deception-other-context")
  check "explicit cross-scope assessment retains scope but gains no occurrence or observation"
    (elem (objectProjectionId "assessment:deception-other-context") (viewIncludedNodes other)
      && null (inspectionApplications otherDetail)
      && all (\n -> not (elem (projectedNodeKind n) ["occurrence","observation"])) (includedNodes projection other))
  let hasError result = case result of Left _ -> True; Right _ -> False
  check "invalid, duplicate and oversized focus rejected" (all hasError
    [applicationView projection (FocusInput "g:cheating-forms"),
     applicationView projection (FocusOccurrence "absent"),
     applicationView projection (FocusAssessments ["unknown"]),
     applicationView projection (FocusAssessments ["assessment:deception-alternative","assessment:deception-alternative"]),
     applicationView projection (FocusAssessments (map assessmentId (take 5 (documentAssessments caseDocument))))])
  check "partition and snapshot bindings validated before encoding"
    (hasError (encodeViewSvg projection focused {viewProjectionId="other-projection"})
      && hasError (encodeViewJson projection focused {viewIncludedNodes=[]})
      && null (validateProjectionView projection focused))
  anchored <- require (recoverOriginalSource projection (SourceRef "source:case-note" (Just (TextSpan 6 15 1 7 1 16))))
  locator <- require (recoverOriginalSource projection (SourceRef "source:registry" Nothing))
  unanchored <- require (recoverOriginalSource projection (SourceRef "source:interview" Nothing))
  check "exact UTF-8 excerpt; locator-only and unanchored remain without excerpt"
    (excerptText anchored == Just "猫 item." && excerptState anchored == "anchored"
      && excerptState locator == "locator_only" && excerptText locator == Nothing
      && excerptState unanchored == "retained_unanchored" && excerptText unanchored == Nothing
      && hasError (recoverOriginalSource projection (SourceRef "source:case-note" (Just (TextSpan 7 15 1 8 1 16)))))
  check "compiler spans stay separate from original excerpts" (not (null (resolvedGeneratedSpans (inspectionResolution selected)))
    && all ((/= "source:case-note") . sourceMappingSource) (resolvedGeneratedSpans (inspectionResolution selected)))
  pending <- evaluateDoc pendingCase
  pendingProjection <- require (projectEvaluation pending)
  unresolved <- require (inspectAssessment pendingProjection "assessment:property-fault-pending")
  skipped <- require (inspectAssessment pendingProjection (assessmentFor "f:unsoundness-time"))
  check "selected unresolved distinct from unselected alternative and evaluated result"
    (inspectionSelected unresolved && assessmentClassification (inspectionAssessment unresolved) == Classification (Unresolved NotDetermined)
      && all (\a -> applicationSelected a && applicationEvaluation a == "evaluated" && applicationComputed a == Just "unresolved")
        (inspectionApplications unresolved))
  check "selected guard assessment retained when not evaluated"
    (inspectionSelected skipped && assessmentClassification (inspectionAssessment skipped) == Classification NotProved
      && all (\a -> applicationSelected a && applicationEvaluation a == "not_evaluated"
        && applicationComputed a == Nothing && applicationSkipReason a /= Nothing) (inspectionApplications skipped))
  assumptionView <- require (applicationView pendingProjection (FocusInput "f:property-fraudulent-or-dishonest"))
  svg <- require (encodeViewSvg pendingProjection assumptionView)
  check "assumptions have no fabricated case assertions"
    (null [n | n <- includedNodes pendingProjection assumptionView, projectedNodeRole n == "assertion"]
      && BS.isInfixOf "Authored assumption; no case assertion cited." svg)
  revised <- evaluateDoc revisedCase
  let oldSnapshot = evaluationSnapshot base
  check "narrative revision preserves original snapshot, selection and classifications"
    (snapshotDocument oldSnapshot == caseDocument && documentAssessments caseDocument == documentAssessments revisedCase
      && documentAnalyses caseDocument == documentAnalyses revisedCase
      && snapshotId oldSnapshot /= snapshotId (evaluationSnapshot revised)
      && hasError (projectEvaluationOn revisedCase base))
  comparison <- require (projectComparison base revised)
  check "narrative edit changes provenance without changing computation"
    (null (projectedChangedObservations comparison) && length (projectedUnchangedObservations comparison) == 26
      && not (projectedConclusionChanged comparison)
      && case projectedAssessmentChanges comparison of
        [row] -> let change = assessmentChange row in changeReferencedMaterial change
          && not (changeSelection change || changeClassification change || changeAuthorship change)
        _ -> False)
  explicit <- require (projectComparison revised pending)
  check "explicit selection change remains mapped to stable occurrences"
    (length (projectedChangedObservations explicit) == 20 && projectedConclusionChanged explicit
      && any (changeSelection . assessmentChange) (projectedAssessmentChanges explicit)
      && length (nub (map observationChangeAlignment (projectedChangedObservations explicit))) == 20)
  putStrLn "case/application views: incomplete drafts, explicit provenance, selection versus execution, UTF-8 recovery and narrative revision passed"

evaluateDoc :: AuthoringDocument -> IO Evaluation
evaluateDoc doc = require (compileAnalysis doc "analysis:cheating" >>= evaluateAnalysis)
includedNodes :: Projection -> ProjectionView -> [ProjectionNode]
includedNodes projection view = [n | n <- projectionNodes (projectionData projection), elem (projectedNodeId n) (viewIncludedNodes view)]
require :: Show a => Either a b -> IO b
require = either (fail . show) pure
check :: String -> Bool -> IO ()
check label condition = unless condition (fail ("case/application view: " <> label))
