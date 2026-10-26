{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Lexer (lexSource) where

import qualified Data.ByteString as BS
import Data.Char (isAsciiLower, isAsciiUpper, isDigit)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Yuho.Surface.Token

lexSource :: FilePath -> BS.ByteString -> Either Diagnostic [Token]
lexSource path bytes
  | BS.length bytes > 65536 = at "SFE016" path origin "source exceeds 65536 bytes"
  | otherwise = case Encoding.decodeUtf8' bytes of
      Left _ -> at "SFE001" path origin "source is not strict UTF-8"
      Right source -> go (Text.unpack source) 1 1 0 []
  where
    origin = Token EndToken "" 1 1
    size char = BS.length (Encoding.encodeUtf8 (Text.singleton char))
    wordChar char = isAsciiLower char || isAsciiUpper char || isDigit char
      || char `elem` ("_:./-" :: String)
    emit remaining line column count reversed token
      | count >= (4096 :: Int) = at "SFE016" path token "token limit exceeded"
      | otherwise = go remaining line column (count + 1) (token : reversed)
    go [] line column _ reversed = Right (reverse (Token EndToken "" line column : reversed))
    go remaining line column count reversed = case remaining of
          '\n':rest -> go rest (line + 1) 1 count reversed
          char:rest | char == ' ' || char == '\t' -> go rest line (column + size char) count reversed
          '\r':_ -> at "SFE001" path (Token EndToken "" line column) "only LF source is supported"
          '\0':_ -> at "SFE001" path (Token EndToken "" line column) "NUL is unsupported"
          '/':'/':rest -> let (comment, after) = break (== '\n') rest
            in if any (`elem` ("\r\0" :: String)) comment
               then at "SFE001" path (Token EndToken "" line column) "invalid comment"
               else go after line (column + 2 + sum (map size comment)) count reversed
          '"':rest -> case break (== '"') rest of
            (value, '"':after)
              | not (any (`elem` ("\n\r\0" :: String)) value)
                && '\\' `notElem` value ->
                  emit after line (column + 2 + sum (map size value)) count reversed
                    (Token StringToken (Text.pack value) line column)
              | otherwise -> at "SFE013" path (Token StringToken "" line column) "string escapes or line breaks are unsupported"
            _ -> at "SFE001" path (Token StringToken "" line column) "unterminated string"
          char:rest | char `elem` ("{}(),;=" :: String) ->
            emit rest line (column + 1) count reversed (Token SymbolToken (Text.singleton char) line column)
          char:_ | wordChar char ->
            let (value, after) = span wordChar remaining
                item = Text.pack value
            in emit after line (column + length value) count reversed (Token WordToken item line column)
          char:_ -> at "SFE001" path (Token EndToken (Text.singleton char) line column) "invalid character"
