{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Codec (encodeDocument, decodeDocument, encodeRecord) where

import qualified Data.Aeson as Aeson
import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as Lazy
import qualified Data.Text as Text
import Yuho.Authoring.Types
import Yuho.Protocol.Json (J(..), decodeJson, lookupField)

-- Aeson emits deterministic records with the pinned dependency configuration.
-- Snapshots hash these bytes, not a promise of cross-version canonicalization.
encodeRecord :: Aeson.ToJSON a => a -> BS.ByteString
encodeRecord = Lazy.toStrict . Aeson.encode

encodeDocument :: AuthoringDocument -> BS.ByteString
encodeDocument = encodeRecord

decodeDocument :: BS.ByteString -> Either AuthoringDiagnostic AuthoringDocument
decodeDocument bytes = do
  -- Also rejects duplicate JSON keys, excessive depth, and oversized documents.
  value <- either (Left . problem "AJSON" "/") Right (decodeJson bytes)
  case lookupField "documentFormat" value of
    Just (JStr version) | version == authoringFormat -> pure ()
    _ -> Left (problem "AVERSION" "/documentFormat" "unsupported authoring format")
  either (Left . problem "AJSON" "/" . Text.pack) Right
    (Aeson.eitherDecodeStrict' bytes)
  where problem code location message = AuthoringDiagnostic code location [] message
