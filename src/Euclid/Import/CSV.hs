{-# LANGUAGE OverloadedStrings #-}

module Euclid.Import.CSV
    ( importCsvToEuclid
    ) where

import Data.Char (isAlphaNum, isSpace)
import Data.List (foldl')
import Data.Maybe (fromMaybe)
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Model.Types

data EntityImportRow = EntityImportRow
    { entityRowName :: Text
    , entityRowType :: Text
    , entityRowTimeline :: Text
    , entityRowTimelineKind :: Text
    , entityRowStart :: Text
    , entityRowEnd :: Text
    , entityRowAttributes :: [(Text, Text)]
    }

data TimelineSeed = TimelineSeed
    { seedName :: Text
    , seedKind :: Text
    , seedStart :: Text
    , seedEnd :: Text
    }

importCsvToEuclid :: Text -> Either [Diagnostic] Text
importCsvToEuclid input
    | null rows =
        Left [diag 0 "empty CSV"]
    | hasRelationshipColumns =
        importRelationships header dataRows
    | hasEntityColumns =
        importEntities header dataRows
    | otherwise =
        Left [diag 1 "unsupported CSV schema; expected entity or relationship columns"]
  where
    rows = filter (not . T.null) (map T.stripEnd (T.lines input))
    header =
        case rows of
            [] -> []
            firstRow : _ -> map normalizeHeader (parseCsvFields firstRow)
    dataRows = zip [2 ..] (map parseCsvFields (drop 1 rows))
    hasRelationshipColumns = hasAnyColumn ["source", "from"] && hasAnyColumn ["target", "to"]
    hasEntityColumns = hasAnyColumn ["name", "id"]
    hasAnyColumn aliases = any (`elem` header) aliases

importEntities :: [Text] -> [(Int, [Text])] -> Either [Diagnostic] Text
importEntities header rows = do
    entityRows <- traverse buildEntityRow rows
    let timelineBlocks = map renderTimelineBlock (buildTimelineSeeds entityRows)
        entityBlocks = map renderEntityBlock entityRows
    pure (T.intercalate "\n\n" (timelineBlocks ++ entityBlocks) <> "\n")
  where
    buildEntityRow (lineNumber, columns)
        | T.null rawName =
            Left [diag lineNumber "empty name"]
        | otherwise =
            Right
                EntityImportRow
                    { entityRowName = sanitizeIdentifier rawName "entity"
                    , entityRowType = sanitizeIdentifier (defaultText "entity" rawType) "entity"
                    , entityRowTimeline = sanitizeIdentifier (defaultText "imported" rawTimeline) "timeline"
                    , entityRowTimelineKind = normalizeTimelineKind rawTimelineKind
                    , entityRowStart = resolvedStart
                    , entityRowEnd = resolvedEnd
                    , entityRowAttributes =
                        [ (sanitizeIdentifier label "field", value)
                        | label <- header
                        , label `notElem` ignoredColumns
                        , let value = lookupColumn [label]
                        , not (T.null value)
                        ]
                    }
      where
        lookupColumn aliases = columnValueAny header columns aliases
        rawName = lookupColumn ["name", "id"]
        rawType = lookupColumn ["type", "entity_type"]
        rawTimeline = lookupColumn ["timeline", "lane", "track"]
        rawTimelineKind = lookupColumn ["timeline_kind"]
        rawStart = lookupColumn ["start", "time_start"]
        rawEnd = lookupColumn ["end", "time_end"]
        resolvedStart =
            if T.null rawStart
                then
                    if T.null rawEnd
                        then T.pack (show (lineNumber - 1))
                        else rawEnd
                else rawStart
        resolvedEnd =
            if T.null rawEnd
                then resolvedStart
                else rawEnd
        ignoredColumns =
            [ "name"
            , "id"
            , "type"
            , "entity_type"
            , "timeline"
            , "lane"
            , "track"
            , "timeline_kind"
            , "start"
            , "time_start"
            , "end"
            , "time_end"
            ]

buildTimelineSeeds :: [EntityImportRow] -> [TimelineSeed]
buildTimelineSeeds = foldl' insertSeed []
  where
    insertSeed seeds rowValue =
        let currentSeed =
                TimelineSeed
                    { seedName = entityRowTimeline rowValue
                    , seedKind = entityRowTimelineKind rowValue
                    , seedStart = entityRowStart rowValue
                    , seedEnd = entityRowEnd rowValue
                    }
         in case break ((== seedName currentSeed) . seedName) seeds of
                (before, existing : after) ->
                    before ++ [mergeSeed existing currentSeed] ++ after
                (before, []) ->
                    before ++ [currentSeed]

    mergeSeed existing incoming =
        TimelineSeed
            { seedName = seedName existing
            , seedKind =
                if seedKind existing == "linear"
                    then seedKind incoming
                    else seedKind existing
            , seedStart = minTimeText (seedStart existing) (seedStart incoming)
            , seedEnd = maxTimeText (seedEnd existing) (seedEnd incoming)
            }

renderTimelineBlock :: TimelineSeed -> Text
renderTimelineBlock timelineSeed =
    T.unlines
        [ "timeline " <> seedName timelineSeed <> " {"
        , "    kind: " <> seedKind timelineSeed <> ","
        , "    start: " <> seedStart timelineSeed <> ","
        , "    end: " <> seedEnd timelineSeed <> ","
        , "}"
        ]

renderEntityBlock :: EntityImportRow -> Text
renderEntityBlock rowValue =
    T.unlines $
        [ "entity " <> entityRowName rowValue <> " : " <> entityRowType rowValue <> " {"
        ]
            ++ [ "    " <> label <> ": " <> renderLiteral value <> ","
               | (label, value) <- entityRowAttributes rowValue
               ]
            ++ [ "    appears_on: " <> entityRowTimeline rowValue <> " @ " <> entityRowStart rowValue <> ".." <> entityRowEnd rowValue <> ","
               , "}"
               ]

importRelationships :: [Text] -> [(Int, [Text])] -> Either [Diagnostic] Text
importRelationships header rows =
    render <$> traverse renderRow rows
  where
    render blocks = T.unlines blocks
    renderRow (lineNumber, columns)
        | T.null rawSource || T.null rawTarget =
            Left [diag lineNumber "empty source or target"]
        | otherwise =
            Right (baseRel <> temporalSuffix <> ";")
      where
        lookupColumn aliases = columnValueAny header columns aliases
        rawSource = lookupColumn ["source", "from"]
        rawTarget = lookupColumn ["target", "to"]
        sourceValue = sanitizeIdentifier rawSource "source"
        targetValue = sanitizeIdentifier rawTarget "target"
        labelValue = lookupColumn ["label", "relationship", "edge"]
        startValue = lookupColumn ["start", "time_start"]
        endValue = lookupColumn ["end", "time_end"]
        baseRel =
            if T.null labelValue
                then "rel " <> sourceValue <> " --> " <> targetValue
                else "rel " <> sourceValue <> " -[\"" <> escapeString labelValue <> "\"]-> " <> targetValue
        temporalSuffix =
            if T.null startValue || T.null endValue
                then ""
                else " @ " <> startValue <> ".." <> endValue

parseCsvFields :: Text -> [Text]
parseCsvFields rawLine = reverse (finalize insideQuotes currentField reversedFields)
  where
    (insideQuotes, currentField, reversedFields) = go False False "" [] (T.unpack rawLine)

    go insideQuoteState sawClosingQuote fieldValue fieldsAcc chars =
        case chars of
            [] -> (insideQuoteState, fieldValue, fieldsAcc)
            '"' : '"' : rest | insideQuoteState ->
                go True False (T.snoc fieldValue '"') fieldsAcc rest
            '"' : rest | insideQuoteState ->
                go False True fieldValue fieldsAcc rest
            '"' : rest ->
                go True False fieldValue fieldsAcc rest
            ',' : rest | not insideQuoteState ->
                go False False "" (trim fieldValue : fieldsAcc) rest
            charValue : rest ->
                let nextFieldValue =
                        if sawClosingQuote && isSpace charValue
                            then fieldValue
                            else T.snoc fieldValue charValue
                 in go insideQuoteState False nextFieldValue fieldsAcc rest

    finalize _ fieldValue fieldsAcc =
        trim fieldValue : fieldsAcc

columnValueAny :: [Text] -> [Text] -> [Text] -> Text
columnValueAny header columns aliases =
    foldl'
        (\found alias -> if T.null found then columnValue header columns alias else found)
        ""
        aliases

columnValue :: [Text] -> [Text] -> Text -> Text
columnValue header columns label =
    case lookupIndex 0 header of
        Nothing -> ""
        Just indexValue -> fromMaybe "" (safeIndex indexValue columns)
  where
    lookupIndex _ [] = Nothing
    lookupIndex indexValue (headerLabel : rest)
        | headerLabel == label = Just indexValue
        | otherwise = lookupIndex (indexValue + 1) rest

safeIndex :: Int -> [a] -> Maybe a
safeIndex indexValue values
    | indexValue < 0 = Nothing
    | otherwise =
        case drop indexValue values of
            [] -> Nothing
            value : _ -> Just value

normalizeHeader :: Text -> Text
normalizeHeader = T.toLower . trim

normalizeTimelineKind :: Text -> Text
normalizeTimelineKind rawKind =
    case T.toLower (trim rawKind) of
        "branch" -> "branch"
        "parallel" -> "parallel"
        "loop" -> "loop"
        _ -> "linear"

sanitizeIdentifier :: Text -> Text -> Text
sanitizeIdentifier raw fallback
    | T.null normalized = fallback
    | startsWithDigit normalized = fallback <> "_" <> normalized
    | otherwise = normalized
  where
    normalized =
        T.dropAround (== '_') $
            T.map
                (\charValue -> if isAlphaNum charValue || charValue == '_' then charValue else '_')
                (trim raw)

    startsWithDigit textValue =
        case T.uncons textValue of
            Just (firstChar, _) -> '0' <= firstChar && firstChar <= '9'
            Nothing -> False

renderLiteral :: Text -> Text
renderLiteral rawValue
    | normalized `elem` ["true", "false", "null"] = normalized
    | isNumericLike normalized = normalized
    | isIsoDateLike normalized = normalized
    | otherwise = "\"" <> escapeString normalized <> "\""
  where
    normalized = trim rawValue

escapeString :: Text -> Text
escapeString =
    T.replace "\\" "\\\\"
        . T.replace "\"" "\\\""

isNumericLike :: Text -> Bool
isNumericLike value =
    not (T.null value)
        && T.all (\charValue -> charValue == '-' || charValue == '.' || ('0' <= charValue && charValue <= '9')) value
        && T.any (\charValue -> '0' <= charValue && charValue <= '9') value

isIsoDateLike :: Text -> Bool
isIsoDateLike value =
    T.length value == 10
        && T.index value 4 == '-'
        && T.index value 7 == '-'
        && T.all isDateChar value
  where
    isDateChar charValue = charValue == '-' || ('0' <= charValue && charValue <= '9')

minTimeText :: Text -> Text -> Text
minTimeText left right =
    case compareTimeText left right of
        GT -> right
        _ -> left

maxTimeText :: Text -> Text -> Text
maxTimeText left right =
    case compareTimeText left right of
        LT -> right
        _ -> left

compareTimeText :: Text -> Text -> Ordering
compareTimeText left right =
    case (parseNumeric left, parseNumeric right) of
        (Just leftValue, Just rightValue) -> compare leftValue rightValue
        _ -> compare left right

parseNumeric :: Text -> Maybe Integer
parseNumeric rawValue =
    case reads (T.unpack rawValue) of
        [(value, "")] -> Just value
        _ -> Nothing

trim :: Text -> Text
trim = T.dropAround isSpace

defaultText :: Text -> Text -> Text
defaultText fallback value
    | T.null value = fallback
    | otherwise = value

diag :: Int -> Text -> Diagnostic
diag lineNumber message =
    Diagnostic
        { diagnosticLevel = DiagnosticError
        , diagnosticSource = "import:csv:line:" <> T.pack (show lineNumber)
        , diagnosticMessage = message
        , diagnosticSpan = Nothing
        }
