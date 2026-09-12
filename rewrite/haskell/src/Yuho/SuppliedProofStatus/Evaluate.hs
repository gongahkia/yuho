{-# LANGUAGE OverloadedStrings #-}
module Yuho.SuppliedProofStatus.Evaluate
  ( evaluateProof, evaluateProofReference, allStatus, anyStatus ) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Data.Text (Text)
import Yuho.Core.Types
  ( Diagnostic, Provision(..), ProvisionKind(..), Requirement(..)
  , RequirementKind(..), diagnostic )
import Yuho.Exception.Evaluate (aggregateBranches)
import Yuho.Exception.Types
  ( ExceptionTrace(..), RawException(..), Truth(..) )
import Yuho.Exception.Validate
  ( ValidatedGraph, RuleKey, ResolvedException, ResolvedRule, exceptionDetails
  , exceptionTarget, orderedKeys, rootKey, ruleExceptionsFor, ruleFor
  , ruleKeyText, ruleProgram, ruleSource, sharedFacts )
import Yuho.Kernel.Evaluate (branches)
import Yuho.SuppliedProofStatus.Types

allStatus :: [Truth] -> Truth
allStatus values
  | FalseValue `elem` values = FalseValue
  | UnresolvedValue `elem` values = UnresolvedValue
  | otherwise = TrueValue

anyStatus :: [Truth] -> Truth
anyStatus values
  | TrueValue `elem` values = TrueValue
  | UnresolvedValue `elem` values = UnresolvedValue
  | otherwise = FalseValue

evaluateProof :: ValidatedProof -> Either Diagnostic ProofResult
evaluateProof = evaluateWithMemo True

evaluateProofReference :: ValidatedProof -> Either Diagnostic ProofResult
evaluateProofReference = evaluateWithMemo False

evaluateWithMemo :: Bool -> ValidatedProof -> Either Diagnostic ProofResult
evaluateWithMemo memoize validated = do
  let graph = validatedProofGraph validated
  (root, results) <- evaluateRule memoize graph (rootKey graph) Map.empty
  let ordered = [result | key <- orderedKeys graph, Just result <- [Map.lookup key results]]
  pure (ProofResult (ruleKeyText (rootKey graph)) (proofRuleStatus root) ordered)

evaluateRule :: Bool -> ValidatedGraph StatusBinding -> RuleKey
  -> Map RuleKey ProofRule -> Either Diagnostic (ProofRule, Map RuleKey ProofRule)
evaluateRule memoize graph key prior =
  case if memoize then Map.lookup key prior else Nothing of
    Just cached -> Right (cached, prior)
    Nothing -> case ruleFor graph key of
      Nothing -> internal "/registry" "validated target rule missing"
      Just rule -> do
        (reversed, finalMemo) <- foldM (evaluateBranch memoize graph rule)
          ([], prior) (branches (ruleProgram rule) [])
        let pairs = reverse reversed
            branchResults = map fst pairs
            traces = concatMap snd pairs
            kind = if null branchResults then DefinitionOnly else Executable
            status = aggregateBranches (map proofBranchStatus branchResults)
            result = ProofRule (ruleKeyText key) (ruleSource rule)
              status kind branchResults traces
        pure (result, Map.insert key result finalMemo)

evaluateBranch :: Bool -> ValidatedGraph StatusBinding -> ResolvedRule
  -> ([(ProofBranch, [ProofTrace])], Map RuleKey ProofRule)
  -> (Provision, [Requirement])
  -> Either Diagnostic ([(ProofBranch, [ProofTrace])], Map RuleKey ProofRule)
evaluateBranch memoize graph rule (reversed, prior) (provision, requirements) = do
  evaluated <- traverse (evaluateRequirement (sharedFacts graph) (provisionId provision))
    requirements
  let ordinary = allStatus (map fst evaluated)
      traces = concatMap snd evaluated
      traceIds = map proofTraceId traces
      branchId = provisionId provision
      path = provisionPath provision
      simple status reason = ProofBranch branchId path status reason traceIds [] []
  case ordinary of
    FalseValue -> pure ((simple FalseValue ProofRequirementsNotSatisfied, traces) : reversed, prior)
    UnresolvedValue -> pure ((simple UnresolvedValue ProofRequirementsUnresolved, traces) : reversed, prior)
    TrueValue -> do
      (guards, memo) <- foldM (evaluateGuard memoize graph) ([], prior)
        (ruleExceptionsFor rule branchId)
      let ordered = reverse guards
          statuses = map exceptionTraceGuardStatus ordered
          (finalStatus, reason)
            | TrueValue `elem` statuses = (FalseValue, ProofDefeated)
            | UnresolvedValue `elem` statuses = (UnresolvedValue, ProofExceptionUnresolved)
            | otherwise = (TrueValue, ProofSatisfied)
          applicable = [exceptionTraceId item | item <- ordered, exceptionTraceFired item]
          branch = ProofBranch branchId path finalStatus reason traceIds ordered applicable
      pure ((branch, traces) : reversed, memo)

evaluateGuard :: Bool -> ValidatedGraph StatusBinding
  -> ([ExceptionTrace], Map RuleKey ProofRule) -> ResolvedException
  -> Either Diagnostic ([ExceptionTrace], Map RuleKey ProofRule)
evaluateGuard memoize graph (reversed, prior) resolved = do
  (target, memo) <- evaluateRule memoize graph (exceptionTarget resolved) prior
  let details = exceptionDetails resolved
      status = proofRuleStatus target
      trace = ExceptionTrace (rawExceptionId details) (rawExceptionSource details)
        (rawExceptionSpan details) (proofRuleId target) status status
        (status == TrueValue)
  pure (trace : reversed, memo)

evaluateRequirement :: Map Text StatusBinding -> Text -> Requirement
  -> Either Diagnostic (Truth, [ProofTrace])
evaluateRequirement bindings branch requirement = do
  evaluated <- traverse (evaluateRequirement bindings branch)
    (requirementMembers requirement)
  status <- case requirementKind requirement of
    Leaf -> case Map.lookup (requirementId requirement) bindings of
      Just binding -> pure (projection (suppliedStatus binding))
      Nothing -> internal ("/facts/" <> requirementId requirement)
        "validated leaf status binding missing"
    All -> pure (allStatus (map fst evaluated))
    Any -> pure (anyStatus (map fst evaluated))
  let kind = case requirementKind requirement of
        Leaf -> "leaf"; All -> "all"; Any -> "any"
      trace = ProofTrace branch (requirementId requirement) kind
        (requirementPath requirement) (requirementSpan requirement) status
        (map requirementId (requirementMembers requirement))
  pure (status, trace : concatMap snd evaluated)

internal :: Text -> Text -> Either Diagnostic a
internal pointer reason = Left (diagnostic "KERR001" "evaluate" pointer Nothing
  [("reason", reason)])
