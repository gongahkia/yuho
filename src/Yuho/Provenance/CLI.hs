{-# LANGUAGE OverloadedStrings #-}
module Yuho.Provenance.CLI (runProvenance,provenanceOperation) where
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Map.Strict as M
import qualified Data.Text as T
import System.Exit (exitFailure)
import System.IO (stdout,stderr)
import Yuho.Dependency.Types
import Yuho.Dependency.Check (failure,ensure,checkedDigest,checkedComponents,checkedQuantitative,encode)
import Yuho.Dependency.Run
import Yuho.Dependency.Codec
import Yuho.Surface.Dependency (loadDependencyProject)
import Yuho.Surface.Dependency.CLI (DependencyInputKind(..),readArtifact)
import Yuho.Provenance.Build
import Yuho.Provenance.Types
import Yuho.Provenance.View

provenanceOperation :: DependencyInputKind -> Text -> FilePath -> Maybe FilePath -> Maybe Text
  -> IO (Either DependencyDiagnostic A.Value)
provenanceOperation kind op path output target=case (kind,op,output,target) of
  (CurrentDependencySource,"inspect",Nothing,Nothing)->do
    loaded<-loadDependencyProject path
    pure (A.toJSON <$> (loaded >>= projectStaticProvenance))
  (SavedDependencyArtifact,"inspect",Nothing,Nothing)->do
    saved<-readArtifact path
    pure (A.toJSON <$> (saved >>= checkDependencyArtifact >>= projectStaticProvenance))
  (_,"trace",Nothing,Nothing)->loadExecution >>= pure . (>>= fmap A.toJSON . projectTypedProvenance)
  (_,"explain",Nothing,Just focus)->loadExecution >>= pure . (>>= (\e->projectTypedProvenance e >>= \p->explainProvenance p focus))
  (CurrentDependencySource,"provenance",Just out,_)->do
    loaded<-loadDependencyProject path
    finish out "current_sources" (loaded >>= executeDependencyPlan)
  (SavedDependencyArtifact,"provenance",Just out,_)->do
    saved<-readArtifact path
    finish out "embedded_artifact" (saved >>= replayDependencyPlan)
  _->pure (failure "PVREQUEST" [] "expected inspect without focus/output, or provenance with new output directory and optional exact focus identity")
 where
  loadExecution=case kind of
    CurrentDependencySource->fmap (>>=executeDependencyPlan) (loadDependencyProject path)
    SavedDependencyArtifact->fmap (>>=replayDependencyPlan) (readArtifact path)
  finish :: FilePath -> Text -> Either DependencyDiagnostic DependencyExecution -> IO (Either DependencyDiagnostic A.Value)
  finish _ _ (Left d)=pure (Left d)
  finish out authority' (Right execution)=case do
      projection<-projectTypedProvenance execution
      files<-exportTypedProvenance projection target
      let artifact=encodeDependencyArtifact (saveDependencyArtifact execution)
          complete=("artifact.json",artifact):files
      ensure "PVLIMIT" [] "saved artifact exceeds the 8 MiB replay input bound" (BS.length artifact<=8388608)
      ensure "PVLIMIT" [] "complete publication exceeds 32 MiB" (sum (map (BS.length . snd) complete)<=33554432)
      pure (projection,complete) of
    Left d->pure (Left d)
    Right (projection,files)->do
      published<-publishTypedProvenance out files
      pure (A.object ["format" A..= provenanceFormat,"profile" A..= ("TypedFiniteRules-v1"::Text),"profiles" A..= (["TypedFiniteRules-v1"]++["ExactQuantities-v1" | any ((/=Nothing) . checkedQuantitative) (M.elems (checkedComponents (executionPlan execution)))]::[Text])
        ,"projection" A..= projectionIdentity projection,"execution" A..= dependencyExecutionId execution
        ,"source_authority" A..= authority',"evaluated" A..= True,"output" A..= out
        ,"snapshot" A..= checkedDigest (executionPlan execution)] <$ published)

runProvenance :: [String] -> IO ()
runProvenance args=do
  result<-case args of
    ["trace",path]->provenanceOperation CurrentDependencySource "trace" path Nothing Nothing
    ["trace-artifact",path]->provenanceOperation SavedDependencyArtifact "trace" path Nothing Nothing
    ["explain",path,"--focus",focus]->provenanceOperation SavedDependencyArtifact "explain" path Nothing (Just (T.pack focus))
    ["inspect",path]->provenanceOperation CurrentDependencySource "inspect" path Nothing Nothing
    ["inspect-artifact",path]->provenanceOperation SavedDependencyArtifact "inspect" path Nothing Nothing
    op:path:rest | op `elem` ["run","replay"]->case flags rest Nothing Nothing of
      Left d->pure (Left d)
      Right (out,target)->provenanceOperation (if op=="run" then CurrentDependencySource else SavedDependencyArtifact) "provenance" path out target
    _->pure (failure "PVREQUEST" [] "usage: yuho provenance inspect PROJECT | inspect-artifact ARTIFACT | trace PROJECT | trace-artifact ARTIFACT | explain ARTIFACT --focus ID | run PROJECT --output NEW_DIRECTORY [--focus ID] | replay ARTIFACT --output NEW_DIRECTORY [--focus ID]")
  case result of
    Left d->BS.hPut stderr (encode d<>"\n")>>exitFailure
    Right value->BS.hPut stdout (encode value<>"\n")
 where
  flags [] out target=Right (out,target)
  flags ("--output":out:rest) Nothing target=flags rest (Just out) target
  flags ("--focus":target:rest) out Nothing=flags rest out (Just (T.pack target))
  flags _ _ _=failure "PVREQUEST" [] "unknown or duplicate provenance option"
