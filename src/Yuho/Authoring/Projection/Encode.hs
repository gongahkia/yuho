{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Projection.Encode
  ( encodeProjection, lawOccurrenceView, encodeProjectionLegacyJson
  , encodeProjectionLegacyXml, encodeProjectionSvg ) where

import qualified Data.ByteString as BS
import Data.List (sortOn)
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Projection
import Yuho.Authoring.Projection.Render
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue)
import Yuho.SuppliedProofStatus.Types (SuppliedStatus(..), UnresolvedReason(..))
import qualified Yuho.Diagram.Types as Legacy
import qualified Yuho.Diagram.Encode as Legacy

ensureValid :: Projection -> Either [AuthoringDiagnostic] ProjectionData
ensureValid projection = case validateProjection (projectionData projection) of
  [] -> Right (projectionData projection)
  diagnostics -> Left diagnostics

encodeProjection :: Projection -> Either [AuthoringDiagnostic] BS.ByteString
encodeProjection projection = (<> "\n") . encodeRecord <$> ensureValid projection

-- | This is deliberately a named, selected view. All context omitted here is
-- retained in the full projection and enumerated in the companion bindings.
lawOccurrenceView :: Projection -> Either [AuthoringDiagnostic] ProjectionView
lawOccurrenceView projection = do
  value <- ensureValid projection
  let nodes = [n | n <- projectionNodes value, projectedNodeKind n == "occurrence"]
      edges = [e | e <- projectionEdges value, projectedEdgeSemantics e == "occurrence_structure"]
      roots = [n | n <- nodes, Just o <- [projectedNodeOccurrence n], null (occurrenceEdges o)]
      visit seen key
        | Set.member key seen = []
        | otherwise = key : concat [visit (Set.insert key seen) (projectedEdgeTo e)
            | e <- sortOn ((== "exception") . projectedEdgeKind) edges, projectedEdgeFrom e == key]
      ordered = concatMap (visit Set.empty . projectedNodeId) roots
      allNodeIds = map projectedNodeId nodes
      edgeIds = map projectedEdgeId edges
  if sortOn id ordered == sortOn id allNodeIds && length roots == 1
    then pure () else Left [issue "PVIEW" "/projectionNodes" allNodeIds "law occurrence view is not one connected tree"]
  pure (ProjectionView projectionViewFormat (projectionIdentity "view" (projectionId value,"law-occurrences" :: Text))
    (projectionId value) "Selected analysis law occurrence tree, including its guard. Remaining authorship/provenance is in the complete projection."
    ordered edgeIds
    [projectedNodeId n | n <- projectionNodes value, projectedNodeId n `notElem` ordered]
    [projectedEdgeId e | e <- projectionEdges value, projectedEdgeId e `notElem` edgeIds]
    [ViewBinding key ("node-" <> key) | key <- ordered]
    [EdgeBinding i key ("edge-" <> key) | (i,key) <- zip [0..] edgeIds])

legacyGraph :: ProjectionData -> ProjectionView -> Legacy.SemanticGraph
legacyGraph value view = Legacy.SemanticGraph (viewId view) Legacy.RuleView nodes edges notice
  where
    nodes = [Legacy.GraphNode (projectedNodeId n) (projectedNodeRole n) (conciseLabel n)
      Nothing Nothing Nothing | key <- viewIncludedNodes view,
        n <- projectionNodes value, projectedNodeId n == key]
    edges = [Legacy.GraphEdge (projectedEdgeFrom e) (projectedEdgeTo e)
      (projectedEdgeKind e) (projectedEdgeKind e) | e <- projectionEdges value,
        projectedEdgeId e `elem` viewIncludedEdges view]
    notice = "Selected law tree; full states, identities and context: " <> projectionId value

encodeProjectionLegacyJson :: Projection -> Either [AuthoringDiagnostic] BS.ByteString
encodeProjectionLegacyJson projection = do
  value <- ensureValid projection
  view <- lawOccurrenceView projection
  pure (Legacy.encodeSemanticGraph (legacyGraph value view))

encodeProjectionLegacyXml :: Projection -> Either [AuthoringDiagnostic] BS.ByteString
encodeProjectionLegacyXml projection = do
  value <- ensureValid projection
  view <- lawOccurrenceView projection
  either (\message -> Left [issue "PXML" "/projectionNodes" [] message]) Right
    (Legacy.encodeSemanticGraphXml (legacyGraph value view))

