{-# LANGUAGE OverloadedStrings #-}

module Euclid.Import.JSONLD
    ( importJsonLdToEuclid
    ) where

import Control.Applicative ((<|>))
import qualified Data.Aeson as Aeson
import Data.Aeson.Key (Key, fromText, toText)
import qualified Data.Aeson.KeyMap as KeyMap
import qualified Data.Map.Strict as Map
import Data.Maybe (fromMaybe, mapMaybe)
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as TE
import qualified Data.Vector as Vector
import Euclid.Model.Types (Diagnostic(..), DiagnosticLevel(..))

data JsonLdNode = JsonLdNode
    { nodeIdentifier :: Text
    , nodeTypeName :: Text
    , nodeTimeline :: Text
    , nodeStart :: Text
    , nodeEnd :: Text
    , nodeAttributes :: [(Text, Aeson.Value)]
    , nodeRelationships :: [(Text, Text)]
    }

importJsonLdToEuclid :: Text -> Either [Diagnostic] Text
importJsonLdToEuclid input =
    case Aeson.eitherDecodeStrict' (TE.encodeUtf8 input) of
        Left err ->
            Left [Diagnostic DiagnosticError "import:jsonld" (T.pack err) Nothing]
        Right value ->
            case extractObjects value of
                [] ->
                    Left [Diagnostic DiagnosticError "import:jsonld" "no object records found in JSON-LD input" Nothing]
                objects ->
                    let indexedObjects = zip [1 :: Int ..] objects
                        identifierMap = buildIdentifierMap indexedObjects
                        nodes = map (buildNode identifierMap) indexedObjects
                     in Right (renderJsonLd nodes)

extractObjects :: Aeson.Value -> [Aeson.Object]
extractObjects (Aeson.Array values) = mapMaybe unwrapObject (Vector.toList values)
extractObjects (Aeson.Object obj) =
    case KeyMap.lookup "@graph" obj of
        Just (Aeson.Array values) -> mapMaybe unwrapObject (Vector.toList values)
        _ -> maybe [] pure (unwrapObject (Aeson.Object obj))
extractObjects _ = []

unwrapObject :: Aeson.Value -> Maybe Aeson.Object
unwrapObject (Aeson.Object obj) = Just obj
unwrapObject _ = Nothing

buildIdentifierMap :: [(Int, Aeson.Object)] -> Map.Map Text Text
buildIdentifierMap =
    foldr insertObjectIdentifiers Map.empty
  where
    insertObjectIdentifiers (indexValue, obj) acc =
        let primaryIdentifier = objectIdentifier indexValue obj
            aliases = mapMaybe (`lookupScalarText` obj) ["@id", "name"]
         in foldr (\aliasValue -> Map.insert aliasValue primaryIdentifier) acc aliases

buildNode :: Map.Map Text Text -> (Int, Aeson.Object) -> JsonLdNode
buildNode identifierMap (indexValue, obj) =
    JsonLdNode
        { nodeIdentifier = objectIdentifier indexValue obj
        , nodeTypeName = sanitizeIdentifier (objectType obj) "entity"
        , nodeTimeline = sanitizeIdentifier (lookupScalarTextWithDefault ["timeline"] "jsonld_import" obj) "jsonld_import"
        , nodeStart = lookupScalarTextWithDefault ["start"] "1900-01-01" obj
        , nodeEnd = lookupScalarTextWithDefault ["end"] "2100-12-31" obj
        , nodeAttributes =
            [ (sanitizeIdentifier (toText keyValue) "field", value)
            | (keyValue, value) <- KeyMap.toList obj
            , let keyText = toText keyValue
            , keyText `notElem` ignoredKeys
            , not (isReferenceValue value)
            ]
        , nodeRelationships =
            [ (toText keyValue, resolveReference identifierMap refValue)
            | (keyValue, value) <- KeyMap.toList obj
            , let keyText = toText keyValue
            , keyText `notElem` ignoredKeys
            , refValue <- extractReferenceValues value
            ]
        }
  where
    ignoredKeys = ["name", "@id", "type", "@type", "timeline", "start", "end", "@context", "@graph"]

renderJsonLd :: [JsonLdNode] -> Text
renderJsonLd nodes =
    T.unlines $
        [ "timeline jsonld_import {"
        , "    kind: linear,"
        , "    start: 1900-01-01,"
        , "    end: 2100-12-31,"
        , "}"
        , ""
        ]
            ++ concatMap renderNode nodes
            ++ concatMap renderNodeRelationships nodes

renderNode :: JsonLdNode -> [Text]
renderNode node =
    [ "entity " <> nodeIdentifier node <> " : " <> nodeTypeName node <> " {"
    ]
        ++ maybeDisplayName node
        ++ [ "    " <> label <> ": " <> renderJsonValue value <> ","
           | (label, value) <- nodeAttributes node
           ]
        ++ [ "    appears_on: " <> nodeTimeline node <> " @ " <> nodeStart node <> ".." <> nodeEnd node <> ","
           , "}"
           , ""
           ]

renderNodeRelationships :: JsonLdNode -> [Text]
renderNodeRelationships node =
    [ "rel " <> nodeIdentifier node <> " -[\"" <> escapeString label <> "\"]-> " <> targetIdentifier <> ";"
    | (label, targetIdentifier) <- nodeRelationships node
    ]
        ++ ["" | not (null (nodeRelationships node))]

maybeDisplayName :: JsonLdNode -> [Text]
maybeDisplayName node =
    if nodeIdentifier node == displayField
        then []
        else ["    display_name: \"" <> escapeString displayField <> "\","]
  where
    displayField = T.replace "_" " " (nodeIdentifier node)

objectIdentifier :: Int -> Aeson.Object -> Text
objectIdentifier indexValue obj =
    sanitizeIdentifier
        (lookupScalarTextWithDefault ["name", "@id"] ("jsonld_entity_" <> T.pack (show indexValue)) obj)
        ("jsonld_entity_" <> T.pack (show indexValue))

objectType :: Aeson.Object -> Text
objectType obj =
    fromMaybe "entity" $
        lookupScalarText "@type" obj
            <|> lookupScalarText "type" obj

lookupScalarTextWithDefault :: [Text] -> Text -> Aeson.Object -> Text
lookupScalarTextWithDefault keys fallback obj =
    fromMaybe fallback (go keys)
  where
    go [] = Nothing
    go (keyValue : rest) =
        lookupScalarText keyValue obj <|> go rest

lookupScalarText :: Text -> Aeson.Object -> Maybe Text
lookupScalarText keyName obj =
    case KeyMap.lookup (fromStringKey keyName) obj of
        Just (Aeson.String textValue) -> Just textValue
        Just (Aeson.Array values) ->
            firstTextValue (Vector.toList values)
        Just value ->
            Just (T.pack (show value))
        Nothing ->
            Nothing

firstTextValue :: [Aeson.Value] -> Maybe Text
firstTextValue values =
    case mapMaybe scalarTextValue values of
        textValue : _ -> Just textValue
        [] -> Nothing

scalarTextValue :: Aeson.Value -> Maybe Text
scalarTextValue (Aeson.String textValue) = Just textValue
scalarTextValue (Aeson.Number numberValue) = Just (T.pack (show numberValue))
scalarTextValue (Aeson.Bool boolValue) = Just (if boolValue then "true" else "false")
scalarTextValue _ = Nothing

isReferenceValue :: Aeson.Value -> Bool
isReferenceValue value =
    not (null (extractReferenceValues value))

extractReferenceValues :: Aeson.Value -> [Text]
extractReferenceValues value =
    case value of
        Aeson.Object obj ->
            maybe [] pure (lookupScalarText "@id" obj)
        Aeson.Array values ->
            concatMap extractReferenceValues (Vector.toList values)
        _ ->
            []

resolveReference :: Map.Map Text Text -> Text -> Text
resolveReference identifierMap rawReference =
    fromMaybe
        (sanitizeIdentifier rawReference "jsonld_ref")
        (Map.lookup rawReference identifierMap)

fromStringKey :: Text -> Key
fromStringKey = fromText

renderJsonValue :: Aeson.Value -> Text
renderJsonValue value =
    case value of
        Aeson.String textValue -> "\"" <> escapeString textValue <> "\""
        Aeson.Number numberValue -> T.pack (show numberValue)
        Aeson.Bool boolValue -> if boolValue then "true" else "false"
        Aeson.Null -> "null"
        Aeson.Array values ->
            "[" <> T.intercalate ", " (map renderJsonValue (Vector.toList values)) <> "]"
        Aeson.Object obj ->
            "\"" <> escapeString (T.pack (show (Aeson.Object obj))) <> "\""

sanitizeIdentifier :: Text -> Text -> Text
sanitizeIdentifier raw fallback
    | T.null normalized = fallback
    | startsWithDigit normalized = fallback <> "_" <> normalized
    | otherwise = normalized
  where
    normalized =
        T.dropAround (== '_') $
            T.map
                (\charValue -> if isIdentifierChar charValue then charValue else '_')
                (trimIdentifierSource raw)

    startsWithDigit textValue =
        case T.uncons textValue of
            Just (firstChar, _) -> '0' <= firstChar && firstChar <= '9'
            Nothing -> False

trimIdentifierSource :: Text -> Text
trimIdentifierSource raw =
    case reverseNonEmpty (filter (not . T.null) (splitIdentifierSource raw)) of
        partValue : _ -> partValue
        [] -> T.strip raw

splitIdentifierSource :: Text -> [Text]
splitIdentifierSource =
    T.split (\charValue -> charValue `elem` ['/', '#', ':', ' '])

reverseNonEmpty :: [a] -> [a]
reverseNonEmpty = reverse

isIdentifierChar :: Char -> Bool
isIdentifierChar charValue =
    ('0' <= charValue && charValue <= '9')
        || ('A' <= charValue && charValue <= 'Z')
        || ('a' <= charValue && charValue <= 'z')
        || charValue == '_'

escapeString :: Text -> Text
escapeString =
    T.replace "\\" "\\\\"
        . T.replace "\"" "\\\""
