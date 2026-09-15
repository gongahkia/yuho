{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
module Yuho.Surface.Modules
  ( AuthoredModel(..), loadAuthoredModel, authoredPrefix
  , validateAuthoredChecked, validateAuthoredTargets ) where

import Control.Exception (IOException, try)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import System.FilePath (isAbsolute, takeDirectory, takeExtension, takeFileName, (</>))
import System.Posix.Files (fileSize, getSymbolicLinkStatus, isRegularFile)
import Yuho.Surface.AST hiding (Attachment)
import qualified Yuho.Surface.AST as AST
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Parser (parseModel)
import Yuho.Surface.Token

data AuthoredModel = AuthoredModel
  { authoredModel :: Model
  , authoredHost :: Maybe Text
  , authoredImports :: [(Text,Text,Text)]
  , authoredVisible :: [Text]
  } deriving (Eq, Show)

data Import = Import Token Token Token deriving (Eq, Show)
data ExportKind = ExportModel | ExportDefinition | ExportOffence
  | ExportException | ExportParticipation | ExportAttempt deriving (Eq, Ord, Show)
data Export = Export ExportKind Token deriving (Eq, Show)
data StatutoryModule = StatutoryModule Token Token [Import] [Export] Token deriving (Eq, Show)
data Use = Use ExportKind Token deriving (Eq, Show)
data Attachment = SimpleAttachment Token Token
  | ScopedAttachment Token ExportKind Token Token Token Token deriving (Eq, Show)
data Host = Host Token Token [Import] [Use] [Attachment] deriving (Eq, Show)

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
  [] -> at "SFM001" path (Token EndToken "" 1 1) "unexpected end of module source"

takeText :: Text -> P Token
takeText wanted = P $ \path input -> case input of
  token:rest | tokenText token == wanted -> Right (token,rest)
  token:_ -> at "SFM001" path token ("expected " <> wanted)
  [] -> at "SFM001" path (Token EndToken "" 1 1) ("expected " <> wanted)

takeKind :: Kind -> P Token
takeKind wanted = P $ \path input -> case input of
  token:rest | tokenKind token == wanted -> Right (token,rest)
  token:_ -> at "SFM001" path token "unexpected module token"
  [] -> at "SFM001" path (Token EndToken "" 1 1) "unexpected end of module source"

word :: P Token
word = takeKind WordToken

string :: P Token
string = takeKind StringToken

manyWhile :: Text -> P a -> P [a]
manyWhile wanted action = do
  next <- current
  if tokenText next == wanted then do
    item <- action
    (item :) <$> manyWhile wanted action
  else pure []

importDecl :: P Import
importDecl = do
  _ <- takeText "import"
  name <- word
  _ <- takeText "version"
  version <- word
  _ <- takeText "as"
  alias <- word
  _ <- takeText ";"
  pure (Import name version alias)

exportKind :: Token -> P ExportKind
exportKind token = case tokenText token of
  "model" -> pure ExportModel
  "definition" -> pure ExportDefinition
  "offence" -> pure ExportOffence
  "general-exception" -> pure ExportException
  "participation" -> pure ExportParticipation
  "attempt" -> pure ExportAttempt
  _ -> P $ \path _ -> at "SFM006" path token "unsupported module export kind"

exportDecl :: P Export
exportDecl = do
  _ <- takeText "export"
  kindToken <- word
  kindValue <- exportKind kindToken
  item <- word
  _ <- takeText ";"
  pure (Export kindValue item)

moduleParser :: P StatutoryModule
moduleParser = do
  _ <- takeText "statutory-module"
  name <- word
  _ <- takeText "version"
  version <- word
  _ <- takeText "{"
  imports <- manyWhile "import" importDecl
  exports <- manyWhile "export" exportDecl
  _ <- takeText "source-model"
  source <- string
  _ <- takeText ";"
  _ <- takeText "}"
  _ <- takeKind EndToken
  pure (StatutoryModule name version imports exports source)

useDecl :: P Use
useDecl = do
  _ <- takeText "use"
  kindToken <- word
  kindValue <- exportKind kindToken
  item <- word
  _ <- takeText ";"
  pure (Use kindValue item)

attachmentDecl :: P Attachment
attachmentDecl = do
  _ <- takeText "attach"
  exception <- word
  _ <- takeText "to"
  kindToken <- word
  targetKind <- exportKind kindToken
  target <- word
  next <- current
  if tokenText next == ";" then takeText ";" >> pure (SimpleAttachment exception target)
  else do
    _ <- takeText "for"
    role <- word
    _ <- takeText "context"
    context <- word
    _ <- takeText "as"
    instanceId <- word
    _ <- takeText ";"
    pure (ScopedAttachment exception targetKind target role context instanceId)

hostParser :: P Host
hostParser = do
  _ <- takeText "modular-model"
  item <- word
  _ <- takeText "{"
  _ <- takeText "module-root"
  root <- string
  _ <- takeText ";"
  imports <- manyWhile "import" importDecl
  uses <- manyWhile "use" useDecl
  attachments <- manyWhile "attach" attachmentDecl
  _ <- takeText "}"
  _ <- takeKind EndToken
  pure (Host item root imports uses attachments)

parseWith :: P a -> FilePath -> BS.ByteString -> Either Diagnostic a
parseWith parser path bytes = do
  tokens <- lexSource path bytes
  fst <$> runP parser path tokens

safeName :: Text -> Bool
safeName value = not (Text.null value) && Text.count "." value >= 1
  && Text.all (\c -> c `elem` (['a'..'z'] ++ ['0'..'9'] ++ ".-")) value

safeVersion :: Text -> Bool
safeVersion value = case Text.splitOn "." value of
  [a,b,c] -> all numeric [a,b,c]
  _ -> False
  where numeric part = not (Text.null part) && Text.all (`elem` ['0'..'9']) part

safeLocal :: Token -> Bool
safeLocal token = let value = Text.unpack (tokenText token) in
  not (null value) && not (isAbsolute value) && takeFileName value == value
    && takeExtension value == ".yh" && value /= "." && value /= ".."

readBounded :: FilePath -> FilePath -> Token -> IO (Either Diagnostic BS.ByteString)
readBounded path owner origin = do
  result <- try $ do
    status <- getSymbolicLinkStatus path
    if isRegularFile status && fileSize status <= 65536
      then BS.readFile path else ioError (userError "unsafe module file")
  pure $ case result of
    Left (_ :: IOException) -> Left (Diagnostic "SFM003" owner origin
      "module or source model unavailable, unsafe or too large" Nothing)
    Right bytes -> Right bytes

qualified :: FilePath -> Token -> Either Diagnostic (Text,Text)
qualified path token = case Text.splitOn "::" (tokenText token) of
  [alias,item] | not (Text.null alias) && not (Text.null item) -> Right (alias,item)
  _ -> at "SFM007" path token "typed module reference must be alias-qualified"

data Loaded = Loaded FilePath StatutoryModule Model

loadAuthoredModel :: FilePath -> BS.ByteString -> IO (Either Diagnostic AuthoredModel)
loadAuthoredModel path bytes = case lexSource path bytes of
  Right (first:_) | tokenText first == "modular-model" -> loadHost path bytes
  _ -> pure (AuthoredModel <$> parseModel path bytes <*> pure Nothing <*> pure []
    <*> pure [])

loadHost :: FilePath -> BS.ByteString -> IO (Either Diagnostic AuthoredModel)
loadHost path bytes = case parseWith hostParser path bytes of
  Left issue -> pure (Left issue)
  Right (Host hostId rootToken imports uses attachments) -> do
    let rootText = Text.unpack (tokenText rootToken)
        rootPath = takeDirectory path </> rootText
        rootSafe = not (null rootText) && not (isAbsolute rootText)
          && all (`notElem` ["",".."] ) (Text.splitOn "/" (tokenText rootToken))
    if not rootSafe then pure (at "SFM002" path rootToken "unsafe local module root")
    else do
      loaded <- loadImports path rootPath imports
      pure $ do
        modules <- loaded
        validateAliases path imports
        selectedRef <- case [item | Use ExportModel item <- uses] of
          [item] -> Right item
          [] -> at "SFM008" path hostId "modular host must explicitly use one exported model"
          _:second:_ -> at "SFM008" path second "modular host selects multiple models"
        selected <- resolveUse path modules ExportModel selectedRef
        let model = loadedModel selected
        mapM_ (validateUse path modules model) uses
        mapM_ (validateAttachment path modules model) attachments
        let records = [(tokenText name,tokenText version,tokenText alias)
              | Import name version alias <- imports]
            visible = [item | Use kindValue token <- uses, kindValue /= ExportModel,
              Right (_,item) <- [qualified path token]]
        Right (AuthoredModel model (Just (tokenText hostId)) records visible)

loadImports :: FilePath -> FilePath -> [Import] -> IO (Either Diagnostic (Map Text Loaded))
loadImports hostPath root imports = go Map.empty Set.empty Set.empty imports
  where
    go aliases _ _ [] = pure (Right aliases)
    go aliases identities active (item@(Import name _ alias):rest)
      | length identities >= 32 = pure (at "SFM004" hostPath name "module count limit exceeded")
      | Map.member (tokenText alias) aliases = pure (at "SFM005" hostPath alias "duplicate module alias")
      | Set.member (importIdentity item) identities = pure
          (at "SFM005" hostPath name "duplicate module identity")
      | otherwise = do
          result <- loadOne identities active item
          case result of
            Left issue -> pure (Left issue)
            Right (loaded,newIdentities) -> go (Map.insert (tokenText alias) loaded aliases)
              newIdentities active rest
    loadOne identities active (Import name version _) = do
      let identity = tokenText name <> "@" <> tokenText version
          file = root </> Text.unpack (tokenText name <> "@" <> tokenText version <> ".yh")
      if not (safeName (tokenText name) && safeVersion (tokenText version)) then
        pure (at "SFM002" hostPath name "invalid module name or exact version")
      else if Set.member identity active then
        pure (at "SFM005" hostPath name "module import cycle")
      else do
        sourceResult <- readBounded file hostPath name
        case sourceResult of
          Left issue -> pure (Left issue)
          Right source -> case parseWith moduleParser file source of
            Left issue -> pure (Left issue)
            Right declaration@(StatutoryModule actual actualVersion dependencies exports modelToken)
              | tokenText actual /= tokenText name || tokenText actualVersion /= tokenText version ->
                  pure (atRelated "SFM004" hostPath name "module identity or exact version mismatch"
                    file actual)
              | null exports -> pure (at "SFM006" file actual "module must explicitly export a symbol")
              | not (safeLocal modelToken) -> pure (at "SFM002" file modelToken "unsafe source-model reference")
              | length dependencies > 32 -> pure (at "SFM004" file actual "module dependency limit exceeded")
              | otherwise -> do
                  let aliases = [tokenText dependencyAlias
                        | Import _ _ dependencyAlias <- dependencies]
                      duplicateAlias = Set.size (Set.fromList aliases) /= length aliases
                  dependencyResult <- if duplicateAlias
                    then pure (at "SFM005" file actual "duplicate module dependency alias")
                    else loadDependencies file root (Set.insert identity active) dependencies
                  case dependencyResult of
                    Left issue -> pure (Left issue)
                    Right dependencyIds -> do
                      let modelPath = takeDirectory file </> Text.unpack (tokenText modelToken)
                      modelBytes <- readBounded modelPath file modelToken
                      pure $ do
                        raw <- modelBytes
                        model <- parseModel modelPath raw
                        validateExports file model exports
                        let ids = Set.insert identity (identities `Set.union` dependencyIds)
                        if Set.size ids > 32 then at "SFM004" hostPath name "module count limit exceeded"
                        else Right (Loaded file declaration model,ids)
    loadDependencies _ _ activeSet dependencies = goDependencies Set.empty dependencies
      where
        goDependencies seen [] = pure (Right seen)
        goDependencies seen (item@(Import name _ _):rest)
          | Set.member (importIdentity item) seen = pure
              (at "SFM005" hostPath name "duplicate module identity")
          | otherwise = do
              one <- loadOne seen activeSet item
              case one of
                Left issue -> pure (Left issue)
                Right (_,ids) -> goDependencies (Set.union seen ids) rest
    importIdentity (Import name version _) = tokenText name <> "@" <> tokenText version

validateAliases :: FilePath -> [Import] -> Either Diagnostic ()
validateAliases path = go Set.empty
  where
    go _ [] = Right ()
    go seen (Import _ _ alias:rest)
      | Set.member (tokenText alias) seen = at "SFM005" path alias "duplicate module alias"
      | otherwise = go (Set.insert (tokenText alias) seen) rest

loadedModel :: Loaded -> Model
loadedModel (Loaded _ _ model) = model

loadedExports :: Loaded -> [Export]
loadedExports (Loaded _ (StatutoryModule _ _ _ exports _) _) = exports

resolveUse :: FilePath -> Map Text Loaded -> ExportKind -> Token -> Either Diagnostic Loaded
resolveUse path modules wanted token = do
  (alias,item) <- qualified path token
  loaded <- maybe (at "SFM007" path token "unknown module alias") Right (Map.lookup alias modules)
  case [() | Export kindValue exported <- loadedExports loaded,
        kindValue == wanted, tokenText exported == item] of
    [()] -> Right loaded
    [] -> at "SFM006" path token "private, missing or wrong-kind module reference"
    _ -> at "SFM005" path token "ambiguous duplicate module export"

validateUse :: FilePath -> Map Text Loaded -> Model -> Use -> Either Diagnostic ()
validateUse path modules model (Use kindValue token) = do
  loaded <- resolveUse path modules kindValue token
  if modelIdentifier (loadedModel loaded) == modelIdentifier model then Right ()
  else at "SFM009" path token "used declarations do not share the selected authored model"

validateExports :: FilePath -> Model -> [Export] -> Either Diagnostic ()
validateExports path model exports = do
  let symbols = modelSymbols model
  case [token | Export kindValue token <- exports,
        Map.lookup (tokenText token) symbols /= Just kindValue] of
    token:_ -> at "SFM006" path token "export is private, missing or has the wrong declaration kind"
    [] -> Right ()
  let keys = [(kindValue,tokenText token) | Export kindValue token <- exports]
  if Set.size (Set.fromList keys) == length keys then Right ()
  else case exports of
    _:Export _ second:_ -> at "SFM005" path second "duplicate module export"
    _ -> at "SFM005" path (modelIdentifier model) "duplicate module export"

modelSymbols :: Model -> Map Text ExportKind
modelSymbols model = Map.fromList $ (tokenText (modelIdentifier model),ExportModel) : case modelBody model of
  DefinitionsLegal definitions _ offences exceptions _ _ ->
    [(tokenText (definitionId item),ExportDefinition) | item <- definitions]
    ++ [(tokenText (ruleIdentifier item),ExportOffence) | item <- offences]
    ++ [(tokenText (ruleIdentifier item),ExportException) | GeneralException item <- exceptions]
  MultiLegal _ offences exceptions _ _ ->
    [(tokenText (ruleIdentifier item),ExportOffence) | item <- offences]
    ++ [(tokenText (ruleIdentifier item),ExportException) | GeneralException item <- exceptions]
  ActorScopedLegal _ _ _ _ offence (IntentionalAidRoute participation _) attempt
    (ActorExceptionDefinition _ exception) _ _ _ -> actorSymbols offence participation attempt exception
  AbetmentLegal _ _ _ _ offence abetment attempt (ActorExceptionDefinition _ exception) _ _ _ ->
    actorSymbols offence (abetmentRule abetment) attempt exception
  _ -> []
  where
    actorSymbols offence participation attempt exception =
      [(tokenText (ruleIdentifier offence),ExportOffence)
      ,(tokenText (ruleIdentifier participation),ExportParticipation)
      ,(tokenText (ruleIdentifier (attemptRule attempt)),ExportAttempt)
      ,(tokenText (ruleIdentifier exception),ExportException)]

validateAttachment :: FilePath -> Map Text Loaded -> Model -> Attachment -> Either Diagnostic ()
validateAttachment path modules model declaration = case declaration of
  SimpleAttachment exception target -> do
    _ <- resolveUse path modules ExportException exception
    _ <- resolveUse path modules ExportOffence target
    (_,exceptionId) <- qualified path exception
    (_,targetId) <- qualified path target
    case modelBody model of
      DefinitionsLegal _ _ _ _ rows _ | any (matchesSimple exceptionId targetId) rows -> Right ()
      MultiLegal _ _ _ rows _ | any (matchesSimple exceptionId targetId) rows -> Right ()
      _ -> at "SFM010" path exception "imported exception attachment is absent or incompatible"
  ScopedAttachment exception targetKind target role context instanceId -> do
    _ <- resolveUse path modules ExportException exception
    _ <- resolveUse path modules targetKind target
    (_,exceptionId) <- qualified path exception
    (_,targetId) <- qualified path target
    case modelBody model of
      ActorScopedLegal _ _ _ _ _ _ _ _ rows _ _ | any (matchesScoped exceptionId targetId role context instanceId) rows -> Right ()
      AbetmentLegal _ _ _ _ _ _ _ _ rows _ _ | any (matchesScoped exceptionId targetId role context instanceId) rows -> Right ()
      _ -> at "SFM010" path exception "imported actor-scoped attachment is absent or incompatible"
  where
    matchesSimple exceptionId targetId (AST.Attachment _ exception target) =
      tokenText exception == exceptionId && tokenText target == targetId
    matchesScoped exceptionId targetId role context instanceId item =
      tokenText (attachmentDefinition item) == exceptionId
      && tokenText (attachmentTargetTokenLocal (attachmentTargetKind item)) == targetId
      && tokenText (attachmentSubjectRole item) == tokenText role
      && tokenText (contextTokenLocal (attachmentContext item)) == tokenText context
      && tokenText (attachmentInstanceId item) == tokenText instanceId

attachmentTargetTokenLocal :: AttachmentTargetKind -> Token
attachmentTargetTokenLocal kindValue = case kindValue of
  CandidateOffenceTarget item -> item
  ParticipationAttachmentTarget item -> item
  AttemptAttachmentTarget item -> item

contextTokenLocal :: ActContext -> Token
contextTokenLocal context = case context of
  PrincipalConductContext item -> item
  AidConductContext item -> item
  AttemptConductContext item -> item

authoredPrefix :: AuthoredModel -> Text
authoredPrefix authored = case authoredHost authored of
  Nothing -> ""
  Just host -> case authoredImports authored of
    [("effective-expression",expression,reason)] -> Text.unlines
      ["Temporal model: " <> host
      ,"Selected authored expression: " <> expression
      ,"Mechanical interval match: " <> reason
      ,"This selection applies authored assumptions; it is not a legal-currency determination."]
    imports -> Text.unlines
      (["Modular host: " <> host
       ,"Authored module versions select local model identity, not law by conduct date."
       ,"Resolved imports:"] ++
       ["  " <> name <> "@" <> version <> " as " <> alias
        | (name,version,alias) <- imports])

validateAuthoredChecked :: FilePath -> AuthoredModel -> Checked
  -> Either Diagnostic ()
validateAuthoredChecked path authored (Checked model scenario _ _ _) =
  validateAuthoredTargets path authored (selectedTargets model scenario)
  where
    selectedTargets _ Nothing = []
    selectedTargets _ (Just (Scenario _ _ _ _ targets)) = targets
    selectedTargets _ (Just (ActorScopedScenario _ _ targets _ _ _ _ _ _ _ _ _)) = targets
    selectedTargets selected (Just (ParticipationScenario _ _ _ _ _ _ _ _)) =
      case modelBody selected of
        ParticipationLegal _ _ _ _ _ _ (IntentionalAidRoute route _) _ _ ->
          [ruleIdentifier route]
        _ -> []
    selectedTargets selected (Just (AttemptScenario _ _ _ _ _ _ _ _ _)) =
      case modelBody selected of
        AttemptLegal _ _ _ _ attempt _ _ -> [ruleIdentifier (attemptRule attempt)]
        _ -> []

validateAuthoredTargets :: FilePath -> AuthoredModel -> [Token]
  -> Either Diagnostic ()
validateAuthoredTargets path authored targets = case authoredHost authored of
  Nothing -> Right ()
  Just _ | any (\(name,_,_) -> name == "effective-expression")
      (authoredImports authored) -> Right ()
  Just _ -> case [target | target <- targets,
      not (Set.member (tokenText target) visible)] of
    target:_ -> at "SFM006" path target
      "analysis target is private or was not explicitly composed by the modular host"
    [] -> Right ()
  where visible = Set.fromList (authoredVisible authored)
