{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.CLI (main) where

import Control.Exception (IOException, finally, try)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text.Encoding as Encoding
import System.Directory (doesDirectoryExist, removeFile)
import System.Environment (getArgs)
import System.Exit (exitFailure)
import System.FilePath (takeDirectory)
import System.IO (IOMode(ReadMode), hClose, openBinaryTempFile, stderr, stdout, withBinaryFile)
import System.Posix.Files (createLink, fileSize, getSymbolicLinkStatus, isRegularFile)
import Yuho.Kernel.Run (runLine)
import qualified Yuho.Corpus as Corpus
import Yuho.CoreYuho.Normalize (normalizeCase, normalizeChecked, normalizePresumption)
import Yuho.Diagram.Build
  ( caseGraph, presumptionGraph, programGraph, typedFiniteGraph, typedFiniteCaseGraph )
import Yuho.Diagram.Encode (encodeSemanticGraph, encodeSvg)
import Yuho.Diagram.Types (DiagramFormat(..), DiagramView(..), SemanticGraph)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, textValue)
import Yuho.Release
  ( doctorReport, initialiseProject, locateRepository, releaseName, releaseVersion
  , verifyReleaseManifest )
import Yuho.Surface.Compile (checkParsed, compileParsed)
import Yuho.Surface.AST (AnalysisCase(..), CaseAllegation(..))
import Yuho.Surface.Case
  ( caseModelFile, checkAnalysisCase, compileAnalysisCase, runAnalysisCase
  , explainAnalysisCase )
import Yuho.Surface.Explain (explainChecked)
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Modules
  ( AuthoredModel(..), authoredPrefix, loadAuthoredModel
  , validateAuthoredChecked, validateAuthoredTargets )
import Yuho.Surface.Parser (parseAnalysisCase)
import Yuho.Surface.Presumption
  ( PresumptionProgram(..), explainPresumptionProgram, loadPresumptionProgram )
import Yuho.Surface.TypedFinite
  ( TypedFiniteCase(..), TypedFiniteAllegation(..), loadTypedFiniteProgram
  , loadTypedFiniteCase, encodeTypedFiniteRequest, encodeTypedFiniteCase
  , explainTypedFinite, explainTypedFiniteCase )
import Yuho.CoreYuho.TypedFinite (evaluateTypedFinite, finiteProgramId)
import Yuho.Surface.Temporal (loadAuthoredInput)
import Yuho.Surface.Token (Diagnostic(..), Kind(..), Token(..), diagnosticJson)

data Command = Check | Compile | Run | Explain | Diagram DiagramView DiagramFormat
  deriving (Eq)
data Options = Options Command FilePath (Maybe FilePath) (Maybe FilePath)

main :: IO ()
main = do
  arguments <- getArgs
  case arguments of
    ["help"] -> BS.hPut stdout usage
    ["--help"] -> BS.hPut stdout usage
    ["--version"] -> BS.hPut stdout (Encoding.encodeUtf8
      (releaseName <> " v" <> releaseVersion <> "\n"))
    "fmt":_ -> releaseIssue
      "fmt is not available in v1 because the authoritative lexer does not preserve comments"
    "corpus":rest -> Corpus.runCorpus rest
    ["version"] -> BS.hPut stdout (Encoding.encodeUtf8
      (releaseName <> " v" <> releaseVersion <> "\n"))
    "doctor":rest -> case rootFlag rest of
      Left message -> releaseIssue message
      Right root -> doctorReport root >>= BS.hPut stdout . (<> "\n") . encodeJson
    ["init",destination] -> initialiseProject destination >>= either releaseIssue
      (const (BS.hPut stdout "{\"status\":\"created\"}\n"))
    "release":"verify":rest -> case rootFlag rest of
      Left message -> releaseIssue message
      Right rootOption -> do
        root <- locateRepository rootOption >>= either releaseIssue pure
        verified <- verifyReleaseManifest root >>= either releaseIssue pure
        let (count,digest) = verified
        BS.hPut stdout (encodeJson (JObj
          [("status",JStr "verified"),("artifact_count",JNum (toInteger count))
          ,("manifest_sha256",JStr digest)]) <> "\n")
    _ -> case options arguments of
      Left message -> report (Diagnostic "SFE001" "<command>" origin message Nothing)
      Right selected -> operate selected
  where origin = Token EndToken "" 1 1

rootFlag :: [String] -> Either Text (Maybe FilePath)
rootFlag [] = Right Nothing
rootFlag ["--root",path] = Right (Just path)
rootFlag _ = Left "expected optional --root <path>"

releaseIssue :: Text -> IO a
releaseIssue message = report (Diagnostic "SFRL001" "<release>"
  (Token EndToken "" 1 1) message Nothing)

