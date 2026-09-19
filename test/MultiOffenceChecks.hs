{-# LANGUAGE OverloadedStrings #-}
module MultiOffenceChecks (runMultiOffenceChecks) where

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

runMultiOffenceChecks :: FilePath -> IO ()
runMultiOffenceChecks root = do
  let base = root </> "research/singapore/section-84-pilot/multi-offence"
      modelPath = base </> "section323-section379-with-section84.yh"
      scenarioPath name = base </> "scenarios" </> name <> ".yh"
  modelSource <- BS.readFile modelPath
  check "one typed general exception and two explicit attachments" $ case
      checkSource modelPath modelSource Nothing of
    Right (Checked model Nothing [] _ (Just _)) -> case modelBody model of
      MultiLegal scopes offences exceptions attachments outputs ->
        length scopes == 4 && length offences == 2 && length exceptions == 1
          && length attachments == 2 && length outputs == 6
          && all ((== OffenceKind) . ruleKind) offences
          && map (map (tokenText . sectionToken) . ruleSections) offences
            == [["319","321","323"],["378","379"]]
          && case exceptions of
            [GeneralException item] -> ruleKind item == ExceptionKind
              && ruleTarget item == Nothing
              && map (tokenText . sectionToken) (ruleSections item) == ["84"]
              && length (ruleElements item) == 8
            _ -> False
      _ -> False
    _ -> False
  let positive =
        [("01_hurt_satisfied", "satisfied", "satisfied", "o:voluntary-hurt")
        ,("02_hurt_nature", "not_satisfied", "defeated", "o:voluntary-hurt")
        ,("03_hurt_knowledge", "satisfied", "satisfied", "o:voluntary-hurt")
        ,("04_hurt_unresolved", "unresolved", "requirements_unresolved", "o:voluntary-hurt")
        ,("05_theft_satisfied", "satisfied", "satisfied", "o:theft")
        ,("06_theft_nature", "not_satisfied", "defeated", "o:theft")
        ,("07_theft_control", "not_satisfied", "defeated", "o:theft")
        ,("08_theft_wrongfulness", "not_satisfied", "defeated", "o:theft")
        ,("09_theft_not_movable", "not_satisfied", "requirements_not_satisfied", "o:theft")
        ,("10_theft_consent", "not_satisfied", "requirements_not_satisfied", "o:theft")
        ,("11_theft_dishonesty", "not_satisfied", "requirements_not_satisfied", "o:theft")
        ,("12_theft_movement_unresolved", "unresolved", "requirements_unresolved", "o:theft")]
  forM_ positive $ \(name, expectedStatus, expectedReason, target) -> do
    scenario <- BS.readFile (scenarioPath name)
    let supplied = Just (scenarioPath name, scenario)
    case (checkSource modelPath modelSource supplied,
          compileSource modelPath modelSource supplied) of
      (Right checked, Right request) -> do
        check (name <> " compiles deterministically")
          (compileSource modelPath modelSource supplied == Right request)
        check (name <> " evaluates the selected technical branch")
          (responsePair (runLine request) == Just (expectedStatus, expectedReason))
        check (name <> " excludes the other offence and scope facts")
          (requestIsolated target request)
        case explainChecked modelPath checked of
          Left _ -> check (name <> " Haskell explanation exists") False
          Right explanation -> do
            check (name <> " names selected attachment and stable support")
              (("Selected candidate offence: " <> target) `Text.isInfixOf` explanation
              && ("Attachment: s 84 -> candidate " <> target) `Text.isInfixOf` explanation
              && "Definition instance: shared x:section84" `Text.isInfixOf` explanation
              && "f:ordinary-wrongfulness-incapacity -> q:ordinary + q:wrong-operator"
                 `Text.isInfixOf` explanation
              && "No guilt, conviction, acquittal or sentence was determined."
                 `Text.isInfixOf` explanation)
            if name == "06_theft_nature" then do
              snapshot <- BS.readFile (base </> "snapshots/06_theft_nature.txt")
              check "theft explanation canonical plain-text snapshot"
                (Encoding.encodeUtf8 explanation == snapshot)
            else pure ()
      _ -> check (name <> " checks and compiles") False
  let refusals =
        [("13_missing_target", "SFE036")
        ,("14_unknown_target", "SFE038")
        ,("15_multiple_targets", "SFE037")
        ,("16_missing_theft_scope", "SFE022")
        ,("17_unselected_assignment", "SFE039")]
  forM_ refusals $ \(name, expected) -> do
    scenario <- BS.readFile (scenarioPath name)
    check (name <> " rejects with source-located diagnostic") $ case
        compileSource modelPath modelSource (Just (scenarioPath name, scenario)) of
      Left issue -> diagnosticCode issue == expected
        && diagnosticPath issue == scenarioPath name
        && tokenLine (diagnosticToken issue) > 0
        && tokenColumn (diagnosticToken issue) > 0
      Right _ -> False
  theft <- BS.readFile (scenarioPath "05_theft_satisfied")
  let badModel old new = errorCode (checkSource modelPath
        (replace old new modelSource) Nothing)
      badScenario old new = errorCode (compileSource modelPath modelSource
        (Just (scenarioPath "05_theft_satisfied", replace old new theft)))
      attachment = "  attach x:section84 to o:theft;"
      exceptionBlock = Text.takeWhile (/= '\0') $ snd $ Text.breakOn
        "  general-exception x:section84" (Encoding.decodeUtf8 modelSource)
      duplicateException = Text.takeWhile (/= '\0')
        (fst (Text.breakOn "  attach x:section84" exceptionBlock))
  check "unknown general exception" (badModel attachment
    "  attach x:unknown to o:theft;" == Just "SFE044")
  check "unknown candidate offence" (badModel attachment
    "  attach x:section84 to o:unknown;" == Just "SFE033")
  check "element cannot be attachment target" (badModel attachment
    "  attach x:section84 to f:movable-property;" == Just "SFE034")
  check "private group cannot be attachment target" (badModel attachment
    "  attach x:section84 to g:theft-requirements;" == Just "SFE034")
  check "duplicate attachment" (badModel attachment
    (attachment <> "\n" <> attachment) == Just "SFE035")
  check "unattached exception cannot defeat theft" (badModel attachment "" == Nothing
    && errorCode (compileSource modelPath (replace attachment "" modelSource)
      (Just (scenarioPath "05_theft_satisfied", theft))) == Just "SFE040")
  check "private offence graph cannot read another offence leaf"
    (badModel "(f:movable-property, f:another-possession"
      "(f:hurt-caused, f:another-possession" == Just "SFE045")
  check "duplicate general exception"
    (badModel "  attach x:section84 to o:voluntary-hurt;"
      (duplicateException <> "\n  attach x:section84 to o:voluntary-hurt;")
      == Just "SFE043")
  check "missing target-specific classification" (badScenario
    "  f:movable-property = proved;\n" "" == Just "SFE042")
  check "statutory section references are checked contextual metadata"
    (badModel "sections 378,379" "sections 378,unknown" == Just "SFE031")
  check "unselected scope acknowledgement is rejected"
    (badScenario "  assume a:dishonesty-externally-classified;"
      "  assume a:outside-section-334;" == Just "SFE023")
  check "scenario cannot add attachment" (badScenario
    "  analyse o:theft;" "  analyse o:theft;\n  attach x:section84 to o:theft;"
    == Just "SFE001")
  putStrLn "multi-offence surface: 12 selected technical cases, 5 scenario refusals and attachment/privacy diagnostics passed"

sectionToken :: StatutorySection -> Token
sectionToken (StatutorySection item) = item

check :: String -> Bool -> IO ()
check label success = unless success (putStrLn ("multi-offence failed: " <> label) >> exitFailure)

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

requestIsolated :: Text -> BS.ByteString -> Bool
requestIsolated target bytes = case decodeJson bytes of
  Left _ -> False
  Right request ->
    let bindings = maybe [] id (lookupField "facts" request >>= objectFields)
        facts = map fst bindings
        registry = maybe [] id (lookupField "registry" request >>= arrayValue)
        root = lookupField "root_rule" request >>= textValue
        other = if target == "o:theft" then "f:hurt-caused" else "f:movable-property"
        candidateLeaf = if target == "o:theft" then "f:movable-property" else "f:hurt-caused"
        wanted = if target == "o:theft" then "r:section379-candidate"
          else "r:section323-candidate"
        exceptionBurden = lookup "f:unsoundness-time" bindings >>= lookupField "burden"
        candidateBurden = lookup candidateLeaf bindings >>= lookupField "burden"
    in length registry == 2 && length facts == (if target == "o:theft" then 14 else 13)
      && other `notElem` facts && all (not . Text.isPrefixOf "a:") facts
      && exceptionBurden /= Nothing && candidateBurden == Nothing
      && root == Just wanted
      && not (BS.isInfixOf (Encoding.encodeUtf8 other) bytes)
