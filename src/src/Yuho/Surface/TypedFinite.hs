{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Surface.TypedFinite
  ( loadTypedFiniteProgram, parseTypedFiniteModel, parseTypedFiniteScenario
  , TypedFiniteScenario(..), TypedFiniteCase(..), TypedFiniteAllegation(..)
  , loadTypedFiniteCase, encodeTypedFiniteRequest, encodeTypedFiniteCase
  , explainTypedFinite, explainTypedFiniteCase
  ) where

import Control.Exception (IOException, try)
import Control.Monad (unless, when)
import qualified Data.ByteString as BS
import Data.List (nub)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Calendar (Day)
import Data.Time.Format (defaultTimeLocale, parseTimeM)
import System.FilePath ((</>), isAbsolute, takeDirectory)
import System.Posix.Files (fileSize, getSymbolicLinkStatus, isRegularFile)
import Yuho.CoreYuho.TypedFinite
import Yuho.Exception.Types (Truth(..))
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson)
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Token

data RawScalarType = RawInteger | RawDate | RawEnum Token | RawMoney Token
  deriving (Eq, Show)

data RawModel = RawModel
  { rawModelId :: Token
  , rawLimit :: Token
  , rawEntityTypes :: [Token]
  , rawEntities :: [(Token,Token)]
  , rawEnums :: [(Token,[Token])]
  , rawScalars :: [(Token,RawScalarType)]
  , rawPredicates :: [(Token,[Token],Token)]
  , rawPropositions :: [Token]
  , rawRequirements :: [(Token,FiniteExpr)]
  , rawRules :: [(Token,[(Token,Token)],Token,Token,FiniteExpr,Maybe Token)]
  , rawNorms :: [(Token,Token,Token,Token,FiniteExpr,Maybe Token)]
  , rawRoutes :: [(Token,Token,Token,Token,FiniteExpr,Maybe Token)]
  , rawPriorities :: [(Token,Token)]
  , rawModuleRoot :: Maybe Token
  , rawImports :: [(Token,Token,Token)]
  , rawUses :: [(Token,Token)]
  , rawLimitations :: [Token]
  } deriving (Eq, Show)

data RawModule = RawModule Token Token [(Token,Token)] RawModel deriving (Eq, Show)

data TypedFiniteScenario = TypedFiniteScenario
  { scenarioIdentifier :: Token
  , scenarioModel :: Token
  , scenarioFacts :: [(Token,[Token],Token,Token)]
  , scenarioValues :: [(Token,RawValue)]
  } deriving (Eq, Show)

data RawValue
  = RawIntegerValue Token
  | RawDateValue Token
  | RawEnumValue Token Token
  | RawMoneyValue Token Token
  | RawUnresolvedValue Token
  deriving (Eq, Show)

data TypedFiniteAllegation = TypedFiniteAllegation
  { typedAllegationId :: Text
  , typedAllegationProgram :: TypedFiniteProgram
  , typedAllegationResult :: TypedFiniteResult
  } deriving (Eq, Show)

data TypedFiniteCase = TypedFiniteCase
  { typedCaseId :: Text
  , typedCaseShared :: [(Text,GroundFact,[Text])]
  , typedCaseAllegations :: [TypedFiniteAllegation]
  } deriving (Eq, Show)

newtype P a = P { runP :: FilePath -> [Token] -> Either Diagnostic (a,[Token]) }

instance Functor P where
  fmap function (P action) = P $ \path input -> do
    (value,rest) <- action path input
    pure (function value,rest)

instance Applicative P where
  pure value = P $ \_ input -> Right (value,input)
  P function <*> P action = P $ \path input -> do
    (apply,rest) <- function path input
    (value,final) <- action path rest
    pure (apply value,final)

instance Monad P where
  P action >>= next = P $ \path input -> do
    (value,rest) <- action path input
    runP (next value) path rest

current :: P Token
current = P $ \path input -> case input of
  token:_ -> Right (token,input)
  [] -> at "SFT001" path origin "unexpected end of typed-rules source"
  where origin = Token EndToken "" 1 1

takeText :: Text -> P Token
takeText wanted = P $ \path input -> case input of
  token:rest | tokenText token == wanted -> Right (token,rest)
  token:_ -> at "SFT001" path token ("expected " <> wanted)
  [] -> at "SFT001" path (Token EndToken "" 1 1) ("expected " <> wanted)

word :: P Token
word = P $ \path input -> case input of
  token:rest | tokenKind token == WordToken -> Right (token,rest)
  token:_ -> at "SFT001" path token "expected word"
  [] -> at "SFT001" path (Token EndToken "" 1 1) "expected word"

string :: P Token
string = P $ \path input -> case input of
  token:rest | tokenKind token == StringToken -> Right (token,rest)
  token:_ -> at "SFT001" path token "expected string"
  [] -> at "SFT001" path (Token EndToken "" 1 1) "expected string"

optionalText :: Text -> P Bool
optionalText wanted = do
  token <- current
  if tokenText token == wanted then takeText wanted >> pure True else pure False

manyBefore :: Text -> P a -> P [a]
manyBefore ending action = go []
  where
    go reversed = do
      token <- current
      if tokenText token == ending then pure (reverse reversed)
      else if tokenKind token == EndToken then takeText ending >> pure []
      else action >>= \item -> go (item:reversed)

commaList :: P a -> P [a]
commaList action = do
  token <- current
  if tokenText token == ")" then pure [] else do
    first <- action
    rest <- more
    pure (first:rest)
  where
    more = do
      token <- current
      if tokenText token == ")" then pure [] else do
        _ <- takeText ","
        item <- action
        (item:) <$> more

parseExpression :: P FiniteExpr
parseExpression = do
  headToken <- word
  case tokenText headToken of
    "all" -> aggregate AllExpr
    "any" -> aggregate AnyExpr
    "not" -> do
      _ <- takeText "("
      member <- parseExpression
      _ <- takeText ")"
      pure (NotExpr member)
    "forall" -> quantified ForallExpr
    "exists" -> quantified ExistsExpr
    "at-least" -> cardinal AtLeast
    "at-most" -> cardinal AtMost
    "exactly" -> cardinal Exactly
    "compare" -> comparison
    value | "q:" `Text.isPrefixOf` value -> pure (ReferenceExpr value)
    name -> do
      _ <- takeText "("
      arguments <- commaList term
      _ <- takeText ")"
      pure (PredicateExpr name arguments)
  where
    aggregate constructor = do
      _ <- takeText "("
      members <- commaList parseExpression
      _ <- takeText ")"
      pure (constructor members)
    quantified constructor = do
      variable <- word
      _ <- takeText "as"
      kindValue <- word
      _ <- takeText "("
      body <- parseExpression
      _ <- takeText ")"
      pure (constructor (tokenText variable) (tokenText kindValue) body)
    cardinal kindValue = do
      threshold <- word
      amount <- integerToken threshold
      _ <- takeText "("
      members <- commaList parseExpression
      _ <- takeText ")"
      pure (CardinalityExpr kindValue (fromInteger amount) members)
    comparison = do
      _ <- takeText "("
      left <- word
      _ <- takeText ","
      operation <- word
      _ <- takeText ","
      right <- word
      upper <- if tokenText operation == "in-half-open" then do
        _ <- takeText ","
        Just <$> word
        else pure Nothing
      _ <- takeText ")"
      parsed <- comparisonToken operation
      pure (ComparisonExpr parsed (tokenText left) (tokenText right) (tokenText <$> upper))
    term = do
      item <- word
      pure $ if "var:" `Text.isPrefixOf` tokenText item
        then VariableTerm (tokenText item) else EntityTerm (tokenText item)

comparisonToken :: Token -> P Comparison
comparisonToken token = case tokenText token of
  "eq" -> pure Equal
  "neq" -> pure NotEqual
  "lt" -> pure LessThan
  "lte" -> pure LessEqual
  "gt" -> pure GreaterThan
  "gte" -> pure GreaterEqual
  "in-half-open" -> pure InHalfOpen
  _ -> P $ \path _ -> at "SFT008" path token "unsupported comparison"

integerToken :: Token -> P Integer
integerToken token = case reads (Text.unpack (tokenText token)) of
  [(value,"")] -> pure value
  _ -> P $ \path _ -> at "SFT008" path token "expected integer"

