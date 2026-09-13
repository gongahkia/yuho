module Main (main) where

import qualified Data.ByteString as BS
import System.Environment (getArgs)
import System.Exit (ExitCode(..), exitWith)
import System.IO (stderr)
import Yuho.ModelBundle.Diff (diagnosticsJson, runDiff)
import Yuho.ModelBundle.Run (runArgs)
import Yuho.Protocol.Json (encodeJson)

main :: IO ()
main = do
  args <- getArgs
  case args of
    "diff" : _ -> do
      (code, result, failures) <- runDiff args
      case result of
        Just report -> BS.putStr (encodeJson report <> BS.singleton 10)
        Nothing -> BS.hPutStr stderr (encodeJson (diagnosticsJson failures) <> BS.singleton 10)
      exitWith (if code == 0 then ExitSuccess else ExitFailure code)
    _ -> do
      (code, result) <- runArgs args
      BS.putStr (encodeJson result <> BS.singleton 10)
      exitWith (if code == 0 then ExitSuccess else ExitFailure code)
