{-# LANGUAGE OverloadedStrings #-}
-- Shared XML and text primitives for the reference SVGs.
module Yuho.Authoring.Projection.Render
  ( number, wrap, xmlCharacter, escape, computedLabel, evaluationLabel, skipLabel, provisionFor ) where

import Control.Applicative ((<|>))
import Data.List (find)
import Data.Maybe (listToMaybe, mapMaybe)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Authoring.Projection.Types
import Yuho.Authoring.Types

-- Display wording only; canonical values stay in the projection and SVG titles.
computedLabel :: Maybe Text -> Text
computedLabel = maybe "No computed result" id

evaluationLabel :: Text -> Text
evaluationLabel state = case state of
  "not_requested" -> "Evaluation not requested"
  "not_evaluated" -> "Not evaluated"
  "evaluated" -> "Evaluated"
  "not_applicable" -> "Not applicable"
  _ -> state

skipLabel :: Text -> Text
skipLabel = Text.replace "_" " " . Text.replace
  "exception guard skipped because main branch: " "Main branch: "

-- Prefer an object's authored citation, otherwise show its authored rule's
-- citation through the existing occurrence mapping. No new source is inferred.
provisionFor :: ProjectionData -> ProjectionNode -> Maybe Text
provisionFor value node = direct <|> listToMaybe (mapMaybe citation rules)
  where
    law = documentLaw (snapshotDocument (projectionSnapshot value))
    authored = maybe (originAuthoredObjects (projectedNodeOrigin node))
      (\o -> [occurrenceAuthoredNode o]) (projectedNodeOccurrence node)
    citation key = find ((== key) . nodeId) (lawNodes law) >>= nodeCitation
    direct = listToMaybe (mapMaybe citation authored)
    rules = [occurrenceAuthoredRule o | n <- projectionNodes value,
      Just o <- [projectedNodeOccurrence n], elem (occurrenceAuthoredNode o) authored]

number :: Int -> Text
number = Text.pack . show

wrap :: Int -> Text -> [Text]
wrap limit = foldr add [] . Text.words
  where
    add word [] = [word]
    add word (line:rest)
      | Text.length word + 1 + Text.length line <= limit = (word <> " " <> line):rest
      | otherwise = word:line:rest

xmlCharacter :: Char -> Bool
xmlCharacter c = c `elem` ['\t','\n','\r'] || c >= '\x20' && c <= '\xD7FF'
  || c >= '\xE000' && c <= '\xFFFD' || c >= '\x10000' && c <= '\x10FFFF'

escape :: Text -> Text
escape = Text.concatMap (\c -> case c of
  '&' -> "&amp;"; '<' -> "&lt;"; '>' -> "&gt;"; '"' -> "&quot;"; '\'' -> "&apos;"
  '\t' -> "&#x9;"; '\n' -> "&#xA;"; '\r' -> "&#xD;"; _ -> Text.singleton c)
