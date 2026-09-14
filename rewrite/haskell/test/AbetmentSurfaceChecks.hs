{-# LANGUAGE OverloadedStrings #-}
module AbetmentSurfaceChecks (runAbetmentSurfaceChecks) where

import Control.Monad (forM, unless, when)
import qualified Data.ByteString as BS
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

runAbetmentSurfaceChecks :: FilePath -> IO ()
runAbetmentSurfaceChecks root = do
  let base = root </> "research/singapore/abetment-routes-pilot"
      modelPath = base </> "section107-routes-theft.yh"
      scenarioPath name = base </> "scenarios" </> name <> ".yh"
  source <- BS.readFile modelPath
  check "typed three-route abetment and one shared exception" $
    case checkSource modelPath source Nothing of
      Right (Checked model Nothing [] _ (Just _)) -> case modelBody model of
        AbetmentLegal roles _ _ _ offence abetment _
          (ActorExceptionDefinition _ shared) attachments _ outputs ->
            length roles == 4 && ruleKind offence == OffenceKind
              && length (abetmentRoutes abetment) == 3
              && ruleKind (abetmentRule abetment) == ParticipationKind
              && ruleKind shared == ExceptionKind
              && length (ruleElements shared) == 8
              && length attachments == 3 && length outputs == 14
        _ -> False
      _ -> False
  let cases =
        [("01_instigation_established","satisfied")
        ,("02_instigation_not_proved","not_satisfied")
        ,("03_instigation_unresolved","unresolved")
        ,("04_principal_target_not_satisfied","not_satisfied")
        ,("05_consequence_not_proved","not_satisfied")
        ,("06_instigation_abettor_section84","not_satisfied")
        ,("07_instigation_principal_isolation","satisfied")
        ,("08_conspiracy_act","satisfied")
        ,("09_conspiracy_omission","satisfied")
        ,("10_conspiracy_no_agreement","not_satisfied")
        ,("11_conspiracy_no_conduct","not_satisfied")
        ,("12_conspiracy_no_pursuance","not_satisfied")
        ,("13_conspiracy_agreement_unresolved","unresolved")
        ,("14_conspiracy_conduct_unresolved","unresolved")
        ,("15_aid_abettor_section84","not_satisfied")
        ,("16_conspiracy_abettor_section84","not_satisfied")
        ,("17_aid_by_act","satisfied")
        ,("18_aid_by_omission","satisfied")
        ,("19_aid_no_intention","not_satisfied")
        ,("20_aid_link_unresolved","unresolved")
        ,("21_two_routes_satisfied","satisfied")
        ,("22_unresolved_plus_satisfied","satisfied")
        ,("23_attempter_isolation","satisfied")
        ,("24_principal_unresolved_isolation","satisfied")]
  compiled <- forM cases $ \(name,wanted) -> do
    scenario <- BS.readFile (scenarioPath name)
    let supplied = Just (scenarioPath name,scenario)
    case (checkSource modelPath source supplied,compileSource modelPath source supplied) of
      (Right checked,Right request) -> do
        check (name <> " deterministic compilation")
          (compileSource modelPath source supplied == Right request)
        let response = runLine request
        check (name <> " technical result") (responseStatus response == Just wanted)
        check (name <> " no completed-target dependency")
          (not ("f:movable-property" `BS.isInfixOf` request)
            || name == "04_principal_target_not_satisfied")
        check (name <> " no actor IDs as proof facts")
          (not ("actor:participant-1" `BS.isInfixOf` request))
        case explainChecked modelPath checked of
          Right explanation -> do
            check (name <> " route-aware explanation")
              ("General exception instance:" `Text.isInfixOf` explanation
                && "Other actor instances:" `Text.isInfixOf` explanation
                && "No guilt, conviction, acquittal" `Text.isInfixOf` explanation
                && (name == "04_principal_target_not_satisfied" ||
                    "Overall technical s 107 status:" `Text.isInfixOf` explanation))
            when (name `elem` ["01_instigation_established", "08_conspiracy_act",
                "15_aid_abettor_section84", "17_aid_by_act"]) $ do
              snapshot <- BS.readFile (base </> "snapshots" </> name <> ".txt")
              check (name <> " explanation snapshot")
                (Encoding.encodeUtf8 explanation == snapshot)
          Left _ -> check (name <> " explanation") False
        pure (name,request)
      _ -> check (name <> " checks and compiles") False >> pure (name,BS.empty)
  let requestFor name = lookup name compiled
  check "principal section 84 cannot defeat instigation" $
    case (requestFor "01_instigation_established",
          requestFor "07_instigation_principal_isolation") of
      (Just first,Just other) -> responseStatus (runLine first) ==
        responseStatus (runLine other)
      _ -> False
  check "attempter section 84 cannot defeat instigation" $
    case requestFor "23_attempter_isolation" of
      Just request -> responseStatus (runLine request) == Just "satisfied"
      _ -> False
  check "s 107 and s 109 stay distinct when consequence is not proved" $
    case requestFor "05_consequence_not_proved" of
      Just request -> let response = runLine request in
        traceStatus response "g:section107-routes" == Just "satisfied"
          && traceStatus response "g:section109" == Just "not_satisfied"
      _ -> False
  check "conspiracy agreement and pursuant link are independently decisive" $
    case requestFor "12_conspiracy_no_pursuance" of
      Just request -> let response = runLine request in
        traceStatus response "f:agreement-link" == Just "satisfied"
          && traceStatus response "f:pursuance-link" == Just "not_satisfied"
      _ -> False
  baseScenario <- BS.readFile (scenarioPath "01_instigation_established")
  let modelError old new = errorCode (checkSource modelPath
        (replace old new source) Nothing)
      scenarioError old new = errorCode (checkSource modelPath source
        (Just (scenarioPath "invalid",replace old new baseScenario)))
      refuse label actual wanted = check label (actual == Just wanted)
  refuse "duplicate route IDs" (modelError
    "route:conspiracy" "route:instigation") "SFE101"
  refuse "unsupported route" (modelError
    "instigation route route:instigation" "deemed-instigation route route:instigation") "SFE100"
  refuse "reversed instigation" (modelError
    "rel:instigates from role:alleged-abettor to role:principal"
    "rel:instigates from role:principal to role:alleged-abettor") "SFE102"
  refuse "missing conspiracy agreement" (modelError
    "f:agreement-link, g:pursuant-form" "f:instigation-link, g:pursuant-form") "SFE103"
  refuse "wrong co-conspirator" (modelError
    "with role:co-conspirator" "with role:principal") "SFE103"
  refuse "wrong target" (modelError
    "abetment p:abet-theft actor role:alleged-abettor target o:theft"
    "abetment p:abet-theft actor role:alleged-abettor target o:unknown") "SFE100"
  refuse "Penal Code s 107 cannot use Evidence Act authority" (modelError
    "authority abetment PenalCode1871 src:pc section 107"
    "authority abetment EvidenceAct1893 src:pc section 107") "SFE074"
  refuse "wrong section 84 attachment target" (modelError
    "to participation p:abet-theft" "to participation f:instigation-link") "SFE087"
  refuse "same principal and alleged abettor" (scenarioError
    "bind role:alleged-abettor to actor:participant-1"
    "bind role:alleged-abettor to actor:principal-1") "SFE088"
  refuse "missing co-conspirator binding" (scenarioError
    "  bind role:co-conspirator to actor:co-1;\n" "") "SFE088"
  refuse "reversed relation actors" (scenarioError
    "rel:instigates from actor:participant-1 to actor:principal-1"
    "rel:instigates from actor:principal-1 to actor:participant-1") "SFE102"
  refuse "derived route output assignment" (scenarioError
    "rel:instigates from actor:participant-1 to actor:principal-1 = proved;"
    "g:section107-routes by actor:participant-1 = proved;") "SFE065"
  refuse "unselected offence assignment" (scenarioError
    "  rel:instigates from actor:participant-1 to actor:principal-1 = proved;"
    "  f:movable-property by actor:principal-1 = proved;\n  rel:instigates from actor:participant-1 to actor:principal-1 = proved;") "SFE009"
  refuse "wrong instance actor" (scenarioError
    "f:unsoundness-time by actor:participant-1 context aid-conduct"
    "f:unsoundness-time by actor:principal-1 context aid-conduct") "SFE091"
  refuse "wrong instance context" (scenarioError
    "f:unsoundness-time by actor:participant-1 context aid-conduct"
    "f:unsoundness-time by actor:participant-1 context principal-conduct") "SFE092"
  check "invalid model produces no request" $
    case compileSource modelPath (replace
      "instigation route route:instigation" "deemed-instigation route route:instigation"
      source) (Just (scenarioPath "invalid",baseScenario)) of
      Left _ -> True
      Right _ -> False
  putStrLn "typed s 107 abetment: 24 technical scenarios and 15 refusals passed"

check :: String -> Bool -> IO ()
check label success = unless success
  (putStrLn ("typed abetment failed: " <> label) >> exitFailure)

replace :: Text.Text -> Text.Text -> BS.ByteString -> BS.ByteString
replace old new = Encoding.encodeUtf8 . Text.replace old new . Encoding.decodeUtf8

errorCode :: Either Diagnostic a -> Maybe Text.Text
errorCode (Left issue)
  | not (null (diagnosticPath issue))
      && tokenLine (diagnosticToken issue) > 0
      && tokenColumn (diagnosticToken issue) > 0 = Just (diagnosticCode issue)
errorCode _ = Nothing

responseStatus :: BS.ByteString -> Maybe Text.Text
responseStatus bytes = do
  value <- either (const Nothing) Just (decodeJson bytes)
  lookupField "status" value >>= textValue

traceStatus :: BS.ByteString -> Text.Text -> Maybe Text.Text
traceStatus bytes wanted = do
  value <- either (const Nothing) Just (decodeJson bytes)
  JArr (rule:_) <- lookupField "rules" value
  JArr rows <- lookupField "trace" rule
  case [status | item <- rows,
    (lookupField "id" item >>= textValue) == Just wanted,
    Just status <- [lookupField "value" item >>= textValue]] of
    [status] -> Just status
    _ -> Nothing
