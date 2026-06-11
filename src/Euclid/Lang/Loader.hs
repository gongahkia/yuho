{-# LANGUAGE OverloadedStrings #-}

module Euclid.Lang.Loader
    ( loadProgramWithImports
    ) where

import Control.Exception (IOException, try)
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.IO as TIO
import Euclid.Lang.AST
import Euclid.Lang.Parser (parseProgram)
import Euclid.Model.Types
import System.Directory (makeAbsolute)
import System.FilePath ((</>), normalise, takeDirectory)

loadProgramWithImports :: FilePath -> IO (Either [Diagnostic] Program)
loadProgramWithImports filePath = do
    loaded <- loadFile [] filePath
    pure $ do
        (resolvedPath, statements) <- loaded
        pure (ProgramData resolvedPath statements)

loadFile :: [FilePath] -> FilePath -> IO (Either [Diagnostic] (FilePath, [Stmt]))
loadFile visited filePath = do
    resolvedPath <- normalise <$> makeAbsolute filePath
    if resolvedPath `elem` visited
        then
            pure $
                Left
                    [ loaderDiagnostic
                        resolvedPath
                        ( "import cycle detected: "
                            <> T.intercalate " -> " (map T.pack (reverse (resolvedPath : visited)))
                        )
                    ]
        else do
            sourceResult <- try (TIO.readFile resolvedPath)
            case sourceResult of
                Left readError ->
                    pure (Left [loaderDiagnostic resolvedPath ("could not read import: " <> T.pack (show (readError :: IOException)))])
                Right source ->
                    case parseProgram resolvedPath source of
                        Left diags -> pure (Left diags)
                        Right (ProgramData _ statements) -> do
                            expanded <- traverse (expandStatement (resolvedPath : visited) resolvedPath) statements
                            pure $
                                case sequence expanded of
                                    Left diags -> Left diags
                                    Right expandedStatements -> Right (resolvedPath, concat expandedStatements)

expandStatement :: [FilePath] -> FilePath -> Stmt -> IO (Either [Diagnostic] [Stmt])
expandStatement visited currentFile stmt =
    case stmtNode stmt of
        StmtImportNode importPath -> do
            let resolvedImport = takeDirectory currentFile </> T.unpack importPath
            loaded <- loadFile visited resolvedImport
            pure (snd <$> loaded)
        _ -> pure (Right [stmt])

loaderDiagnostic :: FilePath -> Text -> Diagnostic
loaderDiagnostic filePath message =
    Diagnostic
        { diagnosticLevel = DiagnosticError
        , diagnosticSource = "loader"
        , diagnosticMessage = message
        , diagnosticSpan =
            Just
                noSourceSpan
                    { spanFile = filePath
                    }
        }
