{-# LANGUAGE OverloadedStrings #-}
module LanguageExpansionChecks (runLanguageExpansionChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, lookupField, textValue)
import Yuho.Surface.Compile (checkParsed, compileParsed)
import Yuho.Surface.Explain (explainChecked)
import Yuho.Surface.Modules (AuthoredModel(..), authoredPrefix, loadAuthoredModel)
import Yuho.Surface.Temporal (loadAuthoredInput)
import Yuho.Surface.Token (Diagnostic(..), tokenColumn, tokenLine)

runLanguageExpansionChecks :: FilePath -> IO ()
runLanguageExpansionChecks root = do
  moduleChecks root
  temporalChecks root
  penaltyAndCorpusChecks root
  putStrLn "language expansion: modules, temporal selection, penalties and 20 corpus scenarios passed"

moduleChecks :: FilePath -> IO ()
moduleChecks root = do
  let base = root </> "research/singapore/section-84-pilot/statutory-definitions"
      standalonePath = base </> "section323-section379-definitions.yh"
      theftHost = base </> "modular-theft-with-section84.yh"
      hurtHost = base </> "modular-hurt-with-section84.yh"
      theftScenarioPath = base </> "scenarios/18_theft_satisfied.yh"
      hurtScenarioPath = base </> "scenarios/17_hurt_satisfied.yh"
      cyclePath = base </> "refusal-import-cycle.yh"
  standalone <- BS.readFile standalonePath
  theftSource <- BS.readFile theftHost
  hurtSource <- BS.readFile hurtHost
  theftScenario <- BS.readFile theftScenarioPath
  hurtScenario <- BS.readFile hurtScenarioPath
  forM_ [(theftHost,theftSource,theftScenarioPath,theftScenario),
         (hurtHost,hurtSource,hurtScenarioPath,hurtScenario)] $
    \(hostPath,hostSource,scenarioPath,scenario) -> do
      modular <- loadAuthoredModel hostPath hostSource >>= requireRight "module load"
      standaloneModel <- loadAuthoredModel standalonePath standalone
        >>= requireRight "standalone load"
      let supplied = Just (scenarioPath,scenario)
          modularRequest = compileParsed hostPath (authoredModel modular) supplied
          standaloneRequest = compileParsed standalonePath
            (authoredModel standaloneModel) supplied
      check "modular and standalone request bytes are identical"
        (modularRequest == standaloneRequest)
      check "modular and standalone response bytes are identical"
        ((runLine <$> modularRequest) == (runLine <$> standaloneRequest))
      check "modular compilation is deterministic"
        (modularRequest == compileParsed hostPath (authoredModel modular) supplied)
  refusal <- BS.readFile cyclePath
  expectLoad "import cycle is source located" "SFM005" cyclePath
    (loadAuthoredModel cyclePath refusal)
  expectLoad "unsafe module root is refused" "SFM002" theftHost
    (loadAuthoredModel theftHost (replace "module-root \".\"" "module-root \"../private\"" theftSource))
  expectLoad "missing exact module version is refused" "SFM003" theftHost
    (loadAuthoredModel theftHost (replace "version 1.0.0 as theft"
      "version 9.0.0 as theft" theftSource))
  expectLoad "private export access is refused" "SFM006" theftHost
    (loadAuthoredModel theftHost (replace "s84::x:section84" "defs::x:section84" theftSource))
  expectLoad "wrong declaration kind is refused" "SFM006" theftHost
    (loadAuthoredModel theftHost (replace "use offence theft::o:theft"
      "use definition theft::o:theft" theftSource))
  expectLoad "import alone does not select a model" "SFM008" theftHost
    (loadAuthoredModel theftHost (replace
      "  use model theft::SingaporePenalCodeStatutoryDefinitionsResearchPrototype-v1;\n" "" theftSource))
  expectLoad "duplicate alias is refused" "SFM005" theftHost
    (loadAuthoredModel theftHost (replace "as theft;" "as defs;" theftSource))

temporalChecks :: FilePath -> IO ()
temporalChecks root = do
  let base = root </> "rewrite/frontend/fixtures/synthetic"
      modelPath = base </> "temporal_restricted_entry.yh"
      beforePath = base </> "temporal_before_boundary.yh"
      boundaryPath = base </> "temporal_at_boundary.yh"
  modelSource <- BS.readFile modelPath
  before <- BS.readFile beforePath
  boundary <- BS.readFile boundaryPath
  beforeRequest <- temporalRequest modelPath modelSource beforePath before
  boundaryRequest <- temporalRequest modelPath modelSource boundaryPath boundary
  check "pre-boundary authored expression is not satisfied"
    (status (runLine beforeRequest) == Just "not_satisfied")
  check "boundary uses inclusive effective-from expression"
    (status (runLine boundaryRequest) == Just "satisfied")
  boundaryAgain <- temporalRequest modelPath modelSource boundaryPath boundary
  check "temporal compilation is deterministic"
    (boundaryRequest == boundaryAgain)
  temporalExplanation <- explanationBytes modelPath modelSource boundaryPath boundary
  temporalSnapshot <- BS.readFile (base </> "temporal_boundary_explain.txt")
  check "temporal selection explanation snapshot" (temporalExplanation == temporalSnapshot)
  expectTemporal "missing conduct date scenario is refused" "SFT006" modelPath
    (loadAuthoredInput modelPath modelSource Nothing)
  expectTemporal "authored interval gap is refused" "SFT005" modelPath
    (loadAuthoredInput modelPath (replace "effective-to 2024-01-01"
      "effective-to 2023-12-31" modelSource) (Just (boundaryPath,boundary)))
  expectTemporal "authored interval overlap is refused" "SFT005" modelPath
    (loadAuthoredInput modelPath (replace "effective-to 2024-01-01"
      "effective-to 2024-01-02" modelSource) (Just (boundaryPath,boundary)))
  expectTemporal "invalid interval is refused" "SFT004" modelPath
    (loadAuthoredInput modelPath (replace "effective-from 2020-01-01"
      "effective-from 2025-01-01" modelSource) (Just (boundaryPath,boundary)))
  expectTemporal "date outside authored intervals is refused" "SFT007" beforePath
    (loadAuthoredInput modelPath modelSource
      (Just (beforePath,replace "2023-12-31" "2019-12-31" before)))

penaltyAndCorpusChecks :: FilePath -> IO ()
penaltyAndCorpusChecks root = do
  let base = root </> "research/singapore/offence-corpus-pilot"
      modelPath = base </> "modular-cheating-mischief.yh"
      sourcePath = base </> "cheating-mischief.yh"
      cheating =
        [("01_property_form_satisfied","satisfied",True)
        ,("02_act_harm_form_satisfied","satisfied",True)
        ,("03_both_forms_satisfied","satisfied",True)
        ,("04_deception_not_proved","not_satisfied",False)
        ,("05_property_fault_not_proved","not_satisfied",False)
        ,("06_property_inducement_not_proved","not_satisfied",False)
        ,("07_act_harm_not_proved","not_satisfied",False)
        ,("08_property_fault_unresolved","unresolved",False)
        ,("09_act_harm_unresolved","unresolved",False)
        ,("10_section84_defeats","not_satisfied",False)]
      mischief =
        [("01_intention_destruction_satisfied","satisfied",True)
        ,("02_knowledge_change_satisfied","satisfied",True)
        ,("03_intention_change_satisfied","satisfied",True)
        ,("04_knowledge_destruction_satisfied","satisfied",True)
        ,("05_mental_state_not_proved","not_satisfied",False)
        ,("06_interference_not_proved","not_satisfied",False)
        ,("07_intention_unresolved","unresolved",False)
        ,("08_destruction_unresolved","unresolved",False)
        ,("09_knowledge_resolves_alternative","satisfied",True)
        ,("10_section84_defeats","not_satisfied",False)]
  hostSource <- BS.readFile modelPath
  source <- BS.readFile sourcePath
  forM_ [("cheating",name,wanted,selected) | (name,wanted,selected) <- cheating]
    (runCorpus modelPath hostSource base "pen:section417")
  forM_ [("mischief",name,wanted,selected) | (name,wanted,selected) <- mischief]
    (runCorpus modelPath hostSource base "pen:section426")
  cheatingExplanation <- explanationBytes modelPath hostSource
    (base </> "scenarios/cheating/01_property_form_satisfied.yh")
    =<< BS.readFile (base </> "scenarios/cheating/01_property_form_satisfied.yh")
  cheatingSnapshot <- BS.readFile (base </> "snapshots/cheating-property-form.txt")
  check "cheating explanation snapshot" (cheatingExplanation == cheatingSnapshot)
  mischiefExplanation <- explanationBytes modelPath hostSource
    (base </> "scenarios/mischief/02_knowledge_change_satisfied.yh")
    =<< BS.readFile (base </> "scenarios/mischief/02_knowledge_change_satisfied.yh")
  mischiefSnapshot <- BS.readFile (base </> "snapshots/mischief-knowledge-change.txt")
  check "mischief explanation snapshot" (mischiefExplanation == mischiefSnapshot)
  expectChecked "unsupported imprisonment unit is refused" "SFP004" sourcePath
    (replace "maximum 3 years" "maximum 3 fortnights" source)
  expectChecked "unbounded minimum is refused" "SFP004" sourcePath
    (replace "minimum not-stated maximum 3" "minimum unbounded maximum 3" source)
  expectChecked "missing candidate source is refused" "SFP003" sourcePath
    (replace "source src:pc-offence-corpus provision 417"
      "source src:missing provision 417" source)
  expectChecked "malformed penalty provision is refused" "SFP003" sourcePath
    (replace "provision 417" "provision sentence" source)
  scenarioPath <- pure (base </> "scenarios/cheating/01_property_form_satisfied.yh")
  scenario <- BS.readFile scenarioPath
  loaded <- loadAuthoredModel modelPath hostSource >>= requireRight "corpus module load"
  check "missing selected classification is refused" $ case compileParsed modelPath
      (authoredModel loaded) (Just (scenarioPath,replace "  f:deception = proved;\n" "" scenario)) of
    Left issue -> diagnosticCode issue == "SFE042" && located issue scenarioPath
    Right _ -> False
  check "inappropriate target scope is refused" $ case compileParsed modelPath
      (authoredModel loaded) (Just (scenarioPath,replace
        "a:bounded-section415-text-expression" "a:bounded-section425-text-expression" scenario)) of
    Left issue -> diagnosticCode issue == "SFE023" && located issue scenarioPath
    Right _ -> False

runCorpus :: FilePath -> BS.ByteString -> FilePath -> Text
  -> (String,String,Text,Bool) -> IO ()
runCorpus modelPath hostSource base penaltyId (family,name,wanted,wantPenalty) = do
  let scenarioPath = base </> "scenarios" </> family </> name <> ".yh"
  scenario <- BS.readFile scenarioPath
  resolved <- loadAuthoredInput modelPath hostSource (Just (scenarioPath,scenario))
    >>= requireRight name
  let (authored,supplied) = resolved
      request = compileParsed modelPath (authoredModel authored) supplied
  compiled <- either (const (failed (name <> " compile"))) pure request
  check (name <> " deterministic compile")
    (request == compileParsed modelPath (authoredModel authored) supplied)
  let response = runLine compiled
  check (name <> " technical status") (status response == Just wanted)
  check (name <> " penalty selection remains separate")
    ((penaltyId `elem` selectedPenaltyIds response) == wantPenalty)

temporalRequest :: FilePath -> BS.ByteString -> FilePath -> BS.ByteString -> IO BS.ByteString
temporalRequest modelPath modelSource scenarioPath scenario = do
  resolved <- loadAuthoredInput modelPath modelSource (Just (scenarioPath,scenario))
    >>= requireRight "temporal load"
  let (authored,supplied) = resolved
  either (const (failed "temporal compile")) pure
    (compileParsed modelPath (authoredModel authored) supplied)

explanationBytes :: FilePath -> BS.ByteString -> FilePath -> BS.ByteString
  -> IO BS.ByteString
explanationBytes modelPath modelSource scenarioPath scenario = do
  resolved <- loadAuthoredInput modelPath modelSource (Just (scenarioPath,scenario))
    >>= requireRight "explanation load"
  let (authored,supplied) = resolved
  checked <- either (const (failed "explanation check")) pure
    (checkParsed modelPath (authoredModel authored) supplied)
  explanation <- either (const (failed "explanation render")) pure
    (explainChecked modelPath checked)
  pure (Encoding.encodeUtf8 (authoredPrefix authored <> explanation))

expectLoad :: String -> Text -> FilePath -> IO (Either Diagnostic AuthoredModel) -> IO ()
expectLoad label code path action = action >>= \result -> check label $ case result of
  Left issue -> diagnosticCode issue == code && located issue path
  Right _ -> False

expectTemporal :: String -> Text -> FilePath
  -> IO (Either Diagnostic (AuthoredModel,Maybe (FilePath,BS.ByteString))) -> IO ()
expectTemporal label code path action = action >>= \result -> check label $ case result of
  Left issue -> diagnosticCode issue == code && located issue path
  Right _ -> False

expectChecked :: String -> Text -> FilePath -> BS.ByteString -> IO ()
expectChecked label code path source = do
  result <- loadAuthoredModel path source
  case result of
    Left issue -> check label (diagnosticCode issue == code && located issue path)
    Right authored -> check label $ case compileParsed path (authoredModel authored) Nothing of
      Left issue -> diagnosticCode issue == code && located issue path
      Right _ -> False

requireRight :: String -> Either Diagnostic a -> IO a
requireRight label result = case result of
  Left _ -> failed label
  Right value -> pure value

located :: Diagnostic -> FilePath -> Bool
located issue path = diagnosticPath issue == path
  && tokenLine (diagnosticToken issue) > 0 && tokenColumn (diagnosticToken issue) > 0

status :: BS.ByteString -> Maybe Text
status bytes = either (const Nothing) (\value -> lookupField "status" value >>= textValue)
  (decodeJson bytes)

selectedPenaltyIds :: BS.ByteString -> [Text]
selectedPenaltyIds bytes = case decodeJson bytes of
  Left _ -> []
  Right value -> case lookupField "selected_penalties" value of
    Just (JArr items) -> [identifier | item <- items,
      Just identifier <- [lookupField "penalty_id" item >>= textValue]]
    _ -> []

replace :: Text -> Text -> BS.ByteString -> BS.ByteString
replace old new = Encoding.encodeUtf8 . Text.replace old new . Encoding.decodeUtf8

check :: String -> Bool -> IO ()
check label success = unless success (failed label)

failed :: String -> IO a
failed label = putStrLn ("language expansion failed: " <> label) >> exitFailure
