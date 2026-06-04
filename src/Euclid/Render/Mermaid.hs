{-# LANGUAGE OverloadedStrings #-}

module Euclid.Render.Mermaid
    ( renderMermaid
    ) where

import Data.List (sortOn)
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Model.Types (TimePoint(..), TimelineKind(..), timePointOrdinal)
import Euclid.Render.Layout

data MermaidTimeMode
    = MermaidDates
    | MermaidOrdinals
    deriving (Eq, Show)

renderMermaid :: Layout -> Text
renderMermaid layout =
    T.unlines $
        [ "gantt"
        , "    title Euclid Timeline"
        , dateFormatLine
        , axisFormatLine
        , "    todayMarker off"
        , "    %% Euclid relationships are not represented in Mermaid Gantt output."
        , "    %% Branch, parallel, and loop timelines render as labeled sections."
        ]
            ++ concatMap renderSection (layoutTimelines layout)
  where
    timeMode = mermaidTimeMode layout
    dateFormatLine =
        case timeMode of
            MermaidDates -> "    dateFormat YYYY-MM-DD"
            MermaidOrdinals -> "    dateFormat X"
    axisFormatLine =
        case timeMode of
            MermaidDates -> "    axisFormat %Y-%m-%d"
            MermaidOrdinals -> "    axisFormat %s"
    renderSection tl =
        ("    section " <> mermaidText (layoutTimelineName tl <> " [" <> timelineKindText (layoutTimelineKind tl) <> "]"))
            : map renderEntity (entitiesForTimeline tl)
    entitiesForTimeline tl =
        sortOn
            (\entity -> (layoutEntityLane entity, layoutEntityStart entity, layoutEntityName entity))
            [ entity
            | entity <- layoutEntities layout
            , layoutEntityTimeline entity == layoutTimelineName tl
            ]
    renderEntity entity =
        "    "
            <> mermaidText (entityLabel entity)
            <> " :"
            <> T.intercalate ", " (taskMetadata entity)
    taskMetadata entity
        | layoutEntityStart entity == layoutEntityEnd entity =
            ["milestone", renderPoint timeMode (layoutEntityStartPoint entity), "1d"]
        | otherwise =
            [renderPoint timeMode (layoutEntityStartPoint entity), renderPoint timeMode (layoutEntityEndPoint entity)]

mermaidTimeMode :: Layout -> MermaidTimeMode
mermaidTimeMode layout
    | not (null points) && all isDatePoint points = MermaidDates
    | otherwise = MermaidOrdinals
  where
    points =
        concat
            [ [layoutTimelineStartPoint timeline, layoutTimelineEndPoint timeline]
            | timeline <- layoutTimelines layout
            ]
            ++ concat
                [ [layoutEntityStartPoint entity, layoutEntityEndPoint entity]
                | entity <- layoutEntities layout
                ]
    isDatePoint (TimeDate _) = True
    isDatePoint (TimeOrdinal _) = False

renderPoint :: MermaidTimeMode -> TimePoint -> Text
renderPoint MermaidDates (TimeDate day) = T.pack (show day)
renderPoint MermaidDates point = T.pack (show (timePointOrdinal point))
renderPoint MermaidOrdinals point = T.pack (show (timePointOrdinal point))

entityLabel :: LayoutEntity -> Text
entityLabel entity =
    layoutEntityName entity
        <> " ["
        <> layoutEntityType entity
        <> maybe "" ("/" <>) (layoutEntityNarrative entity)
        <> "]"

timelineKindText :: TimelineKind -> Text
timelineKindText TimelineLinear = "linear"
timelineKindText TimelineBranch = "branch"
timelineKindText TimelineParallel = "parallel"
timelineKindText TimelineLoop = "loop"

mermaidText :: Text -> Text
mermaidText =
    T.strip
        . T.unwords
        . T.words
        . T.map
            ( \char ->
                case char of
                    ':' -> '-'
                    ',' -> ' '
                    '\n' -> ' '
                    '\r' -> ' '
                    '\t' -> ' '
                    _ -> char
            )
