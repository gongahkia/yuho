{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Surface.TypedFinite
  ( loadTypedFiniteProgram, parseTypedFiniteModel, parseTypedFiniteScenario
  , TypedFiniteScenario(..), TypedFiniteCase(..), TypedFiniteAllegation(..)
  , loadTypedFiniteCase, encodeTypedFiniteRequest, encodeTypedFiniteCase
  , explainTypedFinite, explainTypedFiniteCase
  , inspectTypedFiniteModel, inspectTypedFiniteScenario, prepareTypedFiniteInspection
  , typedDeclarationTokens, expandedNodeEstimate, dependencySourcePaths, prepareDependencyTyped, prepareDependencyTypedScoped
  , prepareDependencyTypedQuantitative
  , loadTypedFiniteQuantitative
  ) where

import Control.Exception (IOException, try)
import Control.Monad (unless, when)
import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as BL
import Data.List (nub)
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Set (Set)
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Calendar (Day)
import Data.Time.Format (defaultTimeLocale, parseTimeM)
import System.FilePath ((</>), isAbsolute, takeDirectory, normalise)
import System.Posix.Files (fileSize, getSymbolicLinkStatus, isRegularFile)
import Yuho.CoreYuho.TypedFinite
import Yuho.Exception.Types (Truth(..))
import Yuho.Protocol.Decode (sha256Text)
import qualified Data.Text.Encoding as UTF8
import Yuho.Protocol.Json (J(..), decodeJson, encodeJson)
import Yuho.Surface.InspectionData (locatedToken)
import Yuho.Surface.Lexer (lexSource)
import Yuho.ScopedDefinitions.Types
import qualified Yuho.Quantitative as Q
import qualified Data.Aeson as A
import Yuho.Surface.Token

data RawScalarType = RawInteger | RawDate | RawEnum Token | RawMoney Token | RawCount Token
  deriving (Eq, Show)

-- Authored templates and explicit uses are surface objects, not new Core operators.
data RawTemplate = RawTemplate
  { rawTemplateName :: Token, rawTemplateLookup :: Text
  , rawTemplateParameters :: [(Token,Token)], rawTemplateBody :: FiniteExpr
  , rawTemplatePath :: FilePath, rawTemplateOwner :: Text, rawTemplateVersion :: Maybe Text
  , rawTemplateDigest :: Text, rawTemplateSignature :: [(Token,[Token],Token)]
  } deriving (Eq,Show)

data RawModel = RawModel
  { rawModelId :: Token
  , rawLimit :: Token
  , rawEntityTypes :: [Token]
  , rawEntities :: [(Token,Token)]
  , rawEnums :: [(Token,[Token])]
  , rawScalars :: [(Token,RawScalarType)]
  , rawPredicates :: [(Token,[Token],Token)]
  -- Origins belong to declarations selected by the resolver, not to names
  -- guessed from a diagnostic. The optional token is the actual host use-site.
  , rawDeclarationSources :: [(Text,Token,FilePath,Maybe Token)]
  , rawPropositions :: [Token]
  , rawRequirements :: [(Token,FiniteExpr)]
  , rawRules :: [(Token,[(Token,Token)],Token,Token,FiniteExpr,Maybe Token)]
  , rawNorms :: [(Token,Token,Token,Token,FiniteExpr,Maybe Token)]
  , rawRoutes :: [(Token,Token,Token,Token,FiniteExpr,Maybe Token)]
  , rawPriorities :: [(Token,Token)]
  , rawModuleRoot :: Maybe Token
  , rawImports :: [(Token,Token,Token)]
  , rawUses :: [(Token,Token)]
  , rawDependencySlots :: [Token]
  , rawTemplates :: [RawTemplate]
  , rawScopedUses :: [(Token,Token,[Token])]
  , rawLimitations :: [Token]
  , rawQuantitative :: [Token]
  , rawQuantDefinitions :: [Q.QDefinition]
  , rawSourceOwner :: (FilePath,BS.ByteString)
  , rawSourceBundle :: Map FilePath BS.ByteString
  } deriving (Eq, Show)

data RawModule = RawModule Token Token [(Token,Token)] RawModel deriving (Eq, Show)

data TypedFiniteScenario = TypedFiniteScenario
  { scenarioIdentifier :: Token
  , scenarioModel :: Token
  , scenarioFacts :: [(Token,[Token],Token,Token)]
  , scenarioValues :: [(Token,RawValue)]
  , scenarioValueReasons :: Map Text Token
  } deriving (Eq, Show)

data RawValue
  = RawIntegerValue Token
  | RawDateValue Token
  | RawEnumValue Token Token
  | RawMoneyValue Token Token
  | RawCountValue Token Token
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

parseScalarType :: P RawScalarType
parseScalarType = do
  token <- word
  case tokenText token of
    "integer"->pure RawInteger
    "date"->pure RawDate
    "enum"->RawEnum <$> word
    "money"->RawMoney <$> word
    "count"->RawCount <$> word
    _->P $ \path _->at "SFT008" path token "unsupported scalar type"

quantityType :: RawScalarType -> Q.QType
quantityType ty=case ty of
  RawInteger->Q.QInteger;RawMoney c->Q.QMoney (tokenText c)
  RawCount domain->Q.QCount (tokenText domain);RawDate->Q.QDate;RawEnum e->Q.QEnum (tokenText e)

parseQuantity :: Int -> P Q.QExpr
parseQuantity depth=do
  token<-word
  when (depth>16) (P $ \path _->at "QLIMIT" path token "quantitative AST depth exceeds 16")
  _<-takeText "("
  result<-case tokenText token of
    "ref"->Q.QRef . tokenText <$> word
    "integer"->Q.QConstant Q.QInteger <$> number
    "money"->do c<-word;_<-takeText ",";Q.QConstant (Q.QMoney (tokenText c)) <$> number
    "count-value"->do d<-word;_<-takeText ",";Q.QConstant (Q.QCount (tokenText d)) <$> number
    "scale"->do n<-number;_<-takeText ",";Q.QScale n <$> parseQuantity (depth+1)
    "sum"->Q.QSum <$> commaList item
    "count"->Q.QCountItems <$> commaList counted
    _->P $ \path _->at "QOPERATION" path token "supported operations: ref, typed constant, sum, count, scale"
  _<-takeText ")"
  pure result
  where
    number=do
      t<-word
      P $ \path rest->do
        when (Text.length (tokenText t)>1235) (at "QLIMIT" path t "numeric literal exceeds 4096-bit budget")
        n<-numeric path t
        unless (Q.bounded n) (at "QLIMIT" path t "numeric literal exceeds 4096-bit budget")
        pure (n,rest)
    item=do
      _<-takeText "item";i<-word;_<-takeText "value";e<-parseQuantity (depth+1)
      hasFilter<-optionalText "when"
      condition<-if hasFilter then Just . tokenText <$> word else pure Nothing
      pure (Q.QItem (tokenText i) e condition)
    counted=do _<-takeText "item";i<-word;_<-takeText "when";c<-word;pure (tokenText i,tokenText c)

parseModelDeclaration :: P (RawModel -> RawModel)
parseModelDeclaration = do
  headToken <- word
  case tokenText headToken of
    "quantitative" -> do
      _ <- takeText "version"
      version <- string
      _ <- takeText ";"
      pure (\m->m {rawQuantitative=rawQuantitative m++[version]})
    "derive" -> do
      identifier <- word
      _ <- takeText "type"
      ty <- parseScalarType
      _ <- takeText "="
      expression <- parseQuantity 0
      _ <- takeText ";"
      let site=Q.QSite "" (tokenLine identifier) (tokenColumn identifier) 0 0 (tokenText identifier)
          definition=Q.QDefinition (tokenText identifier) (quantityType ty) expression site [] "" Nothing [] [] []
      pure (\m->m {rawScalars=rawScalars m++[(identifier,ty)],rawQuantDefinitions=rawQuantDefinitions m++[definition]})
    "requirement-template" -> do
      identifier <- word
      _ <- takeText "("
      parameters <- commaList parameter
      _ <- takeText ")"
      _ <- takeText "="
      body <- parseExpression
      _ <- takeText ";"
      pure (\model -> model {rawTemplates = rawTemplates model ++
        [RawTemplate identifier (tokenText identifier) parameters body "" "" Nothing "" []]})
    "requirement-use" -> do
      identifier <- word
      _ <- takeText "from"
      target <- word
      _ <- takeText "("
      arguments <- commaList word
      _ <- takeText ")"
      _ <- takeText "assessments"
      _ <- takeText "scenario"
      _ <- takeText ";"
      pure (\model -> model {rawScopedUses = rawScopedUses model ++ [(identifier,target,arguments)]})
    "dependency-condition" -> do
      identifier <- word
      _ <- takeText "type"
      _ <- takeText "technical-condition"
      _ <- takeText ";"
      pure (\model -> model { rawDependencySlots = rawDependencySlots model ++ [identifier] })
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
      declaredType <- parseScalarType
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
      pure (ownTemplates path bytes (tokenText identifier) Nothing (foldl (flip ($)) emptyModel declarations))

emptyRawModel :: Token -> RawModel
emptyRawModel identifier = RawModel identifier (Token WordToken "2048" 1 1)
  [] [] [] [] [] [] [] [] [] [] [] [] Nothing [] [] [] [] [] [] [] [] ("",BS.empty) Map.empty

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
      pure (RawModule name version exports (ownTemplates path bytes (tokenText name) (Just (tokenText version)) model))
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
        [value | Left value <- entries] [(i,v) | Right (i,v,_) <- entries]
        (Map.fromList [(tokenText i,r) | Right (i,_,Just r)<-entries]))
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
            "count" -> RawCountValue <$> word <*> word
            "unresolved" -> do
              _ <- takeText "reason"
              RawUnresolvedValue <$> string
            _ -> P $ \source _ -> at "SFT008" source valueKind "unsupported scalar value"
          hasReason <- optionalText "reason"
          reason <- if hasReason then Just <$> string else pure Nothing
          _ <- takeText ";"
          pure (Right (identifier,value,reason))
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
  Right rawModel | hasQuantities rawModel ->pure (at "QWORKFLOW" path (rawModelId rawModel)
    "this opt-in quantity model requires the quantitative execution/projection workflow")
  Right rawModel -> do
    composed <- loadTypedModules path rawModel
    pure $ do
      (model,moduleRecords) <- composed
      when (hasQuantities model) (at "QWORKFLOW" path (rawModelId rawModel)
        "selected quantitative scalars require the opt-in quantitative workflow")
      (scenarioPath,scenarioRaw) <- maybe
        (at "SFT011" path (rawModelId model) "typed-rules model requires a scenario") Right
        scenarioBytes
      scenario <- parseTypedFiniteScenario scenarioPath scenarioRaw
      when (tokenText (scenarioModel scenario) /= tokenText (rawModelId model))
        (at "SFT002" scenarioPath (scenarioModel scenario) "scenario model identity mismatch")
      program <- either (Left . importDiagnostic path rawModel) Right
        (validateModel path scenarioPath model scenario)
      pure program { finiteModules = moduleRecords }

