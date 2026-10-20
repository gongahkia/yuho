{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Inspection of explicit reusable expressions, not rule-result chaining.
module Yuho.Authoring.Definitions
  ( DefinitionInspection(..), DefinitionOccurrence(..)
  , inspectDefinition, inspectDefinitionOccurrence
  , definitionView, definitionOccurrenceView ) where

import Data.Aeson (ToJSON(..), genericToJSON)
import Data.List (find, nub)
import Data.Text (Text)
import GHC.Generics (Generic)
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Interaction
import Yuho.Authoring.Projection
import Yuho.Authoring.Projection.Views (validateProjectionView)
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue, occurrenceDefinitions)
import Yuho.Protocol.Decode (sha256Text)

data DefinitionInspection = DefinitionInspection
  { sharedDefinition :: LawNode, sharedDefinitionDigest :: Text
  , sharedBodyNodes :: [LawNode], sharedBodyEdges :: [LawEdge]
  , sharedOriginalSources :: [SourceRecord], sharedUses :: [LawEdge]
  , sharedReferencingRules :: [LawNode], sharedOccurrences :: [DefinitionOccurrence]
  } deriving (Eq, Show, Generic)

data DefinitionOccurrence = DefinitionOccurrence
  { linkedDefinition :: LawNode, linkedDefinitionDigest :: Text
  , linkedAnalysis :: Analysis, linkedReferencePath :: [LawEdge]
  , linkedRequirement :: RequirementExplanation
  , linkedKernelMappings :: [IdentityMapping]
  , linkedOriginalReferences :: [SourceRef]
  } deriving (Eq, Show, Generic)

-- Document-wide meaning is single-authored; occurrences are only those in the
-- selected projection. Other rules/uses remain inspectable without evaluation.
inspectDefinition :: Projection -> Text -> Either [AuthoringDiagnostic] DefinitionInspection
inspectDefinition projection key = do
  let value = projectionData projection
      doc = snapshotDocument (projectionSnapshot value)
      law = documentLaw doc
      nodes = lawNodes law
      edges = lawEdges law
      failDefinition = Left [issue "DDEFINITION" "/definitionFocus" [key]
        "focus must name an explicit definition in a v0.2 authored document"]
  definition <- case find ((== key) . nodeId) nodes of
    Just n | documentFormat doc == linkedAuthoringFormat, nodeKind n == "definition" -> Right n
    _ -> failDefinition
  let bodyIds = closure (\current -> [edgeTo e | e <- edges, edgeFrom e == current,
        edgeKind e `elem` ["defines","member","use"]]) [key]
      bodyNodes = filter ((`elem` bodyIds) . nodeId) nodes
      bodyEdges = [e | e <- edges, edgeFrom e `elem` bodyIds,
        edgeKind e `elem` ["defines","member","use"]]
      originals = [s | s <- documentSources doc, sourceId s `elem`
        map referenceSource (concatMap nodeSources bodyNodes)]
      digest = sha256Text (encodeRecord (bodyNodes,bodyEdges,originals))
      uses = [e | e <- edges, edgeKind e == "use", edgeTo e == key]
      parentIds = closure (\current -> [edgeFrom e | e <- edges,
        edgeTo e == current, edgeKind e /= "exception"]) [key]
      rules = [n | n <- nodes, nodeKind n == "rule", nodeId n `elem` parentIds]
      occurrences = [n | n <- projectionNodes value, projectedNodeKind n == "occurrence",
        Just o <- [projectedNodeOccurrence n], key `elem` map nodeId (occurrenceDefinitions doc (occurrenceEdges o))]
  details <- traverse (describeOccurrence projection definition digest) occurrences
  pure (DefinitionInspection definition digest bodyNodes bodyEdges originals uses rules details)

inspectDefinitionOccurrence :: Projection -> Text -> Either [AuthoringDiagnostic] [DefinitionOccurrence]
inspectDefinitionOccurrence projection handle = do
  detail <- focusRequirement projection (RequirementOccurrence handle)
  let doc = snapshotDocument (projectionSnapshot (projectionData projection))
      path = maybe [] occurrenceEdges (projectedNodeOccurrence (explanationOccurrence detail))
  traverse (\d -> do
    info <- inspectDefinition projection (nodeId d)
    describeOccurrence projection d (sharedDefinitionDigest info) (explanationOccurrence detail))
    (occurrenceDefinitions doc path)

describeOccurrence :: Projection -> LawNode -> Text -> ProjectionNode
                   -> Either [AuthoringDiagnostic] DefinitionOccurrence
