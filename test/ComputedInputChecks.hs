{-# LANGUAGE OverloadedStrings #-}
module ComputedInputChecks (runComputedInputChecks) where

import Control.Monad (forM_,unless)
import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as KM
import qualified Data.ByteString as BS
import Data.Maybe (fromJust)
import qualified Data.Text as T
import ComputedExample
import Yuho.Authoring

check :: String -> Bool -> IO ()
check label value=unless value (fail ("computed input: "<>label))
right :: Show e => Either e a -> IO a
right=either (fail . show) pure
isLeft :: Either a b -> Bool
isLeft (Left _)=True
isLeft _=False
-- Explicit semantic alignment only: authored object/path, technical value,
-- actual evaluation and branch/skip reasons. Generated request IDs, assessment
-- IDs/spans and snapshots intentionally differ, and remain in the full records.
semantic :: ApplicationReport -> A.Value
semantic r=A.toJSON (reportConclusion r,
  [(observationNode x,observationOccurrence x,observationComputed x,observationEvaluation x,observationSkipReason x) | x<-reportRequirements r],
  [(ruleAuthoredId x,ruleComputed x,ruleEvaluation x,ruleBranchReason x) | x<-reportRules r],
  [(exceptionRelationship x,exceptionComputed x,exceptionEvaluation x,exceptionFired x,exceptionSkipReason x) | x<-reportExceptions r])
derivations :: PresumptionReport -> A.Value
derivations r=A.toJSON ([(registeredId (registrationAuthored x),registrationRouteState x,registrationTriggerResult x,registrationRebuttalResult x) | x<-presumptionReportDerivations r],
  [(effectiveInput x,effectiveDirectValue x,effectiveValue x,effectiveRoutes x) | x<-presumptionReportLeaves r])

runComputedInputChecks :: IO ()
runComputedInputChecks=do
  forM_ [(TechnicalTrue,Proved,"satisfied"),(TechnicalFalse,NotProved,"not_satisfied"),(TechnicalUnresolved "original-reason-α",Unresolved NotDetermined,"unresolved")] $ \(status,classification,expected)->do
    d<-right (workflow status False False NotProved NotProved)
    check "complete integration validates" (null (validateComputedInput d))
    e<-right (executeComputedInput d)
    reference<-right (proofReference classification)
    let r=computedInputReport e
    check "independent proof parity, including branch reasons" (semantic (computedDownstreamReport r)==semantic (evaluationReport reference) && reportConclusion (computedDownstreamReport r)==expected)
    check "original status/actual observation retained" (typedObservedStatus (computedOriginalObservation r)==expected && computedMappedClassification r==Classification classification)
    check "generated overlay explicit; persisted original missing slot unchanged" (computedGeneratedOrigin r=="generated_computed_input_bridge" && assessmentOrigin (computedGeneratedAssessment r)=="external_assertion" && computedEvaluationDocument e==d && all ((/=assessmentId (computedGeneratedAssessment r)).assessmentId) (documentAssessments (fromJust (destinationProof (computedDestination d)))))
    restored<-right (decodeComputedInputDocument (encodeComputedInputDocument d))
    replay<-right (executeComputedInput restored)
    check "saved replay snapshot" (computedInputReport replay==r)
    p<-right (projectComputedInput e)
    v<-right (computedInputReferenceView p)
    check "complete projection/navigation" (null (validateComputedProjection (computedProjectionData p)) && not (null (computedNavigation (computedProjectionData p))))
    check "all encoders valid" (all (not . isLeft) [encodeComputedInputViewJson p v,encodeComputedInputViewXml p v,encodeComputedInputViewSvg p v])
    let bad=v {viewVersion="unsupported"}
    check "view format guard" (all isLeft [encodeComputedInputViewJson p bad,encodeComputedInputViewXml p bad,encodeComputedInputViewSvg p bad])
    check "view state isolated" (computedInputReport e==r)
    excerpt<-right (recoverComputedInputSource e "source" (SourceRef "packet" (Just (TextSpan 0 57 1 1 1 58))))
    check "original Unicode excerpt" (excerptText excerpt==Just "Zoë records access for Actor One to Resource R for read.")
    let pd=computedProjectionData p
    check "duplicate generated projection identity rejected" (not (null (validateComputedProjection pd {computedProjectionNodes=computedProjectionNodes pd++take 1 (computedProjectionNodes pd)})))
  forM_ [(TechnicalTrue,NotProved,NotProved,False,"active","satisfied"),
      (TechnicalFalse,NotProved,NotProved,False,"inactive","not_satisfied"),
      (TechnicalUnresolved "unreviewed",NotProved,NotProved,False,"unresolved","unresolved"),
      (TechnicalTrue,NotProved,Proved,False,"rebutted","not_satisfied"),
      (TechnicalTrue,Proved,Proved,False,"rebutted","satisfied"),
      (TechnicalTrue,NotProved,NotProved,True,"active","unresolved")] $ \(status,direct,rebuttal,guard,state,expected)->do
    d<-right (workflow status True guard direct rebuttal)
    e<-right (executeComputedInput d)
    let supplied=case status of TechnicalTrue->Proved; TechnicalFalse->NotProved; TechnicalUnresolved _->Unresolved NotDetermined
    reference<-right (presumptionReference guard supplied direct rebuttal)
    let actual=presumptionEvaluationReport (fromJust (computedEvaluationPresumption e));r=presumptionEvaluationReport reference
    check "presumption parity of routes, direct/effective, conditions" (derivations actual==derivations r)
    check "presumption downstream full semantic parity" (semantic (presumptionReportProof actual)==semantic (presumptionReportProof r) && reportConclusion (presumptionReportProof actual)==expected)
    check "independent route expectations" (map registrationRouteState (presumptionReportDerivations actual)==[state])
    check "global derivation versus skipped proof guard" (not guard || (all ((=="evaluated").registrationEvaluation) (presumptionReportDerivations actual) && any (\x->observationNode x=="target" && observationComputed x==Nothing && observationEvaluation x=="not_evaluated" && observationSkipReason x/=Nothing) (reportRequirements (presumptionReportProof actual))))
    p<-right (projectComputedInput e);_<-right (computedInputReferenceView p)
    check "presumption complete projection" (null (validateComputedProjection (computedProjectionData p)))
  forM_ [(ExactInteger 35,NotProved,"not_satisfied"),(ExactInteger 36,Proved,"satisfied"),(UnknownInteger "integer" "awaiting-measurement",Unresolved NotDetermined,"unresolved")] $ \(value,supplied,expected)->do
    doc<-right (scalarSource value >>= \s->workflowFrom s False False NotProved NotProved)
    e<-right (executeComputedInput doc)
    ref<-right (proofReference supplied)
    check "exact scalar computed-input parity" (semantic (computedDownstreamReport (computedInputReport e))==semantic (evaluationReport ref) && typedObservedStatus (computedOriginalObservation (computedInputReport e))==expected)
  negativeChecks
  putStrLn "computed-input: 3 relational proof, 3 exact-integer proof and 6 independent presumption parity scenarios, scoped mapping, snapshots, replay, provenance, projections and refusal matrix passed"

negativeChecks :: IO ()
negativeChecks=do
  d<-right (workflow TechnicalTrue False False NotProved NotProved)
  e<-right (executeComputedInput d)
  let b=computedBinding d
      bind f=d {computedBinding=f b}
      refuses code doc=do
        let errors=validateComputedInput doc
        check (T.unpack code<>" validation refusal") (any ((==code).diagnosticCode) errors)
        check (T.unpack code<>" execution refusal") (isLeft (executeComputedInput doc))
  forM_ ["unknown","typed-rule","typed-proposition"] $ \key->refuses "CBOBSERVATION" (bind (\x->x {computedSourceExpression=key}))
  refuses "CBSTALE" (bind (\x->x {computedSourceDocument="wrong-document"}))
  check "unknown source analysis" (isLeft (executeComputedInput (bind (\x->x {computedSourceAnalysis="unknown"}))))
  refuses "CBMAPPING" (bind (\x->x {computedPolicy=ComputedStatusPolicy "unsupported" "not_determined"}))
  refuses "CBMAPPING" (bind (\x->x {computedPolicy=ComputedStatusPolicy computedStatusMapping "missing-reason"}))
  refuses "CBSCOPE" (bind (\x->x {computedDestinationScope=Scope "actor:two" "event:synthetic"}))
  refuses "CBTARGET" (bind (\x->x {computedDestinationInput="unknown"}))
  refuses "CBTARGET" (bind (\x->x {computedDestinationInput="rule"}))
  refuses "CBPROFILE" d {computedDestination=(computedDestination d) {destinationProfile=typedEvaluatorProfile}}
  refuses "CBPROFILE" d {computedDestination=(computedDestination d) {destinationProof=fmap (\x->x {documentFormat=linkedAuthoringFormat}) (destinationProof (computedDestination d))}}
  refuses "CBLIMIT" (bind (\x->x {computedRationale=T.replicate 1048577 "x"}))
  refuses "PSOURCE" (bind (\x->x {computedOriginalSources=[SourceRef "missing" Nothing]}))
  check "invalid original span" (not (null (validateComputedInput (bind (\x->x {computedOriginalSources=[SourceRef "packet" (Just (TextSpan 3 4 1 4 1 5))]})))))
  let changed=d {computedTypedSource=(computedTypedSource d) {typedAssessments=[x {typedClassification=TechnicalFalse} | x<-typedAssessments (computedTypedSource d)]}}
  check "stale upstream actual evaluation rejected" (isLeft (executeComputedInputWith changed (computedEvaluationSource e)))
  check "stale upstream after fresh evaluation still needs reauthorised binding" (isLeft (executeComputedInput changed))
  check "stale composite attachment rejected" (isLeft (projectComputedInputOn changed e))
  check "original remains inspectable" (reportConclusion (computedDownstreamReport (computedInputReport e))=="satisfied")
  let tupleChange=(computedTypedSource d) {typedApplications=[x {applicationTuple=(applicationTuple x) {tupleArguments=["actor:one","resource:r","action:write"]}} | x<-typedApplications (computedTypedSource d)],typedAssessments=[x {assessedTuple=(assessedTuple x) {tupleArguments=["actor:one","resource:r","action:write"]}} | x<-typedAssessments (computedTypedSource d)]}
  check "changed tuple cannot reuse prior result" (isLeft (executeComputedInputWith d {computedTypedSource=tupleChange} (computedEvaluationSource e)))
  let base=fromJust (destinationProof (computedDestination d))
      conflict=base {documentAssessments=[Assessment "conflict" "trigger" scope (Classification NotProved) "Conflicting authored input" "Author" "fixture" "assumption" [] []],documentAnalyses=[a {analysisAssessments=["conflict"]} | a<-documentAnalyses base]}
  check "conflict rejected even when author constructing binding" (isLeft (makeComputedInputBinding "conflict-binding" (computedEvaluationSource e) "expr:relationship" (proofInputDestination conflict "proof-analysis") "trigger" policy "Explicit" []))
  let updated=d {computedDestination=proofInputDestination base {documentAssertions=[CaseAssertion "new-narrative" "Revised narrative" scope []]} "proof-analysis"}
  check "stale destination binding rejected" (isLeft (executeComputedInput updated) && isLeft (projectComputedInputOn updated e))
  -- Closed record paths, including nested policy and nested typed constructors.
  let json=A.toJSON d
      unknown (A.Object o)=A.Object (KM.insert "misspelled" (A.Bool True) o)
      unknown v=v
      mutate name f (A.Object o)=A.Object (case KM.lookup name o of Just x->KM.insert name (f x) o; Nothing->o)
      mutate _ _ v=v
  forM_ [unknown json,mutate "computedBinding" unknown json,mutate "computedBinding" (mutate "computedPolicy" unknown) json,
      mutate "computedDestination" unknown json,mutate "computedTypedSource" unknown json] $ \value->check "closed constructor rejects unknown field" (isLeft (decodeComputedInputDocument (encodeRecord value)))
  let bytes=encodeComputedInputDocument d
  let missingSource=originalSource {typedAnalyses=[a {selectedTypedAssessments=[]} | a<-typedAnalyses originalSource]}
      originalSource=computedTypedSource d
  check "missing upstream assessment is not unresolved" (not (null (validateComputedInput d {computedTypedSource=missingSource})))
  check "backend source resource limit preserved" (not (null (validateComputedInput d {computedTypedSource=originalSource {typedLimitations=[T.replicate 1048577 "x"]}})))
  check "missing direct destination still missing without bridge" (isLeft (compileAnalysis base "proof-analysis"))
  pdoc<-right (workflow TechnicalTrue True False NotProved NotProved)
  let pdest=computedDestination pdoc
      pbase=fromJust (destinationPresumption pdest)
      underlying=presumptionProofDocument pbase
      missingRebuttal=pbase {presumptionProofDocument=underlying {documentAnalyses=[a {analysisAssessments=filter (/="rebuttal-assessment") (analysisAssessments a)} | a<-documentAnalyses underlying]}}
  check "missing rebuttal never converted to not-proved" (isLeft (makeComputedInputBinding "no-rebuttal" (computedEvaluationSource e) "expr:relationship" (presumptionInputDestination missingRebuttal "proof-analysis") "trigger" policy "Explicit" []))
  let external=bind (\x->x {computedPolicy=ComputedStatusPolicy computedStatusMapping "external_decision_pending"})
  uncertain<-right (workflow (TechnicalUnresolved "retain-this-upstream-reason") False False NotProved NotProved)
  let mapped=uncertain {computedBinding=(computedBinding uncertain) {computedPolicy=computedPolicy (computedBinding external)}}
  mappedResult<-right (executeComputedInput mapped)
  check "explicit external pending mapping and original reason retained" (computedMappedClassification (computedInputReport mappedResult)==Classification (Unresolved ExternalDecisionPending) && any ((==TechnicalUnresolved "retain-this-upstream-reason").typedClassification) (typedAssessments (typedSnapshotDocument (computedTypedSnapshot (computedInputReport mappedResult)))))
  check "duplicate binding key rejected" (isLeft (decodeComputedInputDocument (BS.cons 123 ("\"computedBinding\":{},"<>BS.drop 1 bytes))))
  check "missing binding rejected" (case json of A.Object o->isLeft (decodeComputedInputDocument (encodeRecord (A.Object (KM.delete "computedBinding" o))));_->False)
  -- The source type cannot contain a proof output or integration dependency.
  check "reverse/cyclic dependency unsupported by closed source shape" (isLeft (decodeComputedInputDocument (encodeRecord (mutate "computedTypedSource" (const json) json))))
