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

-- Reference presentation only. IDs, observations and view partitions are
-- unchanged; row height follows the visible text so skip reasons are not clipped.
encodeProjectionSvg :: Projection -> Either [AuthoringDiagnostic] BS.ByteString
encodeProjectionSvg projection = do
  value <- ensureValid projection
  view <- lawOccurrenceView projection
  let nodes = [n | key <- viewIncludedNodes view, n <- projectionNodes value, projectedNodeId n == key]
      edges = [e | e <- projectionEdges value, elem (projectedEdgeId e) (viewIncludedEdges view)]
      analysis = snapshotAnalysis (projectionSnapshot value)
      depth n = maybe 0 (length . occurrenceEdges) (projectedNodeOccurrence n)
      leftX n = 64 + 34 * depth n
      titleLines n = wrap (max 20 (div (692-leftX n-32) 8)) (conciseLabel n)
      referenceLines n = maybe [] (wrap 48 . ("Provision: " <>)) (provisionFor value n)
      suppliedLines :: ProjectionNode -> [Text]
      suppliedLines n = case projectedNodeBinding n of
        Just b -> case bindingSupplied b of
          Just (Classification status) ->
            (if bindingState b == "selected" then "Selected assessment" else "Unselected assessment")
            : case status of
              Proved -> ["proved"]
              NotProved -> ["not_proved"]
              Unresolved reason -> ["unresolved",case reason of
                NotDetermined -> "not_determined"
                ExternalDecisionPending -> "external_decision_pending"]
          Nothing -> ["Missing assessment"]
        Nothing -> ["—"]
      notes n = maybe [] (wrap 34 . ("Skip reason: " <>) . skipLabel) (projectedNodeSkipReason n)
        ++ maybe [] (wrap 34 . ("Branch: " <>) . Text.replace "_" " ") (projectedNodeBranchReason n)
      rowHeight n = max 96 (maximum
        [42 + 19 * length (titleLines n) + 17 * length (referenceLines n) + 12,
         42 + 19 * length (suppliedLines n) + 12,
         42 + 18 * length (notes n) + 24])
      labelled = [(n,rowHeight n) | n <- nodes]
      starts = scanl (\y (_,h) -> y+h+12) 172 labelled
      positions = Map.fromList [(projectedNodeId n,(leftX n,y,h)) | ((n,h),y) <- zip labelled starts]
      width = 1460 :: Int
      height = 172 + sum [h+12 | (_,h) <- labelled] + 80
      visible = concat [titleLines n ++ referenceLines n ++ suppliedLines n
          ++ [computedLabel (projectedNodeComputed n),evaluationLabel (projectedNodeEvaluation n)] ++ notes n | n <- nodes]
        ++ [analysisId analysis,scopeActor (analysisScope analysis),scopeContext (analysisScope analysis)]
  if all (Text.all xmlCharacter) visible then pure () else
    Left [issue "PXML" "/projectionNodes" [] "XML 1.0 forbids a character in the reference view"]
  let text x y size weight content = "<text x=\"" <> number x <> "\" y=\"" <> number y
        <> "\" font-size=\"" <> number size <> "\" font-weight=\"" <> weight <> "\">" <> escape content <> "</text>"
      renderEdge edge = case (Map.lookup (projectedEdgeFrom edge) positions,Map.lookup (projectedEdgeTo edge) positions) of
        (Just (x1,y1,h1),Just (x2,y2,_)) ->
          "<path id=\"edge-" <> projectedEdgeId edge <> "\" data-projection-edge=\"" <> projectedEdgeId edge
          <> "\" data-kind=\"" <> projectedEdgeKind edge <> "\" d=\"M " <> number (x1+12) <> " " <> number (y1+h1)
          <> " V " <> number (y2+26) <> " H " <> number (x2-4)
          <> "\" fill=\"none\" stroke=\"" <> (if projectedEdgeKind edge == "exception" then "#9a3412" else "#64748b")
          <> "\" stroke-width=\"1.5\" marker-end=\"url(#arrow)\""
          <> (if projectedEdgeKind edge == "exception" then " stroke-dasharray=\"5 4\"" else "")
          <> "><title>" <> escape (projectedEdgeKind edge <> " — authored relationship "
            <> Text.intercalate ", " (originAuthoredObjects (projectedEdgeOrigin edge))) <> "</title></path>"
        _ -> ""
      renderNode n = case Map.lookup (projectedNodeId n) positions of
        Nothing -> ""
        Just (x,y,h) ->
          let kind = case projectedNodeRole n of
                "all" -> "All required (ALL)"
                "any" -> "At least one required (ANY)"
                "rule" | depth n > 0 -> "Exception guard"
                       | otherwise -> "Main rule"
                _ -> "Legal input"
              rowText xpos offset size weight spacing linesValue = Text.concat
                [text xpos (y+offset+i*spacing) size weight line | (i,line) <- zip [0..] linesValue]
              authored = maybe "" occurrenceAuthoredNode (projectedNodeOccurrence n)
          in "<g id=\"node-" <> projectedNodeId n <> "\" data-projection-node=\"" <> projectedNodeId n
            <> "\" data-authored-id=\"" <> escape authored <> "\"><title>"
            <> escape (Encoding.decodeUtf8 (encodeRecord n)) <> "</title><rect x=\"" <> number x <> "\" y=\""
            <> number y <> "\" width=\"" <> number (width-x-28) <> "\" height=\"" <> number h
            <> "\" rx=\"6\" fill=\"#ffffff\" stroke=\"#cbd5e1\"/>"
            <> text (x+16) (y+20) 12 "600" kind
            <> rowText (x+16) 43 16 "500" 19 (titleLines n)
            <> rowText (x+16) (47+19*length (titleLines n)) 13 "400" 17 (referenceLines n)
            <> rowText 718 43 16 "500" 19 (suppliedLines n)
            <> text 964 (y+43) 16 "500" (computedLabel (projectedNodeComputed n))
            <> text 1178 (y+43) 16 "500" (evaluationLabel (projectedNodeEvaluation n))
            <> rowText 1178 65 13 "400" 18 (notes n) <> "</g>"
      svg = Text.unlines
        (["<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
          "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"" <> number width <> "\" height=\"" <> number height
            <> "\" viewBox=\"0 0 " <> number width <> " " <> number height <> "\" role=\"img\" aria-labelledby=\"title desc\">",
          "<title id=\"title\">Authored analysis — " <> escape (analysisId analysis) <> "</title>",
          "<desc id=\"desc\">Selected law tree and guard. Selection, supplied classification, computation and evaluation are separate.</desc>",
          "<metadata id=\"projection-view\">" <> escape (Encoding.decodeUtf8 (encodeRecord view)) <> "</metadata>",
          "<style>text{font-family:system-ui,-apple-system,sans-serif;fill:#0f172a;font-variant-numeric:tabular-nums}path{stroke-linejoin:round}</style>",
          "<defs><marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"5\" markerHeight=\"5\" orient=\"auto\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#64748b\"/></marker></defs>",
          "<rect width=\"100%\" height=\"100%\" fill=\"#f8fafc\"/>",
          text 28 36 22 "600" ("Analysis: " <> analysisId analysis <> " · " <> projectionMode value),
          text 28 62 14 "400" ("Scope actor: " <> scopeActor (analysisScope analysis) <> " · Context: " <> scopeContext (analysisScope analysis)),
          text 28 87 13 "400" "Selected law tree and guard. Assertions, alternatives, sources and annotations remain in the complete projection.",
          text 28 111 13 "400" "Solid: explicit requirement structure. Dashed: exception attachment. No evidence-strength or causal inference.",
          text 80 151 12 "600" "AUTHORED REQUIREMENT / GROUP",text 718 151 12 "600" "SUPPLIED CLASSIFICATION",
          text 964 151 12 "600" "COMPUTED RESULT",text 1178 151 12 "600" "EVALUATION STATE",
          "<g id=\"connections\">"] ++ map renderEdge edges ++ ["</g><g id=\"occurrences\">"] ++ map renderNode nodes ++
          ["</g>",text 28 (height-49) 13 "400" "No computed result differs from not_satisfied. Supplied not_proved does not establish factual falsity.",
           text 28 (height-27) 12 "400" ("Full projection: " <> projectionId value),"</svg>"])
  pure (Encoding.encodeUtf8 svg)
