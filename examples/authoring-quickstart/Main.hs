{-# LANGUAGE OverloadedStrings #-}
-- Built as a separate package outside Yuho. Only public SDK imports.
module Main (main) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import System.Directory (createDirectoryIfMissing)
import System.Environment (getArgs)
import System.FilePath ((</>))
import Yuho.Authoring

main :: IO ()
main = do
  args <- getArgs
  (input,output) <- case args of
    [path,directory] -> pure (path,directory)
    _ -> fail "usage: yuho-sdk-quickstart HURT_DOCUMENT.json OUTPUT_DIRECTORY"
  supplied <- BS.readFile input >>= require . decodeDocument
  -- The documented input is the existing bounded hurt fixture, supplied by
  -- path. This program does not discover research or import consumer modules.
  let analysis = "analysis:hurt"
      scope = Scope "actor:alex" "context:synthetic-yard-incident"
      note = SourceRecord "source:quickstart-note" "synthetic" (Just "explicit quickstart note")
        (Just "Synthetic: Mei reports pain (痛) in her arm after the push.")
  anchor <- require (sourceAnchorCodePoints note 11 58)
  withSource <- require (editCaseAssertion "assertion:pain"
    (\a -> a {assertionSources=assertionSources a ++ [anchor]})
    (supplied {documentSources=documentSources supplied ++ [note]}))
  let assessment = Assessment "assessment:quickstart-causation" "f:hurt-caused-by-act" scope
        (Classification Proved) "Explicit synthetic classification for this example; not derived from the source link."
        "quickstart-caller" "synthetic_fixture" "case_material"
        ["assertion:push","assertion:pain","assertion:account"] [anchor]
      alternative = withSource {documentAssessments=documentAssessments withSource ++ [assessment]}
  document <- require (selectAssessment analysis (assessmentId assessment) alternative)
  ready analysis document
  result <- require (compileAnalysis document analysis >>= evaluateAnalysis)
  projection <- require (projectEvaluation result)
  detail <- require (inspectAssessment projection (assessmentId assessment))
  excerpt <- require (recoverOriginalSource projection anchor)
  view <- require (applicationView projection (FocusAssessments [assessmentId assessment]))
  complete <- require (encodeProjection projection)
  svg <- require (encodeViewSvg projection view)
  json <- require (encodeViewJson projection view)
  xml <- require (encodeViewXml projection view)
  -- A successful edit is only a candidate. Validate and explicitly reevaluate.
  revised <- require (editCaseAssertion "assertion:pain"
    (\a -> a {assertionDescription=assertionDescription a <> " Revised narrative: the account was recorded later."}) document)
  ready analysis revised
  newer <- require (compileAnalysis revised analysis >>= evaluateAnalysis)
  comparison <- require (projectComparison result newer)
  stale <- case projectEvaluationOn revised result of
    Left diagnostics -> pure diagnostics
    Right _ -> fail "old evaluation silently attached to revised document"
  unless (null (projectedChangedObservations comparison)
    && documentAssessments document == documentAssessments revised
    && snapshotDocument (evaluationSnapshot result) == document
    && excerptText excerpt == Just "Mei reports pain (痛) in her arm after the push.")
    (fail "quickstart lifecycle changed its promised distinctions")
  createDirectoryIfMissing True output
  let files = [("authored.document.json",encodeDocument document),
        ("revised.document.json",encodeDocument revised),
        ("application.json",encodeRecord (evaluationReport result)),
        ("revised.application.json",encodeRecord (evaluationReport newer)),
        ("validation.json",encodeRecord (validateAnalysis document analysis)),
        ("application.projection.json",complete),("application.view-bindings.json",encodeRecord view),
        ("application.svg",svg),("application.view.json",json),("application.view.xml",xml),
        ("assessment-inspection.json",encodeRecord detail),("original-excerpt.json",encodeRecord excerpt),
        ("narrative.comparison.json",encodeRecord comparison),("stale-diagnostics.json",encodeRecord stale)]
  mapM_ (\(name,bytes) -> BS.writeFile (output </> name) bytes) files
  -- Actually reload the saved authored revision and evaluate it again.
  reloaded <- BS.readFile (output </> "revised.document.json") >>= require . decodeDocument
  ready analysis reloaded
  replay <- require (compileAnalysis reloaded analysis >>= evaluateAnalysis)
  unless (reloaded == revised && evaluationKernelResponse replay == evaluationKernelResponse newer)
    (fail "saved document did not reproduce the revised evaluation")
  let summary = Map.fromList [("before" :: Text,reportConclusion (evaluationReport result)),
        ("after",reportConclusion (evaluationReport newer)),
        ("oldSnapshot",snapshotId (evaluationSnapshot result)),
        ("newSnapshot",snapshotId (evaluationSnapshot newer)),
        ("excerpt",maybe "" id (excerptText excerpt)),("savedReloaded","true")]
  BS.writeFile (output </> "summary.json") (encodeRecord summary)
  BS.putStr (encodeRecord summary) >> BS.putStr "\n"

ready :: Text -> AuthoringDocument -> IO ()
ready key doc = let report = validateAnalysis doc key in
  unless (analysisReady report) (fail (show (validationDiagnostics report)))

require :: Show a => Either a b -> IO b
require = either (fail . show) pure
