{-# LANGUAGE OverloadedStrings #-}
module ConformanceChecks (runConformanceChecks) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import qualified Data.Text as Text
import qualified Data.Text.Encoding as TextEncoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.CoreYuho.Conformance (evaluateConformanceBytes)
import Yuho.Protocol.Json (arrayValue, decodeJson, lookupField)

runConformanceChecks :: FilePath -> IO ()
runConformanceChecks root = do
  let directory = root </> "mechanisation/conformance"
      vectorPath = directory </> "core-yuho-v0.1.json"
      resultPath = directory </> "core-yuho-v0.1.haskell.json"
  vectors <- BS.readFile vectorPath
  retained <- BS.readFile resultPath
  first <- either (failed . show) pure (evaluateConformanceBytes vectors)
  second <- either (failed . show) pure (evaluateConformanceBytes vectors)
  check "conformance evaluation is deterministic" (first == second)
  check "retained Haskell conformance output" (first == retained)
  vectorCount <- countRows "vectors" vectors
  resultCount <- countRows "results" first
  check "conformance vector count" (vectorCount == 95 && resultCount == vectorCount)
  check "real normalized fixture origins retained"
    (all (`BS.isInfixOf` vectors) (map TextEncoding.encodeUtf8
      [ "research/singapore/research-release/scenarios/rash-endangerment/01_satisfied_primary.yh"
      , "research/singapore/models/section84-explicit-attachments.yh"
      ]))
  check "unsupported schema fails closed" $ case evaluateConformanceBytes
    "{\"schema\":\"unknown\",\"vectors\":[]}" of
      Left _ -> True
      Right _ -> False
  check "unsupported vector kind fails closed" $ case evaluateConformanceBytes
    "{\"schema\":\"yuho.core-conformance-v0.1\",\"vectors\":[{\"id\":\"bad\",\"kind\":\"unknown\"}]}" of
      Left _ -> True
      Right _ -> False
  putStrLn "core conformance: schema, 95 vectors, determinism and refusals passed"

countRows :: String -> BS.ByteString -> IO Int
countRows field bytes = case decodeJson bytes >>= maybe
    (Left "missing rows") Right . (>>= arrayValue) . lookupField (Text.pack field) of
  Left issue -> failed (show issue)
  Right rows -> pure (length rows)

check :: String -> Bool -> IO ()
check label value = unless value (failed label)

failed :: String -> IO a
failed label = putStrLn ("core conformance failed: " <> label) >> exitFailure
