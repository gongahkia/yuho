{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltySelection.Run (runPenaltyLine) where

import qualified Data.ByteString as BS
import Yuho.Core.Types (Diagnostic)
import Yuho.Exception.Evaluate (evaluateGraph)
import Yuho.Exception.Types (rejectException)
import Yuho.PenaltySelection.Decode (decodePenaltyRequest)
import Yuho.PenaltySelection.Encode (encodeSelection, encodeSelectionReject)
import Yuho.PenaltySelection.Select (selectPenalties)
import Yuho.PenaltySelection.Types
import Yuho.PenaltySelection.Validate (validatePenalties)
import Yuho.Protocol.Decode (inputDigest)
import Yuho.Protocol.Json (J, lookupField, textValue)
import Yuho.TypedFacts.Types (TypedRequest(..))
import Yuho.TypedFacts.Validate (typedGraph)

runPenaltyLine :: J -> BS.ByteString
runPenaltyLine value =
  let identifier = maybe "?" id (lookupField "request_id" value >>= textValue)
      digest = inputDigest value
      root = maybe "?" id (lookupField "root_rule" value >>= textValue)
      rejected :: Diagnostic -> BS.ByteString
      rejected issue = encodeSelectionReject (rejectException identifier digest root issue)
  in case decodePenaltyRequest value of
    Left issue -> rejected issue
    Right request -> case validatePenalties request of
      Left issue -> rejected issue
      Right validated ->
        let typed = penaltyTypedRequest request
            exceptionRequest = typedExceptionRequest typed
        in case evaluateGraph exceptionRequest (typedGraph (validatedTyped validated)) of
          Left issue -> rejected issue
          Right result -> case selectPenalties validated result of
            Left issue -> rejected issue
            Right selection -> either rejected id (encodeSelection typed result selection)
