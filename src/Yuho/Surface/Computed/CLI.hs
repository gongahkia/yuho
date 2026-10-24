{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Surface.Computed.CLI (runComputedCommand) where

import Control.Exception (IOException, evaluate, try)
import qualified Data.Aeson as J
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as T
import System.Exit (exitFailure)
import System.IO (stderr, stdout)
import System.Posix.Files (getSymbolicLinkStatus, isRegularFile, fileSize)
import Yuho.Surface.Dependency (dependencyInput)
import Yuho.Surface.Dependency.CLI (runDependencyCommand)
import Yuho.Surface.Publication (publishExport)
import qualified Yuho.Authoring as A
import Yuho.Protocol.Json (encodeJson)
import Yuho.Surface.Computed
import Yuho.Surface.Token

runComputedCommand :: [String] -> IO ()
runComputedCommand args = case args of
  _:path:_ -> do
    selected <- dependencyInput path
    if selected then runDependencyCommand args else runLegacyComputedCommand args
  _ -> runLegacyComputedCommand args

runLegacyComputedCommand :: [String] -> IO ()
runLegacyComputedCommand ["--help"] = BS.hPut stdout
  "usage: yuho compose check PROJECT.yh [--against ARTIFACT.json]; yuho compose run PROJECT.yh --output NEW_DIRECTORY; yuho compose replay ARTIFACT.json --output NEW_DIRECTORY\n"
runLegacyComputedCommand ["check",path] = do
  plan<-loadComposition path >>= require
  BS.hPut stdout (A.encodeRecord (compositionCheck plan) <> "\n")
runLegacyComputedCommand ["check",path,"--against",saved] = do
  plan<-loadComposition path >>= require
  previous<-readArtifact saved
  require (checkCompositionAttachment plan previous)
  BS.hPut stdout (A.encodeRecord (compositionCheck plan) <> "\n")
runLegacyComputedCommand ["run",path,"--output",out] = do
  plan<-loadComposition path >>= require
  evaluation<-require (executeComposition plan)
  export out evaluation
runLegacyComputedCommand ["replay",path,"--output",out] = do
  document<-readArtifact path
  evaluation<-requireSDK path (A.executeComputedInput document)
  export out evaluation
runLegacyComputedCommand _ = failAt "SFC001" "<command>" "expected compose check, run or replay; see yuho compose --help"

require :: Either Diagnostic a -> IO a
require = either (\e -> BS.hPut stderr (encodeJson (diagnosticJson e) <> "\n") >> exitFailure) pure
failAt :: Text -> FilePath -> Text -> IO a
failAt code path message = require (Left (Diagnostic code path (Token EndToken "" 1 1) message Nothing))
requireSDK :: FilePath -> Either [A.AuthoringDiagnostic] a -> IO a
requireSDK path = either (\es -> case es of
  e:_ -> failAt (A.diagnosticCode e) path (A.diagnosticMessage e <> "; " <> A.diagnosticLocation e <> "; " <> T.intercalate ", " (A.diagnosticObjects e))
  [] -> failAt "SFC009" path "SDK returned empty diagnostic failure") pure
readArtifact :: FilePath -> IO A.ComputedInputDocument
readArtifact path = do
  result<-try $ do
    stat<-getSymbolicLinkStatus path
    if isRegularFile stat && fileSize stat<=1048576
      then BS.readFile path else ioError (userError "unsafe artifact")
  bytes<-case result of
    Left (_ :: IOException) -> failAt "SFC005" path "artifact must be a regular non-symlink file of at most one MiB"
    Right value -> pure value
  requireSDK path (either (Left . (:[])) Right (A.decodeComputedInputDocument bytes))
export :: FilePath -> A.ComputedInputEvaluation -> IO ()
export out evaluation = do
  projection<-requireSDK out (A.projectComputedInput evaluation)
  view<-requireSDK out (A.computedInputReferenceView projection)
  json<-requireSDK out (A.encodeComputedInputViewJson projection view)
  xml<-requireSDK out (A.encodeComputedInputViewXml projection view)
  svg<-requireSDK out (A.encodeComputedInputViewSvg projection view)
  let document=A.computedEvaluationDocument evaluation
      report=A.computedInputReport evaluation
      files=[("artifact.json",A.encodeComputedInputDocument document),("report.json",A.encodeRecord report)
        ,("projection.json",A.encodeComputedProjection projection),("view-bindings.json",A.encodeRecord view)
        ,("view.json",json),("view.xml",xml),("view.svg",svg)
        ,("source-map.json",A.encodeRecord (compositionSourceMap document))]
  result<-try $ do
    -- Force every encoded byte before creating a staging directory. In particular,
    -- a lazy encoding failure must never occur after publication.
    mapM_ (evaluate . BS.length . snd) files
    publishExport out files
  case result of
    Left (issue :: IOException) -> failAt "SFC006" out
      ("could not publish complete output directory: " <> T.pack (show issue))
    Right () -> BS.hPut stdout (A.encodeRecord (J.object
      ["status" J..= ("evaluated" :: Text),"execution" J..= A.computedExecutionId report
      ,"output" J..= out,"replay_authority" J..= ("artifact.json retains exact sources and binding; replay does not read live .yh files" :: Text)]) <> "\n")
