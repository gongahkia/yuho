{-# LANGUAGE OverloadedStrings #-}
-- Internal encoders for source locations; these are not original-law anchors.
module Yuho.Surface.InspectionData (locatedToken, sourceRecord) where

import qualified Data.ByteString as BS
import qualified Data.Text as Text
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Protocol.Json (J(..))
import Yuho.Surface.Token

-- The lexer retains starts only. Do not manufacture an AST end span.
locatedToken :: FilePath -> BS.ByteString -> Token -> J
locatedToken path bytes token = JObj
  [("text",JStr (tokenText token)),("kind",JStr kindName)
  ,("source",JStr (Text.pack path)),("extent",JStr "token_start_only")
  ,("line",JNum (toInteger (tokenLine token)))
  ,("column",JNum (toInteger (tokenColumn token)))
  ,("byte_offset",JNum (toInteger offset))]
  where
    offset = sum (map ((+ 1) . BS.length)
      (take (tokenLine token - 1) (BS.split 10 bytes))) + tokenColumn token - 1
    kindName = case tokenKind token of
      WordToken -> "word"; StringToken -> "string"; SymbolToken -> "symbol"; EndToken -> "end"

sourceRecord :: FilePath -> BS.ByteString -> J
sourceRecord path bytes = JObj
  [("path",JStr (Text.pack path)),("sha256",JStr (sha256Text bytes))
  ,("utf8_bytes",JNum (toInteger (BS.length bytes)))]
