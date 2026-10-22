{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
-- | Opt-in control envelope. Child commands are this executable's existing CLI;
-- no parser, lowering, evaluator or renderer is duplicated here.
module Yuho.Machine (runMachine) where

import Control.Exception (IOException, try)
import Control.Monad (unless, when)
import qualified Data.Aeson as A
import qualified Data.Aeson.Key as K
import qualified Data.Aeson.KeyMap as KM
import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as BL
import Data.List (nub)
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import System.Directory (makeAbsolute)
import System.Environment (getExecutablePath)
import System.Exit (ExitCode(..), exitFailure)
import System.IO (stdin, stdout, stderr)
import System.Posix.Files (getSymbolicLinkStatus, isRegularFile, fileSize)
import System.Process (readProcessWithExitCode)
import qualified Yuho.Authoring as SDK
import qualified Yuho.Protocol.Json as Strict

requestVersion, responseVersion :: Text
requestVersion = "yuho.machine-request/v0.1-experimental"
responseVersion = "yuho.machine-response/v0.1-experimental"

data Request = Request Text Text FilePath [(Text,Text)]

runMachine :: [String] -> IO ()
runMachine ["--help"] = BS.hPut stdout
  "usage: yuho machine REQUEST.json | yuho machine - (one JSON request on stdin); see docs/machine-interface.md\n"
runMachine args = do
  bytes <- case args of
    ["-"] -> BS.hGet stdin 65537
    [path] -> readBounded 65536 path >>= either (bad Nothing "SMIO" "/" . T.pack) pure
    _ -> bad Nothing "SMREQUEST" "/" "expected machine REQUEST.json or machine -"
  value <- either (bad Nothing "SMJSON" "/") pure (Strict.decodeJson bytes)
  when (BS.length bytes > 65536) (bad Nothing "SMLIMIT" "/" "control request exceeds 65536 bytes")
  req <- either (\(field,message) -> bad Nothing "SMREQUEST" field message) pure (parseRequest value)
  let Request kind op path fields = req
  absolute <- traverse (\(key,v) -> if key `elem` ["scenario","output","against"]
    then (,) key . T.pack <$> makeAbsolute (T.unpack v) else pure (key,v)) fields
  input <- makeAbsolute path
  let selected = Request kind op input absolute
  if kind == "computed-input-json" && op == "check"
    then checkArtifact selected
    else delegate selected

parseRequest :: Strict.J -> Either (Text,Text) Request
parseRequest value = do
  pairs <- case value of Strict.JObj xs -> Right xs; _ -> Left ("/","expected closed request object")
  let get field = case lookup field pairs of
        Just (Strict.JStr t) | not (T.null (T.strip t)) && not (T.any (=='\0') t) -> Right t
        _ -> Left ("/"<>field,"required nonempty string")
  version <- get "format"
  unless (version == requestVersion) (Left ("/format","unsupported version "<>version<>"; expected "<>requestVersion))
  kind <- get "input_kind"; op <- get "operation"; path <- get "path"
  (optional,required) <- case (kind,op) of
    ("native-yh","inspect") -> Right (["scenario","stage"],[])
    ("native-yh",x) | x `elem` ["check","compile","run"] -> Right (["scenario"],[])
    ("native-yh","diagram") -> Right (["scenario"],["output","view","encoding"])
    ("composition-yh","check") -> Right (["against"],[])
    ("composition-yh","run") -> Right ([],["output"])
    ("computed-input-json","check") -> Right ([],[])
    ("computed-input-json","replay") -> Right ([],["output"])
    _ -> Left ("/operation","unsupported input_kind/operation pair; no implicit profile translation")
  let allowed=["format","input_kind","operation","path"]++optional++required
  case [key | (key,_)<-pairs,key `notElem` allowed] of
    key:_ -> Left ("/"<>key,"unknown or inapplicable field")
    [] -> pure ()
  mapM_ get required
  extras <- traverse (\key -> (,) key <$> get key) [key | (key,_)<-pairs,key `elem` optional++required]
  mapM_ (\(key,choices) -> case lookup key extras of
    Just v | v `notElem` choices -> Left ("/"<>key,"unsupported value "<>v)
    _ -> Right ()) [("stage",["all","parsed","checked","normalized","lowered"])
      ,("view",["rule","modules","case","trace"]),("encoding",["json","xml","svg"])]
  pure (Request kind op (T.unpack path) extras)

-- Errors on the control boundary carry a JSON pointer, not a fabricated .yh span.
bad :: Maybe Request -> Text -> Text -> Text -> IO a
bad req code location message = do
  emit req False A.Null [] [A.object ["code" A..= code,"location" A..= location,"message" A..= message]] []
  exitFailure

readBounded :: Int -> FilePath -> IO (Either String BS.ByteString)
readBounded limit path = do
  result <- try $ do
    stat <- getSymbolicLinkStatus path
    unless (isRegularFile stat && fileSize stat <= fromIntegral limit)
      (ioError (userError "expected regular non-symlink file within byte limit"))
    bytes <- BS.readFile path
    when (BS.length bytes > limit) (ioError (userError "file exceeds byte limit"))
    pure bytes
  pure $ case result of
    Left (e :: IOException) -> Left (show e)
    Right b -> Right b

checkArtifact :: Request -> IO ()
checkArtifact req@(Request _ _ path _) = do
  bytes <- readBounded 1048576 path >>= either (bad (Just req) "SMIO" "/path" . T.pack) pure
  doc <- case SDK.decodeComputedInputDocument bytes of
    Left d -> emit (Just req) False A.Null [] [A.toJSON d] [] >> exitFailure
    Right d -> pure d
  let ds = SDK.validateComputedInput doc
      profiles = ["TypedFiniteRules-v1",SDK.destinationProfile (SDK.computedDestination doc)]
  emit (Just req) (null ds) (A.object ["status" A..= ("checked"::Text),"evaluated" A..= False
    ,"binding" A..= SDK.computedBinding doc]) profiles (map A.toJSON ds) []
  unless (null ds) exitFailure

delegate :: Request -> IO ()
delegate req@(Request kind op path fields) = do
  executable <- getExecutablePath
  let flags=[T.unpack flag | (key,v)<-fields,flag<-["--"<> (if key=="encoding" then "format" else key),v]]
      command = (if kind=="native-yh" then [T.unpack op,path] else ["compose",T.unpack op,path]) ++ flags
  executed <- try (readProcessWithExitCode executable command "")
  (status,out,err) <- case executed of
    Left (e :: IOException) -> bad (Just req) "SMIO" "/" (T.pack (show e))
    Right x -> pure x
  let parse text = A.eitherDecodeStrict' (UTF8.encodeUtf8 (T.pack text)) :: Either String A.Value
      diagnostics = case parse err of Right d -> [d]; Left _ -> []
      success = status == ExitSuccess
  when (not (null err) && null diagnostics) (BS.hPut stderr (UTF8.encodeUtf8 (T.pack err)))
  payload <- if null out then pure A.Null else case parse out of
    Right v -> pure v
    Left _ -> bad (Just req) "SMCONTRACT" "/payload" "native command did not return structured JSON"
  let exports = case lookup "output" fields of
        Nothing -> []
        Just p | kind=="native-yh" -> [A.object ["path" A..= p,"contract" A..= ("simplified-semantic-graph"::Text)]]
        Just p -> [A.object ["directory" A..= p,"contract" A..= ("complete-computed-projection-and-reference-views"::Text)
          ,"files" A..= (["artifact.json","report.json","projection.json","view-bindings.json","view.json","view.xml","view.svg","source-map.json"]::[Text])]]
  emit (Just req) success payload (profilesIn payload) diagnostics (if success then exports else [])
  unless success exitFailure

-- Only report profiles actually present in the payload, never infer truth or
-- observation categories from a label. Native check may not report a profile.
profilesIn :: A.Value -> [Text]
profilesIn value = nub (go value)
  where
    known=["SuppliedProofStatus-v1","TypedFiniteRules-v1","RegisteredPresumptionDerivations-v1"
      ,"PenaltySelection-v1","Core-v1","ExceptionOverride-v1","TypedLeaves-v1","Terms-v1"]
    go (A.Object x) = concat
      [case valueAtKey of
         A.String t | K.toText key `elem` ["fragment","destinationProfile","profile","evaluator"] && t `elem` known -> [t]
         _ -> go valueAtKey
      | (key,valueAtKey) <- KM.toList x]
    go (A.Array xs) = concatMap go xs
    go _ = []

emit :: Maybe Request -> Bool -> A.Value -> [Text] -> [A.Value] -> [A.Value] -> IO ()
emit req success payload profiles diagnostics exports = BL.hPut stdout (A.encode (A.object
  ["format" A..= responseVersion,"success" A..= success
  ,"operation" A..= fmap (\(Request _ op _ _) -> op) req
  ,"input_kind" A..= fmap (\(Request k _ _ _) -> k) req
  ,"semantic_profiles" A..= profiles
  ,"profile_authority" A..= (if null profiles then "not_reported_by_operation" else "native_payload" :: Text)
  ,"effects" A..= effects req,"payload" A..= payload,"diagnostics" A..= diagnostics,"exports" A..= exports]) <> "\n")
  where
    effects Nothing = A.Null
    effects (Just (Request kind op _ _)) = A.object
      ["evaluation" A..= (if op=="inspect" || (kind/="native-yh" && op=="check") then "none"
          else if op `elem` ["run","replay"] then "requested" else "native_command_may_evaluate" :: Text)
      ,"source_authority" A..= (if kind=="computed-input-json" then "embedded_artifact" else "current_sources" :: Text)
      ,"writes" A..= (if op=="diagram" || (kind/="native-yh" && op `elem` ["run","replay"])
          then "new_output_only" else "none" :: Text)]
