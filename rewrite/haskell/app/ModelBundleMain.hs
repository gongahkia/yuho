module Main (main) where

import qualified Data.ByteString as BS
import System.Environment (getArgs)
import System.Exit (ExitCode(..), exitWith)
import Yuho.ModelBundle.Run (runArgs)
import Yuho.Protocol.Json (encodeJson)

main :: IO ()
main = do
  args <- getArgs
  (code, result) <- runArgs args
  BS.putStr (encodeJson result <> BS.singleton 10)
  exitWith (if code == 0 then ExitSuccess else ExitFailure code)
