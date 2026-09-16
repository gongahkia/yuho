{-# LANGUAGE OverloadedStrings #-}
module ReleaseChecks (runReleaseChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, lookupField, textValue)
import Yuho.Surface.Case
  ( caseModelFile, checkAnalysisCase, compileAnalysisCase, explainAnalysisCase
  , runAnalysisCase )
import Yuho.Surface.Compile (compileParsed)
import Yuho.Surface.Modules (AuthoredModel(..), loadAuthoredModel)
import Yuho.Surface.Parser (parseAnalysisCase)
import Yuho.Surface.Presumption
  ( PresumptionProgram(..), explainPresumptionProgram, loadPresumptionProgram )
import Yuho.Surface.Temporal (loadAuthoredInput)
import Yuho.Surface.Token (Diagnostic(..))

runReleaseChecks :: FilePath -> IO ()
runReleaseChecks root = do
  corpusChecks root
  caseChecks root
  presumptionChecks root
  crossCuttingChecks root
  putStrLn "research release: independent modules, 56 corpus scenarios, general cases and presumption surface passed"

corpusChecks :: FilePath -> IO ()
corpusChecks root = do
  let base = root </> "research/singapore/research-release"
      standalonePath = base </> "singapore-criminal-law-release.yh"
      modularPath = base </> "modular-singapore-criminal-law-release.yh"
      families = ["rash-endangerment","assault","misappropriation",
        "criminal-breach-of-trust","receiving-property","criminal-trespass",
        "wrongful-restraint"]
      scenarios = [prefix <> suffix <> ".yh" | prefix <- ["01_","02_","03_","04_",
        "05_","06_","07_","08_"], suffix <- case prefix of
          "01_" -> ["satisfied_primary"]
          "02_" -> ["satisfied_alternative"]
          "03_" -> ["conduct_not_proved"]
          "04_" -> ["fault_or_circumstance_not_proved"]
          "05_" -> ["material_unresolved"]
          "06_" -> ["exception_defeats"]
          "07_" -> ["exception_unresolved"]
          _ -> ["exception_defeats_unresolved_offence"]]
  standaloneSource <- BS.readFile standalonePath
  modularSource <- BS.readFile modularPath
  standalone <- loadAuthoredModel standalonePath standaloneSource >>= right "standalone release"
  let duplicate = Encoding.encodeUtf8 (Text.replace
        "  use offence rash::o:rash-endangerment;"
        (Text.unlines ["  use offence rash::o:rash-endangerment;",
          "  use offence rash::o:rash-endangerment;"])
        (Encoding.decodeUtf8 modularSource))
  duplicateResult <- loadAuthoredModel modularPath duplicate
  check "colliding exported legal identities are refused" $ case duplicateResult of
    Left issue -> diagnosticCode issue == "SFM012"
    Right _ -> False
  forM_ families $ \family -> forM_ scenarios $ \name -> do
    let scenarioPath = base </> "scenarios" </> family </> name
    scenario <- BS.readFile scenarioPath
    (modular,supplied) <- loadAuthoredInput modularPath modularSource
      (Just (scenarioPath,scenario)) >>= right "composed release"
    first <- either (const (failed ("compile " <> family <> "/" <> name))) pure
      (compileParsed modularPath (authoredModel modular) supplied)
    second <- either (const (failed "deterministic compile")) pure
      (compileParsed modularPath (authoredModel modular) supplied)
    check "release scenario compilation is deterministic" (first == second)
    check "release scenario runs" (status (runLine first) `elem`
      map Just ["satisfied","not_satisfied","unresolved"])
    if name == "01_satisfied_primary.yh" then do
      let ordinary = compileParsed standalonePath (authoredModel standalone)
            (Just (scenarioPath,scenario))
      check "independent modular graph equals monolithic request" (ordinary == Right first)
      check "independent modular graph equals monolithic response"
        ((runLine <$> ordinary) == Right (runLine first))
    else pure ()

caseChecks :: FilePath -> IO ()
caseChecks root = do
  let cases =
        [root </> "research/singapore/research-release/case-property-deception-showcase.yh"
        ,root </> "research/singapore/research-release/case-person-harm-showcase.yh"
        ,root </> "research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh"]
  forM_ cases $ \path -> do
    source <- BS.readFile path
    declaration <- either (const (failed "case parse")) pure (parseAnalysisCase path source)
    modelPath <- either (const (failed "case model path")) pure (caseModelFile path declaration)
    modelSource <- BS.readFile modelPath
    authored <- loadAuthoredModel modelPath modelSource >>= right "case model load"
    checked <- either (const (failed "general case check")) pure
      (checkAnalysisCase path declaration modelPath (authoredModel authored))
    first <- either (const (failed "case compile")) pure (compileAnalysisCase checked)
    check "case compilation is deterministic" (compileAnalysisCase checked == Right first)
    _ <- either (const (failed "case run")) pure (runAnalysisCase checked)
    explanation <- either (const (failed "case explanation")) pure
      (explainAnalysisCase modelPath checked)
    check "case explanation has no aggregate judicial outcome"
      ("no aggregate case status" `Text.isInfixOf` explanation
        && "No guilt, conviction, acquittal, liability or sentence was determined."
          `Text.isSuffixOf` Text.strip explanation)

presumptionChecks :: FilePath -> IO ()
presumptionChecks root = do
  let base = root </> "rewrite/frontend/fixtures/synthetic"
      rows = [("active","active"),("inactive","inactive"),
        ("rebutted","rebutted"),("unresolved","unresolved")]
  forM_ rows $ \(name,wanted) -> do
    let path = base </> "presumption_" <> name <> ".yh"
    source <- BS.readFile path
    program <- loadPresumptionProgram path source >>= right "presumption program"
    check "presumption request uses registered variant"
      (field "fragment" (presumptionRequest program) == Just "RegisteredPresumptionDerivations-v1")
    check "presumption state is explained" (derivationStates (presumptionResult program) == [wanted])
    explanation <- either (const (failed "presumption explanation")) pure
      (explainPresumptionProgram program)
    check "presumption explanation refuses evidence assessment"
      ("does not assess evidence" `Text.isInfixOf` explanation)
    if name == "active" then do
      let duplicate = Encoding.encodeUtf8 (Text.replace
            "  presumption pres:fictional-authorization target"
            (Text.unlines ["  presumption pres:fictional-authorization target f:no-authorization source src:fictional-rule trigger f:knowledge rebuttal f:rescue-purpose;",
              "  presumption pres:fictional-authorization target"])
            (Encoding.decodeUtf8 source))
      refused <- loadPresumptionProgram path duplicate
      check "duplicate presumption identities are source-located refusals" $ case refused of
        Left issue -> diagnosticCode issue == "SFR003"
        Right _ -> False
    else pure ()

crossCuttingChecks :: FilePath -> IO ()
crossCuttingChecks root = do
  let base = root </> "research/singapore/research-release"
      rows =
        [("attempt-assault.yh","scenario-attempt-assault.yh","satisfied")
        ,("attempt-misappropriation.yh","scenario-attempt-misappropriation.yh","not_satisfied")
        ,("intentional-aid-misappropriation.yh","scenario-intentional-aid-misappropriation.yh","satisfied")]
  forM_ rows $ \(modelName,scenarioName,wanted) -> do
    let modelPath = base </> modelName
        scenarioPath = base </> scenarioName
    modelSource <- BS.readFile modelPath
    scenario <- BS.readFile scenarioPath
    authored <- loadAuthoredModel modelPath modelSource >>= right "cross-cutting model"
    request <- either (const (failed "cross-cutting compile")) pure
      (compileParsed modelPath (authoredModel authored) (Just (scenarioPath,scenario)))
    check "cross-cutting result" (status (runLine request) == Just wanted)

status :: BS.ByteString -> Maybe Text
status = field "status"

field :: Text -> BS.ByteString -> Maybe Text
field key bytes = either (const Nothing) (\value -> lookupField key value >>= textValue)
  (decodeJson bytes)

derivationStates :: BS.ByteString -> [Text]
derivationStates bytes = case decodeJson bytes of
  Right value -> case lookupField "presumption_derivations" value of
    Just (JArr rows) -> [state | row <- rows,
      Just state <- [lookupField "state" row >>= textValue]]
    _ -> []
  Left _ -> []

right :: String -> Either Diagnostic a -> IO a
right label value = case value of
  Left _ -> failed label
  Right item -> pure item

check :: String -> Bool -> IO ()
check label value = unless value (failed label)

failed :: String -> IO a
failed label = putStrLn ("research release failed: " <> label) >> exitFailure
