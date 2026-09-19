{-# LANGUAGE OverloadedStrings #-}
module Yuho.CoreYuho.Semantics
  ( evaluateRequirement, allTruth, anyTruth, branchTruth, guardedTruth
  , evaluateGuardedBranch, presumptionState, presumptionEffective
  , selectTemporal ) where

import Data.Map.Strict (Map)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import Yuho.CoreYuho.Types
import Yuho.Exception.Evaluate (aggregateBranches, aggregateGuards)
import Yuho.Exception.Types (Truth(..))
import Yuho.Presumption.Evaluate (combineEffective, deriveState)
import Yuho.Presumption.Types (DerivationState)
import Yuho.SuppliedProofStatus.Evaluate (allStatus, anyStatus)

allTruth :: [CoreTruth] -> CoreTruth
allTruth = allStatus

anyTruth :: [CoreTruth] -> CoreTruth
anyTruth = anyStatus

branchTruth :: [CoreTruth] -> CoreTruth
branchTruth = aggregateBranches

guardedTruth :: [CoreTruth] -> CoreTruth
guardedTruth = fst . aggregateGuards

evaluateGuardedBranch :: CoreTruth -> [CoreTruth] -> CoreTruth
evaluateGuardedBranch ordinary guards = case ordinary of
  TrueValue -> guardedTruth guards
  FalseValue -> FalseValue
  UnresolvedValue -> UnresolvedValue

presumptionState :: CoreTruth -> CoreTruth -> DerivationState
presumptionState = deriveState

presumptionEffective :: CoreTruth -> [DerivationState] -> CoreTruth
presumptionEffective = combineEffective

evaluateRequirement :: Map Text CoreTruth -> CoreRequirement -> Either Text CoreTruth
evaluateRequirement supplied expression = case expression of
  CoreInput identifier _ embedded -> case embedded <|> Map.lookup identifier supplied of
    Just value -> Right value
    Nothing -> Left identifier
  CoreAll _ members -> allTruth <$> traverse (evaluateRequirement supplied) members
  CoreAny _ members -> anyTruth <$> traverse (evaluateRequirement supplied) members
  where
    (<|>) (Just value) _ = Just value
    (<|>) Nothing other = other

selectTemporal :: Integer -> [CoreInterval] -> Either Text CoreInterval
selectTemporal conductDate intervals = case filter contains intervals of
  [selected] -> Right selected
  [] -> Left "gap"
  _ -> Left "overlap"
  where
    contains interval = coreIntervalFrom interval <= conductDate
      && maybe True (conductDate <) (coreIntervalTo interval)
