{-# LANGUAGE OverloadedStrings #-}
-- | Complete plan evidence plus an explicitly focused native v0.2 reference view.
module Yuho.Dependency.Projection where
import qualified Data.Aeson.Key
import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as AM
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as M
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as U
import Yuho.Dependency.Types
import Yuho.Dependency.Check
import Yuho.Dependency.Run
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Dependency.Codec
import Yuho.Diagram.Types
import Yuho.Diagram.Encode
import qualified Yuho.Surface.TypedFinite
import Yuho.Surface.Lexer (lexSource)
import qualified Yuho.Surface.Token as ST

sourceMapDependencyPlan :: DependencyExecution -> A.Value
sourceMapDependencyPlan e=A.object ["format" A..= ("yuho.dependency-source-map/v0.1-experimental"::Text)
  ,"sources" A..= [A.object ["path" A..= path,"sha256" A..= sha256Text (U.encodeUtf8 text),"utf8" A..= text
      ,"tokens" A..= tokens path text] | (path,text)<-M.toAscList (dependencySources doc)]
  ,"origins" A..= planOrigins (dependencyPlan doc)
  ,"notice" A..= ("Declaration tokens use original half-open UTF-8 byte coordinates. Locator-only legal origins have no invented quotation. Generated request inputs have separate execution origin."::Text)]
 where
  doc=checkedDocument (executionPlan e)
  tokens path text=case lexSource path (U.encodeUtf8 text) of
    Left _->[]
    Right ts->[A.object ["text" A..= ST.tokenText t,"line" A..= ST.tokenLine t,"column" A..= ST.tokenColumn t
      ,"start" A..= start t,"end" A..= (start t+BS.length (U.encodeUtf8 (ST.tokenText t))+if ST.tokenKind t==ST.StringToken then 2 else 0)]
      | t<-ts,ST.tokenKind t/=ST.EndToken]
    where
      bytes=U.encodeUtf8 text
      start t=sum [BS.length line+1 | line<-take (ST.tokenLine t-1) (BS.split 10 bytes)]+ST.tokenColumn t-1

projectDependencyPlan :: DependencyExecution -> Either DependencyDiagnostic A.Value
projectDependencyPlan e=do
  let graph=dependencyGraph e
  unique "view graph node" (map graphNodeId (semanticGraphNodes graph))
  ensure "DEPOBSERVATION" [] "view edge has unknown endpoint" (all (\edge->all (`elem` map graphNodeId (semanticGraphNodes graph)) [graphEdgeFrom edge,graphEdgeTo edge]) (semanticGraphEdges graph))
  json<-jsonBytes (encodeNativeSemanticGraph graph)
  pure (A.object ["format" A..= projectionFormat,"execution" A..= dependencyExecutionId e
    ,"document" A..= checkedDocument (executionPlan e),"report" A..= reportDependencyPlan e
    ,"source_map" A..= sourceMapDependencyPlan e,"view" A..= json,"bindings" A..= dependencyViewBindings e
    ,"checked_components" A..= [A.object ["component" A..= key,"template_snapshot" A..= checkedTemplateDigest c
       ,"declared_scope" A..= checkedScope c,"local_scope" A..= checkedLocalScope c
       ,"identity_maps" A..= (componentNominals (checkedComponent c),componentEntities (checkedComponent c))
       ,"slots" A..= checkedSlots c,"checked_request" A..= request c
       ,"notice" A..= ("Checked request contains structural slot placeholders; authoritative evaluated inputs are in the execution request."::Text)]
       | (key,c)<-M.toAscList (checkedComponents (executionPlan e))]])
 where request c=case jsonBytes (Yuho.Surface.TypedFinite.encodeTypedFiniteRequest "DEPENDENCY-TEMPLATE" (checkedProgram c)) of
        Right v->v;Left _->A.Null

dependencyGraph :: DependencyExecution -> SemanticGraph
dependencyGraph e=SemanticGraph (dependencyExecutionId e) TraceView nodes edges
  "Focused dependency view: actual ports, conversions, generated slots and candidate availability. Full AST, eager read occurrences, sources and supports remain in projection.json; candidates are not imposed sentences."
 where
  p=dependencyPlan (checkedDocument (executionPlan e))
  componentId key=case M.lookup key (checkedComponents (executionPlan e)) of
    Just c->componentObjectKey (planIdentity p) c "component" key
    Nothing->qualifiedIdentity [planIdentity p,"invalid-component",key]
  convertId key=qualifiedIdentity [planIdentity p,"conversion",key]
  candidateId key=case [x | x<-executionCandidates e,candidateIdentity (availabilityCandidate x)==key] of
    [x]->conversionDestination (availabilityGuard x)
    _->qualifiedIdentity [planIdentity p,"invalid-candidate",key]
  allConversions=executionConversions e++map availabilityGuard (executionCandidates e)
  ports=M.elems (M.fromList [(observationIdentity v,v) | c<-allConversions,let v=conversionSource c])
  boundary s=Just (scopeActor s<>" / "<>scopeContext s<>maybe "" (" / "<>) (scopeAllegation s)<>" / occurrence "<>scopeIdentity s)
  componentNodes=[GraphNode (componentId (executionComponent c)) "component"
      (executionComponent c<>" | "<>executionState c<>componentSummary c) Nothing Nothing (boundary (executionScope c)) | c<-executionComponents e]
  portNodes=[(GraphNode (observationIdentity v) (if observationValue v==Nothing then "unavailable_port" else "observation")
      (portComponent (observationPort v)<>" / "<>portObject (observationPort v)<>" | "<>portCategory (observationPort v)
        <>" | "<>observationState v<>" | "<>valueText (observationValue v)) Nothing (fmap (valueText . Just) (observationValue v)) (boundary (observationScope v)))
      {graphNodeObservation=Just (CoreObservation (if observationValue v==Nothing then "not_evaluated" else "evaluated")
        (fmap (valueText . Just) (observationValue v)) Nothing
        (if observationValue v==Nothing then Just (T.intercalate "; " (observationCauses v)) else Nothing))} | v<-ports]
  conversionNodes=[GraphNode (convertId (conversionIdentity c)) "conversion"
      (conversionIdentity c<>" | "<>conversionPolicy c<>" | "<>valueText (conversionValue c)
        <>if any (T.isPrefixOf "conflict:") (conversionCauses c) then " | conflict origin retained" else "")
      (Just (conversionRationale c)) Nothing (boundary (observationScope (conversionSource c))) | c<-allConversions]
  slotNodes=[(GraphNode (conversionDestination c) "condition_slot"
      (bindingComponent b<>" / "<>bindingSlot b<>" | converted condition "<>valueText (conversionValue c)
        <>if applied b then " | applied runtime input" else " | not applied: destination not evaluated") Nothing
      (if applied b then fmap (valueText . Just) (conversionValue c) else Nothing) (boundary (observationScope (conversionSource c))))
      {graphNodeObservation=Just (CoreObservation (if applied b then "evaluated" else "not_evaluated")
        (if applied b then fmap (valueText . Just) (conversionValue c) else Nothing) Nothing
        (if applied b then Nothing else Just "destination blocked; no generated backend fact applied"))}
      | c<-executionConversions e,b<-planBindings p,bindingIdentity b==conversionIdentity c]
  applied b=any (\c->executionComponent c==bindingComponent b && executionState c=="evaluated") (executionComponents e)
  candidateNodes=[GraphNode (candidateId (candidateIdentity c)) "candidate"
      (candidateIdentity c<>" | "<>candidateModality c<>" | "<>availabilityText (availabilityState record)
        <>" | "<>termSummary (termValue (candidateTerm c))<>" | authored candidate only") Nothing Nothing (boundary (observationScope (conversionSource (availabilityGuard record))))
      | record<-executionCandidates e,let c=availabilityCandidate record]
  nodes=componentNodes++portNodes++conversionNodes++slotNodes++candidateNodes
  edges=[GraphEdge (componentId (portComponent (observationPort v))) (observationIdentity v) (if observationValue v==Nothing then "blocked_port" else "produces") (if observationValue v==Nothing then "port unavailable; component not evaluated" else "actual selected port") | v<-ports]
    ++[GraphEdge (observationIdentity (conversionSource c)) (convertId (conversionIdentity c)) "converts" "explicit policy" | c<-allConversions]
    ++concat [[GraphEdge (convertId (conversionIdentity c)) (conversionDestination c) "supplies" "execution-only input"
      ,GraphEdge (conversionDestination c) (componentId (bindingComponent b)) (if applied b then "consumed_by" else "required_by") (if applied b then "required slot applied" else "not applied: destination not evaluated")]
      | c<-executionConversions e,b<-planBindings p,bindingIdentity b==conversionIdentity c]
    ++[GraphEdge (convertId (candidateIdentity (availabilityCandidate c))) (candidateId (candidateIdentity (availabilityCandidate c))) "guards" "technical availability" | c<-executionCandidates e]

valueText :: Maybe TechnicalValue -> Text
valueText (Just Satisfied)="satisfied"
valueText (Just NotSatisfied)="not_satisfied"
valueText (Just Unresolved)="unresolved"
valueText Nothing="not_evaluated"
availabilityText :: CandidateAvailability -> Text
availabilityText Eligible="eligible"
availabilityText Ineligible="ineligible"
availabilityText (EligibilityUnresolved _)="eligibility unresolved"
availabilityText (NotEvaluated _)="guard not evaluated"

-- Included and omitted partition the declared focused-view domain. Every
-- omitted eager read still has a real record in report.components[].reads.
dependencyViewBindings :: DependencyExecution -> A.Value
dependencyViewBindings e=A.object ["format" A..= ("yuho.dependency-view-bindings/v0.1-experimental"::Text)
  ,"projection" A..= projectionFormat,"execution" A..= dependencyExecutionId e
  ,"included" A..= [A.object ["semantic_id" A..= graphNodeId n,"category" A..= graphNodeKind n
     ,"record" A..= nodeRecord (graphNodeId n)] | n<-semanticGraphNodes graph]
  ,"edges" A..= [A.object ["identity" A..= qualifiedIdentity [graphEdgeFrom x,graphEdgeTo x,graphEdgeKind x]
     ,"from" A..= graphEdgeFrom x,"to" A..= graphEdgeTo x,"relationship" A..= graphEdgeKind x] | x<-semanticGraphEdges graph]
  ,"omitted" A..= [v | c<-executionComponents e,r<-executionReads c,Just v<-[field "identity" r]]
  ,"domain" A..= ("focused semantic records plus all eager evaluation read occurrences; original checked source/AST and complete backend records are retained separately"::Text)]
 where
  graph=dependencyGraph e
  p=dependencyPlan (checkedDocument (executionPlan e))
  allConversions=executionConversions e++map availabilityGuard (executionCandidates e)
  nodeRecord key=case [A.object ["kind" A..= ("component"::Text),"scope" A..= executionScope c,"snapshot" A..= executionSnapshot c,"record" A..= c]
       | c<-executionComponents e,Just template<-[M.lookup (executionComponent c) (checkedComponents (executionPlan e))],key==componentObjectKey (planIdentity p) template "component" (executionComponent c)]
      ++[A.object ["kind" A..= (if observationValue v==Nothing then "unavailable_port" else "observation"::Text),"scope" A..= observationScope v,"snapshot" A..= observationSnapshot v,"record" A..= v]
       | x<-allConversions,let v=conversionSource x,key==observationIdentity v]
      ++[A.object ["kind" A..= ("conversion"::Text),"scope" A..= observationScope (conversionSource x),"snapshot" A..= observationSnapshot (conversionSource x),"record" A..= x]
       | x<-allConversions,key==qualifiedIdentity [planIdentity p,"conversion",conversionIdentity x]]
      ++[A.object ["kind" A..= ("condition_slot"::Text),"scope" A..= executionScope c
         ,"snapshot" A..= executionSnapshot c,"template_snapshot" A..= executionTemplate c,"record" A..= x]
       | x<-executionConversions e,key==conversionDestination x,b<-planBindings p,bindingIdentity b==conversionIdentity x
       ,c<-executionComponents e,executionComponent c==bindingComponent b]
      ++[A.object ["kind" A..= ("candidate"::Text),"scope" A..= observationScope (conversionSource (availabilityGuard c)),"record" A..= c]
       | c<-executionCandidates e,key==conversionDestination (availabilityGuard c)] of
    x:_->x
    []->A.Null
  field k (A.Object o)=AM.lookup k o
  field _ _=Nothing

exportDependencyPlan :: DependencyExecution -> Either DependencyDiagnostic [(FilePath,BS.ByteString)]
exportDependencyPlan e=do
  projection<-projectDependencyPlan e
  xml<-either (failure "DEPOBSERVATION" []) Right (encodeNativeSemanticGraphXml graph)
  let files=[("artifact.json",encodeDependencyArtifact (saveDependencyArtifact e)),("report.json",encode (reportDependencyPlan e))
        ,("projection.json",encode projection),("view-bindings.json",encode (dependencyViewBindings e))
        ,("view.json",encodeNativeSemanticGraph graph),("view.xml",xml),("view.svg",encodeNativeSvg graph)
        ,("source-map.json",encode (sourceMapDependencyPlan e))]
  ensure "DEPLIMIT" [] "complete encoded export exceeds 32 MiB" (sum (map (BS.length . snd) files)<=33554432)
  pure files
 where graph=dependencyGraph e


validateDependencyViewBindings :: DependencyExecution -> A.Value -> Either DependencyDiagnostic ()
validateDependencyViewBindings e submitted=ensure "DEPOBSERVATION" []
  "view binding differs from the authoritative category/scope/snapshot/endpoint correspondence"
  (submitted==dependencyViewBindings e)

validateDependencyProjection :: DependencyExecution -> A.Value -> Either DependencyDiagnostic ()
validateDependencyProjection e submitted=do
  expected<-projectDependencyPlan e
  ensure "DEPOBSERVATION" [] "projection differs from the authoritative execution/source record" (submitted==expected)


-- Presentation reads actual versioned records; it does not calculate truth or
-- choose a candidate term child. Full records remain authoritative.
componentSummary :: ComponentRecord -> Text
componentSummary c
  | null (executionIncoming c) || executionState c/="evaluated" = ""
  | otherwise = " | model expressions: "<>T.intercalate "; "
      [textField "id" r<>"="<>textField "status" r | r<-arrayField "expressions" (executionBackend c)]

textField :: Data.Aeson.Key.Key -> A.Value -> Text
textField key (A.Object obj)=case AM.lookup key obj of Just (A.String t)->t;_->""
textField _ _=""
arrayField :: Data.Aeson.Key.Key -> A.Value -> [A.Value]
arrayField key (A.Object obj)=case AM.lookup key obj of Just (A.Array xs)->foldr (:) [] xs;_->[]
arrayField _ _=[]
termSummary :: A.Value -> Text
termSummary value=case textField "kind" value of
  "life_imprisonment"->"life imprisonment"
  "death"->"death"
  "fine"->"fine "<>textField "currency" value<>bounds
  "caning"->"caning"<>bounds
  "term_imprisonment"->"term imprisonment "<>textField "unit" value<>bounds
  kind->kind<>"("<>T.intercalate "; " (map termSummary (arrayField "terms" value))<>")"
 where
  bounds=" [minimum "<>endpoint "minimum"<>", maximum "<>endpoint "maximum"<>"]"
  endpoint key=case value of
    A.Object obj->case AM.lookup key obj of
      Just e->case textField "kind" e of
        "not_stated"->"not stated";"unbounded"->"unbounded"
        _->case e of A.Object o->case AM.lookup "value" o of
                       Just (A.String t)->t
                       Just n->U.decodeUtf8 (encode n)
                       _->"invalid"
                     _->"invalid"
      _->"invalid"
    _->"invalid"