hasQuantities :: RawModel -> Bool
hasQuantities m=not (null (rawQuantitative m) && null (rawQuantDefinitions m))
  || any (\(_,t)->case t of RawCount _->True;_->False) (rawScalars m)

-- Native source entry retains the checked plan until actual run/diagram time.
loadTypedFiniteQuantitative :: FilePath -> BS.ByteString -> Maybe (FilePath,BS.ByteString)
  -> IO (Either Diagnostic (TypedFiniteProgram,Maybe Q.QPlan))
loadTypedFiniteQuantitative path bytes supplied=case parseTypedFiniteModel path bytes of
  Left d->pure (Left d)
  Right raw | not (hasQuantities raw) && null (rawImports raw)->fmap (fmap (\p->(p,Nothing))) (loadTypedFiniteProgram path bytes supplied)
  Right raw->do
    loaded<-loadTypedModules path raw
    pure $ do
      (selected,records)<-loaded
      (sp,sb)<-maybe (at "QMISSING" path (rawModelId raw) "quantitative model requires scenario") Right supplied
      scenario<-parseTypedFiniteScenario sp sb
      unless (tokenText (scenarioModel scenario)==tokenText (rawModelId raw))
        (at "SFT002" sp (scenarioModel scenario) "scenario model identity mismatch")
      if hasQuantities selected then do
        expanded<-expandScopedModel path selected
        (p,q)<-prepareQuantities (Map.insert (normalise sp) sb (rawSourceBundle expanded)) path sp expanded scenario
        pure (p {finiteModules=records},q)
      else do
        p<-either (Left . importDiagnostic path raw) Right (validateModel path sp selected scenario)
        pure (p {finiteModules=records},Nothing)

-- Legacy fallback for diagnostics without retained declaration context.
-- Do not replace an authoritative primary/related pair with a name-based host
-- fallback. Selected declarations now retain their defining origin separately.
importDiagnostic :: FilePath -> RawModel -> Diagnostic -> Diagnostic
importDiagnostic path host issue
  | diagnosticPath issue == path
  , diagnosticRelated issue == Nothing
  , not (tokenText (diagnosticToken issue) `elem` hostDeclarations)
  , [use] <- [token | (_,token) <- rawUses host
    , last (Text.splitOn "::" (tokenText token)) == tokenText (diagnosticToken issue)] =
      issue { diagnosticToken = use, diagnosticRelated = Nothing
            , diagnosticMessage = diagnosticMessage issue
                <> "; at importing use-site (defining source location not retained)" }
  | otherwise = issue { diagnosticRelated = related }
  where
    related = case diagnosticRelated issue of
      Just (relatedPath,token) | relatedPath == path
        , tokenText token `notElem` [tokenText i | (i,_,_) <- rawPredicates host]
        , [use] <- [t | (_,t) <- rawUses host
          , last (Text.splitOn "::" (tokenText t)) == tokenText token] -> Just (path,use)
      value -> value
    hostDeclarations = map (tokenText . fst) (rawRequirements host)
      ++ [tokenText i | (i,_,_,_,_,_) <- rawRules host]
      ++ [tokenText i | (i,_,_,_,_,_) <- rawNorms host ++ rawRoutes host]

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
            validateSelectionDuplicates path model selections
            let merged = selectTemplates model aliased (foldl mergeSelection model selections)
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
  uniqueIdentities Map.empty imports
  when (length imports > 32) (at "SFT010" path (let (name,_,_) = imports !! 32 in name)
    "module count limit exceeded")
  where
    -- The comparison key includes the exact version; the diagnostic token must
    -- remain the actual source name, not a synthetic name@version span.
    uniqueIdentities _ [] = Right ()
    uniqueIdentities seen ((name,version,_):rest) =
      let key = (tokenText name,tokenText version)
      in case Map.lookup key seen of
        Just previous -> atRelated "SFT002" path name "duplicate module identity" path previous
        Nothing -> uniqueIdentities (Map.insert key name seen) rest

resolveUse :: FilePath -> [(Text,RawModule)] -> (Token,Token)
  -> Either Diagnostic (Text,Token,Token,RawModel)
resolveUse path modules (kindToken,qualifiedToken) = case Text.splitOn "::" (tokenText qualifiedToken) of
  [alias,identifier] -> case [declaration | (candidateAlias,declaration@(RawModule _ _ exports _)) <- modules,
      candidateAlias == alias,
      any (\(kindValue,item) -> tokenText kindValue == tokenText kindToken
        && tokenText item == identifier) exports] of
    [RawModule _ _ _ body] -> Right (tokenText kindToken,
      qualifiedToken { tokenText = identifier },qualifiedToken,body)
    [] -> at "SFT014" path qualifiedToken "private, missing or wrong-kind module reference"
    _ -> at "SFT014" path qualifiedToken "ambiguous module reference"
  _ -> at "SFT014" path qualifiedToken "module use must be alias-qualified"

