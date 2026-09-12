{-# LANGUAGE OverloadedStrings #-}
module Yuho.Core.Types
  ( Span(..), Diagnostic(..), Source(..), RequirementKind(..), Requirement(..)
  , Provision(..), KernelInput(..), Request(..), Trace(..), Branch(..), KernelResult(..)
  , diagnostic
  ) where

import Data.ByteString (ByteString)
import Data.Map.Strict (Map)
import Data.Text (Text)
import Data.Time.Calendar (Day)

data Span = Span
  { spanStart :: Int, spanEnd :: Int
  , spanStartLine :: Int, spanStartCol :: Int
  , spanEndLine :: Int, spanEndCol :: Int
  } deriving (Eq, Show)

data Diagnostic = Diagnostic
  { diagCode :: Text, diagStage :: Text, diagSeverity :: Text, diagPath :: Text
  , diagSpan :: Maybe Span, diagParameters :: [(Text, Text)]
  } deriving (Eq, Show)

diagnostic :: Text -> Text -> Text -> Maybe Span -> [(Text, Text)] -> Diagnostic
diagnostic code stage path sourceSpan parameters =
  Diagnostic code stage "error" path sourceSpan parameters

data Source = Source
  { sourcePath :: Text, sourceText :: Text, sourceBytes :: ByteString
  , sourceSha256 :: Text
  } deriving (Eq, Show)

data RequirementKind = Leaf | All | Any deriving (Eq, Show)
data Requirement = Requirement
  { requirementKind :: RequirementKind, requirementId :: Text
  , requirementPath :: [Text], requirementSpan :: Span
  , requirementMembers :: [Requirement], requirementPointer :: Text
  } deriving (Eq, Show)

data Provision = Provision
  { provisionId :: Text, provisionPath :: [Text], provisionSpan :: Span
  , provisionDefinitions :: Bool, provisionRequirements :: [Requirement]
  , provisionChildren :: [Provision], provisionPointer :: Text
  } deriving (Eq, Show)

data KernelInput
  = Evaluate Source Provision (Map Text Bool) Day Int
  | Validate Source Bool [Diagnostic] Day
  deriving (Eq, Show)

data Request = Request
  { requestId :: Text, requestInput :: KernelInput, requestDigest :: Text
  } deriving (Eq, Show)

data Trace = Trace
  { traceBranch :: Text, traceId :: Text, traceKind :: Text
  , tracePath :: [Text], traceSpan :: Span, traceValue :: Bool
  , traceChildren :: [Text]
  } deriving (Eq, Show)

data Branch = Branch
  { branchId :: Text, branchPath :: [Text], branchValue :: Bool
  , branchTraceIds :: [Text]
  } deriving (Eq, Show)

data KernelResult = KernelResult
  { resultRequestId :: Text, resultDigest :: Text, resultStatus :: Text
  , resultProvisionKind :: Text, resultBranches :: [Branch]
  , resultTrace :: [Trace], resultDiagnostics :: [Diagnostic]
  } deriving (Eq, Show)
