{-# LANGUAGE OverloadedStrings #-}

module Euclid.Core.Filter
    ( filterWorldByNarrative
    ) where

import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import Euclid.Model.Types

filterWorldByNarrative :: Text -> World -> World
filterWorldByNarrative narrativeName world =
    world
        { worldTimelines = filteredTimelines
        , worldEntities = filteredEntities
        , worldRelationships = filteredRelationships
        }
  where
    filteredEntities =
        Map.filter (entityInNarrative narrativeName) (worldEntities world)
    keptEntityNames = Map.keysSet filteredEntities
    referencedTimelines =
        Set.fromList
            [ appearanceTimeline appearance
            | entity <- Map.elems filteredEntities
            , appearance <- entityAppearances entity
            ]
    filteredTimelines =
        Map.filterWithKey
            (\timelineId _ -> Set.member timelineId referencedTimelines)
            (worldTimelines world)
    filteredRelationships =
        [ relationship
        | relationship <- worldRelationships world
        , Set.member (relSource relationship) keptEntityNames
        , Set.member (relTarget relationship) keptEntityNames
        ]

entityInNarrative :: Text -> Entity -> Bool
entityInNarrative narrativeName entity =
    case Map.lookup "narrative" (entityFields entity) of
        Just (VString entityNarrative) -> entityNarrative == narrativeName
        _ -> True
