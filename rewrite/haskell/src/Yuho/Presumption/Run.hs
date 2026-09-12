{-# LANGUAGE OverloadedStrings #-}
module Yuho.Presumption.Run (runPresumptionLine) where

import qualified Data.ByteString as BS
import Yuho.Core.Types (Diagnostic)
import Yuho.Presumption.Decode (decodePresumptionRequest)
import Yuho.Presumption.Encode (encodePresumptionReject, encodePresumptionResult)
import Yuho.Presumption.Evaluate (evaluatePresumptions)
import Yuho.Presumption.Types (ValidatedPresumption(..), PresumptionResult(..))
import Yuho.Presumption.Validate (validatePresumptionRequest)
import Yuho.Protocol.Decode (inputDigest)
import Yuho.Protocol.Json (J, lookupField, textValue)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProofWith)
import Yuho.SuppliedProofStatus.Select (selectProofPenalties)

runPresumptionLine :: J -> BS.ByteString
runPresumptionLine value =
  let identifier = maybe "?" id (lookupField "request_id" value >>= textValue)
      digest = inputDigest value
      root = maybe "?" id (lookupField "root_rule" value >>= textValue)
      rejected :: Diagnostic -> BS.ByteString
      rejected = encodePresumptionReject identifier digest root
  in case decodePresumptionRequest value of
    Left issue -> rejected issue
    Right request -> case validatePresumptionRequest request of
      Left issue -> rejected issue
      Right validated -> case evaluatePresumptions validated of
        Left issue -> rejected issue
        Right presumption -> case evaluateProofWith
          (presumptionValidatedBase validated) (presumptionEffective presumption) of
          Left issue -> rejected issue
          Right result -> case selectProofPenalties
            (presumptionValidatedBase validated) result of
            Left issue -> rejected issue
            Right selection -> either rejected id
              (encodePresumptionResult validated presumption result selection)
