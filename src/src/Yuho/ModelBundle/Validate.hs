{-# LANGUAGE OverloadedStrings #-}
module Yuho.ModelBundle.Validate
  ( decodeCore, validateCore, semanticIds, scopeDigest ) where

import Data.Char (ord)
import Data.Foldable (traverse_)
import Data.List (sort)
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Calendar (fromGregorianValid)
import Yuho.Core.Types (Diagnostic(..), Request(..), Span(..))
import Yuho.Exception.Decode (decodeExceptionRequest)
import Yuho.Exception.Types (ExceptionRequest(..))
import Yuho.Exception.Validate (validateGraph)
import Yuho.Kernel.Validate (validateInput)
import Yuho.ModelBundle.Json
import Yuho.ModelBundle.Types
import Yuho.PenaltySelection.Decode (decodePenaltyRequest)
import Yuho.PenaltySelection.Validate (validatePenalties)
import Yuho.PenaltyTerms.Decode (decodeTermsRequest)
import Yuho.PenaltyTerms.Validate (validateTerms)
import Yuho.Presumption.Decode (decodePresumptionRequest)
import Yuho.Presumption.Validate (validatePresumptionRequest)
import Yuho.Protocol.Decode (decodeRequest)
import Yuho.Protocol.Json (J(..), encodeJson, lookupField)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)
import Yuho.TypedFacts.Decode (decodeTypedRequest)
import Yuho.TypedFacts.Validate (validateTyped)

decodeCore :: J -> Either Failure Core
decodeCore root = do
  _ <- obj "" ["schema", "canonical_profile", "hash_algorithm", "model_id"
    , "artifacts", "legal_sources", "derivations", "semantic_mappings", "scope"
    , "executable_model"] root
  match "" "schema" "yuho.model-bundle/v1" root
  match "" "canonical_profile" "yuho.sorted-json/v1" root
  match "" "hash_algorithm" "sha256" root
  modelId <- field "" "model_id" root >>= str "/model_id"
  requireId "/model_id" modelId
  artifacts <- list "/artifacts" 256 root "artifacts" decodeArtifact
  sources <- list "/legal_sources" 1024 root "legal_sources" decodeSourceRecord
  derivations <- list "/derivations" 4096 root "derivations" decodeDerivation
  mappings <- list "/semantic_mappings" 8192 root "semantic_mappings" decodeMapping
  scope <- field "" "scope" root >>= decodeScope
  model <- field "" "executable_model" root
  _ <- obj "/executable_model" ["artifact_digest", "format", "fragment"] model
  modelDigest <- field "/executable_model" "artifact_digest" model >>= str "/executable_model/artifact_digest"
  match "/executable_model" "format" "yuho.kernel-input/v1" model
  fragment <- field "/executable_model" "fragment" model >>= str "/executable_model/fragment"
  _ <- tagged "/executable_model/fragment" fragments fragment
  let core = Core root artifacts sources mappings derivations scope modelDigest fragment modelId
  validateStructure core
  pure core

fragments :: [Text]
fragments = ["ClosedBooleanBranches-v1", "AcyclicGuardedExceptions-v1"
  , "TypedBooleanFacts-v1", "GuardedPenaltySelection-v1", "PenaltyTerms-v1"
  , "SuppliedProofStatus-v1", "RegisteredPresumptionDerivations-v1"]

list :: Text -> Int -> J -> Text -> (Text -> J -> Either Failure a) -> Either Failure [a]
list path limit parent key parser = do
  values <- field "" key parent >>= arr path
  if length values > limit then issue "MBRES001" path "count limit exceeded" else pure ()
  traverse (\(index, value) -> parser (path <> "/" <> Text.pack (show index)) value)
    (zip [0 :: Int ..] values)

match :: Text -> Text -> Text -> J -> Either Failure ()
match path key expected parent = do
  value <- field path key parent >>= str (path <> "/" <> key)
  if value == expected then pure () else issue "MBCAP001" (path <> "/" <> key) "unsupported profile"

requireId :: Text -> Text -> Either Failure ()
requireId path value = if safeId value then pure () else issue "MBINV001" path "invalid local ID"