mergeSelection :: RawModel -> (Text,Token,Token,RawModel) -> RawModel
mergeSelection host (kindValue,identifier,useSite,moduleModel) = merged
  { rawDeclarationSources = rawDeclarationSources host ++
      [(kind,token,file,Just useSite) | (kind,token,file,_) <- rawDeclarationSources moduleModel
      ,kind == kindValue, tokenText token == tokenText identifier]
  , rawQuantDefinitions=rawQuantDefinitions host++
      [d {Q.qUseSite=Just (uncurry (\file bytes->quantitySite file bytes useSite) (rawSourceOwner host))}
       | kindValue=="scalar",d<-rawQuantDefinitions moduleModel,Q.qName d==tokenText identifier]
  , rawSourceBundle=Map.union (rawSourceBundle host) (rawSourceBundle moduleModel) }
  where
  merged = case kindValue of
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
  selected accessor predicate = filter predicate (accessor moduleModel)

-- Admission happens while a resolved selection still owns both its module
-- declaration tokens and its actual host use token. After merging, names are
-- required to be unique; they cannot be used to reconstruct duplicate origins.
-- Priorities are edges (not unique named declarations) and deliberately absent.
validateSelectionDuplicates :: FilePath -> RawModel -> [(Text,Token,Token,RawModel)]
  -> Either Diagnostic ()
validateSelectionDuplicates _ _ [] = Right ()
validateSelectionDuplicates path host selections = mapM_ checkCategory categories
  where
    categories = [("requirement","SFDUPLICATE","duplicate use-site/requirement identity")]
      ++ [(kind,"SFT002",message) | (kind,message) <-
        [("entity-type","duplicate entity type"),("entity","duplicate entity")
        ,("enum-type","duplicate enum type"),("scalar","duplicate scalar")
        ,("predicate","duplicate predicate"),("proposition","duplicate proposition")
        ,("rule","duplicate rule"),("norm","duplicate norm")
        ,("responsibility-route","duplicate responsibility route")]]
    checkCategory (kind,code,message) = do
      let local = [(tokenText token,file,token) | (category,token,file,_) <- rawDeclarationSources host
                   ,category == kind]
            ++ [(tokenText i,path,i) | kind == "requirement",(i,_,_) <- rawScopedUses host]
      initial <- uniqueSites code message Map.empty local
      _ <- foldSelections kind code message initial selections
      pure ()
    foldSelections _ _ _ seen [] = Right seen
    foldSelections kind code message seen ((category,identifier,useSite,body):rest)
      | category /= kind = foldSelections kind code message seen rest
      | otherwise = do
          let original = [(tokenText token,file,token) | (k,token,file,_) <- rawDeclarationSources body
                           ,k == kind,tokenText token == tokenText identifier]
          -- A duplicate within the module is its own error, independent of the
          -- host selection. Do not replace those two original declaration sites.
          _ <- uniqueSites code message Map.empty original
          next <- uniqueSites code message seen [(tokenText identifier,path,useSite)
            | not (null original)]
          foldSelections kind code message next rest
    -- Keep the namespace key separate from the actual source token (in
    -- particular, a host token still contains its original alias qualification).
    uniqueSites _ _ seen [] = Right seen
    uniqueSites code message seen ((key,file,token):rest) = case Map.lookup key seen of
      Just (previousFile,previousToken) ->
        atRelated code file token message previousFile previousToken
      Nothing -> uniqueSites code message (Map.insert key (file,token) seen) rest

validateModel :: FilePath -> FilePath -> RawModel -> TypedFiniteScenario
  -> Either Diagnostic TypedFiniteProgram
validateModel = validateModelWith True

-- The ordinary loader retains its established evaluation-backed acceptance check.
-- Inspection uses the same structural checks, then checks ground input presence.
validateModelWith :: Bool -> FilePath -> FilePath -> RawModel -> TypedFiniteScenario
  -> Either Diagnostic TypedFiniteProgram
validateModelWith execute = validateModelMode execute False

validateModelMode :: Bool -> Bool -> FilePath -> FilePath -> RawModel -> TypedFiniteScenario
  -> Either Diagnostic TypedFiniteProgram
validateModelMode execute fullReadiness path scenarioPath rawModel scenario = do
  model <- expandScopedModel path rawModel
  validateExpandedModel execute fullReadiness path scenarioPath model scenario

validateExpandedModel :: Bool -> Bool -> FilePath -> FilePath -> RawModel -> TypedFiniteScenario
  -> Either Diagnostic TypedFiniteProgram
validateExpandedModel execute fullReadiness path scenarioPath model scenario = do
  case rawDependencySlots model of
    slot:_ -> at "DEPMISSING" path slot "dependency template requires a checked-project binding; standalone execution is unavailable"
    [] -> pure ()
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
  mapM_ (\decl@(i,_)->atDeclaration "entity" i (\file->validateEntity file typeNames decl)) (rawEntities model)
  mapM_ (validateDomainSize path) (Set.toList typeNames)
  scalarDecls <- traverse (\decl@(i,_)->atDeclaration "scalar" i (\file->scalarDeclaration file enumMap decl)) (rawScalars model)
  predicates <- traverse (\decl@(identifier,_,_) ->
    let (file,site)=predicateSource path model identifier
    in relatedImport path site (predicateDeclaration file typeNames decl)) (rawPredicates model)
  let entities = [EntityDecl (tokenText identifier) (tokenText kindValue)
        | (identifier,kindValue) <- rawEntities model]
      entityIndex = Map.fromList [(identifier,kindValue) | EntityDecl identifier kindValue <- entities]
      predicateIndex = Map.fromList [(predicateName item,item) | item <- predicates]
      scalarIndex = Map.fromList [(scalarName item,scalarType item) | item <- scalarDecls]
      requirementIndex = Map.fromList [(tokenText identifier,expression)
        | (identifier,expression) <- rawRequirements model]
      propositionSet = Set.fromList (map tokenText (rawPropositions model))
  mapM_ (\(identifier,expression) -> relatedPredicate expression
    (atDeclaration "requirement" identifier (\file->validateExpression file identifier typeNames entityIndex
      predicateIndex scalarIndex requirementIndex Set.empty 0 expression))) (rawRequirements model)
  rules <- traverse (\decl@(i,_,_,_,_,_)->atDeclaration "rule" i (\file->ruleDeclaration file typeNames propositionSet entityIndex
    predicateIndex scalarIndex requirementIndex decl)) (rawRules model)
  norms <- traverse (\decl@(i,_,_,_,_,_)->atDeclaration "norm" i (\file->normDeclaration file propositionSet entityIndex typeNames
    predicateIndex scalarIndex requirementIndex decl)) (rawNorms model)
  routes <- traverse (\decl@(i,_,_,_,_,_)->atDeclaration "responsibility-route" i (\file->routeDeclaration file propositionSet entityIndex typeNames
    predicateIndex scalarIndex requirementIndex decl)) (rawRoutes model)
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
  nodeCount <- if execute then do
      expanded <- either (at "SFT011" scenarioPath (scenarioIdentifier scenario)) Right
        (evaluateTypedFinite program)
      pure (length (finiteResultExpressions expanded) + length (finiteResultRules expanded)
        + length (finiteResultPropositions expanded) + expressionNodes program)
    else do
      if fullReadiness then either (at "SFT011" scenarioPath (scenarioIdentifier scenario)) Right
        (checkTypedFiniteInputs program) else checkGroundInputs path scenarioPath model scenario program
      pure (length (finiteRequirements program) + length (finiteRules program)
        + length (finitePropositions program) + expressionNodes program)
  when (nodeCount > fromInteger limit) (at "SFT010" path (rawLimit model)
    "generated-node limit exceeded")
  pure program
  where
    atDeclaration kind identifier action=
      let (file,site)=declarationSource path model kind identifier
      in relatedImport path site (action file)
    relatedPredicate (PredicateExpr name _) (Left issue)
      | diagnosticCode issue `elem` ["SFT004","SFT005"] = case
          [token | (token,_,_) <- rawPredicates model, tokenText token == name] of
          [token] -> Left issue { diagnosticRelated = Just (fst (predicateSource path model token),token) }
          _ -> Left issue
    relatedPredicate _ result = result
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
  RawCount domain | Q.numeric (Q.QCount (tokenText domain))->Right IntegerType
                  | otherwise->at "QTYPE" path domain "count domain must be nonblank and <=128 characters"
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