parseModelDeclaration :: P (RawModel -> RawModel)
parseModelDeclaration = do
  headToken <- word
  case tokenText headToken of
    "limit" -> do
      value <- word
      _ <- takeText ";"
      pure (\model -> model { rawLimit = value })
    "module-root" -> do
      root <- string
      _ <- takeText ";"
      pure (\model -> model { rawModuleRoot = Just root })
    "import" -> do
      name <- word
      _ <- takeText "version"
      version <- word
      _ <- takeText "as"
      alias <- word
      _ <- takeText ";"
      pure (\model -> model { rawImports = rawImports model ++ [(name,version,alias)] })
    "use" -> do
      kindValue <- word
      identifier <- word
      _ <- takeText ";"
      pure (\model -> model { rawUses = rawUses model ++ [(kindValue,identifier)] })
    "entity-type" -> do
      identifier <- word
      _ <- takeText ";"
      pure (\model -> model { rawEntityTypes = rawEntityTypes model ++ [identifier] })
    "entity" -> do
      identifier <- word
      _ <- takeText "as"
      kindValue <- word
      _ <- takeText ";"
      pure (\model -> model { rawEntities = rawEntities model ++ [(identifier,kindValue)] })
    "enum-type" -> do
      identifier <- word
      _ <- takeText "values"
      first <- word
      rest <- enumRest
      _ <- takeText ";"
      pure (\model -> model { rawEnums = rawEnums model ++ [(identifier,first:rest)] })
    "scalar" -> do
      identifier <- word
      _ <- takeText "type"
      typeToken <- word
      declaredType <- case tokenText typeToken of
        "integer" -> pure RawInteger
        "date" -> pure RawDate
        "enum" -> RawEnum <$> word
        "money" -> RawMoney <$> word
        _ -> P $ \path _ -> at "SFT008" path typeToken "unsupported scalar type"
      _ <- takeText ";"
      pure (\model -> model { rawScalars = rawScalars model ++ [(identifier,declaredType)] })
    "predicate" -> do
      identifier <- word
      _ <- takeText "("
      arguments <- commaList word
      _ <- takeText ")"
      _ <- takeText "kind"
      kindValue <- word
      _ <- takeText ";"
      pure (\model -> model { rawPredicates = rawPredicates model
        ++ [(identifier,arguments,kindValue)] })
    "proposition" -> do
      identifier <- word
      _ <- takeText ";"
      pure (\model -> model { rawPropositions = rawPropositions model ++ [identifier] })
    "requirement" -> do
      identifier <- word
      _ <- takeText "="
      expression <- parseExpression
      _ <- takeText ";"
      pure (\model -> model { rawRequirements = rawRequirements model
        ++ [(identifier,expression)] })
    "rule" -> do
      identifier <- word
      hasParameters <- optionalText "("
      parameters <- if hasParameters then do
        values <- commaList parameter
        _ <- takeText ")"
        pure values else pure []
      polarity <- word
      _ <- takeText "proposition"
      conclusion <- word
      _ <- takeText "when"
      body <- parseExpression
      hasCitation <- optionalText "citation"
      citation <- if hasCitation then Just <$> string else pure Nothing
      _ <- takeText ";"
      pure (\model -> model { rawRules = rawRules model
        ++ [(identifier,parameters,polarity,conclusion,body,citation)] })
    "norm" -> do
      identifier <- word
      _ <- takeText "subject"
      subject <- word
      _ <- takeText "modality"
      modality <- word
      _ <- takeText "action"
      _ <- takeText "proposition"
      action <- word
      _ <- takeText "when"
      body <- parseExpression
      hasCitation <- optionalText "citation"
      citation <- if hasCitation then Just <$> string else pure Nothing
      _ <- takeText ";"
      pure (\model -> model { rawNorms = rawNorms model
        ++ [(identifier,subject,modality,action,body,citation)] })
    "responsibility-route" -> do
      identifier <- word
      _ <- takeText "subject"
      subject <- word
      _ <- takeText "kind"
      kindValue <- word
      _ <- takeText "target"
      _ <- takeText "proposition"
      target <- word
      _ <- takeText "when"
      body <- parseExpression
      hasCitation <- optionalText "citation"
      citation <- if hasCitation then Just <$> string else pure Nothing
      _ <- takeText ";"
      pure (\model -> model { rawRoutes = rawRoutes model
        ++ [(identifier,subject,kindValue,target,body,citation)] })
    "priority" -> do
      higher <- word
      _ <- takeText "over"
      lower <- word
      _ <- takeText ";"
      pure (\model -> model { rawPriorities = rawPriorities model ++ [(higher,lower)] })
    "limitation" -> do
      value <- string
      _ <- takeText ";"
      pure (\model -> model { rawLimitations = rawLimitations model ++ [value] })
    _ -> P $ \path _ -> at "SFT001" path headToken "unsupported typed-rules declaration"
  where
    enumRest = do
      token <- current
      if tokenText token == ";" then pure [] else do
        _ <- takeText ","
        item <- word
        (item:) <$> enumRest
    parameter = do
      variable <- word
      _ <- takeText "as"
      kindValue <- word
      pure (variable,kindValue)

parseTypedFiniteModel :: FilePath -> BS.ByteString -> Either Diagnostic RawModel
parseTypedFiniteModel path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP parser path tokens
  where
    parser = do
      _ <- takeText "typed-rules-model"
      identifier <- word
      _ <- takeText "{"
      declarations <- manyBefore "}" parseModelDeclaration
      _ <- takeText "}"
      _ <- P $ \source tokens -> case tokens of
        token:rest | tokenKind token == EndToken -> Right (token,rest)
        token:_ -> at "SFT001" source token "trailing typed-rules source"
        [] -> at "SFT001" source (Token EndToken "" 1 1) "missing end token"
      let emptyModel = emptyRawModel identifier
      pure (foldl (flip ($)) emptyModel declarations)

emptyRawModel :: Token -> RawModel
emptyRawModel identifier = RawModel identifier (Token WordToken "2048" 1 1)
  [] [] [] [] [] [] [] [] [] [] [] Nothing [] [] []

parseTypedFiniteModule :: FilePath -> BS.ByteString -> Either Diagnostic RawModule
parseTypedFiniteModule path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP parser path tokens
  where
    parser = do
      _ <- takeText "typed-rules-module"
      name <- word
      _ <- takeText "version"
      version <- word
      _ <- takeText "{"
      entries <- manyBefore "}" moduleEntry
      _ <- takeText "}"
      _ <- P $ \source tokens -> case tokens of
        token:rest | tokenKind token == EndToken -> Right (token,rest)
        token:_ -> at "SFT001" source token "trailing typed-rules module"
        [] -> at "SFT001" source (Token EndToken "" 1 1) "missing end token"
      let exports = [value | Left value <- entries]
          declarations = [value | Right value <- entries]
          model = foldl (flip ($)) (emptyRawModel name) declarations
      pure (RawModule name version exports model)
    moduleEntry = do
      token <- current
      if tokenText token == "export" then do
        _ <- takeText "export"
        kindValue <- word
        identifier <- word
        _ <- takeText ";"
        pure (Left (kindValue,identifier))
      else Right <$> parseModelDeclaration

parseTypedFiniteScenario :: FilePath -> BS.ByteString -> Either Diagnostic TypedFiniteScenario
parseTypedFiniteScenario path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP parser path tokens
  where
    parser = do
      _ <- takeText "typed-rules-scenario"
      identifier <- word
      _ <- takeText "for"
      model <- word
      _ <- takeText "{"
      entries <- manyBefore "}" entry
      _ <- takeText "}"
      _ <- P $ \source tokens -> case tokens of
        token:rest | tokenKind token == EndToken -> Right (token,rest)
        token:_ -> at "SFT001" source token "trailing typed-rules scenario"
        [] -> at "SFT001" source (Token EndToken "" 1 1) "missing end token"
      pure (TypedFiniteScenario identifier model
        [value | Left value <- entries] [value | Right value <- entries])
    entry = do
      headToken <- word
      case tokenText headToken of
        "classify" -> do
          predicate <- word
          _ <- takeText "("
          arguments <- commaList word
          _ <- takeText ")"
          _ <- takeText "as"
          status <- word
          _ <- takeText "reason"
          reason <- string
          _ <- takeText ";"
          pure (Left (predicate,arguments,status,reason))
        "value" -> do
          identifier <- word
          _ <- takeText "="
          valueKind <- word
          value <- case tokenText valueKind of
            "integer" -> RawIntegerValue <$> word
            "date" -> RawDateValue <$> word
            "enum" -> RawEnumValue <$> word <*> word
            "money" -> RawMoneyValue <$> word <*> word
            "unresolved" -> do
              _ <- takeText "reason"
              RawUnresolvedValue <$> string
            _ -> P $ \source _ -> at "SFT008" source valueKind "unsupported scalar value"
          _ <- takeText ";"
          pure (Right (identifier,value))
        _ -> P $ \source _ -> at "SFT001" source headToken
          "unsupported typed-rules scenario declaration"

data RawTypedCase = RawTypedCase Token Token
  [(Token,Token,[Token],Token,Token)] [(Token,Token,[Token])]

