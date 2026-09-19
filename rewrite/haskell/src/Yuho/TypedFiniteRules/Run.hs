{-# LANGUAGE OverloadedStrings #-}
module Yuho.TypedFiniteRules.Run (runTypedFiniteLine, encodeTypedFiniteResult) where

import Control.Monad (unless, when)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Calendar (Day)
import Data.Time.Format (defaultTimeLocale, parseTimeM)
import Yuho.CoreYuho.TypedFinite
import Yuho.Exception.Types (Truth(..))
import Yuho.Protocol.Decode (inputDigest)
import Yuho.Protocol.Json
  ( J(..), arrayValue, encodeJson, integerValue, lookupField, objectFields, textValue )

runTypedFiniteLine :: J -> BS.ByteString
runTypedFiniteLine request =
  let requestId = maybe "?" id (lookupField "request_id" request >>= textValue)
      digest = inputDigest request
  in case decodeRequest request of
    Left reason -> reject requestId digest reason
    Right program -> case evaluateTypedFinite program of
      Left reason -> reject requestId digest reason
      Right result -> encodeTypedFiniteResult requestId digest result

reject :: Text -> Text -> Text -> BS.ByteString
reject requestId digest reason = encodeJson (JObj
  [("protocol",JStr "yuho.kernel-protocol/v1")
  ,("request_id",JStr requestId)
  ,("result_schema",JStr "yuho.kernel-result/v1")
  ,("fragment",JStr "TypedFiniteRules-v1")
  ,("input_digest",JStr digest)
  ,("status",JStr "rejected")
  ,("expressions",JArr [])
  ,("rules",JArr [])
  ,("propositions",JArr [])
  ,("diagnostics",JArr [JObj
      [("code",JStr "KTF001"),("stage",JStr "validate"),("severity",JStr "error")
      ,("path",JStr "/"),("span",JNull)
      ,("parameters",JObj [("reason",JStr reason)])]])]) <> "\n"

encodeTypedFiniteResult :: Text -> Text -> TypedFiniteResult -> BS.ByteString
encodeTypedFiniteResult requestId digest result = encodeJson (JObj
  [("protocol",JStr "yuho.kernel-protocol/v1")
  ,("request_id",JStr requestId)
  ,("result_schema",JStr "yuho.kernel-result/v1")
  ,("fragment",JStr "TypedFiniteRules-v1")
  ,("input_digest",JStr digest)
  ,("status",JStr "evaluated")
  ,("expressions",JArr (map expressionResult (finiteResultExpressions result)))
  ,("rules",JArr (map ruleResult (finiteResultRules result)))
  ,("propositions",JArr (map propositionResult (finiteResultPropositions result)))
  ,("diagnostics",JArr [])]) <> "\n"

expressionResult :: ExprObservation -> J
expressionResult row = JObj
  [("id",JStr (expressionLabel row)),("status",JStr (truthName (expressionStatus row)))
  ,("bindings",JArr [JObj [("variable",JStr variable),("entity",JStr entity)]
      | (variable,entity) <- expressionBindings row])
  ,("detail",JStr (expressionDetail row))]

ruleResult :: RuleObservation -> J
ruleResult row = JObj
  [("id",JStr (observedRule row))
  ,("polarity",JStr (if observedPolarity row == Establish then "establish" else "defeat"))
  ,("conclusion",JStr (observedProposition row))
  ,("status",JStr (truthName (observedStatus row)))
  ,("witness_bindings",JArr [JArr [JObj [("variable",JStr variable),("entity",JStr entity)]
      | (variable,entity) <- binding] | binding <- observedBindings row])
  ,("defeated_by",JArr (map JStr (observedDefeatedBy row)))]

propositionResult :: PropositionObservation -> J
propositionResult row = JObj
  [("id",JStr (observedPropositionId row))
  ,("status",JStr (truthName (propositionStatus row)))
  ,("state",JStr (propositionState row))
  ,("rules",JArr (map JStr (propositionRules row)))]

decodeRequest :: J -> Either Text TypedFiniteProgram
decodeRequest value = do
  fields value ["fragment","input_schema","operation","policy","program","protocol","request_id"]
  literal value "protocol" "yuho.kernel-protocol/v1"
  literal value "input_schema" "yuho.kernel-input/v1"
  literal value "operation" "evaluate"
  literal value "fragment" "TypedFiniteRules-v1"
  requestId <- textField value "request_id"
  boundedText "request_id" requestId
  policy <- field value "policy"
  fields policy ["max_nodes"]
  maximumNodes <- integerField policy "max_nodes"
  when (maximumNodes < 1 || maximumNodes > 2048) (Left "max_nodes outside 1..2048")
  program <- field value "program" >>= decodeProgram
  when (programSize program > fromInteger maximumNodes) (Left "normalized program exceeds max_nodes")
  validateDecoded program
  pure program

decodeProgram :: J -> Either Text TypedFiniteProgram
decodeProgram value = do
  fields value ["entities","entity_types","facts","id","limitations","predicates","priorities","propositions","requirements","rules","scalars","values"]
  identifier <- textField value "id"
  entityTypes <- arrayField value "entity_types" >>= traverse decodeEntityType
  entities <- arrayField value "entities" >>= traverse decodeEntity
  predicates <- arrayField value "predicates" >>= traverse decodePredicate
  scalars <- arrayField value "scalars" >>= traverse decodeScalar
  propositions <- arrayField value "propositions" >>= traverse asText
  requirements <- arrayField value "requirements" >>= traverse decodeRequirement
  rules <- arrayField value "rules" >>= traverse decodeRule
  priorities <- arrayField value "priorities" >>= traverse decodePriority
  facts <- arrayField value "facts" >>= traverse decodeFact
  values <- arrayField value "values" >>= traverse decodeValueRow
  limitations <- arrayField value "limitations" >>= traverse asText
  pure (TypedFiniteProgram identifier entityTypes entities predicates scalars propositions
    requirements rules priorities facts (Map.fromList values) [] limitations)

decodeEntityType :: J -> Either Text EntityTypeDecl
decodeEntityType value = EntityTypeDecl <$> asText value

decodeEntity :: J -> Either Text EntityDecl
decodeEntity value = do
  fields value ["id","type"]
  EntityDecl <$> textField value "id" <*> textField value "type"

decodePredicate :: J -> Either Text PredicateDecl
decodePredicate value = do
  fields value ["arguments","id","kind"]
  name <- textField value "id"
  arguments <- arrayField value "arguments" >>= traverse asText
  kindText <- textField value "kind"
  kindValue <- case kindText of
    "conduct" -> Right PredicateConduct
    "circumstance" -> Right PredicateCircumstance
    "mental-state" -> Right PredicateMentalState
    "relationship" -> Right PredicateRelationship
    _ -> Left "unknown predicate kind"
  pure (PredicateDecl name arguments kindValue)

decodeScalar :: J -> Either Text ScalarDecl
decodeScalar value = do
  fields value ["id","type"]
  ScalarDecl <$> textField value "id" <*> (field value "type" >>= decodeScalarType)

decodeScalarType :: J -> Either Text ScalarType
decodeScalarType value = do
  kindValue <- textField value "kind"
  case kindValue of
    "integer" -> fields value ["kind"] >> pure IntegerType
    "date" -> fields value ["kind"] >> pure DateType
    "enum" -> do
      fields value ["kind","members","name"]
      EnumType <$> textField value "name" <*> (arrayField value "members" >>= traverse asText)
    "money" -> do
      fields value ["currency","kind"]
      MoneyType <$> textField value "currency"
    _ -> Left "unknown scalar type"

decodeRequirement :: J -> Either Text (Text,FiniteExpr)
decodeRequirement value = do
  fields value ["expression","id"]
  (,) <$> textField value "id" <*> (field value "expression" >>= decodeExpression 0)

decodeExpression :: Int -> J -> Either Text FiniteExpr
decodeExpression depth value = do
  when (depth > 16) (Left "expression depth exceeds 16")
  kindValue <- textField value "kind"
  case kindValue of
    "predicate" -> do
      fields value ["arguments","kind","predicate"]
      PredicateExpr <$> textField value "predicate"
        <*> (arrayField value "arguments" >>= traverse decodeTerm)
    "comparison" -> do
      rawFields <- maybe (Left "comparison is not an object") Right (objectFields value)
      let names = map fst rawFields
      unless (sortNames names `elem`
        [sortNames ["kind","operation","left","right"],sortNames ["kind","operation","left","right","upper"]])
        (Left "comparison has unexpected fields")
      operation <- textField value "operation" >>= decodeComparison
      ComparisonExpr operation <$> textField value "left" <*> textField value "right"
        <*> optionalTextField value "upper"
    "all" -> AllExpr <$> members
    "any" -> AnyExpr <$> members
    "not" -> fields value ["kind","member"] >> (NotExpr <$> (field value "member" >>= decodeExpression (depth + 1)))
    "forall" -> quantifier ForallExpr
    "exists" -> quantifier ExistsExpr
    "at-least" -> cardinal AtLeast
    "at-most" -> cardinal AtMost
    "exactly" -> cardinal Exactly
    "reference" -> fields value ["id","kind"] >> (ReferenceExpr <$> textField value "id")
    _ -> Left "unknown expression kind"
  where
    members = fields value ["kind","members"] >>
      (arrayField value "members" >>= traverse (decodeExpression (depth + 1)))
    quantifier constructor = do
      fields value ["entity_type","kind","member","variable"]
      constructor <$> textField value "variable" <*> textField value "entity_type"
        <*> (field value "member" >>= decodeExpression (depth + 1))
    cardinal constructor = do
      fields value ["kind","members","threshold"]
      threshold <- integerField value "threshold"
      when (threshold < 0 || threshold > 2048) (Left "invalid cardinality threshold")
      CardinalityExpr constructor (fromInteger threshold)
        <$> (arrayField value "members" >>= traverse (decodeExpression (depth + 1)))

decodeTerm :: J -> Either Text Term
decodeTerm value = do
  fields value ["id","kind"]
  kindValue <- textField value "kind"
  identifier <- textField value "id"
  case kindValue of
    "entity" -> Right (EntityTerm identifier)
    "variable" -> Right (VariableTerm identifier)
    _ -> Left "unknown term kind"

decodeComparison :: Text -> Either Text Comparison
decodeComparison value = case value of
  "eq" -> Right Equal; "neq" -> Right NotEqual; "lt" -> Right LessThan
  "lte" -> Right LessEqual; "gt" -> Right GreaterThan; "gte" -> Right GreaterEqual
  "in-half-open" -> Right InHalfOpen
  _ -> Left "unknown comparison operation"

decodeRule :: J -> Either Text RuleDecl
decodeRule value = do
  raw <- maybe (Left "rule is not an object") Right (objectFields value)
  let names = sortNames (map fst raw)
  unless (names `elem` [sortNames ["body","conclusion","id","parameters","polarity"],
    sortNames ["body","citation","conclusion","id","parameters","polarity"]])
    (Left "rule has unexpected fields")
  polarity <- textField value "polarity" >>= \item -> case item of
    "establish" -> Right Establish; "defeat" -> Right Defeat; _ -> Left "unknown rule polarity"
  parameters <- arrayField value "parameters" >>= traverse decodeParameter
  RuleDecl <$> textField value "id" <*> pure parameters <*> pure polarity
    <*> textField value "conclusion" <*> (field value "body" >>= decodeExpression 0)
    <*> optionalTextField value "citation"

decodeParameter :: J -> Either Text (Text,Text)
decodeParameter value = do
  fields value ["entity_type","variable"]
  (,) <$> textField value "variable" <*> textField value "entity_type"

decodePriority :: J -> Either Text PriorityDecl
decodePriority value = fields value ["higher","lower"] >>
  (PriorityDecl <$> textField value "higher" <*> textField value "lower")

decodeFact :: J -> Either Text GroundFact
decodeFact value = do
  fields value ["arguments","predicate","reason","status"]
  status <- textField value "status" >>= decodeTruth
  GroundFact <$> textField value "predicate"
    <*> (arrayField value "arguments" >>= traverse asText)
    <*> pure status <*> textField value "reason"

decodeValueRow :: J -> Either Text (Text,ScalarValue)
decodeValueRow value = do
  fields value ["id","value"]
  (,) <$> textField value "id" <*> (field value "value" >>= decodeScalarValue)

decodeScalarValue :: J -> Either Text ScalarValue
decodeScalarValue value = do
  kindValue <- textField value "kind"
  case kindValue of
    "integer" -> fields value ["kind","value"] >> (IntegerValue <$> integerField value "value")
    "date" -> do
      fields value ["kind","value"]
      raw <- textField value "value"
      maybe (Left "invalid date value") (Right . DateValue) (parseDate raw)
    "enum" -> fields value ["kind","name","value"] >>
      (EnumValue <$> textField value "name" <*> textField value "value")
    "money" -> fields value ["currency","kind","minor_units"] >>
      (MoneyValue <$> textField value "currency" <*> integerField value "minor_units")
    "unresolved" -> do
      fields value ["expected_type","kind","reason"]
      ScalarUnresolved <$> textField value "reason" <*> (field value "expected_type" >>= decodeScalarType)
    _ -> Left "unknown scalar value kind"

decodeTruth :: Text -> Either Text Truth
decodeTruth "satisfied" = Right TrueValue
decodeTruth "not_satisfied" = Right FalseValue
decodeTruth "unresolved" = Right UnresolvedValue
decodeTruth _ = Left "unknown technical status"

validateDecoded :: TypedFiniteProgram -> Either Text ()
validateDecoded program = do
  let unique label values = unless (length values == Map.size (Map.fromList [(value,()) | value <- values]))
        (Left ("duplicate " <> label))
      types = [value | EntityTypeDecl value <- finiteEntityTypes program]
      entities = [(identifier,kindValue) | EntityDecl identifier kindValue <- finiteEntities program]
      predicates = finitePredicates program
      rules = finiteRules program
  unique "entity type" types
  unique "entity" (map fst entities)
  unique "predicate" (map predicateName predicates)
  unique "scalar" (map scalarName (finiteScalars program))
  unique "proposition" (finitePropositions program)
  unique "requirement" (map fst (finiteRequirements program))
  unique "rule" (map ruleName rules)
  unique "ground fact" [groundKey (groundPredicate fact) (groundArguments fact) | fact <- finiteFacts program]
  when (length types > 32 || length entities > 256 || length predicates > 128
    || length rules > 128 || length (finitePriorities program) > 256
    || length (finiteFacts program) > 1024) (Left "typed finite resource limit exceeded")
  unless (all ((`elem` types) . snd) entities) (Left "entity has unknown nominal type")
  unless (all (all (`elem` types) . predicateArguments) predicates)
    (Left "predicate has unknown argument type")
  unless (all ((`elem` finitePropositions program) . ruleConclusion) rules)
    (Left "rule has unknown conclusion")
  unless (not (null (finiteLimitations program))) (Left "limitations required")

programSize :: TypedFiniteProgram -> Int
programSize program = length (finiteEntityTypes program) + length (finiteEntities program)
  + length (finitePredicates program) + length (finiteScalars program)
  + length (finitePropositions program) + length (finiteRequirements program)
  + length (finiteRules program) + length (finitePriorities program)
  + length (finiteFacts program) + Map.size (finiteValues program)

fields :: J -> [Text] -> Either Text ()
fields value expected = do
  actual <- maybe (Left "expected object") (Right . map fst) (objectFields value)
  unless (sortNames actual == sortNames expected) (Left "object has missing or unexpected fields")

sortNames :: [Text] -> [Text]
sortNames = Set.toAscList . Set.fromList

field :: J -> Text -> Either Text J
field value name = maybe (Left ("missing field " <> name)) Right (lookupField name value)

textField :: J -> Text -> Either Text Text
textField value name = field value name >>= asText

optionalTextField :: J -> Text -> Either Text (Maybe Text)
optionalTextField value name = case lookupField name value of
  Nothing -> Right Nothing
  Just item -> Just <$> asText item

integerField :: J -> Text -> Either Text Integer
integerField value name = field value name >>= \item -> maybe
  (Left ("field is not integer: " <> name)) Right (integerValue item)

arrayField :: J -> Text -> Either Text [J]
arrayField value name = field value name >>= \item -> maybe
  (Left ("field is not array: " <> name)) Right (arrayValue item)

asText :: J -> Either Text Text
asText value = maybe (Left "expected text") Right (textValue value)

literal :: J -> Text -> Text -> Either Text ()
literal value name expected = do
  actual <- textField value name
  unless (actual == expected) (Left ("unsupported " <> name))

boundedText :: Text -> Text -> Either Text ()
boundedText label value = when (Text.null value || Text.length value > 128)
  (Left (label <> " length outside 1..128"))

parseDate :: Text -> Maybe Day
parseDate = parseTimeM True defaultTimeLocale "%F" . Text.unpack
