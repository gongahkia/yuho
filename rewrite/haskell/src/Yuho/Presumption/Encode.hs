{-# LANGUAGE OverloadedStrings #-}
module Yuho.Presumption.Encode
  ( encodePresumptionResult, encodePresumptionReject ) where

import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic, ProvisionKind(..), diagnostic)
import Yuho.Exception.Types (Truth(..))
import Yuho.PenaltySelection.Encode (warningJson)
import Yuho.Presumption.Types
import Yuho.Protocol.Encode (diagnosticJson, spanJson)
import Yuho.Protocol.Json (J(..), encodeJson)
import Yuho.SuppliedProofStatus.Encode
  ( branchJson, traceJson, observation, selectedJson, occurrenceJson, strings )
import Yuho.SuppliedProofStatus.Types

encodePresumptionResult :: ValidatedPresumption -> PresumptionResult
  -> ProofResult -> ProofSelection -> Either Diagnostic BS.ByteString
encodePresumptionResult validated presumption result selection = do
  let base = presumptionValidatedBase validated
      request = validatedProofRequest base
  rules <- traverse (ruleJson base presumption) (proofResultRules result)
  selected <- traverse (selectedJson base) (proofSelected selection)
  derivations <- traverse (derivationJson presumption)
    (presumptionDerivations presumption)
  pure (line (JObj
    [ ("protocol", JStr "yuho.kernel-protocol/v1")
    , ("request_id", JStr (proofRequestId request))
    , ("result_schema", JStr "yuho.kernel-result/v1")
    , ("fragment", JStr "RegisteredPresumptionDerivations-v1")
    , ("input_digest", JStr (proofRequestDigest request))
    , ("root_rule", JStr (proofResultRoot result))
    , ("status", JStr (satisfactionText (proofResultStatus result)))
    , ("rules", JArr rules)
    , ("diagnostics", JArr [])
    , ("selected_penalties", JArr selected)
    , ("penalty_selection_trace", JArr
        (map occurrenceJson (proofSelectionTrace selection)))
    , ("selection_warnings", JArr
        (map warningJson (proofSelectionWarnings selection)))
    , ("presumption_derivations", JArr derivations)
    ]))

encodePresumptionReject :: Text -> Text -> Text -> Diagnostic -> BS.ByteString
encodePresumptionReject identifier digest root issue = line (JObj
  [ ("protocol", JStr "yuho.kernel-protocol/v1")
  , ("request_id", JStr identifier)
  , ("result_schema", JStr "yuho.kernel-result/v1")
  , ("fragment", JStr "RegisteredPresumptionDerivations-v1")
  , ("input_digest", JStr digest)
  , ("root_rule", JStr root)
  , ("status", JStr "rejected")
  , ("rules", JArr [])
  , ("diagnostics", JArr [diagnosticJson issue])
  , ("selected_penalties", JArr [])
  , ("penalty_selection_trace", JArr [])
  , ("selection_warnings", JArr [])
  , ("presumption_derivations", JArr [])
  ])

ruleJson :: ValidatedProof -> PresumptionResult -> ProofRule
  -> Either Diagnostic J
ruleJson base presumption rule = do
  observations <- traverse (proofObservation base presumption rule)
    [trace | trace <- proofRuleTrace rule, proofTraceKind trace == "leaf"]
  pure (JObj
    [ ("id", JStr (proofRuleId rule))
    , ("source_id", JStr (proofRuleSource rule))
    , ("status", JStr (satisfactionText (proofRuleStatus rule)))
    , ("provision_kind", JStr (case proofRuleKind rule of
        Executable -> "executable"; DefinitionOnly -> "definition_only"
        NoProvision -> "none"))
    , ("branches", JArr (map branchJson (proofRuleBranches rule)))
    , ("trace", JArr (map traceJson (proofRuleTrace rule)))
    , ("proof_observations", JArr observations)
    ])

proofObservation :: ValidatedProof -> PresumptionResult -> ProofRule -> ProofTrace
  -> Either Diagnostic J
proofObservation base presumption rule trace = do
  let leaf = proofTraceId trace
  resolution <- case Map.lookup leaf (presumptionResolutions presumption) of
    Just found -> pure found
    Nothing -> internal ("/facts/" <> leaf) "effective leaf resolution missing"
  if proofTraceStatus trace == leafEffective resolution then pure () else
    internal ("/facts/" <> leaf) "effective leaf differs from rule trace"
  original <- observation base rule (trace { proofTraceStatus = leafDirect resolution })
  let activeIds = [registrationId (derivationRegistration route)
        | route <- leafRoutes resolution, derivationState route == Active]
      unresolvedIds = if leafDirect resolution == FalseValue
        && leafEffective resolution == UnresolvedValue
        then [registrationId (derivationRegistration route)
          | route <- leafRoutes resolution, derivationState route == RouteUnresolved]
        else []
  case original of
    JObj fields -> pure (JObj
      ([ (key, if key == "satisfaction"
          then JStr (satisfactionText (leafEffective resolution)) else value)
       | (key, value) <- fields]
       ++ [("direct_satisfaction", JStr (satisfactionText (leafDirect resolution)))
          , ("effective_satisfaction", JStr (satisfactionText (leafEffective resolution)))
          , ("active_presumption_ids", strings activeIds)
          , ("unresolved_presumption_ids", strings unresolvedIds)]))
    _ -> internal ("/facts/" <> leaf) "proof observation is not an object"

derivationJson :: PresumptionResult -> Derivation -> Either Diagnostic J
derivationJson result route = do
  let registration = derivationRegistration route
  resolution <- case Map.lookup (registrationTarget registration)
      (presumptionResolutions result) of
    Just found -> pure found
    Nothing -> internal (registrationPointer registration) "target resolution missing"
  pure (JObj
    [ ("presumption_id", JStr (registrationId registration))
    , ("target_leaf_id", JStr (registrationTarget registration))
    , ("source_id", JStr (registrationSource registration))
    , ("span", spanJson (registrationSpan registration))
    , ("trigger", conditionJson (derivationTrigger route))
    , ("rebuttal", conditionJson (derivationRebuttal route))
    , ("trigger_value", JStr (satisfactionText (conditionTraceValue
        (derivationTrigger route))))
    , ("rebuttal_value", JStr (satisfactionText (conditionTraceValue
        (derivationRebuttal route))))
    , ("state", JStr (stateText (derivationState route)))
    , ("target_direct_satisfaction", JStr (satisfactionText (leafDirect resolution)))
    , ("target_effective_satisfaction", JStr (satisfactionText (leafEffective resolution)))
    ])

conditionJson :: ConditionTrace -> J
conditionJson trace = JObj
  [ ("kind", JStr (conditionTraceKind trace))
  , ("span", spanJson (conditionTraceSpan trace))
  , ("leaf_id", maybe JNull JStr (conditionTraceLeaf trace))
  , ("value", JStr (satisfactionText (conditionTraceValue trace)))
  , ("children", JArr (map conditionJson (conditionTraceChildren trace)))
  ]

line :: J -> BS.ByteString
line value = encodeJson value <> BS.singleton 10

internal :: Text -> Text -> Either Diagnostic a
internal pointer reason = Left (diagnostic "KERR001" "evaluate" pointer Nothing
  [("reason", reason)])
