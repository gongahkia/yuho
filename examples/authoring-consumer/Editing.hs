{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Editing
  ( EditingStages(..), editingStages, cheatingEditingExample
  , acknowledgementExamples, runEditingConsumer ) where

import Control.Monad (forM, unless)
import Data.Aeson (ToJSON)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import GHC.Generics (Generic)
import System.Directory (createDirectoryIfMissing)
import System.FilePath ((</>))
import Acknowledgements
import Cheating
import Hurt
import Yuho.Authoring

data EditingStages = EditingStages
  { labelRevision :: AuthoringDocument, hypotheticalRevision :: AuthoringDocument
  , invalidIntermediate :: AuthoringDocument, repairedRevision :: AuthoringDocument
  , narrativeRevision :: AuthoringDocument, alternativeAdded :: AuthoringDocument
  , alternativeSelected :: AuthoringDocument, incompleteSelection :: AuthoringDocument }

editingStages :: Either [AuthoringDiagnostic] EditingStages
editingStages = do
  anchor <- hurtNoteAnchor
  let document = hurtDocument anchor
  labelled <- editLawNode "f:act-performed"
    (\n -> n {nodeLabel="Doing an act — revised display label"}) document
  grouped <- editLawNode "g:section321-fault" (\n -> n {nodeKind="all",
    nodeLabel="SDK experiment: intention AND knowledge"}) labelled
  headed <- editLawNode "o:voluntary-hurt" (\n -> n {nodeLabel="SDK EXPERIMENT: hypothetical hurt structure"}) grouped
  let experiment = headed {documentLaw=(documentLaw headed)
        {lawRevision="sdk-experiment-any-to-all-v1",lawScope=lawScope (documentLaw headed) ++
          ["Hypothetical SDK editing exercise only: both intention and knowledge required. Not an interpretation of the retained hurt model."]}}
      edge = "edge:g:section321-fault/f:knowledge-hurt-likely"
  -- Return an invalid candidate without deleting or cascading any references.
  disconnected <- editLawEdge edge (\e -> e {edgeTo="draft:disconnected-knowledge"}) experiment
  repaired <- editLawEdge edge (\e -> e {edgeTo="f:knowledge-hurt-likely"}) disconnected
  narrative <- editCaseAssertion "assertion:pain"
    (\a -> a {assertionDescription=assertionDescription a <> " Revised narrative: the account was recorded later."}) document
  let alternative = Assessment "assessment:hurt:causation-review-v2" "f:hurt-caused-by-act" hurtScope
        (Classification (Unresolved NotDetermined))
        "Explicit caller review after the narrative edit: causation classification remains not determined. References are provenance, not evidence aggregation."
        "editing-demo-caller" "synthetic_fixture" "case_material"
        ["assertion:push","assertion:pain","assertion:account"] [anchor]
      added = narrative {documentAssessments=documentAssessments narrative ++ [alternative]}
  -- An append is a straightforward record update; existing validation checks
  -- new ID conflicts and references. No separate insert wrapper is needed.
  case validateDocument added of [] -> pure (); errors -> Left errors
  selected <- selectAssessment hurtAnalysis (assessmentId alternative) added
  let missing = selected {documentAnalyses=[a {analysisAssessments=
        filter (/= assessmentId alternative) (analysisAssessments a)} | a <- documentAnalyses selected]}
  pure (EditingStages labelled experiment disconnected repaired narrative added selected missing)

-- The same four general helpers on the retained cheating example. Its ordinary
-- default consumer workflow remains unchanged.
cheatingEditingExample :: Either [AuthoringDiagnostic] AuthoringDocument
cheatingEditingExample = do
  labelled <- editLawNode "f:deception" (\n -> n {nodeLabel="Deceiving a person — edited display label"}) cheatingDocument
  disconnected <- editLawEdge "edge:cheating-root" (\e -> e {edgeTo="draft:disconnected-cheating"}) labelled
  repaired <- editLawEdge "edge:cheating-root" (\e -> e {edgeTo="g:cheating-requirements"}) disconnected
  narrative <- editCaseAssertion "assertion:description"
    (\a -> a {assertionDescription=assertionDescription a <> " Revised account."}) repaired
  selectAssessment "analysis:cheating" "assessment:property-fault-pending" narrative

-- Every tuple calls the full checked operation independently. No acceptance
-- token is carried from the successful example to another input.
acknowledgementExamples :: AcknowledgementPolicy -> Acknowledgements
                        -> [(String,AcknowledgementPolicy,Acknowledgements,Text)]
acknowledgementExamples policy supplied =
  [("success",policy,supplied,hurtAnalysis)] ++
  [("missing-" <> show i,policy,supplied {acknowledgedAssumptions=filter (/= key) (acknowledgedAssumptions supplied)},hurtAnalysis)
    | (i,key) <- zip [1 :: Int ..] hurtRequiredAssumptions] ++
  [("unknown",policy,supplied {acknowledgedAssumptions=acknowledgedAssumptions supplied ++ ["a:unknown"]},hurtAnalysis),
   ("duplicate",policy,supplied {acknowledgedAssumptions=acknowledgedAssumptions supplied ++ ["a:outside-section-334"]},hurtAnalysis),
   ("wrong-policy-model",policy {policyContext=(policyContext policy) {acknowledgementLaw="law:other"}},supplied,hurtAnalysis),
   ("wrong-ack-analysis",policy,supplied {acknowledgedContext=(acknowledgedContext supplied)
      {acknowledgementAnalysis="analysis:other"}},hurtAnalysis),
   ("unknown-analysis",policy,supplied,"analysis:missing")]

data SessionRow = SessionRow
  { stage :: Text, snapshot :: Maybe Text, conclusion :: Maybe Text
  , faultComputed :: Maybe Text, ordinaryComputed :: Maybe Text
  , guardEvaluation :: Maybe Text, guardSkipReason :: Maybe Text
  , diagnostics :: [AuthoringDiagnostic] }
  deriving (Show, Generic)
instance ToJSON SessionRow

runEditingConsumer :: [String] -> IO ()
runEditingConsumer args = do
  anchor <- require hurtNoteAnchor
  let document = hurtDocument anchor
  directory <- case args of
    ["--artifacts",path] -> pure (Just path)
    [] -> pure Nothing
    _ -> fail "usage: yuho-authoring-consumer --edit-demo [--artifacts DIRECTORY]"
  stages <- require editingStages
  context <- require (acknowledgementContext document hurtAnalysis)
  let policy = AcknowledgementPolicy context hurtRequiredAssumptions
      acknowledged = Acknowledgements context hurtExampleAcknowledgements
  (baseline,receipt) <- require (evaluateAcknowledged policy acknowledged document hurtAnalysis)
  labelled <- run (labelRevision stages)
  hypothetical <- run (hypotheticalRevision stages)
  let invalid = invalidIntermediate stages
      invalidReport = validateAnalysis invalid hurtAnalysis
  invalidErrors <- rejected (compileAnalysis invalid hurtAnalysis)
  invalidProjection <- rejected (projectAuthored invalid hurtAnalysis)
  unless (not (analysisReady invalidReport) && repairedRevision stages == hypotheticalRevision stages)
    (fail "invalid stage accepted or repair changed unrelated content")
  reloaded <- require (decodeDocument (encodeDocument (repairedRevision stages)))
  unless (reloaded == repairedRevision stages && analysisReady (validateAnalysis reloaded hurtAnalysis))
    (fail "repair round-trip or validation failed")
  repaired <- run reloaded
  narrative <- run (narrativeRevision stages)
  added <- run (alternativeAdded stages)
  selected <- run (alternativeSelected stages)
  labelComparison <- rejected (compareAnalyses baseline labelled)
  structuralComparison <- rejected (compareAnalyses baseline hypothetical)
  staleLabel <- rejected (projectEvaluationOn (labelRevision stages) baseline)
  staleNarrative <- rejected (projectEvaluationOn (narrativeRevision stages) baseline)
  originalProjection <- require (projectEvaluation baseline)
  unless (snapshotDocument (evaluationSnapshot baseline) == document)
    (fail "earlier immutable snapshot changed")
  narrativeComparison <- require (projectComparison baseline narrative)
  additionComparison <- require (projectComparison narrative added)
  selectionComparison <- require (projectComparison added selected)
  authoredMissing <- require (projectAuthored (incompleteSelection stages) hurtAnalysis)
  missingErrors <- rejected (compileAnalysis (incompleteSelection stages) hurtAnalysis)
  beforeView <- require (caseView authoredMissing)
  selectedProjection <- require (projectEvaluation selected)
  focused <- require (applicationView selectedProjection (FocusAssessments
    ["assessment:hurt:causation-review-v2",hurtAssessmentId "f:hurt-caused-by-act" Proved]))
  narrativeProjection <- require (projectEvaluation narrative)
  narrativeView <- require (caseView narrativeProjection)
  inspection <- require (inspectAssessment selectedProjection "assessment:hurt:causation-review-v2")
  skipped <- require (inspectAssessment selectedProjection (hurtAssessmentId "f:unsoundness-time" NotProved))
  retained <- require (inspectAssessment selectedProjection (hurtAssessmentId "f:hurt-caused-by-act" Proved))
  rendered <- concat <$> sequence
    [lawFiles "hurt-baseline" originalProjection,
     require (projectEvaluation labelled) >>= lawFiles "hurt-label-revision",
     require (projectEvaluation hypothetical) >>= lawFiles "hurt-SDK-EXPERIMENT-all",
     viewFiles "hurt-selection-application" selectedProjection focused,
     viewFiles "hurt-narrative-case" narrativeProjection narrativeView,
     viewFiles "hurt-missing-case" authoredMissing beforeView]
  ackRecords <- concat <$> forM (acknowledgementExamples policy acknowledged) (\(name,p,a,key) -> do
    let result = evaluateAcknowledged p a document key
        prefix = "data/ack-" <> name
        inputs = encodeRecord (p,a,key)
    case result of
      Left failure -> pure [(prefix <> ".inputs.json",inputs),(prefix <> ".rejected.json",encodeRecord failure)]
      Right (evaluated,report) -> pure [(prefix <> ".inputs.json",inputs),(prefix <> ".accepted.json",encodeRecord report),
        (prefix <> ".application.json",encodeRecord (evaluationReport evaluated))])
  cheating <- require cheatingEditingExample
  cheatingResult <- require (compileAnalysis cheating "analysis:cheating" >>= evaluateAnalysis)
  let rows = map (uncurry row)
        [("baseline",baseline),("label_revision",labelled),("SDK_EXPERIMENT_any_to_all",hypothetical)] ++
        [SessionRow "invalid_disconnected_edge" Nothing Nothing Nothing Nothing Nothing Nothing invalidErrors] ++
        map (uncurry row) [("repair_round_trip",repaired),("narrative_revision",narrative),
          ("alternative_added_unselected",added),("alternative_explicitly_selected",selected)]
      runs = [("hurt-baseline",document,baseline),("hurt-label-revision",labelRevision stages,labelled),
        ("hurt-SDK-EXPERIMENT-all",hypotheticalRevision stages,hypothetical),
        ("hurt-repaired",reloaded,repaired),("hurt-narrative",narrativeRevision stages,narrative),
        ("hurt-alternative-added",alternativeAdded stages,added),("hurt-alternative-selected",alternativeSelected stages,selected)]
      records = concatMap runFiles runs ++ rendered ++ ackRecords ++
        [("INDEX.md",Encoding.encodeUtf8 index),
         ("data/editing-session.json",encodeRecord rows),
         ("data/hurt-invalid.document.json",encodeDocument invalid),
         ("data/hurt-invalid.validation.json",encodeRecord invalidReport),
         ("data/hurt-invalid.compile-diagnostics.json",encodeRecord invalidErrors),
         ("data/hurt-invalid.projection-diagnostics.json",encodeRecord invalidProjection),
         ("data/hurt-missing.document.json",encodeDocument (incompleteSelection stages)),
         ("data/hurt-missing.compile-diagnostics.json",encodeRecord missingErrors),
         ("data/label-comparison-rejected.json",encodeRecord labelComparison),
         ("data/structural-comparison-rejected.json",encodeRecord structuralComparison),
         ("data/label-stale-rejected.json",encodeRecord staleLabel),
         ("data/narrative-stale-rejected.json",encodeRecord staleNarrative),
         ("data/narrative.comparison.json",encodeRecord narrativeComparison),
         ("data/addition.comparison.json",encodeRecord additionComparison),
         ("data/selection.comparison.json",encodeRecord selectionComparison),
         ("data/selected.inspection.json",encodeRecord inspection),
         ("data/retained.inspection.json",encodeRecord retained),
         ("data/skipped.inspection.json",encodeRecord skipped),
         ("data/baseline-acknowledgements.json",encodeRecord receipt),
         ("data/cheating-edited.document.json",encodeDocument cheating),
         ("data/cheating-edited.application.json",encodeRecord (evaluationReport cheatingResult))]
  case directory of
    Nothing -> pure ()
    Just path -> do
      createDirectoryIfMissing True (path </> "data")
      mapM_ (\(name,bytes) -> BS.writeFile (path </> name) bytes) records
  BS.putStr (encodeRecord rows) >> BS.putStr "\n"
  where
    run doc = require (compileAnalysis doc hurtAnalysis >>= evaluateAnalysis)

row :: Text -> Evaluation -> SessionRow
row label evaluated = SessionRow label (Just (reportSnapshot report)) (Just (reportConclusion report))
  (computed "g:section321-fault") (computed "g:voluntary-hurt")
  (exceptionEvaluation <$> guard) (guard >>= exceptionSkipReason) []
  where
    report = evaluationReport evaluated
    computed key = case filter ((== key) . observationNode) (reportRequirements report) of
      [o] -> observationComputed o
      _ -> Nothing
    guard = case reportExceptions report of [x] -> Just x; _ -> Nothing

runFiles :: (String,AuthoringDocument,Evaluation) -> [(FilePath,BS.ByteString)]
runFiles (name,doc,result) =
  [("data/" <> name <> ".document.json",encodeDocument doc),
   ("data/" <> name <> ".validation.json",encodeRecord (validateAnalysis doc hurtAnalysis)),
   ("data/" <> name <> ".application.json",encodeRecord (evaluationReport result)),
   ("data/" <> name <> ".request.json",compiledRequest (evaluationCompilation result)),
   ("data/" <> name <> ".result.json",evaluationKernelResponse result)]

lawFiles :: String -> Projection -> IO [(FilePath,BS.ByteString)]
lawFiles name projection = do
  view <- require (lawOccurrenceView projection)
  complete <- require (encodeProjection projection)
  json <- require (encodeProjectionLegacyJson projection)
  xml <- require (encodeProjectionLegacyXml projection)
  svg <- require (encodeProjectionSvg projection)
  pure [(name <> ".svg",svg),("data/" <> name <> ".projection.json",complete),
    ("data/" <> name <> ".view-bindings.json",encodeRecord view),
    ("data/" <> name <> ".view.json",json),("data/" <> name <> ".view.xml",xml)]

viewFiles :: String -> Projection -> ProjectionView -> IO [(FilePath,BS.ByteString)]
viewFiles name projection view = do
  svg <- require (encodeViewSvg projection view)
  other <- dataFiles name projection view
  pure ((name <> ".svg",svg):other)

dataFiles :: String -> Projection -> ProjectionView -> IO [(FilePath,BS.ByteString)]
dataFiles name projection view = do
  complete <- require (encodeProjection projection)
  json <- require (encodeViewJson projection view)
  xml <- require (encodeViewXml projection view)
  pure [("data/" <> name <> ".projection.json",complete),
    ("data/" <> name <> ".view-bindings.json",encodeRecord view),
    ("data/" <> name <> ".view.json",json),("data/" <> name <> ".view.xml",xml)]

index :: Text
index = Text.unlines
  ["# Tranche 05: editing through the public SDK", "",
   "Synthetic fixture classifications only. The ANY-to-ALL copy is an SDK experiment, not a legal interpretation.",
   "", "- hurt-baseline.svg / .png: unchanged intention scenario; satisfied, exception evaluated and not satisfied.",
   "- hurt-label-revision.svg / .png: same authored input ID, new label/snapshot/law fingerprint, same computation.",
   "- hurt-SDK-EXPERIMENT-all.svg / .png: explicitly hypothetical revision; both fault inputs required, ordinary requirements fail and guard is skipped.",
   "- hurt-narrative-case.svg / .png: revised assertion text with unchanged selections/classifications.",
   "- hurt-selection-application.svg / .png: newly added assessment explicitly selected as unresolved; retained proved assessment remains unselected.",
   "- hurt-missing-case.svg / .png: missing binding, authored-only; no computation invented.",
   "", "data/ retains baseline, revised, invalid and repaired documents; evaluations and immutable snapshots in projections;",
   "view bindings with explicit omissions; invalid compile/projection diagnostics; stale/incompatible attachment diagnostics;",
   "compatible narrative/addition/selection comparisons; assessment inspections; and cheating edits using the same helpers.",
   "editing-session.json records each stage. Invalid drafts have no evaluation or projected result.",
   "ack-*.inputs.json and accepted/rejected examples keep caller acknowledgements separate from legal statuses.",
   "The checked operation enforces the explicit caller requirement set against the current model/analysis every time.",
   "The hypothetical law revision uses bare SDK evaluation; the original hurt acknowledgement policy does not admit that revision.",
   "No retained .yh fixture, evaluator semantics or public serialization format is changed."]

require :: Show a => Either a b -> IO b
require = either (fail . show) pure

rejected :: Either [AuthoringDiagnostic] a -> IO [AuthoringDiagnostic]
rejected = either pure (const (fail "operation unexpectedly accepted"))
