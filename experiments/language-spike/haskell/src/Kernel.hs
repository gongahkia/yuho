module Kernel (run, decodeFailure) where

import Control.Monad (foldM)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import qualified Data.Set as Set
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Json (J(..), encodeJson, field, object)
import Sha256 (sha256)

data Span = Span
  { spanStart :: Integer, spanEnd :: Integer
  , spanStartLine :: Integer, spanStartCol :: Integer
  , spanEndLine :: Integer, spanEndCol :: Integer
  } deriving (Eq, Show)

data Kind = Leaf | AllOf | AnyOf | Unsupported String deriving (Eq, Show)

data Requirement = Requirement
  { reqKind :: Kind, reqId :: String, reqPath :: [String], reqSpan :: Span
  , reqMembers :: [Requirement], reqPointer :: String
  } deriving (Eq, Show)

data Provision = Provision
  { provId :: String, provPath :: [String], provSpan :: Span
  , provRequirements :: [Requirement], provChildren :: [Provision]
  , provDefinitions :: Bool, provPointer :: String
  } deriving (Eq, Show)

data Diagnostic = Diagnostic
  { diagCode :: String, diagStage :: String, diagSeverity :: String, diagPath :: String
  , diagSpan :: Maybe Span, diagParameters :: [(String, String)]
  } deriving (Eq, Show)

data Input = Evaluate Provision (Map.Map String Bool) Integer
           | Validate Bool [Diagnostic]

data Trace = Trace
  { traceBranch :: String, traceId :: String, traceKind :: String
  , tracePath :: [String], traceSpan :: Span, traceValue :: Bool
  , traceChildren :: [String]
  }

data Branch = Branch
  { branchId :: String, branchPath :: [String], branchValue :: Bool
  , branchTraceIds :: [String]
  }

protocol, resultSchema, fragmentName :: String
protocol = "yuho.kernel-protocol/v1"
resultSchema = "yuho.kernel-result/v1"
fragmentName = "ClosedBooleanBranches-v1"

asString :: J -> Either String String
asString (JStr value) = Right value
asString _ = Left "expected string"

asBool :: J -> Either String Bool
asBool (JBool value) = Right value
asBool _ = Left "expected Boolean"

asInteger :: J -> Either String Integer
asInteger (JNum value) = Right value
asInteger _ = Left "expected integer"

asArray :: J -> Either String [J]
asArray (JArr value) = Right value
asArray _ = Left "expected array"

asObject :: J -> Either String [(String, J)]
asObject (JObj value) = Right value
asObject _ = Left "expected object"

named :: (J -> Either String a) -> String -> J -> Either String a
named decoder key value = field key value >>= decoder

strings :: J -> Either String [String]
strings value = asArray value >>= traverse asString

decodeSpan :: J -> Either String Span
decodeSpan value = do
  start <- named asInteger "start" value
  end <- named asInteger "end" value
  startLine <- named asInteger "start_line" value
  startCol <- named asInteger "start_col" value
  endLine <- named asInteger "end_line" value
  endCol <- named asInteger "end_col" value
  if start < 0 || end < start || startLine < 1 || endLine < startLine
     || startCol < 1 || endCol < 1
    then Left "invalid span"
    else Right (Span start end startLine startCol endLine endCol)

decodeRequirement :: String -> J -> Either String Requirement
decodeRequirement pointer value = do
  kindText <- named asString "kind" value
  identifier <- named asString "id" value
  path <- field "path" value >>= strings
  sourceSpan <- field "span" value >>= decodeSpan
  let kind = case kindText of
        "leaf" -> Leaf
        "all" -> AllOf
        "any" -> AnyOf
        _ -> Unsupported kindText
  members <- case kind of
    Leaf -> Right []
    Unsupported _ -> Right []
    _ -> do
      items <- field "members" value >>= asArray
      traverse (\(index, item) ->
        decodeRequirement (pointer ++ "/members/" ++ show index) item) (zip [0 :: Int ..] items)
  pure (Requirement kind identifier path sourceSpan members pointer)

