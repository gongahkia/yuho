{-# LANGUAGE OverloadedStrings #-}

module Euclid.Core.Validation
    ( validateWorld
    ) where

import qualified Data.List as List
import qualified Data.Map.Strict as Map
import Data.Maybe (isNothing)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Model.Types

validateWorld :: World -> [Diagnostic]
validateWorld world =
    concat
        [ validateTimelines world
        , validateEntities world
        , validateRelationships world
        , validateLegalSupport world
        , validateContinuousCoverage world
        ]

validationDiagnostic :: Maybe SourceSpan -> DiagnosticLevel -> Text -> Diagnostic
validationDiagnostic sourceSpan level message =
    Diagnostic
        { diagnosticLevel = level
        , diagnosticSource = "validation"
        , diagnosticMessage = message
        , diagnosticSpan = sourceSpan
        }

validateTimelines :: World -> [Diagnostic]
validateTimelines world =
    concatMap validateTimeline (Map.elems (worldTimelines world))
  where
    validateTimeline timeline =
        timelineBoundsDiagnostics timeline
            ++ maybe [] (timelineRefDiagnostics timeline "parent") (timelineParent timeline)
            ++ maybe [] (forkMergeDiagnostics "fork_from") (timelineForkFrom timeline)
            ++ maybe [] (forkMergeDiagnostics "merge_into") (timelineMergeInto timeline)
    timelineRefDiagnostics timeline label refName =
        [ validationDiagnostic
            (timelineSourceSpan timeline)
            DiagnosticError
            ( "timeline "
                <> timelineName timeline
                <> " references missing "
                <> label
                <> " timeline "
                <> refName
            )
        | isNothing (findTimeline refName world)
        ]
    forkMergeDiagnostics label (refName, _) =
        [ validationDiagnostic
            Nothing
            DiagnosticError
            ("missing " <> label <> " timeline " <> refName)
        | isNothing (findTimeline refName world)
        ]
    timelineBoundsDiagnostics timeline =
        [ validationDiagnostic
            (timelineSourceSpan timeline)
            DiagnosticError
            ("timeline " <> timelineName timeline <> " has start after end")
        | timePointOrdinal (timelineStart timeline) > timePointOrdinal (timelineEnd timeline)
        ]
validateEntities :: World -> [Diagnostic]
validateEntities world =
    concatMap validateEntity (Map.elems (worldEntities world))
  where
    definedTypes = worldTypes world
    validateEntity entity =
        typeDiagnostics entity
            ++ requiredFieldDiagnostics entity
            ++ fieldTypeDiagnostics entity
            ++ concatMap (appearanceDiagnostics entity) (entityAppearances entity)
    typeDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticWarning
            ("entity " <> entityName entity <> " uses unknown type " <> entityType entity)
        | Set.notMember (entityType entity) builtInTypes
        , Map.notMember (entityType entity) definedTypes
        ]
    requiredFieldDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticError
            ( "entity "
                <> entityName entity
                <> " is missing required field "
                <> typeFieldName fieldDef
                <> " for type "
                <> entityType entity
            )
        | fieldDef <- resolvedTypeFields entity
        , not (typeFieldOptional fieldDef)
        , isNothing (entityDeclaredFieldValue entity (typeFieldName fieldDef))
        ]
    fieldTypeDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticError
            ( "entity "
                <> entityName entity
                <> " field "
                <> fieldName
                <> " does not match declared type "
                <> typeFieldType fieldDef
            )
        | fieldDef <- resolvedTypeFields entity
        , let fieldName = typeFieldName fieldDef
        , Just fieldValue <- [entityDeclaredFieldValue entity fieldName]
        , not (valueMatchesDeclaredType world fieldValue (typeFieldType fieldDef))
        ]
    resolvedTypeFields entity
        | Just fields <- Map.lookup (entityType entity) builtInTypeFields = fields
        | Set.member (entityType entity) builtInTypes = []
        | otherwise =
            maybe [] (Map.elems . flattenTypeFields world) (Map.lookup (entityType entity) definedTypes)
    appearanceDiagnostics entity appearance =
        timelineDiagnostics
            ++ rangeDiagnostics
            ++ timelineBoundsDiagnostics
      where
        referencedTimeline = findTimeline (appearanceTimeline appearance) world
        timelineDiagnostics =
            [ validationDiagnostic
                (entitySourceSpan entity)
                DiagnosticError
                ( "entity "
                    <> entityName entity
                    <> " references missing timeline "
                    <> appearanceTimeline appearance
                )
            | isNothing (findTimeline (appearanceTimeline appearance) world)
            ]
        rangeDiagnostics =
            [ validationDiagnostic
                (entitySourceSpan entity)
                DiagnosticError
                ("entity " <> entityName entity <> " has an appearance range with start after end")
            | let rangeValue = appearanceRange appearance
            , timePointOrdinal (rangeStart rangeValue) > timePointOrdinal (rangeEnd rangeValue)
            ]
        timelineBoundsDiagnostics =
            [ validationDiagnostic
                (entitySourceSpan entity)
                DiagnosticError
                ( "entity "
                    <> entityName entity
                    <> " has an appearance outside the bounds of timeline "
                    <> appearanceTimeline appearance
                )
            | Just timeline <- [referencedTimeline]
            , let rangeValue = appearanceRange appearance
            , timePointOrdinal (rangeStart rangeValue) < timePointOrdinal (timelineStart timeline)
                || timePointOrdinal (rangeEnd rangeValue) > timePointOrdinal (timelineEnd timeline)
            ]