parseTypedFiniteCase :: FilePath -> BS.ByteString -> Either Diagnostic RawTypedCase
parseTypedFiniteCase path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP parser path tokens
  where
    parser = do
      _ <- takeText "typed-rules-case"
      identifier <- word
      _ <- takeText "model"
      modelPath <- string
      _ <- takeText "{"
      entries <- manyBefore "}" entry
      _ <- takeText "}"
      let shared = [value | Left value <- entries]
          allegations = [value | Right value <- entries]
      pure (RawTypedCase identifier modelPath shared allegations)
    entry = do
      headToken <- word
      case tokenText headToken of
        "shared-classification" -> do
          identifier <- word
          predicate <- word
          _ <- takeText "("
          arguments <- commaList word
          _ <- takeText ")"
          _ <- takeText "as"
          status <- word
          _ <- takeText "reason"
          reason <- string
          _ <- takeText ";"
          pure (Left (identifier,predicate,arguments,status,reason))
        "allegation" -> do
          identifier <- word
          _ <- takeText "scenario"
          scenarioPath <- string
          uses <- manyUses
          _ <- takeText ";"
          pure (Right (identifier,scenarioPath,uses))
        _ -> P $ \source _ -> at "SFT001" source headToken
          "unsupported typed-rules case declaration"
    manyUses = do
      token <- current
      if tokenText token == "use" then takeText "use" >> word >>= \item -> (item:) <$> manyUses
      else pure []

loadTypedFiniteCase :: FilePath -> BS.ByteString -> IO (Either Diagnostic TypedFiniteCase)
loadTypedFiniteCase path bytes = case parseTypedFiniteCase path bytes of
  Left issue -> pure (Left issue)
  Right (RawTypedCase identifier modelToken rawShared rawAllegations) -> do
    let local token = let value = Text.unpack (tokenText token) in
          not (null value) && not (isAbsolute value)
          && all (`notElem` ["",".."]) (Text.splitOn "/" (tokenText token))
    if not (local modelToken) then pure (at "SFT013" path modelToken "unsafe typed-rules case model path")
    else do
      modelBytes <- readBounded (takeDirectory path </> Text.unpack (tokenText modelToken)) path modelToken
      case modelBytes of
        Left issue -> pure (Left issue)
        Right modelSource -> case parseTypedFiniteModel (Text.unpack (tokenText modelToken)) modelSource of
          Left issue -> pure (Left issue)
          Right rawModel -> do
            composed <- loadTypedModules (takeDirectory path </> Text.unpack (tokenText modelToken)) rawModel
            case composed of
              Left issue -> pure (Left issue)
              Right (model,moduleRecords) -> do
                loaded <- traverse (loadAllegation model moduleRecords rawShared local) rawAllegations
                pure $ do
                  allegations <- sequence loaded
                  when (null allegations || length allegations > 32)
                    (at "SFT010" path identifier "typed-rules case requires 1..32 allegations")
                  uniqueTokens path "SFT002" "duplicate allegation ID"
                    [token | (token,_,_) <- rawAllegations]
                  uniqueTokens path "SFT002" "duplicate shared classification ID"
                    [token | (token,_,_,_,_) <- rawShared]
                  shared <- traverse (sharedRecord rawAllegations) rawShared
                  pure (TypedFiniteCase (tokenText identifier) shared allegations)
  where
    loadAllegation model modules rawShared local (allegationId,scenarioToken,uses)
      | not (local scenarioToken) = pure (at "SFT013" path scenarioToken "unsafe allegation scenario path")
      | otherwise = do
          scenarioBytes <- readBounded (takeDirectory path </> Text.unpack (tokenText scenarioToken)) path scenarioToken
          pure $ do
            source <- scenarioBytes
            scenario <- parseTypedFiniteScenario (Text.unpack (tokenText scenarioToken)) source
            selected <- traverse (selectShared rawShared) uses
            let scenarioWithShared = scenario { scenarioFacts = scenarioFacts scenario
                  ++ [(predicate,arguments,status,reason) | (_,predicate,arguments,status,reason) <- selected] }
            when (tokenText (scenarioModel scenario) /= tokenText (rawModelId model))
              (at "SFT002" path (scenarioModel scenario) "case scenario model identity mismatch")
            program <- validateModel path (Text.unpack (tokenText scenarioToken)) model scenarioWithShared
            let withModules = program { finiteModules = modules }
            result <- either (at "SFT011" path allegationId) Right (evaluateTypedFinite withModules)
            pure (TypedFiniteAllegation (tokenText allegationId) withModules result)
    selectShared shared identifier = case [item | item@(sharedId,_,_,_,_) <- shared,
        tokenText sharedId == tokenText identifier] of
      [item] -> Right item
      [] -> at "SFT003" path identifier "unknown shared classification"
      _ -> at "SFT002" path identifier "ambiguous shared classification"
    sharedRecord allegations (sharedId,predicate,arguments,status,reason) = do
      truth <- statusValue path status
      let fact = GroundFact (tokenText predicate) (map tokenText arguments) truth (tokenText reason)
          destinations = [tokenText allegationId | (allegationId,_,uses) <- allegations,
            any ((== tokenText sharedId) . tokenText) uses]
      pure (tokenText sharedId,fact,destinations)

loadTypedFiniteProgram :: FilePath -> BS.ByteString -> Maybe (FilePath,BS.ByteString)
  -> IO (Either Diagnostic TypedFiniteProgram)
loadTypedFiniteProgram path modelBytes scenarioBytes = case parseTypedFiniteModel path modelBytes of
  Left issue -> pure (Left issue)
  Right rawModel -> do
    composed <- loadTypedModules path rawModel
    pure $ do
      (model,moduleRecords) <- composed
      (scenarioPath,scenarioRaw) <- maybe
        (at "SFT011" path (rawModelId model) "typed-rules model requires a scenario") Right
        scenarioBytes
      scenario <- parseTypedFiniteScenario scenarioPath scenarioRaw
      when (tokenText (scenarioModel scenario) /= tokenText (rawModelId model))
        (at "SFT002" scenarioPath (scenarioModel scenario) "scenario model identity mismatch")
      program <- validateModel path scenarioPath model scenario
      pure program { finiteModules = moduleRecords }

loadTypedModules :: FilePath -> RawModel
  -> IO (Either Diagnostic (RawModel,[FiniteModule]))
loadTypedModules path model
  | null (rawImports model) && null (rawUses model) = pure (Right (model,[]))
  | otherwise = case rawModuleRoot model of
      Nothing -> pure (at "SFT013" path (rawModelId model) "module-root required for imports")
      Just rootToken -> do
        let rootText = Text.unpack (tokenText rootToken)
            safeRoot = not (null rootText) && not (isAbsolute rootText)
              && all (`notElem` ["",".."]) (Text.splitOn "/" (tokenText rootToken))
        if not safeRoot then pure (at "SFT013" path rootToken "unsafe typed-rules module root")
        else do
          loaded <- traverse (loadOne (takeDirectory path </> rootText)) (rawImports model)
          pure $ do
            modules <- sequence loaded
            validateImportIdentities path (rawImports model)
            let aliased = zip [tokenText alias | (_,_,alias) <- rawImports model] modules
            selections <- traverse (resolveUse path aliased) (rawUses model)
            let merged = foldl mergeSelection model selections
                records = [FiniteModule (tokenText name) (tokenText version)
                  (tokenText alias) [(tokenText kindValue,tokenText identifier)
                    | (kindValue,identifier) <- exports]
                  | ((name,version,alias),RawModule _ _ exports _) <- zip (rawImports model) modules]
            pure (merged,records)
  where
    loadOne root (name,version,_) = do
      let identity = tokenText name <> "@" <> tokenText version
          file = root </> Text.unpack (identity <> ".yh")
      if not (safeModuleName (tokenText name) && safeVersion (tokenText version))
        then pure (at "SFT013" path name "invalid module name or exact version")
        else do
          bytes <- readBounded file path name
          pure $ do
            source <- bytes
            declaration@(RawModule actual actualVersion _ body) <- parseTypedFiniteModule file source
            unless (tokenText actual == tokenText name && tokenText actualVersion == tokenText version)
              (at "SFT013" file actual "module identity or exact version mismatch")
            unless (null (rawImports body) && null (rawUses body))
              (at "SFT013" file actual "nested typed-rules imports are outside v0.2")
            pure declaration

safeModuleName :: Text -> Bool
safeModuleName value = not (Text.null value) && Text.count "." value >= 1
  && Text.all (\character -> character `elem` (['a'..'z'] ++ ['0'..'9'] ++ ".-")) value