options :: [String] -> Either Text Options
options arguments = case arguments of
  "diagram":path:rest -> do
    (scenario, output, view, format) <- diagramFlags rest Nothing Nothing Nothing Nothing
    selectedView <- maybe (Left "diagram requires --view rule|modules|case|trace") Right view
    selectedFormat <- maybe (Left "diagram requires --format svg|json") Right format
    destination <- maybe (Left "diagram requires --output <path>") (Right . Just) output
    Right (Options (Diagram selectedView selectedFormat) path scenario destination)
  command:path:rest -> do
    operation <- case command of
      "check" -> Right Check
      "compile" -> Right Compile
      "run" -> Right Run
      "explain" -> Right Explain
      _ -> Left "expected check, compile, run, explain, diagram, corpus, doctor, init, version or release verify"
    (scenario, output) <- flags rest Nothing Nothing
    if operation /= Compile && output /= Nothing
      then Left "--output applies only to compile"
      else Right (Options operation path scenario output)
  _ -> Left (Encoding.decodeUtf8 (BS.init usage))
  where
    flags [] scenario output = Right (scenario, output)
    flags ("--scenario":path:rest) Nothing output = flags rest (Just path) output
    flags ("--output":path:rest) scenario Nothing = flags rest scenario (Just path)
    flags _ _ _ = Left "unknown or duplicate option"
    diagramFlags [] scenario output view format = Right (scenario,output,view,format)
    diagramFlags ("--scenario":path:rest) Nothing output view format =
      diagramFlags rest (Just path) output view format
    diagramFlags ("--output":path:rest) scenario Nothing view format =
      diagramFlags rest scenario (Just path) view format
    diagramFlags ("--view":value:rest) scenario output Nothing format = do
      selected <- case value of
        "rule" -> Right RuleView
        "modules" -> Right ModulesView
        "case" -> Right CaseView
        "trace" -> Right TraceView
        _ -> Left "unknown diagram view"
      diagramFlags rest scenario output (Just selected) format
    diagramFlags ("--format":value:rest) scenario output view Nothing = do
      selected <- case value of
        "svg" -> Right SvgFormat
        "json" -> Right JsonFormat
        _ -> Left "unknown diagram format"
      diagramFlags rest scenario output view (Just selected)
    diagramFlags _ _ _ _ _ = Left "unknown or duplicate diagram option"

usage :: BS.ByteString
usage = "usage: yuho check|compile|run|explain <source.yh> [--scenario <path>] [--output <path>]; yuho diagram <source.yh> --view rule|modules|case|trace --format svg|json --output <path> [--scenario <path>]; yuho corpus ...; yuho doctor [--root <path>]; yuho init <directory>; yuho version; yuho release verify [--root <path>]\n"

readSource :: FilePath -> IO (Either Diagnostic BS.ByteString)
readSource path = do
  result <- try $ do
    status <- getSymbolicLinkStatus path
    if not (isRegularFile status) || fileSize status > 65536
      then ioError (userError "source must be a regular file at most 65536 bytes")
      else withBinaryFile path ReadMode (\handle -> BS.hGet handle 65537)
  pure $ case result of
    Left (_ :: IOException) -> Left (Diagnostic "SFE015" path origin "source unavailable, unsafe or too large" Nothing)
    Right bytes | BS.length bytes > 65536 ->
      Left (Diagnostic "SFE015" path origin "source unavailable, unsafe or too large" Nothing)
    Right bytes -> Right bytes
  where origin = Token EndToken "" 1 1

