module Main where
import qualified Data.ByteString as BS
import qualified Data.Aeson as A
import qualified Data.ByteString.Lazy.Char8 as BL
import System.Environment (getArgs)
import System.Exit (exitFailure)
import Yuho.Authoring.Dependency
main :: IO ()
main = do
  [path] <- getArgs
  bytes <- BS.readFile path
  case decodeDependencyDocument bytes >>= checkDependencyPlan of
    Left diagnostic -> BL.putStrLn (A.encode diagnostic) >> exitFailure
    Right _ -> fail "expected an invalid source-backed document"
