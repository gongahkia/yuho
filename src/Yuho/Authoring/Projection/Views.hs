{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Two bounded selections over an existing complete projection.
module Yuho.Authoring.Projection.Views
  ( ApplicationFocus(..), caseView, applicationView, validateProjectionView ) where

import Data.Aeson (ToJSON(..), genericToJSON)
import Data.List (find, nub, sort, sortOn)
import qualified Data.Set as Set
import Data.Text (Text)
import GHC.Generics (Generic)
import Yuho.Authoring.Projection
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue)

data ApplicationFocus = FocusInput Text | FocusOccurrence Text | FocusAssessments [Text]
  deriving (Eq, Show, Generic)
instance ToJSON ApplicationFocus where toJSON = genericToJSON jsonOptions

-- Includes every assertion, its direct sources, descriptive relationships
-- incident on those objects (both endpoints), and directly relevant annotations.
-- The one-hop endpoint rule preserves challenges to assessments without expanding
-- their application neighbourhood. Unmapped assertions are never filtered.
caseView :: Projection -> Either [AuthoringDiagnostic] ProjectionView
caseView projection =
  let doc = snapshotDocument (projectionSnapshot (projectionData projection))
      assertions = map assertionId (documentAssertions doc)
      sources = [referenceSource ref | a <- documentAssertions doc, ref <- assertionSources a]
      base = nub (assertions ++ sources)
      relationships = [r | r <- documentRelationships doc,
        elem (relationshipFrom r) base || elem (relationshipTo r) base]
      endpoints = concat [[relationshipFrom r,relationshipTo r] | r <- relationships]
      related = base ++ endpoints ++ map relationshipId relationships
      annotations = [a | a <- documentAnnotations doc, any (\key -> elem key related) (annotationAbout a)]
      handles = [relationshipId r | r <- relationships,
        any (elem (relationshipId r) . annotationAbout) annotations]
      nodes = map objectProjectionId (nub (base ++ endpoints ++ handles ++ map annotationId annotations))
      kinds = ["assertion_source","annotation_about","chronology","support","challenge",
        "relationship_subject","relationship_object"]
  in makeView projection ("case" :: Text) nodes kinds
    "Case: all authored assertions, direct original sources, one-hop descriptive endpoints and relevant annotations. No legal relevance is inferred from absent assessment links."

-- Input/occurrence focus includes the selected binding and retained alternatives
-- for that input in the analysis scope. Explicit assessment focus includes only
-- the named assessments; unselected assessments do not gain a run observation.
applicationView :: Projection -> ApplicationFocus -> Either [AuthoringDiagnostic] ProjectionView
applicationView projection focus = do
  let value = projectionData projection
      snapshot = projectionSnapshot value
      doc = snapshotDocument snapshot
      scope = analysisScope (snapshotAnalysis snapshot)
      occurrences = [n | n <- projectionNodes value, projectedNodeKind n == "occurrence",
        projectedNodeRole n == "input"]
      assessmentsFor n = [a | a <- documentAssessments doc, assessmentScope a == scope,
        maybe False ((== assessmentInput a) . occurrenceAuthoredNode) (projectedNodeOccurrence n)]
      focusError objects message = Left [issue "PFOCUS" "/applicationFocus" objects message]
  (assessments,focusedOccurrences) <- case focus of
    FocusInput key -> case [n | n <- occurrences,
        maybe False ((== key) . occurrenceAuthoredNode) (projectedNodeOccurrence n)] of
      [n] -> Right (assessmentsFor n,[n])
      _ -> focusError [key] "input must identify one input occurrence in the selected analysis"
    FocusOccurrence key -> case find ((== key) . projectedNodeId) occurrences of
      Just n -> Right (assessmentsFor n,[n])
      Nothing -> focusError [key] "focus must identify a projected input occurrence"
    FocusAssessments keys
      | null keys || length keys /= length (nub keys) -> focusError keys "select one to four distinct assessment IDs"
      | otherwise -> do
          selected <- traverse (\key -> maybe (focusError [key] "assessment not found") Right
            (find ((== key) . assessmentId) (documentAssessments doc))) keys
          let activeOccurrences = [n | n <- occurrences,
                elem (projectedNodeBinding n >>= bindingAssessment) (map (Just . assessmentId) selected)]
          Right (selected,activeOccurrences)
  if length assessments <= 4 then pure () else
    focusError (map assessmentId assessments) "focus exceeds four assessments; use a smaller explicit assessment selection"
  let assertionIds = nub (concatMap assessmentAssertions assessments)
      assertions = [a | a <- documentAssertions doc, elem (assertionId a) assertionIds]
      targets = [n | n <- lawNodes (documentLaw doc), elem (nodeId n) (map assessmentInput assessments)
        || any (maybe False ((== nodeId n) . occurrenceAuthoredNode) . projectedNodeOccurrence) focusedOccurrences]
      sourceIds = nub (map referenceSource (concatMap assessmentSources assessments
        ++ concatMap assertionSources assertions ++ concatMap nodeSources targets))
      base = map assessmentId assessments ++ assertionIds ++ sourceIds ++ map nodeId targets
      annotations = [a | a <- documentAnnotations doc, any (\key -> elem key base) (annotationAbout a)]
      observationIds = [observationProjectionId o | n <- focusedOccurrences,
        Just o <- [projectedNodeObservation n]]
      nodes = map objectProjectionId (nub (base ++ map annotationId annotations))
        ++ map projectedNodeId focusedOccurrences ++ observationIds
      kinds = ["assessment_assertion","assessment_source","assertion_source","assessment_input",
        "law_source","selected_assessment","instance_of","observes","annotation_about","chronology","support","challenge"]
  makeView projection focus nodes kinds
    "Application: explicit focus, assessment provenance and legal targets. Alternatives retain supplied classifications; only selected bindings have associated run observations. Remaining context is omitted explicitly."

