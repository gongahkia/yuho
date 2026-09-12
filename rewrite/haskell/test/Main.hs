{-# LANGUAGE OverloadedStrings #-}
module Main (main) where

import Control.Monad (forM_, unless)
import qualified Data.Aeson as Aeson
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.List (sortOn)
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Char (ord)
import System.Directory (doesFileExist, getCurrentDirectory)
import System.Exit (exitFailure)
import System.FilePath ((</>), takeDirectory)
import Test.QuickCheck (Property, Testable, arbitrary, forAll, isSuccess, quickCheckWithResult, stdArgs, maxSuccess)
import ExceptionChecks (runExceptionChecks)
import TypedFactsChecks (runTypedChecks)
import Yuho.Core.Source (validateSpan)
import Yuho.Core.Types (Source(..), Span(..))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, textValue)

main :: IO ()
main = do
  root <- repositoryRoot
  let frozen = root </> "experiments/language-spike/fixtures"
      hardening = root </> "rewrite/haskell/test/fixtures"
  golden frozen
  hardeningCases hardening
  runExceptionChecks (root </> "rewrite/haskell/test/exception-fixtures")
  runTypedChecks (root </> "rewrite/haskell/test/typed-fixtures")
  b06 <- readJson (frozen </> "requests/B06.json")
  b01 <- readJson (frozen </> "requests/B01.json")
  b03 <- readJson (frozen </> "requests/B03.json")
  b05 <- readJson (frozen </> "requests/B05.json")
  check "definition-only remains false" (let result = runLine (encodeJson b05)
    in statusOf result == Just "false" && fieldText "provision_kind" result == Just "definition_only")
  property "recursive All/Any and complete ordered trace" (booleanProperty b06)
  property "alternative sibling branches" (alternativesProperty b01)
  property "inherited ancestor conjunction" (inheritanceProperty b03)
  property "missing facts reject rather than evaluate false" (totalFactsProperty b06)
  property "fact insertion order cannot change declaration trace" (factOrderProperty b06)
  property "canonical bytes independent of input object-key order" (canonicalProperty b06)
  property "out-of-source spans reject" sourceSpanProperty
  putStrLn "foundation: golden, hardening, and semantic properties passed"

repositoryRoot :: IO FilePath
repositoryRoot = do
  current <- getCurrentDirectory
  let candidates = take 8 (iterate takeDirectory current)
  locate candidates
  where
    locate [] = putStrLn "repository root not found" >> exitFailure
    locate (candidate:rest) = do
      present <- doesFileExist (candidate </> "experiments/language-spike/fixtures/MANIFEST.json")
      if present then pure candidate else locate rest

golden :: FilePath -> IO ()
golden root = forM_ cases $ \name -> do
  request <- BS.readFile (root </> "requests" </> name <> ".json")
  expected <- BS.readFile (root </> "expected" </> name <> ".json")
  check ("golden " <> name) (runLine request == expected)
  where
    cases = ["B01", "B02", "B03", "B04", "B05", "B06", "B07",
             "P01", "P02", "P03", "P04", "R01", "R02", "R03", "R04"]

hardeningCases :: FilePath -> IO ()
hardeningCases root = do
  bytes <- BS.readFile (root </> "CASES.json")
  manifest <- case Aeson.eitherDecodeStrict' bytes of
    Left message -> putStrLn message >> exitFailure
    Right value -> pure (value :: Map.Map Text (Map.Map Text Text))
  forM_ (Map.toList manifest) $ \(name, expected) ->
    if name == "H12" then pure () else do
      let suffix = if name `elem` ["H11", "H15", "H17"] then ".txt" else ".json"
      request <- BS.readFile (root </> "requests" </> Text.unpack name <> suffix)
      let response = decodeJson (runLine request)
          actual = do
            result <- either (const Nothing) Just response
            status <- lookupField "status" result >>= textValue
            case lookupField "diagnostics" result of
              Just (JArr []) -> Just (status, "", "")
              Just (JArr (first:_)) -> do
                code <- lookupField "code" first >>= textValue
                stage <- lookupField "stage" first >>= textValue
                Just (status, code, stage)
              _ -> Nothing
          wanted = (Map.lookup "status" expected, Map.lookup "code" expected, Map.lookup "stage" expected)
      check ("hardening " <> Text.unpack name) (fmap (\(a,b,c) -> (Just a, Just b, Just c)) actual == Just wanted)

readJson :: FilePath -> IO J
readJson path = do
  bytes <- BS.readFile path
  case decodeJson bytes of
    Left issue -> putStrLn (Text.unpack issue) >> exitFailure
    Right value -> pure value

