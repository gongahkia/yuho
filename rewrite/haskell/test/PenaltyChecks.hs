{-# LANGUAGE OverloadedStrings #-}
module PenaltyChecks (runPenaltyChecks) where

import Control.Monad (forM_, unless)
import qualified Data.Aeson as Aeson
import qualified Data.ByteString as BS
import qualified Data.List as List
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Test.QuickCheck (arbitrary, forAll, isSuccess, maxSuccess, quickCheckWithResult, stdArgs)
import Yuho.Exception.Evaluate (evaluateGraph, evaluateGraphReference)
import Yuho.Exception.Types
import Yuho.Kernel.Run (runLine)
import Yuho.PenaltySelection.Decode (decodePenaltyRequest)
import Yuho.PenaltySelection.Select (overlapPaths, selectPenalties)
import Yuho.PenaltySelection.Types
import Yuho.PenaltySelection.Validate (validatePenalties)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, objectFields, textValue)
import Yuho.TypedFacts.Types (TypedRequest(..))
import Yuho.TypedFacts.Validate (typedGraph, typedRequest)

runPenaltyChecks :: FilePath -> IO ()
runPenaltyChecks directory = do
  cases <- BS.readFile (directory </> "CASES.json")
  rows <- case decodeJson cases >>= maybe (Left "expected cases") Right . objectFields of
    Left reason -> putStrLn (Text.unpack reason) >> exitFailure
    Right found -> pure found
  forM_ rows $ \(name, expected) -> do
    file <- maybe (putStrLn "missing fixture filename" >> exitFailure) pure
      (lookupField "request_file" expected >>= textValue)
    request <- BS.readFile (directory </> Text.unpack file)
    let result = runLine request
        actual = (,) <$> field "status" result <*> diagnosticCode result
        wanted = (,) <$> (lookupField "status" expected >>= textValue)
                     <*> (lookupField "code" expected >>= textValue)
    if name == "GP38" then check "4096 occurrence boundary" (largeBoundary result)
      else check ("penalty fixture " <> Text.unpack name) (actual == wanted)
  true <- readRequest directory "GP01"
  defeated <- readRequest directory "GP04"
  inherited <- readRequest directory "GP06"
  duplicated <- readRequest directory "GP07"
  sibling <- readRequest directory "GP08"
  guardTrue <- readRequest directory "GP09"
  guardFalse <- readRequest directory "GP10"
  sameGuard <- readRequest directory "GP12"
  overlap <- readRequest directory "GP13"
  permuted <- readRequest directory "GP14"
  separate <- readRequest directory "GP15"
  target <- readRequest directory "GP18"
  missing <- readRequest directory "GP19"
  scoped <- readRequest directory "GP20"
  typed <- readRequest directory "GP28"
  provenance <- readRequest directory "GP29"
  exact <- readRequest directory "GP36"
  property "selection determinism under registry order" (forAll arbitrary $ \flag ->
    let sample = factValue "f:target" flag defeated
    in selectedIds (response sample) == selectedIds (response (reverseRegistry sample)))
  property "no selection outside final-true branches" (forAll arbitrary $ \(first, second) ->
    supportsTrue (response (factValue "f:first" first
      (factValue "f:second" second duplicated))))
  property "exception defeat suppresses candidates" (forAll arbitrary $ \flag ->
    null (selectedIds (response (factValue "f:root" flag defeated))))
  property "guard uses evaluated leaf Boolean" (forAll arbitrary $ \flag ->
    selectedIds (response (factValue "f:third" flag
      (factValue "f:second" True guardTrue))) ==
      (if flag then ["pen:root:1"] else []))
  property "ancestor declaration stays on descendant path" (forAll arbitrary $ \flag ->
    let result = response (factValue "f:second" flag inherited)
    in all (`elem` [["second"]]) (supportPaths result))
  property "sibling declarations do not leak" (forAll arbitrary $ \flag ->
    null (selectedIds (response (factValue "f:second" flag sibling))))
  property "one selected record per penalty ID" (forAll arbitrary $ \flag ->
    let ids = selectedIds (response (factValue "f:first" flag duplicated))
    in ids == List.nub ids)
  property "all satisfied descendants support inherited ID" (forAll arbitrary $ \flag ->
    let result = response (factValue "f:first" flag duplicated)
    in supportPaths result == (if flag then [["first"], ["second"]] else [["second"]]))
  property "same true guard declarations accumulate" (forAll arbitrary $ \flag ->
    selectedIds (response (factValue "f:root" flag sameGuard)) ==
      (if flag then ["pen:one", "pen:two"] else []))
  property "overlap retains all candidates" (forAll arbitrary $ \flag ->
    let result = response (factValue "f:third" flag (factValue "f:second" True overlap))
    in selectedIds result == (if flag then ["pen:one", "pen:two"] else ["pen:one"]))
  property "KSEL001 requires distinct same-provision guards on one path"
    (forAll arbitrary $ \flag ->
      warningCount (response (factValue "f:third" flag
        (factValue "f:second" True overlap))) ==
        (if flag then 1 else 0) && warningCount (response sameGuard) == 0 &&
        warningCount (response separate) == 0)
  property "declaration permutation preserves verdict and ID set"
    (forAll arbitrary $ \flag ->
      let left = response (factValue "f:third" flag (factValue "f:second" True overlap))
          right = response (factValue "f:third" flag (factValue "f:second" True permuted))
      in field "status" left == field "status" right &&
         List.sort (selectedIds left) == List.sort (selectedIds right))
  property "exact guard ID does not normalize" (forAll arbitrary $ \flag ->
    diagnosticCode (response (factValue "f:root" flag exact)) == Just "KINV008")
  property "invalid guard models never select" (forAll arbitrary $ \flag ->
    let first = response (factValue "f:root" flag missing)
        second = response (factValue "f:second" flag scoped)
    in field "status" first == Just "rejected" &&
       field "status" second == Just "rejected" &&
       null (selectedIds first) && null (selectedIds second))
  property "matching typed metadata cannot alter selection" (forAll arbitrary $ \flag ->
    (not . null . selectedIds) (response (factValue "f:root" flag typed)) ==
      (not . null . selectedIds) (response (factValue "f:root" flag true)))
  property "descriptive provenance cannot alter selection" (forAll arbitrary $ \flag ->
    let changed = modify "facts" (modify "f:root" (modify "provenance"
          (const (JObj [("source_label", JStr (if flag then "first" else "second"))]))))
          provenance
    in selectedIds (response changed) == selectedIds (response provenance))
  property "memoized and reference dependency evaluation agree" (forAll arbitrary $ \flag ->
    referenceAgreement (factValue "f:target" flag target))
  property "canonical bytes ignore object insertion order" (forAll arbitrary $ \flag ->
    let sample = factValue "f:root" flag true
    in response sample == response (reverseObjects sample))
  check "unresolved branch skips guard at pure boundary" (unresolvedSkip true)
  check "distinct guards selected only on disjoint paths do not overlap"
    (disjointOverlap overlap)
  check "false guard on satisfied branch is visible" (
    traceResults (response guardFalse) == ["guard_false"])
  putStrLn "penalty: 49 fixtures, 18 bounded properties and 3 internal cases passed"
  where
    property title predicate = do
      result <- quickCheckWithResult stdArgs {maxSuccess = 25} predicate
      check title (isSuccess result)