validateRelationships :: World -> [Diagnostic]
validateRelationships world =
    concatMap validateRelationship (worldRelationships world)
  where
    validateRelationship relationship =
        sourceDiagnostics
            ++ targetDiagnostics
            ++ temporalScopeDiagnostics
            ++ causalOrderDiagnostics
            ++ builtInRelationshipDiagnostics
            ++ contradictionDiagnostics
      where
        labelText = relLabel relationship
        sourceEntity = findEntity (relSource relationship) world
        targetEntity = findEntity (relTarget relationship) world
        sourceDiagnostics =
            [ validationDiagnostic
                (relSourceSpan relationship)
                DiagnosticError
                ("relationship source not found: " <> relSource relationship)
            | isNothing sourceEntity
            ]
        targetDiagnostics =
            [ validationDiagnostic
                (relSourceSpan relationship)
                DiagnosticError
                ("relationship target not found: " <> relTarget relationship)
            | isNothing targetEntity
            ]
        temporalScopeDiagnostics =
            [ validationDiagnostic
                (relSourceSpan relationship)
                DiagnosticError
                ( "relationship temporal scope has start after end: "
                    <> relSource relationship
                    <> " -> "
                    <> relTarget relationship
                )
            | Just rangeValue <- [relTemporalScope relationship]
            , timePointOrdinal (rangeStart rangeValue) > timePointOrdinal (rangeEnd rangeValue)
            ]
        causalOrderDiagnostics =
            [ validationDiagnostic
                (relSourceSpan relationship)
                DiagnosticWarning
                ( "causal relationship '"
                    <> relSource relationship
                    <> " -> "
                    <> relTarget relationship
                    <> "' has source appearing after target (temporal ordering violation)"
                )
            | relCausalKind relationship /= CausalNone
            , Just causalSourceEntity <- [findEntity (relSource relationship) world]
            , Just causalTargetEntity <- [findEntity (relTarget relationship) world]
            , not (null (entityAppearances causalSourceEntity))
            , not (null (entityAppearances causalTargetEntity))
            , let sourceEnd = minimum [timePointOrdinal (rangeEnd (appearanceRange a)) | a <- entityAppearances causalSourceEntity]
                  targetStart = maximum [timePointOrdinal (rangeStart (appearanceRange a)) | a <- entityAppearances causalTargetEntity]
            , sourceEnd > targetStart
            ]
        builtInRelationshipDiagnostics =
            case labelText >>= (`Map.lookup` builtInRelationshipSemantics) of
                Nothing -> []
                Just semantics ->
                    relationshipEndpointDiagnostics "source" (relSource relationship) sourceEntity (relationshipSourceTypes semantics)
                        ++ relationshipEndpointDiagnostics "target" (relTarget relationship) targetEntity (relationshipTargetTypes semantics)
                        ++ relationshipTemporalDiagnostics semantics
        relationshipEndpointDiagnostics endpointName endpointEntityName maybeEntity expectedTypes =
            [ validationDiagnostic
                (relSourceSpan relationship)
                DiagnosticWarning
                ( "legal relationship '"
                    <> label
                    <> "' expects "
                    <> endpointName
                    <> " type "
                    <> renderExpectedTypes expectedTypes
                    <> ", got "
                    <> entityType entity
                    <> " for "
                    <> endpointEntityName
                )
            | not (null expectedTypes)
            , Just label <- [labelText]
            , Just entity <- [maybeEntity]
            , not (any (entityTypeInheritsFrom world (entityType entity)) expectedTypes)
            ]
        relationshipTemporalDiagnostics semantics =
            [ validationDiagnostic
                (relSourceSpan relationship)
                DiagnosticWarning
                ( "legal relationship '"
                    <> label
                    <> "' expects "
                    <> temporalExpectation rule
                    <> ", but "
                    <> relSource relationship
                    <> " and "
                    <> relTarget relationship
                    <> " do not match that direction"
                )
            | Just label <- [labelText]
            , Just rule <- [relationshipTemporalRule semantics]
            , relCausalKind relationship == CausalNone
            , Just source <- [sourceEntity]
            , Just target <- [targetEntity]
            , not (relationshipSatisfiesTemporalRule rule source target)
            ]
        contradictionDiagnostics =
            [ validationDiagnostic
                (relSourceSpan relationship)
                DiagnosticWarning
                ( "contradiction on timeline "
                    <> renderTimelineNames sharedTimelines
                    <> ": "
                    <> relSource relationship
                    <> " contradicts "
                    <> relTarget relationship
                )
            | labelText == Just "contradicts"
            , Just source <- [sourceEntity]
            , Just target <- [targetEntity]
            , let sharedTimelines = sharedAppearanceTimelines source target
            , not (null sharedTimelines)
            ]