safeVersion :: Text -> Bool
safeVersion value = case Text.splitOn "." value of
  [major,minor,patch] -> all semverNumeric [major,minor,patch]
  _ -> False
  where semverNumeric item = not (Text.null item) && Text.all (`elem` ['0'..'9']) item

readBounded :: FilePath -> FilePath -> Token -> IO (Either Diagnostic BS.ByteString)
readBounded file owner token = do
  result <- try $ do
    status <- getSymbolicLinkStatus file
    if isRegularFile status && fileSize status <= 65536
      then BS.readFile file else ioError (userError "unsafe typed-rules module")
  pure $ case result of
    Left (_ :: IOException) -> at "SFT013" owner token "module unavailable, unsafe or too large"
    Right bytes -> Right bytes

validateImportIdentities :: FilePath -> [(Token,Token,Token)] -> Either Diagnostic ()
validateImportIdentities path imports = do
  uniqueTokens path "SFT002" "duplicate module alias" [alias | (_,_,alias) <- imports]
  uniqueTokens path "SFT002" "duplicate module identity"
    [name { tokenText = tokenText name <> "@" <> tokenText version }
      | (name,version,_) <- imports]
  when (length imports > 32) (at "SFT010" path (let (name,_,_) = imports !! 32 in name)
    "module count limit exceeded")

resolveUse :: FilePath -> [(Text,RawModule)] -> (Token,Token)
  -> Either Diagnostic (Text,Token,RawModel)
resolveUse path modules (kindToken,qualifiedToken) = case Text.splitOn "::" (tokenText qualifiedToken) of
  [alias,identifier] -> case [declaration | (candidateAlias,declaration@(RawModule _ _ exports _)) <- modules,
      candidateAlias == alias,
      any (\(kindValue,item) -> tokenText kindValue == tokenText kindToken
        && tokenText item == identifier) exports] of
    [RawModule _ _ _ body] -> Right (tokenText kindToken,
      qualifiedToken { tokenText = identifier },body)
    [] -> at "SFT014" path qualifiedToken "private, missing or wrong-kind module reference"
    _ -> at "SFT014" path qualifiedToken "ambiguous module reference"
  _ -> at "SFT014" path qualifiedToken "module use must be alias-qualified"

mergeSelection :: RawModel -> (Text,Token,RawModel) -> RawModel
mergeSelection host (kindValue,identifier,moduleModel) = case kindValue of
  "entity-type" -> host { rawEntityTypes = rawEntityTypes host
      ++ selected rawEntityTypes (\item -> tokenText item == tokenText identifier) }
  "entity" -> host { rawEntities = rawEntities host
      ++ selected rawEntities (\(item,_) -> tokenText item == tokenText identifier) }
  "enum-type" -> host { rawEnums = rawEnums host
      ++ selected rawEnums (\(item,_) -> tokenText item == tokenText identifier) }
  "scalar" -> host { rawScalars = rawScalars host
      ++ selected rawScalars (\(item,_) -> tokenText item == tokenText identifier) }
  "predicate" -> host { rawPredicates = rawPredicates host
      ++ selected rawPredicates (\(item,_,_) -> tokenText item == tokenText identifier) }
  "proposition" -> host { rawPropositions = rawPropositions host
      ++ selected rawPropositions (\item -> tokenText item == tokenText identifier) }
  "requirement" -> host { rawRequirements = rawRequirements host
      ++ selected rawRequirements (\(item,_) -> tokenText item == tokenText identifier) }
  "rule" -> host { rawRules = rawRules host
      ++ selected rawRules (\(item,_,_,_,_,_) -> tokenText item == tokenText identifier) }
  "norm" -> host { rawNorms = rawNorms host
      ++ selected rawNorms (\(item,_,_,_,_,_) -> tokenText item == tokenText identifier) }
  "responsibility-route" -> host { rawRoutes = rawRoutes host
      ++ selected rawRoutes (\(item,_,_,_,_,_) -> tokenText item == tokenText identifier) }
  "priority" -> host { rawPriorities = rawPriorities host
      ++ selected rawPriorities (\(item,_) -> tokenText item == tokenText identifier) }
  _ -> host
  where selected accessor predicate = filter predicate (accessor moduleModel)

validateModel :: FilePath -> FilePath -> RawModel -> TypedFiniteScenario
  -> Either Diagnostic TypedFiniteProgram
validateModel path scenarioPath model scenario = do
  limit <- numeric path (rawLimit model)
  when (limit < 1 || limit > 2048) (at "SFT010" path (rawLimit model)
    "generated-node limit must be between 1 and 2048")
  enforceLimit path "entity types" 32 (rawEntityTypes model)
  enforceLimit path "entities" 256 (map fst (rawEntities model))
  enforceLimit path "predicates" 128 [token | (token,_,_) <- rawPredicates model]
  enforceLimit path "scalars" 256 (map fst (rawScalars model))
  enforceLimit path "ground applications" 1024 [token | (token,_,_,_) <- scenarioFacts scenario]
  enforceLimit path "rules" 128 [token | (token,_,_,_,_,_) <- rawRules model]
  enforceLimit path "norms" 64 [token | (token,_,_,_,_,_) <- rawNorms model]
  enforceLimit path "responsibility routes" 64
    [token | (token,_,_,_,_,_) <- rawRoutes model]
  enforceLimit path "priority edges" 256 (map fst (rawPriorities model))
  mapM_ (identifierLength path) (allIdentifiers model)
  uniqueTokens path "SFT002" "duplicate entity type" (rawEntityTypes model)
  uniqueTokens path "SFT002" "duplicate entity" (map fst (rawEntities model))
  uniqueTokens path "SFT002" "duplicate enum type" (map fst (rawEnums model))
  uniqueTokens path "SFT002" "duplicate scalar" (map fst (rawScalars model))
  uniqueTokens path "SFT002" "duplicate predicate" [token | (token,_,_) <- rawPredicates model]
  uniqueTokens path "SFT002" "duplicate proposition" (rawPropositions model)
  uniqueTokens path "SFT002" "duplicate requirement" (map fst (rawRequirements model))
  uniqueTokens path "SFT002" "duplicate rule" [token | (token,_,_,_,_,_) <- rawRules model]
  uniqueTokens path "SFT002" "duplicate norm" [token | (token,_,_,_,_,_) <- rawNorms model]
  uniqueTokens path "SFT002" "duplicate responsibility route"
    [token | (token,_,_,_,_,_) <- rawRoutes model]
  let typeNames = Set.fromList (map tokenText (rawEntityTypes model))
      enumMap = Map.fromList [(tokenText name,map tokenText values) | (name,values) <- rawEnums model]
  mapM_ (validateEntity path typeNames) (rawEntities model)
  mapM_ (validateDomainSize path) (Set.toList typeNames)
  scalarDecls <- traverse (scalarDeclaration path enumMap) (rawScalars model)
  predicates <- traverse (predicateDeclaration path typeNames) (rawPredicates model)
  let entities = [EntityDecl (tokenText identifier) (tokenText kindValue)
        | (identifier,kindValue) <- rawEntities model]
      entityIndex = Map.fromList [(identifier,kindValue) | EntityDecl identifier kindValue <- entities]
      predicateIndex = Map.fromList [(predicateName item,item) | item <- predicates]
      scalarIndex = Map.fromList [(scalarName item,scalarType item) | item <- scalarDecls]
      requirementIndex = Map.fromList [(tokenText identifier,expression)
        | (identifier,expression) <- rawRequirements model]
      propositionSet = Set.fromList (map tokenText (rawPropositions model))
  mapM_ (\(identifier,expression) -> validateExpression path typeNames entityIndex
    predicateIndex scalarIndex requirementIndex Set.empty 0 expression
      >> pure identifier) (rawRequirements model)
  rules <- traverse (ruleDeclaration path typeNames propositionSet entityIndex
    predicateIndex scalarIndex requirementIndex) (rawRules model)
  norms <- traverse (normDeclaration path propositionSet entityIndex typeNames
    predicateIndex scalarIndex requirementIndex) (rawNorms model)
  routes <- traverse (routeDeclaration path propositionSet entityIndex typeNames
    predicateIndex scalarIndex requirementIndex) (rawRoutes model)
  let elaborated = rules ++ map normRule norms ++ map routeRule routes
      normNames = Map.fromList [(normName item,ruleName (normRule item)) | item <- norms]
      routeNames = Map.fromList [(routeName item,ruleName (routeRule item)) | item <- routes]
      normalizeEndpoint token = token { tokenText = Map.findWithDefault
        (Map.findWithDefault (tokenText token) (tokenText token) routeNames)
        (tokenText token) normNames }
      normalizedPriorities = [(normalizeEndpoint higher,normalizeEndpoint lower)
        | (higher,lower) <- rawPriorities model]
  priorities <- traverse (priorityDeclaration path (Set.fromList (map ruleName elaborated)))
    normalizedPriorities
  validatePriorityAcyclic path priorities
  facts <- traverse (groundFact scenarioPath entityIndex predicateIndex) (scenarioFacts scenario)
  uniqueGroundFacts scenarioPath facts
  values <- traverse (scalarAssignment scenarioPath scalarIndex) (scenarioValues scenario)
  uniqueTokens scenarioPath "SFT002" "duplicate scalar assignment"
    (map fst (scenarioValues scenario))
  let valueMap = Map.fromList values
      missingValues = Set.toList (Map.keysSet scalarIndex `Set.difference` Map.keysSet valueMap)
  case missingValues of
    first:_ -> at "SFT011" scenarioPath (scenarioIdentifier scenario)
      ("missing required scalar value " <> first)
    [] -> pure ()
  when (null (rawLimitations model)) (at "SFT012" path (rawModelId model)
    "typed-rules limitations are required")
  let program = TypedFiniteProgram (tokenText (rawModelId model))
        (map (EntityTypeDecl . tokenText) (rawEntityTypes model)) entities predicates
        scalarDecls (map tokenText (rawPropositions model))
        [(tokenText identifier,expression) | (identifier,expression) <- rawRequirements model]
        elaborated norms routes priorities facts valueMap [] (map tokenText (rawLimitations model))
  estimated <- either (at "SFT010" path (rawLimit model)) Right
    (expandedNodeEstimate program)
  when (estimated > fromInteger limit) (at "SFT010" path (rawLimit model)
    "generated-node limit exceeded before evaluation")
  expanded <- either (at "SFT011" scenarioPath (scenarioIdentifier scenario)) Right
    (evaluateTypedFinite program)
  let nodeCount = length (finiteResultExpressions expanded) + length (finiteResultRules expanded)
        + length (finiteResultPropositions expanded) + expressionNodes program
  when (nodeCount > fromInteger limit) (at "SFT010" path (rawLimit model)
    "generated-node limit exceeded")
  pure program
  where
    validateDomainSize source kindValue = when
      (length [() | (_,declared) <- rawEntities model, tokenText declared == kindValue] > 64)
      (at "SFT010" source (rawModelId model) "entity-per-type limit exceeded")

