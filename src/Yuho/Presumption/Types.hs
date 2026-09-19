{-# LANGUAGE OverloadedStrings #-}
module Yuho.Presumption.Types
  ( Condition(..), ConditionKind(..), Registration(..), PresumptionRequest(..)
  , ValidatedPresumption(..), ConditionTrace(..), DerivationState(..)
  , Derivation(..), LeafResolution(..), PresumptionResult(..), stateText
  ) where

import Data.Map.Strict (Map)
import Data.Text (Text)
import Yuho.Core.Types (Span)
import Yuho.Exception.Types (Truth)
import Yuho.SuppliedProofStatus.Types (ProofRequest, ValidatedProof)

data ConditionKind = EffectiveLeaf Text | ConditionAll [Condition]
  | ConditionAny [Condition] deriving (Eq, Show)
data Condition = Condition
  { conditionSpan :: Span, conditionKind :: ConditionKind
  } deriving (Eq, Show)
data Registration = Registration
  { registrationId :: Text, registrationTarget :: Text
  , registrationSource :: Text, registrationSpan :: Span
  , registrationTrigger :: Condition, registrationRebuttal :: Condition
  , registrationPointer :: Text
  } deriving (Eq, Show)
data PresumptionRequest = PresumptionRequest
  { presumptionBase :: ProofRequest, presumptionRules :: [Registration]
  , presumptionPriorIds :: [Text]
  }
data ValidatedPresumption = ValidatedPresumption
  { presumptionValidatedBase :: ValidatedProof
  , presumptionValidatedRules :: [Registration]
  , presumptionByTarget :: Map Text [Registration]
  }
data ConditionTrace = ConditionTrace
  { conditionTraceKind :: Text, conditionTraceLeaf :: Maybe Text
  , conditionTraceSpan :: Span, conditionTraceValue :: Truth
  , conditionTraceChildren :: [ConditionTrace]
  } deriving (Eq, Show)
data DerivationState = Active | Inactive | Rebutted | RouteUnresolved
  deriving (Eq, Show)
data Derivation = Derivation
  { derivationRegistration :: Registration
  , derivationTrigger :: ConditionTrace, derivationRebuttal :: ConditionTrace
  , derivationState :: DerivationState
  } deriving (Eq, Show)
data LeafResolution = LeafResolution
  { leafDirect :: Truth, leafEffective :: Truth
  , leafRoutes :: [Derivation]
  } deriving (Eq, Show)
data PresumptionResult = PresumptionResult
  { presumptionEffective :: Map Text Truth
  , presumptionResolutions :: Map Text LeafResolution
  , presumptionDerivations :: [Derivation]
  } deriving (Eq, Show)

stateText :: DerivationState -> Text
stateText Active = "active"
stateText Inactive = "inactive"
stateText Rebutted = "rebutted"
stateText RouteUnresolved = "unresolved"