makeView :: ToJSON a => Projection -> a -> [Text] -> [Text] -> Text
         -> Either [AuthoringDiagnostic] ProjectionView
makeView projection selection included kinds scope = do
  let value = projectionData projection
      allNodes = projectionNodes value
      nodeIds = Set.fromList included
      rank n = case projectedNodeRole n of
        "assertion" -> 0 :: Int
        "original_source" -> 1
        "assessment" -> 2
        "annotation" -> 6
        _ | projectedNodeKind n == "occurrence" -> 4
          | projectedNodeKind n == "observation" -> 5
          | otherwise -> 3
      nodes = map projectedNodeId (sortOn rank [n | n <- allNodes, Set.member (projectedNodeId n) nodeIds])
      edges = [e | e <- projectionEdges value, elem (projectedEdgeKind e) kinds,
        Set.member (projectedEdgeFrom e) nodeIds, Set.member (projectedEdgeTo e) nodeIds]
      edgeIds = map projectedEdgeId edges
      view = ProjectionView projectionViewFormat
        (projectionIdentity "view" (projectionId value,selection,nodes,edgeIds)) (projectionId value) scope
        nodes edgeIds [projectedNodeId n | n <- allNodes, Set.notMember (projectedNodeId n) nodeIds]
        [projectedEdgeId e | e <- projectionEdges value, not (elem (projectedEdgeId e) edgeIds)]
        [ViewBinding key ("node-" <> key) | key <- nodes]
        [EdgeBinding i key ("edge-" <> key) | (i,key) <- zip [0..] edgeIds]
      missing = [key | key <- included, not (elem key (map projectedNodeId allNodes))]
      diagnostics = validateProjectionView projection view ++
        [issue "PVIEW" "/viewIncludedNodes" missing "requested projected objects are absent" | not (null missing)]
        ++ [issue "PVIEWLIMIT" "/viewIncludedNodes" [] "reference view exceeds 64 nodes or 128 relationships"
           | length nodes > 64 || length edges > 128]
  if null diagnostics then Right view else Left diagnostics

-- Public view records can be passed back to encoders. Validate complete
-- partitions, endpoint closure and exact DOM/index bindings before rendering.
validateProjectionView :: Projection -> ProjectionView -> [AuthoringDiagnostic]
validateProjectionView projection view = validateProjection value ++ mismatch ++ partitionErrors ++ endpointErrors ++ bindings
  where
    value = projectionData projection
    ns = viewIncludedNodes view
    es = viewIncludedEdges view
    allNodes = map projectedNodeId (projectionNodes value)
    allEdges = map projectedEdgeId (projectionEdges value)
    bad code objects message = issue code "/projectionView" objects message
    mismatch = [bad "PVIEWSTALE" [] "view version or projection identity does not match"
      | viewVersion view /= projectionViewFormat || viewProjectionId view /= projectionId value]
    partitionErrors = [bad "PVIEWPARTITION" [] "included and omitted objects must partition the complete projection"
      | sort (ns ++ viewOmittedNodes view) /= sort allNodes
        || sort (es ++ viewOmittedEdges view) /= sort allEdges]
    endpointErrors = [bad "PVIEWENDPOINT" [projectedEdgeId e] "included edge has an omitted endpoint"
      | e <- projectionEdges value, elem (projectedEdgeId e) es,
        not (elem (projectedEdgeFrom e) ns && elem (projectedEdgeTo e) ns)]
    bindings = [bad "PVIEWBINDING" [] "DOM or edge-index bindings do not match the selected objects"
      | viewNodeBindings view /= [ViewBinding key ("node-" <> key) | key <- ns]
        || viewEdgeBindings view /= [EdgeBinding i key ("edge-" <> key) | (i,key) <- zip [0..] es]]
