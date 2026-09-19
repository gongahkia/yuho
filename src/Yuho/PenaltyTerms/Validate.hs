{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltyTerms.Validate (validateTerms, validateTermStructure) where

import Control.Monad (foldM)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Char (ord)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Core.Types (Diagnostic, Source, Span(..), Provision(..), Requirement(..), diagnostic)
import Yuho.Exception.Types (ExceptionRequest(..), RawGraph(..), RawRule(..), RawException(..))
import Yuho.PenaltySelection.Types
  ( PenaltyRequest(..), PenaltyDeclaration(..), ValidatedPenalties(..) )
import Yuho.PenaltySelection.Validate (validatePenalties)
import Yuho.PenaltyTerms.Types
import Yuho.Protocol.Decode (asArray, asText, closed, decodeSpan, required, invalid)
import Yuho.Protocol.Json (J(..), objectFields)
import Yuho.TypedFacts.Types (TypedRequest(..))

validateTerms :: TermsRequest -> Either Diagnostic ValidatedTerms
validateTerms (TermsRequest request rawTerms) = do
  validated <- validatePenalties request
  let raw = exceptionRawGraph (typedExceptionRequest (penaltyTypedRequest request))
  terms <- validateTermStructure raw (validatedDeclarations validated) rawTerms
  pure (ValidatedTerms validated terms)

validateTermStructure :: RawGraph a -> [PenaltyDeclaration] -> [RawTerm]
  -> Either Diagnostic (Map Text Term)
validateTermStructure raw declarations rawTerms = do
  let reserved = Set.fromList (allIds raw ++ map penaltyId declarations)
  (_, entries) <- foldM (validateOne raw declarations) (reserved, []) rawTerms
  pure (Map.fromList (reverse entries))

validateOne :: RawGraph a -> [PenaltyDeclaration] -> (Set Text, [(Text, Term)])
  -> RawTerm -> Either Diagnostic (Set Text, [(Text, Term)])
validateOne raw declarations (seen, entries) item = do
  declaration <- case [candidate | candidate <- declarations
      , penaltyId candidate == rawTermPenaltyId item] of
    [found] -> Right found
    _ -> Left (diagnostic "KERR001" "evaluate" (rawTermPointer item) Nothing
      [("reason", "validated penalty declaration missing")])
  source <- case lookup (penaltySource declaration) (rawSources raw) of
    Just found -> Right found
    Nothing -> Left (diagnostic "KERR001" "evaluate" (rawTermPointer item) Nothing
      [("reason", "validated source missing")])
  (updated, term) <- validateTerm source (penaltySpan declaration) 1 seen
    (rawTermPointer item) (rawTermValue item)
  pure (updated, (penaltyId declaration, term) : entries)

validateTerm :: Source -> Span -> Int -> Set Text -> Text -> J
  -> Either Diagnostic (Set Text, Term)
validateTerm source parent depth seen pointer value = do
  if depth > 16 then Left (diagnostic "KDEC002" "decode" pointer Nothing
    [("reason", "term tree depth exceeds 16")]) else pure ()
  kind <- required asText pointer "kind" value
  rejectUnsupported pointer value
  let common = ["kind", "term_id", "span"]
      atom extra = closed pointer (common ++ extra) value
  case kind of
    "all_of" -> group AllOf
    "exactly_one_of" -> group ExactlyOneOf
    "one_or_more_of" -> group OneOrMoreOf
    "term_imprisonment" -> do
      atom ["unit", "minimum", "maximum"]
      (next, identifier, spanValue) <- identity
      unit <- required asText pointer "unit" value >>= decodeUnit (pointer <> "/unit")
      lower <- endpoint integerAmount False (pointer <> "/minimum") =<<
        required (\_ -> Right) pointer "minimum" value
      upper <- endpoint integerAmount False (pointer <> "/maximum") =<<
        required (\_ -> Right) pointer "maximum" value
      ordered pointer lower upper
      pure (next, Term identifier spanValue (Atom (TermImprisonment unit lower upper)))
    "fine" -> do
      atom ["currency", "minimum", "maximum"]
      (next, identifier, spanValue) <- identity
      currency <- required asText pointer "currency" value
      if currency == "SGD" then pure () else Left (diagnostic "KCAP001" "capability"
        (pointer <> "/currency") (Just spanValue) [("kind", currency)])
      lower <- endpoint fineAmount False (pointer <> "/minimum") =<<
        required (\_ -> Right) pointer "minimum" value
      upper <- endpoint fineAmount True (pointer <> "/maximum") =<<
        required (\_ -> Right) pointer "maximum" value
      ordered pointer lower upper
      pure (next, Term identifier spanValue (Atom (Fine lower upper)))
    "caning" -> do
      atom ["minimum", "maximum"]
      (next, identifier, spanValue) <- identity
      lower <- endpoint integerAmount False (pointer <> "/minimum") =<<
        required (\_ -> Right) pointer "minimum" value
      upper <- endpoint integerAmount False (pointer <> "/maximum") =<<
        required (\_ -> Right) pointer "maximum" value
      ordered pointer lower upper
      pure (next, Term identifier spanValue (Atom (Caning lower upper)))
    "life_imprisonment" -> do
      atom []
      (next, identifier, spanValue) <- identity
      pure (next, Term identifier spanValue (Atom LifeImprisonment))
    "death" -> do
      atom []
      (next, identifier, spanValue) <- identity
      pure (next, Term identifier spanValue (Atom Death))
    other -> Left (diagnostic "KCAP001" "capability" (pointer <> "/kind") Nothing
      [("kind", other)])
  where
    identity = do
      identifier <- required asText pointer "term_id" value
      if not (validTermId identifier)
        then invariant (pointer <> "/term_id") "invalid term ID" else pure ()
      if Set.member identifier seen
        then invariant (pointer <> "/term_id") "duplicate term ID" else pure ()
      spanValue <- required (decodeSpan source) pointer "span" value
      if inside parent spanValue then pure ()
        else invariant (pointer <> "/span") "term span outside containing declaration or node"
      pure (Set.insert identifier seen, identifier, spanValue)
    group constructor = do
      closed pointer ["kind", "term_id", "span", "terms"] value
      (next, identifier, spanValue) <- identity
      children <- required asArray pointer "terms" value
      if length children < 2 then invariant (pointer <> "/terms")
        "combinator requires at least two children" else pure ()
      (updated, reversed) <- foldM (\(used, built) (index, child) -> do
        (more, part) <- validateTerm source spanValue (depth + 1) used
          (pointer <> "/terms/" <> Text.pack (show index)) child
        pure (more, part : built)) (next, []) (zip [0 :: Int ..] children)
      pure (updated, Term identifier spanValue (constructor (reverse reversed)))

inside :: Span -> Span -> Bool
inside outer inner = spanStart outer <= spanStart inner && spanEnd inner <= spanEnd outer

validTermId :: Text -> Bool
validTermId identifier = case Text.splitOn ":" identifier of
  "term" : segments -> not (null segments) && all (not . Text.null) segments
  _ -> False

decodeUnit :: Text -> Text -> Either Diagnostic DurationUnit
decodeUnit _ "days" = Right Days
decodeUnit _ "weeks" = Right Weeks
decodeUnit _ "months" = Right Months
decodeUnit _ "years" = Right Years
decodeUnit pointer other = Left (diagnostic "KCAP001" "capability" pointer Nothing
  [("kind", other)])

endpoint :: (Text -> J -> Either Diagnostic a) -> Bool -> Text -> J
  -> Either Diagnostic (Endpoint a)
endpoint parse allowOpen pointer value = do
  kind <- required asText pointer "kind" value
  case kind of
    "not_stated" -> closed pointer ["kind"] value >> pure NotStated
    "unbounded" -> do
      closed pointer ["kind"] value
      if allowOpen then Right Unbounded else invariant pointer "unbounded endpoint not allowed"
    "specified" -> do
      closed pointer ["kind", "value"] value
      Specified <$> required parse pointer "value" value
    _ -> Left (diagnostic "KCAP001" "capability" (pointer <> "/kind") Nothing
      [("kind", kind)])

integerAmount :: Text -> J -> Either Diagnostic Integer
integerAmount pointer (JNum number)
  | number >= 1 && number <= 1000000 = Right number
  | otherwise = invariant pointer "integer endpoint outside 1..1000000"
integerAmount pointer _ = invalid pointer "expected integer endpoint"

fineAmount :: Text -> J -> Either Diagnostic Integer
fineAmount pointer (JStr input) =
  let pieces = Text.splitOn "." input
      digits part = not (Text.null part) && Text.all (\c -> c >= '0' && c <= '9') part
      amount part = Text.foldl' (\acc c -> acc * 10 + toInteger (ord c - ord '0')) 0 part
      parse whole fraction
        | not (digits whole) || Text.length whole > 18
          || (Text.length whole > 1 && Text.isPrefixOf "0" whole) =
            invalid pointer "invalid fine decimal grammar"
        | maybe False (\part -> not (digits part) || Text.length part > 2) fraction =
            invalid pointer "invalid fine decimal grammar"
        | otherwise =
            let cents = amount whole * 100 + maybe 0 (\part ->
                  amount part * if Text.length part == 1 then 10 else 1) fraction
            in if cents > 0 then Right cents else invariant pointer "fine must be positive"
  in case pieces of
    [whole] -> parse whole Nothing
    [whole, fraction] -> parse whole (Just fraction)
    _ -> invalid pointer "invalid fine decimal grammar"
fineAmount pointer _ = invalid pointer "expected fine decimal string"

ordered :: Ord a => Text -> Endpoint a -> Endpoint a -> Either Diagnostic ()
ordered pointer (Specified lower) (Specified upper)
  | lower > upper = invariant pointer "minimum exceeds maximum"
ordered _ _ _ = Right ()

invariant :: Text -> Text -> Either Diagnostic a
invariant pointer reason = Left (diagnostic "KINV009" "validate" pointer Nothing
  [("reason", reason)])

rejectUnsupported :: Text -> J -> Either Diagnostic ()
rejectUnsupported pointer value = case objectFields value of
  Nothing -> invalid pointer "expected term object"
  Just fields -> case [key | (key, _) <- fields, key `elem` unsupportedFeatureFields] of
    key : _ -> Left (diagnostic "KCAP001" "capability" (pointer <> "/" <> key)
      Nothing [("kind", key)])
    [] -> Right ()

allIds :: RawGraph a -> [Text]
allIds raw = map fst (rawSources raw) ++ concatMap ruleIds (rawRules raw)
  where
    ruleIds rule = rawRuleId rule : map rawExceptionId (rawRuleExceptions rule)
      ++ provisionIds (rawRuleProgram rule)
    provisionIds provision = provisionId provision
      : concatMap requirementIds (provisionRequirements provision)
      ++ concatMap provisionIds (provisionChildren provision)
    requirementIds requirement = requirementId requirement
      : concatMap requirementIds (requirementMembers requirement)
