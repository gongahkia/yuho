{-# LANGUAGE OverloadedStrings #-}
module ActorExceptionSurfaceChecks (runActorExceptionSurfaceChecks) where

import Control.Monad (forM, unless)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, lookupField, textValue)
import Yuho.Surface.AST
import Yuho.Surface.Compile (checkSource, compileSource)
import Yuho.Surface.Explain (explainChecked)
import Yuho.Surface.Token (Diagnostic(..), Token(..))

runActorExceptionSurfaceChecks :: FilePath -> IO ()
runActorExceptionSurfaceChecks root = do
  let base = root </> "research/singapore/actor-exception-pilot"
      modelPath = base </> "actor-scoped-section84.yh"
      scenarioPath name = base </> "scenarios" </> name <> ".yh"
  source <- BS.readFile modelPath
  check "one typed shared exception and three attachments" $
    case checkSource modelPath source Nothing of
      Right (Checked model Nothing [] _ (Just _)) -> case modelBody model of
        ActorScopedLegal roles _ _ scopes offence (IntentionalAidRoute route _)
          attempt (ActorExceptionDefinition (ActorSubject subject) shared)
          attachments citations outputs ->
            length roles == 3 && length scopes == 13 && length citations == 8
              && length outputs == 9 && ruleKind offence == OffenceKind
              && ruleKind route == ParticipationKind
              && ruleKind (attemptRule attempt) == AttemptKind
              && ruleKind shared == ExceptionKind
              && tokenText subject == "subject:actor"
              && length (ruleElements shared) == 8
              && case attachments of
                [ActorExceptionAttachment _ (CandidateOffenceTarget _) _
                  (PrincipalConductContext _) _,
                 ActorExceptionAttachment _ (ParticipationAttachmentTarget _) _
                  (AidConductContext _) _,
                 ActorExceptionAttachment _ (AttemptAttachmentTarget _) _
                  (AttemptConductContext _) _] -> True
                _ -> False
        _ -> False
      _ -> False
  let cases =
        [("01_principal_not_established","satisfied","xi:principal-section84")
        ,("02_principal_nature","not_satisfied","xi:principal-section84")
        ,("03_principal_unresolved","unresolved","xi:principal-section84")
        ,("04_principal_ignores_abettor","satisfied","xi:principal-section84")
        ,("05_abettor_not_established","satisfied","xi:abettor-section84")
        ,("06_abettor_nature","not_satisfied","xi:abettor-section84")
        ,("07_abettor_ignores_principal","satisfied","xi:abettor-section84")
        ,("08_abettor_unresolved","unresolved","xi:abettor-section84")
        ,("09_abettor_wrong_partial","satisfied","xi:abettor-section84")
        ,("10_attempter_not_established","satisfied","xi:attempter-section84")
        ,("11_attempter_control","not_satisfied","xi:attempter-section84")
        ,("12_attempter_ignores_principal","satisfied","xi:attempter-section84")
        ,("13_attempter_unresolved","unresolved","xi:attempter-section84")
        ,("14_attempter_preparation","not_satisfied","xi:attempter-section84")
        ,("15_principal_ignores_abettor_unresolved","satisfied","xi:principal-section84")
        ,("16_abettor_wrong_both","not_satisfied","xi:abettor-section84")]
  responses <- forM cases $ \(name,wanted,instanceId) -> do
    scenario <- BS.readFile (scenarioPath name)
    let supplied = Just (scenarioPath name,scenario)
    case (checkSource modelPath source supplied,compileSource modelPath source supplied) of
      (Right checked,Right request) -> do
        check (name <> " deterministic compilation")
          (compileSource modelPath source supplied == Right request)
        let response = runLine request
        check (name <> " technical status") (responseStatus response == Just wanted)
        check (name <> " one selected guard")
          (if name == "14_attempter_preparation"
            then selectedGuard response == Nothing
              && Encoding.encodeUtf8 instanceId `BS.isInfixOf` request
            else selectedGuard response == Just instanceId)
        check (name <> " no actor metadata as proof facts")
          (not ("actor:principal-1" `BS.isInfixOf` request)
            && not ("a:post-2022-section-84-expression-applicable" `BS.isInfixOf` request))
        case explainChecked modelPath checked of
          Right explanation -> check (name <> " actor-scoped explanation")
            ("Definition: x:section84" `Text.isInfixOf` explanation
              && ("General exception instance: " <> instanceId) `Text.isInfixOf` explanation
              && "Other actor instances:" `Text.isInfixOf` explanation
              && "No guilt, conviction, acquittal" `Text.isInfixOf` explanation)
          Left _ -> check (name <> " explanation") False
        pure (name,response,request)
      _ -> check (name <> " checks and compiles") False >> pure (name,BS.empty,BS.empty)
  let result name = [(response,request) | (caseName,response,request) <- responses,
        caseName == name]
      sameBranch first second = case (result first,result second) of
        ([(left,_)],[(right,_)]) -> rootRule left == rootRule right
        _ -> False
  check "abettor result cannot defeat principal" (sameBranch
    "01_principal_not_established" "04_principal_ignores_abettor")
  check "principal result cannot defeat abettor" (sameBranch
    "05_abettor_not_established" "07_abettor_ignores_principal")
  check "principal result cannot defeat attempter" (sameBranch
    "10_attempter_not_established" "12_attempter_ignores_principal")
  check "other actor unresolved cannot propagate" (sameBranch
    "01_principal_not_established" "15_principal_ignores_abettor_unresolved")
  case result "15_principal_ignores_abettor_unresolved" of
    [(response,request)] -> check "other actor's unresolved input cannot propagate"
      ("f:abettor-section84--unsoundness-time" `BS.isInfixOf` request
        && "\"kind\":\"unresolved\"" `BS.isInfixOf` request
        && responseStatus response == Just "satisfied")
    _ -> check "observed unresolved case exists" False
  case result "04_principal_ignores_abettor" of
    [(_,request)] -> check "active instances have distinct leaf IDs"
      ("f:principal-section84--unsoundness-time" `BS.isInfixOf` request
        && "f:abettor-section84--unsoundness-time" `BS.isInfixOf` request
        && not ("f:attempter-section84--unsoundness-time" `BS.isInfixOf` request))
    _ -> check "observed instance case exists" False
  baseScenario <- BS.readFile (scenarioPath "01_principal_not_established")
  let scenarioError old new = errorCode (checkSource modelPath source
        (Just (scenarioPath "invalid",replace old new baseScenario)))
      modelError old new = errorCode (checkSource modelPath (replace old new source) Nothing)
      refuse label actual wanted = check label (actual == Just wanted)
  refuse "unqualified section 84 classification" (scenarioError
    "exception-status xi:principal-section84 f:unsoundness-time by actor:principal-1 context principal-conduct"
    "f:unsoundness-time by actor:principal-1") "SFE090"
  refuse "unknown exception instance" (scenarioError
    "xi:principal-section84 f:unsoundness-time" "xi:unknown f:unsoundness-time") "SFE089"
  refuse "wrong subject actor" (scenarioError
    "f:unsoundness-time by actor:principal-1" "f:unsoundness-time by actor:participant-1") "SFE091"
  refuse "wrong act context" (scenarioError
    "f:unsoundness-time by actor:principal-1 context principal-conduct"
    "f:unsoundness-time by actor:principal-1 context aid-conduct") "SFE092"
  refuse "inactive instance input" (scenarioError
    "  exception-status xi:principal-section84 f:unsoundness-time"
    "  exception-status xi:abettor-section84 f:unsoundness-time by actor:participant-1 context aid-conduct = not_proved;\n  exception-status xi:principal-section84 f:unsoundness-time") "SFE093"
  refuse "attachment subject belongs to target" (modelError
    "to offence o:theft for role:principal" "to offence o:theft for role:alleged-abettor") "SFE088"
  refuse "offence element cannot be attachment target" (modelError
    "to offence o:theft for role:principal" "to offence f:movable-property for role:principal") "SFE087"
  refuse "duplicate instance ID" (modelError
    "as xi:abettor-section84;" "as xi:principal-section84;") "SFE089"
  refuse "scenario cannot rebind attachment" (scenarioError
    "  analyse o:theft;" "  analyse o:theft;\n  attach x:section84 to offence o:theft;") "SFE096"
  refuse "cross-instance graph reference" (modelError
    "all g:nature (f:nature-causation, f:nature-incapacity);"
    "all g:nature (f:xi-principal-section84--nature-causation, f:nature-incapacity);") "SFE095"
  refuse "global unscoped section 84 fact" (scenarioError
    "  analyse o:theft;" "  analyse o:theft;\n  f:unsoundness-time = proved;") "SFE090"
  refuse "missing selected instance input" (scenarioError
    "  exception-status xi:principal-section84 f:unsoundness-time by actor:principal-1 context principal-conduct = not_proved;\n"
    "") "SFE009"
  refuse "unknown observed instance" (scenarioError
    "  analyse o:theft;" "  analyse o:theft;\n  observe xi:unknown;") "SFE089"
  check "invalid scenario has no successful request" $
    case compileSource modelPath source (Just (scenarioPath "invalid",replace
      "xi:principal-section84 f:unsoundness-time" "xi:unknown f:unsoundness-time"
      baseScenario)) of
      Left _ -> True
      Right _ -> False
  putStrLn "actor-scoped section 84: 16 technical scenarios and 13 refusals passed"

