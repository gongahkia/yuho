{-# LANGUAGE OverloadedStrings #-}
module Yuho.ModelBundle.Types
  ( Failure(..), issue, Artifact(..), SourceRecord(..), Mapping(..), Derivation(..)
  , Scope(..), Core(..), Review(..), Validation(..), limits
  ) where

import Data.Text (Text)
import Yuho.Core.Types (Span)
import Yuho.Protocol.Json (J)

data Failure = Failure
  { failureCode :: Text, failurePath :: Text, failureMessage :: Text
  } deriving (Eq, Show)

issue :: Text -> Text -> Text -> Either Failure a
issue code path message = Left (Failure code path message)

data Artifact = Artifact
  { artifactDigest :: Text, artifactLength :: Integer
  , artifactMediaType :: Text, artifactRole :: Text
  } deriving (Eq, Show)

data SourceRecord = SourceRecord
  { recordId :: Text, recordWork :: Text, recordExpression :: Text
  , recordManifestation :: Text, recordArtifact :: Text
  , recordType :: Text, recordLanguage :: Text, recordJurisdiction :: Text
  , recordMetadata :: J
  } deriving (Eq, Show)

data Mapping = Mapping
  { mappingSemanticId :: Text, mappingArtifact :: Text, mappingSource :: Text
  , mappingRole :: Text, mappingSpan :: Span
  } deriving (Eq, Show)

data Derivation = Derivation
  { derivationChild :: Text, derivationParent :: Text
  , derivationTool :: Text, derivationVersion :: Text, derivationConfiguration :: Text
  } deriving (Eq, Show)

data Scope = Scope
  { scopeIds :: [Text], scopeSources :: [Text], scopeExpressions :: [Text]
  , scopeExclusions :: [(Text, Text)], scopeRaw :: J
  } deriving (Eq, Show)

data Core = Core
  { coreRaw :: J, coreArtifacts :: [Artifact], coreSources :: [SourceRecord]
  , coreMappings :: [Mapping], coreDerivations :: [Derivation]
  , coreScope :: Scope, coreModelDigest :: Text, coreModelFragment :: Text
  , coreModelId :: Text
  } deriving (Eq, Show)

data Review = Review
  { reviewId :: Text, reviewBundleDigest :: Text, reviewScopeDigest :: Text
  , reviewPurposes :: [Text], reviewSemanticIds :: [Text], reviewSourceIds :: [Text]
  , reviewCoverageKind :: Text, reviewOutcome :: Text
  } deriving (Eq, Show)

data Validation = Validation
  { validatedDigest :: Text, validatedScopeDigest :: Text
  , validatedApplicable :: [Text], validatedStale :: [Text]
  , validatedPartial :: [Text], validatedPolicyMet :: Bool
  } deriving (Eq, Show)

limits :: [(Text, Integer)]
limits =
  [ ("manifest_bytes", 1048576), ("review_bytes", 1048576)
  , ("reviews", 64), ("artifacts", 256), ("artifact_bytes", 33554432)
  , ("combined_artifact_bytes", 134217728), ("sources", 1024)
  , ("mappings", 8192), ("scope_ids", 8192), ("exclusions", 1024)
  , ("derivations", 4096), ("depth", 16)
  ]
