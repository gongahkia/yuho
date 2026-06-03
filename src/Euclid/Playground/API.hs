{-# LANGUAGE OverloadedStrings #-}

module Euclid.Playground.API
    ( PlaygroundRequest(..)
    , handlePlaygroundJson
    , playgroundResponse
    ) where

import qualified Data.Aeson as Aeson
import qualified Data.ByteString.Lazy as BL
import Data.Text (Text)
import qualified Data.Text as T
import Euclid.Core.Eval
import Euclid.Core.Validation
import Euclid.Lang.Parser
import Euclid.Model.Types
import Euclid.Render.HTML
import Euclid.Render.JSON
import Euclid.Render.Layout
import Euclid.Render.Markdown
import Euclid.Render.Mermaid
import Euclid.Render.SVG

data PlaygroundRequest = PlaygroundRequest
    { playgroundCommand :: Text
    , playgroundFileName :: FilePath
    , playgroundSource :: Text
    , playgroundFormat :: Maybe Text
    }
    deriving (Eq, Show)

instance Aeson.FromJSON PlaygroundRequest where
    parseJSON =
        Aeson.withObject "PlaygroundRequest" $ \obj ->
            PlaygroundRequest
                <$> obj Aeson..: "command"
                <*> obj Aeson..:? "fileName" Aeson..!= "<playground>"
                <*> obj Aeson..: "source"
                <*> obj Aeson..:? "format"

handlePlaygroundJson :: BL.ByteString -> BL.ByteString
handlePlaygroundJson input =
    case Aeson.eitherDecode input of
        Left message ->
            Aeson.encode $
                responseObject
                    False
                    [ playgroundDiagnostic DiagnosticError "playground" ("invalid request JSON: " <> T.pack message)
                    ]
                    Nothing
        Right request ->
            Aeson.encode (playgroundResponse request)

playgroundResponse :: PlaygroundRequest -> Aeson.Value
playgroundResponse request =
    case loadWorldFromSource (playgroundFileName request) (playgroundSource request) of
        Left diagnostics ->
            responseObject False (map diagnosticObject diagnostics) Nothing
        Right (worldValue, diagnostics) ->
            case playgroundCommand request of
                "check" ->
                    responseObject (not (hasErrors diagnostics)) (map diagnosticObject diagnostics) Nothing
                "export" ->
                    case renderPlaygroundExport (playgroundFormat request) worldValue of
                        Left message ->
                            responseObject
                                False
                                (map diagnosticObject diagnostics ++ [playgroundDiagnostic DiagnosticError "playground" message])
                                Nothing
                        Right output ->
                            responseObject (not (hasErrors diagnostics)) (map diagnosticObject diagnostics) (Just output)
                other ->
                    responseObject
                        False
                        [playgroundDiagnostic DiagnosticError "playground" ("unknown playground command: " <> other)]
                        Nothing

loadWorldFromSource :: FilePath -> Text -> Either [Diagnostic] (World, [Diagnostic])
loadWorldFromSource fileName source =
    case parseProgram fileName source of
        Left diagnostics -> Left diagnostics
        Right program ->
            case evalProgram program of
                Left diagnostic -> Left [diagnostic]
                Right worldValue -> Right (worldValue, validateWorld worldValue)

renderPlaygroundExport :: Maybe Text -> World -> Either Text Text
renderPlaygroundExport requestedFormat worldValue =
    case T.toLower (maybe "svg" id requestedFormat) of
        "svg" ->
            Right (renderSvg defaultSvgOptions (computeLayout worldValue))
        "html" ->
            Right (renderInteractiveHtml (computeLayout worldValue))
        "json" ->
            Right (renderJson worldValue)
        "md" ->
            Right (renderMarkdown worldValue)
        "markdown" ->
            Right (renderMarkdown worldValue)
        "mermaid" ->
            Right (renderMermaid (computeLayout worldValue))
        other ->
            Left ("unknown playground export format: " <> other)

responseObject :: Bool -> [Aeson.Value] -> Maybe Text -> Aeson.Value
responseObject ok diagnostics maybeOutput =
    Aeson.object
        [ "ok" Aeson..= ok
        , "diagnostics" Aeson..= diagnostics
        , "output" Aeson..= maybeOutput
        ]

diagnosticObject :: Diagnostic -> Aeson.Value
diagnosticObject diagnostic =
    Aeson.object
        [ "level" Aeson..= diagnosticLevelText (diagnosticLevel diagnostic)
        , "source" Aeson..= diagnosticSource diagnostic
        , "message" Aeson..= diagnosticMessage diagnostic
        ]

playgroundDiagnostic :: DiagnosticLevel -> Text -> Text -> Aeson.Value
playgroundDiagnostic level source message =
    Aeson.object
        [ "level" Aeson..= diagnosticLevelText level
        , "source" Aeson..= source
        , "message" Aeson..= message
        ]

diagnosticLevelText :: DiagnosticLevel -> Text
diagnosticLevelText DiagnosticError = "error"
diagnosticLevelText DiagnosticWarning = "warning"

hasErrors :: [Diagnostic] -> Bool
hasErrors =
    any ((== DiagnosticError) . diagnosticLevel)