property :: Testable prop => String -> prop -> IO ()
property name statement = do
  putStrLn name
  result <- quickCheckWithResult stdArgs { maxSuccess = 100 } statement
  unless (isSuccess result) exitFailure

booleanProperty :: J -> Property
booleanProperty request = forAll arbitrary $ \(a, b, c) ->
  let response = runLine (encodeJson (applyFacts request [("a", a), ("b", b), ("c", c)]))
  in statusOf response == Just (if a && (b || c) then "true" else "false")
     && traceIds response == Just ["group:all", "a", "group:any", "b", "c"]

alternativesProperty :: J -> Property
alternativesProperty request = forAll arbitrary $ \(first, second) ->
  let response = runLine (encodeJson (applyFacts request [("first", first), ("second", second)]))
  in statusOf response == Just (if first || second then "true" else "false")
     && branchStatuses response == Just [first, second]

inheritanceProperty :: J -> Property
inheritanceProperty request = forAll arbitrary $ \(common, first, second) ->
  let response = runLine (encodeJson (applyFacts request [("common", common), ("first", first), ("second", second)]))
  in statusOf response == Just (if common && (first || second) then "true" else "false")
     && (length <$> traceIds response) == Just 4

totalFactsProperty :: J -> Property
totalFactsProperty request = forAll arbitrary $ \(a, c) ->
  let response = runLine (encodeJson (applyFacts request [("a", a), ("c", c)]))
  in statusOf response == Just "rejected" && firstCode response == Just "KINV001"

factOrderProperty :: J -> Property
factOrderProperty request = forAll arbitrary $ \(a, b, c) ->
  let facts = [("a", a), ("b", b), ("c", c)]
      forward = runLine (encodeJson (applyFacts request facts))
      backward = runLine (encodeJson (applyFacts request (reverse facts)))
  in forward == backward && traceIds forward == Just ["group:all", "a", "group:any", "b", "c"]

canonicalProperty :: J -> Property
canonicalProperty request = forAll arbitrary $ \seed ->
  runLine (encodeJson request) == runLine (encodeJson (reorder seed request))

sourceSpanProperty :: Property
sourceSpanProperty = forAll arbitrary $ \extra ->
  let source = Source "fixture.yh" "a\nb\nc\n" "a\nb\nc\n" "unused"
      invalid = Span 0 (7 + abs (extra `mod` 100)) 1 1 4 1
  in not (validateSpan source invalid)

applyFacts :: J -> [(Text, Bool)] -> J
applyFacts request values =
  modifyField "facts" (const (JObj [(key, JBool value) | (key, value) <- values])) request

modifyField :: Text -> (J -> J) -> J -> J
modifyField key transform (JObj pairs) =
  JObj [(name, if name == key then transform value else value) | (name, value) <- pairs]
modifyField _ _ value = value

reorder :: Int -> J -> J
reorder seed value = case value of
  JObj pairs -> JObj (sortOn (score . fst) [(key, reorder (seed + 1) item) | (key, item) <- pairs])
  JArr items -> JArr (map (reorder (seed + 1)) items)
  other -> other
  where
    score = Text.foldl' (\acc character -> acc * 33 + ord character) seed

statusOf :: BS.ByteString -> Maybe Text
statusOf = fieldText "status"

fieldText :: Text -> BS.ByteString -> Maybe Text
fieldText key response = either (const Nothing) (\value -> lookupField key value >>= textValue) (decodeJson response)

firstCode :: BS.ByteString -> Maybe Text
firstCode response = do
  result <- either (const Nothing) Just (decodeJson response)
  JArr (first:_) <- lookupField "diagnostics" result
  lookupField "code" first >>= textValue

traceIds :: BS.ByteString -> Maybe [Text]
traceIds response = do
  result <- either (const Nothing) Just (decodeJson response)
  JArr edges <- lookupField "trace" result
  traverse (\edge -> lookupField "id" edge >>= textValue) edges

branchStatuses :: BS.ByteString -> Maybe [Bool]
branchStatuses response = do
  result <- either (const Nothing) Just (decodeJson response)
  JArr branches <- lookupField "branches" result
  traverse (\branch -> do
    status <- lookupField "status" branch >>= textValue
    case status of "true" -> Just True; "false" -> Just False; _ -> Nothing) branches

check :: String -> Bool -> IO ()
check label condition = unless condition (putStrLn ("FAIL " <> label) >> exitFailure)