sharedAppearanceTimelines :: Entity -> Entity -> [Text]
sharedAppearanceTimelines leftEntity rightEntity =
    Set.toAscList $
        entityTimelineNames leftEntity `Set.intersection` entityTimelineNames rightEntity
  where
    entityTimelineNames entity =
        Set.fromList [appearanceTimeline appearance | appearance <- entityAppearances entity]

renderTimelineNames :: [Text] -> Text
renderTimelineNames [] = "none"
renderTimelineNames [singleTimeline] = singleTimeline
renderTimelineNames timelineNames =
    T.intercalate ", " (init timelineNames) <> ", and " <> last timelineNames

renderExpectedTypes :: [Text] -> Text
renderExpectedTypes [] = "any"
renderExpectedTypes [expectedType] = expectedType
renderExpectedTypes [firstType, secondType] = firstType <> " or " <> secondType
renderExpectedTypes typeNames =
    T.intercalate ", " (init typeNames) <> ", or " <> last typeNames

temporalExpectation :: RelationshipTemporalRule -> Text
temporalExpectation SourceBeforeTarget = "source to appear before target"
temporalExpectation SourceAfterTarget = "source to appear after target"

relationshipSatisfiesTemporalRule :: RelationshipTemporalRule -> Entity -> Entity -> Bool
relationshipSatisfiesTemporalRule rule source target =
    null (entityAppearances source)
        || null (entityAppearances target)
        || case rule of
            SourceBeforeTarget ->
                any
                    (\sourceEnd -> any (sourceEnd <=) targetStarts)
                    sourceEnds
            SourceAfterTarget ->
                any
                    (\sourceStart -> any (sourceStart >=) targetEnds)
                    sourceStarts
  where
    sourceStarts = [timePointOrdinal (rangeStart (appearanceRange appearance)) | appearance <- entityAppearances source]
    sourceEnds = [timePointOrdinal (rangeEnd (appearanceRange appearance)) | appearance <- entityAppearances source]
    targetStarts = [timePointOrdinal (rangeStart (appearanceRange appearance)) | appearance <- entityAppearances target]
    targetEnds = [timePointOrdinal (rangeEnd (appearanceRange appearance)) | appearance <- entityAppearances target]

validateLegalSupport :: World -> [Diagnostic]
validateLegalSupport world =
    concatMap entityDiagnostics (Map.elems (worldEntities world))
  where
    citedTargets =
        Set.fromList
            [ relTarget relationship
            | relationship <- worldRelationships world
            , relLabel relationship == Just "cites"
            ]
    depositionDeponents =
        Set.fromList
            [ deponent
            | entity <- Map.elems (worldEntities world)
            , entityType entity == "deposition"
            , Just (VString deponent) <- [entityDeclaredFieldValue entity "deponent"]
            ]
    entityDiagnostics entity =
        uncitedClaimDiagnostics entity
            ++ witnessDepositionDiagnostics entity
    uncitedClaimDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticWarning
            ("claim " <> entityName entity <> " has no inbound cites relationship")
        | entityType entity == "claim"
        , Set.notMember (entityName entity) citedTargets
        ]
    witnessDepositionDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticWarning
            ("witness " <> entityName entity <> " has no matching deposition")
        | entityType entity == "witness"
        , Set.null (witnessNames entity `Set.intersection` depositionDeponents)
        ]

witnessNames :: Entity -> Set.Set Text
witnessNames entity =
    Set.fromList $
        entityName entity
            : [ witnessName
              | Just (VString witnessName) <- [entityDeclaredFieldValue entity "name"]
              ]

