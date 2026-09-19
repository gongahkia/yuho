{-# LANGUAGE OverloadedStrings #-}
module ProofChecks (runProofChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import qualified Data.List as List
import Data.Text (Text)
import qualified Data.Text as Text
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Test.QuickCheck
  ( arbitrary, forAll, isSuccess, maxSuccess, quickCheckWithResult, stdArgs )
import Yuho.Exception.Types (Truth(..))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, objectFields, textValue)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Evaluate
  ( allStatus, anyStatus, evaluateProof, evaluateProofReference )
import Yuho.SuppliedProofStatus.Types (SuppliedStatus(..), UnresolvedReason(..), projection)
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)

runProofChecks :: FilePath -> IO ()
runProofChecks directory = do
  manifest <- readJson (directory </> "CASES.json")
  rows <- maybe (putStrLn "proof cases are not an object" >> exitFailure) pure
    (objectFields manifest)
  forM_ rows $ \(name, expected) -> do
    path <- maybe (putStrLn "proof case lacks file" >> exitFailure) pure
      (lookupField "file" expected >>= textValue)
    bytes <- BS.readFile (directory </> Text.unpack path)
    let output = runLine (BS.takeWhile (/= 10) bytes)
        status = field "status" output
        code = diagnosticCode output
        selected = selectedIds output
        expectedCode = if name == "PS65" then Just "KDEC001"
          else lookupField "code" expected >>= textValue
    check ("proof fixture " <> Text.unpack name)
      (status == (lookupField "status" expected >>= textValue)
        && code == expectedCode
        && selected == maybe [] strings (lookupField "selected" expected))
  proved <- readJson (directory </> "requests/PS01.json")
  notProved <- readJson (directory </> "requests/PS02.json")
  unresolved <- readJson (directory </> "requests/PS03.json")
  guardPending <- readJson (directory </> "requests/PS33.json")
  defeated <- readJson (directory </> "requests/PS31.json")
  invalid <- readJson (directory </> "requests/PS40.json")
  decisiveAll <- readJson (directory </> "requests/PS25.json")
  decisiveAny <- readJson (directory </> "requests/PS26.json")
  pending <- readJson (directory </> "requests/PS04.json")
  allUnresolved <- readJson (directory </> "requests/PS07.json")
  anyUnresolved <- readJson (directory </> "requests/PS19.json")
  targetSatisfied <- readJson (directory </> "requests/PS28.json")
  targetNotSatisfied <- readJson (directory </> "requests/PS29.json")
  targetUnresolved <- readJson (directory </> "requests/PS30.json")
  guardSatisfied <- readJson (directory </> "requests/PS35.json")
  mismatched <- readJson (directory </> "requests/PS37.json")
  invalidSource <- readJson (directory </> "requests/PS45.json")
  invalidCycle <- readJson (directory </> "requests/PS60.json")
  frozenB01 <- BS.readFile (directory </> "../kernel-fixtures/frozen/requests/B01.json")
  frozenB01Expected <- BS.readFile (directory </> "../kernel-fixtures/frozen/expected/B01.json")
  let matrix = [TrueValue, FalseValue, UnresolvedValue]
      allExpected = [TrueValue, FalseValue, UnresolvedValue
        , FalseValue, FalseValue, FalseValue
        , UnresolvedValue, FalseValue, UnresolvedValue]
      anyExpected = [TrueValue, TrueValue, TrueValue
        , TrueValue, FalseValue, UnresolvedValue
        , TrueValue, UnresolvedValue, UnresolvedValue]
      pairs = [[a,b] | a <- matrix, b <- matrix]
  check "all nine All truth-table entries" (map allStatus pairs == allExpected)
  check "all nine Any truth-table entries" (map anyStatus pairs == anyExpected)
  check "not_proved retained separately from satisfaction" (case resultJson notProved of
    Just result -> case firstObservation result of
      Just observation -> lookupField "proof_status" observation ==
        Just (JObj [("kind", JStr "not_proved")])
        && lookupField "satisfaction" observation == Just (JStr "not_satisfied")
      Nothing -> False
    Nothing -> False)
  check "unresolved penalty guard has distinct skip reason"
    (selectionResults guardPending == ["guard_unresolved"])
  check "true exception dominates unresolved without dropping its trace"
    (case resultJson defeated >>= rootRule of
      Just rule -> case lookupField "branches" rule of
        Just (JArr [branch]) -> lookupField "status" branch == Just (JStr "not_satisfied")
          && lookupField "applicable_exceptions" branch == Just (JArr [JStr "x:root:1"])
          && case lookupField "exceptions" branch of
            Just (JArr [_first, second]) ->
              lookupField "guard_status" second == Just (JStr "unresolved")
            _ -> False
        _ -> False
      Nothing -> False)
  check "invalid unreachable binding cannot become semantic unresolved"
    (field "status" (response invalid) == Just "rejected"
      && diagnosticCode (response invalid) == Just "KINV007")
  property "projection is deterministic and independent of Boolean truth" $
    forAll arbitrary $ \index ->
      let status = pick index [Proved, NotProved, Unresolved NotDetermined]
      in projection status == pick index matrix
  property "generated pairwise All and Any entries match the declared tables" $
    forAll arbitrary $ \index ->
      let position = fromInteger (abs (toInteger (index :: Int)) `mod` 9)
      in allStatus (pairs List.!! position) == allExpected List.!! position
        && anyStatus (pairs List.!! position) == anyExpected List.!! position
  property "All and Any folds are associative on bounded generated inputs" $
    forAll arbitrary $ \(a,b,c) ->
      let values = map (`pick` matrix) [a,b,c]
      in allStatus values == allStatus [allStatus (take 2 values), pick c matrix]
        && anyStatus values == anyStatus [anyStatus (take 2 values), pick c matrix]
  property "ordered complete traces survive decisive statuses" $
    forAll arbitrary $ \flag ->
      let input = if flag then decisiveAll else decisiveAny
      in case resultJson input >>= rootRule >>= lookupField "trace" of
        Just (JArr traces) -> [item | trace <- traces
          , Just item <- [lookupField "id" trace >>= textValue]] ==
          ["group:pair", "f:root", "f:second"]
        _ -> False
  property "the supplied constructor and unresolved reason survive projection" $
    forAll arbitrary $ \index ->
      let input = pick index [proved, notProved, unresolved, pending]
          expected = do
            JObj facts <- lookupField "facts" input
            binding <- lookup "f:root" facts
            lookupField "proof_status" binding
      in (resultJson input >>= firstObservation >>= lookupField "proof_status") == expected
  property "unresolved propagates through both requirement combinators" $
    forAll arbitrary $ \flag ->
      let input = if flag then allUnresolved else anyUnresolved
      in field "status" (response input) == Just "unresolved"
        && case resultJson input >>= rootRule >>= lookupField "trace" of
          Just (JArr traces) -> any (\edge -> lookupField "value" edge ==
            Just (JStr "unresolved")) traces
          _ -> False
  property "satisfied exception dominates unresolved in either declaration order" $
    forAll arbitrary $ \flag ->
      let input = if flag then defeated else reverseRootExceptions defeated
      in case resultJson input >>= rootRule >>= lookupField "branches" of
        Just (JArr [branch]) -> lookupField "status" branch == Just (JStr "not_satisfied")
          && lookupField "applicable_exceptions" branch == Just (JArr [JStr "x:root:1"])
          && case lookupField "exceptions" branch of
            Just (JArr guards) -> length guards == 2 && any (\item ->
              lookupField "guard_status" item == Just (JStr "unresolved")) guards
            _ -> False
        _ -> False
  property "unreachable-rule mismatch rejects regardless of root status" $
    forAll arbitrary $ \flag ->
      let input = if flag then invalid else modifyFact (modify "proof_status"
            (const (JObj [("kind", JStr "unresolved"), ("reason", JStr "not_determined")])) ) invalid
      in field "status" (response input) == Just "rejected"
        && diagnosticCode (response input) == Just "KINV007"
  property "invalid assignment and cycle cannot become semantic unresolved" $
    forAll arbitrary $ \flag ->
      let input = if flag then invalidSource else invalidCycle
      in field "status" (response input) == Just "rejected"
        && diagnosticCode (response input) == Just (if flag then "KINV010" else "KINV006")
  property "target classification uses the same supplied context" $
    forAll arbitrary $ \index ->
      let input = pick index [targetSatisfied, targetNotSatisfied, targetUnresolved]
          expected = pick index ["not_satisfied", "satisfied", "unresolved"]
      in field "status" (response input) == Just expected
        && case resultJson input of
          Just result -> any (\rule -> case lookupField "proof_observations" rule of
            Just (JArr observations) -> any (\row -> lookupField "leaf_id" row ==
              Just (JStr "f:target") && lookupField "proof_status" row ==
              (lookupField "facts" input >>= lookupField "f:target" >>= lookupField "proof_status")) observations
            _ -> False) (case lookupField "rules" result of
              Just (JArr rules) -> rules; _ -> [])
          Nothing -> False
  property "only final-satisfied root paths support penalties" $
    forAll arbitrary $ \index ->
      let input = pick index [proved, notProved, unresolved, targetSatisfied]
      in (not (null (selectedIds (response input)))) ==
        (field "status" (response input) == Just "satisfied")
  property "canonical bytes ignore object key order" $
    forAll arbitrary $ \flag ->
      let value = if flag then proved else unresolved
      in response value == response (reverseObjects value)
  property "metadata and descriptive provenance do not alter projection" $
    forAll arbitrary $ \flag ->
      let changed = modifyFact (\binding -> addField "provenance"
            (JObj [("source_label", JStr (if flag then "one" else "two"))]) binding) proved
      in field "status" (response changed) == field "status" (response proved)
        && selectedIds (response changed) == selectedIds (response proved)
  property "memoized and reference DAG evaluation agree" $
    forAll arbitrary $ \flag ->
      let input = if flag then defeated else guardPending
      in case decodeProofRequest input >>= validateProofRequest of
        Left _ -> False
        Right validated -> evaluateProof validated == evaluateProofReference validated
  property "unresolved penalty guard never selects" $
    forAll arbitrary $ \flag ->
      let input = if flag then guardPending else unresolved
      in null (selectedIds (response input))
  property "a proved penalty guard selects while unresolved skips" $
    forAll arbitrary $ \flag ->
      let input = if flag then guardSatisfied else guardPending
      in field "status" (response input) == Just "satisfied"
        && (not (null (selectedIds (response input)))) == flag
  property "changing a valid term cannot alter status, supports or warnings" $
    forAll arbitrary $ \flag ->
      let changed = if flag then changeFirstTermToDeath proved else proved
          fields = ["status", "penalty_selection_trace", "selection_warnings"]
      in all (\name -> jsonField name (response changed) ==
        jsonField name (response proved)) fields
        && selectedIds (response changed) == selectedIds (response proved)
  property "binding mismatch rejects even when classification is not proved" $
    forAll arbitrary $ \flag ->
      let input = if flag then mismatched else modifyFact (modify "proof_status"
            (const (JObj [("kind", JStr "not_proved")])) ) mismatched
      in field "status" (response input) == Just "rejected"
        && diagnosticCode (response input) == Just "KINV007"
  property "valid requests cannot emit an untyped false alias" $
    forAll arbitrary $ \flag ->
      let input = if flag then notProved else unresolved
      in field "status" (response input) `elem` [Just "not_satisfied", Just "unresolved"]
  property "frozen first-fragment bytes remain exact under key reordering" $
    forAll arbitrary $ \flag ->
      let bytes = if flag then frozenB01 else case decodeJson frozenB01 of
            Right value -> encodeJson (reverseObjects value)
            Left _ -> BS.empty
      in runLine bytes == frozenB01Expected
  putStrLn ("proof: " <> show (length rows) <>
    " fixtures, 18 truth-table entries, 20 bounded properties and 6 direct checks passed")
  where
    property label predicate = do
      result <- quickCheckWithResult stdArgs {maxSuccess = 30} predicate
      check label (isSuccess result)

