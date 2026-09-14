{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.CLI (main) where

import Control.Exception (IOException, finally, try)
import qualified Data.ByteString as BS
import Data.Text (Text)
import System.Directory (doesDirectoryExist, removeFile)
import System.Environment (getArgs)
import System.Exit (exitFailure)
import System.FilePath (takeDirectory)
import System.IO (hClose, openBinaryTempFile, stderr, stdout)
import System.Posix.Files (createLink, fileSize, getSymbolicLinkStatus, isRegularFile)
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (decodeJson, encodeJson, lookupField, textValue)
import Yuho.Surface.Compile (checkSource, compileSource)
import Yuho.Surface.Token (Diagnostic(..), Kind(..), Token(..), diagnosticJson)

data Command = Check | Compile | Run deriving (Eq)
data Options = Options Command FilePath (Maybe FilePath) (Maybe FilePath)

main :: IO ()
main = do
  arguments <- getArgs
  case options arguments of
    Left message -> report (Diagnostic "SFE001" "<command>" origin message)
    Right selected -> operate selected
  where origin = Token EndToken "" 1 1

options :: [String] -> Either Text Options
options arguments = case arguments of
  command:path:rest -> do
    operation <- case command of
      "check" -> Right Check
      "compile" -> Right Compile
      "run" -> Right Run
      _ -> Left "expected check, compile or run"
    (scenario, output) <- flags rest Nothing Nothing
    if operation /= Compile && output /= Nothing
      then Left "--output applies only to compile"
      else Right (Options operation path scenario output)
  _ -> Left "usage: yuho check|compile|run <source.yh> [--scenario <path>] [--output <path>]"
  where
    flags [] scenario output = Right (scenario, output)
    flags ("--scenario":path:rest) Nothing output = flags rest (Just path) output
    flags ("--output":path:rest) scenario Nothing = flags rest scenario (Just path)
    flags _ _ _ = Left "unknown or duplicate option"

readSource :: FilePath -> IO (Either Diagnostic BS.ByteString)
readSource path = do
  result <- try $ do
    status <- getSymbolicLinkStatus path
    if not (isRegularFile status) || fileSize status > 65536
      then ioError (userError "source must be a regular file at most 65536 bytes")
      else BS.readFile path
  pure $ case result of
    Left (_ :: IOException) -> Left (Diagnostic "SFE015" path origin "source unavailable, unsafe or too large")
    Right bytes -> Right bytes
  where origin = Token EndToken "" 1 1

operate :: Options -> IO ()
operate (Options command path scenarioPath output) = do
  source <- readSource path
  scenario <- traverse (\item -> do
    result <- readSource item
    pure ((,) item <$> result)) scenarioPath
  case (source, scenario) of
    (Left issue, _) -> report issue
    (_, Just (Left issue)) -> report issue
    (Right bytes, other) -> do
      let supplied = case other of
            Just (Right item) -> Just item
            _ -> Nothing
          compiled = compileSource path bytes supplied
      case command of
        Check -> case checkSource path bytes supplied of
          Left issue -> report issue
          Right _ -> BS.hPut stdout "{\"status\":\"valid\"}\n"
        Compile -> case compiled of
          Left issue -> report issue
          Right request -> case output of
            Nothing -> BS.hPut stdout request
            Just destination -> publish destination request
        Run -> case compiled of
          Left issue -> report issue
          Right request -> do
            let response = runLine request
            case decodeJson response of
              Right value | (lookupField "status" value >>= textValue) /= Just "rejected" ->
                BS.hPut stdout response
              _ -> report (Diagnostic "SFE014" path (Token EndToken "" 1 1)
                "compiled request was rejected by the Haskell kernel")

publish :: FilePath -> BS.ByteString -> IO ()
publish destination bytes = do
  parentExists <- doesDirectoryExist (takeDirectory destination)
  if not parentExists
    then report (Diagnostic "SFE015" destination origin "output parent does not exist")
    else do
      result <- try $ do
        (temporary, handle) <- openBinaryTempFile (takeDirectory destination) ".yuho-compile-"
        (do BS.hPut handle bytes
            hClose handle
            createLink temporary destination) `finally` do
              _ <- try (hClose handle) :: IO (Either IOException ())
              removeFile temporary
      case result of
        Left (_ :: IOException) -> report (Diagnostic "SFE015" destination origin "output is unsafe or already exists")
        Right () -> pure ()
  where origin = Token EndToken "" 1 1

report :: Diagnostic -> IO a
report issue = do
  BS.hPut stderr (encodeJson (diagnosticJson issue) <> "\n")
  exitFailure
