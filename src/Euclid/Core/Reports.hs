{-# LANGUAGE OverloadedStrings #-}

module Euclid.Core.Reports
    ( renderContradictions
    , renderDeadlinesReport
    , renderExhibitsCsv
    , renderLegalReview
    , renderIssuesReport
    , renderScenarioDiff
    , renderScenarioReport
    , renderSourcesReport
    ) where

import Data.Char (isAlphaNum, toLower)
import qualified Data.List as List
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Core.Diff
import Euclid.Core.Validation
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

renderScenarioDiff :: World -> Text -> Either Text Text
renderScenarioDiff world scenarioName =
    case Map.lookup scenarioName (worldScenarios world) of
        Nothing -> Left ("unknown scenario: " <> scenarioName)
        Just scenarioWorld ->
            Right $
                T.unlines
                    [ "Scenario: " <> scenarioName
                    , "fork_from: " <> maybe "-" (maybe "-" id) (Map.lookup scenarioName (worldScenarioForks world))
                    , "scenario_diagnostics:"
                    ]
                    <> T.unlines (map ("  " <>) (renderDiagnostics (validateWorld scenarioWorld)))
                    <> "\n"
                    <> diffWorlds world scenarioWorld

renderScenarioReport :: World -> Text
renderScenarioReport world
    | Map.null (worldScenarios world) = "No scenarios.\n"
    | otherwise =
        T.unlines $
            "Scenarios:"
                : concatMap renderScenario (Map.toAscList (worldScenarios world))
  where
    renderScenario (scenarioName, scenarioWorld) =
        [ "- " <> scenarioName
        , "  fork_from: " <> maybe "-" (maybe "-" id) (Map.lookup scenarioName (worldScenarioForks world))
        , "  diagnostics:"
        ]
            ++ map ("    " <>) (renderDiagnostics (validateWorld scenarioWorld))
            ++ ["  diff:"]
            ++ map ("    " <>) (nonEmptyLines (diffWorlds world scenarioWorld))

renderLegalReview :: [Diagnostic] -> World -> Text
renderLegalReview diagnostics world =
    T.intercalate
        "\n"
        [ T.unlines ("Diagnostics:" : map ("  " <>) (renderDiagnostics diagnostics))
        , renderSourcesReport world
        , renderDeadlinesReport world
        , renderIssuesReport world
        , renderScenarioReport world
        ]

renderSourcesReport :: World -> Text
renderSourcesReport world =
    T.unlines $
        ["Source Bundles:"]
            ++ renderSourceBundles
            ++ [""]
            ++ ["Sources:"]
            ++ renderSources
            ++ [""]
            ++ ["Locators:"]
            ++ renderLocators
  where
    renderSourceBundles
        | Map.null (worldSourceBundles world) = ["  (none)"]
        | otherwise = concatMap renderSourceBundle (List.sortOn sourceBundleName (Map.elems (worldSourceBundles world)))
    renderSourceBundle sourceBundle =
        [ "- " <> sourceBundleName sourceBundle
        , "  sources: " <> renderBundleMembers (sourceBundleSources sourceBundle)
        , "  fields: " <> renderFields (sourceBundleFields sourceBundle)
        ]
    renderBundleMembers [] = "(none)"
    renderBundleMembers sourceNames =
        T.intercalate
            ", "
            [ sourceNameValue <> missingSuffix sourceNameValue
            | sourceNameValue <- sourceNames
            ]
    missingSuffix sourceNameValue
        | Map.member sourceNameValue (worldSources world) = ""
        | otherwise = " (missing)"
    renderSources
        | Map.null (worldSources world) = ["  (none)"]
        | otherwise = concatMap renderSource (List.sortOn sourceRecordName (Map.elems (worldSources world)))
    renderSource sourceRecord =
        [ "- " <> sourceRecordName sourceRecord <> " [" <> sourceRecordKind sourceRecord <> "]"
        , "  citation: " <> sourceFieldOrEmpty "citation" sourceRecord
        , "  normalized_citation: " <> normalizedSourceField "citation" sourceRecord
        , "  canonical_id: " <> sourceFieldOrEmpty "canonical_id" sourceRecord
        , "  normalized_canonical_id: " <> normalizedSourceField "canonical_id" sourceRecord
        , "  title: " <> sourceFieldOrEmpty "title" sourceRecord
        , "  url: " <> sourceFieldOrEmpty "url" sourceRecord
        , "  referenced_by: " <> renderEntityList (entitiesReferencingSource (sourceRecordName sourceRecord))
        ]
    sourceFieldOrEmpty fieldName sourceRecord =
        maybe "" valueToText (Map.lookup fieldName (sourceRecordFields sourceRecord))
    normalizedSourceField fieldName sourceRecord =
        case Map.lookup fieldName (sourceRecordFields sourceRecord) of
            Just (VString value) -> normalizeSourceText value
            _ -> ""
    entitiesReferencingSource sourceNameValue =
        List.sort
            [ entityName entity
            | entity <- Map.elems (worldEntities world)
            , entitySourceReference entity == Just sourceNameValue
            ]
    entitySourceReference entity =
        case Map.lookup "source_ref" (entityFields entity) of
            Just (VSourceRef sourceNameValue) -> Just sourceNameValue
            Just (VString sourceNameValue) -> Just sourceNameValue
            _ -> Nothing
    renderLocators
        | Map.null (worldSourceLocators world) = ["  (none)"]
        | otherwise = concatMap renderLocator (List.sortOn sourceLocatorName (Map.elems (worldSourceLocators world)))
    renderLocator locator =
        [ "- " <> sourceLocatorName locator
        , "  source_ref: " <> sourceLocatorSource locator <> missingSourceSuffix (sourceLocatorSource locator)
        , "  fields: " <> renderFields (sourceLocatorFields locator)
        ]
    missingSourceSuffix sourceNameValue
        | Map.member sourceNameValue (worldSources world) = ""
        | otherwise = " (missing)"

renderDeadlinesReport :: World -> Text
renderDeadlinesReport world =
    T.unlines $
        ["Rulesets:"]
            ++ renderRulesets
            ++ [""]
            ++ ["Deadline Rules:"]
            ++ renderDeadlineRules
            ++ [""]
            ++ ["Deadline Entities:"]
            ++ renderDeadlineEntities
  where
    renderRulesets
        | Map.null (worldRulesets world) = ["  (none)"]
        | otherwise = concatMap renderRuleset (List.sortOn rulesetName (Map.elems (worldRulesets world)))
    renderRuleset ruleset =
        [ "- " <> rulesetName ruleset
        , "  jurisdiction: " <> maybe "-" id (rulesetJurisdiction ruleset)
        , "  procedure: " <> maybe "-" id (rulesetProcedure ruleset)
        , "  court: " <> maybe "-" id (rulesetCourt ruleset)
        , "  effective: " <> maybe "-" renderRange (rulesetEffective ruleset)
        , "  source_ref: " <> maybe "-" renderSourceRef (rulesetSourceRef ruleset)
        , "  fields: " <> renderFields (rulesetFields ruleset)
        ]
    renderDeadlineRules
        | Map.null (worldDeadlineRules world) = ["  (none)"]
        | otherwise = concatMap renderDeadlineRule (List.sortOn deadlineRuleName (Map.elems (worldDeadlineRules world)))
    renderDeadlineRule deadlineRule =
        [ "- " <> deadlineRuleName deadlineRule
        , "  ruleset: " <> deadlineRuleRuleset deadlineRule <> missingRulesetSuffix (deadlineRuleRuleset deadlineRule)
        , "  rule: " <> deadlineRuleRule deadlineRule
        , "  trigger: " <> deadlineRuleTrigger deadlineRule
        , "  actor: " <> maybe "-" id (deadlineRuleActor deadlineRule)
        , "  action: " <> maybe "-" id (deadlineRuleAction deadlineRule)
        , "  offset: " <> valueToText (deadlineRuleOffset deadlineRule)
        , "  direction: " <> deadlineDirectionText (deadlineRuleDirection deadlineRule)
        , "  counting: " <> deadlineCountingText (deadlineRuleCounting deadlineRule)
        , "  source_ref: " <> maybe "-" renderSourceRef (deadlineRuleSourceRef deadlineRule)
        , "  fields: " <> renderFields (deadlineRuleFields deadlineRule)
        ]
    renderDeadlineEntities =
        case List.sortOn entityName [entity | entity <- Map.elems (worldEntities world), entityType entity == "deadline"] of
            [] -> ["  (none)"]
            deadlineEntities -> map renderDeadlineEntity deadlineEntities
    renderDeadlineEntity entity =
        "- "
            <> entityName entity
            <> " | rule="
            <> fieldOrEmpty "rule" entity
            <> " | due="
            <> fieldOrEmpty "due" entity
            <> " | jurisdiction="
            <> fieldOrEmpty "jurisdiction" entity
            <> " | rule_ref="
            <> maybe "-" valueToText (Map.lookup "rule_ref" (entityFields entity))
            <> " | source_ref="
            <> maybe "-" valueToText (Map.lookup "source_ref" (entityFields entity))
    renderSourceRef sourceNameValue =
        sourceNameValue <> missingSourceSuffix sourceNameValue
    missingSourceSuffix sourceNameValue
        | Map.member sourceNameValue (worldSources world) = ""
        | otherwise = " (missing)"
    missingRulesetSuffix rulesetNameValue
        | Map.member rulesetNameValue (worldRulesets world) = ""
        | otherwise = " (missing)"

renderIssuesReport :: World -> Text
renderIssuesReport world =
    T.unlines $
        ["Issues:"]
            ++ renderIssues
            ++ [""]
            ++ ["Elements:"]
            ++ renderElements
  where
    renderIssues
        | Map.null (worldIssues world) = ["  (none)"]
        | otherwise = concatMap renderIssue (List.sortOn legalIssueName (Map.elems (worldIssues world)))
    renderIssue issue =
        [ "- " <> legalIssueName issue
        , "  title: " <> maybe "-" id (legalIssueTitle issue)
        , "  question: " <> maybe "-" id (legalIssueQuestion issue)
        , "  burden: " <> maybe "-" id (legalIssueBurden issue)
        , "  standard: " <> maybe "-" id (legalIssueStandard issue)
        , "  source_ref: " <> maybe "-" renderSourceRef (legalIssueSourceRef issue)
        , "  fields: " <> renderFields (legalIssueFields issue)
        ]
    renderElements
        | Map.null (worldIssueElements world) = ["  (none)"]
        | otherwise = concatMap renderElement (List.sortOn issueElementName (Map.elems (worldIssueElements world)))
    renderElement element =
        [ "- " <> issueElementName element
        , "  issue: " <> issueElementIssue element <> missingIssueSuffix (issueElementIssue element)
        , "  text: " <> issueElementText element
        , "  burden: " <> maybe "-" id (issueElementBurden element)
        , "  source_ref: " <> maybe "-" renderSourceRef (issueElementSourceRef element)
        , "  fields: " <> renderFields (issueElementFields element)
        ]
    renderSourceRef sourceNameValue =
        sourceNameValue <> missingSourceSuffix sourceNameValue
    missingSourceSuffix sourceNameValue
        | Map.member sourceNameValue (worldSources world) = ""
        | otherwise = " (missing)"
    missingIssueSuffix issueNameValue
        | Map.member issueNameValue (worldIssues world) = ""
        | otherwise = " (missing)"

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

renderFields :: Map.Map Text Value -> Text
renderFields fields
    | Map.null fields = "-"
    | otherwise =
        T.intercalate
            ", "
            [ fieldName <> "=" <> valueToText fieldValue
            | (fieldName, fieldValue) <- Map.toAscList fields
            ]

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
valueToText (VRange rangeValue) =
    renderTimePointForReport (rangeStart rangeValue) <> ".." <> renderTimePointForReport (rangeEnd rangeValue)
valueToText (VEntityRef name) = name
valueToText (VSourceRef name) = name
valueToText (VTimelineRef name) = name
valueToText (VRulesetRef name) = name
valueToText (VDeadlineRuleRef name) = name
valueToText (VLocatorRef name) = name
valueToText (VIssueRef name) = name
valueToText (VIssueElementRef name) = name
valueToText (VClosureRef closureId) = "<closure:" <> T.pack (show closureId) <> ">"

renderRange :: TimeRange -> Text
renderRange rangeValue =
    renderTimePointForReport (rangeStart rangeValue) <> ".." <> renderTimePointForReport (rangeEnd rangeValue)

deadlineCountingText :: DeadlineCounting -> Text
deadlineCountingText CountingCalendarDays = "calendar_days"
deadlineCountingText CountingCalendarDaysWithLastDayRollover = "calendar_days_with_last_day_rollover"
deadlineCountingText CountingClearDays = "clear_days"
deadlineCountingText CountingBusinessDays = "business_days"
deadlineCountingText CountingCourtDays = "court_days"

deadlineDirectionText :: DeadlineDirection -> Text
deadlineDirectionText DeadlineAfter = "after"
deadlineDirectionText DeadlineBefore = "before"

normalizeSourceText :: Text -> Text
normalizeSourceText =
    T.unwords
        . T.words
        . T.map normalizeChar
        . T.strip
  where
    normalizeChar charValue
        | isAlphaNum charValue = toLower charValue
        | otherwise = ' '

renderEntityList :: [Text] -> Text
renderEntityList [] = "(none)"
renderEntityList values = T.intercalate ", " values

nonEmptyLines :: Text -> [Text]
nonEmptyLines =
    filter (not . T.null) . T.lines

renderDiagnostics :: [Diagnostic] -> [Text]
renderDiagnostics [] = ["(none)"]
renderDiagnostics diagnostics = map renderDiagnostic diagnostics

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
