{-# LANGUAGE OverloadedStrings #-}
module Yuho.TypedFacts.Encode (encodeTypedResult, encodeTypedReject, typedResultJson) where

import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import Yuho.Core.Types (Diagnostic, Trace(..), diagnostic)
import Yuho.Exception.Encode (exceptionResultJson, ruleJson)
import Yuho.Exception.Types
import Yuho.Protocol.Json (J(..), encodeJson)
import Yuho.TypedFacts.Types

encodeTypedResult :: TypedRequest -> ExceptionResult -> Either Diagnostic BS.ByteString
encodeTypedResult request result =
  (<> BS.singleton 10) . encodeJson <$> typedResultJson request result

typedResultJson :: TypedRequest -> ExceptionResult -> Either Diagnostic J
typedResultJson request result = do
  rules <- traverse (observedRule request) (exceptionResultRules result)
  pure (setFields (exceptionResultJson result)
    [("fragment", JStr "TypedBooleanFacts-v1"), ("rules", JArr rules)])

encodeTypedReject :: ExceptionResult -> BS.ByteString
encodeTypedReject result = encodeJson (setFields (exceptionResultJson result)
  [("fragment", JStr "TypedBooleanFacts-v1")]) <> BS.singleton 10

observedRule :: TypedRequest -> RuleResult -> Either Diagnostic J
observedRule request result = do
  observations <- traverse (observation request (ruleResultId result))
    [trace | trace <- ruleResultTrace result, traceKind trace == "leaf"]
  pure (setFields (ruleJson result) [("fact_observations", JArr observations)])

observation :: TypedRequest -> Text -> Trace -> Either Diagnostic J
observation request ruleId trace = case Map.lookup (traceId trace) (typedBindings request) of
  Nothing -> Left (internal trace "missing validated leaf binding")
  Just binding
    | bindingValue binding /= traceValue trace ->
        Left (internal trace "Boolean projection changed during evaluation")
    | otherwise ->
        let declaration = Map.lookup (traceId trace) (typedDeclarations request)
            burdenChecked = maybe False (maybe False (const True) . metadataBurden) declaration
            standardChecked = maybe False (maybe False (const True) . metadataStandard) declaration
            base = [("rule_id", JStr ruleId), ("branch_id", JStr (traceBranch trace))
              , ("leaf_id", JStr (traceId trace)), ("type", JStr "bool")
              , ("value", JBool (bindingValue binding))
              , ("burden_check", JStr (checkText burdenChecked))
              , ("standard_check", JStr (checkText standardChecked))]
            provenance = maybe [] (\item -> [("provenance", provenanceJson item)])
              (bindingProvenance binding)
        in Right (JObj (base ++ provenance))
  where
    internal item reason = diagnostic "KERR001" "evaluate"
      ("/facts/" <> traceId item) (Just (traceSpan item)) [("reason", reason)]
    checkText True = "matched"
    checkText False = "not_declared"

provenanceJson :: Provenance -> J
provenanceJson value = JObj (concat
  [ maybe [] (\item -> [("source_label", JStr item)]) (provenanceSourceLabel value)
  , maybe [] (\item -> [("recorded_date", JStr item)]) (provenanceRecordedDate value)
  , maybe [] (\item -> [("jurisdiction", JStr item)]) (provenanceJurisdiction value)
  ])

setFields :: J -> [(Text, J)] -> J
setFields (JObj fields) replacements = JObj
  ([(key, maybe value id (lookup key replacements)) | (key, value) <- fields]
  ++ [(key, value) | (key, value) <- replacements, key `notElem` map fst fields])
setFields other _ = other
