{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltyTerms.Types
  ( Endpoint(..), DurationUnit(..), Punishment(..), TermKind(..), Term(..)
  , RawTerm(..), TermsRequest(..), ValidatedTerms(..), unsupportedFeatureFields
  ) where

import Data.Map.Strict (Map)
import Data.Text (Text)
import Yuho.Core.Types (Span)
import Yuho.PenaltySelection.Types (PenaltyRequest, ValidatedPenalties)
import Yuho.Protocol.Json (J)

data Endpoint a = NotStated | Unbounded | Specified a deriving (Eq, Show)
data DurationUnit = Days | Weeks | Months | Years deriving (Eq, Show)
data Punishment
  = TermImprisonment DurationUnit (Endpoint Integer) (Endpoint Integer)
  | LifeImprisonment
  | Fine (Endpoint Integer) (Endpoint Integer)
  | Caning (Endpoint Integer) (Endpoint Integer)
  | Death
  deriving (Eq, Show)
data TermKind
  = Atom Punishment
  | AllOf [Term]
  | ExactlyOneOf [Term]
  | OneOrMoreOf [Term]
  deriving (Eq, Show)
data Term = Term {termId :: Text, termSpan :: Span, termKind :: TermKind}
  deriving (Eq, Show)
data RawTerm = RawTerm {rawTermPenaltyId :: Text, rawTermValue :: J, rawTermPointer :: Text}
  deriving (Eq, Show)
data TermsRequest = TermsRequest PenaltyRequest [RawTerm]
data ValidatedTerms = ValidatedTerms ValidatedPenalties (Map Text Term)

unsupportedFeatureFields :: [Text]
unsupportedFeatureFields = ["sentencing_mode", "mandatory", "discretionary"
  , "concurrent", "consecutive", "suspended", "default_of_fine"
  , "compensation", "forfeiture", "disqualification", "community_sentence"
  , "corrective_detention", "preventive_detention", "person_eligibility"
  , "cross_act_limit", "supplementary", "condition", "prose", "duration"
  , "mixed_components", "fine_unlimited", "mandatory_min_imprisonment"
  , "mandatory_min_fine", "caning_unspecified", "death_penalty"
  , "sentence_framework", "currency_conversion"]
