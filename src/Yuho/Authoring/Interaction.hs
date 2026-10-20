{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Pure navigation over one retained projection. Focus is not an authored edit.
module Yuho.Authoring.Interaction
  ( RequirementFocus(..), RequirementExplanation(..), RequirementNeighbour(..)
  , AssessmentContext(..), ExplanationOptions(..), defaultExplanationOptions
  , focusRequirement, explanationView ) where

import Data.Aeson (ToJSON(..), genericToJSON)
import Data.List (find, nub)
import Data.Maybe (mapMaybe)
import Data.Text (Text)
import GHC.Generics (Generic)
import Yuho.Authoring.Projection
import Yuho.Authoring.Projection.Inspect
import Yuho.Authoring.Projection.Views (validateProjectionView)
import Yuho.Authoring.Report
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue)

-- | Authored IDs are resolved within this projection's selected analysis/scope.
-- Occurrence handles must come from the same law/target/scope, not another run's
-- observation ID or a definition handle.
data RequirementFocus = AuthoredRequirement Text | RequirementOccurrence Text
  deriving (Eq, Show, Generic)

-- | Sources remain references here; recoverOriginalSource reveals text on demand.
-- Applications of unselected assessments have no attributed run computation.
data AssessmentContext = AssessmentContext
  { contextAssessment :: Assessment, contextProjectedId :: Text
  , contextSelected :: Bool, contextAssertions :: [CaseAssertion]
  , contextAssertionLinks :: [AssertionLinks], contextSourceReferences :: [SourceRef]
  , contextApplications :: [AssessmentApplication]
  } deriving (Eq, Show, Generic)

data RequirementNeighbour = RequirementNeighbour
  { neighbourLaw :: LawNode, neighbourOccurrence :: ProjectionNode
  , neighbourObservation :: Maybe ProjectionNode, neighbourConnection :: ProjectionEdge
  , neighbourAuthoredRelationships :: [LawEdge]
  } deriving (Eq, Show, Generic)

data RequirementExplanation = RequirementExplanation
  { explanationSnapshot :: Text, explanationProjection :: Text
  , explanationLawId :: Text, explanationLawRevision :: Text
  , explanationAnalysis :: Analysis, explanationDefinition :: LawNode
  , explanationDefinitionId :: Text, explanationOccurrence :: ProjectionNode
  , explanationObservation :: Maybe ProjectionNode
  , explanationSelected :: Maybe AssessmentContext
  , explanationAlternatives :: [AssessmentContext]
  , explanationDependencies :: [RequirementNeighbour]
  , explanationParents :: [RequirementNeighbour]
  , explanationAncestors :: [RequirementNeighbour]
  , explanationSourceReferences :: [SourceRef]
  , explanationRules :: [RuleObservation], explanationExceptions :: [ExceptionObservation]
  } deriving (Eq, Show, Generic)

-- | Optional display detail, never stored in an authored document or snapshot.
-- Explicit source IDs prevent opening an entire stipulation packet by default.
data ExplanationOptions = ExplanationOptions
  { includeAlternativeAssessments :: Bool, expandedOriginalSources :: [Text]
  } deriving (Eq, Show, Generic)

defaultExplanationOptions :: ExplanationOptions
defaultExplanationOptions = ExplanationOptions False []

focusRequirement :: Projection -> RequirementFocus
                 -> Either [AuthoringDiagnostic] RequirementExplanation
focusRequirement projection focus = do
  let value = projectionData projection
      snapshot = projectionSnapshot value
      doc = snapshotDocument snapshot
      law = documentLaw doc
      analysis = snapshotAnalysis snapshot
      nodes = projectionNodes value
      occurrences = [n | n <- nodes, projectedNodeKind n == "occurrence"]
      matching = case focus of
        AuthoredRequirement key -> [n | n <- occurrences,
          maybe False ((== key) . occurrenceAuthoredNode) (projectedNodeOccurrence n)]
        RequirementOccurrence key -> filter ((== key) . projectedNodeId) occurrences
      requested = case focus of { AuthoredRequirement key -> key; RequirementOccurrence key -> key }
      bad message = Left [issue "IFOCUS" "/requirementFocus" [requested,analysisId analysis] message]
  occurrence <- case matching of
    [n] -> Right n
    [] -> bad "no requirement occurrence in this analysis/scope; use an authored requirement ID or its structural occurrence handle"
    _ -> bad "authored requirement has multiple occurrences; use an explicit structural occurrence handle"
  definition <- case projectedNodeOccurrence occurrence >>= \o ->
      find ((== occurrenceAuthoredNode o) . nodeId) (lawNodes law) of
    Just n -> Right n
    Nothing -> bad "occurrence has no authored law definition"
  let observation n = projectedNodeObservation n >>= \identity ->
        find ((== observationProjectionId identity) . projectedNodeId) nodes
      neighbour edge key = do
        n <- find ((== key) . projectedNodeId) occurrences
        identity <- projectedNodeOccurrence n
        original <- find ((== occurrenceAuthoredNode identity) . nodeId) (lawNodes law)
        pure (RequirementNeighbour original n (observation n) edge
          [e | e <- lawEdges law, elem (edgeId e) (originAuthoredObjects (projectedEdgeOrigin edge))])
      structural = filter ((== "occurrence_structure") . projectedEdgeSemantics) (projectionEdges value)
      children n = mapMaybe (\e -> neighbour e (projectedEdgeTo e))
        [e | e <- structural, projectedEdgeFrom e == projectedNodeId n]
      parents n = mapMaybe (\e -> neighbour e (projectedEdgeFrom e))
        [e | e <- structural, projectedEdgeTo e == projectedNodeId n]
      ancestors n = concat [p : ancestors (neighbourOccurrence p) | p <- parents n]
      compatible = [a | a <- documentAssessments doc, nodeKind definition == "input",
        assessmentInput a == nodeId definition, assessmentScope a == analysisScope analysis]
      selectedId = projectedNodeBinding occurrence >>= bindingAssessment
      describe a = do
        detail <- inspectAssessment projection (assessmentId a)
        let assertions = resolvedAssertions (inspectionResolution detail)
        links <- traverse (caseAssertionLinks projection . assertionId) assertions
        pure (AssessmentContext a (inspectionProjectedAssessment detail) (inspectionSelected detail)
          assertions links (nub (assessmentSources a ++ concatMap assertionSources assertions))
          (inspectionApplications detail))
  assessments <- traverse describe compatible
  let selected = find ((== selectedId) . Just . assessmentId . contextAssessment) assessments
      alternatives = filter (not . contextSelected) assessments
  pure (RequirementExplanation (snapshotId snapshot) (projectionId value) (lawId law) (lawRevision law)
    analysis definition (objectProjectionId (nodeId definition)) occurrence (observation occurrence)
    selected alternatives (children occurrence) (parents occurrence) (ancestors occurrence)
    (nub (nodeSources definition ++ concatMap contextSourceReferences assessments))
    (maybe [] reportRules (projectionApplication value)) (maybe [] reportExceptions (projectionApplication value)))

