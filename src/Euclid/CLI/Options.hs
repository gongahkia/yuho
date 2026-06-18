{-# LANGUAGE OverloadedStrings #-}

module Euclid.CLI.Options
    ( Command(..)
    , DiffFormat(..)
    , DiffOptions(..)
    , ExportFormat(..)
    , ExportOptions(..)
    , ImportFormat(..)
    , ImportOptions(..)
    , Options(..)
    , RunOptions(..)
    , ScenarioDiffOptions(..)
    , parseDiffFormat
    , parseExportFormat
    , optionsParserInfo
    ) where

import Data.Char (toLower)
import Data.Text (Text)
import qualified Data.Text as T
import Options.Applicative

data ExportFormat
    = ExportSvg
    | ExportHtml
    | ExportJson
    | ExportMarkdown
    | ExportMermaid
    deriving (Eq, Show)

data DiffFormat
    = DiffSvg
    | DiffHtml
    deriving (Eq, Show)

data ImportFormat
    = ImportCsv
    | ImportGedcom
    | ImportJsonld
    deriving (Eq, Show)

data ExportOptions = ExportOptions
    { exportFile :: FilePath
    , exportFormat :: ExportFormat
    , exportOutput :: Maybe FilePath
    , exportWidth :: Maybe Int
    , exportHeight :: Maybe Int
    , exportNarrative :: Maybe Text
    }
    deriving (Eq, Show)

data RunOptions = RunOptions
    { runFile :: FilePath
    , runNarrative :: Maybe Text
    }
    deriving (Eq, Show)

data DiffOptions = DiffOptions
    { diffLeftFile :: FilePath
    , diffRightFile :: FilePath
    , diffFormat :: Maybe DiffFormat
    , diffOutput :: Maybe FilePath
    }
    deriving (Eq, Show)

data ScenarioDiffOptions = ScenarioDiffOptions
    { scenarioDiffFile :: FilePath
    , scenarioDiffName :: Text
    }
    deriving (Eq, Show)

data ImportOptions = ImportOptions
    { importFile :: FilePath
    , importFormat :: ImportFormat
    , importOutput :: Maybe FilePath
    }
    deriving (Eq, Show)

data Command
    = CommandRun RunOptions
    | CommandExport ExportOptions
    | CommandCheck FilePath
    | CommandContradict FilePath
    | CommandDiff DiffOptions
    | CommandScenarioDiff ScenarioDiffOptions
    | CommandScenarioReport FilePath
    | CommandSources FilePath
    | CommandDeadlines FilePath
    | CommandIssues FilePath
    | CommandReview FilePath
    | CommandExhibits FilePath
    | CommandImport ImportOptions
    | CommandRepl
    | CommandLsp
    deriving (Eq, Show)

data Options = Options
    { optVerbose :: Bool
    , optConfig :: Maybe FilePath
    , optTheme :: Maybe Text
    , optCommand :: Command
    }
    deriving (Eq, Show)

optionsParserInfo :: ParserInfo Options
optionsParserInfo =
    info
        (helper <*> optionsParser)
        (fullDesc <> progDesc "Euclid timeline DSL and terminal explorer")

optionsParser :: Parser Options
optionsParser =
    Options
        <$> switch (long "verbose" <> help "Enable verbose logging")
        <*> optional (strOption (long "config" <> metavar "PATH" <> help "Path to TOML config"))
        <*> optional (T.pack <$> strOption (long "theme" <> metavar "NAME" <> help "Theme name or TOML path"))
        <*> hsubparser
            ( command "run" (info runParser (progDesc "Run the analytical terminal UI"))
                <> command "export" (info exportParser (progDesc "Export a .euclid file"))
                <> command "check" (info checkParser (progDesc "Parse and validate a .euclid file"))
                <> command "contradict" (info contradictParser (progDesc "List contradiction edges with supporting evidence"))
                <> command "diff" (info diffParser (progDesc "Semantic diff of two .euclid files"))
                <> command "scenario-diff" (info scenarioDiffParser (progDesc "Diff a stored legal scenario against its base world"))
                <> command "scenario-report" (info scenarioReportParser (progDesc "List stored legal scenarios and their diffs"))
                <> command "sources" (info sourcesParser (progDesc "Audit source records, bundles, and citation normalization"))
                <> command "deadlines" (info deadlinesParser (progDesc "Audit rulesets, deadline rules, and deadline entities"))
                <> command "issues" (info issuesParser (progDesc "Audit legal issues and elements"))
                <> command "review" (info reviewParser (progDesc "Review diagnostics, sources, rulesets, issues, and scenarios"))
                <> command "exhibits" (info exhibitsParser (progDesc "Emit exhibit list CSV"))
                <> command "import" (info importParser (progDesc "Import external data into .euclid"))
                <> command "repl" (info replParser (progDesc "Interactive REPL"))
                <> command "lsp" (info lspParser (progDesc "Run the stdio language server"))
            )

runParser :: Parser Command
runParser =
    CommandRun
        <$> ( RunOptions
                <$> argument str (metavar "FILE")
                <*> narrativeOption
            )

exportParser :: Parser Command
exportParser =
    CommandExport
        <$> ( ExportOptions
                <$> argument str (metavar "FILE")
                <*> option
                    (eitherReader parseExportFormat)
                    (short 'f' <> long "format" <> value ExportSvg <> metavar "FORMAT" <> help "svg | html | json | md | mermaid")
                <*> optional (strOption (short 'o' <> long "output" <> metavar "PATH"))
                <*> optional (option auto (long "width" <> metavar "PIXELS"))
                <*> optional (option auto (long "height" <> metavar "PIXELS"))
                <*> narrativeOption
            )

narrativeOption :: Parser (Maybe Text)
narrativeOption =
    optional $
        T.pack
            <$> strOption
                ( long "narrative"
                    <> metavar "NAME"
                    <> help "Filter to entities for a narrative while retaining neutral shared context"
                )

checkParser :: Parser Command
checkParser =
    CommandCheck
        <$> argument str (metavar "FILE")

contradictParser :: Parser Command
contradictParser =
    CommandContradict
        <$> argument str (metavar "FILE")

diffParser :: Parser Command
diffParser =
    CommandDiff
        <$> ( DiffOptions
                <$> argument str (metavar "FILE1")
                <*> argument str (metavar "FILE2")
                <*> optional
                    ( option
                        (eitherReader parseDiffFormat)
                        (short 'f' <> long "format" <> metavar "FORMAT" <> help "Visual diff format: svg | html")
                    )
                <*> optional (strOption (short 'o' <> long "output" <> metavar "PATH"))
            )

scenarioDiffParser :: Parser Command
scenarioDiffParser =
    CommandScenarioDiff
        <$> ( ScenarioDiffOptions
                <$> argument str (metavar "FILE")
                <*> (T.pack <$> argument str (metavar "SCENARIO"))
            )

scenarioReportParser :: Parser Command
scenarioReportParser =
    CommandScenarioReport
        <$> argument str (metavar "FILE")

sourcesParser :: Parser Command
sourcesParser =
    CommandSources
        <$> argument str (metavar "FILE")

deadlinesParser :: Parser Command
deadlinesParser =
    CommandDeadlines
        <$> argument str (metavar "FILE")

issuesParser :: Parser Command
issuesParser =
    CommandIssues
        <$> argument str (metavar "FILE")

reviewParser :: Parser Command
reviewParser =
    CommandReview
        <$> argument str (metavar "FILE")

exhibitsParser :: Parser Command
exhibitsParser =
    CommandExhibits
        <$> argument str (metavar "FILE")

importParser :: Parser Command
importParser =
    CommandImport
        <$> ( ImportOptions
                <$> argument str (metavar "FILE")
                <*> option
                    (eitherReader parseImportFormat)
                    (long "from" <> value ImportCsv <> metavar "FORMAT" <> help "csv | gedcom | jsonld")
                <*> optional (strOption (short 'o' <> long "output" <> metavar "PATH"))
            )

replParser :: Parser Command
replParser = pure CommandRepl

lspParser :: Parser Command
lspParser = pure CommandLsp

parseExportFormat :: String -> Either String ExportFormat
parseExportFormat raw =
    case map toLower raw of
        "svg" -> Right ExportSvg
        "html" -> Right ExportHtml
        "json" -> Right ExportJson
        "md" -> Right ExportMarkdown
        "markdown" -> Right ExportMarkdown
        "mermaid" -> Right ExportMermaid
        other -> Left ("unknown export format: " <> other <> " (supported: svg, html, json, md, mermaid)")

parseDiffFormat :: String -> Either String DiffFormat
parseDiffFormat raw =
    case map toLower raw of
        "svg" -> Right DiffSvg
        "html" -> Right DiffHtml
        other -> Left ("unknown diff format: " <> other <> " (supported: svg, html)")

parseImportFormat :: String -> Either String ImportFormat
parseImportFormat raw =
    case map toLower raw of
        "csv" -> Right ImportCsv
        "gedcom" -> Right ImportGedcom
        "jsonld" -> Right ImportJsonld
        other -> Left ("unknown import format: " <> other)
