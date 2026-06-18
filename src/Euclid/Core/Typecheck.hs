{-# LANGUAGE OverloadedStrings #-}

module Euclid.Core.Typecheck
    ( typeCheckProgram
    ) where

import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Lang.AST
import Euclid.Model.Types

data StaticType
    = TypeUnknown
    | TypeNull
    | TypeInt
    | TypeString
    | TypeBool
    | TypeDate
    | TypeDuration
    | TypeList
    | TypeRange
    | TypeEntity
    | TypeEntityNamed Text
    | TypeTimeline
    | TypeSource
    | TypeRuleset
    | TypeDeadlineRule
    | TypeLocator
    | TypeIssue
    | TypeIssueElement
    | TypeClosure
    deriving (Eq, Ord, Show)

data TypeEnv = TypeEnv
    { envTypes :: Set Text
    , envValues :: Map Text StaticType
    , envEntities :: Map Text Text
    , envTimelines :: Set Text
    , envSources :: Set Text
    , envRulesets :: Set Text
    , envDeadlineRules :: Set Text
    , envLocators :: Set Text
    , envIssues :: Set Text
    , envIssueElements :: Set Text
    , envFunctions :: Map Text ([(Text, Text)], Maybe Text)
    }
    deriving (Eq, Show)

emptyTypeEnv :: TypeEnv
emptyTypeEnv =
    TypeEnv
        { envTypes = builtInTypes
        , envValues = Map.empty
        , envEntities = Map.empty
        , envTimelines = Set.empty
        , envSources = Set.empty
        , envRulesets = Set.empty
        , envDeadlineRules = Set.empty
        , envLocators = Set.empty
        , envIssues = Set.empty
        , envIssueElements = Set.empty
        , envFunctions = Map.empty
        }

typeCheckProgram :: Program -> [Diagnostic]
typeCheckProgram (ProgramData _ statements) =
    snd (foldl checkStmt (emptyTypeEnv, []) statements)

checkStmt :: (TypeEnv, [Diagnostic]) -> Stmt -> (TypeEnv, [Diagnostic])
checkStmt (env, diagnostics) (StmtData sourceSpan statement) =
    let (nextEnv, newDiagnostics) = checkStmtNode sourceSpan env statement
    in (nextEnv, diagnostics ++ newDiagnostics)

checkStmtNode :: SourceSpan -> TypeEnv -> StmtNode -> (TypeEnv, [Diagnostic])
checkStmtNode sourceSpan env statement =
    case statement of
        StmtTypeNode decl ->
            ( env{envTypes = Set.insert (typeDeclName decl) (envTypes env)}
            , concatMap (checkTypeField sourceSpan env) (typeDeclFields decl)
            )
        StmtSourceNode decl ->
            let diagnostics = concatMap (checkExprExpectAny sourceSpan env . snd) (Map.toAscList (sourceDeclFields decl))
            in (env{envSources = Set.insert (sourceDeclName decl) (envSources env)}, diagnostics)
        StmtSourceBundleNode decl ->
            let diagnostics = concatMap (checkExprExpectAny sourceSpan env . snd) (Map.toAscList (sourceBundleDeclFields decl))
            in (env, diagnostics)
        StmtSourceLocatorNode decl ->
            let fields = sourceLocatorDeclFields decl
                diagnostics =
                    maybe [] (expectType sourceSpan env TypeSource) (Map.lookup "source_ref" fields)
                        ++ concatMap (checkExprExpectAny sourceSpan env . snd) (Map.toAscList (Map.delete "source_ref" fields))
            in (env{envLocators = Set.insert (sourceLocatorDeclName decl) (envLocators env)}, diagnostics)
        StmtRulesetNode decl ->
            let fields = rulesetDeclFields decl
                diagnostics =
                    maybe [] (expectTextLike sourceSpan env) (Map.lookup "jurisdiction" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "court" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "procedure" fields)
                        ++ maybe [] (expectType sourceSpan env TypeRange) (Map.lookup "effective" fields)
                        ++ maybe [] (expectType sourceSpan env TypeSource) (Map.lookup "source_ref" fields)
                        ++ concatMap (checkExprExpectAny sourceSpan env . snd) (Map.toAscList (dropKnownFields ["jurisdiction", "court", "procedure", "effective", "source_ref"] fields))
            in (env{envRulesets = Set.insert (rulesetDeclName decl) (envRulesets env)}, diagnostics)
        StmtDeadlineRuleNode decl ->
            let fields = deadlineRuleDeclFields decl
                diagnostics =
                    maybe [] (expectType sourceSpan env TypeRuleset) (Map.lookup "ruleset" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "rule" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "trigger" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "actor" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "action" fields)
                        ++ maybe [] (expectType sourceSpan env TypeDuration) (Map.lookup "offset" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "direction" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "counting" fields)
                        ++ maybe [] (expectType sourceSpan env TypeSource) (Map.lookup "source_ref" fields)
                        ++ concatMap (checkExprExpectAny sourceSpan env . snd) (Map.toAscList (dropKnownFields ["ruleset", "rule", "trigger", "actor", "action", "offset", "direction", "counting", "source_ref"] fields))
            in (env{envDeadlineRules = Set.insert (deadlineRuleDeclName decl) (envDeadlineRules env)}, diagnostics)
        StmtIssueNode decl ->
            let fields = legalIssueDeclFields decl
                diagnostics =
                    maybe [] (expectTextLike sourceSpan env) (Map.lookup "title" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "question" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "burden" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "standard" fields)
                        ++ maybe [] (expectType sourceSpan env TypeSource) (Map.lookup "source_ref" fields)
                        ++ concatMap (checkExprExpectAny sourceSpan env . snd) (Map.toAscList (dropKnownFields ["title", "question", "burden", "standard", "source_ref"] fields))
            in (env{envIssues = Set.insert (legalIssueDeclName decl) (envIssues env)}, diagnostics)
        StmtIssueElementNode decl ->
            let fields = issueElementDeclFields decl
                diagnostics =
                    maybe [] (expectType sourceSpan env TypeIssue) (Map.lookup "issue" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "text" fields)
                        ++ maybe [] (expectTextLike sourceSpan env) (Map.lookup "burden" fields)
                        ++ maybe [] (expectType sourceSpan env TypeSource) (Map.lookup "source_ref" fields)
                        ++ concatMap (checkExprExpectAny sourceSpan env . snd) (Map.toAscList (dropKnownFields ["issue", "text", "burden", "source_ref"] fields))
            in (env{envIssueElements = Set.insert (issueElementDeclName decl) (envIssueElements env)}, diagnostics)
        StmtTimelineNode decl ->
            let startDiagnostics = expectTimePoint sourceSpan env (timelineDeclStart decl)
                endDiagnostics = expectTimePoint sourceSpan env (timelineDeclEnd decl)
                jurisdictionDiagnostics = maybe [] (expectTextLike sourceSpan env) (timelineDeclJurisdiction decl)
                courtDiagnostics = maybe [] (expectTextLike sourceSpan env) (timelineDeclCourt decl)
                procedureDiagnostics = maybe [] (expectTextLike sourceSpan env) (timelineDeclProcedure decl)
                loopDiagnostics = maybe [] (expectType sourceSpan env TypeInt) (timelineDeclLoopCount decl)
            in
                ( env{envTimelines = Set.insert (timelineDeclName decl) (envTimelines env)}
                , startDiagnostics ++ endDiagnostics ++ jurisdictionDiagnostics ++ courtDiagnostics ++ procedureDiagnostics ++ loopDiagnostics
                )
        StmtEntityNode decl ->
            let entityTypeName = maybe "entity" id (entityDeclType decl)
                fieldDiagnostics = concatMap (checkExprExpectAny sourceSpan env . snd) (Map.toAscList (entityDeclFields decl))
                appearanceDiagnostics =
                    concat
                        [ expectTimePoint sourceSpan env (appearanceDeclStart appearance)
                            ++ expectTimePoint sourceSpan env (appearanceDeclEnd appearance)
                        | appearance <- entityDeclAppearances decl
                        ]
                stateChangeDiagnostics =
                    concat
                        [ expectTimePoint sourceSpan env (stateChangeDeclTime stateChange)
                            ++ concatMap (checkExprExpectAny sourceSpan env . snd) (Map.toAscList (stateChangeDeclFields stateChange))
                        | stateChange <- entityDeclStateChanges decl
                        ]
                annotationDiagnostics =
                    maybe [] (expectType sourceSpan env TypeString) (annotationDeclNote (entityDeclAnnotation decl))
                        ++ maybe [] (expectType sourceSpan env TypeString) (annotationDeclSource (entityDeclAnnotation decl))
                        ++ maybe [] (expectType sourceSpan env TypeInt) (annotationDeclConfidence (entityDeclAnnotation decl))
                        ++ concatMap (expectType sourceSpan env TypeString) (annotationDeclTags (entityDeclAnnotation decl))
                recurrenceDiagnostics = maybe [] (expectType sourceSpan env TypeDuration) (entityDeclRecurrence decl)
                skipDiagnostics = concatMap (expectType sourceSpan env TypeDate) (entityDeclSkip decl)
            in
                ( env{envEntities = Map.insert (entityDeclName decl) entityTypeName (envEntities env)}
                , fieldDiagnostics
                    ++ appearanceDiagnostics
                    ++ stateChangeDiagnostics
                    ++ annotationDiagnostics
                    ++ recurrenceDiagnostics
                    ++ skipDiagnostics
                )
        StmtRelationshipTypeNode decl ->
            ( env
            , concatMap (checkKnownType sourceSpan env "relationship source") (relationshipTypeDeclSources decl)
                ++ concatMap (checkKnownType sourceSpan env "relationship target") (relationshipTypeDeclTargets decl)
                ++ maybe [] (expectType sourceSpan env TypeInt) (relationshipTypeDeclMinInbound decl)
                ++ maybe [] (expectType sourceSpan env TypeInt) (relationshipTypeDeclMaxInbound decl)
                ++ maybe [] (expectType sourceSpan env TypeInt) (relationshipTypeDeclMinOutbound decl)
                ++ maybe [] (expectType sourceSpan env TypeInt) (relationshipTypeDeclMaxOutbound decl)
            )
        StmtRelationshipNode decl ->
            ( env
            , maybe [] (\(startExpr, endExpr) -> expectTimePoint sourceSpan env startExpr ++ expectTimePoint sourceSpan env endExpr) (relationshipDeclTemporalScope decl)
            )
        StmtConstraintNode decl ->
            let (_, diagnostics) = foldl checkConstraintStmt (env, []) (constraintDeclBody decl)
            in (env, diagnostics)
        StmtViewNode decl ->
            ( env
            , maybe [] (\(startExpr, endExpr) -> expectTimePoint sourceSpan env startExpr ++ expectTimePoint sourceSpan env endExpr) (viewDeclTimeRange decl)
            )
        StmtScenarioNode decl ->
            let (_, diagnostics) = foldl checkStmt (env, []) (scenarioDeclBody decl)
            in (env, diagnostics)
        StmtImportNode _ ->
            (env, [])
        StmtLetNode decl ->
            let (inferredType, diagnostics) = inferExpr sourceSpan env (letValue decl)
                annotationDiagnostics =
                    maybe [] (\expectedName -> annotationMismatch sourceSpan expectedName inferredType) (letTypeAnnotation decl)
                storedType = maybe inferredType typeFromName (letTypeAnnotation decl)
            in (env{envValues = Map.insert (letName decl) storedType (envValues env)}, diagnostics ++ annotationDiagnostics)
        StmtForNode decl ->
            let (iterableType, iterableDiagnostics) = inferForIterable sourceSpan env (forIterable decl)
                bodyEnv = env{envValues = Map.insert (forVar decl) iterableType (envValues env)}
                (_, bodyDiagnostics) = foldl checkStmt (bodyEnv, []) (forBody decl)
            in (env, iterableDiagnostics ++ bodyDiagnostics)
        StmtRepeatNode decl ->
            let (_, bodyDiagnostics) = foldl checkStmt (env, []) (repeatBody decl)
            in (env, expectType sourceSpan env TypeInt (repeatCount decl) ++ bodyDiagnostics)
        StmtWhileNode decl ->
            let (_, bodyDiagnostics) = foldl checkStmt (env, []) (whileBody decl)
            in (env, expectType sourceSpan env TypeBool (whileCondition decl) ++ bodyDiagnostics)
        StmtFunctionNode decl ->
            ( env{envFunctions = Map.insert (fnName decl) (fnParams decl, fnReturnType decl) (envFunctions env)}
            , []
            )
        StmtIfNode decl ->
            let thenDiagnostics = snd (foldl checkStmt (env, []) (ifThenBlock decl))
                elseIfDiagnostics =
                    concat
                        [ expectType sourceSpan env TypeBool conditionExpr
                            ++ snd (foldl checkStmt (env, []) branchBody)
                        | (conditionExpr, branchBody) <- ifElseIfBlocks decl
                        ]
                elseDiagnostics = maybe [] (snd . foldl checkStmt (env, [])) (ifElseBlock decl)
            in (env, expectType sourceSpan env TypeBool (ifCondition decl) ++ thenDiagnostics ++ elseIfDiagnostics ++ elseDiagnostics)
        StmtMatchNode decl ->
            let (_, subjectDiagnostics) = inferExpr sourceSpan env (matchSubject decl)
                armDiagnostics = concatMap (snd . foldl checkStmt (env, []) . matchArmBody) (matchArms decl)
            in (env, subjectDiagnostics ++ armDiagnostics)
        StmtReturnNode maybeExpr ->
            (env, maybe [] (checkExprExpectAny sourceSpan env) maybeExpr)
        StmtAssignNode name expr ->
            let (actualType, diagnostics) = inferExpr sourceSpan env expr
                mismatchDiagnostics =
                    case Map.lookup name (envValues env) of
                        Nothing -> []
                        Just expectedType -> mismatchDiagnosticsFor sourceSpan expectedType actualType
            in (env, diagnostics ++ mismatchDiagnostics)
        StmtExprNode expr ->
            (env, checkExprExpectAny sourceSpan env expr)

checkConstraintStmt :: (TypeEnv, [Diagnostic]) -> Stmt -> (TypeEnv, [Diagnostic])
checkConstraintStmt (env, diagnostics) stmt@(StmtData sourceSpan statement) =
    case statement of
        StmtExprNode expr ->
            (env, diagnostics ++ expectType sourceSpan env TypeBool expr)
        _ ->
            let (nextEnv, newDiagnostics) = checkStmt (env, []) stmt
            in (nextEnv, diagnostics ++ newDiagnostics)

checkTypeField :: SourceSpan -> TypeEnv -> TypeField -> [Diagnostic]
checkTypeField sourceSpan env field =
    checkKnownType sourceSpan env ("field " <> typeFieldName field) (typeFieldType field)

checkKnownType :: SourceSpan -> TypeEnv -> Text -> Text -> [Diagnostic]
checkKnownType sourceSpan env context typeNameValue =
    [ typeDiagnostic sourceSpan ("unknown " <> context <> " type: " <> typeNameValue)
    | Set.notMember typeNameValue (envTypes env)
    , typeNameValue `notElem` scalarTypeNames
    ]

scalarTypeNames :: [Text]
scalarTypeNames =
    ["int", "string", "bool", "date", "duration", "list", "range", "timeline", "source", "ruleset", "deadline_rule", "locator", "issue", "issue_element", "closure"]

inferForIterable :: SourceSpan -> TypeEnv -> ForIterable -> (StaticType, [Diagnostic])
inferForIterable sourceSpan env iterable =
    case iterable of
        ForRange startExpr endExpr ->
            (TypeInt, expectType sourceSpan env TypeInt startExpr ++ expectType sourceSpan env TypeInt endExpr)
        ForList exprs ->
            let diagnostics = concatMap (checkExprExpectAny sourceSpan env) exprs
            in (TypeUnknown, diagnostics)
        ForExpr expr ->
            let (exprType, diagnostics) = inferExpr sourceSpan env expr
            in (iteratedType exprType, diagnostics)

iteratedType :: StaticType -> StaticType
iteratedType TypeRange = TypeInt
iteratedType TypeList = TypeUnknown
iteratedType otherType = otherType

checkExprExpectAny :: SourceSpan -> TypeEnv -> Expr -> [Diagnostic]
checkExprExpectAny sourceSpan env expr =
    snd (inferExpr sourceSpan env expr)

expectTimePoint :: SourceSpan -> TypeEnv -> Expr -> [Diagnostic]
expectTimePoint sourceSpan env expr =
    let (actualType, diagnostics) = inferExpr sourceSpan env expr
    in diagnostics ++
        [ typeDiagnostic sourceSpan ("expected date or int time point, got " <> renderStaticType actualType)
        | actualType /= TypeUnknown
        , actualType `notElem` [TypeDate, TypeInt]
        ]

expectTextLike :: SourceSpan -> TypeEnv -> Expr -> [Diagnostic]
expectTextLike _ _ (ExprIdent _) = []
expectTextLike sourceSpan env expr =
    expectType sourceSpan env TypeString expr

dropKnownFields :: [Text] -> Map Text Expr -> Map Text Expr
dropKnownFields fieldNames fields =
    foldr Map.delete fields fieldNames

expectType :: SourceSpan -> TypeEnv -> StaticType -> Expr -> [Diagnostic]
expectType sourceSpan env expectedType expr =
    let (actualType, diagnostics) = inferExpr sourceSpan env expr
    in diagnostics ++ mismatchDiagnosticsFor sourceSpan expectedType actualType

mismatchDiagnosticsFor :: SourceSpan -> StaticType -> StaticType -> [Diagnostic]
mismatchDiagnosticsFor sourceSpan expectedType actualType =
    [ typeDiagnostic sourceSpan ("type mismatch: expected " <> renderStaticType expectedType <> " but got " <> renderStaticType actualType)
    | not (typesCompatible expectedType actualType)
    ]

annotationMismatch :: SourceSpan -> Text -> StaticType -> [Diagnostic]
annotationMismatch sourceSpan expectedName actualType =
    mismatchDiagnosticsFor sourceSpan (typeFromName expectedName) actualType

inferExpr :: SourceSpan -> TypeEnv -> Expr -> (StaticType, [Diagnostic])
inferExpr sourceSpan env expr =
    case expr of
        ExprValue value ->
            (typeFromValue value, [])
        ExprIdent name ->
            case Map.lookup name (envValues env) of
                Just valueType -> (valueType, [])
                Nothing ->
                    case Map.lookup name (envEntities env) of
                        Just entityTypeName -> (TypeEntityNamed entityTypeName, [])
                        Nothing
                            | Set.member name (envTimelines env) -> (TypeTimeline, [])
                            | Set.member name (envSources env) -> (TypeSource, [])
                            | Set.member name (envRulesets env) -> (TypeRuleset, [])
                            | Set.member name (envDeadlineRules env) -> (TypeDeadlineRule, [])
                            | Set.member name (envLocators env) -> (TypeLocator, [])
                            | Set.member name (envIssues env) -> (TypeIssue, [])
                            | Set.member name (envIssueElements env) -> (TypeIssueElement, [])
                            | otherwise -> (TypeUnknown, [])
        ExprList exprs ->
            (TypeList, concatMap (checkExprExpectAny sourceSpan env) exprs)
        ExprRange startExpr endExpr ->
            (TypeRange, expectTimePoint sourceSpan env startExpr ++ expectTimePoint sourceSpan env endExpr)
        ExprQuantifier _ variableName iterableExpr bodyExpr ->
            let (iterableTypeValue, iterableDiagnostics) = inferExpr sourceSpan env iterableExpr
                bodyEnv = env{envValues = Map.insert variableName (iteratedType iterableTypeValue) (envValues env)}
                bodyDiagnostics = expectType sourceSpan bodyEnv TypeBool bodyExpr
            in (TypeBool, iterableDiagnostics ++ bodyDiagnostics)
        ExprIndex objectExpr indexExpr ->
            let (_, objectDiagnostics) = inferExpr sourceSpan env objectExpr
                indexDiagnostics = expectType sourceSpan env TypeInt indexExpr
            in (TypeUnknown, objectDiagnostics ++ indexDiagnostics)
        ExprField objectExpr _ ->
            let (_, diagnostics) = inferExpr sourceSpan env objectExpr
            in (TypeUnknown, diagnostics)
        ExprCall (ExprIdent name) argExprs ->
            inferNamedCall sourceSpan env name argExprs
        ExprCall calleeExpr argExprs ->
            let (_, calleeDiagnostics) = inferExpr sourceSpan env calleeExpr
                argDiagnostics = concatMap (checkExprExpectAny sourceSpan env) argExprs
            in (TypeUnknown, calleeDiagnostics ++ argDiagnostics)
        ExprClosure _ _ ->
            (TypeClosure, [])
        ExprBinary op lhs rhs ->
            inferBinary sourceSpan env op lhs rhs
        ExprUnary op operand ->
            inferUnary sourceSpan env op operand
        ExprTemporalAccess objectExpr _ timeExpr ->
            let (_, objectDiagnostics) = inferExpr sourceSpan env objectExpr
                timeDiagnostics = expectTimePoint sourceSpan env timeExpr
            in (TypeUnknown, objectDiagnostics ++ timeDiagnostics)

inferNamedCall :: SourceSpan -> TypeEnv -> Text -> [Expr] -> (StaticType, [Diagnostic])
inferNamedCall sourceSpan env name argExprs =
    let argResults = map (inferExpr sourceSpan env) argExprs
        argTypes = map fst argResults
        argDiagnostics = concatMap snd argResults
    in case builtinType name argTypes of
        Just (returnType, diagnostics) -> (returnType, argDiagnostics ++ map (typeDiagnostic sourceSpan) diagnostics)
        Nothing ->
            case Map.lookup name (envFunctions env) of
                Just (params, returnTypeName) ->
                    let expectedTypes = map (typeFromName . snd) params
                        arityDiagnostics =
                            [ typeDiagnostic sourceSpan ("function " <> name <> " expected " <> showText (length expectedTypes) <> " arguments but got " <> showText (length argTypes))
                            | length expectedTypes /= length argTypes
                            ]
                        argumentDiagnostics =
                            concat
                                [ mismatchDiagnosticsFor sourceSpan expectedType actualType
                                | (expectedType, actualType) <- zip expectedTypes argTypes
                                ]
                    in (maybe TypeUnknown typeFromName returnTypeName, argDiagnostics ++ arityDiagnostics ++ argumentDiagnostics)
                Nothing -> (TypeUnknown, argDiagnostics)

builtinType :: Text -> [StaticType] -> Maybe (StaticType, [Text])
builtinType name argTypes =
    case name of
        "len" -> expectOverloads TypeInt [[TypeList], [TypeString]]
        "before" -> expectOverloads TypeBool [[TypeInt, TypeInt], [TypeDate, TypeDate], [TypeRange, TypeRange], [TypeEntity, TypeEntity]]
        "after" -> expectOverloads TypeBool [[TypeInt, TypeInt], [TypeDate, TypeDate], [TypeRange, TypeRange], [TypeEntity, TypeEntity]]
        "contains" -> expectOverloads TypeBool [[TypeString, TypeString], [TypeRange, TypeRange], [TypeEntity, TypeEntity], [TypeDate, TypeDate, TypeDate, TypeDate], [TypeInt, TypeInt, TypeInt, TypeInt]]
        "range" -> expectOverloads TypeRange [[TypeInt, TypeInt], [TypeDate, TypeDate]]
        "entities_where" -> expectOverloads TypeList [[TypeString]]
        "active_on" -> expectOverloads TypeList [[TypeTimeline]]
        "alive_at" -> expectOverloads TypeList [[TypeInt], [TypeDate]]
        "inbound" -> expectOverloads TypeList [[TypeEntity, TypeString], [TypeString, TypeString]]
        "outbound" -> expectOverloads TypeList [[TypeEntity, TypeString], [TypeString, TypeString]]
        "has_inbound" -> expectOverloads TypeBool [[TypeEntity, TypeString], [TypeString, TypeString]]
        "has_outbound" -> expectOverloads TypeBool [[TypeEntity, TypeString], [TypeString, TypeString]]
        "type_of" -> expectOverloads TypeString [[TypeEntity], [TypeString]]
        "to_string" -> expectArity TypeString 1
        "years" -> expectOverloads TypeDuration [[TypeInt]]
        "months" -> expectOverloads TypeDuration [[TypeInt]]
        "days" -> expectOverloads TypeDuration [[TypeInt]]
        "duration_days" -> expectOverloads TypeInt [[TypeDuration]]
        "duration_months" -> expectOverloads TypeInt [[TypeDuration]]
        "duration_years" -> expectOverloads TypeInt [[TypeDuration]]
        "duration_between" -> expectOverloads TypeDuration [[TypeDate, TypeDate], [TypeRange]]
        "midpoint" -> expectOverloads TypeUnknown [[TypeRange], [TypeDate, TypeDate]]
        "head" -> expectOverloads TypeUnknown [[TypeList]]
        "tail" -> expectOverloads TypeList [[TypeList]]
        "last" -> expectOverloads TypeUnknown [[TypeList]]
        "reverse" -> expectOverloads TypeList [[TypeList]]
        "flatten" -> expectOverloads TypeList [[TypeList]]
        "sort" -> expectOverloads TypeList [[TypeList]]
        "unique" -> expectOverloads TypeList [[TypeList]]
        "split" -> expectOverloads TypeList [[TypeString, TypeString]]
        "replace" -> expectOverloads TypeString [[TypeString, TypeString, TypeString]]
        "substring" -> expectOverloads TypeString [[TypeString, TypeInt, TypeInt]]
        "starts_with" -> expectOverloads TypeBool [[TypeString, TypeString]]
        "ends_with" -> expectOverloads TypeBool [[TypeString, TypeString]]
        "to_upper" -> expectOverloads TypeString [[TypeString]]
        "to_lower" -> expectOverloads TypeString [[TypeString]]
        "trim" -> expectOverloads TypeString [[TypeString]]
        "abs" -> expectOverloads TypeInt [[TypeInt]]
        "min" -> expectOverloads TypeInt [[TypeInt, TypeInt]]
        "max" -> expectOverloads TypeInt [[TypeInt, TypeInt]]
        "clamp" -> expectOverloads TypeInt [[TypeInt, TypeInt, TypeInt]]
        "causes_of" -> expectOverloads TypeList [[TypeEntity]]
        "effects_of" -> expectOverloads TypeList [[TypeEntity]]
        "related_to" -> expectOverloads TypeList [[TypeEntity]]
        _
            | Set.member name intervalNames -> expectOverloads TypeBool [[TypeRange, TypeRange], [TypeEntity, TypeEntity], [TypeDate, TypeDate, TypeDate, TypeDate], [TypeInt, TypeInt, TypeInt, TypeInt]]
            | otherwise -> Nothing
  where
    expectArity returnType arity =
        Just
            ( returnType
            , [ "builtin " <> name <> " expected " <> showText arity <> " arguments but got " <> showText (length argTypes)
              | length argTypes /= arity
              ]
            )
    expectOverloads returnType overloads =
        Just
            ( returnType
            , [ "builtin " <> name <> " expected " <> renderOverloads overloads <> ", got (" <> T.intercalate ", " (map renderStaticType argTypes) <> ")"
              | not (any (matchesTypes argTypes) overloads)
              ]
            )

intervalNames :: Set Text
intervalNames =
    Set.fromList
        [ "contains_range"
        , "during"
        , "equals"
        , "finished_by"
        , "finishes"
        , "meets"
        , "met_by"
        , "overlapped_by"
        , "overlaps"
        , "started_by"
        , "starts"
        ]

matchesTypes :: [StaticType] -> [StaticType] -> Bool
matchesTypes actual expected =
    length actual == length expected
        && and (zipWith typesCompatible expected actual)

inferBinary :: SourceSpan -> TypeEnv -> BinaryOp -> Expr -> Expr -> (StaticType, [Diagnostic])
inferBinary sourceSpan env op lhs rhs =
    let (leftType, leftDiagnostics) = inferExpr sourceSpan env lhs
        (rightType, rightDiagnostics) = inferExpr sourceSpan env rhs
        diagnostics = leftDiagnostics ++ rightDiagnostics
    in case op of
        OpAdd ->
            if any (matchesTypes [leftType, rightType]) [[TypeInt, TypeInt], [TypeString, TypeString], [TypeDate, TypeDuration], [TypeDuration, TypeDate], [TypeDuration, TypeDuration]]
                then (if leftType == TypeString then TypeString else leftType, diagnostics)
                else (TypeUnknown, diagnostics ++ mismatchBinary sourceSpan op leftType rightType)
        OpSub ->
            if any (matchesTypes [leftType, rightType]) [[TypeInt, TypeInt], [TypeDate, TypeDuration], [TypeDate, TypeDate], [TypeDuration, TypeDuration]]
                then (if leftType == TypeDate && rightType == TypeDate then TypeDuration else leftType, diagnostics)
                else (TypeUnknown, diagnostics ++ mismatchBinary sourceSpan op leftType rightType)
        OpMul -> numeric
        OpDiv -> numeric
        OpMod -> numeric
        OpConcat ->
            if any (matchesTypes [leftType, rightType]) [[TypeString, TypeString], [TypeList, TypeList]]
                then (leftType, diagnostics)
                else (TypeUnknown, diagnostics ++ mismatchBinary sourceSpan op leftType rightType)
        OpGt -> comparable
        OpLt -> comparable
        OpGte -> comparable
        OpLte -> comparable
        OpEq -> (TypeBool, diagnostics)
        OpNeq -> (TypeBool, diagnostics)
        OpAnd -> boolean
        OpOr -> boolean
  where
    numeric =
        if matchesTypes [fst (inferExpr sourceSpan env lhs), fst (inferExpr sourceSpan env rhs)] [TypeInt, TypeInt]
            then (TypeInt, snd (inferExpr sourceSpan env lhs) ++ snd (inferExpr sourceSpan env rhs))
            else
                let (leftType, leftDiagnostics) = inferExpr sourceSpan env lhs
                    (rightType, rightDiagnostics) = inferExpr sourceSpan env rhs
                in (TypeUnknown, leftDiagnostics ++ rightDiagnostics ++ mismatchBinary sourceSpan op leftType rightType)
    comparable =
        let (leftType, leftDiagnostics) = inferExpr sourceSpan env lhs
            (rightType, rightDiagnostics) = inferExpr sourceSpan env rhs
        in if any (matchesTypes [leftType, rightType]) [[TypeInt, TypeInt], [TypeDate, TypeDate]]
            then (TypeBool, leftDiagnostics ++ rightDiagnostics)
            else (TypeUnknown, leftDiagnostics ++ rightDiagnostics ++ mismatchBinary sourceSpan op leftType rightType)
    boolean =
        let (leftType, leftDiagnostics) = inferExpr sourceSpan env lhs
            (rightType, rightDiagnostics) = inferExpr sourceSpan env rhs
        in if matchesTypes [leftType, rightType] [TypeBool, TypeBool]
            then (TypeBool, leftDiagnostics ++ rightDiagnostics)
            else (TypeUnknown, leftDiagnostics ++ rightDiagnostics ++ mismatchBinary sourceSpan op leftType rightType)

mismatchBinary :: SourceSpan -> BinaryOp -> StaticType -> StaticType -> [Diagnostic]
mismatchBinary sourceSpan op leftType rightType =
    [ typeDiagnostic sourceSpan ("unsupported operands for " <> T.pack (show op) <> ": " <> renderStaticType leftType <> " and " <> renderStaticType rightType)
    | leftType /= TypeUnknown
    , rightType /= TypeUnknown
    ]

inferUnary :: SourceSpan -> TypeEnv -> UnaryOp -> Expr -> (StaticType, [Diagnostic])
inferUnary sourceSpan env op operand =
    let (operandType, diagnostics) = inferExpr sourceSpan env operand
    in case op of
        OpNeg ->
            if operandType `elem` [TypeInt, TypeDuration, TypeUnknown]
                then (operandType, diagnostics)
                else (TypeUnknown, diagnostics ++ [typeDiagnostic sourceSpan ("unsupported operand for negation: " <> renderStaticType operandType)])
        OpNot ->
            if operandType `elem` [TypeBool, TypeUnknown]
                then (TypeBool, diagnostics)
                else (TypeUnknown, diagnostics ++ [typeDiagnostic sourceSpan ("unsupported operand for !: " <> renderStaticType operandType)])

typeFromValue :: Value -> StaticType
typeFromValue value =
    case value of
        VNull -> TypeNull
        VString _ -> TypeString
        VInt _ -> TypeInt
        VBool _ -> TypeBool
        VDate _ -> TypeDate
        VDuration _ _ _ -> TypeDuration
        VList _ -> TypeList
        VRange _ -> TypeRange
        VEntityRef _ -> TypeEntity
        VSourceRef _ -> TypeSource
        VTimelineRef _ -> TypeTimeline
        VRulesetRef _ -> TypeRuleset
        VDeadlineRuleRef _ -> TypeDeadlineRule
        VLocatorRef _ -> TypeLocator
        VIssueRef _ -> TypeIssue
        VIssueElementRef _ -> TypeIssueElement
        VClosureRef _ -> TypeClosure

typeFromName :: Text -> StaticType
typeFromName name =
    case name of
        "int" -> TypeInt
        "string" -> TypeString
        "bool" -> TypeBool
        "date" -> TypeDate
        "duration" -> TypeDuration
        "list" -> TypeList
        "range" -> TypeRange
        "entity" -> TypeEntity
        "timeline" -> TypeTimeline
        "source" -> TypeSource
        "ruleset" -> TypeRuleset
        "deadline_rule" -> TypeDeadlineRule
        "locator" -> TypeLocator
        "issue" -> TypeIssue
        "issue_element" -> TypeIssueElement
        "closure" -> TypeClosure
        other -> TypeEntityNamed other

typesCompatible :: StaticType -> StaticType -> Bool
typesCompatible _ TypeUnknown = True
typesCompatible TypeUnknown _ = True
typesCompatible _ TypeNull = True
typesCompatible TypeEntity (TypeEntityNamed _) = True
typesCompatible (TypeEntityNamed expected) (TypeEntityNamed actual) = expected == actual
typesCompatible expected actual = expected == actual

renderStaticType :: StaticType -> Text
renderStaticType staticType =
    case staticType of
        TypeUnknown -> "unknown"
        TypeNull -> "null"
        TypeInt -> "int"
        TypeString -> "string"
        TypeBool -> "bool"
        TypeDate -> "date"
        TypeDuration -> "duration"
        TypeList -> "list"
        TypeRange -> "range"
        TypeEntity -> "entity"
        TypeEntityNamed name -> name
        TypeTimeline -> "timeline"
        TypeSource -> "source"
        TypeRuleset -> "ruleset"
        TypeDeadlineRule -> "deadline_rule"
        TypeLocator -> "locator"
        TypeIssue -> "issue"
        TypeIssueElement -> "issue_element"
        TypeClosure -> "closure"

renderOverloads :: [[StaticType]] -> Text
renderOverloads overloads =
    T.intercalate " or " (map renderOverload overloads)
  where
    renderOverload overload = "(" <> T.intercalate ", " (map renderStaticType overload) <> ")"

typeDiagnostic :: SourceSpan -> Text -> Diagnostic
typeDiagnostic sourceSpan message =
    Diagnostic
        { diagnosticLevel = DiagnosticError
        , diagnosticSource = "typecheck"
        , diagnosticMessage = message
        , diagnosticSpan = Just sourceSpan
        }

showText :: Show a => a -> Text
showText = T.pack . show
