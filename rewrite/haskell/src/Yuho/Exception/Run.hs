{-# LANGUAGE OverloadedStrings #-}
module Yuho.Exception.Run (runExceptionLine) where

import qualified Data.ByteString as BS
import Yuho.Core.Types (Diagnostic)
import Yuho.Exception.Decode (decodeExceptionRequest)
import Yuho.Exception.Encode (encodeExceptionResult)
import Yuho.Exception.Evaluate (evaluateGraph)
import Yuho.Exception.Types (rejectException, exceptionRawGraph)
import Yuho.Exception.Validate (validateGraph)
import Yuho.Protocol.Decode (inputDigest)
import Yuho.Protocol.Json (J, lookupField, textValue)

runExceptionLine :: J -> BS.ByteString
runExceptionLine value =
  let identifier = maybe "?" id (lookupField "request_id" value >>= textValue)
      root = maybe "?" id (lookupField "root_rule" value >>= textValue)
      digest = inputDigest value
      rejected :: Diagnostic -> BS.ByteString
      rejected issue = encodeExceptionResult (rejectException identifier digest root issue)
  in case decodeExceptionRequest value of
    Left issue -> rejected issue
    Right request -> case validateGraph (exceptionRawGraph request) of
      Left issue -> rejected issue
      Right graph -> either rejected encodeExceptionResult (evaluateGraph request graph)
