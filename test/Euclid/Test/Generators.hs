{-# LANGUAGE OverloadedStrings #-}

module Euclid.Test.Generators
    ( GeneratedWorld(..)
    , genCsvInput
    , genIntExpression
    , genInvalidRangeWorld
    , genValidWorld
    ) where

import Data.Text (Text)
import qualified Data.Text as T
import qualified Hedgehog as H
import qualified Hedgehog.Gen as Gen
import qualified Hedgehog.Range as Range

data GeneratedWorld = GeneratedWorld
    { generatedSource :: Text
    , generatedTimelineName :: Text
    , generatedFactName :: Text
    , generatedEvidenceName :: Text
    }
    deriving (Eq, Show)

genValidWorld :: H.Gen GeneratedWorld
genValidWorld = do
    timelineName <- genIdentifierWith "timeline_"
    factName <- genIdentifierWith "fact_"
    evidenceName <- genIdentifierWith "evidence_"
    start <- Gen.integral (Range.linear (0 :: Integer) 100)
    duration <- Gen.integral (Range.linear (1 :: Integer) 100)
    let end = start + duration
    factStart <- Gen.integral (Range.linear start end)
    factEnd <- Gen.integral (Range.linear factStart end)
    evidenceStart <- Gen.integral (Range.linear start end)
    evidenceEnd <- Gen.integral (Range.linear evidenceStart end)
    pure
        GeneratedWorld
            { generatedTimelineName = timelineName
            , generatedFactName = factName
            , generatedEvidenceName = evidenceName
            , generatedSource =
                T.unlines
                    [ "timeline " <> timelineName <> " {"
                    , "    start: " <> showText start <> ","
                    , "    end: " <> showText end <> ","
                    , "}"
                    , ""
                    , "entity " <> factName <> " : fact {"
                    , "    summary: \"generated fact\","
                    , "    appears_on: " <> timelineName <> " @ " <> showText factStart <> ".." <> showText factEnd <> ","
                    , "}"
                    , ""
                    , "entity " <> evidenceName <> " : evidence {"
                    , "    citation: \"generated citation\","
                    , "    source: \"generated source\","
                    , "    appears_on: " <> timelineName <> " @ " <> showText evidenceStart <> ".." <> showText evidenceEnd <> ","
                    , "}"
                    , ""
                    , "rel " <> evidenceName <> " -[\"cites\"]-> " <> factName <> ";"
                    ]
            }

genInvalidRangeWorld :: H.Gen Text
genInvalidRangeWorld = do
    timelineName <- genIdentifierWith "timeline_"
    entityName <- genIdentifierWith "entity_"
    start <- Gen.integral (Range.linear (0 :: Integer) 50)
    end <- Gen.integral (Range.linear (start + 1) (start + 100))
    pure $
        T.unlines
            [ "timeline " <> timelineName <> " {"
            , "    start: " <> showText start <> ","
            , "    end: " <> showText end <> ","
            , "}"
            , "entity " <> entityName <> " : fact {"
            , "    appears_on: " <> timelineName <> " @ " <> showText end <> ".." <> showText start <> ","
            , "}"
            ]

genIntExpression :: H.Gen (Text, Integer)
genIntExpression = do
    left <- Gen.integral (Range.linear (-1000 :: Integer) 1000)
    right <- Gen.integral (Range.linear (-1000 :: Integer) 1000)
    divisor <- Gen.filter (/= 0) (Gen.integral (Range.linear (-1000 :: Integer) 1000))
    Gen.element
        [ (showText left <> " + " <> showText right, left + right)
        , (showText left <> " - " <> showText right, left - right)
        , (showText left <> " * " <> showText right, left * right)
        , (showText left <> " / " <> showText divisor, left `div` divisor)
        , (showText left <> " % " <> showText divisor, left `mod` divisor)
        ]

genCsvInput :: H.Gen Text
genCsvInput = do
    firstName <- genIdentifierWith "event_"
    secondName <- Gen.filter (/= firstName) (genIdentifierWith "event_")
    firstStart <- Gen.integral (Range.linear (1 :: Integer) 10)
    secondStart <- Gen.integral (Range.linear (firstStart + 1) 20)
    pure $
        T.unlines
            [ "name,type,timeline,start,end,summary"
            , firstName <> ",fact,generated," <> showText firstStart <> "," <> showText firstStart <> ",First generated row"
            , secondName <> ",fact,generated," <> showText secondStart <> "," <> showText secondStart <> ",Second generated row"
            ]

genIdentifierWith :: Text -> H.Gen Text
genIdentifierWith prefix = do
    suffix <- Gen.text (Range.linear 3 12) (Gen.element identifierChars)
    pure (prefix <> suffix)

identifierChars :: [Char]
identifierChars = ['a' .. 'z'] ++ ['0' .. '9'] ++ "_"

showText :: Show a => a -> Text
showText = T.pack . show
