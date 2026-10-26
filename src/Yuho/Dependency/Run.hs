{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Yuho.Dependency.Run where

import Control.Monad (foldM)
import qualified Data.ByteString
import qualified Data.Text
import qualified Data.Aeson.KeyMap as AM
import qualified Data.Aeson.KeyMap
import qualified Data.Aeson as A
import qualified Data.Aeson.Types as AT
import qualified Data.Aeson.Key
import qualified Data.Text.Encoding
import qualified Yuho.Protocol.Decode
import Data.List (nub, sort, isPrefixOf)
import qualified Data.Map.Strict as M
import qualified Data.Set as S
import Prelude hiding (reads)
import Data.Text (Text)
import qualified Yuho.CoreYuho.TypedFinite as K
import Yuho.ScopedDefinitions.Types
import qualified Yuho.Quantitative as Q
import Yuho.Dependency.Types
import Yuho.Dependency.Check
import qualified Yuho.Protocol.Json as J
import Yuho.Protocol.Decode (inputDigest)
import Yuho.Surface.TypedFinite (encodeTypedFiniteRequest)
import Yuho.TypedFiniteRules.Run (decodeTypedFiniteRequest, encodeTypedFiniteResult)
import GHC.Generics (Generic)

data PortValue = PortValue
  { observationIdentity :: Text, observationPort :: ObservationPort, observationScope :: PlanScope
  , observationSnapshot :: Text, observationBackendId :: Maybe Text, observationValue :: Maybe TechnicalValue
  , observationState :: Text, observationRecord :: A.Value, observationCauses :: [Text]
  } deriving (Eq,Show,Generic)
instance A.ToJSON PortValue

data ConversionRecord = ConversionRecord
  { conversionIdentity :: Text, conversionSource :: PortValue, conversionPolicy :: Text
  , conversionRationale :: Text, conversionReferences :: [Text], conversionDestination :: Text
  , conversionValue :: Maybe TechnicalValue, conversionCauses :: [Text]
  , conversionGeneratedInput :: A.Value } deriving (Eq,Show,Generic)
instance A.ToJSON ConversionRecord

data ComponentRecord = ComponentRecord
  { executionComponent :: Text, executionScope :: PlanScope, executionLocalScope :: A.Value
  , executionTemplate :: Text, executionSnapshot :: Text, executionState :: Text
  , executionBlockedBy :: [Text], executionIncoming :: [ConversionRecord]
  , executionRequest :: A.Value, executionBackend :: A.Value, executionReads :: [A.Value]
  , executionMappings :: A.Value, executionQuantitative :: Maybe Q.QExecution } deriving (Eq,Show,Generic)
instance A.ToJSON ComponentRecord where
  toJSON c=case A.genericToJSON A.defaultOptions c of
    A.Object o->A.Object (case executionQuantitative c of
      Nothing->AM.delete "executionQuantitative" o
      Just q->AM.insert "quantitative" (A.toJSON q) (AM.delete "executionQuantitative" o))
    v->v

data CandidateAvailability = Eligible | Ineligible | EligibilityUnresolved [Text] | NotEvaluated [Text]
  deriving (Eq,Show,Generic)
instance A.ToJSON CandidateAvailability

data CandidateRecord = CandidateRecord
  { availabilityCandidate :: PlanCandidate, availabilityGuard :: ConversionRecord
  , availabilityState :: CandidateAvailability } deriving (Eq,Show,Generic)
instance A.ToJSON CandidateRecord

data DependencyExecution = DependencyExecution
  { executionPlan :: CheckedPlan, executionComponents :: [ComponentRecord]
  , executionConversions :: [ConversionRecord], executionCandidates :: [CandidateRecord]
  , dependencyExecutionId :: Text } deriving (Eq,Show)

reportDependencyPlan :: DependencyExecution -> A.Value
reportDependencyPlan e=A.object
  (["format" A..= reportFormat,"execution" A..= dependencyExecutionId e
  ,"plan_snapshot" A..= checkedDigest (executionPlan e),"order" A..= checkedOrder (executionPlan e)
  ,"components" A..= executionComponents e,"bindings" A..= executionConversions e
  ,"candidates" A..= executionCandidates e
  ,"eligible_candidates" A..= [candidateIdentity (availabilityCandidate c) | c<-executionCandidates e,availabilityState c==Eligible]
  ,"notice" A..= ("Technical authored candidates only; no imposed sentence, proof sufficiency or judicial finding."::Text)] ++ scopedEvidenceFields e
  ++ ["quantitative" A..= quantitativeEvidence e | any ((/=Nothing) . checkedQuantitative) (M.elems (checkedComponents (executionPlan e)))])

quantitativeEvidence :: DependencyExecution -> A.Value
quantitativeEvidence e=A.object ["format" A..= Q.quantitativeFormat
  ,"occurrences" A..= [A.object ["component" A..= executionComponent r,"scope" A..= executionScope r
      ,"snapshot" A..= executionSnapshot r,"evaluation" A..= executionState r
      ,"checked_plan" A..= q,"actual" A..= executionQuantitative r]
    | r<-executionComponents e,Just c<-[M.lookup (executionComponent r) (checkedComponents (executionPlan e))]
    ,Just q<-[checkedQuantitative c]]]

-- | The only production entry. Unavailable typed sources cannot be authored.
executeDependencyPlan :: CheckedPlan -> Either DependencyDiagnostic DependencyExecution
executeDependencyPlan=executePlanModel S.empty

-- | Internal finite-engine test seam: explicitly blocked components, never a
-- fabricated typed backend skip observation. Not exported by Authoring facade.
executePlanModel :: S.Set Text -> CheckedPlan -> Either DependencyDiagnostic DependencyExecution
executePlanModel blocked plan=do
  (records,results,conversions)<-foldM step (M.empty,M.empty,[]) (checkedOrder plan)
  candidates<-traverse (candidate records results conversions) (sortOnId (planCandidates p))
  let ordered=[records M.! i | i<-checkedOrder plan]
      -- New typed read records are a deterministic refinement of the retained
      -- request/read occurrence. Exclude only those additive fields from the
      -- legacy execution digest; unchanged v0.1 saved executions still replay.
      -- Corrected values/causes continue to change the digest and refuse unsafe
      -- old executions. No caller-supplied read record is trusted on replay.
      digestComponent c=c {executionReads=map legacyRead (executionReads c)}
      legacyRead (A.Object x)=A.Object (Data.Aeson.KeyMap.delete "input_records" x)
      legacyRead x=x
      identity=hash (checkedDigest plan,map digestComponent ordered,conversions,candidates)
  pure (DependencyExecution plan ordered conversions candidates identity)
  where
    p=dependencyPlan (checkedDocument plan)
    sortOnId cs=map snd (M.toAscList (M.fromList [(candidateIdentity c,c) | c<-cs]))
    component key=maybe (failure "DEPOBSERVATION" [key] "checked component disappeared") Right (M.lookup key (checkedComponents plan))
    step (records,results,conversions) key=do
      c<-component key
      rawIncoming<-traverse (binding records results) (map snd (M.toAscList (M.fromList
        [(bindingIdentity b,b) | b<-planBindings p,bindingComponent b==key])))
      unique "runtime generated-input handle" (map generatedReason rawIncoming)
      let unavailable=[conversionIdentity x | x<-rawIncoming,conversionValue x==Nothing]
          applied=not (key `S.member` blocked) && null unavailable
          mark x=x {conversionGeneratedInput=case conversionGeneratedInput x of
            A.Object object->A.Object (AM.insert "application_state" (A.String (if applied then "applied" else "not_applied")) object)
            value->value}
          incoming=map mark rawIncoming
          template=checkedTemplateDigest c
          snapshot=hash (template,incoming,"yuho.dependency-lowering/v1"::Text)
          common state why req backend reads=ComponentRecord key (checkedScope c) (A.toJSON (checkedLocalScope c))
            template snapshot state why incoming req backend reads (checkedMappings c) Nothing
      if key `S.member` blocked || not (null unavailable) then
        let record=common "not_evaluated" (if key `S.member` blocked then ["sealed engine model: unavailable component"] else unavailable) A.Null A.Null []
        in pure (M.insert key record records,results,conversions++incoming)
      else do
        let original=checkedProgram c
            replacements=M.fromList [(predicate,conversion) | conversion<-incoming
              , Just predicate<-[lookup (destinationSlot conversion) (checkedSlots c)]]
            destinationSlot x=case [bindingSlot b | b<-planBindings p,bindingIdentity b==conversionIdentity x] of [s]->s; _->""
            lower f=case M.lookup (K.groundPredicate f) replacements of
              Nothing->f
              Just conversion->f {K.groundStatus=maybe (K.groundStatus f) valueTruth (conversionValue conversion)
                ,K.groundReason=generatedReason conversion}
            supplied=original {K.finiteFacts=map lower (K.finiteFacts original)}
        (program,quantitative)<-case checkedQuantitative c of
          Nothing->pure (supplied,Nothing)
          Just qp->case Q.executeQuantitative supplied qp of
            Right (computed,q)->pure (computed,Just q)
            Left d->failure (Q.qFailureCode d) [key,maybe "" id (Q.qFailureOutput d)] (Q.qFailureMessage d)
        let bytes=encodeTypedFiniteRequest "DEPENDENCY-RUN" program
        wire<-either (failure "DEPOBSERVATION" [key]) Right (J.decodeJson bytes)
        validated<-either (failure "DEPOBSERVATION" [key]) Right (decodeTypedFiniteRequest wire)
        (result,reads)<-either (failure "DEPOBSERVATION" [key]) Right (K.evaluateTypedFiniteObserved validated)
        ensure "DEPLIMIT" [key] "actual read ledger exceeds the checked expansion budget" (toInteger (length reads)<=checkedCost plan)
        backend<-jsonBytes (encodeTypedFiniteResult "DEPENDENCY-RUN" (inputDigest wire) result)
        request<-jsonBytes bytes
        let actualSnapshot=hash (template,incoming,request,"yuho.dependency-lowering/v1"::Text)
            record=(common "evaluated" [] request backend (map (readJson key actualSnapshot) reads))
              {executionSnapshot=actualSnapshot,executionQuantitative=quantitative}
        pure (M.insert key record records,M.insert key (result,reads) results,conversions++incoming)
    binding records results b=do
      source<-resolvePort plan records results (bindingPort b)
      dest<-component (bindingComponent b)
      let destKey=componentObjectKey (planIdentity p) dest "technical.condition.slot" (bindingSlot b)
      record<-convert (bindingIdentity b) source (bindingPolicy b) (bindingRationale b) (bindingReferences b) destKey
      predicate<-maybe (failure "DEPOBSERVATION" [bindingSlot b] "checked slot disappeared") Right (lookup (bindingSlot b) (checkedSlots dest))
      pure record {conversionGeneratedInput=A.object
        ["origin" A..= ("execution-generated technical input; not an authored assessment"::Text)
        ,"binding" A..= bindingIdentity b,"predicate" A..= predicate,"arguments" A..= (["dep_template_entity"]::[Text])
        ,"reason" A..= generatedReason record,"technical_value" A..= conversionValue record
        ,"source_observation" A..= observationIdentity source]}
    candidate records results _ c=do
      source<-resolvePort plan records results (candidateGuard c)
      guard<-convert (candidateIdentity c) source (candidatePolicy c) (candidateRationale c) (candidateReferences c)
        (candidateObjectKey (planIdentity p) (observationScope source) (candidateIdentity c))
      pure (CandidateRecord c guard (availability (conversionValue guard) (conversionCauses guard)))

resolvePort :: CheckedPlan -> M.Map Text ComponentRecord -> M.Map Text (K.TypedFiniteResult,[K.FiniteRead])
  -> ObservationPort -> Either DependencyDiagnostic PortValue
resolvePort plan records results port=do
  c<-maybe (failure "DEPOBSERVATION" [portComponent port] "component absent") Right (M.lookup (portComponent port) (checkedComponents plan))
  record<-maybe (failure "DEPOBSERVATION" [portComponent port] "port requested before producing component") Right (M.lookup (portComponent port) records)
  checkPort c port
  let scope=checkedScope c
      key=componentObjectKey (planIdentity (dependencyPlan (checkedDocument plan))) c (portCategory port) (portObject port)
      handle=qualifiedIdentity [key,executionSnapshot record,portObject port]
      ancestryFor ledger result=sort (nub (concatMap conversionCauses used))
        where
          ruleIds=[K.observedRule r | r<-K.finiteResultRules result,K.observedProposition r==portObject port]
          relevant r=case K.readRoot r of
            ["expression",i]->portCategory port=="typed.expression.truth" && i==portObject port
            "rule":i:_->portCategory port=="typed.proposition.resolution" && i `elem` ruleIds
            _->False
          directInputs=concatMap K.readInputs (filter relevant ledger)
          inputs=directInputs++case executionQuantitative record of
            Nothing->[]
            Just q->Q.quantitativeInputs q [i | K.ScalarInput i<-directInputs]
          used=[conversion | conversion<-executionIncoming record
            ,b<-planBindings (dependencyPlan (checkedDocument plan)),bindingIdentity b==conversionIdentity conversion
            ,Just predicate<-[lookup (bindingSlot b) (checkedSlots c)]
            ,K.GroundInput fact<-inputs
            ,K.groundIdentity (K.groundPredicate fact) (K.groundArguments fact)==K.groundIdentity predicate ["dep_template_entity"]]
      value v state row causes=PortValue handle port scope (executionSnapshot record) (if v==Nothing then Nothing else Just (portObject port)) v state row (sort (nub causes))
  if executionState record=="not_evaluated" then pure (value Nothing "not_evaluated" A.Null (executionBlockedBy record)) else do
    (result,ledger)<-maybe (failure "DEPOBSERVATION" [portObject port] "evaluated component has no authoritative result") Right (M.lookup (portComponent port) results)
    let ancestry=ancestryFor ledger result
    case portCategory port of
      "typed.expression.truth"->case [r | r<-K.finiteResultExpressions result,K.expressionLabel r==portObject port] of
        [r]->pure (value (Just (truthValue (K.expressionStatus r))) "evaluated" (A.object
          ["id" A..= K.expressionLabel r,"status" A..= K.truthName (K.expressionStatus r),"detail" A..= K.expressionDetail r])
          (ancestry++["unresolved:"<>handle | K.expressionStatus r==valueTruth Unresolved]))
        _->failure "DEPOBSERVATION" [portObject port] "missing/duplicate promised expression observation"
      "typed.proposition.resolution"->case [r | r<-K.finiteResultPropositions result,K.observedPropositionId r==portObject port] of
        [r]->do
          let state=K.propositionState r; v=truthValue (K.propositionStatus r)
          ensure "DEPOBSERVATION" [portObject port] "backend proposition state/status mismatch"
            ((state,v) `elem` [("established",Satisfied),("defeated",NotSatisfied),("not_established",NotSatisfied),("unresolved",Unresolved),("conflict",Unresolved)])
          pure (value (Just v) state (A.object ["id" A..= K.observedPropositionId r,"status" A..= K.truthName (K.propositionStatus r)
            ,"state" A..= state,"rules" A..= K.propositionRules r]) (ancestry++[state<>":"<>handle | state `elem` ["conflict","unresolved"]]))
        _->failure "DEPOBSERVATION" [portObject port] "missing/duplicate promised proposition observation"
      _->failure "DEPCATEGORY" [portObject port] "unsupported source observation category"

convert :: Text -> PortValue -> Text -> Text -> [Text] -> Text -> Either DependencyDiagnostic ConversionRecord
convert key source policy rationale refs dest=do
  checkPolicy (observationPort source) policy
  result<-case observationValue source of
    Nothing->pure Nothing
    Just value | policy=="yuho.proposition-support/v1" -> do
      mapped<-propositionSupport (observationState source)
      ensure "DEPOBSERVATION" [key] "resolved proposition mapping disagrees with authoritative backend status" (value==mapped)
      pure (Just mapped)
    value->pure value
  let generated=A.object ["origin" A..= ("execution-generated technical input; not an authored assessment"::Text)
        ,"binding" A..= key,"source_observation" A..= observationIdentity source,"technical_value" A..= result]
  pure (ConversionRecord key source policy rationale refs dest result (observationCauses source) generated)

availability :: Maybe TechnicalValue -> [Text] -> CandidateAvailability
availability (Just Satisfied) _=Eligible
availability (Just NotSatisfied) _=Ineligible
availability (Just Unresolved) causes=EligibilityUnresolved causes
availability Nothing causes=NotEvaluated causes

readJson :: Text -> Text -> K.FiniteRead -> A.Value
readJson component snapshot r=A.object
  ["identity" A..= qualifiedIdentity [component,snapshot,qualifiedIdentity (K.readRoot r),qualifiedIdentity (map (Data.Text.pack . show) (K.readPath r)),qualifiedIdentity (concatMap (\(a,b)->[a,b]) (K.readBindings r))]
  ,"root" A..= K.readRoot r,"path" A..= K.readPath r,"bindings" A..= K.readBindings r
  ,"operator" A..= K.readKind r,"status" A..= K.truthName (K.readStatus r),"detail" A..= K.readDetail r
  ,"actual_inputs" A..= map K.inputDisplay (K.readInputs r),"input_records" A..= map inputRecord (K.readInputs r),"evaluation" A..= ("evaluated"::Text)]

-- Versioned typed inputs are authoritative. actual_inputs retains legacy
-- display descriptions only; requirement/scalar names never become facts.
inputRecord :: K.FiniteInput -> A.Value
inputRecord input=A.object (("format" A..= ("yuho.typed-read-input/v1"::Text)):case input of
  K.GroundInput f->["kind" A..= ("ground_predicate"::Text),"predicate" A..= K.groundPredicate f
    ,"arguments" A..= K.groundArguments f,"classification" A..= A.object
      ["status" A..= K.truthName (K.groundStatus f),"reason" A..= K.groundReason f]]
  K.RequirementInput i->["kind" A..= ("requirement_reference"::Text),"requirement" A..= i]
  K.ScalarInput i->["kind" A..= ("scalar_operand"::Text),"scalar" A..= i])

jsonBytes :: Data.ByteString.ByteString -> Either DependencyDiagnostic A.Value
jsonBytes=either (failure "DEPFORMAT" [] . Data.Text.pack) Right . A.eitherDecodeStrict'

-- Backend reasons have a 128-character bound. The complete reversible semantic
-- key remains authoritative in the ledger; this digest is only its short handle.
generatedReason :: ConversionRecord -> Text
generatedReason c="dependency-input "<>hash (conversionIdentity c,conversionSource c,conversionPolicy c,conversionDestination c,conversionValue c)

propositionSupport :: Text -> Either DependencyDiagnostic TechnicalValue
propositionSupport "established"=Right Satisfied
propositionSupport "defeated"=Right NotSatisfied
propositionSupport "not_established"=Right NotSatisfied
propositionSupport "unresolved"=Right Unresolved
propositionSupport "conflict"=Right Unresolved
propositionSupport state=failure "DEPOBSERVATION" [state] "unsupported resolved proposition state"

-- | Opt-in refinement. No new field or digest change for historical documents.
scopedEvidenceFields :: DependencyExecution -> [AT.Pair]
scopedEvidenceFields e
  | null uses=[]
  | otherwise=["scoped_definitions" A..= scopedDefinitionEvidence e]
 where uses=concatMap (scopedUses . checkedScopedDefinitions) (M.elems (checkedComponents (executionPlan e)))

-- Definition keys are structural tuples; occurrences are sealed actual reads.
-- A scenario selection refers to exact authored sources, not an invented fact.
scopedDefinitionEvidence :: DependencyExecution -> A.Value
scopedDefinitionEvidence e=A.object
  ["format" A..= ("yuho.scoped-definitions/v0.1-experimental"::Text)
  ,"definitions" A..= M.elems (M.fromList [(definitionKey d,d) | c<-M.elems (checkedComponents plan),d<-scopedDefinitions (checkedScopedDefinitions c)])
  ,"uses" A..= [A.object ["identity" A..= uid,"declaration" A..= u,"component" A..= executionComponent record
      ,"scope" A..= executionScope record,"snapshot" A..= executionSnapshot record
      ,"definition_snapshot" A..= definitionSnapshot d
      ,"instantiation" A..= qualifiedIdentity [componentKey record "instantiation" (qualifiedIdentity (definitionKey d)),qualifiedIdentity (concatMap (\(a,b)->[a,b]) (useArguments u))]
      ,"selection" A..= A.object ["scenario" A..= useScenario u,"source" A..= useScenarioSource u
        ,"sha256" A..= fmap (hashSource) (M.lookup (useScenarioSource u) (dependencySources doc))
        ,"policy" A..= useAssessmentPolicy u]
      ,"occurrences" A..= [A.object ["identity" A..= qualifiedIdentity [uid,rid],"read" A..= r
            ,"selected_inputs" A..= groundInputs record r
            ,"selected_assessments" A..= selectedAssessments record u r] | r<-executionReads record,selectedRead (useIdentity u) r,Just (A.String rid)<-[fieldValue "identity" r]]]
    | (record,u,d,uid)<-scopedUseRecords e]
  ,"notice" A..= ("One authored definition; distinct use, selected scenario and actual eager evaluation occurrences. Sharing is explicit within the selected scenario; no derived-result or cross-scope assessment transfer."::Text)]
 where
  plan=executionPlan e;doc=checkedDocument plan
  hashSource=Yuho.Protocol.Decode.sha256Text . Data.Text.Encoding.encodeUtf8
  componentKey record category object=case M.lookup (executionComponent record) (checkedComponents plan) of
    Just c->componentObjectKey (planIdentity (dependencyPlan doc)) c category object
    Nothing->qualifiedIdentity ["invalid-checked-component",executionComponent record,category,object]
  selectedRead use r=fieldValue "root" r==Just (A.toJSON (["expression",use]::[Text])) && fieldValue "path" r==Just (A.toJSON ([]::[Int]))
    || fieldValue "operator" r==Just (A.String "reference") && any (\x->fieldValue "kind" x==Just (A.String "requirement_reference") && fieldValue "requirement" x==Just (A.String use)) (listField "input_records" r)
  groundInputs record r=nub [x | child<-executionReads record,fieldValue "root" child==fieldValue "root" r
    ,pathOf r `isPrefixOf` pathOf child,x<-listField "input_records" child,fieldValue "kind" x==Just (A.String "ground_predicate")]
  pathOf=listField "path"
  selectedAssessments record u r=[A.object
    ["identity" A..= componentKey record "assessment-selection" (qualifiedIdentity [Data.Text.pack (selectedSource a),hashSource text,qualifiedIdentity (selectedPredicate a:selectedArguments a)])
    ,"origin" A..= ("authored classification"::Text),"declaration" A..= a,"source_snapshot" A..= hashSource text
    ,"selection" A..= useScenario u]
    | input<-groundInputs record r,Just c<-[M.lookup (executionComponent record) (checkedComponents plan)]
    ,a<-scopedAssessments (checkedScopedDefinitions c)
    ,fieldValue "predicate" input==Just (A.String (selectedPredicate a))
    ,fieldValue "arguments" input==Just (A.toJSON (selectedArguments a))
    ,fieldValue "classification" input==Just (selectedClassification a)
    ,Just text<-[M.lookup (selectedSource a) (dependencySources doc)]]

scopedUseRecords :: DependencyExecution -> [(ComponentRecord,ScopedUse,ScopedDefinition,Text)]
scopedUseRecords e=[(record,u,d,qualifiedIdentity ["scoped-use",componentObjectKey pid c "requirement-use" (useIdentity u)])
  | record<-executionComponents e,Just c<-[M.lookup (executionComponent record) (checkedComponents (executionPlan e))]
  ,u<-scopedUses (checkedScopedDefinitions c),d<-scopedDefinitions (checkedScopedDefinitions c),definitionKey d==useDefinition u]
 where pid=planIdentity (dependencyPlan (checkedDocument (executionPlan e)))

fieldValue :: Text -> A.Value -> Maybe A.Value
fieldValue key (A.Object x)=AM.lookup (Data.Aeson.Key.fromText key) x
fieldValue _ _=Nothing
listField :: Text -> A.Value -> [A.Value]
listField key v=case fieldValue key v of Just (A.Array xs)->foldr (:) [] xs;_->[]
