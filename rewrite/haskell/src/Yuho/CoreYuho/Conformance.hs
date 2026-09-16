{-# LANGUAGE OverloadedStrings #-}
module Yuho.CoreYuho.Conformance
  ( evaluateConformanceBytes ) where

import qualified Data.ByteString as BS
import Data.List (sort)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Data.Maybe (listToMaybe)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.CoreYuho.Semantics
import Yuho.CoreYuho.Types
import Yuho.Exception.Types (Truth(..))
import Yuho.Presumption.Types (DerivationState(..))
import Yuho.Protocol.Json

data Vector
  = AggregateVector Text Text [Truth]
  | RequirementVector Text Text CoreRequirement (Map Text Truth)
  | ExceptionVector Text Truth [Truth]
  | PresumptionVector Text Truth Truth
  | ScopeVector Text CoreScopeKey Text [ScopeAssignment]
  | CaseVector Text [AllegationVector]
  | TemporalVector Text Integer [CoreInterval]

data ScopeAssignment = ScopeAssignment CoreScopeKey Text Truth
data AllegationVector = AllegationVector Text CoreRequirement (Map Text Truth)

evaluateConformanceBytes :: BS.ByteString -> Either Text BS.ByteString
evaluateConformanceBytes bytes = do
  value <- decodeJson bytes
  root <- exactObject "" ["schema","vectors"] value
  schema <- requiredText "/schema" "schema" root
  if schema /= "yuho.core-conformance-v0.1"
    then Left "unsupported conformance schema"
    else pure ()
  rawVectors <- requiredArray "/vectors" "vectors" root
  vectors <- traverse (uncurry parseVector) (zip [0 :: Int ..] rawVectors)
  results <- traverse evaluateVector vectors
  pure (encodeJson (JObj
    [ ("results",JArr results)
    , ("schema",JStr "yuho.core-conformance-results-v0.1")
    ]))

parseVector :: Int -> J -> Either Text Vector
parseVector index value = do
  fields <- objectFields value `orElse` (path <> ": expected object")
  kind <- fieldText path "kind" fields
  let identifier = fieldText path "id" fields
  case kind of
    "all" -> AggregateVector <$> identifier <*> pure kind
      <*> statusArray path fields "values" ["id","kind","values"]
    "any" -> AggregateVector <$> identifier <*> pure kind
      <*> statusArray path fields "values" ["id","kind","values"]
    "branch" -> AggregateVector <$> identifier <*> pure kind
      <*> statusArray path fields "values" ["id","kind","values"]
    "guard" -> AggregateVector <$> identifier <*> pure kind
      <*> statusArray path fields "values" ["id","kind","values"]
    "requirement" -> requirement kind fields
    "definition" -> requirement kind fields
    "exception" -> do
      exactFields path ["guards","id","kind","ordinary"] fields
      ExceptionVector <$> identifier <*> fieldStatus path "ordinary" fields
        <*> statusArrayUnchecked path fields "guards"
    "presumption" -> do
      exactFields path ["id","kind","rebuttal","trigger"] fields
      PresumptionVector <$> identifier <*> fieldStatus path "trigger" fields
        <*> fieldStatus path "rebuttal" fields
    "scope" -> do
      exactFields path ["assignments","id","input","kind","selected"] fields
      ScopeVector <$> identifier <*> (field path "selected" fields >>= parseScopeKey (path <> "/selected"))
        <*> fieldText path "input" fields
        <*> (fieldArray path "assignments" fields >>= traverse (parseScopeAssignment path))
    "case" -> do
      exactFields path ["allegations","id","kind"] fields
      CaseVector <$> identifier
        <*> (fieldArray path "allegations" fields >>= traverse (parseAllegation path))
    "temporal" -> do
      exactFields path ["date","id","intervals","kind"] fields
      TemporalVector <$> identifier <*> fieldInteger path "date" fields
        <*> (fieldArray path "intervals" fields >>= traverse (parseInterval path))
    _ -> Left (path <> ": unsupported construct kind " <> kind)
  where
    path = "/vectors/" <> Text.pack (show index)
    requirement kind fields = do
      exactFields path ["assignments","expression","id","kind","origin"] fields
      RequirementVector <$> fieldText path "id" fields <*> pure kind
        <*> (field path "expression" fields >>= parseRequirement (path <> "/expression"))
        <*> (field path "assignments" fields >>= parseAssignments (path <> "/assignments"))

evaluateVector :: Vector -> Either Text J
evaluateVector vector = case vector of
  AggregateVector identifier kind values -> do
    result <- case kind of
      "all" -> Right (truthName (allTruth values))
      "any" -> Right (truthName (anyTruth values))
      "branch" -> Right (truthName (branchTruth values))
      "guard" -> Right (truthName (guardedTruth values))
      _ -> Left "internal aggregate kind"
    pure (row identifier result)
  RequirementVector identifier _ expression assignments ->
    case evaluateRequirement assignments expression of
      Left missing -> Left (identifier <> ": missing primitive " <> missing)
      Right value -> Right (row identifier (truthName value))
  ExceptionVector identifier ordinary guards ->
    Right (row identifier (truthName (evaluateGuardedBranch ordinary guards)))
  PresumptionVector identifier trigger rebuttal ->
    Right (row identifier (stateName (presumptionState trigger rebuttal)))
  ScopeVector identifier selected input assignments -> case listToMaybe
      [value | ScopeAssignment key item value <- assignments,
        key == selected, item == input] of
    Nothing -> Left (identifier <> ": selected scoped input is missing")
    Just value -> Right (row identifier (truthName value))
  CaseVector identifier allegations -> do
    results <- traverse allegationResult allegations
    Right (row identifier (Text.intercalate ";" results))
  TemporalVector identifier date intervals -> Right $ row identifier $ case
      selectTemporal date intervals of
    Right selected -> "selected:" <> coreIntervalExpression selected
    Left failure -> failure
  where
    allegationResult (AllegationVector item expression assignments) =
      case evaluateRequirement assignments expression of
        Left missing -> Left ("case allegation " <> item
          <> " missing primitive " <> missing)
        Right value -> Right (item <> "=" <> truthName value)
    row identifier result = JObj [("id",JStr identifier),("result",JStr result)]

parseRequirement :: Text -> J -> Either Text CoreRequirement
parseRequirement path value = do
  fields <- objectFields value `orElse` (path <> ": expected object")
  kind <- fieldText path "kind" fields
  identifier <- fieldText path "id" fields
  case kind of
    "input" -> do
      exactFields path ["id","kind"] fields
      Right (CoreInput identifier "" Nothing)
    "all" -> do
      exactFields path ["id","kind","members"] fields
      CoreAll identifier <$> (fieldArray path "members" fields
        >>= traverse (parseRequirement (path <> "/members")))
    "any" -> do
      exactFields path ["id","kind","members"] fields
      CoreAny identifier <$> (fieldArray path "members" fields
        >>= traverse (parseRequirement (path <> "/members")))
    _ -> Left (path <> ": unsupported requirement kind " <> kind)

parseAssignments :: Text -> J -> Either Text (Map Text Truth)
parseAssignments path value = do
  fields <- objectFields value `orElse` (path <> ": expected object")
  pairs <- traverse parse fields
  pure (Map.fromList pairs)
  where
    parse (identifier,statusValue) = do
      status <- textValue statusValue `orElse` (path <> "/" <> identifier <> ": expected status")
      parsedStatus <- parseStatus (path <> "/" <> identifier) status
      pure (identifier,parsedStatus)

parseScopeKey :: Text -> J -> Either Text CoreScopeKey
parseScopeKey path value = do
  fields <- exactObject path ["actor","context","instance","role"] value
  CoreScopeKey <$> fieldText path "actor" fields <*> fieldText path "role" fields
    <*> fieldText path "context" fields <*> fieldText path "instance" fields

parseScopeAssignment :: Text -> J -> Either Text ScopeAssignment
parseScopeAssignment parent value = do
  let path = parent <> "/assignments"
  fields <- exactObject path ["input","key","status"] value
  ScopeAssignment <$> (field path "key" fields >>= parseScopeKey (path <> "/key"))
    <*> fieldText path "input" fields <*> fieldStatus path "status" fields

parseAllegation :: Text -> J -> Either Text AllegationVector
parseAllegation parent value = do
  let path = parent <> "/allegations"
  fields <- exactObject path ["assignments","expression","id"] value
  AllegationVector <$> fieldText path "id" fields
    <*> (field path "expression" fields >>= parseRequirement (path <> "/expression"))
    <*> (field path "assignments" fields >>= parseAssignments (path <> "/assignments"))

parseInterval :: Text -> J -> Either Text CoreInterval
parseInterval parent value = do
  let path = parent <> "/intervals"
  fields <- exactObject path ["expression","from","supersedes","to","version"] value
  CoreInterval <$> fieldText path "expression" fields <*> fieldInteger path "from" fields
    <*> optionalInteger path "to" fields <*> fieldText path "version" fields
    <*> optionalText path "supersedes" fields

statusArray :: Text -> [(Text,J)] -> Text -> [Text] -> Either Text [Truth]
statusArray path fields name allowed = do
  exactFields path allowed fields
  statusArrayUnchecked path fields name

statusArrayUnchecked :: Text -> [(Text,J)] -> Text -> Either Text [Truth]
statusArrayUnchecked path fields name =
  fieldArray path name fields >>= traverse parse
  where
    parse value = do
      raw <- textValue value `orElse` (path <> "/" <> name <> ": expected status")
      parseStatus (path <> "/" <> name) raw

fieldStatus :: Text -> Text -> [(Text,J)] -> Either Text Truth
fieldStatus path name fields = fieldText path name fields >>= parseStatus (path <> "/" <> name)

parseStatus :: Text -> Text -> Either Text Truth
parseStatus _ "satisfied" = Right TrueValue
parseStatus _ "not_satisfied" = Right FalseValue
parseStatus _ "unresolved" = Right UnresolvedValue
parseStatus path value = Left (path <> ": unsupported status " <> value)

truthName :: Truth -> Text
truthName TrueValue = "satisfied"
truthName FalseValue = "not_satisfied"
truthName UnresolvedValue = "unresolved"

stateName :: DerivationState -> Text
stateName Active = "active"
stateName Inactive = "inactive"
stateName Rebutted = "rebutted"
stateName RouteUnresolved = "unresolved"

exactObject :: Text -> [Text] -> J -> Either Text [(Text,J)]
exactObject path allowed value = do
  fields <- objectFields value `orElse` (path <> ": expected object")
  exactFields path allowed fields
  pure fields

exactFields :: Text -> [Text] -> [(Text,J)] -> Either Text ()
exactFields path allowed fields =
  let actual = sort (map fst fields)
      expected = sort allowed
  in if actual == expected then Right ()
     else Left (path <> ": expected fields " <> Text.intercalate "," expected)

field :: Text -> Text -> [(Text,J)] -> Either Text J
field path name fields = maybe (Left (path <> ": missing " <> name)) Right (lookup name fields)

fieldText :: Text -> Text -> [(Text,J)] -> Either Text Text
fieldText path name fields = field path name fields >>= \value ->
  textValue value `orElse` (path <> "/" <> name <> ": expected string")

requiredText :: Text -> Text -> [(Text,J)] -> Either Text Text
requiredText = fieldText

fieldInteger :: Text -> Text -> [(Text,J)] -> Either Text Integer
fieldInteger path name fields = field path name fields >>= \value ->
  integerValue value `orElse` (path <> "/" <> name <> ": expected integer")

fieldArray :: Text -> Text -> [(Text,J)] -> Either Text [J]
fieldArray path name fields = field path name fields >>= \value ->
  arrayValue value `orElse` (path <> "/" <> name <> ": expected array")

requiredArray :: Text -> Text -> [(Text,J)] -> Either Text [J]
requiredArray = fieldArray

optionalInteger :: Text -> Text -> [(Text,J)] -> Either Text (Maybe Integer)
optionalInteger path name fields = field path name fields >>= \value -> case value of
  JNull -> Right Nothing
  _ -> Just <$> (integerValue value `orElse` (path <> "/" <> name <> ": expected integer or null"))

optionalText :: Text -> Text -> [(Text,J)] -> Either Text (Maybe Text)
optionalText path name fields = field path name fields >>= \value -> case value of
  JNull -> Right Nothing
  _ -> Just <$> (textValue value `orElse` (path <> "/" <> name <> ": expected string or null"))

orElse :: Maybe a -> Text -> Either Text a
orElse value issue = maybe (Left issue) Right value
