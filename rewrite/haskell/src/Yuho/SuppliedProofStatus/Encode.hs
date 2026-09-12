{-# LANGUAGE OverloadedStrings #-}
module Yuho.SuppliedProofStatus.Encode
  ( encodeProofResult, encodeProofReject ) where

import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic, ProvisionKind(..), diagnostic)
import Yuho.Exception.Types (ExceptionTrace(..), RawGraph(..))
import Yuho.PenaltySelection.Encode (guardJson, warningJson)
import Yuho.PenaltySelection.Types (PenaltyDeclaration(..))
import Yuho.PenaltyTerms.Encode (termJson)
import Yuho.Protocol.Encode (diagnosticJson, spanJson)
import Yuho.Protocol.Json (J(..), encodeJson)
import Yuho.SuppliedProofStatus.Types
import Yuho.TypedFacts.Types (Metadata(..), Provenance(..))

encodeProofResult :: ValidatedProof -> ProofResult -> ProofSelection
  -> Either Diagnostic BS.ByteString
encodeProofResult validated result selection = do
  rules <- traverse (ruleJson validated) (proofResultRules result)
  selected <- traverse (selectedJson validated) (proofSelected selection)
  pure (line (common (validatedProofRequest validated) (proofResultRoot result)
    (satisfactionText (proofResultStatus result)) rules [] selected
    (map occurrenceJson (proofSelectionTrace selection))
    (map warningJson (proofSelectionWarnings selection))))

encodeProofReject :: Text -> Text -> Text -> Diagnostic -> BS.ByteString
encodeProofReject identifier digest root issue = line (JObj
  [ ("protocol", JStr "yuho.kernel-protocol/v1")
  , ("request_id", JStr identifier)
  , ("result_schema", JStr "yuho.kernel-result/v1")
  , ("fragment", JStr "SuppliedProofStatus-v1")
  , ("input_digest", JStr digest)
  , ("root_rule", JStr root)
  , ("status", JStr "rejected")
  , ("rules", JArr [])
  , ("diagnostics", JArr [diagnosticJson issue])
  , ("selected_penalties", JArr [])
  , ("penalty_selection_trace", JArr [])
  , ("selection_warnings", JArr [])
  ])

common :: ProofRequest -> Text -> Text -> [J] -> [Diagnostic] -> [J] -> [J]
  -> [J] -> J
common request root status rules issues selected trace warnings = JObj
  [ ("protocol", JStr "yuho.kernel-protocol/v1")
  , ("request_id", JStr (proofRequestId request))
  , ("result_schema", JStr "yuho.kernel-result/v1")
  , ("fragment", JStr "SuppliedProofStatus-v1")
  , ("input_digest", JStr (proofRequestDigest request))
  , ("root_rule", JStr root)
  , ("status", JStr status)
  , ("rules", JArr rules)
  , ("diagnostics", JArr (map diagnosticJson issues))
  , ("selected_penalties", JArr selected)
  , ("penalty_selection_trace", JArr trace)
  , ("selection_warnings", JArr warnings)
  ]

ruleJson :: ValidatedProof -> ProofRule -> Either Diagnostic J
ruleJson validated rule = do
  observations <- traverse (observation validated rule)
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

branchJson :: ProofBranch -> J
branchJson branch = JObj
  [ ("id", JStr (proofBranchId branch))
  , ("path", strings (proofBranchPath branch))
  , ("status", JStr (satisfactionText (proofBranchStatus branch)))
  , ("reason", JStr (reasonText (proofBranchReason branch)))
  , ("trace_ids", strings (proofBranchTraceIds branch))
  , ("exceptions", JArr (map exceptionJson (proofBranchGuards branch)))
  , ("applicable_exceptions", strings (proofBranchApplicable branch))
  ]

traceJson :: ProofTrace -> J
traceJson trace = JObj
  [ ("branch", JStr (proofTraceBranch trace))
  , ("id", JStr (proofTraceId trace))
  , ("kind", JStr (proofTraceKind trace))
  , ("path", strings (proofTracePath trace))
  , ("span", spanJson (proofTraceSpan trace))
  , ("value", JStr (satisfactionText (proofTraceStatus trace)))
  , ("children", strings (proofTraceChildren trace))
  ]

exceptionJson :: ExceptionTrace -> J
exceptionJson trace = JObj
  [ ("id", JStr (exceptionTraceId trace))
  , ("source_id", JStr (exceptionTraceSource trace))
  , ("span", spanJson (exceptionTraceSpan trace))
  , ("target_rule", JStr (exceptionTraceTarget trace))
  , ("target_status", JStr (satisfactionText (exceptionTraceTargetStatus trace)))
  , ("guard_status", JStr (satisfactionText (exceptionTraceGuardStatus trace)))
  , ("applicable", JBool (exceptionTraceFired trace))
  ]