describeOccurrence projection definition digest occurrence = do
  detail <- focusRequirement projection (RequirementOccurrence (projectedNodeId occurrence))
  let value = projectionData projection
      doc = snapshotDocument (projectionSnapshot value)
      path = maybe [] occurrenceEdges (projectedNodeOccurrence occurrence)
      edges = [e | key <- path, e <- lawEdges (documentLaw doc), edgeId e == key]
      kernel = projectedNodeObservation occurrence >>= observationOriginalKernelId
      mappings = maybe [] (filter ((== kernel) . Just . identityKernelId) . projectionCompilerIdentities)
        (projectionCompiler value)
      refs = nub (nodeSources definition ++ explanationSourceReferences detail)
  pure (DefinitionOccurrence definition digest (explanationAnalysis detail) edges detail mappings refs)

-- | Bounded authored overview: one definition card and explicit paths back to
-- referencing rules, rather than copied executable subtrees. Sources/body stay
-- in the complete projection and inspection record.
definitionView :: Projection -> Text -> Either [AuthoringDiagnostic] ProjectionView
definitionView projection key = do
  info <- inspectDefinition projection key
  let law = documentLaw (snapshotDocument (projectionSnapshot (projectionData projection)))
      ids = closure (\current -> [edgeFrom e | e <- lawEdges law,
        edgeTo e == current, edgeKind e /= "exception"]) [key]
  selectedView projection "One authored definition and its explicit uses; expanded bodies, scoped results and sources remain in the complete projection."
    (map objectProjectionId (nub (key : map nodeId (sharedReferencingRules info) ++ ids)))
    ["use","requires","member","defines"]

definitionOccurrenceView :: Projection -> Text -> Either [AuthoringDiagnostic] ProjectionView
definitionOccurrenceView projection handle = do
  details <- inspectDefinitionOccurrence projection handle
  if null details then Left [issue "DOCCURRENCE" "/definitionOccurrence" [handle]
    "this occurrence does not pass through a reusable definition"] else pure ()
  base <- explanationView projection (RequirementOccurrence handle) defaultExplanationOptions
  let definitions = map linkedDefinition details
      sourceIds = map referenceSource (concatMap nodeSources definitions)
      uses = [edgeId e | d <- details, e <- linkedReferencePath d, edgeKind e == "use"]
  selectedView projection "Scoped requirement, selected assessment, shared definition, explicit use and original source; remaining context is retained in the complete projection."
    (nub (viewIncludedNodes base ++ map (objectProjectionId . nodeId) definitions
      ++ map objectProjectionId uses ++ map objectProjectionId sourceIds))
    ["selected_assessment","assessment_assertion","assessment_source","instance_of",
     "definition_use","relationship_object","law_source","member","requires","use"]

selectedView :: Projection -> Text -> [Text] -> [Text] -> Either [AuthoringDiagnostic] ProjectionView
selectedView projection label requested kinds = do
  let value = projectionData projection
      edges = [e | e <- projectionEdges value, projectedEdgeKind e `elem` kinds,
        projectedEdgeFrom e `elem` requested, projectedEdgeTo e `elem` requested]
      edgeIds = map projectedEdgeId edges
      result = ProjectionView projectionViewFormat
        (projectionIdentity "view" (projectionId value,label,requested,edgeIds)) (projectionId value)
        label requested edgeIds
        [projectedNodeId n | n <- projectionNodes value, projectedNodeId n `notElem` requested]
        [projectedEdgeId e | e <- projectionEdges value, projectedEdgeId e `notElem` edgeIds]
        [ViewBinding k ("node-" <> k) | k <- requested]
        [EdgeBinding i k ("edge-" <> k) | (i,k) <- zip [0..] edgeIds]
      diagnostics = validateProjectionView projection result
  if not (null diagnostics) then Left diagnostics else pure ()
  if length requested <= 64 && length edges <= 128 then Right result
    else Left [issue "PVIEWLIMIT" "/definitionView" [] "reference view exceeds 64 nodes or 128 edges; no truncation"]

instance ToJSON DefinitionInspection where toJSON = genericToJSON jsonOptions
instance ToJSON DefinitionOccurrence where toJSON = genericToJSON jsonOptions

-- Visit authored objects once, even when an unselected definition has many
-- acyclic references. Inspection inventories do not instantiate expression DAGs.
closure :: (Text -> [Text]) -> [Text] -> [Text]
closure next = go []
  where go seen [] = reverse seen
        go seen (key:rest)
          | key `elem` seen = go seen rest
          | otherwise = go (key:seen) (next key ++ rest)
