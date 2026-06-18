{-# LANGUAGE OverloadedStrings #-}

module Euclid.Render.Diff
    ( renderDiffHtml
    , renderDiffSvg
    ) where

import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Config.Loader (SvgTheme(..))
import Euclid.Render.Layout
import Euclid.Render.SVG (SvgOptions(..))

renderDiffSvg :: SvgOptions -> Text -> Layout -> Text -> Layout -> Text
renderDiffSvg options leftTitle leftLayout rightTitle rightLayout =
    T.unlines $
        [ "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        , "<svg class=\"euclid-diff-svg\" xmlns=\"http://www.w3.org/2000/svg\" width=\"" <> showText canvasWidth <> "\" height=\"" <> showText canvasHeight <> "\" viewBox=\"0 0 " <> showText canvasWidth <> " " <> showText canvasHeight <> "\">"
        , "<rect width=\"100%\" height=\"100%\" fill=\"" <> themeBackground (svgTheme options) <> "\"/>"
        , "<text x=\"32\" y=\"42\" fill=\"" <> themeText (svgTheme options) <> "\" font-size=\"28\" font-family=\"monospace\">" <> escapeXml (svgTitle options) <> "</text>"
        , "<line x1=\"" <> showDouble dividerX <> "\" y1=\"64\" x2=\"" <> showDouble dividerX <> "\" y2=\"" <> showText (canvasHeight - 28) <> "\" stroke=\"" <> themeText (svgTheme options) <> "\" opacity=\"0.18\"/>"
        ]
            ++ renderColumn leftOriginX leftTitle leftLayout
            ++ renderColumn rightOriginX rightTitle rightLayout
            ++ ["</svg>"]
  where
    canvasWidth = svgWidth options
    canvasHeight = svgHeight options
    dividerX = fromIntegral canvasWidth / 2 :: Double
    columnWidth = fromIntegral canvasWidth / 2 - 72 :: Double
    leftOriginX = 40 :: Double
    rightOriginX = dividerX + 32
    originY = 92 :: Double
    laneHeight = 52 :: Double
    minTime = min (layoutMinTime leftLayout) (layoutMinTime rightLayout)
    maxTime = max (max (layoutMaxTime leftLayout) (layoutMaxTime rightLayout)) (minTime + 1)
    scaleX columnX ordinal =
        let numerator = fromIntegral (ordinal - minTime)
            denominator = fromIntegral (maxTime - minTime)
         in columnX + 40 + numerator / denominator * (columnWidth - 56)
    laneY laneIndex = originY + fromIntegral laneIndex * laneHeight
    renderColumn columnX title layout =
        [ "<text x=\"" <> showDouble columnX <> "\" y=\"72\" fill=\"" <> themeText (svgTheme options) <> "\" font-size=\"18\" font-family=\"monospace\">" <> escapeXml title <> "</text>"
        , "<rect x=\"" <> showDouble (columnX - 8) <> "\" y=\"82\" width=\"" <> showDouble columnWidth <> "\" height=\"" <> showText (canvasHeight - 116) <> "\" fill=\"none\" stroke=\"" <> themeText (svgTheme options) <> "\" opacity=\"0.14\"/>"
        ]
            ++ map (renderTimeline columnX) (layoutTimelines layout)
            ++ map (renderEntity columnX) (layoutEntities layout)
            ++ map (renderRelationship columnX layout) (layoutRelationships layout)
    renderTimeline columnX timeline =
        T.concat
            [ "<line x1=\""
            , showDouble (scaleX columnX (layoutTimelineStart timeline))
            , "\" y1=\""
            , showDouble (laneY (layoutTimelineLane timeline))
            , "\" x2=\""
            , showDouble (scaleX columnX (layoutTimelineEnd timeline))
            , "\" y2=\""
            , showDouble (laneY (layoutTimelineLane timeline))
            , "\" stroke=\""
            , themeText (svgTheme options)
            , "\" stroke-width=\"2\" opacity=\"0.3\"/>"
            , "<text x=\""
            , showDouble columnX
            , "\" y=\""
            , showDouble (laneY (layoutTimelineLane timeline) + 5)
            , "\" fill=\""
            , themeTimeline (svgTheme options)
            , "\" font-family=\"monospace\" font-size=\"13\">"
            , escapeXml (layoutTimelineName timeline)
            , "</text>"
            ]
    renderEntity columnX entity =
        let y = laneY (layoutEntityLane entity) - 14
            x = scaleX columnX (layoutEntityStart entity)
            width = max 16.0 (scaleX columnX (layoutEntityEnd entity) - x)
            fillColor = maybe (themeEntity (svgTheme options)) narrativeColor (layoutEntityNarrative entity)
            label = layoutEntityName entity
            labelWidth = estimatedTextWidth 11 label
            rightEdge = columnX - 8 + columnWidth - 8
            (labelX, labelAnchor)
                | x + width + 8 + labelWidth <= rightEdge = (x + width + 8, "")
                | x - 8 - labelWidth >= columnX = (x - 8, " text-anchor=\"end\"")
                | otherwise = (max columnX (rightEdge - labelWidth), "")
         in T.concat
                [ "<rect x=\""
                , showDouble x
                , "\" y=\""
                , showDouble y
                , "\" width=\""
                , showDouble width
                , "\" height=\"24\" rx=\"5\" fill=\""
                , fillColor
                , "\" opacity=\"0.9\""
                , maybe "" (\narrative -> " data-narrative=\"" <> escapeXml narrative <> "\"") (layoutEntityNarrative entity)
                , "/>"
                , "<text x=\""
                , showDouble labelX
                , "\" y=\""
                , showDouble (y + 16)
                , "\" fill=\""
                , themeText (svgTheme options)
                , "\" font-family=\"monospace\" font-size=\"11\""
                , labelAnchor
                , ">"
                , escapeXml label
                , "</text>"
                ]
    renderRelationship columnX layout relationship =
        case lookupEntityMidpoint columnX layout (layoutRelSource relationship) of
            Nothing -> ""
            Just (sourceX, sourceY) ->
                case lookupEntityMidpoint columnX layout (layoutRelTarget relationship) of
                    Nothing -> ""
                    Just (targetX, targetY) ->
                        let isContradiction = layoutRelLabel relationship == Just "contradicts"
                            strokeColor = if isContradiction then "#dc2626" else themeRelationship (svgTheme options)
                            strokeWidth = if isContradiction then "2.75" else "1.2"
                            dashArray = if isContradiction then "" else " stroke-dasharray=\"4,4\""
                            relClass = if isContradiction then "diff-relationship contradiction" else "diff-relationship"
                         in renderRelationshipShape relClass strokeColor strokeWidth dashArray sourceX sourceY targetX targetY
    lookupEntityMidpoint columnX layout name =
        case filter (\entity -> layoutEntityName entity == name) (layoutEntities layout) of
            [] -> Nothing
            (entity : _) ->
                let x1 = scaleX columnX (layoutEntityStart entity)
                    x2 = scaleX columnX (layoutEntityEnd entity)
                 in Just ((x1 + x2) / 2, laneY (layoutEntityLane entity) - 2)

    renderRelationshipShape relClass strokeColor strokeWidth dashArray sourceX sourceY targetX targetY
        | abs (sourceX - targetX) < 1 && abs (sourceY - targetY) < 1 =
            T.concat
                [ "<path d=\"M "
                , showDouble sourceX
                , " "
                , showDouble sourceY
                , " C "
                , showDouble sourceX
                , " "
                , showDouble (sourceY - 42)
                , " "
                , showDouble (sourceX + 72)
                , " "
                , showDouble (sourceY - 42)
                , " "
                , showDouble (sourceX + 72)
                , " "
                , showDouble sourceY
                , "\" fill=\"none\" stroke=\""
                , strokeColor
                , "\" stroke-width=\""
                , strokeWidth
                , "\" class=\""
                , relClass
                , "\""
                , dashArray
                , "/>"
                ]
        | otherwise =
            T.concat
                [ "<line x1=\""
                , showDouble sourceX
                , "\" y1=\""
                , showDouble sourceY
                , "\" x2=\""
                , showDouble targetX
                , "\" y2=\""
                , showDouble targetY
                , "\" stroke=\""
                , strokeColor
                , "\" stroke-width=\""
                , strokeWidth
                , "\" class=\""
                , relClass
                , "\""
                , dashArray
                , "/>"
                ]

renderDiffHtml :: SvgOptions -> Text -> Layout -> Text -> Layout -> Text
renderDiffHtml options leftTitle leftLayout rightTitle rightLayout =
    T.unlines
        [ "<!DOCTYPE html>"
        , "<html><head><meta charset=\"utf-8\">"
        , "<title>" <> escapeXml (svgTitle options) <> "</title>"
        , "<style>body{margin:0;background:#111827;color:#f9fafb;font-family:monospace}.wrap{padding:20px}.caption{margin:0 0 12px;color:#d1d5db}</style>"
        , "</head><body><main class=\"wrap\">"
        , "<p class=\"caption\">Side-by-side Euclid diff. Narrative entities use deterministic colors; contradiction edges are red.</p>"
        , renderDiffSvg options leftTitle leftLayout rightTitle rightLayout
        , "</main></body></html>"
        ]

showText :: Show a => a -> Text
showText = T.pack . show

showDouble :: Double -> Text
showDouble = T.pack . show

estimatedTextWidth :: Double -> Text -> Double
estimatedTextWidth fontSize text =
    fromIntegral (T.length text) * fontSize * 0.62

narrativeColor :: Text -> Text
narrativeColor narrative =
    narrativePalette !! (fromIntegral (hashText narrative `mod` fromIntegral (length narrativePalette)))

narrativePalette :: [Text]
narrativePalette =
    [ "#2563eb"
    , "#059669"
    , "#d97706"
    , "#7c3aed"
    , "#db2777"
    , "#0891b2"
    ]

hashText :: Text -> Integer
hashText =
    T.foldl' (\acc char -> acc * 33 + fromIntegral (fromEnum char)) 5381

escapeXml :: Text -> Text
escapeXml =
    T.concatMap
        ( \c ->
            case c of
                '<' -> "&lt;"
                '>' -> "&gt;"
                '&' -> "&amp;"
                '"' -> "&quot;"
                '\'' -> "&apos;"
                _ -> T.singleton c
        )