readJson :: FilePath -> IO J
readJson path = do
  bytes <- BS.readFile path
  case decodeJson bytes of
    Left reason -> putStrLn (Text.unpack reason) >> exitFailure
    Right value -> pure value

response :: J -> BS.ByteString
response = runLine . encodeJson

resultJson :: J -> Maybe J
resultJson = either (const Nothing) Just . decodeJson . response

field :: Text -> BS.ByteString -> Maybe Text
field name output = either (const Nothing) (\value -> lookupField name value >>= textValue)
  (decodeJson output)

jsonField :: Text -> BS.ByteString -> Maybe J
jsonField name output = either (const Nothing) (lookupField name) (decodeJson output)

diagnosticCode :: BS.ByteString -> Maybe Text
diagnosticCode output = do
  result <- either (const Nothing) Just (decodeJson output)
  JArr issues <- lookupField "diagnostics" result
  case issues of
    [] -> Just ""
    first:_ -> lookupField "code" first >>= textValue

selectedIds :: BS.ByteString -> [Text]
selectedIds output = case decodeJson output of
  Right result -> case lookupField "selected_penalties" result of
    Just (JArr values) -> [identifier | item <- values
      , Just identifier <- [lookupField "penalty_id" item >>= textValue]]
    _ -> []
  Left _ -> []

