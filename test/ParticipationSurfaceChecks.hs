{-# LANGUAGE OverloadedStrings #-}
module ParticipationSurfaceChecks (runParticipationSurfaceChecks) where

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

runParticipationSurfaceChecks :: FilePath -> IO ()
runParticipationSurfaceChecks root = do
  let base = root </> "research/singapore/abetment-pilot"
      modelPath = base </> "intentional-aid-theft.yh"
      scenarioPath name = base </> "scenarios" </> name <> ".yh"
  source <- BS.readFile modelPath
  check "typed model and one authored intentional-aid graph" $ case
      checkSource modelPath source Nothing of
    Right (Checked model Nothing [] _ Nothing) -> case modelBody model of
      ParticipationLegal roles definitions facts mental assumptions offence
        (IntentionalAidRoute route relation) citations outputs ->
          length roles == 2 && length definitions == 3
            && length facts == 10 && length mental == 4
            && length assumptions == 6 && length citations == 8
            && length outputs == 10 && ruleKind offence == OffenceKind
            && ruleKind route == ParticipationKind
            && tokenText (relationIdentifier relation) == "rel:aid"
            && map definitionKind definitions == [WrongfulGain,WrongfulLoss,Dishonesty]
      _ -> False
    _ -> False
  let cases =
        [("01_aid_by_act","satisfied")
        ,("02_illegal_omission","satisfied")
        ,("03_no_aid_intention","not_satisfied")
        ,("04_no_aid_conduct","not_satisfied")
        ,("05_principal_not_proved","not_satisfied")
        ,("06_no_consequence","not_satisfied")
        ,("07_aid_unresolved","unresolved")
        ,("08_intention_unresolved","unresolved")
        ,("09_principal_intention_only","not_satisfied")
        ,("10_abettor_intention_only","not_satisfied")]
  forM_ cases $ \(name,wanted) -> do
    scenario <- BS.readFile (scenarioPath name)
    let supplied = Just (scenarioPath name,scenario)
    case (checkSource modelPath source supplied,compileSource modelPath source supplied) of
      (Right checked,Right request) -> do
        check (name <> " deterministic compilation")
          (compileSource modelPath source supplied == Right request)
        check (name <> " technical result") (responseStatus (runLine request) == Just wanted)
        check (name <> " no actor or scope facts in kernel request")
          (not ("actor:principal-1" `BS.isInfixOf` request)
            && not ("a:only-intentional-aid-route" `BS.isInfixOf` request))
        case explainChecked modelPath checked of
          Right explanation -> do
            check (name <> " actor-aware explanation")
              ("Principal role: actor:principal-1" `Text.isInfixOf` explanation
                && "Alleged-abettor role: actor:participant-1" `Text.isInfixOf` explanation
                && "Relationship: actor:participant-1 -> actor:principal-1" `Text.isInfixOf` explanation
                && "Penal Code 1871 s 107" `Text.isInfixOf` explanation
                && "Evidence Act 1893 s 107" `Text.isInfixOf` explanation
                && "No guilt, conviction, acquittal" `Text.isInfixOf` explanation)
            if name `elem` ["01_aid_by_act","02_illegal_omission"] then do
              snapshot <- BS.readFile (base </> "snapshots" </> name <> ".txt")
              check (name <> " stable explanation snapshot")
                (Encoding.encodeUtf8 explanation == snapshot)
            else pure ()
          Left _ -> check (name <> " explanation") False
      _ -> check (name <> " checks and compiles") False
  baseScenario <- BS.readFile (scenarioPath "01_aid_by_act")
  let scenarioError old new = errorCode (checkSource modelPath source
        (Just (scenarioPath "invalid",replace old new baseScenario)))
      modelError old new = errorCode (checkSource modelPath
        (replace old new source) Nothing)
      refusal label got wanted = check label (got == Just wanted)
  refusal "missing principal binding" (scenarioError
    "  bind role:principal to actor:principal-1;\n" "") "SFE063"
  refusal "missing alleged-abettor binding" (scenarioError
    "  bind role:alleged-abettor to actor:participant-1;\n" "") "SFE063"
  refusal "duplicate role binding" (scenarioError
    "  bind role:principal to actor:principal-1;"
    "  bind role:principal to actor:principal-1;\n  bind role:principal to actor:principal-1;") "SFE064"
  refusal "distinct actors required" (scenarioError
    "bind role:alleged-abettor to actor:participant-1"
    "bind role:alleged-abettor to actor:principal-1") "SFE064"
  refusal "unknown role" (scenarioError
    "bind role:principal to actor:principal-1"
    "bind role:unknown to actor:principal-1") "SFE063"
  refusal "missing analysis target" (scenarioError
    "  analyse p:intentional-aid;\n" "") "SFE036"
  refusal "multiple analysis targets" (scenarioError
    "  analyse p:intentional-aid;"
    "  analyse p:intentional-aid;\n  analyse p:intentional-aid;") "SFE037"
  refusal "reversed relation" (scenarioError
    "rel:aid from actor:participant-1 to actor:principal-1"
    "rel:aid from actor:principal-1 to actor:participant-1") "SFE068"
  refusal "principal fact attributed to alleged abettor" (scenarioError
    "f:movable-property by actor:principal-1"
    "f:movable-property by actor:participant-1") "SFE067"
  refusal "aid fact attributed to principal" (scenarioError
    "f:aid-by-act by actor:participant-1"
    "f:aid-by-act by actor:principal-1") "SFE067"
  refusal "unattributed actor fact" (scenarioError
    "f:movable-property by actor:principal-1"
    "f:movable-property") "SFE065"
  refusal "unknown actor cannot supply principal intention" (scenarioError
    "f:intends-wrongful-gain by actor:principal-1"
    "f:intends-wrongful-gain by actor:other-1") "SFE067"
  refusal "missing relation status" (scenarioError
    "  rel:aid from actor:participant-1 to actor:principal-1 = proved;\n" "") "SFE068"
  refusal "duplicate relation status" (scenarioError
    "  rel:aid from actor:participant-1 to actor:principal-1 = proved;"
    "  rel:aid from actor:participant-1 to actor:principal-1 = proved;\n  rel:aid from actor:participant-1 to actor:principal-1 = proved;") "SFE002"
  refusal "missing participation scope" (scenarioError
    "  assume a:no-express-punishment-provision-modelled;\n" "") "SFE022"
  refusal "duplicate scope acknowledgement" (scenarioError
    "  assume a:no-express-punishment-provision-modelled;"
    "  assume a:no-express-punishment-provision-modelled;\n  assume a:no-express-punishment-provision-modelled;") "SFE024"
  refusal "duplicate party declaration" (modelError
    "    party-role role:principal;"
    "    party-role role:principal;\n    party-role role:principal;") "SFE063"
  refusal "unsupported instigation" (modelError
    "route intentional-aid" "route instigation") "SFE070"
  refusal "unsupported conspiracy" (modelError
    "route intentional-aid" "route conspiracy") "SFE070"
  refusal "bare s 107 authority is ambiguous" (modelError
    "authority abetment PenalCode1871" "authority abetment section") "SFE073"
  refusal "Evidence Act s 107 cannot author abetment" (modelError
    "authority abetment PenalCode1871" "authority abetment EvidenceAct1893") "SFE074"
  refusal "Penal Code s 107 cannot author burden context" (modelError
    "authority burden-context EvidenceAct1893" "authority burden-context PenalCode1871") "SFE074"
  refusal "relation target must be theft" (modelError
    "to role:principal target o:theft" "to role:principal target o:other") "SFE068"
  refusal "relation direction is typed" (modelError
    "from role:alleged-abettor to role:principal"
    "from role:principal to role:alleged-abettor") "SFE068"
  refusal "unknown analysis target" (scenarioError
    "analyse p:intentional-aid" "analyse o:theft") "SFE069"
  refusal "missing classification" (scenarioError
    "  f:intends-aid by actor:participant-1 = proved;\n" "") "SFE009"
  putStrLn "typed participation: 10 technical scenarios, 2 snapshots and 26 refusals passed"

check :: String -> Bool -> IO ()
check label success = unless success
  (putStrLn ("typed participation failed: " <> label) >> exitFailure)

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
