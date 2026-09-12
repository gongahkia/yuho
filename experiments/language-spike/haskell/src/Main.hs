module Main (main) where

import qualified Data.ByteString as BS
import qualified Data.ByteString.Char8 as Char8
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Json (encodeJson, parseJson)
import Kernel (decodeFailure, run)
import System.IO (hIsEOF, stdin, stdout)

main :: IO ()
main = loop

loop :: IO ()
loop = do
  done <- hIsEOF stdin
  if done then pure () else do
    line <- Char8.hGetLine stdin
    let response = case Encoding.decodeUtf8' line of
          Left _ -> decodeFailure "invalid UTF-8"
          Right textValue -> case parseJson (Text.unpack textValue) of
            Left message -> decodeFailure message
            Right value -> run value
    BS.hPut stdout (Encoding.encodeUtf8 (Text.pack (encodeJson response ++ "\n")))
    loop