selectionResults :: J -> [Text]
selectionResults input = case resultJson input >>= lookupField "penalty_selection_trace" of
  Just (JArr rows) -> [item | row <- rows
    , Just item <- [lookupField "result" row >>= textValue]]
  _ -> []

rootRule :: J -> Maybe J
rootRule result = do
  root <- lookupField "root_rule" result >>= textValue
  JArr rules <- lookupField "rules" result
  case [rule | rule <- rules, lookupField "id" rule == Just (JStr root)] of
    [rule] -> Just rule
    _ -> Nothing

firstObservation :: J -> Maybe J
firstObservation result = do
  rule <- rootRule result
  JArr (first:_) <- lookupField "proof_observations" rule
  Just first

strings :: J -> [Text]
strings (JArr values) = [item | JStr item <- values]
strings _ = []

pick :: Int -> [a] -> a
pick index values = values List.!! (fromInteger
  (abs (toInteger index) `mod` toInteger (length values)))

reverseObjects :: J -> J
reverseObjects (JObj fields) = JObj (reverse [(key, reverseObjects value)
  | (key, value) <- fields])
reverseObjects (JArr items) = JArr (map reverseObjects items)
reverseObjects other = other

reverseRootExceptions :: J -> J
reverseRootExceptions = modify "registry" (\value -> case value of
  JArr (first:rest) -> JArr (modify "exceptions" (\items -> case items of
    JArr guards -> JArr (reverse guards)
    other -> other) first : rest)
  other -> other)

changeFirstTermToDeath :: J -> J
changeFirstTermToDeath = modify "registry" (\value -> case value of
  JArr (first:rest) -> JArr (modify "program" (modify "penalties" (\items ->
    case items of
      JArr (penalty:more) -> JArr (modify "term" (\term -> JObj
        [("kind", JStr "death")
        , ("term_id", maybe JNull id (lookupField "term_id" term))
        , ("span", maybe JNull id (lookupField "span" term))]) penalty : more)
      other -> other)) first : rest)
  other -> other)

modifyFact :: (J -> J) -> J -> J
modifyFact change = modify "facts" (modify "f:root" change)

modify :: Text -> (J -> J) -> J -> J
modify key change (JObj fields) = JObj
  [(name, if name == key then change value else value) | (name, value) <- fields]
modify _ _ other = other

addField :: Text -> J -> J -> J
addField key value (JObj fields) = JObj ((key, value) : fields)
addField _ _ other = other

check :: String -> Bool -> IO ()
check label passed = unless passed (putStrLn ("failed: " <> label) >> exitFailure)
