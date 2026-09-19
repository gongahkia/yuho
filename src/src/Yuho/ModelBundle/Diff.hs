{-# LANGUAGE OverloadedStrings #-}
module Yuho.ModelBundle.Diff (runDiff, diagnosticsJson) where

import Control.Exception (IOException, try)
import Data.Text (Text)
import Yuho.ModelBundle.ChangeSet (compareSnapshots, encodeChangeSet)
import Yuho.ModelBundle.Package (PackageSnapshot, validatePackageSnapshot)
import Yuho.ModelBundle.Types (Failure(..))
import Yuho.Protocol.Json (J(..))

runDiff :: [String] -> IO (Int, Maybe J, [Failure])
runDiff args = case args of
  ["diff", oldDirectory, newDirectory] -> do
    old <- checked oldDirectory
    new <- checked newDirectory
    case (old, new) of
      (Left oldProblem, Left newProblem)
        | isIo oldProblem || isIo newProblem -> pure (2, Nothing,
            [side "old" oldProblem, side "new" newProblem])
        | otherwise -> pure (1, Nothing, [side "old" oldProblem, side "new" newProblem])
      (Left problem, _) -> pure (if isIo problem then 2 else 1, Nothing, [side "old" problem])
      (_, Left problem) -> pure (if isIo problem then 2 else 1, Nothing, [side "new" problem])
      (Right oldSnapshot, Right newSnapshot) -> do
        -- Check both complete validated snapshots again before publishing a report.
        -- This detects mutation during comparison without using filesystem metadata.
        oldAgain <- checked oldDirectory
        newAgain <- checked newDirectory
        case (oldAgain, newAgain) of
          (Right oldCurrent, Right newCurrent)
            | oldCurrent == oldSnapshot && newCurrent == newSnapshot ->
                case compareSnapshots oldSnapshot newSnapshot of
                  Left failure -> pure (4, Nothing, [failure])
                  Right report -> pure (0, Just (encodeChangeSet report), [])
          _ -> pure (1, Nothing,
            [Failure "MBCDINV002" "/bundles" "validated package changed during comparison"])
  _ -> pure (2, Nothing,
    [Failure "MBCDUSAGE001" "/command" "usage: yuho-model-bundle diff <old-directory> <new-directory>"])

checked :: FilePath -> IO (Either Failure PackageSnapshot)
checked directory = do
  outcome <- try (validatePackageSnapshot directory Nothing)
    :: IO (Either IOException (Either Failure PackageSnapshot))
  pure (either (const (Left (Failure "MBCDIO001" "/bundle" "path or I/O failure"))) id outcome)

isIo :: Failure -> Bool
isIo failure = failureCode failure == "MBCDIO001"

side :: Text -> Failure -> Failure
side label failure = failure {failurePath = "/" <> label <> failurePath failure}

diagnosticsJson :: [Failure] -> J
diagnosticsJson failures = JObj
  [("schema", JStr "yuho.model-bundle-diff-diagnostics/v1")
  , ("diagnostics", JArr (map failureJson failures))]

failureJson :: Failure -> J
failureJson failure = JObj
  [("code", JStr (failureCode failure))
  , ("path", JStr (failurePath failure))
  , ("message", JStr (failureMessage failure))]
