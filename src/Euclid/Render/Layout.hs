{-# LANGUAGE OverloadedStrings #-}

module Euclid.Render.Layout
    ( Layout(..)
    , LayoutEntity(..)
    , LayoutRelationship(..)
    , LayoutTimeline(..)
    , computeLayout
    ) where

import Data.List (sortOn)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import Euclid.Model.Types

data LayoutTimeline = LayoutTimeline
    { layoutTimelineName :: Text
    , layoutTimelineKind :: TimelineKind
    , layoutTimelineLane :: Int
    , layoutTimelineStart :: Integer
    , layoutTimelineEnd :: Integer
    }
    deriving (Eq, Show)

data LayoutEntity = LayoutEntity
    { layoutEntityName :: Text
    , layoutEntityType :: Text
    , layoutEntityNarrative :: Maybe Text
    , layoutEntityTimeline :: Text
    , layoutEntityLane :: Int
    , layoutEntityStart :: Integer
    , layoutEntityEnd :: Integer
    }
    deriving (Eq, Show)

data LayoutRelationship = LayoutRelationship
    { layoutRelSource :: Text
    , layoutRelTarget :: Text
    , layoutRelLabel :: Maybe Text
    }
    deriving (Eq, Show)

data Layout = Layout
    { layoutTimelines :: [LayoutTimeline]
    , layoutEntities :: [LayoutEntity]
    , layoutRelationships :: [LayoutRelationship]
    , layoutMinTime :: Integer
    , layoutMaxTime :: Integer
    }
    deriving (Eq, Show)

computeLayout :: World -> Layout
computeLayout world =
    Layout
        { layoutTimelines = timelines
        , layoutEntities = entities
        , layoutRelationships =
            [ LayoutRelationship (relSource relationship) (relTarget relationship) (relLabel relationship)
            | relationship <- worldRelationships world
            ]
        , layoutMinTime = if null allTimes then 0 else minimum allTimes
        , layoutMaxTime = if null allTimes then 100 else maximum allTimes
        }
  where
    timelineValues = sortOn (timePointOrdinal . timelineStart) (Map.elems (worldTimelines world))
    timelineLaneMap = snd (foldl assignTimelineLane (0, Map.empty) timelineValues)
    assignTimelineLane (nextLane, laneMap) timeline =
        let rowsForTimeline = sortedRowsForTimeline (timelineName timeline)
            laneSpan = max 2 (length rowsForTimeline + 2)
         in (nextLane + laneSpan, Map.insert (timelineName timeline) nextLane laneMap)
    timelines =
        [ LayoutTimeline
            { layoutTimelineName = timelineName timeline
            , layoutTimelineKind = timelineKind timeline
            , layoutTimelineLane = laneIndex
            , layoutTimelineStart = timePointOrdinal (timelineStart timeline)
            , layoutTimelineEnd = timePointOrdinal (timelineEnd timeline)
            }
        | timeline <- timelineValues
        , let laneIndex = Map.findWithDefault 0 (timelineName timeline) timelineLaneMap
        ]
    entityRows =
        [ ( appearanceTimeline appearance
          , timePointOrdinal (rangeStart (appearanceRange appearance))
          , entityName entity
          , appearanceIndex
          , entity
          , appearance
          )
        | entity <- Map.elems (worldEntities world)
        , (appearanceIndex, appearance) <- zip [0 :: Int ..] (entityAppearances entity)
        ]
    entityRowsByTimeline =
        Map.fromListWith
            (++)
            [(timelineNameValue, [row]) | row@(timelineNameValue, _, _, _, _, _) <- entityRows]
    sortedRowsForTimeline timelineNameValue =
        sortOn
            (\(_, startOrdinal, entityNameValue, appearanceIndex, _, _) -> (startOrdinal, entityNameValue, appearanceIndex))
            (Map.findWithDefault [] timelineNameValue entityRowsByTimeline)
    entityLaneMap =
        Map.fromList
            [ ( (entityName entity, appearanceIndex, appearanceTimeline appearance)
              , baseLane + rowIndex + 1
              )
            | timeline <- timelineValues
            , let baseLane = Map.findWithDefault 0 (timelineName timeline) timelineLaneMap
            , (rowIndex, (_, _, _, appearanceIndex, entity, appearance)) <-
                zip [0 :: Int ..] (sortedRowsForTimeline (timelineName timeline))
            ]
    entities =
        concatMap layoutEntityForTimeline (Map.elems (worldEntities world))
    layoutEntityForTimeline entity =
        [ LayoutEntity
            { layoutEntityName = entityName entity
            , layoutEntityType = entityType entity
            , layoutEntityNarrative = entityNarrative entity
            , layoutEntityTimeline = appearanceTimeline appearance
            , layoutEntityLane = entityLane
            , layoutEntityStart = timePointOrdinal (rangeStart (appearanceRange appearance))
            , layoutEntityEnd = timePointOrdinal (rangeEnd (appearanceRange appearance))
            }
        | (appearanceIndex, appearance) <- zip [0 ..] (entityAppearances entity)
        , let entityLane =
                Map.findWithDefault
                    appearanceIndex
                    (entityName entity, appearanceIndex, appearanceTimeline appearance)
                    entityLaneMap
        ]
    allTimes =
        [ layoutTimelineStart timeline
        | timeline <- timelines
        ]
            ++ [ layoutTimelineEnd timeline | timeline <- timelines ]
            ++ [ layoutEntityStart entity | entity <- entities ]
            ++ [ layoutEntityEnd entity | entity <- entities ]

entityNarrative :: Entity -> Maybe Text
entityNarrative entity =
    case Map.lookup "narrative" (entityFields entity) of
        Just (VString narrativeName) -> Just narrativeName
        _ -> Nothing
