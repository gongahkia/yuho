{-# LANGUAGE OverloadedStrings #-}
module ReleaseV1Checks (runReleaseV1Checks) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import Data.List (find)
import qualified Data.Text as Text
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.CoreYuho.TypedFinite
import Yuho.Protocol.Json (decodeJson, encodeJson)
import Yuho.Surface.Compile (compileSource)
import Yuho.Surface.TypedFinite
  ( explainTypedFinite, loadTypedFiniteProgram, encodeTypedFiniteRequest )

runReleaseV1Checks :: FilePath -> IO ()
runReleaseV1Checks root = do
  let typed = root </> "examples/typed-finite-v0.3"
      modelPath = typed </> "normative-responsibility.yh"
      scenarioPath = typed </> "normative-responsibility-satisfied.yh"
  model <- BS.readFile modelPath
  scenario <- BS.readFile scenarioPath
  program <- loadTypedFiniteProgram modelPath model (Just (scenarioPath,scenario))
    >>= either (const (failed "v0.3 typed model checks")) pure
  result <- either (const (failed "v0.3 typed evaluation")) pure
    (evaluateTypedFinite program)
  check "three normative positions and routes are retained"
    (length (finiteNorms program) == 2 && length (finiteRoutes program) == 1)
  check "norm priority resolves through existing rule calculus"
    ((propositionState <$> find ((== "p:specified-action") . observedPropositionId)
      (finiteResultPropositions result)) == Just "defeated")
  check "responsibility route explicitly establishes only its target"
    ((propositionState <$> find ((== "p:responsibility-route") . observedPropositionId)
      (finiteResultPropositions result)) == Just "established")
  let request = encodeTypedFiniteRequest "v0.3-release-check" program
  check "v0.3 lowering remains TypedFiniteRules-v1"
    ("\"fragment\":\"TypedFiniteRules-v1\"" `BS.isInfixOf` request)
  check "v0.3 explanation retains legal boundary"
    ("does not assess evidence" `Text.isInfixOf` explainTypedFinite program result)

  let modularModelPath = typed </> "modular-normative-responsibility.yh"
      modularScenarioPath = typed </> "modular-normative-responsibility-satisfied.yh"
  modularModel <- BS.readFile modularModelPath
  modularScenario <- BS.readFile modularScenarioPath
  modularProgram <- loadTypedFiniteProgram modularModelPath modularModel
      (Just (modularScenarioPath,modularScenario))
    >>= either (const (failed "v0.3 norm/route module composition")) pure
  check "norms and routes survive exact-version module composition"
    (length (finiteModules modularProgram) == 1
      && length (finiteNorms modularProgram) == 2
      && length (finiteRoutes modularProgram) == 1)

  let synthetic = root </> "examples/synthetic"
      penaltyModel = synthetic </> "rich-candidate-sanctions.yh"
      penaltyScenario = synthetic </> "scenario-rich-candidate-sanctions.yh"
  penaltySource <- BS.readFile penaltyModel
  penaltyAssignments <- BS.readFile penaltyScenario
  compiled <- either (const (failed "rich candidate sanctions compile")) pure
    (compileSource penaltyModel penaltySource (Just (penaltyScenario,penaltyAssignments)))
  canonical <- either (const (failed "rich candidate sanctions JSON")) (pure . encodeJson)
    (decodeJson compiled)
  check "rich candidate sanctions lower to existing term schema"
    (all (`BS.isInfixOf` canonical)
      ["\"kind\":\"death\"","\"kind\":\"life_imprisonment\""
      ,"\"kind\":\"caning\"","\"kind\":\"all_of\""
      ,"\"kind\":\"exactly_one_of\""])
  putStrLn "release v1: normative positions, responsibility routes and rich sanctions passed"

check :: String -> Bool -> IO ()
check label value = unless value (failed label)

failed :: String -> IO a
failed label = putStrLn ("release v1 checks failed: " <> label) >> exitFailure