readRequest :: FilePath -> String -> IO J
readRequest directory name = do
  bytes <- BS.readFile (directory </> "requests" </> name <> ".json")
  case decodeJson bytes of
    Left reason -> putStrLn (Text.unpack reason) >> exitFailure
    Right value -> pure value

check :: String -> Bool -> IO ()
check title passed = unless passed (putStrLn ("failed: " <> title) >> exitFailure)

response :: J -> BS.ByteString
response = runLine . encodeJson

field :: Text -> BS.ByteString -> Maybe Text
field key bytes = either (const Nothing) (\value -> lookupField key value >>= textValue)
  (decodeJson bytes)

diagnosticCode :: BS.ByteString -> Maybe Text
diagnosticCode bytes = do
  value <- either (const Nothing) Just (decodeJson bytes)
  JArr issues <- lookupField "diagnostics" value
  case issues of
    [] -> Just ""
    first : _ -> lookupField "code" first >>= textValue

selectedIds :: BS.ByteString -> [Text]
selectedIds bytes = case decodeJson bytes of
  Left _ -> []
  Right value -> case lookupField "selected_penalties" value of
    Just (JArr items) -> [identifier | item <- items
      , Just identifier <- [lookupField "penalty_id" item >>= textValue]]
    _ -> []

supportPaths :: BS.ByteString -> [[Text]]
supportPaths bytes = case decodeJson bytes of
  Left _ -> []
  Right value -> [path | Just (JArr items) <- [lookupField "selected_penalties" value]
    , item <- items, Just (JArr supports) <- [lookupField "supporting_branches" item]
    , support <- supports, Just (JArr pieces) <- [lookupField "path" support]
    , Just path <- [traverse textValue pieces]]

