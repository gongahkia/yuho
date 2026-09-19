{-# LANGUAGE OverloadedStrings #-}
module Yuho.PenaltyTerms.Run (runTermsLine) where

import qualified Data.ByteString as BS
import Yuho.Core.Types (Diagnostic)
import Yuho.Exception.Evaluate (evaluateGraph)
import Yuho.Exception.Types (rejectException)
import Yuho.PenaltySelection.Select (selectPenalties)
import Yuho.PenaltySelection.Types (PenaltyRequest(..), ValidatedPenalties(..))
import Yuho.PenaltyTerms.Decode (decodeTermsRequest)
import Yuho.PenaltyTerms.Encode (encodeTerms, encodeTermsReject)
import Yuho.PenaltyTerms.Types (TermsRequest(..), ValidatedTerms(..))
import Yuho.PenaltyTerms.Validate (validateTerms)
import Yuho.Protocol.Decode (inputDigest)
import Yuho.Protocol.Json (J, lookupField, textValue)
import Yuho.TypedFacts.Types (TypedRequest(..))
import Yuho.TypedFacts.Validate (typedGraph)

runTermsLine :: J -> BS.ByteString
runTermsLine value =
  let identifier = maybe "?" id (lookupField "request_id" value >>= textValue)
      digest = inputDigest value
      root = maybe "?" id (lookupField "root_rule" value >>= textValue)
      rejected :: Diagnostic -> BS.ByteString
      rejected issue = encodeTermsReject (rejectException identifier digest root issue)
  in case decodeTermsRequest value of
    Left issue -> rejected issue
    Right request@(TermsRequest penalty _) -> case validateTerms request of
      Left issue -> rejected issue
      Right (ValidatedTerms validated terms) ->
        let typed = penaltyTypedRequest penalty
            exceptionRequest = typedExceptionRequest typed
        in case evaluateGraph exceptionRequest (typedGraph (validatedTyped validated)) of
          Left issue -> rejected issue
          Right result -> case selectPenalties validated result of
            Left issue -> rejected issue
            Right selection -> either rejected id (encodeTerms typed result selection terms)
