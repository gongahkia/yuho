{-# LANGUAGE OverloadedStrings #-}
module ModelBundleChecks (runModelBundleChecks) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import Data.Either (isLeft, isRight)
import Data.List (sort)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Test.QuickCheck (Gen, Testable, arbitrary, forAll, isSuccess, maxSuccess, quickCheckWithResult, stdArgs)
import Yuho.Core.Source (validateSpan)
import Yuho.Core.Types (Source(..), Span(..))
import Yuho.ModelBundle.Json (digestBytes, digestDomain, parseCanonical)
import Yuho.ModelBundle.Types (Core(..), Failure(..), Scope(..))
import Yuho.ModelBundle.Validate (decodeCore, scopeDigest, validateCore)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField)

runModelBundleChecks :: FilePath -> IO ()
runModelBundleChecks fixtures = do
  let base = fixtures </> "bundles/MB01-minimal"
  manifestBytes <- BS.readFile (base </> "model-bundle.json")
  manifest <- case parseCanonical "/model-bundle.json" manifestBytes >>= decodeCore of
    Left problem -> print problem >> exitFailure
    Right value -> pure value
  modelBytes <- BS.readFile (base </> "artifacts/sha256" </> Text.unpack (coreModelDigest manifest))
  model <- case decodeJson modelBytes of
    Left problem -> print problem >> exitFailure
    Right value -> pure value
  check "model bundle executable inventory" (isRight (validateCore manifest model))
  check "model bundle exact source scope" (scopeSources (coreScope manifest) == ["src:main"])
  check "model bundle fixed domain separator" (digestDomain "yuho.model-bundle/v1" manifestBytes
    /= digestDomain "yuho.model-scope/v1" manifestBytes)
  check "model bundle rejects noncanonical input" (isLeft (parseCanonical "/x" (manifestBytes <> "\n")))
  check "model bundle rejects duplicate keys" (isLeft (parseCanonical "/x" "{\"a\":1,\"a\":2}"))
  let mappings = case lookupField "semantic_mappings" (coreRaw manifest) of
        Just (JArr (first:_)) -> replicate 8193 first
        _ -> []
      excessive = case coreRaw manifest of
        JObj fields -> JObj [(key, if key == "semantic_mappings" then JArr mappings else value)
          | (key, value) <- fields]
        other -> other
  check "model bundle mapping count before reference work"
    (either ((== "MBRES001") . failureCode) (const False) (decodeCore excessive))
  let unicodeBytes = Encoding.encodeUtf8 "A😀\r\nB"
      unicodeSource = Source "synthetic" "A😀\r\nB" unicodeBytes "unused"
  check "model bundle source span boundary"
    (validateSpan unicodeSource (Span 1 5 1 2 1 6)
      && not (validateSpan unicodeSource (Span 2 5 1 3 1 6)))
  property "bundle digest deterministic" $ forAll (arbitrary :: Gen Int) $ \n ->
    let bytes = encodeJson (JNum (toInteger n))
    in digestDomain "yuho.model-bundle/v1" bytes == digestDomain "yuho.model-bundle/v1" bytes
  property "bundle core change alters observed digest" $ forAll (arbitrary :: Gen Int) $ \n ->
    digestDomain "yuho.model-bundle/v1" (encodeJson (JNum (toInteger n)))
      /= digestDomain "yuho.model-bundle/v1" (encodeJson (JNum (toInteger n + 1)))
  property "canonical object key ordering" $ forAll (arbitrary :: Gen Int) $ \n ->
    encodeJson (JObj [("z", JNum (toInteger n)), ("a", JBool True)]) ==
      encodeJson (JObj [("a", JBool True), ("z", JNum (toInteger n))])
  property "source ordered arrays stay ordered" $ forAll (arbitrary :: Gen Int) $ \n ->
    let a = JNum (toInteger n); b = JNum (toInteger n + 1)
    in encodeJson (JArr [a,b]) /= encodeJson (JArr [b,a])
  property "no Unicode source normalization" $ forAll (arbitrary :: Gen Int) $ \n ->
    let suffix = Text.pack (show n)
    in digestBytes (Encoding.encodeUtf8 ("é" <> suffix))
      /= digestBytes (Encoding.encodeUtf8 ("e\x0301" <> suffix))
  property "no newline normalization" $ forAll (arbitrary :: Gen Int) $ \n ->
    let suffix = Text.pack (show n)
    in digestBytes (Encoding.encodeUtf8 ("a\r\n" <> suffix))
      /= digestBytes (Encoding.encodeUtf8 ("a\n" <> suffix))
  property "scope digest changes with scope content" $ forAll (arbitrary :: Gen Int) $ \n ->
    let first = manifest {coreScope = (coreScope manifest) {scopeRaw = JObj [("n", JNum (toInteger n))]}}
        second = manifest {coreScope = (coreScope manifest) {scopeRaw = JObj [("n", JNum (toInteger n + 1))]}}
    in scopeDigest first /= scopeDigest second
  property "canonical semantic scope order" $ forAll (arbitrary :: Gen Int) $ \n ->
    let ids = scopeIds (coreScope manifest)
        rotated = if odd n then reverse ids else ids
    in sort rotated == ids
  putStrLn "model bundle: pure properties passed"

check :: String -> Bool -> IO ()
check name condition = unless condition (putStrLn ("failed: " <> name) >> exitFailure)

property :: Testable prop => String -> prop -> IO ()
property name statement = do
  putStrLn name
  result <- quickCheckWithResult stdArgs {maxSuccess = 100} statement
  unless (isSuccess result) exitFailure
