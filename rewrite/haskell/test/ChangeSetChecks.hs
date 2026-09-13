{-# LANGUAGE OverloadedStrings #-}
module ChangeSetChecks (runChangeSetChecks) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import Data.Either (isLeft)
import Data.List (sort)
import qualified Data.Text as Text
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Test.QuickCheck (Testable, elements, forAll, isSuccess, maxSuccess, quickCheckWithResult, stdArgs)
import Yuho.ModelBundle.ChangeSet
import Yuho.ModelBundle.Package (PackageSnapshot, validatePackageSnapshot)
import Yuho.ModelBundle.Types (Failure(..))
import Yuho.Protocol.Json (J(..), encodeJson, lookupField)

runChangeSetChecks :: FilePath -> IO ()
runChangeSetChecks fixtures = do
  let base = fixtures </> "bundles/DX01-base"
      review = fixtures </> "bundles/DX02-same-core-review"
      source = fixtures </> "bundles/DX03-source-metadata"
      model = fixtures </> "bundles/DX06-model-artifact"
  a <- snapshot base
  b <- snapshot review
  c <- snapshot source
  d <- snapshot model
  equal <- report a a
  changed <- report a c
  reverseChange <- report c a
  check "change-set equal cores have only unchanged records"
    (all ((== Unchanged) . rowClassification) (changeRows equal)
      && changeOldBundle equal == changeNewBundle equal)
  check "change-set same core review is detached"
    (case compareSnapshots a b of
      Right value -> changeOldBundle value == changeNewBundle value
        && null (changeOldNonApplicableReviews value)
      Left _ -> False)
  check "change-set modified stable source"
    (any (\row -> rowCategory row == "legal_sources"
      && rowClassification row == Modified) (changeRows changed))
  check "change-set direction swaps exact subject digests"
    (changeOldBundle changed == changeNewBundle reverseChange
      && changeNewBundle changed == changeOldBundle reverseChange)
  check "change-set changed model reports wider uncertainty"
    (case compareSnapshots a d of
      Right value -> lookupField "wider_downstream_impact" (encodeChangeSet value) == Just (JStr "unknown")
      Left _ -> False)
  let bytes = encodeJson (encodeChangeSet changed)
  check "change-set canonical decode round trip" (decodeChangeSet bytes == Right changed)
  check "change-set malformed JSON rejects" (isLeft (decodeChangeSet "{"))
  check "change-set duplicate key rejects"
    (isLeft (decodeChangeSet (BS.init bytes <> ",\"schema\":\"yuho.model-bundle-change-set/v1\"}")))
  let root = encodeChangeSet changed
      wrongEnum = replace "changes" (case lookupField "changes" root of
        Just (JArr (JObj row:rest)) -> JArr (JObj (("classification", JStr "renamed")
          : filter ((/= "classification") . fst) row) : rest)
        other -> maybe (JArr []) id other) root
      unknownField = case root of
        JObj pairs -> JObj (("untrusted", JBool True) : pairs)
        other -> other
  check "change-set unknown classification rejects" (isLeft (decodeChangeSet (encodeJson wrongEnum)))
  check "change-set unknown field rejects" (isLeft (decodeChangeSet (encodeJson unknownField)))
  check "change-set count cap rejects"
    (case checkChangeSetLimits changed {changeRows = replicate (changeRecordLimit + 1)
        (ChangeRow "scope" "synthetic" Added Nothing (Just (Text.replicate 64 "a")))} of
      Left failure -> failureCode failure == "MBCDRES001"
      Right _ -> False)
  check "change-set byte cap rejects"
    (case checkChangeSetLimits changed {changeAffectedIds = [Text.replicate changeSetLimit "x"]} of
      Left failure -> failureCode failure == "MBCDRES001"
      Right _ -> False)
  let pairs = [(a,a), (a,b), (a,c), (c,a), (a,d), (d,a), (c,d)]
  property "change-set deterministic validated comparison" $ forAll (elements pairs) $ \(left,right) ->
    compareSnapshots left right == compareSnapshots left right
  property "change-set directional row classes" $ forAll (elements pairs) $ \(left,right) ->
    case (compareSnapshots left right, compareSnapshots right left) of
      (Right forward, Right backward) ->
        sort (map flipRow (changeRows forward)) == sort (map rowTuple (changeRows backward))
      _ -> False
  property "change-set summary count consistency" $ forAll (elements pairs) $ \(left,right) ->
    case compareSnapshots left right of
      Right result -> (lookupField "summary" (encodeChangeSet result) >>= lookupField "total")
        == Just (JNum (toInteger (length (changeRows result))))
      _ -> False
  putStrLn "model bundle change set: pure checks and bounded properties passed"

rowTuple :: ChangeRow -> (Text.Text, Text.Text, Classification, Maybe Text.Text, Maybe Text.Text)
rowTuple row = (rowCategory row, rowIdentity row, rowClassification row
  , rowOldDigest row, rowNewDigest row)

flipRow :: ChangeRow -> (Text.Text, Text.Text, Classification, Maybe Text.Text, Maybe Text.Text)
flipRow row = (rowCategory row, rowIdentity row, flipClass (rowClassification row)
  , rowNewDigest row, rowOldDigest row)

flipClass :: Classification -> Classification
flipClass Added = Removed
flipClass Removed = Added
flipClass value = value

replace :: Text.Text -> J -> J -> J
replace key value (JObj pairs) = JObj [(name, if name == key then value else item)
  | (name, item) <- pairs]
replace _ _ value = value

snapshot :: FilePath -> IO PackageSnapshot
snapshot path = do
  result <- validatePackageSnapshot path Nothing
  case result of
    Left failure -> print failure >> exitFailure
    Right value -> pure value

report :: PackageSnapshot -> PackageSnapshot -> IO ChangeSet
report old new = case compareSnapshots old new of
  Left failure -> print failure >> exitFailure
  Right value -> pure value

check :: String -> Bool -> IO ()
check name condition = unless condition (putStrLn ("failed: " <> name) >> exitFailure)

property :: Testable prop => String -> prop -> IO ()
property name statement = do
  putStrLn name
  result <- quickCheckWithResult stdArgs {maxSuccess = 100} statement
  unless (isSuccess result) exitFailure
