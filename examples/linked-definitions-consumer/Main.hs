{-# LANGUAGE OverloadedStrings #-}
module Main (main) where

import Control.Monad (forM_, unless)
import Data.Aeson (ToJSON, object, (.=))
import qualified Data.ByteString as BS
import Data.List (find)
import Data.Text (Text)
import System.Directory (createDirectoryIfMissing)
import System.Environment (getArgs)
import System.FilePath ((</>))
import LinkedExample
import Yuho.Authoring

require :: Show e => Either e a -> IO a
require = either (fail . show) pure

check :: String -> Bool -> IO ()
check label value = unless value (fail label)

save :: ToJSON a => FilePath -> String -> a -> IO ()
save out name = BS.writeFile (out </> name) . encodeRecord

run :: FilePath -> String -> AuthoringDocument -> Text -> IO Evaluation
run out name doc analysis = do
  let validation = validateAnalysis doc analysis
  check "analysis not ready" (analysisReady validation)
  save out (name <> ".validation.json") validation
  compiled <- require (compileAnalysis doc analysis)
  evaluated <- require (evaluateAnalysis compiled)
  projection <- require (projectEvaluation evaluated)
  save out (name <> ".report.json") (evaluationReport evaluated)
  save out (name <> ".snapshot.json") (evaluationSnapshot evaluated)
  save out (name <> ".mappings.json") (compiledRequirements compiled)
  BS.writeFile (out </> name <> ".request.json") (compiledRequest compiled)
  require (encodeProjection projection) >>= BS.writeFile (out </> name <> ".projection.json")
  view <- require (lawOccurrenceView projection)
  export out (name <> "-law") projection view
  pure evaluated

export :: FilePath -> String -> Projection -> ProjectionView -> IO ()
export out name projection view = do
  check "invalid view" (null (validateProjectionView projection view))
  save out (name <> ".bindings.json") view
  require (encodeProjection projection) >>= BS.writeFile (out </> name <> ".projection.json")
  require (encodeViewJson projection view) >>= BS.writeFile (out </> name <> ".view.json")
  require (encodeViewXml projection view) >>= BS.writeFile (out </> name <> ".xml")
  require (encodeViewSvg projection view) >>= BS.writeFile (out </> name <> ".svg")

rejection :: FilePath -> String -> Either [AuthoringDiagnostic] a -> IO ()
rejection out name value = case value of
  Left errors | not (null errors) -> save out name errors
  _ -> fail ("expected refusal: " <> name)

main :: IO ()
main = do
  args <- getArgs
  out <- case args of { [path] -> pure path; _ -> fail "usage: yuho-linked-definitions NEW_OUTPUT_DIRECTORY" }
  createDirectoryIfMissing True out
  original <- require linkedDocument
  check "document structurally valid" (null (validateDocument original))
  BS.writeFile (out </> "baseline.document.json") (encodeDocument original)
  BS.writeFile (out </> "independent-flat.document.json") (encodeDocument (flatDocument Proved NotProved Proved NotProved))
  reloaded <- require (decodeDocument (encodeDocument original))
  check "exact document round trip" (reloaded == original)
  a <- run out "baseline-A" reloaded "analysis:A"
  b <- run out "baseline-B" reloaded "analysis:B"
  check "independent contexts" (reportConclusion (evaluationReport a) == "satisfied"
    && reportConclusion (evaluationReport b) == "unresolved")
  forM_ [("A",a),("B",b)] $ \(label,evaluation) -> do
    projection <- require (projectEvaluation evaluation)
    definition <- require (inspectDefinition projection definitionKey)
    check "one definition and two explicit uses" (length (sharedUses definition) == 2
      && length (sharedReferencingRules definition) == 2)
    save out ("definition-" <> label <> ".json") definition
    detail <- require (focusRequirement projection (AuthoredRequirement gain))
    let handle = projectedNodeId (explanationOccurrence detail)
    links <- require (inspectDefinitionOccurrence projection handle)
    save out ("occurrence-" <> label <> ".json") links
    view <- require (definitionOccurrenceView projection handle)
    export out ("occurrence-" <> label) projection view
    case nodeSources (sharedDefinition definition) of
      ref:_ -> require (recoverOriginalSource projection ref) >>= save out ("source-" <> label <> ".json")
      _ -> fail "definition source missing"
  projection <- require (projectEvaluation a)
  require (definitionView projection definitionKey) >>= export out "one-definition-two-uses" projection
  revised <- require (revisedDefinition reloaded)
  BS.writeFile (out </> "hypothetical-revision.document.json") (encodeDocument revised)
  ra <- run out "revision-A" revised "analysis:A"
  rb <- run out "revision-B" revised "analysis:B"
  forM_ [("A",ra),("B",rb)] $ \(label,evaluation) -> do
    p <- require (projectEvaluation evaluation)
    require (inspectDefinition p definitionKey) >>= save out ("definition-revision-" <> label <> ".json")
  check "both uses compiled revised shared meaning" (all ((== "not_satisfied") . reportConclusion . evaluationReport) [ra,rb])
  rejection out "stale-attachment.json" (projectEvaluationOn revised a)
  rejection out "incompatible-law-revision.json" (compareAnalyses a ra)
  check "original retained" (snapshotDocument (evaluationSnapshot a) == original)
  let actorChanged = setInput scopeA gain NotProved original
  ca <- run out "actor-A-change" actorChanged "analysis:A"
  cb <- run out "actor-B-unchanged" actorChanged "analysis:B"
  check "no actor leakage" (reportConclusion (evaluationReport ca) == "not_satisfied"
    && reportConclusion (evaluationReport cb) == reportConclusion (evaluationReport b))
  require (projectComparison a ca) >>= save out "actor-A.comparison.json"
  let missing = original {documentAnalyses=[if analysisId x == "analysis:A" then x
        {analysisAssessments=filter (/= "actor:A:f:intends-wrongful-gain") (analysisAssessments x)} else x
        | x <- documentAnalyses original]}
      wrongScope = original {documentAnalyses=[if analysisId x == "analysis:B" then x
        {analysisAssessments="actor:A:f:intends-wrongful-gain" : filter (/= "actor:B:f:intends-wrongful-gain") (analysisAssessments x)} else x
        | x <- documentAnalyses original]}
  BS.writeFile (out </> "missing.document.json") (encodeDocument missing)
  BS.writeFile (out </> "wrong-scope.document.json") (encodeDocument wrongScope)
  save out "missing.validation.json" (validateAnalysis missing "analysis:A")
  save out "wrong-scope.validation.json" (validateAnalysis wrongScope "analysis:B")
  rejection out "missing.compile-refusal.json" (compileAnalysis missing "analysis:A")
  rejection out "wrong-scope.compile-refusal.json" (compileAnalysis wrongScope "analysis:B")
  let summary = object ["baselineA" .= reportConclusion (evaluationReport a),
        "baselineB" .= reportConclusion (evaluationReport b),
        "revisedA" .= reportConclusion (evaluationReport ra),"revisedB" .= reportConclusion (evaluationReport rb),
        "oneActorChanged" .= reportConclusion (evaluationReport ca),"otherActorUnchanged" .= reportConclusion (evaluationReport cb),
        "definitionCount" .= length (filter ((== "definition") . nodeKind) (lawNodes (documentLaw original))),
        "firstLeafMapping" .= find ((== gain) . mappedNode) (evaluationMappings a)]
  save out "summary.json" summary
  BS.putStr (encodeRecord summary)
