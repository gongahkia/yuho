{-# LANGUAGE OverloadedStrings #-}
module Yuho.SuppliedProofStatus.Run (runProofLine) where

import qualified Data.ByteString as BS
import Yuho.Core.Types (Diagnostic)
import Yuho.Protocol.Decode (inputDigest)
import Yuho.Protocol.Json (J, lookupField, textValue)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Encode (encodeProofReject, encodeProofResult)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProof)
import Yuho.SuppliedProofStatus.Select (selectProofPenalties)
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)

runProofLine :: J -> BS.ByteString
runProofLine value =
  let identifier = maybe "?" id (lookupField "request_id" value >>= textValue)
      digest = inputDigest value
      root = maybe "?" id (lookupField "root_rule" value >>= textValue)
      rejected :: Diagnostic -> BS.ByteString
      rejected = encodeProofReject identifier digest root
  in case decodeProofRequest value of
    Left issue -> rejected issue
    Right request -> case validateProofRequest request of
      Left issue -> rejected issue
      Right validated -> case evaluateProof validated of
        Left issue -> rejected issue
        Right result -> case selectProofPenalties validated result of
          Left issue -> rejected issue
          Right selection -> either rejected id
            (encodeProofResult validated result selection)
