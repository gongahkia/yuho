{-# LANGUAGE OverloadedStrings #-}
module Yuho.Kernel.Run (runLine, rejectResource) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import Yuho.Core.Types
import Yuho.Exception.Run (runExceptionLine)
import Yuho.PenaltySelection.Run (runPenaltyLine)
import Yuho.PenaltyTerms.Run (runTermsLine)
import Yuho.Presumption.Run (runPresumptionLine)
import Yuho.SuppliedProofStatus.Run (runProofLine)
import Yuho.TypedFacts.Run (runTypedLine)
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
    in if (lookupField "fragment" value >>= textValue) == Just "RegisteredPresumptionDerivations-v1"
       then runPresumptionLine value
       else if (lookupField "fragment" value >>= textValue) == Just "SuppliedProofStatus-v1"
       then runProofLine value
       else if (lookupField "fragment" value >>= textValue) == Just "PenaltyTerms-v1"
       then runTermsLine value
       else if (lookupField "fragment" value >>= textValue) == Just "GuardedPenaltySelection-v1"
       then runPenaltyLine value
       else if (lookupField "fragment" value >>= textValue) == Just "TypedBooleanFacts-v1"
       then runTypedLine value
       else if (lookupField "fragment" value >>= textValue) == Just "AcyclicGuardedExceptions-v1"
       then runExceptionLine value else case decodeRequest value of
      Left issue -> rejected issue
      Right request -> case validateInput (requestInput request) of
        Left issue -> rejected issue
        Right () -> either rejected encodeResult (evaluate request)

rejectResource :: BS.ByteString
rejectResource = encodeResult (reject "?" (sha256Text BS.empty)
  (diagnostic "KDEC002" "decode" "/" Nothing
    [("reason", "request exceeds 1048576 bytes")]))

reject :: Text -> Text -> Diagnostic -> KernelResult
reject identifier digest issue = KernelResult identifier digest ResultRejected NoProvision [] [] [issue]
