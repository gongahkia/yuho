{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltySelection.Types
  ( PenaltyGuard(..), RawPenalty(..), PenaltyDeclaration(..), PenaltyRequest(..)
  , BranchUse(..), ValidatedPenalties(..), Support(..), PenaltyOccurrence(..)
  , SelectedPenalty(..), SelectionWarning(..), Selection(..)
  ) where

import Data.Map.Strict (Map)
import Data.Text (Text)
import Yuho.Core.Types (Span)
import Yuho.Exception.Types (BranchReason, Truth)
import Yuho.Protocol.Json (J)
import Yuho.TypedFacts.Types (TypedRequest)
import Yuho.TypedFacts.Validate (ValidatedTyped)

data PenaltyGuard = Unguarded | LeafTrue Text deriving (Eq, Show)

data RawPenalty = RawPenalty
  { rawPenaltyId :: Text, rawPenaltyRule :: Text, rawPenaltyProvision :: Text
  , rawPenaltySource :: Text, rawPenaltySpanJson :: J
  , rawPenaltyGuard :: PenaltyGuard, rawPenaltyIndex :: Int
  , rawPenaltyPointer :: Text
  } deriving (Eq, Show)

data PenaltyDeclaration = PenaltyDeclaration
  { penaltyId :: Text, penaltyRule :: Text, penaltyProvision :: Text
  , penaltyPath :: [Text], penaltySource :: Text, penaltySpan :: Span
  , penaltyGuard :: PenaltyGuard, penaltyIndex :: Int, penaltyPointer :: Text
  } deriving (Eq, Show)

data PenaltyRequest = PenaltyRequest
  { penaltyTypedRequest :: TypedRequest, penaltyRawDeclarations :: [RawPenalty]
  } deriving (Eq, Show)

data BranchUse = BranchUse
  { useRule :: Text, useBranch :: Text, usePath :: [Text]
  , useLeaves :: [Text], useDeclarations :: [PenaltyDeclaration]
  } deriving (Eq, Show)

data ValidatedPenalties = ValidatedPenalties
  { validatedTyped :: ValidatedTyped
  , validatedDeclarations :: [PenaltyDeclaration]
  , validatedRootUses :: [BranchUse]
  , validatedAllUses :: Map Text [BranchUse]
  }

data Support = Support
  { supportBranch :: Text, supportPath :: [Text], supportInherited :: Bool
  , supportGuardResult :: Maybe Bool
  } deriving (Eq, Show)

data PenaltyOccurrence = PenaltyOccurrence
  { occurrenceDeclaration :: PenaltyDeclaration
  , occurrenceBranch :: Text, occurrencePath :: [Text]
  , occurrenceInherited :: Bool, occurrenceStatus :: Truth
  , occurrenceReason :: BranchReason, occurrenceGuard :: Maybe Bool
  , occurrenceResult :: Text
  } deriving (Eq, Show)

data SelectedPenalty = SelectedPenalty PenaltyDeclaration [Support] deriving (Eq, Show)

data SelectionWarning = SelectionWarning
  { warningRule :: Text, warningProvision :: Text, warningPath :: [Text]
  , warningBranchPaths :: [[Text]], warningPenaltyIds :: [Text]
  , warningGuardIds :: [Text]
  } deriving (Eq, Show)

data Selection = Selection
  { selectedPenalties :: [SelectedPenalty]
  , selectionTrace :: [PenaltyOccurrence]
  , selectionWarnings :: [SelectionWarning]
  } deriving (Eq, Show)
