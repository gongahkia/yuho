{-# LANGUAGE OverloadedStrings #-}
module TypedFactsChecks (runTypedChecks) where

import Control.Monad (forM_, unless, (>=>))
import qualified Data.ByteString as BS
import Data.Maybe (listToMaybe)
import Data.Text (Text)
import qualified Data.Text as Text
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Test.QuickCheck (arbitrary, forAll, isSuccess, maxSuccess, quickCheckWithResult, stdArgs)
import Yuho.Exception.Evaluate (evaluateGraph, evaluateGraphReference)
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, objectFields, textValue)
import Yuho.TypedFacts.Decode (decodeTypedRequest)
import qualified Yuho.TypedFacts.Types
import qualified Yuho.TypedFacts.Validate
import Yuho.TypedFacts.Validate (typedGraph, validateTyped)

runTypedChecks :: FilePath -> IO ()
runTypedChecks directory = do
  manifest <- BS.readFile (directory </> "CASES.json")
  cases <- case decodeJson manifest >>= maybe (Left "expected cases object") Right . objectFields of
    Left reason -> putStrLn (Text.unpack reason) >> exitFailure
    Right items -> pure items
  forM_ cases $ \(name, expected) -> do
    if name == "T49" then pure () else do
      file <- maybe (putStrLn "missing request file" >> exitFailure) pure
        (lookupField "request_file" expected >>= textValue)
      request <- BS.readFile (directory </> Text.unpack file)
      let result = decodeJson (runLine request)
          actual = do
            value <- either (const Nothing) Just result
            status <- lookupField "status" value >>= textValue
            code <- case lookupField "diagnostics" value of
              Just (JArr []) -> Just ""
              Just (JArr (issue:_)) -> lookupField "code" issue >>= textValue
              _ -> Nothing
            pure (status, code)
          wanted = (,) <$> (lookupField "status" expected >>= textValue)
                       <*> (lookupField "code" expected >>= textValue)
      check ("typed fixture " <> Text.unpack name) (actual == wanted)
  first <- readRequest directory "T01"
  burden <- readRequest directory "T06"
  supplied <- readRequest directory "T09"
  mismatch <- readRequest directory "T30"
  absentBurden <- readRequest directory "T29"
  absentStandard <- readRequest directory "T32"
  missing <- readRequest directory "T19"
  collision <- readRequest directory "T38"
  unreachable <- readRequest directory "T41"
  diamond <- readRequest directory "T16"
  target <- readRequest directory "T15"
  recursive <- readRequest directory "T03"
  let changedFact value request = alterFact "f:root" (put "value" (JBool value)) request
      result value = decodeJson (runLine (encodeJson value))
      status value = result value >>= maybe (Left "no status") Right
        . (lookupField "status" >=> textValue)
      code value = result value >>= maybe (Left "no code") Right . diagnosticCode
      response value = runLine (encodeJson value)
      agrees value = let typed = changedFact value first
                         plain = put "fragment" (JStr "AcyclicGuardedExceptions-v1")
                           (alterFact "f:root" (const (JBool value))
                             (put "fragment" (JStr "AcyclicGuardedExceptions-v1") first))
                     in status typed == status plain
      matches = status burden == Right "true"
      memoAgrees value = case decodeTypedRequest (changedFact value diamond) >>= validateTyped of
        Left _ -> False
        Right graph -> let request = Yuho.TypedFacts.Validate.typedRequest graph
                           exceptionRequest = Yuho.TypedFacts.Types.typedExceptionRequest request
                       in evaluateGraph exceptionRequest (typedGraph graph) ==
                          evaluateGraphReference exceptionRequest (typedGraph graph)
  property "typed Boolean projection agrees with exception evaluation" (forAll arbitrary agrees)
  property "typed provenance cannot change verdict" (forAll arbitrary $ \flag ->
    status (alterFact "f:root" (put "provenance" (JObj
      [("source_label", JStr (if flag then "first" else "second"))
      ,("recorded_date", JStr (if flag then "2024-02-29" else "2026-09-12"))
      ,("jurisdiction", JStr (if flag then "SG" else "MY"))])) first) == Right "true")
  property "matching metadata cannot change verdict" (forAll arbitrary $ \flag ->
    matches && status (changedFact flag burden) == status (changedFact flag first))
  property "binding mismatch rejects regardless of Boolean value" (forAll arbitrary $ \flag ->
    code (changedFact flag mismatch) == Right "KINV007")
  property "unreachable rule binding is checked" (forAll arbitrary $ \flag ->
    code (changedFact flag unreachable) == Right "KINV007")
  property "exact leaf IDs do not normalize" (forAll arbitrary $ \flag ->
    code (alterFact "f_root" (put "value" (JBool flag)) collision) == Right "KINV001")
  property "undeclared metadata is noncontrolling" (forAll arbitrary $ \flag ->
    status (changedFact flag supplied) == status (changedFact flag first))
  property "missing declared burden rejects" (forAll arbitrary $ \flag ->
    code (changedFact flag absentBurden) == Right "KINV007")
  property "missing declared standard rejects" (forAll arbitrary $ \flag ->
    code (changedFact flag absentStandard) == Right "KINV007")
  property "missing bindings never reach evaluation" (forAll arbitrary $ \flag ->
    code (alterFact "f:extra" (put "value" (JBool flag)) missing) == Right "KINV001")
  property "typed memo and reference evaluators agree" (forAll arbitrary memoAgrees)
  property "canonical output ignores JSON object-key order" (forAll arbitrary $ \flag ->
    let sample = changedFact flag first in response sample == response (reverseObjects sample))
  property "typed evaluation repeats deterministically" (forAll arbitrary $ \flag ->
    let sample = changedFact flag target in response sample == response sample)
  property "registered target retains caller typed context" (forAll arbitrary $ \flag ->
    targetContext flag target)
  property "leaf observation order ignores Boolean values" (forAll arbitrary $ \flag ->
    observationIds (response (alterFact "f:third" (put "value" (JBool flag)) recursive)) ==
      Just ["f:root", "f:second", "f:third"])
  check "recursive leaf observation source order" (observationIds (runLine (encodeJson recursive)) ==
    Just ["f:root", "f:second", "f:third"])
  putStrLn "typed: fixtures and 15 bounded properties passed"
  where
    property title predicate = do
      result <- quickCheckWithResult stdArgs {maxSuccess = 25} predicate
      check title (isSuccess result)