numeric :: FilePath -> Token -> Either Diagnostic Integer
numeric path token = case reads (Text.unpack (tokenText token)) of
  [(value,"")] -> Right value
  _ -> at "SFT008" path token "invalid integer"

enforceLimit :: FilePath -> Text -> Int -> [Token] -> Either Diagnostic ()
enforceLimit path label maximumCount values = when (length values > maximumCount)
  (at "SFT010" path (values !! maximumCount) (label <> " limit exceeded"))

identifierLength :: FilePath -> Token -> Either Diagnostic ()
identifierLength path token = when (Text.length (tokenText token) > 128)
  (at "SFT010" path token "identifier exceeds 128 characters")

allIdentifiers :: RawModel -> [Token]
allIdentifiers model = rawEntityTypes model ++ map fst (rawEntities model)
  ++ map fst (rawEnums model) ++ map fst (rawScalars model)
  ++ [token | (token,_,_) <- rawPredicates model] ++ rawPropositions model
  ++ map fst (rawRequirements model) ++ [token | (token,_,_,_,_,_) <- rawRules model]
  ++ [token | (token,_,_,_,_,_) <- rawNorms model]
  ++ [token | (token,_,_,_,_,_) <- rawRoutes model]

uniqueTokens :: FilePath -> Text -> Text -> [Token] -> Either Diagnostic ()
uniqueTokens path code message = go Set.empty
  where
    go _ [] = Right ()
    go seen (token:rest)
      | Set.member (tokenText token) seen = at code path token message
      | otherwise = go (Set.insert (tokenText token) seen) rest

validateEntity :: FilePath -> Set Text -> (Token,Token) -> Either Diagnostic ()
validateEntity path types (_,kindValue) = unless (Set.member (tokenText kindValue) types)
  (at "SFT003" path kindValue "unknown nominal entity type")

scalarDeclaration :: FilePath -> Map Text [Text] -> (Token,RawScalarType)
  -> Either Diagnostic ScalarDecl
scalarDeclaration path enums (identifier,rawType) = ScalarDecl (tokenText identifier) <$> case rawType of
  RawInteger -> Right IntegerType
  RawDate -> Right DateType
  RawEnum name -> maybe (at "SFT003" path name "unknown enum type")
    (Right . EnumType (tokenText name)) (Map.lookup (tokenText name) enums)
  RawMoney currency | validCurrency (tokenText currency) -> Right (MoneyType (tokenText currency))
                    | otherwise -> at "SFT008" path currency "currency must be three uppercase letters"

validCurrency :: Text -> Bool
validCurrency value = Text.length value == 3 && Text.all (`elem` ['A'..'Z']) value

predicateDeclaration :: FilePath -> Set Text -> (Token,[Token],Token)
  -> Either Diagnostic PredicateDecl
predicateDeclaration path types (identifier,arguments,kindToken) = do
  when (null arguments || length arguments > 4) (at "SFT004" path identifier
    "predicate arity must be between 1 and 4")
  mapM_ (\argument -> unless (Set.member (tokenText argument) types)
    (at "SFT003" path argument "unknown predicate argument type")) arguments
  kindValue <- case tokenText kindToken of
    "conduct" -> Right PredicateConduct
    "circumstance" -> Right PredicateCircumstance
    "mental-state" -> Right PredicateMentalState
    "relationship" -> Right PredicateRelationship
    _ -> at "SFT004" path kindToken "unsupported predicate kind"
  pure (PredicateDecl (tokenText identifier) (map tokenText arguments) kindValue)

validateExpression :: FilePath -> Set Text -> Map Text Text -> Map Text PredicateDecl
  -> Map Text ScalarType -> Map Text FiniteExpr -> Set Text -> Int -> FiniteExpr
  -> Either Diagnostic ()
validateExpression path types entities predicates scalars requirements scope depth expression = do
  when (depth > 4) (at "SFT010" path origin "quantifier nesting limit exceeded")
  case expression of
    PredicateExpr name terms -> do
      signature <- maybe (at "SFT003" path origin ("unknown predicate " <> name)) Right
        (Map.lookup name predicates)
      when (length terms /= length (predicateArguments signature))
        (at "SFT004" path origin "predicate argument count mismatch")
      sequence_ [validateTerm expected term | (expected,term) <- zip (predicateArguments signature) terms]
    ComparisonExpr operation left right upper -> validateComparison operation left right upper
    AllExpr members -> mapM_ recurse members
    AnyExpr members -> mapM_ recurse members
    NotExpr member -> recurse member
    ForallExpr variable kindValue body -> quantify variable kindValue body
    ExistsExpr variable kindValue body -> quantify variable kindValue body
    CardinalityExpr _ threshold members -> do
      when (threshold < 0) (at "SFT009" path origin "negative cardinality threshold")
      when (null members) (at "SFT009" path origin "cardinality requires at least one proposition")
      mapM_ recurse members
    ReferenceExpr identifier -> unless (Map.member identifier requirements)
      (at "SFT003" path origin ("unknown requirement " <> identifier))
  where
    origin = Token WordToken "typed-expression" 1 1
    recurse = validateExpression path types entities predicates scalars requirements scope depth
    validateTerm expected term = case term of
      EntityTerm identifier -> case Map.lookup identifier entities of
        Just actual | actual == expected -> Right ()
        Just _ -> at "SFT005" path origin "predicate entity type mismatch"
        Nothing -> at "SFT003" path origin ("unknown entity " <> identifier)
      VariableTerm variable -> if Set.member (variable <> "@" <> expected) scope then Right ()
        else at "SFT006" path origin ("free or wrongly typed variable " <> variable)
    quantify variable kindValue body = do
      unless ("var:" `Text.isPrefixOf` variable) (at "SFT006" path origin
        "quantified variables require var: prefix")
      unless (Set.member kindValue types) (at "SFT003" path origin "unknown quantified type")
      when (any (Text.isPrefixOf (variable <> "@")) (Set.toList scope))
        (at "SFT006" path origin "variable shadowing is unsupported")
      validateExpression path types entities predicates scalars requirements
        (Set.insert (variable <> "@" <> kindValue) scope) (depth + 1) body
    validateComparison operation left right upper = do
      leftType <- maybe (at "SFT003" path origin ("unknown scalar " <> left)) Right
        (Map.lookup left scalars)
      rightType <- maybe (at "SFT003" path origin ("unknown scalar " <> right)) Right
        (Map.lookup right scalars)
      unless (leftType == rightType) (at "SFT008" path origin "comparison type mismatch")
      case (operation,leftType,upper) of
        (InHalfOpen,DateType,Just upperName) -> do
          upperType <- maybe (at "SFT003" path origin "unknown interval upper scalar") Right
            (Map.lookup upperName scalars)
          unless (upperType == DateType) (at "SFT008" path origin "date interval type mismatch")
        (InHalfOpen,_,_) -> at "SFT008" path origin "half-open membership requires three dates"
        (_,EnumType _ _,_) | operation `notElem` [Equal,NotEqual] ->
          at "SFT008" path origin "enums support only equality and inequality"
        (_,_,Nothing) -> Right ()
        _ -> at "SFT008" path origin "unexpected comparison upper operand"