operate :: Options -> IO ()
operate (Options command path scenarioPath output) = do
  source <- readSource path
  scenario <- traverse (\item -> do
    result <- readSource item
    pure ((,) item <$> result)) scenarioPath
  case (source, scenario) of
    (Left issue, _) -> report issue
    (_, Just (Left issue)) -> report issue
    (Right bytes, other) -> do
      let supplied = case other of
            Just (Right item) -> Just item
            _ -> Nothing
      case lexSource path bytes of
        Left issue -> report issue
        Right (first:_) | tokenText first == "analysis-case" ->
          operateCase command path bytes scenarioPath output
        Right (first:_) | tokenText first == "presumption-program" ->
          operatePresumption command path bytes scenarioPath output
        Right (first:_) | tokenText first == "typed-rules-model" ->
          operateTypedFinite command path bytes supplied output
        Right (first:_) | tokenText first == "typed-rules-case" ->
          operateTypedFiniteCase command path bytes scenarioPath output
        _ -> do
          (authored,resolvedScenario) <- loadAuthoredInput path bytes supplied
            >>= either report pure
          let model = authoredModel authored
              compiled = compileParsed path model resolvedScenario
              validationPath = maybe path fst resolvedScenario
          case command of
            Check -> case checkParsed path model resolvedScenario of
              Left issue -> report issue
              Right checked -> case validateAuthoredChecked validationPath authored checked of
                Left issue -> report issue
                Right () -> BS.hPut stdout "{\"status\":\"valid\"}\n"
            Compile -> case compiled of
              Left issue -> report issue
              Right request -> case checkParsed path model resolvedScenario
                  >>= validateAuthoredChecked validationPath authored of
                Left issue -> report issue
                Right () -> case output of
                  Nothing -> BS.hPut stdout request
                  Just destination -> publish destination request
            Run -> case compiled of
              Left issue -> report issue
              Right request -> do
                case checkParsed path model resolvedScenario
                    >>= validateAuthoredChecked validationPath authored of
                  Left issue -> report issue
                  Right () -> do
                    let response = runLine request
                    case decodeJson response of
                      Right value | (lookupField "status" value >>= textValue) /= Just "rejected" ->
                        BS.hPut stdout response
                      _ -> report (Diagnostic "SFE014" path (Token EndToken "" 1 1)
                        "compiled request was rejected by the Haskell kernel" Nothing)
            Explain -> case checkParsed path model resolvedScenario of
              Left issue -> report issue
              Right checked -> case validateAuthoredChecked validationPath authored checked of
                Left issue -> report issue
                Right () -> case explainChecked path checked of
                  Left issue -> report issue
                  Right explanation -> BS.hPut stdout
                    (Encoding.encodeUtf8 (authoredPrefix authored <> explanation))
            Diagram view format -> case checkParsed path model resolvedScenario of
              Left issue -> report issue
              Right checked -> case validateAuthoredChecked validationPath authored checked of
                Left issue -> report issue
                Right () -> emitDiagram output format
                  (programGraph view (normalizeChecked authored checked))

operateCase :: Command -> FilePath -> BS.ByteString -> Maybe FilePath
  -> Maybe FilePath -> IO ()
operateCase command path bytes scenarioPath output = do
  case scenarioPath of
    Just _ -> report (Diagnostic "SFE106" path origin
      "analysis case contains its own allegation inputs" Nothing)
    Nothing -> pure ()
  declaration <- either report pure (parseAnalysisCase path bytes)
  modelPath <- either report pure (caseModelFile path declaration)
  modelBytes <- readSource modelPath >>= either report pure
  authored <- loadAuthoredModel modelPath modelBytes >>= either report pure
  let model = authoredModel authored
      AnalysisCase _ _ _ _ allegations = declaration
  either report pure (validateAuthoredTargets path authored
    [target | CaseAllegation _ _ target _ _ _ <- allegations])
  checked <- either report pure (checkAnalysisCase path declaration modelPath model)
  case command of
    Check -> BS.hPut stdout "{\"kind\":\"analysis-case\",\"status\":\"valid\"}\n"
    Compile -> do
      request <- either report pure (compileAnalysisCase checked)
      case output of
        Nothing -> BS.hPut stdout request
        Just destination -> publish destination request
    Run -> either report (BS.hPut stdout) (runAnalysisCase checked)
    Explain -> either report (BS.hPut stdout . Encoding.encodeUtf8
      . (authoredPrefix authored <>)) (explainAnalysisCase modelPath checked)
    Diagram view format -> if view `notElem` [CaseView,TraceView] then report
      (Diagnostic "SFD001" path origin "analysis case requires --view case or trace" Nothing)
      else emitDiagram output format (caseGraph view (normalizeCase authored checked))
  where origin = Token EndToken "" 1 1

operatePresumption :: Command -> FilePath -> BS.ByteString -> Maybe FilePath
  -> Maybe FilePath -> IO ()
operatePresumption command path bytes scenarioPath output = do
  case scenarioPath of
    Just _ -> report (Diagnostic "SFR001" path origin
      "presumption program names its own base scenario" Nothing)
    Nothing -> pure ()
  program <- loadPresumptionProgram path bytes >>= either report pure
  case command of
    Check -> BS.hPut stdout "{\"kind\":\"presumption-program\",\"status\":\"valid\"}\n"
    Compile -> case output of
      Nothing -> BS.hPut stdout (presumptionRequest program)
      Just destination -> publish destination (presumptionRequest program)
    Run -> BS.hPut stdout (presumptionResult program)
    Explain -> either report (BS.hPut stdout . Encoding.encodeUtf8)
      (explainPresumptionProgram program)
    Diagram view format -> if view /= TraceView then report
      (Diagnostic "SFD001" path origin "presumption program requires --view trace" Nothing)
      else emitDiagram output format
        (presumptionGraph (normalizePresumption program))
  where origin = Token EndToken "" 1 1

operateTypedFinite :: Command -> FilePath -> BS.ByteString
  -> Maybe (FilePath,BS.ByteString) -> Maybe FilePath -> IO ()