-- | An ordered adapter into the existing view contract and encoders. The
-- occurrence (including its result) comes first, then the selected assessment,
-- case assertions, requested sources and explicitly requested alternatives.
-- Definition/observation handles and distant context stay in the full projection
-- and explanation; every omission is recorded. No status is invented or copied.
explanationView :: Projection -> RequirementFocus -> ExplanationOptions
                -> Either [AuthoringDiagnostic] ProjectionView
explanationView projection focus options = do
  explanation <- focusRequirement projection focus
  let value = projectionData projection
      selected = maybe [] (:[]) (explanationSelected explanation)
      alternatives = if includeAlternativeAssessments options then explanationAlternatives explanation else []
      contexts = selected ++ alternatives
      occurrence = explanationOccurrence explanation
      sourceIds = expandedOriginalSources options
      permittedSources = nub (map referenceSource (nodeSources (explanationDefinition explanation)
        ++ concatMap contextSourceReferences contexts))
      failView code objects message = Left [issue code "/explanationView" objects message]
  if length sourceIds == length (nub sourceIds) && all (`elem` permittedSources) sourceIds
    then pure () else failView "ISOURCE" sourceIds "expanded sources must be distinct original source IDs referenced by this focus"
  if length contexts <= 4 then pure () else failView "PVIEWLIMIT"
    (map (assessmentId . contextAssessment) contexts) "reference view exceeds four assessments; use a smaller explicit application focus"
  let selectedAssertions = nub (concatMap (map assertionId . contextAssertions) selected)
      otherAssertions = [key | c <- alternatives, a <- contextAssertions c,
        let key = assertionId a, not (elem key selectedAssertions)]
      requested = nub (projectedNodeId occurrence : map contextProjectedId selected
        ++ map objectProjectionId selectedAssertions
        ++ [explanationDefinitionId explanation | not (null alternatives)
              || any ((`elem` sourceIds) . referenceSource) (nodeSources (explanationDefinition explanation))]
        ++ map objectProjectionId sourceIds
        ++ map contextProjectedId alternatives ++ map objectProjectionId otherAssertions
        ++ map (projectedNodeId . neighbourOccurrence) (explanationDependencies explanation))
      kinds = ["selected_assessment","assessment_assertion","assessment_source","assertion_source",
        "law_source","instance_of","assessment_input","member","requires","use","defines","definition_use",
        "exception","chronology","support","challenge"]
      edges = [e | e <- projectionEdges value, elem (projectedEdgeKind e) kinds,
        elem (projectedEdgeFrom e) requested, elem (projectedEdgeTo e) requested]
      edgeIds = map projectedEdgeId edges
      allNodes = map projectedNodeId (projectionNodes value)
      view = ProjectionView projectionViewFormat
        (projectionIdentity "view" (projectionId value,focus,options,requested,edgeIds)) (projectionId value)
        "Requirement explanation: result, selected assessment, then case material. Sources and alternatives expand only on request. Full identities and omitted context remain in the complete projection."
        requested edgeIds (filter (`notElem` requested) allNodes)
        [projectedEdgeId e | e <- projectionEdges value, not (elem (projectedEdgeId e) edgeIds)]
        [ViewBinding key ("node-" <> key) | key <- requested]
        [EdgeBinding i key ("edge-" <> key) | (i,key) <- zip [0..] edgeIds]
      diagnostics = validateProjectionView projection view
  if null diagnostics then pure () else Left diagnostics
  if length requested <= 64 && length edges <= 128 then Right view else
    failView "PVIEWLIMIT" [] "reference view exceeds 64 nodes or 128 relationships; no objects were truncated"

instance ToJSON RequirementFocus where toJSON = genericToJSON jsonOptions
instance ToJSON AssessmentContext where toJSON = genericToJSON jsonOptions
instance ToJSON RequirementNeighbour where toJSON = genericToJSON jsonOptions
instance ToJSON RequirementExplanation where toJSON = genericToJSON jsonOptions
instance ToJSON ExplanationOptions where toJSON = genericToJSON jsonOptions
