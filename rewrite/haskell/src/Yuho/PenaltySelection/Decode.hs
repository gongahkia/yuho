{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltySelection.Decode (decodePenaltyRequest) where

import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Core.Types (Diagnostic, diagnostic)
import Yuho.Exception.Types (ExceptionRequest(..))
import Yuho.Protocol.Decode
  ( asArray, asText, closed, countIds, decodePolicy, inputDigest, required )
import Yuho.Protocol.Json (J(..), objectFields)
import Yuho.TypedFacts.Decode (decodeTypedRequest)
import Yuho.TypedFacts.Types (TypedRequest(..))
import Yuho.PenaltySelection.Types

decodePenaltyRequest :: J -> Either Diagnostic PenaltyRequest
decodePenaltyRequest root = do
  closed "" ["protocol", "request_id", "operation", "input_schema", "fragment"
    , "sources", "policy", "registry", "root_rule", "facts"] root
  (_, maxNodes) <- required (\_ -> decodePolicy) "" "policy" root
  if countIds root + countPenaltyIds root > maxNodes
    then Left (diagnostic "KINV004" "validate" "/registry" Nothing
      [("reason", "semantic node limit exceeded")])
    else pure ()
  values <- required asArray "" "registry" root
  (transformedRules, declarations) <- unzip <$> traverse transformRule
    (zip [0 :: Int ..] values)
  let allDeclarations = concat declarations
  transformed <- replace root
    [("fragment", JStr "TypedBooleanFacts-v1"), ("registry", JArr transformedRules)]
  typed <- decodeTypedRequest transformed
  let original = typedExceptionRequest typed
      withDigest = original {exceptionRequestDigest = inputDigest root}
  pure (PenaltyRequest typed {typedExceptionRequest = withDigest} allDeclarations)

countPenaltyIds :: J -> Int
countPenaltyIds value = case value of
  JObj fields -> length [() | (key, _) <- fields, key == "penalty_id"]
    + sum (map (countPenaltyIds . snd) fields)
  JArr items -> sum (map countPenaltyIds items)
  _ -> 0

transformRule :: (Int, J) -> Either Diagnostic (J, [RawPenalty])
transformRule (index, value) = do
  let pointer = "/registry/" <> indexText index
  ruleId <- required asText pointer "id" value
  program <- required (\_ -> Right) pointer "program" value
  (updated, declarations) <- transformProvision ruleId (pointer <> "/program") program
  result <- replace value [("program", updated)]
  pure (result, declarations)

transformProvision :: Text -> Text -> J -> Either Diagnostic (J, [RawPenalty])
transformProvision ruleId pointer value = do
  provisionId <- required asText pointer "id" value
  penaltyValues <- required asArray pointer "penalties" value
  own <- traverse (uncurry (decodePenalty ruleId provisionId (pointer <> "/penalties")))
    (zip [0 :: Int ..] penaltyValues)
  children <- required asArray pointer "children" value
  (updatedChildren, nested) <- unzip <$> traverse
    (\(index, child) -> transformProvision ruleId
      (pointer <> "/children/" <> indexText index) child)
    (zip [0 :: Int ..] children)
  fields <- object pointer value
  pure (JObj ([(key, if key == "children" then JArr updatedChildren else item)
    | (key, item) <- fields, key /= "penalties"]), own ++ concat nested)

decodePenalty :: Text -> Text -> Text -> Int -> J -> Either Diagnostic RawPenalty
decodePenalty ruleId provisionId prefix index value = do
  let pointer = prefix <> "/" <> indexText index
  fields <- object pointer value
  case filter (\(key, _) -> key `elem` unsupportedTerms) fields of
    (term, _) : _ -> Left (diagnostic "KCAP001" "capability"
      (pointer <> "/" <> term) Nothing [("kind", term)])
    [] -> pure ()
  closed pointer ["penalty_id", "source_id", "span", "guard"] value
  identifier <- required asText pointer "penalty_id" value
  sourceId <- required asText pointer "source_id" value
  sourceSpan <- required (\_ -> Right) pointer "span" value
  guardValue <- required (\_ -> Right) pointer "guard" value
  guard <- decodeGuard (pointer <> "/guard") guardValue
  pure (RawPenalty identifier ruleId provisionId sourceId sourceSpan guard index pointer)

decodeGuard :: Text -> J -> Either Diagnostic PenaltyGuard
decodeGuard pointer value = do
  kind <- required asText pointer "kind" value
  case kind of
    "unguarded" -> closed pointer ["kind"] value >> pure Unguarded
    "leaf_true" -> do
      closed pointer ["kind", "leaf_id"] value
      LeafTrue <$> required asText pointer "leaf_id" value
    _ -> Left (diagnostic "KCAP001" "capability" (pointer <> "/kind")
      Nothing [("kind", kind)])

unsupportedTerms :: [Text]
unsupportedTerms = ["imprisonment", "imprisonment_min", "imprisonment_max"
  , "fine", "fine_min", "fine_max", "fine_unlimited", "caning", "caning_min"
  , "caning_max", "caning_unspecified", "death", "death_penalty"
  , "mandatory_min_imprisonment", "mandatory_min_fine", "minimum", "maximum"
  , "currency", "duration", "unit", "combinator", "nested", "supplementary"
  , "sentencing", "condition"]

replace :: J -> [(Text, J)] -> Either Diagnostic J
replace value replacements = do
  fields <- object "" value
  pure (JObj [(key, maybe item id (lookup key replacements)) | (key, item) <- fields])

object :: Text -> J -> Either Diagnostic [(Text, J)]
object pointer value = maybe
  (Left (diagnostic "KDEC001" "decode" pointer Nothing [("reason", "expected object")]))
  Right (objectFields value)

indexText :: Int -> Text
indexText = Text.pack . show
