{-# LANGUAGE OverloadedStrings #-}
module CoreYuhoChecks (runCoreYuhoChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.List (sort)
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Test.QuickCheck (elements, forAll, isSuccess, listOf, maxSuccess,
  quickCheckWithResult, stdArgs)
import Yuho.CoreYuho.Registry (publicConstructs)
import Yuho.CoreYuho.Semantics
import Yuho.CoreYuho.Types
import Yuho.Exception.Types (Truth(..))
import Yuho.Presumption.Types (DerivationState(..))
import Yuho.Protocol.Json (arrayValue, decodeJson, lookupField, textValue)
import Yuho.Surface.Compile (checkParsed)
import Yuho.Surface.Modules (AuthoredModel(..), loadAuthoredModel)
import Yuho.CoreYuho.Normalize (normalizeChecked)

runCoreYuhoChecks :: FilePath -> IO ()
runCoreYuhoChecks root = do
  truthTables
  properties
  registryCheck root
  normalizationCheck root
  putStrLn "core yuho: exhaustive truth tables, properties, registry and normalization passed"

truthTables :: IO ()
truthTables = do
  let domain = [TrueValue,FalseValue,UnresolvedValue]
      lists = concat [sequence (replicate count domain) | count <- [0..3]]
  forM_ lists $ \values -> do
    check "all truth table" (allTruth values == expectedAll values)
    check "any truth table" (anyTruth values == expectedAny values)
    check "branch truth table" (branchTruth values == expectedAny values)
    check "guard truth table" (guardedTruth values == expectedGuard values)
  forM_ [(trigger,rebuttal) | trigger <- domain, rebuttal <- domain] $ \(trigger,rebuttal) ->
    check "presumption truth table" (presumptionState trigger rebuttal ==
      expectedPresumption trigger rebuttal)
  check "active presumption makes false target effective"
    (presumptionEffective FalseValue [Active] == TrueValue)
  check "unresolved presumption remains unresolved"
    (presumptionEffective FalseValue [RouteUnresolved] == UnresolvedValue)

properties :: IO ()
properties = do
  let generator = listOf (elements [TrueValue,FalseValue,UnresolvedValue])
  result <- quickCheckWithResult stdArgs { maxSuccess = 200 } $
    forAll generator $ \values -> allTruth values == allTruth (reverse values)
      && anyTruth values == anyTruth (reverse values)
      && branchTruth values == branchTruth (reverse values)
      && guardedTruth values == guardedTruth (reverse values)
  check "all/any/branch/guard order independence" (isSuccess result)
  let expression = CoreAll "g:root"
        [CoreInput "f:a" "q:a" Nothing,
         CoreAny "g:choice" [CoreInput "f:b" "q:b" Nothing,
           CoreInput "f:c" "q:c" Nothing]]
      facts = Map.fromList [("f:a",TrueValue),("f:b",FalseValue),
        ("f:c",UnresolvedValue)]
  check "core evaluation is total for a closed finite tree"
    (evaluateRequirement facts expression == Right UnresolvedValue)
  check "missing primitive is explicit"
    (evaluateRequirement Map.empty expression == Left "f:a")
  total <- quickCheckWithResult stdArgs { maxSuccess = 200 } $
    forAll (elements [TrueValue,FalseValue,UnresolvedValue]) $ \a ->
    forAll (elements [TrueValue,FalseValue,UnresolvedValue]) $ \b ->
    forAll (elements [TrueValue,FalseValue,UnresolvedValue]) $ \c ->
      let supplied = Map.fromList [("f:a",a),("f:b",b),("f:c",c)]
          first = evaluateRequirement supplied expression
      in first == Right (allTruth [a,anyTruth [b,c]])
        && first == evaluateRequirement supplied expression
  check "closed finite Core evaluation is total and deterministic" (isSuccess total)

registryCheck :: FilePath -> IO ()
registryCheck root = do
  bytes <- BS.readFile (root </> "docs/rewrite/core-yuho-conformance-v0.1.json")
  value <- either (const (failed "registry is valid JSON")) pure (decodeJson bytes)
  rows <- maybe (failed "registry has constructs") pure
    (lookupField "constructs" value >>= arrayValue)
  names <- mapM (maybe (failed "registry construct name") pure
    . (>>= textValue) . lookupField "construct") rows
  check "every public construct has exactly one conformance entry"
    (sort names == sort publicConstructs && length names == length publicConstructs)
  forM_ rows $ \row -> forM_
    ["parser","checker","core","lowering","kernel_variant","explanation",
     "diagram","test_evidence"] $ \field ->
      check ("registry field " <> show field) $ case lookupField field row >>= textValue of
        Just valueText -> not (valueText == "")
        Nothing -> False

normalizationCheck :: FilePath -> IO ()
normalizationCheck root = do
  let base = root </> "research/singapore/research-release"
      modelPath = base </> "modular-singapore-criminal-law-release.yh"
      scenarioPath = base </> "scenarios/rash-endangerment/01_satisfied_primary.yh"
  modelSource <- BS.readFile modelPath
  scenario <- BS.readFile scenarioPath
  authored <- loadAuthoredModel modelPath modelSource >>= either
    (const (failed "modular model load")) pure
  checked <- either (const (failed "checked model normalization")) pure
    (checkParsed modelPath (authoredModel authored) (Just (scenarioPath,scenario)))
  let core = normalizeChecked authored checked
  check "normalized core retains independent modules" (length (coreProgramModules core) == 7)
  check "normalized core retains rules and penalties"
    (length (coreProgramRules core) >= 11 && length (coreProgramPenalties core) == 7)

expectedAll :: [Truth] -> Truth
expectedAll values
  | FalseValue `elem` values = FalseValue
  | UnresolvedValue `elem` values = UnresolvedValue
  | otherwise = TrueValue

expectedAny :: [Truth] -> Truth
expectedAny values
  | TrueValue `elem` values = TrueValue
  | UnresolvedValue `elem` values = UnresolvedValue
  | otherwise = FalseValue

expectedGuard :: [Truth] -> Truth
expectedGuard values
  | TrueValue `elem` values = FalseValue
  | UnresolvedValue `elem` values = UnresolvedValue
  | otherwise = TrueValue

expectedPresumption :: Truth -> Truth -> DerivationState
expectedPresumption FalseValue _ = Inactive
expectedPresumption _ TrueValue = Rebutted
expectedPresumption TrueValue FalseValue = Active
expectedPresumption _ _ = RouteUnresolved

check :: String -> Bool -> IO ()
check label value = unless value (failed label)

failed :: String -> IO a
failed label = putStrLn ("core yuho failed: " <> label) >> exitFailure
