{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Surface.Dependency.CLI (runDependencyCommand) where
import Control.Exception (IOException, try)
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as T
import System.Exit (exitFailure)
import System.IO (stdout,stderr)
import System.Posix.Files (getSymbolicLinkStatus,isRegularFile,fileSize)
import Yuho.Dependency.Types
import Yuho.Dependency.Check
import Yuho.Dependency.Run
import Yuho.Dependency.Codec
import Yuho.Surface.Dependency (loadDependencyProject)
import Yuho.Dependency.Publication (publishDependencyPlan)

require :: Either DependencyDiagnostic a -> IO a
require=either (\e->BS.hPut stderr (encode e<>"\n")>>exitFailure) pure
runDependencyCommand :: [String] -> IO ()
runDependencyCommand ["check",path]=do
  isArtifact<-artifactInput path
  p<-if isArtifact then readArtifact path >>= require . checkDependencyArtifact else loadDependencyProject path >>= require
  checked p
runDependencyCommand ["check",path,"--against",saved]=do
  p<-loadDependencyProject path >>= require
  a<-readArtifact saved
  require (checkDependencyAttachment p a)
  checked p
runDependencyCommand ["run",path,"--output",out]=do
  p<-loadDependencyProject path >>= require
  require (executeDependencyPlan p) >>= publish out
runDependencyCommand ["replay",path,"--output",out]=readArtifact path >>= require . replayDependencyPlan >>= publish out
runDependencyCommand _=require (failure "DEPFORMAT" [] "expected compose check PROJECT [--against ARTIFACT], run PROJECT --output NEW_DIRECTORY, or replay ARTIFACT --output NEW_DIRECTORY")

checked :: CheckedPlan -> IO ()
checked p=BS.hPut stdout (encode (A.object ["format" A..= planFormat,"status" A..= ("checked"::Text)
  ,"evaluated" A..= False,"snapshot" A..= checkedDigest p,"order" A..= checkedOrder p
  ,"expanded_cost" A..= checkedCost p,"profile" A..= ("TypedFiniteRules-v1"::Text)])<>"\n")
readArtifact :: FilePath -> IO DependencyArtifact
readArtifact path=readBytes path >>= require . decodeDependencyArtifact
readBytes :: FilePath -> IO BS.ByteString
readBytes path=do
  result<-try $ do
    s<-getSymbolicLinkStatus path
    if isRegularFile s && fileSize s<=8388608 then BS.readFile path else ioError (userError "expected regular non-symlink dependency artifact <=8 MiB")
  case result of
    Left (e::IOException)->require (failure "DEPFORMAT" [] (T.pack (show e)))
    Right b->pure b
artifactInput :: FilePath -> IO Bool
artifactInput path=do
  bytes<-readBytes path
  pure $ case A.eitherDecodeStrict' bytes of Right (A.Object _)->True;_->False
publish :: FilePath -> DependencyExecution -> IO ()
publish out e=do
  publishDependencyPlan out e >>= require
  BS.hPut stdout (encode (A.object ["format" A..= reportFormat,"status" A..= ("evaluated"::Text)
    ,"profile" A..= ("TypedFiniteRules-v1"::Text),"execution" A..= dependencyExecutionId e,"output" A..= out
    ,"replay_authority" A..= ("exact embedded dependency plan and sources; no live source IO during replay"::Text)])<>"\n")
