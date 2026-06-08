{-# LANGUAGE OverloadedStrings #-}

module Euclid.Core.Eval
    ( evalProgram
    ) where

import Control.Monad (foldM, unless)
import Data.Foldable (traverse_)
import qualified Data.List
import Data.Map.Strict (Map)
import qualified Data.Map.Strict as Map
import Data.Maybe (fromMaybe, isJust)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as T
import Data.Time (toModifiedJulianDay)
import Euclid.Lang.AST
import Euclid.Model.Types

data EvalState = EvalState
    { evalWorld :: World
    , evalEnv :: Map Text Value
    , evalMutableNames :: Set.Set Text
    , evalFunctions :: Map Text FnDecl
    , evalClosures :: Map Integer ClosureDef
    , evalNextClosureId :: Integer
    , evalFunctionDepth :: Int
    , evalReturnValue :: Maybe Value
    , evalCurrentSpan :: Maybe SourceSpan
    }

data ClosureDef = ClosureDef
    { closureParams :: [(Text, Text)]
    , closureBody :: Expr
    , closureCapturedEnv :: Map Text Value
    }

maxWhileIterations :: Integer
maxWhileIterations = 10000

evaluatorDiagnostic :: EvalState -> Text -> Diagnostic
evaluatorDiagnostic state message =
    Diagnostic
        { diagnosticLevel = DiagnosticError
        , diagnosticSource = "evaluator"
        , diagnosticMessage = message
        , diagnosticSpan = evalCurrentSpan state
        }

evalProgram :: Program -> Either Diagnostic World
evalProgram (ProgramData _ statements) =
    evalWorld <$> foldM evalStmt (EvalState emptyWorld Map.empty Set.empty Map.empty Map.empty 0 0 Nothing Nothing) statements

evalStmt :: EvalState -> Stmt -> Either Diagnostic EvalState
evalStmt state (StmtData currentSpan statement) =
    case evalReturnValue state of
        Just _ -> pure state
        Nothing ->
            let scopedState = state{evalCurrentSpan = Just currentSpan}
             in case statement of
                StmtTypeNode decl -> do
                    rejectDuplicate scopedState "type" (typeDeclName decl) (worldTypes (evalWorld scopedState))
                    (state1, metaValues) <- evalExprMap scopedState (typeDeclMeta decl)
                    let world' =
                            (evalWorld state1)
                                { worldTypes =
                                    Map.insert
                                        (typeDeclName decl)
                                        TypeDef
                                            { typeName = typeDeclName decl
                                            , typeParent = typeDeclParent decl
                                            , typeFields = typeDeclFields decl
                                            , typeMeta = metaValues
                                            , typeSourceSpan = evalCurrentSpan scopedState
                                            }
                                        (worldTypes (evalWorld state1))
                                }
                    pure state1{evalWorld = world'}
                StmtTimelineNode decl -> do
                    rejectDuplicate scopedState "timeline" (timelineDeclName decl) (worldTimelines (evalWorld scopedState))
                    kindValue <- resolveTimelineKind scopedState (timelineDeclName decl) (timelineDeclKind decl)
                    (state1, startValue) <- exprToTimePoint scopedState (timelineDeclStart decl)
                    (state2, endValue) <- exprToTimePoint state1 (timelineDeclEnd decl)
                    (state3, loopCountValue) <- evalOptionalInteger state2 (timelineDeclLoopCount decl)
                    (state4, forkValue) <- evalOptionalTimelineRef state3 (timelineDeclForkFrom decl)
                    (state5, mergeValue) <- evalOptionalTimelineRef state4 (timelineDeclMergeInto decl)
                    let world' =
                            (evalWorld state5)
                                { worldTimelines =
                                    Map.insert
                                        (timelineDeclName decl)
                                        Timeline
                                            { timelineName = timelineDeclName decl
                                            , timelineKind = kindValue
                                            , timelineStart = startValue
                                            , timelineEnd = endValue
                                            , timelineParent = timelineDeclParent decl
                                            , timelineForkFrom = forkValue
                                            , timelineMergeInto = mergeValue
                                            , timelineLoopCount = loopCountValue
                                            , timelineSourceSpan = evalCurrentSpan scopedState
                                            }
                                        (worldTimelines (evalWorld state5))
                                }
                    pure state5{evalWorld = world'}
                StmtEntityNode decl -> do
                    rejectDuplicate scopedState "entity" (entityDeclName decl) (worldEntities (evalWorld scopedState))
                    (state1, fieldValues) <- evalExprMap scopedState (entityDeclFields decl)
                    (state2, appearances) <- evalAppearances state1 (entityDeclAppearances decl)
                    (state3, stateChanges) <- evalStateChanges state2 (entityDeclStateChanges decl)
                    let ad = entityDeclAnnotation decl
                    (state4, noteVal) <- evalOptionalExpr state3 (annotationDeclNote ad)
                    (state5, sourceVal) <- evalOptionalExpr state4 (annotationDeclSource ad)
                    (state6, confVal) <- evalOptionalExpr state5 (annotationDeclConfidence ad)
                    (state7, tagVals) <- evalExprList state6 (annotationDeclTags ad)
                    (state8, recurrence) <- evalRecurrence state7 (entityDeclRecurrence decl) (entityDeclSkip decl)
                    let annotation = Annotation
                            { annotationNote = case noteVal of {Just (VString t) -> Just t; _ -> Nothing}
                            , annotationSource = case sourceVal of {Just (VString t) -> Just t; _ -> Nothing}
                            , annotationConfidence = case confVal of {Just (VInt n) -> Just (fromInteger n / 100.0); _ -> Nothing}
                            , annotationTags = [t | VString t <- tagVals]
                            }
                        world' =
                            (evalWorld state8)
                                { worldEntities =
                                    Map.insert
                                        (entityDeclName decl)
                                        Entity
                                            { entityName = entityDeclName decl
                                            , entityType = maybe "entity" id (entityDeclType decl)
                                            , entityFields = fieldValues
                                            , entityAppearances = appearances
                                            , entityStateChanges = stateChanges
                                            , entityAnnotation = annotation
                                            , entityRecurrence = recurrence
                                            , entitySourceSpan = evalCurrentSpan scopedState
                                            }
                                        (worldEntities (evalWorld state8))
                                }
                    pure state8{evalWorld = world'}
                StmtRelationshipNode decl -> do
                    (state1, scope) <-
                        case relationshipDeclTemporalScope decl of
                            Nothing -> pure (scopedState, Nothing)
                            Just (startExpr, endExpr) -> do
                                (state', startValue) <- exprToTimePoint scopedState startExpr
                                (state'', endValue) <- exprToTimePoint state' endExpr
                                pure (state'', Just (TimeRange startValue endValue))
                    let causalKind = case relationshipDeclCausalKind decl of
                            CausalDeclNone -> CausalNone
                            CausalDeclCauses -> CausalCauses
                            CausalDeclEnables -> CausalEnables
                        world' =
                            (evalWorld state1)
                                { worldRelationships =
                                    worldRelationships (evalWorld state1)
                                        ++ [ Relationship
                                                { relSource = relationshipDeclSource decl
                                                , relLabel = relationshipDeclLabel decl
                                                , relTarget = relationshipDeclTarget decl
                                                , relDirected = relationshipDeclDirected decl
                                                , relCausalKind = causalKind
                                                , relTemporalScope = scope
                                                , relSourceSpan = evalCurrentSpan scopedState
                                                }
                                           ]
                                }
                    pure state1{evalWorld = world'}
                StmtViewNode decl -> do
                    (state1, timeRange) <- case viewDeclTimeRange decl of
                        Nothing -> pure (scopedState, Nothing)
                        Just (startExpr, endExpr) -> do
                            (s1, sv) <- exprToTimePoint scopedState startExpr
                            (s2, ev) <- exprToTimePoint s1 endExpr
                            pure (s2, Just (TimeRange sv ev))
                    let world' = (evalWorld state1)
                            { worldViews = Map.insert (viewDeclName decl)
                                View
                                    { viewName = viewDeclName decl
                                    , viewTimelines = viewDeclTimelines decl
                                    , viewEntityFilter = viewDeclFilter decl
                                    , viewTimeRange = timeRange
                                    , viewHighlight = viewDeclHighlight decl
                                    , viewSourceSpan = evalCurrentSpan scopedState
                                    }
                                (worldViews (evalWorld state1))
                            }
                    pure state1{evalWorld = world'}
                StmtScenarioNode decl -> do
                    -- fork current world state, evaluate body in fork, store as scenario
                    let baseWorld = evalWorld scopedState
                        forkState = scopedState -- inherits all current state
                    scenarioState <- foldM evalStmt forkState (scenarioDeclBody decl)
                    let scenarioWorld = evalWorld scenarioState
                        world' = baseWorld
                            { worldScenarios = Map.insert (scenarioDeclName decl) scenarioWorld (worldScenarios baseWorld) }
                    pure scopedState{evalWorld = world'}
                StmtConstraintNode decl ->
                    let world' = (evalWorld scopedState)
                            { worldConstraints = worldConstraints (evalWorld scopedState)
                                ++ [Constraint (constraintDeclName decl) (evalCurrentSpan scopedState)]
                            }
                    in do
                        -- evaluate constraint body in current world to check it passes
                        constraintState <- foldM evalStmt scopedState (constraintDeclBody decl)
                        pure constraintState{evalWorld = world'}
                StmtImportNode _ ->
                    pure state
                StmtLetNode decl -> do
                    (state1, value) <- evalExpr scopedState (letValue decl)
                    maybe (pure ()) (assertTypeMatches state1 value) (letTypeAnnotation decl)
                    pure $
                        state1
                            { evalEnv = Map.insert (letName decl) value (evalEnv state1)
                            , evalMutableNames =
                                if letMutable decl
                                    then Set.insert (letName decl) (evalMutableNames state1)
                                    else Set.delete (letName decl) (evalMutableNames state1)
                            }
                StmtAssignNode name expr ->
                    if Map.member name (evalEnv scopedState)
                        then
                            if Set.member name (evalMutableNames scopedState)
                                then do
                                    (state1, value) <- evalExpr scopedState expr
                                    pure state1{evalEnv = Map.insert name value (evalEnv state1)}
                                else
                                    Left (evaluatorDiagnostic scopedState ("cannot assign to immutable variable: " <> name))
                        else
                            Left (evaluatorDiagnostic scopedState ("cannot assign to undefined variable: " <> name))
                StmtForNode decl ->
                    evalForLoop scopedState decl
                StmtRepeatNode decl ->
                    evalRepeatLoop scopedState decl
                StmtWhileNode decl ->
                    evalWhileLoop scopedState decl
                StmtFunctionNode decl -> do
                    let world' =
                            (evalWorld scopedState)
                                { worldFunctions =
                                    Map.insert
                                        (fnName decl)
                                        FunctionSig
                                            { functionName = fnName decl
                                            , functionParams = fnParams decl
                                            , functionReturnType = fnReturnType decl
                                            , functionSourceSpan = evalCurrentSpan scopedState
                                            }
                                        (worldFunctions (evalWorld scopedState))
                                }
                    pure
                        scopedState
                            { evalWorld = world'
                            , evalFunctions = Map.insert (fnName decl) decl (evalFunctions scopedState)
                            }
                StmtIfNode decl -> do
                    (state1, conditionValue) <- evalExpr scopedState (ifCondition decl)
                    case conditionValue of
                        VBool True -> foldM evalStmt state1 (ifThenBlock decl)
                        VBool False -> evalElseBranches state1 (ifElseIfBlocks decl) (ifElseBlock decl)
                        _ -> Left (evaluatorDiagnostic state1 "if condition must evaluate to a boolean")
                StmtMatchNode decl ->
                    evalMatch scopedState decl
                StmtReturnNode maybeExpr ->
                    if evalFunctionDepth scopedState <= 0
                        then
                            Left (evaluatorDiagnostic scopedState "return can only be used inside a function")
                        else do
                            (state1, returnValue) <-
                                case maybeExpr of
                                    Nothing -> pure (scopedState, VNull)
                                    Just expr -> evalExpr scopedState expr
                            pure state1{evalReturnValue = Just returnValue}
                StmtExprNode expr ->
                    fst <$> evalExpr scopedState expr

evalExpr :: EvalState -> Expr -> Either Diagnostic (EvalState, Value)
evalExpr state (ExprValue value) = Right (state, value)
evalExpr state (ExprIdent name) =
    case Map.lookup name (evalEnv state) of
        Just value -> Right (state, value)
        Nothing ->
            case findEntity name (evalWorld state) of
                Just _ -> Right (state, VEntityRef name)
                Nothing ->
                    case findTimeline name (evalWorld state) of
                        Just _ -> Right (state, VTimelineRef name)
                        Nothing ->
                            Left (evaluatorDiagnostic state ("unresolved identifier: " <> name))
evalExpr state (ExprList exprs) = do
    (nextState, values) <- evalExprList state exprs
    pure (nextState, VList values)
evalExpr state (ExprRange startExpr endExpr) = do
    (state1, startValue) <- evalExpr state startExpr
    (state2, endValue) <- evalExpr state1 endExpr
    case (startValue, endValue) of
        (VInt startInt, VInt endInt) ->
            pure
                ( state2
                , VList $
                    map VInt $
                        if startInt <= endInt
                            then [startInt .. endInt]
                            else reverse [endInt .. startInt]
                )
        _ ->
            pure (state2, VList [startValue, endValue])
evalExpr state (ExprIndex objectExpr indexExpr) = do
    (state1, objectValue) <- evalExpr state objectExpr
    (state2, indexValue) <- evalExpr state1 indexExpr
    case indexValue of
        VInt indexInt
            | indexInt < 0 ->
                Left (evaluatorDiagnostic state2 "index must be non-negative")
            | otherwise ->
                do
                    indexedValue <- evalIndex state2 objectValue (fromInteger indexInt)
                    pure (state2, indexedValue)
        _ ->
            Left (evaluatorDiagnostic state2 "index expression must evaluate to an integer")
evalExpr state (ExprField objectExpr fieldName) = do
    (state1, objectValue) <- evalExpr state objectExpr
    fieldValue <- evalFieldAccess state1 objectValue fieldName
    pure (state1, fieldValue)
evalExpr state (ExprCall calleeExpr argExprs) =
    evalCall state calleeExpr argExprs
evalExpr state (ExprClosure params bodyExpr) =
    let closureId = evalNextClosureId state
        closureDef =
            ClosureDef
                { closureParams = params
                , closureBody = bodyExpr
                , closureCapturedEnv = evalEnv state
                }
        nextState =
            state
                { evalClosures = Map.insert closureId closureDef (evalClosures state)
                , evalNextClosureId = closureId + 1
                }
     in Right (nextState, VClosureRef closureId)
evalExpr state (ExprTemporalAccess objExpr fieldName timeExpr) = do
    (state1, objValue) <- evalExpr state objExpr
    (state2, timeValue) <- evalExpr state1 timeExpr
    case timePointFromValue timeValue of
        Left msg -> Left (evaluatorDiagnostic state2 msg)
        Right tp -> case objValue of
            VEntityRef name ->
                case findEntity name (evalWorld state2) of
                    Just entity -> case entityFieldAt entity fieldName tp of
                        Just v -> Right (state2, v)
                        Nothing -> unknownField "entity" fieldName
                    Nothing -> Left (evaluatorDiagnostic state2 ("unknown entity: " <> name))
            _ -> Left (evaluatorDiagnostic state2 "temporal access requires an entity reference")
evalExpr state (ExprUnary op operand) = do
    (state1, value) <- evalExpr state operand
    resultValue <- evalUnary state1 op value
    pure (state1, resultValue)
evalExpr state (ExprBinary op lhs rhs) = do
    (state1, leftValue) <- evalExpr state lhs
    (state2, rightValue) <- evalExpr state1 rhs
    resultValue <- evalBinary state2 op leftValue rightValue
    pure (state2, resultValue)

evalUnary :: EvalState -> UnaryOp -> Value -> Either Diagnostic Value
evalUnary _ OpNeg (VInt value) = Right (VInt (negate value))
evalUnary _ OpNeg (VDuration y m d) = Right (VDuration (negate y) (negate m) (negate d))
evalUnary _ OpNot (VBool value) = Right (VBool (not value))
evalUnary state op value =
    Left $
        evaluatorDiagnostic
            state
            ("unsupported operand for " <> T.pack (show op) <> ": " <> T.pack (show value))

evalBinary :: EvalState -> BinaryOp -> Value -> Value -> Either Diagnostic Value
evalBinary _ OpAdd (VInt leftValue) (VInt rightValue) = Right (VInt (leftValue + rightValue))
evalBinary _ OpAdd (VString leftValue) (VString rightValue) = Right (VString (leftValue <> rightValue))
evalBinary _ OpAdd (VDate d) (VDuration y m days) = Right (VDate (addDurationToDay d y m days))
evalBinary _ OpAdd (VDuration y m days) (VDate d) = Right (VDate (addDurationToDay d y m days))
evalBinary _ OpAdd (VDuration y1 m1 d1) (VDuration y2 m2 d2) = Right (VDuration (y1+y2) (m1+m2) (d1+d2))
evalBinary _ OpSub (VDate d) (VDuration y m days) = Right (VDate (addDurationToDay d (negate y) (negate m) (negate days)))
evalBinary _ OpSub (VDate d1) (VDate d2) = Right (VDuration 0 0 (daysBetween d1 d2))
evalBinary _ OpSub (VDuration y1 m1 d1) (VDuration y2 m2 d2) = Right (VDuration (y1-y2) (m1-m2) (d1-d2))
evalBinary _ OpSub (VInt leftValue) (VInt rightValue) = Right (VInt (leftValue - rightValue))
evalBinary _ OpMul (VInt leftValue) (VInt rightValue) = Right (VInt (leftValue * rightValue))
evalBinary state OpDiv _ (VInt 0) = Left (evaluatorDiagnostic state "division by zero")
evalBinary _ OpDiv (VInt leftValue) (VInt rightValue) = Right (VInt (div leftValue rightValue))
evalBinary state OpMod _ (VInt 0) = Left (evaluatorDiagnostic state "modulo by zero")
evalBinary _ OpMod (VInt leftValue) (VInt rightValue) = Right (VInt (mod leftValue rightValue))
evalBinary _ OpConcat (VString leftValue) (VString rightValue) = Right (VString (leftValue <> rightValue))
evalBinary _ OpConcat (VList leftValue) (VList rightValue) = Right (VList (leftValue ++ rightValue))
evalBinary _ OpGt (VInt leftValue) (VInt rightValue) = Right (VBool (leftValue > rightValue))
evalBinary _ OpGt (VDate leftValue) (VDate rightValue) = Right (VBool (leftValue > rightValue))
evalBinary _ OpLt (VInt leftValue) (VInt rightValue) = Right (VBool (leftValue < rightValue))
evalBinary _ OpLt (VDate leftValue) (VDate rightValue) = Right (VBool (leftValue < rightValue))
evalBinary _ OpGte (VInt leftValue) (VInt rightValue) = Right (VBool (leftValue >= rightValue))
evalBinary _ OpGte (VDate leftValue) (VDate rightValue) = Right (VBool (leftValue >= rightValue))
evalBinary _ OpLte (VInt leftValue) (VInt rightValue) = Right (VBool (leftValue <= rightValue))
evalBinary _ OpLte (VDate leftValue) (VDate rightValue) = Right (VBool (leftValue <= rightValue))
evalBinary _ OpEq leftValue rightValue = Right (VBool (leftValue == rightValue))
evalBinary _ OpNeq leftValue rightValue = Right (VBool (leftValue /= rightValue))
evalBinary _ OpAnd (VBool leftValue) (VBool rightValue) = Right (VBool (leftValue && rightValue))
evalBinary _ OpOr (VBool leftValue) (VBool rightValue) = Right (VBool (leftValue || rightValue))
evalBinary state op leftValue rightValue =
    Left $
        evaluatorDiagnostic
            state
            ( "unsupported operands for "
                <> T.pack (show op)
                <> ": "
                <> T.pack (show leftValue)
                <> " and "
                <> T.pack (show rightValue)
            )

evalIndex :: EvalState -> Value -> Int -> Either Diagnostic Value
evalIndex state (VList values) indexValue
    | indexValue < length values = Right (values !! indexValue)
    | otherwise = Left (indexOutOfBounds state "list" indexValue (length values))
evalIndex state (VString textValue) indexValue
    | indexValue < T.length textValue =
        Right (VString (T.singleton (T.index textValue indexValue)))
    | otherwise =
        Left (indexOutOfBounds state "string" indexValue (T.length textValue))
evalIndex state value _ =
    Left (evaluatorDiagnostic state ("cannot index into value " <> T.pack (show value)))

indexOutOfBounds :: EvalState -> Text -> Int -> Int -> Diagnostic
indexOutOfBounds state targetName indexValue targetLength =
    evaluatorDiagnostic
        state
        ( 
            "index "
                <> T.pack (show indexValue)
                <> " is out of bounds for "
                <> targetName
                <> " of length "
                <> T.pack (show targetLength)
        )

evalCall :: EvalState -> Expr -> [Expr] -> Either Diagnostic (EvalState, Value)
evalCall state (ExprIdent name) argExprs = do
    (state1, argValues) <- evalExprList state argExprs
    case Map.lookup name (evalFunctions state1) of
        Just fnDecl ->
            callNamedFunction state1 name fnDecl argValues
        Nothing ->
            case evalBuiltin state1 name argValues of
                Just builtinValue ->
                    pure (state1, builtinValue)
                Nothing ->
                    case Map.lookup name (evalEnv state1) of
                        Just (VClosureRef closureId) ->
                            callClosure state1 closureId argValues
                        Just _ ->
                            Left (evaluatorDiagnostic state1 "only named functions and closure values are callable in the current implementation")
                        Nothing ->
                            undefinedFunction state1 name
evalCall state calleeExpr argExprs = do
    (state1, calleeValue) <- evalExpr state calleeExpr
    (state2, argValues) <- evalExprList state1 argExprs
    case calleeValue of
        VClosureRef closureId ->
            callClosure state2 closureId argValues
        _ ->
            Left (evaluatorDiagnostic state2 "only named functions and closure values are callable in the current implementation")

callNamedFunction :: EvalState -> Text -> FnDecl -> [Value] -> Either Diagnostic (EvalState, Value)
callNamedFunction state name fnDecl argValues =
    if length argValues /= length (fnParams fnDecl)
        then
            Left $
                evaluatorDiagnostic
                    state
                    ( "function "
                        <> name
                        <> " expected "
                        <> T.pack (show (length (fnParams fnDecl)))
                        <> " arguments but got "
                        <> T.pack (show (length argValues))
                    )
        else do
            traverse_ (uncurry (assertTypeMatches state)) (zip argValues (map snd (fnParams fnDecl)))
            let savedEnv = evalEnv state
                savedMutableNames = evalMutableNames state
                savedReturn = evalReturnValue state
                paramBindings = Map.fromList (zip (map fst (fnParams fnDecl)) argValues)
                paramNames = Set.fromList (map fst (fnParams fnDecl))
                callState =
                    state
                        { evalEnv = paramBindings `Map.union` savedEnv
                        , evalMutableNames = savedMutableNames `Set.difference` paramNames
                        , evalFunctionDepth = evalFunctionDepth state + 1
                        , evalReturnValue = Nothing
                        }
            (resultState, resultValue) <- evalBlockWithResult callState (fnBody fnDecl)
            let finalValue = fromMaybe resultValue (evalReturnValue resultState)
            maybe (pure ()) (assertTypeMatches resultState finalValue) (fnReturnType fnDecl)
            pure
                ( resultState
                    { evalEnv = savedEnv
                    , evalMutableNames = savedMutableNames
                    , evalFunctionDepth = evalFunctionDepth state
                    , evalReturnValue = savedReturn
                    }
                , finalValue
                )

callClosure :: EvalState -> Integer -> [Value] -> Either Diagnostic (EvalState, Value)
callClosure state closureId argValues =
    case Map.lookup closureId (evalClosures state) of
        Nothing ->
            Left (evaluatorDiagnostic state ("unknown closure reference: " <> T.pack (show closureId)))
        Just closureDef ->
            if length argValues /= length (closureParams closureDef)
                then
                    Left $
                        evaluatorDiagnostic
                            state
                            ( "closure expected "
                                <> T.pack (show (length (closureParams closureDef)))
                                <> " arguments but got "
                                <> T.pack (show (length argValues))
                            )
                else do
                    let savedEnv = evalEnv state
                        savedMutableNames = evalMutableNames state
                        paramBindings = Map.fromList (zip (map fst (closureParams closureDef)) argValues)
                        paramNames = Set.fromList (map fst (closureParams closureDef))
                        callState =
                            state
                                { evalEnv = paramBindings `Map.union` closureCapturedEnv closureDef
                                , evalMutableNames = savedMutableNames `Set.difference` paramNames
                                , evalFunctionDepth = evalFunctionDepth state + 1
                                , evalReturnValue = Nothing
                                }
                    (resultState, resultValue) <- evalExpr callState (closureBody closureDef)
                    pure
                        ( resultState
                            { evalEnv = savedEnv
                            , evalMutableNames = savedMutableNames
                            , evalFunctionDepth = evalFunctionDepth state
                            , evalReturnValue = evalReturnValue state
                            }
                        , resultValue
                        )

evalBuiltin :: EvalState -> Text -> [Value] -> Maybe Value
evalBuiltin state name args =
    case name of
        "len" ->
            case args of
                [VList items] -> Just (VInt (toInteger (length items)))
                [VString textValue] -> Just (VInt (toInteger (T.length textValue)))
                _ -> Nothing
        "before" ->
            case args of
                [leftValue, rightValue] -> VBool <$> ((<) <$> valueToOrdinal leftValue <*> valueToOrdinal rightValue)
                _ -> Nothing
        "after" ->
            case args of
                [leftValue, rightValue] -> VBool <$> ((>) <$> valueToOrdinal leftValue <*> valueToOrdinal rightValue)
                _ -> Nothing
        "type_of" ->
            case args of
                [VEntityRef entityNameValue] ->
                    VString . entityType <$> findEntity entityNameValue (evalWorld state)
                [VString entityNameValue] ->
                    VString . entityType <$> findEntity entityNameValue (evalWorld state)
                _ -> Nothing
        -- math builtins
        "abs" -> case args of [VInt v] -> Just (VInt (Prelude.abs v)); _ -> Nothing
        "min" -> case args of [VInt a, VInt b] -> Just (VInt (Prelude.min a b)); _ -> Nothing
        "max" -> case args of [VInt a, VInt b] -> Just (VInt (Prelude.max a b)); _ -> Nothing
        "clamp" -> case args of [VInt v, VInt lo, VInt hi] -> Just (VInt (Prelude.max lo (Prelude.min hi v))); _ -> Nothing
        -- string builtins
        "contains" -> case args of
            [VString haystack, VString needle] -> Just (VBool (T.isInfixOf needle haystack))
            _ -> allenRelation args (\s1 e1 s2 e2 -> s1 < s2 && e1 > e2)
        "starts_with" -> case args of [VString text, VString pfx] -> Just (VBool (T.isPrefixOf pfx text)); _ -> Nothing
        "ends_with" -> case args of [VString text, VString sfx] -> Just (VBool (T.isSuffixOf sfx text)); _ -> Nothing
        "to_upper" -> case args of [VString text] -> Just (VString (T.toUpper text)); _ -> Nothing
        "to_lower" -> case args of [VString text] -> Just (VString (T.toLower text)); _ -> Nothing
        "trim" -> case args of [VString text] -> Just (VString (T.strip text)); _ -> Nothing
        "split" -> case args of [VString text, VString delim] -> Just (VList (map VString (T.splitOn delim text))); _ -> Nothing
        "replace" -> case args of [VString text, VString old, VString new] -> Just (VString (T.replace old new text)); _ -> Nothing
        "substring" -> case args of
            [VString text, VInt start, VInt end] ->
                let s = fromInteger start; e = fromInteger end
                in Just (VString (T.take (e - s) (T.drop s text)))
            _ -> Nothing
        "to_string" -> case args of
            [VInt v] -> Just (VString (T.pack (show v)))
            [VBool v] -> Just (VString (if v then "true" else "false"))
            [VString v] -> Just (VString v)
            [VNull] -> Just (VString "null")
            [VDate d] -> Just (VString (T.pack (show d)))
            _ -> Nothing
        -- list builtins
        "head" -> case args of [VList (x:_)] -> Just x; _ -> Nothing
        "tail" -> case args of [VList (_:xs)] -> Just (VList xs); _ -> Nothing
        "last" -> case args of [VList xs] | not (null xs) -> Just (Prelude.last xs); _ -> Nothing
        "reverse" -> case args of [VList xs] -> Just (VList (Prelude.reverse xs)); _ -> Nothing
        "flatten" -> case args of [VList xs] -> Just (VList (concatMap flattenValue xs)); _ -> Nothing
        "range" -> case args of [VInt a, VInt b] -> Just (VList (map VInt [a..b])); _ -> Nothing
        "sort" -> case args of [VList xs] -> Just (VList (sortValues xs)); _ -> Nothing
        "unique" -> case args of [VList xs] -> Just (VList (uniqueValues xs)); _ -> Nothing
        -- temporal builtins: duration constructors
        "years" -> case args of [VInt n] -> Just (VDuration n 0 0); _ -> Nothing
        "months" -> case args of [VInt n] -> Just (VDuration 0 n 0); _ -> Nothing
        "days" -> case args of [VInt n] -> Just (VDuration 0 0 n); _ -> Nothing
        "duration_days" -> case args of [VDuration _ _ d] -> Just (VInt d); _ -> Nothing
        "duration_months" -> case args of [VDuration _ m _] -> Just (VInt m); _ -> Nothing
        "duration_years" -> case args of [VDuration y _ _] -> Just (VInt y); _ -> Nothing
        -- Allen's interval algebra (operating on pairs of date ranges)
        "overlaps" -> allenRelation args (\s1 e1 s2 e2 -> s1 < s2 && e1 > s2 && e1 < e2)
        "during" -> allenRelation args (\s1 e1 s2 e2 -> s1 > s2 && e1 < e2)
        "meets" -> allenRelation args (\s1 e1 s2 _e2 -> e1 == s2)
        "starts" -> allenRelation args (\s1 e1 s2 e2 -> s1 == s2 && e1 < e2)
        "finishes" -> allenRelation args (\s1 e1 _s2 e2 -> e1 == e2 && s1 > _s2)
        "equals" -> allenRelation args (\s1 e1 s2 e2 -> s1 == s2 && e1 == e2)
        -- temporal utilities
        "midpoint" -> case args of
            [VDate d1, VDate d2] ->
                let diff = daysBetween d2 d1
                in Just (VDate (addDurationToDay d1 0 0 (diff `div` 2)))
            _ -> Nothing
        "duration_between" -> case args of
            [VDate d1, VDate d2] -> Just (VDuration 0 0 (Prelude.abs (daysBetween d1 d2)))
            _ -> Nothing
        -- temporal queries (world-aware)
        "alive_at" -> case args of
            [VDate d] ->
                let tp = TimeDate d
                    ord = timePointOrdinal tp
                    matching = Map.elems (worldEntities (evalWorld state))
                    alive = filter (\e -> any (\a ->
                        timePointOrdinal (rangeStart (appearanceRange a)) <= ord &&
                        ord <= timePointOrdinal (rangeEnd (appearanceRange a))) (entityAppearances e)) matching
                in Just (VList (map (VEntityRef . entityName) alive))
            [VInt i] ->
                let ord = i
                    matching = Map.elems (worldEntities (evalWorld state))
                    alive = filter (\e -> any (\a ->
                        timePointOrdinal (rangeStart (appearanceRange a)) <= ord &&
                        ord <= timePointOrdinal (rangeEnd (appearanceRange a))) (entityAppearances e)) matching
                in Just (VList (map (VEntityRef . entityName) alive))
            _ -> Nothing
        "active_on" -> case args of
            [VTimelineRef tlName] ->
                let matching = filter (\e -> any (\a -> appearanceTimeline a == tlName) (entityAppearances e))
                        (Map.elems (worldEntities (evalWorld state)))
                in Just (VList (map (VEntityRef . entityName) matching))
            _ -> Nothing
        "entities_where" -> case args of
            [VString typeName] ->
                let matching = filter (\e -> entityType e == typeName)
                        (Map.elems (worldEntities (evalWorld state)))
                in Just (VList (map (VEntityRef . entityName) matching))
            _ -> Nothing
        "causes_of" -> case args of
            [VEntityRef target] ->
                let rels = worldRelationships (evalWorld state)
                    directCauses = [relSource r | r <- rels, relTarget r == target, relCausalKind r /= CausalNone]
                in Just (VList (map VEntityRef directCauses))
            _ -> Nothing
        "effects_of" -> case args of
            [VEntityRef source] ->
                let rels = worldRelationships (evalWorld state)
                    directEffects = [relTarget r | r <- rels, relSource r == source, relCausalKind r /= CausalNone]
                in Just (VList (map VEntityRef directEffects))
            _ -> Nothing
        "related_to" -> case args of
            [VEntityRef name] ->
                let rels = worldRelationships (evalWorld state)
                    related = [relTarget r | r <- rels, relSource r == name]
                        ++ [relSource r | r <- rels, relTarget r == name]
                in Just (VList (map VEntityRef (uniqueTexts related)))
            _ -> Nothing
        _ -> Nothing

uniqueTexts :: [Text] -> [Text]
uniqueTexts = go Set.empty
  where
    go _ [] = []
    go seen (x:xs)
        | Set.member x seen = go seen xs
        | otherwise = x : go (Set.insert x seen) xs

allenRelation :: [Value] -> (Integer -> Integer -> Integer -> Integer -> Bool) -> Maybe Value
allenRelation args relation =
    case args of
        [VEntityRef _, VEntityRef _] -> Nothing -- needs world context, handled elsewhere
        [VDate s1, VDate e1, VDate s2, VDate e2] ->
            let o = toModifiedJulianDay
            in Just (VBool (relation (o s1) (o e1) (o s2) (o e2)))
        _ -> Nothing

flattenValue :: Value -> [Value]
flattenValue (VList xs) = concatMap flattenValue xs
flattenValue x = [x]

sortValues :: [Value] -> [Value]
sortValues xs = Data.List.sortOn valueOrdKey xs

valueOrdKey :: Value -> (Int, Integer, Text)
valueOrdKey (VInt v) = (0, v, "")
valueOrdKey (VString v) = (1, 0, v)
valueOrdKey (VBool v) = (2, if v then 1 else 0, "")
valueOrdKey (VDate d) = (3, toModifiedJulianDay d, "")
valueOrdKey _ = (9, 0, "")

uniqueValues :: [Value] -> [Value]
uniqueValues = go Set.empty
  where
    go _ [] = []
    go seen (x:xs)
        | Set.member x seen = go seen xs
        | otherwise = x : go (Set.insert x seen) xs

valueToOrdinal :: Value -> Maybe Integer
valueToOrdinal (VInt value) = Just value
valueToOrdinal (VDate day) = Just (timePointOrdinal (TimeDate day))
valueToOrdinal _ = Nothing

assertTypeMatches :: EvalState -> Value -> Text -> Either Diagnostic ()
assertTypeMatches state value expectedType
    | valueMatchesType state value expectedType = pure ()
    | otherwise =
        Left $
            evaluatorDiagnostic
                state
                ( "type mismatch: expected "
                    <> expectedType
                    <> " but got "
                    <> renderValueType state value
                )

valueMatchesType :: EvalState -> Value -> Text -> Bool
valueMatchesType _ VNull _ = True
valueMatchesType _ (VInt _) "int" = True
valueMatchesType _ (VString _) "string" = True
valueMatchesType _ (VBool _) "bool" = True
valueMatchesType _ (VDate _) "date" = True
valueMatchesType _ (VList _) "list" = True
valueMatchesType _ (VEntityRef _) "entity" = True
valueMatchesType state (VEntityRef entityNameValue) expectedType =
    case findEntity entityNameValue (evalWorld state) of
        Nothing -> False
        Just entity ->
            entityType entity == expectedType
                || hasTypeAncestor (evalWorld state) (entityType entity) expectedType
valueMatchesType _ (VTimelineRef _) "timeline" = True
valueMatchesType _ (VClosureRef _) "closure" = True
valueMatchesType _ (VDuration _ _ _) "duration" = True
valueMatchesType _ _ _ = False

renderValueType :: EvalState -> Value -> Text
renderValueType _ VNull = "null"
renderValueType _ (VInt _) = "int"
renderValueType _ (VString _) = "string"
renderValueType _ (VBool _) = "bool"
renderValueType _ (VDate _) = "date"
renderValueType _ (VList _) = "list"
renderValueType state (VEntityRef entityNameValue) =
    maybe "entity" entityType (findEntity entityNameValue (evalWorld state))
renderValueType _ (VTimelineRef _) = "timeline"
renderValueType _ (VClosureRef _) = "closure"
renderValueType _ (VDuration _ _ _) = "duration"

hasTypeAncestor :: World -> Text -> Text -> Bool
hasTypeAncestor worldValue currentType expectedType =
    currentType == expectedType
        || case Map.lookup currentType (worldTypes worldValue) of
            Nothing -> False
            Just typeDef ->
                case typeParent typeDef of
                    Nothing -> False
                    Just parentName -> hasTypeAncestor worldValue parentName expectedType

undefinedFunction :: EvalState -> Text -> Either Diagnostic a
undefinedFunction state name =
    Left (evaluatorDiagnostic state ("undefined function: " <> name))

evalFieldAccess :: EvalState -> Value -> Text -> Either Diagnostic Value
evalFieldAccess state objectValue fieldName =
    case objectValue of
        VEntityRef name ->
            case findEntity name (evalWorld state) of
                Just entity ->
                    case fieldName of
                        "name" -> Right (VString (entityName entity))
                        "type" -> Right (VString (entityType entity))
                        "note" -> Right (maybe VNull VString (annotationNote (entityAnnotation entity)))
                        "source" -> Right (maybe VNull VString (annotationSource (entityAnnotation entity)))
                        "confidence" -> Right (maybe VNull (\c -> VInt (round (c * 100))) (annotationConfidence (entityAnnotation entity)))
                        "tags" -> Right (VList (map VString (annotationTags (entityAnnotation entity))))
                        _ ->
                            maybe
                                ( maybe
                                    (unknownField "entity" fieldName)
                                    Right
                                    (lookupTypeMetaValue (evalWorld state) (entityType entity) fieldName)
                                )
                                Right
                                (Map.lookup fieldName (entityFields entity))
                Nothing ->
                    Left (evaluatorDiagnostic state ("unknown entity reference: " <> name))
        VTimelineRef name ->
            case findTimeline name (evalWorld state) of
                Just timeline ->
                    case fieldName of
                        "name" -> Right (VString (timelineName timeline))
                        "kind" -> Right (VString (timelineKindText (timelineKind timeline)))
                        "start" -> Right (timePointToValue (timelineStart timeline))
                        "end" -> Right (timePointToValue (timelineEnd timeline))
                        "parent" -> Right (maybe VNull VString (timelineParent timeline))
                        "loop_count" -> Right (maybe VNull VInt (timelineLoopCount timeline))
                        _ -> unknownField "timeline" fieldName
                Nothing ->
                    Left (evaluatorDiagnostic state ("unknown timeline reference: " <> name))
        _ ->
            Left $
                evaluatorDiagnostic
                    state
                    ( "cannot access field "
                        <> fieldName
                        <> " on value "
                        <> T.pack (show objectValue)
                    )

timelineKindText :: TimelineKind -> Text
timelineKindText TimelineLinear = "linear"
timelineKindText TimelineBranch = "branch"
timelineKindText TimelineParallel = "parallel"
timelineKindText TimelineLoop = "loop"

timePointToValue :: TimePoint -> Value
timePointToValue (TimeDate day) = VDate day
timePointToValue (TimeOrdinal value) = VInt value

unknownField :: Text -> Text -> Either Diagnostic a
unknownField targetKind fieldName =
    Left $
        Diagnostic
            { diagnosticLevel = DiagnosticError
            , diagnosticSource = "evaluator"
            , diagnosticMessage = "unknown " <> targetKind <> " field: " <> fieldName
            , diagnosticSpan = Nothing
            }

lookupTypeMetaValue :: World -> Text -> Text -> Maybe Value
lookupTypeMetaValue worldValue typeNameValue fieldName =
    case Map.lookup typeNameValue (worldTypes worldValue) of
        Nothing -> Nothing
        Just typeDef ->
            case Map.lookup fieldName (typeMeta typeDef) of
                Just metaValue -> Just metaValue
                Nothing ->
                    case typeParent typeDef of
                        Nothing -> Nothing
                        Just parentName -> lookupTypeMetaValue worldValue parentName fieldName

evalExprList :: EvalState -> [Expr] -> Either Diagnostic (EvalState, [Value])
evalExprList state exprs =
    foldM
        ( \(currentState, values) expr -> do
            (nextState, value) <- evalExpr currentState expr
            pure (nextState, values ++ [value])
        )
        (state, [])
        exprs

evalExprMap :: EvalState -> Map Text Expr -> Either Diagnostic (EvalState, Map Text Value)
evalExprMap state exprs = do
    (nextState, values) <-
        foldM
            ( \(currentState, entries) (fieldName, expr) -> do
                (updatedState, value) <- evalExpr currentState expr
                pure (updatedState, entries ++ [(fieldName, value)])
            )
            (state, [])
            (Map.toAscList exprs)
    pure (nextState, Map.fromList values)

evalAppearances :: EvalState -> [AppearanceDecl] -> Either Diagnostic (EvalState, [Appearance])
evalAppearances state appearanceDecls =
    foldM
        ( \(currentState, appearances) appearance -> do
            (state1, startValue) <- exprToTimePoint currentState (appearanceDeclStart appearance)
            (state2, endValue) <- exprToTimePoint state1 (appearanceDeclEnd appearance)
            pure
                ( state2
                , appearances
                    ++ [ Appearance
                            (appearanceDeclTimeline appearance)
                            (TimeRange startValue endValue)
                       ]
                )
        )
        (state, [])
        appearanceDecls

evalStateChanges :: EvalState -> [StateChangeDecl] -> Either Diagnostic (EvalState, [StateChange])
evalStateChanges state decls =
    foldM
        ( \(currentState, changes) decl -> do
            (state1, tp) <- exprToTimePoint currentState (stateChangeDeclTime decl)
            (state2, fields) <- evalExprMap state1 (stateChangeDeclFields decl)
            pure (state2, changes ++ [StateChange tp fields])
        )
        (state, [])
        decls

evalRecurrence :: EvalState -> Maybe Expr -> [Expr] -> Either Diagnostic (EvalState, Maybe Recurrence)
evalRecurrence state Nothing _ = pure (state, Nothing)
evalRecurrence state (Just expr) skipExprs = do
    (state1, value) <- evalExpr state expr
    (state2, skipVals) <- evalExprList state1 skipExprs
    let skipDays = [d | VDate d <- skipVals]
    case value of
        VDuration y m d -> do
            let pattern
                    | y > 0 = RecurYearly y
                    | m > 0 = RecurMonthly m
                    | d >= 7 && d `mod` 7 == 0 = RecurWeekly (d `div` 7)
                    | otherwise = RecurDaily (Prelude.max 1 d)
            pure (state2, Just (Recurrence pattern skipDays))
        _ -> Left (evaluatorDiagnostic state2 "recurrence must be a duration value")

evalOptionalExpr :: EvalState -> Maybe Expr -> Either Diagnostic (EvalState, Maybe Value)
evalOptionalExpr state Nothing = pure (state, Nothing)
evalOptionalExpr state (Just expr) = do
    (nextState, value) <- evalExpr state expr
    pure (nextState, Just value)

evalOptionalInteger :: EvalState -> Maybe Expr -> Either Diagnostic (EvalState, Maybe Integer)
evalOptionalInteger state Nothing = pure (state, Nothing)
evalOptionalInteger state (Just expr) = do
    (nextState, value) <- exprToInteger state expr
    pure (nextState, Just value)

evalOptionalTimelineRef :: EvalState -> Maybe (Text, Expr) -> Either Diagnostic (EvalState, Maybe (Text, TimePoint))
evalOptionalTimelineRef state Nothing = pure (state, Nothing)
evalOptionalTimelineRef state (Just (name, expr)) = do
    (nextState, point) <- exprToTimePoint state expr
    pure (nextState, Just (name, point))

evalBlockWithResult :: EvalState -> [Stmt] -> Either Diagnostic (EvalState, Value)
evalBlockWithResult state statements =
    foldM
        ( \(currentState, _) stmt ->
            case evalReturnValue currentState of
                Just returnValue -> pure (currentState, returnValue)
                Nothing -> evalStmtResult currentState stmt
        )
        (state, VNull)
        statements

evalStmtResult :: EvalState -> Stmt -> Either Diagnostic (EvalState, Value)
evalStmtResult state (StmtReturn maybeExpr) = do
    nextState <- evalStmt state (StmtReturn maybeExpr)
    pure (nextState, fromMaybe VNull (evalReturnValue nextState))
evalStmtResult state (StmtExpr expr) = evalExpr state expr
evalStmtResult state stmt = do
    nextState <- evalStmt state stmt
    pure (nextState, VNull)

exprToTimePoint :: EvalState -> Expr -> Either Diagnostic (EvalState, TimePoint)
exprToTimePoint state expr = do
    (nextState, value) <- evalExpr state expr
    case timePointFromValue value of
        Left message ->
            Left (evaluatorDiagnostic nextState message)
        Right point -> Right (nextState, point)

exprToInteger :: EvalState -> Expr -> Either Diagnostic (EvalState, Integer)
exprToInteger state expr = do
    (nextState, value) <- evalExpr state expr
    case value of
        VInt intValue -> Right (nextState, intValue)
        _ ->
            Left (evaluatorDiagnostic nextState "expected an integer expression")

rejectDuplicate :: EvalState -> Text -> Text -> Map Text a -> Either Diagnostic ()
rejectDuplicate state kind name entries =
    unless (Map.notMember name entries) $
        Left (evaluatorDiagnostic state ("duplicate " <> kind <> ": " <> name))

evalElseBranches :: EvalState -> [(Expr, [Stmt])] -> Maybe [Stmt] -> Either Diagnostic EvalState
evalElseBranches state [] Nothing = pure state
evalElseBranches state [] (Just elseBlock) = foldM evalStmt state elseBlock
evalElseBranches state ((conditionExpr, branchBody) : rest) elseBlock = do
    (state1, conditionValue) <- evalExpr state conditionExpr
    case conditionValue of
        VBool True -> foldM evalStmt state1 branchBody
        VBool False -> evalElseBranches state1 rest elseBlock
        _ -> Left (evaluatorDiagnostic state1 "else-if condition must evaluate to a boolean")

evalMatch :: EvalState -> MatchDecl -> Either Diagnostic EvalState
evalMatch state decl = do
    (state1, subjectValue) <- evalExpr state (matchSubject decl)
    evalMatchArms state1 subjectValue (matchArms decl)

evalMatchArms :: EvalState -> Value -> [MatchArm] -> Either Diagnostic EvalState
evalMatchArms state _ [] = pure state
evalMatchArms state subjectValue (arm : remainingArms)
    | matchPatternMatches (matchArmPattern arm) subjectValue =
        evalMatchArm state subjectValue arm
    | otherwise =
        evalMatchArms state subjectValue remainingArms

evalMatchArm :: EvalState -> Value -> MatchArm -> Either Diagnostic EvalState
evalMatchArm state subjectValue arm =
    case matchArmPattern arm of
        MatchPatternBind name -> do
            let previousBinding = Map.lookup name (evalEnv state)
                scopedState =
                    state
                        { evalEnv =
                            Map.insert name subjectValue (evalEnv state)
                        }
            matchedState <- foldM evalStmt scopedState (matchArmBody arm)
            pure matchedState{evalEnv = restoreBinding previousBinding name (evalEnv matchedState)}
        _ ->
            foldM evalStmt state (matchArmBody arm)

matchPatternMatches :: MatchPattern -> Value -> Bool
matchPatternMatches MatchPatternWildcard _ = True
matchPatternMatches (MatchPatternValue patternValue) subjectValue = patternValue == subjectValue
matchPatternMatches (MatchPatternBind _) _ = True

evalForLoop :: EvalState -> ForDecl -> Either Diagnostic EvalState
evalForLoop state decl = do
    (state1, values) <- evalForIterable state (forIterable decl)
    let previousBinding = Map.lookup (forVar decl) (evalEnv state1)
    iteratedState <-
        foldM
            ( \currentState value ->
                case evalReturnValue currentState of
                    Just _ -> pure currentState
                    Nothing -> do
                        let scopedState =
                                currentState
                                    { evalEnv =
                                        Map.insert (forVar decl) value (evalEnv currentState)
                                    }
                        foldM evalStmt scopedState (forBody decl)
            )
            state1
            values
    pure iteratedState{evalEnv = restoreBinding previousBinding (forVar decl) (evalEnv iteratedState)}

evalForIterable :: EvalState -> ForIterable -> Either Diagnostic (EvalState, [Value])
evalForIterable state iterable =
    case iterable of
        ForRange startExpr endExpr -> do
            (state1, startValue) <- exprToInteger state startExpr
            (state2, endValue) <- exprToInteger state1 endExpr
            pure
                ( state2
                , map VInt $
                    if startValue <= endValue
                        then [startValue .. endValue]
                        else reverse [endValue .. startValue]
                )
        ForList exprs ->
            evalExprList state exprs
        ForExpr expr -> do
            (state1, value) <- evalExpr state expr
            case value of
                VList values -> pure (state1, values)
                _ -> pure (state1, [value])

restoreBinding :: Maybe Value -> Text -> Map Text Value -> Map Text Value
restoreBinding Nothing name env = Map.delete name env
restoreBinding (Just value) name env = Map.insert name value env

resolveTimelineKind :: EvalState -> Text -> Maybe Expr -> Either Diagnostic TimelineKind
resolveTimelineKind _ _ Nothing = Right TimelineLinear
resolveTimelineKind _ _ (Just (ExprIdent "linear")) = Right TimelineLinear
resolveTimelineKind _ _ (Just (ExprIdent "branch")) = Right TimelineBranch
resolveTimelineKind _ _ (Just (ExprIdent "parallel")) = Right TimelineParallel
resolveTimelineKind _ _ (Just (ExprIdent "loop")) = Right TimelineLoop
resolveTimelineKind state timelineNameValue (Just _) =
    Left (evaluatorDiagnostic state ("invalid timeline kind for " <> timelineNameValue))

evalRepeatLoop :: EvalState -> RepeatDecl -> Either Diagnostic EvalState
evalRepeatLoop state decl = do
    (state1, countValue) <- exprToInteger state (repeatCount decl)
    if countValue < 0
        then
            Left (evaluatorDiagnostic state1 "repeat count must be non-negative")
        else
            foldM
                ( \currentState _ ->
                    case evalReturnValue currentState of
                        Just _ -> pure currentState
                        Nothing -> foldM evalStmt currentState (repeatBody decl)
                )
                state1
                [1 .. countValue]

evalWhileLoop :: EvalState -> WhileDecl -> Either Diagnostic EvalState
evalWhileLoop = go 0
  where
    go iterations state decl
        | isJust (evalReturnValue state) = pure state
        | iterations >= maxWhileIterations =
            Left (evaluatorDiagnostic state "while loop exceeded the maximum iteration limit")
        | otherwise = do
            (state1, conditionValue) <- evalExpr state (whileCondition decl)
            case conditionValue of
                VBool True -> do
                    steppedState <- foldM evalStmt state1 (whileBody decl)
                    go (iterations + 1) steppedState decl
                VBool False -> pure state
                _ -> Left (evaluatorDiagnostic state1 "while condition must evaluate to a boolean")
