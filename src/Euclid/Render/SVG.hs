{-# LANGUAGE OverloadedStrings #-}

module Euclid.Render.SVG
    ( SvgOptions(..)
    , defaultSvgOptions
    , renderSvg
    ) where

import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Config.Loader (SvgTheme(..), darkTheme)
import Euclid.Render.Layout

data SvgOptions = SvgOptions
    { svgWidth :: Int
    , svgHeight :: Int
    , svgTitle :: Text
    , svgTheme :: SvgTheme
    }
    deriving (Eq, Show)

defaultSvgOptions :: SvgOptions
defaultSvgOptions =
    SvgOptions
        { svgWidth = 1600
        , svgHeight = 900
        , svgTitle = "Euclid"
        , svgTheme = darkTheme
        }

renderSvg :: SvgOptions -> Layout -> Text
renderSvg options layout =
    T.unlines $
        [ "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        , "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"" <> showText (svgWidth options) <> "\" height=\"" <> showText (svgHeight options) <> "\" viewBox=\"0 0 " <> showText (svgWidth options) <> " " <> showText (svgHeight options) <> "\">"
        , "<rect width=\"100%\" height=\"100%\" fill=\"" <> themeBackground (svgTheme options) <> "\"/>"
        , "<text x=\"32\" y=\"48\" fill=\"" <> themeText (svgTheme options) <> "\" font-size=\"28\" font-family=\"monospace\">" <> escapeXml (svgTitle options) <> "</text>"
        ]
            ++ map renderTimeline (layoutTimelines layout)
            ++ map renderEntity (layoutEntities layout)
            ++ map renderRelationship (layoutRelationships layout)
            ++ ["</svg>"]
  where
    minTime = layoutMinTime layout
    maxTime = max (layoutMaxTime layout) (minTime + 1)
    drawableWidth = fromIntegral (svgWidth options - 120) :: Double
    originX = 80.0 :: Double
    originY = 100.0 :: Double
    laneHeight = 54.0 :: Double
    scaleX ordinal =
        let numerator = fromIntegral (ordinal - minTime)
            denominator = fromIntegral (maxTime - minTime)
         in originX + numerator / denominator * drawableWidth
    laneY laneIndex = originY + fromIntegral laneIndex * laneHeight
    renderTimeline timeline =
        T.concat
            [ "<g>"
            , "<line x1=\""
            , showDouble (scaleX (layoutTimelineStart timeline))
            , "\" y1=\""
            , showDouble (laneY (layoutTimelineLane timeline))
            , "\" x2=\""
            , showDouble (scaleX (layoutTimelineEnd timeline))
            , "\" y2=\""
            , showDouble (laneY (layoutTimelineLane timeline))
            , "\" stroke=\""
            , themeText (svgTheme options)
            , "\" stroke-width=\"3\" opacity=\"0.35\"/>"
            , "<text x=\"20\" y=\""
            , showDouble (laneY (layoutTimelineLane timeline) + 6)
            , "\" fill=\""
            , themeTimeline (svgTheme options)
            , "\" font-family=\"monospace\" font-size=\"16\">"
            , escapeXml (layoutTimelineName timeline)
            , "</text>"
            , "</g>"
            ]
    renderEntity entity =
        let y = laneY (layoutEntityLane entity) - 16
            x = scaleX (layoutEntityStart entity)
            width = max 14.0 (scaleX (layoutEntityEnd entity) - x)
            fillColor = maybe (themeEntity (svgTheme options)) narrativeColor (layoutEntityNarrative entity)
         in T.concat
                [ "<g>"
                , "<rect x=\""
                , showDouble x
                , "\" y=\""
                , showDouble y
                , "\" width=\""
                , showDouble width
                , "\" height=\"28\" rx=\"6\" fill=\""
                , fillColor
                , "\" opacity=\"0.9\""
                , maybe "" (\narrative -> " data-narrative=\"" <> escapeXml narrative <> "\"") (layoutEntityNarrative entity)
                , "/>"
                , "<text x=\""
                , showDouble (x + 8)
                , "\" y=\""
                , showDouble (y + 19)
                , "\" fill=\""
                , themeText (svgTheme options)
                , "\" font-family=\"monospace\" font-size=\"14\">"
                , escapeXml (layoutEntityName entity <> " [" <> layoutEntityType entity <> "]")
                , "</text>"
                , "</g>"
                ]
    renderRelationship relationship =
        case lookupEntityMidpoint (layoutRelSource relationship) of
            Nothing -> ""
            Just (sourceX, sourceY) ->
                case lookupEntityMidpoint (layoutRelTarget relationship) of
                    Nothing -> ""
                    Just (targetX, targetY) ->
                        let isContradiction = layoutRelLabel relationship == Just "contradicts"
                            strokeColor = if isContradiction then "#dc2626" else themeRelationship (svgTheme options)
                            strokeWidth = if isContradiction then "2.75" else "1.5"
                            dashArray = if isContradiction then "" else " stroke-dasharray=\"5,5\""
                            relClass = if isContradiction then "relationship contradiction" else "relationship"
                         in
                        T.concat
                            [ "<g>"
                            , renderRelationshipShape relClass strokeColor strokeWidth dashArray sourceX sourceY targetX targetY
                            , "<text x=\""
                            , showDouble ((sourceX + targetX) / 2)
                            , "\" y=\""
                            , showDouble ((sourceY + targetY) / 2 - 4)
                            , "\" fill=\""
                            , strokeColor
                            , "\" font-family=\"monospace\" font-size=\"12\">"
                            , escapeXml (maybe "rel" id (layoutRelLabel relationship))
                            , "</text>"
                            , "</g>"
                            ]
    lookupEntityMidpoint name =
        case filter (\entity -> layoutEntityName entity == name) (layoutEntities layout) of
            [] -> Nothing
            (entity : _) ->
                let x1 = scaleX (layoutEntityStart entity)
                    x2 = scaleX (layoutEntityEnd entity)
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

showText :: Show a => a -> Text
showText = T.pack . show

showDouble :: Double -> Text
showDouble = T.pack . show

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