decodeProvision :: String -> J -> Either String Provision
decodeProvision pointer value = do
  identifier <- named asString "id" value
  path <- field "path" value >>= strings
  sourceSpan <- field "span" value >>= decodeSpan
  definitions <- named asBool "definitions" value
  reqValues <- field "requirements" value >>= asArray
  requirements <- traverse (\(index, item) ->
    decodeRequirement (pointer ++ "/requirements/" ++ show index) item)
    (zip [0 :: Int ..] reqValues)
  childValues <- field "children" value >>= asArray
  children <- traverse (\(index, item) ->
    decodeProvision (pointer ++ "/children/" ++ show index) item)
    (zip [0 :: Int ..] childValues)
  pure (Provision identifier path sourceSpan requirements children definitions pointer)

decodeDiagnostic :: J -> Either String Diagnostic
decodeDiagnostic value = do
  code <- named asString "code" value
  stage <- named asString "stage" value
  severity <- named asString "severity" value
  pointer <- named asString "path" value
  sourceSpan <- field "span" value >>= \item -> case item of
    JNull -> Right Nothing
    _ -> Just <$> decodeSpan item
  parameterValue <- field "parameters" value >>= asObject
  parameters <- traverse (\(key, item) -> (,) key <$> asString item) parameterValue
  if severity /= "error" && severity /= "warning" && severity /= "info"
    then Left "invalid diagnostic severity"
    else Right (Diagnostic code stage severity pointer sourceSpan parameters)

decodeInput :: J -> Either String Input
decodeInput root = do
  schema <- named asString "input_schema" root
  fragment <- named asString "fragment" root
  if schema /= "yuho.kernel-input/v1" || fragment /= fragmentName
    then Left "unsupported input schema or fragment"
    else pure ()
  source <- field "source" root
  sourceText <- named asString "text" source
  sourceHash <- named asString "sha256" source
  _ <- named asString "path" source
  if sha256 (Encoding.encodeUtf8 (Text.pack sourceText)) /= sourceHash
    then Left "source SHA-256 mismatch"
    else pure ()
  policy <- field "policy" root
  _ <- named asString "reference_date" policy
  maxNodes <- named asInteger "max_nodes" policy
  if maxNodes < 1 || maxNodes > 1024 then Left "invalid max_nodes" else pure ()
  operation <- named asString "operation" root
  case operation of
    "evaluate" -> do
      program <- field "program" root >>= decodeProvision "/program"
      factValues <- field "facts" root >>= asObject
      facts <- traverse (\(key, item) -> (,) key <$> asBool item) factValues
      pure (Evaluate program (Map.fromList facts) maxNodes)
    "validate" -> do
      parserResult <- field "parser_result" root
      accepted <- named asBool "accepted" parserResult
      _ <- named asString "source_version" parserResult
      diagnosticValues <- field "diagnostics" parserResult >>= asArray
      diagnostics <- traverse decodeDiagnostic diagnosticValues
      pure (Validate accepted diagnostics)
    _ -> Left "unsupported operation"

spanJson :: Span -> J
spanJson value = object
  [ ("start", JNum (spanStart value)), ("end", JNum (spanEnd value))
  , ("start_line", JNum (spanStartLine value)), ("start_col", JNum (spanStartCol value))
  , ("end_line", JNum (spanEndLine value)), ("end_col", JNum (spanEndCol value))
  ]

diagnosticJson :: Diagnostic -> J
diagnosticJson value = object
  [ ("code", JStr (diagCode value)), ("stage", JStr (diagStage value))
  , ("severity", JStr (diagSeverity value)), ("path", JStr (diagPath value))
  , ("span", maybe JNull spanJson (diagSpan value))
  , ("parameters", object [(key, JStr item) | (key, item) <- diagParameters value])
  ]

