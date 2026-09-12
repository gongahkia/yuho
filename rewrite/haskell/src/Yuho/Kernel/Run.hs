{-# LANGUAGE OverloadedStrings #-}
module Yuho.Kernel.Run (runLine, rejectResource) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import Yuho.Core.Types
import Yuho.Kernel.Evaluate (evaluate)
import Yuho.Kernel.Validate (validateInput)
import Yuho.Protocol.Decode (decodeRequest, inputDigest, sha256Text)
import Yuho.Protocol.Encode (encodeResult)
import Yuho.Protocol.Json (decodeJson, lookupField, textValue)

runLine :: BS.ByteString -> BS.ByteString
runLine bytes = case decodeJson bytes of
  Left reason -> encodeResult (reject "?" (sha256Text BS.empty)
    (diagnostic "KDEC001" "decode" "/" Nothing [("reason", reason)]))
  Right value ->
    let requestIdentifier = maybe "?" id (lookupField "request_id" value >>= textValue)
        digest = inputDigest value
        rejected issue = encodeResult (reject requestIdentifier digest issue)
    in case decodeRequest value of
      Left issue -> rejected issue
      Right request -> case validateInput (requestInput request) of
        Left issue -> rejected issue
        Right () -> either rejected encodeResult (evaluate request)

rejectResource :: BS.ByteString
rejectResource = encodeResult (reject "?" (sha256Text BS.empty)
  (diagnostic "KDEC002" "decode" "/" Nothing
    [("reason", "request exceeds 1048576 bytes")]))

reject :: Text -> Text -> Diagnostic -> KernelResult
reject identifier digest issue = KernelResult identifier digest "rejected" "none" [] [] [issue]