validateExpression :: FilePath -> Token -> Set Text -> Map Text Text -> Map Text PredicateDecl
  -> Map Text ScalarType -> Map Text FiniteExpr -> Set Text -> Int -> FiniteExpr
  -> Either Diagnostic ()
validateExpression path origin types entities predicates scalars requirements scope depth expression = do
  when (depth > 4) (at "SFT010" path origin "quantifier nesting limit exceeded")
  case expression of
    PredicateExpr name terms -> do
      signature <- maybe (at "SFT003" path origin ("unknown predicate " <> name)) Right
        (Map.lookup name predicates)
      when (length terms /= length (predicateArguments signature))
        (at "SFT004" path origin ("predicate " <> name <> " argument count mismatch: expected "
          <> Text.pack (show (length (predicateArguments signature)))
          <> ", supplied " <> Text.pack (show (length terms))))
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
    recurse = validateExpression path origin types entities predicates scalars requirements scope depth
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
      validateExpression path origin types entities predicates scalars requirements
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
  validateExpression path identifier types entities predicates scalars requirements scope 0 body
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
  validateExpression path identifier types entities predicates scalars requirements Set.empty 0 body
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
  validateExpression path identifier types entities predicates scalars requirements Set.empty 0 body
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
      | Set.member key seen = at "SFT002" path (Token WordToken (groundKey (groundPredicate item) (groundArguments item)) 1 1)
          "duplicate ground classification"
      | otherwise = go (Set.insert key seen) rest
      where key = groundIdentity (groundPredicate item) (groundArguments item)

scalarAssignment :: FilePath -> Map Text ScalarType -> (Token,RawValue)
  -> Either Diagnostic (Text,ScalarValue)
scalarAssignment path declarations (identifier,raw) = do
  expected <- maybe (at "SFT003" path identifier "unknown scalar assignment") Right
    (Map.lookup (tokenText identifier) declarations)
  value <- case (expected,raw) of
    (kindValue,RawUnresolvedValue reason) -> Right (ScalarUnresolved (tokenText reason) kindValue)
    (IntegerType,RawIntegerValue token) -> IntegerValue <$> numeric path token
    (IntegerType,RawCountValue _ token) -> IntegerValue <$> numeric path token
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

-- | Structured parsed declarations. FiniteExpr is already constructed by this
-- parser; child-token spans are not retained. Identifier tokens remain exact.
inspectTypedFiniteModel :: FilePath -> BS.ByteString -> Either Diagnostic J
inspectTypedFiniteModel path bytes = do
  model <- parseTypedFiniteModel path bytes
  tokens <- lexSource path bytes
  let loc = locatedToken path bytes
      expressionRow (identifier,expression) = JObj
        [("id",loc identifier),("expression",expressionJson expression)]
      rawType RawInteger = JObj [("kind",JStr "integer")]
      rawType RawDate = JObj [("kind",JStr "date")]
      rawType (RawEnum token) = JObj [("kind",JStr "enum"),("name",loc token)]
      rawType (RawMoney token) = JObj [("kind",JStr "money"),("currency",loc token)]
      rawType (RawCount token) = JObj [("kind",JStr "count"),("domain",loc token)]
  pure (JObj ([("id",loc (rawModelId model)),("limit",loc (rawLimit model))
    ,("tokens",JArr (map loc tokens))
    ,("entity_types",JArr (map loc (rawEntityTypes model)))
    ,("entities",JArr [JObj [("id",loc i),("type",loc t)] | (i,t) <- rawEntities model])
    ,("predicates",JArr [JObj [("id",loc i),("arguments",JArr (map loc args)),("kind",loc k)]
      | (i,args,k) <- rawPredicates model])
    ,("scalars",JArr [JObj [("id",loc i),("type",rawType t)] | (i,t) <- rawScalars model])
    ,("requirements",JArr (map expressionRow (rawRequirements model)))
    ,("rules",JArr [JObj [("id",loc i),("parameters",JArr [JObj [("variable",loc v),("type",loc t)] | (v,t) <- ps])
      ,("polarity",loc polarity),("conclusion",loc conclusion),("body",expressionJson body)
      ,("citation",maybe JNull loc citation)] | (i,ps,polarity,conclusion,body,citation) <- rawRules model])
    ,("propositions",JArr (map loc (rawPropositions model)))
    ,("limitations",JArr (map loc (rawLimitations model)))
    ,("scope",JStr "declaration overview plus complete source tokens; not lossless authoring interchange")]
    ++ [("quantitative", either (const JNull) id (decodeJson (BL.toStrict (A.encode (rawQuantDefinitions model)))))
       | not (null (rawQuantDefinitions model))]
    ++ if null (rawTemplates model) && null (rawScopedUses model) then [] else
      [("scoped_templates",JArr [JObj [("id",loc (rawTemplateName t))
        ,("formals",JArr [JObj [("variable",loc v),("type",loc k)] | (v,k)<-rawTemplateParameters t])
        ,("body",expressionJson (rawTemplateBody t))] | t<-rawTemplates model])
      ,("scoped_uses",JArr [JObj [("id",loc i),("definition",loc target),("arguments",JArr (map loc args))
        ,("assessments",JStr "scenario")] | (i,target,args)<-rawScopedUses model])]))

-- | Inspection admits ground, non-module programs only. It never calls
-- evaluateTypedFinite: presence checks traverse structure, not truth values.
prepareTypedFiniteInspection :: FilePath -> BS.ByteString -> Maybe (FilePath,BS.ByteString)
  -> Either Diagnostic TypedFiniteProgram
prepareTypedFiniteInspection path bytes supplied = do
  model <- parseTypedFiniteModel path bytes
  when (hasQuantities model) (at "SFI002" path (rawModelId model)
    "quantitative parsed inspection is available; compose check retains the non-evaluated complete quantity plan; frozen kernel lowering alone omits authored calculations")
  unless (null (rawTemplates model) && null (rawScopedUses model))
    (at "SFI002" path (rawModelId model)
      "checked inspection of scoped templates is unavailable; use parsed inspection and non-evaluating compose check with the complete scoped projection after execution")
  unless (null (rawImports model) && null (rawUses model)
    && null (rawNorms model) && null (rawRoutes model)
    && all (null . parameters) (rawRules model))
    (at "SFI002" path (rawModelId model)
      "checked typed inspection currently requires ground rules without imports, norms or responsibility routes")
  (scenarioPath,rawScenario) <- maybe (at "SFT011" path (rawModelId model)
    "typed-rules model requires a scenario") Right supplied
  scenario <- parseTypedFiniteScenario scenarioPath rawScenario
  when (tokenText (scenarioModel scenario) /= tokenText (rawModelId model))
    (at "SFT002" scenarioPath (scenarioModel scenario) "scenario model identity mismatch")
  validateModelWith False path scenarioPath model scenario
  where parameters (_,ps,_,_,_,_) = ps

checkGroundInputs :: FilePath -> FilePath -> RawModel -> TypedFiniteScenario -> TypedFiniteProgram
  -> Either Diagnostic ()
checkGroundInputs path scenarioPath raw scenario program = do
  mapM_ (uncurry (walk Set.empty)) (rawRequirements raw)
  mapM_ (\(identifier,_,_,_,body,_) -> walk Set.empty identifier body) (rawRules raw)
  where
    facts = Set.fromList [groundIdentity (groundPredicate f) (groundArguments f) | f <- finiteFacts program]
    definitions = Map.fromList [(tokenText i,(i,e)) | (i,e) <- rawRequirements raw]
    walk active origin expression = case expression of
      PredicateExpr name arguments -> do
        entities <- traverse (entity origin) arguments
        let key = groundKey name entities
        unless (Set.member (groundIdentity name entities) facts) (atRelated "SFT011" scenarioPath (scenarioIdentifier scenario)
          ("missing ground classification " <> key) path origin)
      ComparisonExpr {} -> Right () -- Declaration/value checks ran above; no comparison is computed.
      AllExpr members -> mapM_ (walk active origin) members
      AnyExpr members -> mapM_ (walk active origin) members
      NotExpr member -> walk active origin member
      CardinalityExpr _ _ members -> mapM_ (walk active origin) members
      ReferenceExpr name
        | Set.member name active -> at "SFT010" path origin "cyclic requirement expansion"
        | otherwise -> case Map.lookup name definitions of
            Nothing -> at "SFT003" path origin ("unknown requirement " <> name)
            Just (identifier,body) -> walk (Set.insert name active) identifier body
      _ -> at "SFI002" path origin "quantified inspection is unsupported; use the existing compile/run path"
    entity _ (EntityTerm identifier) = Right identifier
    entity origin _ = at "SFI002" path origin "inspection requires ground entity terms"


