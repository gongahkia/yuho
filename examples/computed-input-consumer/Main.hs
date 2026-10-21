{-# LANGUAGE OverloadedStrings #-}
module Main (main) where

import Control.Monad (forM_,unless)
import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as KM
import qualified Data.ByteString as BS
import qualified Data.Text as T
import System.Directory (createDirectoryIfMissing)
import System.Environment (getArgs)
import System.FilePath ((</>))
import Yuho.Authoring
import ComputedExample

right :: Show e => Either e a -> IO a
right=either (fail . show) pure
check :: String -> Bool -> IO ()
check label value=unless value (fail label)
semantic :: ApplicationReport -> A.Value
semantic r=A.toJSON (reportConclusion r,
  [(observationNode x,observationOccurrence x,observationComputed x,observationEvaluation x,observationSkipReason x) | x<-reportRequirements r],
  [(ruleAuthoredId x,ruleComputed x,ruleEvaluation x,ruleBranchReason x) | x<-reportRules r],
  [(exceptionRelationship x,exceptionComputed x,exceptionEvaluation x,exceptionFired x,exceptionSkipReason x) | x<-reportExceptions r])
main :: IO ()
main=do
  args<-getArgs
  out<-case args of [path]->pure path;_->fail "usage: yuho-computed-input OUTPUT_DIRECTORY"
  createDirectoryIfMissing True out
  let save name x=BS.writeFile (out</>name) (encodeRecord x)
      export name doc=do
        check "ready before execution" (null (validateComputedInput doc))
        save (name<>".document.json") doc
        save (name<>".source.document.json") (computedTypedSource doc)
        save (name<>".destination.document.json") (computedDestination doc)
        save (name<>".binding.json") (computedBinding doc)
        replay<-right (decodeComputedInputDocument (encodeComputedInputDocument doc))
        check "authored round trip" (replay==doc)
        e<-right (executeComputedInput replay)
        save (name<>".report.json") (computedInputReport e)
        p<-right (projectComputedInput e)
        save (name<>".projection.json") (computedProjectionData p)
        save (name<>".inspection.json") (computedSourceInspection (computedProjectionData p))
        view<-right (computedInputReferenceView p)
        save (name<>".bindings.json") view
        BS.writeFile (out</>name<>".view.json") =<< right (encodeComputedInputViewJson p view)
        BS.writeFile (out</>name<>".view.xml") =<< right (encodeComputedInputViewXml p view)
        BS.writeFile (out</>name<>".svg") =<< right (encodeComputedInputViewSvg p view)
        _<-right (projectComputedInputOn doc e)
        again<-right (executeComputedInput replay)
        check "snapshot/report replay stable" (computedInputReport again==computedInputReport e)
        save (name<>".replay.json") (A.object ["stable" A..=True,"execution" A..=computedExecutionId (computedInputReport e)])
        let sourceDoc=computedTypedSource doc
            firstSource=case typedOriginalSources sourceDoc of x:_->x;_->error "fixture source missing"
        anchor<-right (sourceAnchorCodePoints firstSource 0 56)
        excerpt<-right (recoverComputedInputSource e "source" anchor)
        save (name<>".source-recovery.json") excerpt
        check "exact original Unicode excerpt" (excerptText excerpt==Just "Zoë records access for Actor One to Resource R for read.")
        putStrLn (name<>" -> "<>T.unpack (reportConclusion (computedDownstreamReport (computedInputReport e)) ))
        pure e
  proofs<-mapM (\(name,status,supplied,expected)->do
    d<-right (workflow status False False NotProved NotProved)
    e<-export name d
    reference<-right (proofReference supplied)
    save (name<>".reference.document.json") (snapshotDocument (evaluationSnapshot reference))
    save (name<>".reference.report.json") (evaluationReport reference)
    let r=computedInputReport e
    check "explicit independent expected outcome" (reportConclusion (computedDownstreamReport r)==expected)
    check "independent supplied proof parity" (semantic (computedDownstreamReport r)==semantic (evaluationReport reference))
    save (name<>".parity.json") (A.object ["equalTechnicalObservations" A..=True,"expected" A..=expected,"integrated" A..=semantic (computedDownstreamReport r),"reference" A..=semantic (evaluationReport reference),"sameProvenance" A..=False])
    pure e) [("proof-true",TechnicalTrue,Proved,"satisfied"),("proof-false",TechnicalFalse,NotProved,"not_satisfied"),("proof-unresolved",TechnicalUnresolved "external-review-needed",Unresolved NotDetermined,"unresolved")]
  forM_ [("presumption-active",TechnicalTrue,Proved,NotProved,NotProved,False,"active","satisfied"),
      ("presumption-inactive",TechnicalFalse,NotProved,NotProved,NotProved,False,"inactive","not_satisfied"),
      ("presumption-unresolved",TechnicalUnresolved "external-review-needed",Unresolved NotDetermined,NotProved,NotProved,False,"unresolved","unresolved"),
      ("presumption-rebutted",TechnicalTrue,Proved,NotProved,Proved,False,"rebutted","not_satisfied"),
      ("presumption-direct",TechnicalTrue,Proved,Proved,Proved,False,"rebutted","satisfied"),
      ("presumption-skipped",TechnicalTrue,Proved,NotProved,NotProved,True,"active","unresolved")] $ \(name,status,supplied,direct,rebuttal,guard,route,expected)->do
    d<-right (workflow status True guard direct rebuttal)
    e<-export name d
    reference<-right (presumptionReference guard supplied direct rebuttal)
    save (name<>".reference.document.json") (presumptionSnapshotDocument (presumptionEvaluationSnapshot reference))
    save (name<>".reference.report.json") (presumptionEvaluationReport reference)
    actual<-case computedDerivationReport (computedInputReport e) of Just x->pure x;_->fail "missing derivation report"
    let ref=presumptionEvaluationReport reference
        details r=A.toJSON ([(registeredId (registrationAuthored x),registrationRouteState x,registrationTriggerResult x,registrationRebuttalResult x) | x<-presumptionReportDerivations r],[(effectiveInput x,effectiveDirectValue x,effectiveValue x,effectiveRoutes x) | x<-presumptionReportLeaves r])
    check "independent route/outcome expectations" (map registrationRouteState (presumptionReportDerivations actual)==[route] && reportConclusion (presumptionReportProof actual)==expected)
    check "independent route/direct/effective/condition and proof parity" (details actual==details ref && semantic (presumptionReportProof actual)==semantic (presumptionReportProof ref))
    save (name<>".parity.json") (A.object ["equalTechnicalObservations" A..=True,"sameProvenance" A..=False,"expectedRoute" A..=route,"expectedConclusion" A..=expected,"derivations" A..=details actual,"downstream" A..=semantic (presumptionReportProof actual)])
  forM_ [("integer-boundary",ExactInteger 35,NotProved),("integer-above",ExactInteger 36,Proved),("integer-unresolved",UnknownInteger "integer" "pending-original-value",Unresolved NotDetermined)] $ \(name,value,supplied)->do
    doc<-right (scalarSource value >>= \s->workflowFrom s False False NotProved NotProved)
    e<-export name doc
    ref<-right (proofReference supplied)
    check "independent exact scalar bridge parity" (semantic (computedDownstreamReport (computedInputReport e))==semantic (evaluationReport ref))
    save (name<>".reference.document.json") (snapshotDocument (evaluationSnapshot ref))
    save (name<>".reference.report.json") (evaluationReport ref)
    save (name<>".parity.json") (A.object ["equalTechnicalObservations" A..=True,"sameProvenance" A..=False])
  let first=case proofs of x:_->x;_->error "proof matrix empty"
      original=computedEvaluationDocument first
      bind f=original {computedBinding=f (computedBinding original)}
      reject name doc=do
        save (name<>".invalid-document.json") doc
        let errors=validateComputedInput doc
        check "invalid input rejected before downstream evaluation" (not (null errors))
        save (name<>".diagnostics.json") errors
        check "no downstream execution" (case executeComputedInput doc of Left _->True;_->False)
  forM_ [("unknown-observation",bind (\b->b {computedSourceExpression="unknown"})),
      ("wrong-category",bind (\b->b {computedSourceExpression="typed-rule"})),
      ("unknown-source-document",bind (\b->b {computedSourceDocument="unknown"})),
      ("unknown-source-analysis",bind (\b->b {computedSourceAnalysis="unknown"})),
      ("unsupported-mapping",bind (\b->b {computedPolicy=ComputedStatusPolicy "unknown" "not_determined"})),
      ("missing-reason",bind (\b->b {computedPolicy=ComputedStatusPolicy computedStatusMapping ""})),
      ("wrong-actor",bind (\b->b {computedDestinationScope=Scope "actor:two" "event:synthetic"})),
      ("unknown-target",bind (\b->b {computedDestinationInput="unknown"})),
      ("nonprimitive-target",bind (\b->b {computedDestinationInput="rule"})),
      ("bad-original-source",bind (\b->b {computedOriginalSources=[SourceRef "unknown" Nothing]})),
      ("bad-original-anchor",bind (\b->b {computedOriginalSources=[SourceRef "packet" (Just (TextSpan 3 4 1 4 1 5))]})),
      ("reverse-profile",original {computedDestination=(computedDestination original) {destinationProfile=typedEvaluatorProfile}})] $ uncurry reject
  let changed=original {computedTypedSource=(computedTypedSource original) {typedAssessments=[x {typedClassification=TechnicalFalse} | x<-typedAssessments (computedTypedSource original)]}}
  reject "stale-upstream" changed
  save "stale-attachment.json" (case projectComputedInputOn changed first of Left errors->A.toJSON errors;_->A.Null)
  save "snapshot-revision.json" (A.object ["original" A..=computedExecutionId (computedInputReport first),"revised" A..=[computedExecutionId (computedInputReport e) | e<-drop 1 proofs],"originalStillInspectable" A..=(reportConclusion (computedDownstreamReport (computedInputReport first))=="satisfied")])
  let dest=computedDestination original
  base<-right (computedDestinationDocument dest)
  let conflictAssessment=Assessment "conflict" "trigger" scope (Classification NotProved) "Explicit conflicting fixture assumption" "Author" "synthetic_fixture" "assumption" [] []
      conflicting=proofInputDestination base {documentAssessments=documentAssessments base++[conflictAssessment],documentAnalyses=[a {analysisAssessments=analysisAssessments a++["conflict"]} | a<-documentAnalyses base]} "proof-analysis"
  case makeComputedInputBinding "conflict-binding" (computedEvaluationSource first) "expr:relationship" conflicting "trigger" policy "Explicit" [] of
    Left errors->save "direct-conflict.diagnostics.json" errors
    Right _->fail "selected direct assessment conflict accepted"
  let swapped=(computedTypedSource original) {typedApplications=[a {applicationTuple=(applicationTuple a) {tupleArguments=["actor:one","resource:r","action:write"]}} | a<-typedApplications (computedTypedSource original)],typedAssessments=[a {assessedTuple=(assessedTuple a) {tupleArguments=["actor:one","resource:r","action:write"]}} | a<-typedAssessments (computedTypedSource original)]}
  reject "stale-changed-tuple" original {computedTypedSource=swapped}
  reject "stale-destination" original {computedDestination=proofInputDestination base {documentAssertions=[CaseAssertion "revision" "New narrative" scope []]} "proof-analysis"}
  let malformed=case A.toJSON original of A.Object obj->A.Object (KM.insert "unexpected" (A.Bool True) obj);x->x
  save "unknown-field.input.json" malformed
  case decodeComputedInputDocument (encodeRecord malformed) of Left errors->save "unknown-field.diagnostics.json" errors;_->fail "unknown field accepted"
  putStrLn "computed-input consumer: original inputs retained, twelve independent references, exact source recovery, replay, scopes, stale attachment and exports passed"