digestShape :: Text -> Text -> Either Failure ()
digestShape path value = if Text.length value == 64 && Text.all isHex value
  then pure () else issue "MBINV001" path "expected lowercase SHA-256 digest"
  where isHex ch = (ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f')

decodeArtifact :: Text -> J -> Either Failure Artifact
decodeArtifact path value = do
  _ <- obj path ["sha256", "byte_length", "media_type", "role"] value
  digest <- field path "sha256" value >>= str (path <> "/sha256")
  digestShape (path <> "/sha256") digest
  size <- field path "byte_length" value >>= number (path <> "/byte_length")
  if size < 0 || size > 33554432 then issue "MBRES001" (path <> "/byte_length") "artifact size limit" else pure ()
  media <- field path "media_type" value >>= str (path <> "/media_type")
  role <- field path "role" value >>= str (path <> "/role")
  _ <- tagged (path <> "/role") ["executable_model", "source_text", "evidence"] role
  _ <- tagged (path <> "/media_type")
    ["application/json", "text/plain; charset=utf-8", "application/pdf", "text/html"
    , "application/xml", "image/png", "image/jpeg"] media
  if (role == "source_text" && media /= "text/plain; charset=utf-8")
    || (role == "executable_model" && media /= "application/json")
    then issue "MBINV001" path "artifact role and media type disagree" else pure ()
  pure (Artifact digest size media role)

decodeSourceRecord :: Text -> J -> Either Failure SourceRecord
decodeSourceRecord path value = do
  _ <- obj path ["source_id", "work_id", "expression_id", "manifestation_id"
    , "artifact_digest", "source_type", "language", "jurisdiction", "identifiers"
    , "publisher_label", "locator", "dates"] value
  rid <- requiredText path "source_id" value
  work <- requiredText path "work_id" value
  expression <- requiredText path "expression_id" value
  manifestation <- requiredText path "manifestation_id" value
  traverse_ (uncurry requireId) [(path <> "/source_id", rid), (path <> "/work_id", work)
    , (path <> "/expression_id", expression), (path <> "/manifestation_id", manifestation)]
  artifact <- requiredText path "artifact_digest" value
  digestShape (path <> "/artifact_digest") artifact
  sourceType <- requiredText path "source_type" value
  _ <- tagged (path <> "/source_type") ["legislation", "judgment", "synthetic", "other"] sourceType
  language <- requiredText path "language" value
  jurisdiction <- requiredText path "jurisdiction" value
  ids <- field path "identifiers" value >>= arr (path <> "/identifiers")
  identifierTexts <- traverse (str (path <> "/identifiers")) ids
  uniqueSorted (path <> "/identifiers") identifierTexts
  traverse_ (\key -> traverse_ (str (path <> "/" <> key)) (lookupField key value))
    ["publisher_label", "locator"]
  dates <- field path "dates" value
  validateDates (path <> "/dates") dates
  pure (SourceRecord rid work expression manifestation artifact sourceType language jurisdiction value)

requiredText :: Text -> Text -> J -> Either Failure Text
requiredText path key value = field path key value >>= str (path <> "/" <> key)

validateDates :: Text -> J -> Either Failure ()
validateDates path value = do
  _ <- obj path ["publication", "decision", "revision", "commencement"
    , "effective_from", "effective_to", "retrieval", "supersession"] value
  pairs <- fields path value
  traverse_ (\(key, item) -> str (path <> "/" <> key) item >>= date (path <> "/" <> key)) pairs
  case (lookupField "effective_from" value, lookupField "effective_to" value) of
    (Just (JStr a), Just (JStr b)) | a > b -> issue "MBINV001" path "effective interval reversed"
    _ -> pure ()
  case (lookupField "publication" value, lookupField "supersession" value) of
    (Just (JStr a), Just (JStr b)) | a > b -> issue "MBINV001" path "supersession before publication"
    _ -> pure ()

date :: Text -> Text -> Either Failure ()
date path value = case Text.splitOn "-" value of
  [year,month,day]
    | Text.length year == 4 && Text.length month == 2 && Text.length day == 2
      && Text.all asciiDigit (year <> month <> day)
      && fromGregorianValid (toInteger (digits year)) (digits month) (digits day) /= Nothing -> pure ()
  _ -> issue "MBINV001" path "invalid ISO calendar date"
  where
    asciiDigit ch = ch >= '0' && ch <= '9'
    digits = Text.foldl' (\n ch -> n * 10 + ord ch - ord '0') 0

decodeDerivation :: Text -> J -> Either Failure Derivation
decodeDerivation path value = do
  _ <- obj path ["child_digest", "parent_digest", "tool_name", "tool_version", "configuration"] value
  child <- requiredText path "child_digest" value
  parent <- requiredText path "parent_digest" value
  digestShape (path <> "/child_digest") child
  digestShape (path <> "/parent_digest") parent
  tool <- requiredText path "tool_name" value
  version <- requiredText path "tool_version" value
  config <- requiredText path "configuration" value
  pure (Derivation child parent tool version config)

decodeMapping :: Text -> J -> Either Failure Mapping
decodeMapping path value = do
  _ <- obj path ["semantic_id", "artifact_digest", "source_id", "role", "span"] value
  sid <- requiredText path "semantic_id" value
  requireId (path <> "/semantic_id") sid
  artifact <- requiredText path "artifact_digest" value
  digestShape (path <> "/artifact_digest") artifact
  source <- requiredText path "source_id" value
  requireId (path <> "/source_id") source
  role <- requiredText path "role" value
  _ <- tagged (path <> "/role") ["definition", "requirement", "exception"
    , "presumption", "penalty_declaration", "penalty_term", "burden_annotation"
    , "standard_annotation", "supporting_context", "rule", "provision"] role
  sourceSpan <- field path "span" value >>= spanAt (path <> "/span")
  pure (Mapping sid artifact source role sourceSpan)

decodeScope :: J -> Either Failure Scope
decodeScope value = do
  let path = "/scope"
  _ <- obj path ["coverage_mode", "semantic_ids", "source_ids", "expression_ids"
    , "exclusions", "limitations", "unsupported_capabilities", "jurisdictions"
    , "subject_matters", "temporal_context"] value
  match path "coverage_mode" "enumerated_only" value
  ids <- scopeList path "semantic_ids" 8192 value
  sources <- scopeList path "source_ids" 1024 value
  expressions <- scopeList path "expression_ids" 1024 value
  exclusionsValue <- field path "exclusions" value >>= arr (path <> "/exclusions")
  if length exclusionsValue > 1024 then issue "MBRES001" (path <> "/exclusions") "count limit" else pure ()
  exclusions <- traverse (\(i, item) -> do
    let at = path <> "/exclusions/" <> Text.pack (show i)
    _ <- obj at ["exclusion_id", "reason"] item
    eid <- requiredText at "exclusion_id" item
    requireId (at <> "/exclusion_id") eid
    reason <- requiredText at "reason" item
    pure (eid, reason)) (zip [0 :: Int ..] exclusionsValue)
  uniqueSorted (path <> "/exclusions") (map fst exclusions)
  if any (`elem` ids) (map fst exclusions) then issue "MBINV001" path "exclusion overlaps positive semantic scope" else pure ()
  traverse_ (\key -> scopeList path key 1024 value >> pure ())
    ["limitations", "unsupported_capabilities", "jurisdictions", "subject_matters"]
  temporal <- field path "temporal_context" value
  _ <- obj (path <> "/temporal_context") ["kind", "date"] temporal
  kind <- requiredText (path <> "/temporal_context") "kind" temporal
  _ <- tagged (path <> "/temporal_context/kind") ["unspecified", "asserted_point_in_time"] kind
  case (kind, lookupField "date" temporal) of
    ("unspecified", Nothing) -> pure ()
    ("asserted_point_in_time", Just (JStr x)) -> date (path <> "/temporal_context/date") x
    _ -> issue "MBINV001" (path <> "/temporal_context") "date and temporal kind disagree"
  pure (Scope ids sources expressions exclusions value)

scopeList :: Text -> Text -> Int -> J -> Either Failure [Text]
scopeList path key limit parent = do
  values <- field path key parent >>= arr (path <> "/" <> key)
  if length values > limit then issue "MBRES001" (path <> "/" <> key) "count limit" else pure ()
  xs <- traverse (str (path <> "/" <> key)) values
  uniqueSorted (path <> "/" <> key) xs
  pure xs

validateStructure :: Core -> Either Failure ()
validateStructure core = do
  let arts = coreArtifacts core
      sources = coreSources core
      maps = coreMappings core
      derivs = coreDerivations core
      artIds = map artifactDigest arts
      sourceIds = map recordId sources
      expressionIds = sort (Set.toList (Set.fromList (map recordExpression sources)))
      modelArts = filter ((== "executable_model") . artifactRole) arts
      sourceMap = Map.fromList [(recordId s, s) | s <- sources]
      artMap = Map.fromList [(artifactDigest a, a) | a <- arts]
      mapOrder m = (mappingSemanticId m, mappingArtifact m, spanStart (mappingSpan m), spanEnd (mappingSpan m))
  uniqueSorted "/artifacts" artIds
  uniqueSorted "/legal_sources" sourceIds
  if map mapOrder maps /= sort (map mapOrder maps)
    then issue "MBINV001" "/semantic_mappings" "mappings not canonical order" else pure ()
  if length maps /= Set.size (Set.fromList (map mapOrder maps))
    then issue "MBINV001" "/semantic_mappings" "duplicate mapping" else pure ()
  if map (\d -> (derivationChild d, derivationParent d)) derivs /=
     sort (map (\d -> (derivationChild d, derivationParent d)) derivs)
    then issue "MBINV001" "/derivations" "derivations not canonical order" else pure ()
  if length derivs /= Set.size (Set.fromList (map (\d -> (derivationChild d, derivationParent d)) derivs))
    then issue "MBINV001" "/derivations" "duplicate derivation" else pure ()
  if sum (map artifactLength arts) > 134217728
    then issue "MBRES001" "/artifacts" "combined artifact size limit" else pure ()
  case modelArts of
    [a] | artifactDigest a == coreModelDigest core -> pure ()
    _ -> issue "MBINV001" "/executable_model" "exactly one referenced model artifact required"
  traverse_ (\s -> if Map.member (recordArtifact s) artMap then pure ()
    else issue "MBINV001" "/legal_sources" "missing source artifact") sources
  traverse_ (\s -> case Map.lookup (recordArtifact s) artMap of
    Just a | artifactRole a /= "executable_model" -> pure ()
    _ -> issue "MBINV001" "/legal_sources" "source record cannot name executable model") sources
  let referenced = Set.fromList (coreModelDigest core : map recordArtifact sources ++
        concat [[derivationChild d, derivationParent d] | d <- derivs])
  if any (`Set.notMember` referenced) artIds
    then issue "MBINV001" "/artifacts" "unreferenced artifact declaration" else pure ()
  let manifestations = map recordManifestation sources
      exprWorks = Map.fromListWith (++) [(recordExpression s, [(recordWork s, recordLanguage s)]) | s <- sources]
  if Set.size (Set.fromList manifestations) /= length manifestations
    then issue "MBINV001" "/legal_sources" "duplicate manifestation ID" else pure ()
  traverse_ (\xs -> if all (== headSafe xs) xs then pure ()
    else issue "MBINV001" "/legal_sources" "expression has conflicting work or language") (Map.elems exprWorks)
  if scopeSources (coreScope core) /= sourceIds
    then issue "MBINV001" "/scope/source_ids" "scope source inventory mismatch" else pure ()
  if scopeExpressions (coreScope core) /= expressionIds
    then issue "MBINV001" "/scope/expression_ids" "scope expression inventory mismatch" else pure ()
  traverse_ (\m -> case (Map.lookup (mappingSource m) sourceMap, Map.lookup (mappingArtifact m) artMap) of
    (Just s, Just a) | recordArtifact s == mappingArtifact m && artifactRole a == "source_text" -> pure ()
    _ -> issue "MBINV001" "/semantic_mappings" "mapping source or span-bearing artifact missing") maps
  traverse_ (\d -> if Map.member (derivationChild d) artMap && Map.member (derivationParent d) artMap
    then pure () else issue "MBINV001" "/derivations" "missing derivation artifact") derivs
  if hasCycle derivs then issue "MBINV001" "/derivations" "artifact derivation cycle" else pure ()
  let mappedIds = Set.fromList (map mappingSemanticId maps)
      scopedIds = Set.fromList (scopeIds (coreScope core))
  if mappedIds /= scopedIds then issue "MBINV001" "/semantic_mappings" "mapping and positive scope differ" else pure ()
  if any ((== "source_text") . artifactRole) arts &&
     any (\a -> artifactRole a == "source_text" &&
       artifactDigest a `notElem` map recordArtifact sources) arts
    then issue "MBINV001" "/artifacts" "text artifact has no source record" else pure ()
  if any (\d -> case Map.lookup (derivationChild d) artMap of
       Just a -> artifactRole a /= "source_text"
       Nothing -> True) derivs
    then issue "MBINV001" "/derivations" "derivation child must be extracted text" else pure ()
  if any (\d -> case Map.lookup (derivationParent d) artMap of
       Just a -> artifactRole a == "executable_model"
       Nothing -> True) derivs
    then issue "MBINV001" "/derivations" "derivation parent must be a source artifact" else pure ()
  where
    headSafe (x:_) = x
    headSafe [] = ("", "")

hasCycle :: [Derivation] -> Bool
hasCycle ds = any (visit Set.empty) (map derivationChild ds)
  where
    parents x = [derivationParent d | d <- ds, derivationChild d == x]
    visit seen x = Set.member x seen || any (visit (Set.insert x seen)) (parents x)

semanticIds :: J -> Either Failure [Text]
semanticIds request = do
  _ <- obj "/executable_model" ["protocol", "request_id", "operation", "input_schema"
    , "fragment", "source", "sources", "program", "registry", "root_rule", "facts"
    , "policy", "presumptions", "parser_result"] request
  match "/executable_model" "input_schema" "yuho.kernel-input/v1" request
  match "/executable_model" "protocol" "yuho.kernel-protocol/v1" request
  operation <- requiredText "/executable_model" "operation" request
  if operation == "evaluate" then pure () else issue "MBCAP001" "/executable_model/operation" "only evaluate artifacts supported"
  let roots = [value | key <- ["program", "registry", "presumptions"], Just value <- [lookupField key request]]
      ids = concatMap collect roots
  if null roots || null ids then issue "MBINV001" "/executable_model" "no executable semantic inventory" else pure ()
  traverse_ (requireId "/executable_model") ids
  if length ids /= Set.size (Set.fromList ids)
    then issue "MBINV001" "/executable_model" "duplicate executable semantic ID" else pure ()
  pure (sort ids)
  where
    collect (JObj xs) = [s | (key,JStr s) <- xs, key `elem`
      ["id", "exception_id", "penalty_id", "term_id", "presumption_id"]]
      ++ concatMap (collect . snd) xs
    collect (JArr xs) = concatMap collect xs
    collect _ = []

validateCore :: Core -> J -> Either Failure ()
validateCore core model = do
  validateExecutable (coreModelFragment core) model
  ids <- semanticIds model
  fragment <- requiredText "/executable_model" "fragment" model
  if fragment /= coreModelFragment core then issue "MBINV001" "/executable_model/fragment" "fragment mismatch" else pure ()
  if ids /= scopeIds (coreScope core)
    then issue "MBINV001" "/scope/semantic_ids" "scope differs from executable inventory" else pure ()

-- Package validation reuses only decoders and model validators; no rule is evaluated.
validateExecutable :: Text -> J -> Either Failure ()
validateExecutable fragment value
  | fragment `notElem` fragments = issue "MBCAP001" "/executable_model/fragment" "unknown kernel fragment"
  | otherwise = fromKernel $ case fragment of
  "ClosedBooleanBranches-v1" -> do
    request <- decodeRequest value
    validateInput (requestInput request)
  "AcyclicGuardedExceptions-v1" -> do
    request <- decodeExceptionRequest value
    _ <- validateGraph (exceptionRawGraph request)
    pure ()
  "TypedBooleanFacts-v1" -> do
    request <- decodeTypedRequest value
    _ <- validateTyped request
    pure ()
  "GuardedPenaltySelection-v1" -> do
    request <- decodePenaltyRequest value
    _ <- validatePenalties request
    pure ()
  "PenaltyTerms-v1" -> do
    request <- decodeTermsRequest value
    _ <- validateTerms request
    pure ()
  "SuppliedProofStatus-v1" -> do
    request <- decodeProofRequest value
    _ <- validateProofRequest request
    pure ()
  "RegisteredPresumptionDerivations-v1" -> do
    request <- decodePresumptionRequest value
    _ <- validatePresumptionRequest request
    pure ()
  _ -> Right ()
  where
    fromKernel = either (\d -> issue "MBINV001" ("/executable_model" <> diagPath d)
      ("kernel model validation: " <> diagCode d)) Right

scopeDigest :: Core -> Text
scopeDigest core = digestDomain "yuho.model-scope/v1" (encodeJson (scopeRaw (coreScope core)))
