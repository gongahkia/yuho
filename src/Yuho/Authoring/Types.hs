{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Experimental authoring format. This module is not a stable API promise.
module Yuho.Authoring.Types where

import Data.Aeson
import Data.Map.Strict (Map)
import Data.Text (Text)
import Data.Time.Calendar (Day)
import GHC.Generics (Generic)
import qualified Yuho.SuppliedProofStatus.Types as Proof

authoringFormat, linkedAuthoringFormat, evaluatorProfile :: Text
authoringFormat = "yuho.authoring/v0.1-experimental"
-- | Explicit opt-in: definition nodes, defines bodies and use references.
-- Existing records and v0.1 interpretation remain unchanged.
linkedAuthoringFormat = "yuho.authoring/v0.2-experimental"
evaluatorProfile = "SuppliedProofStatus-v1"

-- | Half-open UTF-8 byte offsets and one-based UTF-8 byte columns.
data TextSpan = TextSpan
  { start :: Int, end :: Int, startLine :: Int, startColumn :: Int
  , endLine :: Int, endColumn :: Int
  } deriving (Eq, Show, Generic)

data SourceRecord = SourceRecord
  { sourceId :: Text, sourceKind :: Text, sourceLocator :: Maybe Text
  , sourceText :: Maybe Text
  } deriving (Eq, Show, Generic)

data SourceRef = SourceRef
  { referenceSource :: Text, referenceSpan :: Maybe TextSpan
  } deriving (Eq, Show, Generic)

data LawNode = LawNode
  { nodeId :: Text, nodeKind :: Text, nodeLabel :: Text
  , nodeQuotation :: Maybe Text, nodeCitation :: Maybe Text
  , nodeSources :: [SourceRef]
  } deriving (Eq, Show, Generic)

-- | Direction: rule -> requirement (requires), group -> child (member),
-- main rule -> exception rule (exception). Array order preserves child order.
data LawEdge = LawEdge
  { edgeId :: Text, edgeFrom :: Text, edgeTo :: Text, edgeKind :: Text
  } deriving (Eq, Show, Generic)

data LawDefinition = LawDefinition
  { lawId :: Text, lawRevision :: Text, lawNodes :: [LawNode]
  , lawEdges :: [LawEdge], lawScope :: [Text]
  } deriving (Eq, Show, Generic)

data Scope = Scope { scopeActor :: Text, scopeContext :: Text }
  deriving (Eq, Ord, Show, Generic)

data CaseAssertion = CaseAssertion
  { assertionId :: Text, assertionDescription :: Text
  , assertionScope :: Scope, assertionSources :: [SourceRef]
  } deriving (Eq, Show, Generic)

-- | Uses the backend's supplied constructors, without orphan JSON instances.
newtype Classification = Classification { classificationStatus :: Proof.SuppliedStatus }
  deriving (Eq, Show)

data Assessment = Assessment
  { assessmentId :: Text, assessmentInput :: Text, assessmentScope :: Scope
  , assessmentClassification :: Classification, assessmentReason :: Text
  , assessmentIssuer :: Text, assessmentOrigin :: Text, assessmentBasis :: Text
  , assessmentAssertions :: [Text], assessmentSources :: [SourceRef]
  } deriving (Eq, Show, Generic)

data Analysis = Analysis
  { analysisId :: Text, analysisTarget :: Text, analysisScope :: Scope
  , analysisAssessments :: [Text], analysisReferenceDate :: Day
  } deriving (Eq, Show, Generic)

-- | These relationships never enter the evaluator.
data Relationship = Relationship
  { relationshipId :: Text, relationshipKind :: Text
  , relationshipFrom :: Text, relationshipTo :: Text, relationshipComment :: Text
  } deriving (Eq, Show, Generic)

data Annotation = Annotation
  { annotationId :: Text, annotationAbout :: [Text], annotationText :: Text
  , annotationState :: Text
  } deriving (Eq, Show, Generic)

-- | Presentation values are strings (including coordinates), not semantics.
data Presentation = Presentation
  { presentationObject :: Text, presentationProperties :: Map Text Text
  } deriving (Eq, Show, Generic)

data AuthoringDocument = AuthoringDocument
  { documentFormat :: Text, documentId :: Text, documentLaw :: LawDefinition
  , documentSources :: [SourceRecord], documentAssertions :: [CaseAssertion]
  , documentAssessments :: [Assessment], documentAnalyses :: [Analysis]
  , documentRelationships :: [Relationship], documentAnnotations :: [Annotation]
  , documentPresentation :: [Presentation]
  } deriving (Eq, Show, Generic)

data AuthoringDiagnostic = AuthoringDiagnostic
  { diagnosticCode :: Text, diagnosticLocation :: Text
  , diagnosticObjects :: [Text], diagnosticMessage :: Text
  } deriving (Eq, Show, Generic)

data OpenInput = OpenInput
  { openInputId :: Text, openOccurrence :: [Text], openRule :: Text
  , openScope :: Scope, openState :: Text, openAssessment :: Maybe Text
  } deriving (Eq, Show, Generic)

data ValidationReport = ValidationReport
  { documentValid :: Bool, analysisReady :: Bool
  , validationDiagnostics :: [AuthoringDiagnostic], openInputs :: [OpenInput]
  } deriving (Eq, Show, Generic)

-- | A structural occurrence is an ordered path of authored relationship IDs.
data RequirementMapping = RequirementMapping
  { mappedNode :: Text, mappedOccurrence :: [Text], mappedRule :: Text
  , mappedKernelRequirement :: Text, mappedKernelRule :: Text
  , mappedKernelBranch :: Text, mappedAssessment :: Maybe Text
  , mappedAssignment :: Maybe Text
  } deriving (Eq, Show, Generic)

data GeneratedSource = GeneratedSource
  { generatedSourceId :: Text, generatedSourceKind :: Text
  , generatedSourceText :: Text, generatedSourceObjects :: [Text]
  } deriving (Eq, Show, Generic)

data IdentityMapping = IdentityMapping
  { identityKernelId :: Text, identityKind :: Text, identityAuthoredIds :: [Text]
  } deriving (Eq, Show, Generic)

data SourceMapping = SourceMapping
  { sourceMappingKernelId :: Text, sourceMappingSource :: Text
  , sourceMappingSpan :: TextSpan, sourceMappingObjects :: [Text]
  , sourceMappingOriginals :: [SourceRef]
  } deriving (Eq, Show, Generic)

data Snapshot = Snapshot
  { snapshotId :: Text, snapshotLawDigest :: Text, snapshotProfile :: Text
  , snapshotAnalysis :: Analysis, snapshotDocument :: AuthoringDocument
  } deriving (Eq, Show, Generic)

jsonOptions :: Options
jsonOptions = defaultOptions { rejectUnknownFields = True }

instance ToJSON Classification where
  toJSON (Classification status) = case status of
    Proof.Proved -> object ["kind" .= ("proved" :: Text)]
    Proof.NotProved -> object ["kind" .= ("not_proved" :: Text)]
    Proof.Unresolved reason -> object ["kind" .= ("unresolved" :: Text),
      "reason" .= (case reason of
        Proof.NotDetermined -> "not_determined" :: Text
        Proof.ExternalDecisionPending -> "external_decision_pending")]
instance FromJSON Classification where
  parseJSON = withObject "Classification" $ \obj -> do
    kind <- obj .: "kind"
    case (kind :: Text) of
      "proved" | length obj == 1 -> pure (Classification Proof.Proved)
      "not_proved" | length obj == 1 -> pure (Classification Proof.NotProved)
      "unresolved" | length obj == 2 -> do
        reason <- obj .: "reason"
        Classification . Proof.Unresolved <$> case (reason :: Text) of
          "not_determined" -> pure Proof.NotDetermined
          "external_decision_pending" -> pure Proof.ExternalDecisionPending
          _ -> fail "unsupported unresolved reason"
      _ -> fail "unsupported supplied classification or fields"

instance ToJSON TextSpan where toJSON = genericToJSON jsonOptions
instance FromJSON TextSpan where parseJSON = genericParseJSON jsonOptions
instance ToJSON SourceRecord where toJSON = genericToJSON jsonOptions
instance FromJSON SourceRecord where parseJSON = genericParseJSON jsonOptions
instance ToJSON SourceRef where toJSON = genericToJSON jsonOptions
instance FromJSON SourceRef where parseJSON = genericParseJSON jsonOptions
instance ToJSON LawNode where toJSON = genericToJSON jsonOptions
instance FromJSON LawNode where parseJSON = genericParseJSON jsonOptions
instance ToJSON LawEdge where toJSON = genericToJSON jsonOptions
instance FromJSON LawEdge where parseJSON = genericParseJSON jsonOptions
instance ToJSON LawDefinition where toJSON = genericToJSON jsonOptions
instance FromJSON LawDefinition where parseJSON = genericParseJSON jsonOptions
instance ToJSON Scope where toJSON = genericToJSON jsonOptions
instance FromJSON Scope where parseJSON = genericParseJSON jsonOptions
instance ToJSON CaseAssertion where toJSON = genericToJSON jsonOptions
instance FromJSON CaseAssertion where parseJSON = genericParseJSON jsonOptions
instance ToJSON Assessment where toJSON = genericToJSON jsonOptions
instance FromJSON Assessment where parseJSON = genericParseJSON jsonOptions
instance ToJSON Analysis where toJSON = genericToJSON jsonOptions
instance FromJSON Analysis where parseJSON = genericParseJSON jsonOptions
instance ToJSON Relationship where toJSON = genericToJSON jsonOptions
instance FromJSON Relationship where parseJSON = genericParseJSON jsonOptions
instance ToJSON Annotation where toJSON = genericToJSON jsonOptions
instance FromJSON Annotation where parseJSON = genericParseJSON jsonOptions
instance ToJSON Presentation where toJSON = genericToJSON jsonOptions
instance FromJSON Presentation where parseJSON = genericParseJSON jsonOptions
instance ToJSON AuthoringDocument where toJSON = genericToJSON jsonOptions
instance FromJSON AuthoringDocument where parseJSON = genericParseJSON jsonOptions
instance ToJSON AuthoringDiagnostic where toJSON = genericToJSON jsonOptions
instance ToJSON OpenInput where toJSON = genericToJSON jsonOptions
instance ToJSON ValidationReport where toJSON = genericToJSON jsonOptions
instance ToJSON RequirementMapping where toJSON = genericToJSON jsonOptions
instance ToJSON GeneratedSource where toJSON = genericToJSON jsonOptions
instance ToJSON IdentityMapping where toJSON = genericToJSON jsonOptions
instance ToJSON SourceMapping where toJSON = genericToJSON jsonOptions
instance ToJSON Snapshot where toJSON = genericToJSON jsonOptions
