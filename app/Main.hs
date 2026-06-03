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
import Euclid.Core.Validation
import Euclid.Import.CSV
import Euclid.Import.GEDCOM
import Euclid.Import.JSONLD
import Euclid.Lang.AST (Program(..), Stmt, pattern Program)
import Euclid.Lang.Parser
import Euclid.Model.Types
import Euclid.Render.Layout
import Euclid.Render.HTML
import Euclid.Render.JSON
import Euclid.Render.Markdown
import Euclid.Render.Mermaid
import Euclid.Render.SVG
import Euclid.Tooling.LSP
import Euclid.TUI.App
import System.Directory
import System.Exit (exitFailure)
import System.FilePath ((</>), normalise, replaceExtension, takeBaseName, takeDirectory)
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
        CommandDiff leftPath rightPath -> runDiff leftPath rightPath
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

runDiff :: FilePath -> FilePath -> IO ()
runDiff leftPath rightPath = do
    leftWorldValue <- loadEuclidFile leftPath
    rightWorldValue <- loadEuclidFile rightPath
    TIO.putStrLn (diffWorlds (loadedWorld leftWorldValue) (loadedWorld rightWorldValue))

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
                    case evalProgram (Program (replProgram state ++ [statement])) of
                        Left diag -> do
                            reportDiagnostics [diag]
                            replLoop state
                        Right worldValue -> do
                            let newDiagnostics = validateWorld worldValue
                            reportDiagnostics newDiagnostics
                            replLoop
                                state
                                    { replProgram = replProgram state ++ [statement]
                                    , replWorld = worldValue
                                    , replDiagnostics = newDiagnostics
                                    }

loadEuclidFile :: FilePath -> IO LoadedWorld
loadEuclidFile filePath = do
    source <- loadSourceWithImports [] filePath
    case parseProgram filePath source of
        Left diags -> do
            reportDiagnostics diags
            exitFailure
        Right program ->
            case evalProgram program of
                Left diag -> do
                    reportDiagnostics [diag]
                    exitFailure
                Right worldValue -> do
                    let diagnostics = validateWorld worldValue
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

loadSourceWithImports :: [FilePath] -> FilePath -> IO Text
loadSourceWithImports visited filePath = do
    let normalizedPath = normalise filePath
    when (normalizedPath `elem` visited) $ do
        putStrLn ("Import cycle detected at " <> normalizedPath)
        exitFailure
    source <- TIO.readFile normalizedPath
    expandedLines <- traverse (expandLine (normalizedPath : visited) normalizedPath) (T.lines source)
    pure (T.unlines (concat expandedLines))

expandLine :: [FilePath] -> FilePath -> Text -> IO [Text]
expandLine visited currentFile lineValue =
    case parseImportLine lineValue of
        Nothing -> pure [lineValue]
        Just relativePath -> do
            importedSource <- loadSourceWithImports visited (takeDirectory currentFile </> T.unpack relativePath)
            pure (T.lines importedSource)

parseImportLine :: Text -> Maybe Text
parseImportLine rawLine =
    let cleaned = T.strip rawLine
     in if "import \"" `T.isPrefixOf` cleaned && "\";" `T.isSuffixOf` cleaned
            then Just (T.dropEnd 2 (T.drop 8 cleaned))
            else Nothing

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
