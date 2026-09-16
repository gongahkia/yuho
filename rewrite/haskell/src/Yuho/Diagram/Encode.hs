{-# LANGUAGE OverloadedStrings #-}
module Yuho.Diagram.Encode (encodeSemanticGraph, encodeSvg) where

import qualified Data.ByteString as BS
import Data.List (sortOn)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Diagram.Types
import Yuho.Protocol.Json (J(..), encodeJson)

encodeSemanticGraph :: SemanticGraph -> BS.ByteString
encodeSemanticGraph graph = encodeJson (JObj
  [ ("format",JStr "yuho.semantic-graph/v0.1")
  , ("graph_id",JStr (semanticGraphId graph))
  , ("view",JStr (viewText (semanticGraphView graph)))
  , ("nodes",JArr (map nodeJson (semanticGraphNodes graph)))
  , ("edges",JArr (map edgeJson (semanticGraphEdges graph)))
  , ("notice",JStr (semanticGraphNotice graph))
  ]) <> "\n"

nodeJson :: GraphNode -> J
nodeJson item = JObj
  ([ ("id",JStr (graphNodeId item)),("kind",JStr (graphNodeKind item))
   , ("label",JStr (graphNodeLabel item))]
   ++ optional "citation" (graphNodeCitation item)
   ++ optional "status" (graphNodeStatus item)
   ++ optional "boundary" (graphNodeBoundary item))

edgeJson :: GraphEdge -> J
edgeJson item = JObj
  [("from",JStr (graphEdgeFrom item)),("to",JStr (graphEdgeTo item)),
   ("kind",JStr (graphEdgeKind item)),("label",JStr (graphEdgeLabel item))]

optional :: Text -> Maybe Text -> [(Text,J)]
optional _ Nothing = []
optional key (Just value) = [(key,JStr value)]

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
    ++ map (edgeSvg positions) (semanticGraphEdges graph)
    ++ ["</g><g id=\"nodes\">"]
    ++ map (nodeSvg positions) ordered
    ++ ["</g>",legendSvg legendY,
        "<text x=\"24\" y=\"" <> number (height - 18) <> "\" font-size=\"11\" fill=\"#7f1d1d\">" <>
          escape (semanticGraphNotice graph) <> "</text>","</svg>"]))
  where
    ordered = sortOn (\item -> (nodeLayer (graphNodeKind item),graphNodeId item))
      (semanticGraphNodes graph)
    grouped = Map.fromListWith (++) [(nodeLayer (graphNodeKind item),[item]) | item <- ordered]
    placed = concat [zipWith (position layer) [0 :: Int ..] (reverse items)
      | (layer,items) <- Map.toAscList grouped]
    positions = Map.fromList [(graphNodeId item,(x,y)) | (item,x,y) <- placed]
    maxRows = maximum (1 : map length (Map.elems grouped))
    width = max 960 (fromIntegral (Map.size grouped) * 270 + 80)
    legendY = fromIntegral (maxRows * 130 + 60)
    height = legendY + 150
    position layer row item = (item,40 + fromIntegral layer * 270,
      40 + fromIntegral row * 130)

edgeSvg :: Map.Map Text (Double,Double) -> GraphEdge -> Text
edgeSvg positions edge = case (Map.lookup (graphEdgeFrom edge) positions,
    Map.lookup (graphEdgeTo edge) positions) of
  (Just (x1,y1),Just (x2,y2)) -> Text.concat
    ["<path class=\"edge\" data-kind=\"",escape (graphEdgeKind edge),"\" d=\"M ",
     number (x1 + 210)," ",number (y1 + 38)," C ",number (x1 + 235)," ",number (y1 + 38),
     " ",number (x2 - 25)," ",number (y2 + 38)," ",number x2," ",number (y2 + 38),"\"/>",
     "<text class=\"edge-label\" x=\"",number ((x1+x2)/2 + 90),"\" y=\"",
     number ((y1+y2)/2 + 31),"\">",escape (graphEdgeLabel edge),"</text>"]
  _ -> ""

nodeSvg :: Map.Map Text (Double,Double) -> GraphNode -> Text
nodeSvg positions item = case Map.lookup (graphNodeId item) positions of
  Nothing -> ""
  Just (x,y) -> Text.concat
    ["<g id=\"",xmlId (graphNodeId item),"\" data-semantic-id=\"",
     escape (graphNodeId item),"\" data-kind=\"",escape (graphNodeKind item),"\">",
     shape (graphNodeKind item) x y,
     "<text class=\"node-label\" x=\"",number (x+12),"\" y=\"",number (y+20),"\">",
     tspans (x+12) (wrapLabel (graphNodeLabel item)),"</text>",
     meta x y (graphNodeCitation item) (graphNodeStatus item),"</g>"]

