{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE CPP #-}
{-# LANGUAGE ForeignFunctionInterface #-}
module Yuho.Surface.Computed.CLI (runComputedCommand) where

import Control.Exception (IOException, bracketOnError, evaluate, try)
import Control.Monad (when)
import qualified Data.Aeson as J
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as T
import System.Directory (makeAbsolute, removeDirectoryRecursive)
import System.Exit (exitFailure)
import System.FilePath ((</>), takeDirectory, takeFileName, splitDirectories)
import System.IO (stderr, stdout)
import System.Posix.Files (getSymbolicLinkStatus, isRegularFile, isDirectory, fileSize)
import System.Posix.Temp (mkdtemp)
import System.IO.Error (isDoesNotExistError)
#if defined(linux_HOST_OS)
import Foreign.C.String (CString, withCString)
import Foreign.C.Types (CInt(..), CUInt(..))
import Foreign.C.Error (throwErrnoIfMinus1_)
#endif
import qualified Yuho.Authoring as A
import Yuho.Protocol.Json (encodeJson)
import Yuho.Surface.Computed
import Yuho.Surface.Token

runComputedCommand :: [String] -> IO ()
runComputedCommand ["--help"] = BS.hPut stdout
  "usage: yuho compose check PROJECT.yh [--against ARTIFACT.json]; yuho compose run PROJECT.yh --output NEW_DIRECTORY; yuho compose replay ARTIFACT.json --output NEW_DIRECTORY\n"
runComputedCommand ["check",path] = do
  plan<-loadComposition path >>= require
  BS.hPut stdout (A.encodeRecord (compositionCheck plan) <> "\n")
runComputedCommand ["check",path,"--against",saved] = do
  plan<-loadComposition path >>= require
  previous<-readArtifact saved
  require (checkCompositionAttachment plan previous)
  BS.hPut stdout (A.encodeRecord (compositionCheck plan) <> "\n")
runComputedCommand ["run",path,"--output",out] = do
  plan<-loadComposition path >>= require
  evaluation<-require (executeComposition plan)
  export out evaluation
runComputedCommand ["replay",path,"--output",out] = do
  document<-readArtifact path
  evaluation<-requireSDK path (A.executeComputedInput document)
  export out evaluation
runComputedCommand _ = failAt "SFC001" "<command>" "expected compose check, run or replay; see yuho compose --help"

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

-- Linux renameat2(RENAME_NOREPLACE) publishes the completed directory in one
-- filesystem operation and refuses *any* existing destination, including an empty
-- directory or a dangling link. There is deliberately no check-then-rename fallback.
-- This is atomic visibility/no-clobber, not a power-loss durability guarantee.
publishExport :: FilePath -> [(FilePath,BS.ByteString)] -> IO ()
publishExport out files = do
  when (null out || takeFileName out `elem` ["", ".", ".."]
        || ".." `elem` splitDirectories out)
    (ioError (userError "output must name a new directory without parent traversal"))
  destination <- makeAbsolute out
  let parent = takeDirectory destination
  checkParents parent
  existing <- try (getSymbolicLinkStatus destination)
  case existing of
    Right _ -> ioError (userError "output destination already exists; use a new directory")
    Left issue | isDoesNotExistError issue -> pure ()
               | otherwise -> ioError issue
  bracketOnError (mkdtemp (parent </> ".yuho-compose-")) removeDirectoryRecursive $ \staging -> do
    mapM_ (\(name,bytes) -> BS.writeFile (staging </> name) bytes) files
    publishNoReplace staging destination
  where
    checkParents path = do
      stat <- getSymbolicLinkStatus path
      when (not (isDirectory stat))
        (ioError (userError "output parent and ancestors must be real directories, not links"))
      let parent = takeDirectory path
      when (parent /= path) (checkParents parent)

publishNoReplace :: FilePath -> FilePath -> IO ()
#if defined(linux_HOST_OS)
publishNoReplace source destination = withCString source $ \src ->
  withCString destination $ \dst ->
    throwErrnoIfMinus1_ "renameat2(RENAME_NOREPLACE)" (renameNoReplace (-100) src (-100) dst 1)

foreign import ccall unsafe "renameat2"
  renameNoReplace :: CInt -> CString -> CInt -> CString -> CUInt -> IO CInt
#else
publishNoReplace _ _ = ioError (userError
  "atomic no-replace directory publication is unsupported on this platform; no output published")
#endif
