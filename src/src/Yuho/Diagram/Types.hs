{-# LANGUAGE OverloadedStrings #-}
module Yuho.Diagram.Types
  ( DiagramView(..), DiagramFormat(..), GraphNode(..), GraphEdge(..)
  , SemanticGraph(..), nodeId ) where

import Data.Text (Text)

data DiagramView = RuleView | ModulesView | CaseView | TraceView
  deriving (Eq, Show)

data DiagramFormat = SvgFormat | JsonFormat deriving (Eq, Show)

data GraphNode = GraphNode
  { graphNodeId :: Text
  , graphNodeKind :: Text
  , graphNodeLabel :: Text
  , graphNodeCitation :: Maybe Text
  , graphNodeStatus :: Maybe Text
  , graphNodeBoundary :: Maybe Text
  } deriving (Eq, Show)

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
