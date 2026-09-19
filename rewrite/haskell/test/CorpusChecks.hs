{-# LANGUAGE OverloadedStrings #-}
module CorpusChecks (runCorpusChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.List (sort)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Directory (listDirectory)
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Corpus
import Yuho.CoreYuho.TypedFinite (evaluateTypedFinite)
import Yuho.Diagram.Encode (encodeSemanticGraph, encodeSvg)
import Yuho.Diagram.Types (SemanticGraph)
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (decodeJson, lookupField, textValue)
import Yuho.Surface.Case
  ( caseModelFile, checkAnalysisCase, compileAnalysisCase, explainAnalysisCase
  , runAnalysisCase )
import Yuho.Surface.Compile (checkParsed, compileParsed)
import Yuho.Surface.Explain (explainChecked)
import Yuho.Surface.Modules (AuthoredModel(..), loadAuthoredModel)
import Yuho.Surface.Parser (parseAnalysisCase)
import Yuho.Surface.Token (Diagnostic(..))
import Yuho.Surface.TypedFinite (encodeTypedFiniteRequest, loadTypedFiniteProgram)

runCorpusChecks :: FilePath -> IO ()
runCorpusChecks root = do
  coverageChecks root
  scenarioChecks root
  caseChecks root
  showcaseChecks root
  refusalChecks root
  putStrLn "Singapore corpus v0.3: coverage, 129 scenarios, 4 cases and refusals passed"

coverageChecks :: FilePath -> IO ()
coverageChecks root = do
  (coverage,_) <- loadCoverage root >>= rightText "coverage load"
  validateCoverage root coverage >>= rightText "coverage validation"
  check "complete saved Penal Code inventory" (length (coverageProvisions coverage) == 524)
  check "coverage summary is derived from the inventory"
    (summaryProvisions (coverageSummary coverage) == length (coverageProvisions coverage))
  check "coverage registers no negative scenario fixture"
    (all (\row -> all (\path -> not (any (`Text.isInfixOf` Text.pack path) negativeNames))
      (provisionScenarios row)) (coverageProvisions coverage))
  graph <- either (const (failed "coverage graph")) pure
    (coverageGraph Nothing Nothing Nothing coverage)
  let first = encodeSemanticGraph graph
  check "complete coverage graph is deterministic" (first == encodeSemanticGraph graph)
  check "complete coverage graph is valid JSON"
    (either (const False) (const True) (decodeJson first))
  expectedInventory <- BS.readFile (root </> "research/singapore/corpus-v0.3/graphs/penal-code-inventory.json")
  check "retained complete inventory graph" (first == expectedInventory)
  retainedSvg root "category-public-order.svg"
    (coverageGraph (Just "public-order") Nothing Nothing coverage)
  retainedSvg root "category-documents-records-and-identity.svg"
    (coverageGraph (Just "documents-records-and-identity") Nothing Nothing coverage)
  retainedSvg root "chapter-8-public-tranquillity.svg"
    (coverageGraph Nothing (Just "chapter-8-public-tranquillity") Nothing coverage)
  retainedSvg root "chapter-18-documents-and-records.svg"
    (coverageGraph Nothing (Just "chapter-18-documents-and-records") Nothing coverage)
  where
    negativeNames = ["missing_section334","missing_post2022","missing_section323a",
      "derived_assignment","unreachable_assignment","missing_reachable"]

scenarioChecks :: FilePath -> IO ()
scenarioChecks root = do
  let base = root </> "research/singapore/corpus-v0.3"
      modelPath = base </> "modular-singapore-criminal-law-corpus-v0.3.yh"
      scenariosRoot = base </> "scenarios"
  modelSource <- BS.readFile modelPath
  authored <- loadAuthoredModel modelPath modelSource >>= right "corpus host"
  families <- sort <$> listDirectory scenariosRoot
  paths <- fmap concat $ mapM (scenarioPaths scenariosRoot) families
  check "15 new offence-family scenario matrices" (length families == 15)
  check "120 generated decision-covering scenarios" (length paths == 120)
  forM_ families $ \family -> do
    let scenarioPath = scenariosRoot </> family </> "01_satisfied_primary.yh"
    scenario <- BS.readFile scenarioPath
    let missing = Encoding.encodeUtf8 . Text.unlines . dropFirstAssignment . Text.lines $
          Encoding.decodeUtf8 scenario
    case checkParsed modelPath (authoredModel authored) (Just (scenarioPath,missing)) of
      Left issue -> check ("missing primitive classification is refused for " <> family
        <> " with " <> Text.unpack (diagnosticCode issue)) (diagnosticCode issue == "SFE042")
      Right _ -> failed ("missing primitive classification accepted for " <> family)
  forM_ paths $ \scenarioPath -> do
    scenario <- BS.readFile scenarioPath
    checked <- either (const (failed ("check " <> scenarioPath))) pure
      (checkParsed modelPath (authoredModel authored) (Just (scenarioPath,scenario)))
    first <- either (const (failed ("compile " <> scenarioPath))) pure
      (compileParsed modelPath (authoredModel authored) (Just (scenarioPath,scenario)))
    second <- either (const (failed "deterministic corpus compile")) pure
      (compileParsed modelPath (authoredModel authored) (Just (scenarioPath,scenario)))
    check "corpus compile is deterministic" (first == second)
    check "corpus request executes to a technical status"
      (status (runLine first) `elem` map Just ["satisfied","not_satisfied","unresolved"])
    explanation <- either (const (failed "corpus explanation")) pure
      (explainChecked modelPath checked)
    check "corpus explanation retains the no-outcome boundary"
      ("No guilt, conviction, acquittal or sentence was determined."
        `Text.isInfixOf` explanation)
  where
    scenarioPaths directory family = do
      names <- sort <$> listDirectory (directory </> family)
      pure [directory </> family </> name | name <- names, ".yh" `Text.isSuffixOf` Text.pack name]
    dropFirstAssignment rows = case break (Text.isPrefixOf "  f:") rows of
      (before,_:after) -> before ++ after
      _ -> rows

retainedSvg :: FilePath -> FilePath -> Either Text.Text SemanticGraph -> IO ()
retainedSvg root name selected = do
  selectedGraph <- either (const (failed ("retained graph " <> name))) pure selected
  expected <- BS.readFile (root </> "research/singapore/corpus-v0.3/graphs" </> name)
  check ("retained deterministic SVG " <> name) (encodeSvg selectedGraph == expected)

caseChecks :: FilePath -> IO ()
caseChecks root = forM_ names $ \name -> do
  let path = root </> "research/singapore/corpus-v0.3" </> name
  source <- BS.readFile path
  declaration <- either (const (failed "v0.3 case parse")) pure (parseAnalysisCase path source)
  modelPath <- either (const (failed "v0.3 case model")) pure (caseModelFile path declaration)
  modelSource <- BS.readFile modelPath
  authored <- loadAuthoredModel modelPath modelSource >>= right "v0.3 case host"
  checked <- either (const (failed "v0.3 case check")) pure
    (checkAnalysisCase path declaration modelPath (authoredModel authored))
  first <- either (const (failed "v0.3 case compile")) pure (compileAnalysisCase checked)
  check "v0.3 case compile is deterministic" (compileAnalysisCase checked == Right first)
  _ <- either (const (failed "v0.3 case run")) pure (runAnalysisCase checked)
  explanation <- either (const (failed "v0.3 case explain")) pure
    (explainAnalysisCase modelPath checked)
  check "v0.3 case has no aggregate judicial status"
    ("no aggregate case status" `Text.isInfixOf` explanation)
  where
    names = ["case-public-order-and-justice.yh","case-person-harm-v03.yh",
      "case-documents-and-intimidation.yh","case-actor-exception-isolation-v03.yh"]

showcaseChecks :: FilePath -> IO ()
showcaseChecks root = forM_ showcases $ \(modelName,scenarioNames) ->
  forM_ scenarioNames $ \scenarioName -> do
    let base = root </> "research/singapore/corpus-v0.3/showcases"
        modelPath = base </> modelName
        scenarioPath = base </> scenarioName
    model <- BS.readFile modelPath
    scenario <- BS.readFile scenarioPath
    program <- loadTypedFiniteProgram modelPath model (Just (scenarioPath,scenario))
      >>= right "typed corpus showcase"
    _ <- either (const (failed "typed corpus showcase evaluation")) pure
      (evaluateTypedFinite program)
    let request = encodeTypedFiniteRequest "singapore-corpus-v0.3-showcase" program
        second = encodeTypedFiniteRequest "singapore-corpus-v0.3-showcase" program
    check "typed corpus showcase compilation is deterministic" (request == second)
    check "typed corpus showcase runs"
      (status (runLine request) == Just "evaluated")
  where
    showcases =
      [("typed-section83-age.yh",map ("typed-section83-age-" <>) statuses)
      ,("typed-unlawful-assembly-cardinality.yh",map ("typed-unlawful-assembly-" <>) statuses)
      ,("typed-property-and-fine.yh",map ("typed-property-and-fine-" <>) statuses)]
    statuses = ["satisfied.yh","not-satisfied.yh","unresolved.yh"]

refusalChecks :: FilePath -> IO ()
refusalChecks root = do
  let path = root </> "research/singapore/corpus-v0.3/modules/obstruction-of-justice.yh"
  source <- BS.readFile path
  let invalid = Encoding.encodeUtf8
        (Text.replace "sections 204A" "sections 204a" (Encoding.decodeUtf8 source))
  parsed <- loadAuthoredModel path invalid
  let result = parsed >>= \authored -> checkParsed path (authoredModel authored) Nothing
  check "lowercase statutory suffix is rejected with the stable section diagnostic" $ case result of
    Left issue -> diagnosticCode issue == "SFE031"
    Right _ -> False

status :: BS.ByteString -> Maybe Text.Text
status bytes = either (const Nothing) (\value -> lookupField "status" value >>= textValue)
  (decodeJson bytes)

right :: String -> Either Diagnostic a -> IO a
right label value = case value of
  Left _ -> failed label
  Right item -> pure item

rightText :: String -> Either Text.Text a -> IO a
rightText label value = case value of
  Left _ -> failed label
  Right item -> pure item

check :: String -> Bool -> IO ()
check label value = unless value (failed label)

failed :: String -> IO a
failed label = putStrLn ("corpus checks failed: " <> label) >> exitFailure
