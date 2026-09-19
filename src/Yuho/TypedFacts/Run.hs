{-# LANGUAGE OverloadedStrings #-}
module Yuho.TypedFacts.Run (runTypedLine) where

import qualified Data.ByteString as BS
import Yuho.Core.Types (Diagnostic)
import Yuho.Exception.Evaluate (evaluateGraph)
import Yuho.Exception.Types
import Yuho.Protocol.Decode (inputDigest)
import Yuho.Protocol.Json (J, lookupField, textValue)
import Yuho.TypedFacts.Decode (decodeTypedRequest)
import Yuho.TypedFacts.Encode (encodeTypedReject, encodeTypedResult)
import Yuho.TypedFacts.Types (typedExceptionRequest)
import Yuho.TypedFacts.Validate (typedGraph, validateTyped)

runTypedLine :: J -> BS.ByteString
runTypedLine value =
  let identifier = maybe "?" id (lookupField "request_id" value >>= textValue)
      digest = inputDigest value
      root = maybe "?" id (lookupField "root_rule" value >>= textValue)
      rejected :: Diagnostic -> BS.ByteString
      rejected issue = encodeTypedReject (rejectException identifier digest root issue)
  in case decodeTypedRequest value of
    Left issue -> rejected issue
    Right request -> case validateTyped request of
      Left issue -> rejected issue
      Right validated -> case evaluateGraph (typedExceptionRequest request) (typedGraph validated) of
        Left issue -> rejected issue
        Right result -> either rejected id (encodeTypedResult request result)
