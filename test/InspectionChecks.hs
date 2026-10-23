{-# LANGUAGE OverloadedStrings #-}
module InspectionChecks (runInspectionChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.CoreYuho.Normalize (normalizeChecked, normalizeCheckedStructure)
import Yuho.CoreYuho.Types (CoreProgram(..))
import Yuho.Protocol.Json
import Yuho.Surface.Compile (checkSource)
import Yuho.Surface.Inspect (inspectSource, inspectionVersion)
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Modules (AuthoredModel(..))
import Yuho.Surface.AST (Checked(..))
import Yuho.Surface.Token
import Yuho.Surface.TypedFinite (loadTypedFiniteProgram)

runInspectionChecks :: FilePath -> IO ()
runInspectionChecks root = do
  let proofPath = root </> "examples/synthetic/restricted_entry.yh"
      scenarioPath = root </> "examples/synthetic/scenario_all_proved.yh"
      typedPath = root </> "test/fixtures/typed-authoring/permission.yh"
      typedScenarioPath = root </> "test/fixtures/typed-authoring/permission.yhs"
      presumptionPath = root </> "examples/synthetic/presumption_active.yh"
  proof <- BS.readFile proofPath
  scenario <- BS.readFile scenarioPath
  typed <- BS.readFile typedPath
  typedScenario <- BS.readFile typedScenarioPath
  presumption <- BS.readFile presumptionPath
  let cases = [(proofPath,proof,Just (scenarioPath,scenario),["parsed","checked","normalized","lowered"])
              ,(typedPath,typed,Just (typedScenarioPath,typedScenario),["parsed","checked","lowered"])
              ,(presumptionPath,presumption,Nothing,["parsed","lowered","checked"])]
  forM_ cases $ \(path,source,supplied,order) -> do
    inspected <- inspectSource "all" path source supplied >>= right "inspect all"
    repeated <- inspectSource "all" path source supplied >>= right "deterministic replay"
    check "version and no evaluation" (lookupField "format" inspected == Just (JStr inspectionVersion)
      && lookupField "evaluated" inspected == Just (JBool False))
    check "deterministic serialized inspection" (encodeJson inspected == encodeJson repeated)
    check "actual stage order" (map (field "stage") (rows (field "stages" inspected)) == map JStr order)
    check "pipeline-specific lowering dependency"
      (field "depends_on" (stage "lowered" inspected) ==
        JArr [JStr (if path == presumptionPath then "parsed" else "checked")])
    if path == presumptionPath then check "presumption validation follows actual lowering"
      (field "depends_on" (stage "checked" inspected) == JArr [JStr "lowered"]) else pure ()
    forM_ order $ \name -> do
      single <- inspectSource name path source supplied >>= right "selected stage"
      check "selected stage equals all-stage record" (field "stages" single == JArr [stage name inspected])
    let mappings = rows (field "mappings" (field "data" (stage "lowered" inspected)))
    check "nonempty source mappings" (not (null mappings))
    forM_ mappings $ \mapping -> do
      check "original source starts retained" (field "extent" (field "authored" mapping) == JStr "token_start_only")
      check "original source offset nonnegative" (case field "byte_offset" (field "authored" mapping) of
        JNum n -> n >= 0; _ -> False)
  proofAll <- inspectSource "all" proofPath proof (Just (scenarioPath,scenario)) >>= right "proof stages"
  frozen <- BS.readFile (root </> "examples/synthetic/request.json") >>= right "frozen request" . decodeJson
  check "lowered request equals independently retained request"
    (field "request" (field "data" (stage "lowered" proofAll)) == frozen)
  checked@(Checked model _ _ _ _) <- right "proof checked" (checkSource proofPath proof (Just (scenarioPath,scenario)))
  let authored = AuthoredModel model Nothing [] [] []
      structural = normalizeCheckedStructure authored checked
      evaluated = normalizeChecked authored checked
  check "structural Core contains no computation" (Map.null (coreProgramRuleStatuses structural)
    && Map.null (coreProgramBranchReasons structural))
  check "structural normalization preserves existing Core"
    (evaluated { coreProgramRuleStatuses = Map.empty, coreProgramBranchReasons = Map.empty
      , coreProgramObservations = Map.empty, coreProgramGuards = [] } == structural)
  parsedOnly <- inspectSource "parsed" typedPath typed Nothing
  check "parsing does not demand scenario/evaluate" (either (const False) (const True) parsedOnly)
  noNormalized <- inspectSource "normalized" typedPath typed (Just (typedScenarioPath,typedScenario))
  check "unavailable stage diagnostic" (code noNormalized == Just "SFI003")
  let cyclic = replace "trigger f:knowledge" "trigger f:no-authorization" presumption
  loweredCycle <- inspectSource "lowered" presumptionPath cyclic Nothing
  checkedCycle <- inspectSource "checked" presumptionPath cyclic Nothing
  check "registration cycle is checked after lowering, without evaluation"
    (either (const False) (const True) loweredCycle && code checkedCycle == Just "SFR004")
  unsupported <- inspectSource "all" "nested.yh" "temporal-model Unknown {}" Nothing
  check "unsupported inspection input explicit" (code unsupported == Just "SFI002")
  let badArity = replace "q:ada = permission(actor:ada,resource:r,kind:read)"
        "q:ada = permission(actor:ada,resource:r)" typed
  bad <- loadTypedFiniteProgram typedPath badArity (Just (typedScenarioPath,typedScenario))
  check "ordinary diagnostic retains declaration position and related predicate" $ case bad of
    Left issue -> diagnosticCode issue == "SFT004"
      && tokenLine (diagnosticToken issue) == 14 && tokenColumn (diagnosticToken issue) == 14
      && fmap (tokenLine . snd) (diagnosticRelated issue) == Just 12
    _ -> False
  missing <- inspectSource "checked" typedPath typed
    (Just (typedScenarioPath,replace " classify permission(actor:ada,resource:r,kind:read) as proved reason \"Independent positive tuple\";\n" "" typedScenario))
  check "missing classification is not an unresolved computation" $ case missing of
    Left issue -> diagnosticCode issue == "SFT011" && diagnosticRelated issue /= Nothing
    _ -> False
  let wrongType = replace "q:ada = permission(actor:ada,resource:r,kind:read)"
        "q:ada = permission(resource:r,resource:r,kind:read)" typed
  typeError <- inspectSource "checked" typedPath wrongType (Just (typedScenarioPath,typedScenario))
  check "type mismatch at retained declaration" (code typeError == Just "SFT005")
  unknown <- inspectSource "checked" typedPath
    (replace "q:ada = permission(actor:ada" "q:ada = absent(actor:ada" typed)
    (Just (typedScenarioPath,typedScenario))
  check "unresolved predicate diagnostic" (code unknown == Just "SFT003")
  lexed <- right "UTF-8 lexer" (lexSource "utf8.yh" (Encoding.encodeUtf8 "quote q:x \"é猫\";"))
  check "multibyte columns are bytes" (map tokenColumn lexed == [1,7,11,18,19])
  let unicode = replace "limit 2048;" "limit 2048; // é猫😀\n" typed
  unicodeView <- inspectSource "parsed" typedPath unicode Nothing >>= right "multibyte inspection"
  let tokens = rows (field "tokens" (field "data" (stage "parsed" unicodeView)))
  forM_ tokens $ \token -> case (field "byte_offset" token,field "text" token,field "kind" token) of
    (JNum offset,JStr text,JStr kind) | kind == "word" ->
      check "source byte mapping recovers exact token"
        (BS.take (BS.length (Encoding.encodeUtf8 text)) (BS.drop (fromInteger offset) unicode) == Encoding.encodeUtf8 text)
    _ -> pure ()
  putStrLn "inspection: stage isolation, exact requests, deterministic mappings and located diagnostics passed"

field :: Text -> J -> J
field key = maybe JNull id . lookupField key
rows :: J -> [J]
rows (JArr xs) = xs
rows _ = []
stage :: Text -> J -> J
stage name value = case [s | s <- rows (field "stages" value), field "stage" s == JStr name] of
  [s] -> s
  _ -> JNull
code :: Either Diagnostic a -> Maybe Text
code = either (Just . diagnosticCode) (const Nothing)
replace :: Text -> Text -> BS.ByteString -> BS.ByteString
replace a b = Encoding.encodeUtf8 . Text.replace a b . Encoding.decodeUtf8
check :: String -> Bool -> IO ()
check label ok = unless ok (putStrLn ("inspection failed: " <> label) >> exitFailure)
right :: Show e => String -> Either e a -> IO a
right label = either (\issue -> putStrLn (label <> ": " <> show issue) >> exitFailure) pure
