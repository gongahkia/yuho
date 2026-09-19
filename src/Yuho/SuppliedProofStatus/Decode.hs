{-# LANGUAGE OverloadedStrings #-}
module Yuho.SuppliedProofStatus.Decode (decodeProofRequest) where

import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Core.Types (Diagnostic(..), Source, diagnostic)
import Yuho.Exception.Decode (decodeGraphWith)
import Yuho.PenaltySelection.Decode (extractPenalties)
import Yuho.PenaltyTerms.Decode (extractTerms)
import Yuho.Protocol.Decode
  ( asArray, asText, closed, countIds, decodePolicy, decodeSpan, inputDigest
  , invalid, required )
import Yuho.Protocol.Json (J(..), lookupField, objectFields)
import Yuho.SuppliedProofStatus.Types
import Yuho.TypedFacts.Decode (decodeMetadataFields, decodeProvenance, stripDeclarations)

decodeProofRequest :: J -> Either Diagnostic ProofRequest
decodeProofRequest root = do
  closed "" ["protocol", "request_id", "operation", "input_schema", "fragment"
    , "sources", "policy", "registry", "root_rule", "facts"] root
  (_, maxNodes) <- required (\_ -> decodePolicy) "" "policy" root
  if countIds root + sum (map (`countKey` root)
      ["penalty_id", "term_id", "assignment_id"]) > maxNodes
    then Left (diagnostic "KINV004" "validate" "/registry" Nothing
      [("reason", "semantic node limit exceeded")]) else pure ()
  (withoutTerms, terms) <- extractTerms root
  (withoutPenalties, penalties) <- extractPenalties withoutTerms
  registry <- required asArray "" "registry" withoutPenalties
  (stripped, declarations) <- stripDeclarations registry
  transformed <- replace withoutPenalties
    [("fragment", JStr "AcyclicGuardedExceptions-v1"), ("registry", JArr stripped)]
  (identifier, graph) <- decodeGraphWith decodeBindings transformed
  pure (ProofRequest identifier (inputDigest root) graph
    (Map.fromList (concat declarations)) penalties terms)

decodeBindings :: [(Text, Source)] -> J -> Either Diagnostic (Map Text StatusBinding)
decodeBindings sources value = do
  fields <- maybe (invalid "/facts" "expected object") Right (objectFields value)
  pairs <- traverse (\(key, item) -> do
    if Text.null key then invalid "/facts" "empty leaf ID" else pure ()
    binding <- decodeBinding sources ("/facts/" <> key) item
    pure (key, binding)) fields
  pure (Map.fromList pairs)

decodeBinding :: [(Text, Source)] -> Text -> J -> Either Diagnostic StatusBinding
decodeBinding sources pointer value = do
  closed pointer ["proof_status", "status_source", "burden"
    , "standard_of_proof", "provenance"] value
  status <- required decodeStatus pointer "proof_status" value
  source <- required (decodeStatusSource sources) pointer "status_source" value
  metadata <- decodeMetadataFields pointer value
  provenance <- traverse (decodeProvenance (pointer <> "/provenance"))
    (lookupField "provenance" value)
  pure (StatusBinding status source metadata provenance)

decodeStatus :: Text -> J -> Either Diagnostic SuppliedStatus
decodeStatus pointer value = do
  kind <- required asText pointer "kind" value
  case kind of
    "proved" -> closed pointer ["kind"] value >> pure Proved
    "not_proved" -> closed pointer ["kind"] value >> pure NotProved
    "unresolved" -> do
      closed pointer ["kind", "reason"] value
      reason <- required asText pointer "reason" value
      case reason of
        "not_determined" -> pure (Unresolved NotDetermined)
        "external_decision_pending" -> pure (Unresolved ExternalDecisionPending)
        _ -> invalid (pointer <> "/reason") "unknown unresolved reason"
    "presumed" -> deferred "presumed"
    "rebutted" -> deferred "rebutted"
    _ -> invalid (pointer <> "/kind") "unknown proof-status constructor"
  where
    deferred kind = Left (diagnostic "KCAP001" "capability" (pointer <> "/kind")
      Nothing [("kind", kind)])

decodeStatusSource :: [(Text, Source)] -> Text -> J
  -> Either Diagnostic StatusSource
decodeStatusSource sources pointer value = do
  closed pointer ["assignment_id", "source_id", "span", "origin", "issuer_label"] value
  identifier <- required (boundedText 128) pointer "assignment_id" value
  sourceId <- required (boundedText 128) pointer "source_id" value
  issuer <- required (boundedText 256) pointer "issuer_label" value
  originName <- required asText pointer "origin" value
  origin <- case originName of
    "external_assertion" -> pure ExternalAssertion
    "synthetic_fixture" -> pure SyntheticFixture
    _ -> invalid (pointer <> "/origin") "unknown status origin"
  source <- case lookup sourceId sources of
    Just found -> pure found
    Nothing -> Left (diagnostic "KINV010" "validate" (pointer <> "/source_id")
      Nothing [("source_id", sourceId), ("reason", "status source not registered")])
  spanValue <- case required (decodeSpan source) pointer "span" value of
    Right found -> pure found
    Left issue | diagCode issue == "KINV003" ->
      Left (diagnostic "KINV010" "validate" (pointer <> "/span")
        Nothing [("source_id", sourceId), ("reason", "invalid assignment span")])
    Left issue -> Left issue
  pure (StatusSource identifier sourceId spanValue origin issuer)

boundedText :: Int -> Text -> J -> Either Diagnostic Text
boundedText limit pointer value = do
  item <- asText pointer value
  if Text.null item || BS.length (Encoding.encodeUtf8 item) > limit
    then invalid pointer "empty or overlong string" else pure item

replace :: J -> [(Text, J)] -> Either Diagnostic J
replace value replacements = do
  fields <- maybe (invalid "" "expected object") Right (objectFields value)
  pure (JObj [(key, maybe item id (lookup key replacements)) | (key, item) <- fields])

countKey :: Text -> J -> Int
countKey wanted value = case value of
  JObj fields -> length [() | (key, _) <- fields, key == wanted]
    + sum (map (countKey wanted . snd) fields)
  JArr items -> sum (map (countKey wanted) items)
  _ -> 0