makeDiagnostic :: String -> String -> String -> Maybe Span -> [(String, String)] -> Diagnostic
makeDiagnostic code stage pointer sourceSpan parameters =
  Diagnostic code stage "error" pointer sourceSpan parameters

validateProgram :: Integer -> Map.Map String Bool -> Provision -> Either Diagnostic ()
validateProgram maxNodes facts root = do
  let nodes = allNodes root
  if toInteger (length nodes) > maxNodes
    then Left (makeDiagnostic "KINV004" "validate" "/program" (Just (provSpan root)) [])
    else pure ()
  _ <- foldM checkNode Set.empty nodes
  let leaves = [(reqId item, reqSpan item) | Right item <- nodes, reqKind item == Leaf]
  mapM_ (\(identifier, sourceSpan) ->
    if Map.member identifier facts then Right ()
    else Left (makeDiagnostic "KINV001" "validate" ("/facts/" ++ identifier)
               (Just sourceSpan) [("id", identifier)])) leaves
  where
    checkNode seen node = case node of
      Left provision ->
        if Set.member (provId provision) seen
          then Left (makeDiagnostic "KINV002" "validate"
                     (provPointer provision ++ "/id") (Just (provSpan provision))
                     [("id", provId provision)])
          else Right (Set.insert (provId provision) seen)
      Right requirement -> case reqKind requirement of
        Unsupported kind ->
          Left (makeDiagnostic "KCAP001" "capability"
                (reqPointer requirement ++ "/kind") (Just (reqSpan requirement))
                [("kind", kind)])
        _ | Set.member (reqId requirement) seen ->
              Left (makeDiagnostic "KINV002" "validate"
                    (reqPointer requirement ++ "/id") (Just (reqSpan requirement))
                    [("id", reqId requirement)])
          | reqKind requirement /= Leaf && null (reqMembers requirement) ->
              Left (makeDiagnostic "KINV004" "validate"
                    (reqPointer requirement ++ "/members") (Just (reqSpan requirement)) [])
          | otherwise -> Right (Set.insert (reqId requirement) seen)

allNodes :: Provision -> [Either Provision Requirement]
allNodes provision =
  Left provision : concatMap requirementNodes (provRequirements provision)
  ++ concatMap allNodes (provChildren provision)

requirementNodes :: Requirement -> [Either Provision Requirement]
requirementNodes value = Right value : concatMap requirementNodes (reqMembers value)

leafBranches :: Provision -> [Requirement] -> [(Provision, [Requirement])]
leafBranches provision inherited =
  let direct = inherited ++ provRequirements provision
      descendants = concatMap (\child -> leafBranches child direct) (provChildren provision)
  in if not (null descendants) then descendants
     else if null direct then [] else [(provision, direct)]

evaluateRequirement :: Map.Map String Bool -> String -> Requirement
                    -> Either Diagnostic (Bool, [Trace])
evaluateRequirement facts currentBranchId requirement =
  case reqKind requirement of
    Unsupported kind ->
      Left (makeDiagnostic "KCAP001" "capability" (reqPointer requirement ++ "/kind")
            (Just (reqSpan requirement)) [("kind", kind)])
    Leaf -> case Map.lookup (reqId requirement) facts of
      Nothing -> Left (makeDiagnostic "KINV001" "validate" ("/facts/" ++ reqId requirement)
                       (Just (reqSpan requirement)) [("id", reqId requirement)])
      Just value -> Right (value, [makeTrace value []])
    kind -> do
      evaluated <- traverse (evaluateRequirement facts currentBranchId) (reqMembers requirement)
      let values = map fst evaluated
          value = if kind == AllOf then and values else or values
          children = concatMap snd evaluated
      Right (value, makeTrace value (map reqId (reqMembers requirement)) : children)
  where
    makeTrace value children =
      Trace currentBranchId (reqId requirement) (kindName (reqKind requirement))
        (reqPath requirement) (reqSpan requirement) value children

