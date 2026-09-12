{-# LANGUAGE OverloadedStrings #-}
module Yuho.TypedFacts.Types
  ( BurdenHolder(..), BurdenKind(..), Burden(..), Standard(..), Provenance(..)
  , Metadata(..), Binding(..), TypedRequest(..), burdenText, standardText
  ) where

import Data.Map.Strict (Map)
import Data.Text (Text)
import Yuho.Exception.Types (ExceptionRequest)

data BurdenHolder = Prosecution | Defence deriving (Eq, Show)
data BurdenKind = Unspecified | Legal | Evidential deriving (Eq, Show)
data Burden = Burden BurdenHolder BurdenKind deriving (Eq, Show)
data Standard = BeyondReasonableDoubt | BalanceOfProbabilities deriving (Eq, Show)
data Provenance = Provenance
  { provenanceSourceLabel :: Maybe Text
  , provenanceRecordedDate :: Maybe Text
  , provenanceJurisdiction :: Maybe Text
  } deriving (Eq, Show)
data Metadata = Metadata
  { metadataBurden :: Maybe Burden
  , metadataStandard :: Maybe Standard
  } deriving (Eq, Show)
data Binding = Binding
  { bindingValue :: Bool
  , bindingMetadata :: Metadata
  , bindingProvenance :: Maybe Provenance
  } deriving (Eq, Show)
data TypedRequest = TypedRequest
  { typedExceptionRequest :: ExceptionRequest
  , typedBindings :: Map Text Binding
  , typedDeclarations :: Map Text Metadata
  } deriving (Eq, Show)

burdenText :: Burden -> Text
burdenText (Burden holder kind) = holderText holder <> ":" <> kindText kind
  where
    holderText Prosecution = "prosecution"
    holderText Defence = "defence"
    kindText Unspecified = "unspecified"
    kindText Legal = "legal"
    kindText Evidential = "evidential"

standardText :: Standard -> Text
standardText BeyondReasonableDoubt = "beyond_reasonable_doubt"
standardText BalanceOfProbabilities = "balance_of_probabilities"
