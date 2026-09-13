{-# LANGUAGE OverloadedStrings #-}
module Yuho.ModelBundle.ChangeSet
  ( Classification(..), ChangeRow(..), ChangeSet(..), compareSnapshots
  , encodeChangeSet, decodeChangeSet, checkChangeSetLimits
  , changeSetLimit, changeRecordLimit
  ) where

import qualified Data.ByteString as BS
import Data.List (sort, sortOn)
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Core.Types (Span(..))
import Yuho.ModelBundle.Json (arr, digestDomain, field, fields, obj, parseCanonical, str)
import Yuho.ModelBundle.Package (PackageSnapshot(..))
import Yuho.ModelBundle.Types
import Yuho.Protocol.Json (J(..), encodeJson, lookupField)

data Classification = Added | Removed | Unchanged | Modified | UnknownRelationship
  deriving (Eq, Ord, Show)

data ChangeRow = ChangeRow
  { rowCategory :: Text, rowIdentity :: Text, rowClassification :: Classification
  , rowOldDigest :: Maybe Text, rowNewDigest :: Maybe Text
  } deriving (Eq, Show)

data ChangeSet = ChangeSet
  { changeOldBundle :: Text, changeNewBundle :: Text
  , changeRows :: [ChangeRow], changeAffectedIds :: [Text]
  , changeOldNonApplicableReviews :: [Text], changeNewApplicableReviews :: [Text]
  , changeNewStaleReviews :: [Text], changeNewPartialReviews :: [Text]
  } deriving (Eq, Show)

-- The shared closed JSON decoder accepts at most one MiB. A stored report must
-- remain readable by that decoder, so this is stricter than the proposed 64 MiB.
changeSetLimit, changeRecordLimit :: Int
changeSetLimit = 1048576
changeRecordLimit = 100000

compareSnapshots :: PackageSnapshot -> PackageSnapshot -> Either Failure ChangeSet
compareSnapshots old new = do
  let oldCore = snapshotCore old
      newCore = snapshotCore new
      oldDigest = validatedDigest (snapshotValidation old)
      newDigest = validatedDigest (snapshotValidation new)
      artifactRows = diffCategory "artifacts" (artifactIndex oldCore) (artifactIndex newCore)
      sourceRows = diffCategory "legal_sources" (sourceIndex oldCore) (sourceIndex newCore)
      workRows = diffCategory "work_groups" (groupIndex recordWork oldCore) (groupIndex recordWork newCore)
      expressionRows = diffCategory "expression_groups" (groupIndex recordExpression oldCore) (groupIndex recordExpression newCore)
      manifestationRows = diffCategory "manifestations" (manifestationIndex oldCore) (manifestationIndex newCore)
      derivationRows = diffCategory "derivations" (derivationIndex oldCore) (derivationIndex newCore)
      mappingRows = diffMappings oldCore newCore
      scopeRows = diffCategory "scope" (scopeIndex oldCore) (scopeIndex newCore)
      modelRows = diffCategory "executable_model" (singleIndex "request" (lookupField "executable_model" (coreRaw oldCore)))
        (singleIndex "request" (lookupField "executable_model" (coreRaw newCore)))
      metadataRows = diffCategory "metadata" (metadataIndex oldCore) (metadataIndex newCore)
      reviewRows = diffReviews (Map.fromList (snapshotReviewDigests old))
        (Map.fromList (snapshotReviewDigests new))
      unmatchedOld = [rowIdentity r | r <- artifactRows, rowClassification r == Removed]
      unmatchedNew = [rowIdentity r | r <- artifactRows, rowClassification r == Added]
      unknownArtifact = if null unmatchedOld || null unmatchedNew then [] else
        [ChangeRow "artifacts" "unpaired-digests" UnknownRelationship
          (Just (recordDigest (JArr (map JStr unmatchedOld))))
          (Just (recordDigest (JArr (map JStr unmatchedNew))))]
      rows = sortOn rowKey (concat [artifactRows, unknownArtifact, sourceRows, workRows
        , expressionRows, manifestationRows, derivationRows, mappingRows, scopeRows
        , modelRows, metadataRows, reviewRows])
      changedSources = Set.fromList [rowIdentity r | r <- sourceRows, rowClassification r /= Unchanged]
      changedArtifacts = Set.fromList [rowIdentity r | r <- artifactRows, rowClassification r /= Unchanged]
      changedDerived = Set.fromList [Text.take 64 (rowIdentity r) | r <- derivationRows
        , rowClassification r /= Unchanged]
      mappingIds = [mappingSemanticId m | m <- coreMappings oldCore ++ coreMappings newCore
        , Set.member (mappingSource m) changedSources
          || Set.member (mappingArtifact m) changedArtifacts
          || Set.member (mappingArtifact m) changedDerived]
      changedMappingIds = [Text.takeWhile (/= '|') (rowIdentity r) | r <- mappingRows
        , rowClassification r /= Unchanged]
      changedScopeIds = [Text.drop (Text.length "semantic_id:") (rowIdentity r) | r <- scopeRows
        , Text.isPrefixOf "semantic_id:" (rowIdentity r), rowClassification r /= Unchanged]
      changedExclusions = [rowIdentity r | r <- scopeRows
        , Text.isPrefixOf "exclusion:" (rowIdentity r), rowClassification r /= Unchanged]
      affected = sort (Set.toList (Set.fromList
        (mappingIds ++ changedMappingIds ++ changedScopeIds ++ changedExclusions)))
      oldNonApplicable = if oldDigest == newDigest then []
        else map fst (snapshotReviewDigests old)
      result = ChangeSet oldDigest newDigest rows affected oldNonApplicable
        (validatedApplicable (snapshotValidation new))
        (validatedStale (snapshotValidation new))
        (validatedPartial (snapshotValidation new))
  checkChangeSetLimits result

checkChangeSetLimits :: ChangeSet -> Either Failure ChangeSet
checkChangeSetLimits result =
  if length (changeRows result) > changeRecordLimit
    then Left (Failure "MBCDRES001" "/changes" "change record count limit exceeded")
    else if BS.length (encodeJson (encodeChangeSet result)) + 1 > changeSetLimit
      then Left (Failure "MBCDRES001" "/" "canonical report exceeds one MiB")
      else Right result

rowKey :: ChangeRow -> (Int, Text, Classification, Maybe Text, Maybe Text)
rowKey row = (categoryOrder (rowCategory row), rowIdentity row
  , rowClassification row, rowOldDigest row, rowNewDigest row)

categoryOrder :: Text -> Int
categoryOrder category = case lookup category (zip categories [0..]) of
  Just index -> index
  Nothing -> length categories

categories :: [Text]
categories = ["artifacts", "legal_sources", "work_groups", "expression_groups"
  , "manifestations", "derivations", "semantic_mappings", "scope"
  , "executable_model", "metadata", "reviews"]

recordDigest :: J -> Text
recordDigest = digestDomain "yuho.model-bundle-change-record/v1" . encodeJson

diffCategory :: Text -> Map.Map Text J -> Map.Map Text J -> [ChangeRow]
diffCategory category old new =
  [let prior = Map.lookup identifier old
       later = Map.lookup identifier new
       classification = case (prior, later) of
         (Nothing, Just _) -> Added
         (Just _, Nothing) -> Removed
         (Just a, Just b) | a == b -> Unchanged
         _ -> Modified
   in ChangeRow category identifier classification (recordDigest <$> prior) (recordDigest <$> later)
  | identifier <- Set.toAscList (Map.keysSet old `Set.union` Map.keysSet new)]

diffReviews :: Map.Map Text Text -> Map.Map Text Text -> [ChangeRow]
diffReviews old new =
  [let prior = Map.lookup identifier old
       later = Map.lookup identifier new
       classification = case (prior, later) of
         (Nothing, Just _) -> Added
         (Just _, Nothing) -> Removed
         (Just a, Just b) | a == b -> Unchanged
         _ -> Modified
   in ChangeRow "reviews" identifier classification prior later
  | identifier <- Set.toAscList (Map.keysSet old `Set.union` Map.keysSet new)]

artifactIndex :: Core -> Map.Map Text J
artifactIndex core = Map.fromList [(artifactDigest a, JObj
  [("sha256", JStr (artifactDigest a)), ("byte_length", JNum (artifactLength a))
  , ("media_type", JStr (artifactMediaType a)), ("role", JStr (artifactRole a))])
  | a <- coreArtifacts core]

sourceIndex :: Core -> Map.Map Text J
sourceIndex core = Map.fromList [(recordId s, recordMetadata s) | s <- coreSources core]

manifestationIndex :: Core -> Map.Map Text J
manifestationIndex core = Map.fromList [(recordManifestation s, recordMetadata s) | s <- coreSources core]

groupIndex :: (SourceRecord -> Text) -> Core -> Map.Map Text J
groupIndex select core = Map.map (JArr . map JStr . sort) $ Map.fromListWith (++)
  [(select source, [recordId source]) | source <- coreSources core]

derivationIndex :: Core -> Map.Map Text J
derivationIndex core = Map.fromList
  [(derivationChild d <> ":" <> derivationParent d, JObj
    [("child_digest", JStr (derivationChild d)), ("parent_digest", JStr (derivationParent d))
    , ("tool_name", JStr (derivationTool d)), ("tool_version", JStr (derivationVersion d))
    , ("configuration", JStr (derivationConfiguration d))]) | d <- coreDerivations core]

scopeIndex :: Core -> Map.Map Text J
scopeIndex core = Map.fromList $ concat
  [ [("semantic_id:" <> value, JStr value) | value <- scopeIds scope]
  , [("source_id:" <> value, JStr value) | value <- scopeSources scope]
  , [("expression_id:" <> value, JStr value) | value <- scopeExpressions scope]
  , [("exclusion:" <> identifier, JStr reason) | (identifier, reason) <- scopeExclusions scope]
  , [("field:" <> key, value) | (key, value) <- objectPairs (scopeRaw scope)
      , key `notElem` ["semantic_ids", "source_ids", "expression_ids", "exclusions"]]
  ] where scope = coreScope core

metadataIndex :: Core -> Map.Map Text J
metadataIndex core = Map.fromList [(key, value) | (key, value) <- objectPairs (coreRaw core)
  , key `elem` ["schema", "canonical_profile", "hash_algorithm", "model_id"]]

singleIndex :: Text -> Maybe J -> Map.Map Text J
singleIndex key = maybe Map.empty (Map.singleton key)

objectPairs :: J -> [(Text, J)]
objectPairs (JObj pairs) = pairs
objectPairs _ = []

mappingBase :: Mapping -> Text
mappingBase mapping = Text.intercalate "|" [mappingSemanticId mapping, mappingSource mapping
  , mappingRole mapping, mappingArtifact mapping]

mappingValue :: Mapping -> J
mappingValue mapping = JObj
  [("semantic_id", JStr (mappingSemanticId mapping))
  , ("source_id", JStr (mappingSource mapping))
  , ("role", JStr (mappingRole mapping))
  , ("artifact_digest", JStr (mappingArtifact mapping))
  , ("span", spanValue (mappingSpan mapping))]

spanValue :: Span -> J
spanValue location = JObj
  [("start", JNum (toInteger (spanStart location))), ("end", JNum (toInteger (spanEnd location)))
  , ("start_line", JNum (toInteger (spanStartLine location)))
  , ("start_col", JNum (toInteger (spanStartCol location)))
  , ("end_line", JNum (toInteger (spanEndLine location)))
  , ("end_col", JNum (toInteger (spanEndCol location)))]

diffMappings :: Core -> Core -> [ChangeRow]
diffMappings old new = concatMap one (Set.toAscList (Map.keysSet olds `Set.union` Map.keysSet news))
  where
    grouped core = Map.fromListWith (++) [(mappingBase m, [mappingValue m]) | m <- coreMappings core]
    olds = grouped old
    news = grouped new
    one key = case (Map.findWithDefault [] key olds, Map.findWithDefault [] key news) of
      ([a], [b]) -> diffCategory "semantic_mappings" (Map.singleton key a) (Map.singleton key b)
      ([a], []) -> diffCategory "semantic_mappings" (Map.singleton key a) Map.empty
      ([], [b]) -> diffCategory "semantic_mappings" Map.empty (Map.singleton key b)
      (a, b) -> [ChangeRow "semantic_mappings" key UnknownRelationship
        (recordDigest . JArr . sortOn encodeJson <$> nonempty a)
        (recordDigest . JArr . sortOn encodeJson <$> nonempty b)]
    nonempty [] = Nothing
    nonempty xs = Just xs

classText :: Classification -> Text
classText value = case value of
  Added -> "added"
  Removed -> "removed"
  Unchanged -> "unchanged"
  Modified -> "modified"
  UnknownRelationship -> "unknown-relationship"

classFromText :: Text -> Maybe Classification
classFromText value = lookup value [(classText kind, kind)
  | kind <- [Added, Removed, Unchanged, Modified, UnknownRelationship]]

encodeChangeSet :: ChangeSet -> J
encodeChangeSet value = JObj
  [("schema", JStr "yuho.model-bundle-change-set/v1")
  , ("canonical_profile", JStr "yuho.sorted-json/v1")
  , ("old_bundle_digest", JStr (changeOldBundle value))
  , ("new_bundle_digest", JStr (changeNewBundle value))
  , ("core_relation", JStr (if changeOldBundle value == changeNewBundle value then "identical" else "different"))
  , ("summary", JObj ([("total", JNum (toInteger (length rows)))] ++
      [(classText kind, JNum (toInteger (length (filter ((== kind) . rowClassification) rows))))
      | kind <- [Added, Removed, Unchanged, Modified, UnknownRelationship]]))
  , ("changes", JArr (map encodeRow rows))
  , ("directly_affected_ids", JArr (map JStr (changeAffectedIds value)))
  , ("wider_downstream_impact", JStr "unknown")
  , ("review_impact", JObj
      [("old_reviews_non_applicable_to_new", JArr (map JStr (changeOldNonApplicableReviews value)))
      , ("new_applicable_asserted_reviews", JArr (map JStr (changeNewApplicableReviews value)))
      , ("new_stale_reviews", JArr (map JStr (changeNewStaleReviews value)))
      , ("new_partial_reviews", JArr (map JStr (changeNewPartialReviews value)))
      , ("review_authentication", JStr "none")])]
  where rows = changeRows value

encodeRow :: ChangeRow -> J
encodeRow row = JObj
  [("category", JStr (rowCategory row)), ("identity", JStr (rowIdentity row))
  , ("classification", JStr (classText (rowClassification row)))
  , ("old_record_digest", maybe JNull JStr (rowOldDigest row))
  , ("new_record_digest", maybe JNull JStr (rowNewDigest row))]

decodeChangeSet :: BS.ByteString -> Either Failure ChangeSet
decodeChangeSet bytes = do
  if BS.length bytes > changeSetLimit
    then Left (Failure "MBCDRES001" "/" "stored report exceeds one MiB") else pure ()
  root <- parseCanonical "/change_set" bytes
  _ <- exact "/change_set" ["schema", "canonical_profile", "old_bundle_digest"
    , "new_bundle_digest", "core_relation", "summary", "changes", "directly_affected_ids"
    , "wider_downstream_impact", "review_impact"] root
  expectText "/change_set" "schema" "yuho.model-bundle-change-set/v1" root
  expectText "/change_set" "canonical_profile" "yuho.sorted-json/v1" root
  old <- field "/change_set" "old_bundle_digest" root >>= digestText "/change_set/old_bundle_digest"
  new <- field "/change_set" "new_bundle_digest" root >>= digestText "/change_set/new_bundle_digest"
  expectText "/change_set" "core_relation" (if old == new then "identical" else "different") root
  expectText "/change_set" "wider_downstream_impact" "unknown" root
  rows <- field "/change_set" "changes" root >>= arr "/change_set/changes" >>= traverse decodeRow
  if length rows > changeRecordLimit then Left (Failure "MBCDRES001" "/changes" "change record count limit exceeded")
    else pure ()
  affected <- textList root "directly_affected_ids"
  review <- field "/change_set" "review_impact" root
  _ <- exact "/change_set/review_impact" ["old_reviews_non_applicable_to_new"
    , "new_applicable_asserted_reviews", "new_stale_reviews", "new_partial_reviews"
    , "review_authentication"] review
  expectText "/change_set/review_impact" "review_authentication" "none" review
  oldNonApplicable <- textList review "old_reviews_non_applicable_to_new"
  newApplicable <- textList review "new_applicable_asserted_reviews"
  newStale <- textList review "new_stale_reviews"
  newPartial <- textList review "new_partial_reviews"
  let result = ChangeSet old new rows affected oldNonApplicable newApplicable newStale newPartial
  if rows /= sortOn rowKey rows
      || Set.size (Set.fromList [(rowCategory r, rowIdentity r) | r <- rows]) /= length rows
      || not (all sortedUnique
      [affected, oldNonApplicable, newApplicable, newStale, newPartial])
    then Left (Failure "MBCDINV001" "/change_set" "semantic arrays not canonical")
    else if encodeJson (encodeChangeSet result) /= bytes
      then Left (Failure "MBCDINV001" "/change_set" "summary or report fields inconsistent")
      else Right result

decodeRow :: J -> Either Failure ChangeRow
decodeRow value = do
  _ <- exact "/changes" ["category", "identity", "classification"
    , "old_record_digest", "new_record_digest"] value
  category <- field "/changes" "category" value >>= str "/changes/category"
  if category `elem` categories then pure ()
    else Left (Failure "MBCDDEC001" "/changes/category" "unknown record category")
  identity <- field "/changes" "identity" value >>= str "/changes/identity"
  classificationText <- field "/changes" "classification" value >>= str "/changes/classification"
  classification <- maybe (Left (Failure "MBCDDEC001" "/changes/classification" "unknown classification"))
    Right (classFromText classificationText)
  prior <- field "/changes" "old_record_digest" value >>= maybeDigest "/changes/old_record_digest"
  later <- field "/changes" "new_record_digest" value >>= maybeDigest "/changes/new_record_digest"
  case (classification, prior, later) of
    (Added, Nothing, Just _) -> pure ()
    (Removed, Just _, Nothing) -> pure ()
    (Unchanged, Just a, Just b) | a == b -> pure ()
    (Modified, Just a, Just b) | a /= b -> pure ()
    (UnknownRelationship, _, _) -> pure ()
    _ -> Left (Failure "MBCDINV001" "/changes" "classification and digest presence disagree")
  pure (ChangeRow category identity classification prior later)

maybeDigest :: Text -> J -> Either Failure (Maybe Text)
maybeDigest _ JNull = Right Nothing
maybeDigest path value = Just <$> digestText path value

digestText :: Text -> J -> Either Failure Text
digestText path value = do
  digest <- str path value
  if Text.length digest == 64 && Text.all (\c -> c >= '0' && c <= '9' || c >= 'a' && c <= 'f') digest
    then Right digest else Left (Failure "MBCDDEC001" path "expected lowercase SHA-256 digest")

textList :: J -> Text -> Either Failure [Text]
textList parent key = field "/change_set" key parent >>= arr ("/change_set/" <> key)
  >>= traverse (str ("/change_set/" <> key))

sortedUnique :: [Text] -> Bool
sortedUnique values = values == sort (Set.toList (Set.fromList values))

expectText :: Text -> Text -> Text -> J -> Either Failure ()
expectText path key expected parent = do
  actual <- field path key parent >>= str (path <> "/" <> key)
  if actual == expected then Right ()
    else Left (Failure "MBCDDEC001" (path <> "/" <> key) "unsupported or inconsistent value")

exact :: Text -> [Text] -> J -> Either Failure J
exact path required value = do
  _ <- obj path required value
  pairs <- fields path value
  if sort (map fst pairs) == sort required then Right value
    else Left (Failure "MBCDDEC001" path "missing or unknown report field")
