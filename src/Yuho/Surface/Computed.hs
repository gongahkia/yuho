{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
-- | Bounded source-to-SDK adapter. All execution belongs to the existing SDK.
module Yuho.Surface.Computed
  ( SourceComposition, loadComposition, compositionDocument, compositionCheck
  , executeComposition, checkCompositionAttachment, compositionSourceMap
  ) where

import Control.Exception (IOException, try)
import Control.Monad (unless)
import qualified Data.Aeson as J
import qualified Data.ByteString as BS
import Data.List (find, nub)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import Data.Time.Calendar (Day)
import Data.Time.Format (defaultTimeLocale, parseTimeM)
import System.FilePath (isAbsolute, takeDirectory, takeFileName, takeExtension, (</>))
import System.Posix.Files (getSymbolicLinkStatus, isRegularFile, fileSize)
import qualified Yuho.Authoring as A
import qualified Yuho.CoreYuho.TypedFinite as K
import Yuho.Exception.Types (Truth(..))
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Surface.AST
import Yuho.Surface.Check (checkModel)
import Yuho.Surface.Computed.Parser
import Yuho.Surface.Lexer (lexSource)
import Yuho.Surface.Parser (parseModel, parseScenario)
import Yuho.Surface.Presumption (PresumptionSource(..), Registration(..), parsePresumptionSource)
import Yuho.Surface.Token
import Yuho.Surface.TypedFinite (prepareTypedFiniteInspection, parseTypedFiniteScenario, TypedFiniteScenario(..), typedDeclarationTokens)

data Blob = Blob FilePath BS.ByteString A.SourceRecord [Token]
data SourceComposition = SourceComposition FilePath Project A.ComputedInputDocument
compositionDocument :: SourceComposition -> A.ComputedInputDocument
compositionDocument (SourceComposition _ _ d) = d

ident :: Token -> Text
ident = tokenText
scope :: Selection -> A.Scope
scope s = A.Scope (ident (selectionActor s)) (ident (selectionContext s))
fresh :: Text -> [Text] -> Text
fresh category path = "yh:" <> category <> ":" <> sha256Text (A.encodeRecord path)
origin :: Token
origin = Token EndToken "" 1 1
sdk :: FilePath -> Token -> Either [A.AuthoringDiagnostic] a -> Either Diagnostic a
sdk p t = either failure Right
  where
    failure (x:_) = at (A.diagnosticCode x) p t
      (A.diagnosticMessage x <> "; " <> A.diagnosticLocation x <> "; objects: " <> T.intercalate ", " (A.diagnosticObjects x))
    failure [] = at "SFC009" p t "SDK operation returned an empty failure"
require :: Bool -> FilePath -> Token -> Text -> Either Diagnostic ()
require ok p t message = unless ok (at "SFC002" p t message)

readBlob :: FilePath -> Text -> Bool -> IO (Either Diagnostic Blob)
readBlob path role tokenize = do
  result <- try $ do
    status <- getSymbolicLinkStatus path
    if isRegularFile status && fileSize status <= 65536
      then BS.readFile path else ioError (userError "unsafe source")
  pure $ case result of
    Left (_ :: IOException) -> at "SFC005" path origin "source must be an available regular non-symlink file of at most 65536 bytes"
    Right bytes -> do
      text <- either (const (at "SFC005" path origin "source is not valid UTF-8")) Right (UTF8.decodeUtf8' bytes)
      tokens <- if tokenize then lexSource path bytes else Right []
      pure (Blob path bytes (A.SourceRecord ("yh-source:" <> role) (if tokenize then "other" else "case")
        (Just (T.pack (takeFileName path))) (Just text)) tokens)
localBlob :: FilePath -> Text -> Bool -> Token -> IO (Either Diagnostic Blob)
localBlob owner role tokenize token
  | isAbsolute name || takeFileName name /= name || name `elem` ["", ".", ".."]
    || (tokenize && takeExtension name `notElem` [".yh", ".yhs"]) =
      pure (at "SFC005" owner token "references must name sibling .yh/.yhs files (or sibling text for an assertion); traversal, imports and URLs are unsupported")
  | otherwise = readBlob (takeDirectory owner </> name) role tokenize
  where name = T.unpack (ident token)
blobRecord :: Blob -> A.SourceRecord
blobRecord (Blob _ _ r _) = r
blobPath :: Blob -> FilePath
blobPath (Blob p _ _ _) = p
blobBytes :: Blob -> BS.ByteString
blobBytes (Blob _ b _ _) = b
-- The old parser retains token starts, not ends. Anchor the exact containing
-- source line, explicitly not a fabricated token/operand extent.
lineRef :: Blob -> Token -> Either Diagnostic A.SourceRef
lineRef (Blob p bytes record _) t = sdk p t $ A.sourceAnchorBytes record (toInteger start) (toInteger end)
  where
    linesBefore = take (tokenLine t - 1) (BS.split 10 bytes)
    start = sum (map ((+1) . BS.length) linesBefore)
    end = start + BS.length (BS.takeWhile (/=10) (BS.drop start bytes))
wholeRef :: Blob -> Either Diagnostic A.SourceRef
wholeRef b = sdk (blobPath b) origin (A.sourceAnchorBytes (blobRecord b) 0 (toInteger (BS.length (blobBytes b))))
-- Use parser-retained declaration tokens, not repeated reference strings.
declaration :: Blob -> Text -> Text -> Either Diagnostic Token
declaration (Blob p bytes _ _) kind key = do
  entries <- if kind=="value"
    then map (\(t,_) -> ("value",t)) . scenarioValues <$> parseTypedFiniteScenario p bytes
    else typedDeclarationTokens p bytes
  case [t | (k,t) <- entries,k==kind,ident t==key] of
    [t] -> Right t
    _ -> at "SFC003" p origin ("missing or ambiguous " <> kind <> " declaration " <> key)

loadComposition :: FilePath -> IO (Either Diagnostic SourceComposition)
loadComposition path = do
  raw <- readBlob path "project" True
  case raw >>= \b -> (,) b <$> parseProject path (blobBytes b) of
    Left e -> pure (Left e)
    Right (projectBlob,p) -> do
      tm <- localBlob path "typed-model" True (sourceModel p)
      ts <- localBlob path "typed-scenario" True (sourceScenario p)
      dm <- localBlob path "destination-model" True (destinationModel p)
      cases <- mapM (\(AssertionSource key _ src) -> localBlob path ("assertion:" <> ident key) False src) (projectAssertions p)
      destination <- case dm of
        Left e -> pure (Left e)
        Right b -> loadDestination path p projectBlob b
      pure $ do
        source <- tm; scenario <- ts; caseBlobs <- sequence cases
        typed <- lowerTyped path p projectBlob source scenario caseBlobs
        dest <- destination
        compiled <- sdk path (selectionObject (sourceSelection p))
          (A.compileTypedAnalysis typed (ident (selectionId (sourceSelection p))))
        let snapshot = A.typedCompiledSnapshot compiled
            b = A.ComputedInputBinding (ident (bindingId p)) (A.typedDocumentId typed)
              (ident (selectionId (sourceSelection p))) (ident (selectionObject (sourceSelection p)))
              (scope (sourceSelection p)) (A.typedSnapshotId snapshot) (destinationIdentity dest)
              (ident (selectionId (destinationSelection p))) (ident (selectionObject (destinationSelection p)))
              (scope (destinationSelection p)) (A.computedDestinationDigest dest)
              (A.ComputedStatusPolicy (ident (bindingMapping p)) (ident (bindingUnresolved p)))
              (ident (bindingRationale p)) []
        bindingRef <- lineRef projectBlob (bindingId p)
        let doc = A.ComputedInputDocument A.computedInputFormat (ident (projectId p)) typed dest
              b { A.computedOriginalSources = [bindingRef] }
        sdk path (bindingId p) (case A.validateComputedInput doc of [] -> Right (); es -> Left es)
        pure (SourceComposition path p doc)
  where destinationIdentity dest = maybe (maybe "" A.documentId (A.destinationProof dest)) A.presumptionDocumentId (A.destinationPresumption dest)

-- Each invocation authorises fresh source evaluation. The public constructor
-- pins the actual emitted observation; the checked plan is not an observation.
executeComposition :: SourceComposition -> Either Diagnostic A.ComputedInputEvaluation
executeComposition (SourceComposition path p doc) = do
  source <- sdk path (sourceModel p) (A.compileTypedAnalysis (A.computedTypedSource doc)
    (A.computedSourceAnalysis (A.computedBinding doc)) >>= A.evaluateTypedAnalysis)
  let planned = A.computedBinding doc
  binding <- sdk path (bindingId p) $ A.makeComputedInputBinding (A.computedBindingId planned) source
    (A.computedSourceExpression planned) (A.computedDestination doc) (A.computedDestinationInput planned)
    (A.computedPolicy planned) (A.computedRationale planned) (A.computedOriginalSources planned)
  require (binding == planned) path (bindingId p) "evaluated binding differs from the checked source plan"
  sdk path (bindingId p) (A.executeComputedInputWith doc source)

checkCompositionAttachment :: SourceComposition -> A.ComputedInputDocument -> Either Diagnostic ()
checkCompositionAttachment (SourceComposition path p current) old =
  unless (old == current) (at "SFCSTALE" path (projectId p)
    "saved execution declaration differs from the current exact source plan; replay the frozen artifact alone or explicitly run the changed sources afresh")

compositionCheck :: SourceComposition -> J.Value
compositionCheck (SourceComposition _ _ doc) = J.object
  ["format" J..= ("yuho.source-composition-check/v0.1-experimental" :: Text)
  ,"status" J..= ("checked" :: Text),"evaluated" J..= False
  ,"binding" J..= A.computedBinding doc,"source_map" J..= compositionSourceMap doc]

compositionSourceMap :: A.ComputedInputDocument -> J.Value
compositionSourceMap doc = J.object
  ["format" J..= ("yuho.source-composition-map/v0.1-experimental" :: Text)
  ,"coordinates" J..= ("original .yh line anchors: zero-based half-open UTF-8 bytes; one-based byte columns. Not generated kernel spans or legislative quotation authentication." :: Text)
  ,"source" J..= component (A.typedOriginalSources typed)
      [(kind,A.typedId meta,A.typedSources meta) | (kind,meta) <- A.typedObjects typed]
  ,"destination" J..= either (const J.Null) (\base -> component (A.documentSources base)
      ([(A.nodeKind n,A.nodeId n,A.nodeSources n) | n <- A.lawNodes (A.documentLaw base)] ++
       [("supplied_assessment",A.assessmentId a,A.assessmentSources a) | a <- A.documentAssessments base])) (A.computedDestinationDocument (A.computedDestination doc))
  ,"authority" J..= ("fresh .yh run authorises current retained sources; artifact replay uses embedded sources only. No generated assessment is written to a source file." :: Text)]
  where
    typed = A.computedTypedSource doc
    component sources objects = J.object
      ["sources" J..= [J.object ["id" J..= A.sourceId s,"locator" J..= A.sourceLocator s
        ,"sha256" J..= fmap (sha256Text . UTF8.encodeUtf8) (A.sourceText s)] | s <- sources]
      ,"objects" J..= [J.object ["category" J..= kind,"id" J..= key,"original_line_anchors" J..= refs]
        | (kind,key,refs) <- objects]]

lowerTyped :: FilePath -> Project -> Blob -> Blob -> Blob -> [Blob] -> Either Diagnostic A.TypedDocument
lowerTyped path p projectBlob modelBlob scenarioBlob caseBlobs = do
  program <- prepareTypedFiniteInspection (blobPath modelBlob) (blobBytes modelBlob)
    (Just (blobPath scenarioBlob,blobBytes scenarioBlob))
  parsedScenario <- parseTypedFiniteScenario (blobPath scenarioBlob) (blobBytes scenarioBlob)
  let selected = sourceSelection p; target = ident (selectionObject selected)
      failAt = selectionObject selected
  require (null (K.finitePriorities program) && null (K.finiteModules program)
    && null (K.finiteNorms program) && null (K.finiteRoutes program)) path failAt
    "computed source supports no priorities, modules, norms or responsibility routes"
  (name,expression) <- case K.finiteRequirements program of
    [(key,e)] | key==target -> Right (key,e)
    _ -> at "SFC003" path failAt "source must name the single original requirement expression; rule/proposition observations and multiple named requirements are not admitted"
  rule <- case K.finiteRules program of
    [r] | K.ruleName r == ident (selectionRule selected), null (K.ruleParameters r)
      , K.rulePolarity r == K.Establish, K.ruleBody r == K.ReferenceExpr name
      , K.finitePropositions program == [K.ruleConclusion r] -> Right r
    _ -> at "SFC002" path (selectionRule selected) "expected one grounded establishing rule referring to the named requirement and one proposition; no erasure of extra rules/parameters"
  require (all ((==K.IntegerType) . K.scalarType) (K.finiteScalars program)) path failAt "only exact integer scalars are admitted"
  mapM_ (\predicate -> do
    token <- declaration modelBlob "predicate" (K.predicateName predicate)
    require (K.predicateKind predicate==K.PredicateRelationship) (blobPath modelBlob) token
      "only relationship-kind predicates are admitted; other source predicate categories are not reclassified by the SDK adapter")
    (K.finitePredicates program)
  require (ident (selectionActor selected) `elem` [key | K.EntityDecl key _ <- K.finiteEntities program]) path (selectionActor selected)
    "source actor must identify a retained concrete entity; actor/context scopes are explicitly authored, not inferred from tuple labels"
  expressionToken <- declaration modelBlob "requirement" name
  rootRef <- lineRef modelBlob expressionToken
  let labels = [(ident k,ident v) | (k,v) <- projectLabels p]
      meta key refs = A.TypedMeta key (maybe key id (lookup key labels)) Nothing refs
      plain key = meta key [rootRef]
      appId ground = fresh "application" [K.groundKey (A.tuplePredicate ground) (A.tupleArguments ground)]
      tuple fact = A.GroundTuple (K.groundPredicate fact) (K.groundArguments fact)
      factApp fact = appId (tuple fact)
      scopeValue = scope selected
      technical TrueValue _ = A.TechnicalTrue
      technical FalseValue _ = A.TechnicalFalse
      technical UnresolvedValue reason = A.TechnicalUnresolved reason
  (expressions,links,usedApps,usedScalars) <- lowerExpression (blobPath modelBlob) expressionToken plain appId name [] expression
  assessments <- mapM (\fact -> do
    token <- case [t | (t,args,_,_) <- scenarioFacts parsedScenario
      , ident t==K.groundPredicate fact, map ident args==K.groundArguments fact] of
      [t] -> Right t
      _ -> at "SFC003" (blobPath scenarioBlob) origin "ground tuple has no unique original classification declaration"
    ref <- lineRef scenarioBlob token
    let app = factApp fact; key=fresh "assessment" [app]
    pure (A.TypedAssessment (meta key [ref]) app (tuple fact) scopeValue
      (technical (K.groundStatus fact) (K.groundReason fact)) (K.groundReason fact)
      "Authored .yh scenario" "external_assertion" "assumption" [])) (K.finiteFacts program)
  values <- mapM (\(key,v) -> do
    token <- declaration scenarioBlob "value" key
    ref <- lineRef scenarioBlob token
    exact <- case v of
      K.IntegerValue n -> Right (A.ExactInteger n)
      K.ScalarUnresolved reason K.IntegerType -> Right (A.UnknownInteger "integer" reason)
      _ -> at "SFC002" (blobPath scenarioBlob) token "only exact integer values or explicitly unresolved integers are admitted"
    pure (A.TypedValue (meta (fresh "value" [key]) [ref]) key scopeValue exact
      "Explicit value in retained .yh scenario; no unit conversion inferred" "Authored .yh scenario")) (Map.toAscList (K.finiteValues program))
  assertions <- sequence [do
    require (ident expr==target && length usedApps==1 && case expression of K.PredicateExpr {} -> True; _ -> False)
      path expr "assertion support must explicitly name the single ground predicate expression, not a derived group or scalar"
    ref<-wholeRef blob
    pure (A.CaseAssertion (ident key) (maybe "" id (A.sourceText (blobRecord blob))) scopeValue [ref])
    | (AssertionSource key expr _,blob) <- zip (projectAssertions p) caseBlobs]
  let withAssertions a = a { A.typedAssertionRefs = [A.assertionId x | x <- assertions, A.assessedApplication a `elem` usedApps] }
      entityMeta kind key = do t<-declaration modelBlob kind key; ref<-lineRef modelBlob t; pure (meta key [ref])
  types <- mapM (\(K.EntityTypeDecl key) -> A.TypedEntityType <$> entityMeta "entity-type" key) (K.finiteEntityTypes program)
  entities <- mapM (\(K.EntityDecl key typ) -> (\m -> A.TypedEntity m typ) <$> entityMeta "entity" key) (K.finiteEntities program)
  predicates <- mapM (\x -> do
    m<-entityMeta "predicate" (K.predicateName x)
    pure (A.TypedPredicate m [A.TypedArgument ("argument-" <> T.pack (show i)) typ | (i,typ)<-zip [1::Int ..] (K.predicateArguments x)])) (K.finitePredicates program)
  scalars <- mapM (\x -> do
    m<-entityMeta "scalar" (K.scalarName x)
    pure (A.TypedScalar m "integer" (Just "Exact externally supplied integers; no physical-unit semantics"))) (K.finiteScalars program)
  ruleMeta <- entityMeta "rule" (K.ruleName rule)
  propMeta <- entityMeta "proposition" (K.ruleConclusion rule)
  let doc = A.TypedDocument A.typedAuthoringFormat (fresh "typed-document" [K.finiteProgramId program])
        (K.finiteProgramId program) "source-composition-v1" types entities predicates
        [A.TypedApplication (meta (A.assessedApplication a) (A.typedSources (A.typedAssessmentMeta a))) (A.assessedTuple a) | a <- assessments]
        scalars expressions (A.TypedLink (fresh "body" [K.ruleName rule]) (K.ruleName rule) name "typed_body":links)
        [A.TypedRule ruleMeta {A.typedCitation=K.ruleCitation rule} (K.ruleConclusion rule)] [A.TypedProposition propMeta]
        (map withAssertions assessments) values
        [A.TypedAnalysis (ident (selectionId selected)) (K.ruleName rule) (K.ruleConclusion rule) scopeValue
          [A.typedId (A.typedAssessmentMeta a) | a<-assessments,A.assessedApplication a `elem` usedApps]
          [A.typedId (A.valueMeta v) | v<-values,A.valueScalar v `elem` usedScalars]]
        (map blobRecord ([projectBlob,modelBlob,scenarioBlob]++caseBlobs)) assertions [] [] (K.finiteLimitations program)
  require (length labels==length (nub (map fst labels)) && all (\(key,_) -> key `elem` map (A.typedId . snd) (A.typedObjects doc)) labels)
    path (projectId p) "labels must refer uniquely to existing typed objects; equal labels do not identify equal actors"
  pure doc

lowerExpression :: FilePath -> Token -> (Text -> A.TypedMeta) -> (A.GroundTuple -> Text) -> Text -> [Text] -> K.FiniteExpr
  -> Either Diagnostic ([A.TypedExpression],[A.TypedLink],[Text],[Text])
lowerExpression path token meta appId root trail expression = case expression of
  K.PredicateExpr predicate args -> do
    arguments <- mapM (\t -> case t of K.EntityTerm x -> Right x; _ -> unsupported) args
    let app=appId (A.GroundTuple predicate arguments)
    pure ([A.TypedExpression (meta key) (A.GroundApplication app)],[],[app],[])
  K.ComparisonExpr op l r Nothing | op `elem` [K.GreaterThan,K.Equal] ->
    pure ([A.TypedExpression (meta key) (A.IntegerComparison (if op==K.GreaterThan then "gt" else "eq") l r)],[],[],[l,r])
  K.AllExpr children -> group A.TypedAll children
  K.AnyExpr children -> group A.TypedAny children
  _ -> unsupported
  where
    key = if null trail then root else fresh "expression" (root:trail)
    unsupported = at "SFC002" path token "computed composition admits ground predicates, integer gt/eq and finite all/any only; references, not, quantifiers, cardinality and other scalar operations are not erased"
    group form children = do
      nested <- sequence [lowerExpression path token meta appId root (trail++[T.pack (show i)]) e | (i,e)<-zip [0::Int ..] children]
      let childKeys=[A.typedId (A.expressionMeta x) | (x:_,_,_,_)<-nested]
      pure (A.TypedExpression (meta key) form:concat [ns | (ns,_,_,_)<-nested]
        ,[A.TypedLink (fresh "member" [key,c]) key c "typed_member" | c<-childKeys]++concat [es | (_,es,_,_)<-nested]
        ,nub (concat [as | (_,_,as,_)<-nested]),nub (concat [vs | (_,_,_,vs)<-nested]))

loadDestination :: FilePath -> Project -> Blob -> Blob -> IO (Either Diagnostic A.ComputedDestination)
loadDestination path p projectBlob source = case lexSource (blobPath source) (blobBytes source) of
  Left e -> pure (Left e)
  Right (first:_) | ident first=="presumption-program" -> case parsePresumptionSource (blobPath source) (blobBytes source) of
    Left e -> pure (Left e)
    Right registered -> do
      model <- localBlob (blobPath source) "proof-model" True (presumptionSourceModel registered)
      scenario <- localBlob (blobPath source) "proof-scenario" True (presumptionSourceScenario registered)
      pure $ do
        require (destinationScenario p==Nothing) path (destinationModel p)
          "presumption-program declares its own base-scenario; no destination-scenario override"
        m<-model; s<-scenario
        base<-lowerProof path p projectBlob m s [source]
        registrations<-mapM (registration base) (presumptionSourceRegistrations registered)
        let document = A.PresumptionDocument A.presumptionAuthoringFormat
              (ident (presumptionSourceName registered)) base registrations
              ["Original contextual burden/standard annotations are retained, not executed."
              ,ident (presumptionSourceBearer registered),ident (presumptionSourceStandard registered),ident (presumptionSourceNote registered)]
        require (not (null registrations) && length registrations<=16) (blobPath source) (presumptionSourceName registered)
          "source presumption programs require 1 to 16 registrations"
        pure (A.presumptionInputDestination document (ident (selectionId (destinationSelection p))))
  Right (first:_) | ident first/="model" -> pure (at "SFC002" (blobPath source) first
    "destination must be a Synthetic proof model or presumption-program; typed, temporal, case and other profile composition is unsupported")
  Right _ -> case destinationScenario p of
    Nothing -> pure (at "SFC002" path (destinationModel p) "proof destination requires an explicit separate destination-scenario")
    Just fileToken -> do
      scenario<-localBlob path "proof-scenario" True fileToken
      pure $ do
        s<-scenario
        base<-lowerProof path p projectBlob source s []
        pure (A.proofInputDestination base (ident (selectionId (destinationSelection p))))
  where
    registration base (Registration key target cited trigger rebuttal) = do
      require ("pres:" `T.isPrefixOf` ident key) (blobPath source) key "registration needs an explicit pres: identity"
      require (ident cited `elem` map A.sourceId (A.documentSources base)) (blobPath source) cited "unknown original presumption source"
      ref<-lineRef source key
      triggerRef<-lineRef source trigger
      rebuttalRef<-lineRef source rebuttal
      pure (A.AuthoredRegistration (ident key) (ident key) (ident target)
        [ident (selectionId (destinationSelection p))] [ref,A.SourceRef (ident cited) Nothing]
        (A.RegisteredCondition (fresh "trigger" [ident key]) "leaf_effective" (Just (ident trigger)) [] [triggerRef])
        (A.RegisteredCondition (fresh "rebuttal" [ident key]) "leaf_effective" (Just (ident rebuttal)) [] [rebuttalRef]))

lowerProof :: FilePath -> Project -> Blob -> Blob -> Blob -> [Blob] -> Either Diagnostic A.AuthoringDocument
lowerProof path p projectBlob modelBlob scenarioBlob extraSources = do
  model<-parseModel (blobPath modelBlob) (blobBytes modelBlob)
  require (null (modelCandidatePenalties model)) (blobPath modelBlob) (modelIdentifier model)
    "computed destination does not admit candidate penalties"
  (offence,exception)<-case modelBody model of
    Synthetic x y _ -> Right (x,y)
    _ -> at "SFC002" (blobPath modelBlob) (modelIdentifier model)
      "source composition currently admits the existing fictional Synthetic proof form only, optionally wrapped by presumption-program; no statutory families, linked/typed/temporal destinations"
  -- Existing structure checker is authoritative; absence of a scenario here is
  -- its ordinary draft path. Only the SDK binding may fill the one missing slot.
  Checked _ _ _ mainTree maybeGuard <- checkModel (blobPath modelBlob) model Nothing
  guardTree<-maybe (at "SFC002" (blobPath modelBlob) (modelIdentifier model) "expected synthetic exception tree") Right maybeGuard
  let selected=destinationSelection p
  require (ident (selectionRule selected)==ident (ruleIdentifier offence)) path (selectionRule selected)
    "destination analysis must select the authored offence identity"
  scenario<-parseScenario (blobPath scenarioBlob) (blobBytes scenarioBlob)
  entries<-case scenario of
    Scenario key owner values acknowledgements targets -> do
      require (ident key==ident (modelRequest model) && ident owner==ident (modelIdentifier model)) (blobPath scenarioBlob) owner "scenario/request model identity mismatch"
      require (null acknowledgements && null targets) (blobPath scenarioBlob) key "computed synthetic scenario does not admit analysis-target overrides or scope acknowledgements"
      pure values
    _ -> at "SFC002" (blobPath scenarioBlob) origin "only ordinary explicit proof classifications are admitted"
  mainNodes<-treeNodes mainTree
  guardNodes<-treeNodes guardTree
  mainRef<-lineRef modelBlob (ruleIdentifier offence)
  guardRef<-lineRef modelBlob (ruleIdentifier exception)
  assessments<-mapM assessment entries
  date<-maybe (at "SFC002" (blobPath modelBlob) (modelDate model) "invalid analysis reference date") Right
    (parseTimeM True defaultTimeLocale "%Y-%m-%d" (T.unpack (ident (modelDate model))) :: Maybe Day)
  let mainId=ident (ruleIdentifier offence);guardId=ident (ruleIdentifier exception)
      mainNode=A.LawNode mainId "rule" mainId Nothing (Just (ident (ruleId offence))) [mainRef]
      guardNode=A.LawNode guardId "rule" guardId Nothing (Just (ident (ruleId exception))) [guardRef]
      edge from to kind=A.LawEdge (fresh kind [from,to]) from to kind
      edges= [edge mainId (treeKey mainTree) "requires",edge mainId guardId "exception",edge guardId (treeKey guardTree) "requires"]
        ++treeEdges mainTree++treeEdges guardTree
      originals=[A.SourceRecord (ident i) (if ident k=="synthetic_status" then "synthetic" else "other") (Just (ident loc)) Nothing | SourceDecl i k loc<-modelSources model]
      BurdenAnnotation a b c d=modelBurden model
      context=A.Annotation (fresh "context" [ident (modelIdentifier model)]) [mainId,guardId]
        ("Retained contextual annotation only: " <> T.intercalate " " (map ident [a,b,c,d])) "retained"
  pure (A.AuthoringDocument A.authoringFormat (fresh "proof-document" [ident (modelIdentifier model)])
    (A.LawDefinition (ident (modelIdentifier model)) "source-composition-v1" (mainNode:guardNode:mainNodes++guardNodes)
      edges (map ident (modelLimitations model)))
    (map blobRecord ([projectBlob,modelBlob,scenarioBlob]++extraSources)++originals) [] assessments
    [A.Analysis (ident (selectionId selected)) mainId (scope selected) (map A.assessmentId assessments) date] [] [context] [])
  where
    treeKey (ResolvedLeaf t _)=ident t
    treeKey (ResolvedGroup t _ _)=ident t
    treeEdges (ResolvedLeaf _ _)=[]
    treeEdges (ResolvedGroup t _ children)=
      [A.LawEdge (fresh "member" [ident t,treeKey c]) (ident t) (treeKey c) "member" | c<-children]++concatMap treeEdges children
    treeNodes tree=case tree of
      ResolvedLeaf t quote -> do
        model<-parseModel (blobPath modelBlob) (blobBytes modelBlob)
        text<-maybe (at "SFC003" (blobPath modelBlob) quote "original quote missing") Right (lookupByText quote (modelQuotes model))
        ref<-lineRef modelBlob t; quoteRef<-lineRef modelBlob text
        pure [A.LawNode (ident t) "input" (ident text) (Just (ident text)) Nothing [ref,quoteRef]]
      ResolvedGroup t comb children -> do
        ref<-lineRef modelBlob t; nested<-concat <$> mapM treeNodes children
        pure (A.LawNode (ident t) (if comb==All then "all" else "any") (ident t) Nothing Nothing [ref]:nested)
    lookupByText key rows = snd <$> find ((==ident key) . ident . fst) rows
    assessment (Assignment key status reason) = do
      classification<-case (ident status,ident <$> reason) of
        ("proved",Nothing)->Right A.Proved
        ("not_proved",Nothing)->Right A.NotProved
        ("unresolved",Just "not_determined")->Right (A.Unresolved A.NotDetermined)
        ("unresolved",Just "external_decision_pending")->Right (A.Unresolved A.ExternalDecisionPending)
        _ -> at "SFE010" (blobPath scenarioBlob) status "invalid explicit proof classification or unresolved reason"
      ref<-lineRef scenarioBlob key
      pure (A.Assessment (fresh "direct-assessment" [ident key]) (ident key) (scope (destinationSelection p))
        (A.Classification classification) "Explicit classification in retained .yh scenario; no evidence interpretation"
        "Authored .yh scenario" "external_assertion" "assumption" [] [ref])
