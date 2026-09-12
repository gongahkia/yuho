{-# LANGUAGE OverloadedStrings #-}
module ExceptionChecks (runExceptionChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Test.QuickCheck
  ( Property, Testable, arbitrary, forAll, isSuccess, maxSuccess
  , quickCheckWithResult, stdArgs, vectorOf, chooseInt )
import Yuho.Core.Types (Diagnostic(..), Trace(..))
import Yuho.Exception.Decode (decodeExceptionRequest)
import Yuho.Exception.Evaluate
  ( aggregateBranches, aggregateGuards, evaluateGraph, evaluateGraphReference )
import Yuho.Exception.Types
import Yuho.Exception.Validate (ValidatedGraph, sharedFacts, validateGraph)
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, textValue)

runExceptionChecks :: FilePath -> IO ()
runExceptionChecks root = do
  manifest <- readJson (root </> "CASES.json")
  case manifest of
    JObj cases -> forM_ cases (checkCase root)
    _ -> failCheck "exception manifest shape"
  diamond <- readJson (root </> "requests/E06.json")
  ordered <- readJson (root </> "requests/E17.json")
  reversed <- readJson (root </> "requests/E18.json")
  falseGuard <- readJson (root </> "requests/E03.json")
  trueGuard <- readJson (root </> "requests/E02.json")
  property "memoized and direct DAG evaluation agree" (memoProperty diamond)
  property "evaluation and target resolution are deterministic" (resolutionProperty diamond)
  property "canonical response ignores object key order" (canonicalProperty diamond)
  property "any true guard defeats, even with unresolved" trueDominatesProperty
  property "unresolved controls exactly when no guard is true" unresolvedProperty
  property "all false guards preserve the branch" falseGuardsProperty
  property "reordering exceptions changes trace order, not verdict or fired set"
    (reorderProperty ordered reversed)
  property "adding a false exception preserves the verdict" (addFalseProperty falseGuard)
  property "missing references never reach evaluation" (missingProperty trueGuard)
  property "validated graph order cannot manufacture a cycle" (acyclicProperty diamond)
  property "target sees the unchanged caller fact map" (factsProperty trueGuard)
  check "internal true plus unresolved" (aggregateGuards [TrueValue, UnresolvedValue]
    == (FalseValue, Defeated))
  check "internal false plus unresolved" (aggregateGuards [FalseValue, UnresolvedValue]
    == (UnresolvedValue, GuardUnresolved))
  check "rule aggregation" (aggregateBranches [FalseValue, UnresolvedValue] == UnresolvedValue
    && aggregateBranches [FalseValue, TrueValue, UnresolvedValue] == TrueValue)
  putStrLn "exception fragment: fixtures and semantic properties passed"

checkCase :: FilePath -> (Text, J) -> IO ()
checkCase root (name, expected)
  | name == "E35" = pure ()
  | otherwise = do
      let suffix = if name `elem` ["E32", "E33"] then ".txt" else ".json"
      request <- BS.readFile (root </> "requests" </> Text.unpack name <> suffix)
      response <- case decodeJson (runLine request) of
        Left reason -> failCheck ("response JSON " <> Text.unpack reason)
        Right result -> pure result
      let expectedStatus = fieldText "status" expected
          expectedCode = fieldText "code" expected
          expectedStage = fieldText "stage" expected
          actualCode = case fieldArray "diagnostics" response of
            Just (first:_) -> fieldText "code" first
            Just [] -> Just ""
            _ -> Nothing
          actualStage = case fieldArray "diagnostics" response of
            Just (first:_) -> fieldText "stage" first
            Just [] -> Just ""
            _ -> Nothing
          rules = maybe [] id (fieldArray "rules" response)
          rootRule = case filter ((== Just "r:root") . fieldText "id") rules of
            (item:_) -> Just item
            [] -> Nothing
          branches = maybe [] (maybe [] id . fieldArray "branches") rootRule
          actualStatuses = map (fieldText "status") branches
          actualReasons = map (fieldText "reason") branches
          expectedStatuses = maybe [] (map textValue) (fieldArray "branches" expected)
          expectedReasons = maybe [] (map textValue) (fieldArray "reasons" expected)
          fired = concatMap (maybe [] id . fieldArray "applicable_exceptions") branches
          expectedFired = maybe [] id (fieldArray "fired" expected)
          actualRules = Map.fromList [(identifier, status)
            | item <- rules, Just identifier <- [fieldText "id" item],
              Just status <- [fieldText "status" item]]
          expectedRules = case lookupField "rules" expected of
            Just (JObj values) -> Map.fromList [(identifier, status)
              | (identifier, JStr status) <- values]
            _ -> Map.empty
      check ("exception " <> Text.unpack name) (
        fieldText "status" response == expectedStatus && actualCode == expectedCode
        && actualStage == expectedStage && actualStatuses == expectedStatuses
        && actualReasons == expectedReasons && fired == expectedFired
        && actualRules == expectedRules)

readJson :: FilePath -> IO J
readJson path = do
  bytes <- BS.readFile path
  case decodeJson bytes of
    Left reason -> failCheck (Text.unpack reason)
    Right value -> pure value

fieldText :: Text -> J -> Maybe Text
fieldText key value = lookupField key value >>= textValue

fieldArray :: Text -> J -> Maybe [J]
fieldArray key value = case lookupField key value of
  Just (JArr items) -> Just items
  _ -> Nothing

property :: Testable prop => String -> prop -> IO ()
property label statement = do
  putStrLn label
  result <- quickCheckWithResult stdArgs {maxSuccess = 100} statement
  unless (isSuccess result) exitFailure

check :: String -> Bool -> IO ()
check label condition = unless condition (failCheck label)

failCheck :: String -> IO a
failCheck label = putStrLn ("FAIL " <> label) >> exitFailure

decoded :: J -> Maybe (ExceptionRequest, ValidatedGraph)
decoded request = do
  parsed <- either (const Nothing) Just (decodeExceptionRequest request)
  graph <- either (const Nothing) Just (validateGraph (exceptionRawGraph parsed))
  Just (parsed, graph)

setFacts :: J -> [(Text, Bool)] -> J
setFacts request facts = changeField "facts" (const (JObj
  [(key, JBool value) | (key, value) <- facts])) request

changeField :: Text -> (J -> J) -> J -> J
changeField key transform (JObj fields) = JObj
  [(name, if name == key then transform value else value) | (name, value) <- fields]
changeField _ _ value = value

reverseObjects :: J -> J
reverseObjects (JObj fields) = JObj (reverse
  [(name, reverseObjects value) | (name, value) <- fields])
reverseObjects (JArr values) = JArr (map reverseObjects values)
reverseObjects value = value

ruleStatuses :: ExceptionResult -> Map.Map Text Truth
ruleStatuses result = Map.fromList [(ruleResultId rule, ruleResultStatus rule)
  | rule <- exceptionResultRules result]

firedSet :: ExceptionResult -> Set.Set Text
firedSet result = Set.fromList [identifier | rule <- exceptionResultRules result,
  branch <- ruleResultBranches rule, identifier <- exceptionBranchApplicable branch]

memoProperty :: J -> Property
memoProperty request = forAll arbitrary $ \(a, b, c, d) ->
  let changed = setFacts request [("f:root", a), ("f:left", b),
                                  ("f:right", c), ("f:leaf", d)]
  in case decoded changed of
    Nothing -> False
    Just (parsed, graph) -> evaluateGraph parsed graph == evaluateGraphReference parsed graph

resolutionProperty :: J -> Property
resolutionProperty request = forAll arbitrary $ \(a, b, c, d) ->
  let changed = setFacts request [("f:root", a), ("f:left", b),
                                  ("f:right", c), ("f:leaf", d)]
      reordered = changeField "registry" reverseArray changed
      run value = do
        (parsed, graph) <- decoded value
        either (const Nothing) Just (evaluateGraph parsed graph)
  in case (run changed, run reordered) of
    (Just first, Just second) -> exceptionResultStatus first == exceptionResultStatus second
      && ruleStatuses first == ruleStatuses second
    _ -> False
  where
    reverseArray (JArr values) = JArr (reverse values)
    reverseArray value = value

canonicalProperty :: J -> Property
canonicalProperty request = forAll arbitrary $ \(a, b, c, d) ->
  let changed = setFacts request [("f:root", a), ("f:left", b),
                                  ("f:right", c), ("f:leaf", d)]
  in runLine (encodeJson changed) == runLine (encodeJson (reverseObjects changed))

truths :: [Int] -> [Truth]
truths = map (\value -> case value of
  0 -> FalseValue
  1 -> TrueValue
  _ -> UnresolvedValue)

trueDominatesProperty :: Property
trueDominatesProperty = forAll (vectorOf 5 (chooseInt (0, 2))) $ \values ->
  aggregateGuards (TrueValue : truths values) == (FalseValue, Defeated)

unresolvedProperty :: Property
unresolvedProperty = forAll (vectorOf 5 (chooseInt (0, 2))) $ \values ->
  let statuses = truths values
      (result, _) = aggregateGuards statuses
  in if TrueValue `elem` statuses then result == FalseValue
     else if UnresolvedValue `elem` statuses then result == UnresolvedValue
     else result == TrueValue

falseGuardsProperty :: Property
falseGuardsProperty = forAll (chooseInt (0, 10)) $ \size ->
  aggregateGuards (replicate size FalseValue) == (TrueValue, Satisfied)

reorderProperty :: J -> J -> Property
reorderProperty forward backward = forAll arbitrary $ \(a, b, c) ->
  let facts = [("f:root", a), ("f:a", b), ("f:b", c)]
      run value = do
        (parsed, graph) <- decoded (setFacts value facts)
        either (const Nothing) Just (evaluateGraph parsed graph)
  in case (run forward, run backward) of
    (Just first, Just second) -> exceptionResultStatus first == exceptionResultStatus second
      && firedSet first == firedSet second
    _ -> False

addFalseProperty :: J -> Property
addFalseProperty request = forAll arbitrary $ \caller ->
  let base = setFacts request [("f:root", caller), ("f:target", False)]
      extra = changeField "registry" addToRoot base
      run value = do
        (parsed, graph) <- decoded value
        either (const Nothing) Just (evaluateGraph parsed graph)
  in case (run base, run extra) of
    (Just first, Just second) -> exceptionResultStatus first == exceptionResultStatus second
    _ -> False
  where
    addToRoot (JArr (JObj fields : rest)) =
      JArr (JObj [(key, if key == "exceptions" then appendException value else value)
        | (key, value) <- fields] : rest)
    addToRoot value = value
    appendException (JArr (JObj fields : rest)) = JArr
      (JObj fields : rest ++ [JObj [(key, if key == "id" then JStr "x:root:2" else value)
        | (key, value) <- fields]])
    appendException value = value

missingProperty :: J -> Property
missingProperty request = forAll arbitrary $ \caller ->
  let changed = setFacts request [("f:root", caller), ("f:target", True)]
      missing = changeField "registry" changeRoot changed
  in case decodeExceptionRequest missing of
    Left _ -> False
    Right parsed -> case validateGraph (exceptionRawGraph parsed) of
      Left issue -> diagCode issue == "KINV005"
      Right _ -> False
  where
    changeRoot (JArr (JObj fields : rest)) = JArr
      (JObj [(key, if key == "exceptions" then changeEx value else value)
       | (key, value) <- fields] : rest)
    changeRoot value = value
    changeEx (JArr (JObj fields : rest)) = JArr
      (JObj [(key, if key == "guard" then changeField "target"
        (const (JStr "r:absent")) value else value) | (key, value) <- fields] : rest)
    changeEx value = value

acyclicProperty :: J -> Property
acyclicProperty request = forAll arbitrary $ \(a, b, c, d) ->
  let facts = [("f:root", a), ("f:left", b), ("f:right", c), ("f:leaf", d)]
  in case decoded (setFacts request facts) of
    Nothing -> False
    Just (parsed, graph) -> case evaluateGraph parsed graph of
      Right _ -> True
      Left _ -> False

factsProperty :: J -> Property
factsProperty request = forAll arbitrary $ \targetFact ->
  let facts = [("f:root", True), ("f:target", targetFact)]
  in case decoded (setFacts request facts) of
    Nothing -> False
    Just (parsed, graph) -> case evaluateGraph parsed graph of
      Left _ -> False
      Right result -> sharedFacts graph == Map.fromList facts
        && case [traceValue edge | rule <- exceptionResultRules result,
                   ruleResultId rule == "r:target", edge <- ruleResultTrace rule,
                   traceId edge == "f:target"] of
             [observed] -> observed == targetFact
             _ -> False
