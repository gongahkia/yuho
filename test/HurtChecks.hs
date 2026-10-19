{-# LANGUAGE OverloadedStrings #-}
module HurtChecks (runHurtChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.List (find, sort)
import Data.Maybe (isNothing)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import System.FilePath ((</>))
import Cheating (cheatingDocument)
import Hurt
import Yuho.Authoring
import qualified Yuho.Surface.Token as Surface
import Yuho.Exception.Types (ExceptionTrace(..), RawGraph(..))
import Yuho.Protocol.Json (decodeJson)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProof)
import qualified Yuho.SuppliedProofStatus.Types as Proof
import Yuho.Surface.Compile (compileSource)

runHurtChecks :: FilePath -> IO ()
runHurtChecks root = do
  parity root
  workflows
  putStrLn "hurt SDK: six independent legacy translations, scope boundaries, comparisons, provenance and views passed"

run :: AuthoringDocument -> IO Evaluation
run doc = require (compileAnalysis doc hurtAnalysis >>= evaluateAnalysis)

scenario :: String -> IO AuthoringDocument
scenario name = do
  anchor <- require hurtNoteAnchor
  maybe (fail ("missing scenario " <> name)) pure (lookup name (hurtScenarios anchor))

-- Expectations are handwritten from the retained scenarios. The legacy path
-- independently parses, checks and lowers its own .yh source before evaluation.
expected :: [(String,Text,Text,Text,Maybe Text)]
expected =
  [("01_intention_no_exception","satisfied","satisfied","satisfied",Just "not_satisfied"),
   ("02_knowledge_no_exception","satisfied","satisfied","satisfied",Just "not_satisfied"),
   ("03_hurt_not_proved","not_satisfied","requirements_not_satisfied","not_satisfied",Nothing),
   ("05_offence_causation_unresolved","unresolved","requirements_unresolved","unresolved",Nothing),
   ("06_nature_route","not_satisfied","defeated","satisfied",Just "satisfied"),
   ("11_section84_unresolved","unresolved","exception_unresolved","satisfied",Just "unresolved")]

parity :: FilePath -> IO ()
parity root = do
  let base = root </> "research/singapore/section-84-pilot/hurt-offence"
      modelPath = base </> "section323-with-section84.yh"
  model <- BS.readFile modelPath
  forM_ expected $ \(name,conclusion,reason,ordinary,guard) -> do
    let scenarioPath = base </> "scenarios" </> name <> ".yh"
    bytes <- BS.readFile scenarioPath
    legacyBytes <- require (compileSource modelPath model (Just (scenarioPath,bytes)))
    value <- require (decodeJson legacyBytes)
    decoded <- require (decodeProofRequest value)
    validated <- require (validateProofRequest decoded)
    legacy <- require (evaluateProof validated)
    doc <- scenario name
    adapted <- run doc
    let report = evaluationReport adapted
        traces = concatMap Proof.proofRuleTrace (Proof.proofResultRules legacy)
    check (name <> " independent overall expectation and parity")
      (Proof.satisfactionText (Proof.proofResultStatus legacy) == conclusion && reportConclusion report == conclusion)
    check (name <> " exact requirement coverage")
      (sort (map observationNode (reportRequirements report)) == sort (map fst requirementMap))
    forM_ requirementMap $ \(authored,legacyId) -> do
      row <- requireMaybe "SDK requirement" (find ((== authored) . observationNode) (reportRequirements report))
      let old = find ((== legacyId) . Proof.proofTraceId) traces
      check (name <> " input/group status and execution " <> Text.unpack authored)
        (observationComputed row == (Proof.satisfactionText . Proof.proofTraceStatus <$> old)
          && observationEvaluation row == if isNothing old then "not_evaluated" else "evaluated")
      check (name <> " skipped requirement reason " <> Text.unpack authored)
        (observationSkipReason row == if isNothing old
          then Just ("exception guard skipped because main branch: " <> reason) else Nothing)
    forM_ [("o:voluntary-hurt","r:section323-candidate"),("x:section84","r:section84")] $ \(authored,legacyId) -> do
      row <- requireMaybe "SDK rule" (find ((== authored) . ruleAuthoredId) (reportRules report))
      let old = find ((== legacyId) . Proof.proofRuleId) (Proof.proofResultRules legacy)
      check (name <> " rule/branch result " <> Text.unpack authored)
        (ruleComputed row == (Proof.satisfactionText . Proof.proofRuleStatus <$> old)
          && ruleEvaluation row == if isNothing old then "not_evaluated" else "evaluated")
      check (name <> " independent branch reasons")
        (fmap (:[]) (ruleBranchReason row) == (map (reasonName . Proof.proofBranchReason) . Proof.proofRuleBranches <$> old))
    ordinaryRow <- requireMaybe "ordinary group" (find ((== "g:voluntary-hurt") . observationNode) (reportRequirements report))
    mainRule <- requireMaybe "main rule" (find ((== "o:voluntary-hurt") . ruleAuthoredId) (reportRules report))
    check (name <> " ordinary and branch expectation")
      (observationComputed ordinaryRow == Just ordinary && ruleBranchReason mainRule == Just reason)
    let oldGuards = [g | r <- Proof.proofResultRules legacy, Proof.proofRuleId r == "r:section323-candidate",
          b <- Proof.proofRuleBranches r, g <- Proof.proofBranchGuards b]
    check (name <> " attachment status, execution, firing and reason") (case (oldGuards,reportExceptions report) of
      ([],[g]) -> guard == Nothing && exceptionEvaluation g == "not_evaluated"
        && exceptionComputed g == Nothing && exceptionFired g == Nothing
        && exceptionSkipReason g == Just ("exception guard skipped because main branch: " <> reason)
      ([old],[g]) -> exceptionComputed g == guard
        && guard == Just (Proof.satisfactionText (exceptionTraceGuardStatus old))
        && exceptionEvaluation g == "evaluated" && exceptionFired g == Just (exceptionTraceFired old)
        && exceptionFired g == fmap (== "satisfied") guard && exceptionSkipReason g == Nothing
      _ -> False)
    -- Both paths explicitly retain the unresolved supplied reason, not just its
    -- truth projection; decoding happens before either evaluator invocation.
    let sdkStatuses = [(mappedNode m,classificationStatus . assessmentClassification <$> assmt)
          | m <- evaluationMappings adapted,
            let assmt = mappedAssessment m >>= \key -> find ((== key) . assessmentId) (documentAssessments doc),
            mappedAssessment m /= Nothing]
    check (name <> " all thirteen explicitly bound inputs") (length sdkStatuses == 13)
    forM_ sdkStatuses $ \(authored,supplied) -> do
      oldId <- requireMaybe "explicit input mapping" (lookup authored requirementMap)
      check (name <> " supplied classification and unresolved reason " <> Text.unpack authored)
        (supplied == (Proof.suppliedStatus <$> Map.lookup oldId (rawFacts (Proof.proofRawGraph decoded))))
    putStrLn ("hurt parity " <> name <> ": legacy=SDK " <> Text.unpack conclusion
      <> "; branch=" <> Text.unpack reason <> "; guard=" <> maybe "skipped" Text.unpack guard)
  forM_ ["12_missing_section334","13_missing_post2022","15_missing_section323a"] $ \name -> do
    let path = base </> "scenarios" </> name <> ".yh"
    bytes <- BS.readFile path
    check (name <> " legacy requires explicit scope acknowledgements")
      (case compileSource modelPath model (Just (path,bytes)) of
        Left d -> Surface.diagnosticCode d == "SFE022"; Right _ -> False)

-- The authored identifiers intentionally correspond, but generated request,
-- branch, assignment and span identities do not. This is an explicit semantic
-- mapping independent of both translators, not a digest/label comparison.
requirementMap :: [(Text,Text)]
requirementMap = [(key,key) | key <-
  ["f:act-performed","f:hurt-caused","f:hurt-caused-by-act","f:intention-to-cause-hurt","f:knowledge-hurt-likely",
   "g:section321-fault","g:voluntary-hurt","f:unsoundness-time","f:nature-causation","f:nature-incapacity",
   "f:wrong-causation","f:ordinary-wrongfulness-incapacity","f:contrary-law-incapacity","f:control-causation",
   "f:control-incapacity","g:nature","g:wrongfulness","g:control","g:section84-routes","g:section84-requirements"]]

reasonName :: Proof.ProofReason -> Text
reasonName reason = case reason of
  Proof.ProofSatisfied -> "satisfied"
  Proof.ProofRequirementsNotSatisfied -> "requirements_not_satisfied"
  Proof.ProofRequirementsUnresolved -> "requirements_unresolved"
  Proof.ProofDefeated -> "defeated"
  Proof.ProofExceptionUnresolved -> "exception_unresolved"

workflows :: IO ()
workflows = do
  anchor <- require hurtNoteAnchor
  let document = hurtDocument anchor
      draftDocument = hurtDraft anchor
      scenarios = hurtScenarios anchor
  forM_ scenarios $ \(_,doc) -> check "complete authored round-trip" (decodeDocument (encodeDocument doc) == Right doc)
  draft <- require (projectAuthored draftDocument hurtAnalysis)
  before <- require (caseView draft)
  check "draft missing bindings remain visible without computation"
    (length (projectionOpenInputs (projectionData draft)) == 13
      && all (isNothing . projectedNodeComputed) (projectionNodes (projectionData draft))
      && case compileAnalysis draftDocument hurtAnalysis of
        Left diagnostics -> length (filter ((== "AMISSING") . diagnosticCode) diagnostics) == 13
        Right _ -> False)
  links <- require (caseAssertionLinks draft "assertion:weather")
  check "unmapped assertion and draft included"
    (null (linkedAssessments links) && objectProjectionId "assertion:weather" `elem` viewIncludedNodes before
      && objectProjectionId "annotation:hurt-draft" `elem` viewIncludedNodes before)
  intention <- run document
  knowledge <- scenario "02_knowledge_no_exception" >>= run
  pending <- scenario "05_offence_causation_unresolved" >>= run
  guard <- scenario "11_section84_unresolved" >>= run
  routes <- require (compareAnalyses intention knowledge)
  check "changed intention/knowledge routes, same conclusion"
    (not (comparisonConclusionChanged routes) && length (comparisonAssessments routes) == 2
      && sort (map changeObject (comparisonChanged routes)) == ["f:intention-to-cause-hurt","f:knowledge-hurt-likely"])
  uncertainty <- require (projectComparison pending guard)
  check "same unresolved conclusion retains different execution and reasons"
    (not (projectedConclusionChanged uncertainty)
      && any observationEvaluationChanged (projectedChangedObservations uncertainty)
      && any observationBranchReasonChanged (projectedChangedObservations uncertainty))
  p <- require (projectEvaluation pending)
  detail <- require (inspectAssessment p (hurtAssessmentId "f:hurt-caused-by-act" (Unresolved NotDetermined)))
  alt <- require (inspectAssessment p (hurtAssessmentId "f:hurt-caused-by-act" Proved))
  skipped <- require (inspectAssessment p (hurtAssessmentId "f:unsoundness-time" NotProved))
  check "selected unresolved, multiple assertions and cross-context provenance"
    (inspectionSelected detail && length (resolvedAssertions (inspectionResolution detail)) == 3
      && any ((== Scope "actor:mei" "context:synthetic-clinic-note") . assertionScope)
        (resolvedAssertions (inspectionResolution detail))
      && all ((== Just "unresolved") . applicationComputed) (inspectionApplications detail))
  check "proved alternative stays unselected without run attribution"
    (not (inspectionSelected alt) && assessmentClassification (inspectionAssessment alt) == Classification Proved
      && all (\a -> not (applicationSelected a) && applicationComputed a == Nothing && applicationObservation a == Nothing)
        (inspectionApplications alt))
  check "selected guard is not necessarily evaluated"
    (inspectionSelected skipped && all (\a -> applicationEvaluation a == "not_evaluated"
      && isNothing (applicationComputed a) && applicationSkipReason a /= Nothing) (inspectionApplications skipped))
  note <- require (recoverOriginalSource p anchor)
  locator <- require (recoverOriginalSource p (SourceRef "source:hurt-law" Nothing))
  check "UTF-8 original excerpt and locator-only law reference"
    (excerptText note == Just "Mei reports pain (痛) in her arm after the push."
      && excerptState locator == "locator_only" && excerptText locator == Nothing)
  focus <- require (applicationView p (FocusInput "f:hurt-caused-by-act"))
  check "focus bindings valid, descriptive chronology not executable"
    (null (validateProjectionView p focus) && not (null (viewOmittedNodes focus))
      && any (\e -> projectedEdgeKind e == "chronology" && projectedEdgeSemantics e == "descriptive")
        (projectionEdges (projectionData p)))
  let revised = document {documentAssertions=[a {assertionDescription=assertionDescription a <> " Revised narrative."}
        | a <- documentAssertions document]}
  check "stale snapshot rejected" (case projectEvaluationOn revised intention of
    Left diagnostics -> any ((== "PSTALE") . diagnosticCode) diagnostics; Right _ -> False)
  revisedRun <- run revised
  metadata <- require (compareAnalyses intention revisedRun)
  check "narrative revision does not change classifications or computation"
    (null (comparisonChanged metadata) && any changeReferencedMaterial (comparisonAssessments metadata)
      && not (any changeClassification (comparisonAssessments metadata)))
  cheating <- require (compileAnalysis cheatingDocument "analysis:cheating" >>= evaluateAnalysis)
  check "incompatible cross-model comparison rejected" (case compareAnalyses intention cheating of
    Left diagnostics -> any ((== "AINCOMPATIBLE") . diagnosticCode) diagnostics; Right _ -> False)
  cheatingP <- require (projectEvaluation cheating)
  hurtGuard <- require (inspectAssessment p (hurtAssessmentId "f:unsoundness-time" NotProved))
  cheatingGuard <- require (inspectAssessment cheatingP "assessment:unsoundness-time")
  check "repeated section84 input names resolve within their snapshot"
    (assessmentInput (inspectionAssessment hurtGuard) == assessmentInput (inspectionAssessment cheatingGuard)
      && assessmentScope (inspectionAssessment hurtGuard) == hurtScope
      && inspectionSnapshot hurtGuard /= inspectionSnapshot cheatingGuard
      && map applicationOccurrence (inspectionApplications hurtGuard) /= map applicationOccurrence (inspectionApplications cheatingGuard))
  -- Deliberate boundary: retained context is not a typed SDK policy. Identity /
  -- references are checked, but omission of this annotation is not SFE022 here.
  let noAcknowledgements = document {documentAnnotations=filter
        (not . Text.isPrefixOf "a:" . annotationId) (documentAnnotations document)}
  check "scope annotations retained, not silently executable SDK policy"
    (length (filter (Text.isPrefixOf "a:" . annotationId) (documentAnnotations document)) == 3
      && analysisReady (validateAnalysis noAcknowledgements hurtAnalysis))

require :: Show a => Either a b -> IO b
require = either (fail . show) pure

requireMaybe :: String -> Maybe a -> IO a
requireMaybe label = maybe (fail label) pure

check :: String -> Bool -> IO ()
check label value = unless value (fail ("hurt SDK: " <> label))
