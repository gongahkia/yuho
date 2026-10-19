{-# LANGUAGE OverloadedStrings #-}
-- | Bounded case/application reference exports over validated view bindings.
module Yuho.Authoring.Projection.ViewEncode
  ( encodeViewJson, encodeViewXml, encodeViewSvg ) where

import qualified Data.ByteString as BS
import Data.List (find, nub)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Projection
import Yuho.Authoring.Projection.Inspect
import Yuho.Authoring.Projection.Render
import Yuho.Authoring.Projection.Views
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue)
import qualified Yuho.Diagram.Types as Legacy
import qualified Yuho.Diagram.Encode as Legacy
import Yuho.SuppliedProofStatus.Types (SuppliedStatus(..), UnresolvedReason(..))

checkedView :: Projection -> ProjectionView -> Either [AuthoringDiagnostic] ()
checkedView projection view = case validateProjectionView projection view of
  [] -> Right ()
  diagnostics -> Left diagnostics

legacyView :: Projection -> ProjectionView -> Legacy.SemanticGraph
legacyView projection view = Legacy.SemanticGraph (viewId view) Legacy.CaseView
  [Legacy.GraphNode (projectedNodeId n) (projectedNodeRole n) (projectedNodeLabel n)
    Nothing Nothing Nothing | key <- viewIncludedNodes view, n <- projectionNodes value, projectedNodeId n == key]
  [Legacy.GraphEdge (projectedEdgeFrom e) (projectedEdgeTo e) (projectedEdgeKind e) (projectedEdgeKind e)
    | key <- viewIncludedEdges view, e <- projectionEdges value, projectedEdgeId e == key]
  ("Selected authorship view. Complete identities, states and omitted context: " <> projectionId value)
  where value = projectionData projection

encodeViewJson :: Projection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeViewJson projection view = checkedView projection view >> pure (Legacy.encodeSemanticGraph (legacyView projection view))

encodeViewXml :: Projection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeViewXml projection view = do
  checkedView projection view
  either (\message -> Left [issue "PXML" "/projectionView" [] message]) Right
    (Legacy.encodeSemanticGraphXml (legacyView projection view))

classification :: Classification -> Text
classification (Classification status) = case status of
  Proved -> "proved"
  NotProved -> "not_proved"
  Unresolved NotDetermined -> "unresolved(not_determined)"
  Unresolved ExternalDecisionPending -> "unresolved(external_decision_pending)"

scopeText :: Scope -> Text
scopeText scope = "Actor: " <> scopeActor scope <> " | Context: " <> scopeContext scope

-- Separate cards retain each object's actual state. Assertions and sources
-- deliberately have no computed-status line. Only selected applications can
-- obtain observations; an alternative is never overlaid with the target result.
nodeLines :: Projection -> ProjectionView -> ProjectionNode -> [Text]
nodeLines projection view n = case projectedNodeRole n of
  "assertion" -> case find ((== original) . assertionId) (documentAssertions doc) of
    Just a -> [assertionDescription a,scopeText (assertionScope a)]
      ++ case caseAssertionLinks projection original of
        Right links | null (linkedAssessments links) -> ["No assessment link in document."]
                    | null (linkedSelectedAssessments links) -> ["Assessment links retained; none selected for this analysis."]
                    | otherwise -> ["Assessment links: " <> count (linkedAssessments links)
                        <> " | Selected for this analysis: " <> count (linkedSelectedAssessments links)]
        Left _ -> []
    Nothing -> []
  "assessment" -> case inspectAssessment projection original of
    Right detail -> let a = inspectionAssessment detail
      in [if inspectionSelected detail then "SELECTED for this analysis" else "UNSELECTED alternative; no run observation attributed",
          "Supplied: " <> classification (assessmentClassification a),scopeText (assessmentScope a),
          "Basis: " <> assessmentBasis a <> " | Origin: " <> assessmentOrigin a,
          "Issuer: " <> assessmentIssuer a,"Reason: " <> assessmentReason a]
        ++ ["Authored assumption; no case assertion cited." | assessmentBasis a == "assumption", null (assessmentAssertions a)]
    Left _ -> []
  "original_source" -> case find ((== original) . sourceId) (documentSources doc) of
    Just s -> ["Original source (" <> sourceKind s <> "): " <> maybe (sourceId s) id (sourceLocator s)]
      ++ [if sourceText s == Nothing then "Locator/reference only; no excerpt or precise location invented."
          else "Retained original text. Only explicitly anchored references yield excerpts."]
      ++ ["Anchored excerpt: " <> excerpt | ref <- sourceRefs original,
          Right recovered <- [recoverOriginalSource projection ref], Just excerpt <- [excerptText recovered]]
    Nothing -> []
  "annotation" -> case find ((== original) . annotationId) (documentAnnotations doc) of
    Just a -> [Text.toUpper (annotationState a) <> " annotation",annotationText a]
    Nothing -> []
  _ | projectedNodeKind n == "occurrence" -> ["Legal occurrence: " <> readable (projectedNodeLabel n)]
        ++ evaluationLines n
    | projectedNodeKind n == "observation" -> ["Existing run observation"] ++ evaluationLines n
    | otherwise -> [readable (projectedNodeLabel n),"Authored " <> projectedNodeRole n]
  where
    value = projectionData projection
    doc = snapshotDocument (projectionSnapshot value)
    original = case originAuthoredObjects (projectedNodeOrigin n) of
      key:_ -> key
      [] -> projectedNodeLabel n
    count = Text.pack . show . length
    readable label = Text.replace "-" " " (if label == original
      then case Text.breakOn ":" label of
        (_,suffix) | not (Text.null suffix) -> Text.drop 1 suffix
        _ -> label
      else label)
    sourceRefs key = nub [ref | e <- projectionEdges value, Just ref <- [projectedEdgeOriginalSource e],
      referenceSource ref == key, elem (projectedEdgeId e) sourceEdges]
    -- Restrict visible source excerpts to references from the selected cards.
    sourceEdges = viewIncludedEdges view
    evaluationLines node =
      ["Evaluation: " <> projectedNodeEvaluation node,
       "Computed: " <> maybe "absent" id (projectedNodeComputed node)]
      ++ maybe [] (\b -> ["Current selected assessment: " <> maybe "MISSING" id (bindingAssessment b)]) (projectedNodeBinding node)
      ++ maybe [] (\why -> ["Skip reason: " <> Text.replace "_" " " why]) (projectedNodeSkipReason node)

