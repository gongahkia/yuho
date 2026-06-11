{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE PatternSynonyms #-}

module Main (main) where

import Control.Monad (when)
import Data.List (isSuffixOf, sort)
import Data.Maybe (fromMaybe, listToMaybe)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.IO as TIO
import Options.Applicative (execParser)
import Euclid.CLI.Options
import Euclid.Config.Loader
import Euclid.Core.Diff
import Euclid.Core.Eval
import Euclid.Core.Filter
import Euclid.Core.Reports
import Euclid.Core.Typecheck
import Euclid.Core.Validation
import Euclid.Import.CSV
import Euclid.Import.GEDCOM
import Euclid.Import.JSONLD
import Euclid.Lang.AST (Program(..), Stmt, pattern Program)
import Euclid.Lang.Loader
import Euclid.Lang.Parser
import Euclid.Model.Types
import Euclid.Render.Layout
import Euclid.Render.Diff
import Euclid.Render.HTML
import Euclid.Render.JSON
import Euclid.Render.Markdown
import Euclid.Render.Mermaid
import Euclid.Render.SVG
import Euclid.Tooling.LSP
import Euclid.TUI.App
import System.Directory
import System.Exit (exitFailure)
import System.FilePath ((</>), replaceExtension, takeBaseName)
import System.IO (hFlush, stdout)

data LoadedWorld = LoadedWorld
    { loadedWorld :: World
    , loadedDiagnostics :: [Diagnostic]
    , loadedProgram :: Program
    }

data ReplState = ReplState
    { replProgram :: [Stmt]
    , replWorld :: World
    , replDiagnostics :: [Diagnostic]
    }

main :: IO ()
main = do
    options <- execParser optionsParserInfo
    configValue <- loadConfig (optConfig options)
    when (optVerbose options) $
        putStrLn "Running Euclid"
    runCommand configValue options

runCommand :: EuclidConfig -> Options -> IO ()
runCommand configValue options =
    case optCommand options of
        CommandRun runOpts -> do
            loaded <- loadEuclidFile (runFile runOpts)
            let filtered = applyNarrativeFilter (runNarrative runOpts) loaded
            reportDiagnostics (loadedDiagnostics filtered)
            runEuclidTui (runFile runOpts) (loadedWorld filtered)
        CommandExport exportOpts -> runExport configValue (optTheme options) exportOpts
        CommandCheck filePath -> runCheck filePath
        CommandContradict filePath -> runContradict filePath
        CommandDiff diffOpts -> runDiff configValue (optTheme options) diffOpts
        CommandScenarioDiff scenarioDiffOpts -> runScenarioDiff scenarioDiffOpts
        CommandScenarioReport filePath -> runScenarioReport filePath
        CommandSources filePath -> runSources filePath
        CommandDeadlines filePath -> runDeadlines filePath
        CommandIssues filePath -> runIssues filePath
        CommandReview filePath -> runReview filePath
        CommandExhibits filePath -> runExhibits filePath
        CommandImport importOpts -> runImport importOpts
        CommandRepl -> runRepl
        CommandLsp -> runLspServer

runExport :: EuclidConfig -> Maybe Text -> ExportOptions -> IO ()
runExport configValue themeOverride exportOptions = do
    loaded <- applyNarrativeFilter (exportNarrative exportOptions) <$> loadEuclidFile (exportFile exportOptions)
    themeValue <- resolveSvgTheme themeOverride configValue
    case effectiveExportFormat configValue exportOptions of
        ExportSvg -> do
            let svgOptions =
                    defaultSvgOptions
                        { svgWidth =
                            fromMaybe
                                (fromMaybe (svgWidth defaultSvgOptions) (configDefaultWidth configValue))
                                (exportWidth exportOptions)
                        , svgHeight =
                            fromMaybe
                                (fromMaybe (svgHeight defaultSvgOptions) (configDefaultHeight configValue))
                                (exportHeight exportOptions)
                        , svgTitle = T.pack (takeBaseName (exportFile exportOptions))
                        , svgTheme = themeValue
                        }
                outputPath = fromMaybe (replaceExtension (exportFile exportOptions) "svg") (exportOutput exportOptions)
                svgDocument = renderSvg svgOptions (computeLayout (loadedWorld loaded))
            TIO.writeFile outputPath svgDocument
            reportDiagnostics (loadedDiagnostics loaded)
            putStrLn ("Wrote " <> outputPath)
        ExportHtml -> do
            let outputPath = fromMaybe (replaceExtension (exportFile exportOptions) "html") (exportOutput exportOptions)
                htmlDocument = renderInteractiveHtml (computeLayout (loadedWorld loaded))
            TIO.writeFile outputPath htmlDocument
            reportDiagnostics (loadedDiagnostics loaded)
            putStrLn ("Wrote " <> outputPath)
        ExportJson -> do
            let outputPath = fromMaybe (replaceExtension (exportFile exportOptions) "json") (exportOutput exportOptions)
            TIO.writeFile outputPath (renderJson (loadedWorld loaded))
            reportDiagnostics (loadedDiagnostics loaded)
            putStrLn ("Wrote " <> outputPath)
        ExportMarkdown -> do
            let outputPath = fromMaybe (replaceExtension (exportFile exportOptions) "md") (exportOutput exportOptions)
            TIO.writeFile outputPath (renderMarkdown (loadedWorld loaded))
            reportDiagnostics (loadedDiagnostics loaded)
            putStrLn ("Wrote " <> outputPath)
        ExportMermaid -> do
            let outputPath = fromMaybe (replaceExtension (exportFile exportOptions) "mmd") (exportOutput exportOptions)
            TIO.writeFile outputPath (renderMermaid (computeLayout (loadedWorld loaded)))
            reportDiagnostics (loadedDiagnostics loaded)
            putStrLn ("Wrote " <> outputPath)

runCheck :: FilePath -> IO ()
runCheck filePath = do
    loaded <- loadEuclidFile filePath
    if null (loadedDiagnostics loaded)
        then putStrLn "OK"
        else do
            reportDiagnostics (loadedDiagnostics loaded)
            when (hasErrors (loadedDiagnostics loaded)) exitFailure

runContradict :: FilePath -> IO ()
runContradict filePath = do
    loaded <- loadEuclidFile filePath
    when (hasErrors (loadedDiagnostics loaded)) $ do
        reportDiagnostics (loadedDiagnostics loaded)
        exitFailure
    TIO.putStr (renderContradictions (loadedWorld loaded))

runDiff :: EuclidConfig -> Maybe Text -> DiffOptions -> IO ()
runDiff configValue themeOverride diffOptions = do
    leftWorldValue <- loadEuclidFile (diffLeftFile diffOptions)
    rightWorldValue <- loadEuclidFile (diffRightFile diffOptions)
    case diffFormat diffOptions of
        Nothing ->
            TIO.putStrLn (diffWorlds (loadedWorld leftWorldValue) (loadedWorld rightWorldValue))
        Just DiffSvg -> do
            themeValue <- resolveSvgTheme themeOverride configValue
            let outputPath = fromMaybe (defaultDiffOutput "svg") (diffOutput diffOptions)
                svgOptions =
                    defaultSvgOptions
                        { svgWidth = fromMaybe (svgWidth defaultSvgOptions) (configDefaultWidth configValue)
                        , svgHeight = fromMaybe (svgHeight defaultSvgOptions) (configDefaultHeight configValue)
                        , svgTitle = "Euclid diff"
                        , svgTheme = themeValue
                        }
                document =
                    renderDiffSvg
                        svgOptions
                        (T.pack (takeBaseName (diffLeftFile diffOptions)))
                        (computeLayout (loadedWorld leftWorldValue))
                        (T.pack (takeBaseName (diffRightFile diffOptions)))
                        (computeLayout (loadedWorld rightWorldValue))
            TIO.writeFile outputPath document
            putStrLn ("Wrote " <> outputPath)
        Just DiffHtml -> do
            themeValue <- resolveSvgTheme themeOverride configValue
            let outputPath = fromMaybe (defaultDiffOutput "html") (diffOutput diffOptions)
                svgOptions =
                    defaultSvgOptions
                        { svgWidth = fromMaybe (svgWidth defaultSvgOptions) (configDefaultWidth configValue)
                        , svgHeight = fromMaybe (svgHeight defaultSvgOptions) (configDefaultHeight configValue)
                        , svgTitle = "Euclid diff"
                        , svgTheme = themeValue
                        }
                document =
                    renderDiffHtml
                        svgOptions
                        (T.pack (takeBaseName (diffLeftFile diffOptions)))
                        (computeLayout (loadedWorld leftWorldValue))
                        (T.pack (takeBaseName (diffRightFile diffOptions)))
                        (computeLayout (loadedWorld rightWorldValue))
            TIO.writeFile outputPath document
            putStrLn ("Wrote " <> outputPath)
  where
    defaultDiffOutput extension =
        takeBaseName (diffLeftFile diffOptions)
            <> "-vs-"
            <> takeBaseName (diffRightFile diffOptions)
            <> "."
            <> extension

runScenarioDiff :: ScenarioDiffOptions -> IO ()
runScenarioDiff scenarioDiffOptions = do
    loaded <- loadEuclidFile (scenarioDiffFile scenarioDiffOptions)
    when (hasErrors (loadedDiagnostics loaded)) $ do
        reportDiagnostics (loadedDiagnostics loaded)
        exitFailure
    case renderScenarioDiff (loadedWorld loaded) (scenarioDiffName scenarioDiffOptions) of
        Left message -> do
            TIO.putStrLn message
            exitFailure
        Right report ->
            TIO.putStr report

runScenarioReport :: FilePath -> IO ()
runScenarioReport filePath = do
    loaded <- loadEuclidFile filePath
    when (hasErrors (loadedDiagnostics loaded)) $ do
        reportDiagnostics (loadedDiagnostics loaded)
        exitFailure
    TIO.putStr (renderScenarioReport (loadedWorld loaded))

runSources :: FilePath -> IO ()
runSources filePath = do
    loaded <- loadEuclidFile filePath
    when (hasErrors (loadedDiagnostics loaded)) $ do
        reportDiagnostics (loadedDiagnostics loaded)
        exitFailure
    TIO.putStr (renderSourcesReport (loadedWorld loaded))

runDeadlines :: FilePath -> IO ()
runDeadlines filePath = do
    loaded <- loadEuclidFile filePath
    when (hasErrors (loadedDiagnostics loaded)) $ do
        reportDiagnostics (loadedDiagnostics loaded)
        exitFailure
    TIO.putStr (renderDeadlinesReport (loadedWorld loaded))

runIssues :: FilePath -> IO ()
runIssues filePath = do
    loaded <- loadEuclidFile filePath
    when (hasErrors (loadedDiagnostics loaded)) $ do
        reportDiagnostics (loadedDiagnostics loaded)
        exitFailure
    TIO.putStr (renderIssuesReport (loadedWorld loaded))

runReview :: FilePath -> IO ()
runReview filePath = do
    loaded <- loadEuclidFile filePath
    TIO.putStr (renderLegalReview (loadedDiagnostics loaded) (loadedWorld loaded))
    when (hasErrors (loadedDiagnostics loaded)) exitFailure

runExhibits :: FilePath -> IO ()
runExhibits filePath = do
    loaded <- loadEuclidFile filePath
    when (hasErrors (loadedDiagnostics loaded)) $ do
        reportDiagnostics (loadedDiagnostics loaded)
        exitFailure
    TIO.putStr (renderExhibitsCsv (loadedWorld loaded))

runImport :: ImportOptions -> IO ()
runImport importOptions = do
    input <- TIO.readFile (importFile importOptions)
    let imported =
            case importFormat importOptions of
                ImportCsv -> importCsvToEuclid input
                ImportGedcom -> importGedcomToEuclid input
                ImportJsonld -> importJsonLdToEuclid input
    case imported of
        Left diags -> do
            reportDiagnostics diags
            exitFailure
        Right euclidSource ->
            case importOutput importOptions of
                Nothing -> TIO.putStrLn euclidSource
                Just outputPath -> TIO.writeFile outputPath euclidSource

runRepl :: IO ()
runRepl = do
    putStrLn "Euclid REPL"
    putStrLn ":load <path|index> | :files | :world | :entities | :rels | :validate | :timeline | :quit"
    replLoop initialReplState

initialReplState :: ReplState
initialReplState =
    ReplState
        { replProgram = []
        , replWorld = emptyWorld
        , replDiagnostics = []
        }

replLoop :: ReplState -> IO ()
replLoop state = do
    putStr "euclid> "
    hFlush stdout
    input <- getLine
    case words input of
        [] -> replLoop state
        [":quit"] -> pure ()
        [":q"] -> pure ()
        [":files"] -> do
            files <- discoverEuclidFiles "."
            mapM_ putStrLn (zipWith (\idx filePath -> show idx <> "  " <> filePath) [1 :: Int ..] files)
            replLoop state
        [":f"] -> do
            files <- discoverEuclidFiles "."
            mapM_ putStrLn (zipWith (\idx filePath -> show idx <> "  " <> filePath) [1 :: Int ..] files)
            replLoop state
        [":world"] -> do
            TIO.putStrLn (renderWorldSummary (replWorld state))
            replLoop state
        [":w"] -> do
            TIO.putStrLn (renderWorldSummary (replWorld state))
            replLoop state
        [":entities"] -> do
            mapM_ (TIO.putStrLn . renderEntitySummary) (Map.elems (worldEntities (replWorld state)))
            replLoop state
        [":e"] -> do
            mapM_ (TIO.putStrLn . renderEntitySummary) (Map.elems (worldEntities (replWorld state)))
            replLoop state
        [":rels"] -> do
            mapM_ (TIO.putStrLn . renderRelationshipSummary) (worldRelationships (replWorld state))
            replLoop state
        [":r"] -> do
            mapM_ (TIO.putStrLn . renderRelationshipSummary) (worldRelationships (replWorld state))
            replLoop state
        [":validate"] -> do
            reportDiagnostics (validateWorld (replWorld state))
            replLoop state
        [":v"] -> do
            reportDiagnostics (validateWorld (replWorld state))
            replLoop state
        [":timeline"] -> do
            TIO.putStrLn (renderTimelineView (replWorld state))
            replLoop state
        [":t"] -> do
            TIO.putStrLn (renderTimelineView (replWorld state))
            replLoop state
        [":load", target] -> do
            filePath <- resolveLoadTarget target
            loaded <- loadEuclidFile filePath
            reportDiagnostics (loadedDiagnostics loaded)
            replLoop
                ReplState
                    { replProgram = let Program statements = loadedProgram loaded in statements
                    , replWorld = loadedWorld loaded
                    , replDiagnostics = loadedDiagnostics loaded
                    }
        _ ->
            case parseStatement "<repl>" (T.pack input) of
                Left diags -> do
                    reportDiagnostics diags
                    replLoop state
                Right statement ->
                    let nextProgram = Program (replProgram state ++ [statement])
                        typeDiagnostics = typeCheckProgram nextProgram
                    in if hasErrors typeDiagnostics
                        then do
                            reportDiagnostics typeDiagnostics
                            replLoop state
                        else
                            case evalProgram nextProgram of
                                Left diag -> do
                                    reportDiagnostics [diag]
                                    replLoop state
                                Right worldValue -> do
                                    let newDiagnostics = typeDiagnostics ++ validateWorld worldValue
                                    reportDiagnostics newDiagnostics
                                    replLoop
                                        state
                                            { replProgram = replProgram state ++ [statement]
                                            , replWorld = worldValue
                                            , replDiagnostics = newDiagnostics
                                            }

loadEuclidFile :: FilePath -> IO LoadedWorld
loadEuclidFile filePath = do
    loadedProgramResult <- loadProgramWithImports filePath
    case loadedProgramResult of
        Left diags -> do
            reportDiagnostics diags
            exitFailure
        Right program ->
            let typeDiagnostics = typeCheckProgram program
            in if hasErrors typeDiagnostics
                then do
                    reportDiagnostics typeDiagnostics
                    exitFailure
                else
                    case evalProgram program of
                        Left diag -> do
                            reportDiagnostics [diag]
                            exitFailure
                        Right worldValue -> do
                            let diagnostics = typeDiagnostics ++ validateWorld worldValue
                            pure
                                LoadedWorld
                                    { loadedWorld = worldValue
                                    , loadedDiagnostics = diagnostics
                                    , loadedProgram = program
                                    }

applyNarrativeFilter :: Maybe Text -> LoadedWorld -> LoadedWorld
applyNarrativeFilter Nothing loaded = loaded
applyNarrativeFilter (Just narrativeName) loaded =
    loaded
        { loadedWorld = filteredWorld
        , loadedDiagnostics = validateWorld filteredWorld
        }
  where
    filteredWorld = filterWorldByNarrative narrativeName (loadedWorld loaded)

discoverEuclidFiles :: FilePath -> IO [FilePath]
discoverEuclidFiles root = do
    entries <- listDirectory root
    let filtered = filter (`notElem` [".git", "target", "dist-newstyle"]) entries
    paths <- traverse toPath filtered
    pure (sort (concat paths))
  where
    toPath entry = do
        let path = root </> entry
        isDir <- doesDirectoryExist path
        if isDir
            then discoverEuclidFiles path
            else pure [path | ".euclid" `isSuffixOf` path]

renderWorldSummary :: World -> Text
renderWorldSummary worldValue =
    T.unlines
        [ "timelines: " <> T.pack (show (Map.size (worldTimelines worldValue)))
        , "entities: " <> T.pack (show (Map.size (worldEntities worldValue)))
        , "relationships: " <> T.pack (show (length (worldRelationships worldValue)))
        , "types: " <> T.pack (show (Map.size (worldTypes worldValue)))
        ]

renderTimelineView :: World -> Text
renderTimelineView worldValue =
    if null timelineLines
        then "(no timelines loaded)\n"
        else T.unlines timelineLines
  where
    timelineLines =
        concatMap renderTimeline (Map.elems (worldTimelines worldValue))
    renderTimeline timeline =
        let matchingEntities =
                [ entity
                | entity <- Map.elems (worldEntities worldValue)
                , any (\appearance -> appearanceTimeline appearance == timelineName timeline) (entityAppearances entity)
                ]
            header =
                timelineName timeline
                    <> " ["
                    <> T.pack (show (timelineKind timeline))
                    <> "] "
                    <> T.pack (show (timePointOrdinal (timelineStart timeline)))
                    <> ".."
                    <> T.pack (show (timePointOrdinal (timelineEnd timeline)))
            entityLines =
                [ "  - " <> entityName entity <> " : " <> renderAppearanceRanges (timelineName timeline) entity
                | entity <- matchingEntities
                ]
         in header : entityLines

renderAppearanceRanges :: Text -> Entity -> Text
renderAppearanceRanges timelineValue entity =
    T.intercalate
        ", "
        [ T.pack (show (timePointOrdinal (rangeStart (appearanceRange appearance))))
            <> ".."
            <> T.pack (show (timePointOrdinal (rangeEnd (appearanceRange appearance))))
        | appearance <- entityAppearances entity
        , appearanceTimeline appearance == timelineValue
        ]

renderEntitySummary :: Entity -> Text
renderEntitySummary entity =
    entityName entity
        <> " : "
        <> entityType entity
        <> " appearances="
        <> T.pack (show (length (entityAppearances entity)))

renderRelationshipSummary :: Relationship -> Text
renderRelationshipSummary relationship =
    relSource relationship
        <> " "
        <> maybe "-->" (\labelValue -> "-[\"" <> labelValue <> "\"]->") (relLabel relationship)
        <> " "
        <> relTarget relationship

reportDiagnostics :: [Diagnostic] -> IO ()
reportDiagnostics = mapM_ (TIO.putStrLn . renderDiagnostic)

hasErrors :: [Diagnostic] -> Bool
hasErrors = any ((== DiagnosticError) . diagnosticLevel)

effectiveExportFormat :: EuclidConfig -> ExportOptions -> ExportFormat
effectiveExportFormat _ exportOptions = exportFormat exportOptions

resolveLoadTarget :: String -> IO FilePath
resolveLoadTarget target =
    case reads target of
        [(indexValue, "")] -> do
            files <- discoverEuclidFiles "."
            case listToMaybe (drop (indexValue - 1) files) of
                Just filePath -> pure filePath
                Nothing -> do
                    putStrLn ("No .euclid file at index " <> show indexValue)
                    exitFailure
        _ -> pure target
