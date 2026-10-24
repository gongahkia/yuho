{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Yuho.Dependency.Codec where
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as T
import GHC.Generics (Generic)
import Yuho.Dependency.Types
import Yuho.Dependency.Check
import Yuho.Dependency.Run
import qualified Yuho.Protocol.Json as J

artifactFormat :: Text
artifactFormat="yuho.dependency-artifact/v0.1-experimental"
data DependencyArtifact = DependencyArtifact { artifactFormatVersion :: Text
  , artifactDocument :: DependencyDocument, artifactSourceDigest :: Text, artifactExecutionDigest :: Text }
  deriving (Eq,Show,Generic)
instance A.ToJSON DependencyArtifact where toJSON=A.genericToJSON options
instance A.FromJSON DependencyArtifact where parseJSON=A.genericParseJSON options

decodeDependencyDocument :: BS.ByteString -> Either DependencyDiagnostic DependencyDocument
decodeDependencyDocument=decodeClosed
encodeDependencyDocument :: DependencyDocument -> BS.ByteString
encodeDependencyDocument=encode

decodeClosed :: A.FromJSON a => BS.ByteString -> Either DependencyDiagnostic a
decodeClosed bytes=do
  ensure "DEPLIMIT" [] "encoded dependency input exceeds 8 MiB" (BS.length bytes<=8388608)
  _<-either (failure "DEPFORMAT" []) Right (J.decodeJsonBounded 8388608 bytes)
  either (failure "DEPFORMAT" [] . T.pack) Right (A.eitherDecodeStrict' bytes)

saveDependencyArtifact :: DependencyExecution -> DependencyArtifact
saveDependencyArtifact e=DependencyArtifact artifactFormat (checkedDocument (executionPlan e))
  (checkedDigest (executionPlan e)) (dependencyExecutionId e)
encodeDependencyArtifact :: DependencyArtifact -> BS.ByteString
encodeDependencyArtifact=encode
decodeDependencyArtifact :: BS.ByteString -> Either DependencyDiagnostic DependencyArtifact
decodeDependencyArtifact bytes=decodeClosed bytes >>= \a->checkDependencyArtifact a >> pure a
checkDependencyArtifact :: DependencyArtifact -> Either DependencyDiagnostic CheckedPlan
checkDependencyArtifact a=do
  ensure "DEPFORMAT" [] "unsupported dependency artifact version" (artifactFormatVersion a==artifactFormat)
  ensure "DEPFORMAT" [] "artifact digests must be complete lowercase SHA-256 values"
    (all (\x->T.length x==64 && T.all (`elem` ("0123456789abcdef"::String)) x) [artifactSourceDigest a,artifactExecutionDigest a])
  plan<-checkDependencyPlan (artifactDocument a)
  ensure "DEPSTALE" [] "artifact exact-source digest does not match its retained plan/bundle" (checkedDigest plan==artifactSourceDigest a)
  pure plan
replayDependencyPlan :: DependencyArtifact -> Either DependencyDiagnostic DependencyExecution
replayDependencyPlan a=do
  p<-checkDependencyArtifact a
  e<-executeDependencyPlan p
  ensure "DEPSTALE" [] "replayed execution differs from the saved immutable execution" (dependencyExecutionId e==artifactExecutionDigest a)
  pure e
checkDependencyAttachment :: CheckedPlan -> DependencyArtifact -> Either DependencyDiagnostic ()
checkDependencyAttachment p a=do
  _<-checkDependencyArtifact a
  ensure "DEPSTALE" [] "live plan/source attachment changed (including same-status revisions)" (checkedDigest p==artifactSourceDigest a)
