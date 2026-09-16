{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Surface.Presumption
  ( PresumptionProgram(..), loadPresumptionProgram, explainPresumptionProgram ) where

import Control.Exception (IOException, try)
import qualified Data.ByteString as BS
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import System.FilePath (isAbsolute, takeDirectory, takeExtension, takeFileName, (</>))
import System.Posix.Files (fileSize, getSymbolicLinkStatus, isRegularFile)
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson, lookupField, objectFields, textValue)
import Yuho.Surface.Compile (compileParsed)
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Modules (AuthoredModel(..), loadAuthoredModel)
import Yuho.Surface.Token

data Registration = Registration Token Token Token Token Token deriving (Eq, Show)

data PresumptionProgram = PresumptionProgram
  { presumptionName :: Token
  , presumptionBurdenBearer :: Token
  , presumptionStandard :: Token
  , presumptionNote :: Token
  , presumptionRegistrations :: [(Text,Text,Text,Text,Text)]
  , presumptionRequest :: BS.ByteString
  , presumptionResult :: BS.ByteString
  } deriving (Eq, Show)

newtype P a = P { runP :: FilePath -> [Token] -> Either Diagnostic (a,[Token]) }

instance Functor P where
  fmap f (P action) = P $ \path input -> do
    (value,rest) <- action path input
    pure (f value,rest)

instance Applicative P where
  pure value = P $ \_ input -> Right (value,input)
  P function <*> P action = P $ \path input -> do
    (f,rest) <- function path input
    (item,final) <- action path rest
    pure (f item,final)

instance Monad P where
  P action >>= function = P $ \path input -> do
    (value,rest) <- action path input
    runP (function value) path rest

takeText :: Text -> P Token
takeText wanted = P $ \path input -> case input of
  token:rest | tokenText token == wanted -> Right (token,rest)
  token:_ -> at "SFR001" path token ("expected " <> wanted)
  [] -> at "SFR001" path (Token EndToken "" 1 1) ("expected " <> wanted)

takeKind :: Kind -> P Token
takeKind wanted = P $ \path input -> case input of
  token:rest | tokenKind token == wanted -> Right (token,rest)
  token:_ -> at "SFR001" path token "unexpected presumption token"
  [] -> at "SFR001" path (Token EndToken "" 1 1) "unexpected end of presumption source"

word :: P Token
word = takeKind WordToken

string :: P Token
string = takeKind StringToken

current :: P Token
current = P $ \path input -> case input of
  token:_ -> Right (token,input)
  [] -> at "SFR001" path (Token EndToken "" 1 1) "unexpected end of presumption source"

registration :: P Registration
registration = do
  _ <- takeText "presumption"
  item <- word
  _ <- takeText "target"
  target <- word
  _ <- takeText "source"
  source <- word
  _ <- takeText "trigger"
  trigger <- word
  _ <- takeText "rebuttal"
  rebuttal <- word
  _ <- takeText ";"
  pure (Registration item target source trigger rebuttal)

programParser :: P (Token,Token,Token,Token,Token,Token,[Registration])
programParser = do
  _ <- takeText "presumption-program"
  name <- word
  _ <- takeText "{"
  _ <- takeText "base-model"
  model <- string
  _ <- takeText ";"
  _ <- takeText "base-scenario"
  scenario <- string
  _ <- takeText ";"
  _ <- takeText "burden"
  _ <- takeText "bearer"
  bearer <- word
  _ <- takeText "standard"
  standard <- word
  _ <- takeText "note"
  note <- string
  _ <- takeText ";"
  registrations <- manyRegistrations
  _ <- takeText "}"
  _ <- takeKind EndToken
  pure (name,model,scenario,bearer,standard,note,registrations)
  where
    manyRegistrations = do
      next <- current
      if tokenText next == "presumption" then do
        item <- registration
        (item :) <$> manyRegistrations
      else pure []

loadPresumptionProgram :: FilePath -> BS.ByteString
  -> IO (Either Diagnostic PresumptionProgram)
loadPresumptionProgram path bytes = case lexSource path bytes >>= \tokens ->
    fst <$> runP programParser path tokens of
  Left issue -> pure (Left issue)
  Right (name,modelToken,scenarioToken,bearer,standard,note,registrations) -> do
    let resolve token = takeDirectory path </> Text.unpack (tokenText token)
    if not (safeSibling modelToken && safeSibling scenarioToken)
      then pure (at "SFR002" path modelToken
        "presumption base model and scenario must be sibling .yh files")
      else do
        modelBytes <- readBounded path modelToken (resolve modelToken)
        scenarioBytes <- readBounded path scenarioToken (resolve scenarioToken)
        case (modelBytes,scenarioBytes) of
          (Right rawModel,Right rawScenario) -> do
            authored <- loadAuthoredModel (resolve modelToken) rawModel
            pure $ do
              loaded <- authored
              if null registrations || length registrations > 16 then
                at "SFR003" path name "presumption program requires 1 to 16 registrations"
              else pure ()
              let identities = [tokenText item
                    | Registration item _ _ _ _ <- registrations]
              if length identities == Set.size (Set.fromList identities)
                  && all ("pres:" `Text.isPrefixOf`) identities
                then pure () else at "SFR003" path name
                  "presumption identities must be unique typed pres: identifiers"
              base <- compileParsed (resolve modelToken) (authoredModel loaded)
                (Just (resolve scenarioToken,rawScenario))
              value <- either (\_ -> at "SFR004" path name
                "compiled presumption base is not JSON") Right (decodeJson base)
              requestValue <- addRegistrations path registrations value
              let request = encodeJson requestValue
                  result = runLine request
              response <- either (\_ -> at "SFR004" path name
                "presumption kernel response is not JSON") Right (decodeJson result)
              case lookupField "status" response >>= textValue of
                Just "rejected" -> at "SFR004" path name
                  "registered-presumption kernel rejected the authored program"
                Just _ -> Right (PresumptionProgram name bearer standard note
                  [(tokenText item,tokenText target,tokenText source,
                    tokenText trigger,tokenText rebuttal)
                  | Registration item target source trigger rebuttal <- registrations]
                  request result)
                Nothing -> at "SFR004" path name "presumption response has no status"
          (Left issue,_) -> pure (Left issue)
          (_,Left issue) -> pure (Left issue)

