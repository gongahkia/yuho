{-# LANGUAGE OverloadedStrings #-}
-- Private adapter for Aeson's tagged non-record sums. rejectUnknownFields does
-- not close their outer objects, so check constructor keys before generic parsing.
module Yuho.Authoring.Typed.JSON (closedTaggedJSON) where

import Data.Aeson (Value, withObject, (.:))
import qualified Data.Aeson.Key as Key
import qualified Data.Aeson.KeyMap as KeyMap
import Data.Aeson.Types (Parser, JSONPathElement(Key), (<?>))
import Data.List (find, sort)
import Data.Text (Text)
import qualified Data.Text as Text

closedTaggedJSON :: String -> [(Text,Bool)] -> (Value -> Parser a) -> Value -> Parser a
closedTaggedJSON label variants parse value = withObject label (\fields -> do
  tag <- fields .: "tag"
  case lookup tag variants of
    Nothing -> fail ("unsupported " <> label <> " constructor: " <> Text.unpack tag) <?> Key "tag"
    Just payload -> do
      let allowed = "tag" : ["contents" | payload]
      case find (`notElem` allowed) (sort (KeyMap.keys fields)) of
        Just key -> fail ("unexpected field " <> show (Key.toText key) <> " in " <> Text.unpack tag) <?> Key key
        Nothing -> parse value) value
