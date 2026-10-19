{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- Caller-side admission check. Nothing in this module is SDK/kernel policy.
module Acknowledgements
  ( AcknowledgementContext(..), AcknowledgementPolicy(..), Acknowledgements(..)
  , AcknowledgementDiagnostic(..), AcknowledgementReport(..), CheckedFailure(..)
  , acknowledgementContext, checkAcknowledgements, evaluateAcknowledged ) where

import Data.Aeson (ToJSON)
import Data.List (group, sort)
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Calendar (Day)
import GHC.Generics (Generic)
import Yuho.Authoring
import Yuho.Authoring.Snapshot (makeSnapshot)

data AcknowledgementContext = AcknowledgementContext
  { acknowledgementLaw :: Text, acknowledgementRevision :: Text
  , acknowledgementLawDigest :: Text, acknowledgementAnalysis :: Text
  , acknowledgementTarget :: Text, acknowledgementScope :: Scope
  , acknowledgementDate :: Day
  } deriving (Eq, Show, Generic)
instance ToJSON AcknowledgementContext

data AcknowledgementPolicy = AcknowledgementPolicy
  { policyContext :: AcknowledgementContext, requiredAssumptions :: [Text] }
  deriving (Eq, Show, Generic)
instance ToJSON AcknowledgementPolicy

data Acknowledgements = Acknowledgements
  { acknowledgedContext :: AcknowledgementContext, acknowledgedAssumptions :: [Text] }
  deriving (Eq, Show, Generic)
instance ToJSON Acknowledgements

data AcknowledgementDiagnostic = AcknowledgementDiagnostic
  { acknowledgementCode :: Text, acknowledgementLocation :: Text
  , acknowledgementObjects :: [Text], acknowledgementMessage :: Text }
  deriving (Eq, Show, Generic)
instance ToJSON AcknowledgementDiagnostic

data AcknowledgementReport = AcknowledgementReport
  { checkedPolicy :: AcknowledgementPolicy, checkedAcknowledgements :: Acknowledgements
  , checkedAnalysis :: Text, checkedSnapshot :: Text
  , checkedNotice :: Text }
  deriving (Eq, Show, Generic)
instance ToJSON AcknowledgementReport

-- No rejected operation contains an Evaluation or success/snapshot receipt.
data CheckedFailure = CheckedFailure
  { acknowledgementDiagnostics :: [AcknowledgementDiagnostic]
  , authoringDiagnostics :: [AuthoringDiagnostic] }
  deriving (Eq, Show, Generic)
instance ToJSON CheckedFailure

acknowledgementContext :: AuthoringDocument -> Text
                       -> Either [AcknowledgementDiagnostic] AcknowledgementContext
acknowledgementContext doc key = case filter ((== key) . analysisId) (documentAnalyses doc) of
  [analysis] -> let law = documentLaw doc; snapshot = makeSnapshot doc analysis in
    Right (AcknowledgementContext (lawId law) (lawRevision law) (snapshotLawDigest snapshot)
      key (analysisTarget analysis) (analysisScope analysis) (analysisReferenceDate analysis))
  _ -> Left [problem "ACKCONTEXT" "/analysis" [key] "analysis context must identify exactly one current analysis"]

checkAcknowledgements :: AcknowledgementPolicy -> Acknowledgements -> AuthoringDocument -> Text
                      -> Either [AcknowledgementDiagnostic] ()
checkAcknowledgements policy supplied doc key = do
  current <- acknowledgementContext doc key
  let required = requiredAssumptions policy
      given = acknowledgedAssumptions supplied
      errors =
        [problem "ACKCONTEXT" "/policyContext" [key] "policy does not apply to the current law definition and analysis"
          | policyContext policy /= current] ++
        [problem "ACKCONTEXT" "/acknowledgedContext" [key] "acknowledgements do not apply to the current law definition and analysis"
          | acknowledgedContext supplied /= current] ++
        [problem "ACKPOLICY" "/requiredAssumptions" required "requirements must be explicit, nonempty, distinct IDs"
          | null required || any (Text.null . Text.strip) required || not (null (duplicates required))] ++
        [problem "ACKMISSING" "/acknowledgedAssumptions" [key,item] "required modelling assumption was not explicitly acknowledged"
          | item <- required, item `notElem` given] ++
        [problem "ACKUNKNOWN" "/acknowledgedAssumptions" [key,item] "acknowledgement is not in the caller's required set"
          | item <- given, item `notElem` required] ++
        [problem "ACKDUPLICATE" "/acknowledgedAssumptions" [key,item] "acknowledgement occurs more than once"
          | item <- duplicates given]
  if null errors then Right () else Left errors

-- Check the CURRENT inputs on EVERY invocation, before compileAnalysis.
-- An earlier report is a receipt, never an acceptance token or executable input.
evaluateAcknowledged :: AcknowledgementPolicy -> Acknowledgements -> AuthoringDocument -> Text
                     -> Either CheckedFailure (Evaluation,AcknowledgementReport)
evaluateAcknowledged policy supplied doc key = do
  either (Left . flip CheckedFailure []) Right (checkAcknowledgements policy supplied doc key)
  compiled <- either (Left . CheckedFailure []) Right (compileAnalysis doc key)
  result <- either (Left . CheckedFailure []) Right (evaluateAnalysis compiled)
  let receipt = AcknowledgementReport policy supplied key (snapshotId (evaluationSnapshot result))
        "Caller acknowledgement of modelling assumptions only; neither their truth/legal adequacy nor a supplied legal classification is established."
  pure (result,receipt)

problem :: Text -> Text -> [Text] -> Text -> AcknowledgementDiagnostic
problem = AcknowledgementDiagnostic

duplicates :: [Text] -> [Text]
duplicates xs = [key | key:_:_ <- group (sort xs)]
