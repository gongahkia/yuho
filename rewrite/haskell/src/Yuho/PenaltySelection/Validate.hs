{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltySelection.Validate (validatePenalties, validatePenaltyStructure) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Core.Types
import Yuho.Exception.Types
import Yuho.Kernel.Evaluate (branches)
import Yuho.Protocol.Decode (decodeSpan)
import Yuho.PenaltySelection.Types
import Yuho.TypedFacts.Types (TypedRequest(..))
import Yuho.TypedFacts.Validate (validateTyped)

maxExpandedOccurrences :: Int
maxExpandedOccurrences = 4096

validatePenalties :: PenaltyRequest -> Either Diagnostic ValidatedPenalties
validatePenalties request = do
  let typed = penaltyTypedRequest request
      raw = exceptionRawGraph (typedExceptionRequest typed)
  validated <- validateTyped typed
  (declarations, rootUses, indexed) <- validatePenaltyStructure raw
    (penaltyRawDeclarations request)
  pure (ValidatedPenalties validated declarations rootUses indexed)

validatePenaltyStructure :: RawGraph a -> [RawPenalty]
  -> Either Diagnostic ([PenaltyDeclaration], [BranchUse], Map Text [BranchUse])
validatePenaltyStructure raw rawDeclarations = do
  _ <- foldM unique (Set.fromList (allSemanticIds raw)) rawDeclarations
  declarations <- traverse (validateDeclaration raw) rawDeclarations
  let byProvision = Map.fromListWith (flip (++))
        [(penaltyProvision item, [item]) | item <- declarations]
  occurrenceCount <- sum <$> traverse (countOccurrences byProvision) (rawRules raw)
  if occurrenceCount > maxExpandedOccurrences
    then Left (diagnostic "KDEC002" "decode" "/registry" Nothing
      [("reason", "expanded penalty occurrences exceed 4096")])
    else pure ()
  allUses <- traverse (ruleUses byProvision) (rawRules raw)
  let indexed = Map.fromList allUses
  mapM_ (validateScope indexed) declarations
  let rootUses = Map.findWithDefault [] (rawRoot raw) indexed
  pure (declarations, rootUses, indexed)

countOccurrences :: Map Text [PenaltyDeclaration] -> RawRule -> Either Diagnostic Int
countOccurrences declarations rule = sum <$> traverse countBranch
  (branches (rawRuleProgram rule) [])
  where
    countBranch (branch, _) = case pathTo (provisionId branch) (rawRuleProgram rule) of
      Nothing -> Left (diagnostic "KERR001" "evaluate" (provisionPointer branch)
        (Just (provisionSpan branch)) [("reason", "branch ancestry missing")])
      Just ancestors -> Right (sum [length (Map.findWithDefault [] (provisionId item)
        declarations) | item <- ancestors])

unique :: Set Text -> RawPenalty -> Either Diagnostic (Set Text)
unique seen item
  | Text.null (rawPenaltyId item) || not ("pen:" `Text.isPrefixOf` rawPenaltyId item)
      || Text.length (rawPenaltyId item) <= 4 =
      Left (diagnostic "KINV004" "validate" (rawPenaltyPointer item <> "/penalty_id")
        Nothing [("reason", "invalid penalty ID")])
  | Set.member (rawPenaltyId item) seen =
      Left (diagnostic "KINV002" "validate" (rawPenaltyPointer item <> "/penalty_id")
        Nothing [("id", rawPenaltyId item)])
  | otherwise = Right (Set.insert (rawPenaltyId item) seen)

validateDeclaration :: RawGraph a -> RawPenalty -> Either Diagnostic PenaltyDeclaration
validateDeclaration raw item = do
  (rule, provision) <- case [(rule, provision)
    | rule <- rawRules raw, provision <- allProvisions (rawRuleProgram rule)
    , rawRuleId rule == rawPenaltyRule item
    , provisionId provision == rawPenaltyProvision item] of
    [found] -> Right found
    _ -> Left (diagnostic "KERR001" "evaluate" (rawPenaltyPointer item) Nothing
      [("reason", "decoded provision missing after validation")])
  source <- case lookup (rawPenaltySource item) (rawSources raw) of
    Just found -> Right found
    Nothing -> Left (diagnostic "KINV005" "validate"
      (rawPenaltyPointer item <> "/source_id") Nothing
      [("id", rawPenaltySource item)])
  if rawPenaltySource item == rawRuleSource rule then pure () else
    Left (diagnostic "KINV004" "validate" (rawPenaltyPointer item <> "/source_id")
      Nothing [("reason", "penalty source differs from declaring rule")])
  spanValue <- decodeSpan source (rawPenaltyPointer item <> "/span")
    (rawPenaltySpanJson item)
  let parent = provisionSpan provision
  if spanStart parent <= spanStart spanValue && spanEnd spanValue <= spanEnd parent
    then pure () else Left (diagnostic "KINV003" "validate"
      (rawPenaltyPointer item <> "/span") (Just spanValue) [])
  pure (PenaltyDeclaration (rawPenaltyId item) (rawPenaltyRule item)
    (provisionId provision) (provisionPath provision) (rawPenaltySource item)
    spanValue (rawPenaltyGuard item) (rawPenaltyIndex item) (rawPenaltyPointer item))

ruleUses :: Map Text [PenaltyDeclaration] -> RawRule
  -> Either Diagnostic (Text, [BranchUse])
ruleUses declarations rule = do
  uses <- traverse makeUse (branches (rawRuleProgram rule) [])
  pure (rawRuleId rule, uses)
  where
    makeUse (branch, requirements) = do
      ancestors <- case pathTo (provisionId branch) (rawRuleProgram rule) of
        Just found -> Right found
        Nothing -> Left (diagnostic "KERR001" "evaluate" (provisionPointer branch)
          (Just (provisionSpan branch)) [("reason", "branch ancestry missing")])
      let inherited = concatMap (\item -> Map.findWithDefault [] (provisionId item) declarations)
            ancestors
      pure (BranchUse (rawRuleId rule) (provisionId branch) (provisionPath branch)
        (concatMap leafIds requirements) inherited)

validateScope :: Map Text [BranchUse] -> PenaltyDeclaration -> Either Diagnostic ()
validateScope _ declaration | penaltyGuard declaration == Unguarded = Right ()
validateScope indexed declaration = case penaltyGuard declaration of
  Unguarded -> Right ()
  LeafTrue leaf -> do
    let uses = [use | use <- Map.findWithDefault [] (penaltyRule declaration) indexed
          , declaration `elem` useDeclarations use]
        bad = [use | use <- uses, leaf `notElem` useLeaves use]
    case (uses, bad) of
      ([], _) -> reject "no executable descendant contains guard" "absent"
      (_, first:_) -> reject "guard outside inherited branch requirements"
        (useBranch first)
      _ -> Right ()
    where
      reject reason affectedBranch = Left (diagnostic "KINV008" "validate"
        (penaltyPointer declaration <> "/guard/leaf_id")
        (Just (penaltySpan declaration))
        [("penalty_id", penaltyId declaration), ("leaf_id", leaf)
        , ("rule", penaltyRule declaration), ("branch_id", affectedBranch)
        , ("reason", reason)])

pathTo :: Text -> Provision -> Maybe [Provision]
pathTo wanted current
  | provisionId current == wanted = Just [current]
  | otherwise = case [current : path | child <- provisionChildren current
      , Just path <- [pathTo wanted child]] of
      first : _ -> Just first
      [] -> Nothing

allProvisions :: Provision -> [Provision]
allProvisions current = current : concatMap allProvisions (provisionChildren current)

allSemanticIds :: RawGraph a -> [Text]
allSemanticIds raw = map fst (rawSources raw) ++ concatMap ruleIds (rawRules raw)
  where
    ruleIds rule = rawRuleId rule : map rawExceptionId (rawRuleExceptions rule)
      ++ concatMap provisionIds (allProvisions (rawRuleProgram rule))
    provisionIds provision = provisionId provision
      : concatMap requirementIds (provisionRequirements provision)
    requirementIds requirement = requirementId requirement
      : concatMap requirementIds (requirementMembers requirement)

leafIds :: Requirement -> [Text]
leafIds requirement = case requirementKind requirement of
  Leaf -> [requirementId requirement]
  All -> concatMap leafIds (requirementMembers requirement)
  Any -> concatMap leafIds (requirementMembers requirement)
