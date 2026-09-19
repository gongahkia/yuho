{-# LANGUAGE OverloadedStrings #-}
module Yuho.Presumption.Decode (decodePresumptionRequest) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Core.Types (Diagnostic, Source, Span(..), diagnostic)
import Yuho.Presumption.Types
import Yuho.Protocol.Decode
  ( asArray, asText, closed, countIds, decodePolicy, decodeSpan, inputDigest
  , invalid, required )
import Yuho.Protocol.Json (J(..), lookupField, objectFields)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Types (ProofRequest(..))
import Yuho.Exception.Types (RawGraph(..))

decodePresumptionRequest :: J -> Either Diagnostic PresumptionRequest
decodePresumptionRequest root = do
  closed "" ["protocol", "request_id", "operation", "input_schema", "fragment"
    , "sources", "policy", "registry", "root_rule", "facts", "presumptions"] root
  values <- required asArray "" "presumptions" root
  (_, maxNodes) <- required (\_ -> decodePolicy) "" "policy" root
  baseValue <- replaceRoot root
  let ordinary = countIds baseValue + sum (map (`countKey` baseValue)
        ["penalty_id", "term_id", "assignment_id"])
      extra = length values + sum (map conditionCount values)
  if ordinary + extra > maxNodes then
    Left (diagnostic "KINV004" "validate" "/presumptions" Nothing
      [("reason", "semantic node limit exceeded")]) else pure ()
  base <- decodeProofRequest baseValue
  rules <- traverse (uncurry (decodeRegistration (rawSources (proofRawGraph base))))
    (zip [0 :: Int ..] values)
  pure (PresumptionRequest (base { proofRequestDigest = inputDigest root })
    rules (semanticIds baseValue))

replaceRoot :: J -> Either Diagnostic J
replaceRoot root = case objectFields root of
  Nothing -> invalid "" "expected object"
  Just fields -> pure (JObj
    [(key, if key == "fragment" then JStr "SuppliedProofStatus-v1" else value)
    | (key, value) <- fields, key /= "presumptions"])

decodeRegistration :: [(Text, Source)] -> Int -> J -> Either Diagnostic Registration
decodeRegistration sources index value = do
  let pointer = "/presumptions/" <> Text.pack (show index)
      unsupported = ["irrebuttable", "burden_shift", "burden_effect"
        , "authority_predicate", "priority"]
  case [key | key <- unsupported, lookupField key value /= Nothing] of
    key : _ -> capability (pointer <> "/" <> key) key
    [] -> pure ()
  closed pointer ["presumption_id", "target_leaf_id", "source_id", "span"
    , "trigger", "rebuttal"] value
  identifier <- required boundedId pointer "presumption_id" value
  target <- required boundedId pointer "target_leaf_id" value
  sourceId <- required boundedId pointer "source_id" value
  source <- case lookup sourceId sources of
    Just found -> pure found
    Nothing -> Left (diagnostic "KINV005" "validate" (pointer <> "/source_id")
      Nothing [("id", sourceId)])
  sourceSpan <- required (decodeSpan source) pointer "span" value
  trigger <- required (decodeCondition source sourceSpan 1) pointer "trigger" value
  rebuttal <- required (decodeCondition source sourceSpan 1) pointer "rebuttal" value
  pure (Registration identifier target sourceId sourceSpan trigger rebuttal pointer)

decodeCondition :: Source -> Span -> Int -> Text -> J -> Either Diagnostic Condition
decodeCondition source owner depth pointer value = do
  if depth > 16 then Left (diagnostic "KINV004" "validate" pointer Nothing
    [("reason", "presumption condition depth exceeds 16")]) else pure ()
  kind <- required asText pointer "kind" value
  if kind `elem` ["leaf_effective", "all_of", "any_of"] then pure () else
    capability (pointer <> "/kind") kind
  sourceSpan <- required (decodeSpan source) pointer "span" value
  if spanStart owner <= spanStart sourceSpan && spanEnd sourceSpan <= spanEnd owner
    then pure () else Left (diagnostic "KINV003" "validate" (pointer <> "/span")
      (Just sourceSpan) [("reason", "condition outside registration span")])
  node <- case kind of
    "leaf_effective" -> do
      closed pointer ["kind", "span", "leaf_id"] value
      EffectiveLeaf <$> required boundedId pointer "leaf_id" value
    "all_of" -> ConditionAll <$> group
    "any_of" -> ConditionAny <$> group
    _ -> capability (pointer <> "/kind") kind
  pure (Condition sourceSpan node)
  where
    group = do
      closed pointer ["kind", "span", "members"] value
      members <- required asArray pointer "members" value
      if length members < 2 then Left (diagnostic "KINV004" "validate"
        (pointer <> "/members") Nothing
        [("reason", "condition group needs at least two members")]) else pure ()
      traverse (\(index, item) -> decodeCondition source owner (depth + 1)
        (pointer <> "/members/" <> Text.pack (show index)) item)
        (zip [0 :: Int ..] members)

boundedId :: Text -> J -> Either Diagnostic Text
boundedId pointer value = do
  item <- asText pointer value
  if Text.null item || BS.length (Encoding.encodeUtf8 item) > 128
    then invalid pointer "empty or overlong ID" else pure item

capability :: Text -> Text -> Either Diagnostic a
capability pointer kind = Left (diagnostic "KCAP001" "capability" pointer Nothing
  [("kind", kind)])

conditionCount :: J -> Int
conditionCount value = case value of
  JObj fields -> sum [count item | (key, item) <- fields
    , key == "trigger" || key == "rebuttal"]
  _ -> 0
  where
    count node = 1 + case lookupField "members" node of
      Just (JArr members) -> sum (map count members)
      _ -> 0

countKey :: Text -> J -> Int
countKey wanted value = case value of
  JObj fields -> length [() | (key, _) <- fields, key == wanted]
    + sum (map (countKey wanted . snd) fields)
  JArr items -> sum (map (countKey wanted) items)
  _ -> 0

semanticIds :: J -> [Text]
semanticIds value = case value of
  JObj fields -> [identifier | (key, JStr identifier) <- fields
    , key `elem` ["id", "penalty_id", "term_id", "assignment_id"]]
    ++ concatMap (semanticIds . snd) fields
  JArr items -> concatMap semanticIds items
  _ -> []
