{-# LANGUAGE OverloadedStrings #-}
-- | Recover retained source references in an explicit component namespace.
-- Recovery is not a claim that the quotation proves a technical/legal result.
module Yuho.Dependency.Source (dependencyComponentSources,recoverDependencyReference,dependencyOriginRecord) where
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as M
import qualified Data.Set as S
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as U
import System.FilePath ((</>),takeDirectory,normalise)
import qualified Yuho.Authoring.Types as A
import qualified Yuho.Authoring.Source as A
import qualified Yuho.Authoring.Typed as A
import Yuho.Dependency.Types
import Yuho.Dependency.Check
import Yuho.Dependency.Run (DependencyExecution(..))
import Yuho.Surface.TypedFinite (dependencySourcePaths)

dependencyComponentSources :: DependencyExecution -> Text -> Either DependencyDiagnostic [A.SourceRecord]
dependencyComponentSources execution key=do
  c<-maybe (failure "DEPNAME" [key] "unknown source component namespace") Right (M.lookup key (checkedComponents plan))
  sources<-case (componentProfile (checkedComponent c),componentTemplate (checkedComponent c)) of
    ("sdk-typed-v0.3",_)->do
      text<-source (componentModel (checkedComponent c))
      d<-either (failure "DEPFORMAT" [key] . A.diagnosticMessage) Right (A.decodeTypedDocument (U.encodeUtf8 text))
      pure (A.typedOriginalSources d)
    (_,Just _)->pure [] -- In-memory template authority is the authored structured record, not an invented text file.
    _->do
      let declaration=checkedComponent c
          files=componentModel declaration:maybe [] (:[]) (componentScenario declaration)
            ++maybe [] (:[]) (dependencyProjectSource doc)
      paths<-closure S.empty files
      traverse (\path->A.SourceRecord (T.pack path) "dependency-authored-source" (Just (T.pack path)) . Just <$> source path) (S.toAscList paths)
  pure sources
 where
  plan=executionPlan execution;doc=checkedDocument plan
  source path=maybe (failure "DEPMISSING" [T.pack path] "source absent from immutable bundle") Right (M.lookup (normalise path) (dependencySources doc))
  closure seen []=Right seen
  closure seen (path:rest)
    | path `S.member` seen=closure seen rest
    | otherwise=do
      text<-source path
      children<-either (Left . surfaceFailureIn (dependencySources doc)) Right (dependencySourcePaths path (U.encodeUtf8 text))
      closure (S.insert path seen) (rest++map (normalise . (takeDirectory path </>)) children)

recoverDependencyReference :: DependencyExecution -> Text -> A.SourceRef
  -> Either DependencyDiagnostic (A.SourceRecord,Maybe Text)
recoverDependencyReference execution component reference=do
  sources<-dependencyComponentSources execution component
  source<-case [s | s<-sources,A.sourceId s==A.referenceSource reference] of
    [s]->Right s
    _->failure "DEPNAME" [component,A.referenceSource reference] "unknown or ambiguous source in the selected component namespace"
  case A.referenceSpan reference of
    Nothing->pure (source,Nothing) -- Locator-only means no invented quotation.
    Just spanValue->do
      canonical<-either (failure "DEPFORMAT" [component] . T.intercalate "; " . map A.diagnosticMessage) Right
        (A.sourceAnchorBytes source (toInteger (A.start spanValue)) (toInteger (A.end spanValue)))
      ensure "DEPSTALE" [component] "source coordinates do not correspond to the exact retained UTF-8 bytes" (canonical==reference)
      text<-maybe (failure "DEPFORMAT" [component] "quotation requires retained text") Right (A.sourceText source)
      let bytes=U.encodeUtf8 text
          excerpt=BS.take (A.end spanValue-A.start spanValue) (BS.drop (A.start spanValue) bytes)
      pure (source,Just (U.decodeUtf8 excerpt))


-- Plan authorisation origins and component SourceRefs are separate namespaces.
-- Equal text IDs cannot make a locator into a component quotation anchor.
dependencyOriginRecord :: DependencyExecution -> Text -> Either DependencyDiagnostic SourceOrigin
dependencyOriginRecord execution key=case
  [o | o<-planOrigins (dependencyPlan (checkedDocument (executionPlan execution))),originIdentity o==key] of
  [o]->Right o
  _->failure "DEPNAME" [key] "unknown plan authorisation origin"