operateTypedFinite command path bytes scenario output = do
  program <- loadTypedFiniteProgram path bytes scenario >>= either report pure
  result <- either (report . issue) pure (evaluateTypedFinite program)
  let request = encodeTypedFiniteRequest (finiteProgramId program <> "-request") program
  case command of
    Check -> BS.hPut stdout "{\"kind\":\"typed-finite-rules\",\"status\":\"valid\"}\n"
    Compile -> case output of
      Nothing -> BS.hPut stdout request
      Just destination -> publish destination request
    Run -> case decodeJson (runLine request) of
      Right value | (lookupField "status" value >>= textValue) == Just "evaluated" ->
        BS.hPut stdout (runLine request)
      _ -> report (issue "typed finite request was rejected by the Haskell kernel")
    Explain -> BS.hPut stdout (Encoding.encodeUtf8 (explainTypedFinite program result))
    Diagram view format -> if view `notElem` [RuleView,ModulesView,TraceView]
      then report (Diagnostic "SFD001" path origin
        "typed-rules model requires --view rule, modules or trace" Nothing)
      else emitDiagram output format (typedFiniteGraph view program result)
  where
    origin = Token EndToken "" 1 1
    issue message = Diagnostic "SFT011" path origin message Nothing

operateTypedFiniteCase :: Command -> FilePath -> BS.ByteString -> Maybe FilePath
  -> Maybe FilePath -> IO ()
operateTypedFiniteCase command path bytes scenario output = do
  case scenario of
    Just _ -> report (issue "typed-rules case contains its own allegation scenarios")
    Nothing -> pure ()
  declaration <- loadTypedFiniteCase path bytes >>= either report pure
  let encoded = encodeTypedFiniteCase declaration
      results = [(typedAllegationId item,typedAllegationResult item)
        | item <- typedCaseAllegations declaration]
  case command of
    Check -> BS.hPut stdout "{\"kind\":\"typed-finite-case\",\"status\":\"valid\"}\n"
    Compile -> case output of
      Nothing -> BS.hPut stdout encoded
      Just destination -> publish destination encoded
    Run -> do
      rows <- traverse runAllegation (typedCaseAllegations declaration)
      BS.hPut stdout (encodeJson (JObj
        [("kind",JStr "typed-finite-case-result"),("id",JStr (typedCaseId declaration))
        ,("allegations",JArr rows),("aggregate_status",JNull)]) <> "\n")
    Explain -> BS.hPut stdout (Encoding.encodeUtf8 (explainTypedFiniteCase declaration))
    Diagram view format -> if view `notElem` [CaseView,TraceView]
      then report (issue "typed-rules case requires --view case or trace")
      else emitDiagram output format (typedFiniteCaseGraph view (typedCaseId declaration)
        results (typedCaseShared declaration))
  where
    origin = Token EndToken "" 1 1
    issue message = Diagnostic "SFT011" path origin message Nothing
    runAllegation allegation = case decodeJson (runLine (encodeTypedFiniteRequest
        (typedAllegationId allegation <> "-request") (typedAllegationProgram allegation))) of
      Right value | (lookupField "status" value >>= textValue) == Just "evaluated" ->
        pure (JObj [("id",JStr (typedAllegationId allegation)),("result",value)])
      _ -> report (issue "typed finite allegation was rejected by the Haskell kernel")

publish :: FilePath -> BS.ByteString -> IO ()
publish destination bytes = do
  parentExists <- doesDirectoryExist (takeDirectory destination)
  if not parentExists
    then report (Diagnostic "SFE015" destination origin "output parent does not exist" Nothing)
    else do
      result <- try $ do
        (temporary, handle) <- openBinaryTempFile (takeDirectory destination) ".yuho-compile-"
        (do BS.hPut handle bytes
            hClose handle
            createLink temporary destination) `finally` do
              _ <- try (hClose handle) :: IO (Either IOException ())
              removeFile temporary
      case result of
        Left (_ :: IOException) -> report (Diagnostic "SFE015" destination origin "output is unsafe or already exists" Nothing)
        Right () -> pure ()
  where origin = Token EndToken "" 1 1

emitDiagram :: Maybe FilePath -> DiagramFormat -> SemanticGraph -> IO ()
emitDiagram destination format graph = case destination of
  Nothing -> report (Diagnostic "SFD001" "<diagram>" origin
    "diagram output path is required" Nothing)
  Just path -> publish path bytes
  where
    bytes = case format of
      SvgFormat -> encodeSvg graph
      JsonFormat -> encodeSemanticGraph graph
    origin = Token EndToken "" 1 1

report :: Diagnostic -> IO a
report issue = do
  BS.hPut stderr (encodeJson (diagnosticJson issue) <> "\n")
  exitFailure
