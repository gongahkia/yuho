{-# LANGUAGE OverloadedStrings #-}
module Yuho.Exception.Types
  ( Truth(..), BranchReason(..), RawException(..), RawRule(..), RawGraph(..)
  , ExceptionRequest(..), ExceptionTrace(..), ExceptionBranch(..), RuleResult(..)
  , ExceptionStatus(..), ExceptionResult(..), truthText, rejectException
  ) where

import Data.Map.Strict (Map)
import Data.Text (Text)
import Data.Time.Calendar (Day)
import Yuho.Core.Types (Diagnostic, Provision, Source, Span, Trace, ProvisionKind(..))

data Truth = TrueValue | FalseValue | UnresolvedValue deriving (Eq, Ord, Show)
data BranchReason = Satisfied | RequirementsFailed | Defeated | GuardUnresolved
  deriving (Eq, Show)

data RawException = RawException
  { rawExceptionId :: Text, rawExceptionBranch :: Text
  , rawExceptionSource :: Text, rawExceptionSpan :: Span
  , rawExceptionTarget :: Text, rawExceptionPointer :: Text
  } deriving (Eq, Show)

data RawRule = RawRule
  { rawRuleId :: Text, rawRuleSource :: Text, rawRuleProgram :: Provision
  , rawRuleExceptions :: [RawException], rawRulePointer :: Text
  } deriving (Eq, Show)

data RawGraph = RawGraph
  { rawRoot :: Text, rawSources :: [(Text, Source)], rawRules :: [RawRule]
  , rawFacts :: Map Text Bool, rawDate :: Day, rawMaxNodes :: Int
  } deriving (Eq, Show)

data ExceptionRequest = ExceptionRequest
  { exceptionRequestId :: Text, exceptionRequestDigest :: Text
  , exceptionRawGraph :: RawGraph
  } deriving (Eq, Show)

data ExceptionTrace = ExceptionTrace
  { exceptionTraceId :: Text, exceptionTraceSource :: Text
  , exceptionTraceSpan :: Span, exceptionTraceTarget :: Text
  , exceptionTraceTargetStatus :: Truth, exceptionTraceGuardStatus :: Truth
  , exceptionTraceFired :: Bool
  } deriving (Eq, Show)

data ExceptionBranch = ExceptionBranch
  { exceptionBranchId :: Text, exceptionBranchPath :: [Text]
  , exceptionBranchStatus :: Truth, exceptionBranchReason :: BranchReason
  , exceptionBranchTraceIds :: [Text]
  , exceptionBranchGuards :: [ExceptionTrace]
  , exceptionBranchApplicable :: [Text]
  } deriving (Eq, Show)

data RuleResult = RuleResult
  { ruleResultId :: Text, ruleResultSource :: Text, ruleResultStatus :: Truth
  , ruleResultKind :: ProvisionKind, ruleResultBranches :: [ExceptionBranch]
  , ruleResultTrace :: [Trace]
  } deriving (Eq, Show)

data ExceptionStatus = Judgment Truth | Rejected deriving (Eq, Show)
data ExceptionResult = ExceptionResult
  { exceptionResultRequestId :: Text, exceptionResultDigest :: Text
  , exceptionResultRoot :: Text, exceptionResultStatus :: ExceptionStatus
  , exceptionResultRules :: [RuleResult], exceptionResultDiagnostics :: [Diagnostic]
  } deriving (Eq, Show)

truthText :: Truth -> Text
truthText TrueValue = "true"
truthText FalseValue = "false"
truthText UnresolvedValue = "unresolved"

rejectException :: Text -> Text -> Text -> Diagnostic -> ExceptionResult
rejectException requestId digest root issue =
  ExceptionResult requestId digest root Rejected [] [issue]
