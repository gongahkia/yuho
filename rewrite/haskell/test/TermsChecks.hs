{-# LANGUAGE OverloadedStrings #-}
module TermsChecks (runTermsChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import qualified Data.List as List
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Data.Text (Text)
import qualified Data.Text as Text
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Test.QuickCheck (arbitrary, forAll, isSuccess, maxSuccess, quickCheckWithResult, stdArgs)
import Yuho.Kernel.Run (runLine)
import Yuho.PenaltyTerms.Decode (decodeTermsRequest)
import Yuho.PenaltyTerms.Encode (termJson)
import Yuho.PenaltyTerms.Types (Term, ValidatedTerms(..))
import Yuho.PenaltyTerms.Validate (validateTerms)
import Yuho.Core.Types (Diagnostic)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, objectFields, textValue)

runTermsChecks :: FilePath -> IO ()
runTermsChecks directory = do
  cases <- readJson (directory </> "CASES.json")
  rows <- maybe (putStrLn "term cases are not an object" >> exitFailure) pure
    (objectFields cases)
  forM_ rows $ \(name, expected) -> do
    path <- maybe (putStrLn "term case lacks file" >> exitFailure) pure
      (lookupField "request_file" expected >>= textValue)
    bytes <- BS.readFile (directory </> Text.unpack path)
    let result = runLine (compact bytes)
        status = field "status" result
        code = diagnosticCode result
        expectedCode = if name == "PT66" then Just "KDEC001"
          else lookupField "code" expected >>= textValue
        selected = selectedIds result
    check ("term fixture " <> Text.unpack name)
      (status == (lookupField "status" expected >>= textValue)
        && code == expectedCode
        && selected == maybe [] strings (lookupField "selected" expected))
  basic <- readJson (directory </> "requests/PT01.json")
  fine <- readJson (directory </> "requests/PT03.json")
  choice <- readJson (directory </> "requests/PT11.json")
  alternative <- readJson (directory </> "requests/PT12.json")
  nested <- readJson (directory </> "requests/PT14.json")
  inherited <- readJson (directory </> "requests/PT17.json")
  defeated <- readJson (directory </> "requests/PT18.json")
  overlap <- readJson (directory </> "requests/PT19.json")
  target <- readJson (directory </> "requests/PT20.json")
  invalid <- readJson (directory </> "requests/PT36.json")
  unselected <- readJson (directory </> "requests/PT16.json")
  old <- readJson (directory </> "../penalty-fixtures/requests/GP01.json")
  property "term decode and canonical encode are stable" (forAll arbitrary $ \flag ->
    let input = if flag then fine else basic
        output = response input
    in case validatedMap input of
      Left _ -> False
      Right terms -> hasTerm output &&
        (encodeJson <$> selectedTerm output) ==
          (encodeJson . termJson <$> Map.lookup "pen:root:1" terms))
  property "term validation is deterministic" (forAll arbitrary $ \flag ->
    let input = if flag then invalid else basic
    in validatedMap input == validatedMap (reverseObjects input))
  property "canonical bytes ignore JSON key order" (forAll arbitrary $ \flag ->
    let input = if flag then choice else nested
    in response input == response (reverseObjects input))
  property "authored child order is preserved" (forAll arbitrary $ \flag ->
    let input = if flag then choice else swapChildren choice
    in termChildIds (response input) ==
       (if flag then ["term:child:0", "term:child:1"]
        else ["term:child:1", "term:child:0"]))
  property "valid term changes leave selection IDs unchanged" (forAll arbitrary $ \flag ->
    selectedIds (response (swapKind flag basic)) == selectedIds (response basic))
  property "valid term changes leave supports unchanged" (forAll arbitrary $ \flag ->
    selectedField "supporting_branches" (response (swapKind flag inherited)) ==
      selectedField "supporting_branches" (response inherited))
  property "valid term changes leave overlap warnings unchanged" (forAll arbitrary $ \flag ->
    jsonField "selection_warnings" (response (swapKind flag overlap)) ==
      jsonField "selection_warnings" (response overlap))
  property "unselected terms are validated" (forAll arbitrary $ \flag ->
    let input = if flag then invalidTerm unselected else unselected
    in field "status" (response input) == Just (if flag then "rejected" else "false"))
  property "invalid bounds never produce selected terms" (forAll arbitrary $ \flag ->
    let input = invalidTerm (if flag then basic else inherited)
    in field "status" (response input) == Just "rejected" &&
       null (selectedIds (response input)))
  property "unit remains nominal without conversion" (forAll arbitrary $ \flag ->
    let input = setUnit (if flag then "months" else "years") basic
    in selectedIds (response input) == selectedIds (response basic)
       && selectedTermField "unit" (response input) == Just (JStr
          (if flag then "months" else "years")))
  property "non-SGD currency cannot be converted" (forAll arbitrary $ \flag ->
    let input = setCurrency (if flag then "USD" else "EUR") fine
    in diagnosticCode (response input) == Just "KCAP001")
  property "source tree is not flattened or distributed" (forAll arbitrary $ \flag ->
    let input = if flag then nested else alternative
    in selectedTermField "kind" (response input) == Just
      (JStr (if flag then "all_of" else "exactly_one_of"))
      && termChildIds (response input) /= [])
  property "dependency target terms do not become root selections" (forAll arbitrary $ \flag ->
    let input = setFact flag target
    in null (selectedIds (response input)))
  property "exception defeat suppresses selected terms" (forAll arbitrary $ \flag ->
    let input = setFact flag defeated
    in null (selectedIds (response input)))
  property "selected record has exactly its declaration term" (forAll arbitrary $ \flag ->
    let input = swapKind flag basic
    in selectedTermField "term_id" (response input) == Just (JStr "term:fixture"))
  property "fourth-fragment selection survives fifth-fragment terms" (forAll arbitrary $ \flag ->
    let newInput = setFact flag basic
        oldInput = setFact flag old
        newResult = response newInput
        oldResult = response oldInput
    in field "status" newResult == field "status" oldResult
      && selectedIds newResult == selectedIds oldResult
      && jsonField "penalty_selection_trace" newResult ==
        jsonField "penalty_selection_trace" oldResult)
  property "selected IDs remain globally unique" (forAll arbitrary $ \flag ->
    let ids = selectedIds (response (setFact flag overlap))
    in ids == List.nub ids)
  property "duplicate term IDs reject regardless of facts" (forAll arbitrary $ \flag ->
    let input = setFact flag invalid
    in field "status" (response input) == Just "rejected" &&
       diagnosticCode (response input) == Just "KINV009")
  check "fine amount uses two canonical fractional digits"
    (selectedEndpoint fine == Just "1.20")
  check "term rejection has no partial judgment" (null (selectedIds (response invalid)))
  check "legacy fine_unlimited is a capability rejection"
    (diagnosticCode (response (addTermField "fine_unlimited" (JBool True) basic)) ==
      Just "KCAP001")
  check "declaration sentencing metadata is a capability rejection"
    (diagnosticCode (response (addPenaltyField "sentencing_mode"
      (JStr "mandatory") basic)) == Just "KCAP001")
  putStrLn "terms: 68 fixtures, 18 bounded properties and 4 direct checks passed"
  where
    property label predicate = do
      result <- quickCheckWithResult stdArgs {maxSuccess = 25} predicate
      check label (isSuccess result)

compact :: BS.ByteString -> BS.ByteString
compact bytes = case decodeJson bytes of
  Right parsed -> encodeJson parsed
  Left _ -> BS.filter (/= 10) bytes

readJson :: FilePath -> IO J
readJson path = do
  bytes <- BS.readFile path
  case decodeJson bytes of
    Left reason -> putStrLn (Text.unpack reason) >> exitFailure
    Right parsed -> pure parsed

response :: J -> BS.ByteString
response = runLine . encodeJson

field :: Text -> BS.ByteString -> Maybe Text
field name output = jsonField name output >>= textValue

jsonField :: Text -> BS.ByteString -> Maybe J
jsonField name output = either (const Nothing) (lookupField name) (decodeJson output)

diagnosticCode :: BS.ByteString -> Maybe Text
diagnosticCode output = do
  JArr issues <- jsonField "diagnostics" output
  case issues of
    [] -> Just ""
    first : _ -> lookupField "code" first >>= textValue

selectedIds :: BS.ByteString -> [Text]
selectedIds output = maybe [] (\values -> [identifier | item <- values
  , Just identifier <- [lookupField "penalty_id" item >>= textValue]])
  (arrayValue =<< jsonField "selected_penalties" output)

hasTerm :: BS.ByteString -> Bool
hasTerm output = case jsonField "selected_penalties" output of
  Just (JArr (first:_)) -> lookupField "term" first /= Nothing
  _ -> False

selectedTerm :: BS.ByteString -> Maybe J
selectedTerm output = do
  JArr (first:_) <- jsonField "selected_penalties" output
  lookupField "term" first

validatedMap :: J -> Either Diagnostic (Map Text Term)
validatedMap input = do
  decoded <- decodeTermsRequest input
  ValidatedTerms _ terms <- validateTerms decoded
  pure terms

selectedField :: Text -> BS.ByteString -> [J]
selectedField name output = maybe [] (\values -> [value | item <- values
  , Just value <- [lookupField name item]])
  (arrayValue =<< jsonField "selected_penalties" output)

selectedTermField :: Text -> BS.ByteString -> Maybe J
selectedTermField name output = do
  JArr (first:_) <- jsonField "selected_penalties" output
  term <- lookupField "term" first
  lookupField name term

selectedEndpoint :: J -> Maybe Text
selectedEndpoint input = do
  term <- selectedTermField "minimum" (response input)
  lookupField "value" term >>= textValue

termChildIds :: BS.ByteString -> [Text]
termChildIds output = case selectedTermField "terms" output of
  Just (JArr children) -> [identifier | child <- children
    , Just identifier <- [lookupField "term_id" child >>= textValue]]
  _ -> []

strings :: J -> [Text]
strings (JArr values) = [item | JStr item <- values]
strings _ = []

arrayValue :: J -> Maybe [J]
arrayValue (JArr values) = Just values
arrayValue _ = Nothing

modify :: Text -> (J -> J) -> J -> J
modify key transform (JObj fields) = JObj
  [(name, if name == key then transform value else value) | (name, value) <- fields]
modify _ _ other = other

mapPenalties :: (J -> J) -> J -> J
mapPenalties transform = modify "registry" (\value -> case value of
  JArr rules -> JArr (map (modify "program" (walk transform)) rules)
  other -> other)
  where
    walk change provision = modify "children" (\value -> case value of
      JArr children -> JArr (map (walk change) children)
      other -> other) (modify "penalties" (\value -> case value of
        JArr penalties -> JArr (map change penalties)
        other -> other) provision)

swapKind :: Bool -> J -> J
swapKind flag = mapPenalties (modify "term" (\term ->
  if not flag then term else JObj
    [("term_id", maybe JNull id (lookupField "term_id" term))
    , ("span", maybe JNull id (lookupField "span" term))
    , ("kind", JStr "death")] ))

invalidTerm :: J -> J
invalidTerm = mapPenalties (modify "term" (modify "maximum" (const
  (JObj [("kind", JStr "specified"), ("value", JNum 0)]))))

setUnit :: Text -> J -> J
setUnit unit = mapPenalties (modify "term" (modify "unit" (const (JStr unit))))

setCurrency :: Text -> J -> J
setCurrency currency = mapPenalties (modify "term" (modify "currency"
  (const (JStr currency))))

addTermField :: Text -> J -> J -> J
addTermField key value = mapPenalties (modify "term" (addField key value))

addPenaltyField :: Text -> J -> J -> J
addPenaltyField key value = mapPenalties (addField key value)

addField :: Text -> J -> J -> J
addField key value (JObj fields) = JObj ((key, value) : fields)
addField _ _ other = other

setFact :: Bool -> J -> J
setFact value = modify "facts" (modify "f:root" (modify "value"
  (const (JBool value))))

swapChildren :: J -> J
swapChildren = mapPenalties (modify "term" (modify "terms" (\value -> case value of
  JArr children -> JArr (reverse children)
  other -> other)))

reverseObjects :: J -> J
reverseObjects (JObj fields) = JObj (reverse [(key, reverseObjects value)
  | (key, value) <- fields])
reverseObjects (JArr items) = JArr (map reverseObjects items)
reverseObjects other = other

check :: String -> Bool -> IO ()
check label passed = unless passed (putStrLn ("failed: " <> label) >> exitFailure)
