{-# LANGUAGE OverloadedStrings #-}
module Yuho.SuppliedProofStatus.Types
  ( UnresolvedReason(..), SuppliedStatus(..), StatusOrigin(..), StatusSource(..)
  , StatusBinding(..), ProofRequest(..), ValidatedProof(..), ProofReason(..), ProofTrace(..)
  , ProofBranch(..), ProofRule(..), ProofResult(..), ProofSupport(..)
  , ProofOccurrence(..), ProofSelected(..), ProofSelection(..)
  , projection, satisfactionText, suppliedStatusJson
  ) where

import Data.Map.Strict (Map)
import Data.Text (Text)
import Yuho.Core.Types (ProvisionKind, Span)
import Yuho.Exception.Types (ExceptionTrace, RawGraph, Truth(..))
import Yuho.Exception.Validate (ValidatedGraph)
import Yuho.PenaltySelection.Types
  ( BranchUse, PenaltyDeclaration, RawPenalty, SelectionWarning )
import Yuho.PenaltyTerms.Types (RawTerm, Term)
import Yuho.Protocol.Json (J(..))
import Yuho.TypedFacts.Types (Metadata, Provenance)

data UnresolvedReason = NotDetermined | ExternalDecisionPending deriving (Eq, Show)
data SuppliedStatus = Proved | NotProved | Unresolved UnresolvedReason
  deriving (Eq, Show)
data StatusOrigin = ExternalAssertion | SyntheticFixture deriving (Eq, Show)
data StatusSource = StatusSource
  { assignmentId :: Text, assignmentSourceId :: Text, assignmentSpan :: Span
  , assignmentOrigin :: StatusOrigin, assignmentIssuer :: Text
  } deriving (Eq, Show)
data StatusBinding = StatusBinding
  { suppliedStatus :: SuppliedStatus, statusSource :: StatusSource
  , statusMetadata :: Metadata, statusProvenance :: Maybe Provenance
  } deriving (Eq, Show)

data ProofRequest = ProofRequest
  { proofRequestId :: Text, proofRequestDigest :: Text
  , proofRawGraph :: RawGraph StatusBinding
  , proofDeclarations :: Map Text Metadata
  , proofRawPenalties :: [RawPenalty]
  , proofRawTerms :: [RawTerm]
  }

data ValidatedProof = ValidatedProof
  { validatedProofRequest :: ProofRequest
  , validatedProofGraph :: ValidatedGraph StatusBinding
  , validatedProofDeclarations :: [PenaltyDeclaration]
  , validatedProofRootUses :: [BranchUse]
  , validatedProofTerms :: Map Text Term
  }

data ProofReason = ProofSatisfied | ProofRequirementsNotSatisfied
  | ProofRequirementsUnresolved | ProofDefeated | ProofExceptionUnresolved
  deriving (Eq, Show)

data ProofTrace = ProofTrace
  { proofTraceBranch :: Text, proofTraceId :: Text, proofTraceKind :: Text
  , proofTracePath :: [Text], proofTraceSpan :: Span, proofTraceStatus :: Truth
  , proofTraceChildren :: [Text]
  } deriving (Eq, Show)
data ProofBranch = ProofBranch
  { proofBranchId :: Text, proofBranchPath :: [Text]
  , proofBranchStatus :: Truth, proofBranchReason :: ProofReason
  , proofBranchTraceIds :: [Text], proofBranchGuards :: [ExceptionTrace]
  , proofBranchApplicable :: [Text]
  } deriving (Eq, Show)
data ProofRule = ProofRule
  { proofRuleId :: Text, proofRuleSource :: Text, proofRuleStatus :: Truth
  , proofRuleKind :: ProvisionKind, proofRuleBranches :: [ProofBranch]
  , proofRuleTrace :: [ProofTrace]
  } deriving (Eq, Show)
data ProofResult = ProofResult
  { proofResultRoot :: Text, proofResultStatus :: Truth, proofResultRules :: [ProofRule]
  } deriving (Eq, Show)

data ProofSupport = ProofSupport
  { proofSupportBranch :: Text, proofSupportPath :: [Text]
  , proofSupportInherited :: Bool, proofSupportGuard :: Maybe Truth
  } deriving (Eq, Show)
data ProofOccurrence = ProofOccurrence
  { proofOccurrenceDeclaration :: PenaltyDeclaration
  , proofOccurrenceBranch :: Text, proofOccurrencePath :: [Text]
  , proofOccurrenceInherited :: Bool, proofOccurrenceStatus :: Truth
  , proofOccurrenceReason :: ProofReason, proofOccurrenceGuard :: Maybe Truth
  , proofOccurrenceResult :: Text
  } deriving (Eq, Show)
data ProofSelected = ProofSelected PenaltyDeclaration [ProofSupport]
  deriving (Eq, Show)
data ProofSelection = ProofSelection
  { proofSelected :: [ProofSelected], proofSelectionTrace :: [ProofOccurrence]
  , proofSelectionWarnings :: [SelectionWarning]
  } deriving (Eq, Show)

projection :: SuppliedStatus -> Truth
projection Proved = TrueValue
projection NotProved = FalseValue
projection (Unresolved _) = UnresolvedValue

satisfactionText :: Truth -> Text
satisfactionText TrueValue = "satisfied"
satisfactionText FalseValue = "not_satisfied"
satisfactionText UnresolvedValue = "unresolved"

suppliedStatusJson :: SuppliedStatus -> J
suppliedStatusJson Proved = JObj [("kind", JStr "proved")]
suppliedStatusJson NotProved = JObj [("kind", JStr "not_proved")]
suppliedStatusJson (Unresolved reason) = JObj
  [("kind", JStr "unresolved"), ("reason", JStr (case reason of
    NotDetermined -> "not_determined"
    ExternalDecisionPending -> "external_decision_pending"))]
