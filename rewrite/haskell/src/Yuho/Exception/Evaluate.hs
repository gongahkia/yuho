{-# LANGUAGE OverloadedStrings #-}
module Yuho.Exception.Evaluate
  ( evaluateGraph, evaluateGraphReference, aggregateGuards, aggregateBranches ) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Yuho.Core.Types
import Yuho.Exception.Types
import Yuho.Exception.Validate
import Yuho.Kernel.Evaluate (branches, evaluateBranch)

aggregateGuards :: [Truth] -> (Truth, BranchReason)
aggregateGuards guards
  | TrueValue `elem` guards = (FalseValue, Defeated)
  | UnresolvedValue `elem` guards = (UnresolvedValue, GuardUnresolved)
  | otherwise = (TrueValue, Satisfied)

aggregateBranches :: [Truth] -> Truth
aggregateBranches values
  | TrueValue `elem` values = TrueValue
  | UnresolvedValue `elem` values = UnresolvedValue
  | otherwise = FalseValue

evaluateGraph :: ExceptionRequest -> ValidatedGraph -> Either Diagnostic ExceptionResult
evaluateGraph = evaluateWithMemo True

evaluateGraphReference :: ExceptionRequest -> ValidatedGraph -> Either Diagnostic ExceptionResult
evaluateGraphReference = evaluateWithMemo False

evaluateWithMemo :: Bool -> ExceptionRequest -> ValidatedGraph
  -> Either Diagnostic ExceptionResult
evaluateWithMemo memoize request graph = do
  (rootResult, results) <- evaluateRule memoize graph (rootKey graph) Map.empty
  let ordered = [result | key <- orderedKeys graph, Just result <- [Map.lookup key results]]
  pure (ExceptionResult (exceptionRequestId request) (exceptionRequestDigest request)
    (ruleKeyText (rootKey graph)) (Judgment (ruleResultStatus rootResult)) ordered [])

evaluateRule :: Bool -> ValidatedGraph -> RuleKey -> Map RuleKey RuleResult
  -> Either Diagnostic (RuleResult, Map RuleKey RuleResult)
evaluateRule memoize graph key prior =
  case if memoize then Map.lookup key prior else Nothing of
    Just cached -> Right (cached, prior)
    Nothing -> case ruleFor graph key of
      Nothing -> Left (diagnostic "KERR001" "evaluate" "/registry" Nothing
        [("target", ruleKeyText key)])
      Just rule -> do
        let executable = branches (ruleProgram rule) []
        (reversed, finalMemo) <- foldM (evaluateOne memoize graph rule)
          ([], prior) executable
        let branchPairs = reverse reversed
            branchResults = map fst branchPairs
            traces = concatMap snd branchPairs
            kind = if null branchResults then DefinitionOnly else Executable
            status = aggregateBranches (map exceptionBranchStatus branchResults)
            result = RuleResult (ruleKeyText key) (ruleSource rule)
              status kind branchResults traces
        Right (result, Map.insert key result finalMemo)

evaluateOne :: Bool -> ValidatedGraph -> ResolvedRule
  -> ([(ExceptionBranch, [Trace])], Map RuleKey RuleResult)
  -> (Provision, [Requirement])
  -> Either Diagnostic ([(ExceptionBranch, [Trace])], Map RuleKey RuleResult)
evaluateOne memoize graph rule (reversed, prior) (provision, requirements) = do
  (ordinary, traces) <- evaluateBranch (sharedFacts graph) (provision, requirements)
  if not (branchValue ordinary) then do
    let branch = ExceptionBranch (branchId ordinary) (branchPath ordinary)
          FalseValue RequirementsFailed (branchTraceIds ordinary) [] []
    Right ((branch, traces) : reversed, prior)
  else do
    (guards, nextMemo) <- foldM (evaluateGuard memoize graph) ([], prior)
      (ruleExceptionsFor rule (branchId ordinary))
    let ordered = reverse guards
        (status, reason) = aggregateGuards (map exceptionTraceGuardStatus ordered)
        fired = [exceptionTraceId guard | guard <- ordered, exceptionTraceFired guard]
        branch = ExceptionBranch (branchId ordinary) (branchPath ordinary)
          status reason (branchTraceIds ordinary) ordered fired
    Right ((branch, traces) : reversed, nextMemo)

evaluateGuard :: Bool -> ValidatedGraph
  -> ([ExceptionTrace], Map RuleKey RuleResult) -> ResolvedException
  -> Either Diagnostic ([ExceptionTrace], Map RuleKey RuleResult)
evaluateGuard memoize graph (reversed, prior) resolved = do
  (target, nextMemo) <- evaluateRule memoize graph (exceptionTarget resolved) prior
  let details = exceptionDetails resolved
      status = ruleResultStatus target
      trace = ExceptionTrace (rawExceptionId details) (rawExceptionSource details)
        (rawExceptionSpan details) (ruleResultId target) status status
        (status == TrueValue)
  Right (trace : reversed, nextMemo)
