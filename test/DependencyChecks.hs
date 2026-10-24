{-# LANGUAGE OverloadedStrings #-}
module DependencyChecks (runDependencyChecks) where
import Control.Exception (bracket)
import System.Directory (getTemporaryDirectory,removeDirectoryRecursive)
import System.FilePath ((</>))
import System.Posix.Temp (mkdtemp)
import qualified Data.Aeson.KeyMap as AM
import Data.List (find)
import qualified Data.List
import qualified Data.Text
import Control.Monad (unless,forM_)
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as BL
import qualified Data.Map.Strict as M
import Data.Text (Text)
import qualified Data.Text.Encoding as U
import qualified Yuho.Authoring as SDK
import qualified Yuho.Authoring.Dependency as D
import Yuho.Protocol.Json (J(..),decodeJson,lookupField)
import qualified TypedExamples as Examples

runDependencyChecks :: IO ()
runDependencyChecks=do
  forM_ [(D.Satisfied,"not_satisfied"),(D.NotSatisfied,"satisfied"),(D.Unresolved,"unresolved")] $ \(value,expected)->do
    checked<-ok (D.checkDependencyPlan (document value))
    execution<-ok (D.executeDependencyPlan checked)
    report<-either (fail . show) pure (decodeJson (encode (D.reportDependencyPlan execution)))
    unless (destinationStatus report==Just (JStr expected)) (fail "independent in-memory template outcome mismatch")
    artifact<-ok (D.decodeDependencyArtifact (D.encodeDependencyArtifact (D.saveDependencyArtifact execution)))
    replay<-ok (D.replayDependencyPlan artifact)
    unless (D.dependencyExecutionId replay==D.dependencyExecutionId execution) (fail "immutable SDK replay changed execution")
    files<-ok (D.exportDependencyPlan execution)
    unless (length files==8 && all (not . BS.null . snd) files) (fail "SDK export set incomplete")
    temp<-getTemporaryDirectory
    bracket (mkdtemp (temp </> "yuho-dependency-sdk-")) removeDirectoryRecursive $ \folder->do
      D.publishDependencyPlan (folder </> "new") execution >>= ok
      D.publishDependencyPlan (folder </> "new") execution >>= refuse "DEPPUBLISH"
      retained<-BS.readFile (folder </> "new/artifact.json") >>= ok . D.decodeDependencyArtifact
      _<-ok (D.replayDependencyPlan retained)
      pure ()
    let bindings=D.dependencyViewBindings execution
    case bindings of
      A.Object object->case AM.lookup "included" object of
        Just (A.Array rows)->case foldr (:) [] rows of
          A.Object a:A.Object b:rest->do
            let wrong=A.Object (AM.insert "included" (A.toJSON (A.Object (AM.insert "record" (maybe A.Null id (AM.lookup "record" b)) a):A.Object b:rest)) object)
            refuse "DEPOBSERVATION" (D.validateDependencyViewBindings execution wrong)
          _->fail "view did not expose independently testable bindings"
        _->fail "view bindings missing"
      _->fail "view binding object missing"
    let bad=(document value) {D.dependencyPlan=(D.dependencyPlan (document value)) {D.planBindings=[binding,binding {D.bindingIdentity="same-value-other-writer"}]}}
    refuse "DEPWRITER" (D.checkDependencyPlan bad)
    let missing=(document value) {D.dependencyPlan=(D.dependencyPlan (document value)) {D.planBindings=[]}}
    refuse "DEPMISSING" (D.checkDependencyPlan missing)
    let wrong=(document value) {D.dependencyPlan=(D.dependencyPlan (document value)) {D.planBindings=[binding {D.bindingPolicy="yuho.technical-status-to-proof/v1"}]}}
    refuse "DEPPOLICY" (D.checkDependencyPlan wrong)
  sdk<-either (fail . show) pure Examples.permissionDocument
  let bytes=SDK.encodeTypedDocument sdk
      scope=D.PlanScope "sdk-scope" "person:ada" "context:access" Nothing Nothing [("person:ada","role:person"),("context:access","role:context")]
      component=D.PlanComponent "sdk-producer" "sdk-typed-v0.3" "permission.json" Nothing (Just ("analysis","analysis:ada")) "sdk-scope"
        [("actor","role:person")] [("actor:ada","person:ada")] "Explicit selected SDK analysis scope, preserving its actual context" Nothing Nothing
      candidate=D.PlanCandidate "permission-candidate" "sdk-scope" (D.ObservationPort "sdk-producer" "typed.expression.truth" "q:ada")
        "yuho.condition-identity/v1" "unspecified" "Synthetic candidate only" ["origin"] (D.DataTerm lifeTerm) Nothing
      doc=D.DependencyDocument D.planFormat (D.DependencyPlan "sdk-plan" [D.SourceOrigin "origin" "urn:fictional-sdk-control"] [scope] [component] [] [candidate])
        (M.singleton "permission.json" (U.decodeUtf8 bytes)) Nothing
  checked<-ok (D.checkDependencyPlan doc)
  execution<-ok (D.executeDependencyPlan checked)
  json<-either (fail . show) pure (decodeJson (encode (D.reportDependencyPlan execution)))
  unless (lookupField "eligible_candidates" json==Just (JArr [JStr "permission-candidate"])) (fail "actual SDK producer port was not consumed")
  ref<-either (fail . show) pure Examples.caseReference
  (_,quote)<-ok (D.recoverDependencyReference execution "sdk-producer" ref)
  unless (quote==Just "Zoë permits Ada to read Server R.") (fail "SDK original UTF-8 quotation recovery changed")
  (_,locatorOnly)<-ok (D.recoverDependencyReference execution "sdk-producer" (SDK.SourceRef "source:cma" Nothing))
  unless (locatorOnly==Nothing) (fail "locator-only origin invented a quotation")
  refuse "DEPNAME" (D.recoverDependencyReference execution "unrelated-component" ref)
  case SDK.referenceSpan ref of
    Just spanValue->refuse "DEPFORMAT" (D.recoverDependencyReference execution "sdk-producer" ref {SDK.referenceSpan=Just spanValue {SDK.start=3}})
    Nothing->fail "independent source anchor missing"
  -- Real executions with formerly ambiguous pairs, distinct values, and
  -- Unicode/long IDs. Oracles compare tuples, not the key helper's output.
  let original=document D.Satisfied
      p=D.dependencyPlan original
  supplier<-maybe (fail "missing independently authored supplier") pure (find ((=="supplier") . D.componentIdentity) (D.planComponents p))
  template<-maybe (fail "supplier is not an in-memory template") pure (D.componentTemplate supplier)
  let declarations=[("a","b--c",D.Satisfied),("a--b","c",D.NotSatisfied),("λ長識別子","觀察:"<>Data.Text.replicate 80 "λ",D.Unresolved)]
      collisionComponent (owner,object,value)=supplier {D.componentIdentity=owner,D.componentTemplate=Just template
        {D.templateRequirements=[(object,D.TemplateAtom "own" ["person:a","event:i"])],D.templateFacts=[("own",["person:a","event:i"],value,"Independent collision control")]}}
      consequence (owner,object,_)=D.PlanCandidate ("candidate:"<>owner) "occurrence:one" (D.ObservationPort owner "typed.expression.truth" object)
        "yuho.condition-identity/v1" "unspecified" "Independent tuple/status control" ["origin"] (D.DataTerm lifeTerm) Nothing
      collision=original {D.dependencyPlan=p {D.planComponents=map collisionComponent declarations,D.planBindings=[],D.planCandidates=map consequence declarations}}
  collisionPlan<-ok (D.checkDependencyPlan collision)
  collisionExecution<-ok (D.executeDependencyPlan collisionPlan)
  raw<-either (fail . show) pure (decodeJson (encode (D.reportDependencyPlan collisionExecution)))
  case lookupField "candidates" raw of
    Just (JArr records)->do
      let observations=[o | r<-records,Just guard<-[lookupField "availabilityGuard" r],Just o<-[lookupField "conversionSource" guard]]
          tuples=[(owner,object,value) | o<-observations,Just port<-[lookupField "observationPort" o]
            ,Just (JStr owner)<-[lookupField "portComponent" port],Just (JStr object)<-[lookupField "portObject" port]
            ,Just (JStr value)<-[lookupField "observationValue" o]]
      unless (all (`elem` tuples) [("a","b--c","Satisfied"),("a--b","c","NotSatisfied"),("λ長識別子","觀察:"<>Data.Text.replicate 80 "λ","Unresolved")])
        (fail "scoped pairs lost identity or inherited another value")
      let ids=[i | o<-observations,Just (JStr i)<-[lookupField "observationIdentity" o]]
      unless (length ids==3 && length (Data.List.nub ids)==3) (fail "actual scoped observations collided")
    _->fail "collision control lost candidates"
  -- The new artifact decoder is closed and detects duplicate JSON keys.
  let encoded=D.encodeDependencyDocument (document D.Satisfied)
  refuse "DEPFORMAT" (D.decodeDependencyDocument (BS.init encoded<> ",\"unexpected\":true}"))
  refuse "DEPFORMAT" (D.decodeDependencyDocument "{\"dependencyFormat\":\"x\",\"dependencyFormat\":\"y\"}")
  unless (D.qualifiedIdentity ["a","b--c"]/=D.qualifiedIdentity ["a--b","c"]
    && D.qualifiedIdentity ["λ","規則"]/=D.qualifiedIdentity ["λ規","則"]) (fail "tuple identity collision")
  putStrLn "checked dependencies: independent SDK templates, T/F/U, writer/readiness/refusals, real SDK producer, replay and source identities passed"
 where encode=BL.toStrict . A.encode

-- This entire expectation is authored independently of the new checker/encoder.
destinationStatus :: J -> Maybe J
destinationStatus report=do
  JArr cs<-lookupField "components" report
  c<-one [x | x<-cs,lookupField "executionComponent" x==Just (JStr "downstream")]
  backend<-lookupField "executionBackend" c
  JArr qs<-lookupField "expressions" backend
  q<-one [x | x<-qs,lookupField "id" x==Just (JStr "q:answer")]
  lookupField "status" q
 where one [x]=Just x;one _=Nothing

document :: D.TechnicalValue -> D.DependencyDocument
document value=D.DependencyDocument D.planFormat (D.DependencyPlan "in-memory" [D.SourceOrigin "origin" "urn:fictional:technical-support"]
  [scope] [component "supplier" supplier,component "downstream" downstream] [binding] []) M.empty Nothing
 where
  scope=D.PlanScope "occurrence:one" "person:a" "event:i" Nothing Nothing [("person:a","role:person"),("event:i","role:event")]
  component key t=D.PlanComponent key "native-typed" "" Nothing Nothing "occurrence:one" [("person","role:person"),("event","role:event")]
    [("person:a","person:a"),("event:i","event:i")] "Explicit fictional actor and incident identity" (Just t) Nothing
  base=D.TechnicalTemplate "in-memory-template" ["person","event"] [("person:a","person"),("event:i","event")]
    [("own",["person","event"])] [] [] [] [] [("own",["person:a","event:i"],value,"independently supplied primitive")] ["Fictional control, not legal proof"]
  supplier=base {D.templateRequirements=[("q:source",D.TemplateAtom "own" ["person:a","event:i"])]}
  downstream=base {D.templateConditions=["in:qualification"],D.templateFacts=[("own",["person:a","event:i"],D.Satisfied,"independent local criterion")]
    ,D.templateRequirements=[("q:answer",D.TemplateAll [D.TemplateAtom "own" ["person:a","event:i"],D.TemplateNot (D.TemplateCondition "in:qualification")])]
    ,D.templatePropositions=["p:answer"],D.templateRules=[("r:answer","p:answer","q:answer")]}

binding :: D.PlanBinding
binding=D.PlanBinding "binding:qualification" (D.ObservationPort "supplier" "typed.expression.truth" "q:source") "downstream" "in:qualification"
  "yuho.condition-identity/v1" "Technical condition only, no proof assessment" ["origin"] Nothing

lifeTerm :: A.Value
lifeTerm=A.object ["kind" A..= ("life_imprisonment"::Text),"term_id" A..= ("term:life"::Text),"span" A..= A.object
  ["start" A..= (0::Int),"end" A..= (0::Int),"start_line" A..= (1::Int),"start_col" A..= (1::Int),"end_line" A..= (1::Int),"end_col" A..= (1::Int)]]

ok :: Show e => Either e a -> IO a
ok=either (fail . show) pure
refuse :: Text -> Either D.DependencyDiagnostic a -> IO ()
refuse code (Left d)=unless (D.dependencyCode d==code) (fail (show d))
refuse code (Right _)=fail ("expected refusal "<>show code)
