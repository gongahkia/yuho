{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Projection.Types where

import Data.Aeson (ToJSON(..), genericToJSON)
import Data.Text (Text)
import GHC.Generics (Generic)
import Yuho.Authoring.Types
import Yuho.Authoring.Report (ApplicationReport, AssessmentChange, ObservationChange)

projectionFormat, projectionComparisonFormat, projectionViewFormat :: Text
projectionFormat = "yuho.analysis-projection/v0.1-experimental"
projectionComparisonFormat = "yuho.projection-comparison/v0.1-experimental"
projectionViewFormat = "yuho.projection-view/v0.1-experimental"

-- | Independent of assessment selection, analysis name and kernel numbering.
data OccurrenceIdentity = OccurrenceIdentity
  { occurrenceLawDigest :: Text, occurrenceTarget :: Text, occurrenceScope :: Scope
  , occurrenceAuthoredNode :: Text, occurrenceAuthoredRule :: Text
  , occurrenceEdges :: [Text]
  } deriving (Eq, Ord, Show, Generic)

-- | The run's original report category/key and kernel IDs, where available.
data ObservationIdentity = ObservationIdentity
  { observationRunSnapshot :: Text, observationProfile :: Text
  , observationCategory :: Text, observationAuthoredObject :: Text
  , observationAuthoredPath :: [Text], observationOriginalKernelId :: Maybe Text
  , observationOriginalBranchId :: Maybe Text
  } deriving (Eq, Ord, Show, Generic)

data ProjectionOrigin = ProjectionOrigin
  { originKind :: Text, originRole :: Text, originAuthoredObjects :: [Text]
  } deriving (Eq, Show, Generic)

data ProjectedBinding = ProjectedBinding
  { bindingState :: Text, bindingAssessment :: Maybe Text
  , bindingSupplied :: Maybe Classification, bindingReason :: Maybe Text
  } deriving (Eq, Show, Generic)

data ProjectionNode = ProjectionNode
  { projectedNodeId :: Text, projectedNodeKind :: Text, projectedNodeRole :: Text
  , projectedNodeLabel :: Text, projectedNodeOrigin :: ProjectionOrigin
  , projectedNodeOccurrence :: Maybe OccurrenceIdentity
  , projectedNodeObservation :: Maybe ObservationIdentity
  , projectedNodeSelected :: Maybe Bool, projectedNodeBinding :: Maybe ProjectedBinding
  , projectedNodeComputed :: Maybe Text, projectedNodeEvaluation :: Text
  , projectedNodeSkipReason :: Maybe Text, projectedNodeBranchReason :: Maybe Text
  } deriving (Eq, Show, Generic)

data ProjectionEdge = ProjectionEdge
  { projectedEdgeId :: Text, projectedEdgeFrom :: Text, projectedEdgeTo :: Text
  , projectedEdgeKind :: Text, projectedEdgeSemantics :: Text
  , projectedEdgeOrigin :: ProjectionOrigin
  , projectedEdgeOriginalSource :: Maybe SourceRef
  } deriving (Eq, Show, Generic)

data CompilerProvenance = CompilerProvenance
  { projectionGeneratedSources :: [GeneratedSource]
  , projectionCompilerIdentities :: [IdentityMapping]
  , projectionGeneratedSpans :: [SourceMapping]
  } deriving (Eq, Show, Generic)

-- | Full derived contract. The retained document is the authoring source.
data ProjectionData = ProjectionData
  { projectionVersion :: Text, projectionId :: Text, projectionMode :: Text
  , projectionSnapshot :: Snapshot, projectionApplication :: Maybe ApplicationReport
  , projectionCompiler :: Maybe CompilerProvenance
  , projectionNodes :: [ProjectionNode], projectionEdges :: [ProjectionEdge]
  , projectionDiagnostics :: [AuthoringDiagnostic], projectionOpenInputs :: [OpenInput]
  , projectionNotice :: Text
  } deriving (Eq, Show, Generic)

data ProjectedAssessmentChange = ProjectedAssessmentChange
  { assessmentChange :: AssessmentChange, assessmentChangeOccurrence :: Text
  , assessmentChangeOldNode :: Maybe Text, assessmentChangeNewNode :: Maybe Text
  } deriving (Eq, Show, Generic)

data ProjectedObservationChange = ProjectedObservationChange
  { observationChange :: ObservationChange
  , observationChangeAlignment :: Text
  , observationChangeOldNode :: Text, observationChangeNewNode :: Text
  , observationChangeOldIdentity :: ObservationIdentity
  , observationChangeNewIdentity :: ObservationIdentity
  , observationComputedFieldChanged :: Bool, observationComputedValueChanged :: Bool
  , observationEvaluationChanged :: Bool, observationReasonChanged :: Bool
  , observationBranchReasonChanged :: Bool
  } deriving (Eq, Show, Generic)

data ProjectionComparison = ProjectionComparison
  { projectionComparisonVersion :: Text
  , comparisonOldProjection :: Text, comparisonNewProjection :: Text
  , projectedAssessmentChanges :: [ProjectedAssessmentChange]
  , projectedChangedObservations :: [ProjectedObservationChange]
  , projectedUnchangedObservations :: [ProjectedObservationChange]
  , projectedOldConclusion :: Text, projectedNewConclusion :: Text
  , projectedConclusionChanged :: Bool
  } deriving (Eq, Show, Generic)

data ProjectionResolution = ProjectionResolution
  { resolvedSnapshot :: Text, resolvedAuthoredIds :: [Text]
  , resolvedLawNodes :: [LawNode], resolvedLawRelationships :: [LawEdge]
  , resolvedAssessments :: [Assessment], resolvedAssertions :: [CaseAssertion]
  , resolvedOriginalSources :: [SourceRecord], resolvedOriginalReferences :: [SourceRef]
  , resolvedRelationships :: [Relationship], resolvedAnnotations :: [Annotation]
  , resolvedGeneratedSpans :: [SourceMapping]
  } deriving (Eq, Show, Generic)

-- Explicitly identifies the selected rendering scope and every omitted object.
data ViewBinding = ViewBinding
  { viewBindingProjectedId :: Text, viewBindingRenderedId :: Text
  } deriving (Eq, Show, Generic)
data EdgeBinding = EdgeBinding
  { edgeBindingIndex :: Int, edgeBindingProjectedId :: Text
  , edgeBindingRenderedId :: Text
  } deriving (Eq, Show, Generic)
data ProjectionView = ProjectionView
  { viewVersion :: Text, viewId :: Text, viewProjectionId :: Text
  , viewScope :: Text, viewIncludedNodes :: [Text], viewIncludedEdges :: [Text]
  , viewOmittedNodes :: [Text], viewOmittedEdges :: [Text]
  , viewNodeBindings :: [ViewBinding], viewEdgeBindings :: [EdgeBinding]
  } deriving (Eq, Show, Generic)

instance ToJSON OccurrenceIdentity where toJSON = genericToJSON jsonOptions
instance ToJSON ObservationIdentity where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectionOrigin where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectedBinding where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectionNode where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectionEdge where toJSON = genericToJSON jsonOptions
instance ToJSON CompilerProvenance where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectionData where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectedAssessmentChange where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectedObservationChange where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectionComparison where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectionResolution where toJSON = genericToJSON jsonOptions
instance ToJSON ViewBinding where toJSON = genericToJSON jsonOptions
instance ToJSON EdgeBinding where toJSON = genericToJSON jsonOptions
instance ToJSON ProjectionView where toJSON = genericToJSON jsonOptions
