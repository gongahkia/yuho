{-# LANGUAGE OverloadedStrings #-}

module Euclid.Core.Diff
    ( diffWorlds
    ) where

import Data.List (sort)
import qualified Data.Map.Strict as Map
import Data.Set (Set)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Model.Types

diffWorlds :: World -> World -> Text
diffWorlds leftWorld rightWorld =
    T.unlines $
        concat
            [ renderNamedSection "Sources" (worldSources leftWorld) (worldSources rightWorld) renderSource
            , renderNamedSection "Source Bundles" (worldSourceBundles leftWorld) (worldSourceBundles rightWorld) renderSourceBundle
            , renderNamedSection "Source Locators" (worldSourceLocators leftWorld) (worldSourceLocators rightWorld) renderSourceLocator
            , renderNamedSection "Rulesets" (worldRulesets leftWorld) (worldRulesets rightWorld) renderRuleset
            , renderNamedSection "Deadline Rules" (worldDeadlineRules leftWorld) (worldDeadlineRules rightWorld) renderDeadlineRule
            , renderNamedSection "Issues" (worldIssues leftWorld) (worldIssues rightWorld) renderIssue
            , renderNamedSection "Issue Elements" (worldIssueElements leftWorld) (worldIssueElements rightWorld) renderIssueElement
            , renderNamedSection "Timelines" (worldTimelines leftWorld) (worldTimelines rightWorld) renderTimeline
            , renderNamedSection "Entities" (worldEntities leftWorld) (worldEntities rightWorld) renderEntity
            , renderNamedSection "Relationship Types" (worldRelationshipTypes leftWorld) (worldRelationshipTypes rightWorld) renderRelationshipType
            , renderSetSection "Relationships" leftRelationships rightRelationships
            ]
  where
    leftRelationships = Set.fromList (map renderRelationshipSummary (worldRelationships leftWorld))
    rightRelationships = Set.fromList (map renderRelationshipSummary (worldRelationships rightWorld))

renderNamedSection :: Text -> Map.Map Text a -> Map.Map Text a -> (a -> Text) -> [Text]
renderNamedSection title leftMap rightMap renderValue =
    [ title <> ":"
    ]
        ++ renderDelta "+ only in right" addedNames
        ++ renderDelta "- only in left" removedNames
        ++ renderChanged changedEntries
  where
    leftNames = Set.fromList (Map.keys leftMap)
    rightNames = Set.fromList (Map.keys rightMap)
    addedNames = Set.toList (rightNames `Set.difference` leftNames)
    removedNames = Set.toList (leftNames `Set.difference` rightNames)
    changedEntries =
        [ (name, leftSummary, rightSummary)
        | name <- sort (Set.toList (leftNames `Set.intersection` rightNames))
        , let leftSummary = renderValue (leftMap Map.! name)
        , let rightSummary = renderValue (rightMap Map.! name)
        , leftSummary /= rightSummary
        ]

renderSetSection :: Text -> Set Text -> Set Text -> [Text]
renderSetSection title leftSet rightSet =
    [ title <> ":"
    ]
        ++ renderDelta "+ only in right" (Set.toList (rightSet `Set.difference` leftSet))
        ++ renderDelta "- only in left" (Set.toList (leftSet `Set.difference` rightSet))

renderDelta :: Text -> [Text] -> [Text]
renderDelta _ [] = ["  (no differences)"]
renderDelta label values =
    map (\value -> "  " <> label <> " " <> value) (sort values)

renderChanged :: [(Text, Text, Text)] -> [Text]
renderChanged [] = []
renderChanged entries =
    concatMap
        (\(name, leftSummary, rightSummary) -> ["  ~ changed " <> name, "    left: " <> leftSummary, "    right: " <> rightSummary])
        entries

renderTimeline :: Timeline -> Text
renderTimeline timeline =
    T.intercalate
        " | "
        [ "kind=" <> T.pack (show (timelineKind timeline))
        , "start=" <> T.pack (show (timePointOrdinal (timelineStart timeline)))
        , "end=" <> T.pack (show (timePointOrdinal (timelineEnd timeline)))
        , "parent=" <> maybe "-" id (timelineParent timeline)
        , "jurisdiction=" <> maybe "-" id (timelineJurisdiction timeline)
        , "court=" <> maybe "-" id (timelineCourt timeline)
        , "procedure=" <> maybe "-" id (timelineProcedure timeline)
        , "fork_from=" <> maybe "-" renderTimelineRef (timelineForkFrom timeline)
        , "merge_into=" <> maybe "-" renderTimelineRef (timelineMergeInto timeline)
        , "loop=" <> maybe "-" (T.pack . show) (timelineLoopCount timeline)
        ]

renderSource :: SourceRecord -> Text
renderSource sourceRecord =
    T.intercalate
        " | "
        [ "kind=" <> sourceRecordKind sourceRecord
        , "fields=" <> renderFields (sourceRecordFields sourceRecord)
        ]

renderSourceBundle :: SourceBundle -> Text
renderSourceBundle sourceBundle =
    T.intercalate
        " | "
        [ "sources=" <> renderTypeList (sourceBundleSources sourceBundle)
        , "fields=" <> renderFields (sourceBundleFields sourceBundle)
        ]

renderSourceLocator :: SourceLocator -> Text
renderSourceLocator locator =
    T.intercalate
        " | "
        [ "source_ref=" <> sourceLocatorSource locator
        , "fields=" <> renderFields (sourceLocatorFields locator)
        ]

renderRuleset :: Ruleset -> Text
renderRuleset ruleset =
    T.intercalate
        " | "
        [ "jurisdiction=" <> maybe "-" id (rulesetJurisdiction ruleset)
        , "court=" <> maybe "-" id (rulesetCourt ruleset)
        , "procedure=" <> maybe "-" id (rulesetProcedure ruleset)
        , "effective=" <> maybe "-" renderRange (rulesetEffective ruleset)
        , "source_ref=" <> maybe "-" id (rulesetSourceRef ruleset)
        , "fields=" <> renderFields (rulesetFields ruleset)
        ]

renderDeadlineRule :: DeadlineRule -> Text
renderDeadlineRule deadlineRule =
    T.intercalate
        " | "
        [ "ruleset=" <> deadlineRuleRuleset deadlineRule
        , "rule=" <> deadlineRuleRule deadlineRule
        , "trigger=" <> deadlineRuleTrigger deadlineRule
        , "actor=" <> maybe "-" id (deadlineRuleActor deadlineRule)
        , "action=" <> maybe "-" id (deadlineRuleAction deadlineRule)
        , "offset=" <> renderValue (deadlineRuleOffset deadlineRule)
        , "direction=" <> deadlineDirectionText (deadlineRuleDirection deadlineRule)
        , "counting=" <> deadlineCountingText (deadlineRuleCounting deadlineRule)
        , "source_ref=" <> maybe "-" id (deadlineRuleSourceRef deadlineRule)
        , "fields=" <> renderFields (deadlineRuleFields deadlineRule)
        ]

renderIssue :: LegalIssue -> Text
renderIssue issue =
    T.intercalate
        " | "
        [ "title=" <> maybe "-" id (legalIssueTitle issue)
        , "question=" <> maybe "-" id (legalIssueQuestion issue)
        , "burden=" <> maybe "-" id (legalIssueBurden issue)
        , "standard=" <> maybe "-" id (legalIssueStandard issue)
        , "source_ref=" <> maybe "-" id (legalIssueSourceRef issue)
        , "fields=" <> renderFields (legalIssueFields issue)
        ]

renderIssueElement :: IssueElement -> Text
renderIssueElement issueElement =
    T.intercalate
        " | "
        [ "issue=" <> issueElementIssue issueElement
        , "text=" <> issueElementText issueElement
        , "burden=" <> maybe "-" id (issueElementBurden issueElement)
        , "source_ref=" <> maybe "-" id (issueElementSourceRef issueElement)
        , "fields=" <> renderFields (issueElementFields issueElement)
        ]

renderRelationshipType :: RelationshipType -> Text
renderRelationshipType relationshipType =
    T.intercalate
        " | "
        [ "source=" <> renderTypeList (relationshipSourceTypes semantics)
        , "target=" <> renderTypeList (relationshipTargetTypes semantics)
        , "temporal=" <> maybe "-" temporalRuleText (relationshipTemporalRule semantics)
        , "required=" <> if relationshipTypeRequired relationshipType then "true" else "false"
        , "cardinality=" <> renderCardinality (relationshipTypeCardinality relationshipType)
        ]
  where
    semantics = relationshipTypeSemantics relationshipType

renderEntity :: Entity -> Text
renderEntity entity =
    T.intercalate
        " | "
        [ "type=" <> entityType entity
        , "fields=" <> renderFields (entityFields entity)
        , "appears=" <> renderAppearances (entityAppearances entity)
        ]

renderFields :: Map.Map Text Value -> Text
renderFields fields
    | Map.null fields = "-"
    | otherwise =
        T.intercalate
            ", "
            [ key <> "=" <> renderValue value
            | (key, value) <- Map.toAscList fields
            ]

renderValue :: Value -> Text
renderValue value =
    case value of
        VNull -> "null"
        VString textValue -> textValue
        VInt intValue -> T.pack (show intValue)
        VBool boolValue -> if boolValue then "true" else "false"
        VDate day -> T.pack (show day)
        VDuration years months days -> T.pack (show years) <> "y " <> T.pack (show months) <> "m " <> T.pack (show days) <> "d"
        VList values -> "[" <> T.intercalate ", " (map renderValue values) <> "]"
        VRange rangeValue -> renderRange rangeValue
        VEntityRef name -> name
        VSourceRef name -> name
        VTimelineRef name -> name
        VRulesetRef name -> name
        VDeadlineRuleRef name -> name
        VLocatorRef name -> name
        VIssueRef name -> name
        VIssueElementRef name -> name
        VClosureRef closureId -> "<closure:" <> T.pack (show closureId) <> ">"

renderAppearances :: [Appearance] -> Text
renderAppearances [] = "-"
renderAppearances appearances =
    T.intercalate
        ", "
        [ appearanceTimeline appearance
            <> "@"
            <> T.pack (show (timePointOrdinal (rangeStart (appearanceRange appearance))))
            <> ".."
            <> T.pack (show (timePointOrdinal (rangeEnd (appearanceRange appearance))))
        | appearance <- appearances
        ]

renderRelationshipSummary :: Relationship -> Text
renderRelationshipSummary relationship =
    relSource relationship
        <> " "
        <> maybe "--" (\label -> "-[" <> label <> "]->") (relLabel relationship)
        <> " "
        <> relTarget relationship

renderTypeList :: [Text] -> Text
renderTypeList [] = "any"
renderTypeList values = T.intercalate "," values

renderTimelineRef :: (Text, TimePoint) -> Text
renderTimelineRef (name, point) =
    name <> "@" <> renderTimePoint point

renderRange :: TimeRange -> Text
renderRange rangeValue =
    renderTimePoint (rangeStart rangeValue) <> ".." <> renderTimePoint (rangeEnd rangeValue)

renderCardinality :: RelationshipCardinality -> Text
renderCardinality cardinality
    | null parts = "-"
    | otherwise = T.intercalate "," parts
  where
    parts =
        concat
            [ maybe [] (\value -> ["min_inbound=" <> T.pack (show value)]) (relationshipMinInbound cardinality)
            , maybe [] (\value -> ["max_inbound=" <> T.pack (show value)]) (relationshipMaxInbound cardinality)
            , maybe [] (\value -> ["min_outbound=" <> T.pack (show value)]) (relationshipMinOutbound cardinality)
            , maybe [] (\value -> ["max_outbound=" <> T.pack (show value)]) (relationshipMaxOutbound cardinality)
            ]

temporalRuleText :: RelationshipTemporalRule -> Text
temporalRuleText SourceBeforeTarget = "source_before_target"
temporalRuleText SourceAfterTarget = "source_after_target"

deadlineCountingText :: DeadlineCounting -> Text
deadlineCountingText CountingCalendarDays = "calendar_days"
deadlineCountingText CountingCalendarDaysWithLastDayRollover = "calendar_days_with_last_day_rollover"
deadlineCountingText CountingClearDays = "clear_days"
deadlineCountingText CountingBusinessDays = "business_days"
deadlineCountingText CountingCourtDays = "court_days"

deadlineDirectionText :: DeadlineDirection -> Text
deadlineDirectionText DeadlineAfter = "after"
deadlineDirectionText DeadlineBefore = "before"
