{-# LANGUAGE OverloadedStrings #-}
module Yuho.SuppliedProofStatus.Select (selectProofPenalties) where

import Data.Maybe (mapMaybe)
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic, diagnostic)
import Yuho.Exception.Types (BranchReason(..), Truth(..))
import Yuho.PenaltySelection.Select (makeWarnings)
import Yuho.PenaltySelection.Types
  ( BranchUse(..), PenaltyDeclaration(..), PenaltyGuard(..), PenaltyOccurrence(..) )
import Yuho.SuppliedProofStatus.Types

selectProofPenalties :: ValidatedProof -> ProofResult
  -> Either Diagnostic ProofSelection
selectProofPenalties validated result = do
  root <- case [rule | rule <- proofResultRules result
    , proofRuleId rule == proofResultRoot result] of
    [found] -> pure found
    _ -> internal "/root_rule" "evaluated root rule missing"
  let uses = validatedProofRootUses validated
      branches = proofRuleBranches root
  if map useBranch uses == map proofBranchId branches then pure () else
    internal "/registry" "validated branch order differs from evaluation"
  occurrences <- concat <$> traverse (uncurry (selectBranch root)) (zip uses branches)
  let chosen = [item | item <- occurrences, proofOccurrenceResult item == "selected"]
      declarations = [item | item <- validatedProofDeclarations validated
        , penaltyRule item == proofResultRoot result]
      selected = mapMaybe (selectedRecord chosen) declarations
      oldChosen = map toOld chosen
      warnings = makeWarnings (proofResultRoot result) uses declarations oldChosen
  pure (ProofSelection selected occurrences warnings)

selectBranch :: ProofRule -> BranchUse -> ProofBranch
  -> Either Diagnostic [ProofOccurrence]
selectBranch rule use branch = traverse (selectOne rule use branch)
  (useDeclarations use)

selectOne :: ProofRule -> BranchUse -> ProofBranch -> PenaltyDeclaration
  -> Either Diagnostic ProofOccurrence
selectOne rule use branch declaration = do
  (guardResult, outcome) <- case proofBranchReason branch of
    ProofRequirementsNotSatisfied -> pure (Nothing, "branch_requirements_not_satisfied")
    ProofRequirementsUnresolved -> pure (Nothing, "branch_requirements_unresolved")
    ProofDefeated -> pure (Nothing, "branch_exception_defeated")
    ProofExceptionUnresolved -> pure (Nothing, "branch_exception_unresolved")
    ProofSatisfied -> case proofBranchStatus branch of
      TrueValue -> case penaltyGuard declaration of
        Unguarded -> pure (Nothing, "selected")
        LeafTrue leaf -> do
          value <- traceLeaf rule (useBranch use) leaf
          pure (Just value, case value of
            TrueValue -> "selected"
            FalseValue -> "guard_not_satisfied"
            UnresolvedValue -> "guard_unresolved")
      _ -> internal (penaltyPointer declaration)
        "satisfied branch has non-satisfied final status"
  pure (ProofOccurrence declaration (useBranch use) (usePath use)
    (penaltyProvision declaration /= useBranch use)
    (proofBranchStatus branch) (proofBranchReason branch) guardResult outcome)

traceLeaf :: ProofRule -> Text -> Text -> Either Diagnostic Truth
traceLeaf rule branch leaf = case [proofTraceStatus trace | trace <- proofRuleTrace rule
  , proofTraceBranch trace == branch, proofTraceId trace == leaf
  , proofTraceKind trace == "leaf"] of
  [value] -> pure value
  _ -> internal ("/facts/" <> leaf) "resolved penalty guard leaf missing from trace"

selectedRecord :: [ProofOccurrence] -> PenaltyDeclaration -> Maybe ProofSelected
selectedRecord occurrences declaration = case
  [ProofSupport (proofOccurrenceBranch item) (proofOccurrencePath item)
    (proofOccurrenceInherited item) (proofOccurrenceGuard item)
  | item <- occurrences
  , penaltyId (proofOccurrenceDeclaration item) == penaltyId declaration] of
  [] -> Nothing
  supports -> Just (ProofSelected declaration supports)

toOld :: ProofOccurrence -> PenaltyOccurrence
toOld item = PenaltyOccurrence (proofOccurrenceDeclaration item)
  (proofOccurrenceBranch item) (proofOccurrencePath item)
  (proofOccurrenceInherited item) TrueValue Satisfied
  (case proofOccurrenceGuard item of
    Just TrueValue -> Just True
    _ -> Nothing) "selected"

internal :: Text -> Text -> Either Diagnostic a
internal pointer reason = Left (diagnostic "KERR001" "evaluate" pointer Nothing
  [("reason", reason)])
