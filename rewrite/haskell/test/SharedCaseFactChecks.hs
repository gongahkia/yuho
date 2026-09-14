{-# LANGUAGE OverloadedStrings #-}
module SharedCaseFactChecks (runSharedCaseFactChecks) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, textValue)
import Yuho.Surface.AST
import Yuho.Surface.Case
import Yuho.Surface.CaseFacts (expandCaseFacts)
import Yuho.Surface.Parser (parseAnalysisCase, parseModel)
import Yuho.Surface.Token (Diagnostic(..), Token(..))

runSharedCaseFactChecks :: FilePath -> IO ()
runSharedCaseFactChecks root = do
  let base = root </> "research/singapore/abetment-routes-pilot"
      modelPath = base </> "section107-routes-theft.yh"
      sharedPath = base </> "case-warehouse-shared.yh"
      names =
        [ ("case-warehouse-shared.yh",["satisfied","satisfied","not_satisfied"])
        , ("case-warehouse-shared-proved.yh",["satisfied","satisfied","not_satisfied"])
        , ("case-warehouse-shared-unresolved.yh",["satisfied","satisfied","not_satisfied"])
        , ("case-warehouse-shared-mixed.yh",["not_satisfied","satisfied","not_satisfied"])
        , ("case-warehouse-shared-isolation.yh",["not_satisfied","satisfied","not_satisfied"])
        , ("case-warehouse-shared-mixed-three.yh",["not_satisfied","not_satisfied","satisfied"])
        , ("case-warehouse-shared-order.yh",["satisfied","satisfied","not_satisfied"])
        , ("case-warehouse-shared-all-principal.yh",["satisfied","satisfied","not_satisfied"])
        ]
  modelSource <- BS.readFile modelPath
  model <- either (const (failed "model parse")) pure
    (parseModel modelPath modelSource)
  rows <- mapM (\(name,wanted) -> do
    let path = base </> name
    source <- BS.readFile path
    declaration <- either (const (failed (name <> " parse"))) pure
      (parseAnalysisCase path source)
    checked <- either (const (failed (name <> " check"))) pure
      (checkAnalysisCase path declaration modelPath model)
    compiled <- either (const (failed (name <> " compile"))) pure
      (compileAnalysisCase checked)
    result <- either (const (failed (name <> " run"))) pure
      (runAnalysisCase checked)
    explanation <- either (const (failed (name <> " explain"))) pure
      (explainAnalysisCase modelPath checked)
    check (name <> " statuses") (statuses result == Just wanted)
    check (name <> " canonical input") $ case decodeJson compiled of
      Right value -> encodeJson value == compiled
        && lookupField "supplied_facts" value /= Nothing
      Left _ -> False
    check (name <> " canonical result") $ case decodeJson result of
      Right value -> encodeJson value <> "\n" == result
        && lookupField "supplied_facts" value /= Nothing
      Left _ -> False
    check (name <> " evidence boundary")
      ("Yuho did not assess evidence or determine these facts."
        `Text.isInfixOf` explanation)
    direct <- either (const (failed (name <> " direct expansion"))) pure
      (equivalentDirect path model declaration)
    directChecked <- either (const (failed (name <> " direct check"))) pure
      (checkAnalysisCase path direct modelPath model)
    check (name <> " direct request parity")
      (requests checked == requests directChecked)
    check (name <> " direct response parity")
      (map runLine (requests checked) == map runLine (requests directChecked))
    check (name <> " direct status parity")
      (case runAnalysisCase directChecked of
        Right directResult -> statuses result == statuses directResult
        Left _ -> False)
    check (name <> " deterministic compilation")
      (compileAnalysisCase checked == Right compiled
        && runAnalysisCase checked == Right result)
    pure (name,compiled,result)) names
  let findRow name = [(input,result) | (item,input,result) <- rows,item == name]
  check "fact declaration order leaves canonical bytes unchanged" $
    findRow "case-warehouse-shared.yh" ==
      findRow "case-warehouse-shared-order.yh"
  sharedSource <- BS.readFile sharedPath
  sharedDeclaration <- either (const (failed "typed case fact parse")) pure
    (parseAnalysisCase sharedPath sharedSource)
  check "four closed typed case fact kinds" $ case sharedDeclaration of
    AnalysisCase _ _ _ facts _ ->
      [kind | CaseFact _ kind _ _ <- facts] ==
        [FactConduct,FactMentalState,FactCircumstance,FactRelationship]
        && any (\fact -> case fact of
          CaseFact _ _ (CaseExceptionSubject _ _ _) _ -> True
          _ -> False) facts
  targetedSource <- BS.readFile (base </> "case-warehouse-shared-mixed-three.yh")
  let load bytes = do
        declaration <- parseAnalysisCase sharedPath bytes
        checkAnalysisCase sharedPath declaration modelPath model
      refusal label before after wanted = check label $ case
        load (replace before after sharedSource) of
          Left issue -> diagnosticCode issue == wanted
            && diagnosticPath issue == sharedPath
            && tokenLine (diagnosticToken issue) > 0
            && tokenColumn (diagnosticToken issue) > 0
          Right _ -> False
  check "target-directed attempt fact requires its authored offence" $
    case load (replace "target o:theft status proved reason \"synthetic target-directed intention\""
      "target o:unknown status proved reason \"synthetic target-directed intention\""
      targetedSource) of
      Left issue -> diagnosticCode issue == "SFE113"
      Right _ -> False
  refusal "unknown fact" "bind-fact fact:principal-movement"
    "bind-fact fact:unknown" "SFE110"
  refusal "duplicate fact" "supplied-fact fact:principal-dishonesty"
    "supplied-fact fact:principal-movement" "SFE111"
  refusal "unknown primitive" "to input f:property-moved"
    "to input f:unknown" "SFE114"
  refusal "derived offence group" "to input f:property-moved"
    "to input g:theft-requirements" "SFE114"
  refusal "derived route group" "to relation-input rel:agreement"
    "to input g:section107-routes" "SFE114"
  refusal "s109 candidate group" "to relation-input rel:agreement"
    "to input g:section109" "SFE114"
  refusal "fact kind mismatch" "fact:principal-movement kind conduct"
    "fact:principal-movement kind mental-state" "SFE112"
  refusal "subject actor mismatch" "fact:principal-movement kind conduct subject actor:principal-1"
    "fact:principal-movement kind conduct subject actor:participant-1" "SFE113"
  refusal "relation endpoint mismatch" "from actor:participant-1 to actor:co-1 target o:theft"
    "from actor:participant-1 to actor:principal-1 target o:theft" "SFE113"
  refusal "relation target mismatch" "from actor:participant-1 to actor:co-1 target o:theft"
    "from actor:participant-1 to actor:co-1 target o:unknown" "SFE113"
  refusal "exception context mismatch" "instance xi:principal-section84 context principal-conduct status"
    "instance xi:principal-section84 context aid-conduct status" "SFE113"
  refusal "exception instance mismatch" "instance xi:principal-section84 context principal-conduct status"
    "instance xi:abettor-section84 context principal-conduct status" "SFE113"
  refusal "duplicate binding" "bind-fact fact:principal-movement to input f:property-moved;"
    "bind-fact fact:principal-movement to input f:property-moved;\n    bind-fact fact:principal-movement to input f:property-moved;" "SFE115"
  refusal "one fact cannot cross distinct conduct concepts"
    "bind-fact fact:principal-movement to input f:property-moved;"
    "bind-fact fact:principal-movement to input f:property-moved;\n    bind-fact fact:principal-movement to input f:moved-for-taking;" "SFE117"
  refusal "direct and fact conflict" "bind-fact fact:principal-movement to input f:property-moved;"
    "bind-fact fact:principal-movement to input f:property-moved;\n    f:property-moved by actor:principal-1 = proved;" "SFE115"
  refusal "unused fact" "bind-fact fact:principal-movement to input f:property-moved;"
    "f:property-moved by actor:principal-1 = proved;" "SFE116"
  refusal "missing input after expansion" "f:another-possession by actor:principal-1 = proved;"
    "" "SFE118"
  refusal "acknowledgement cannot be an input" "to input f:property-moved"
    "to input a:punishment-outside-scope" "SFE114"
  refusal "attempt stage cannot be a proof fact" "to input f:property-moved"
    "to input f:substantial-step" "SFE114"
  refusal "attempt-stage domain is not a proof input"
    "stage stage:theft-conduct by actor:attempt-actor-1 = preparation_only;"
    "bind-fact fact:principal-movement to input f:substantial-step;" "SFE114"
  refusal "unscoped section84 input" "to exception-input xi:principal-section84 f:unsoundness-time"
    "to input f:unsoundness-time" "SFE114"
  refusal "bad status domain" "fact:principal-movement kind conduct subject actor:principal-1 status proved"
    "fact:principal-movement kind conduct subject actor:principal-1 status preparation_only" "SFE010"
  check "indirect fact target is not accepted" $ case parseAnalysisCase sharedPath
    (replace "to input f:property-moved" "to fact fact:principal-dishonesty" sharedSource) of
      Left issue -> diagnosticCode issue == "SFE112"
      Right _ -> False
  putStrLn "shared case facts: eight authored shared cases, direct equivalence and refusal matrix passed"

equivalentDirect :: FilePath -> Model -> AnalysisCase -> Either Diagnostic AnalysisCase
equivalentDirect path model (AnalysisCase item location actors facts allegations) = do
  direct <- mapM (\allegation@(CaseAllegation allegationId kind target role _ _) -> do
    scenario <- expandCaseFacts path model actors facts allegation
    pure (CaseAllegation allegationId kind target role scenario [])) allegations
  pure (AnalysisCase item location actors [] direct)

requests :: CheckedCase -> [BS.ByteString]
requests (CheckedCase _ _ _ _ issues) =
  [request | CheckedIssue _ _ request <- issues]

statuses :: BS.ByteString -> Maybe [Text]
statuses bytes = either (const Nothing) (\value -> do
  JArr issues <- lookupField "issues" value
  mapM (\issue -> lookupField "status" issue >>= textValue) issues)
  (decodeJson bytes)

replace :: Text -> Text -> BS.ByteString -> BS.ByteString
replace old new = Encoding.encodeUtf8 . Text.replace old new . Encoding.decodeUtf8

check :: String -> Bool -> IO ()
check label success = unless success (failed label)

failed :: String -> IO a
failed label = putStrLn ("shared case facts failed: " <> label) >> exitFailure