conciseLabel :: ProjectionNode -> Text
conciseLabel n = case projectedNodeOccurrence n of
  Just o | projectedNodeLabel n == occurrenceAuthoredNode o ->
    Text.replace "-" " " (case Text.breakOn ":" (projectedNodeLabel n) of
      (_,suffix) | not (Text.null suffix) -> Text.drop 1 suffix
      _ -> projectedNodeLabel n)
  _ -> projectedNodeLabel n

-- The legacy SVG's fixed 76px boxes and truncated labels cannot express these
-- separate state fields. This reference renderer is confined to the new format.
encodeProjectionSvg :: Projection -> Either [AuthoringDiagnostic] BS.ByteString
encodeProjectionSvg projection = do
  value <- ensureValid projection
  view <- lawOccurrenceView projection
  let nodes = [n | key <- viewIncludedNodes view, n <- projectionNodes value, projectedNodeId n == key]
      edges = [e | e <- projectionEdges value, projectedEdgeId e `elem` viewIncludedEdges view]
      snapshot = projectionSnapshot value
      analysis = snapshotAnalysis snapshot
      texts = analysisId analysis : scopeActor (analysisScope analysis) : scopeContext (analysisScope analysis)
        : concat [[projectedNodeLabel n,maybe "" occurrenceAuthoredNode (projectedNodeOccurrence n),
           maybe "" id (projectedNodeSkipReason n),maybe "" id (projectedNodeBranchReason n)] | n <- nodes]
  if all (Text.all xmlCharacter) texts then pure () else Left [issue "PXML" "/projectionNodes"
    [key | n <- nodes, let key = projectedNodeId n, not (Text.all xmlCharacter (projectedNodeLabel n))]
    "XML 1.0 forbids a character in the reference view"]
  let rowHeight = 124 :: Int
      top = 172 :: Int
      width = 1460 :: Int
      height = top + length nodes * rowHeight + 90
      positions = Map.fromList [(projectedNodeId n,(64 + 34 * depth n,top + i*rowHeight))
        | (i,n) <- zip [0..] nodes]
      depth n = maybe 0 (length . occurrenceEdges) (projectedNodeOccurrence n)
      text x y size weight content = "<text x=\"" <> number x <> "\" y=\"" <> number y <>
        "\" font-size=\"" <> number size <> "\" font-weight=\"" <> weight <> "\">" <> escape content <> "</text>"
      renderEdge edge = case (Map.lookup (projectedEdgeFrom edge) positions,Map.lookup (projectedEdgeTo edge) positions) of
        (Just (x1,y1),Just (x2,y2)) ->
          "<path id=\"edge-" <> projectedEdgeId edge <> "\" data-projection-edge=\"" <> projectedEdgeId edge <>
          "\" data-kind=\"" <> projectedEdgeKind edge <> "\" d=\"M " <> number (x1+12) <> " " <> number (y1+108) <>
          " V " <> number (y2+26) <> " H " <> number (x2-4) <>
          "\" fill=\"none\" stroke=\"" <> (if projectedEdgeKind edge == "exception" then "#9a3412" else "#64748b") <>
          "\" stroke-width=\"1.5\" marker-end=\"url(#arrow)\"" <>
          (if projectedEdgeKind edge == "exception" then " stroke-dasharray=\"5 4\"" else "") <>
          "><title>" <> escape (projectedEdgeKind edge <> " — authored relationship " <>
            Text.intercalate ", " (originAuthoredObjects (projectedEdgeOrigin edge))) <> "</title></path>"
        _ -> "" -- unreachable after projection and view validation
      renderNode n = case Map.lookup (projectedNodeId n) positions of
        Nothing -> ""
        Just (x,y) ->
          let titleLines = wrap 43 (conciseLabel n)
              shownTitle = if length titleLines <= 3 then titleLines else take 2 titleLines ++ ["… full label in metadata"]
              suppliedLines = case projectedNodeBinding n of
                Just b -> case bindingSupplied b of
                  Just (Classification status) -> case status of
                    Proved -> ["proved","selected assessment"]
                    NotProved -> ["not_proved","selected assessment"]
                    Unresolved reason -> ["unresolved",case reason of NotDetermined -> "not_determined"; ExternalDecisionPending -> "external_decision_pending"]
                  Nothing -> ["MISSING ASSESSMENT"]
                Nothing -> ["— " <> projectedNodeRole n]
              computed = maybe "absent" id (projectedNodeComputed n)
              skip = maybe [] (wrap 30 . Text.replace "_" " " . Text.replace
                "exception guard skipped because main branch: " "Skip: ") (projectedNodeSkipReason n)
              branch = maybe [] (wrap 30 . ("Branch: " <>)) (projectedNodeBranchReason n)
              guardLabel = if projectedNodeRole n == "rule" && depth n > 0 then "EXCEPTION GUARD" else Text.toUpper (projectedNodeRole n)
              rowText xpos offset size weight linesValue = Text.concat
                [text xpos (y+offset+i*16) size weight line | (i,line) <- zip [0..] linesValue]
              authored = maybe "" occurrenceAuthoredNode (projectedNodeOccurrence n)
          in "<g id=\"node-" <> projectedNodeId n <> "\" data-projection-node=\"" <> projectedNodeId n <>
            "\" data-authored-id=\"" <> escape authored <> "\">" <>
            "<title>" <> escape (Encoding.decodeUtf8 (encodeRecord n)) <> "</title>" <>
            "<rect x=\"" <> number x <> "\" y=\"" <> number y <> "\" width=\"" <> number (width-x-28) <>
            "\" height=\"108\" rx=\"6\" fill=\"#ffffff\" stroke=\"#cbd5e1\"/>" <>
            text (x+16) (y+19) 10 "600" guardLabel <>
            rowText (x+16) 43 14 "500" shownTitle <>
            rowText 718 39 13 "500" suppliedLines <>
            rowText 964 39 13 "500" [computed] <>
            rowText 1178 39 13 "500" [projectedNodeEvaluation n] <>
            rowText 1178 61 11 "400" (skip ++ branch) <> "</g>"
      svg = Text.unlines
        (["<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
          "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"" <> number width <> "\" height=\"" <> number height <>
            "\" viewBox=\"0 0 " <> number width <> " " <> number height <> "\" role=\"img\" aria-labelledby=\"title desc\">",
          "<title id=\"title\">Authored analysis — " <> escape (analysisId analysis) <> "</title>",
          "<desc id=\"desc\">Selected connected law occurrence tree. Supplied classifications, computed results and evaluation states are separate. Full context is in the companion projection.</desc>",
          "<metadata id=\"projection-view\">" <> escape (Encoding.decodeUtf8 (encodeRecord view)) <> "</metadata>",
          "<style>text{font-family:system-ui,-apple-system,sans-serif;fill:#0f172a;font-variant-numeric:tabular-nums}path{stroke-linejoin:round}</style>",
          "<defs><marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"5\" markerHeight=\"5\" orient=\"auto\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#64748b\"/></marker></defs>",
          "<rect width=\"100%\" height=\"100%\" fill=\"#f8fafc\"/>",
          text 28 36 22 "600" ("Analysis: " <> analysisId analysis <> " · " <> projectionMode value),
          text 28 62 13 "400" ("Actor: " <> scopeActor (analysisScope analysis) <> " · Context: " <> scopeContext (analysisScope analysis)),
          text 28 87 12 "400" "View: selected law occurrence tree and guard. Assertions, alternatives, sources and annotations remain in the complete projection.",
          text 28 111 12 "400" "Solid connectors: explicit requirement structure. Dashed connector: exception attachment. No evidence-strength or causal inference.",
          text 80 151 11 "600" "AUTHORED REQUIREMENT / GROUP",text 718 151 11 "600" "SUPPLIED CLASSIFICATION",
          text 964 151 11 "600" "COMPUTED RESULT",text 1178 151 11 "600" "EVALUATION STATE",
          "<g id=\"connections\">"] ++ map renderEdge edges ++ ["</g><g id=\"occurrences\">"] ++ map renderNode nodes ++
          ["</g>",text 28 (height-52) 12 "400" "Absent computed result is distinct from not_satisfied. not_proved remains supplied information, without a factual-falsity finding.",
           text 28 (height-29) 12 "400" ("Full projection: " <> projectionId value),"</svg>"])
  pure (Encoding.encodeUtf8 svg)
