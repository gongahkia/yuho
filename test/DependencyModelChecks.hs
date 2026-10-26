{-# LANGUAGE OverloadedStrings #-}
-- Internal finite engine/conversion conformance model. Not an authorable adapter.
module Main (main) where
import Control.Monad (unless)
import qualified Data.Aeson as A
import qualified Data.ByteString.Lazy.Char8 as BL
import qualified Data.Set as S
import Data.Text (Text)
import qualified Data.Text as T
import System.Environment (getArgs)
import Yuho.Dependency.Types
import Yuho.Dependency.Check
import Yuho.Dependency.Run
import Yuho.Dependency.Projection (dependencyGraph)
import Yuho.Diagram.Encode (encodeNativeSemanticGraph)
import qualified Data.Aeson.KeyMap as AM
import qualified Data.Aeson as JSON
import qualified Yuho.Authoring.Provenance as PV
import Yuho.Surface.Dependency (loadDependencyProject)

main :: IO ()
main=do
  args<-getArgs
  case args of
    [project]->do
      plan<-loadDependencyProject project >>= either (fail . show) pure
      execution<-either (fail . show) pure (executePlanModel (S.singleton "gate:a") plan)
      let blocked=[c | c<-executionComponents execution,executionState c=="not_evaluated"]
      unless (map executionComponent blocked==["gate:a","receipt:a"] && all (\c->null (executionReads c) && executionBackend c==A.Null) blocked)
        (fail "unavailable source was conflated with U/evaluated backend observation")
      unless (all (\c->observationBackendId (conversionSource c)==Nothing && conversionValue c==Nothing)
        [c | c<-executionConversions execution,portComponent (observationPort (conversionSource c))=="gate:a"])
        (fail "blocked model fabricated an actual backend observation")
      let cand=[c | c<-executionCandidates execution,candidateIdentity (availabilityCandidate c)=="cand:a"]
      case cand of
        [c]->case availabilityState c of
          NotEvaluated _->pure ()
          _->fail "skipped guard availability collapsed"
        _->fail "candidate missing"
      case JSON.eitherDecodeStrict' (encodeNativeSemanticGraph (dependencyGraph execution)) of
        Right (A.Object view)->case AM.lookup "nodes" view of
          Just (A.Array nodes)->do
            let unavailable=[n | A.Object n<-foldr (:) [] nodes,AM.lookup "kind" n==Just (A.String "unavailable_port")]
            unless (not (null unavailable) && all (\n->AM.lookup "status" n==Nothing &&
                case AM.lookup "observation" n of
                  Just (A.Object o)->AM.lookup "evaluation" o==Just (A.String "not_evaluated")
                    && AM.lookup "technical_value" o==Nothing
                    && AM.member "skip_reason" o
                  _->False) unavailable)
              (fail "unavailable graph port fabricated a technical value")
          _->fail "sealed model view omitted nodes"
        _->fail "sealed model view was not structured"
      projection<-either (fail . show) pure (PV.projectTypedProvenance execution)
      let authorityComponent n=case PV.authority n of
            A.Object o->AM.lookup "component" o
            _->Nothing
          isBlocked n=authorityComponent n `elem` map (Just . A.String) ["gate:a","receipt:a"]
          fabricated n=isBlocked n && PV.category n `elem` ["evaluation_read","expression_observation","rule_observation","proposition_observation","generated_condition_input"]
      unless (not (any fabricated (PV.nodes projection))) (fail "complete provenance fabricated blocked execution")
      unless (any (\n->PV.category n=="unavailable_port" && PV.state n==Nothing) (PV.nodes projection))
        (fail "complete provenance lost unavailable ports")
      pure ()
    _->fail "expected a checked two-scope model for the sealed unavailable control"
  values<-traverse vector vectors
  BL.putStrLn (A.encode values)
 where
  scope=PlanScope "engine:scope" "actor:a" "context:i" Nothing Nothing [("actor:a","person"),("context:i","event")]
  vectors=[("T","typed.expression.truth","evaluated",Just Satisfied,False)
    ,("F","typed.expression.truth","evaluated",Just NotSatisfied,False)
    ,("U","typed.expression.truth","evaluated",Just Unresolved,False)
    ,("P-established","typed.proposition.resolution","established",Just Satisfied,False)
    ,("P-defeated","typed.proposition.resolution","defeated",Just NotSatisfied,False)
    ,("P-not-established","typed.proposition.resolution","not_established",Just NotSatisfied,False)
    ,("P-unresolved","typed.proposition.resolution","unresolved",Just Unresolved,False)
    ,("P-conflict","typed.proposition.resolution","conflict",Just Unresolved,True)
    ,("unavailable","typed.expression.truth","not_evaluated",Nothing,False)]
  vector (key,category,state,value,conflict)=do
    let source=PortValue "sealed-vector-handle" (ObservationPort "engine-model" category "port:one") scope "sealed-model-snapshot"
          (if value==Nothing then Nothing else Just "port:one") value state A.Null ["conflict:sealed-opposing-supports" | conflict]
        policy=if category=="typed.expression.truth" then "yuho.condition-identity/v1" else "yuho.proposition-support/v1"
    record<-either (fail . show) pure (convert key source policy "Independent finite model vector, not authored source evidence" ["sealed-model"] "slot:one")
    pure (A.object ["id" A..= (key::Text),"value" A..= valueName (conversionValue record)
      ,"conflict" A..= any (T.isPrefixOf "conflict:") (conversionCauses record)
      ,"availability" A..= available (availability (conversionValue record) (conversionCauses record))])
  valueName (Just Satisfied)="satisfied"::Text
  valueName (Just NotSatisfied)="not_satisfied"
  valueName (Just Unresolved)="unresolved"
  valueName Nothing="not_evaluated"
  available Eligible="eligible"::Text
  available Ineligible="ineligible"
  available (EligibilityUnresolved _)="unresolved"
  available (NotEvaluated _)="not_evaluated"
