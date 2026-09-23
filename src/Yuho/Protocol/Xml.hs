{-# LANGUAGE OverloadedStrings #-}
module Yuho.Protocol.Xml (encodeXml) where

import qualified Data.ByteString as BS
import qualified Data.ByteString.Builder as Builder
import qualified Data.ByteString.Lazy as Lazy
import Data.List (sortOn)
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Protocol.Json (J(..))

-- | Render a protocol value as a deterministic XML tree. This is Yuho's
-- generic technical XML format, not a legal-document vocabulary.
encodeXml :: J -> Either Text BS.ByteString
encodeXml value = do
  body <- render value
  pure (Lazy.toStrict (Builder.toLazyByteString
    (literal "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
      <> literal "<yuho:document xmlns:yuho=\"urn:yuho:xml:v1\">"
      <> body <> literal "</yuho:document>\n")))

render :: J -> Either Text Builder.Builder
render value = case value of
  JNull -> pure (literal "<yuho:null/>")
  JBool item -> pure (literal "<yuho:boolean>"
    <> literal (if item then "true" else "false") <> literal "</yuho:boolean>")
  JNum item -> pure (literal "<yuho:number>" <> Builder.string8 (show item)
    <> literal "</yuho:number>")
  JStr item -> element "string" <$> escaped False item
  JArr items -> do
    rows <- traverse entry (zip [0 :: Int ..] items)
    pure (element "array" (mconcat rows))
  JObj fields -> do
    rows <- traverse member (sortOn fst fields)
    pure (element "object" (mconcat rows))
  where
    entry (index,item) = do
      rendered <- render item
      pure (literal "<yuho:item index=\"" <> Builder.string8 (show index)
        <> literal "\">" <> rendered <> literal "</yuho:item>")
    member (name,item) = do
      encodedName <- escaped True name
      rendered <- render item
      pure (literal "<yuho:member name=\"" <> encodedName <> literal "\">"
        <> rendered <> literal "</yuho:member>")

element :: String -> Builder.Builder -> Builder.Builder
element name content = literal ("<yuho:" <> name <> ">") <> content
  <> literal ("</yuho:" <> name <> ">")

literal :: String -> Builder.Builder
literal = Builder.string8

escaped :: Bool -> Text -> Either Text Builder.Builder
escaped attribute value
  | Text.all permitted value = Right (Builder.byteString
      (Encoding.encodeUtf8 (Text.concat (map escape (Text.unpack value)))))
  | otherwise = Left "XML 1.0 forbids a control character in compiled output"
  where
    permitted character = character == '\t' || character == '\n' || character == '\r'
      || (character >= '\x20' && character <= '\xD7FF')
      || (character >= '\xE000' && character <= '\xFFFD')
      || (character >= '\x10000' && character <= '\x10FFFF')
    escape character = case character of
      '&' -> "&amp;"
      '<' -> "&lt;"
      '>' -> "&gt;"
      '\t' -> "&#x9;"
      '\n' -> "&#xA;"
      '\r' -> "&#xD;"
      '"' | attribute -> "&quot;"
      '\'' | attribute -> "&apos;"
      _ -> Text.singleton character
