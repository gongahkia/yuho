{-# LANGUAGE OverloadedStrings #-}
module SurfaceChecks (runSurfaceChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Protocol.Json (J(..), decodeJson, lookupField, textValue)
import Yuho.Surface.AST (Body(..), Checked(..), Model(..), Resolved(..))
import Yuho.Surface.Compile (checkSource, compileSource)
import Yuho.Surface.Token (Diagnostic(..), tokenColumn, tokenLine)

runSurfaceChecks :: FilePath -> IO ()
runSurfaceChecks root = do
  let sectionPath = root </> "research/singapore/section-84-pilot/surface/section84.yh"
      sectionFixture = root </> "research/singapore/section-84-pilot/prototype"
      syntheticPath = root </> "rewrite/frontend/fixtures/synthetic/restricted_entry.yh"
      scenarioPath = root </> "rewrite/frontend/fixtures/synthetic/scenario_all_proved.yh"
      syntheticFixture = root </> "rewrite/frontend/fixtures/synthetic"
  sectionSource <- BS.readFile sectionPath
  syntheticSource <- BS.readFile syntheticPath
  scenario <- BS.readFile scenarioPath
  sectionRequest <- BS.readFile (sectionFixture </> "request.json")
  syntheticRequest <- BS.readFile (syntheticFixture </> "request.json")
  syntheticResponse <- BS.readFile (syntheticFixture </> "response.json")
  check "section 84 source parses with a located executable group" $ case checkSource sectionPath sectionSource Nothing of
    Right (Checked model _ _ (ResolvedGroup token _ _) Nothing) ->
      tokenLine token == 38 && tokenColumn token > 0 && case modelBody model of
        Section _ _ _ _ _ _ _ -> True
        _ -> False
    _ -> False
  check "synthetic offence and exception are distinct typed declarations" $ case
      checkSource syntheticPath syntheticSource (Just (scenarioPath, scenario)) of
    Right (Checked model _ _ (ResolvedGroup _ _ _) (Just (ResolvedGroup _ _ _))) ->
      case modelBody model of
        Synthetic _ _ _ -> True
        _ -> False
    _ -> False
  let compiledSection = compileSource sectionPath sectionSource Nothing
      compiledSynthetic = compileSource syntheticPath syntheticSource (Just (scenarioPath, scenario))
  check "section 84 exact 7599 bytes and frozen SHA-256" $
    compiledSection == Right sectionRequest && BS.length sectionRequest == 7599
      && sha256Text sectionRequest == "1ebe4d4fdd3de643e938c512fafd1c68ed437728b1249d32b6a236639a58d6e2"
      && not (BS.isSuffixOf "\n" sectionRequest)
  check "synthetic v0.1 exact frozen request and response" $
    compiledSynthetic == Right syntheticRequest
      && sha256Text syntheticRequest == "2c46977bbb855fac477d85f4d8dc2581d992bb87253cc1372146fb679212a535"
      && runLine syntheticRequest == syntheticResponse
  check "compilation deterministic" $
    compiledSection == compileSource sectionPath sectionSource Nothing
      && compiledSynthetic == compileSource syntheticPath syntheticSource (Just (scenarioPath, scenario))
  let cases =
        ["X00-unclassified", "X01-nature", "X02-wrongfulness", "X03-moral-not-proved"
        ,"X04-control", "X05-unsoundness-not-proved", "X06-causation-not-proved"
        ,"X07-no-route", "X08-unresolved-premise", "X09-multiple-unresolved"
        ,"X10-proved-plus-unresolved", "X11-one-wrongfulness-component"]
  forM_ cases $ \name -> do
    expectedRequest <- BS.readFile (sectionFixture </> "fixtures/requests" </> name <> ".json")
    expectedResponse <- BS.readFile (sectionFixture </> "fixtures/snapshots" </> name <> ".json")
    let authored = scenarioVariant sectionSource expectedRequest
    check ("section 84 authored classification replay " <> name) $ case authored of
      Left _ -> False
      Right source -> case compileSource sectionPath source Nothing of
        Left _ -> False
        Right request -> request == expectedRequest && runLine request == expectedResponse
  check "invalid proof classification is source located" $
    errorCode (compileSource sectionPath
      (replace "= unresolved(not_determined);" "= asserted;" sectionSource) Nothing)
      == Just "SFE010"
  check "unknown executable reference rejected" $
    errorCode (compileSource sectionPath
      (replace "all g:nature (f:nature-causation" "all g:nature (f:unknown" sectionSource) Nothing)
      `elem` [Just "SFE003", Just "SFE006"]
  check "contextual annotation cannot become a proposition" $
    errorCode (compileSource sectionPath
      (replace "(f:nature-causation, f:nature-incapacity)" "(section107, f:nature-incapacity)" sectionSource) Nothing)
      == Just "SFE012"
  check "bad burden rejected without affecting a technical fact" $
    errorCode (compileSource sectionPath (replace "balance_of_probabilities" "beyond_reasonable_doubt" sectionSource) Nothing)
      == Just "SFE011"
  check "malformed UTF-8 rejected" $
    errorCode (compileSource sectionPath (sectionSource <> BS.pack [255]) Nothing) == Just "SFE001"
  check "unsupported module syntax rejected" $
    errorCode (compileSource sectionPath "language YuhoSurface-v0.2;" Nothing) == Just "SFE001"
  check "limitations remain non-executable" $
    compileSource syntheticPath (replace "Not legal advice;" "Not a judicial output;" syntheticSource)
      (Just (scenarioPath, scenario)) == compiledSynthetic
  putStrLn "surface: frozen requests, 12 authored section 84 response replays, and negative cases passed"

check :: String -> Bool -> IO ()
check label success = unless success (putStrLn ("surface failed: " <> label) >> exitFailure)

replace :: Text -> Text -> BS.ByteString -> BS.ByteString
replace old new = Encoding.encodeUtf8 . Text.replace old new . Encoding.decodeUtf8

errorCode :: Either Diagnostic a -> Maybe Text
errorCode (Left issue) = Just (diagnosticCode issue)
errorCode (Right _) = Nothing

scenarioVariant :: BS.ByteString -> BS.ByteString -> Either Text BS.ByteString
scenarioVariant source fixture = do
  value <- decodeJson fixture
  requestId <- maybe (Left "missing request ID") Right (lookupField "request_id" value >>= textValue)
  facts <- case lookupField "facts" value of
    Just (JObj rows) -> Right rows
    _ -> Left "missing facts"
  assignments <- traverse row facts
  let original = Encoding.decodeUtf8 source
      (prefix, rest) = Text.breakOn "  proof_assignments {" original
      (_, suffix) = Text.breakOn "  limitations {" rest
  if Text.null rest || Text.null suffix then Left "source assignment block missing"
  else pure (Encoding.encodeUtf8
    (Text.replace "request X00;" ("request " <> requestId <> ";") prefix
      <> "  proof_assignments {\n" <> Text.concat assignments <> "  }\n\n" <> suffix))
  where
    row (name, item) = do
      status <- maybe (Left "missing proof status") Right (lookupField "proof_status" item)
      kind <- maybe (Left "missing proof kind") Right (lookupField "kind" status >>= textValue)
      let reason = lookupField "reason" status >>= textValue
      pure ("    " <> name <> " = " <> kind
        <> maybe "" (\value -> "(" <> value <> ")") reason <> ";\n")
