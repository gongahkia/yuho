{-# LANGUAGE OverloadedStrings #-}
module Yuho.Presumption.Validate (validatePresumptionRequest) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic, diagnostic)
import Yuho.Exception.Types (RawGraph(..))
import Yuho.Presumption.Resolve (referencedLeaves, resolveGraph)
import Yuho.Presumption.Types
import Yuho.SuppliedProofStatus.Types (ProofRequest(..))
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)

validatePresumptionRequest :: PresumptionRequest
  -> Either Diagnostic ValidatedPresumption
validatePresumptionRequest request = do
  base <- validateProofRequest (presumptionBase request)
  let rules = presumptionRules request
      leaves = Map.keysSet (rawFacts (proofRawGraph (presumptionBase request)))
      prior = Set.fromList (presumptionPriorIds request)
  _ <- foldM (validateOne leaves prior) Set.empty rules
  targets <- resolveGraph rules
  pure (ValidatedPresumption base rules targets)

validateOne :: Set Text -> Set Text -> Set Text -> Registration
  -> Either Diagnostic (Set Text)
validateOne leaves prior seen item = do
  let identifier = registrationId item
      pointer = registrationPointer item
  if Set.member identifier prior || Set.member identifier seen then
    Left (diagnostic "KINV002" "validate" (pointer <> "/presumption_id")
      (Just (registrationSpan item)) [("id", identifier)]) else pure ()
  if Set.member (registrationTarget item) leaves then pure () else
    missing (pointer <> "/target_leaf_id") (registrationTarget item)
  mapM_ (checkCondition leaves (pointer <> "/trigger"))
    (referencedLeaves (registrationTrigger item))
  mapM_ (checkCondition leaves (pointer <> "/rebuttal"))
    (referencedLeaves (registrationRebuttal item))
  pure (Set.insert identifier seen)

checkCondition :: Set Text -> Text -> Text -> Either Diagnostic ()
checkCondition leaves pointer identifier = if Set.member identifier leaves
  then pure () else missing pointer identifier

missing :: Text -> Text -> Either Diagnostic a
missing pointer identifier = Left (diagnostic "KINV005" "validate" pointer
  Nothing [("leaf_id", identifier)])
