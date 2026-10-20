{-# LANGUAGE OverloadedStrings #-}
module InteractionChecks (runInteractionChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.List (find)
import Data.Maybe (isNothing)
import Data.Text (Text)
import System.FilePath ((</>))
import Cheating (cheatingDocument)
import Hurt
import Yuho.Authoring

runInteractionChecks :: FilePath -> IO ()
runInteractionChecks root = do
  anchor <- require hurtNoteAnchor
  pendingDoc <- scenario anchor "05_offence_causation_unresolved"
  original <- evaluate pendingDoc hurtAnalysis
  p <- require (projectEvaluation original)
  let focus = AuthoredRequirement "f:hurt-caused-by-act"
  detail <- require (focusRequirement p focus)
  occurrence <- pure (explanationOccurrence detail)
  selected <- required "selected assessment" (explanationSelected detail)
  check "selected unresolved supplied separately from computed"
    (contextSelected selected && assessmentClassification (contextAssessment selected) == Classification (Unresolved NotDetermined)
      && projectedNodeComputed occurrence == Just "unresolved" && projectedNodeEvaluation occurrence == "evaluated")
  same <- require (focusRequirement p (RequirementOccurrence (projectedNodeId occurrence)))
  check "authored and occurrence focus agree" (same == detail)
  observation <- required "run observation" (explanationObservation detail)
  check "definition, occurrence, assessment and observation identities stay separate"
    (length (unique [explanationDefinitionId detail,projectedNodeId occurrence,
      contextProjectedId selected,projectedNodeId observation]) == 4)
  check "ancestors and authored relationship mapping"
    (map (nodeId . neighbourLaw) (explanationAncestors detail) == ["g:voluntary-hurt","o:voluntary-hurt"]
      && all (not . null . neighbourAuthoredRelationships) (explanationAncestors detail))
  check "all three assertions with cross-context scope retained"
    (length (contextAssertions selected) == 3 && any ((== "actor:mei") . scopeActor . assertionScope) (contextAssertions selected)
      && length (contextAssertionLinks selected) == 3)
  check "alternatives keep classification and receive no computation"
    (length (explanationAlternatives detail) == 2 && all (not . contextSelected) (explanationAlternatives detail)
      && all (\a -> all (\x -> applicationComputed x == Nothing && applicationObservation x == Nothing
          && not (applicationSelected x)) (contextApplications a)) (explanationAlternatives detail))
  forM_ [AuthoredRequirement "unknown",AuthoredRequirement "assertion:push",
         RequirementOccurrence (explanationDefinitionId detail),RequirementOccurrence (projectedNodeId observation)] $ \bad ->
    rejected "IFOCUS" (case bad of {AuthoredRequirement k -> k; RequirementOccurrence k -> k}) (focusRequirement p bad)
  let before = evaluationSnapshot original
  view <- require (explanationView p focus defaultExplanationOptions)
  expanded <- require (explanationView p focus (ExplanationOptions False ["source:hurt-note"]))
  alternatives <- require (explanationView p focus (ExplanationOptions True []))
  forM_ [view,expanded,alternatives] $ \v -> do
    check "view bindings and endpoints" (null (validateProjectionView p v))
    _ <- require (encodeViewJson p v)
    _ <- require (encodeViewXml p v)
    _ <- require (encodeViewSvg p v)
    pure ()
  check "default reading order starts with occurrence and selected assessment"
    (take 2 (viewIncludedNodes view) == [projectedNodeId occurrence,contextProjectedId selected])
  let nodesIn v = filter (\n -> projectedNodeId n `elem` viewIncludedNodes v) (projectionNodes (projectionData p))
  check "source expansion explicit, alternatives opt-in"
    (all ((/= "original_source") . projectedNodeRole) (nodesIn view)
      && length (filter ((== "original_source") . projectedNodeRole) (nodesIn expanded)) == 1
      && length (filter ((== "assessment") . projectedNodeRole) (nodesIn alternatives)) == 3)
  check "alternatives bind to definition, without inheriting the occurrence result"
    (explanationDefinitionId detail `elem` viewIncludedNodes alternatives
      && length [e | e <- projectionEdges (projectionData p), projectedEdgeId e `elem` viewIncludedEdges alternatives,
          projectedEdgeKind e == "assessment_input", projectedEdgeTo e == explanationDefinitionId detail] == 3
      && length [e | e <- projectionEdges (projectionData p), projectedEdgeId e `elem` viewIncludedEdges alternatives,
          projectedEdgeKind e == "selected_assessment", projectedEdgeTo e == projectedNodeId occurrence] == 1)
  check "sources and assertions have no legal status"
    (all (\n -> projectedNodeComputed n == Nothing && projectedNodeEvaluation n == "not_applicable")
      [n | n <- nodesIn expanded, projectedNodeRole n `elem` ["original_source","assertion"]])
  rejected "ISOURCE" "source:hurt-register" (explanationView p focus (ExplanationOptions False ["source:hurt-register"]))
  rejected "ISOURCE" "source:hurt-note" (explanationView p focus (ExplanationOptions False ["source:hurt-note","source:hurt-note"]))
  excerpt <- require (recoverOriginalSource p anchor)
  check "UTF-8 original excerpt" (excerptText excerpt == Just "Mei reports pain (痛) in her arm after the push.")
  locator <- require (recoverOriginalSource p (SourceRef "source:hurt-law" Nothing))
  check "locator-only source stays unanchored" (excerptText locator == Nothing && excerptState locator == "locator_only")
  check "inspection and display leave snapshot/document intact"
    (evaluationSnapshot original == before && snapshotDocument before == pendingDoc)
  guardDetail <- require (focusRequirement p (AuthoredRequirement "f:unsoundness-time"))
  guardAssessment <- required "selected guard" (explanationSelected guardDetail)
  check "selected assumption guard remains skipped"
    (assessmentClassification (contextAssessment guardAssessment) == Classification NotProved
      && assessmentBasis (contextAssessment guardAssessment) == "assumption" && null (contextAssertions guardAssessment)
      && projectedNodeComputed (explanationOccurrence guardDetail) == Nothing
      && projectedNodeEvaluation (explanationOccurrence guardDetail) == "not_evaluated"
      && projectedNodeSkipReason (explanationOccurrence guardDetail) == Just "exception guard skipped because main branch: requirements_unresolved"
      && any ((== "not_evaluated") . exceptionEvaluation) (explanationExceptions detail))
  group <- require (focusRequirement p (AuthoredRequirement "g:voluntary-hurt"))
  check "group dependencies without supplied assessment"
    (isNothing (explanationSelected group) && null (explanationAlternatives group)
      && length (explanationDependencies group) == 4)
  groupSvg <- require (explanationView p (AuthoredRequirement "g:voluntary-hurt") defaultExplanationOptions >>= encodeViewSvg p)
  check "group semantics visibly labelled" ("All required" `BS.isInfixOf` groupSvg)
  anySvg <- require (explanationView p (AuthoredRequirement "g:section321-fault") defaultExplanationOptions >>= encodeViewSvg p)
  check "alternative group meaning visible" ("At least one required" `BS.isInfixOf` anySvg)
  let moreAlternatives = pendingDoc {documentAssessments=documentAssessments pendingDoc ++
        [(contextAssessment selected) {assessmentId="extra-alternative-1"},
         (contextAssessment selected) {assessmentId="extra-alternative-2"}]}
  many <- require (projectAuthored moreAlternatives hurtAnalysis)
  allAlternatives <- require (focusRequirement many focus)
  check "explanation retains alternatives beyond reference-view budget" (length (explanationAlternatives allAlternatives) == 4)
  rejected "PVIEWLIMIT" "extra-alternative-1" (explanationView many focus (ExplanationOptions True []))
  draft <- require (projectAuthored (hurtDraft anchor) hurtAnalysis >>= \x -> focusRequirement x focus)
  check "missing is not unresolved or not evaluated"
    (isNothing (explanationSelected draft) && projectedNodeComputed (explanationOccurrence draft) == Nothing
      && projectedNodeEvaluation (explanationOccurrence draft) == "not_requested"
      && (projectedNodeBinding (explanationOccurrence draft) >>= Just . bindingState) == Just "missing")
  let otherScope = Scope "actor:another" "context:another"
      incompatible = (contextAssessment selected) {assessmentId="assessment:other-scope",assessmentScope=otherScope}
      withOther = pendingDoc {documentAssessments=documentAssessments pendingDoc ++ [incompatible]}
  otherP <- require (projectAuthored withOther hurtAnalysis)
  otherFocus <- require (focusRequirement otherP focus)
  check "retained alternatives limited to analysis scope" (all ((/= "assessment:other-scope") . assessmentId . contextAssessment)
    (explanationAlternatives otherFocus))
  rejected "ESCOPE" "assessment:other-scope" (selectAssessment hurtAnalysis "assessment:other-scope" withOther)
  let foreignDocument = pendingDoc {documentAnalyses=[a {analysisScope=otherScope} | a <- documentAnalyses pendingDoc],
        documentAssessments=[a {assessmentScope=otherScope} | a <- documentAssessments pendingDoc]}
  foreignP <- require (projectAuthored foreignDocument hurtAnalysis)
  rejected "IFOCUS" (projectedNodeId occurrence) (focusRequirement foreignP (RequirementOccurrence (projectedNodeId occurrence)))
  let alternativeId = hurtAssessmentId "f:hurt-caused-by-act" Proved
  revisedDoc <- require (selectAssessment hurtAnalysis alternativeId pendingDoc)
  revised <- evaluate revisedDoc hurtAnalysis
  check "explicit selection creates a new snapshot without replacing original"
    (snapshotId (evaluationSnapshot revised) /= snapshotId before && snapshotDocument before == pendingDoc)
  rejected "PSTALE" (documentId revisedDoc) (projectEvaluationOn revisedDoc original)
  comparison <- require (compareAnalyses original revised)
  aligned <- require (projectComparison original revised)
  check "changed assessment and aligned observations"
    (length (comparisonAssessments comparison) == 1 && not (null (projectedChangedObservations aligned))
      && not (null (projectedUnchangedObservations aligned)) && projectedConclusionChanged aligned)
  intention <- scenario anchor "01_intention_no_exception" >>= (`evaluate` hurtAnalysis)
  knowledge <- scenario anchor "02_knowledge_no_exception" >>= (`evaluate` hurtAnalysis)
  unchanged <- require (projectComparison intention knowledge)
  check "two changed inputs, unchanged satisfied conclusion"
    (not (projectedConclusionChanged unchanged) && projectedNewConclusion unchanged == "satisfied"
      && length (projectedAssessmentChanges unchanged) == 2 && length (projectedChangedObservations unchanged) == 2)
  failed <- scenario anchor "03_hurt_not_proved" >>= (`evaluate` hurtAnalysis) >>= require . projectEvaluation
  notProved <- require (focusRequirement failed (AuthoredRequirement "f:hurt-caused"))
  check "supplied not_proved retains technical evaluated non-satisfaction"
    (fmap (assessmentClassification . contextAssessment) (explanationSelected notProved) == Just (Classification NotProved)
      && projectedNodeComputed (explanationOccurrence notProved) == Just "not_satisfied")
  defeated <- scenario anchor "06_nature_route" >>= (`evaluate` hurtAnalysis) >>= require . projectEvaluation
  defeatedDetail <- require (focusRequirement defeated (AuthoredRequirement "o:voluntary-hurt"))
  defeatedSvg <- require (explanationView defeated (AuthoredRequirement "o:voluntary-hurt") defaultExplanationOptions >>= encodeViewSvg defeated)
  check "evaluated exception defeat and rule reason recoverable"
    (any ((== Just "defeated") . ruleBranchReason) (explanationRules defeatedDetail)
      && any ((== Just True) . exceptionFired) (explanationExceptions defeatedDetail)
      && "Branch reason: defeated" `BS.isInfixOf` defeatedSvg)
  cheating <- evaluate cheatingDocument "analysis:cheating"
  case compareAnalyses original cheating of
    Left _ -> pure ()
    Right _ -> fail "cross-model interaction comparison accepted"
  s441 root
  putStrLn "interaction SDK: focus, provenance, opt-in views, immutable revisions, scope, and both models passed"

s441 :: FilePath -> IO ()
s441 root = do
  doc <- BS.readFile (root </> "examples/authoring-consumer/fixtures/section441.document.json") >>= require . decodeDocument
  p <- evaluate doc "analysis:s441"
  eDoc <- require (selectAssessment "analysis:s441" "position:E" doc)
  e <- evaluate eDoc "analysis:s441"
  nDoc <- require (selectAssessment "analysis:s441" "position:N" doc)
  n <- evaluate nDoc "analysis:s441"
  forM_ [(p,"unresolved"),(e,"satisfied"),(n,"not_satisfied")] $ \(result,status) -> do
    check "s441 independent supplied expectation" (reportConclusion (evaluationReport result) == status)
    check "s441 entry unchanged, remaining varies"
      (computed "route:entry" result == Just "not_satisfied" && computed "route:remaining" result == Just status)
  projection <- require (projectEvaluation p)
  detail <- require (focusRequirement projection (AuthoredRequirement "remain:unlawful"))
  selected <- required "P selected" (explanationSelected detail)
  check "P and retained E/N resolved"
    (assessmentId (contextAssessment selected) == "position:P"
      && map (assessmentId . contextAssessment) (explanationAlternatives detail) == ["position:E","position:N"]
      && map assertionId (contextAssertions selected) == ["case:request","case:arrangement"])
  let requestRefs = concatMap assertionSources [a | a <- contextAssertions selected, assertionId a == "case:request"]
  recovered <- traverse (require . recoverOriginalSource projection) requestRefs
  check "exact original request excerpt" (any ((== Just "At 10:15 I asked Jun to leave.") . excerptText) recovered)
  compared <- require (projectComparison p e)
  check "s441 four changed / sixteen unchanged observations"
    (length (projectedChangedObservations compared) == 4 && length (projectedUnchangedObservations compared) == 16
      && all observationComputedValueChanged (projectedChangedObservations compared)
      && all (not . observationEvaluationChanged) (projectedChangedObservations compared))
  where computed key result = observationComputed =<< find ((== key) . observationNode) (reportRequirements (evaluationReport result))

scenario :: SourceRef -> String -> IO AuthoringDocument
scenario anchor name = required name (lookup name (hurtScenarios anchor))

evaluate :: AuthoringDocument -> Text -> IO Evaluation
evaluate doc key = require (compileAnalysis doc key >>= evaluateAnalysis)

unique :: Eq a => [a] -> [a]
unique [] = []
unique (x:xs) = x : unique (filter (/= x) xs)

check :: String -> Bool -> IO ()
check label = flip unless (fail ("interaction: " <> label))

rejected :: Text -> Text -> Either [AuthoringDiagnostic] a -> IO ()
rejected code object result = case result of
  Left diagnostics -> check ("diagnostic " <> show code)
    (any (\d -> diagnosticCode d == code && object `elem` diagnosticObjects d) diagnostics)
  Right _ -> fail ("expected rejection " <> show code)

required :: String -> Maybe a -> IO a
required label = maybe (fail label) pure

require :: Show e => Either e a -> IO a
require = either (fail . show) pure