shape :: Text -> Double -> Double -> Text
shape kindValue x y
  | kindValue == "actor" = Text.concat ["<ellipse cx=\"",number (x+105),"\" cy=\"",
      number (y+38),"\" rx=\"105\" ry=\"38\" fill=\"#f8fafc\" stroke=\"#1e3a8a\" stroke-width=\"2\"/>"]
  | kindValue `elem` ["exception","attachment","presumption"] = rect "8" "6 3" "#fff7ed" "#9a3412"
  | kindValue `elem` ["input","shared-fact"] = rect "0" "3 2" "#f0fdf4" "#166534"
  | kindValue `elem` ["all","any"] = rect "22" "" "#f5f3ff" "#6d28d9"
  | kindValue == "penalty" = rect "0" "8 3 2 3" "#fefce8" "#854d0e"
  | otherwise = rect "8" "" "#eff6ff" "#1d4ed8"
  where
    rect radius dash fill stroke = Text.concat
      ["<rect x=\"",number x,"\" y=\"",number y,"\" width=\"210\" height=\"76\" rx=\"",
       radius,"\" fill=\"",fill,"\" stroke=\"",stroke,"\" stroke-width=\"2\"",
       if Text.null dash then "" else " stroke-dasharray=\"" <> dash <> "\"","/>"]

meta :: Double -> Double -> Maybe Text -> Maybe Text -> Text
meta x y citation status = Text.concat
  [maybe "" (line (y+58) . ("citation: " <>)) citation,
   maybe "" (line (y+70) . ("status: " <>)) status]
  where line offset value = Text.concat ["<text class=\"node-meta\" x=\"",
          number (x+12),"\" y=\"",number offset,"\">",escape value,"</text>"]

tspans :: Double -> [Text] -> Text
tspans x values = Text.concat ["<tspan x=\"" <> number x <> "\" dy=\"" <>
  (if index == (0 :: Int) then "0" else "14") <> "\">" <> escape value <> "</tspan>"
  | (index,value) <- zip [0 :: Int ..] (take 3 values)]

wrapLabel :: Text -> [Text]
wrapLabel value = concatMap wrapLine (Text.lines value)
  where
    wrapLine line = go [] [] (Text.words line)
    go result current [] = reverse (if null current then result else Text.unwords (reverse current):result)
    go result current (word:rest)
      | Text.length (Text.unwords (reverse (word:current))) <= 30 = go result (word:current) rest
      | null current = go (word:result) [] rest
      | otherwise = go (Text.unwords (reverse current):result) [word] rest

legendSvg :: Double -> Text
legendSvg y = Text.concat
  ["<g id=\"legend\"><text class=\"legend\" x=\"24\" y=\"",number y,
   "\" font-weight=\"700\">Legend</text>",
   "<text class=\"legend\" x=\"24\" y=\"",number (y+20),
   "\">ellipse actor; square/dotted input or fact; rounded rule/group; dashed exception; dash-dot penalty. Colours are redundant.</text>",
   "<text class=\"legend\" x=\"24\" y=\"",number (y+40),
   "\">Statuses are supplied or technical: satisfied, not satisfied, unresolved, defeated, not evaluated.</text></g>"]

nodeLayer :: Text -> Int
nodeLayer kindValue
  | kindValue `elem` ["module","temporal","actor","input","shared-fact"] = 0
  | kindValue `elem` ["all","any","element","relation","presumption"] = 1
  | kindValue `elem` ["definition","exception","attachment"] = 2
  | kindValue `elem` ["offence","participation","attempt","rule","allegation"] = 3
  | kindValue == "penalty" = 4
  | otherwise = 2

viewText :: DiagramView -> Text
viewText view = case view of
  RuleView -> "rule"
  ModulesView -> "modules"
  CaseView -> "case"
  TraceView -> "trace"

escape :: Text -> Text
escape = Text.concatMap character
  where
    character '&' = "&amp;"
    character '<' = "&lt;"
    character '>' = "&gt;"
    character '\"' = "&quot;"
    character '\'' = "&apos;"
    character value = Text.singleton value

xmlId :: Text -> Text
xmlId = ("node-" <>) . Text.map (\value -> if valid value then value else '-')
  where valid value = value `elem` ['a'..'z'] || value `elem` ['A'..'Z']
          || value `elem` ['0'..'9'] || value `elem` ['-','_','.']

number :: Double -> Text
number = Text.pack . show . (round :: Double -> Int)
