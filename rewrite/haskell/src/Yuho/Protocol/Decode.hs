{-# LANGUAGE OverloadedStrings #-}
module Yuho.Protocol.Decode
  ( decodeRequest, inputDigest, sha256Text, countIds, decodeSource, decodePolicy
  , decodeFacts, decodeProvision, decodeSpan, closed, required, asText, asArray
  , invalid
  ) where

import Crypto.Hash (Digest, SHA256(..), hashWith)
import Data.Char (ord)
import qualified Data.ByteString as BS
import Data.Map.Strict (Map)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Data.Time.Calendar (Day, fromGregorianValid)
import Yuho.Core.Source (validSourcePath, validateSpan)
import Yuho.Core.Types
import Yuho.Protocol.Json

sha256Text :: BS.ByteString -> Text
sha256Text bytes = Text.pack (show (hashWith SHA256 bytes :: Digest SHA256))

inputDigest :: J -> Text
inputDigest root =
  let keys = case lookupField "operation" root >>= textValue of
        Just "validate" -> ["input_schema", "fragment", "source", "parser_result", "policy"]
        _ | (lookupField "fragment" root >>= textValue) `elem`
              [Just "AcyclicGuardedExceptions-v1", Just "TypedBooleanFacts-v1"] ->
          ["input_schema", "fragment", "sources", "registry", "root_rule", "facts", "policy"]
        _ -> ["input_schema", "fragment", "source", "program", "facts", "policy"]
      fields = traverse (\key -> (,) key <$> lookupField key root) keys
  in maybe (sha256Text BS.empty) (sha256Text . encodeJson . JObj) fields

decodeRequest :: J -> Either Diagnostic Request
decodeRequest root = do
  received <- required asText "" "protocol" root
  if received /= "yuho.kernel-protocol/v1"
    then Left (diagnostic "KPROT001" "protocol" "/protocol" Nothing
               [("received", received)])
    else pure ()
  closed "" ["protocol", "request_id", "operation", "input_schema", "fragment", "source", "policy", "program", "facts", "parser_result"] root
  identifier <- required asText "" "request_id" root
  if case Text.uncons identifier of
       Just (first, rest) -> not (asciiUpper first && Text.length rest == 2 && Text.all asciiDigit rest)
       Nothing -> True
    then invalid "/request_id" "invalid request ID"
    else pure ()
  schema <- required asText "" "input_schema" root
  if schema /= "yuho.kernel-input/v1" then invalid "/input_schema" "unsupported input schema" else pure ()
  fragment <- required asText "" "fragment" root
  if fragment /= "ClosedBooleanBranches-v1"
    then Left (diagnostic "KCAP001" "capability" "/fragment" Nothing [("kind", fragment)])
    else pure ()
  source <- required (\_ -> decodeSource) "" "source" root
  (day, maxNodes) <- required (\_ -> decodePolicy) "" "policy" root
  operation <- required asText "" "operation" root
  kernelInput <- case operation of
    "evaluate" -> do
      absent "/parser_result" "parser_result" root
      programValue <- required (\_ -> Right) "" "program" root
      if countIds programValue > maxNodes
        then Left (diagnostic "KINV004" "validate" "/program" Nothing [])
        else pure ()
      program <- decodeProvision source "/program" programValue
      facts <- required (\_ -> decodeFacts) "" "facts" root
      pure (Evaluate source program facts day maxNodes)
    "validate" -> do
      absent "/program" "program" root
      absent "/facts" "facts" root
      (accepted, diags) <- required (\_ -> decodeParserResult source) "" "parser_result" root
      pure (Validate source accepted diags day)
    _ -> invalid "/operation" "unsupported operation"
  pure (Request identifier kernelInput (inputDigest root))
  where
    asciiUpper ch = ch >= 'A' && ch <= 'Z'
    asciiDigit ch = ch >= '0' && ch <= '9'

countIds :: J -> Int
countIds value = case value of
  JObj fields -> (if lookup "id" fields == Nothing then 0 else 1)
    + sum (map (countIds . snd) fields)
  JArr values -> sum (map countIds values)
  _ -> 0

decodeSource :: J -> Either Diagnostic Source
decodeSource value = do
  closed "/source" ["path", "text", "sha256"] value
  path <- required asText "/source" "path" value
  original <- required asText "/source" "text" value
  digest <- required asText "/source" "sha256" value
  let bytes = Encoding.encodeUtf8 original
  if not (validSourcePath path) then invalid "/source/path" "path must be relative POSIX" else pure ()
  if sha256Text bytes /= digest then invalid "/source/sha256" "source SHA-256 mismatch" else pure ()
  pure (Source path original bytes digest)

decodePolicy :: J -> Either Diagnostic (Day, Int)
decodePolicy value = do
  closed "/policy" ["reference_date", "max_nodes"] value
  dateText <- required asText "/policy" "reference_date" value
  date <- case Text.splitOn "-" dateText of
    [year, month, day]
      | Text.length year == 4 && Text.length month == 2 && Text.length day == 2
        && Text.all asciiDigit (year <> month <> day) ->
          maybe (invalid "/policy/reference_date" "impossible calendar date") Right
            (fromGregorianValid (readDigits year) (fromInteger (readDigits month)) (fromInteger (readDigits day)))
    _ -> invalid "/policy/reference_date" "date must be YYYY-MM-DD"
  number <- required asInt "/policy" "max_nodes" value
  if number < 1 || number > 1024 then invalid "/policy/max_nodes" "max_nodes outside 1..1024" else pure ()
  pure (date, number)
  where
    asciiDigit ch = ch >= '0' && ch <= '9'
    readDigits = Text.foldl' (\acc digit -> acc * 10 + toInteger (ord digit - ord '0')) 0

decodeFacts :: J -> Either Diagnostic (Map Text Bool)
decodeFacts value = do
  fields <- asObject "/facts" value
  pairs <- traverse (\(key, item) -> (,) key <$> asBool ("/facts/" <> key) item) fields
  pure (Map.fromList pairs)

decodeParserResult :: Source -> J -> Either Diagnostic (Bool, [Diagnostic])
decodeParserResult source value = do
  closed "/parser_result" ["accepted", "diagnostics", "source_version"] value
  accepted <- required asBool "/parser_result" "accepted" value
  version <- required asText "/parser_result" "source_version" value
  if version /= "yuho-5.1" then invalid "/parser_result/source_version" "unsupported parser source version" else pure ()
  items <- required asArray "/parser_result" "diagnostics" value
  diagnostics <- traverse (\(index, item) -> decodeDiagnostic source
    ("/parser_result/diagnostics/" <> Text.pack (show index)) item) (zip [0 :: Int ..] items)
  if accepted && any ((== "error") . diagSeverity) diagnostics
    then Left (diagnostic "KINV004" "validate" "/parser_result/accepted" Nothing [])
    else pure (accepted, diagnostics)

decodeDiagnostic :: Source -> Text -> J -> Either Diagnostic Diagnostic
decodeDiagnostic source pointer value = do
  closed pointer ["code", "stage", "severity", "path", "span", "parameters"] value
  code <- required asText pointer "code" value
  stage <- required asText pointer "stage" value
  severity <- required asText pointer "severity" value
  path <- required asText pointer "path" value
  if severity `elem` ["error", "warning", "info"] then pure ()
    else invalid (pointer <> "/severity") "unsupported diagnostic severity"
  spanValue <- required (\_ -> Right) pointer "span" value
  sourceSpan <- case spanValue of
    JNull -> Right Nothing
    other -> Just <$> decodeSpan source (pointer <> "/span") other
  parameterValue <- required asObject pointer "parameters" value
  parameters <- traverse (\(key, item) -> (,) key <$>
    asText (pointer <> "/parameters/" <> key) item) parameterValue
  pure (Diagnostic code stage severity path sourceSpan parameters)

decodeProvision :: Source -> Text -> J -> Either Diagnostic Provision
decodeProvision source pointer value = do
  closed pointer ["id", "path", "span", "definitions", "requirements", "children"] value
  identifier <- required asText pointer "id" value
  path <- required decodePath pointer "path" value
  sourceSpan <- required (decodeSpan source) pointer "span" value
  definitions <- required asBool pointer "definitions" value
  reqValues <- required asArray pointer "requirements" value
  childValues <- required asArray pointer "children" value
  if Text.null identifier then invalid (pointer <> "/id") "empty ID" else pure ()
  if definitions && (not (null reqValues) || not (null childValues))
    then Left (diagnostic "KINV004" "validate" (pointer <> "/definitions") (Just sourceSpan) [])
    else pure ()
  requirements <- traverse (\(index, item) -> decodeRequirement source
    (pointer <> "/requirements/" <> Text.pack (show index)) item) (zip [0 :: Int ..] reqValues)
  children <- traverse (\(index, item) -> decodeProvision source
    (pointer <> "/children/" <> Text.pack (show index)) item) (zip [0 :: Int ..] childValues)
  if any (not . inside sourceSpan . requirementSpan) requirements
     || any (not . inside sourceSpan . provisionSpan) children
    then Left (diagnostic "KINV003" "validate" (pointer <> "/span") (Just sourceSpan) [])
    else pure ()
  pure (Provision identifier path sourceSpan definitions requirements children pointer)

decodeRequirement :: Source -> Text -> J -> Either Diagnostic Requirement
decodeRequirement source pointer value = do
  identifier <- required asText pointer "id" value
  kindText <- required asText pointer "kind" value
  path <- required decodePath pointer "path" value
  sourceSpan <- required (decodeSpan source) pointer "span" value
  kind <- case kindText of
    "leaf" -> Right Leaf
    "all" -> Right All
    "any" -> Right Any
    _ -> Left (diagnostic "KCAP001" "capability" (pointer <> "/kind")
                (Just sourceSpan) [("kind", kindText)])
  case kind of
    Leaf -> do
      if lookupField "members" value /= Nothing
        then Left (diagnostic "KINV004" "validate" (pointer <> "/members") (Just sourceSpan) [])
        else pure ()
      closed pointer ["id", "kind", "path", "span"] value
      if Text.null identifier then invalid (pointer <> "/id") "empty ID" else pure ()
      pure (Requirement kind identifier path sourceSpan [] pointer)
    All -> group kind identifier path sourceSpan
    Any -> group kind identifier path sourceSpan
  where
    group kind identifier path sourceSpan = do
      closed pointer ["id", "kind", "path", "span", "members"] value
      items <- required asArray pointer "members" value
      if Text.null identifier then invalid (pointer <> "/id") "empty ID" else pure ()
      if null items then Left (diagnostic "KINV004" "validate"
        (pointer <> "/members") (Just sourceSpan) []) else pure ()
      members <- traverse (\(index, item) -> decodeRequirement source
        (pointer <> "/members/" <> Text.pack (show index)) item) (zip [0 :: Int ..] items)
      if any (not . inside sourceSpan . requirementSpan) members
        then Left (diagnostic "KINV003" "validate" (pointer <> "/span") (Just sourceSpan) [])
        else pure (Requirement kind identifier path sourceSpan members pointer)

inside :: Span -> Span -> Bool
inside parent child = spanStart parent <= spanStart child && spanEnd child <= spanEnd parent

decodePath :: Text -> J -> Either Diagnostic [Text]
decodePath pointer value = do
  items <- asArray pointer value
  path <- traverse (asText pointer) items
  if null path || any Text.null path then invalid pointer "empty provision path" else pure path

decodeSpan :: Source -> Text -> J -> Either Diagnostic Span
decodeSpan source pointer value = do
  closed pointer ["start", "end", "start_line", "start_col", "end_line", "end_col"] value
  start <- required asInt pointer "start" value
  end <- required asInt pointer "end" value
  startLine <- required asInt pointer "start_line" value
  startCol <- required asInt pointer "start_col" value
  endLine <- required asInt pointer "end_line" value
  endCol <- required asInt pointer "end_col" value
  let sourceSpan = Span start end startLine startCol endLine endCol
  if validateSpan source sourceSpan then Right sourceSpan
    else Left (diagnostic "KINV003" "validate" pointer (Just sourceSpan) [])

closed :: Text -> [Text] -> J -> Either Diagnostic ()
closed pointer allowed value = do
  fields <- asObject pointer value
  case filter (\(key, _) -> key `notElem` allowed) fields of
    (unknown, _) : _ -> Left (diagnostic "KINV004" "validate" (pointer <> "/" <> unknown) Nothing [])
    [] -> Right ()

absent :: Text -> Text -> J -> Either Diagnostic ()
absent pointer key value = case lookupField key value of
  Nothing -> Right ()
  Just _ -> Left (diagnostic "KINV004" "validate" pointer Nothing [])

required :: (Text -> J -> Either Diagnostic a) -> Text -> Text -> J -> Either Diagnostic a
required parser pointer key value = case lookupField key value of
  Nothing -> invalid (pointer <> "/" <> key) "missing field"
  Just item -> parser (pointer <> "/" <> key) item

asText :: Text -> J -> Either Diagnostic Text
asText _ (JStr value) = Right value
asText pointer _ = invalid pointer "expected string"

asBool :: Text -> J -> Either Diagnostic Bool
asBool _ (JBool value) = Right value
asBool pointer _ = invalid pointer "expected Boolean"

asInt :: Text -> J -> Either Diagnostic Int
asInt pointer (JNum value)
  | value >= toInteger (minBound :: Int) && value <= toInteger (maxBound :: Int) =
      Right (fromInteger value)
  | otherwise = invalid pointer "integer outside host range"
asInt pointer _ = invalid pointer "expected integer"

asArray :: Text -> J -> Either Diagnostic [J]
asArray _ (JArr values) = Right values
asArray pointer _ = invalid pointer "expected array"

asObject :: Text -> J -> Either Diagnostic [(Text, J)]
asObject _ (JObj fields) = Right fields
asObject pointer _ = invalid pointer "expected object"

invalid :: Text -> Text -> Either Diagnostic a
invalid pointer reason = Left (diagnostic "KDEC001" "decode" pointer Nothing [("reason", reason)])
