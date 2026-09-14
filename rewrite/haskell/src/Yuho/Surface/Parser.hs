{-# LANGUAGE OverloadedStrings #-}
module Yuho.Surface.Parser (parseModel, parseScenario) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import Yuho.Surface.AST
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Token

newtype P a = P { runP :: FilePath -> [Token] -> Either Diagnostic (a, [Token]) }

instance Functor P where
  fmap f (P action) = P $ \path input -> do
    (value, rest) <- action path input
    pure (f value, rest)

instance Applicative P where
  pure value = P $ \_ input -> Right (value, input)
  P function <*> P value = P $ \path input -> do
    (f, rest) <- function path input
    (item, final) <- value path rest
    pure (f item, final)

instance Monad P where
  P action >>= function = P $ \path input -> do
    (value, rest) <- action path input
    runP (function value) path rest

current :: P Token
current = P $ \path input -> case input of
  token:_ -> Right (token, input)
  [] -> at "SFE001" path (Token EndToken "" 1 1) "unexpected end of source"

need :: Text -> P Token
need wanted = P $ \path input -> case input of
  token:rest | tokenText token == wanted -> Right (token, rest)
  token:_ -> at (if tokenText token `elem` deferred then "SFE013" else "SFE001")
    path token ("expected " <> wanted)
  [] -> at "SFE001" path (Token EndToken "" 1 1) ("expected " <> wanted)
  where deferred = ["exception", "presumption", "penalty", "sentence", "outcome", "evidence"]

kind :: Kind -> P Token
kind wanted = P $ \path input -> case input of
  token:rest | tokenKind token == wanted -> Right (token, rest)
  token:_ -> at "SFE001" path token "unexpected token kind"
  [] -> at "SFE001" path (Token EndToken "" 1 1) "unexpected end of source"

word :: P Token
word = kind WordToken

string :: P Token
string = kind StringToken

optional :: Text -> P Bool
optional wanted = do
  token <- current
  if tokenText token == wanted then need wanted >> pure True else pure False

manyBefore :: Text -> P a -> P [a]
manyBefore ending action = go []
  where
    go reversed = do
      token <- current
      if tokenText token == ending then pure (reverse reversed)
      else if tokenKind token == EndToken then need ending >> pure []
      else do
        item <- action
        go (item : reversed)

assignment :: P Assignment
assignment = do
  item <- word
  _ <- need "="
  status <- word
  hasReason <- optional "("
  reason <- if hasReason then do
    value <- word
    _ <- need ")"
    pure (Just value)
    else pure Nothing
  _ <- need ";"
  pure (Assignment item status reason)

assignments :: P [Assignment]
assignments = do
  _ <- need "{"
  rows <- manyBefore "}" assignment
  _ <- need "}"
  pure rows

group :: Token -> P Proposition
group headToken = do
  item <- word
  _ <- need "("
  first <- word
  more <- manyBefore ")" $ do
    _ <- need ","
    word
  _ <- need ")"
  _ <- need ";"
  pure (Group item (if tokenText headToken == "all" then All else Any) (first : more))

proposition :: P Proposition
proposition = do
  headToken <- word
  case tokenText headToken of
    "leaf" -> do
      item <- word
      _ <- need "proposition"
      propositionId <- word
      _ <- need "quote"
      quoteId <- word
      supported <- optional "support"
      support <- if supported then Just <$> word else pure Nothing
      _ <- need ";"
      pure (Leaf item (Just propositionId) quoteId support)
    "all" -> group headToken
    "any" -> group headToken
    _ -> P $ \path _ -> at "SFE005" path headToken "unsupported proposition"

elementOrGroup :: P (Either Element Proposition)
elementOrGroup = do
  headToken <- word
  case tokenText headToken of
    "element" -> do
      category <- word
      item <- word
      _ <- need "quote"
      quoteId <- word
      _ <- need ";"
      pure (Left (Element category item quoteId))
    "all" -> Right <$> group headToken
    "any" -> Right <$> group headToken
    _ -> P $ \path _ -> at "SFE013" path headToken "unsupported rule declaration"

rule :: Text -> P Rule
rule role = do
  headToken <- need role
  item <- word
  target <- if role == "exception" then do
    _ <- need "to"
    Just <$> word
    else pure Nothing
  _ <- need "rule"
  declaredRule <- word
  _ <- need "program"
  programId <- word
  _ <- need "path"
  path <- word
  _ <- need "{"
  declarations <- manyBefore "}" elementOrGroup
  _ <- need "}"
  pure (Rule headToken item target declaredRule programId path
    [value | Left value <- declarations] [value | Right value <- declarations])

provenance :: P ([SourceDecl], Maybe Token, [(Token, Token)])
provenance = do
  _ <- need "provenance"
  _ <- need "{"
  rows <- manyBefore "}" $ do
    headToken <- word
    case tokenText headToken of
      "source" -> do
        item <- word
        role <- word
        location <- string
        _ <- need ";"
        pure (Left (Left (SourceDecl item role location)))
      "mapping_source" -> do
        item <- word
        _ <- need ";"
        pure (Left (Right item))
      "quote" -> do
        item <- word
        value <- string
        _ <- need ";"
        pure (Right (item, value))
      _ -> P $ \path _ -> at "SFE013" path headToken "unsupported provenance declaration"
  _ <- need "}"
  let mappings = [item | Left (Right item) <- rows]
  case mappings of
    [] -> pure ([item | Left (Left item) <- rows], Nothing, [item | Right item <- rows])
    [mapping] -> pure ([item | Left (Left item) <- rows], Just mapping, [item | Right item <- rows])
    second:_ -> P $ \path _ -> at "SFE002" path second "duplicate mapping source"

annotations :: P (Token, Token, Token, Token)
annotations = do
  _ <- need "annotations"
  _ <- need "{"
  _ <- need "burden"
  a <- word
  b <- word
  c <- word
  d <- word
  _ <- need ";"
  _ <- need "}"
  pure (a, b, c, d)

limitations :: P [Token]
limitations = do
  _ <- need "limitations"
  _ <- need "{"
  values <- manyBefore "}" $ do
    value <- string
    _ <- need ";"
    pure value
  _ <- need "}"
  pure values

body :: P ([SourceDecl], [(Token, Token)], (Token, Token, Token, Token), Body)
body = do
  next <- current
  if tokenText next == "root" then do
    _ <- need "root"
    rootId <- word
    _ <- need "program"
    programId <- word
    _ <- need "path"
    path <- word
    _ <- need "requires"
    requirement <- word
    _ <- need ";"
    (sources, mapping, quotes) <- provenance
    burden <- annotations
    _ <- need "propositions"
    _ <- need "{"
    declarations <- manyBefore "}" proposition
    _ <- need "}"
    _ <- need "proof_assignments"
    assigned <- assignments
    case mapping of
      Nothing -> P $ \file _ -> at "SFE014" file rootId "mapping source required"
      Just source -> pure (sources, quotes, burden,
        Section rootId programId path requirement source declarations assigned)
  else do
    (sources, mapping, quotes) <- provenance
    case mapping of
      Just item -> P $ \file _ -> at "SFE014" file item "mapping source is unsupported for synthetic model"
      Nothing -> pure ()
    burden <- annotations
    offence <- rule "offence"
    exception <- rule "exception"
    _ <- need "outputs"
    _ <- need "{"
    outputs <- manyBefore "}" $ do
      label <- word
      target <- word
      _ <- need ";"
      pure (label, target)
    _ <- need "}"
    pure (sources, quotes, burden, Synthetic offence exception outputs)

modelParser :: P Model
modelParser = do
  _ <- need "model"
  item <- word
  _ <- need "{"
  _ <- need "variant"
  variant <- word
  _ <- need ";"
  _ <- need "jurisdiction"
  jurisdiction <- word
  _ <- need ";"
  _ <- need "purpose"
  purpose <- word
  _ <- need ";"
  _ <- need "request"
  requestId <- word
  _ <- need ";"
  _ <- need "policy"
  referenceDate <- word
  limit <- word
  _ <- need ";"
  (sources, quotes, burden, parsedBody) <- body
  limits <- limitations
  _ <- need "}"
  _ <- kind EndToken
  pure (Model item variant jurisdiction purpose requestId referenceDate limit
    sources quotes burden parsedBody limits)

parseModel :: FilePath -> BS.ByteString -> Either Diagnostic Model
parseModel path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP modelParser path tokens

scenarioParser :: P Scenario
scenarioParser = do
  _ <- need "scenario"
  requestId <- word
  _ <- need "for"
  modelId <- word
  assigned <- assignments
  _ <- kind EndToken
  pure (Scenario requestId modelId assigned)

parseScenario :: FilePath -> BS.ByteString -> Either Diagnostic Scenario
parseScenario path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP scenarioParser path tokens
