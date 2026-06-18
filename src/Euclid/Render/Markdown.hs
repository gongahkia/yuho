{-# LANGUAGE OverloadedStrings #-}

module Euclid.Render.Markdown
    ( renderMarkdown
    ) where

import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Map.Strict as Map
import Euclid.Model.Types

renderMarkdown :: World -> Text
renderMarkdown world = T.unlines $
    ["# Timeline Summary", ""]
    ++ sourcesSection
    ++ [""]
    ++ sourceBundlesSection
    ++ [""]
    ++ sourceLocatorsSection
    ++ [""]
    ++ rulesetsSection
    ++ [""]
    ++ deadlineRulesSection
    ++ [""]
    ++ issuesSection
    ++ [""]
    ++ issueElementsSection
    ++ [""]
    ++ timelinesSection
    ++ [""]
    ++ entitiesSection
    ++ [""]
    ++ relationshipTypesSection
    ++ [""]
    ++ relationshipsSection
  where
    sourcesSection =
        ["## Sources", "", "| Name | Kind | Fields |", "| --- | --- | --- |"]
        ++ [ "| " <> sourceRecordName sourceRecord
            <> " | " <> sourceRecordKind sourceRecord
            <> " | " <> renderFields (sourceRecordFields sourceRecord)
            <> " |"
           | sourceRecord <- Map.elems (worldSources world)
           ]
    sourceBundlesSection =
        ["## Source Bundles", "", "| Name | Sources | Fields |", "| --- | --- | --- |"]
        ++ [ "| " <> sourceBundleName sourceBundle
            <> " | " <> renderTypeList (sourceBundleSources sourceBundle)
            <> " | " <> renderFields (sourceBundleFields sourceBundle)
            <> " |"
           | sourceBundle <- Map.elems (worldSourceBundles world)
           ]
    sourceLocatorsSection =
        ["## Source Locators", "", "| Name | Source | Fields |", "| --- | --- | --- |"]
        ++ [ "| " <> sourceLocatorName locator
            <> " | " <> sourceLocatorSource locator
            <> " | " <> renderFields (sourceLocatorFields locator)
            <> " |"
           | locator <- Map.elems (worldSourceLocators world)
           ]
    rulesetsSection =
        ["## Rulesets", "", "| Name | Jurisdiction | Court | Procedure | Effective | Source | Fields |", "| --- | --- | --- | --- | --- | --- | --- |"]
        ++ [ "| " <> rulesetName ruleset
            <> " | " <> maybe "-" id (rulesetJurisdiction ruleset)
            <> " | " <> maybe "-" id (rulesetCourt ruleset)
            <> " | " <> maybe "-" id (rulesetProcedure ruleset)
            <> " | " <> maybe "-" renderRange (rulesetEffective ruleset)
            <> " | " <> maybe "-" id (rulesetSourceRef ruleset)
            <> " | " <> renderFields (rulesetFields ruleset)
            <> " |"
           | ruleset <- Map.elems (worldRulesets world)
           ]
    deadlineRulesSection =
        ["## Deadline Rules", "", "| Name | Ruleset | Rule | Trigger | Actor | Action | Offset | Direction | Counting | Source |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        ++ [ "| " <> deadlineRuleName deadlineRule
            <> " | " <> deadlineRuleRuleset deadlineRule
            <> " | " <> deadlineRuleRule deadlineRule
            <> " | " <> deadlineRuleTrigger deadlineRule
            <> " | " <> maybe "-" id (deadlineRuleActor deadlineRule)
            <> " | " <> maybe "-" id (deadlineRuleAction deadlineRule)
            <> " | " <> valueText (deadlineRuleOffset deadlineRule)
            <> " | " <> deadlineDirectionText (deadlineRuleDirection deadlineRule)
            <> " | " <> deadlineCountingText (deadlineRuleCounting deadlineRule)
            <> " | " <> maybe "-" id (deadlineRuleSourceRef deadlineRule)
            <> " |"
           | deadlineRule <- Map.elems (worldDeadlineRules world)
           ]
    issuesSection =
        ["## Issues", "", "| Name | Title | Question | Burden | Standard | Source | Fields |", "| --- | --- | --- | --- | --- | --- | --- |"]
        ++ [ "| " <> legalIssueName issue
            <> " | " <> maybe "-" id (legalIssueTitle issue)
            <> " | " <> maybe "-" id (legalIssueQuestion issue)
            <> " | " <> maybe "-" id (legalIssueBurden issue)
            <> " | " <> maybe "-" id (legalIssueStandard issue)
            <> " | " <> maybe "-" id (legalIssueSourceRef issue)
            <> " | " <> renderFields (legalIssueFields issue)
            <> " |"
           | issue <- Map.elems (worldIssues world)
           ]
    issueElementsSection =
        ["## Issue Elements", "", "| Name | Issue | Text | Burden | Source | Fields |", "| --- | --- | --- | --- | --- | --- |"]
        ++ [ "| " <> issueElementName element
            <> " | " <> issueElementIssue element
            <> " | " <> issueElementText element
            <> " | " <> maybe "-" id (issueElementBurden element)
            <> " | " <> maybe "-" id (issueElementSourceRef element)
            <> " | " <> renderFields (issueElementFields element)
            <> " |"
           | element <- Map.elems (worldIssueElements world)
           ]
    timelinesSection =
        ["## Timelines", "", "| Name | Kind | Start | End | Jurisdiction | Court | Procedure |", "| --- | --- | --- | --- | --- | --- | --- |"]
        ++ [ "| " <> timelineName tl
            <> " | " <> kindText (timelineKind tl)
            <> " | " <> showT (timePointOrdinal (timelineStart tl))
            <> " | " <> showT (timePointOrdinal (timelineEnd tl))
            <> " | " <> maybe "-" id (timelineJurisdiction tl)
            <> " | " <> maybe "-" id (timelineCourt tl)
            <> " | " <> maybe "-" id (timelineProcedure tl)
            <> " |"
           | tl <- Map.elems (worldTimelines world)
           ]
    entitiesSection =
        ["## Entities", "", "| Name | Type | Appearances |", "| --- | --- | --- |"]
        ++ [ "| " <> entityName e
            <> " | " <> entityType e
            <> " | " <> T.intercalate "; " (map renderApp (entityAppearances e))
            <> " |"
           | e <- Map.elems (worldEntities world)
           ]
    relationshipsSection =
        ["## Relationships", "", "| Source | Label | Target |", "| --- | --- | --- |"]
        ++ [ "| " <> relSource r
            <> " | " <> maybe "-" id (relLabel r)
            <> " | " <> relTarget r
            <> " |"
           | r <- worldRelationships world
           ]
    relationshipTypesSection =
        ["## Relationship Types", "", "| Name | Source types | Target types | Temporal | Required | Cardinality |", "| --- | --- | --- | --- | --- | --- |"]
        ++ [ "| " <> relationshipTypeName relationshipType
            <> " | " <> renderTypeList (relationshipSourceTypes semantics)
            <> " | " <> renderTypeList (relationshipTargetTypes semantics)
            <> " | " <> maybe "-" temporalRuleText (relationshipTemporalRule semantics)
            <> " | " <> boolText (relationshipTypeRequired relationshipType)
            <> " | " <> renderCardinality (relationshipTypeCardinality relationshipType)
            <> " |"
           | relationshipType <- Map.elems (worldRelationshipTypes world)
           , let semantics = relationshipTypeSemantics relationshipType
           ]
    renderApp a =
        appearanceTimeline a <> " @ " <> showT (timePointOrdinal (rangeStart (appearanceRange a)))
            <> ".." <> showT (timePointOrdinal (rangeEnd (appearanceRange a)))

renderFields :: Map.Map Text Value -> Text
renderFields fields
    | Map.null fields = "-"
    | otherwise =
        T.intercalate
            ", "
            [ key <> "=" <> valueText value
            | (key, value) <- Map.toAscList fields
            ]

valueText :: Value -> Text
valueText value =
    case value of
        VNull -> "null"
        VString textValue -> textValue
        VInt intValue -> showT intValue
        VBool boolValue -> boolText boolValue
        VDate day -> showT day
        VDuration years months days -> showT years <> "y " <> showT months <> "m " <> showT days <> "d"
        VList values -> "[" <> T.intercalate ", " (map valueText values) <> "]"
        VRange rangeValue -> renderTimePoint (rangeStart rangeValue) <> ".." <> renderTimePoint (rangeEnd rangeValue)
        VEntityRef name -> name
        VSourceRef name -> name
        VTimelineRef name -> name
        VRulesetRef name -> name
        VDeadlineRuleRef name -> name
        VLocatorRef name -> name
        VIssueRef name -> name
        VIssueElementRef name -> name
        VClosureRef closureId -> "<closure:" <> showT closureId <> ">"

renderRange :: TimeRange -> Text
renderRange rangeValue =
    renderTimePoint (rangeStart rangeValue) <> ".." <> renderTimePoint (rangeEnd rangeValue)

renderTypeList :: [Text] -> Text
renderTypeList [] = "any"
renderTypeList values = T.intercalate ", " values

renderCardinality :: RelationshipCardinality -> Text
renderCardinality cardinality
    | null parts = "-"
    | otherwise = T.intercalate ", " parts
  where
    parts =
        concat
            [ maybe [] (\value -> ["min_inbound=" <> showT value]) (relationshipMinInbound cardinality)
            , maybe [] (\value -> ["max_inbound=" <> showT value]) (relationshipMaxInbound cardinality)
            , maybe [] (\value -> ["min_outbound=" <> showT value]) (relationshipMinOutbound cardinality)
            , maybe [] (\value -> ["max_outbound=" <> showT value]) (relationshipMaxOutbound cardinality)
            ]

temporalRuleText :: RelationshipTemporalRule -> Text
temporalRuleText SourceBeforeTarget = "source before target"
temporalRuleText SourceAfterTarget = "source after target"

deadlineCountingText :: DeadlineCounting -> Text
deadlineCountingText CountingCalendarDays = "calendar_days"
deadlineCountingText CountingCalendarDaysWithLastDayRollover = "calendar_days_with_last_day_rollover"
deadlineCountingText CountingClearDays = "clear_days"
deadlineCountingText CountingBusinessDays = "business_days"
deadlineCountingText CountingCourtDays = "court_days"

deadlineDirectionText :: DeadlineDirection -> Text
deadlineDirectionText DeadlineAfter = "after"
deadlineDirectionText DeadlineBefore = "before"

boolText :: Bool -> Text
boolText True = "true"
boolText False = "false"

kindText :: TimelineKind -> Text
kindText TimelineLinear = "linear"
kindText TimelineBranch = "branch"
kindText TimelineParallel = "parallel"
kindText TimelineLoop = "loop"

showT :: Show a => a -> Text
showT = T.pack . show