-- Connected card list with numbered, explicitly typed relationships. Each
-- relationship has its own gutter lane and legend row; no edge deduplication.
encodeViewSvg :: Projection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeViewSvg projection view = do
  checkedView projection view
  let value = projectionData projection
      nodes = [n | key <- viewIncludedNodes view, n <- projectionNodes value, projectedNodeId n == key]
      edges = [e | key <- viewIncludedEdges view, e <- projectionEdges value, projectedEdgeId e == key]
      cardLines n = concatMap (concatMap (wrap 112) . Text.lines) (nodeLines projection view n)
      labelled = [(n,cardLines n) | n <- nodes]
      labels = concatMap snd labelled
  if length nodes <= 64 && length edges <= 128 then pure () else
    Left [issue "PVIEWLIMIT" "/projectionView" [] "reference SVG supports at most 64 nodes and 128 relationships"]
  if all (Text.all xmlCharacter) (labels ++ map projectedNodeLabel nodes
      ++ concatMap (originAuthoredObjects . projectedNodeOrigin) nodes
      ++ [viewScope view,analysisId (snapshotAnalysis (projectionSnapshot value))]) then pure () else
    Left [issue "PXML" "/projectionView" [] "XML 1.0 forbids a character in the reference view"]
  let gutter = 120 + 7 * length edges
      cardX = gutter + 44
      width = cardX + 1000
      cardHeight linesValue = 76 + 20 * length linesValue
      starts = scanl (\y (_,linesValue) -> y + cardHeight linesValue + 20) 170 labelled
      positions = Map.fromList [(projectedNodeId n,(y,cardHeight linesValue)) | ((n,linesValue),y) <- zip labelled starts]
      edgeTop = 170 + sum [cardHeight linesValue + 20 | (_,linesValue) <- labelled] + 30
      text x y size weight content = "<text x=\"" <> number x <> "\" y=\"" <> number y
        <> "\" font-size=\"" <> number size <> "\" font-weight=\"" <> weight <> "\">" <> escape content <> "</text>"
      original n = maybe (projectedNodeLabel n) id (case projectedNodeOccurrence n of
          Just o -> Just (occurrenceAuthoredNode o)
          Nothing -> case originAuthoredObjects (projectedNodeOrigin n) of {key:_ -> Just key; [] -> Nothing})
      role n
        | projectedNodeKind n == "occurrence" = "legal occurrence"
        | projectedNodeKind n == "observation" = "run observation"
        | projectedNodeRole n == "input" = "legal input definition"
        | otherwise = projectedNodeRole n
      name key = case find ((== key) . projectedNodeId) nodes of
        Just n -> let label = original n
          in (if Text.length label <= 60 then label else Text.take 57 label <> "…") <> " [" <> role n <> "]"
        Nothing -> key
      legendRows = [wrap (max 80 (div (width-56) 7))
          ("E" <> number (i+1) <> " · " <> projectedEdgeKind e <> " [" <> projectedEdgeSemantics e <> "] · "
            <> name (projectedEdgeFrom e) <> " → " <> name (projectedEdgeTo e))
        | (i,e) <- zip [0..] edges]
      legendStarts = scanl (\y linesValue -> y + 17 * length linesValue + 14) edgeTop legendRows
      height = edgeTop + sum [17 * length linesValue + 14 | linesValue <- legendRows] + 90
      endpoint key index = do
        (y,h) <- Map.lookup key positions
        pure (y + 30 + mod (index*17) (max 17 (h-46)))
      edgeMarkup (i,e) = case (endpoint (projectedEdgeFrom e) i,endpoint (projectedEdgeTo e) i) of
        (Just fromY,Just toY) ->
          let lane = gutter - i*7
              badge = "E" <> number (i+1)
          in "<g><path id=\"edge-" <> projectedEdgeId e <> "\" data-projection-edge=\"" <> projectedEdgeId e
            <> "\" data-kind=\"" <> projectedEdgeKind e <> "\" d=\"M " <> number cardX <> " " <> number fromY
            <> " H " <> number lane <> " V " <> number toY <> " H " <> number (cardX-3)
            <> "\" fill=\"none\" stroke=\"#64748b\" stroke-width=\"1.2\" marker-end=\"url(#arrow)\""
            <> (if elem (projectedEdgeSemantics e) ["descriptive","provenance"] then " stroke-dasharray=\"4 3\"" else "")
            <> "><title>" <> escape (Encoding.decodeUtf8 (encodeRecord e)) <> "</title></path>"
            <> text (cardX-34) (fromY-4) 10 "600" badge <> "</g>"
        _ -> ""
      card ((n,linesValue),y) =
        "<g id=\"node-" <> projectedNodeId n <> "\" data-projection-node=\"" <> projectedNodeId n
        <> "\" data-authored-id=\"" <> escape (original n) <> "\"><title>"
        <> escape (Encoding.decodeUtf8 (encodeRecord n)) <> "</title><rect x=\"" <> number cardX
        <> "\" y=\"" <> number y <> "\" width=\"968\" height=\"" <> number (cardHeight linesValue)
        <> "\" rx=\"5\" fill=\"white\" stroke=\"#cbd5e1\"/>"
        <> text (cardX+16) (y+22) 11 "600" (Text.toUpper (role n) <> " · " <> original n)
        <> Text.concat [text (cardX+16) (y+49+j*20) 13 "400" line | (j,line) <- zip [0..] linesValue]
        <> "</g>"
      legend (linesValue,y) = Text.concat
        [text 28 (y+i*17) 12 "400" line | (i,line) <- zip [0..] linesValue]
      markup = Text.unlines
        ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
         "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"" <> number width <> "\" height=\"" <> number height
           <> "\" viewBox=\"0 0 " <> number width <> " " <> number height <> "\" role=\"img\" aria-labelledby=\"title\">",
         "<title id=\"title\">Case information and explicit application assessments</title>",
         "<metadata id=\"projection-view\">" <> escape (Encoding.decodeUtf8 (encodeRecord view)) <> "</metadata>",
         "<style>text{font-family:system-ui,-apple-system,sans-serif;fill:#0f172a}path{stroke-linejoin:round}</style>",
         "<defs><marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"5\" markerHeight=\"5\" orient=\"auto\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#64748b\"/></marker></defs>",
         "<rect width=\"100%\" height=\"100%\" fill=\"#f8fafc\"/>",
         text 28 34 21 "600" "Case information and explicit application",
         text 28 60 13 "400" ("Analysis: " <> analysisId (snapshotAnalysis (projectionSnapshot value)) <> " · " <> projectionMode value),
         Text.concat [text 28 (86+i*17) 12 "400" line | (i,line) <- zip [0..] (wrap 150 (viewScope view))],
         text 28 146 12 "400" "Citations and descriptive links carry no evidence weight or entailment. Unselected assessments have no attributed computation.",
         "<g id=\"connections\">" <> Text.concat (map edgeMarkup (zip [0..] edges)) <> "</g>",
         "<g id=\"objects\">" <> Text.concat (map card (zip labelled starts)) <> "</g>",
         Text.concat (map legend (zip legendRows legendStarts)),
         text 28 (height-44) 11 "400" ("Full context and omitted-object bindings: " <> projectionId value),
         "</svg>"]
  pure (Encoding.encodeUtf8 markup)