supportsTrue :: BS.ByteString -> Bool
supportsTrue bytes = case decodeJson bytes of
  Left _ -> False
  Right value -> case lookupField "rules" value of
    Just (JArr (root:_)) ->
      let statuses = [(identifier, status) | Just (JArr branches) <-
            [lookupField "branches" root], branch <- branches
            , Just identifier <- [lookupField "id" branch >>= textValue]
            , Just status <- [lookupField "status" branch >>= textValue]]
      in all (\identifier -> lookup identifier statuses == Just "true")
        [identifier | Just (JArr penalties) <- [lookupField "selected_penalties" value]
          , item <- penalties
          , Just (JArr supports) <- [lookupField "supporting_branches" item]
          , support <- supports
          , Just identifier <- [lookupField "branch_id" support >>= textValue]]
    _ -> False

warningCount :: BS.ByteString -> Int
warningCount bytes = case decodeJson bytes of
  Left _ -> 0
  Right value -> case lookupField "selection_warnings" value of
    Just (JArr items) -> length items
    _ -> 0

traceResults :: BS.ByteString -> [Text]
traceResults bytes = case decodeJson bytes of
  Left _ -> []
  Right value -> [outcome | Just (JArr items) <- [lookupField "penalty_selection_trace" value]
    , item <- items, Just outcome <- [lookupField "result" item >>= textValue]]

largeBoundary :: BS.ByteString -> Bool
largeBoundary bytes = case (Aeson.eitherDecodeStrict' bytes ::
  Either String (Map.Map Text Aeson.Value)) of
  Left _ -> False
  Right result ->
    let fieldList key = case Map.lookup key result of
          Just value -> case Aeson.fromJSON value of
            Aeson.Success items -> Just (items :: [Aeson.Value])
            Aeson.Error _ -> Nothing
          Nothing -> Nothing
    in Map.lookup "status" result == Just (Aeson.String "true") &&
      fmap length (fieldList "selected_penalties") == Just 64 &&
      fmap length (fieldList "penalty_selection_trace") == Just 4096 &&
      fieldList "selection_warnings" == Just []

factValue :: Text -> Bool -> J -> J
factValue identifier truth = modify "facts" (modify identifier (modify "value" (const (JBool truth))))

modify :: Text -> (J -> J) -> J -> J
modify key change (JObj fields) = JObj
  [(name, if name == key then change value else value) | (name, value) <- fields]
modify _ _ other = other

reverseObjects :: J -> J
reverseObjects (JObj fields) = JObj (reverse
  [(key, reverseObjects value) | (key, value) <- fields])
reverseObjects (JArr items) = JArr (map reverseObjects items)
reverseObjects other = other

reverseRegistry :: J -> J
reverseRegistry = modify "registry" change
  where
    change (JArr items) = JArr (reverse items)
    change other = other

referenceAgreement :: J -> Bool
referenceAgreement input = case decodePenaltyRequest input >>= validatePenalties of
  Left _ -> False
  Right graph -> let typed = typedRequest (validatedTyped graph)
                     request = typedExceptionRequest typed
                     validated = typedGraph (validatedTyped graph)
                 in case (evaluateGraph request validated,
                          evaluateGraphReference request validated) of
                   (Right memoized, Right reference) -> memoized == reference &&
                     selectPenalties graph memoized == selectPenalties graph reference
                   _ -> False

unresolvedSkip :: J -> Bool
unresolvedSkip input = case decodePenaltyRequest input >>= validatePenalties of
  Left _ -> False
  Right graph ->
    let typed = typedRequest (validatedTyped graph)
        request = typedExceptionRequest typed
    in case evaluateGraph request (typedGraph (validatedTyped graph)) of
      Left _ -> False
      Right evaluated -> case exceptionResultRules evaluated of
        root : others -> case ruleResultBranches root of
          branch : rest ->
            let changedBranch = branch {exceptionBranchStatus = UnresolvedValue,
                                        exceptionBranchReason = GuardUnresolved}
                changedRule = root {ruleResultBranches = changedBranch : rest}
                changedResult = evaluated {exceptionResultRules = changedRule : others}
            in case selectPenalties graph changedResult of
              Right selection -> selectedPenalties selection == [] &&
                map occurrenceResult (selectionTrace selection) == ["branch_unresolved"]
              Left _ -> False
          [] -> False
        [] -> False

disjointOverlap :: J -> Bool
disjointOverlap input = case decodePenaltyRequest input >>= validatePenalties of
  Left _ -> False
  Right graph -> case validatedDeclarations graph of
    first : second : _ ->
      let uses = [BranchUse "r:root" "p:first" ["first"] [] [first, second],
                  BranchUse "r:root" "p:second" ["second"] [] [first, second]]
          occurrence item branch path = PenaltyOccurrence item branch path False TrueValue
            Satisfied (Just True) "selected"
          selected = [occurrence first "p:first" ["first"],
                      occurrence second "p:second" ["second"]]
      in overlapPaths "p:root" uses selected == []
    _ -> False
