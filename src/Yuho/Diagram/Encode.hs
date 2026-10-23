{-# LANGUAGE OverloadedStrings #-}
module Yuho.Diagram.Encode
  ( encodeSemanticGraph, encodeSemanticGraphXml, encodeSvg, encodeNativeSvg
  , encodeNativeSemanticGraph, encodeNativeSemanticGraphXml ) where

import qualified Data.ByteString as BS
import Data.List (sortOn)
import Data.Char (ord)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Numeric (showHex)
import Yuho.Diagram.Types
import Yuho.Protocol.Json (J(..), encodeJson)

encodeSemanticGraph :: SemanticGraph -> BS.ByteString
encodeSemanticGraph = encodeGraph "v0.1" False

encodeNativeSemanticGraph :: SemanticGraph -> BS.ByteString
encodeNativeSemanticGraph = encodeGraph "v0.2" True

encodeGraph :: Text -> Bool -> SemanticGraph -> BS.ByteString
encodeGraph version observations graph = encodeJson (JObj
  [ ("format",JStr ("yuho.semantic-graph/" <> version))
  , ("graph_id",JStr (semanticGraphId graph))
  , ("view",JStr (viewText (semanticGraphView graph)))
  , ("nodes",JArr (map (nodeJson . keepObservation observations) (semanticGraphNodes graph)))
  , ("edges",JArr (map edgeJson (semanticGraphEdges graph)))
  , ("notice",JStr (semanticGraphNotice graph))
  ]) <> "\n"

encodeSemanticGraphXml :: SemanticGraph -> Either Text BS.ByteString
encodeSemanticGraphXml = encodeGraphXml "v0.1" False

encodeNativeSemanticGraphXml :: SemanticGraph -> Either Text BS.ByteString
encodeNativeSemanticGraphXml = encodeGraphXml "v0.2" True

-- SDK reference-view v0.1 encoders remain byte-compatible. Only the native
-- command opts into the new observation contract; complete projections are not
-- rewritten and their existing format/version checks remain in force.
keepObservation :: Bool -> GraphNode -> GraphNode
keepObservation True node = node
keepObservation False node = node { graphNodeObservation = Nothing }

encodeGraphXml :: Text -> Bool -> SemanticGraph -> Either Text BS.ByteString
encodeGraphXml version observations graph
  | all (Text.all xmlCharacter) graphTexts = Right (Encoding.encodeUtf8 (Text.unlines
      (["<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
       ,"<yuho:semantic-graph" <> attribute "xmlns:yuho" ("urn:yuho:semantic-graph:" <> version)
          <> attribute "format" ("yuho.semantic-graph/" <> version)
          <> attribute "graph-id" (semanticGraphId graph)
          <> attribute "view" (viewText (semanticGraphView graph)) <> ">"
       ,"  <yuho:nodes>"]
       ++ map ("    " <>) (map (nodeXml . keepObservation observations) (semanticGraphNodes graph))
       ++ ["  </yuho:nodes>","  <yuho:edges>"]
       ++ map ("    " <>) (map edgeXml (semanticGraphEdges graph))
       ++ ["  </yuho:edges>","  <yuho:notice>" <> xmlEscape (semanticGraphNotice graph)
            <> "</yuho:notice>","</yuho:semantic-graph>"])))
  | otherwise = Left "XML 1.0 forbids a control character in semantic graph output"
  where
    graphTexts = [semanticGraphId graph,semanticGraphNotice graph]
      ++ concatMap nodeTexts (semanticGraphNodes graph)
      ++ concatMap edgeTexts (semanticGraphEdges graph)

nodeXml :: GraphNode -> Text
nodeXml item = "<yuho:node" <> attribute "id" (graphNodeId item)
  <> attribute "kind" (graphNodeKind item) <> attribute "label" (graphNodeLabel item)
  <> optionalAttribute "citation" (graphNodeCitation item)
  <> optionalAttribute "status" (graphNodeStatus item)
  <> optionalAttribute "boundary" (graphNodeBoundary item)
  <> maybe "" observationXml (graphNodeObservation item) <> "/>"

observationXml :: CoreObservation -> Text
observationXml value = attribute "evaluation" (coreObservationEvaluation value)
  <> optionalAttribute "technical-value" (coreObservationValue value)
  <> optionalAttribute "branch-reason" (coreObservationBranchReason value)
  <> optionalAttribute "skip-reason" (coreObservationSkipReason value)

edgeXml :: GraphEdge -> Text
edgeXml item = "<yuho:edge" <> attribute "from" (graphEdgeFrom item)
  <> attribute "to" (graphEdgeTo item) <> attribute "kind" (graphEdgeKind item)
  <> attribute "label" (graphEdgeLabel item) <> "/>"

nodeTexts :: GraphNode -> [Text]
nodeTexts item = [graphNodeId item,graphNodeKind item,graphNodeLabel item]
  ++ maybe [] pure (graphNodeCitation item) ++ maybe [] pure (graphNodeStatus item)
  ++ maybe [] pure (graphNodeBoundary item)
  ++ maybe [] observationTexts (graphNodeObservation item)

edgeTexts :: GraphEdge -> [Text]
edgeTexts item = [graphEdgeFrom item,graphEdgeTo item,graphEdgeKind item,graphEdgeLabel item]

attribute :: Text -> Text -> Text
attribute name value = " " <> name <> "=\"" <> xmlEscape value <> "\""

optionalAttribute :: Text -> Maybe Text -> Text
optionalAttribute _ Nothing = ""
optionalAttribute name (Just value) = attribute name value

xmlCharacter :: Char -> Bool
xmlCharacter value = value == '\t' || value == '\n' || value == '\r'
  || (value >= '\x20' && value <= '\xD7FF')
  || (value >= '\xE000' && value <= '\xFFFD')
  || (value >= '\x10000' && value <= '\x10FFFF')

xmlEscape :: Text -> Text
xmlEscape = Text.concatMap character
  where
    character '&' = "&amp;"
    character '<' = "&lt;"
    character '>' = "&gt;"
    character '\t' = "&#x9;"
    character '\n' = "&#xA;"
    character '\r' = "&#xD;"
    character '\"' = "&quot;"
    character '\'' = "&apos;"
    character value = Text.singleton value

nodeJson :: GraphNode -> J
nodeJson item = JObj
  ([ ("id",JStr (graphNodeId item)),("kind",JStr (graphNodeKind item))
   , ("label",JStr (graphNodeLabel item))]
   ++ optional "citation" (graphNodeCitation item)
   ++ optional "status" (graphNodeStatus item)
   ++ optional "boundary" (graphNodeBoundary item)
   ++ maybe [] (\value -> [("observation",observationJson value)]) (graphNodeObservation item))

observationJson :: CoreObservation -> J
observationJson value = JObj
  ([("evaluation",JStr (coreObservationEvaluation value))]
   ++ optional "technical_value" (coreObservationValue value)
   ++ optional "branch_reason" (coreObservationBranchReason value)
   ++ optional "skip_reason" (coreObservationSkipReason value))

observationTexts :: CoreObservation -> [Text]
observationTexts value = coreObservationEvaluation value :
  concatMap (maybe [] pure) [coreObservationValue value,
    coreObservationBranchReason value,coreObservationSkipReason value]

edgeJson :: GraphEdge -> J
edgeJson item = JObj
  [("from",JStr (graphEdgeFrom item)),("to",JStr (graphEdgeTo item)),
   ("kind",JStr (graphEdgeKind item)),("label",JStr (graphEdgeLabel item))]

optional :: Text -> Maybe Text -> [(Text,J)]
optional _ Nothing = []
optional key (Just value) = [(key,JStr value)]

-- All geometry is derived from wrapped content and occupied layers. Routing uses
-- separate gutters/top lanes; no edge label or route is drawn through card text.
-- Conservative monospace cell estimates include wide Unicode characters.
encodeNativeSvg :: SemanticGraph -> BS.ByteString
encodeNativeSvg graph = Encoding.encodeUtf8 (Text.unlines
  (["<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
   ,"<svg xmlns=\"http://www.w3.org/2000/svg\"" <> attribute "width" (number width)
      <> attribute "height" (number height) <> attribute "viewBox" ("0 0 " <> number width <> " " <> number height)
      <> " role=\"img\" aria-labelledby=\"title desc\" data-graph-format=\"yuho.semantic-graph/v0.2\">"
   ,"<title id=\"title\">Yuho semantic diagram: " <> escape (semanticGraphId graph) <> "</title>"
   ,"<desc id=\"desc\">" <> escape (semanticGraphNotice graph) <> "</desc>"
   ,"<defs><marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"7\" markerHeight=\"7\" orient=\"auto\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#475569\"/></marker></defs>"
   ,"<rect width=\"100%\" height=\"100%\" fill=\"white\"/>"
   ,"<style>text{font-family:DejaVu Sans Mono,monospace;fill:#0f172a;font-size:12px}.edge{stroke:#64748b;stroke-width:1.2;fill:none;marker-end:url(#arrow)}.edge-label{font-size:11px}.node-label{font-weight:700}.node-meta{fill:#334155}</style>"
   ,"<g id=\"edges\">"]
   ++ concat [edgeSvg positions index edge | (index,edge) <- zip [0..] edges]
   ++ ["</g><g id=\"nodes\">"]
   ++ map nodeSvg placed
   ++ ["</g>"] ++ footer ++ ["</svg>"]))
  where
    ordered = sortOn (\n -> (nodeLayer (graphNodeKind n),graphNodeId n)) (semanticGraphNodes graph)
    grouped = Map.fromListWith (++) [(nodeLayer (graphNodeKind n),[n]) | n <- reverse ordered]
    columns = map snd (Map.toAscList grouped)
    edges = sortOn (\e -> (graphEdgeFrom e,graphEdgeTo e,graphEdgeKind e,graphEdgeLabel e)) (semanticGraphEdges graph)
    -- Each edge has its own numbered lane, so its label remains readable even
    -- for same-column and backward links. Gutter width follows actual degree.
    degree column = length [e | e <- edges, any (\n -> graphNodeId n == graphEdgeFrom e
       || graphNodeId n == graphEdgeTo e) column]
    gap column = 48 + 12 * fromIntegral (degree column)
    columnWidths = [maximum (280 : map naturalWidth column) | column <- columns]
    columnGaps = zipWith (\a b -> 48+6*fromIntegral (degree a+degree b)) columns (drop 1 columns ++ [[]])
    xs = scanl (+) (48+6*fromIntegral (length edges)) (zipWith (+) columnWidths columnGaps)
    laneLabels = [wrapText (floor ((width-96)/8)) ("E" <> Text.pack (show (i+1)) <> " " <> graphEdgeKind e <> ": " <> graphEdgeLabel e) | (i,e) <- zip [0::Int ..] edges]
    laneHeights = [22+18*fromIntegral (length linesValue) | linesValue <- laneLabels]
    laneStarts = scanl (+) 24 laneHeights
    top = 50 + sum laneHeights
    placed = concat [placeColumn x top w column | (x,w,column) <- zip3 xs columnWidths columns]
    positions = Map.fromList [(graphNodeId n,(x,y,w,h)) | (n,x,y,w,h,_) <- placed]
    width = max 980 (maximum (0:[x+w | (_,x,_,w,_,_) <- placed]) + 48
      + maximum (0:map gap columns))
    bottom = maximum (top : [y+h | (_,_,y,_,h,_) <- placed])
    footerLines = concatMap (wrapText (floor ((width-80)/8)))
      ["Legend: kind labels identify structure. Dotted cards mark input/fact roles; dashed grey cards are NOT EVALUATED."
      ,"Technical value, execution state, branch reason and supplied classification are separate. E-numbers identify routed relationships."
      ,semanticGraphNotice graph]
    footer = [textLine "legend" 40 (bottom+44+18*fromIntegral i) line | (i,line) <- zip [0::Int ..] footerLines]
    height = bottom+70+18*fromIntegral (length footerLines)
    edgeSvg positionsMap index edge = case (Map.lookup (graphEdgeFrom edge) positionsMap,
        Map.lookup (graphEdgeTo edge) positionsMap) of
      (Just (x1,y1,w1,h1),Just (x2,y2,_,h2)) ->
        let peers predicate identifier = [e | e <- edges, predicate e == identifier]
            rank predicate identifier = fromIntegral (length (takeWhile (/= edge) (peers predicate identifier)))
            a=x1+w1+16+6*rank graphEdgeFrom (graphEdgeFrom edge)
            b=x2-16-6*rank graphEdgeTo (graphEdgeTo edge)
            linesValue=laneLabels !! index
            lane=laneStarts !! index + 18*fromIntegral (length linesValue)
            labelWidth=16+8*fromIntegral (maximum (0:map cellWidth linesValue))
            labelX=max 40 (min (width-labelWidth-40) ((a+b-labelWidth)/2))
            mid1=y1+h1/2;mid2=y2+h2/2
        in ["<g" <> attribute "data-from" (graphEdgeFrom edge) <> attribute "data-to" (graphEdgeTo edge)
              <> attribute "data-kind" (graphEdgeKind edge) <> ">"
           ,"<title>" <> escape (graphEdgeFrom edge <> " -> " <> graphEdgeTo edge <> ": " <> graphEdgeLabel edge) <> "</title>"
           ,"<path class=\"edge\"" <> attribute "d" ("M " <> point (x1+w1) mid1 <> " H " <> number a
              <> " V " <> number lane <> " H " <> number b <> " V " <> number mid2 <> " H " <> number x2) <> "/>"
           ,"<rect" <> attribute "x" (number labelX) <> attribute "y" (number (lane-21-18*fromIntegral (length linesValue-1)))
              <> attribute "width" (number labelWidth) <> attribute "height" (number (18*fromIntegral (length linesValue))) <> " fill=\"white\"/>"
           ,Text.unlines [textLine "edge-label" (labelX+4) (lane-7-18*fromIntegral (length linesValue-1-j)) line | (j,line) <- zip [0::Int ..] linesValue],"</g>"]
      _ -> []

-- Node tuple retains exact wrapped lines for geometry tests and rendering.
placeColumn :: Double -> Double -> Double -> [GraphNode]
  -> [(GraphNode,Double,Double,Double,Double,[(Text,Text)])]
placeColumn _ _ _ [] = []
placeColumn x y width (n:rest) = (n,x,y,width,height,content) : placeColumn x (y+height+32) width rest
  where
    content = [(role,line) | (role,value) <- nodeContent n,
      line <- wrapText (floor ((width-32)/8)) value]
    height = 28+18*fromIntegral (length content)

naturalWidth :: GraphNode -> Double
naturalWidth n = min 400 (max 280 (32+8*fromIntegral longest))
  where longest=maximum (0:[cellWidth line | (_,value) <- nodeContent n,line <- Text.lines value])

nodeContent :: GraphNode -> [(Text,Text)]
nodeContent n = [("node-meta","kind: " <> graphNodeKind n),("node-label",graphNodeLabel n)]
  ++ maybe [] (pure . (,) "node-meta" . ("citation: " <>)) (graphNodeCitation n)
  ++ [ ("node-meta","status: " <> value) | Just value <- [graphNodeStatus n]
       , maybe True ((/= Just value) . coreObservationValue) (graphNodeObservation n) ]
  ++ maybe [] (map ((,) "node-meta") . observationLines) (graphNodeObservation n)
  ++ maybe [] (pure . (,) "node-meta" . ("scope: " <>)) (graphNodeBoundary n)
  where
    observationLines value = ["evaluation: " <> coreObservationEvaluation value]
      ++ maybe [] (pure . ("technical value: " <>)) (coreObservationValue value)
      ++ maybe [] (pure . ("branch reason: " <>)) (coreObservationBranchReason value)
      ++ maybe [] (pure . ("skip reason: " <>)) (coreObservationSkipReason value)

nodeSvg :: (GraphNode,Double,Double,Double,Double,[(Text,Text)]) -> Text
nodeSvg (n,x,y,width,height,content) = Text.unlines
  (["<g" <> attribute "id" (xmlId (graphNodeId n)) <> attribute "data-semantic-id" (graphNodeId n)
      <> attribute "data-kind" (graphNodeKind n) <> attribute "data-x" (number x) <> attribute "data-y" (number y)
      <> attribute "data-width" (number width) <> attribute "data-height" (number height)
      <> maybe "" observationXml (graphNodeObservation n) <> ">"
   ,"<title>" <> escape (Text.intercalate " | " (graphNodeId n:map snd (nodeContent n))) <> "</title>"
   ,"<rect" <> attribute "x" (number x) <> attribute "y" (number y)
      <> attribute "width" (number width) <> attribute "height" (number height)
      <> " rx=\"8\"" <> attribute "fill" fill <> attribute "stroke" stroke <> " stroke-width=\"2\""
      <> (if skipped then " stroke-dasharray=\"8 4\"" else if graphNodeKind n `elem` ["input","scalar","ground-fact","shared-fact","direct-input"]
         then " stroke-dasharray=\"3 2\"" else "") <> "/>"
   ] ++ [textLine role (x+16) (y+22+18*fromIntegral i) line | (i,(role,line)) <- zip [0::Int ..] content]
   ++ ["</g>"])
  where
    skipped = maybe False ((=="not_evaluated") . coreObservationEvaluation) (graphNodeObservation n)
    (fill,stroke) | skipped = ("#f1f5f9","#64748b")
                  | graphNodeKind n `elem` ["exception","guard","presumption"] = ("#fff7ed","#9a3412")
                  | graphNodeKind n `elem` ["all","any","comparison"] = ("#f5f3ff","#6d28d9")
                  | otherwise = ("#eff6ff","#1d4ed8")

textLine :: Text -> Double -> Double -> Text -> Text
textLine role x y line = "<text" <> attribute "class" role <> attribute "x" (number x)
  <> attribute "y" (number y) <> ">" <> escape line <> "</text>"

point :: Double -> Double -> Text
point x y = number x <> " " <> number y

-- Deliberately conservative for fallback CJK/emoji glyphs; no text is truncated.
cellWidth :: Text -> Int
cellWidth = Text.foldl' (\n c -> n + if ord c >= 0x1100 then 2 else 1) 0

wrapText :: Int -> Text -> [Text]
wrapText limit = concatMap split . Text.splitOn "\n"
  where
    split value | Text.null value = [""]
                | otherwise =
                    let (prefix,rest)=chunk 0 Text.empty value
                        breakAt=Text.length (Text.takeWhileEnd (/= ' ') prefix)
                        boundary=Text.length prefix-breakAt-1
                        (a,b) = if not (Text.null rest) && boundary > Text.length prefix `div` 2
                          then (Text.take boundary prefix,Text.drop (boundary+1) prefix <> rest)
                          else (prefix,rest)
                    in a : if Text.null b then [] else split b
    chunk used prefix remaining = case Text.uncons remaining of
      Nothing -> (prefix,Text.empty)
      Just (c,rest) | used + cellWidth (Text.singleton c) > max 2 limit -> (prefix,remaining)
                    | otherwise -> chunk (used+cellWidth (Text.singleton c)) (Text.snoc prefix c) rest

nodeLayer :: Text -> Int
nodeLayer kindValue
  | kindValue `elem` ["module","temporal","actor","input","shared-fact","entity-type","entity","scalar","direct-input"] = 0
  | kindValue `elem` ["all","any","element","relation","presumption","predicate","ground-fact","comparison","forall","exists","cardinality","negation","effective-input"] = 1
  | kindValue `elem` ["definition","exception","attachment","guard"] = 2
  | kindValue `elem` ["offence","participation","attempt","rule","allegation","finite-rule","proposition","conflict"] = 3
  | kindValue == "penalty" = 4
  | otherwise = 2

viewText :: DiagramView -> Text
viewText view = case view of
  RuleView -> "rule"
  ModulesView -> "modules"
  CaseView -> "case"
  TraceView -> "trace"

escape :: Text -> Text
escape = xmlEscape

-- Injective codepoint encoding prevents distinct semantic IDs sharing a DOM ID.
xmlId :: Text -> Text
xmlId value = "node-" <> Text.intercalate "_" [Text.pack (showHex (ord c) "") | c <- Text.unpack value]

number :: Double -> Text
number = Text.pack . show . (round :: Double -> Int)

-- Frozen v0.1 SVG encoder for retained corpus/reference artifacts. Native CLI
-- exports explicitly use encodeNativeSvg and the corrected v0.2 observations.
encodeSvg :: SemanticGraph -> BS.ByteString
encodeSvg graph = Encoding.encodeUtf8 (Text.unlines
  (["<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
    "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"" <> number width <>
      "\" height=\"" <> number height <> "\" viewBox=\"0 0 " <> number width <>
      " " <> number height <> "\" role=\"img\" aria-labelledby=\"title desc\">",
    "<title id=\"title\">Yuho semantic diagram: " <> escape (semanticGraphId graph) <> "</title>",
    "<desc id=\"desc\">" <> escape (semanticGraphNotice graph) <> "</desc>",
    "<defs><marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#334155\"/></marker></defs>",
    "<rect width=\"100%\" height=\"100%\" fill=\"#ffffff\"/>",
    "<style>text{font-family:ui-sans-serif,system-ui,sans-serif;fill:#0f172a}.edge{stroke:#475569;stroke-width:1.5;fill:none;marker-end:url(#arrow)}.edge-label{font-size:10px;fill:#475569}.node-label{font-size:12px;font-weight:600}.node-meta{font-size:10px}.legend{font-size:11px}</style>",
    "<g id=\"edges\">"]
    ++ map (legacyEdgeSvg positions) (semanticGraphEdges graph)
    ++ ["</g><g id=\"nodes\">"]
    ++ map (legacyNodeSvg positions) ordered
    ++ ["</g>",legacyLegendSvg legendY,
        "<text x=\"24\" y=\"" <> number (height - 18) <> "\" font-size=\"11\" fill=\"#7f1d1d\">" <>
          escape (semanticGraphNotice graph) <> "</text>","</svg>"]))
  where
    ordered = sortOn (\item -> (legacyNodeLayer (graphNodeKind item),graphNodeId item))
      (semanticGraphNodes graph)
    grouped = Map.fromListWith (++) [(legacyNodeLayer (graphNodeKind item),[item]) | item <- ordered]
    placed = concat [zipWith (position layer) [0 :: Int ..] (reverse items)
      | (layer,items) <- Map.toAscList grouped]
    positions = Map.fromList [(graphNodeId item,(x,y)) | (item,x,y) <- placed]
    maxRows = maximum (1 : map length (Map.elems grouped))
    width = max 960 (fromIntegral (Map.size grouped) * 270 + 80)
    legendY = fromIntegral (maxRows * 130 + 60)
    height = legendY + 150
    position layer row item = (item,40 + fromIntegral layer * 270,
      40 + fromIntegral row * 130)

legacyEdgeSvg :: Map.Map Text (Double,Double) -> GraphEdge -> Text
legacyEdgeSvg positions edge = case (Map.lookup (graphEdgeFrom edge) positions,
    Map.lookup (graphEdgeTo edge) positions) of
  (Just (x1,y1),Just (x2,y2)) -> Text.concat
    ["<path class=\"edge\" data-kind=\"",escape (graphEdgeKind edge),"\" d=\"M ",
     number (x1 + 210)," ",number (y1 + 38)," C ",number (x1 + 235)," ",number (y1 + 38),
     " ",number (x2 - 25)," ",number (y2 + 38)," ",number x2," ",number (y2 + 38),"\"/>",
     "<text class=\"edge-label\" x=\"",number ((x1+x2)/2 + 90),"\" y=\"",
     number ((y1+y2)/2 + 31),"\">",escape (graphEdgeLabel edge),"</text>"]
  _ -> ""

legacyNodeSvg :: Map.Map Text (Double,Double) -> GraphNode -> Text
legacyNodeSvg positions item = case Map.lookup (graphNodeId item) positions of
  Nothing -> ""
  Just (x,y) -> Text.concat
    ["<g id=\"",legacyXmlId (graphNodeId item),"\" data-semantic-id=\"",
     escape (graphNodeId item),"\" data-kind=\"",escape (graphNodeKind item),"\">",
     legacyShape (graphNodeKind item) x y,
     "<text class=\"node-label\" x=\"",number (x+12),"\" y=\"",number (y+20),"\">",
     legacyTspans (x+12) (legacyWrapLabel (graphNodeLabel item)),"</text>",
     legacyMeta x y (graphNodeCitation item) (graphNodeStatus item),"</g>"]

legacyShape :: Text -> Double -> Double -> Text
legacyShape kindValue x y
  | kindValue == "actor" = Text.concat ["<ellipse cx=\"",number (x+105),"\" cy=\"",
      number (y+38),"\" rx=\"105\" ry=\"38\" fill=\"#f8fafc\" stroke=\"#1e3a8a\" stroke-width=\"2\"/>"]
  | kindValue `elem` ["exception","attachment","presumption","conflict"] = rect "8" "6 3" "#fff7ed" "#9a3412"
  | kindValue `elem` ["input","shared-fact","ground-fact","scalar"] = rect "0" "3 2" "#f0fdf4" "#166534"
  | kindValue `elem` ["all","any","forall","exists","cardinality","negation"] = rect "22" "" "#f5f3ff" "#6d28d9"
  | kindValue == "penalty" = rect "0" "8 3 2 3" "#fefce8" "#854d0e"
  | otherwise = rect "8" "" "#eff6ff" "#1d4ed8"
  where
    rect radius dash fill stroke = Text.concat
      ["<rect x=\"",number x,"\" y=\"",number y,"\" width=\"210\" height=\"76\" rx=\"",
       radius,"\" fill=\"",fill,"\" stroke=\"",stroke,"\" stroke-width=\"2\"",
       if Text.null dash then "" else " stroke-dasharray=\"" <> dash <> "\"","/>"]

legacyMeta :: Double -> Double -> Maybe Text -> Maybe Text -> Text
legacyMeta x y citation status = Text.concat
  [maybe "" (line (y+58) . ("citation: " <>)) citation,
   maybe "" (line (y+70) . ("status: " <>)) status]
  where line offset value = Text.concat ["<text class=\"node-meta\" x=\"",
          number (x+12),"\" y=\"",number offset,"\">",escape value,"</text>"]

legacyTspans :: Double -> [Text] -> Text
legacyTspans x values = Text.concat ["<tspan x=\"" <> number x <> "\" dy=\"" <>
  (if index == (0 :: Int) then "0" else "14") <> "\">" <> escape value <> "</tspan>"
  | (index,value) <- zip [0 :: Int ..] (take 3 values)]

legacyWrapLabel :: Text -> [Text]
legacyWrapLabel value = concatMap wrapLine (Text.lines value)
  where
    wrapLine line = go [] [] (Text.words line)
    go result current [] = reverse (if null current then result else Text.unwords (reverse current):result)
    go result current (word:rest)
      | Text.length (Text.unwords (reverse (word:current))) <= 30 = go result (word:current) rest
      | null current = go (word:result) [] rest
      | otherwise = go (Text.unwords (reverse current):result) [word] rest

legacyLegendSvg :: Double -> Text
legacyLegendSvg y = Text.concat
  ["<g id=\"legend\"><text class=\"legend\" x=\"24\" y=\"",number y,
   "\" font-weight=\"700\">Legend</text>",
   "<text class=\"legend\" x=\"24\" y=\"",number (y+20),
   "\">ellipse actor; square/dotted input or fact; rounded rule/group; dashed exception; dash-dot penalty. Colours are redundant.</text>",
   "<text class=\"legend\" x=\"24\" y=\"",number (y+40),
   "\">Statuses are supplied or technical: satisfied, not satisfied, unresolved, defeated, not evaluated.</text></g>"]

legacyNodeLayer :: Text -> Int
legacyNodeLayer kindValue
  | kindValue `elem` ["module","temporal","actor","input","shared-fact","entity-type","entity","scalar"] = 0
  | kindValue `elem` ["all","any","element","relation","presumption","predicate","ground-fact","comparison","forall","exists","cardinality","negation"] = 1
  | kindValue `elem` ["definition","exception","attachment"] = 2
  | kindValue `elem` ["offence","participation","attempt","rule","allegation","finite-rule","proposition","conflict"] = 3
  | kindValue == "penalty" = 4
  | otherwise = 2

legacyXmlId :: Text -> Text
legacyXmlId = ("node-" <>) . Text.map (\value -> if valid value then value else '-')
  where valid value = value `elem` ['a'..'z'] || value `elem` ['A'..'Z']
          || value `elem` ['0'..'9'] || value `elem` ['-','_','.']