inspectTypedFiniteScenario :: FilePath -> BS.ByteString -> Either Diagnostic J
inspectTypedFiniteScenario path bytes = do
  scenario <- parseTypedFiniteScenario path bytes
  tokens <- lexSource path bytes
  let loc = locatedToken path bytes
  pure (JObj [("id",loc (scenarioIdentifier scenario)),("model",loc (scenarioModel scenario))
    ,("classifications",JArr [JObj [("predicate",loc p),("arguments",JArr (map loc args))
      ,("status",loc status),("reason",loc reason)] | (p,args,status,reason) <- scenarioFacts scenario])
    ,("value_declarations",JArr [loc i | (i,_) <- scenarioValues scenario])
    ,("tokens",JArr (map loc tokens))])

-- Actual parser-retained declaration identities. References in rule bodies are
-- deliberately absent; textual adjacency is not declaration correspondence.
typedDeclarationTokens :: FilePath -> BS.ByteString -> Either Diagnostic [(Text,Token)]
typedDeclarationTokens path bytes = do
  model <- parseTypedFiniteModel path bytes
  pure ([ ("entity-type",t) | t <- rawEntityTypes model ]
    ++ [("entity",t) | (t,_) <- rawEntities model]
    ++ [("predicate",t) | (t,_,_) <- rawPredicates model]
    ++ [("scalar",t) | (t,_) <- rawScalars model]
    ++ [("requirement",t) | (t,_) <- rawRequirements model]
    ++ [("rule",t) | (t,_,_,_,_,_) <- rawRules model]
    ++ [("proposition",t) | t <- rawPropositions model])


-- | Direct source closure for immutable dependency bundles. Resolution is against
-- retained virtual paths; no evaluation and no live IO occurs in preparation.
dependencySourcePaths :: FilePath -> BS.ByteString -> Either Diagnostic [FilePath]
dependencySourcePaths _ bytes | BS.take 1 (BS.dropWhile (`elem` [9,10,13,32]) bytes)=="{" = Right []
dependencySourcePaths path bytes = do
  tokens <- lexSource path bytes
  case tokens of
    t:_ | tokenText t == "typed-rules-case" -> do
      RawTypedCase _ model _ allegations <- parseTypedFiniteCase path bytes
      pure (Text.unpack (tokenText model):[Text.unpack (tokenText sc) | (_,sc,_)<-allegations])
    t:_ | tokenText t == "typed-rules-model" -> do
      m <- parseTypedFiniteModel path bytes
      pure [Text.unpack (tokenText root) </> Text.unpack (tokenText name <> "@" <> tokenText version <> ".yh")
        | Just root <- [rawModuleRoot m], (name,version,_) <- rawImports m]
    _ -> pure []

prepareDependencyTyped :: Map FilePath BS.ByteString -> FilePath -> Maybe FilePath -> Maybe Text
  -> Either Diagnostic (TypedFiniteProgram,[(Text,Text)],Maybe (Text,Text))
prepareDependencyTyped bundle path scenarioPath allegation = do
  (p,s,c,_) <- prepareDependencyTypedScoped bundle path scenarioPath allegation
  pure (p,s,c)

prepareDependencyTypedScoped :: Map FilePath BS.ByteString -> FilePath -> Maybe FilePath -> Maybe Text
  -> Either Diagnostic (TypedFiniteProgram,[(Text,Text)],Maybe (Text,Text),ScopedCompilation)
prepareDependencyTypedScoped bundle path scenarioPath allegation = do
  (p,s,c,sc,q)<-prepareDependencyTypedQuantitative bundle path scenarioPath allegation
  case q of
    Nothing->pure (p,s,c,sc)
    Just _->at "QWORKFLOW" path (Token WordToken "" 1 1)
      "quantitative derivations require the checked quantitative workflow; no frozen scalar-input coercion"

prepareDependencyTypedQuantitative :: Map FilePath BS.ByteString -> FilePath -> Maybe FilePath -> Maybe Text
  -> Either Diagnostic (TypedFiniteProgram,[(Text,Text)],Maybe (Text,Text),ScopedCompilation,Maybe Q.QPlan)
