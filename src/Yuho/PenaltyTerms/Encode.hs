{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltyTerms.Encode (encodeTerms, encodeTermsReject, termJson) where

import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Core.Types (Diagnostic, diagnostic)
import Yuho.Exception.Types (ExceptionResult)
import Yuho.PenaltySelection.Encode (selectionResultJson, selectionRejectJson)
import Yuho.PenaltySelection.Types (Selection)
import Yuho.PenaltyTerms.Types
import Yuho.Protocol.Encode (spanJson)
import Yuho.Protocol.Json (J(..), encodeJson, lookupField, textValue)
import Yuho.TypedFacts.Types (TypedRequest)

encodeTerms :: TypedRequest -> ExceptionResult -> Selection -> Map Text Term
  -> Either Diagnostic BS.ByteString
encodeTerms typed result selection terms = do
  base <- selectionResultJson typed result selection
  selected <- case lookupField "selected_penalties" base of
    Just (JArr records) -> traverse (attach terms) records
    _ -> internal "selected penalty list missing"
  pure (line (setFields base [("fragment", JStr "PenaltyTerms-v1")
    , ("selected_penalties", JArr selected)]))

encodeTermsReject :: ExceptionResult -> BS.ByteString
encodeTermsReject result = line (setFields (selectionRejectJson result)
  [("fragment", JStr "PenaltyTerms-v1")])

attach :: Map Text Term -> J -> Either Diagnostic J
attach terms record = do
  identifier <- maybe (internal "selected penalty ID missing") Right
    (lookupField "penalty_id" record >>= textValue)
  term <- maybe (internal "validated selected term missing") Right
    (Map.lookup identifier terms)
  pure (setFields record [("term", termJson term)])

termJson :: Term -> J
termJson (Term identifier spanValue kind) = JObj
  ([ ("term_id", JStr identifier), ("span", spanJson spanValue)] ++ kindFields kind)

kindFields :: TermKind -> [(Text, J)]
kindFields kind = case kind of
  Atom punishment -> atomFields punishment
  AllOf children -> group "all_of" children
  ExactlyOneOf children -> group "exactly_one_of" children
  OneOrMoreOf children -> group "one_or_more_of" children
  where
    group label children = [("kind", JStr label), ("terms", JArr (map termJson children))]

atomFields :: Punishment -> [(Text, J)]
atomFields punishment = case punishment of
  TermImprisonment unit lower upper ->
    [("kind", JStr "term_imprisonment"), ("unit", JStr (unitText unit))
    , ("minimum", endpointJson JNum lower), ("maximum", endpointJson JNum upper)]
  LifeImprisonment -> [("kind", JStr "life_imprisonment")]
  Fine lower upper ->
    [("kind", JStr "fine"), ("currency", JStr "SGD")
    , ("minimum", endpointJson (JStr . decimal) lower)
    , ("maximum", endpointJson (JStr . decimal) upper)]
  Caning lower upper ->
    [("kind", JStr "caning"), ("minimum", endpointJson JNum lower)
    , ("maximum", endpointJson JNum upper)]
  Death -> [("kind", JStr "death")]

endpointJson :: (a -> J) -> Endpoint a -> J
endpointJson _ NotStated = JObj [("kind", JStr "not_stated")]
endpointJson _ Unbounded = JObj [("kind", JStr "unbounded")]
endpointJson encode (Specified amount) = JObj
  [("kind", JStr "specified"), ("value", encode amount)]

unitText :: DurationUnit -> Text
unitText Days = "days"
unitText Weeks = "weeks"
unitText Months = "months"
unitText Years = "years"

decimal :: Integer -> Text
decimal cents = Text.pack (show (cents `div` 100)) <> "."
  <> Text.justifyRight 2 '0' (Text.pack (show (cents `mod` 100)))

setFields :: J -> [(Text, J)] -> J
setFields (JObj fields) replacements = JObj
  ([(key, maybe value id (lookup key replacements)) | (key, value) <- fields]
  ++ [(key, value) | (key, value) <- replacements, key `notElem` map fst fields])
setFields other _ = other

line :: J -> BS.ByteString
line value = encodeJson value <> BS.singleton 10

internal :: Text -> Either Diagnostic a
internal reason = Left (diagnostic "KERR001" "evaluate" "/selected_penalties" Nothing
  [("reason", reason)])
