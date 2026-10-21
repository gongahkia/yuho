{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Explicit experimental wrapper; descriptive support/challenge edges never execute.
module Yuho.Authoring.Presumption.Types where

import Data.Aeson
import Data.Text (Text)
import GHC.Generics (Generic)
import Yuho.Authoring.Types
import Yuho.Authoring.Report (ApplicationReport, RequirementObservation)

presumptionAuthoringFormat, presumptionProfile, presumptionProjectionFormat :: Text
presumptionAuthoringFormat = "yuho.authoring/v0.4-experimental"
presumptionProfile = "RegisteredPresumptionDerivations-v1"
presumptionProjectionFormat = "yuho.presumption-projection/v0.4-experimental"

-- | Closed record: kind is leaf_effective, all_of or any_of. All fields are
-- explicit: a leaf has Just input/no children; a group has Nothing/2+ children.
data RegisteredCondition = RegisteredCondition
  { registeredConditionId :: Text, registeredConditionKind :: Text
  , registeredConditionLeaf :: Maybe Text, registeredConditionMembers :: [RegisteredCondition]
  , registeredConditionSources :: [SourceRef]
  } deriving (Eq, Show, Generic)
data AuthoredRegistration = AuthoredRegistration
  { registeredId :: Text, registeredLabel :: Text, registeredTarget :: Text
  , registeredAnalyses :: [Text], registeredSources :: [SourceRef]
  , registeredTrigger :: RegisteredCondition, registeredRebuttal :: RegisteredCondition
  } deriving (Eq, Show, Generic)
data PresumptionDocument = PresumptionDocument
  { presumptionDocumentFormat :: Text, presumptionDocumentId :: Text
  , presumptionProofDocument :: AuthoringDocument
  , presumptionRegistrations :: [AuthoredRegistration]
  , presumptionContext :: [Text]
  } deriving (Eq, Show, Generic)
data PresumptionSnapshot = PresumptionSnapshot
  { presumptionSnapshotId :: Text, presumptionSnapshotProfile :: Text
  , presumptionSnapshotAnalysis :: Analysis, presumptionSnapshotDocument :: PresumptionDocument
  } deriving (Eq, Show, Generic)
data PresumptionMapping = PresumptionMapping
  { presumptionMappingKind :: Text, presumptionMappingAuthored :: Text
  , presumptionMappingKernel :: Text, presumptionMappingPath :: [Text]
  , presumptionMappingSource :: Text, presumptionMappingSpan :: TextSpan
  , presumptionMappingOriginals :: [SourceRef]
  } deriving (Eq, Show, Generic)
data ResolvedCondition = ResolvedCondition
  { resolvedConditionObject :: RegisteredCondition, resolvedConditionValue :: Text
  , resolvedConditionChildren :: [ResolvedCondition]
  } deriving (Eq, Show, Generic)
data RegistrationObservation = RegistrationObservation
  { registrationObservationId :: Text, registrationAuthored :: AuthoredRegistration
  , registrationEvaluation :: Text, registrationRouteState :: Text
  , registrationTriggerResult :: ResolvedCondition, registrationRebuttalResult :: ResolvedCondition
  } deriving (Eq, Show, Generic)
data EffectiveLeafObservation = EffectiveLeafObservation
  { effectiveObservationId :: Text, effectiveInput :: Text, effectiveScope :: Scope
  , effectiveDirectAssessment :: Assessment, effectiveDirectValue :: Text, effectiveValue :: Text
  , effectiveRoutes :: [Text], effectiveDownstream :: [RequirementObservation]
  } deriving (Eq, Show, Generic)
data PresumptionReport = PresumptionReport
  { presumptionReportSnapshot :: Text, presumptionReportAnalysis :: Analysis
  , presumptionReportLeaves :: [EffectiveLeafObservation]
  , presumptionReportDerivations :: [RegistrationObservation]
  , presumptionReportProof :: ApplicationReport, presumptionReportNotice :: Text
  } deriving (Eq, Show, Generic)
data PresumptionValidation = PresumptionValidation
  { presumptionDocumentValid :: Bool, presumptionAnalysisReady :: Bool
  , presumptionDiagnostics :: [AuthoringDiagnostic], presumptionOpenInputs :: [OpenInput]
  } deriving (Eq, Show, Generic)

conditionObjects :: RegisteredCondition -> [RegisteredCondition]
conditionObjects c = c : concatMap conditionObjects (registeredConditionMembers c)
conditionLeaves :: RegisteredCondition -> [Text]
conditionLeaves c = maybe [] (:[]) (registeredConditionLeaf c) ++ concatMap conditionLeaves (registeredConditionMembers c)
registrationsFor :: PresumptionDocument -> Text -> [AuthoredRegistration]
registrationsFor d key = filter (elem key . registeredAnalyses) (presumptionRegistrations d)

instance ToJSON RegisteredCondition where toJSON = genericToJSON jsonOptions
instance FromJSON RegisteredCondition where parseJSON = genericParseJSON jsonOptions
instance ToJSON AuthoredRegistration where toJSON = genericToJSON jsonOptions
instance FromJSON AuthoredRegistration where parseJSON = genericParseJSON jsonOptions
instance ToJSON PresumptionDocument where toJSON = genericToJSON jsonOptions
instance FromJSON PresumptionDocument where parseJSON = genericParseJSON jsonOptions
instance ToJSON PresumptionSnapshot where toJSON = genericToJSON jsonOptions
instance ToJSON PresumptionMapping where toJSON = genericToJSON jsonOptions
instance ToJSON ResolvedCondition where toJSON = genericToJSON jsonOptions
instance ToJSON RegistrationObservation where toJSON = genericToJSON jsonOptions
instance ToJSON EffectiveLeafObservation where toJSON = genericToJSON jsonOptions
instance ToJSON PresumptionReport where toJSON = genericToJSON jsonOptions
instance ToJSON PresumptionValidation where toJSON = genericToJSON jsonOptions