prepareDependencyTypedQuantitative bundle path scenarioPath allegation = do
  bytes <- source path
  tokens <- lexSource path bytes
  case tokens of
    t:_ | tokenText t == "typed-rules-case" -> do
      RawTypedCase caseId modelToken shared allegations <- parseTypedFiniteCase path bytes
      uniqueTokens path "DEPNAME" "duplicate allegation" [i | (i,_,_)<-allegations]
      uniqueTokens path "DEPNAME" "duplicate shared classification" [i | (i,_,_,_,_)<-shared]
      selected <- maybe (at "DEPNAME" path caseId "case component requires an allegation entry") Right allegation
      (identifier,sc,uses) <- case [a | a@(i,_,_)<-allegations,tokenText i==selected] of
        [a]->Right a; _->at "DEPNAME" path caseId "unknown or ambiguous allegation entry"
      when (null allegations || length allegations>32) (at "DEPLIMIT" path caseId "case requires 1..32 allegations")
      mapM_ (\(_,_,_,status,_)->statusValue path status >> pure ()) shared
      let mp=takeDirectory path </> Text.unpack (tokenText modelToken)
          sp=takeDirectory path </> Text.unpack (tokenText sc)
      m <- source mp >>= parseTypedFiniteModel mp >>= modules mp
      scenario <- source sp >>= parseTypedFiniteScenario sp
      additions <- traverse (\i->case [x | x@(k,_,_,_,_)<-shared,tokenText k==tokenText i] of
        [(_,predId,args,status,reason)]->Right (predId,args,status,reason)
        _->at "DEPNAME" path i "unknown shared classification") uses
      (program,slots,scoped,quantitative) <- prepare mp sp m (scenario {scenarioFacts=scenarioFacts scenario++additions})
      let actualOrigins=[a {selectedSource=normalise path} | a<-scopedAssessments scoped
            ,any (\(predId,args,_,_)->selectedPredicate a==tokenText predId && selectedArguments a==map tokenText args) additions]
          retained=[a | a<-scopedAssessments scoped,not (any (\b->selectedPredicate a==selectedPredicate b && selectedArguments a==selectedArguments b) actualOrigins)]
      pure (program,slots,Just (tokenText caseId,tokenText identifier),scoped {scopedAssessments=retained++actualOrigins},quantitative)
    _ -> do
      when (allegation/=Nothing) (at "DEPNAME" path origin "allegation selector requires an actual typed case")
      m <- parseTypedFiniteModel path bytes >>= modules path
      sp <- maybe (at "DEPMISSING" path origin "component requires scenario") Right scenarioPath
      scenario <- source sp >>= parseTypedFiniteScenario sp
      (program,slots,scoped,quantitative)<-prepare path sp m scenario
      pure (program,slots,Nothing,scoped,quantitative)
  where
    origin=Token EndToken "" 1 1
    source file=maybe (at "DEPMISSING" file origin "source is absent from retained bundle") Right (Map.lookup (normalise file) bundle)
    modules mp m = do
      validateImportIdentities mp (rawImports m)
      loaded <- traverse (\(name,version,alias)->do
        unless (safeModuleName (tokenText name) && safeVersion (tokenText version))
          (at "SFT013" mp name "invalid exact module identity")
        root<-maybe (at "SFT013" mp name "module-root required") Right (rawModuleRoot m)
        unless (not (isAbsolute (Text.unpack (tokenText root)))
          && all (`notElem` ["",".",".."]) (Text.splitOn "/" (tokenText root)))
          (at "SFT013" mp root "unsafe module root")
        let file=takeDirectory mp </> Text.unpack (tokenText root) </> Text.unpack (tokenText name<>"@"<>tokenText version<>".yh")
        declaration@(RawModule actual actualVersion _ body)<-source file >>= parseTypedFiniteModule file
        unless (tokenText actual==tokenText name && tokenText actualVersion==tokenText version
          && null (rawImports body) && null (rawUses body) && null (rawDependencySlots body))
          (at "SFT013" file actual "module identity mismatch or unsupported nested import/template")
        pure (alias,declaration)) (rawImports m)
      selections<-traverse (resolveUse mp [(tokenText a,d) | (a,d)<-loaded]) (rawUses m)
      validateSelectionDuplicates mp m selections
      pure (selectTemplates m [(tokenText a,d) | (a,d)<-loaded] (foldl mergeSelection m selections))
    prepare mp sp original scenario = do
      m <- expandScopedModel mp original
      scoped <- scopedCompilation mp sp original scenario
      unless (tokenText (scenarioModel scenario)==tokenText (rawModelId m))
        (at "SFT002" sp (scenarioModel scenario) "scenario model identity mismatch")
      uniqueTokens mp "DEPWRITER" "duplicate condition slot" (rawDependencySlots m)
      let slots=[(tokenText i,"dep_"<>sha256Text (UTF8.encodeUtf8 (tokenText i))) | i<-rawDependencySlots m]
          generatedType="dep_template_type"
          generatedEntity="dep_template_entity"
          generated=map snd slots++[generatedType,generatedEntity]
      when (not (null slots) && (any (\i->tokenText i `elem` generated) (allIdentifiers m)
          || any (\(i,_,_)->tokenText i=="condition") (rawPredicates m)))
        (at "DEPWRITER" mp (rawModelId m) "template reserved identity conflicts with an authored declaration")
      let tok x=Token WordToken x 1 1
          rewrite e=case e of
            PredicateExpr "condition" [EntityTerm i] | not (null slots) -> case lookup i slots of
              Just n->Right (PredicateExpr n [EntityTerm generatedEntity])
              Nothing->at "DEPNAME" mp (rawModelId m) ("unknown condition slot "<>i)
            PredicateExpr "condition" _ | not (null slots)->at "DEPCATEGORY" mp (rawModelId m) "condition expects one declared slot"
            AllExpr xs->AllExpr <$> traverse rewrite xs; AnyExpr xs->AnyExpr <$> traverse rewrite xs
            NotExpr x->NotExpr <$> rewrite x; ForallExpr v t x->ForallExpr v t <$> rewrite x
            ExistsExpr v t x->ExistsExpr v t <$> rewrite x
            CardinalityExpr k n xs->CardinalityExpr k n <$> traverse rewrite xs
            _->Right e
      requirements<-traverse (\(i,e)->(,) i <$> rewrite e) (rawRequirements m)
      rules<-traverse (\(i,ps,pol,p,e,c)->do e'<-rewrite e; pure (i,ps,pol,p,e',c)) (rawRules m)
      norms<-traverse (\(i,a,modality,p,e,c)->do e'<-rewrite e;pure (i,a,modality,p,e',c)) (rawNorms m)
      routes<-traverse (\(i,a,k,p,e,c)->do e'<-rewrite e;pure (i,a,k,p,e',c)) (rawRoutes m)
      -- Placeholders exist only during structural readiness. They are never
      -- observations and are replaced by execution-only inputs before evaluation.
      let withSlots=m {rawDependencySlots=[],rawRequirements=requirements,rawRules=rules,rawNorms=norms,rawRoutes=routes
            ,rawEntityTypes=rawEntityTypes m++[tok generatedType | not (null slots)]
            ,rawEntities=rawEntities m++[(tok generatedEntity,tok generatedType) | not (null slots)]
            ,rawPredicates=rawPredicates m++[(tok n,[tok generatedType],tok "circumstance") | (_,n)<-slots]}
          scenarioSlots=scenario {scenarioFacts=scenarioFacts scenario++
            [(tok n,[tok generatedEntity],tok "unresolved",Token StringToken "structural binding placeholder; not an observation" 1 1) | (_,n)<-slots]}
      -- Only an active dependency construct owns these input identities.
      -- Without holes, condition is an ordinary authored predicate.
      when (not (null slots) && any (\(i,_,_,_)->tokenText i `elem` (map fst slots++map snd slots++["condition"])) (scenarioFacts scenario))
        (at "DEPWRITER" sp (scenarioIdentifier scenario) "a dependency slot cannot have a direct classification")
      (program,quantitative)<-prepareQuantities bundle mp sp withSlots scenarioSlots
      pure (program,slots,scoped,quantitative)

-- Static quantitative preparation retains actual authored values separately
-- from readiness-only output placeholders. No arithmetic/filter is evaluated.
prepareQuantities :: Map FilePath BS.ByteString -> FilePath -> FilePath -> RawModel -> TypedFiniteScenario
  -> Either Diagnostic (TypedFiniteProgram,Maybe Q.QPlan)
prepareQuantities bundle mp sp model scenario
  | null (rawQuantitative model) && null definitions && not (any isCount (rawScalars model)) = do
      when (any (\(_,v)->case v of RawCountValue {}->True;_->False) (scenarioValues scenario))
        (at "QFORMAT" sp (scenarioIdentifier scenario) "count inputs require an opt-in quantitative model")
      p<-validateModelMode False True mp sp model scenario
      pure (p,Nothing)
  | otherwise=do
      unless (map tokenText (rawQuantitative model)==[Q.quantitativeFormat])
        (at "QFORMAT" mp (rawModelId model) "exactly one quantitative version declaration is required")
      mapM_ (\(i,_)->when (tokenText i `elem` outputs)
        (at "QWRITER" sp i "a derived-only output cannot have an authored supplied value")) (scenarioValues scenario)
      mapM_ (\(_,raw)->case raw of
        RawIntegerValue t->literalSize t
        RawMoneyValue _ t->literalSize t
        RawCountValue _ t->literalSize t
        _->pure ()) (scenarioValues scenario)
      let tok i=Token WordToken i 1 1
          placeholders=[(tok (Q.qName d),RawUnresolvedValue (Token StringToken "static derivation placeholder; not evaluated and not a supplied assessment" 1 1)) | d<-definitions]
      p<-validateModelMode False True mp sp model (scenario {scenarioValues=scenarioValues scenario++placeholders})
      inputs<-traverse (input p) (scenarioValues scenario)
      mapM_ checkImportedAuthority definitions
      plan<-either (Left . issue) Right (Q.checkQuantitative p types inputs definitions)
      let conditions=[(tokenText i,sourceSite "requirement" i) | (i,_)<-rawRequirements model]
      pure (p,Just plan {Q.qConditions=conditions})
  where
    definitions=rawQuantDefinitions model
    literalSize t=when (Text.length (tokenText t)>1235)
      (at "QLIMIT" sp t "numeric input literal exceeds the 4096-bit parsing budget")
    outputs=map Q.qName definitions
    types=Map.fromList [(tokenText i,quantityType t) | (i,t)<-rawScalars model]
    isCount (_,RawCount _)=True
    isCount _=False
    input p (i,raw)=do
      let name=tokenText i
      ty<-maybe (at "QNAME" sp i "unknown quantitative input") Right (Map.lookup name types)
      case (ty,raw) of
        (Q.QCount domain,RawCountValue actual _)->unless (domain==tokenText actual) (at "QTYPE" sp actual "count domain mismatch")
        (Q.QCount _,RawUnresolvedValue _)->pure ()
        (Q.QCount _,_)->at "QTYPE" sp i "Count inputs require an explicit count domain value"
        (_,RawCountValue _ _)->at "QTYPE" sp i "count values cannot supply a dimensionless/currency/date/enum scalar"
        _->pure ()
      reason<-case raw of
        RawUnresolvedValue r->pure (tokenText r)
        _->maybe (at "QREASON" sp i "quantitative inputs require an explicit source reason") (pure . tokenText)
             (Map.lookup name (scenarioValueReasons scenario))
      value<-maybe (at "QMISSING" sp i "missing checked input value") Right (Map.lookup name (finiteValues p))
      let bytes=Map.findWithDefault BS.empty (normalise sp) bundle
      declaration<-case [d | (d,_)<-rawScalars model,tokenText d==name] of
        [d]->pure (sourceSite "scalar" d)
        _->at "QNAME" sp i "input has no unique authored scalar declaration"
      pure (Q.QInput name ty value reason (quantitySite sp bytes i) (sha256Text bytes) declaration)
    sourceSite kind i=let (file,_)=declarationSource mp model kind i
      in quantitySite file (Map.findWithDefault BS.empty (normalise file) bundle) i
    checkImportedAuthority d=case Q.qUseSite d of
      Nothing->pure ()
      Just _->do
        let actual kind name=case [token | (k,token,_,_)<-rawDeclarationSources model,k==kind,tokenText token==name] of
              [i]->Just (sourceSite kind i)
              _->Nothing
            originals=Q.qInputOrigins d
        unless (all (\name->name `elem` map fst originals) (quantityReferences (Q.qExpression d)))
          (Left (issue (Q.QFailure "QAUTHORITY" "imported derivation must declare its scalar inputs in its original module" (Just (Q.qName d)))))
        mapM_ (\(name,site)->unless (actual "scalar" name==Just site)
          (Left (issue (Q.QFailure "QAUTHORITY" ("select the original module scalar explicitly: "<>name) (Just (Q.qName d)))))) originals
        unless (all (\name->name `elem` map fst (Q.qFilterOrigins d)) (quantityFilters (Q.qExpression d)))
          (Left (issue (Q.QFailure "QAUTHORITY" "imported inclusion requires its original module requirement" (Just (Q.qName d)))))
        mapM_ (\(name,site)->unless (actual "requirement" name==Just site)
          (Left (issue (Q.QFailure "QAUTHORITY" ("select the original inclusion requirement explicitly: "<>name) (Just (Q.qName d)))))) (Q.qFilterOrigins d)
    issue e=case [d | d<-definitions,Just (Q.qName d)==Q.qFailureOutput e] of
      [d]->let s=Q.qSite d in Diagnostic (Q.qFailureCode e) (Q.qSource s)
        (Token WordToken (Q.qToken s) (Q.qLine s) (Q.qColumn s)) (Q.qFailureMessage e)
        (fmap (\u->(Q.qSource u,Token WordToken (Q.qToken u) (Q.qLine u) (Q.qColumn u))) (Q.qUseSite d))
      _->Diagnostic (Q.qFailureCode e) mp (rawModelId model) (Q.qFailureMessage e) Nothing

