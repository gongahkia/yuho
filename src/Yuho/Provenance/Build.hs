{-# LANGUAGE OverloadedStrings #-}
-- Projection only: no arithmetic or truth evaluation. All executed records come
-- from the sealed existing executor. Original declaration origins use the same
-- resolver as admission, never a text search for possible source owners.
module Yuho.Provenance.Build (projectTypedProvenance,projectStaticProvenance,validateTypedProvenance) where
import Control.Monad (forM,unless)
import qualified Data.Aeson as A
import qualified Data.Aeson.Key as AK
import qualified Data.Aeson.KeyMap as AM
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as M
import qualified Data.Set as S
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as U
import qualified Yuho.CoreYuho.TypedFinite as K
import qualified Yuho.Authoring.Types as SDK
import qualified Yuho.Authoring.Typed as SDK
import qualified Yuho.Authoring.Source as SDK
import qualified Yuho.Quantitative as Q
import qualified Yuho.Quantitative.Graph as QG
import Yuho.ScopedDefinitions.Types
import Yuho.Dependency.Types hiding (projectionFormat)
import Yuho.Dependency.Check
import Yuho.Dependency.Run
import qualified Yuho.Dependency.Projection as Old
import Yuho.Provenance.Types
import Yuho.Diagram.Types
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Surface.TypedFinite (dependencyTypedOrigins,encodeTypedFiniteRequest)

field :: Text -> A.Value -> A.Value
field k (A.Object o)=M.findWithDefault A.Null k (M.fromList [(AK.toText a,b) | (a,b)<-AM.toList o])
field _ _=A.Null
text :: Text -> A.Value -> Text
text k v=case field k v of A.String t->t;_->""
rows :: Text -> A.Value -> [A.Value]
rows k v=case field k v of A.Array xs->foldr (:) [] xs;_->[]
texts :: Text -> A.Value -> [Text]
texts k v=[x | A.String x<-rows k v]
string :: Text -> A.Value
string=A.String
enc :: A.ToJSON a => a -> Text
enc=U.decodeUtf8 . encode
scopeAuthority :: ComponentRecord -> A.Value
scopeAuthority r=A.object ["component" A..= executionComponent r,"scope" A..= executionScope r
  ,"snapshot" A..= executionSnapshot r,"template" A..= executionTemplate r]
componentKey :: CheckedPlan -> Text -> [Text]
componentKey p c=["component",checkedDigest p,c]
sourceKey :: FilePath -> Text -> [Text]
sourceKey path bytes=["source",T.pack path,sha256Text (U.encodeUtf8 bytes)]

-- Exact equality coalesces the same authored source only. A key collision with
-- different ownership or content is always an error, never winner selection.
finish :: Text -> Text -> A.Value -> [Node] -> [Edge] -> Either DependencyDiagnostic Projection
finish mode auth backing ns es=do
  nmap<-foldRecords identity ns
  emap<-foldRecords edgeIdentity es
  let known=M.keysSet nmap
  ensure "PVREFERENCE" [] "provenance edge has absent endpoint"
    (all (\e->S.member (from e) known && S.member (to e) known) (M.elems emap))
  ensure "PVCATEGORY" [] "unknown node category or incompatible typed provenance endpoints"
    (all ((`elem` nodeCategories) . category) (M.elems nmap) && all (\e->
      (category (nmap M.! from e),category (nmap M.! to e)) `elem` edgeSignature (relationship e)) (M.elems emap))
  ensure "PVLIMIT" [] "complete provenance exceeds 65536 nodes or 262144 edges"
    (M.size nmap<=65536 && M.size emap<=262144)
  let result=Projection (key [provenanceFormat,mode,auth,sha256Text (encode (M.elems nmap,M.elems emap))]) mode auth (M.elems nmap) (M.elems emap) backing
  ensure "PVLIMIT" [] "complete encoded provenance exceeds 32 MiB" (BS.length (encode result)<=33554432)
  pure result
 where
  foldRecords f=foldl (\acc x->do
    m<-acc
    case M.lookup (f x) m of
      Just prior->ensure "PVIDENTITY" [f x] "distinct records have the same structural identity" (prior==x) >> pure m
      Nothing->pure (M.insert (f x) x m)) (Right M.empty)

projectStaticProvenance :: CheckedPlan -> Either DependencyDiagnostic Projection
projectStaticProvenance p=do
  parts<-traverse (staticComponent p) (M.toAscList (checkedComponents p))
  planPart<-staticPlan p
  finish "checked_not_evaluated" (checkedDigest p) (A.toJSON (checkedDocument p))
    (sourceNodes p++fst planPart++concatMap fst parts) (snd planPart++concatMap snd parts)

sourceNodes :: CheckedPlan -> [Node]
sourceNodes p=[node (sourceKey path bytes) "source_document" (T.pack path) "authored" Nothing A.Null
  (A.object ["path" A..= path,"sha256" A..= sha256Text (U.encodeUtf8 bytes),"utf8" A..= bytes])
  | (path,bytes)<-M.toAscList (dependencySources (checkedDocument p))]

staticComponent :: CheckedPlan -> (Text,CheckedComponent) -> Either DependencyDiagnostic ([Node],[Edge])
staticComponent p (name,c)=do
  request<-jsonBytes (encodeTypedFiniteRequest "PROVENANCE-CHECKED" (checkedProgram c))
  let declaration=checkedComponent c
      auth=A.object ["component" A..= name,"scope" A..= checkedScope c,"template_snapshot" A..= checkedTemplateDigest c]
      ck=componentKey p name
      component=node ck "checked_component" name "checked_not_evaluated" Nothing auth
        (A.object ["declaration" A..= declaration,"local_scope" A..= checkedLocalScope c
          ,"mappings" A..= checkedMappings c,"scoped" A..= checkedScopedDefinitions c
          ,"quantitative" A..= checkedQuantitative c,"slots" A..= checkedSlots c])
      structure=node (ck++["checked_structure"]) "checked_structure" "Checked structure; placeholders are not observations"
        "checked_not_evaluated" Nothing auth request
      program=field "program" request
      categories=[("entity_types","entity-type"),("entities","entity"),("predicates","predicate"),("scalars","scalar")
        ,("requirements","requirement"),("rules","rule"),("propositions","proposition"),("enum_types","enum-type")]
      loweredTarget kind i
        | kind=="norm",i `elem` map K.normName (K.finiteNorms (checkedProgram c))=Just ("r:norm:"<>i)
        | kind=="responsibility-route",i `elem` map K.routeName (K.finiteRoutes (checkedProgram c))=Just ("r:route:"<>i)
        | otherwise=Nothing
      loweringLinks owner kind i=[edge owner (key (ck++["declaration","rule",target])) "lowered_as" (string kind)
        | Just target<-[loweredTarget kind i]]
      declarations=[(kind,case v of A.String t->t;_->text "id" v,v) | (array,kind)<-categories,v<-rows array program]
  (origins,_)<-originsFor p c
  sdkPart<-sdkAuthorship p c declarations
  original<-forM origins $ \(kind,name',site,use)->do
    (n,es)<-locatedDeclaration p kind name' site
    let uk=ck++["import_use",kind,name']
    case use of
      Nothing->pure ([n],es++[edge (identity n) (key (ck++["declaration",kind,name'])) "checked_as" A.Null
        | any (\(k,i,_)->k==kind && i==name') declarations]++loweringLinks (identity n) kind name')
      Just u->do
        source<-siteSource p u
        let un=node uk "authored_use" (Q.qToken u) "authored" Nothing auth (A.toJSON u)
        pure ([n,un],es++[edge source (key uk) "authored_in" (A.toJSON u),edge (identity n) (key uk) "selected_declaration" A.Null]
          ++[edge (key uk) (key (ck++["declaration",kind,name'])) "checked_as" A.Null
            | any (\(k,i,_)->k==kind && i==name') declarations]++loweringLinks (key uk) kind name')
  let lowered=[node (ck++["declaration",kind,i]) "checked_declaration" (kind<>" "<>i)
        "checked_not_evaluated" Nothing auth (A.object ["kind" A..= kind,"name" A..= i,"checked" A..= v
        ,"origin" A..= (if any (\(k,n,_,_)->k==kind && n==i) origins then "located_authored"
          else "structured_or_lowered; original authority retained in component record"::Text)]) | (kind,i,v)<-declarations]
      links=[edge (key ck) (identity n) "declares_checked" A.Null | n<-lowered]
  pure (component:structure:lowered++fst sdkPart++concatMap fst original,
    edge (key ck) (identity structure) "has_checked_structure" A.Null:links++snd sdkPart++concatMap snd original)

originsFor :: CheckedPlan -> CheckedComponent -> Either DependencyDiagnostic ([(Text,Text,Q.QSite,Maybe Q.QSite)],[(Text,Q.QSite)])
originsFor p c=case (componentProfile decl,componentTemplate decl) of
  ("native-typed",Nothing)->either (Left . surfaceFailureIn sources) Right
    (dependencyTypedOrigins (M.map U.encodeUtf8 sources) (componentModel decl) (componentScenario decl) (snd <$> componentEntry decl))
  _->Right ([],[])
 where decl=checkedComponent c;sources=dependencySources (checkedDocument p)

siteSource :: CheckedPlan -> Q.QSite -> Either DependencyDiagnostic Text
siteSource p site=do
  contents<-maybe (failure "PVSOURCE" [T.pack (Q.qSource site)] "source absent") Right
    (M.lookup (Q.qSource site) (dependencySources (checkedDocument p)))
  let bs=U.encodeUtf8 contents; start=Q.qStart site;end=Q.qEnd site
      actual=BS.take (end-start) (BS.drop start bs)
      prefix=BS.take start bs
      ls=BS.split 10 prefix
      line=length ls;column=BS.length (last ls)+1
  ensure "PVSPAN" [Q.qToken site] "source span/token/UTF-8 coordinates disagree with retained owner"
    (start>=0 && end>=start && end<=BS.length bs && actual==U.encodeUtf8 (Q.qToken site)
      && line==Q.qLine site && column==Q.qColumn site)
  pure (key (sourceKey (Q.qSource site) contents))

locatedDeclaration :: CheckedPlan -> Text -> Text -> Q.QSite -> Either DependencyDiagnostic (Node,[Edge])
locatedDeclaration p kind name site=do
  source<-siteSource p site
  let n=node ["authored_declaration",source,kind,name,T.pack (show (Q.qStart site))]
        "authored_declaration" (kind<>" "<>name) "authored" Nothing A.Null (A.toJSON site)
  pure (n,[edge source (identity n) "authored_in" (A.toJSON site)])

projectTypedProvenance :: DependencyExecution -> Either DependencyDiagnostic Projection
projectTypedProvenance execution=do
  static<-projectStaticProvenance p
  legacy<-Old.projectDependencyPlan execution
  components<-traverse (executedComponent execution) (executionComponents execution)
  sourceLinks<-retainedSourceLinks execution
  let graph=Old.dependencyGraph execution
      oldRecord i=case [field "record" row | row<-rows "included" (Old.dependencyViewBindings execution),text "semantic_id" row==i] of
        [v]->v;_->A.Null
      oldKey i=key ["accepted_evidence",dependencyExecutionId execution,i]
      oldNodes=[node ["accepted_evidence",dependencyExecutionId execution,graphNodeId n] (graphNodeKind n) (graphNodeLabel n)
        (maybe "retained" coreObservationEvaluation (graphNodeObservation n)) (graphNodeStatus n)
        (A.object ["original_identity" A..= graphNodeId n,"boundary" A..= graphNodeBoundary n]) (oldRecord (graphNodeId n))
        | n<-semanticGraphNodes graph]
      oldEdges=[edge (oldKey (graphEdgeFrom x)) (oldKey (graphEdgeTo x)) (graphEdgeKind x) (string (graphEdgeLabel x)) | x<-semanticGraphEdges graph]
      selected=[edge (observationKey p r (if portCategory (observationPort port)=="typed.expression.truth" then "expressions" else "propositions") (portObject (observationPort port)))
          (oldKey (observationIdentity port)) "selected_port" (A.toJSON (observationPort port))
        | conversion<-executionConversions execution++map availabilityGuard (executionCandidates execution)
        ,let port=conversionSource conversion,observationValue port/=Nothing
        ,r<-executionComponents execution,executionComponent r==portComponent (observationPort port)]
      authoredLinks=[edge (key ["plan_binding",checkedDigest p,bindingIdentity b])
          (oldKey (qualifiedIdentity [planIdentity (dependencyPlan (checkedDocument p)),"conversion",bindingIdentity b])) "executes_binding" A.Null
          | b<-planBindings (dependencyPlan (checkedDocument p))]
        ++[edge (key ["plan_candidate",checkedDigest p,candidateIdentity (availabilityCandidate c)])
          (oldKey (conversionDestination (availabilityGuard c))) "candidate_effect" A.Null | c<-executionCandidates execution]
      scopeLinks=[edge (key (componentKey p (executionComponent r))) (oldKey (graphNodeId n)) "retained_component" A.Null
        | r<-executionComponents execution,n<-semanticGraphNodes graph,graphNodeKind n=="component"
        ,Just c<-[M.lookup (executionComponent r) (checkedComponents p)]
        ,graphNodeId n==componentObjectKey (planIdentity (dependencyPlan (checkedDocument p))) c "component" (executionComponent r)]
  finish "executed" (dependencyExecutionId execution) legacy
    (nodes static++oldNodes++concatMap fst components) (edges static++oldEdges++selected++scopeLinks++authoredLinks++sourceLinks++concatMap snd components)
 where p=executionPlan execution

observationKey :: CheckedPlan -> ComponentRecord -> Text -> Text -> Text
observationKey p r category' name=key (componentKey p (executionComponent r)++[executionSnapshot r,"observation",category',name])

executedComponent :: DependencyExecution -> ComponentRecord -> Either DependencyDiagnostic ([Node],[Edge])
executedComponent execution r=do
  c<-maybe (failure "PVREFERENCE" [executionComponent r] "checked component absent") Right (M.lookup (executionComponent r) (checkedComponents p))
  (_,scalarOrigins)<-originsFor p c
  sdkSelections<-selectedSDK p c
  let ck=componentKey p (executionComponent r);ak=ck++[executionSnapshot r];auth=scopeAuthority r
      cid=key ck
      evaluated=executionState r=="evaluated"
      actualProgram=field "program" (executionRequest r)
      factKey f=key (ak++["fact",text "predicate" f,enc (field "arguments" f)])
      scalarKey i=case executionQuantitative r of
        Just q | [s]<-filter (\s->Q.qOutput s==i && null (Q.qPath s)) (Q.qSteps q) ->oldKey (QG.stepId (Old.quantitativePrefix r) s)
        Just q | i `elem` map Q.qInputName (Q.qInputs (Q.qCheckedPlan q)) ->oldKey (QG.inputId (Old.quantitativePrefix r) i)
        _->key (ak++["scalar",i])
      decl kind i=key (ck++["declaration",kind,i])
      incoming f=[x | x<-executionIncoming r,text "predicate" (conversionGeneratedInput x)==text "predicate" f
        ,field "arguments" (conversionGeneratedInput x)==field "arguments" f]
      scoped f=[a | a<-scopedAssessments (checkedScopedDefinitions c),selectedPredicate a==text "predicate" f
        ,A.toJSON (selectedArguments a)==field "arguments" f]
      supplied f=[v | (kind,i,v)<-sdkSelections,kind=="assessment",i==K.groundIdentityText (text "predicate" f) (texts "arguments" f)]
      facts=[node (ak++["fact",text "predicate" f,enc (field "arguments" f)])
        (if null (incoming f) then "selected_classification" else "generated_condition_input")
        (text "predicate" f<>"("<>T.intercalate ", " (texts "arguments" f)<>") | "<>text "status" f)
        (if null (incoming f) then "supplied" else "execution_generated") (Just (text "status" f)) auth
        (A.object ["actual" A..= f,"selected_native" A..= scoped f,"selected_sdk" A..= supplied f
          ,"generated_by" A..= map conversionIdentity (incoming f)]) | f<-rows "facts" actualProgram]
      quantityNames=case executionQuantitative r of Nothing->[];Just q->M.keys (Q.qValues q)
      values=[node (ak++["scalar",text "id" v]) "selected_scalar" (text "id" v<>" | "<>enc (field "value" v)) "supplied" Nothing auth
        (A.object ["actual" A..= v,"exact" A..= fmap Q.scalarRecord (M.lookup (text "id" v) (K.finiteValues (checkedProgram c))),"source" A..= lookup (text "id" v) scalarOrigins
          ,"selected_sdk" A..= [x | (kind,i,x)<-sdkSelections,kind=="value",i==text "id" v]])
        | v<-rows "values" actualProgram,text "id" v `notElem` quantityNames]
      observations=[node (ck++[executionSnapshot r,"observation",kind,text "id" v]) (case kind of "expressions"->"expression_observation";"rules"->"rule_observation";_->"proposition_observation")
        (text "id" v<>" | "<>text "status" v<>if text "state" v=="" then "" else " | "<>text "state" v)
        "evaluated" (Just (text "status" v)) auth v
        | kind<-["expressions","rules","propositions"],v<-rows kind (executionBackend r)]
      observationLinks=[edge (decl (case kind of "expressions"->"requirement";"rules"->"rule";_->"proposition") (text "id" v))
        (observationKey p r kind (text "id" v)) "evaluated_as" A.Null
        | kind<-["expressions","rules","propositions"],v<-rows kind (executionBackend r)]
      rules=[edge (observationKey p r "rules" (text "id" rule)) (observationKey p r "propositions" (text "conclusion" rule)) "resolution_rule" rule
        | rule<-rows "rules" (executionBackend r)]
      priority=[edge (observationKey p r "rules" high) (observationKey p r "rules" (text "id" rule)) "blocks_by_priority" rule
        | rule<-rows "rules" (executionBackend r),high<-texts "defeated_by" rule]
      factLinks=[edge (decl "predicate" (text "predicate" f)) (factKey f) "classifies_application" A.Null | f<-rows "facts" actualProgram]
        ++[edge (oldKey (conversionDestination cv)) (factKey f) "generated_by_binding" (A.toJSON cv)
          | f<-rows "facts" actualProgram,cv<-incoming f]
      sdkLinks=[edge (key (ck++["sdk_object",text "typedId" (field "typedAssessmentMeta" v)])) (factKey f) "selects_sdk_input" v
        | f<-rows "facts" actualProgram,v<-supplied f]
        ++[edge (key (ck++["sdk_object",text "typedId" (field "valueMeta" v)])) (scalarKey i) "selects_sdk_input" v
          | (kind,i,v)<-sdkSelections,kind=="value",i `elem` map (text "id") (rows "values" actualProgram)]
      scalarLinks=[edge (decl "scalar" (text "id" v)) (scalarKey (text "id" v)) "selects_scalar" A.Null | v<-rows "values" actualProgram]
  -- A retained not-evaluated component has no backend rows or fabricated reads.
  ensure "PVEVIDENCE" [executionComponent r] "unevaluated component contains execution records"
    (evaluated || (null (executionReads r) && executionBackend r==A.Null && executionQuantitative r==Nothing))
  inputSites<-fmap concat $ forM (rows "facts" actualProgram) $ \f->forM (scoped f) $ \a->do
    site<-assessmentSite p a
    source<-siteSource p site
    pure (edge source (factKey f) "selected_assessment" (A.toJSON site))
  valueSites<-forM [(v,site) | v<-rows "values" actualProgram,Just site<-[lookup (text "id" v) scalarOrigins]] $ \(v,site)->do
    source<-siteSource p site
    pure (edge source (scalarKey (text "id" v)) "selected_value" (A.toJSON site))
  normal<-readGraph (ak++["read"]) auth decl factKey scalarKey (executionReads r)
  filters<-case executionQuantitative r of
    Nothing->pure []
    Just q->fmap concat $ forM (Q.qSteps q) $ \s->do
      let declared=case Q.qNode s of
            Q.QSum xs->[(item,condition) | Q.QItem item _ (Just condition)<-xs]
            Q.QCountItems xs->xs
            _->[]
          actual=Q.qFilterReads s
      ensure "PVEVIDENCE" [Q.qOutput s] "filter records do not match the authored item occurrences"
        (map snd declared==map fst actual)
      forM (zip declared actual) $ \((item,condition),(_,rs))->do
        let prefix=ak++["filter_read",Q.qOutput s,enc (Q.qPath s),item,condition]
            records=map (readJson (executionComponent r) (executionSnapshot r)) rs
        (ns,es)<-readGraph prefix auth decl factKey scalarKey records
        let rootNodes=[n | n<-ns,rows "path" (record n)==[],texts "root" (record n)==["expression",condition]]
        ensure "PVEVIDENCE" [condition] "filter root observation missing" (length rootNodes==1)
        pure (ns,es++[edge (identity n) (oldKey (QG.stepId (Old.quantitativePrefix r) s)) "filter_decision"
          (A.object ["item" A..= item,"condition" A..= condition,"membership" A..= lookup item (Q.qItems s)]) | n<-rootNodes])
  let readRoots=[edge (readKey (ak++["read"]) row) (observationKey p r (if rootKind=="expression" then "expressions" else "rules") rootName) "evaluated_root" A.Null
        | row<-executionReads r,null (rows "path" row),rootKind:rootName:_<-[texts "root" row]]
      scopedLinks=[edge (readKey (ak++["read"]) row) (oldKey (text "identity" occurrence)) "scoped_occurrence" A.Null
        | use<-rows "uses" (scopedDefinitionEvidence execution),text "component" use==executionComponent r
        ,occurrence<-rows "occurrences" use,let row=field "read" occurrence]
      actual=node (ak++["execution"]) "component_execution" (executionComponent r<>" | "<>executionState r) (executionState r) Nothing auth
        (A.object ["request" A..= executionRequest r,"backend" A..= executionBackend r,"blocked_by" A..= executionBlockedBy r])
  pure (actual:facts++values++observations++fst normal++concatMap fst filters,
    edge cid (identity actual) "executed_component" A.Null:observationLinks++rules++priority++factLinks++scalarLinks++inputSites++valueSites
    ++sdkLinks++snd normal++concatMap snd filters++readRoots++scopedLinks)
 where
  p=executionPlan execution
  oldKey i=key ["accepted_evidence",dependencyExecutionId execution,i]

readKey :: [Text] -> A.Value -> Text
readKey prefix row=key (prefix++[enc (field "root" row),enc (field "path" row),enc (field "bindings" row)])

-- The evaluator emits root/path/bindings for every eager occurrence. Immediate
-- parent paths identify an actual ledger row, never a hypothetical AST branch.
readGraph :: [Text] -> A.Value -> (Text->Text->Text) -> (A.Value->Text) -> (Text->Text) -> [A.Value]
  -> Either DependencyDiagnostic ([Node],[Edge])
readGraph prefix auth decl fact scalar ledger=do
  unique "actual read occurrence" (map (readKey prefix) ledger)
  parts<-forM ledger $ \row->do
    let path=rows "path" row; root=field "root" row
        n=node (prefix++[enc root,enc (field "path" row),enc (field "bindings" row)]) "evaluation_read"
          (text "operator" row<>" | "<>text "status" row<>" | "<>T.intercalate "/" (texts "root" row)
            <>" | path "<>enc path<>" | "<>enc (field "bindings" row)) "evaluated" (Just (text "status" row)) auth row
    parents<-if null path then pure [] else case [other | other<-ledger,field "root" other==root,rows "path" other==init path] of
      [parent]->pure [edge (identity n) (readKey prefix parent) "evaluated_operand" (A.object ["operand" A..= last path])]
      _->failure "PVEVIDENCE" [identity n] "actual read has no unique evaluated parent"
    inputs<-forM (rows "input_records" row) $ \input->case text "kind" input of
      "ground_predicate"->pure (edge (fact input) (identity n) "reads_classification" input)
      "scalar_operand"->pure (edge (scalar (text "scalar" input)) (identity n) "reads_scalar" input)
      "requirement_reference"->pure (edge (decl "requirement" (text "requirement" input)) (identity n) "expands_reference" input)
      _->failure "PVEVIDENCE" [identity n] "unknown actual read input category"
    pure (n,parents++inputs)
  pure (map fst parts,concatMap snd parts)

assessmentSite :: CheckedPlan -> ScopedAssessment -> Either DependencyDiagnostic Q.QSite
assessmentSite p a=do
  contents<-maybe (failure "PVSOURCE" [] "selected assessment source absent") Right (M.lookup (selectedSource a) (dependencySources (checkedDocument p)))
  let start=sum [BS.length line+1 | line<-take (selectedLine a-1) (BS.split 10 (U.encodeUtf8 contents))]+selectedColumn a-1
  pure (Q.QSite (selectedSource a) (selectedLine a) (selectedColumn a) start (start+BS.length (U.encodeUtf8 (selectedPredicate a))) (selectedPredicate a))

-- Compile mappings already selected the actual assessment IDs. Decode only the
-- retained source document, without reevaluating or consulting live files.
selectedSDK :: CheckedPlan -> CheckedComponent -> Either DependencyDiagnostic [(Text,Text,A.Value)]
selectedSDK p c
  | componentProfile (checkedComponent c)/="sdk-typed-v0.3"=Right []
  | otherwise=do
    contents<-maybe (failure "PVSOURCE" [] "SDK source absent") Right
      (M.lookup (componentModel (checkedComponent c)) (dependencySources (checkedDocument p)))
    d<-either (failure "PVSOURCE" [] . SDK.diagnosticMessage) Right (SDK.decodeTypedDocument (U.encodeUtf8 contents))
    let mappings=rows "kernel_mappings" (checkedMappings c)
        byId=[("assessment",SDK.typedId (SDK.typedAssessmentMeta a),A.toJSON a) | a<-SDK.typedAssessments d]
          ++[("value",SDK.typedId (SDK.valueMeta v),A.toJSON v) | v<-SDK.typedValues d]
    forM [m | m<-mappings,text "typedMappingCategory" m `elem` ["assessment","value"]] $ \m->case
      [v | (kind,i,v)<-byId,kind==text "typedMappingCategory" m,i==text "typedMappingAuthoredId" m] of
        [v]->pure (text "typedMappingCategory" m,text "typedMappingKernelId" m,v)
        _->failure "PVEVIDENCE" [] "selected SDK assessment mapping is absent or ambiguous"

validateTypedProvenance :: DependencyExecution -> A.Value -> Either DependencyDiagnostic ()
validateTypedProvenance execution submitted=do
  expected<-projectTypedProvenance execution
  unless (A.toJSON expected==submitted) (failure "PVSTALE" [] "projection differs from authoritative source, selected inputs, execution or edge correspondence")

-- Original scoped/quantitative locations already retained by their accepted
-- compilers are checked against the same immutable source bundle before use.
retainedSourceLinks :: DependencyExecution -> Either DependencyDiagnostic [Edge]
retainedSourceLinks e=do
  scoped<-fmap concat $ forM (scopedUseRecords e) $ \(_,u,d,uid)->do
    definitionSite<-siteAt (definitionSource d) (definitionLine d) (definitionColumn d) (definitionName d)
    useSite<-siteAt (useSource u) (useLine u) (useColumn u) (useIdentity u)
    a<-link definitionSite (qualifiedIdentity ("shared-definition":definitionKey d)) "authored_in"
    b<-link useSite uid "authored_in"
    pure [a,b]
  quantities<-fmap concat $ forM (executionComponents e) $ \r->case executionQuantitative r of
    Nothing->pure []
    Just q->do
      definitions<-fmap concat $ forM (Q.qDefinitions (Q.qCheckedPlan q)) $ \d->do
        a<-link (Q.qSite d) (QG.definitionId d) "authored_in"
        b<-link (maybe (Q.qSite d) id (Q.qUseSite d)) (QG.useId (Old.quantitativePrefix r) (Q.qName d)) "authored_in"
        pure [a,b]
      inputs<-forM (Q.qInputs (Q.qCheckedPlan q)) $ \i->link (Q.qInputSite i) (QG.inputId (Old.quantitativePrefix r) (Q.qInputName i)) "selected_value"
      pure (definitions++inputs)
  pure (scoped++quantities)
 where
  p=executionPlan e
  link site target relation=do
    owner<-siteSource p site
    pure (edge owner (key ["accepted_evidence",dependencyExecutionId e,target]) relation (A.toJSON site))
  siteAt file line column token=do
    content<-maybe (failure "PVSOURCE" [T.pack file] "original scoped source absent") Right (M.lookup file (dependencySources (checkedDocument p)))
    let start=sum [BS.length x+1 | x<-take (line-1) (BS.split 10 (U.encodeUtf8 content))]+column-1
    pure (Q.QSite file line column start (start+BS.length (U.encodeUtf8 token)) token)

staticPlan :: CheckedPlan -> Either DependencyDiagnostic ([Node],[Edge])
staticPlan p=do
  let plan=dependencyPlan (checkedDocument p)
      origins=[node ["authorisation",checkedDigest p,originIdentity o] "authorisation_origin"
        (originIdentity o<>" | "<>originLocator o) "authored" Nothing A.Null (A.toJSON o) | o<-planOrigins plan]
      bindings=[(node ["plan_binding",checkedDigest p,bindingIdentity b] "authored_binding" (bindingIdentity b<>" | "<>bindingPolicy b)
          "authored" Nothing A.Null (A.toJSON b),bindingLocation b,bindingReferences b) | b<-planBindings plan]
      candidates=[(node ["plan_candidate",checkedDigest p,candidateIdentity c] "authored_candidate" (candidateIdentity c<>" | authored candidate")
          "authored" Nothing A.Null (A.toJSON c),candidateLocation c,candidateReferences c) | c<-planCandidates plan]
  located<-forM (bindings++candidates) $ \(n,loc,refs)->do
    sites<-case loc of
      Nothing->pure []
      Just l->do
        content<-maybe (failure "PVSOURCE" [T.pack (locationPath l)] "plan declaration source absent") Right
          (M.lookup (locationPath l) (dependencySources (checkedDocument p)))
        let bs=U.encodeUtf8 content;start=locationStart l;end=locationEnd l
        token<-either (const (failure "PVSPAN" [] "plan span cuts UTF-8 code point")) Right
          (U.decodeUtf8' (BS.take (end-start) (BS.drop start bs)))
        let site=Q.QSite (locationPath l) (locationLine l) (locationColumn l) start end token
        source<-siteSource p site
        pure [edge source (identity n) "authored_in" (A.toJSON site)]
    pure (n,sites++[edge (key ["authorisation",checkedDigest p,ref]) (identity n) "authorisation_rationale" A.Null | ref<-refs])
  pure (origins++map fst located,concatMap snd located)

-- SDK records keep their own source-reference namespace, not an invented file
-- span in the enclosing JSON document. Unselected objects remain authored only.
sdkAuthorship :: CheckedPlan -> CheckedComponent -> [(Text,Text,A.Value)] -> Either DependencyDiagnostic ([Node],[Edge])
sdkAuthorship p c declarations
  | componentProfile (checkedComponent c)/="sdk-typed-v0.3"=Right ([],[])
  | otherwise=do
    content<-maybe (failure "PVSOURCE" [] "SDK source missing") Right (M.lookup file (dependencySources (checkedDocument p)))
    d<-either (failure "PVSOURCE" [] . SDK.diagnosticMessage) Right (SDK.decodeTypedDocument (U.encodeUtf8 content))
    let ck=componentKey p name
        sk source=key (ck++["sdk_source",SDK.sourceId source])
        objectId meta=key (ck++["sdk_object",SDK.typedId meta])
        sources=[node (ck++["sdk_source",SDK.sourceId source]) "sdk_source_record" (SDK.sourceId source)
          "authored" Nothing (string (key (sourceKey file content))) (A.toJSON source) | source<-SDK.typedOriginalSources d]
        objectRecords=[(text "typedId" (field metaKey value),value)
          | (array,metaKey)<-[("typedEntityTypes","entityTypeMeta"),("typedEntities","entityMeta"),("typedPredicates","predicateMeta")
            ,("typedApplications","applicationMeta"),("typedScalars","scalarMeta"),("typedExpressions","expressionMeta")
            ,("typedRules","typedRuleMeta"),("typedPropositions","propositionMeta"),("typedAssessments","typedAssessmentMeta"),("typedValues","valueMeta")]
          ,value<-rows array (A.toJSON d)]
        inputAuthority=[edge (key (ck++["sdk_object",SDK.assessedApplication a])) (objectId (SDK.typedAssessmentMeta a)) "assesses_application" (A.toJSON (SDK.assessedTuple a))
          | a<-SDK.typedAssessments d]
          ++[edge (key (ck++["sdk_object",SDK.valueScalar v])) (objectId (SDK.valueMeta v)) "supplies_declared_scalar" A.Null | v<-SDK.typedValues d]
        objects=[node (ck++["sdk_object",SDK.typedId meta]) "sdk_authored_object" (kind<>" "<>SDK.typedLabel meta)
          "authored" Nothing (string (key (sourceKey file content))) (A.object ["kind" A..= kind,"metadata" A..= meta,"object" A..= lookup (SDK.typedId meta) objectRecords])
          | (kind,meta)<-SDK.typedObjects d]
        mappedKind kind=case kind of "expression"->"requirement";"entity_type"->"entity-type";_->kind
        maps=[edge (key (ck++["sdk_object",text "typedMappingAuthoredId" m]))
          (key (ck++["declaration",mappedKind (text "typedMappingCategory" m),text "typedMappingKernelId" m])) "compiled_sdk_declaration" m
          | m<-rows "kernel_mappings" (checkedMappings c)
          ,any (\(kind,i,_)->kind==mappedKind (text "typedMappingCategory" m) && i==text "typedMappingKernelId" m) declarations]
    refs<-fmap concat $ forM (SDK.typedObjects d) $ \(_,meta)->forM (SDK.typedSources meta) $ \ref->do
      source<-case [x | x<-SDK.typedOriginalSources d,SDK.sourceId x==SDK.referenceSource ref] of
        [x]->Right x
        _->failure "PVSOURCE" [SDK.referenceSource ref] "SDK source owner absent or ambiguous"
      case SDK.referenceSpan ref of
        Nothing->pure ()
        Just span'->do
          canonical<-either (failure "PVSPAN" [] . T.intercalate "; " . map SDK.diagnosticMessage) Right
            (SDK.sourceAnchorBytes source (toInteger (SDK.start span')) (toInteger (SDK.end span')))
          ensure "PVSPAN" [] "SDK source-reference coordinates disagree with retained owner" (canonical==ref)
      let anchor=node (ck++["sdk_reference",SDK.referenceSource ref,enc (SDK.referenceSpan ref)])
            "source_reference" (SDK.referenceSource ref<>" | "<>maybe "locator only" (\sp->"bytes "<>T.pack (show (SDK.start sp))<>".."<>T.pack (show (SDK.end sp))) (SDK.referenceSpan ref))
            "authored" Nothing (string (sk source)) (A.toJSON ref)
      pure (anchor,[edge (sk source) (identity anchor) "anchors_original" (A.toJSON ref),edge (identity anchor) (objectId meta) "sdk_source_reference" A.Null])
    pure (sources++objects++map fst refs,concatMap snd refs++maps++inputAuthority++[edge (key (sourceKey file content)) (identity n) "declares_sdk_object" A.Null | n<-sources++objects])
 where
  file=componentModel (checkedComponent c)
  name=componentIdentity (checkedComponent c)
