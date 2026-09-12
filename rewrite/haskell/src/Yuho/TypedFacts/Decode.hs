{-# LANGUAGE OverloadedStrings #-}
module Yuho.TypedFacts.Decode (decodeTypedRequest) where

import Data.Char (ord)
import qualified Data.ByteString as BS
import Data.Foldable (traverse_)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Data.Time.Calendar (fromGregorianValid)
import Yuho.Core.Types (Diagnostic, diagnostic)
import Yuho.Exception.Decode (decodeExceptionRequest)
import Yuho.Exception.Types (ExceptionRequest(..))
import Yuho.Protocol.Decode
  ( asArray, asText, closed, countIds, decodePolicy, inputDigest, invalid, required )
import Yuho.Protocol.Json (J(..), lookupField, objectFields)
import Yuho.TypedFacts.Types

decodeTypedRequest :: J -> Either Diagnostic TypedRequest
decodeTypedRequest root = do
  closed "" ["protocol", "request_id", "operation", "input_schema", "fragment"
    , "sources", "policy", "registry", "root_rule", "facts"] root
  sourceValues <- required asArray "" "sources" root
  registryValues <- required asArray "" "registry" root
  (_, maxNodes) <- required (\_ -> decodePolicy) "" "policy" root
  if countIds (JArr sourceValues) + countIds (JArr registryValues) > maxNodes
    then Left (diagnostic "KINV004" "validate" "/registry" Nothing [])
    else pure ()
  bindings <- required (\_ -> decodeBindings) "" "facts" root
  (registry, declarations) <- unzip <$> traverse transformRule (zip [0 :: Int ..] registryValues)
  transformed <- replaceFields root
    [("fragment", JStr "AcyclicGuardedExceptions-v1")
    ,("facts", JObj [(key, JBool (bindingValue binding)) | (key, binding) <- Map.toList bindings])
    ,("registry", JArr registry)]
  request <- decodeExceptionRequest transformed
  pure (TypedRequest request {exceptionRequestDigest = inputDigest root}
    bindings (Map.fromList (concat declarations)))

decodeBindings :: J -> Either Diagnostic (Map.Map Text Binding)
decodeBindings value = do
  fields <- object "/facts" value
  Map.fromList <$> traverse (\(key, item) -> do
    if Text.null key then invalid "/facts" "empty leaf ID" else pure ()
    binding <- decodeBinding ("/facts/" <> key) item
    pure (key, binding)) fields

decodeBinding :: Text -> J -> Either Diagnostic Binding
decodeBinding pointer value = do
  closed pointer ["type", "value", "burden", "standard_of_proof", "provenance"] value
  typeName <- required asText pointer "type" value
  if typeName == "bool" then pure () else capability (pointer <> "/type") typeName
  truth <- required boolAt pointer "value" value
  metadata <- decodeMetadataFields pointer value
  provenance <- traverse (decodeProvenance (pointer <> "/provenance"))
    (lookupField "provenance" value)
  pure (Binding truth metadata provenance)

decodeMetadata :: Text -> J -> Either Diagnostic Metadata
decodeMetadata pointer value = do
  closed pointer ["burden", "standard_of_proof"] value
  fields <- object pointer value
  if null fields then invalid pointer "empty declared metadata" else pure ()
  decodeMetadataFields pointer value

decodeMetadataFields :: Text -> J -> Either Diagnostic Metadata
decodeMetadataFields pointer value = do
  burden <- traverse (decodeBurden (pointer <> "/burden")) (lookupField "burden" value)
  standard <- traverse (decodeStandard (pointer <> "/standard_of_proof"))
    (lookupField "standard_of_proof" value)
  pure (Metadata burden standard)

decodeBurden :: Text -> J -> Either Diagnostic Burden
decodeBurden pointer value = do
  closed pointer ["holder", "kind"] value
  holderName <- required asText pointer "holder" value
  kindName <- required asText pointer "kind" value
  holder <- case holderName of
    "prosecution" -> Right Prosecution
    "defence" -> Right Defence
    _ -> capability (pointer <> "/holder") holderName
  kind <- case kindName of
    "unspecified" -> Right Unspecified
    "legal" -> Right Legal
    "evidential" -> Right Evidential
    _ -> capability (pointer <> "/kind") kindName
  pure (Burden holder kind)

decodeStandard :: Text -> J -> Either Diagnostic Standard
decodeStandard pointer value = do
  name <- asText pointer value
  case name of
    "beyond_reasonable_doubt" -> Right BeyondReasonableDoubt
    "balance_of_probabilities" -> Right BalanceOfProbabilities
    _ -> capability pointer name

decodeProvenance :: Text -> J -> Either Diagnostic Provenance
decodeProvenance pointer value = do
  closed pointer ["source_label", "recorded_date", "jurisdiction"] value
  fields <- object pointer value
  if null fields then invalid pointer "empty provenance" else pure ()
  label <- optionalText pointer "source_label" 256 value
  recorded <- optionalText pointer "recorded_date" 10 value
  jurisdiction <- optionalText pointer "jurisdiction" 64 value
  traverse_ dateCheck recorded
  pure (Provenance label recorded jurisdiction)
  where
    dateCheck item = if validDate item then Right () else
      invalid (pointer <> "/recorded_date") "invalid Gregorian date"

optionalText :: Text -> Text -> Int -> J -> Either Diagnostic (Maybe Text)
optionalText pointer key limit value = traverse readText (lookupField key value)
  where
    readText item = do
      result <- asText (pointer <> "/" <> key) item
      if Text.null result || BS.length (Encoding.encodeUtf8 result) > limit
        then invalid (pointer <> "/" <> key) "empty or overlong string"
        else Right result

validDate :: Text -> Bool
validDate item = case Text.splitOn "-" item of
  [year, month, day]
    | Text.length year == 4 && Text.length month == 2 && Text.length day == 2
      && Text.all digit (year <> month <> day) ->
        case fromGregorianValid (digits year) (fromInteger (digits month))
          (fromInteger (digits day)) of
          Just _ -> True
          Nothing -> False
  _ -> False
  where
    digit ch = ch >= '0' && ch <= '9'
    digits = Text.foldl' (\n ch -> n * 10 + toInteger (ord ch - ord '0')) 0

transformRule :: (Int, J) -> Either Diagnostic (J, [(Text, Metadata)])
transformRule (index, value) = do
  let pointer = "/registry/" <> Text.pack (show index)
  program <- required (\_ -> Right) pointer "program" value
  (updated, declarations) <- transformProvision program
  result <- replaceFields value [("program", updated)]
  pure (result, declarations)

transformProvision :: J -> Either Diagnostic (J, [(Text, Metadata)])
transformProvision value = do
  requirements <- required asArray "" "requirements" value
  children <- required asArray "" "children" value
  (newRequirements, own) <- unzip <$> traverse transformRequirement requirements
  (newChildren, nested) <- unzip <$> traverse transformProvision children
  updated <- replaceFields value
    [("requirements", JArr newRequirements), ("children", JArr newChildren)]
  pure (updated, concat own ++ concat nested)

transformRequirement :: J -> Either Diagnostic (J, [(Text, Metadata)])
transformRequirement value = case lookupField "kind" value of
  Just (JStr "leaf") -> case lookupField "declared_metadata" value of
    Nothing -> Right (value, [])
    Just declaration -> do
      identifier <- required asText "" "id" value
      metadata <- decodeMetadata "/declared_metadata" declaration
      fields <- object "" value
      pure (JObj (filter ((/= "declared_metadata") . fst) fields), [(identifier, metadata)])
  _ -> case lookupField "members" value of
    Nothing -> Right (value, [])
    Just _ -> do
      members <- required asArray "" "members" value
      (updated, declarations) <- unzip <$> traverse transformRequirement members
      result <- replaceFields value [("members", JArr updated)]
      pure (result, concat declarations)

replaceFields :: J -> [(Text, J)] -> Either Diagnostic J
replaceFields value replacements = do
  fields <- object "" value
  pure (JObj [(key, maybe item id (lookup key replacements)) | (key, item) <- fields])

object :: Text -> J -> Either Diagnostic [(Text, J)]
object pointer value = maybe (invalid pointer "expected object") Right (objectFields value)

boolAt :: Text -> J -> Either Diagnostic Bool
boolAt _ (JBool value) = Right value
boolAt pointer _ = invalid pointer "expected Boolean"

capability :: Text -> Text -> Either Diagnostic a
capability pointer name = Left (diagnostic "KCAP001" "capability" pointer Nothing
  [("kind", name)])
