{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE PatternSynonyms #-}
module Yuho.Diagram.Types
  ( DiagramView(..), DiagramFormat(..)
  , GraphNode(GraphNode, graphNodeId, graphNodeKind, graphNodeLabel
      , graphNodeCitation, graphNodeStatus, graphNodeBoundary, graphNodeObservation)
  , GraphEdge(..), CoreObservation(..)
  , SemanticGraph(..), nodeId ) where

import Data.Text (Text)
import Yuho.CoreYuho.Types (CoreObservation(..))

data DiagramView = RuleView | ModulesView | CaseView | TraceView
  deriving (Eq, Show)

data DiagramFormat = SvgFormat | JsonFormat | XmlFormat deriving (Eq, Show)

data GraphNode = GraphNodeData
  { graphNodeId :: Text
  , graphNodeKind :: Text
  , graphNodeLabel :: Text
  , graphNodeCitation :: Maybe Text
  , graphNodeStatus :: Maybe Text
  , graphNodeBoundary :: Maybe Text
  , graphNodeObservation :: Maybe CoreObservation
  } deriving (Eq, Show)

-- Retain the existing six-argument construction interface. New observations are
-- additive and optional; old authored/summary nodes do not acquire computed data.
pattern GraphNode :: Text -> Text -> Text -> Maybe Text -> Maybe Text -> Maybe Text -> GraphNode
pattern GraphNode identifier kindValue label citation status boundary <-
  GraphNodeData identifier kindValue label citation status boundary _
  where GraphNode identifier kindValue label citation status boundary =
          GraphNodeData identifier kindValue label citation status boundary Nothing
{-# COMPLETE GraphNode #-}

data GraphEdge = GraphEdge
  { graphEdgeFrom :: Text
  , graphEdgeTo :: Text
  , graphEdgeKind :: Text
  , graphEdgeLabel :: Text
  } deriving (Eq, Show)

data SemanticGraph = SemanticGraph
  { semanticGraphId :: Text
  , semanticGraphView :: DiagramView
  , semanticGraphNodes :: [GraphNode]
  , semanticGraphEdges :: [GraphEdge]
  , semanticGraphNotice :: Text
  } deriving (Eq, Show)

nodeId :: Text -> Text -> Text
nodeId kindValue identifier = kindValue <> ":" <> identifier