-- Exact authored owner/source retained independently of a use-site alias.
ownTemplates :: FilePath -> BS.ByteString -> Text -> Maybe Text -> RawModel -> RawModel
ownTemplates path bytes owner version m=m
 {rawTemplates=map own (rawTemplates m)
 ,rawDeclarationSources=[(kind,i,normalise path,Nothing) | (kind,i)<-declarations]
 ,rawSourceOwner=(normalise path,bytes)
 ,rawSourceBundle=Map.singleton (normalise path) bytes
 ,rawQuantDefinitions=map ownQuantity (rawQuantDefinitions m)}
 where
  ownQuantity d=d {Q.qSite=quantitySite path bytes (Token WordToken (Q.qName d) (Q.qLine (Q.qSite d)) (Q.qColumn (Q.qSite d)))
    ,Q.qDefinitionKey=[Text.pack (normalise path),owner,maybe "local" id version,Q.qName d,sha256Text bytes]
    ,Q.qDefinitionVersion=case rawQuantitative m of [v]->tokenText v;_->""
    ,Q.qSignatures=[(tokenText i,quantityType t) | (i,t)<-rawScalars m
        ,tokenText i `elem` refs d]
    ,Q.qInputOrigins=[(tokenText i,quantitySite path bytes i) | (i,_)<-rawScalars m,tokenText i `elem` refs d]
    ,Q.qFilterOrigins=[(tokenText i,quantitySite path bytes i) | (i,_)<-rawRequirements m,tokenText i `elem` filterNames d]}
  filterNames d=nubText (concatMap (conditionNames Set.empty) (quantityFilters (Q.qExpression d)))
  conditionNames seen name | Set.member name seen=[]
                          | otherwise=name:case lookup name [(tokenText i,e) | (i,e)<-rawRequirements m] of
                              Nothing->[]
                              Just e->concatMap (conditionNames (Set.insert name seen)) (requirementReferences e)
  refs d=nubText (quantityReferences (Q.qExpression d)++concat
      [scalarReferences e | (i,e)<-rawRequirements m,tokenText i `elem` filterNames d])
  nubText=Set.toList . Set.fromList
  scalarReferences e=case e of ComparisonExpr _ l r u->l:r:maybe [] (:[]) u;_->concatMap scalarReferences (Q.children e)
  requirementReferences e=case e of ReferenceExpr i->[i];_->concatMap requirementReferences (Q.children e)
  declarations=[("entity-type",i) | i<-rawEntityTypes m]
    ++ [("entity",i) | (i,_)<-rawEntities m] ++ [("enum-type",i) | (i,_)<-rawEnums m]
    ++ [("scalar",i) | (i,_)<-rawScalars m] ++ [("predicate",i) | (i,_,_)<-rawPredicates m]
    ++ [("proposition",i) | i<-rawPropositions m] ++ [("requirement",i) | (i,_)<-rawRequirements m]
    ++ [("rule",i) | (i,_,_,_,_,_)<-rawRules m]
    ++ [("norm",i) | (i,_,_,_,_,_)<-rawNorms m]
    ++ [("responsibility-route",i) | (i,_,_,_,_,_)<-rawRoutes m]
    ++ [("priority",i) | (i,_)<-rawPriorities m]
  own t=t {rawTemplatePath=normalise path,rawTemplateOwner=owner,rawTemplateVersion=version
              ,rawTemplateDigest=sha256Text bytes
              ,rawTemplateSignature=rawPredicates m}

quantityReferences :: Q.QExpr -> [Text]
quantityReferences e=case e of
  Q.QRef i->[i];Q.QScale _ x->quantityReferences x
  Q.QSum xs->concat [quantityReferences x | Q.QItem _ x _<-xs];_->[]

quantityFilters :: Q.QExpr -> [Text]
quantityFilters e=case e of
  Q.QScale _ x->quantityFilters x
  Q.QSum xs->concat [maybe [] (:[]) c++quantityFilters x | Q.QItem _ x c<-xs]
  Q.QCountItems xs->map snd xs
  _->[]

quantitySite :: FilePath -> BS.ByteString -> Token -> Q.QSite
quantitySite file bytes token=Q.QSite (normalise file) (tokenLine token) (tokenColumn token)
  offset (offset+BS.length (UTF8.encodeUtf8 (tokenText token))) (tokenText token)
 where offset=sum [BS.length line+1 | line<-take (tokenLine token-1) (BS.split 10 bytes)]+tokenColumn token-1

predicateSource :: FilePath -> RawModel -> Token -> (FilePath,Maybe Token)
predicateSource fallback m=declarationSource fallback m "predicate"

declarationSource :: FilePath -> RawModel -> Text -> Token -> (FilePath,Maybe Token)
declarationSource fallback m kind token=case
  [(file,site) | (category,identifier,file,site)<-rawDeclarationSources m
  ,category==kind,tokenText identifier==tokenText token] of
  [source]->source
  _->(fallback,Nothing)

relatedImport :: FilePath -> Maybe Token -> Either Diagnostic a -> Either Diagnostic a
relatedImport host site result=case (site,result) of
  (Just token,Left issue) | diagnosticRelated issue==Nothing ->
    Left issue {diagnosticRelated=Just (host,token)}
  _->result

selectTemplates :: RawModel -> [(Text,RawModule)] -> RawModel -> RawModel
selectTemplates host modules merged=merged {rawTemplates=rawTemplates host++
  [t {rawTemplateLookup=alias<>"::"<>tokenText (rawTemplateName t)}
  | (alias,RawModule _ _ exports body)<-modules,t<-rawTemplates body
  ,any (\(k,i)->tokenText k=="requirement-template" && tokenText i==tokenText (rawTemplateName t)) exports
  ,any (\(_,target,_)->tokenText target==alias<>"::"<>tokenText (rawTemplateName t)) (rawScopedUses host)]}