check :: String -> Bool -> IO ()
check label success = unless success
  (putStrLn ("actor-scoped section 84 failed: " <> label) >> exitFailure)

replace :: Text -> Text -> BS.ByteString -> BS.ByteString
replace old new = Encoding.encodeUtf8 . Text.replace old new . Encoding.decodeUtf8

errorCode :: Either Diagnostic a -> Maybe Text
errorCode (Left issue)
  | not (null (diagnosticPath issue))
      && tokenLine (diagnosticToken issue) > 0
      && tokenColumn (diagnosticToken issue) > 0 = Just (diagnosticCode issue)
errorCode _ = Nothing

responseStatus :: BS.ByteString -> Maybe Text
responseStatus bytes = do
  value <- either (const Nothing) Just (decodeJson bytes)
  lookupField "status" value >>= textValue

rootRule :: BS.ByteString -> Maybe J
rootRule bytes = do
  value <- either (const Nothing) Just (decodeJson bytes)
  JArr (first:_) <- lookupField "rules" value
  pure first

selectedGuard :: BS.ByteString -> Maybe Text
selectedGuard bytes = do
  root <- rootRule bytes
  JArr [branch] <- lookupField "branches" root
  JArr [guard] <- lookupField "exceptions" branch
  lookupField "id" guard >>= textValue