observation :: ValidatedProof -> ProofRule -> ProofTrace -> Either Diagnostic J
observation validated rule trace = do
  let request = validatedProofRequest validated
      leaf = proofTraceId trace
  binding <- case Map.lookup leaf (rawFacts (proofRawGraph request)) of
    Just found -> pure found
    Nothing -> internal ("/facts/" <> leaf) "validated proof binding missing"
  if projection (suppliedStatus binding) == proofTraceStatus trace then pure () else
    internal ("/facts/" <> leaf) "supplied status projection changed during evaluation"
  branchPath <- case [proofBranchPath branch | branch <- proofRuleBranches rule
    , proofBranchId branch == proofTraceBranch trace] of
    [found] -> pure found
    _ -> internal ("/facts/" <> leaf) "evaluated branch path missing"
  let declaration = Map.lookup leaf (proofDeclarations request)
      checked field = case declaration of
        Just metadata | field metadata -> "matched"
        _ -> "not_declared"
      burdenCheck = checked (maybe False (const True) . metadataBurden)
      standardCheck = checked (maybe False (const True) . metadataStandard)
      provenance = maybe [] (\item -> [("provenance", provenanceJson item)])
        (statusProvenance binding)
  pure (JObj
    ([ ("rule_id", JStr (proofRuleId rule))
    , ("branch_id", JStr (proofTraceBranch trace))
    , ("branch_path", strings branchPath)
    , ("leaf_id", JStr leaf)
    , ("proof_status", suppliedStatusJson (suppliedStatus binding))
    , ("satisfaction", JStr (satisfactionText (proofTraceStatus trace)))
    , ("status_source", sourceJson (statusSource binding))
    , ("burden_check", JStr burdenCheck)
    , ("standard_check", JStr standardCheck)
    ] ++ provenance))

sourceJson :: StatusSource -> J
sourceJson source = JObj
  [ ("assignment_id", JStr (assignmentId source))
  , ("source_id", JStr (assignmentSourceId source))
  , ("span", spanJson (assignmentSpan source))
  , ("origin", JStr (case assignmentOrigin source of
      ExternalAssertion -> "external_assertion"
      SyntheticFixture -> "synthetic_fixture"))
  , ("issuer_label", JStr (assignmentIssuer source))
  ]

provenanceJson :: Provenance -> J
provenanceJson item = JObj (concat
  [ maybe [] (\value -> [("source_label", JStr value)]) (provenanceSourceLabel item)
  , maybe [] (\value -> [("recorded_date", JStr value)]) (provenanceRecordedDate item)
  , maybe [] (\value -> [("jurisdiction", JStr value)]) (provenanceJurisdiction item)
  ])

selectedJson :: ValidatedProof -> ProofSelected -> Either Diagnostic J
selectedJson validated (ProofSelected declaration supports) = do
  term <- case Map.lookup (penaltyId declaration) (validatedProofTerms validated) of
    Just found -> pure found
    Nothing -> internal (penaltyPointer declaration) "validated selected term missing"
  pure (JObj
    [ ("penalty_id", JStr (penaltyId declaration))
    , ("source_id", JStr (penaltySource declaration))
    , ("span", spanJson (penaltySpan declaration))
    , ("declaring_provision_path", strings (penaltyPath declaration))
    , ("declaration_index", JNum (toInteger (penaltyIndex declaration)))
    , ("guard", guardJson (penaltyGuard declaration))
    , ("supporting_branches", JArr (map supportJson supports))
    , ("term", termJson term)
    ])

supportJson :: ProofSupport -> J
supportJson support = JObj
  [ ("branch_id", JStr (proofSupportBranch support))
  , ("path", strings (proofSupportPath support))
  , ("origin", JStr (originText (proofSupportInherited support)))
  , ("guard_result", maybe JNull (JStr . satisfactionText) (proofSupportGuard support))
  ]

occurrenceJson :: ProofOccurrence -> J
occurrenceJson occurrence =
  let declaration = proofOccurrenceDeclaration occurrence in JObj
  [ ("penalty_id", JStr (penaltyId declaration))
  , ("source_id", JStr (penaltySource declaration))
  , ("span", spanJson (penaltySpan declaration))
  , ("branch_id", JStr (proofOccurrenceBranch occurrence))
  , ("branch_path", strings (proofOccurrencePath occurrence))
  , ("origin", JStr (originText (proofOccurrenceInherited occurrence)))
  , ("branch_status", JStr (satisfactionText (proofOccurrenceStatus occurrence)))
  , ("branch_reason", JStr (reasonText (proofOccurrenceReason occurrence)))
  , ("guard_result", JStr (maybe "not_evaluated" satisfactionText
      (proofOccurrenceGuard occurrence)))
  , ("result", JStr (proofOccurrenceResult occurrence))
  ]

reasonText :: ProofReason -> Text
reasonText ProofSatisfied = "satisfied"
reasonText ProofRequirementsNotSatisfied = "requirements_not_satisfied"
reasonText ProofRequirementsUnresolved = "requirements_unresolved"
reasonText ProofDefeated = "defeated"
reasonText ProofExceptionUnresolved = "exception_unresolved"

originText :: Bool -> Text
originText True = "inherited"
originText False = "direct"

strings :: [Text] -> J
strings = JArr . map JStr

line :: J -> BS.ByteString
line value = encodeJson value <> BS.singleton 10

internal :: Text -> Text -> Either Diagnostic a
internal pointer reason = Left (diagnostic "KERR001" "evaluate" pointer Nothing
  [("reason", reason)])
