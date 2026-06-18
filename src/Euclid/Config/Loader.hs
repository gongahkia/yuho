{-# LANGUAGE OverloadedStrings #-}

module Euclid.Config.Loader
    ( EuclidConfig(..)
    , SvgTheme(..)
    , darkTheme
    , defaultConfig
    , lightTheme
    , loadConfig
    , resolveSvgTheme
    ) where

import Control.Applicative ((<|>))
import Data.Char (isDigit, isSpace)
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.IO as TIO
import Data.List (foldl')
import System.Directory (doesFileExist)

data SvgTheme = SvgTheme
    { themeBackground :: Text
    , themeText :: Text
    , themeTimeline :: Text
    , themeEntity :: Text
    , themeRelationship :: Text
    }
    deriving (Eq, Show)

data EuclidConfig = EuclidConfig
    { configDefaultWidth :: Maybe Int
    , configDefaultHeight :: Maybe Int
    , configDefaultFormat :: Maybe Text
    , configThemeName :: Maybe Text
    , configTheme :: Maybe SvgTheme
    }
    deriving (Eq, Show)

defaultConfig :: EuclidConfig
defaultConfig =
    EuclidConfig
        { configDefaultWidth = Nothing
        , configDefaultHeight = Nothing
        , configDefaultFormat = Nothing
        , configThemeName = Nothing
        , configTheme = Nothing
        }

darkTheme :: SvgTheme
darkTheme =
    SvgTheme
        { themeBackground = "#111827"
        , themeText = "#f9fafb"
        , themeTimeline = "#93c5fd"
        , themeEntity = "#10b981"
        , themeRelationship = "#f59e0b"
        }

lightTheme :: SvgTheme
lightTheme =
    SvgTheme
        { themeBackground = "#f8fafc"
        , themeText = "#111827"
        , themeTimeline = "#2563eb"
        , themeEntity = "#059669"
        , themeRelationship = "#d97706"
        }

loadConfig :: Maybe FilePath -> IO EuclidConfig
loadConfig Nothing = pure defaultConfig
loadConfig (Just path) = do
    exists <- doesFileExist path
    if exists
        then parseConfig <$> TIO.readFile path
        else pure defaultConfig

resolveSvgTheme :: Maybe Text -> EuclidConfig -> IO SvgTheme
resolveSvgTheme themeOverride configValue =
    case themeOverride <|> configThemeName configValue of
        Just "light" -> pure (resolvedNamedTheme lightTheme configValue)
        Just "dark" -> pure (resolvedNamedTheme darkTheme configValue)
        Just customPath -> do
            exists <- doesFileExist (T.unpack customPath)
            if exists
                then do
                    customConfig <- parseConfig <$> TIO.readFile (T.unpack customPath)
                    pure (resolvedConfiguredTheme customConfig)
                else pure (resolvedConfiguredTheme configValue)
        Nothing -> pure (resolvedConfiguredTheme configValue)

parseConfig :: Text -> EuclidConfig
parseConfig input =
    snd $
        foldl'
            step
            ("root", defaultConfig)
            (T.lines input)
  where
    step (sectionName, configValue) rawLine =
        case parseLine rawLine of
            Nothing -> (sectionName, configValue)
            Just (Left newSection) -> (newSection, configValue)
            Just (Right (keyValue, value)) ->
                (sectionName, applyEntry configValue sectionName keyValue value)

applyEntry :: EuclidConfig -> Text -> Text -> Text -> EuclidConfig
applyEntry configValue sectionName keyValue value =
    case (sectionName, keyValue) of
        ("export", "default_width") -> configValue{configDefaultWidth = readMaybeInt value}
        ("export", "default_height") -> configValue{configDefaultHeight = readMaybeInt value}
        ("export", "default_format") -> configValue{configDefaultFormat = Just (stripQuotes value)}
        ("theme", "name") -> configValue{configThemeName = Just (stripQuotes value)}
        ("theme", "background") -> configValue{configTheme = Just (withTheme configValue (\themeValue -> themeValue{themeBackground = stripQuotes value}))}
        ("theme", "text") -> configValue{configTheme = Just (withTheme configValue (\themeValue -> themeValue{themeText = stripQuotes value}))}
        ("theme", "timeline") -> configValue{configTheme = Just (withTheme configValue (\themeValue -> themeValue{themeTimeline = stripQuotes value}))}
        ("theme", "entity") -> configValue{configTheme = Just (withTheme configValue (\themeValue -> themeValue{themeEntity = stripQuotes value}))}
        ("theme", "relationship") -> configValue{configTheme = Just (withTheme configValue (\themeValue -> themeValue{themeRelationship = stripQuotes value}))}
        ("root", "theme") -> configValue{configThemeName = Just (stripQuotes value)}
        _ -> configValue

parseLine :: Text -> Maybe (Either Text (Text, Text))
parseLine rawLine
    | T.null cleaned = Nothing
    | "[" `T.isPrefixOf` cleaned && "]" `T.isSuffixOf` cleaned =
        Just (Left (T.dropAround (\charValue -> charValue == '[' || charValue == ']') cleaned))
    | otherwise =
        case T.breakOn "=" cleaned of
            (keyValue, value)
                | T.null value -> Nothing
                | otherwise ->
                    Just (Right (T.strip keyValue, T.strip (T.drop 1 value)))
  where
    cleaned = T.strip (stripInlineComment rawLine)

stripInlineComment :: Text -> Text
stripInlineComment = T.pack . go False . T.unpack
  where
    go _ [] = []
    go insideQuotes (charValue : rest)
        | charValue == '"' = charValue : go (not insideQuotes) rest
        | not insideQuotes && (charValue == '#' || charValue == ';') = []
        | otherwise = charValue : go insideQuotes rest

withTheme :: EuclidConfig -> (SvgTheme -> SvgTheme) -> SvgTheme
withTheme configValue updateTheme =
    updateTheme $
        maybe
            (case fmap T.toLower (configThemeName configValue) of
                Just "light" -> lightTheme
                Just "dark" -> darkTheme
                _ -> darkTheme
            )
            id
            (configTheme configValue)

resolvedConfiguredTheme :: EuclidConfig -> SvgTheme
resolvedConfiguredTheme configValue =
    case fmap T.toLower (configThemeName configValue) of
        Just "light" -> resolvedNamedTheme lightTheme configValue
        Just "dark" -> resolvedNamedTheme darkTheme configValue
        _ -> maybe darkTheme id (configTheme configValue)

resolvedNamedTheme :: SvgTheme -> EuclidConfig -> SvgTheme
resolvedNamedTheme fallbackTheme configValue =
    maybe fallbackTheme id (configTheme configValue)

stripQuotes :: Text -> Text
stripQuotes = T.dropAround (== '"')

readMaybeInt :: Text -> Maybe Int
readMaybeInt rawValue
    | T.all (\charValue -> isDigit charValue || isSpace charValue) rawValue =
        case reads (T.unpack (T.strip rawValue)) of
            [(value, "")] -> Just value
            _ -> Nothing
    | otherwise = Nothing
