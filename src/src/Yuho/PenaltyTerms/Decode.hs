{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltyTerms.Decode (decodeTermsRequest, extractTerms) where

import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Core.Types (Diagnostic, diagnostic)
import Yuho.Exception.Types (ExceptionRequest(..))
import Yuho.PenaltySelection.Decode (decodePenaltyRequest)
import Yuho.PenaltySelection.Types (PenaltyRequest(..))
import Yuho.PenaltyTerms.Types (RawTerm(..), TermsRequest(..), unsupportedFeatureFields)
import Yuho.Protocol.Decode (asArray, asText, closed, countIds, decodePolicy, inputDigest, required)
import Yuho.Protocol.Json (J(..), objectFields)
import Yuho.TypedFacts.Types (TypedRequest(..))

decodeTermsRequest :: J -> Either Diagnostic TermsRequest
decodeTermsRequest root = do
  closed "" ["protocol", "request_id", "operation", "input_schema", "fragment"
    , "sources", "policy", "registry", "root_rule", "facts"] root
  (_, maxNodes) <- required (\_ -> decodePolicy) "" "policy" root
  if countIds root + countKeys "penalty_id" root + countKeys "term_id" root > maxNodes
    then Left (diagnostic "KINV004" "validate" "/registry" Nothing
      [("reason", "semantic node limit exceeded")]) else pure ()
  (strippedRoot, terms) <- extractTerms root
  transformed <- replace strippedRoot [("fragment", JStr "GuardedPenaltySelection-v1")]
  request <- decodePenaltyRequest transformed
  let typed = penaltyTypedRequest request
      original = typedExceptionRequest typed
      restored = original {exceptionRequestDigest = inputDigest root}
  pure (TermsRequest request {penaltyTypedRequest = typed
    {typedExceptionRequest = restored}} terms)

extractTerms :: J -> Either Diagnostic (J, [RawTerm])
extractTerms root = do
  rules <- required asArray "" "registry" root
  (stripped, collected) <- unzip <$> traverse stripRule (zip [0 :: Int ..] rules)
  transformed <- replace root [("registry", JArr stripped)]
  pure (transformed, concat collected)

countKeys :: Text -> J -> Int
countKeys wanted value = case value of
  JObj fields -> length [() | (key, _) <- fields, key == wanted]
    + sum (map (countKeys wanted . snd) fields)
  JArr items -> sum (map (countKeys wanted) items)
  _ -> 0

stripRule :: (Int, J) -> Either Diagnostic (J, [RawTerm])
stripRule (index, value) = do
  let pointer = "/registry/" <> indexText index
  program <- required (\_ -> Right) pointer "program" value
  (updated, terms) <- stripProvision (pointer <> "/program") program
  result <- replace value [("program", updated)]
  pure (result, terms)

stripProvision :: Text -> J -> Either Diagnostic (J, [RawTerm])
stripProvision pointer value = do
  penalties <- required asArray pointer "penalties" value
  (updatedPenalties, own) <- unzip <$> traverse (stripPenalty (pointer <> "/penalties"))
    (zip [0 :: Int ..] penalties)
  children <- required asArray pointer "children" value
  (updatedChildren, nested) <- unzip <$> traverse
    (\(index, child) -> stripProvision (pointer <> "/children/" <> indexText index) child)
    (zip [0 :: Int ..] children)
  result <- replace value [("penalties", JArr updatedPenalties)
    , ("children", JArr updatedChildren)]
  pure (result, concat own ++ concat nested)

stripPenalty :: Text -> (Int, J) -> Either Diagnostic (J, [RawTerm])
stripPenalty prefix (index, value) = do
  let pointer = prefix <> "/" <> indexText index
  fields <- object pointer value
  case [key | (key, _) <- fields, key `elem` unsupportedFeatureFields] of
    key : _ -> Left (diagnostic "KCAP001" "capability" (pointer <> "/" <> key)
      Nothing [("kind", key)])
    [] -> pure ()
  identifier <- required asText pointer "penalty_id" value
  term <- required (\_ -> Right) pointer "term" value
  pure (JObj [(key, item) | (key, item) <- fields, key /= "term"]
    , [RawTerm identifier term (pointer <> "/term")])

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