validateContinuousCoverage :: World -> [Diagnostic]
validateContinuousCoverage world =
    concatMap continuousEntityDiagnostics (Map.elems (worldEntities world))
  where
    continuousEntityDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticWarning
            ( "continuous entity "
                <> entityName entity
                <> " has coverage gap on timeline "
                <> timelineId
                <> " after "
                <> renderTimePointForDiagnostic (rangeEnd (appearanceRange previousAppearance))
                <> " before "
                <> renderTimePointForDiagnostic (rangeStart (appearanceRange nextAppearance))
            )
        | entityIsContinuous entity
        , (timelineId, appearances) <- appearancesByTimeline entity
        , (previousAppearance, nextAppearance) <- coverageGaps appearances
        ]

entityIsContinuous :: Entity -> Bool
entityIsContinuous entity =
    entityDeclaredFieldValue entity "continuous" == Just (VBool True)

appearancesByTimeline :: Entity -> [(Text, [Appearance])]
appearancesByTimeline entity =
    Map.toAscList $
        Map.fromListWith
            (++)
            [ (appearanceTimeline appearance, [appearance])
            | appearance <- entityAppearances entity
            ]

coverageGaps :: [Appearance] -> [(Appearance, Appearance)]
coverageGaps appearances =
    [ (previousAppearance, nextAppearance)
    | (previousAppearance, nextAppearance) <- zip sortedAppearances (drop 1 sortedAppearances)
    , let previousEnd = timePointOrdinal (rangeEnd (appearanceRange previousAppearance))
          nextStart = timePointOrdinal (rangeStart (appearanceRange nextAppearance))
    , nextStart > previousEnd + 1
    ]
  where
    sortedAppearances =
        List.sortOn (timePointOrdinal . rangeStart . appearanceRange) appearances

renderTimePointForDiagnostic :: TimePoint -> Text
renderTimePointForDiagnostic (TimeDate day) = T.pack (show day)
renderTimePointForDiagnostic (TimeOrdinal value) = T.pack (show value)

flattenTypeFields :: World -> TypeDef -> Map.Map Text TypeField
flattenTypeFields world typeDef =
    ownFields `Map.union` inheritedFields
  where
    inheritedFields =
        case typeParent typeDef >>= (`Map.lookup` worldTypes world) of
            Nothing -> Map.empty
            Just parentType -> flattenTypeFields world parentType
    ownFields =
        Map.fromList
            [ (typeFieldName fieldDef, fieldDef)
            | fieldDef <- typeFields typeDef
            ]

valueMatchesDeclaredType :: World -> Value -> Text -> Bool
valueMatchesDeclaredType _ VNull _ = True
valueMatchesDeclaredType _ (VInt _) "int" = True
valueMatchesDeclaredType _ (VString _) "string" = True
valueMatchesDeclaredType _ (VBool _) "bool" = True
valueMatchesDeclaredType _ (VDate _) "date" = True
valueMatchesDeclaredType _ (VList _) "list" = True
valueMatchesDeclaredType _ (VTimelineRef _) "timeline" = True
valueMatchesDeclaredType _ (VClosureRef _) "closure" = True
valueMatchesDeclaredType _ (VDuration _ _ _) "duration" = True
valueMatchesDeclaredType _ (VEntityRef _) "entity" = True
valueMatchesDeclaredType world (VEntityRef referencedEntity) expectedType =
    case findEntity referencedEntity world of
        Nothing -> False
        Just entity ->
            entityType entity == expectedType
                || entityTypeInheritsFrom world (entityType entity) expectedType
valueMatchesDeclaredType _ _ _ = False

entityTypeInheritsFrom :: World -> Text -> Text -> Bool
entityTypeInheritsFrom world actualType expectedType
    | actualType == expectedType = True
    | otherwise =
        case Map.lookup actualType (worldTypes world) >>= typeParent of
            Nothing -> False
            Just parentType -> entityTypeInheritsFrom world parentType expectedType

entityDeclaredFieldValue :: Entity -> Text -> Maybe Value
entityDeclaredFieldValue entity fieldName =
    case Map.lookup fieldName (entityFields entity) of
        Just value -> Just value
        Nothing -> annotationFieldValue entity fieldName

annotationFieldValue :: Entity -> Text -> Maybe Value
annotationFieldValue entity fieldName =
    case fieldName of
        "note" -> VString <$> annotationNote (entityAnnotation entity)
        "source" -> VString <$> annotationSource (entityAnnotation entity)
        "confidence" -> VInt . round . (* 100) <$> annotationConfidence (entityAnnotation entity)
        "tags" ->
            case annotationTags (entityAnnotation entity) of
                [] -> Nothing
                tags -> Just (VList (map VString tags))
        _ -> Nothing