safeSibling :: Token -> Bool
safeSibling token = let value = Text.unpack (tokenText token) in
  not (null value) && not (isAbsolute value) && takeFileName value == value
    && takeExtension value == ".yh" && value /= "." && value /= ".."

readBounded :: FilePath -> Token -> FilePath -> IO (Either Diagnostic BS.ByteString)
readBounded owner origin file = do
  result <- try $ do
    status <- getSymbolicLinkStatus file
    if isRegularFile status && fileSize status <= 65536
      then BS.readFile file else ioError (userError "unsafe presumption input")
  pure $ case result of
    Left (_ :: IOException) -> Left (Diagnostic "SFR002" owner origin
      "presumption base model or scenario unavailable, unsafe or too large" Nothing)
    Right value -> Right value

addRegistrations :: FilePath -> [Registration] -> J -> Either Diagnostic J
addRegistrations path registrations root = do
  fields <- maybe (at "SFR004" path origin "compiled base request must be an object")
    Right (objectFields root)
  facts <- case lookupField "facts" root >>= objectFields of
    Just values -> Right values
    Nothing -> at "SFR004" path origin "compiled base request has no proof facts"
  sources <- case lookupField "sources" root of
    Just (JArr values) -> Right values
    _ -> at "SFR004" path origin "compiled base request has no sources"
  spanValue <- firstProgramSpan root
  rows <- mapM (registrationJson facts sources spanValue) registrations
  pure (JObj ([ (key, if key == "fragment" then JStr
      "RegisteredPresumptionDerivations-v1" else value)
    | (key,value) <- fields, key /= "presumptions"] ++ [("presumptions",JArr rows)]))
  where
    origin = Token EndToken "" 1 1
    registrationJson facts sources spanValue (Registration item target source trigger rebuttal) = do
      mapM_ (knownFact facts) [target,trigger,rebuttal]
      if any (sourceMatches source) sources then pure () else
        at "SFR005" path source "unknown presumption source"
      pure (JObj
        [("presumption_id",JStr (tokenText item))
        ,("target_leaf_id",JStr (tokenText target))
        ,("source_id",JStr (tokenText source))
        ,("span",spanValue)
        ,("trigger",condition spanValue trigger)
        ,("rebuttal",condition spanValue rebuttal)])
    knownFact facts token = if any ((== tokenText token) . fst) facts then Right ()
      else at "SFR005" path token "presumption target, trigger or rebuttal is not a primitive proof fact"
    sourceMatches token value = (lookupField "id" value >>= textValue) == Just (tokenText token)
    condition spanValue token = JObj
      [("kind",JStr "leaf_effective"),("leaf_id",JStr (tokenText token)),("span",spanValue)]

firstProgramSpan :: J -> Either Diagnostic J
firstProgramSpan root = case lookupField "registry" root of
  Just (JArr (first:_)) -> case lookupField "program" first >>= lookupField "span" of
    Just value -> Right value
    Nothing -> failure
  _ -> failure
  where failure = Left (Diagnostic "SFR004" "<presumption>"
          (Token EndToken "" 1 1) "compiled base request has no source span" Nothing)

explainPresumptionProgram :: PresumptionProgram -> Either Diagnostic Text
explainPresumptionProgram program = do
  value <- either (const failure) Right (decodeJson (presumptionResult program))
  status <- maybe failure Right (lookupField "status" value >>= textValue)
  rows <- case lookupField "presumption_derivations" value of
    Just (JArr values) -> Right values
    _ -> failure
  let render row = case (lookupField "presumption_id" row >>= textValue,
        lookupField "state" row >>= textValue,
        lookupField "target_direct_satisfaction" row >>= textValue,
        lookupField "target_effective_satisfaction" row >>= textValue) of
        (Just item,Just state,Just direct,Just effective) ->
          "  " <> item <> ": " <> state <> "; target direct " <> direct
            <> ", effective " <> effective
        _ -> "  malformed derivation"
  pure (Text.unlines
    (["Presumption technical subprogram: " <> tokenText (presumptionName program)
     ,"Kernel fragment: RegisteredPresumptionDerivations-v1"
     ,"Burden bearer annotation: " <> tokenText (presumptionBurdenBearer program)
     ,"Authored standard annotation: " <> tokenText (presumptionStandard program)
     ,"Context: " <> tokenText (presumptionNote program)
     ,"Derivations:"] ++ map render rows ++
     ["Final technical proof status: " <> status
     ,"This subprogram applies supplied classifications; it does not assess evidence or determine that a legal burden was discharged."
     ,"No guilt, conviction, acquittal, liability, punishment or sentence was determined."]))
  where failure = Left (Diagnostic "SFR004" "<presumption>"
          (presumptionName program) "presumption explanation unavailable" Nothing)
