{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Release
  ( releaseName, releaseVersion, locateRepository, doctorReport
  , initialiseProject, verifyReleaseManifest
  ) where

import Control.Exception (IOException, onException, try)
import Control.Monad (forM, unless)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Version (showVersion)
import System.Directory
  ( createDirectory, doesDirectoryExist, doesFileExist
  , doesPathExist, findExecutable, getCurrentDirectory, listDirectory
  , removePathForcibly, renameDirectory )
import System.FilePath ((</>), isAbsolute, takeDirectory)
import System.Info (compilerName, compilerVersion)
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Protocol.Json
  ( J(..), arrayValue, decodeJson, lookupField, objectFields, textValue )

releaseName :: Text
releaseName = "Haskell Yuho Research Language"

releaseVersion :: Text
releaseVersion = "1.0.0"

locateRepository :: Maybe FilePath -> IO (Either Text FilePath)
locateRepository (Just root) = check root
locateRepository Nothing = do
  current <- getCurrentDirectory
  search (take 10 (iterate takeDirectory current))
  where
    search [] = pure (Left "repository root not found; pass --root <path>")
    search (candidate:rest) = do
      found <- check candidate
      case found of
        Right root -> pure (Right root)
        Left _ -> search rest

check :: FilePath -> IO (Either Text FilePath)
check root = do
  marker <- doesFileExist (root </> "rewrite/haskell/yuho-foundation.cabal")
  pure (if marker then Right root else Left "root does not contain the Haskell Yuho release")

doctorReport :: Maybe FilePath -> IO J
doctorReport selected = do
  rootResult <- locateRepository selected
  lean <- findExecutable "lake"
  case rootResult of
    Left message -> pure (JObj
      [("release",JStr releaseName),("version",JStr releaseVersion)
      ,("implementation",JStr "haskell"),("compiler",JStr compilerIdentity)
      ,("status",JStr "incomplete"),("repository",JNull)
      ,("corpus_available",JBool False),("modules_available",JBool False)
      ,("lean_optional",JBool (lean /= Nothing)),("message",JStr message)
      ,("python_required",JBool False),("external_renderer_required",JBool False)])
    Right root -> do
      corpus <- doesFileExist (root </> "research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json")
      modules <- doesDirectoryExist (root </> "research/singapore/corpus-v0.3/modules")
      pure (JObj
        [("release",JStr releaseName),("version",JStr releaseVersion)
        ,("implementation",JStr "haskell"),("compiler",JStr compilerIdentity)
        ,("status",JStr (if corpus && modules then "ready" else "incomplete"))
        ,("repository",JStr (Text.pack root))
        ,("corpus_available",JBool corpus),("modules_available",JBool modules)
        ,("schemas",JArr (map JStr
          ["yuho.kernel-input/v1","yuho.kernel-result/v1","yuho.semantic-graph/v0.1"
          ,"yuho.core-conformance-v0.1","yuho.core-conformance-v0.2"
          ,"yuho.core-conformance-v0.3","yuho.release-manifest/v1.0"]))
        ,("lean_optional",JBool (lean /= Nothing)),("python_required",JBool False)
        ,("external_renderer_required",JBool False)])

compilerIdentity :: Text
compilerIdentity = Text.pack (compilerName <> "-" <> showVersion compilerVersion)

initialiseProject :: FilePath -> IO (Either Text ())
initialiseProject destination = do
  exists <- doesPathExist destination
  if exists then do
    isDirectory <- doesDirectoryExist destination
    contents <- if isDirectory then listDirectory destination else pure [destination]
    pure (Left (if null contents then "destination already exists; init never overwrites"
      else "destination exists and is not empty"))
  else do
    let temporary = destination <> ".yuho-init-tmp"
    temporaryExists <- doesPathExist temporary
    if temporaryExists then pure (Left "temporary init path already exists") else do
      result <- try (build temporary `onException` removePathForcibly temporary)
      pure $ case result of
        Left (_ :: IOException) -> Left "starter project could not be created atomically"
        Right () -> Right ()
  where
    build temporary = do
      createDirectory temporary
      createDirectory (temporary </> "modules")
      BS.writeFile (temporary </> "modules/starter.rules@1.0.0.yh") moduleSource
      BS.writeFile (temporary </> "model.yh") modelSource
      BS.writeFile (temporary </> "scenario.yh") scenarioSource
      BS.writeFile (temporary </> "case.yh") caseSource
      BS.writeFile (temporary </> "README.md") readmeSource
      renameDirectory temporary destination

verifyReleaseManifest :: FilePath -> IO (Either Text (Int,Text))
verifyReleaseManifest root = do
  let path = root </> "release/yuho-haskell-research-v1.0.0.json"
  exists <- doesFileExist path
  if not exists then pure (Left "release manifest is missing") else do
    bytes <- BS.readFile path
    case decodeJson bytes of
      Left message -> pure (Left ("invalid release manifest: " <> message))
      Right value -> case manifestEntries value of
        Left message -> pure (Left message)
        Right entries -> do
          rows <- forM entries $ \(relative,expected) -> do
            if unsafe relative then pure (Left ("unsafe manifest path " <> Text.pack relative))
            else do
              let file = root </> relative
              present <- doesFileExist file
              if not present then pure (Left ("missing manifest artifact " <> Text.pack relative))
              else do
                actual <- sha256Text <$> BS.readFile file
                pure (if actual == expected then Right ()
                  else Left ("digest mismatch for " <> Text.pack relative))
          pure $ case sequence rows of
            Left message -> Left message
            Right _ -> Right (length entries,sha256Text bytes)
  where
    unsafe value = isAbsolute value || any (`elem` ["",".."])
      (map Text.unpack (Text.splitOn "/" (Text.pack value)))

manifestEntries :: J -> Either Text [(FilePath,Text)]
manifestEntries value = do
  schema <- maybe (Left "manifest schema missing") Right (lookupField "schema" value >>= textValue)
  unless (schema == "yuho.release-manifest/v1.0") (Left "unsupported release manifest schema")
  release <- maybe (Left "manifest release missing") Right (lookupField "release" value >>= textValue)
  unless (release == releaseName <> " v" <> releaseVersion) (Left "release identity mismatch")
  artifacts <- maybe (Left "manifest artifacts missing") Right
    (lookupField "artifacts" value >>= arrayValue)
  traverse entry artifacts
  where
    entry item = do
      fields <- maybe (Left "manifest artifact is not an object") Right (objectFields item)
      unless (map fst fields == ["path","sha256"]) (Left "manifest artifact fields are not canonical")
      relative <- maybe (Left "manifest artifact path missing") Right
        (lookupField "path" item >>= textValue)
      digest <- maybe (Left "manifest artifact digest missing") Right
        (lookupField "sha256" item >>= textValue)
      unless (Text.length digest == 64 && Text.all (`elem` (['0'..'9'] ++ ['a'..'f'])) digest)
        (Left "invalid manifest SHA-256")
      pure (Text.unpack relative,digest)

moduleSource, modelSource, scenarioSource, caseSource, readmeSource :: BS.ByteString
moduleSource = "typed-rules-module starter.rules version 1.0.0 {\n  export entity-type person;\n  export predicate acts;\n  export proposition p:candidate;\n  export requirement q:acts;\n  export rule r:candidate;\n  entity-type person;\n  predicate acts(person) kind conduct;\n  proposition p:candidate;\n  requirement q:acts = acts(actor:researcher);\n  rule r:candidate establishes proposition p:candidate when q:acts;\n}\n"
modelSource = "typed-rules-model StarterResearchModel {\n  limit 256;\n  module-root \"modules\";\n  import starter.rules version 1.0.0 as base;\n  use entity-type base::person;\n  use predicate base::acts;\n  use proposition base::p:candidate;\n  use requirement base::q:acts;\n  use rule base::r:candidate;\n  entity actor:researcher as person;\n  limitation \"Synthetic research example; supplied classifications are not evidence findings.\";\n}\n"
scenarioSource = "typed-rules-scenario StarterScenario for StarterResearchModel {\n  classify acts(actor:researcher) as proved reason \"synthetic supplied classification\";\n}\n"
caseSource = "typed-rules-case StarterCase model \"model.yh\" {\n  allegation a:starter scenario \"scenario.yh\";\n}\n"
readmeSource = "# Yuho starter\n\nThis relocatable project uses the Haskell Yuho Research Language. From this directory, set `YUHO` to the built executable and run:\n\n```sh\n$YUHO check model.yh --scenario scenario.yh\n$YUHO compile model.yh --scenario scenario.yh\n$YUHO run model.yh --scenario scenario.yh\n$YUHO explain model.yh --scenario scenario.yh\n$YUHO check case.yh\n$YUHO diagram case.yh --view case --format svg --output case.svg\n```\n\nAll facts are supplied classifications. No evidence or judicial outcome is determined.\n"
