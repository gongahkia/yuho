{-# LANGUAGE OverloadedStrings #-}

module Euclid.Model.Types
    ( Appearance(..)
    , BinaryOp(..)
    , UnaryOp(..)
    , Diagnostic(..)
    , DiagnosticLevel(..)
    , Constraint(..)
    , View(..)
    , RecurrencePattern(..)
    , Recurrence(..)
    , Annotation(..)
    , emptyAnnotation
    , Entity(..)
    , StateChange(..)
    , entityFieldAt
    , FunctionSig(..)
    , CausalKind(..)
    , Relationship(..)
    , RelationshipCardinality(..)
    , RelationshipType(..)
    , RelationshipSemantics(..)
    , RelationshipTemporalRule(..)
    , DeadlineCounting(..)
    , DeadlineDirection(..)
    , DeadlineRule(..)
    , IssueElement(..)
    , LegalIssue(..)
    , Ruleset(..)
    , SourceBundle(..)
    , SourceLocator(..)
    , SourceRecord(..)
    , TimePoint(..)
    , TimeRange(..)
    , Timeline(..)
    , TimelineKind(..)
    , TypeDef(..)
    , TypeField(..)
    , Value(..)
    , World(..)
    , builtInTypeFields
    , builtInRelationshipSemantics
    , builtInTypes
    , emptyWorld
    , findEntity
    , findIssue
    , findIssueElement
    , findDeadlineRule
    , findRuleset
    , findSource
    , findSourceBundle
    , findSourceLocator
    , findTimeline
    , noSourceSpan
    , relationshipSemanticsFor
    , renderDiagnostic
    , renderTimePoint
    , SourceSpan(..)
    , timePointFromValue
    , timePointOrdinal
    , timeRangeFromValues
    , timeRangeOrdinals
    , addDurationToDay
    , daysBetween
    ) where

import qualified Data.List
import Data.List (intercalate)
import Data.Map.Strict (Map)
import qualified Data.Map.Strict as Map
import Data.Set (Set)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as T
import Data.Time (Day, toModifiedJulianDay, addGregorianMonthsClip, addDays, diffDays)

data Value
    = VNull
    | VString Text
    | VInt Integer
    | VBool Bool
    | VDate Day
    | VDuration Integer Integer Integer -- years months days
    | VList [Value]
    | VRange TimeRange
    | VEntityRef Text
    | VSourceRef Text
    | VTimelineRef Text
    | VRulesetRef Text
    | VDeadlineRuleRef Text
    | VLocatorRef Text
    | VIssueRef Text
    | VIssueElementRef Text
    | VClosureRef Integer
    deriving (Eq, Ord, Show)

data BinaryOp
    = OpAdd
    | OpSub
    | OpMul
    | OpDiv
    | OpMod
    | OpConcat
    | OpGt
    | OpLt
    | OpGte
    | OpLte
    | OpEq
    | OpNeq
    | OpAnd
    | OpOr
    deriving (Eq, Ord, Show)

data UnaryOp
    = OpNeg
    | OpNot
    deriving (Eq, Ord, Show)

data TimelineKind
    = TimelineLinear
    | TimelineBranch
    | TimelineParallel
    | TimelineLoop
    deriving (Eq, Ord, Show)

data TimePoint
    = TimeDate Day
    | TimeOrdinal Integer
    deriving (Eq, Ord, Show)

data TimeRange = TimeRange
    { rangeStart :: TimePoint
    , rangeEnd :: TimePoint
    }
    deriving (Eq, Ord, Show)

data TypeField = TypeField
    { typeFieldName :: Text
    , typeFieldType :: Text
    , typeFieldOptional :: Bool
    }
    deriving (Eq, Show)

data SourceSpan = SourceSpan
    { spanFile :: FilePath
    , spanStartLine :: Int
    , spanStartColumn :: Int
    , spanEndLine :: Int
    , spanEndColumn :: Int
    }
    deriving (Eq, Ord, Show)

data TypeDef = TypeDef
    { typeName :: Text
    , typeParent :: Maybe Text
    , typeFields :: [TypeField]
    , typeMeta :: Map Text Value
    , typeSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data Timeline = Timeline
    { timelineName :: Text
    , timelineKind :: TimelineKind
    , timelineStart :: TimePoint
    , timelineEnd :: TimePoint
    , timelineParent :: Maybe Text
    , timelineJurisdiction :: Maybe Text
    , timelineCourt :: Maybe Text
    , timelineProcedure :: Maybe Text
    , timelineForkFrom :: Maybe (Text, TimePoint)
    , timelineMergeInto :: Maybe (Text, TimePoint)
    , timelineLoopCount :: Maybe Integer
    , timelineSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data Appearance = Appearance
    { appearanceTimeline :: Text
    , appearanceRange :: TimeRange
    }
    deriving (Eq, Show)

data StateChange = StateChange
    { stateChangeTime :: TimePoint
    , stateChangeFields :: Map Text Value
    }
    deriving (Eq, Show)

data RecurrencePattern
    = RecurDaily Integer -- every N days
    | RecurWeekly Integer -- every N weeks
    | RecurMonthly Integer -- every N months
    | RecurYearly Integer -- every N years
    deriving (Eq, Ord, Show)

data Recurrence = Recurrence
    { recurrencePattern :: RecurrencePattern
    , recurrenceSkip :: [Day] -- dates to skip
    }
    deriving (Eq, Show)

data Annotation = Annotation
    { annotationNote :: Maybe Text
    , annotationSource :: Maybe Text
    , annotationConfidence :: Maybe Double
    , annotationTags :: [Text]
    }
    deriving (Eq, Show)

emptyAnnotation :: Annotation
emptyAnnotation = Annotation Nothing Nothing Nothing []

data Entity = Entity
    { entityName :: Text
    , entityType :: Text
    , entityFields :: Map Text Value
    , entityAppearances :: [Appearance]
    , entityStateChanges :: [StateChange]
    , entityAnnotation :: Annotation
    , entityRecurrence :: Maybe Recurrence
    , entitySourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

entityFieldAt :: Entity -> Text -> TimePoint -> Maybe Value
entityFieldAt entity field tp =
    let applicable = filter (\sc -> timePointOrdinal (stateChangeTime sc) <= timePointOrdinal tp) (entityStateChanges entity)
        sorted = Data.List.sortOn (negate . timePointOrdinal . stateChangeTime) applicable
        fromChanges = Data.List.find (\sc -> Map.member field (stateChangeFields sc)) sorted >>= Map.lookup field . stateChangeFields
    in case fromChanges of
        Just v -> Just v
        Nothing -> Map.lookup field (entityFields entity)

data CausalKind = CausalNone | CausalCauses | CausalEnables
    deriving (Eq, Ord, Show)

data Relationship = Relationship
    { relSource :: Text
    , relLabel :: Maybe Text
    , relTarget :: Text
    , relDirected :: Bool
    , relCausalKind :: CausalKind
    , relTemporalScope :: Maybe TimeRange
    , relSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data RelationshipTemporalRule
    = SourceBeforeTarget
    | SourceAfterTarget
    deriving (Eq, Ord, Show)

data RelationshipSemantics = RelationshipSemantics
    { relationshipSourceTypes :: [Text]
    , relationshipTargetTypes :: [Text]
    , relationshipTemporalRule :: Maybe RelationshipTemporalRule
    }
    deriving (Eq, Show)

data RelationshipCardinality = RelationshipCardinality
    { relationshipMinInbound :: Maybe Integer
    , relationshipMaxInbound :: Maybe Integer
    , relationshipMinOutbound :: Maybe Integer
    , relationshipMaxOutbound :: Maybe Integer
    }
    deriving (Eq, Show)

data RelationshipType = RelationshipType
    { relationshipTypeName :: Text
    , relationshipTypeSemantics :: RelationshipSemantics
    , relationshipTypeRequired :: Bool
    , relationshipTypeCardinality :: RelationshipCardinality
    , relationshipTypeSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data SourceRecord = SourceRecord
    { sourceRecordName :: Text
    , sourceRecordKind :: Text
    , sourceRecordFields :: Map Text Value
    , sourceRecordSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data SourceBundle = SourceBundle
    { sourceBundleName :: Text
    , sourceBundleSources :: [Text]
    , sourceBundleFields :: Map Text Value
    , sourceBundleSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data SourceLocator = SourceLocator
    { sourceLocatorName :: Text
    , sourceLocatorSource :: Text
    , sourceLocatorFields :: Map Text Value
    , sourceLocatorSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data DeadlineCounting
    = CountingCalendarDays
    | CountingCalendarDaysWithLastDayRollover
    | CountingClearDays
    | CountingBusinessDays
    | CountingCourtDays
    deriving (Eq, Ord, Show)

data DeadlineDirection
    = DeadlineAfter
    | DeadlineBefore
    deriving (Eq, Ord, Show)

data Ruleset = Ruleset
    { rulesetName :: Text
    , rulesetJurisdiction :: Maybe Text
    , rulesetCourt :: Maybe Text
    , rulesetProcedure :: Maybe Text
    , rulesetEffective :: Maybe TimeRange
    , rulesetSourceRef :: Maybe Text
    , rulesetFields :: Map Text Value
    , rulesetSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data DeadlineRule = DeadlineRule
    { deadlineRuleName :: Text
    , deadlineRuleRuleset :: Text
    , deadlineRuleRule :: Text
    , deadlineRuleTrigger :: Text
    , deadlineRuleActor :: Maybe Text
    , deadlineRuleAction :: Maybe Text
    , deadlineRuleOffset :: Value
    , deadlineRuleDirection :: DeadlineDirection
    , deadlineRuleCounting :: DeadlineCounting
    , deadlineRuleSourceRef :: Maybe Text
    , deadlineRuleFields :: Map Text Value
    , deadlineRuleSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data LegalIssue = LegalIssue
    { legalIssueName :: Text
    , legalIssueTitle :: Maybe Text
    , legalIssueQuestion :: Maybe Text
    , legalIssueBurden :: Maybe Text
    , legalIssueStandard :: Maybe Text
    , legalIssueSourceRef :: Maybe Text
    , legalIssueFields :: Map Text Value
    , legalIssueSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data IssueElement = IssueElement
    { issueElementName :: Text
    , issueElementIssue :: Text
    , issueElementText :: Text
    , issueElementBurden :: Maybe Text
    , issueElementSourceRef :: Maybe Text
    , issueElementFields :: Map Text Value
    , issueElementSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data FunctionSig = FunctionSig
    { functionName :: Text
    , functionParams :: [(Text, Text)]
    , functionReturnType :: Maybe Text
    , functionSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data DiagnosticLevel
    = DiagnosticError
    | DiagnosticWarning
    deriving (Eq, Ord, Show)

data Diagnostic = Diagnostic
    { diagnosticLevel :: DiagnosticLevel
    , diagnosticSource :: Text
    , diagnosticMessage :: Text
    , diagnosticSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data View = View
    { viewName :: Text
    , viewTimelines :: [Text]
    , viewEntityFilter :: Maybe Text -- type filter
    , viewTimeRange :: Maybe TimeRange
    , viewHighlight :: [Text] -- entity names to highlight
    , viewSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data Constraint = Constraint
    { constraintName :: Text
    , constraintSourceSpan :: Maybe SourceSpan
    }
    deriving (Eq, Show)

data World = World
    { worldTypes :: Map Text TypeDef
    , worldSources :: Map Text SourceRecord
    , worldSourceBundles :: Map Text SourceBundle
    , worldSourceLocators :: Map Text SourceLocator
    , worldRulesets :: Map Text Ruleset
    , worldDeadlineRules :: Map Text DeadlineRule
    , worldIssues :: Map Text LegalIssue
    , worldIssueElements :: Map Text IssueElement
    , worldTimelines :: Map Text Timeline
    , worldEntities :: Map Text Entity
    , worldRelationships :: [Relationship]
    , worldRelationshipTypes :: Map Text RelationshipType
    , worldFunctions :: Map Text FunctionSig
    , worldConstraints :: [Constraint]
    , worldViews :: Map Text View
    , worldScenarios :: Map Text World -- alternate what-if worlds
    , worldScenarioForks :: Map Text (Maybe Text)
    }
    deriving (Eq, Show)

emptyWorld :: World
emptyWorld =
    World
        { worldTypes = Map.empty
        , worldSources = Map.empty
        , worldSourceBundles = Map.empty
        , worldSourceLocators = Map.empty
        , worldRulesets = Map.empty
        , worldDeadlineRules = Map.empty
        , worldIssues = Map.empty
        , worldIssueElements = Map.empty
        , worldTimelines = Map.empty
        , worldEntities = Map.empty
        , worldRelationships = []
        , worldRelationshipTypes = Map.empty
        , worldFunctions = Map.empty
        , worldConstraints = []
        , worldViews = Map.empty
        , worldScenarios = Map.empty
        , worldScenarioForks = Map.empty
        }

builtInTypes :: Set Text
builtInTypes =
    coreBuiltInTypes `Set.union` Map.keysSet builtInTypeFields

coreBuiltInTypes :: Set Text
coreBuiltInTypes =
    Set.fromList
        [ "entity"
        , "event"
        , "person"
        , "place"
        , "object"
        , "group"
        , "character"
        , "artifact"
        , "location"
        , "faction"
        ]

builtInTypeFields :: Map Text [TypeField]
builtInTypeFields =
    Map.fromList
        [ ( "evidence"
          , [ requiredField "citation" "string"
            , requiredField "source" "string"
            , optionalField "source_ref" "source"
            , optionalField "locator_ref" "locator"
            , optionalField "bates" "string"
            , optionalField "admissibility" "string"
            ]
          )
        , ( "witness"
          , [ optionalField "affiliation" "string"
            , optionalField "credibility" "int"
            ]
          )
        , ("claim", [])
        , ("fact", [])
        , ( "expert_opinion"
          , [ requiredField "opinion" "string"
            , optionalField "source_ref" "source"
            , optionalField "locator_ref" "locator"
            ]
          )
        , ( "deadline"
          , [ requiredField "rule" "string"
            , requiredField "jurisdiction" "string"
            , requiredField "trigger" "string"
            , requiredField "due" "date"
            , optionalField "source_ref" "source"
            , optionalField "rule_ref" "deadline_rule"
            ]
          )
        , ( "exhibit"
          , [ requiredField "number" "string"
            , requiredField "description" "string"
            , optionalField "source_ref" "source"
            , optionalField "locator_ref" "locator"
            ]
          )
        , ( "deposition"
          , [ requiredField "deponent" "string"
            , requiredField "date" "date"
            ]
          )
        ]

builtInRelationshipSemantics :: Map Text RelationshipSemantics
builtInRelationshipSemantics =
    Map.fromList
        [ ("contradicts", unconstrainedRelationship)
        , ("corroborates", unconstrainedRelationship)
        , ("supersedes", temporalRelationship SourceAfterTarget)
        , ("caused", temporalRelationship SourceBeforeTarget)
        , ("causes", temporalRelationship SourceBeforeTarget)
        , ("enabled", temporalRelationship SourceBeforeTarget)
        , ("enables", temporalRelationship SourceBeforeTarget)
        , ("preceded", temporalRelationship SourceBeforeTarget)
        , ( "cites"
          , RelationshipSemantics
                { relationshipSourceTypes = ["evidence"]
                , relationshipTargetTypes = ["claim", "fact"]
                , relationshipTemporalRule = Nothing
                }
          )
        , ( "impeaches"
          , RelationshipSemantics
                { relationshipSourceTypes = ["evidence"]
                , relationshipTargetTypes = ["witness"]
                , relationshipTemporalRule = Nothing
                }
          )
        ]

unconstrainedRelationship :: RelationshipSemantics
unconstrainedRelationship =
    RelationshipSemantics
        { relationshipSourceTypes = []
        , relationshipTargetTypes = []
        , relationshipTemporalRule = Nothing
        }

temporalRelationship :: RelationshipTemporalRule -> RelationshipSemantics
temporalRelationship rule =
    unconstrainedRelationship{relationshipTemporalRule = Just rule}

requiredField :: Text -> Text -> TypeField
requiredField name fieldType =
    TypeField
        { typeFieldName = name
        , typeFieldType = fieldType
        , typeFieldOptional = False
        }

optionalField :: Text -> Text -> TypeField
optionalField name fieldType =
    TypeField
        { typeFieldName = name
        , typeFieldType = fieldType
        , typeFieldOptional = True
        }

noSourceSpan :: SourceSpan
noSourceSpan =
    SourceSpan
        { spanFile = "<unknown>"
        , spanStartLine = 1
        , spanStartColumn = 1
        , spanEndLine = 1
        , spanEndColumn = 1
        }

findTimeline :: Text -> World -> Maybe Timeline
findTimeline name = Map.lookup name . worldTimelines

findEntity :: Text -> World -> Maybe Entity
findEntity name = Map.lookup name . worldEntities

findSource :: Text -> World -> Maybe SourceRecord
findSource name = Map.lookup name . worldSources

findSourceBundle :: Text -> World -> Maybe SourceBundle
findSourceBundle name = Map.lookup name . worldSourceBundles

findSourceLocator :: Text -> World -> Maybe SourceLocator
findSourceLocator name = Map.lookup name . worldSourceLocators

findRuleset :: Text -> World -> Maybe Ruleset
findRuleset name = Map.lookup name . worldRulesets

findDeadlineRule :: Text -> World -> Maybe DeadlineRule
findDeadlineRule name = Map.lookup name . worldDeadlineRules

findIssue :: Text -> World -> Maybe LegalIssue
findIssue name = Map.lookup name . worldIssues

findIssueElement :: Text -> World -> Maybe IssueElement
findIssueElement name = Map.lookup name . worldIssueElements

relationshipSemanticsFor :: World -> Text -> Maybe RelationshipSemantics
relationshipSemanticsFor world label =
    case Map.lookup label (worldRelationshipTypes world) of
        Just relationshipType -> Just (relationshipTypeSemantics relationshipType)
        Nothing -> Map.lookup label builtInRelationshipSemantics

timePointOrdinal :: TimePoint -> Integer
timePointOrdinal (TimeDate day) = toModifiedJulianDay day
timePointOrdinal (TimeOrdinal value) = value

renderTimePoint :: TimePoint -> Text
renderTimePoint (TimeDate day) = T.pack (show day)
renderTimePoint (TimeOrdinal value) = T.pack (show value)

timePointFromValue :: Value -> Either Text TimePoint
timePointFromValue (VDate day) = Right (TimeDate day)
timePointFromValue (VInt value) = Right (TimeOrdinal value)
timePointFromValue value =
    Left $
        "expected a date or integer time point, got " <> T.pack (show value)

timeRangeFromValues :: Value -> Value -> Either Text TimeRange
timeRangeFromValues startValue endValue = do
    startPoint <- timePointFromValue startValue
    endPoint <- timePointFromValue endValue
    pure (TimeRange startPoint endPoint)

timeRangeOrdinals :: TimeRange -> (Integer, Integer)
timeRangeOrdinals rangeValue =
    (timePointOrdinal (rangeStart rangeValue), timePointOrdinal (rangeEnd rangeValue))

renderDiagnostic :: Diagnostic -> Text
renderDiagnostic diagnostic =
    T.intercalate
        " "
        [ levelLabel (diagnosticLevel diagnostic) <> ":"
        , diagnosticSource diagnostic <> "-"
        , maybe "" ((<> "-") . renderSourceSpan) (diagnosticSpan diagnostic)
        , diagnosticMessage diagnostic
        ]
  where
    levelLabel DiagnosticError = "error"
    levelLabel DiagnosticWarning = "warning"

renderSourceSpan :: SourceSpan -> Text
renderSourceSpan sourceSpan =
    T.pack (spanFile sourceSpan)
        <> ":"
        <> T.pack (show (spanStartLine sourceSpan))
        <> ":"
        <> T.pack (show (spanStartColumn sourceSpan))

addDurationToDay :: Day -> Integer -> Integer -> Integer -> Day
addDurationToDay day years months days =
    addDays days $ addGregorianMonthsClip (years * 12 + months) day

daysBetween :: Day -> Day -> Integer
daysBetween = diffDays

_unusedTextHelper :: [Text] -> Text
_unusedTextHelper = T.pack . intercalate ", " . map T.unpack
