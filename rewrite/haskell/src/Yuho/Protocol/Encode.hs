{-# LANGUAGE OverloadedStrings #-}
module Yuho.Protocol.Encode (encodeResult, diagnosticJson, spanJson, traceJson) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import Yuho.Core.Types
import Yuho.Protocol.Json (J(..), encodeJson)

encodeResult :: KernelResult -> BS.ByteString
encodeResult result = encodeJson (JObj
  [ ("protocol", JStr "yuho.kernel-protocol/v1")
  , ("request_id", JStr (resultRequestId result))
  , ("result_schema", JStr "yuho.kernel-result/v1")
  , ("fragment", JStr "ClosedBooleanBranches-v1")
  , ("input_digest", JStr (resultDigest result))
  , ("status", JStr (statusText (resultStatus result)))
  , ("provision_kind", JStr (kindText (resultProvisionKind result)))
  , ("branches", JArr (map branchJson (resultBranches result)))
  , ("trace", JArr (map traceJson (resultTrace result)))
  , ("diagnostics", JArr (map diagnosticJson (resultDiagnostics result)))
  ]) <> BS.singleton 10

branchJson :: Branch -> J
branchJson branch = JObj
  [ ("id", JStr (branchId branch))
  , ("path", strings (branchPath branch))
  , ("status", JStr (boolText (branchValue branch)))
  , ("trace_ids", strings (branchTraceIds branch))
  ]

traceJson :: Trace -> J
traceJson trace = JObj
  [ ("branch", JStr (traceBranch trace))
  , ("id", JStr (traceId trace))
  , ("kind", JStr (traceKind trace))
  , ("path", strings (tracePath trace))
  , ("span", spanJson (traceSpan trace))
  , ("value", JStr (boolText (traceValue trace)))
  , ("children", strings (traceChildren trace))
  ]

diagnosticJson :: Diagnostic -> J
diagnosticJson value = JObj
  [ ("code", JStr (diagCode value))
  , ("stage", JStr (diagStage value))
  , ("severity", JStr (diagSeverity value))
  , ("path", JStr (diagPath value))
  , ("span", maybe JNull spanJson (diagSpan value))
  , ("parameters", JObj [(key, JStr text) | (key, text) <- diagParameters value])
  ]

spanJson :: Span -> J
spanJson spanValue = JObj
  [ ("start", JNum (toInteger (spanStart spanValue)))
  , ("end", JNum (toInteger (spanEnd spanValue)))
  , ("start_line", JNum (toInteger (spanStartLine spanValue)))
  , ("start_col", JNum (toInteger (spanStartCol spanValue)))
  , ("end_line", JNum (toInteger (spanEndLine spanValue)))
  , ("end_col", JNum (toInteger (spanEndCol spanValue)))
  ]

boolText :: Bool -> Text
boolText True = "true"
boolText False = "false"

statusText :: ResultStatus -> Text
statusText ResultTrue = "true"
statusText ResultFalse = "false"
statusText ResultRejected = "rejected"

kindText :: ProvisionKind -> Text
kindText NoProvision = "none"
kindText Executable = "executable"
kindText DefinitionOnly = "definition_only"

strings :: [Text] -> J
strings = JArr . map JStr
