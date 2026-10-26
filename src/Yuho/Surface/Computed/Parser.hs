{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Computed.Parser
  ( Project(..), Selection(..), AssertionSource(..), parseProject ) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Token

data Selection = Selection
  { selectionId :: Token, selectionRule :: Token, selectionObject :: Token
  , selectionActor :: Token, selectionContext :: Token } deriving (Eq, Show)
data AssertionSource = AssertionSource Token Token Token deriving (Eq, Show)
data Project = Project
  { projectId :: Token, sourceModel :: Token, sourceScenario :: Token
  , sourceSelection :: Selection, destinationModel :: Token
  , destinationScenario :: Maybe Token, destinationSelection :: Selection
  , bindingId :: Token, bindingMapping :: Token, bindingUnresolved :: Token
  , bindingRationale :: Token, projectLabels :: [(Token,Token)]
  , projectAssertions :: [AssertionSource] } deriving (Eq, Show)

newtype P a = P { runP :: FilePath -> [Token] -> Either Diagnostic (a,[Token]) }
instance Functor P where fmap f (P p) = P $ \s ts -> do (a,rest)<-p s ts; pure (f a,rest)
instance Applicative P where
  pure a = P $ \_ ts -> Right (a,ts)
  P f <*> P a = P $ \s ts -> do (g,rest)<-f s ts; (x,end)<-a s rest; pure (g x,end)
instance Monad P where P p >>= f = P $ \s ts -> do (a,rest)<-p s ts; runP (f a) s rest
peek :: P Token
peek = P $ \p ts -> case ts of
  t:_ -> Right (t,ts)
  [] -> at "SFC001" p (Token EndToken "" 1 1) "unexpected end of computed-project"
takeWhen :: (Token -> Bool) -> Text -> P Token
takeWhen test expected = P $ \p ts -> case ts of
  t:rest | test t -> Right (t,rest)
  t:_ -> at "SFC001" p t ("expected " <> expected)
  [] -> at "SFC001" p (Token EndToken "" 1 1) ("expected " <> expected)
keyword :: Text -> P Token
keyword value = takeWhen (matchesSyntax value) value
word, string :: P Token
word = takeWhen ((==WordToken) . tokenKind) "identifier"
string = takeWhen ((==StringToken) . tokenKind) "quoted text"
file :: Text -> P Token
file name = keyword name >> string <* keyword ";"
selection :: Text -> Text -> P Selection
selection name objectKind = do
  _<-keyword name; i<-word; _<-keyword "rule"; r<-word
  _<-keyword objectKind; o<-word; _<-keyword "actor"; a<-word
  _<-keyword "context"; c<-word; _<-keyword ";"
  pure (Selection i r o a c)
parser :: P Project
parser = do
  _<-keyword "computed-project"; i<-word; _<-keyword "{"
  m<-file "source-model"; s<-file "source-scenario"
  a<-selection "source-analysis" "expression"
  d<-file "destination-model"
  next<-peek
  ds<-if tokenText next=="destination-scenario" then Just <$> file "destination-scenario" else pure Nothing
  da<-selection "destination-analysis" "input"
  _<-keyword "binding"; b<-word; _<-keyword "mapping"; policy<-string
  _<-keyword "unresolved"; reason<-word; _<-keyword "rationale"; rationale<-string; _<-keyword ";"
  (labels,assertions)<-extras
  _<-keyword "}"; _<-takeWhen ((==EndToken) . tokenKind) "end of source"
  pure (Project i m s a d ds da b policy reason rationale labels assertions)
  where
    extras = do
      next<-peek
      case tokenText next of
        "label" -> do
          _<-keyword "label"; key<-word; value<-string; _<-keyword ";"
          (ls,as)<-extras; pure ((key,value):ls,as)
        "assertion" -> do
          _<-keyword "assertion"; key<-word; _<-keyword "for"; expr<-word
          src<-file "source"
          (ls,as)<-extras; pure (ls,AssertionSource key expr src:as)
        _ -> pure ([],[])
parseProject :: FilePath -> BS.ByteString -> Either Diagnostic Project
parseProject path bytes = lexSource path bytes >>= fmap fst . runP parser path