ruleDeclaration :: FilePath -> Set Text -> Set Text -> Map Text Text
  -> Map Text PredicateDecl -> Map Text ScalarType -> Map Text FiniteExpr
  -> (Token,[(Token,Token)],Token,Token,FiniteExpr,Maybe Token)
  -> Either Diagnostic RuleDecl
ruleDeclaration path types propositions entities predicates scalars requirements
    (identifier,parameters,polarityToken,conclusion,body,citation) = do
  when (length parameters > 4) (at "SFT010" path identifier
    "rule parameter count exceeds 4")
  uniqueTokens path "SFT002" "duplicate rule parameter" (map fst parameters)
  mapM_ (\(_,kindValue) -> unless (Set.member (tokenText kindValue) types)
    (at "SFT003" path kindValue "unknown rule parameter type")) parameters
  unless (Set.member (tokenText conclusion) propositions)
    (at "SFT003" path conclusion "unknown rule conclusion proposition")
  polarity <- case tokenText polarityToken of
    "establishes" -> Right Establish
    "defeats" -> Right Defeat
    _ -> at "SFT007" path polarityToken "rule polarity must be establishes or defeats"
  let scope = Set.fromList [tokenText variable <> "@" <> tokenText kindValue
        | (variable,kindValue) <- parameters]
  validateExpression path types entities predicates scalars requirements scope 0 body
  pure (RuleDecl (tokenText identifier)
    [(tokenText variable,tokenText kindValue) | (variable,kindValue) <- parameters]
    polarity (tokenText conclusion) body (tokenText <$> citation))

normDeclaration :: FilePath -> Set Text -> Map Text Text -> Set Text
  -> Map Text PredicateDecl -> Map Text ScalarType -> Map Text FiniteExpr
  -> (Token,Token,Token,Token,FiniteExpr,Maybe Token)
  -> Either Diagnostic NormDecl
normDeclaration path propositions entities types predicates scalars requirements
    (identifier,subject,modalityToken,action,body,citation) = do
  unless ("n:" `Text.isPrefixOf` tokenText identifier)
    (at "SFT015" path identifier "norm requires n: identifier")
  unless (Map.member (tokenText subject) entities)
    (at "SFT003" path subject "norm subject must be a declared entity")
  unless (Set.member (tokenText action) propositions)
    (at "SFT003" path action "norm action must be a declared proposition")
  modality <- case tokenText modalityToken of
    "required" -> Right Required
    "prohibited" -> Right Prohibited
    "permitted" -> Right Permitted
    _ -> at "SFT015" path modalityToken
      "norm modality must be required, prohibited or permitted"
  validateExpression path types entities predicates scalars requirements Set.empty 0 body
  pure (NormDecl (tokenText identifier) (tokenText subject) modality
    (tokenText action) body (tokenText <$> citation))

routeDeclaration :: FilePath -> Set Text -> Map Text Text -> Set Text
  -> Map Text PredicateDecl -> Map Text ScalarType -> Map Text FiniteExpr
  -> (Token,Token,Token,Token,FiniteExpr,Maybe Token)
  -> Either Diagnostic ResponsibilityRoute
routeDeclaration path propositions entities types predicates scalars requirements
    (identifier,subject,kindToken,target,body,citation) = do
  unless ("route:" `Text.isPrefixOf` tokenText identifier)
    (at "SFT016" path identifier "responsibility route requires route: identifier")
  unless (Map.member (tokenText subject) entities)
    (at "SFT003" path subject "responsibility route subject must be a declared entity")
  unless (Set.member (tokenText target) propositions)
    (at "SFT003" path target "responsibility route target must be a declared proposition")
  kindValue <- case tokenText kindToken of
    "principal-conduct" -> Right PrincipalConduct
    "joint-conduct" -> Right JointConduct
    "instigation" -> Right Instigation
    "conspiracy" -> Right Conspiracy
    "intentional-aid" -> Right IntentionalAid
    "attempt" -> Right AttemptRoute
    value | "other:" `Text.isPrefixOf` value && Text.length value > 6 ->
      Right (AuthoredContribution (Text.drop 6 value))
    _ -> at "SFT016" path kindToken "unsupported responsibility route kind"
  validateExpression path types entities predicates scalars requirements Set.empty 0 body
  unless (expressionMentions (tokenText subject) requirements body)
    (at "SFT016" path subject
      "responsibility route requirements must explicitly mention its subject actor")
  pure (ResponsibilityRoute (tokenText identifier) (tokenText subject) kindValue
    (tokenText target) body (tokenText <$> citation))

normRule :: NormDecl -> RuleDecl
normRule item = RuleDecl ("r:norm:" <> normName item) [] polarity
  (normAction item) (normApplicability item) (normCitation item)
  where
    polarity = case normModality item of
      Prohibited -> Defeat
      Required -> Establish
      Permitted -> Establish

routeRule :: ResponsibilityRoute -> RuleDecl
routeRule item = RuleDecl ("r:route:" <> routeName item) [] Establish
  (routeTarget item) (routeRequirements item) (routeCitation item)

expressionMentions :: Text -> Map Text FiniteExpr -> FiniteExpr -> Bool
expressionMentions wanted requirements = go Set.empty
  where
    go seen expression = case expression of
      PredicateExpr _ terms -> any ((== wanted) . entityName) terms
      AllExpr members -> any (go seen) members
      AnyExpr members -> any (go seen) members
      NotExpr member -> go seen member
      ForallExpr _ _ member -> go seen member
      ExistsExpr _ _ member -> go seen member
      CardinalityExpr _ _ members -> any (go seen) members
      ReferenceExpr identifier
        | Set.member identifier seen -> False
        | otherwise -> maybe False (go (Set.insert identifier seen))
            (Map.lookup identifier requirements)
      _ -> False
    entityName term = case term of
      EntityTerm identifier -> identifier
      VariableTerm _ -> ""

priorityDeclaration :: FilePath -> Set Text -> (Token,Token)
  -> Either Diagnostic PriorityDecl
priorityDeclaration path rules (higher,lower) = do
  unless (Set.member (tokenText higher) rules) (at "SFT003" path higher "unknown higher-priority rule")
  unless (Set.member (tokenText lower) rules) (at "SFT003" path lower "unknown lower-priority rule")
  when (tokenText higher == tokenText lower) (at "SFT007" path higher "self priority is invalid")
  pure (PriorityDecl (tokenText higher) (tokenText lower))

validatePriorityAcyclic :: FilePath -> [PriorityDecl] -> Either Diagnostic ()
validatePriorityAcyclic path priorities = mapM_ (visit Set.empty) nodes
  where
    nodes = nub ([high | PriorityDecl high _ <- priorities] ++ [low | PriorityDecl _ low <- priorities])
    visit active node
      | Set.member node active = at "SFT007" path (Token WordToken node 1 1) "priority cycle"
      | otherwise = mapM_ (visit (Set.insert node active))
          [low | PriorityDecl high low <- priorities, high == node]

groundFact :: FilePath -> Map Text Text -> Map Text PredicateDecl
  -> (Token,[Token],Token,Token) -> Either Diagnostic GroundFact
groundFact path entities predicates (name,arguments,statusToken,reason) = do
  signature <- maybe (at "SFT003" path name "unknown classified predicate") Right
    (Map.lookup (tokenText name) predicates)
  when (length arguments /= length (predicateArguments signature))
    (at "SFT004" path name "classified predicate argument count mismatch")
  sequence_ [case Map.lookup (tokenText argument) entities of
    Just actual | actual == expected -> Right ()
    Just _ -> at "SFT005" path argument "classified predicate entity type mismatch"
    Nothing -> at "SFT003" path argument "unknown classified entity"
    | (expected,argument) <- zip (predicateArguments signature) arguments]
  status <- statusValue path statusToken
  pure (GroundFact (tokenText name) (map tokenText arguments) status (tokenText reason))

statusValue :: FilePath -> Token -> Either Diagnostic Truth
statusValue path token = case tokenText token of
  "proved" -> Right TrueValue
  "not_proved" -> Right FalseValue
  "unresolved" -> Right UnresolvedValue
  _ -> at "SFT008" path token "invalid proof classification"

