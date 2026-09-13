{-# LANGUAGE OverloadedStrings #-}
module Yuho.ModelBundle.Json
  ( parseCanonical, field, optional, obj, arr, str, number, fields, tagged
  , uniqueSorted, depth, digestDomain, digestBytes, spanAt, safeId
  ) where

import Crypto.Hash (Digest, SHA256(..), hashWith)
import qualified Data.ByteString as BS
import Data.List (sort)
import Data.Set (Set)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Core.Types (Span(..))
import Yuho.ModelBundle.Types (Failure(..), issue)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField)

parseCanonical :: Text -> BS.ByteString -> Either Failure J
parseCanonical path bytes = do
  value <- either (issue "MBDEC001" path) Right (decodeJson bytes)
  if depth value > 16 then issue "MBRES001" path "JSON nesting exceeds 16" else pure ()
  if encodeJson value /= bytes then issue "MBDEC002" path "JSON is not canonical" else pure ()
  pure value

depth :: J -> Int
depth value = case value of
  JObj xs -> 1 + maximum (0 : map (depth . snd) xs)
  JArr xs -> 1 + maximum (0 : map depth xs)
  _ -> 0

obj :: Text -> [Text] -> J -> Either Failure J
obj path allowed value = case value of
  JObj xs -> case filter (\(key, _) -> key `notElem` allowed) xs of
    (key, _) : _ -> issue "MBDEC001" (path <> "/" <> key) "unknown field"
    [] -> Right value
  _ -> issue "MBDEC001" path "expected object"

fields :: Text -> J -> Either Failure [(Text, J)]
fields _ (JObj xs) = Right xs
fields path _ = issue "MBDEC001" path "expected object"

field :: Text -> Text -> J -> Either Failure J
field path key value = maybe (issue "MBDEC001" (path <> "/" <> key) "missing field") Right (lookupField key value)

optional :: Text -> J -> Maybe J
optional = lookupField

arr :: Text -> J -> Either Failure [J]
arr _ (JArr xs) = Right xs
arr path _ = issue "MBDEC001" path "expected array"

str :: Text -> J -> Either Failure Text
str path (JStr x)
  | not (Text.null x) && Text.length x <= 1024 = Right x
  | otherwise = issue "MBINV001" path "string must contain 1..1024 characters"
str path _ = issue "MBDEC001" path "expected string"

number :: Text -> J -> Either Failure Integer
number _ (JNum n) = Right n
number path _ = issue "MBDEC001" path "expected integer"

tagged :: Text -> [Text] -> Text -> Either Failure Text
tagged path allowed value
  | value `elem` allowed = Right value
  | otherwise = issue "MBCAP001" path "unsupported value"

uniqueSorted :: Text -> [Text] -> Either Failure ()
uniqueSorted path xs
  | xs == sort xs && Set.size (Set.fromList xs :: Set Text) == length xs = Right ()
  | otherwise = issue "MBINV001" path "list must be sorted and unique"

digestBytes :: BS.ByteString -> Text
digestBytes bytes = Text.pack (show (hashWith SHA256 bytes :: Digest SHA256))

digestDomain :: Text -> BS.ByteString -> Text
digestDomain domain bytes = digestBytes (Encoding.encodeUtf8 domain <> BS.singleton 0 <> bytes)

spanAt :: Text -> J -> Either Failure Span
spanAt path value = do
  _ <- obj path ["start", "end", "start_line", "start_col", "end_line", "end_col"] value
  xs <- traverse (\key -> field path key value >>= number (path <> "/" <> key))
    ["start", "end", "start_line", "start_col", "end_line", "end_col"]
  case traverse bounded xs of
    Just [a,b,c,d,e,f] -> Right (Span a b c d e f)
    _ -> issue "MBINV001" path "span integer outside supported range"
  where
    bounded n | n >= 0 && n <= toInteger (maxBound :: Int) = Just (fromInteger n)
              | otherwise = Nothing

safeId :: Text -> Bool
safeId value = not (Text.null value) && Text.length value <= 128
  && Text.all (\ch -> (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')
    || (ch >= '0' && ch <= '9') || ch `elem` ("-_:." :: String)) value
  && value /= "." && value /= ".."
