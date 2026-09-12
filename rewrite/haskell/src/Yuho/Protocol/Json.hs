{-# LANGUAGE OverloadedStrings #-}
module Yuho.Protocol.Json
  ( J(..), decodeJson, encodeJson, lookupField, objectFields, textValue, integerValue
  , boolValue, arrayValue, maxRequestBytes, maxJsonDepth
  ) where

import qualified Data.Aeson as Aeson
import qualified Data.Aeson.Decoding.ByteString as Decoding
import Data.Aeson.Decoding.Tokens (Lit(..), Number(..), TkArray(..), TkRecord(..), Tokens(..))
import qualified Data.Aeson.Key as Key
import qualified Data.ByteString as BS
import qualified Data.ByteString.Builder as Builder
import qualified Data.ByteString.Lazy as Lazy
import Data.List (sortOn)
import Data.Set (Set)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text

data J = JNull | JBool Bool | JNum Integer | JStr Text | JArr [J] | JObj [(Text, J)]
  deriving (Eq, Show)

maxRequestBytes, maxJsonDepth :: Int
maxRequestBytes = 1048576
maxJsonDepth = 64

decodeJson :: BS.ByteString -> Either Text J
decodeJson bytes
  | BS.length bytes > maxRequestBytes = Left "request exceeds 1048576 bytes"
  | otherwise = do
      (value, remaining) <- token 0 (Decoding.bsToTokens bytes)
      if BS.all isSpace remaining then Right value else Left "trailing JSON bytes"
  where
    isSpace byte = byte == 32 || byte == 9 || byte == 10 || byte == 13

token :: Int -> Tokens k String -> Either Text (J, k)
token depth value
  | depth > maxJsonDepth = Left "JSON nesting exceeds 64 containers"
  | otherwise = case value of
      TkLit LitNull rest -> Right (JNull, rest)
      TkLit LitTrue rest -> Right (JBool True, rest)
      TkLit LitFalse rest -> Right (JBool False, rest)
      TkText item rest -> Right (JStr item, rest)
      TkNumber (NumInteger item) rest -> Right (JNum item, rest)
      TkNumber (NumDecimal _) _ -> Left "non-integer JSON number is outside protocol"
      TkNumber (NumScientific _) _ -> Left "non-integer JSON number is outside protocol"
      TkArrayOpen items -> do
        (parts, rest) <- array (depth + 1) items
        Right (JArr parts, rest)
      TkRecordOpen items -> do
        (parts, rest) <- object (depth + 1) Set.empty items
        Right (JObj parts, rest)
      TkErr message -> Left (Text.pack message)

array :: Int -> TkArray k String -> Either Text ([J], k)
array depth = go []
  where
    go reversed value = case value of
      TkArrayEnd rest -> Right (reverse reversed, rest)
      TkArrayErr message -> Left (Text.pack message)
      TkItem item -> do
        (decoded, next) <- token depth item
        go (decoded : reversed) next

object :: Int -> Set Text -> TkRecord k String -> Either Text ([(Text, J)], k)
object depth = go []
  where
    go reversed seen value = case value of
      TkRecordEnd rest -> Right (reverse reversed, rest)
      TkRecordErr message -> Left (Text.pack message)
      TkPair rawKey item -> do
        let key = Key.toText rawKey
        if Set.member key seen then Left ("duplicate JSON key: " <> key)
        else do
          (decoded, next) <- token depth item
          go ((key, decoded) : reversed) (Set.insert key seen) next

encodeJson :: J -> BS.ByteString
encodeJson = Lazy.toStrict . Builder.toLazyByteString . encode
  where
    encode JNull = Builder.string8 "null"
    encode (JBool True) = Builder.string8 "true"
    encode (JBool False) = Builder.string8 "false"
    encode (JNum value) = Builder.string8 (show value)
    encode (JStr value) = Builder.lazyByteString (Aeson.encode (Aeson.String value))
    encode (JArr values) = brackets '[' ']' (map encode values)
    encode (JObj pairs) = brackets '{' '}'
      [encode (JStr key) <> Builder.char8 ':' <> encode value
      | (key, value) <- sortOn fst pairs]
    brackets left right pieces =
      Builder.char8 left <> mconcat (separate pieces) <> Builder.char8 right
    separate [] = []
    separate (first:rest) = first : map (Builder.char8 ',' <>) rest

lookupField :: Text -> J -> Maybe J
lookupField key (JObj pairs) = lookup key pairs
lookupField _ _ = Nothing

objectFields :: J -> Maybe [(Text, J)]
objectFields (JObj pairs) = Just pairs
objectFields _ = Nothing

textValue :: J -> Maybe Text
textValue (JStr value) = Just value
textValue _ = Nothing

integerValue :: J -> Maybe Integer
integerValue (JNum value) = Just value
integerValue _ = Nothing

boolValue :: J -> Maybe Bool
boolValue (JBool value) = Just value
boolValue _ = Nothing

arrayValue :: J -> Maybe [J]
arrayValue (JArr values) = Just values
arrayValue _ = Nothing
