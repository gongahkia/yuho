{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Surface.Dependency (loadDependencyProject, dependencyInput) where
import Control.Exception (IOException, try)
import Control.Monad (unless)
import qualified Data.Aeson.KeyMap
import qualified Yuho.Core.Source
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as M
import qualified Data.Text as T
import qualified Data.Text.Encoding as U
import System.FilePath ((</>),takeDirectory,takeFileName,normalise)
import System.Posix.Files (getSymbolicLinkStatus,isRegularFile,isDirectory,fileSize)
import qualified Yuho.Surface.Token as ST
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.TypedFinite (dependencySourcePaths)
import Yuho.Surface.Dependency.Parser
import Yuho.Dependency.Types
import Yuho.Dependency.Check
import Yuho.Dependency.Codec (artifactFormat,quantitativeArtifactFormat)

-- IO is confined to retaining source bytes once. Checking/replay is then pure.
loadDependencyProject :: FilePath -> IO (Either DependencyDiagnostic CheckedPlan)
loadDependencyProject path=do
  attempted<-try (readSafe path)
  case attempted of
    Left (e::IOException)->pure (failure "DEPFORMAT" [] (T.pack (show e)))
    Right bytes->case parseDependencyProject (takeFileName path) bytes of
      Left e->pure (Left (surfaceFailureIn (M.singleton (takeFileName path) (either (const "") id (U.decodeUtf8' bytes))) e))
      Right p->do
        let initial=M.singleton (takeFileName path) bytes
            files=concat [[componentModel c]++maybe [] (:[]) (componentScenario c) | c<-planComponents p]
        collected<-collect (takeDirectory path) initial files
        pure $ do
          bundle<-collected
          texts<-traverse (either (failure "DEPFORMAT" [] . T.pack . show) Right . U.decodeUtf8') bundle
          checkDependencyPlan (DependencyDocument planFormat p texts (Just (takeFileName path)))
  where
    collect _ bundle []=pure (Right bundle)
    collect root bundle (file:rest)
      | M.member file bundle=collect root bundle rest
      | M.size bundle>128 || sum (map BS.length (M.elems bundle))>4194304=pure (failure "DEPLIMIT" [] "source closure exceeds limits")
      | otherwise=do
        case safeVirtual file of
          Left e->pure (Left e)
          Right ()->do
            bytes<-try (readSafe (root </> file))
            case bytes of
              Left (e::IOException)->pure (failure "DEPFORMAT" [T.pack file] (T.pack (show e)))
              Right b->case dependencySourcePaths file b of
                Left e->pure (Left (surfaceFailure e))
                Right children->collect root (M.insert file b bundle)
                  (rest++map (normalise . (takeDirectory file </>)) children)
    safeVirtual file=ensure "DEPFORMAT" [T.pack file] "unsafe source/import path" (Yuho.Core.Source.validSourcePath (T.pack file))

readSafe :: FilePath -> IO BS.ByteString
readSafe path=do
  let parents p=do
        status<-getSymbolicLinkStatus p
        unless (isDirectory status) (ioError (userError "source ancestors must be real directories"))
        let parent=takeDirectory p
        if parent==p then pure () else parents parent
  parents (takeDirectory path)
  s<-getSymbolicLinkStatus path
  unless (isRegularFile s && fileSize s<=8388608) (ioError (userError "expected bounded regular non-symlink source"))
  BS.readFile path

dependencyInput :: FilePath -> IO Bool
dependencyInput path=do
  result<-try (readSafe path)
  pure $ case result of
    Left (_::IOException)->False
    Right b->case lexSource path b of
      Right (t:_) | ST.tokenText t=="checked-project"->True
      _->case A.eitherDecodeStrict' b of
        Right (A.Object obj)->Data.Aeson.KeyMap.lookup "artifactFormatVersion" obj `elem` map (Just . A.String) [artifactFormat,quantitativeArtifactFormat]
        _->False