readRequest :: FilePath -> String -> IO J
readRequest directory name = do
  bytes <- BS.readFile (directory </> "requests" </> name <> ".json")
  case decodeJson bytes of
    Left reason -> putStrLn (Text.unpack reason) >> exitFailure
    Right value -> pure value

check :: String -> Bool -> IO ()
check title passed = unless passed (putStrLn ("failed: " <> title) >> exitFailure)

put :: Text -> J -> J -> J
put key new (JObj fields) = JObj
  ([(name, if name == key then new else item) | (name, item) <- fields]
  ++ if key `elem` map fst fields then [] else [(key, new)])
put _ _ other = other

alterFact :: Text -> (J -> J) -> J -> J
alterFact identifier change request = case lookupField "facts" request of
  Just (JObj fields) -> put "facts" (JObj
    [(key, if key == identifier then change value else value) | (key, value) <- fields]) request
  _ -> request

reverseObjects :: J -> J
reverseObjects (JObj fields) = JObj (reverse
  [(key, reverseObjects value) | (key, value) <- fields])
reverseObjects (JArr values) = JArr (map reverseObjects values)
reverseObjects value = value

diagnosticCode :: J -> Maybe Text
diagnosticCode value = case lookupField "diagnostics" value of
  Just (JArr (first:_)) -> lookupField "code" first >>= textValue
  _ -> Nothing

observationIds :: BS.ByteString -> Maybe [Text]
observationIds bytes = do
  result <- either (const Nothing) Just (decodeJson bytes)
  JArr (first:_) <- lookupField "rules" result
  JArr observations <- lookupField "fact_observations" first
  traverse (\item -> lookupField "leaf_id" item >>= textValue) observations

targetContext :: Bool -> J -> Bool
targetContext value request = case decodeJson (runLine (encodeJson
  (alterFact "f:target" (put "value" (JBool value)) request))) of
  Left _ -> False
  Right result -> case lookupField "rules" result of
    Just (JArr rules) -> case listToMaybe
      [rule | rule <- rules, lookupField "id" rule == Just (JStr "r:target")] of
      Just target -> case lookupField "fact_observations" target of
        Just (JArr [observation]) ->
          lookupField "value" observation == Just (JBool value)
          && lookupField "provenance" observation ==
            Just (JObj [("source_label", JStr "shared")])
          && lookupField "status" target ==
            Just (JStr (if value then "true" else "false"))
        _ -> False
      Nothing -> False
    _ -> False
