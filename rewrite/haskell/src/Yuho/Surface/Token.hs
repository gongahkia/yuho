{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Token
  ( Kind(..), Token(..), Diagnostic(..), at, diagnosticJson ) where

import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Protocol.Json (J(..))

data Kind = WordToken | StringToken | SymbolToken | EndToken deriving (Eq, Show)

data Token = Token
  { tokenKind :: Kind
  , tokenText :: Text
  , tokenLine :: Int
  , tokenColumn :: Int
  } deriving (Eq, Show)

data Diagnostic = Diagnostic
  { diagnosticCode :: Text
  , diagnosticPath :: FilePath
  , diagnosticToken :: Token
  , diagnosticMessage :: Text
  } deriving (Eq, Show)

at :: Text -> FilePath -> Token -> Text -> Either Diagnostic a
at code path token message = Left (Diagnostic code path token message)

diagnosticJson :: Diagnostic -> J
diagnosticJson item = JObj
  [ ("code", JStr (diagnosticCode item))
  , ("path", JStr (Text.pack (diagnosticPath item)))
  , ("line", JNum (toInteger (tokenLine (diagnosticToken item))))
  , ("column", JNum (toInteger (tokenColumn (diagnosticToken item))))
  , ("message", JStr (diagnosticMessage item))
  ]
