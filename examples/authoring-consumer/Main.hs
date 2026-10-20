{-# LANGUAGE OverloadedStrings #-}
module Main (main) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import Data.List (find)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import System.Directory (createDirectoryIfMissing)
import System.Environment (getArgs)
import System.FilePath ((</>))
import Cheating
import CaseApplication (runCaseApplicationDemo)
import Hurt (runHurtConsumer)
import Editing (runEditingConsumer)
import SourceAnchors (runSourceAnchorsConsumer)
import InteractionDemo (runInteractionConsumer)
import Yuho.Authoring

main :: IO ()
main = do
  args <- getArgs
  case args of
    "--interact":rest -> runInteractionConsumer rest
    "--anchors-demo":rest -> runSourceAnchorsConsumer rest
    "--edit-demo":rest -> runEditingConsumer rest
    "--model":"hurt":rest -> runHurtConsumer rest
    _ -> runCheatingConsumer args

runCheatingConsumer :: [String] -> IO ()
runCheatingConsumer args = do
  document <- require (decodeDocument (encodeDocument cheatingDocument))
  unless (document == cheatingDocument) (fail "authoring round-trip changed content")
  -- These projections precede compilation and evaluation, including a draft.
  authoredPending <- require (projectAuthored pendingDocument "analysis:cheating")
  let draft = pendingDocument { documentAnalyses = [a { analysisAssessments =
        filter (/= "assessment:property-fault-pending") (analysisAssessments a) }
        | a <- documentAnalyses pendingDocument] }
  authoredDraft <- require (projectAuthored draft "analysis:cheating")
  let validation = validateAnalysis document "analysis:cheating"
  unless (analysisReady validation) (fail (show validation))
  compiled <- require (compileAnalysis document "analysis:cheating")
  original <- require (evaluateAnalysis compiled)
  changed <- require (compileAnalysis pendingDocument "analysis:cheating" >>= evaluateAnalysis)
  comparison <- require (compareAnalyses original changed)
  satisfiedProjection <- require (projectEvaluation original)
  pendingProjection <- require (projectEvaluation changed)
  projectedComparison <- require (projectComparison original changed)
  let defeatedDocument = foldl (\doc input -> withStatus input Proved doc) document
        ["f:unsoundness-time","f:nature-causation","f:nature-incapacity"]
      bothRoutes = foldl (\doc input -> withStatus input Proved doc) document
        ["f:intentional-inducement","f:induced-act-or-omission","f:damage-or-harm"]
  defeated <- require (compileAnalysis defeatedDocument "analysis:cheating" >>= evaluateAnalysis >>= projectEvaluation)
  alternativeBefore <- require (compileAnalysis bothRoutes "analysis:cheating" >>= evaluateAnalysis)
  alternativeAfter <- require (compileAnalysis (withStatus "f:property-fraudulent-or-dishonest" NotProved bothRoutes)
    "analysis:cheating" >>= evaluateAnalysis)
  alternativeComparison <- require (projectComparison alternativeBefore alternativeAfter)
  alternativeBeforeProjection <- require (projectEvaluation alternativeBefore >>= encodeProjection)
  alternativeAfterProjection <- require (projectEvaluation alternativeAfter >>= encodeProjection)
  deception <- maybe (fail "deception occurrence unavailable") pure (find (\n ->
    projectedNodeKind n == "occurrence" && maybe False ((== "f:deception") . occurrenceAuthoredNode)
      (projectedNodeOccurrence n)) (projectionNodes (projectionData satisfiedProjection)))
  recovered <- maybe (fail "projection recovery failed") pure
    (resolveProjectedObject satisfiedProjection (projectedNodeId deception))
  unless (length (resolvedAssertions recovered) == 2 && length (resolvedAssessments recovered) == 1)
    (fail "projection lost assessment or assertion provenance")
  rootContext <- maybe (fail "law context recovery failed") pure
    (resolveProjectedObject satisfiedProjection (objectProjectionId "o:cheating"))
  unless (not (null (resolvedAnnotations rootContext))) (fail "draft annotation not recoverable")
  projectionRecords <- concat <$> mapM (uncurry projectionFiles)
    [("pending-authored",authoredPending),("draft-authored",authoredDraft),
     ("satisfied",satisfiedProjection),("pending",pendingProjection),("defeated",defeated)]
  caseRecords <- runCaseApplicationDemo
  let application = evaluationReport original
      records = [("document.json",encodeDocument document),
        ("pending-document.json",encodeDocument pendingDocument),
        ("validation.json",encodeRecord validation),
        ("application.json",encodeRecord application),
        ("pending-application.json",encodeRecord (evaluationReport changed)),
        ("open-inputs.json",encodeRecord (reportOpenInputs (evaluationReport changed))),
        ("comparison.json",encodeRecord comparison),
        ("request.json",compiledRequest compiled),
        ("result.json",evaluationKernelResponse original),
        ("snapshot.json",encodeRecord (evaluationSnapshot original)),
        ("mappings.json",encodeRecord (compiledRequirements compiled)),
        ("generated-sources.json",encodeRecord (compiledSources compiled)),
        ("source-mappings.json",encodeRecord (compiledSourceMappings compiled)),
        ("comparison-projection.json",encodeRecord projectedComparison),
        ("comparison-excerpt.json",comparisonExcerpt satisfiedProjection pendingProjection projectedComparison),
        ("alternative-route.comparison-projection.json",encodeRecord alternativeComparison),
        ("alternative-before.projection.json",alternativeBeforeProjection),
        ("alternative-after.projection.json",alternativeAfterProjection),
        ("recovered-deception.json",encodeRecord recovered),
        ("recovered-law-context.json",encodeRecord rootContext)] ++ projectionRecords ++ caseRecords
  case args of
    [] -> pure ()
    ["--artifacts",directory] -> do
      createDirectoryIfMissing True directory
      mapM_ (\(name,bytes) -> BS.writeFile (directory </> name) bytes) records
    _ -> fail "usage: yuho-authoring-consumer [--artifacts DIRECTORY]"
  mapM_ (\bytes -> BS.putStr bytes >> BS.putStr "\n")
    [encodeRecord application,encodeRecord comparison]
  where
    require :: Show a => Either a b -> IO b
    require = either (fail . show) pure

-- A small consumer-selected view of the comparison, rather than another
-- comparison contract. Full paths, identities and metadata are in the projection.
comparisonExcerpt :: Projection -> Projection -> ProjectionComparison -> BS.ByteString
comparisonExcerpt old new comparison = encodeRecord
  [Map.fromList
    [("authoredId" :: Text,changeObject row),("kind",changeObservationKind row),
     ("projectedOccurrence",observationChangeAlignment mapped),
     ("oldObservation",observationChangeOldNode mapped),("newObservation",observationChangeNewNode mapped),
     ("oldAssessment",assessment old mapped),("newAssessment",assessment new mapped),
     ("oldSupplied",supplied old mapped),("newSupplied",supplied new mapped),
     ("oldComputed",absent (changeOldComputed row)),("newComputed",absent (changeNewComputed row)),
     ("oldEvaluation",changeOldEvaluation row),("newEvaluation",changeNewEvaluation row),
     ("oldReason",absent (changeOldReason row)),("newReason",absent (changeNewReason row))]
  | mapped <- projectedChangedObservations comparison, let row = observationChange mapped,
    changeObject row `elem` ["f:property-fraudulent-or-dishonest","f:unsoundness-time","o:cheating"]]
  where
    absent = maybe "absent" id
    binding projection row = find ((== observationChangeAlignment row) . projectedNodeId)
      (projectionNodes (projectionData projection)) >>= projectedNodeBinding
    assessment projection row = absent (binding projection row >>= bindingAssessment)
    supplied projection row = maybe "absent" classification (binding projection row >>= bindingSupplied)
    classification :: Classification -> Text
    classification (Classification status) = case status of
      Proved -> "proved"
      NotProved -> "not_proved"
      Unresolved NotDetermined -> "unresolved(not_determined)"
      Unresolved ExternalDecisionPending -> "unresolved(external_decision_pending)"

projectionFiles :: String -> Projection -> IO [(FilePath,BS.ByteString)]
projectionFiles name projection = do
  complete <- require (encodeProjection projection)
  view <- require (lawOccurrenceView projection)
  json <- require (encodeProjectionLegacyJson projection)
  xml <- require (encodeProjectionLegacyXml projection)
  svg <- require (encodeProjectionSvg projection)
  pure [(name <> ".projection.json",complete),(name <> ".view-bindings.json",encodeRecord view),
    (name <> ".view.json",json),(name <> ".view.xml",xml),(name <> ".svg",svg)]
  where
    require :: Show a => Either a b -> IO b
    require = either (fail . show) pure
