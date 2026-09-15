{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Surface.Temporal
  ( loadAuthoredInput ) where

import Control.Exception (IOException, try)
import qualified Data.ByteString as BS
import Data.List (sortOn)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time (Day, defaultTimeLocale, parseTimeM)
import System.FilePath (isAbsolute, takeDirectory, takeExtension, takeFileName, (</>))
import System.Posix.Files (fileSize, getSymbolicLinkStatus, isRegularFile)
import Yuho.Surface.Modules (AuthoredModel(..), loadAuthoredModel)
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Token

data Expression = Expression Token Token (Maybe Token) Token (Maybe Token)
  deriving (Eq, Show)
data TemporalModel = TemporalModel Token [Expression] deriving (Eq, Show)
data TemporalScenario = TemporalScenario Token Token Token deriving (Eq, Show)

newtype P a = P { runP :: FilePath -> [Token] -> Either Diagnostic (a,[Token]) }

instance Functor P where
  fmap f (P action) = P $ \path input -> do
    (value,rest) <- action path input
    pure (f value,rest)

instance Applicative P where
  pure value = P $ \_ input -> Right (value,input)
  P function <*> P value = P $ \path input -> do
    (f,rest) <- function path input
    (item,final) <- value path rest
    pure (f item,final)

instance Monad P where
  P action >>= function = P $ \path input -> do
    (value,rest) <- action path input
    runP (function value) path rest

current :: P Token
current = P $ \path input -> case input of
  token:_ -> Right (token,input)
  [] -> at "SFT001" path (Token EndToken "" 1 1) "unexpected end of temporal source"

takeText :: Text -> P Token
takeText wanted = P $ \path input -> case input of
  token:rest | tokenText token == wanted -> Right (token,rest)
  token:_ -> at "SFT001" path token ("expected " <> wanted)
  [] -> at "SFT001" path (Token EndToken "" 1 1) ("expected " <> wanted)

takeKind :: Kind -> P Token
takeKind wanted = P $ \path input -> case input of
  token:rest | tokenKind token == wanted -> Right (token,rest)
  token:_ -> at "SFT001" path token "unexpected temporal token"
  [] -> at "SFT001" path (Token EndToken "" 1 1) "unexpected end of temporal source"

word :: P Token
word = takeKind WordToken

string :: P Token
string = takeKind StringToken

expressionDecl :: P Expression
expressionDecl = do
  _ <- takeText "expression"
  item <- word
  _ <- takeText "effective-from"
  from <- word
  next <- current
  end <- if tokenText next == "effective-to" then do
      _ <- takeText "effective-to"
      Just <$> word
    else takeText "open-end" >> pure Nothing
  _ <- takeText "source-model"
  source <- string
  nextAfter <- current
  supersedes <- if tokenText nextAfter == "supersedes" then do
      _ <- takeText "supersedes"
      Just <$> word
    else pure Nothing
  _ <- takeText ";"
  pure (Expression item from end source supersedes)

expressions :: P [Expression]
expressions = do
  next <- current
  if tokenText next == "expression" then do
    item <- expressionDecl
    (item :) <$> expressions
  else pure []

modelParser :: P TemporalModel
modelParser = do
  _ <- takeText "temporal-model"
  item <- word
  _ <- takeText "{"
  alternatives <- expressions
  _ <- takeText "}"
  _ <- takeKind EndToken
  pure (TemporalModel item alternatives)

scenarioParser :: P TemporalScenario
scenarioParser = do
  _ <- takeText "temporal-scenario"
  item <- word
  _ <- takeText "{"
  _ <- takeText "conduct-date"
  conductDate <- word
  _ <- takeText ";"
  _ <- takeText "input"
  input <- string
  _ <- takeText ";"
  _ <- takeText "}"
  _ <- takeKind EndToken
  pure (TemporalScenario item conductDate input)

parseWith :: P a -> FilePath -> BS.ByteString -> Either Diagnostic a
parseWith parser path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP parser path tokens

dateValue :: FilePath -> Token -> Either Diagnostic Day
dateValue path token = maybe
  (at "SFT002" path token "invalid ISO conduct or effective date") Right
  (parseTimeM True defaultTimeLocale "%F" (Text.unpack (tokenText token)))

safeLocal :: Token -> Bool
safeLocal token = let value = Text.unpack (tokenText token) in
  not (null value) && not (isAbsolute value) && takeFileName value == value
    && takeExtension value == ".yh" && value /= "." && value /= ".."

readBounded :: FilePath -> FilePath -> Token -> IO (Either Diagnostic BS.ByteString)
readBounded path owner origin = do
  result <- try $ do
    status <- getSymbolicLinkStatus path
    if isRegularFile status && fileSize status <= 65536
      then BS.readFile path else ioError (userError "unsafe temporal file")
  pure $ case result of
    Left (_ :: IOException) -> Left (Diagnostic "SFT003" owner origin
      "temporal source or input unavailable, unsafe or too large" Nothing)
    Right bytes -> Right bytes

data DatedExpression = DatedExpression Expression Day (Maybe Day)

validateExpressions :: FilePath -> Token -> [Expression]
  -> Either Diagnostic [DatedExpression]
validateExpressions path modelId alternatives = do
  if length alternatives < 2 then
    at "SFT004" path modelId "temporal model requires at least two complete expressions"
  else Right ()
  let ids = [tokenText item | Expression item _ _ _ _ <- alternatives]
  if Set.size (Set.fromList ids) == length ids then Right ()
  else at "SFT004" path modelId "duplicate temporal expression identifier"
  dated <- traverse convert alternatives
  let ordered = sortOn (\(DatedExpression _ from _) -> from) dated
  validatePairs ordered
  pure ordered
  where
    convert expression@(Expression _ from end source _) = do
      if safeLocal source then Right ()
      else at "SFT003" path source "unsafe temporal source-model reference"
      start <- dateValue path from
      finish <- traverse (dateValue path) end
      case finish of
        Just value | value <= start -> at "SFT004" path from
          "effective interval must end after it starts"
        _ -> Right (DatedExpression expression start finish)
    validatePairs [] = Right ()
    validatePairs [_] = Right ()
    validatePairs (DatedExpression _ _ Nothing:DatedExpression (Expression next _ _ _ _) _ _:_) =
      at "SFT005" path next "open-ended expression overlaps a later expression"
    validatePairs (DatedExpression _ _ (Just finish):rest@(DatedExpression (Expression next _ _ _ _) start _:_))
      | finish < start = at "SFT005" path next "gap between authored effective intervals"
      | finish > start = at "SFT005" path next "overlapping authored effective intervals"
      | otherwise = validatePairs rest

loadAuthoredInput :: FilePath -> BS.ByteString
  -> Maybe (FilePath, BS.ByteString)
  -> IO (Either Diagnostic (AuthoredModel, Maybe (FilePath, BS.ByteString)))
loadAuthoredInput path bytes supplied = case lexSource path bytes of
  Right (first:_) | tokenText first == "temporal-model" -> loadTemporal path bytes supplied
  _ -> do
    authored <- loadAuthoredModel path bytes
    pure ((\item -> (item,supplied)) <$> authored)

loadTemporal :: FilePath -> BS.ByteString -> Maybe (FilePath, BS.ByteString)
  -> IO (Either Diagnostic (AuthoredModel, Maybe (FilePath, BS.ByteString)))
loadTemporal path bytes supplied = case parseWith modelParser path bytes of
  Left issue -> pure (Left issue)
  Right (TemporalModel modelId alternatives) -> case supplied of
    Nothing -> pure (at "SFT006" path modelId
      "temporal model requires a temporal scenario with conduct-date")
    Just (scenarioPath,scenarioBytes) -> case parseWith scenarioParser scenarioPath scenarioBytes of
      Left issue -> pure (Left issue)
      Right (TemporalScenario _ conductToken inputToken) -> case
          (validateExpressions path modelId alternatives, dateValue scenarioPath conductToken) of
        (Left issue,_) -> pure (Left issue)
        (_,Left issue) -> pure (Left issue)
        (Right dated,Right conductDate) -> case [expression |
            DatedExpression expression start end <- dated,
            start <= conductDate, maybe True (conductDate <) end] of
          [] -> pure (at "SFT007" scenarioPath conductToken
            "conduct-date falls in no authored effective interval")
          _:_:_ -> pure (at "SFT007" scenarioPath conductToken
            "conduct-date matches multiple authored effective intervals")
          [Expression expressionId from end source supersedes] -> do
            let modelPath = takeDirectory path </> Text.unpack (tokenText source)
                inputPath = takeDirectory scenarioPath </> Text.unpack (tokenText inputToken)
            if not (safeLocal inputToken) then pure (at "SFT003" scenarioPath inputToken
              "unsafe temporal input reference")
            else do
              modelResult <- readBounded modelPath path source
              scenarioResult <- readBounded inputPath scenarioPath inputToken
              case (modelResult,scenarioResult) of
                (Left issue,_) -> pure (Left issue)
                (_,Left issue) -> pure (Left issue)
                (Right modelBytes,Right selectedScenario) -> do
                  loaded <- loadAuthoredModel modelPath modelBytes
                  pure $ do
                    authored <- loaded
                    if authoredHost authored /= Nothing then at "SFT008" path source
                      "temporal expressions cannot select another wrapper model"
                    else Right (authored
                      { authoredHost = Just (tokenText modelId)
                      , authoredImports =
                          [("effective-expression",tokenText expressionId,
                            intervalText from end supersedes conductToken)]
                      },Just (inputPath,selectedScenario))

intervalText :: Token -> Maybe Token -> Maybe Token -> Token -> Text
intervalText from end supersedes conduct =
  "conduct-date=" <> tokenText conduct <> "; " <> tokenText from <> " <= date < "
  <> maybe "open" tokenText end <> maybe "" ("; supersedes-metadata=" <>) (tokenText <$> supersedes)
