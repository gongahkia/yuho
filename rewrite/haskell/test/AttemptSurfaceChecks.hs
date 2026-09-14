{-# LANGUAGE OverloadedStrings #-}
module AttemptSurfaceChecks (runAttemptSurfaceChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (decodeJson, lookupField, textValue)
import Yuho.Surface.AST
import Yuho.Surface.Compile (checkSource, compileSource)
import Yuho.Surface.Explain (explainChecked)
import Yuho.Surface.Token (Diagnostic(..), Token(..))

runAttemptSurfaceChecks :: FilePath -> IO ()
runAttemptSurfaceChecks root = do
  let base = root </> "research/singapore/attempt-pilot"
      modelPath = base </> "section511-theft-attempt.yh"
      scenarioPath name = base </> "scenarios" </> name <> ".yh"
  source <- BS.readFile modelPath
  check "typed attempt and non-executable target" $ case checkSource modelPath source Nothing of
    Right (Checked model Nothing [] (ResolvedGroup _ All [ResolvedLeaf _ _,ResolvedLeaf _ _]) Nothing) ->
      case modelBody model of
        AttemptLegal [PartyRole _ AllegedAttempterParty] definitions assumptions target attempt citations outputs ->
          length definitions == 3 && length assumptions == 7 && length citations == 5
            && length outputs == 5 && ruleKind target == OffenceKind
            && ruleKind (attemptRule attempt) == AttemptKind
            && tokenText (ruleIdentifier target) == "o:theft"
            && tokenText (attemptStageOutput (attemptConductStage attempt)) == "f:substantial-step"
        _ -> False
    _ -> False
  let cases =
        [("01_act_towards_commission","satisfied","act_towards_commission")
        ,("02_preparation_only","not_satisfied","preparation_only")
        ,("03_intention_not_proved","not_satisfied","act_towards_commission")
        ,("04_intention_unresolved","unresolved","act_towards_commission")
        ,("05_stage_unresolved","unresolved","unresolved(not_determined)")
        ,("06_both_unresolved","unresolved","unresolved(not_determined)")]
  forM_ cases $ \(name,wanted,stage) -> do
    scenario <- BS.readFile (scenarioPath name)
    let supplied = Just (scenarioPath name,scenario)
    case (checkSource modelPath source supplied,compileSource modelPath source supplied) of
      (Right checked,Right request) -> do
        check (name <> " deterministic compilation")
          (compileSource modelPath source supplied == Right request)
        check (name <> " kernel result") (responseStatus (runLine request) == Just wanted)
        check (name <> " only bounded inputs lower")
          ("f:intends-target" `BS.isInfixOf` request
            && "f:substantial-step" `BS.isInfixOf` request
            && not ("f:movable-property" `BS.isInfixOf` request)
            && not ("a:direct-self-attempt-only" `BS.isInfixOf` request)
            && not ("stage:theft-conduct" `BS.isInfixOf` request)
            && not ("g:dishonestly" `BS.isInfixOf` request))
        case explainChecked modelPath checked of
          Right explanation -> do
            check (name <> " attempt-aware explanation")
              ("Alleged-attempter: actor:attempt-actor-1" `Text.isInfixOf` explanation
                && ("supplied " <> stage) `Text.isInfixOf` explanation
                && "completed theft requirements are not executable prerequisites" `Text.isInfixOf` explanation
                && "Penal Code 1871 s 511" `Text.isInfixOf` explanation
                && "No guilt, conviction, acquittal" `Text.isInfixOf` explanation)
            if name `elem` ["01_act_towards_commission","02_preparation_only","05_stage_unresolved"]
              then do
                snapshot <- BS.readFile (base </> "snapshots" </> name <> ".txt")
                check (name <> " explanation snapshot") (Encoding.encodeUtf8 explanation == snapshot)
              else pure ()
          Left _ -> check (name <> " explanation") False
      _ -> check (name <> " checks and compiles") False
  baseScenario <- BS.readFile (scenarioPath "01_act_towards_commission")
  let scenarioError old new = errorCode (checkSource modelPath source
        (Just (scenarioPath "invalid",replace old new baseScenario)))
      modelError old new = errorCode (checkSource modelPath
        (replace old new source) Nothing)
      refuse label actual wanted = check label (actual == Just wanted)
  refuse "missing actor binding" (scenarioError
    "  bind role:alleged-attempter to actor:attempt-actor-1;\n" "") "SFE083"
  refuse "duplicate actor binding" (scenarioError
    "  bind role:alleged-attempter to actor:attempt-actor-1;"
    "  bind role:alleged-attempter to actor:attempt-actor-1;\n  bind role:alleged-attempter to actor:attempt-actor-2;") "SFE083"
  refuse "unknown actor role" (scenarioError
    "bind role:alleged-attempter" "bind role:unknown") "SFE083"
  refuse "missing attempt analysis target" (scenarioError
    "  analyse attempt:theft;\n" "") "SFE036"
  refuse "unknown attempt analysis target" (scenarioError
    "analyse attempt:theft" "analyse attempt:other") "SFE075"
  refuse "multiple attempt analysis targets" (scenarioError
    "  analyse attempt:theft;"
    "  analyse attempt:theft;\n  analyse attempt:theft;") "SFE037"
  refuse "wrong-actor intention" (scenarioError
    "f:intends-target by actor:attempt-actor-1" "f:intends-target by actor:other-1") "SFE081"
  refuse "wrong-actor stage" (scenarioError
    "stage:theft-conduct by actor:attempt-actor-1" "stage:theft-conduct by actor:other-1") "SFE082"
  refuse "missing stage" (scenarioError
    "  stage stage:theft-conduct by actor:attempt-actor-1 = act_towards_commission;\n" "") "SFE076"
  refuse "duplicate stage" (scenarioError
    "  stage stage:theft-conduct by actor:attempt-actor-1 = act_towards_commission;"
    "  stage stage:theft-conduct by actor:attempt-actor-1 = act_towards_commission;\n  stage stage:theft-conduct by actor:attempt-actor-1 = act_towards_commission;") "SFE077"
  refuse "contradictory stage" (scenarioError
    "  stage stage:theft-conduct by actor:attempt-actor-1 = act_towards_commission;"
    "  stage stage:theft-conduct by actor:attempt-actor-1 = act_towards_commission;\n  stage stage:theft-conduct by actor:attempt-actor-1 = preparation_only;") "SFE077"
  refuse "completed stage" (scenarioError "= act_towards_commission;" "= completed;") "SFE078"
  refuse "unknown stage" (scenarioError "= act_towards_commission;" "= almost_there;") "SFE078"
  refuse "free-text stage" (scenarioError "= act_towards_commission;" "= \"I nearly did it\";") "SFE001"
  refuse "missing intention" (scenarioError
    "  f:intends-target by actor:attempt-actor-1 = proved;\n" "") "SFE081"
  refuse "missing target completion" (scenarioError
    "  target-completion o:theft = not_completed;\n" "") "SFE080"
  refuse "completed target" (scenarioError "= not_completed;" "= completed;") "SFE080"
  refuse "scenario changes target" (scenarioError "target-completion o:theft" "target-completion o:other") "SFE075"
  refuse "scenario target override" (scenarioError
    "  target-completion o:theft = not_completed;"
    "  target-completion o:theft = not_completed;\n  target o:other;") "SFE075"
  refuse "unknown model target" (modelError "target o:theft rule r:section511-candidate"
    "target o:other rule r:section511-candidate") "SFE075"
  refuse "definition cannot be attempt target" (modelError "target o:theft rule r:section511-candidate"
    "target d:dishonestly rule r:section511-candidate") "SFE075"
  refuse "exception cannot be attempt target" (modelError "target o:theft rule r:section511-candidate"
    "target x:section84 rule r:section511-candidate") "SFE075"
  refuse "intention targets wrong offence" (modelError "kind intention target o:theft"
    "kind intention target o:other") "SFE075"
  refuse "model stage attributed elsewhere" (modelError "conduct-stage stage:theft-conduct actor role:alleged-attempter"
    "conduct-stage stage:theft-conduct actor role:principal") "SFE081"
  refuse "unsupported other-actor route" (modelError "route direct-self" "route cause-another") "SFE086"
  refuse "target offence cannot be executable dependency" (modelError
    "all g:attempt-requirements (f:intends-target, f:substantial-step);"
    "all g:attempt-requirements (f:intends-target, g:theft-requirements);") "SFE085"
  refuse "missing direct-attempt scope" (scenarioError
    "  assume a:direct-self-attempt-only;\n" "") "SFE022"
  refuse "missing no-express-provision scope" (scenarioError
    "  assume a:no-express-attempt-punishment-provision-modelled;\n" "") "SFE022"
  refuse "missing external-stage scope" (scenarioError
    "  assume a:stage-externally-classified;\n" "") "SFE022"
  refuse "unattributed intention" (scenarioError
    "f:intends-target by actor:attempt-actor-1" "f:intends-target") "SFE082"
  refuse "target theft fact cannot be supplied as attempt input" (scenarioError
    "  f:intends-target by actor:attempt-actor-1 = proved;"
    "  f:intends-target by actor:attempt-actor-1 = proved;\n  f:movable-property by actor:attempt-actor-1 = proved;") "SFE081"
  refuse "unattributed stage" (scenarioError
    "stage stage:theft-conduct by actor:attempt-actor-1"
    "stage stage:theft-conduct") "SFE001"
  check "failed compilation yields no request" (case compileSource modelPath source
    (Just (scenarioPath "invalid",replace "= act_towards_commission;" "= completed;" baseScenario)) of
      Left _ -> True
      Right _ -> False)
  putStrLn "typed attempt: 6 technical scenarios, 3 snapshots and 32 refusals passed"

check :: String -> Bool -> IO ()
check label success = unless success
  (putStrLn ("typed attempt failed: " <> label) >> exitFailure)

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
