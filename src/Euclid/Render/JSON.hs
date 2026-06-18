{-# LANGUAGE OverloadedStrings #-}

module Euclid.Render.JSON
    ( renderJson
    ) where

import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Map.Strict as Map
import Euclid.Model.Types

renderJson :: World -> Text
renderJson world = T.unlines
    [ "{"
    , "  \"sources\": [" <> T.intercalate ",\n    " (map renderSource (Map.elems (worldSources world))) <> "],"
    , "  \"sourceBundles\": [" <> T.intercalate ",\n    " (map renderSourceBundle (Map.elems (worldSourceBundles world))) <> "],"
    , "  \"sourceLocators\": [" <> T.intercalate ",\n    " (map renderSourceLocator (Map.elems (worldSourceLocators world))) <> "],"
    , "  \"rulesets\": [" <> T.intercalate ",\n    " (map renderRuleset (Map.elems (worldRulesets world))) <> "],"
    , "  \"deadlineRules\": [" <> T.intercalate ",\n    " (map renderDeadlineRule (Map.elems (worldDeadlineRules world))) <> "],"
    , "  \"issues\": [" <> T.intercalate ",\n    " (map renderIssue (Map.elems (worldIssues world))) <> "],"
    , "  \"issueElements\": [" <> T.intercalate ",\n    " (map renderIssueElement (Map.elems (worldIssueElements world))) <> "],"
    , "  \"timelines\": [" <> T.intercalate ",\n    " (map renderTimeline (Map.elems (worldTimelines world))) <> "],"
    , "  \"entities\": [" <> T.intercalate ",\n    " (map renderEntity (Map.elems (worldEntities world))) <> "],"
    , "  \"relationshipTypes\": [" <> T.intercalate ",\n    " (map renderRelationshipType (Map.elems (worldRelationshipTypes world))) <> "],"
    , "  \"relationships\": [" <> T.intercalate ",\n    " (map renderRel (worldRelationships world)) <> "]"
    , "}"
    ]

renderSourceBundle :: SourceBundle -> Text
renderSourceBundle sourceBundle = T.concat
    [ "{\"name\":\"" <> esc (sourceBundleName sourceBundle) <> "\""
    , ",\"sources\":[" <> renderTextList (sourceBundleSources sourceBundle) <> "]"
    , ",\"fields\":{" <> T.intercalate "," [renderField k v | (k, v) <- Map.toList (sourceBundleFields sourceBundle)] <> "}"
    , "}"
    ]

renderSource :: SourceRecord -> Text
renderSource sourceRecord = T.concat
    [ "{\"name\":\"" <> esc (sourceRecordName sourceRecord) <> "\""
    , ",\"kind\":\"" <> esc (sourceRecordKind sourceRecord) <> "\""
    , ",\"fields\":{" <> T.intercalate "," [renderField k v | (k, v) <- Map.toList (sourceRecordFields sourceRecord)] <> "}"
    , "}"
    ]

renderSourceLocator :: SourceLocator -> Text
renderSourceLocator locator = T.concat
    [ "{\"name\":\"" <> esc (sourceLocatorName locator) <> "\""
    , ",\"sourceRef\":\"" <> esc (sourceLocatorSource locator) <> "\""
    , ",\"fields\":{" <> T.intercalate "," [renderField k v | (k, v) <- Map.toList (sourceLocatorFields locator)] <> "}"
    , "}"
    ]

renderRuleset :: Ruleset -> Text
renderRuleset ruleset = T.concat
    [ "{\"name\":\"" <> esc (rulesetName ruleset) <> "\""
    , maybe "" (\value -> ",\"jurisdiction\":\"" <> esc value <> "\"") (rulesetJurisdiction ruleset)
    , maybe "" (\value -> ",\"court\":\"" <> esc value <> "\"") (rulesetCourt ruleset)
    , maybe "" (\value -> ",\"procedure\":\"" <> esc value <> "\"") (rulesetProcedure ruleset)
    , maybe "" (\value -> ",\"effective\":" <> renderRange value) (rulesetEffective ruleset)
    , maybe "" (\value -> ",\"sourceRef\":\"" <> esc value <> "\"") (rulesetSourceRef ruleset)
    , ",\"fields\":{" <> T.intercalate "," [renderField k v | (k, v) <- Map.toList (rulesetFields ruleset)] <> "}"
    , "}"
    ]

renderDeadlineRule :: DeadlineRule -> Text
renderDeadlineRule deadlineRule = T.concat
    [ "{\"name\":\"" <> esc (deadlineRuleName deadlineRule) <> "\""
    , ",\"ruleset\":\"" <> esc (deadlineRuleRuleset deadlineRule) <> "\""
    , ",\"rule\":\"" <> esc (deadlineRuleRule deadlineRule) <> "\""
    , ",\"trigger\":\"" <> esc (deadlineRuleTrigger deadlineRule) <> "\""
    , maybe "" (\value -> ",\"actor\":\"" <> esc value <> "\"") (deadlineRuleActor deadlineRule)
    , maybe "" (\value -> ",\"action\":\"" <> esc value <> "\"") (deadlineRuleAction deadlineRule)
    , ",\"offset\":" <> renderValue (deadlineRuleOffset deadlineRule)
    , ",\"direction\":\"" <> deadlineDirectionText (deadlineRuleDirection deadlineRule) <> "\""
    , ",\"counting\":\"" <> deadlineCountingText (deadlineRuleCounting deadlineRule) <> "\""
    , maybe "" (\value -> ",\"sourceRef\":\"" <> esc value <> "\"") (deadlineRuleSourceRef deadlineRule)
    , ",\"fields\":{" <> T.intercalate "," [renderField k v | (k, v) <- Map.toList (deadlineRuleFields deadlineRule)] <> "}"
    , "}"
    ]

renderIssue :: LegalIssue -> Text
renderIssue issue = T.concat
    [ "{\"name\":\"" <> esc (legalIssueName issue) <> "\""
    , maybe "" (\value -> ",\"title\":\"" <> esc value <> "\"") (legalIssueTitle issue)
    , maybe "" (\value -> ",\"question\":\"" <> esc value <> "\"") (legalIssueQuestion issue)
    , maybe "" (\value -> ",\"burden\":\"" <> esc value <> "\"") (legalIssueBurden issue)
    , maybe "" (\value -> ",\"standard\":\"" <> esc value <> "\"") (legalIssueStandard issue)
    , maybe "" (\value -> ",\"sourceRef\":\"" <> esc value <> "\"") (legalIssueSourceRef issue)
    , ",\"fields\":{" <> T.intercalate "," [renderField k v | (k, v) <- Map.toList (legalIssueFields issue)] <> "}"
    , "}"
    ]

renderIssueElement :: IssueElement -> Text
renderIssueElement issueElement = T.concat
    [ "{\"name\":\"" <> esc (issueElementName issueElement) <> "\""
    , ",\"issue\":\"" <> esc (issueElementIssue issueElement) <> "\""
    , ",\"text\":\"" <> esc (issueElementText issueElement) <> "\""
    , maybe "" (\value -> ",\"burden\":\"" <> esc value <> "\"") (issueElementBurden issueElement)
    , maybe "" (\value -> ",\"sourceRef\":\"" <> esc value <> "\"") (issueElementSourceRef issueElement)
    , ",\"fields\":{" <> T.intercalate "," [renderField k v | (k, v) <- Map.toList (issueElementFields issueElement)] <> "}"
    , "}"
    ]

renderTimeline :: Timeline -> Text
renderTimeline tl = T.concat
    [ "{\"name\":\"" <> esc (timelineName tl) <> "\""
    , ",\"kind\":\"" <> kindText (timelineKind tl) <> "\""
    , ",\"start\":" <> showT (timePointOrdinal (timelineStart tl))
    , ",\"end\":" <> showT (timePointOrdinal (timelineEnd tl))
    , maybe "" (\p -> ",\"parent\":\"" <> esc p <> "\"") (timelineParent tl)
    , maybe "" (\value -> ",\"jurisdiction\":\"" <> esc value <> "\"") (timelineJurisdiction tl)
    , maybe "" (\value -> ",\"court\":\"" <> esc value <> "\"") (timelineCourt tl)
    , maybe "" (\value -> ",\"procedure\":\"" <> esc value <> "\"") (timelineProcedure tl)
    , maybe "" (\value -> ",\"forkFrom\":" <> renderTimelineRef value) (timelineForkFrom tl)
    , maybe "" (\value -> ",\"mergeInto\":" <> renderTimelineRef value) (timelineMergeInto tl)
    , maybe "" (\value -> ",\"loopCount\":" <> showT value) (timelineLoopCount tl)
    , "}"
    ]

renderEntity :: Entity -> Text
renderEntity e = T.concat
    [ "{\"name\":\"" <> esc (entityName e) <> "\""
    , ",\"type\":\"" <> esc (entityType e) <> "\""
    , ",\"fields\":{" <> T.intercalate "," [renderField k v | (k, v) <- Map.toList (entityFields e)] <> "}"
    , ",\"appearances\":[" <> T.intercalate "," (map renderAppearance (entityAppearances e)) <> "]"
    , maybe "" (\n -> ",\"note\":\"" <> esc n <> "\"") (annotationNote (entityAnnotation e))
    , maybe "" (\s -> ",\"source\":\"" <> esc s <> "\"") (annotationSource (entityAnnotation e))
    , maybe "" (\c -> ",\"confidence\":" <> showT c) (annotationConfidence (entityAnnotation e))
    , "}"
    ]

renderField :: Text -> Value -> Text
renderField k v = "\"" <> esc k <> "\":" <> renderValue v

renderValue :: Value -> Text
renderValue VNull = "null"
renderValue (VString t) = "\"" <> esc t <> "\""
renderValue (VInt n) = showT n
renderValue (VBool b) = if b then "true" else "false"
renderValue (VDate d) = "\"" <> showT d <> "\""
renderValue (VDuration y m d) = "\"" <> showT y <> "y" <> showT m <> "m" <> showT d <> "d\""
renderValue (VList vs) = "[" <> T.intercalate "," (map renderValue vs) <> "]"
renderValue (VRange rangeValue) = "{\"start\":\"" <> esc (renderTimePoint (rangeStart rangeValue)) <> "\",\"end\":\"" <> esc (renderTimePoint (rangeEnd rangeValue)) <> "\"}"
renderValue (VEntityRef r) = "\"" <> esc r <> "\""
renderValue (VSourceRef r) = "\"" <> esc r <> "\""
renderValue (VTimelineRef r) = "\"" <> esc r <> "\""
renderValue (VRulesetRef r) = "\"" <> esc r <> "\""
renderValue (VDeadlineRuleRef r) = "\"" <> esc r <> "\""
renderValue (VLocatorRef r) = "\"" <> esc r <> "\""
renderValue (VIssueRef r) = "\"" <> esc r <> "\""
renderValue (VIssueElementRef r) = "\"" <> esc r <> "\""
renderValue (VClosureRef _) = "\"<closure>\""

renderAppearance :: Appearance -> Text
renderAppearance a = T.concat
    [ "{\"timeline\":\"" <> esc (appearanceTimeline a) <> "\""
    , ",\"start\":" <> showT (timePointOrdinal (rangeStart (appearanceRange a)))
    , ",\"end\":" <> showT (timePointOrdinal (rangeEnd (appearanceRange a)))
    , "}"
    ]

renderRel :: Relationship -> Text
renderRel r = T.concat
    [ "{\"source\":\"" <> esc (relSource r) <> "\""
    , ",\"target\":\"" <> esc (relTarget r) <> "\""
    , maybe "" (\l -> ",\"label\":\"" <> esc l <> "\"") (relLabel r)
    , ",\"directed\":" <> if relDirected r then "true" else "false"
    , ",\"causal\":\"" <> causalText (relCausalKind r) <> "\""
    , "}"
    ]

renderRelationshipType :: RelationshipType -> Text
renderRelationshipType relationshipType = T.concat
    [ "{\"name\":\"" <> esc (relationshipTypeName relationshipType) <> "\""
    , ",\"sourceTypes\":[" <> renderTextList (relationshipSourceTypes semantics) <> "]"
    , ",\"targetTypes\":[" <> renderTextList (relationshipTargetTypes semantics) <> "]"
    , maybe "" (\rule -> ",\"temporal\":\"" <> temporalRuleText rule <> "\"") (relationshipTemporalRule semantics)
    , ",\"required\":" <> if relationshipTypeRequired relationshipType then "true" else "false"
    , ",\"cardinality\":" <> renderCardinality (relationshipTypeCardinality relationshipType)
    , "}"
    ]
  where
    semantics = relationshipTypeSemantics relationshipType

renderTimelineRef :: (Text, TimePoint) -> Text
renderTimelineRef (name, point) =
    "{\"timeline\":\"" <> esc name <> "\",\"at\":\"" <> esc (renderTimePoint point) <> "\"}"

renderRange :: TimeRange -> Text
renderRange rangeValue =
    "{\"start\":\"" <> esc (renderTimePoint (rangeStart rangeValue)) <> "\",\"end\":\"" <> esc (renderTimePoint (rangeEnd rangeValue)) <> "\"}"

renderCardinality :: RelationshipCardinality -> Text
renderCardinality cardinality =
    "{"
        <> T.intercalate
            ","
            ( concat
                [ maybe [] (\value -> ["\"minInbound\":" <> showT value]) (relationshipMinInbound cardinality)
                , maybe [] (\value -> ["\"maxInbound\":" <> showT value]) (relationshipMaxInbound cardinality)
                , maybe [] (\value -> ["\"minOutbound\":" <> showT value]) (relationshipMinOutbound cardinality)
                , maybe [] (\value -> ["\"maxOutbound\":" <> showT value]) (relationshipMaxOutbound cardinality)
                ]
            )
        <> "}"

kindText :: TimelineKind -> Text
kindText TimelineLinear = "linear"
kindText TimelineBranch = "branch"
kindText TimelineParallel = "parallel"
kindText TimelineLoop = "loop"

causalText :: CausalKind -> Text
causalText CausalNone = "none"
causalText CausalCauses = "causes"
causalText CausalEnables = "enables"

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

renderTextList :: [Text] -> Text
renderTextList values =
    T.intercalate "," ["\"" <> esc value <> "\"" | value <- values]

showT :: Show a => a -> Text
showT = T.pack . show

esc :: Text -> Text
esc = T.concatMap (\c -> case c of {'"' -> "\\\""; '\\' -> "\\\\"; '\n' -> "\\n"; _ -> T.singleton c})
