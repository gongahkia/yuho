{-# LANGUAGE OverloadedStrings #-}
-- | Validated original-source references, independent of any law or analysis.
module Yuho.Authoring.Source (sourceAnchorBytes, sourceAnchorCodePoints) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Authoring.Compile (byteSpan)
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue, toCoreSpan)
import qualified Yuho.Core.Source as Core
import qualified Yuho.Core.Types as Core

-- | Zero-based, half-open UTF-8 byte offsets in the exact retained source text.
-- Integer accepts external offsets without overflowing before range validation.
sourceAnchorBytes :: SourceRecord -> Integer -> Integer
                  -> Either [AuthoringDiagnostic] SourceRef
sourceAnchorBytes source first lastOffset = do
  content <- retained source
  let bytes = Encoding.encodeUtf8 content
  checkedRange source "/byteRange" "UTF-8 bytes" (toInteger (BS.length bytes)) first lastOffset
  -- Bounds are now <= the ByteString's Int length, before either narrowing.
  let anchor = byteSpan content (fromInteger first) (fromInteger lastOffset)
  if Core.validateSpan (Core.Source "original" content bytes "") (toCoreSpan anchor)
    then Right (SourceRef (sourceId source) (Just anchor))
    else Left [issue "AANCHORBOUNDARY" "/byteRange" [sourceId source]
      "byte endpoints must be UTF-8 code-point boundaries"]

-- | Zero-based, half-open Unicode code-point offsets. These are neither UTF-16
-- code units nor grapheme clusters/display columns. No normalization is done.
sourceAnchorCodePoints :: SourceRecord -> Integer -> Integer
                       -> Either [AuthoringDiagnostic] SourceRef
sourceAnchorCodePoints source first lastOffset = do
  content <- retained source
  let points = Text.unpack content
      count = toInteger (length points)
  checkedRange source "/codePointRange" "Unicode code points" count first lastOffset
  -- Each Haskell Char here is a code point in retained Text. Count was checked
  -- before conversion; encode the exact prefixes and share byte-path validation.
  let offset n = toInteger (BS.length (Encoding.encodeUtf8 (Text.pack (take (fromInteger n) points))))
  sourceAnchorBytes source (offset first) (offset lastOffset)

retained :: SourceRecord -> Either [AuthoringDiagnostic] Text
retained source = case sourceText source of
  Just content -> Right content
  Nothing -> Left [issue "AANCHORTEXT" "/sourceText" [sourceId source]
    "an original anchor requires explicitly supplied retained text; a locator/citation is insufficient"]

checkedRange :: SourceRecord -> Text -> Text -> Integer -> Integer -> Integer
             -> Either [AuthoringDiagnostic] ()
checkedRange source location units size first lastOffset
  | first < 0 || lastOffset < first || lastOffset > size =
      Left [issue "AANCHORRANGE" location [sourceId source]
        ("expected 0 <= start <= end <= " <> Text.pack (show size) <> " (" <> units <>
          "); received [" <> Text.pack (show first) <> "," <> Text.pack (show lastOffset) <> ")")]
  | otherwise = Right ()
