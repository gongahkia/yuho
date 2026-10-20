{-# LANGUAGE OverloadedStrings #-}
-- Headless public-library interactions. Model-specific choices stay here.
module InteractionDemo (runInteractionConsumer) where

import Control.Monad (unless)
import Data.Aeson (Value, ToJSON, object, (.=))
import qualified Data.ByteString as BS
import Data.List (find)
import Data.Maybe (isJust)
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Directory (createDirectoryIfMissing)
import System.FilePath ((</>))
import Acknowledgements
import Hurt
import Yuho.Authoring

runInteractionConsumer :: [String] -> IO ()
runInteractionConsumer args = do
  (path,out) <- case args of
    [documentPath,directory] -> pure (documentPath,directory)
    _ -> fail "usage: yuho-authoring-consumer --interact S441_DOCUMENT.json OUTPUT_DIRECTORY"
  createDirectoryIfMissing True (out </> "data")
  document <- BS.readFile path >>= require . decodeDocument
  original <- evaluateReady document "analysis:s441"
  (revised,_,compared) <- session evaluateReady out "s441" original
    "remain:unlawful" "source:B" "position:E"
  revisedProjection <- require (projectEvaluation revised)
  nDoc <- require (selectAssessment "analysis:s441" "position:N" document)
  n <- evaluateReady nDoc "analysis:s441"
  saveEvaluation out "s441-N" n
  -- Existing law-occurrence output supplies the whole comparison context.
  lawView <- require (lawOccurrenceView revisedProjection)
  export out "s441-P-E-law" revisedProjection lawView True (Just compared)
  anchor <- require hurtNoteAnchor
  pendingDoc <- scenario anchor "05_offence_causation_unresolved"
  pending <- evaluateHurt pendingDoc hurtAnalysis
  (_,pendingProjection,_) <- session evaluateHurt out "hurt" pending
    "f:hurt-caused-by-act" "source:hurt-note" (hurtAssessmentId "f:hurt-caused-by-act" Proved)
  guardView <- require (explanationView pendingProjection (AuthoredRequirement "f:unsoundness-time") defaultExplanationOptions)
  export out "hurt-skipped-guard" pendingProjection guardView False Nothing
  guardDetail <- require (focusRequirement pendingProjection (AuthoredRequirement "f:unsoundness-time"))
  write out "data/hurt-skipped-guard.explanation.json" guardDetail
  intention <- scenario anchor "01_intention_no_exception" >>= (`evaluateHurt` hurtAnalysis)
  knowledge <- scenario anchor "02_knowledge_no_exception" >>= (`evaluateHurt` hurtAnalysis)
  routes <- require (projectComparison intention knowledge)
  saveEvaluation out "hurt-intention" intention
  saveEvaluation out "hurt-knowledge" knowledge
  write out "data/hurt-routes.comparison.json" routes
  let summary = object ["section441" .= map resultSummary [original,revised,n],
        "section441Comparison" .= comparisonSummary compared,
        "hurtPending" .= resultSummary pending,"hurtRoutes" .= comparisonSummary routes]
  write out "summary.json" summary
  BS.writeFile (out </> "INDEX.md") (Encoding.encodeUtf8 artifactIndex)
  BS.putStr (encodeRecord summary) >> BS.putStr "\n"

-- Focus/reveal/display operations use the same immutable projection. Only the
-- explicit selectAssessment step creates a candidate authored revision.
session :: (AuthoringDocument -> Text -> IO Evaluation) -> FilePath -> String -> Evaluation
        -> Text -> Text -> Text -> IO (Evaluation,Projection,ProjectionComparison)
session evaluateDocument out name original input sourceKey alternativeKey = do
  let focus = AuthoredRequirement input
      snapshot = evaluationSnapshot original
      document = snapshotDocument snapshot
      analysisKey = analysisId (snapshotAnalysis snapshot)
  projection <- require (projectEvaluation original)
  explanation <- require (focusRequirement projection focus)
  immediate <- require (explanationView projection focus defaultExplanationOptions)
  export out (name <> "-focus") projection immediate False Nothing
  selected <- maybe (fail "reference interaction requires a selected assessment") pure (explanationSelected explanation)
  reference <- case [ref | ref <- explanationSourceReferences explanation,
      referenceSource ref == sourceKey, isJust (referenceSpan ref)] of
    [ref] -> pure ref
    _ -> fail "requested original source must identify one retained anchor"
  recovered <- require (recoverOriginalSource projection reference)
  -- Only section 441 needs the additional reference diagrams; both model
  -- sessions exercise exactly the same source and alternative operations.
  sources <- require (explanationView projection focus (ExplanationOptions False [sourceKey]))
  alternatives <- require (explanationView projection focus (ExplanationOptions True []))
  if name == "s441" then do
    export out (name <> "-source") projection sources False Nothing
    export out (name <> "-alternatives") projection alternatives False Nothing
    else pure ()
  unless (alternativeKey `elem` map (assessmentId . contextAssessment) (explanationAlternatives explanation))
    (fail "requested selection is not a compatible retained alternative")
  revisedDocument <- require (selectAssessment analysisKey alternativeKey document)
  let validation = validateAnalysis revisedDocument analysisKey
  unless (analysisReady validation) (fail (show validation))
  revised <- evaluateDocument revisedDocument analysisKey
  revisedProjection <- require (projectEvaluation revised)
  -- Stable occurrence alignment is resolved by the SDK, without kernel IDs.
  after <- require (focusRequirement revisedProjection
    (RequirementOccurrence (projectedNodeId (explanationOccurrence explanation))))
  comparison <- require (compareAnalyses original revised)
  mapped <- require (projectComparison original revised)
  revisedView <- require (explanationView revisedProjection focus defaultExplanationOptions)
  if name == "s441" then
    export out (name <> "-revised") revisedProjection (comparisonCaption mapped revisedView) False (Just mapped)
    else pure ()
  stale <- case projectEvaluationOn revisedDocument original of
    Left diagnostics -> pure diagnostics
    Right _ -> fail "old evaluation attached to a revised document"
  write out ("data/" <> name <> ".interaction.json") (object
    ["focusRequest" .= focus,"before" .= explanation,"requestedSource" .= reference,"revealedSource" .= recovered,
     "steps" .= (["focus requirement","inspect selected assessment","reveal requested original source",
       "inspect retained alternatives","explicitly select alternative","validate candidate","compile and evaluate",
       "compare retained runs","map highlights to diagram objects"] :: [Text]),
     "revision" .= object ["operation" .= ("selectAssessment" :: Text),"analysis" .= analysisKey,
       "previousAssessment" .= assessmentId (contextAssessment selected),"selectedAlternative" .= alternativeKey,
       "validation" .= validation,"originalSnapshot" .= snapshotId snapshot,
       "revisedSnapshot" .= snapshotId (evaluationSnapshot revised)],
     "after" .= after,"comparison" .= comparison,"alignedComparison" .= mapped,
     "focusView" .= immediate,"sourceView" .= sources,"alternativesView" .= alternatives,
     "revisedView" .= comparisonCaption mapped revisedView,"staleAttachment" .= stale,
     "highlightBindings" .= map (highlightBinding revisedView) (projectedChangedObservations mapped ++ projectedUnchangedObservations mapped)])
  saveEvaluation out (name <> "-before") original
  saveEvaluation out (name <> "-after") revised
  write out ("data/" <> name <> ".comparison.json") mapped
  pure (revised,projection,mapped)

-- A caller-local presentation overlay, using existing authored alignment and
-- original observation handles. It never changes projection state or semantics.
highlightBinding :: ProjectionView -> ProjectedObservationChange -> Value
highlightBinding view row = object ["authored" .= changeObject (observationChange row),
  "alignment" .= observationChangeAlignment row,"oldObservation" .= observationChangeOldNode row,
  "newObservation" .= observationChangeNewNode row,
  "computedChanged" .= observationComputedFieldChanged row,"evaluationChanged" .= observationEvaluationChanged row,
  "reasonChanged" .= observationReasonChanged row,"branchReasonChanged" .= observationBranchReasonChanged row,
  "includedInView" .= (observationChangeAlignment row `elem` viewIncludedNodes view)]

comparisonCaption :: ProjectionComparison -> ProjectionView -> ProjectionView
comparisonCaption comparison view = view
  { viewId=projectionIdentity "view" (viewId view,comparisonOldProjection comparison,comparisonNewProjection comparison)
  , viewScope="After explicit selection: dashed outlines mark changed observations; plain outlines remain unchanged. "
      <> Text.pack (show (length (projectedChangedObservations comparison))) <> " changed / "
      <> Text.pack (show (length (projectedUnchangedObservations comparison))) <> " unchanged observations; full alignment in data/." }

export :: FilePath -> String -> Projection -> ProjectionView -> Bool -> Maybe ProjectionComparison -> IO ()
export out name projection view law comparison = do
  unless (null (validateProjectionView projection view)) (fail "invalid interaction view")
  complete <- require (encodeProjection projection)
  json <- require (if law then encodeProjectionLegacyJson projection else encodeViewJson projection view)
  xml <- require (if law then encodeProjectionLegacyXml projection else encodeViewXml projection view)
  svg <- require (if law then encodeProjectionSvg projection else encodeViewSvg projection view)
  -- The dedicated law encoder builds its own view; retain that exact companion.
  actualView <- if law then require (lawOccurrenceView projection) else pure view
  BS.writeFile (out </> "data" </> name <> ".projection.json") complete
  write out ("data/" <> name <> ".view-bindings.json") actualView
  BS.writeFile (out </> "data" </> name <> ".view.json") json
  BS.writeFile (out </> "data" </> name <> ".view.xml") xml
  let marked = case comparison of
        Nothing -> svg
        Just changes ->
          let ids = [observationChangeAlignment r | r <- projectedChangedObservations changes]
              css = Text.concat ["#node-" <> key <> " > rect{stroke:#9a3412;stroke-width:3;stroke-dasharray:6 3}" | key <- ids]
              caption = if law then "<text x=\"28\" y=\"130\" font-size=\"12\">Comparison: dashed CARD outlines mark "
                <> Text.pack (show (length (projectedChangedObservations changes))) <> " changed observations; "
                <> Text.pack (show (length (projectedUnchangedObservations changes)))
                <> " plain card outlines remain unchanged. This is supplied-scenario comparison.</text>" else ""
          in Encoding.encodeUtf8 (Text.replace "</svg>" ("<style>" <> css <> "</style>" <> caption <> "</svg>") (Encoding.decodeUtf8 svg))
  BS.writeFile (out </> name <> ".svg") marked
  case comparison of
    Nothing -> pure ()
    Just changes -> write out ("data/" <> name <> ".highlights.json")
      (map (highlightBinding actualView) (projectedChangedObservations changes ++ projectedUnchangedObservations changes))

saveEvaluation :: FilePath -> String -> Evaluation -> IO ()
saveEvaluation out name result = do
  let snapshot = evaluationSnapshot result
  BS.writeFile (out </> "data" </> name <> ".document.json") (encodeDocument (snapshotDocument snapshot))
  write out ("data/" <> name <> ".application-report.json") (evaluationReport result)
  write out ("data/" <> name <> ".snapshot.json") snapshot
  complete <- require (projectEvaluation result >>= encodeProjection)
  BS.writeFile (out </> "data" </> name <> ".projection.json") complete

evaluateReady :: AuthoringDocument -> Text -> IO Evaluation
evaluateReady document key = do
  let validation = validateAnalysis document key
  unless (analysisReady validation) (fail (show validation))
  require (compileAnalysis document key >>= evaluateAnalysis)

evaluateHurt :: AuthoringDocument -> Text -> IO Evaluation
evaluateHurt document key = do
  context <- require (acknowledgementContext document key)
  (result,_) <- require (evaluateAcknowledged (AcknowledgementPolicy context hurtRequiredAssumptions)
    (Acknowledgements context hurtExampleAcknowledgements) document key)
  pure result

scenario :: SourceRef -> String -> IO AuthoringDocument
scenario anchor key = maybe (fail "hurt scenario not found") pure (lookup key (hurtScenarios anchor))

resultSummary :: Evaluation -> Value
resultSummary result = object ["snapshot" .= snapshotId (evaluationSnapshot result),
  "conclusion" .= reportConclusion report,"entry" .= computed "route:entry","remaining" .= computed "route:remaining"]
  where report = evaluationReport result
        computed key = observationComputed =<< find ((== key) . observationNode) (reportRequirements report)

comparisonSummary :: ProjectionComparison -> Value
comparisonSummary comparison = object ["before" .= projectedOldConclusion comparison,
  "after" .= projectedNewConclusion comparison,"conclusionChanged" .= projectedConclusionChanged comparison,
  "assessments" .= length (projectedAssessmentChanges comparison),
  "changed" .= length (projectedChangedObservations comparison),"unchanged" .= length (projectedUnchangedObservations comparison)]

write :: ToJSON a => FilePath -> FilePath -> a -> IO ()
write out name = BS.writeFile (out </> name) . encodeRecord

require :: Show e => Either e a -> IO a
require = either (fail . show) pure

artifactIndex :: Text
artifactIndex = Text.unlines
  ["# Headless diagram interactions", "", "All classifications are supplied; provenance does not determine evidence strength.",
   "s441-focus.svg: P unresolved, requirement/result first, selected assessment second, then request/arrangement assertions.",
   "s441-source.svg: same snapshot with Source B opened explicitly; full stipulation packet remains omitted.",
   "s441-alternatives.svg: same snapshot, retained E and N visible without attributed computation.",
   "s441-revised.svg: explicit E selection, new snapshot, focused computed result satisfied; dashed border marks change.",
   "s441-P-E-law.svg: all aligned law occurrences; dashed borders mark the four changed observations, plain borders the sixteen unchanged.",
   "hurt-focus.svg: ordinary causation unresolved, selected assessment and cross-context case material.",
   "hurt-skipped-guard.svg: selected not_proved assumption; no computed result; main requirements unresolved.",
   "", "data/*.interaction.json records ordered requests, focus responses, source recovery, explicit selection, validation, snapshots,",
   "stale attachment diagnostics and changed/unchanged highlights. data/hurt-routes.comparison.json retains intention/knowledge",
   "variation with an unchanged satisfied conclusion. summary.json includes freshly evaluated P/E/N results.",
   "Every exported view has complete .projection.json, .view-bindings.json and JSON/XML companions under data/.",
   "The section 441 document is an unchanged copy of the independent original-authoring exercise's P document.",
   "Its bounded published-2020-RE s 441 scope, synthetic packet and original reasons remain in the authored snapshots.",
   "Use rsvg-convert --output NAME.png NAME.svg to render previews. No projection operation evaluates or fetches sources."]
