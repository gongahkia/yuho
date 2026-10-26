{-# LANGUAGE OverloadedStrings #-}
-- | Non-evaluating, closed-capability checking. CheckedPlan is opaque in the
-- public facade; only this module constructs its resolved component table.
module Yuho.Dependency.Check where

import Control.Monad (unless)
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as BL
import System.FilePath (normalise)
import Data.List (sort)
import qualified Data.Map.Strict as M
import qualified Data.Set as S
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as U
import Yuho.ScopedDefinitions.Types
import Yuho.Dependency.Types
import qualified Yuho.CoreYuho.TypedFinite as K
import qualified Yuho.Core.Types as C
import Yuho.Core.Source (validSourcePath, validateSpan)
import Yuho.Exception.Types (Truth(..))
import Yuho.Protocol.Decode (sha256Text)
import qualified Yuho.Protocol.Json as J
import Yuho.Surface.Dependency.Parser (parseDependencyProject)
import Yuho.Surface.TypedFinite (prepareDependencyTypedScoped, expandedNodeEstimate, encodeTypedFiniteRequest)
import qualified Yuho.Surface.Token as ST
import qualified Yuho.Authoring.Typed as SDK
import qualified Yuho.Authoring.Types as SDK
import Yuho.TypedFiniteRules.Run (decodeTypedFiniteRequest)
import Yuho.PenaltyTerms.Validate (validateCandidateTerm)

encode :: A.ToJSON a => a -> BS.ByteString
encode=BL.toStrict . A.encode
hash :: A.ToJSON a => a -> Text
hash=sha256Text . encode
failure :: Text -> [Text] -> Text -> Either DependencyDiagnostic a
failure code objects message=Left (DependencyDiagnostic code message objects Nothing [])
ensure :: Text -> [Text] -> Text -> Bool -> Either DependencyDiagnostic ()
ensure code objects message ok=unless ok (failure code objects message)
unique :: Text -> [Text] -> Either DependencyDiagnostic ()
unique label xs=ensure "DEPNAME" xs ("duplicate "<>label) (length xs==S.size (S.fromList xs))
nonblank :: Text -> Bool
nonblank=not . T.null . T.strip
valueTruth :: TechnicalValue -> Truth
valueTruth Satisfied=TrueValue
valueTruth NotSatisfied=FalseValue
valueTruth Unresolved=UnresolvedValue
truthValue :: Truth -> TechnicalValue
truthValue TrueValue=Satisfied
truthValue FalseValue=NotSatisfied
truthValue UnresolvedValue=Unresolved

-- Explicit structural identities, separate from exact-byte fingerprints.
data CheckedComponent = CheckedComponent
  { checkedComponent :: PlanComponent, checkedProgram :: K.TypedFiniteProgram
  , checkedSlots :: [(Text,Text)], checkedScope :: PlanScope
  , checkedLocalScope :: Maybe SDK.Scope, checkedMappings :: A.Value
  , checkedScopedDefinitions :: ScopedCompilation, checkedTemplateDigest :: Text } deriving (Eq,Show)
data CheckedPlan = CheckedPlan { checkedDocument :: DependencyDocument
  , checkedComponents :: M.Map Text CheckedComponent, checkedOrder :: [Text]
  , checkedCost :: Integer, checkedDigest :: Text } deriving (Eq,Show)

checkDependencyPlan :: DependencyDocument -> Either DependencyDiagnostic CheckedPlan
checkDependencyPlan doc = do
  ensure "DEPFORMAT" [] "expected the closed dependency-plan v0.1 format" (dependencyFormat doc==planFormat)
  let p=dependencyPlan doc; cs=planComponents p; bs=planBindings p; candidates=planCandidates p
      scopes=planScopes p; origins=planOrigins p
      sources=M.map U.encodeUtf8 (dependencySources doc)
  ensure "DEPLIMIT" [] "plan bounds: 1..16 components, <=64 bindings, <=32 candidates/scopes, <=4 MiB retained input"
    (not (null cs) && length cs<=16 && length bs<=64 && length candidates<=32 && length scopes<=32
      && sum (map BS.length (M.elems sources))<=4194304 && BS.length (encode doc)<=8388608)
  mapM_ (\(label,ids)->unique label ids)
    [("component",map componentIdentity cs),("scope",map scopeIdentity scopes)
    ,("binding",map bindingIdentity bs),("candidate",map candidateIdentity candidates)
    ,("origin",map originIdentity origins)]
  let ids=planIdentity p:map componentIdentity cs++map scopeIdentity scopes++map bindingIdentity bs++map candidateIdentity candidates
  ensure "DEPLIMIT" ids "identities must be nonempty and <=256 Unicode code points" (all (\x->nonblank x && T.length x<=256) ids)
  mapM_ (\path->ensure "DEPFORMAT" [] "unsafe retained virtual path" (validSourcePath (T.pack path))) (M.keys sources)
  mapM_ (\o->ensure "DEPRATIONALE" [originIdentity o] "origin needs a nonblank locator" (nonblank (originLocator o))) origins
  mapM_ checkScope scopes
  case dependencyProjectSource doc of
    Nothing->pure () -- In-memory SDK authoring: the typed records are authored authority.
    Just path->do
      source<-maybe (failure "DEPMISSING" [] "original checked-project source is missing") Right (M.lookup path sources)
      authored<-either (Left . surfaceFailureIn (dependencySources doc)) Right (parseDependencyProject path source)
      ensure "DEPSTALE" [] "plan declarations no longer correspond to the retained authored checked-project source" (authored==p)
  resolved<-traverse (checkComponent doc) cs
  let table=M.fromList [(componentIdentity (checkedComponent c),c) | c<-resolved]
      component key=maybe (failure "DEPNAME" [key] "unknown component") Right (M.lookup key table)
      refs rationale rs=do
        ensure "DEPRATIONALE" rs "nonblank authorisation rationale and valid origin references required"
          (nonblank rationale && not (null rs) && all (`elem` map originIdentity origins) rs)
      port ref=component (portComponent ref) >>= \c->checkPort c ref >> pure c
  mapM_ (\b->do
    s<-port (bindingPort b); d<-component (bindingComponent b)
    ensure "DEPNAME" [bindingIdentity b,bindingSlot b] "unknown destination condition slot" (bindingSlot b `elem` map fst (checkedSlots d))
    ensure "DEPSCOPE" [bindingIdentity b] "source and destination scopes/occurrences must be identical" (checkedScope s==checkedScope d)
    checkPolicy (bindingPort b) (bindingPolicy b)
    refs (bindingRationale b) (bindingReferences b)) bs
  unique "binding/candidate effect identity" (map bindingIdentity bs++map candidateIdentity candidates)
  let destinations=[componentObjectKey (planIdentity p) c "technical.condition.slot" (bindingSlot b) | b<-bs,Just c<-[M.lookup (bindingComponent b) table]]
  ensure "DEPWRITER" destinations "a fully qualified slot has more than one writer (equal values are still conflicting writers)"
    (length destinations==S.size (S.fromList destinations))
  mapM_ (\c->mapM_ (\(slot,_)->ensure "DEPMISSING" [componentIdentity (checkedComponent c),slot]
    "every condition hole requires exactly one writer" (length [b | b<-bs,bindingComponent b==componentIdentity (checkedComponent c),bindingSlot b==slot]==1)) (checkedSlots c)) resolved
  mapM_ (\c->do
    source<-port (candidateGuard c)
    ensure "DEPSCOPE" [candidateIdentity c] "candidate guard belongs to a different scope/allegation/occurrence"
      (candidateScope c==scopeIdentity (checkedScope source))
    checkPolicy (candidateGuard c) (candidatePolicy c)
    refs (candidateRationale c) (candidateReferences c)
    ensure "DEPUNSUPPORTED" [candidateIdentity c] "modality must be may, shall or unspecified; no sentence selection" (candidateModality c `elem` ["may","shall","unspecified"])
    validateCandidate doc c) candidates
  order<-topologicalOrder (map componentIdentity cs) [(portComponent (bindingPort b),bindingComponent b,bindingIdentity b) | b<-bs]
  checkOrderCertificate order [(portComponent (bindingPort b),bindingComponent b) | b<-bs]
  costs<-traverse (\c->either (failure "DEPLIMIT" [componentIdentity (checkedComponent c)]) Right (expandedNodeEstimate (checkedProgram c))) resolved
  let total=sum costs+toInteger (length bs*8)+sum [termNodes (termValue (candidateTerm c)) | c<-candidates]
  ensure "DEPLIMIT" [] "expanded component/term/ledger cost exceeds 16384" (total<=16384)
  pure (CheckedPlan doc table order total (hash doc))

checkScope :: PlanScope -> Either DependencyDiagnostic ()
checkScope s=do
  unique "project entity identity" (map fst (scopeEntities s))
  ensure "DEPSCOPE" [scopeIdentity s] "actor and context must name explicit project entities"
    (scopeActor s `elem` map fst (scopeEntities s) && scopeContext s `elem` map fst (scopeEntities s))
  ensure "DEPSCOPE" [scopeIdentity s] "case and allegation must be jointly specified" ((scopeCase s==Nothing)==(scopeAllegation s==Nothing))
  ensure "DEPSCOPE" [scopeIdentity s] "empty nominal/entity scope identity" (all (\(a,b)->nonblank a && nonblank b) (scopeEntities s))

checkComponent :: DependencyDocument -> PlanComponent -> Either DependencyDiagnostic CheckedComponent
checkComponent doc c=withLocation (componentLocation c) $ do
  scope<-case [s | s<-planScopes (dependencyPlan doc),scopeIdentity s==componentScope c] of
    [s]->Right s; _->failure "DEPSCOPE" [componentIdentity c] "unknown component scope"
  ensure "DEPRATIONALE" [componentIdentity c] "component identity mapping requires an authorisation rationale" (nonblank (componentRationale c))
  (program,slots,localScope,mappings,actualCase,scoped)<-case (componentProfile c,componentTemplate c) of
    ("native-typed",Nothing)->do
      ensure "DEPFORMAT" [componentIdentity c] "native model entry is implicit or a selected allegation" (maybe True ((=="allegation") . fst) (componentEntry c))
      (p,holes,occ,scopedCompilationInfo)<-either (Left . surfaceFailureIn (dependencySources doc)) Right (prepareDependencyTypedScoped (M.map U.encodeUtf8 (dependencySources doc))
        (componentModel c) (componentScenario c) (snd <$> componentEntry c))
      pure (p,holes,Nothing,A.Null,occ,scopedCompilationInfo)
    ("native-typed",Just t)->do
      ensure "DEPFORMAT" [componentIdentity c] "in-memory technical template has no file/scenario/entry selector"
        (null (componentModel c) && componentScenario c==Nothing && componentEntry c==Nothing)
      (p,holes)<-compileTemplate t
      pure (p,holes,Nothing,A.Null,Nothing,emptyScopedCompilation)
    ("sdk-typed-v0.3",Nothing)->do
      text<-maybe (failure "DEPMISSING" [componentIdentity c] "SDK document absent from exact source bundle") Right (M.lookup (componentModel c) (dependencySources doc))
      d<-either (failure "DEPFORMAT" [componentIdentity c] . SDK.diagnosticMessage) Right (SDK.decodeTypedDocument (U.encodeUtf8 text))
      entry<-case componentEntry c of Just ("analysis",i)->Right i; _->failure "DEPNAME" [componentIdentity c] "SDK component requires actual analysis entry"
      compiled<-either (failure "DEPFORMAT" [componentIdentity c] . T.intercalate "; " . map SDK.diagnosticMessage) Right (SDK.compileTypedAnalysis d entry)
      wire<-either (failure "DEPFORMAT" [componentIdentity c]) Right (J.decodeJson (SDK.typedCompiledRequest compiled))
      p<-either (failure "DEPFORMAT" [componentIdentity c]) Right (decodeTypedFiniteRequest wire)
      let local=SDK.typedAnalysisScope (SDK.typedSnapshotAnalysis (SDK.typedCompiledSnapshot compiled))
      ensure "DEPSCOPE" [componentIdentity c] "actual selected SDK actor/context must map to the project actor/context"
        (lookup (SDK.scopeActor local) (componentEntities c)==Just (scopeActor scope))
      -- SDK contexts are real Scope identifiers, often not entity declarations.
      -- The explicit analysis entry + project scope + rationale authorises this
      -- context correspondence; retain both exact records, never invent an entity.
      pure (p,[],Just local,A.object ["kernel_mappings" A..= SDK.typedCompiledMappings compiled
        ,"selected_analysis" A..= entry,"local_scope" A..= local,"project_scope" A..= scope
        ,"context_correspondence" A..= (SDK.scopeContext local,scopeContext scope)
        ,"authority" A..= componentRationale c],Nothing,emptyScopedCompilation)
    _->failure "DEPUNSUPPORTED" [componentIdentity c] "unsupported component profile or template; no implicit adapter"
  case actualCase of
    Just (caseId,allegation)->ensure "DEPSCOPE" [componentIdentity c] "actual case/allegation selector differs from declared scope"
      (scopeCase scope==Just caseId && scopeAllegation scope==Just allegation)
    Nothing->pure ()
  -- Both template lowerers introduce these private helpers only for actual
  -- condition slots, after rejecting authored collisions. Without slots the
  -- same spellings are ordinary authored identities (including SDK producers).
  let types=[x | K.EntityTypeDecl x<-K.finiteEntityTypes program,null slots || x/="dep_template_type"]
      entities=[(x,t) | K.EntityDecl x t<-K.finiteEntities program,null slots || x/="dep_template_entity"]
  unique "local nominal map" (map fst (componentNominals c))
  unique "local entity map" (map fst (componentEntities c))
  unique "project entity map (injectivity required)" (map snd (componentEntities c))
  mapM_ (\(local,project)->ensure "DEPSCOPE" [componentIdentity c,local,project]
    "nominal map must name an actual local type and a declared project type" (local `elem` types && project `elem` map snd (scopeEntities scope))) (componentNominals c)
  mapM_ (\(local,project)->do
    t<-maybe (failure "DEPSCOPE" [local] "unknown local entity in identity map") Right (lookup local entities)
    ensure "DEPSCOPE" [componentIdentity c,local,project] "identity map nominal correspondence is missing or incompatible"
      (lookup t (componentNominals c)==lookup project (scopeEntities scope) && lookup project (scopeEntities scope)/=Nothing)) (componentEntities c)
  ensure "DEPSCOPE" [componentIdentity c] "actual local entities for project actor and context must be mapped explicitly"
    (all (`elem` map snd (componentEntities c)) (scopeActor scope:[scopeContext scope | localScope==Nothing]))
  -- The protocol validator independently checks every lowered operator/type/limit.
  wire<-either (failure "DEPFORMAT" [componentIdentity c]) Right (J.decodeJson (encodeTypedFiniteRequest "DEPENDENCY-CHECK" program))
  _<-either (failure "DEPFORMAT" [componentIdentity c]) Right (decodeTypedFiniteRequest wire)
  either (failure "DEPMISSING" [componentIdentity c]) Right (K.checkTypedFiniteInputs program)
  pure (CheckedComponent c program slots scope localScope mappings scoped (hash (doc,c,scope,localScope)))

surfaceFailure :: ST.Diagnostic -> DependencyDiagnostic
surfaceFailure=surfaceFailureIn M.empty
surfaceFailureIn :: M.Map FilePath Text -> ST.Diagnostic -> DependencyDiagnostic
surfaceFailureIn sources d=DependencyDiagnostic (ST.diagnosticCode d)
  (ST.diagnosticMessage d<>" ["<>T.pack (ST.diagnosticPath d)<>":"<>T.pack (show (ST.tokenLine (ST.diagnosticToken d)))
    <>":"<>T.pack (show (ST.tokenColumn (ST.diagnosticToken d)))<>"]") []
  (located (ST.diagnosticPath d) (ST.diagnosticToken d))
  (maybe [] (\(p,t)->maybe [] (:[]) (located p t)) (ST.diagnosticRelated d))
 where
  located path token=do
    text<-M.lookup (normalise path) sources
    let bytes=U.encodeUtf8 text
        offset=sum [BS.length line+1 | line<-take (ST.tokenLine token-1) (BS.split 10 bytes)]+ST.tokenColumn token-1
        width=BS.length (U.encodeUtf8 (ST.tokenText token))+(if ST.tokenKind token==ST.StringToken then 2 else 0)
    if offset<0 || offset+width>BS.length bytes then Nothing else
      Just (Location (normalise path) (ST.tokenLine token) (ST.tokenColumn token) offset (offset+width))

withLocation :: Maybe Location -> Either DependencyDiagnostic a -> Either DependencyDiagnostic a
withLocation loc= either (\e->Left e {dependencyLocation=case dependencyLocation e of Nothing->loc; x->x}) Right

checkPort :: CheckedComponent -> ObservationPort -> Either DependencyDiagnostic ()
checkPort c p=do
  let program=checkedProgram c
  case portCategory p of
    "typed.expression.truth"->ensure "DEPNAME" [portObject p] "unknown named expression port" (portObject p `elem` map fst (K.finiteRequirements program))
    "typed.proposition.resolution"->do
      ensure "DEPNAME" [portObject p] "unknown resolved proposition port" (portObject p `elem` K.finitePropositions program)
      ensure "DEPSCOPE" [portObject p] "uninstantiated parameter-aggregated proposition is not an actor-local port"
        (all (null . K.ruleParameters) [r | r<-K.finiteRules program,K.ruleConclusion r==portObject p])
    _->failure "DEPCATEGORY" [portObject p,portCategory p] "unsupported observation category; no rule-body/proof/scalar coercion"

checkPolicy :: ObservationPort -> Text -> Either DependencyDiagnostic ()
checkPolicy p policy=ensure "DEPPOLICY" [portObject p,policy] "explicit policy does not match the source category/technical-condition destination"
  ((portCategory p,policy) `elem` [("typed.expression.truth","yuho.condition-identity/v1"),("typed.proposition.resolution","yuho.proposition-support/v1")])

topologicalOrder :: [Text] -> [(Text,Text,Text)] -> Either DependencyDiagnostic [Text]
topologicalOrder nodes edges=go [] (sort nodes)
  where
    go done []=Right done
    go done pending=case [n | n<-pending,all (\(s,d,_)->d/=n || s `elem` done) edges] of
      []->failure "DEPCYCLE" [i | (s,d,i)<-edges,s `elem` pending,d `elem` pending] "dependency cycle/self-dependency; all involved bindings are listed"
      n:_->go (done++[n]) (filter (/=n) pending)

validateCandidate :: DependencyDocument -> PlanCandidate -> Either DependencyDiagnostic ()
validateCandidate doc c=do
  let (path,text)=case candidateLocation c of
        Just l->(locationPath l,M.findWithDefault "" (locationPath l) (dependencySources doc))
        Nothing->("sdk-candidate", "")
      bytes=U.encodeUtf8 text; endLine=1+BS.count 10 bytes
      endColumn=1+BS.length (BS.takeWhileEnd (/=10) bytes)
      outer=C.Span 0 (BS.length bytes) 1 1 endLine endColumn
      source=C.Source (T.pack path) text bytes (sha256Text bytes)
  wire<-either (failure "DEPFORMAT" [candidateIdentity c]) Right (J.decodeJson (encode (termValue (candidateTerm c))))
  _<-either (\d->failure "DEPUNSUPPORTED" [candidateIdentity c] (C.diagCode d<>" "<>T.pack (show (C.diagParameters d)))) Right (validateCandidateTerm source outer wire)
  case candidateLocation c of
    Nothing->pure ()
    Just loc->ensure "DEPFORMAT" [candidateIdentity c] "invalid authored candidate source location"
      (validateSpan source (C.Span (locationStart loc) (locationEnd loc) (locationLine loc) (locationColumn loc)
        (locationLine loc) (locationColumn loc+locationEnd loc-locationStart loc)))
  pure ()

termNodes :: A.Value -> Integer
termNodes (A.Object fields)=1+sum (map termNodes (foldr (:) [] fields))
termNodes (A.Array xs)=sum (map termNodes (foldr (:) [] xs))
termNodes _=0

compileTemplate :: TechnicalTemplate -> Either DependencyDiagnostic (K.TypedFiniteProgram,[(Text,Text)])
compileTemplate t=do
  unique "template condition" (templateConditions t)
  let slots=[(i,"dep_"<>sha256Text (U.encodeUtf8 i)) | i<-templateConditions t]
      generated=[n | not (null slots),n<-["dep_template_type","dep_template_entity"]]++map snd slots
  ensure "DEPWRITER" generated "authored template identities conflict with reserved lowering objects"
    (not (any (`elem` generated) (templateEntityTypes t++map fst (templateEntities t)++map fst (templatePredicates t))))
  let expr e=case e of
        TemplateAtom n args->Right (K.PredicateExpr n (map K.EntityTerm args))
        TemplateCondition i->maybe (failure "DEPNAME" [i] "unknown template condition")
          (\n->Right (K.PredicateExpr n [K.EntityTerm "dep_template_entity"])) (lookup i slots)
        TemplateAll xs->K.AllExpr <$> traverse expr xs; TemplateAny xs->K.AnyExpr <$> traverse expr xs
        TemplateNot x->K.NotExpr <$> expr x; TemplateReference i->Right (K.ReferenceExpr i)
  requirements<-traverse (\(i,e)->(,) i <$> expr e) (templateRequirements t)
  let program=K.TypedFiniteProgram (templateIdentity t)
        (map K.EntityTypeDecl (templateEntityTypes t++["dep_template_type" | not (null slots)]))
        ([K.EntityDecl i ty | (i,ty)<-templateEntities t]++[K.EntityDecl "dep_template_entity" "dep_template_type" | not (null slots)])
        ([K.PredicateDecl i args K.PredicateRelationship | (i,args)<-templatePredicates t]++[K.PredicateDecl n ["dep_template_type"] K.PredicateCircumstance | (_,n)<-slots])
        [] (templatePropositions t) requirements
        [K.RuleDecl r [] K.Establish p (K.ReferenceExpr q) Nothing | (r,p,q)<-templateRules t] [] [] []
        ([K.GroundFact n args (valueTruth v) reason | (n,args,v,reason)<-templateFacts t]
          ++[K.GroundFact n ["dep_template_entity"] UnresolvedValue "structural binding placeholder; not an observation" | (_,n)<-slots])
        M.empty [] (templateLimitations t)
  ensure "DEPWRITER" [] "template condition cannot have a direct fact"
    (all (\(n,_,_,_)->n `notElem` (map fst slots++map snd slots)) (templateFacts t))
  pure (program,slots)


-- Independent finite rank-certificate check after scheduling; corresponds to
-- ordered/acyclic in the additive Lean model, without trusting edge traversal.
checkOrderCertificate :: [Text] -> [(Text,Text)] -> Either DependencyDiagnostic ()
checkOrderCertificate order edges=do
  unique "scheduled component" order
  let ranks=M.fromList (zip order [0::Int ..])
  mapM_ (\(a,b)->ensure "DEPCYCLE" [a,b] "invalid topological rank certificate"
    (case (M.lookup a ranks,M.lookup b ranks) of (Just x,Just y)->x<y;_->False)) edges


scopeKey :: PlanScope -> [Text]
scopeKey s=[scopeIdentity s,scopeActor s,scopeContext s,maybe "" id (scopeCase s),maybe "" id (scopeAllegation s)
  ,qualifiedIdentity (concatMap (\(a,b)->[a,b]) (sort (scopeEntities s)))]
componentObjectKey :: Text -> CheckedComponent -> Text -> Text -> Text
componentObjectKey namespace c category object=qualifiedIdentity
  ([namespace,componentIdentity (checkedComponent c),maybe "model" (\(a,b)->qualifiedIdentity [a,b]) (componentEntry (checkedComponent c))]
   ++scopeKey (checkedScope c)++[category,object,qualifiedIdentity (concatMap (\(a,b)->[a,b]) (sort (componentEntities (checkedComponent c))))])
candidateObjectKey :: Text -> PlanScope -> Text -> Text
candidateObjectKey namespace scope object=qualifiedIdentity ([namespace,"candidate"]++scopeKey scope++[object])
