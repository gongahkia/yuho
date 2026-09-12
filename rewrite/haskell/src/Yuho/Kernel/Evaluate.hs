{-# LANGUAGE OverloadedStrings #-}
module Yuho.Kernel.Evaluate (evaluate, branches) where

import Data.Map.Strict (Map)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import Yuho.Core.Types

evaluate :: Request -> Either Diagnostic KernelResult
evaluate request = case requestInput request of
  Validate _ accepted diagnostics _ ->
    Right (KernelResult (requestId request) (requestDigest request)
      (if accepted then ResultTrue else ResultRejected) NoProvision [] [] diagnostics)
  Evaluate _ root facts _ _ -> do
    evaluated <- traverse (evaluateBranch facts) (branches root [])
    let branchResults = map fst evaluated
        traces = concatMap snd evaluated
        kind = if null branchResults then DefinitionOnly else Executable
        status = if any branchValue branchResults then ResultTrue else ResultFalse
    pure (KernelResult (requestId request) (requestDigest request)
         status kind branchResults traces [])

branches :: Provision -> [Requirement] -> [(Provision, [Requirement])]
branches provision inherited =
  let direct = inherited ++ provisionRequirements provision
      descendants = concatMap (\child -> branches child direct) (provisionChildren provision)
  in if not (null descendants) then descendants
     else if null direct then [] else [(provision, direct)]

evaluateBranch :: Map Text Bool -> (Provision, [Requirement]) -> Either Diagnostic (Branch, [Trace])
evaluateBranch facts (provision, requirements) = do
  evaluated <- traverse (evaluateRequirement facts (provisionId provision)) requirements
  let value = all fst evaluated
      traces = concatMap snd evaluated
  pure (Branch (provisionId provision) (provisionPath provision) value (map traceId traces), traces)

evaluateRequirement :: Map Text Bool -> Text -> Requirement -> Either Diagnostic (Bool, [Trace])
evaluateRequirement facts branch requirement = do
  evaluated <- traverse (evaluateRequirement facts branch) (requirementMembers requirement)
  value <- case requirementKind requirement of
    Leaf -> case Map.lookup (requirementId requirement) facts of
      Nothing -> Left (diagnostic "KINV001" "validate"
        ("/facts/" <> requirementId requirement) (Just (requirementSpan requirement))
        [("id", requirementId requirement)])
      Just found -> Right found
    All -> Right (and (map fst evaluated))
    Any -> Right (or (map fst evaluated))
  let kind = case requirementKind requirement of
        Leaf -> "leaf"
        All -> "all"
        Any -> "any"
      edge = Trace branch (requirementId requirement) kind
        (requirementPath requirement) (requirementSpan requirement) value
        (map requirementId (requirementMembers requirement))
  pure (value, edge : concatMap snd evaluated)
