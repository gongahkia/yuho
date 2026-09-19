{-# LANGUAGE OverloadedStrings #-}
module Yuho.SuppliedProofStatus.Validate (validateProofRequest) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic, Provision(..), Requirement(..), diagnostic)
import Yuho.Exception.Types (RawGraph(..), RawRule(..), RawException(..))
import Yuho.Exception.Validate (validateGraph)
import Yuho.PenaltySelection.Types (PenaltyDeclaration(..))
import Yuho.PenaltySelection.Validate (validatePenaltyStructure)
import Yuho.PenaltyTerms.Types (Term(..), TermKind(..))
import Yuho.PenaltyTerms.Validate (validateTermStructure)
import Yuho.SuppliedProofStatus.Types
import Yuho.TypedFacts.Validate (validateBindingMetadata)

validateProofRequest :: ProofRequest -> Either Diagnostic ValidatedProof
validateProofRequest request = do
  let raw = proofRawGraph request
  graph <- validateGraph raw
  validateBindingMetadata raw (proofDeclarations request)
    (rawFacts raw) statusMetadata
  assignments <- foldM uniqueAssignment Set.empty (Map.toList (rawFacts raw))
  (declarations, rootUses, _) <- validatePenaltyStructure raw
    (proofRawPenalties request)
  terms <- validateTermStructure raw declarations (proofRawTerms request)
  let termIds = concatMap allTermIds (Map.elems terms)
      collisions = Set.toList (assignments `Set.intersection`
        Set.fromList (termIds ++ map penaltyId declarations ++ graphIds raw))
  case collisions of
    first : _ -> Left (diagnostic "KINV010" "validate" "/facts" Nothing
      [("assignment_id", first), ("reason", "assignment ID collides with semantic ID")])
    [] -> pure ()
  pure (ValidatedProof request graph declarations rootUses terms)

uniqueAssignment :: Set Text -> (Text, StatusBinding) -> Either Diagnostic (Set Text)
uniqueAssignment seen (leaf, binding) =
  let identifier = assignmentId (statusSource binding)
      pointer = "/facts/" <> leaf <> "/status_source/assignment_id"
  in if Set.member identifier seen then Left (diagnostic "KINV010" "validate"
      pointer Nothing [("assignment_id", identifier), ("reason", "duplicate assignment ID")])
     else pure (Set.insert identifier seen)

allTermIds :: Term -> [Text]
allTermIds term = termId term : case termKind term of
  Atom _ -> []
  AllOf children -> concatMap allTermIds children
  ExactlyOneOf children -> concatMap allTermIds children
  OneOrMoreOf children -> concatMap allTermIds children

graphIds :: RawGraph a -> [Text]
graphIds raw = map fst (rawSources raw) ++ concatMap ruleIds (rawRules raw)
  where
    ruleIds rule = rawRuleId rule : map rawExceptionId (rawRuleExceptions rule)
      ++ provisionIds (rawRuleProgram rule)
    provisionIds provision = provisionId provision
      : concatMap requirementIds (provisionRequirements provision)
      ++ concatMap provisionIds (provisionChildren provision)
    requirementIds requirement = requirementId requirement
      : concatMap requirementIds (requirementMembers requirement)