kindName :: Kind -> String
kindName Leaf = "leaf"
kindName AllOf = "all"
kindName AnyOf = "any"
kindName (Unsupported name) = name

evaluateBranch :: Map.Map String Bool -> (Provision, [Requirement])
               -> Either Diagnostic (Branch, [Trace])
evaluateBranch facts (provision, requirements) = do
  evaluated <- traverse (evaluateRequirement facts (provId provision)) requirements
  let value = and (map fst evaluated)
      trace = concatMap snd evaluated
  Right (Branch (provId provision) (provPath provision) value (map traceId trace), trace)

boolName :: Bool -> String
boolName True = "true"
boolName False = "false"

branchJson :: Branch -> J
branchJson branch = object
  [ ("id", JStr (branchId branch)), ("path", JArr (map JStr (branchPath branch)))
  , ("status", JStr (boolName (branchValue branch)))
  , ("trace_ids", JArr (map JStr (branchTraceIds branch)))
  ]

traceJson :: Trace -> J
traceJson trace = object
  [ ("branch", JStr (traceBranch trace)), ("id", JStr (traceId trace))
  , ("kind", JStr (traceKind trace)), ("path", JArr (map JStr (tracePath trace)))
  , ("span", spanJson (traceSpan trace)), ("value", JStr (boolName (traceValue trace)))
  , ("children", JArr (map JStr (traceChildren trace)))
  ]

innerDigest :: J -> String
innerDigest root =
  let operation = named asString "operation" root
      keys = case operation of
        Right "validate" -> ["input_schema","fragment","source","parser_result","policy"]
        _ -> ["input_schema","fragment","source","program","facts","policy"]
      pairs = traverse (\key -> (,) key <$> field key root) keys
  in case pairs of
    Left _ -> sha256 BS.empty
    Right values -> sha256 (Encoding.encodeUtf8 (Text.pack (encodeJson (object values))))

baseResult :: String -> String -> String -> String -> [Branch] -> [Trace] -> [Diagnostic] -> J
baseResult requestId digestValue status kind branches traces diagnostics = object
  [ ("protocol", JStr protocol), ("request_id", JStr requestId)
  , ("result_schema", JStr resultSchema), ("fragment", JStr fragmentName)
  , ("input_digest", JStr digestValue), ("status", JStr status)
  , ("provision_kind", JStr kind), ("branches", JArr (map branchJson branches))
  , ("trace", JArr (map traceJson traces))
  , ("diagnostics", JArr (map diagnosticJson diagnostics))
  ]

run :: J -> J
run root =
  let requestId = either (const "?") id (named asString "request_id" root)
      digestValue = innerDigest root
      reject = baseResult requestId digestValue "rejected" "none" [] []
      received = either (const "") id (named asString "protocol" root)
  in if received /= protocol
     then reject [makeDiagnostic "KPROT001" "protocol" "/protocol" Nothing
                   [("received", received)]]
     else case decodeInput root of
       Left message -> reject [makeDiagnostic "KDEC001" "decode" "/" Nothing
                                [("reason", message)]]
       Right (Validate accepted diagnostics) ->
         baseResult requestId digestValue (if accepted then "true" else "rejected")
           "none" [] [] diagnostics
       Right (Evaluate program facts maxNodes) ->
         case validateProgram maxNodes facts program of
           Left diagnostic -> reject [diagnostic]
           Right () ->
             case traverse (evaluateBranch facts) (leafBranches program []) of
               Left diagnostic -> reject [diagnostic]
               Right evaluated ->
                 let branches = map fst evaluated
                     traces = concatMap snd evaluated
                     kind = if null branches then "definition_only" else "executable"
                 in baseResult requestId digestValue (boolName (any branchValue branches))
                      kind branches traces []

decodeFailure :: String -> J
decodeFailure message =
  baseResult "?" (sha256 BS.empty) "rejected" "none" [] []
    [makeDiagnostic "KDEC001" "decode" "/" Nothing [("reason", message)]]
