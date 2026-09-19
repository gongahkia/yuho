{-# LANGUAGE OverloadedStrings #-}
module DefinitionSurfaceChecks (runDefinitionSurfaceChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (arrayValue, decodeJson, lookupField, objectFields, textValue)
import Yuho.Surface.AST
import Yuho.Surface.Compile (checkSource, compileSource)
import Yuho.Surface.Explain (explainChecked)
import Yuho.Surface.Token (Diagnostic(..), Token(..))

runDefinitionSurfaceChecks :: FilePath -> IO ()
runDefinitionSurfaceChecks root = do
  let base = root </> "research/singapore/section-84-pilot/statutory-definitions"
      modelPath = base </> "section323-section379-definitions.yh"
      scenarioPath name = base </> "scenarios" </> name <> ".yh"
  source <- BS.readFile modelPath
  check "five typed statutory definitions and one shared section 84" $ case
      checkSource modelPath source Nothing of
    Right (Checked model Nothing [] _ (Just _)) -> case modelBody model of
      DefinitionsLegal definitions assumptions offences exceptions attachments outputs ->
        length definitions == 5 && length assumptions == 4 && length offences == 2
          && length exceptions == 1 && length attachments == 2 && length outputs == 9
          && map definitionKind definitions ==
            [HurtResult,VoluntaryHurt,WrongfulGain,WrongfulLoss,Dishonesty]
          && length (definitionMentalStates (definitions !! 1)) == 2
          && length (definitionMentalStates (definitions !! 4)) == 2
      _ -> False
    _ -> False
  let cases =
        [("01_hurt_pain","satisfied","satisfied","o:voluntary-hurt")
        ,("02_hurt_disease","satisfied","satisfied","o:voluntary-hurt")
        ,("03_hurt_infirmity","satisfied","satisfied","o:voluntary-hurt")
        ,("04_hurt_none","not_satisfied","requirements_not_satisfied","o:voluntary-hurt")
        ,("05_hurt_no_causation","not_satisfied","requirements_not_satisfied","o:voluntary-hurt")
        ,("06_hurt_intention","satisfied","satisfied","o:voluntary-hurt")
        ,("07_hurt_knowledge","satisfied","satisfied","o:voluntary-hurt")
        ,("08_hurt_unresolved","unresolved","requirements_unresolved","o:voluntary-hurt")
        ,("10_theft_gain_intent","satisfied","satisfied","o:theft")
        ,("11_theft_loss_intent","satisfied","satisfied","o:theft")
        ,("12_theft_no_dishonest_intent","not_satisfied","requirements_not_satisfied","o:theft")
        ,("13_theft_unresolved_intent","unresolved","requirements_unresolved","o:theft")
        ,("14_theft_no_actual_gain","satisfied","satisfied","o:theft")
        ,("16_theft_ordinary_route","satisfied","satisfied","o:theft")
        ,("17_hurt_satisfied","satisfied","satisfied","o:voluntary-hurt")
        ,("18_theft_satisfied","satisfied","satisfied","o:theft")
        ,("19_hurt_section84","not_satisfied","defeated","o:voluntary-hurt")
        ,("20_theft_section84","not_satisfied","defeated","o:theft")]
  forM_ cases $ \(name,status,reason,target) -> do
    scenario <- BS.readFile (scenarioPath name)
    let supplied = Just (scenarioPath name,scenario)
    case (checkSource modelPath source supplied,
          compileSource modelPath source supplied) of
      (Right checked,Right request) -> do
        check (name <> " deterministic compilation")
          (compileSource modelPath source supplied == Right request)
        check (name <> " technical result")
          (responsePair (runLine request) == Just (status,reason))
        check (name <> " selected closure and no scope facts")
          (requestIsolated target request)
        case explainChecked modelPath checked of
          Right explanation -> do
            check (name <> " definition-aware explanation")
              (("Selected candidate offence: " <> target) `Text.isInfixOf` explanation
                && "Definition instance: shared x:section84" `Text.isInfixOf` explanation
                && "Section 107 context:" `Text.isInfixOf` explanation
                && "No guilt, conviction, acquittal or sentence was determined."
                   `Text.isInfixOf` explanation)
            if name `elem` ["01_hurt_pain","10_theft_gain_intent"] then do
              snapshot <- BS.readFile (base </> "snapshots" </> name <> ".txt")
              check (name <> " stable explanation snapshot")
                (Encoding.encodeUtf8 explanation == snapshot)
            else pure ()
          Left _ -> check (name <> " explanation") False
      _ -> check (name <> " checks and compiles") False
  let refusals =
        [("09_hurt_derived_assignment","SFE059")
        ,("15_theft_derived_assignment","SFE059")
        ,("21_unreachable_assignment","SFE060")
        ,("22_missing_reachable","SFE061")]
  forM_ refusals $ \(name,code) -> do
    scenario <- BS.readFile (scenarioPath name)
    check (name <> " source-located refusal") $ case
        compileSource modelPath source (Just (scenarioPath name,scenario)) of
      Left issue -> diagnosticCode issue == code
        && diagnosticPath issue == scenarioPath name
        && tokenLine (diagnosticToken issue) > 0
        && tokenColumn (diagnosticToken issue) > 0
      Right _ -> False
  let badModel old new = errorCode (checkSource modelPath
        (replace old new source) Nothing)
  check "unknown executable definition" (badModel
    "use d:hurt as hurt-result;" "use d:unknown as hurt-result;" == Just "SFE053")
  check "duplicate statutory definition" (badModel
    "statutory-definition d:wrongful-gain" "statutory-definition d:hurt" == Just "SFE050")
  check "definition cycle" (badModel
    "any g:hurt (f:bodily-pain, f:disease, f:infirmity);"
    "use d:voluntarily-causing-hurt as voluntary-hurt;\n      any g:hurt (f:bodily-pain, f:disease, f:infirmity, d:voluntarily-causing-hurt);"
    == Just "SFE054")
  check "missing definition output" (badModel "output g:hurt;" "" == Just "SFE055")
  check "multiple definition outputs" (badModel "output g:hurt;"
    "output g:hurt;\n      output g:other;" == Just "SFE055")
  check "definition reference type mismatch" (badModel
    "use d:hurt as hurt-result;" "use d:hurt as dishonesty;" == Just "SFE056")
  check "mental-state target type mismatch" (badModel
    "target d:wrongful-gain as wrongful-gain" "target d:wrongful-gain as hurt-result"
    == Just "SFE057")
  check "definition private proposition cannot be used by offence" (badModel
    "all g:section323-requirements (d:voluntarily-causing-hurt);"
    "all g:section323-requirements (g:hurt);" == Just "SFE058")
  check "undeclared executable reference rejected" (badModel
    "use d:voluntarily-causing-hurt as voluntary-hurt;" ""
    == Just "SFE003")
  gainScenario <- BS.readFile (scenarioPath "10_theft_gain_intent")
  let amended = replace "quote q:gain \"gain by unlawful means of property\";"
        "quote q:gain \"changed target-only description\";" source
  check "unused definition has no effect on selected request" $
    case (compileSource modelPath source
      (Just (scenarioPath "10_theft_gain_intent", gainScenario)),
      compileSource modelPath amended
      (Just (scenarioPath "10_theft_gain_intent", gainScenario))) of
      (Right first,Right second) -> first == second
      _ -> False
  putStrLn "statutory definitions: 18 technical scenarios, 4 assignment refusals and 9 graph diagnostics passed"

check :: String -> Bool -> IO ()
check label success = unless success
  (putStrLn ("statutory definitions failed: " <> label) >> exitFailure)

replace :: Text -> Text -> BS.ByteString -> BS.ByteString
replace old new = Encoding.encodeUtf8 . Text.replace old new . Encoding.decodeUtf8

errorCode :: Either Diagnostic a -> Maybe Text
errorCode (Left issue) = Just (diagnosticCode issue)
errorCode (Right _) = Nothing

responsePair :: BS.ByteString -> Maybe (Text, Text)
responsePair bytes = do
  value <- either (const Nothing) Just (decodeJson bytes)
  status <- lookupField "status" value >>= textValue
  rules <- lookupField "rules" value >>= arrayValue
  root <- case rules of item:_ -> Just item; [] -> Nothing
  branches <- lookupField "branches" root >>= arrayValue
  branch <- case branches of item:_ -> Just item; [] -> Nothing
  reason <- lookupField "reason" branch >>= textValue
  pure (status,reason)

requestIsolated :: Text -> BS.ByteString -> Bool
requestIsolated target bytes = case decodeJson bytes of
  Left _ -> False
  Right request ->
    let facts = maybe [] (map fst) (lookupField "facts" request >>= objectFields)
        has key = key `elem` facts
        absent key = key `notElem` facts
        selected = if target == "o:theft" then
          has "f:intends-wrongful-gain" && absent "f:bodily-pain"
          && absent "f:gain-by-unlawful-means" && absent "f:loss-by-unlawful-means"
          else has "f:bodily-pain" && absent "f:intends-wrongful-gain"
    in selected && all (not . Text.isPrefixOf "a:") facts
      && all (not . Text.isPrefixOf "d:") facts
