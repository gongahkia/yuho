{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Experimental, ground-only typed profile. These are not proof-profile nodes.
module Yuho.Authoring.Typed.Types where

import Data.Aeson
import Data.Text (Text)
import GHC.Generics (Generic)
import Yuho.Authoring.Typed.JSON (closedTaggedJSON)
import Yuho.Authoring.Types

typedAuthoringFormat, typedEvaluatorProfile, typedProjectionFormat :: Text
typedAuthoringFormat = "yuho.authoring/v0.3-experimental"
typedEvaluatorProfile = "TypedFiniteRules-v1"
typedProjectionFormat = "yuho.typed-analysis-projection/v0.3-experimental"

data TypedMeta = TypedMeta
  { typedId :: Text, typedLabel :: Text, typedCitation :: Maybe Text, typedSources :: [SourceRef] }
  deriving (Eq, Show, Generic)
newtype TypedEntityType = TypedEntityType { entityTypeMeta :: TypedMeta } deriving (Eq, Show, Generic)
data TypedEntity = TypedEntity
  { entityMeta :: TypedMeta, entityNominalType :: Text } deriving (Eq, Show, Generic)
data TypedArgument = TypedArgument
  { argumentRole :: Text, argumentType :: Text } deriving (Eq, Show, Generic)
data TypedPredicate = TypedPredicate
  { predicateMeta :: TypedMeta, predicateRoles :: [TypedArgument] } deriving (Eq, Show, Generic)
data GroundTuple = GroundTuple
  { tuplePredicate :: Text, tupleArguments :: [Text] } deriving (Eq, Ord, Show, Generic)
data TypedApplication = TypedApplication
  { applicationMeta :: TypedMeta, applicationTuple :: GroundTuple } deriving (Eq, Show, Generic)
data TypedScalar = TypedScalar
  { scalarMeta :: TypedMeta, scalarDeclaredType :: Text, scalarNormalisation :: Maybe Text }
  deriving (Eq, Show, Generic)
-- Public integer-only values. Unknown records retain their expected type; it
-- must match the declaration before the backend can propagate uncertainty.
data ExactScalar = ExactInteger Integer | UnknownInteger Text Text deriving (Eq, Show, Generic)
data TechnicalClassification = TechnicalTrue | TechnicalFalse | TechnicalUnresolved Text
  deriving (Eq, Show, Generic)
data TypedAssessment = TypedAssessment
  { typedAssessmentMeta :: TypedMeta, assessedApplication :: Text, assessedTuple :: GroundTuple
  , typedAssessmentScope :: Scope, typedClassification :: TechnicalClassification
  , typedAssessmentReason :: Text, typedIssuer :: Text, typedOrigin :: Text, typedBasis :: Text
  , typedAssertionRefs :: [Text] } deriving (Eq, Show, Generic)
data TypedValue = TypedValue
  { valueMeta :: TypedMeta, valueScalar :: Text, valueScope :: Scope, valueExact :: ExactScalar
  , valueReason :: Text, valueIssuer :: Text } deriving (Eq, Show, Generic)
-- Groups get children only from explicit typed_member edges. Reference nodes,
-- not, parameters and quantifiers are deliberately absent from this sum.
data TypedForm = GroundApplication Text | IntegerComparison Text Text Text | TypedAll | TypedAny
  deriving (Eq, Show, Generic)
data TypedExpression = TypedExpression
  { expressionMeta :: TypedMeta, expressionForm :: TypedForm } deriving (Eq, Show, Generic)
data TypedLink = TypedLink
  { typedLinkId :: Text, typedLinkFrom :: Text, typedLinkTo :: Text, typedLinkKind :: Text }
  deriving (Eq, Show, Generic)
data TypedRule = TypedRule
  { typedRuleMeta :: TypedMeta, typedRuleConclusion :: Text } deriving (Eq, Show, Generic)
newtype TypedProposition = TypedProposition { propositionMeta :: TypedMeta } deriving (Eq, Show, Generic)
data TypedAnalysis = TypedAnalysis
  { typedAnalysisId :: Text, typedAnalysisRule :: Text, typedAnalysisProposition :: Text
  , typedAnalysisScope :: Scope, selectedTypedAssessments :: [Text], selectedTypedValues :: [Text] }
  deriving (Eq, Show, Generic)
data TypedDocument = TypedDocument
  { typedDocumentFormat :: Text, typedDocumentId :: Text, typedLawId :: Text, typedLawRevision :: Text
  , typedEntityTypes :: [TypedEntityType], typedEntities :: [TypedEntity]
  , typedPredicates :: [TypedPredicate], typedApplications :: [TypedApplication]
  , typedScalars :: [TypedScalar], typedExpressions :: [TypedExpression], typedLinks :: [TypedLink]
  , typedRules :: [TypedRule], typedPropositions :: [TypedProposition]
  , typedAssessments :: [TypedAssessment], typedValues :: [TypedValue], typedAnalyses :: [TypedAnalysis]
  , typedOriginalSources :: [SourceRecord], typedCaseAssertions :: [CaseAssertion]
  , typedAnnotations :: [Annotation], typedPresentation :: [Presentation], typedLimitations :: [Text]
  } deriving (Eq, Show, Generic)

data TypedOpenInput = TypedOpenInput
  { typedOpenObject :: Text, typedOpenKind :: Text, typedOpenState :: Text
  , typedOpenPaths :: [[Text]], typedOpenSelection :: Maybe Text } deriving (Eq, Show, Generic)
data TypedValidation = TypedValidation
  { typedDocumentValid :: Bool, typedAnalysisReady :: Bool
  , typedDiagnostics :: [AuthoringDiagnostic], typedOpenInputs :: [TypedOpenInput] }
  deriving (Eq, Show, Generic)
data TypedSnapshot = TypedSnapshot
  { typedSnapshotId :: Text, typedLawDigest :: Text, typedSnapshotProfile :: Text
  , typedSnapshotAnalysis :: TypedAnalysis, typedSnapshotDocument :: TypedDocument }
  deriving (Eq, Show, Generic)
data TypedOccurrence = TypedOccurrence
  { typedOccurrenceLaw :: Text, typedOccurrenceRule :: Text, typedOccurrenceScope :: Scope
  , typedOccurrenceExpression :: Text, typedOccurrencePath :: [Text] }
  deriving (Eq, Show, Generic)
data TypedKernelMapping = TypedKernelMapping
  { typedMappingCategory :: Text, typedMappingKernelId :: Text, typedMappingAuthoredId :: Text
  , typedMappingPath :: [Text], typedMappingSources :: [SourceRef]
  , typedMappingGeneratedReason :: Maybe Text } deriving (Eq, Show, Generic)
data TypedObservation = TypedObservation
  { typedObservationId :: Text, typedObservationCategory :: Text, typedObservedObject :: Text
  , typedObservedKernelId :: Text, typedObservedStatus :: Text, typedObservedState :: Text
  , typedPropositionResolution :: Maybe Text
  , typedObservationOccurrence :: Maybe TypedOccurrence, typedObservationBackend :: Value }
  deriving (Eq, Show, Generic)
data TypedReport = TypedReport
  { typedReportSnapshot :: Text, typedReportAnalysis :: Text, typedReportScope :: Scope
  , typedReportRule :: Text, typedReportProposition :: Text, typedReportProfile :: Text
  , typedReportExpressions :: [TypedObservation], typedReportRules :: [TypedObservation]
  , typedReportPropositions :: [TypedObservation], typedReportMappings :: [TypedKernelMapping]
  , typedReportNotice :: Text }
  deriving (Eq, Show, Generic)

-- Metadata order is explicit and deterministic; IDs share one document namespace.
typedObjects :: TypedDocument -> [(Text,TypedMeta)]
typedObjects d = [("entity_type",entityTypeMeta x) | x <- typedEntityTypes d]
  ++ [("entity",entityMeta x) | x <- typedEntities d]
  ++ [("predicate",predicateMeta x) | x <- typedPredicates d]
  ++ [("application",applicationMeta x) | x <- typedApplications d]
  ++ [("scalar",scalarMeta x) | x <- typedScalars d]
  ++ [("expression",expressionMeta x) | x <- typedExpressions d]
  ++ [("rule",typedRuleMeta x) | x <- typedRules d]
  ++ [("proposition",propositionMeta x) | x <- typedPropositions d]
  ++ [("assessment",typedAssessmentMeta x) | x <- typedAssessments d]
  ++ [("value",valueMeta x) | x <- typedValues d]

instance ToJSON TypedMeta where toJSON = genericToJSON jsonOptions
instance FromJSON TypedMeta where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedEntityType where toJSON = genericToJSON jsonOptions
instance FromJSON TypedEntityType where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedEntity where toJSON = genericToJSON jsonOptions
instance FromJSON TypedEntity where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedArgument where toJSON = genericToJSON jsonOptions
instance FromJSON TypedArgument where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedPredicate where toJSON = genericToJSON jsonOptions
instance FromJSON TypedPredicate where parseJSON = genericParseJSON jsonOptions
instance ToJSON GroundTuple where toJSON = genericToJSON jsonOptions
instance FromJSON GroundTuple where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedApplication where toJSON = genericToJSON jsonOptions
instance FromJSON TypedApplication where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedScalar where toJSON = genericToJSON jsonOptions
instance FromJSON TypedScalar where parseJSON = genericParseJSON jsonOptions
instance ToJSON ExactScalar where toJSON = genericToJSON jsonOptions
instance FromJSON ExactScalar where
  parseJSON = closedTaggedJSON "ExactScalar" [("ExactInteger",True),("UnknownInteger",True)] (genericParseJSON jsonOptions)
instance ToJSON TechnicalClassification where toJSON = genericToJSON jsonOptions
instance FromJSON TechnicalClassification where
  parseJSON = closedTaggedJSON "TechnicalClassification"
    [("TechnicalTrue",False),("TechnicalFalse",False),("TechnicalUnresolved",True)] (genericParseJSON jsonOptions)
instance ToJSON TypedAssessment where toJSON = genericToJSON jsonOptions
instance FromJSON TypedAssessment where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedValue where toJSON = genericToJSON jsonOptions
instance FromJSON TypedValue where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedForm where toJSON = genericToJSON jsonOptions
instance FromJSON TypedForm where
  parseJSON = closedTaggedJSON "TypedForm"
    [("GroundApplication",True),("IntegerComparison",True),("TypedAll",False),("TypedAny",False)] (genericParseJSON jsonOptions)
instance ToJSON TypedExpression where toJSON = genericToJSON jsonOptions
instance FromJSON TypedExpression where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedLink where toJSON = genericToJSON jsonOptions
instance FromJSON TypedLink where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedRule where toJSON = genericToJSON jsonOptions
instance FromJSON TypedRule where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedProposition where toJSON = genericToJSON jsonOptions
instance FromJSON TypedProposition where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedAnalysis where toJSON = genericToJSON jsonOptions
instance FromJSON TypedAnalysis where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedDocument where toJSON = genericToJSON jsonOptions
instance FromJSON TypedDocument where parseJSON = genericParseJSON jsonOptions
instance ToJSON TypedOpenInput where toJSON = genericToJSON jsonOptions
instance ToJSON TypedValidation where toJSON = genericToJSON jsonOptions
instance ToJSON TypedSnapshot where toJSON = genericToJSON jsonOptions
instance ToJSON TypedOccurrence where toJSON = genericToJSON jsonOptions
instance ToJSON TypedKernelMapping where toJSON = genericToJSON jsonOptions
instance ToJSON TypedObservation where toJSON = genericToJSON jsonOptions
instance ToJSON TypedReport where toJSON = genericToJSON jsonOptions