uniqueGroundFacts :: FilePath -> [GroundFact] -> Either Diagnostic ()
uniqueGroundFacts path facts = go Set.empty facts
  where
    go _ [] = Right ()
    go seen (item:rest)
      | Set.member key seen = at "SFT002" path (Token WordToken key 1 1)
          "duplicate ground classification"
      | otherwise = go (Set.insert key seen) rest
      where key = groundKey (groundPredicate item) (groundArguments item)

scalarAssignment :: FilePath -> Map Text ScalarType -> (Token,RawValue)
  -> Either Diagnostic (Text,ScalarValue)
scalarAssignment path declarations (identifier,raw) = do
  expected <- maybe (at "SFT003" path identifier "unknown scalar assignment") Right
    (Map.lookup (tokenText identifier) declarations)
  value <- case (expected,raw) of
    (kindValue,RawUnresolvedValue reason) -> Right (ScalarUnresolved (tokenText reason) kindValue)
    (IntegerType,RawIntegerValue token) -> IntegerValue <$> numeric path token
    (DateType,RawDateValue token) -> DateValue <$> parseDate path token
    (EnumType enumName members,RawEnumValue enumToken member)
      | tokenText enumToken == enumName && tokenText member `elem` members ->
          Right (EnumValue enumName (tokenText member))
      | otherwise -> at "SFT008" path member "enum value is not a declared member"
    (MoneyType currency,RawMoneyValue currencyToken amount)
      | tokenText currencyToken == currency -> do
          minor <- numeric path amount
          if minor < 0 then at "SFT008" path amount "money minor units cannot be negative"
          else Right (MoneyValue currency minor)
      | otherwise -> at "SFT008" path currencyToken "money currency mismatch"
    _ -> at "SFT008" path identifier "scalar assignment type mismatch"
  pure (tokenText identifier,value)

parseDate :: FilePath -> Token -> Either Diagnostic Day
parseDate path token = maybe (at "SFT008" path token "date must be a real YYYY-MM-DD") Right
  (parseTimeM True defaultTimeLocale "%F" (Text.unpack (tokenText token)))

expressionNodes :: TypedFiniteProgram -> Int
expressionNodes program = sum (map (count . snd) (finiteRequirements program))
  + sum (map (count . ruleBody) (finiteRules program))
  where
    count expression = 1 + case expression of
      AllExpr members -> sum (map count members)
      AnyExpr members -> sum (map count members)
      NotExpr member -> count member
      ForallExpr _ _ member -> count member
      ExistsExpr _ _ member -> count member
      CardinalityExpr _ _ members -> sum (map count members)
      _ -> 0

expandedNodeEstimate :: TypedFiniteProgram -> Either Text Integer
expandedNodeEstimate program = do
  let domains = Map.unionWith (+)
        (Map.fromListWith (+)
          [(kindValue,1 :: Integer) | EntityDecl _ kindValue <- finiteEntities program])
        (Map.fromList [(kindValue,0) | EntityTypeDecl kindValue <- finiteEntityTypes program])
      requirements = Map.fromList (finiteRequirements program)
      expression active item = case item of
        AllExpr members -> aggregate active members
        AnyExpr members -> aggregate active members
        NotExpr member -> (1 +) <$> expression active member
        ForallExpr _ kindValue member -> quantified active kindValue member
        ExistsExpr _ kindValue member -> quantified active kindValue member
        CardinalityExpr _ _ members -> aggregate active members
        ReferenceExpr identifier
          | Set.member identifier active -> Left "cyclic requirement expansion"
          | otherwise -> maybe (Left "unknown requirement expansion")
              (\target -> (1 +) <$> expression (Set.insert identifier active) target)
              (Map.lookup identifier requirements)
        _ -> Right 1
      aggregate active members = (1 +) . sum <$> traverse (expression active) members
      quantified active kindValue member = do
        count <- maybe (Left "unknown quantified domain") Right (Map.lookup kindValue domains)
        size <- expression active member
        pure (1 + count * size)
      parameterCount declaration = product <$> traverse
        (\(_,kindValue) -> maybe (Left "unknown rule parameter domain") Right
          (Map.lookup kindValue domains)) (ruleParameters declaration)
      ruleSize declaration = do
        bindings <- parameterCount declaration
        body <- expression Set.empty (ruleBody declaration)
        pure (1 + bindings * body)
  requirementsSize <- sum <$> traverse
    (\(identifier,item) -> expression (Set.singleton identifier) item)
    (finiteRequirements program)
  rulesSize <- sum <$> traverse ruleSize (finiteRules program)
  pure (fromIntegral (length (finiteEntityTypes program) + length (finiteEntities program)
    + length (finitePredicates program) + length (finiteScalars program)
    + length (finitePropositions program) + length (finiteFacts program))
    + requirementsSize + rulesSize)

encodeTypedFiniteRequest :: Text -> TypedFiniteProgram -> BS.ByteString
encodeTypedFiniteRequest requestId program = encodeJson (JObj
  [("protocol",JStr "yuho.kernel-protocol/v1")
  ,("request_id",JStr requestId)
  ,("operation",JStr "evaluate")
  ,("input_schema",JStr "yuho.kernel-input/v1")
  ,("fragment",JStr "TypedFiniteRules-v1")
  ,("program",programJson program)
  ,("policy",JObj [("max_nodes",JNum 2048)])])

encodeTypedFiniteCase :: TypedFiniteCase -> BS.ByteString
encodeTypedFiniteCase declaration = encodeJson (JObj
  [("kind",JStr "typed-finite-case")
  ,("id",JStr (typedCaseId declaration))
  ,("allegations",JArr [JObj
      [("id",JStr (typedAllegationId item))
      ,("request",requestObject (encodeTypedFiniteRequest
          (typedAllegationId item <> "-request") (typedAllegationProgram item)))]
      | item <- typedCaseAllegations declaration])])
  where
    requestObject bytes = case decodeJson bytes of
      Right value -> value
      Left _ -> JNull

programJson :: TypedFiniteProgram -> J
programJson program = JObj
  [("id",JStr (finiteProgramId program))
  ,("entity_types",JArr [JStr value | EntityTypeDecl value <- finiteEntityTypes program])
  ,("entities",JArr [JObj [("id",JStr identifier),("type",JStr kindValue)]
      | EntityDecl identifier kindValue <- finiteEntities program])
  ,("predicates",JArr (map predicateJson (finitePredicates program)))
  ,("scalars",JArr (map scalarJson (finiteScalars program)))
  ,("propositions",JArr (map JStr (finitePropositions program)))
  ,("requirements",JArr [JObj [("id",JStr identifier),("expression",expressionJson expression)]
      | (identifier,expression) <- finiteRequirements program])
  ,("rules",JArr (map ruleJson (finiteRules program)))
  ,("priorities",JArr [JObj [("higher",JStr high),("lower",JStr low)]
      | PriorityDecl high low <- finitePriorities program])
  ,("facts",JArr (map factJson (finiteFacts program)))
  ,("values",JArr [JObj [("id",JStr identifier),("value",valueJson value)]
      | (identifier,value) <- Map.toAscList (finiteValues program)])
  ,("limitations",JArr (map JStr (finiteLimitations program)))]

predicateJson :: PredicateDecl -> J
predicateJson declaration = JObj
  [("id",JStr (predicateName declaration))
  ,("arguments",JArr (map JStr (predicateArguments declaration)))
  ,("kind",JStr (case predicateKind declaration of
      PredicateConduct -> "conduct"; PredicateCircumstance -> "circumstance"
      PredicateMentalState -> "mental-state"; PredicateRelationship -> "relationship"))]

scalarJson :: ScalarDecl -> J
scalarJson declaration = JObj
  [("id",JStr (scalarName declaration)),("type",scalarTypeJson (scalarType declaration))]

scalarTypeJson :: ScalarType -> J
scalarTypeJson IntegerType = JObj [("kind",JStr "integer")]
scalarTypeJson DateType = JObj [("kind",JStr "date")]
scalarTypeJson (EnumType name members) = JObj
  [("kind",JStr "enum"),("name",JStr name),("members",JArr (map JStr members))]
scalarTypeJson (MoneyType currency) = JObj [("kind",JStr "money"),("currency",JStr currency)]

termJson :: Term -> J
termJson (EntityTerm identifier) = JObj [("kind",JStr "entity"),("id",JStr identifier)]
termJson (VariableTerm identifier) = JObj [("kind",JStr "variable"),("id",JStr identifier)]

