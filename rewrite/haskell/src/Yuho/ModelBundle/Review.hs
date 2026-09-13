{-# LANGUAGE OverloadedStrings #-}
module Yuho.ModelBundle.Review
  ( decodeReview, classifyReviews, reviewPurposesAllowed ) where

import Data.Foldable (traverse_)
import Data.List (sort)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Format (defaultTimeLocale, parseTimeM)
import Data.Time.Clock (UTCTime)
import Yuho.ModelBundle.Json
import Yuho.ModelBundle.Types
import Yuho.Protocol.Json (J(..), lookupField)

reviewPurposesAllowed :: [Text]
reviewPurposesAllowed = ["source_fidelity", "semantic_fidelity", "scope_completeness"
  , "jurisdictional_applicability"]

decodeReview :: Text -> J -> Either Failure Review
decodeReview filename value = do
  let path = "/reviews/" <> filename
  _ <- obj path ["schema", "review_id", "bundle_digest", "scope_digest"
    , "purposes", "coverage", "limitations", "outcome", "reviewed_at", "reviewer"] value
  _ <- taggedField path "schema" ["yuho.review-assertion/v1"] value
  rid <- textField path "review_id" value
  if safeId rid && filename == rid <> ".json" then pure ()
    else issue "MBINV001" (path <> "/review_id") "review ID differs from safe filename"
  bundle <- textField path "bundle_digest" value
  scope <- textField path "scope_digest" value
  traverse_ digest [(path <> "/bundle_digest", bundle), (path <> "/scope_digest", scope)]
  purposes <- field path "purposes" value >>= arr (path <> "/purposes") >>= traverse (str (path <> "/purposes"))
  uniqueSorted (path <> "/purposes") purposes
  if null purposes then issue "MBINV001" (path <> "/purposes") "empty purposes" else pure ()
  traverse_ (tagged (path <> "/purposes") reviewPurposesAllowed) purposes
  limitations <- field path "limitations" value >>= arr (path <> "/limitations")
  traverse_ (str (path <> "/limitations")) limitations
  outcome <- taggedField path "outcome"
    ["asserted_acceptable", "changes_required", "informational"] value
  timestamp <- textField path "reviewed_at" value
  case parseTimeM True defaultTimeLocale "%Y-%m-%dT%H:%M:%SZ" (Text.unpack timestamp) :: Maybe UTCTime of
    Just _ -> pure ()
    Nothing -> issue "MBINV001" (path <> "/reviewed_at") "invalid UTC timestamp"
  reviewer <- field path "reviewer" value
  _ <- obj (path <> "/reviewer") ["reviewer_id", "name", "role", "organisation"] reviewer
  traverse_ (\key -> textField (path <> "/reviewer") key reviewer >> pure ())
    ["reviewer_id", "name", "role"]
  traverse_ (\v -> str (path <> "/reviewer/organisation") v >> pure ())
    (lookupField "organisation" reviewer)
  coverage <- field path "coverage" value
  _ <- obj (path <> "/coverage") ["kind", "scope_digest", "semantic_ids", "source_ids"] coverage
  kind <- taggedField (path <> "/coverage") "kind"
    ["scope_digest", "semantic_ids", "source_ids"] coverage
  (semIds, sourceIds) <- case kind of
    "scope_digest" -> do
      _ <- exactKeys (path <> "/coverage") ["kind", "scope_digest"] coverage
      named <- textField (path <> "/coverage") "scope_digest" coverage
      digest (path <> "/coverage/scope_digest", named)
      if named == scope then pure ([], [])
        else issue "MBINV001" (path <> "/coverage/scope_digest") "coverage digest differs from subject scope"
    "semantic_ids" -> do
      _ <- exactKeys (path <> "/coverage") ["kind", "semantic_ids"] coverage
      xs <- field (path <> "/coverage") "semantic_ids" coverage >>= arr (path <> "/coverage/semantic_ids")
        >>= traverse (str (path <> "/coverage/semantic_ids"))
      uniqueSorted (path <> "/coverage/semantic_ids") xs
      if null xs then issue "MBINV001" (path <> "/coverage/semantic_ids") "empty positive coverage" else pure ()
      traverse_ (coverageId (path <> "/coverage/semantic_ids")) xs
      pure (xs, [])
    _ -> do
      _ <- exactKeys (path <> "/coverage") ["kind", "source_ids"] coverage
      xs <- field (path <> "/coverage") "source_ids" coverage >>= arr (path <> "/coverage/source_ids")
        >>= traverse (str (path <> "/coverage/source_ids"))
      uniqueSorted (path <> "/coverage/source_ids") xs
      if null xs then issue "MBINV001" (path <> "/coverage/source_ids") "empty positive coverage" else pure ()
      traverse_ (coverageId (path <> "/coverage/source_ids")) xs
      pure ([], xs)
  pure (Review rid bundle scope purposes semIds sourceIds kind outcome)

classifyReviews :: Core -> Text -> Text -> Maybe Text -> [Review] -> Either Failure Validation
classifyReviews core bundle scope requested reviews = do
  let ids = Set.fromList (scopeIds (coreScope core))
      sources = Set.fromList (scopeSources (coreScope core))
  let applicable = [r | r <- reviews, reviewBundleDigest r == bundle && reviewScopeDigest r == scope]
  traverse_ (\r -> do
    if all (`Set.member` ids) (reviewSemanticIds r) && all (`Set.member` sources) (reviewSourceIds r)
      then pure () else issue "MBINV001" ("/reviews/" <> reviewId r) "review covers unknown ID") applicable
  let stale = [reviewId r | r <- reviews, reviewBundleDigest r /= bundle || reviewScopeDigest r /= scope]
      fullFor purpose r = reviewCoverageKind r == "scope_digest"
        || (reviewCoverageKind r == "semantic_ids" && purpose /= "source_fidelity"
          && reviewSemanticIds r == scopeIds (coreScope core))
        || (reviewCoverageKind r == "source_ids" && purpose == "source_fidelity"
          && reviewSourceIds r == scopeSources (coreScope core))
      full r = any (`fullFor` r) (reviewPurposes r)
      partial = [reviewId r | r <- applicable, not (full r)]
      policyMet = case requested of
        Nothing -> True
        Just purpose -> any (\r -> purpose `elem` reviewPurposes r
          && reviewOutcome r == "asserted_acceptable" && fullFor purpose r) applicable
  pure (Validation bundle scope (sort (map reviewId applicable)) (sort stale)
    (sort partial) policyMet)

textField :: Text -> Text -> J -> Either Failure Text
textField path key value = field path key value >>= str (path <> "/" <> key)

taggedField :: Text -> Text -> [Text] -> J -> Either Failure Text
taggedField path key allowed value = textField path key value >>= tagged (path <> "/" <> key) allowed

digest :: (Text, Text) -> Either Failure ()
digest (path, value)
  | Text.length value == 64 && Text.all (\c -> c >= '0' && c <= '9' || c >= 'a' && c <= 'f') value = pure ()
  | otherwise = issue "MBINV001" path "invalid lowercase SHA-256 digest"

exactKeys :: Text -> [Text] -> J -> Either Failure ()
exactKeys path expected value = do
  pairs <- fields path value
  if sort (map fst pairs) == sort expected then pure ()
    else issue "MBDEC001" path "wrong fields for tagged coverage"

coverageId :: Text -> Text -> Either Failure ()
coverageId path identifier = if safeId identifier then pure ()
  else issue "MBINV001" path "invalid positive coverage ID"
