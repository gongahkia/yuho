{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltySelection.Encode
  ( encodeSelection, encodeSelectionReject, selectionResultJson, selectionRejectJson ) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic)
import Yuho.Exception.Encode (exceptionResultJson)
import Yuho.Exception.Types
import Yuho.PenaltySelection.Types
import Yuho.Protocol.Encode (spanJson)
import Yuho.Protocol.Json (J(..), encodeJson)
import Yuho.TypedFacts.Encode (typedResultJson)
import Yuho.TypedFacts.Types (TypedRequest)

encodeSelection :: TypedRequest -> ExceptionResult -> Selection
  -> Either Diagnostic BS.ByteString
encodeSelection typed result selection = line <$> selectionResultJson typed result selection

selectionResultJson :: TypedRequest -> ExceptionResult -> Selection
  -> Either Diagnostic J
selectionResultJson typed result selection = do
  base <- typedResultJson typed result
  pure (setFields base
    [("fragment", JStr "GuardedPenaltySelection-v1")
    , ("selected_penalties", JArr (map selectedJson (selectedPenalties selection)))
    , ("penalty_selection_trace", JArr (map occurrenceJson (selectionTrace selection)))
    , ("selection_warnings", JArr (map warningJson (selectionWarnings selection)))])

encodeSelectionReject :: ExceptionResult -> BS.ByteString
encodeSelectionReject = line . selectionRejectJson

selectionRejectJson :: ExceptionResult -> J
selectionRejectJson result = setFields (exceptionResultJson result)
  [("fragment", JStr "GuardedPenaltySelection-v1")
  , ("selected_penalties", JArr [])
  , ("penalty_selection_trace", JArr [])
  , ("selection_warnings", JArr [])]

selectedJson :: SelectedPenalty -> J
selectedJson (SelectedPenalty declaration supports) = JObj
  [("penalty_id", JStr (penaltyId declaration))
  , ("source_id", JStr (penaltySource declaration))
  , ("span", spanJson (penaltySpan declaration))
  , ("declaring_provision_path", strings (penaltyPath declaration))
  , ("declaration_index", JNum (toInteger (penaltyIndex declaration)))
  , ("guard", guardJson (penaltyGuard declaration))
  , ("supporting_branches", JArr (map supportJson supports))]

supportJson :: Support -> J
supportJson support = JObj
  [("branch_id", JStr (supportBranch support))
  , ("path", strings (supportPath support))
  , ("origin", JStr (originText (supportInherited support)))
  , ("guard_result", maybe JNull JBool (supportGuardResult support))]

occurrenceJson :: PenaltyOccurrence -> J
occurrenceJson occurrence =
  let declaration = occurrenceDeclaration occurrence in JObj
  [("penalty_id", JStr (penaltyId declaration))
  , ("source_id", JStr (penaltySource declaration))
  , ("span", spanJson (penaltySpan declaration))
  , ("branch_id", JStr (occurrenceBranch occurrence))
  , ("branch_path", strings (occurrencePath occurrence))
  , ("origin", JStr (originText (occurrenceInherited occurrence)))
  , ("branch_status", JStr (truthText (occurrenceStatus occurrence)))
  , ("branch_reason", JStr (reasonText (occurrenceReason occurrence)))
  , ("guard_result", JStr (maybe "not_evaluated" boolText (occurrenceGuard occurrence)))
  , ("result", JStr (occurrenceResult occurrence))]

warningJson :: SelectionWarning -> J
warningJson warning = JObj
  [("code", JStr "KSEL001")
  , ("stage", JStr "select_penalties")
  , ("severity", JStr "warning")
  , ("rule_id", JStr (warningRule warning))
  , ("declaring_provision_id", JStr (warningProvision warning))
  , ("declaring_provision_path", strings (warningPath warning))
  , ("overlapping_branch_paths", JArr (map strings (warningBranchPaths warning)))
  , ("penalty_ids", strings (warningPenaltyIds warning))
  , ("guard_leaf_ids", strings (warningGuardIds warning))]

guardJson :: PenaltyGuard -> J
guardJson Unguarded = JObj [("kind", JStr "unguarded")]
guardJson (LeafTrue identifier) = JObj
  [("kind", JStr "leaf_true"), ("leaf_id", JStr identifier)]

reasonText :: BranchReason -> Text
reasonText Satisfied = "satisfied"
reasonText RequirementsFailed = "requirements_failed"
reasonText Defeated = "defeated"
reasonText GuardUnresolved = "guard_unresolved"

originText :: Bool -> Text
originText True = "inherited"
originText False = "direct"

boolText :: Bool -> Text
boolText True = "true"
boolText False = "false"

strings :: [Text] -> J
strings = JArr . map JStr

line :: J -> BS.ByteString
line value = encodeJson value <> BS.singleton 10

setFields :: J -> [(Text, J)] -> J
setFields (JObj fields) replacements = JObj
  ([(key, maybe value id (lookup key replacements)) | (key, value) <- fields]
  ++ [(key, value) | (key, value) <- replacements, key `notElem` map fst fields])
setFields other _ = other
