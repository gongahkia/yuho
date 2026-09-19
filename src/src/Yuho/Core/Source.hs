{-# LANGUAGE OverloadedStrings #-}
module Yuho.Core.Source (validSourcePath, validateSpan) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Core.Types (Source(..), Span(..))

validSourcePath :: Text -> Bool
validSourcePath path =
  not (Text.null path) && not (Text.isPrefixOf "/" path)
  && not (Text.any (== '\\') path)
  && all (\part -> part /= ".." && part /= "." && not (Text.null part))
         (Text.splitOn "/" path)

-- Display columns in v1 are one-based UTF-8 byte columns, matching the
-- existing Tree-sitter source-location convention. Offsets are half-open.
validateSpan :: Source -> Span -> Bool
validateSpan source sourceSpan =
  let bytes = sourceBytes source
      start = spanStart sourceSpan
      end = spanEnd sourceSpan
      boundary offset = offset == BS.length bytes ||
        (offset >= 0 && offset < BS.length bytes &&
         let byte = BS.index bytes offset in byte < 0x80 || byte >= 0xc0)
  in start >= 0 && end >= start && end <= BS.length bytes
     && boundary start && boundary end
     && position bytes start == Just (spanStartLine sourceSpan, spanStartCol sourceSpan)
     && position bytes end == Just (spanEndLine sourceSpan, spanEndCol sourceSpan)

position :: BS.ByteString -> Int -> Maybe (Int, Int)
position bytes offset
  | offset < 0 || offset > BS.length bytes = Nothing
  | otherwise = Just (BS.foldl' step (1, 1) (BS.take offset bytes))
  where
    step (line, column) byte
      | byte == 10 = (line + 1, 1)
      | otherwise = (line, column + 1)