-- Formal variables are replaced only by checked entity constants. Quantifier
-- shadowing is refused by the existing checker; constants cannot be captured.
expandScopedModel :: FilePath -> RawModel -> Either Diagnostic RawModel
expandScopedModel path m=do
  uniqueTokens path "SFDUPLICATE" "duplicate template identity" (map rawTemplateName local)
  uniqueTokens path "SFDUPLICATE" "duplicate use-site/requirement identity"
    (map fst (rawRequirements m)++[i | (i,_,_)<-rawScopedUses m])
  when (length (rawTemplates m)>64 || length (rawScopedUses m)>128)
    (at "SFLIMIT" path (rawModelId m) "at most 64 templates and 128 explicit uses")
  mapM_ (\t->relatedImport path (useSite t) (validateTemplate t)) (rawTemplates m)
  expanded<-traverse expand (rawScopedUses m)
  pure m {rawRequirements=rawRequirements m++expanded,rawScopedUses=[]}
 where
  local=[t | t<-rawTemplates m,rawTemplateLookup t==tokenText (rawTemplateName t)]
  types=Set.fromList (map tokenText (rawEntityTypes m))
  entities=Map.fromList [(tokenText i,tokenText t) | (i,t)<-rawEntities m]
  predicates=Map.fromList [(tokenText i,PredicateDecl (tokenText i) (map tokenText ts) PredicateRelationship) | (i,ts,_)<-rawPredicates m]
  hostSignatures=[(tokenText i,map tokenText ts,tokenText k) | (i,ts,k)<-rawPredicates m]
  useSite t=case [target | (_,target,_)<-rawScopedUses m,tokenText target==rawTemplateLookup t] of
    target:_->Just target
    []->Nothing
  validateTemplate t=do
    let origin=rawTemplateName t; formals=rawTemplateParameters t; body=rawTemplateBody t
        atDefinition=rawTemplatePath t
    identifierLength atDefinition origin
    unless ("q:" `Text.isPrefixOf` tokenText origin) (at "SFNAME" atDefinition origin "template identity requires q: prefix")
    when (null formals || length formals>4) (at "SFARITY" atDefinition origin "template needs 1..4 nominal formals")
    uniqueTokens atDefinition "SFDUPLICATE" "duplicate formal" (map fst formals)
    mapM_ (\(v,k)->do
      unless ("var:" `Text.isPrefixOf` tokenText v) (at "SFT006" atDefinition v "formal requires var: prefix")
      unless (Set.member (tokenText k) types) (at "SFT003" atDefinition k "unknown template nominal type")) formals
    closed origin atDefinition body
    mapM_ (\name->unless (any (\(i,as,k)->tokenText i==name
        && (tokenText i,map tokenText as,tokenText k) `elem` hostSignatures) (rawTemplateSignature t)) $ do
      let message="template predicate signature differs from authored definition: "<>name
      case [i | (i,_,_)<-rawTemplateSignature t,tokenText i==name] of
        []->at "SFSIGNATURE" atDefinition origin message
        authored:_->case [i | (i,_,_)<-rawPredicates m,tokenText i==name] of
          [i]->atRelated "SFSIGNATURE" (fst (predicateSource path m i)) i message atDefinition authored
          _->case useSite t of
            Just target->atRelated "SFSIGNATURE" path target message atDefinition authored
            Nothing->at "SFSIGNATURE" atDefinition authored message) (predicateNames body)
    validateExpression atDefinition origin types entities predicates Map.empty Map.empty
      (Set.fromList [tokenText v<>"@"<>tokenText k | (v,k)<-formals]) 0 body
  closed origin file e=case e of
    PredicateExpr _ ts->mapM_ (\term->case term of EntityTerm _->at "SFCAPTURE" file origin "template bodies cannot capture ground entities; declare a nominal formal"; _->Right ()) ts
    ReferenceExpr _->at "SFCAPTURE" file origin "ground requirement references/recursive templates are outside the closed template body; compose explicit uses in ordinary requirements"
    ComparisonExpr {}->at "SFCAPTURE" file origin "scalar captures are outside scoped requirement templates"
    _->mapM_ (closed origin file) (children e)
  expand (i,target,args)=do
    identifierLength path i
    unless ("q:" `Text.isPrefixOf` tokenText i) (at "SFNAME" path i "use identity requires q: prefix")
    t<-case filter ((==tokenText target) . rawTemplateLookup) (rawTemplates m) of
      [x]->Right x
      _->at "SFNAME" path target "unknown, private, wrong-kind or ambiguous requirement-template"
    let fs=rawTemplateParameters t
    unless (length fs==length args) (atRelated "SFARITY" path i "template argument count mismatch"
      (rawTemplatePath t) (rawTemplateName t))
    mapM_ (\((_,k),arg)->unless (Map.lookup (tokenText arg) entities==Just (tokenText k))
      (atRelated "SFT005" path arg "template argument is unknown or has wrong nominal type"
        (rawTemplatePath t) (rawTemplateName t))) (zip fs args)
    let bindings=Map.fromList [(tokenText f,tokenText a) | ((f,_),a)<-zip fs args]
    pure (i,substitute bindings (rawTemplateBody t))
  substitute bindings e=case e of
    PredicateExpr n ts->PredicateExpr n [case term of VariableTerm v->maybe term EntityTerm (Map.lookup v bindings); _->term | term<-ts]
    AllExpr xs->AllExpr (map (substitute bindings) xs)
    AnyExpr xs->AnyExpr (map (substitute bindings) xs)
    NotExpr x->NotExpr (substitute bindings x)
    ForallExpr v k x->ForallExpr v k (substitute (Map.delete v bindings) x)
    ExistsExpr v k x->ExistsExpr v k (substitute (Map.delete v bindings) x)
    CardinalityExpr k n xs->CardinalityExpr k n (map (substitute bindings) xs)
    _->e

children :: FiniteExpr -> [FiniteExpr]
children e=case e of
  AllExpr xs->xs; AnyExpr xs->xs; NotExpr x->[x]; ForallExpr _ _ x->[x]; ExistsExpr _ _ x->[x]; CardinalityExpr _ _ xs->xs; _->[]
predicateNames :: FiniteExpr -> [Text]
predicateNames e=case e of PredicateExpr n _->[n]; _->nub (concatMap predicateNames (children e))

scopedCompilation :: FilePath -> FilePath -> RawModel -> TypedFiniteScenario -> Either Diagnostic ScopedCompilation
scopedCompilation path scenarioPath m scenario=do
  _<-expandScopedModel path m
  let selected=[t | t<-rawTemplates m,any (\(_,target,_)->tokenText target==rawTemplateLookup t) (rawScopedUses m)]
      key t=[rawTemplateOwner t,maybe "local" id (rawTemplateVersion t),tokenText (rawTemplateName t),Text.pack (rawTemplatePath t)]
      expression e=case A.eitherDecodeStrict' (encodeJson (expressionJson e)) of Right x->x;Left _->A.Null
      definition t=ScopedDefinition (key t) (rawTemplatePath t) (rawTemplateDigest t)
        (tokenText (rawTemplateName t)) [(tokenText v,tokenText k) | (v,k)<-rawTemplateParameters t]
        (expression (rawTemplateBody t)) (tokenLine (rawTemplateName t)) (tokenColumn (rawTemplateName t))
      uses=[ScopedUse (tokenText i) (key t) [(tokenText v,tokenText a) | ((v,_),a)<-zip (rawTemplateParameters t) args]
        (normalise path) (tokenLine i) (tokenColumn i) (tokenText (scenarioIdentifier scenario)) (normalise scenarioPath)
        "explicit scenario selection; exact same-scope tuple classifications may be shared; independent selections require distinct selected components/scenarios"
        | (i,target,args)<-rawScopedUses m,t<-selected,rawTemplateLookup t==tokenText target]
  assessments<-traverse (\(predId,args,status,reason)->do
    value<-statusValue scenarioPath status
    pure (ScopedAssessment (tokenText predId) (map tokenText args)
      (A.object ["status" A..= truthName value,"reason" A..= tokenText reason]) (normalise scenarioPath) (tokenLine predId) (tokenColumn predId))) (scenarioFacts scenario)
  pure (ScopedCompilation (nub (map definition selected)) uses assessments)
