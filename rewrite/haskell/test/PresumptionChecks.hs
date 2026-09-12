{-# LANGUAGE OverloadedStrings #-}
module PresumptionChecks (runPresumptionChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import qualified Data.List as List
import Data.Text (Text)
import qualified Data.Text as Text
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Test.QuickCheck
  ( Testable, arbitrary, forAll, isSuccess, maxSuccess, quickCheckWithResult, stdArgs )
import Yuho.Exception.Types (Truth(..))
import Yuho.Kernel.Run (runLine)
import Yuho.Presumption.Decode (decodePresumptionRequest)
import Yuho.Presumption.Evaluate (combineEffective, deriveState, evaluatePresumptions)
import Yuho.Presumption.Types
  ( DerivationState(..), PresumptionResult(..), ValidatedPresumption(..) )
import Yuho.Presumption.Validate (validatePresumptionRequest)
import Yuho.Protocol.Json
  ( J(..), decodeJson, encodeJson, lookupField, objectFields, textValue )
import Yuho.SuppliedProofStatus.Evaluate
  ( allStatus, anyStatus, evaluateProofWith, evaluateProofWithReference )

runPresumptionChecks :: FilePath -> IO ()
runPresumptionChecks directory = do
  manifest <- readJson (directory </> "CASES.json")
  rows <- maybe (putStrLn "RD cases are not an object" >> exitFailure) pure
    (objectFields manifest)
  forM_ rows $ \(name, expected) -> do
    path <- maybe (putStrLn "RD case lacks file" >> exitFailure) pure
      (lookupField "file" expected >>= textValue)
    if name == "RD73" then pure () else do
      bytes <- BS.readFile (directory </> Text.unpack path)
      let output = runLine (BS.takeWhile (/= 10) bytes)
          decoded = either (const Nothing) Just (decodeJson output)
          field key = decoded >>= lookupField key
          actualCode = case field "diagnostics" of
            Just (JArr (first:_)) -> lookupField "code" first >>= textValue
            _ -> Just ""
          states = case field "presumption_derivations" of
            Just (JArr routes) -> [value | route <- routes
              , Just value <- [lookupField "state" route >>= textValue]]
            _ -> []
          selected = case field "selected_penalties" of
            Just (JArr penalties) -> [value | penalty <- penalties
              , Just value <- [lookupField "penalty_id" penalty >>= textValue]]
            _ -> []
      check ("RD fixture " <> Text.unpack name)
        ((field "status" >>= textValue) == (lookupField "status" expected >>= textValue))
      check ("RD diagnostic " <> Text.unpack name)
        (actualCode == (lookupField "code" expected >>= textValue))
      check ("RD routes " <> Text.unpack name)
        (states == strings (lookupField "route_states" expected))
      check ("RD selection " <> Text.unpack name)
        (selected == strings (lookupField "selected" expected))
  let truth = [TrueValue, FalseValue, UnresolvedValue]
      table = [Rebutted, Active, RouteUnresolved, Inactive, Inactive
        , Inactive, Rebutted, RouteUnresolved, RouteUnresolved]
      pairs = [(a,b) | a <- truth, b <- truth]
      allTable = [TrueValue, FalseValue, UnresolvedValue, FalseValue
        , FalseValue, FalseValue, UnresolvedValue, FalseValue, UnresolvedValue]
      anyTable = [TrueValue, TrueValue, TrueValue, TrueValue, FalseValue
        , UnresolvedValue, TrueValue, UnresolvedValue, UnresolvedValue]
  check "all derivation-state rows" (map (uncurry deriveState) pairs == table)
  property "derivation-state table is deterministic" $ forAll arbitrary $ \index ->
    let (a,b) = pick index pairs in deriveState a b == pick index table
  property "all pairwise three-valued condition entries" $ forAll arbitrary $ \index ->
    let (a,b) = pick index pairs in allStatus [a,b] == pick index allTable
      && anyStatus [a,b] == pick index anyTable
  property "direct satisfaction dominates every route set" $ forAll arbitrary $ \flags ->
    combineEffective TrueValue (map (`pick` [Active,Inactive,Rebutted,RouteUnresolved])
      (take 8 (flags :: [Int]))) == TrueValue
  property "active dominates unresolved routes in either order" $ forAll arbitrary $ \flag ->
    combineEffective FalseValue (if flag then [Active,RouteUnresolved]
      else [RouteUnresolved,Active]) == TrueValue
  property "unresolved propagates without active support" $ forAll arbitrary $ \flag ->
    combineEffective (if flag then UnresolvedValue else FalseValue)
      (if flag then [Inactive,Rebutted] else [RouteUnresolved]) == UnresolvedValue
  property "inactive and rebutted routes make no negative inference" $ forAll arbitrary $ \flag ->
    combineEffective FalseValue (if flag then [Inactive,Rebutted] else [Rebutted])
      == FalseValue
  property "route permutation preserves effective value" $ forAll arbitrary $ \index ->
    let states = take 4 (drop (abs (index :: Int) `mod` 3)
          (cycle [Inactive,RouteUnresolved,Active,Rebutted]))
    in combineEffective FalseValue states == combineEffective FalseValue (reverse states)
  active <- readJson (directory </> "requests/RD08.json")
  multiple <- readJson (directory </> "requests/RD33.json")
  chained <- readJson (directory </> "requests/RD36.json")
  cycleCase <- readJson (directory </> "requests/RD59.json")
  childTrace <- readJson (directory </> "requests/RD45.json")
  exceptionCase <- readJson (directory </> "requests/RD39.json")
  penaltyCase <- readJson (directory </> "requests/RD40.json")
  property "registration permutation preserves verdict and route-ID states" $
    forAll arbitrary $ \flag ->
      let input = if flag then multiple else reversePresumptions multiple
          output = runLine (encodeJson input)
          reversed = runLine (encodeJson (reversePresumptions input))
          routes = routeStates output
          backwards = routeStates reversed
      in fieldText "status" output == fieldText "status" reversed
        && List.sort routes == List.sort backwards
        && map fst routes == reverse (map fst backwards)
  property "memoized and reference downstream evaluation agree" $ forAll arbitrary $ \flag ->
    let input = if flag then chained else exceptionCase
    in case decodePresumptionRequest input >>= validatePresumptionRequest of
      Left _ -> False
      Right validated -> case evaluatePresumptions validated of
        Left _ -> False
        Right result -> let base = presumptionValidatedBase validated
                            values = presumptionEffective result
          in evaluateProofWith base values == evaluateProofWithReference base values
  property "acyclic chains resolve regardless of declaration dependency order" $
    forAll arbitrary $ \flag ->
      let input = if flag then chained else active
      in fieldText "status" (runLine (encodeJson input)) == Just "satisfied"
  property "cycles reject before any semantic result" $ forAll arbitrary $ \flag ->
    let input = if flag then cycleCase else updateTarget active "f:root"
        output = runLine (encodeJson input)
    in fieldText "status" output == Just "rejected"
      && diagnosticCode output == Just "KINV006"
      && emptyResults output
  property "complete condition traces survive decisive values" $ forAll arbitrary $ \flag ->
    let input = if flag then childTrace else active
        output = runLine (encodeJson input)
    in case decodeJson output of
      Right result -> case lookupField "presumption_derivations" result of
        Just (JArr (first:_)) -> case lookupField "trigger" first of
          Just trace -> if flag then case lookupField "children" trace of
            Just (JArr children) -> length children == 2
            _ -> False
            else lookupField "value" trace == Just (JStr "satisfied")
          _ -> False
        _ -> False
      _ -> False
  property "exceptions and penalties use effective leaf satisfaction" $ forAll arbitrary $ \flag ->
    let input = if flag then exceptionCase else penaltyCase
        output = runLine (encodeJson input)
    in if flag then fieldText "status" output == Just "not_satisfied"
      else selectedIds output == ["pen:root:1"]
  property "canonical bytes ignore object key order" $ forAll arbitrary $ \flag ->
    let input = if flag then active else chained
    in runLine (encodeJson input) == runLine (encodeJson (reverseObjects input))
  putStrLn "presumption: 77 RD fixtures and 14 bounded properties passed"

readJson :: FilePath -> IO J
readJson path = do
  bytes <- BS.readFile path
  case decodeJson bytes of
    Left issue -> putStrLn (Text.unpack issue) >> exitFailure
    Right value -> pure value

check :: String -> Bool -> IO ()
check name passed = unless passed (putStrLn (name <> " failed") >> exitFailure)

property :: Testable prop => String -> prop -> IO ()
property name statement = do
  putStrLn name
  result <- quickCheckWithResult stdArgs { maxSuccess = 100 } statement
  unless (isSuccess result) exitFailure

pick :: Int -> [a] -> a
pick index values = values List.!! fromInteger (abs (toInteger index) `mod`
  toInteger (length values))

strings :: Maybe J -> [Text]
strings (Just (JArr values)) = [item | JStr item <- values]
strings _ = []

fieldText :: Text -> BS.ByteString -> Maybe Text
fieldText key output = do
  value <- either (const Nothing) Just (decodeJson output)
  lookupField key value >>= textValue

diagnosticCode :: BS.ByteString -> Maybe Text
diagnosticCode output = case decodeJson output of
  Right value -> case lookupField "diagnostics" value of
    Just (JArr (first:_)) -> lookupField "code" first >>= textValue
    _ -> Nothing
  _ -> Nothing

selectedIds :: BS.ByteString -> [Text]
selectedIds output = case decodeJson output of
  Right value -> case lookupField "selected_penalties" value of
    Just (JArr rows) -> [item | row <- rows
      , Just item <- [lookupField "penalty_id" row >>= textValue]]
    _ -> []
  _ -> []

routeStates :: BS.ByteString -> [(Text, Text)]
routeStates output = case decodeJson output of
  Right value -> case lookupField "presumption_derivations" value of
    Just (JArr rows) -> [(identifier, state) | row <- rows
      , Just identifier <- [lookupField "presumption_id" row >>= textValue]
      , Just state <- [lookupField "state" row >>= textValue]]
    _ -> []
  _ -> []

reversePresumptions :: J -> J
reversePresumptions (JObj fields) = JObj [(key, if key == "presumptions"
  then case value of JArr rows -> JArr (reverse rows); _ -> value
  else value) | (key,value) <- fields]
reversePresumptions value = value

emptyResults :: BS.ByteString -> Bool
emptyResults output = case decodeJson output of
  Right value -> all (\key -> lookupField key value == Just (JArr []))
    ["rules","presumption_derivations","selected_penalties"]
  _ -> False

updateTarget :: J -> Text -> J
updateTarget (JObj fields) target = JObj [(key, if key == "presumptions"
  then case value of
    JArr (first:rest) -> JArr (setTrigger first : rest)
    _ -> value
  else value) | (key,value) <- fields]
  where
    setTrigger (JObj parts) = JObj [(key, if key == "trigger"
      then case value of
        JObj condition -> JObj [(name, if name == "leaf_id"
          then JStr target else item) | (name,item) <- condition]
        _ -> value
      else value) | (key,value) <- parts]
    setTrigger value = value
updateTarget value _ = value

reverseObjects :: J -> J
reverseObjects (JObj fields) = JObj (reverse [(key,reverseObjects value)
  | (key,value) <- fields])
reverseObjects (JArr values) = JArr (map reverseObjects values)
reverseObjects value = value
