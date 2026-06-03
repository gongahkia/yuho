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
        , layoutMinTime = minimum (allTimes ++ [0])
        , layoutMaxTime = maximum (allTimes ++ [100])
        }
  where
    timelineValues = sortOn (timePointOrdinal . timelineStart) (Map.elems (worldTimelines world))
    timelineLanes = zip timelineValues [0 ..]
    timelineLaneMap = Map.fromList [(timelineName timeline, laneIndex) | (timeline, laneIndex) <- timelineLanes]
    timelines =
        [ LayoutTimeline
            { layoutTimelineName = timelineName timeline
            , layoutTimelineKind = timelineKind timeline
            , layoutTimelineLane = laneIndex
            , layoutTimelineStart = timePointOrdinal (timelineStart timeline)
            , layoutTimelineEnd = timePointOrdinal (timelineEnd timeline)
            }
        | (timeline, laneIndex) <- timelineLanes
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
                maybe
                    appearanceIndex
                    (\baseLane -> baseLane + appearanceIndex + 1)
                    (Map.lookup (appearanceTimeline appearance) timelineLaneMap)
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
