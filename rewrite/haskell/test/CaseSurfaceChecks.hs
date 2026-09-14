{-# LANGUAGE OverloadedStrings #-}
module CaseSurfaceChecks (runCaseSurfaceChecks) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, textValue)
import Yuho.Surface.AST
import Yuho.Surface.Case
import Yuho.Surface.Parser (parseAnalysisCase, parseModel)
import Yuho.Surface.Token (Diagnostic(..), Token(..))

runCaseSurfaceChecks :: FilePath -> IO ()
runCaseSurfaceChecks root = do
  let base = root </> "research/singapore/abetment-routes-pilot"
      path = base </> "case-warehouse.yh"
      modelPath = base </> "section107-routes-theft.yh"
  source <- BS.readFile path
  modelSource <- BS.readFile modelPath
  model <- either (const (failed "model parse")) pure (parseModel modelPath modelSource)
  parsed <- either (const (failed "case parse")) pure (parseAnalysisCase path source)
  check "typed allegation declaration" $ case parsed of
    AnalysisCase item location bindings facts allegations ->
      tokenText item == "case:warehouse-incident"
        && tokenText location == "section107-routes-theft.yh"
        && length bindings == 4 && null facts
        && [kind | CaseAllegation _ kind _ _ _ _ <- allegations] ==
          [CaseOffence,CaseParticipation,CaseAttempt]
  check "case resolves its sibling model" (caseModelFile path parsed == Right modelPath)
  check "one shared exception has three typed attachments" $ case modelBody model of
    AbetmentLegal _ _ _ _ _ _ _ (ActorExceptionDefinition _ _) attachments _ _ ->
      length attachments == 3
    _ -> False
  checked <- either (const (failed "case check")) pure
    (checkAnalysisCase path parsed modelPath model)
  request <- either (const (failed "case compile")) pure (compileAnalysisCase checked)
  result <- either (const (failed "case run")) pure (runAnalysisCase checked)
  explanation <- either (const (failed "case explain")) pure
    (explainAnalysisCase modelPath checked)
  check "canonical deterministic case compilation" $
    compileAnalysisCase checked == Right request
      && case decodeJson request of
        Right value -> encodeJson value == request
          && lookupField "scope" value == Just (JStr "synthetic_research_only")
          && lookupField "status" value == Nothing
        Left _ -> False
  check "canonical deterministic case result without aggregate status" $
    runAnalysisCase checked == Right result
      && case decodeJson result of
        Right value -> encodeJson value <> "\n" == result
          && lookupField "scope" value == Just (JStr "synthetic_research_only")
          && lookupField "status" value == Nothing
          && issueStatuses value == Just
            [("a:principal-theft","satisfied"),
             ("a:abet-theft","satisfied"),
             ("a:attempt-theft","not_satisfied")]
        Left _ -> False
  check "allegation source order cannot change canonical issue order" $
    case parsed of
      AnalysisCase item location bindings facts allegations ->
        case checkAnalysisCase path (AnalysisCase item location bindings facts
          (reverse allegations)) modelPath model of
          Right reordered -> compileAnalysisCase reordered == Right request
            && runAnalysisCase reordered == Right result
          Left _ -> False
  check "all requests are separately lowered" $ case checked of
    CheckedCase _ _ _ _ [CheckedIssue _ _ first,CheckedIssue _ _ second,
      CheckedIssue _ _ third] ->
        not ("f:instigation-link" `BS.isInfixOf` first)
          && not ("f:movable-property" `BS.isInfixOf` second)
          && not ("f:movable-property" `BS.isInfixOf` third)
          && "f:substantial-step" `BS.isInfixOf` third
    _ -> False
  check "case explanation names each issue without a case disposition" $
    explainAnalysisCase modelPath checked == Right explanation
      && all (`Text.isInfixOf` explanation)
      ["Allegation a:principal-theft", "Allegation a:abet-theft",
       "Allegation a:attempt-theft", "no aggregate case status",
       "No guilt, conviction, acquittal"]
  let load bytes = do
        declaration <- parseAnalysisCase path bytes
        checkAnalysisCase path declaration modelPath model
      statuses bytes = case load bytes of
        Left _ -> Nothing
        Right valid -> case runAnalysisCase valid of
          Left _ -> Nothing
          Right resultBytes -> either (const Nothing) issueStatuses
            (decodeJson resultBytes)
      principalNature = replaceMany source
        ["xi:principal-section84 f:unsoundness-time",
         "xi:principal-section84 f:nature-causation",
         "xi:principal-section84 f:nature-incapacity"]
      abettorNature = replaceMany source
        ["xi:abettor-section84 f:unsoundness-time",
         "xi:abettor-section84 f:nature-causation",
         "xi:abettor-section84 f:nature-incapacity"]
      attemptAct = replace "= preparation_only;" "= act_towards_commission;" source
      attempterControl = replaceMany attemptAct
        ["xi:attempter-section84 f:unsoundness-time",
         "xi:attempter-section84 f:control-causation",
         "xi:attempter-section84 f:control-incapacity"]
  check "principal exception changes only the principal result" $
    statuses principalNature == Just
      [("a:principal-theft","not_satisfied"),
       ("a:abet-theft","satisfied"),
       ("a:attempt-theft","not_satisfied")]
  check "abettor exception changes only the participation result" $
    statuses abettorNature == Just
      [("a:principal-theft","satisfied"),
       ("a:abet-theft","not_satisfied"),
       ("a:attempt-theft","not_satisfied")]
  check "attempt stage and actor exception remain separate" $
    statuses attemptAct == Just
      [("a:principal-theft","satisfied"),
       ("a:abet-theft","satisfied"),
       ("a:attempt-theft","satisfied")]
      && statuses attempterControl == Just
      [("a:principal-theft","satisfied"),
       ("a:abet-theft","satisfied"),
       ("a:attempt-theft","not_satisfied")]
  check "another allegation does not change request bytes" $
    case (load source,load principalNature,load abettorNature) of
      (Right original,Right principalChanged,Right abettorChanged) ->
        issueRequests original 1 == issueRequests principalChanged 1
          && issueRequests original 2 == issueRequests principalChanged 2
          && issueRequests original 0 == issueRequests abettorChanged 0
          && issueRequests original 2 == issueRequests abettorChanged 2
      _ -> False
  let refusal label bytes wanted = check label $ case load bytes of
        Left issue -> diagnosticCode issue == wanted
          && diagnosticPath issue == path
          && tokenLine (diagnosticToken issue) > 0
          && tokenColumn (diagnosticToken issue) > 0
        Right _ -> False
  refusal "wrong typed target" (replace "analyse offence o:theft"
    "analyse offence o:unknown" source) "SFE107"
  refusal "wrong subject role" (replace "o:theft for role:principal"
    "o:theft for role:alleged-abettor" source) "SFE107"
  refusal "duplicate allegation ID" (replace "allegation a:abet-theft"
    "allegation a:principal-theft" source) "SFE106"
  refusal "duplicate allegation kind" (replace
    "allegation a:attempt-theft analyse attempt attempt:theft"
    "allegation a:attempt-theft analyse offence o:theft" source) "SFE106"
  refusal "unsafe model path" (replace "\"section107-routes-theft.yh\""
    "\"../section107-routes-theft.yh\"" source) "SFE106"
  refusal "wrong actor-scoped instance" (replace
    "xi:abettor-section84 f:unsoundness-time"
    "xi:principal-section84 f:unsoundness-time" source) "SFE093"
  check "missing allegation is rejected" $ case parsed of
    AnalysisCase item location bindings facts allegations ->
      case checkAnalysisCase path (AnalysisCase item location bindings facts
        (take 2 allegations)) modelPath model of
        Left issue -> diagnosticCode issue == "SFE106"
        Right _ -> False
  putStrLn "analysis case: three independent issues, actor isolation and seven refusals passed"

issueStatuses :: J -> Maybe [(Text,Text)]
issueStatuses value = do
  JArr rows <- lookupField "issues" value
  mapM (\row -> do
    item <- lookupField "id" row >>= textValue
    status <- lookupField "status" row >>= textValue
    pure (item,status)) rows

issueRequests :: CheckedCase -> Int -> Maybe BS.ByteString
issueRequests (CheckedCase _ _ _ _ rows) index = case drop index rows of
  CheckedIssue _ _ request:_ -> Just request
  [] -> Nothing

replace :: Text -> Text -> BS.ByteString -> BS.ByteString
replace old new = Encoding.encodeUtf8 . Text.replace old new . Encoding.decodeUtf8

replaceMany :: BS.ByteString -> [Text] -> BS.ByteString
replaceMany bytes prefixes = Encoding.encodeUtf8 (Text.unlines
  [if any (`Text.isInfixOf` line) prefixes
    then Text.replace "= not_proved;" "= proved;" line else line
  | line <- Text.lines (Encoding.decodeUtf8 bytes)])

check :: String -> Bool -> IO ()
check label success = unless success (failed label)

failed :: String -> IO a
failed label = putStrLn ("analysis case failed: " <> label) >> exitFailure
