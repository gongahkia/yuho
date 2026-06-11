{-# LANGUAGE OverloadedStrings #-}

module Euclid.Core.Validation
    ( validateWorld
    ) where

import qualified Data.List as List
import Data.Char (isAlphaNum, toLower)
import qualified Data.Map.Strict as Map
import Data.Maybe (isNothing)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Model.Types

validateWorld :: World -> [Diagnostic]
validateWorld world =
    concat
        [ validateSources world
        , validateLegalDeclarations world
        , validateRelationshipTypes world
        , validateTimelines world
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

validateSources :: World -> [Diagnostic]
validateSources world =
    concatMap validateSource (Map.elems (worldSources world))
        ++ validateSourceBundles world
        ++ duplicateSourceDiagnostics
  where
    validateSource sourceRecord =
        provenanceIdentityDiagnostics sourceRecord
            ++ sourceUrlDiagnostics sourceRecord
    provenanceIdentityDiagnostics sourceRecord =
        [ validationDiagnostic
            (sourceRecordSourceSpan sourceRecord)
            DiagnosticWarning
            ("source " <> sourceRecordName sourceRecord <> " should declare at least one of citation, title, or url")
        | all (`Map.notMember` sourceRecordFields sourceRecord) ["citation", "title", "url"]
        ]
    sourceUrlDiagnostics sourceRecord =
        [ validationDiagnostic
            (sourceRecordSourceSpan sourceRecord)
            DiagnosticWarning
            ("source " <> sourceRecordName sourceRecord <> " url should be an http(s) URL")
        | Just (VString urlValue) <- [Map.lookup "url" (sourceRecordFields sourceRecord)]
        , not ("https://" `T.isPrefixOf` urlValue || "http://" `T.isPrefixOf` urlValue)
        ]
    duplicateSourceDiagnostics =
        duplicateFieldDiagnostics "citation" normalizeCitation "normalized citation"
            ++ duplicateFieldDiagnostics "canonical_id" normalizeCanonicalId "canonical source id"
    duplicateFieldDiagnostics fieldName normalize label =
        [ validationDiagnostic
            (sourceRecordSourceSpan sourceRecord)
            DiagnosticWarning
            ( "source "
                <> sourceRecordName sourceRecord
                <> " duplicates "
                <> label
                <> " with "
                <> T.intercalate ", " duplicateNames
            )
        | (keyValue, sourcesForKey) <- Map.toAscList (sourcesByNormalizedField fieldName normalize)
        , not (T.null keyValue)
        , length sourcesForKey > 1
        , sourceRecord <- sourcesForKey
        , let duplicateNames = [sourceRecordName other | other <- sourcesForKey, sourceRecordName other /= sourceRecordName sourceRecord]
        ]
    sourcesByNormalizedField fieldName normalize =
        Map.fromListWith
            (++)
            [ (normalize value, [sourceRecord])
            | sourceRecord <- Map.elems (worldSources world)
            , Just (VString value) <- [Map.lookup fieldName (sourceRecordFields sourceRecord)]
            ]

validateSourceBundles :: World -> [Diagnostic]
validateSourceBundles world =
    concatMap validateSourceBundle (Map.elems (worldSourceBundles world))
  where
    validateSourceBundle sourceBundle =
        missingSourceDiagnostics sourceBundle
            ++ duplicateMemberDiagnostics sourceBundle
    missingSourceDiagnostics sourceBundle =
        [ validationDiagnostic
            (sourceBundleSourceSpan sourceBundle)
            DiagnosticError
            ("source bundle " <> sourceBundleName sourceBundle <> " references missing source " <> sourceNameValue)
        | sourceNameValue <- sourceBundleSources sourceBundle
        , Map.notMember sourceNameValue (worldSources world)
        ]
    duplicateMemberDiagnostics sourceBundle =
        [ validationDiagnostic
            (sourceBundleSourceSpan sourceBundle)
            DiagnosticWarning
            ("source bundle " <> sourceBundleName sourceBundle <> " includes source " <> sourceNameValue <> " more than once")
        | sourceNameValue <- Set.toAscList (duplicateTexts (sourceBundleSources sourceBundle))
        ]

validateLegalDeclarations :: World -> [Diagnostic]
validateLegalDeclarations world =
    concat
        [ validateSourceLocators world
        , validateRulesets world
        , validateDeadlineRules world
        , validateIssues world
        , validateIssueElements world
        ]

validateSourceLocators :: World -> [Diagnostic]
validateSourceLocators world =
    concatMap validateSourceLocator (Map.elems (worldSourceLocators world))
  where
    validateSourceLocator locator =
        missingSourceDiagnostics locator
            ++ locatorShapeDiagnostics locator
    missingSourceDiagnostics locator =
        [ validationDiagnostic
            (sourceLocatorSourceSpan locator)
            DiagnosticError
            ("locator " <> sourceLocatorName locator <> " references missing source " <> sourceLocatorSource locator)
        | Map.notMember (sourceLocatorSource locator) (worldSources world)
        ]
    locatorShapeDiagnostics locator =
        [ validationDiagnostic
            (sourceLocatorSourceSpan locator)
            DiagnosticWarning
            ("locator " <> sourceLocatorName locator <> " should include a concrete locator field such as bates, page, paragraph, line, transcript_page, transcript_line, docket_entry, or url_fragment")
        | all (`Map.notMember` sourceLocatorFields locator) concreteLocatorFields
        ]
    concreteLocatorFields =
        ["bates", "page", "paragraph", "line", "transcript_page", "transcript_line", "docket_entry", "url_fragment"]

validateRulesets :: World -> [Diagnostic]
validateRulesets world =
    concatMap validateRuleset (Map.elems (worldRulesets world))
  where
    validateRuleset ruleset =
        missingJurisdictionDiagnostics ruleset
            ++ missingProcedureDiagnostics ruleset
            ++ sourceDiagnostics ruleset
            ++ effectiveDiagnostics ruleset
    missingJurisdictionDiagnostics ruleset =
        [ validationDiagnostic
            (rulesetSourceSpan ruleset)
            DiagnosticWarning
            ("ruleset " <> rulesetName ruleset <> " should declare jurisdiction")
        | rulesetJurisdiction ruleset == Nothing
        ]
    missingProcedureDiagnostics ruleset =
        [ validationDiagnostic
            (rulesetSourceSpan ruleset)
            DiagnosticWarning
            ("ruleset " <> rulesetName ruleset <> " should declare procedure")
        | rulesetProcedure ruleset == Nothing
        ]
    sourceDiagnostics ruleset =
        case rulesetSourceRef ruleset of
            Nothing ->
                [ validationDiagnostic
                    (rulesetSourceSpan ruleset)
                    DiagnosticError
                    ("ruleset " <> rulesetName ruleset <> " must declare source_ref")
                ]
            Just sourceNameValue ->
                [ validationDiagnostic
                    (rulesetSourceSpan ruleset)
                    DiagnosticError
                    ("ruleset " <> rulesetName ruleset <> " references missing source " <> sourceNameValue)
                | Map.notMember sourceNameValue (worldSources world)
                ]
    effectiveDiagnostics ruleset =
        [ validationDiagnostic
            (rulesetSourceSpan ruleset)
            DiagnosticWarning
            ("ruleset " <> rulesetName ruleset <> " should declare an effective date range")
        | rulesetEffective ruleset == Nothing
        ]

validateDeadlineRules :: World -> [Diagnostic]
validateDeadlineRules world =
    concatMap validateDeadlineRule (Map.elems (worldDeadlineRules world))
  where
    validateDeadlineRule deadlineRule =
        rulesetDiagnostics deadlineRule
            ++ sourceDiagnostics deadlineRule
            ++ offsetDiagnostics deadlineRule
    rulesetDiagnostics deadlineRule =
        [ validationDiagnostic
            (deadlineRuleSourceSpan deadlineRule)
            DiagnosticError
            ("deadline rule " <> deadlineRuleName deadlineRule <> " references missing ruleset " <> deadlineRuleRuleset deadlineRule)
        | Map.notMember (deadlineRuleRuleset deadlineRule) (worldRulesets world)
        ]
    sourceDiagnostics deadlineRule =
        case deadlineRuleSourceRef deadlineRule of
            Nothing ->
                [ validationDiagnostic
                    (deadlineRuleSourceSpan deadlineRule)
                    DiagnosticError
                    ("deadline rule " <> deadlineRuleName deadlineRule <> " must declare source_ref")
                ]
            Just sourceNameValue ->
                [ validationDiagnostic
                    (deadlineRuleSourceSpan deadlineRule)
                    DiagnosticError
                    ("deadline rule " <> deadlineRuleName deadlineRule <> " references missing source " <> sourceNameValue)
                | Map.notMember sourceNameValue (worldSources world)
                ]
    offsetDiagnostics deadlineRule =
        [ validationDiagnostic
            (deadlineRuleSourceSpan deadlineRule)
            DiagnosticError
            ("deadline rule " <> deadlineRuleName deadlineRule <> " offset must be a positive duration")
        | not (positiveDuration (deadlineRuleOffset deadlineRule))
        ]
    positiveDuration (VDuration years months days) = years >= 0 && months >= 0 && days >= 0 && years + months + days > 0
    positiveDuration _ = False

validateIssues :: World -> [Diagnostic]
validateIssues world =
    concatMap validateIssue (Map.elems (worldIssues world))
  where
    validateIssue issue =
        sourceDiagnostics issue
            ++ shapeDiagnostics issue
    sourceDiagnostics issue =
        case legalIssueSourceRef issue of
            Nothing -> []
            Just sourceNameValue ->
                [ validationDiagnostic
                    (legalIssueSourceSpan issue)
                    DiagnosticError
                    ("issue " <> legalIssueName issue <> " references missing source " <> sourceNameValue)
                | Map.notMember sourceNameValue (worldSources world)
                ]
    shapeDiagnostics issue =
        [ validationDiagnostic
            (legalIssueSourceSpan issue)
            DiagnosticWarning
            ("issue " <> legalIssueName issue <> " should declare title or question")
        | legalIssueTitle issue == Nothing
        , legalIssueQuestion issue == Nothing
        ]

validateIssueElements :: World -> [Diagnostic]
validateIssueElements world =
    concatMap validateIssueElement (Map.elems (worldIssueElements world))
  where
    validateIssueElement issueElement =
        issueDiagnostics issueElement
            ++ sourceDiagnostics issueElement
    issueDiagnostics issueElement =
        [ validationDiagnostic
            (issueElementSourceSpan issueElement)
            DiagnosticError
            ("element " <> issueElementName issueElement <> " references missing issue " <> issueElementIssue issueElement)
        | Map.notMember (issueElementIssue issueElement) (worldIssues world)
        ]
    sourceDiagnostics issueElement =
        case issueElementSourceRef issueElement of
            Nothing -> []
            Just sourceNameValue ->
                [ validationDiagnostic
                    (issueElementSourceSpan issueElement)
                    DiagnosticError
                    ("element " <> issueElementName issueElement <> " references missing source " <> sourceNameValue)
                | Map.notMember sourceNameValue (worldSources world)
                ]

validateRelationshipTypes :: World -> [Diagnostic]
validateRelationshipTypes world =
    concatMap validateRelationshipType (Map.elems (worldRelationshipTypes world))
        ++ relationshipCardinalityDiagnostics
  where
    validateRelationshipType relationshipType =
        sourceTypeDiagnostics relationshipType
            ++ targetTypeDiagnostics relationshipType
            ++ cardinalityBoundDiagnostics relationshipType
    sourceTypeDiagnostics relationshipType =
        [ unknownRelationTypeDiagnostic relationshipType "source" relationTypeName
        | relationTypeName <- relationshipSourceTypes (relationshipTypeSemantics relationshipType)
        , not (knownType relationTypeName)
        ]
    targetTypeDiagnostics relationshipType =
        [ unknownRelationTypeDiagnostic relationshipType "target" relationTypeName
        | relationTypeName <- relationshipTargetTypes (relationshipTypeSemantics relationshipType)
        , not (knownType relationTypeName)
        ]
    unknownRelationTypeDiagnostic relationshipType endpoint relationTypeName =
        validationDiagnostic
            (relationshipTypeSourceSpan relationshipType)
            DiagnosticWarning
            ( "relationship type "
                <> relationshipTypeName relationshipType
                <> " references unknown "
                <> endpoint
                <> " type "
                <> relationTypeName
            )
    knownType relationTypeName =
        Set.member relationTypeName builtInTypes || Map.member relationTypeName (worldTypes world)
    cardinalityBoundDiagnostics relationshipType =
        minMaxDiagnostics "inbound" (relationshipMinInbound cardinality) (relationshipMaxInbound cardinality)
            ++ minMaxDiagnostics "outbound" (relationshipMinOutbound cardinality) (relationshipMaxOutbound cardinality)
            ++ negativeDiagnostics "min_inbound" (relationshipMinInbound cardinality)
            ++ negativeDiagnostics "max_inbound" (relationshipMaxInbound cardinality)
            ++ negativeDiagnostics "min_outbound" (relationshipMinOutbound cardinality)
            ++ negativeDiagnostics "max_outbound" (relationshipMaxOutbound cardinality)
      where
        cardinality = relationshipTypeCardinality relationshipType
        minMaxDiagnostics label maybeMin maybeMax =
            [ validationDiagnostic
                (relationshipTypeSourceSpan relationshipType)
                DiagnosticError
                ( "relationship type "
                    <> relationshipTypeName relationshipType
                    <> " has "
                    <> label
                    <> " minimum greater than maximum"
                )
            | Just minValue <- [maybeMin]
            , Just maxValue <- [maybeMax]
            , minValue > maxValue
            ]
        negativeDiagnostics label maybeValue =
            [ validationDiagnostic
                (relationshipTypeSourceSpan relationshipType)
                DiagnosticError
                ("relationship type " <> relationshipTypeName relationshipType <> " has negative " <> label)
            | Just value <- [maybeValue]
            , value < 0
            ]
    relationshipCardinalityDiagnostics =
        concatMap cardinalityDiagnostics (Map.elems (worldRelationshipTypes world))
    cardinalityDiagnostics relationshipType =
        inboundMinDiagnostics ++ inboundMaxDiagnostics ++ outboundMinDiagnostics ++ outboundMaxDiagnostics
      where
        cardinality = relationshipTypeCardinality relationshipType
        inboundCount entity =
            toInteger $
                length
                    [ relationship
                    | relationship <- worldRelationships world
                    , relLabel relationship == Just (relationshipTypeName relationshipType)
                    , relTarget relationship == entityName entity
                    ]
        outboundCount entity =
            toInteger $
                length
                    [ relationship
                    | relationship <- worldRelationships world
                    , relLabel relationship == Just (relationshipTypeName relationshipType)
                    , relSource relationship == entityName entity
                    ]
        targetEntities =
            [ entity
            | entity <- Map.elems (worldEntities world)
            , endpointMatches (relationshipTargetTypes (relationshipTypeSemantics relationshipType)) entity
            ]
        sourceEntities =
            [ entity
            | entity <- Map.elems (worldEntities world)
            , endpointMatches (relationshipSourceTypes (relationshipTypeSemantics relationshipType)) entity
            ]
        inboundMinDiagnostics =
            cardinalitySideDiagnostics relationshipType "inbound" "target" inboundCount (<) (relationshipMinInbound cardinality) targetEntities "fewer than"
        inboundMaxDiagnostics =
            cardinalitySideDiagnostics relationshipType "inbound" "target" inboundCount (>) (relationshipMaxInbound cardinality) targetEntities "more than"
        outboundMinDiagnostics =
            cardinalitySideDiagnostics relationshipType "outbound" "source" outboundCount (<) (relationshipMinOutbound cardinality) sourceEntities "fewer than"
        outboundMaxDiagnostics =
            cardinalitySideDiagnostics relationshipType "outbound" "source" outboundCount (>) (relationshipMaxOutbound cardinality) sourceEntities "more than"
    cardinalitySideDiagnostics relationshipType side endpoint countFn cmp maybeBound entities phrase =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticError
            ( "entity "
                <> entityName entity
                <> " has "
                <> phrase
                <> " "
                <> T.pack (show bound)
                <> " "
                <> side
                <> " "
                <> relationshipTypeName relationshipType
                <> " relationship(s) as "
                <> endpoint
            )
        | Just bound <- [maybeBound]
        , entity <- entities
        , countFn entity `cmp` bound
        ]
    endpointMatches expectedTypes entity =
        null expectedTypes || any (entityTypeInheritsFrom world (entityType entity)) expectedTypes

validateTimelines :: World -> [Diagnostic]
validateTimelines world =
    concatMap validateTimeline (Map.elems (worldTimelines world))
  where
    validateTimeline timeline =
        timelineBoundsDiagnostics timeline
            ++ jurisdictionDiagnostics timeline
            ++ maybe [] (timelineRefDiagnostics timeline "parent") (timelineParent timeline)
            ++ maybe [] (forkMergeDiagnostics timeline "fork_from") (timelineForkFrom timeline)
            ++ maybe [] (forkMergeDiagnostics timeline "merge_into") (timelineMergeInto timeline)
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
    forkMergeDiagnostics timeline label (refName, _) =
        [ validationDiagnostic
            (timelineSourceSpan timeline)
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
    jurisdictionDiagnostics timeline =
        [ validationDiagnostic
            (timelineSourceSpan timeline)
            DiagnosticWarning
            ("timeline " <> timelineName timeline <> " declares jurisdiction but no procedure/ruleset")
        | timelineJurisdiction timeline /= Nothing
        , timelineProcedure timeline == Nothing
        ]
            ++ [ validationDiagnostic
                (timelineSourceSpan timeline)
                DiagnosticWarning
                ("timeline " <> timelineName timeline <> " declares procedure/ruleset but no jurisdiction")
               | timelineProcedure timeline /= Nothing
               , timelineJurisdiction timeline == Nothing
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
            ++ sourceReferenceDiagnostics entity
            ++ locatorReferenceDiagnostics entity
            ++ deadlineRuleReferenceDiagnostics entity
            ++ deadlineJurisdictionDiagnostics entity
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
    sourceReferenceDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticError
            ("entity " <> entityName entity <> " references missing source " <> sourceNameValue)
        | Just sourceValue <- [Map.lookup "source_ref" (entityFields entity)]
        , Just sourceNameValue <- [sourceReferenceName sourceValue]
        , Map.notMember sourceNameValue (worldSources world)
        ]
    locatorReferenceDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticError
            ("entity " <> entityName entity <> " references missing locator " <> locatorNameValue)
        | Just locatorValue <- [Map.lookup "locator_ref" (entityFields entity)]
        , Just locatorNameValue <- [locatorReferenceName locatorValue]
        , Map.notMember locatorNameValue (worldSourceLocators world)
        ]
    deadlineRuleReferenceDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticError
            ("entity " <> entityName entity <> " references missing deadline rule " <> deadlineRuleNameValue)
        | Just ruleValue <- [Map.lookup "rule_ref" (entityFields entity)]
        , Just deadlineRuleNameValue <- [deadlineRuleReferenceName ruleValue]
        , Map.notMember deadlineRuleNameValue (worldDeadlineRules world)
        ]
    deadlineJurisdictionDiagnostics entity =
        [ validationDiagnostic
            (entitySourceSpan entity)
            DiagnosticWarning
            ( "deadline "
                <> entityName entity
                <> " jurisdiction "
                <> deadlineJurisdiction
                <> " does not match any appeared-on timeline jurisdiction"
            )
        | entityType entity == "deadline"
        , Just (VString deadlineJurisdiction) <- [entityDeclaredFieldValue entity "jurisdiction"]
        , let timelineJurisdictions =
                [ jurisdiction
                | appearance <- entityAppearances entity
                , Just timeline <- [findTimeline (appearanceTimeline appearance) world]
                , Just jurisdiction <- [timelineJurisdiction timeline]
                ]
        , not (null timelineJurisdictions)
        , deadlineJurisdiction `notElem` timelineJurisdictions
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
            case labelText >>= relationshipSemanticsFor world of
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

normalizeCitation :: Text -> Text
normalizeCitation =
    normalizeLooseText

normalizeCanonicalId :: Text -> Text
normalizeCanonicalId =
    normalizeLooseText

normalizeLooseText :: Text -> Text
normalizeLooseText =
    T.unwords
        . T.words
        . T.map normalizeChar
        . T.strip
  where
    normalizeChar charValue
        | isAlphaNum charValue = toLower charValue
        | otherwise = ' '

duplicateTexts :: [Text] -> Set.Set Text
duplicateTexts values =
    Map.keysSet $
        Map.filter
            (> (1 :: Int))
            (Map.fromListWith (+) [(value, 1 :: Int) | value <- values])

sourceReferenceName :: Value -> Maybe Text
sourceReferenceName (VSourceRef sourceNameValue) = Just sourceNameValue
sourceReferenceName (VString sourceNameValue) = Just sourceNameValue
sourceReferenceName _ = Nothing

locatorReferenceName :: Value -> Maybe Text
locatorReferenceName (VLocatorRef locatorNameValue) = Just locatorNameValue
locatorReferenceName (VString locatorNameValue) = Just locatorNameValue
locatorReferenceName _ = Nothing

deadlineRuleReferenceName :: Value -> Maybe Text
deadlineRuleReferenceName (VDeadlineRuleRef deadlineRuleNameValue) = Just deadlineRuleNameValue
deadlineRuleReferenceName (VString deadlineRuleNameValue) = Just deadlineRuleNameValue
deadlineRuleReferenceName _ = Nothing

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
valueMatchesDeclaredType _ (VRange _) "range" = True
valueMatchesDeclaredType _ (VTimelineRef _) "timeline" = True
valueMatchesDeclaredType world (VSourceRef sourceNameValue) "source" = Map.member sourceNameValue (worldSources world)
valueMatchesDeclaredType world (VString sourceNameValue) "source" = Map.member sourceNameValue (worldSources world)
valueMatchesDeclaredType world (VRulesetRef rulesetNameValue) "ruleset" = Map.member rulesetNameValue (worldRulesets world)
valueMatchesDeclaredType world (VString rulesetNameValue) "ruleset" = Map.member rulesetNameValue (worldRulesets world)
valueMatchesDeclaredType world (VDeadlineRuleRef deadlineRuleNameValue) "deadline_rule" = Map.member deadlineRuleNameValue (worldDeadlineRules world)
valueMatchesDeclaredType world (VString deadlineRuleNameValue) "deadline_rule" = Map.member deadlineRuleNameValue (worldDeadlineRules world)
valueMatchesDeclaredType world (VLocatorRef locatorNameValue) "locator" = Map.member locatorNameValue (worldSourceLocators world)
valueMatchesDeclaredType world (VString locatorNameValue) "locator" = Map.member locatorNameValue (worldSourceLocators world)
valueMatchesDeclaredType world (VIssueRef issueNameValue) "issue" = Map.member issueNameValue (worldIssues world)
valueMatchesDeclaredType world (VString issueNameValue) "issue" = Map.member issueNameValue (worldIssues world)
valueMatchesDeclaredType world (VIssueElementRef elementNameValue) "issue_element" = Map.member elementNameValue (worldIssueElements world)
valueMatchesDeclaredType world (VString elementNameValue) "issue_element" = Map.member elementNameValue (worldIssueElements world)
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
