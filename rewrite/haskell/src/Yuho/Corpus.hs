{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Corpus
  ( Coverage(..), Provision(..), CoverageSummary(..), loadCoverage
  , validateCoverage, coverageGraph, runCorpus ) where

import Control.Exception (IOException, finally, try)
import Control.Monad (forM_, unless, when)
import Data.Aeson (FromJSON(..), eitherDecodeStrict', withObject, (.:), (.:?))
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import GHC.Generics (Generic)
import System.Directory (doesDirectoryExist, doesFileExist, removeFile)
import System.Exit (exitFailure)
import System.FilePath (isAbsolute, normalise, splitDirectories, takeDirectory, (</>))
import System.IO (IOMode(ReadMode), hClose, openBinaryTempFile, stderr, stdout, withBinaryFile)
import System.Posix.Files (createLink, fileSize, getSymbolicLinkStatus, isRegularFile)
import Yuho.Diagram.Encode (encodeSemanticGraph, encodeSvg)
import Yuho.Diagram.Types
  ( DiagramFormat(..), DiagramView(..), GraphEdge(..), GraphNode(..), SemanticGraph(..) )
import Yuho.Protocol.Json (J(..), encodeJson)

data Coverage = Coverage
  { coverageSchema :: Text
  , coverageInstrument :: Instrument
  , coverageClosedClassifications :: [Text]
  , coverageClosedGaps :: [Text]
  , coverageSummary :: CoverageSummary
  , coverageProvisions :: [Provision]
  } deriving (Eq, Show, Generic)

data Instrument = Instrument
  { instrumentId :: Text
  , instrumentTitle :: Text
  , instrumentSavedSource :: FilePath
  , instrumentSavedSourceSha256 :: Text
  , instrumentChapterBasis :: Text
  , instrumentLegalCurrency :: Text
  } deriving (Eq, Show, Generic)

data CoverageSummary = CoverageSummary
  { summaryProvisions :: Int
  , summaryByClassification :: Map Text Int
  , summaryByChapter :: Map Text Int
  , summaryByCategory :: Map Text Int
  , summaryNewFamilies :: Int
  , summaryTotalFamilies :: Int
  , summaryNewScenarios :: Int
  , summaryTotalScenarios :: Int
  , summaryTotalExceptions :: Int
  , summaryTotalPenalties :: Int
  , summaryTotalCases :: Int
  } deriving (Eq, Show, Generic)

data Provision = Provision
  { provisionInstrument :: Text
  , provisionParent :: Text
  , provisionPath :: Text
  , provisionId :: Text
  , provisionHeading :: Text
  , provisionStructuralState :: Text
  , provisionSourceReference :: FilePath
  , provisionQuotationReference :: Maybe FilePath
  , provisionCrossReferences :: [CrossReference]
  , provisionCategory :: Text
  , provisionClassification :: Text
  , provisionModels :: [FilePath]
  , provisionConstructs :: [Text]
  , provisionScenarios :: [FilePath]
  , provisionScenarioCount :: Int
  , provisionCases :: [FilePath]
  , provisionCaseCount :: Int
  , provisionDefinitionsConsumed :: [Text]
  , provisionDefinitionsExported :: [Text]
  , provisionExceptions :: [Text]
  , provisionParticipation :: Bool
  , provisionAttempt :: Bool
  , provisionPenalties :: [Text]
  , provisionTemporal :: Text
  , provisionReview :: Text
  , provisionLanguageGap :: Maybe Text
  , provisionLimitations :: [Text]
  } deriving (Eq, Show, Generic)

data CrossReference = CrossReference
  { crossKind :: Text
  , crossRaw :: Text
  , crossTarget :: Maybe Text
  , crossResolution :: Text
  } deriving (Eq, Show, Generic)

instance FromJSON Coverage where
  parseJSON = withObject "coverage" $ \value -> Coverage
    <$> value .: "schema" <*> value .: "instrument"
    <*> value .: "closed_classifications" <*> value .: "closed_language_gaps"
    <*> value .: "summary"
    <*> value .: "provisions"

instance FromJSON Instrument where
  parseJSON = withObject "instrument" $ \value -> Instrument
    <$> value .: "id" <*> value .: "title" <*> value .: "saved_source"
    <*> value .: "saved_source_sha256" <*> value .: "chapter_assignment_basis"
    <*> value .: "legal_currency"

instance FromJSON CoverageSummary where
  parseJSON = withObject "summary" $ \value -> CoverageSummary
    <$> value .: "provisions" <*> value .: "by_classification"
    <*> value .: "by_chapter" <*> value .: "by_category"
    <*> value .: "new_offence_families" <*> value .: "total_offence_families"
    <*> value .: "new_scenarios" <*> value .: "total_singapore_scenarios"
    <*> value .: "total_general_exceptions" <*> value .: "total_candidate_penalties"
    <*> value .: "total_cases"

instance FromJSON Provision where
  parseJSON = withObject "provision" $ \value -> Provision
    <$> value .: "instrument_id" <*> value .: "structural_parent"
    <*> value .: "provision_path" <*> value .: "provision_id"
    <*> value .: "heading" <*> value .: "structural_state"
    <*> value .: "source_reference" <*> value .:? "quotation_reference"
    <*> value .: "cross_references" <*> value .: "subject_category"
    <*> value .: "coverage_classification" <*> value .: "executable_model_ids"
    <*> value .: "core_constructs" <*> value .: "scenario_paths"
    <*> value .: "scenario_count" <*> value .: "case_paths"
    <*> value .: "case_count" <*> value .: "definitions_consumed"
    <*> value .: "definitions_exported" <*> value .: "general_exceptions_attached"
    <*> value .: "participation_support" <*> value .: "attempt_support"
    <*> value .: "candidate_penalties" <*> value .: "temporal_support"
    <*> value .: "review_status" <*> value .:? "language_gap" <*> value .: "limitations"

instance FromJSON CrossReference where
  parseJSON = withObject "cross-reference" $ \value -> CrossReference
    <$> value .: "kind" <*> value .: "raw" <*> value .:? "target"
    <*> value .: "resolution"

coverageRelativePath :: FilePath
coverageRelativePath = "research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json"

loadCoverage :: FilePath -> IO (Either Text (Coverage,BS.ByteString))
loadCoverage root = do
  let path = root </> coverageRelativePath
  result <- try $ do
    status <- getSymbolicLinkStatus path
    unless (isRegularFile status && fileSize status <= 4 * 1024 * 1024)
      (ioError (userError "unsafe coverage artifact"))
    withBinaryFile path ReadMode (\handle -> BS.hGet handle (4 * 1024 * 1024 + 1))
  pure $ case result of
    Left (_ :: IOException) -> Left "coverage artifact is unavailable, unsafe or too large"
    Right bytes | BS.length bytes > 4 * 1024 * 1024 -> Left "coverage artifact exceeds 4 MiB"
    Right bytes -> case eitherDecodeStrict' bytes of
      Left message -> Left ("coverage JSON is invalid: " <> Text.pack message)
      Right value -> Right (value,bytes)

validateCoverage :: FilePath -> Coverage -> IO (Either Text ())
validateCoverage root coverage = case pureChecks coverage of
  Left issue -> pure (Left issue)
  Right () -> do
    paths <- validatePaths root coverage
    pure paths

pureChecks :: Coverage -> Either Text ()
pureChecks coverage = do
  unlessE (coverageSchema coverage == "yuho.singapore-criminal-law-coverage/v0.3")
    "unsupported coverage schema"
  let rows = coverageProvisions coverage
      identifiers = map provisionId rows
      classifications = Set.fromList (coverageClosedClassifications coverage)
      gaps = Set.fromList (coverageClosedGaps coverage)
      summary = coverageSummary coverage
      countBy getter = Map.fromListWith (+) [(getter item,1 :: Int) | item <- rows]
  unlessE (not (null rows) && length identifiers == Set.size (Set.fromList identifiers))
    "duplicate or empty provision inventory"
  unlessE (summaryProvisions summary == length rows) "summary provision count mismatch"
  unlessE (summaryByClassification summary == countBy provisionClassification)
    "summary classification counts do not match provisions"
  unlessE (summaryByChapter summary == countBy provisionParent)
    "summary chapter counts do not match provisions"
  unlessE (summaryByCategory summary == countBy provisionCategory)
    "summary category counts do not match provisions"
  forM_ rows $ \row -> do
    unlessE (provisionInstrument row == instrumentId (coverageInstrument coverage))
      ("instrument mismatch at " <> provisionId row)
    unlessE (Set.member (provisionClassification row) classifications)
      ("unknown coverage classification at " <> provisionId row)
    unlessE (maybe True (`Set.member` gaps) (provisionLanguageGap row))
      ("unknown language-gap classification at " <> provisionId row)
    whenE (provisionClassification row `elem` ["executable_research","executable_partial"])
      (not (null (provisionModels row)))
      ("executable provision lacks a registered model: " <> provisionId row)
    unlessE (provisionScenarioCount row == length (provisionScenarios row))
      ("scenario count mismatch at " <> provisionId row)
    unlessE (provisionCaseCount row == length (provisionCases row))
      ("case count mismatch at " <> provisionId row)
    forM_ (provisionCrossReferences row) $ \edge -> case crossResolution edge of
      "resolved" -> case crossTarget edge of
        Just target -> unlessE (target `elem` identifiers)
          ("resolved cross-reference has unknown target: " <> target)
        Nothing -> Left "resolved cross-reference lacks target"
      "unresolved" -> unlessE (crossTarget edge == Nothing)
        "unresolved cross-reference unexpectedly has a target"
      "ambiguous" -> pure ()
      _ -> Left "unknown cross-reference resolution"
  unlessE (instrumentLegalCurrency (coverageInstrument coverage) == "not_determined")
    "coverage artifact must not claim legal currency"
  where
    unlessE condition message = if condition then Right () else Left message
    whenE condition value message = if not condition || value then Right () else Left message

validatePaths :: FilePath -> Coverage -> IO (Either Text ())
validatePaths root coverage = go allPaths
  where
    allPaths = Set.toAscList . Set.fromList $
      instrumentSavedSource (coverageInstrument coverage) : concat
        [stripAnchor (provisionSourceReference item)
          : maybe [] pure (provisionQuotationReference item)
          ++ provisionModels item ++ provisionScenarios item ++ provisionCases item
        | item <- coverageProvisions coverage]
    go [] = pure (Right ())
    go (path:rest)
      | not (safeRelative path) = pure (Left ("unsafe coverage path: " <> Text.pack path))
      | otherwise = do
          exists <- doesFileExist (root </> path)
          if exists then go rest else pure (Left ("coverage path does not exist: " <> Text.pack path))
    stripAnchor = takeWhile (/= '#')

safeRelative :: FilePath -> Bool
safeRelative path = not (null path) && not (isAbsolute path)
  && all (`notElem` ["",".."] ) (splitDirectories (normalise path))

coverageGraph :: Maybe Text -> Maybe Text -> Maybe Text -> Coverage -> Either Text SemanticGraph
coverageGraph category chapter provision coverage = do
  let rows0 = coverageProvisions coverage
      selected = case provision of
        Just identifier -> neighbourhood identifier rows0
        Nothing -> [row | row <- rows0,
          maybe True (== provisionCategory row) category,
          maybe True (== provisionParent row) chapter]
      selectedIds = Set.fromList (map provisionId selected)
      nodes = map provisionNode selected
      edges = [GraphEdge (provisionId row) target "statutory-reference" (crossRaw edge)
        | row <- selected, edge <- provisionCrossReferences row,
          Just target <- [crossTarget edge], Set.member target selectedIds]
  unlessE (not (null selected)) "corpus graph filter matched no provisions"
  pure (SemanticGraph "singapore-penal-code-coverage-v0.3" RuleView nodes edges notice)
  where
    notice = "Structural and executable research coverage are distinct. No evidence, guilt, conviction, acquittal, liability or sentence is determined."
    unlessE condition message = if condition then Right () else Left message
    neighbourhood identifier rows =
      let direct = Set.fromList (identifier : [target | row <- rows,
            provisionId row == identifier, edge <- provisionCrossReferences row,
            Just target <- [crossTarget edge]])
          related row = Set.member (provisionId row) direct || any
            (\edge -> crossTarget edge == Just identifier) (provisionCrossReferences row)
      in [row | row <- rows, related row]

provisionNode :: Provision -> GraphNode
provisionNode row = GraphNode (provisionId row) "provision"
  (provisionId row <> "\n" <> provisionHeading row <> "\n" <> provisionClassification row)
  (Just (Text.pack (provisionSourceReference row))) (Just (provisionReview row))
  (Just (provisionParent row))

data CorpusCommand
  = CorpusSummary FilePath
  | CorpusList FilePath (Maybe Text)
  | CorpusShow FilePath Text
  | CorpusCheck FilePath
  | CorpusCoverage FilePath
  | CorpusGraph FilePath DiagramFormat FilePath (Maybe Text) (Maybe Text) (Maybe Text)

runCorpus :: [String] -> IO ()
runCorpus arguments = case parseCorpus arguments of
  Left issue -> corpusFailure issue
  Right command -> execute command

parseCorpus :: [String] -> Either Text CorpusCommand
parseCorpus arguments = case arguments of
  "summary":rest -> CorpusSummary <$> rootFlags rest "."
  "list":rest -> do
    (root,category) <- listFlags rest "." Nothing
    pure (CorpusList root category)
  "show":identifier:rest -> CorpusShow <$> rootFlags rest "." <*> pure (Text.pack identifier)
  "check":rest -> CorpusCheck <$> rootFlags rest "."
  "coverage":"--format":"json":rest -> CorpusCoverage <$> rootFlags rest "."
  "graph":rest -> do
    (root,format,output,category,chapter,provision) <- graphFlags rest "." Nothing Nothing Nothing Nothing Nothing
    selectedFormat <- maybe (Left "corpus graph requires --format json|svg") Right format
    destination <- maybe (Left "corpus graph requires --output <path>") Right output
    pure (CorpusGraph root selectedFormat destination category chapter provision)
  _ -> Left "usage: yuho corpus summary|list|show|check|coverage|graph [options]"
  where
    rootFlags [] root = Right root
    rootFlags ["--corpus-root",root] _ = Right root
    rootFlags _ _ = Left "unknown or duplicate corpus option"
    listFlags [] root category = Right (root,category)
    listFlags ("--corpus-root":root:rest) "." category = listFlags rest root category
    listFlags ("--category":category:rest) root Nothing = listFlags rest root (Just (Text.pack category))
    listFlags _ _ _ = Left "unknown or duplicate corpus list option"
    graphFlags [] root format output category chapter provision =
      Right (root,format,output,category,chapter,provision)
    graphFlags ("--corpus-root":value:rest) "." format output category chapter provision =
      graphFlags rest value format output category chapter provision
    graphFlags ("--format":"json":rest) root Nothing output category chapter provision =
      graphFlags rest root (Just JsonFormat) output category chapter provision
    graphFlags ("--format":"svg":rest) root Nothing output category chapter provision =
      graphFlags rest root (Just SvgFormat) output category chapter provision
    graphFlags ("--output":value:rest) root format Nothing category chapter provision =
      graphFlags rest root format (Just value) category chapter provision
    graphFlags ("--category":value:rest) root format output Nothing chapter provision =
      graphFlags rest root format output (Just (Text.pack value)) chapter provision
    graphFlags ("--chapter":value:rest) root format output category Nothing provision =
      graphFlags rest root format output category (Just (Text.pack value)) provision
    graphFlags ("--provision":value:rest) root format output category chapter Nothing =
      graphFlags rest root format output category chapter (Just (Text.pack value))
    graphFlags _ _ _ _ _ _ _ = Left "unknown or duplicate corpus graph option"

execute :: CorpusCommand -> IO ()
execute command = do
  let root = commandRoot command
  loaded <- loadCoverage root >>= either corpusFailure pure
  let (coverage,bytes) = loaded
  validateCoverage root coverage >>= either corpusFailure pure
  case command of
    CorpusSummary _ -> BS.hPut stdout (summaryText (coverageSummary coverage))
    CorpusList _ category -> do
      case category of
        Just wanted | not (Map.member wanted (summaryByCategory (coverageSummary coverage))) ->
          corpusFailure "unknown corpus category"
        _ -> pure ()
      let rows = [row | row <- coverageProvisions coverage,
            maybe True (== provisionCategory row) category]
      BS.hPut stdout (Encoding.encodeUtf8 (Text.unlines (map listRow rows)))
    CorpusShow _ identifier -> case [row | row <- coverageProvisions coverage,
        provisionId row == identifier] of
      [row] -> BS.hPut stdout (Encoding.encodeUtf8 (showProvision row))
      _ -> corpusFailure "unknown corpus provision"
    CorpusCheck _ -> BS.hPut stdout (encodeJson (JObj
      [("status",JStr "valid"),("schema",JStr (coverageSchema coverage)),
       ("provisions",JNum (fromIntegral (length (coverageProvisions coverage))))]) <> "\n")
    CorpusCoverage _ -> BS.hPut stdout bytes
    CorpusGraph _ format output category chapter provision -> do
      graph <- either corpusFailure pure (coverageGraph category chapter provision coverage)
      when (format == SvgFormat && length (semanticGraphNodes graph) > 120)
        (corpusFailure "SVG graph filter exceeds 120 provisions; use JSON or a narrower filter")
      publish output (case format of JsonFormat -> encodeSemanticGraph graph; SvgFormat -> encodeSvg graph)

commandRoot :: CorpusCommand -> FilePath
commandRoot command = case command of
  CorpusSummary root -> root
  CorpusList root _ -> root
  CorpusShow root _ -> root
  CorpusCheck root -> root
  CorpusCoverage root -> root
  CorpusGraph root _ _ _ _ _ -> root

summaryText :: CoverageSummary -> BS.ByteString
summaryText summary = Encoding.encodeUtf8 . Text.unlines $
  ["Singapore Criminal Law Research Corpus v0.3",
   "Structural provisions: " <> number (summaryProvisions summary),
   "Executable offence families: " <> number (summaryTotalFamilies summary),
   "Singapore scenarios: " <> number (summaryTotalScenarios summary),
   "General-exception families: " <> number (summaryTotalExceptions summary),
   "Candidate penalties: " <> number (summaryTotalPenalties summary),
   "Analysis cases: " <> number (summaryTotalCases summary),
   "Coverage classifications:"]
  ++ ["  " <> key <> ": " <> number value | (key,value) <- Map.toAscList (summaryByClassification summary)]
  ++ ["Subject categories:"]
  ++ ["  " <> key <> ": " <> number value | (key,value) <- Map.toAscList (summaryByCategory summary)]
  ++ ["Structural coverage is not executable support or legal review."]
  where number = Text.pack . show

listRow :: Provision -> Text
listRow row = Text.intercalate "\t"
  [provisionId row,provisionClassification row,provisionCategory row,provisionHeading row]

showProvision :: Provision -> Text
showProvision row = Text.unlines $
  [provisionId row <> " — " <> provisionHeading row,
   "Structural parent: " <> provisionParent row,
   "Subject category: " <> provisionCategory row,
   "Coverage: " <> provisionClassification row,
   "Review: " <> provisionReview row,
   "Executable models: " <> comma (map Text.pack (provisionModels row)),
   "Scenarios: " <> Text.pack (show (length (provisionScenarios row))),
   "Candidate penalties: " <> comma (provisionPenalties row),
   "Limitations:"] ++ map ("  " <>) (provisionLimitations row)
  where comma [] = "none"; comma values = Text.intercalate ", " values

publish :: FilePath -> BS.ByteString -> IO ()
publish destination bytes = do
  parentExists <- doesDirectoryExist (takeDirectory destination)
  unless parentExists (corpusFailure "output parent does not exist")
  result <- try $ do
    (temporary,handle) <- openBinaryTempFile (takeDirectory destination) ".yuho-corpus-"
    (BS.hPut handle bytes >> hClose handle >> createLink temporary destination) `finally` do
      _ <- try (hClose handle) :: IO (Either IOException ())
      removeFile temporary
  case result of
    Left (_ :: IOException) -> corpusFailure "corpus output is unsafe or already exists"
    Right () -> pure ()

corpusFailure :: Text -> IO a
corpusFailure message = do
  BS.hPut stderr (encodeJson (JObj
    [("code",JStr "SFC001"),("path",JStr "<corpus>"),("line",JNum 1),
     ("column",JNum 1),("message",JStr message)]) <> "\n")
  exitFailure
