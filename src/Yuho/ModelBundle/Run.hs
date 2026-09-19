{-# LANGUAGE OverloadedStrings #-}
module Yuho.ModelBundle.Run (runArgs) where

import Control.Exception (IOException, try)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.ModelBundle.Review (reviewPurposesAllowed)
import Yuho.ModelBundle.Types
import Yuho.ModelBundle.Package (validatePackage)
import Yuho.Protocol.Json (J(..))

runArgs :: [String] -> IO (Int, J)
runArgs args = case args of
  ["validate", directory] -> run directory Nothing
  ["validate", directory, "--require-asserted-review-purpose", purpose]
    | Text.pack purpose `elem` reviewPurposesAllowed -> run directory (Just (Text.pack purpose))
  _ -> pure (2, response "io_error" Nothing Nothing [] [] []
    [Failure "MBUSAGE001" "/command" "usage: yuho-model-bundle validate <directory> [--require-asserted-review-purpose <purpose>]"])
  where
    run directory policy = do
      outcome <- try (validatePackage directory policy) :: IO (Either IOException (Either Failure Validation))
      case outcome of
        Left _ -> pure (2, response "io_error" Nothing Nothing [] [] []
          [Failure "MBIO001" "/bundle" "path or I/O failure"])
        Right (Left failure) -> pure (1, response "invalid" Nothing Nothing [] [] [] [failure])
        Right (Right result) ->
          let status = if validatedPolicyMet result then "valid" else "policy_unmet"
              exitCode = if validatedPolicyMet result then 0 else 3
          in pure (exitCode, response status (Just (validatedDigest result))
            (Just (validatedScopeDigest result)) (validatedApplicable result)
            (validatedStale result) (validatedPartial result) [])

response :: Text -> Maybe Text -> Maybe Text -> [Text] -> [Text] -> [Text] -> [Failure] -> J
response status bundle scope applicable stale partial failures = JObj
  [ ("schema", JStr "yuho.model-bundle-validation/v1")
  , ("status", JStr status)
  , ("bundle_digest", maybe JNull JStr bundle)
  , ("scope_digest", maybe JNull JStr scope)
  , ("applicable_asserted_reviews", JArr (map JStr applicable))
  , ("stale_reviews", JArr (map JStr stale))
  , ("partial_reviews", JArr (map JStr partial))
  , ("review_authentication", JStr "none")
  , ("diagnostics", JArr (map failureJson failures))
  ]

failureJson :: Failure -> J
failureJson failure = JObj
  [ ("code", JStr (failureCode failure))
  , ("path", JStr (failurePath failure))
  , ("message", JStr (failureMessage failure))
  ]