expressionJson :: FiniteExpr -> J
expressionJson expression = case expression of
  PredicateExpr name arguments -> JObj
    [("kind",JStr "predicate"),("predicate",JStr name),("arguments",JArr (map termJson arguments))]
  ComparisonExpr operation left right upper -> JObj
    ([ ("kind",JStr "comparison"),("operation",JStr (comparisonText operation))
     , ("left",JStr left),("right",JStr right)]
     ++ maybe [] (\value -> [("upper",JStr value)]) upper)
  AllExpr members -> membersJson "all" members
  AnyExpr members -> membersJson "any" members
  NotExpr member -> JObj [("kind",JStr "not"),("member",expressionJson member)]
  ForallExpr variable kindValue member -> quantifierJson "forall" variable kindValue member
  ExistsExpr variable kindValue member -> quantifierJson "exists" variable kindValue member
  CardinalityExpr kindValue threshold members -> JObj
    [("kind",JStr (cardinalityText kindValue)),("threshold",JNum (toInteger threshold))
    ,("members",JArr (map expressionJson members))]
  ReferenceExpr identifier -> JObj [("kind",JStr "reference"),("id",JStr identifier)]
  where
    membersJson name members = JObj [("kind",JStr name),("members",JArr (map expressionJson members))]
    quantifierJson name variable kindValue member = JObj
      [("kind",JStr name),("variable",JStr variable),("entity_type",JStr kindValue)
      ,("member",expressionJson member)]

ruleJson :: RuleDecl -> J
ruleJson declaration = JObj
  ([ ("id",JStr (ruleName declaration))
   , ("parameters",JArr [JObj [("variable",JStr variable),("entity_type",JStr kindValue)]
        | (variable,kindValue) <- ruleParameters declaration])
   , ("polarity",JStr (if rulePolarity declaration == Establish then "establish" else "defeat"))
   , ("conclusion",JStr (ruleConclusion declaration))
   , ("body",expressionJson (ruleBody declaration))]
   ++ maybe [] (\citation -> [("citation",JStr citation)]) (ruleCitation declaration))

factJson :: GroundFact -> J
factJson fact = JObj
  [("predicate",JStr (groundPredicate fact)),("arguments",JArr (map JStr (groundArguments fact)))
  ,("status",JStr (truthName (groundStatus fact))),("reason",JStr (groundReason fact))]

valueJson :: ScalarValue -> J
valueJson value = case value of
  IntegerValue number -> JObj [("kind",JStr "integer"),("value",JNum number)]
  DateValue day -> JObj [("kind",JStr "date"),("value",JStr (Text.pack (show day)))]
  EnumValue name member -> JObj [("kind",JStr "enum"),("name",JStr name),("value",JStr member)]
  MoneyValue currency amount -> JObj
    [("kind",JStr "money"),("currency",JStr currency),("minor_units",JNum amount)]
  ScalarUnresolved reason kindValue -> JObj
    [("kind",JStr "unresolved"),("reason",JStr reason),("expected_type",scalarTypeJson kindValue)]

comparisonText :: Comparison -> Text
comparisonText Equal = "eq"; comparisonText NotEqual = "neq"
comparisonText LessThan = "lt"; comparisonText LessEqual = "lte"
comparisonText GreaterThan = "gt"; comparisonText GreaterEqual = "gte"
comparisonText InHalfOpen = "in-half-open"

cardinalityText :: CardinalityKind -> Text
cardinalityText AtLeast = "at-least"
cardinalityText AtMost = "at-most"
cardinalityText Exactly = "exactly"

explainTypedFinite :: TypedFiniteProgram -> TypedFiniteResult -> Text
explainTypedFinite program result = Text.unlines $
  [coreVersion <> " typed finite rules", "Model: " <> finiteProgramId program
  ,"Exact-version modules:"]
  ++ ["- " <> finiteModuleAlias item <> " = " <> finiteModuleName item <> "@"
      <> finiteModuleVersion item | item <- finiteModules program]
  ++ ["Typed entities:"]
  ++ ["- " <> identifier <> " : " <> kindValue | EntityDecl identifier kindValue <- finiteEntities program]
  ++ ["Scalar " <> identifier <> " = " <> scalarValueText value
      | (identifier,value) <- Map.toAscList (finiteValues program)]
  ++ ["Requirement " <> expressionLabel row <> ": " <> truthName (expressionStatus row)
      <> " — " <> expressionDetail row | row <- finiteResultExpressions result]
  ++ ["Rule " <> observedRule row <> " " <> polarityText (observedPolarity row)
      <> " " <> observedProposition row <> ": " <> truthName (observedStatus row)
      <> bindingText (observedBindings row) <> blockedText (observedDefeatedBy row)
      | row <- finiteResultRules result]
  ++ ["Norm " <> normName item <> " — subject " <> normSubject item
      <> ", modality " <> modalityText (normModality item) <> ", action "
      <> normAction item <> ": applicability " <> ruleStatus ("r:norm:" <> normName item)
      | item <- finiteNorms program]
  ++ ["Responsibility route " <> routeName item <> " — subject " <> routeSubject item
      <> ", kind " <> routeKindText (routeKind item) <> ", target " <> routeTarget item
      <> ": requirements " <> ruleStatus ("r:route:" <> routeName item)
      | item <- finiteRoutes program]
  ++ ["Proposition " <> observedPropositionId row <> ": " <> truthName (propositionStatus row)
      <> " (" <> propositionState row <> ")" | row <- finiteResultPropositions result]
  ++ ["Limitations:"] ++ map ("- " <>) (finiteLimitations program)
  ++ ["Technical classifications and scalar values are supplied. Yuho does not assess evidence, determine guilt, conviction, sentence or court disposition."]
  where
    coreVersion | null (finiteNorms program) && null (finiteRoutes program) = "Core Yuho v0.2"
                | otherwise = "Core Yuho v0.3"
    polarityText Establish = "establishes"; polarityText Defeat = "defeats"
    bindingText [] = ""; bindingText bindings = " bindings=" <> Text.pack (show bindings)
    blockedText [] = ""; blockedText rules = " blocked-by=" <> Text.intercalate "," rules
    ruleStatus identifier = case filter ((== identifier) . observedRule)
        (finiteResultRules result) of
      row:_ -> truthName (observedStatus row)
        <> if null (observedDefeatedBy row) then ""
           else " blocked-by=" <> Text.intercalate "," (observedDefeatedBy row)
      [] -> "not evaluated"

modalityText :: NormModality -> Text
modalityText Required = "required"
modalityText Prohibited = "prohibited"
modalityText Permitted = "permitted"

routeKindText :: ResponsibilityKind -> Text
routeKindText PrincipalConduct = "principal-conduct"
routeKindText JointConduct = "joint-conduct"
routeKindText Instigation = "instigation"
routeKindText Conspiracy = "conspiracy"
routeKindText IntentionalAid = "intentional-aid"
routeKindText AttemptRoute = "attempt"
routeKindText (AuthoredContribution value) = "other:" <> value

explainTypedFiniteCase :: TypedFiniteCase -> Text
explainTypedFiniteCase declaration = Text.unlines $
  ["Core Yuho v0.2 typed finite case", "Case: " <> typedCaseId declaration
  ,"Shared ground classifications:"]
  ++ ["- " <> identifier <> " = " <> groundKey (groundPredicate fact) (groundArguments fact)
      <> " -> " <> Text.intercalate "," destinations
      | (identifier,fact,destinations) <- typedCaseShared declaration]
  ++ concat
    [["Allegation " <> typedAllegationId allegation <> ":"]
      ++ ["- requirement " <> expressionLabel row <> " = "
          <> truthName (expressionStatus row) <> " — " <> expressionDetail row
        | row <- finiteResultExpressions (typedAllegationResult allegation)]
      ++ ["- rule " <> observedRule row <> " = " <> truthName (observedStatus row)
          <> case observedDefeatedBy row of
            [] -> ""
            blockers -> " blocked-by=" <> Text.intercalate "," blockers
        | row <- finiteResultRules (typedAllegationResult allegation)]
      ++ ["- proposition " <> observedPropositionId row <> " = "
          <> truthName (propositionStatus row) <> " (" <> propositionState row <> ")"
        | row <- finiteResultPropositions (typedAllegationResult allegation)]
      | allegation <- typedCaseAllegations declaration]
  ++ ["Allegations are evaluated independently. There is no aggregate guilt, liability, conviction, sentence or court disposition."]

scalarValueText :: ScalarValue -> Text
scalarValueText (IntegerValue value) = Text.pack (show value)
scalarValueText (DateValue value) = Text.pack (show value)
scalarValueText (EnumValue name value) = name <> ":" <> value
scalarValueText (MoneyValue currency value) = currency <> " " <> Text.pack (show value) <> " minor-units"
scalarValueText (ScalarUnresolved reason _) = "unresolved(" <> reason <> ")"
