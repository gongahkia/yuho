{-# LANGUAGE OverloadedStrings #-}
module Yuho.Presumption.Evaluate
  ( evaluatePresumptions, deriveState, combineEffective ) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic, diagnostic)
import Yuho.Exception.Types (RawGraph(..), Truth(..))
import Yuho.Presumption.Types
import Yuho.SuppliedProofStatus.Evaluate (allStatus, anyStatus)
import Yuho.SuppliedProofStatus.Types
  ( ProofRequest(..), ValidatedProof(..), projection, suppliedStatus )

deriveState :: Truth -> Truth -> DerivationState
deriveState FalseValue _ = Inactive
deriveState _ TrueValue = Rebutted
deriveState TrueValue FalseValue = Active
deriveState _ _ = RouteUnresolved

combineEffective :: Truth -> [DerivationState] -> Truth
combineEffective TrueValue _ = TrueValue
combineEffective direct states
  | Active `elem` states = TrueValue
  | direct == UnresolvedValue || RouteUnresolved `elem` states = UnresolvedValue
  | otherwise = FalseValue

evaluatePresumptions :: ValidatedPresumption -> Either Diagnostic PresumptionResult
evaluatePresumptions validated = do
  let facts = rawFacts (proofRawGraph
        (validatedProofRequest (presumptionValidatedBase validated)))
  complete <- foldM (\memo leaf -> snd <$> resolveLeaf validated leaf memo)
    Map.empty (Map.keys facts)
  ordered <- traverse (findDerivation complete) (presumptionValidatedRules validated)
  pure (PresumptionResult (Map.map leafEffective complete) complete ordered)

findDerivation :: Map Text LeafResolution -> Registration -> Either Diagnostic Derivation
findDerivation complete registration = case Map.lookup (registrationTarget registration) complete of
  Nothing -> internal "/presumptions" "validated target leaf resolution missing"
  Just resolved -> case [route | route <- leafRoutes resolved
    , registrationId (derivationRegistration route) == registrationId registration] of
    [route] -> pure route
    _ -> internal (registrationPointer registration) "validated derivation missing"

resolveLeaf :: ValidatedPresumption -> Text -> Map Text LeafResolution
  -> Either Diagnostic (Truth, Map Text LeafResolution)
resolveLeaf validated leaf memo = case Map.lookup leaf memo of
  Just found -> pure (leafEffective found, memo)
  Nothing -> do
    let facts = rawFacts (proofRawGraph
          (validatedProofRequest (presumptionValidatedBase validated)))
    binding <- case Map.lookup leaf facts of
      Just found -> pure found
      Nothing -> internal ("/facts/" <> leaf) "validated leaf binding missing"
    let direct = projection (suppliedStatus binding)
        routes = Map.findWithDefault [] leaf (presumptionByTarget validated)
    (reversed, next) <- foldM (evaluateRoute validated) ([], memo) routes
    let ordered = reverse reversed
        effective = combineEffective direct (map derivationState ordered)
        resolution = LeafResolution direct effective ordered
    pure (effective, Map.insert leaf resolution next)

evaluateRoute :: ValidatedPresumption -> ([Derivation], Map Text LeafResolution)
  -> Registration -> Either Diagnostic ([Derivation], Map Text LeafResolution)
evaluateRoute validated (reversed, prior) registration = do
  (trigger, afterTrigger) <- evaluateCondition validated prior
    (registrationTrigger registration)
  (rebuttal, afterRebuttal) <- evaluateCondition validated afterTrigger
    (registrationRebuttal registration)
  let state = deriveState (conditionTraceValue trigger) (conditionTraceValue rebuttal)
  pure (Derivation registration trigger rebuttal state : reversed, afterRebuttal)

evaluateCondition :: ValidatedPresumption -> Map Text LeafResolution -> Condition
  -> Either Diagnostic (ConditionTrace, Map Text LeafResolution)
evaluateCondition validated prior condition = case conditionKind condition of
  EffectiveLeaf identifier -> do
    (value, next) <- resolveLeaf validated identifier prior
    pure (ConditionTrace "leaf_effective" (Just identifier)
      (conditionSpan condition) value [], next)
  ConditionAll children -> group "all_of" allStatus children
  ConditionAny children -> group "any_of" anyStatus children
  where
    group kind operator children = do
      (reversed, next) <- foldM (\(done, memo) child -> do
        (trace, updated) <- evaluateCondition validated memo child
        pure (trace : done, updated)) ([], prior) children
      let ordered = reverse reversed
      pure (ConditionTrace kind Nothing (conditionSpan condition)
        (operator (map conditionTraceValue ordered)) ordered, next)

internal :: Text -> Text -> Either Diagnostic a
internal pointer reason = Left (diagnostic "KERR001" "evaluate" pointer Nothing
  [("reason", reason)])
