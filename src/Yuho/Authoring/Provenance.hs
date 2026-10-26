-- | Opt-in complete typed evidence over the accepted checked dependency domain.
-- Projection and focus constructors are sealed. No evaluator is implemented here.
module Yuho.Authoring.Provenance
  ( Projection, Node, Edge, Focus, provenanceFormat, focusFormat
  , projectionIdentity, projectionMode, projectionAuthority, nodes, edges, retained
  , identity, structuralIdentity, category, label, evaluation, state, authority, record
  , edgeIdentity, from, to, relationship, evidence
  , projectTypedProvenance, projectStaticProvenance, validateTypedProvenance
  , focusProvenance, validateProvenanceFocus, focusProjection, focusRoot
  , focusIncludedNodes, focusOmittedNodes, focusIncludedEdges, focusOmittedEdges
  , explainProvenance, exportTypedProvenance
  ) where
import Data.Text (Text)
import qualified Data.Aeson as A
import Yuho.Provenance.Types (Projection,Node,Edge,provenanceFormat,focusFormat)
import qualified Yuho.Provenance.Types as T
import Yuho.Provenance.Build
import Yuho.Provenance.View (Focus,focusProvenance,validateProvenanceFocus,explainProvenance,exportTypedProvenance)
import qualified Yuho.Provenance.View as V

-- Functions, deliberately not exported record field labels: exposing selectors
-- would permit record-update syntax even with the constructor hidden.
projectionIdentity, projectionMode, projectionAuthority :: Projection -> Text
projectionIdentity=T.projectionIdentity
projectionMode=T.projectionMode
projectionAuthority=T.projectionAuthority
nodes :: Projection -> [Node]
nodes=T.nodes
edges :: Projection -> [Edge]
edges=T.edges
retained :: Projection -> A.Value
retained=T.retained
identity,category,label,evaluation :: Node -> Text
identity=T.identity
category=T.category
label=T.label
evaluation=T.evaluation
structuralIdentity :: Node -> [Text]
structuralIdentity=T.structuralIdentity
state :: Node -> Maybe Text
state=T.state
authority,record :: Node -> A.Value
authority=T.authority
record=T.record
edgeIdentity,from,to,relationship :: Edge -> Text
edgeIdentity=T.edgeIdentity
from=T.from
to=T.to
relationship=T.relationship
evidence :: Edge -> A.Value
evidence=T.evidence
focusProjection :: Focus -> Text
focusProjection=V.focusProjection
focusRoot :: Focus -> Maybe Text
focusRoot=V.focusRoot
focusIncludedNodes,focusOmittedNodes,focusIncludedEdges,focusOmittedEdges :: Focus -> [Text]
focusIncludedNodes=V.focusIncludedNodes
focusOmittedNodes=V.focusOmittedNodes
focusIncludedEdges=V.focusIncludedEdges
focusOmittedEdges=V.focusOmittedEdges
