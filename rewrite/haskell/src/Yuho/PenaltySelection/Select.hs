{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltySelection.Select (selectPenalties, overlapPaths) where

import Data.List (nub)
import Data.Maybe (mapMaybe)
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic, Trace(..), diagnostic)
import Yuho.Exception.Types
import Yuho.PenaltySelection.Types

selectPenalties :: ValidatedPenalties -> ExceptionResult -> Either Diagnostic Selection
selectPenalties validated result = do
  root <- case [rule | rule <- exceptionResultRules result
    , ruleResultId rule == exceptionResultRoot result] of
    [found] -> Right found
    _ -> internal "/root_rule" "evaluated root rule missing"
  let uses = validatedRootUses validated
      branches = ruleResultBranches root
  if map useBranch uses == map exceptionBranchId branches then pure () else
    internal "/registry" "validated branch order differs from evaluation"
  occurrences <- concat <$> traverse (uncurry (selectBranch root)) (zip uses branches)
  let chosen = [item | item <- occurrences, occurrenceResult item == "selected"]
      declarations = [declaration | declaration <- validatedDeclarations validated
        , penaltyRule declaration == exceptionResultRoot result]
      selected = mapMaybe (selectedRecord chosen) declarations
      warnings = makeWarnings (exceptionResultRoot result) uses declarations chosen
  pure (Selection selected occurrences warnings)

selectBranch :: RuleResult -> BranchUse -> ExceptionBranch
  -> Either Diagnostic [PenaltyOccurrence]
selectBranch rule use branch = traverse (selectOne rule use branch)
  (useDeclarations use)

selectOne :: RuleResult -> BranchUse -> ExceptionBranch -> PenaltyDeclaration
  -> Either Diagnostic PenaltyOccurrence
selectOne rule use branch declaration = do
  (guardValue, outcome) <- case exceptionBranchReason branch of
    RequirementsFailed -> Right (Nothing, "branch_requirements_false")
    Defeated -> Right (Nothing, "branch_exception_defeated")
    GuardUnresolved -> Right (Nothing, "branch_unresolved")
    Satisfied -> case exceptionBranchStatus branch of
      TrueValue -> case penaltyGuard declaration of
        Unguarded -> Right (Nothing, "selected")
        LeafTrue leaf -> do
          value <- traceLeaf rule (useBranch use) leaf
          Right (Just value, if value then "selected" else "guard_false")
      _ -> internal (penaltyPointer declaration)
        "satisfied branch has non-true final status"
  pure (PenaltyOccurrence declaration (useBranch use) (usePath use)
    (penaltyProvision declaration /= useBranch use)
    (exceptionBranchStatus branch) (exceptionBranchReason branch) guardValue outcome)

traceLeaf :: RuleResult -> Text -> Text -> Either Diagnostic Bool
traceLeaf rule branch leaf = case [traceValue trace | trace <- ruleResultTrace rule
  , traceBranch trace == branch, traceId trace == leaf, traceKind trace == "leaf"] of
  [value] -> Right value
  _ -> internal ("/facts/" <> leaf) "resolved penalty guard leaf missing from trace"

selectedRecord :: [PenaltyOccurrence] -> PenaltyDeclaration -> Maybe SelectedPenalty
selectedRecord occurrences declaration = case
  [Support (occurrenceBranch item) (occurrencePath item)
    (occurrenceInherited item) (occurrenceGuard item)
  | item <- occurrences, penaltyId (occurrenceDeclaration item) == penaltyId declaration] of
  [] -> Nothing
  supports -> Just (SelectedPenalty declaration supports)

makeWarnings :: Text -> [BranchUse] -> [PenaltyDeclaration]
  -> [PenaltyOccurrence] -> [SelectionWarning]
makeWarnings root uses declarations selected = mapMaybe forProvision provisions
  where
    provisions = nub [penaltyProvision declaration | declaration <- declarations]
    forProvision provision = do
      first <- case [item | item <- declarations, penaltyProvision item == provision] of
        item : _ -> Just item
        [] -> Nothing
      let paths = overlapPaths provision uses selected
          onPaths = [item | item <- selected
            , penaltyProvision (occurrenceDeclaration item) == provision
            , occurrencePath item `elem` paths
            , case penaltyGuard (occurrenceDeclaration item) of
                LeafTrue _ -> True
                Unguarded -> False]
          ids = [penaltyId item | item <- declarations, item `elem`
            map occurrenceDeclaration onPaths]
          guards = nub [leaf | item <- declarations
            , item `elem` map occurrenceDeclaration onPaths
            , LeafTrue leaf <- [penaltyGuard item]]
      if null paths then Nothing else Just (SelectionWarning root provision
        (penaltyPath first) paths ids guards)

-- The pure boundary also covers disjoint-path states that total wire facts do not create.
overlapPaths :: Text -> [BranchUse] -> [PenaltyOccurrence] -> [[Text]]
overlapPaths provision uses selected =
  [usePath use | use <- uses, length (guardsOn (useBranch use)) >= 2]
  where
    guardsOn branch = nub [leaf | item <- selected
      , occurrenceBranch item == branch
      , penaltyProvision (occurrenceDeclaration item) == provision
      , LeafTrue leaf <- [penaltyGuard (occurrenceDeclaration item)]]

internal :: Text -> Text -> Either Diagnostic a
internal pointer reason = Left (diagnostic "KERR001" "evaluate" pointer Nothing
  [("reason", reason)])
