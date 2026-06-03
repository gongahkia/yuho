{-# LANGUAGE OverloadedStrings #-}

module Euclid.Core.Reports
    ( renderContradictions
    , renderExhibitsCsv
    ) where

import qualified Data.List as List
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Model.Types

renderContradictions :: World -> Text
renderContradictions world
    | null contradictionRelationships = "No contradictions.\n"
    | otherwise =
        T.unlines $
            "Contradictions:"
                : concatMap renderContradiction contradictionRelationships
  where
    contradictionRelationships =
        [ relationship
        | relationship <- worldRelationships world
        , relLabel relationship == Just "contradicts"
        ]
    renderContradiction relationship =
        [ "- " <> relSource relationship <> " contradicts " <> relTarget relationship
        , "  timelines: " <> renderTimelineList (relationshipTimelines relationship)
        , "  source evidence:"
        ]
            ++ renderEvidenceList (supportingEvidence (relSource relationship))
            ++ ["  target evidence:"]
            ++ renderEvidenceList (supportingEvidence (relTarget relationship))
    relationshipTimelines relationship =
        case (findEntity (relSource relationship) world, findEntity (relTarget relationship) world) of
            (Just sourceEntity, Just targetEntity) -> sharedTimelineNames sourceEntity targetEntity
            _ -> []
    supportingEvidence targetName =
        List.sortOn entityName
            [ evidence
            | relationship <- worldRelationships world
            , relLabel relationship == Just "cites"
            , relTarget relationship == targetName
            , Just evidence <- [findEntity (relSource relationship) world]
            ]

renderExhibitsCsv :: World -> Text
renderExhibitsCsv world =
    T.unlines $
        csvRow ["number", "entity", "description", "timeline", "start", "end"]
            : concatMap renderExhibitRows exhibits
  where
    exhibits =
        List.sortOn
            (\entity -> (fieldOrEmpty "number" entity, entityName entity))
            [ entity
            | entity <- Map.elems (worldEntities world)
            , entityType entity == "exhibit"
            ]
    renderExhibitRows entity =
        case entityAppearances entity of
            [] -> [renderExhibitRow entity Nothing]
            appearances ->
                [ renderExhibitRow entity (Just appearance)
                | appearance <- List.sortOn appearanceSortKey appearances
                ]
    renderExhibitRow entity maybeAppearance =
        csvRow
            [ fieldOrEmpty "number" entity
            , entityName entity
            , fieldOrEmpty "description" entity
            , maybe "" appearanceTimeline maybeAppearance
            , maybe "" (renderTimePointForReport . rangeStart . appearanceRange) maybeAppearance
            , maybe "" (renderTimePointForReport . rangeEnd . appearanceRange) maybeAppearance
            ]
    appearanceSortKey appearance =
        ( appearanceTimeline appearance
        , timePointOrdinal (rangeStart (appearanceRange appearance))
        , timePointOrdinal (rangeEnd (appearanceRange appearance))
        )

renderEvidenceList :: [Entity] -> [Text]
renderEvidenceList [] = ["    (none)"]
renderEvidenceList evidenceEntities =
    map renderEvidence evidenceEntities

renderEvidence :: Entity -> Text
renderEvidence entity =
    "    - "
        <> entityName entity
        <> " | citation="
        <> fieldOrEmpty "citation" entity
        <> " | source="
        <> fieldOrEmpty "source" entity

fieldOrEmpty :: Text -> Entity -> Text
fieldOrEmpty fieldName entity =
    case fieldName of
        "source" ->
            case annotationSource (entityAnnotation entity) of
                Just sourceValue -> sourceValue
                Nothing -> maybe "" valueToText (Map.lookup fieldName (entityFields entity))
        _ ->
            maybe "" valueToText (Map.lookup fieldName (entityFields entity))

valueToText :: Value -> Text
valueToText VNull = ""
valueToText (VString value) = value
valueToText (VInt value) = T.pack (show value)
valueToText (VBool True) = "true"
valueToText (VBool False) = "false"
valueToText (VDate value) = T.pack (show value)
valueToText (VDuration years months days) =
    T.pack (show years) <> "y " <> T.pack (show months) <> "m " <> T.pack (show days) <> "d"
valueToText (VList values) =
    "[" <> T.intercalate ", " (map valueToText values) <> "]"
valueToText (VEntityRef name) = name
valueToText (VTimelineRef name) = name
valueToText (VClosureRef closureId) = "<closure:" <> T.pack (show closureId) <> ">"

renderTimePointForReport :: TimePoint -> Text
renderTimePointForReport (TimeDate day) = T.pack (show day)
renderTimePointForReport (TimeOrdinal value) = T.pack (show value)

csvRow :: [Text] -> Text
csvRow = T.intercalate "," . map csvField

csvField :: Text -> Text
csvField field
    | T.any (`elem` [',', '"', '\n', '\r']) field =
        "\"" <> T.replace "\"" "\"\"" field <> "\""
    | otherwise = field

sharedTimelineNames :: Entity -> Entity -> [Text]
sharedTimelineNames source target =
    Set.toAscList $
        timelineNames source `Set.intersection` timelineNames target
  where
    timelineNames entity =
        Set.fromList [appearanceTimeline appearance | appearance <- entityAppearances entity]

renderTimelineList :: [Text] -> Text
renderTimelineList [] = "(none)"
renderTimelineList values = T.intercalate ", " values
