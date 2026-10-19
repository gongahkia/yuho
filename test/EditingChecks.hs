{-# LANGUAGE OverloadedStrings #-}
module EditingChecks (runEditingChecks) where

import Control.Monad (forM_, unless)
import Data.List (find)
import Data.Text (Text)
import qualified Data.Text as Text
import Acknowledgements
import Cheating
import Editing
import Hurt
import Yuho.Authoring

runEditingChecks :: IO ()
runEditingChecks = do
  addressing
  session
  acknowledgements
  putStrLn "editing SDK: ID-safe candidates, both examples, structural repair, immutable snapshots, explicit selection and caller acknowledgement boundary passed"

addressing :: IO ()
addressing = do
  anchor <- require hurtNoteAnchor
  let document = hurtDocument anchor
      draftDocument = hurtDraft anchor
  let doc = document
      noChange = editLawNode "f:act-performed" id doc
  check "no-op preserves full document" (noChange == Right doc)
  refusal "unknown ID" "ENOTFOUND" "missing" (editLawNode "missing" id doc)
  refusal "wrong kind edge" "ETYPE" "f:act-performed" (editLawEdge "f:act-performed" id doc)
  refusal "wrong kind assertion" "ETYPE" "source:hurt-law" (editCaseAssertion "source:hurt-law" id doc)
  refusal "rename refused" "EIDENTITY" "f:act-performed"
    (editLawNode "f:act-performed" (\n -> n {nodeId="f:hurt-caused"}) doc)
  let duplicate = doc {documentAnnotations=Annotation "f:act-performed" [] "collision" "draft":documentAnnotations doc}
  refusal "cross-collection duplicate ID" "EDUPLICATE" "f:act-performed"
    (editLawNode "f:act-performed" id duplicate)
  let duplicateAssessment = doc {documentAssessments=documentAssessments doc ++ take 1 (documentAssessments doc)}
  check "new assessment identity conflict diagnosed" (any ((== "ADUPLICATE") . diagnosticCode) (validateDocument duplicateAssessment))
  let chosen = hurtAssessmentId "f:hurt-caused-by-act" Proved
  check "selecting the current binding is idempotent" (selectAssessment hurtAnalysis chosen doc == Right doc)
  refusal "unknown analysis" "ENOTFOUND" "missing" (selectAssessment "missing" chosen doc)
  refusal "wrong assessment kind" "ETYPE" "source:hurt-law" (selectAssessment hurtAnalysis "source:hurt-law" doc)
  let wrongScope = doc {documentAssessments=[if assessmentId a == chosen
        then a {assessmentScope=Scope "actor:other" "context:other"} else a | a <- documentAssessments doc]}
  refusal "wrong scope" "ESCOPE" chosen (selectAssessment hurtAnalysis chosen wrongScope)
  let wrongTarget = doc {documentAssessments=[if assessmentId a == chosen
        then a {assessmentInput="g:voluntary-hurt"} else a | a <- documentAssessments doc]}
  refusal "wrong input kind" "ETARGET" chosen (selectAssessment hurtAnalysis chosen wrongTarget)
  let outside = doc {documentLaw=(documentLaw doc) {lawNodes=LawNode "f:outside" "input" "unrelated draft" Nothing Nothing []:
          lawNodes (documentLaw doc)},
        documentAssessments=[if assessmentId a == chosen then a {assessmentInput="f:outside"} else a | a <- documentAssessments doc]}
  refusal "outside selected slice" "ETARGET" chosen (selectAssessment hurtAnalysis chosen outside)
  let ambiguous = doc {documentAnalyses=[a {analysisAssessments=analysisAssessments a ++
        [hurtAssessmentId "f:hurt-caused-by-act" NotProved]} | a <- documentAnalyses doc]}
  refusal "ambiguous old binding" "EAMBIGUOUS" chosen (selectAssessment hurtAnalysis chosen ambiguous)
  let dangling = doc {documentAnalyses=[a {analysisAssessments="assessment:absent":analysisAssessments a}
        | a <- documentAnalyses doc]}
  refusal "dangling old selection not silently discarded" "ENOTFOUND" "assessment:absent"
    (selectAssessment hurtAnalysis chosen dangling)
  partial <- require (selectAssessment hurtAnalysis chosen draftDocument)
  check "selection works on incomplete binding drafts"
    (length (openInputs (validateAnalysis partial hurtAnalysis)) == 12)
  let deleted = doc {documentLaw=(documentLaw doc)
        {lawNodes=filter ((/= "f:act-performed") . nodeId) (lawNodes (documentLaw doc))}}
  check "manual deletion does not cascade or hide references"
    (documentAssessments deleted == documentAssessments doc
      && any (\d -> diagnosticCode d == "ATARGET" && chosenAct `elem` diagnosticObjects d) (validateDocument deleted)
      && any (\d -> diagnosticCode d == "AREFERENCE" && "f:act-performed" `elem` diagnosticObjects d) (validateDocument deleted))
  where chosenAct = hurtAssessmentId "f:act-performed" Proved

session :: IO ()
session = do
  anchor <- require hurtNoteAnchor
  let document = hurtDocument anchor
  stages <- require editingStages
  baseline <- run document
  labelled <- run (labelRevision stages)
  hypothetical <- run (hypotheticalRevision stages)
  check "label change keeps ID, classification and semantics"
    (map nodeId (lawNodes (documentLaw (labelRevision stages))) == map nodeId (lawNodes (documentLaw document))
      && observations baseline == observations labelled
      && documentAssessments (labelRevision stages) == documentAssessments document)
  refusal "label law fingerprint comparison conservative" "AINCOMPATIBLE" hurtAnalysis (compareAnalyses baseline labelled)
  refusal "old evaluation cannot annotate label revision" "PSTALE" (documentId document) (projectEvaluationOn (labelRevision stages) baseline)
  old <- require (projectEvaluation baseline)
  new <- require (projectEvaluation labelled)
  check "old evaluation retained; authored ID stable but occurrence fingerprint changes"
    (snapshotDocument (evaluationSnapshot baseline) == document
      && snapshotId (evaluationSnapshot baseline) /= snapshotId (evaluationSnapshot labelled)
      && occurrences old /= occurrences new)
  let report = evaluationReport hypothetical
  check "hypothetical ALL has expected computed behaviour"
    (computed "g:section321-fault" report == Just "not_satisfied"
      && computed "g:voluntary-hurt" report == Just "not_satisfied" && reportConclusion report == "not_satisfied"
      && all (\e -> exceptionEvaluation e == "not_evaluated" && exceptionComputed e == Nothing
         && exceptionSkipReason e == Just "exception guard skipped because main branch: requirements_not_satisfied") (reportExceptions report))
  let invalid = invalidIntermediate stages
      errors = validationDiagnostics (validateAnalysis invalid hurtAnalysis)
  check "invalid edge diagnostics name relationship and dangling endpoint"
    (any (\d -> diagnosticCode d == "AREFERENCE" && "edge:g:section321-fault/f:knowledge-hurt-likely" `elem` diagnosticObjects d
      && "draft:disconnected-knowledge" `elem` diagnosticObjects d) errors)
  refusal "invalid draft cannot compile" "AREFERENCE" "draft:disconnected-knowledge" (compileAnalysis invalid hurtAnalysis)
  refusal "invalid draft cannot project as evaluated" "AREFERENCE" "draft:disconnected-knowledge" (projectAuthored invalid hurtAnalysis)
  roundTripped <- require (decodeDocument (encodeDocument (repairedRevision stages)))
  repaired <- run roundTripped
  check "repair exactly restores preceding revision and round-trips all authorship"
    (repairedRevision stages == hypotheticalRevision stages && roundTripped == hypotheticalRevision stages
      && evaluationKernelResponse repaired == evaluationKernelResponse hypothetical)
  forM_ [labelRevision stages,hypotheticalRevision stages,invalid,repairedRevision stages] $ \doc ->
    check "law edits preserve case, sources, alternatives, annotations and presentation"
      (documentSources doc == documentSources document && documentAssertions doc == documentAssertions document
        && documentAssessments doc == documentAssessments document && documentAnalyses doc == documentAnalyses document
        && documentAnnotations doc == documentAnnotations document && documentRelationships doc == documentRelationships document
        && documentPresentation doc == documentPresentation document)
  narrative <- run (narrativeRevision stages)
  added <- run (alternativeAdded stages)
  selected <- run (alternativeSelected stages)
  narrativeDiff <- require (compareAnalyses baseline narrative)
  addedDiff <- require (compareAnalyses narrative added)
  selectedDiff <- require (compareAnalyses added selected)
  check "narrative changes are independent from classifications/selection"
    (documentAssessments (narrativeRevision stages) == documentAssessments document
      && documentAnalyses (narrativeRevision stages) == documentAnalyses document
      && null (comparisonChanged narrativeDiff) && any changeReferencedMaterial (comparisonAssessments narrativeDiff))
  check "adding an alternative is not selection"
    (documentAnalyses (alternativeAdded stages) == documentAnalyses document
      && null (comparisonChanged addedDiff) && null (comparisonAssessments addedDiff))
  check "explicit selection changes computation and retains previous assessment"
    (reportConclusion (evaluationReport selected) == "unresolved" && length (comparisonAssessments selectedDiff) == 1
      && comparisonConclusionChanged selectedDiff
      && documentAssessments (alternativeSelected stages) == documentAssessments (alternativeAdded stages))
  p <- require (projectEvaluation selected)
  selectedInfo <- require (inspectAssessment p "assessment:hurt:causation-review-v2")
  retainedInfo <- require (inspectAssessment p (hurtAssessmentId "f:hurt-caused-by-act" Proved))
  skipped <- require (inspectAssessment p (hurtAssessmentId "f:unsoundness-time" NotProved))
  check "selection, uncertainty, cross-context material and skip states stay distinct"
    (inspectionSelected selectedInfo && not (inspectionSelected retainedInfo)
      && all ((== Nothing) . applicationObservation) (inspectionApplications retainedInfo)
      && any ((== Scope "actor:mei" "context:synthetic-clinic-note") . assertionScope)
        (resolvedAssertions (inspectionResolution selectedInfo))
      && all ((== "not_evaluated") . applicationEvaluation) (inspectionApplications skipped))
  missing <- require (projectAuthored (incompleteSelection stages) hurtAnalysis)
  check "missing assessment not silently unresolved"
    (map openState (projectionOpenInputs (projectionData missing)) == ["missing"]
      && all ((== Nothing) . projectedNodeComputed) (projectionNodes (projectionData missing)))
  cheating <- require cheatingEditingExample
  cheated <- require (compileAnalysis cheating "analysis:cheating" >>= evaluateAnalysis)
  check "all four helpers also work for cheating and retain presentation"
    (reportConclusion (evaluationReport cheated) == "unresolved"
      && documentPresentation cheating == documentPresentation cheatingDocument
      && documentSources cheating == documentSources cheatingDocument
      && documentAssessments cheating == documentAssessments cheatingDocument)
  where
    run doc = require (compileAnalysis doc hurtAnalysis >>= evaluateAnalysis)
    observations e = let r = evaluationReport e in
      (reportConclusion r,[(observationNode o,observationComputed o,observationEvaluation o,observationSkipReason o) | o <- reportRequirements r],
       [(ruleAuthoredId o,ruleComputed o,ruleEvaluation o,ruleBranchReason o) | o <- reportRules r],reportExceptions r)
    occurrences p = [projectedNodeId n | n <- projectionNodes (projectionData p), projectedNodeKind n == "occurrence"]
    computed key report = find ((== key) . observationNode) (reportRequirements report) >>= observationComputed

acknowledgements :: IO ()
acknowledgements = do
  anchor <- require hurtNoteAnchor
  let document = hurtDocument anchor
      draftDocument = hurtDraft anchor
      scenarios = hurtScenarios anchor
  context <- require (acknowledgementContext document hurtAnalysis)
  let policy = AcknowledgementPolicy context hurtRequiredAssumptions
      supplied = Acknowledgements context hurtExampleAcknowledgements
  forM_ (acknowledgementExamples policy supplied) $ \(name,p,a,key) ->
    case evaluateAcknowledged p a document key of
      Right (result,receipt) -> check "only explicit complete acknowledgements accepted"
        (name == "success" && checkedSnapshot receipt == snapshotId (evaluationSnapshot result)
          && checkedPolicy receipt == policy && checkedAcknowledgements receipt == supplied)
      Left failure -> do
        let codes = map acknowledgementCode (acknowledgementDiagnostics failure)
            wanted | "missing-" `Text.isPrefixOf` Text.pack name = "ACKMISSING"
                   | name == "unknown" = "ACKUNKNOWN"
                   | name == "duplicate" = "ACKDUPLICATE"
                   | otherwise = "ACKCONTEXT"
        check ("rejected acknowledgement example " <> name) (name /= "success" && wanted `elem` codes && null (authoringDiagnostics failure))
  forM_ scenarios $ \(name,doc) -> do
    bare <- require (compileAnalysis doc hurtAnalysis >>= evaluateAnalysis)
    (checked,receipt) <- require (evaluateAcknowledged policy supplied doc hurtAnalysis)
    check ("admission changes no kernel bytes: " <> name)
      (compiledRequest (evaluationCompilation bare) == compiledRequest (evaluationCompilation checked)
        && evaluationKernelResponse bare == evaluationKernelResponse checked
        && checkedSnapshot receipt == snapshotId (evaluationSnapshot checked))
  let empty = supplied {acknowledgedAssumptions=[]}
  check "new requirement does not automatically become acknowledged"
    (case checkAcknowledgements (policy {requiredAssumptions=hurtRequiredAssumptions ++ ["a:new-requirement"]}) supplied document hurtAnalysis of
      Left ds -> any (\d -> acknowledgementCode d == "ACKMISSING" && "a:new-requirement" `elem` acknowledgementObjects d) ds
      Right _ -> False)
  check "invalid explicit requirement sets rejected"
    (case checkAcknowledgements (policy {requiredAssumptions=hurtRequiredAssumptions ++ hurtRequiredAssumptions}) supplied document hurtAnalysis of
      Left ds -> any ((== "ACKPOLICY") . acknowledgementCode) ds; Right _ -> False)
  check "acknowledgements checked before compilation even for incomplete bindings"
    (case evaluateAcknowledged policy empty draftDocument hurtAnalysis of
      Left failure -> length (acknowledgementDiagnostics failure) == 3 && null (authoringDiagnostics failure)
      _ -> False)
  check "successful admission still delegates missing-binding failure to SDK"
    (case evaluateAcknowledged policy supplied draftDocument hurtAnalysis of
      Left failure -> null (acknowledgementDiagnostics failure)
        && all ((== "AMISSING") . diagnosticCode) (authoringDiagnostics failure)
      _ -> False)
  stages <- require editingStages
  check "earlier policy/acknowledgements do not admit a changed law fingerprint"
    (case evaluateAcknowledged policy supplied (labelRevision stages) hurtAnalysis of
      Left failure -> all ((== "ACKCONTEXT") . acknowledgementCode) (acknowledgementDiagnostics failure)
      _ -> False)
  let stripped = document {documentAnnotations=filter (not . Text.isPrefixOf "a:" . annotationId) (documentAnnotations document)}
  _ <- require (evaluateAcknowledged policy supplied stripped hurtAnalysis)
  check "retained annotations neither provide nor gate explicit acknowledgement"
    (case evaluateAcknowledged policy empty document hurtAnalysis of
      Left failure -> length (acknowledgementDiagnostics failure) == 3; _ -> False)
  -- Acceptance receipts cannot be passed to evaluateAcknowledged. Current
  -- narrative inputs are checked again and the newly computed snapshot differs.
  (before,_) <- require (evaluateAcknowledged policy supplied document hurtAnalysis)
  (after,receipt) <- require (evaluateAcknowledged policy supplied (narrativeRevision stages) hurtAnalysis)
  check "every invocation binds its own exact snapshot"
    (checkedSnapshot receipt == snapshotId (evaluationSnapshot after)
      && checkedSnapshot receipt /= snapshotId (evaluationSnapshot before))

refusal :: String -> Text -> Text -> Either [AuthoringDiagnostic] a -> IO ()
refusal label code object result = check label (case result of
  Left ds -> any (\d -> diagnosticCode d == code && object `elem` diagnosticObjects d) ds
  Right _ -> False)

require :: Show a => Either a b -> IO b
require = either (fail . show) pure

check :: String -> Bool -> IO ()
check label ok = unless ok (fail ("editing: " <> label))
