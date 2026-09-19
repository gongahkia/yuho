{-# LANGUAGE OverloadedStrings #-}
module Yuho.Exception.Encode (encodeExceptionResult, exceptionResultJson, ruleJson) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import Yuho.Core.Types (ProvisionKind(..))
import Yuho.Exception.Types
import Yuho.Protocol.Encode (diagnosticJson, spanJson, traceJson)
import Yuho.Protocol.Json (J(..), encodeJson)

encodeExceptionResult :: ExceptionResult -> BS.ByteString
encodeExceptionResult result = encodeJson (exceptionResultJson result) <> BS.singleton 10

exceptionResultJson :: ExceptionResult -> J
exceptionResultJson result = JObj
  [ ("protocol", JStr "yuho.kernel-protocol/v1")
  , ("request_id", JStr (exceptionResultRequestId result))
  , ("result_schema", JStr "yuho.kernel-result/v1")
  , ("fragment", JStr "AcyclicGuardedExceptions-v1")
  , ("input_digest", JStr (exceptionResultDigest result))
  , ("root_rule", JStr (exceptionResultRoot result))
  , ("status", JStr (case exceptionResultStatus result of
      Rejected -> "rejected"; Judgment value -> truthText value))
  , ("rules", JArr (map ruleJson (exceptionResultRules result)))
  , ("diagnostics", JArr (map diagnosticJson (exceptionResultDiagnostics result)))
  ]

ruleJson :: RuleResult -> J
ruleJson result = JObj
  [ ("id", JStr (ruleResultId result))
  , ("source_id", JStr (ruleResultSource result))
  , ("status", JStr (truthText (ruleResultStatus result)))
  , ("provision_kind", JStr (kindText (ruleResultKind result)))
  , ("branches", JArr (map branchJson (ruleResultBranches result)))
  , ("trace", JArr (map traceJson (ruleResultTrace result)))
  ]

branchJson :: ExceptionBranch -> J
branchJson branch = JObj
  [ ("id", JStr (exceptionBranchId branch))
  , ("path", textArray (exceptionBranchPath branch))
  , ("status", JStr (truthText (exceptionBranchStatus branch)))
  , ("reason", JStr (reasonText (exceptionBranchReason branch)))
  , ("trace_ids", textArray (exceptionBranchTraceIds branch))
  , ("exceptions", JArr (map exceptionJson (exceptionBranchGuards branch)))
  , ("applicable_exceptions", textArray (exceptionBranchApplicable branch))
  ]

exceptionJson :: ExceptionTrace -> J
exceptionJson trace = JObj
  [ ("id", JStr (exceptionTraceId trace))
  , ("source_id", JStr (exceptionTraceSource trace))
  , ("span", spanJson (exceptionTraceSpan trace))
  , ("target_rule", JStr (exceptionTraceTarget trace))
  , ("target_status", JStr (truthText (exceptionTraceTargetStatus trace)))
  , ("guard_status", JStr (truthText (exceptionTraceGuardStatus trace)))
  , ("applicable", JBool (exceptionTraceFired trace))
  ]

textArray :: [Text] -> J
textArray = JArr . map JStr

kindText :: ProvisionKind -> Text
kindText Executable = "executable"
kindText DefinitionOnly = "definition_only"
kindText NoProvision = "none"

reasonText :: BranchReason -> Text
reasonText Satisfied = "satisfied"
reasonText RequirementsFailed = "requirements_failed"
reasonText Defeated = "defeated"
reasonText GuardUnresolved = "guard_unresolved"
