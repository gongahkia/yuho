{-# LANGUAGE OverloadedStrings #-}
module LegalSurfaceChecks (runLegalSurfaceChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), arrayValue, decodeJson, lookupField, objectFields, textValue)
import Yuho.Surface.AST
import Yuho.Surface.Compile (checkSource, compileSource)
import Yuho.Surface.Explain (explainChecked)
import Yuho.Surface.Token (Diagnostic(..), Token(..))

runLegalSurfaceChecks :: FilePath -> IO ()
runLegalSurfaceChecks root = do
  let base = root </> "research/singapore/section-84-pilot/hurt-offence"
      modelPath = base </> "section323-with-section84.yh"
      scenarioPath name = base </> "scenarios" </> name <> ".yh"
  modelSource <- BS.readFile modelPath
  check "research model checks without a supplied scenario" $ case
      checkSource modelPath modelSource Nothing of
    Right (Checked model Nothing [] (ResolvedGroup _ All _) (Just (ResolvedGroup _ All _))) ->
      case modelBody model of
        Legal scopes offence exception outputs ->
          length scopes == 3 && length outputs == 10
            && ruleKind offence == OffenceKind && ruleKind exception == ExceptionKind
            && map elementCategory (ruleElements offence)
              == [Conduct, Result, Causation, Intention, Knowledge]
            && map elementCategory (ruleElements exception)
              == [Unsoundness, Causation, NatureIncapacity, Causation,
                  OrdinaryWrongfulness, ContraryLawWrongfulness, Causation, ControlIncapacity]
        _ -> False
    _ -> False
  let positive =
        [("01_intention_no_exception", "satisfied", "satisfied")
        ,("02_knowledge_no_exception", "satisfied", "satisfied")
        ,("03_hurt_not_proved", "not_satisfied", "requirements_not_satisfied")
        ,("04_no_fault", "not_satisfied", "requirements_not_satisfied")
        ,("05_offence_causation_unresolved", "unresolved", "requirements_unresolved")
        ,("06_nature_route", "not_satisfied", "defeated")
        ,("07_control_route", "not_satisfied", "defeated")
        ,("08_wrongfulness_both", "not_satisfied", "defeated")
        ,("09_ordinary_only", "satisfied", "satisfied")
        ,("10_contrary_law_only", "satisfied", "satisfied")
        ,("11_section84_unresolved", "unresolved", "exception_unresolved")
        ,("14_all_routes_proved", "not_satisfied", "defeated")]
  forM_ positive $ \(name, expectedStatus, expectedReason) -> do
    scenario <- BS.readFile (scenarioPath name)
    let supplied = Just (scenarioPath name, scenario)
    case (checkSource modelPath modelSource supplied, compileSource modelPath modelSource supplied) of
      (Right checked, Right request) -> do
        check (name <> " compiles deterministically")
          (compileSource modelPath modelSource supplied == Right request)
        check (name <> " produces expected Haskell technical result")
          (responsePair (runLine request) == Just (expectedStatus, expectedReason))
        check (name <> " binds two rules and keeps scope outside executable facts")
          (requestShape request)
        case explainChecked modelPath checked of
          Left _ -> check (name <> " explanation exists") False
          Right explanation -> do
            check (name <> " explanation deterministic and bounded")
              (explainChecked modelPath checked == Right explanation
                && "Scope assumptions: acknowledged by scenario, not inferred or proved"
                   `Text.isInfixOf` explanation
                && "No guilt, conviction, acquittal or sentence was determined."
                   `Text.isInfixOf` explanation)
            if name `elem` ["06_nature_route", "11_section84_unresolved"] then do
              snapshot <- BS.readFile (base </> "snapshots" </> name <> ".txt")
              check (name <> " exact explanation snapshot")
                (Encoding.encodeUtf8 explanation == snapshot)
            else pure ()
      _ -> check (name <> " check and compile succeed") False
  forM_ ["12_missing_section334", "13_missing_post2022", "15_missing_section323a"] $ \name -> do
    scenario <- BS.readFile (scenarioPath name)
    check (name <> " fails closed at the scenario boundary")
      (errorCode (compileSource modelPath modelSource (Just (scenarioPath name, scenario)))
        == Just "SFE022")
    check (name <> " identifies the related model declaration") $ case
        checkSource modelPath modelSource (Just (scenarioPath name, scenario)) of
      Left issue -> case diagnosticRelated issue of
        Just (relatedPath, token) -> relatedPath == modelPath
          && "a:" `Text.isPrefixOf` tokenText token
        Nothing -> False
      Right _ -> False
  baseline <- BS.readFile (scenarioPath "01_intention_no_exception")
  let invalidSource old new = errorCode (checkSource modelPath
        (replace old new modelSource) Nothing)
      invalidScenario old new = errorCode (checkSource modelPath modelSource
        (Just (scenarioPath "01_intention_no_exception", replace old new baseline)))
  check "causation is a typed offence element"
    (invalidSource "element causation f:hurt-caused-by-act"
      "element result f:hurt-caused-by-act" == Just "SFE026")
  check "intention and knowledge remain an alternative"
    (invalidSource "any g:section321-fault" "all g:section321-fault" == Just "SFE027")
  check "exception cannot target a non-offence proposition"
    (invalidSource "to o:voluntary-hurt" "to g:voluntary-hurt" == Just "SFE018")
  check "scope assumption cannot enter the executable graph"
    (invalidSource "(f:act-performed, f:hurt-caused"
      "(a:outside-section-334, f:hurt-caused" == Just "SFE025")
  check "technical output reference must exist and match its type"
    (invalidSource "final_rule r:section323-candidate"
      "final_rule r:unknown" == Just "SFE020")
  check "unknown scope acknowledgement rejected"
    (invalidScenario "assume a:outside-section-334;"
      "assume a:invented;" == Just "SFE023")
  check "duplicate scope acknowledgement rejected"
    (invalidScenario "assume a:outside-section-334;"
      "assume a:outside-section-334;\n  assume a:outside-section-334;" == Just "SFE024")
  check "malformed source fails without request bytes"
    (errorCode (compileSource modelPath "model broken {" Nothing) == Just "SFE001")
  putStrLn "legal surface: 12 technical scenarios, 3 missing-scope cases, typed graph and explanation snapshots passed"

check :: String -> Bool -> IO ()
check label success = unless success (putStrLn ("legal surface failed: " <> label) >> exitFailure)

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
  pure (status, reason)

requestShape :: BS.ByteString -> Bool
requestShape bytes = case decodeJson bytes of
  Left _ -> False
  Right request ->
    let facts = lookupField "facts" request >>= objectFields
        registry = lookupField "registry" request >>= arrayValue
        factIds = maybe [] (map fst) facts
        offence = do
          rows <- registry
          case rows of item:_ -> Just item; [] -> Nothing
        exceptions = offence >>= lookupField "exceptions" >>= arrayValue
        exceptionBinding = do
          rows <- exceptions
          case rows of item:_ -> Just item; [] -> Nothing
        burdenFor key = do
          rows <- facts
          binding <- lookup key rows
          lookupField "burden" binding
    in lookupField "fragment" request == Just (JStr "SuppliedProofStatus-v1")
      && length factIds == 13
      && Set.null (Set.filter (Text.isPrefixOf "a:") (Set.fromList factIds))
      && maybe False ((== 2) . length) registry
      && (exceptionBinding >>= lookupField "effect") == Just (JStr "defeat")
      && burdenFor "f:act-performed" == Nothing
      && burdenFor "f:unsoundness-time" /= Nothing
      && Map.size (Map.fromList [(key, ()) | key <- factIds]) == 13
