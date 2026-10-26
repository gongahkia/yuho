{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Yuho.Dependency.Codec where
import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as AM
import qualified Data.Aeson.Key as AK
import qualified Data.Map.Strict as M
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as T
import GHC.Generics (Generic)
import Yuho.Dependency.Types
import Yuho.Dependency.Check
import Yuho.Dependency.Run
import qualified Yuho.Quantitative as Q
import qualified Yuho.Protocol.Json as J

artifactFormat :: Text
artifactFormat="yuho.dependency-artifact/v0.1-experimental"
quantitativeArtifactFormat :: Text
quantitativeArtifactFormat="yuho.dependency-artifact/v0.2-quantitative-experimental"
data DependencyArtifact = DependencyArtifact { artifactFormatVersion :: Text
  , artifactDocument :: DependencyDocument, artifactSourceDigest :: Text, artifactExecutionDigest :: Text
  , artifactQuantitativeReport :: Maybe A.Value }
  deriving (Eq,Show,Generic)
instance A.ToJSON DependencyArtifact where
  toJSON a=case A.genericToJSON options a of
    A.Object o | artifactQuantitativeReport a==Nothing->A.Object (AM.delete "artifactQuantitativeReport" o)
    v->v
instance A.FromJSON DependencyArtifact where
  parseJSON=A.withObject "DependencyArtifact" $ \o->do
    version<-o A..: "artifactFormatVersion"
    let allowed=["artifactFormatVersion","artifactDocument","artifactSourceDigest","artifactExecutionDigest"]
          ++["artifactQuantitativeReport" | version==quantitativeArtifactFormat]
    if all ((`elem` allowed) . AK.toText) (AM.keys o)
      then A.genericParseJSON options (A.Object o)
      else fail "unknown field for this exact artifact version"

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
saveDependencyArtifact e=DependencyArtifact (if quantified then quantitativeArtifactFormat else artifactFormat) (checkedDocument (executionPlan e))
  (checkedDigest (executionPlan e)) (dependencyExecutionId e) (if quantified then Just (reportDependencyPlan e) else Nothing)
 where quantified=any ((/=Nothing) . checkedQuantitative) (M.elems (checkedComponents (executionPlan e)))
encodeDependencyArtifact :: DependencyArtifact -> BS.ByteString
encodeDependencyArtifact=encode
decodeDependencyArtifact :: BS.ByteString -> Either DependencyDiagnostic DependencyArtifact
decodeDependencyArtifact bytes=decodeClosed bytes >>= \a->checkDependencyArtifact a >> pure a
checkDependencyArtifact :: DependencyArtifact -> Either DependencyDiagnostic CheckedPlan
checkDependencyArtifact a=do
  ensure "DEPFORMAT" [] "unsupported dependency artifact version/report combination"
    ((artifactFormatVersion a==artifactFormat && artifactQuantitativeReport a==Nothing)
      || (artifactFormatVersion a==quantitativeArtifactFormat && artifactQuantitativeReport a/=Nothing))
  ensure "DEPFORMAT" [] "artifact digests must be complete lowercase SHA-256 values"
    (all (\x->T.length x==64 && T.all (`elem` ("0123456789abcdef"::String)) x) [artifactSourceDigest a,artifactExecutionDigest a])
  plan<-checkDependencyPlan (artifactDocument a)
  let quantified=any ((/=Nothing) . checkedQuantitative) (M.elems (checkedComponents plan))
  ensure "DEPFORMAT" [] "quantitative sources require their explicit artifact version"
    ((artifactFormatVersion a==quantitativeArtifactFormat)==quantified)
  ensure "DEPSTALE" [] "artifact exact-source digest does not match its retained plan/bundle" (checkedDigest plan==artifactSourceDigest a)
  case artifactQuantitativeReport a of
    Just (A.Object report)->ensure "DEPSTALE" [] "saved quantitative report attachment differs from its source/execution digests"
      (AM.lookup "format" report==Just (A.String reportFormat)
        && AM.lookup "execution" report==Just (A.String (artifactExecutionDigest a))
        && AM.lookup "plan_snapshot" report==Just (A.String (artifactSourceDigest a))
        && validQuantitativeReport plan report)
    Just _->failure "DEPFORMAT" [] "quantitative artifact requires an object report"
    Nothing->pure ()
  pure plan

-- Static shape/authority validation deliberately does not recompute arithmetic.
-- The complete saved observation values are compared by immutable replay.
validQuantitativeReport :: CheckedPlan -> A.Object -> Bool
validQuantitativeReport plan report=case AM.lookup "quantitative" report of
  Just (A.Object q)->AM.lookup "format" q==Just (A.String Q.quantitativeFormat)
    && case AM.lookup "occurrences" q of
      Just (A.Array occurrences)->
        let names=[n | A.Object o<-foldr (:) [] occurrences,Just (A.String n)<-[AM.lookup "component" o]]
        in length occurrences==M.size expected
          && all validOccurrence occurrences
          && length names==M.size (M.fromList [(n,()) | n<-names])
      _->False
  _->False
 where
  expected=M.filter ((/=Nothing) . checkedQuantitative) (checkedComponents plan)
  validOccurrence (A.Object o)=case AM.lookup "component" o of
    Just (A.String name)->case M.lookup name expected of
      Just component | Just checked<-checkedQuantitative component->
        AM.lookup "checked_plan" o==Just (A.toJSON checked)
        && AM.lookup "scope" o==Just (A.toJSON (checkedScope component))
        && case AM.lookup "actual" o of
          Just A.Null->AM.lookup "evaluation" o==Just (A.String "not_evaluated")
          Just (A.Object actual)->AM.lookup "format" actual==Just (A.String Q.quantitativeFormat)
            && AM.lookup "evaluation" o==Just (A.String "evaluated")
            && AM.lookup "evaluation" actual==Just (A.String "evaluated")
            && AM.lookup "plan" actual==Just (A.toJSON checked)
            && (case AM.lookup "values" actual of Just (A.Object _)->True;_->False)
            && (case AM.lookup "steps" actual of Just (A.Array _)->True;_->False)
          _->False
      _->False
    _->False
  validOccurrence _=False
replayDependencyPlan :: DependencyArtifact -> Either DependencyDiagnostic DependencyExecution
replayDependencyPlan a=do
  p<-checkDependencyArtifact a
  e<-executeDependencyPlan p
  ensure "DEPSTALE" [] "replayed execution differs from the saved immutable execution" (dependencyExecutionId e==artifactExecutionDigest a)
  case artifactQuantitativeReport a of
    Nothing->pure ()
    Just saved->ensure "DEPSTALE" [] "saved quantitative report differs from immutable recomputation" (saved==reportDependencyPlan e)
  pure e
checkDependencyAttachment :: CheckedPlan -> DependencyArtifact -> Either DependencyDiagnostic ()
checkDependencyAttachment p a=do
  _<-checkDependencyArtifact a
  ensure "DEPSTALE" [] "live plan/source attachment changed (including same-status revisions)" (checkedDigest p==artifactSourceDigest a)
