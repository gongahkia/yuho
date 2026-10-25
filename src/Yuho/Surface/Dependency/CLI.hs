{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Surface.Dependency.CLI
  (runDependencyCommand, DependencyInputKind(..), dependencyOperation) where
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

-- The declared authority selects the loader, not a Boolean accepting either
-- representation. Both public entrances share these exact operations.
data DependencyInputKind = CurrentDependencySource | SavedDependencyArtifact

dependencyOperation :: DependencyInputKind -> Text -> FilePath -> Maybe FilePath
  -> Maybe FilePath -> IO (Either DependencyDiagnostic A.Value)
dependencyOperation kind op path output against=case (kind,op,output,against) of
  (CurrentDependencySource,"check",Nothing,attachment)->do
    loaded<-loadDependencyProject path
    case (loaded,attachment) of
      (Left d,_)->pure (Left d)
      (Right p,Nothing)->pure (Right (checkedPayload p))
      (Right p,Just saved)->do
        artifact<-readArtifact saved
        pure (artifact >>= \a->checkDependencyAttachment p a >> pure (checkedPayload p))
  (CurrentDependencySource,"run",Just out,Nothing)->do
    loaded<-loadDependencyProject path
    finish out (loaded >>= executeDependencyPlan)
  (SavedDependencyArtifact,"check",Nothing,Nothing)->do
    artifact<-readArtifact path
    pure (checkedPayload <$> (artifact >>= checkDependencyArtifact))
  (SavedDependencyArtifact,"replay",Just out,Nothing)->do
    artifact<-readArtifact path
    finish out (artifact >>= replayDependencyPlan)
  _->pure (failure "DEPFORMAT" [] "unsupported dependency input-kind/operation/argument combination")
 where
  finish _ (Left d)=pure (Left d)
  finish out (Right e)=do
    published<-publishDependencyPlan out e
    pure (executionPayload out e <$ published)

runDependencyCommand :: [String] -> IO ()
runDependencyCommand args=do
  result<-case args of
    ["check",path]->do
      isArtifact<-artifactInput path
      dependencyOperation (if isArtifact then SavedDependencyArtifact else CurrentDependencySource) "check" path Nothing Nothing
    ["check",path,"--against",saved]->dependencyOperation CurrentDependencySource "check" path Nothing (Just saved)
    ["run",path,"--output",out]->dependencyOperation CurrentDependencySource "run" path (Just out) Nothing
    ["replay",path,"--output",out]->dependencyOperation SavedDependencyArtifact "replay" path (Just out) Nothing
    _->pure (failure "DEPFORMAT" [] "expected compose check PROJECT [--against ARTIFACT], run PROJECT --output NEW_DIRECTORY, or replay ARTIFACT --output NEW_DIRECTORY")
  require result >>= \payload->BS.hPut stdout (encode payload<>"\n")

checkedPayload :: CheckedPlan -> A.Value
checkedPayload p=A.object ["format" A..= planFormat,"status" A..= ("checked"::Text)
  ,"evaluated" A..= False,"snapshot" A..= checkedDigest p,"order" A..= checkedOrder p
  ,"expanded_cost" A..= checkedCost p,"profile" A..= ("TypedFiniteRules-v1"::Text)]
readArtifact :: FilePath -> IO (Either DependencyDiagnostic DependencyArtifact)
readArtifact path=do
  result<-fmap (>>=decodeDependencyArtifact) (readBytes path)
  pure $ case result of
    Left d->Left d {dependencyMessage="expected a saved dependency artifact: "<>dependencyMessage d}
    Right a->Right a
readBytes :: FilePath -> IO (Either DependencyDiagnostic BS.ByteString)
readBytes path=do
  result<-try $ do
    s<-getSymbolicLinkStatus path
    if isRegularFile s && fileSize s<=8388608 then do
      bytes<-BS.readFile path
      if BS.length bytes<=8388608 then pure bytes else ioError (userError "dependency artifact exceeds 8 MiB")
    else ioError (userError "expected regular non-symlink dependency artifact <=8 MiB")
  pure $ case result of
    Left (e::IOException)->failure "DEPFORMAT" [] (T.pack (show e))
    Right b->Right b
artifactInput :: FilePath -> IO Bool
artifactInput path=do
  bytes<-readBytes path >>= require
  pure $ case A.eitherDecodeStrict' bytes of Right (A.Object _)->True;_->False
executionPayload :: FilePath -> DependencyExecution -> A.Value
executionPayload out e=A.object ["format" A..= reportFormat,"status" A..= ("evaluated"::Text)
  ,"profile" A..= ("TypedFiniteRules-v1"::Text),"execution" A..= dependencyExecutionId e,"output" A..= out
  ,"replay_authority" A..= ("exact embedded dependency plan and sources; no live source IO during replay"::Text)]
