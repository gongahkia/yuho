{-# LANGUAGE OverloadedStrings #-}
module ComputedInputRepairChecks (runComputedInputRepairChecks) where

import Control.Exception (SomeException,try)
import Control.Monad (forM_,unless)
import qualified Data.ByteString as BS
import Data.List (find)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import System.FilePath ((</>))
import Yuho.Authoring

check :: String -> Bool -> IO ()
check label value=unless value (fail ("computed-input repair: "<>label))
right :: Show e => Either e a -> IO a
right=either (fail . show) pure
load :: FilePath -> FilePath -> IO ComputedInputDocument
load root file=BS.readFile (root</>"test/fixtures/computed-input-repair"</>file) >>= right . decodeComputedInputDocument

runComputedInputRepairChecks :: FilePath -> IO ()
runComputedInputRepairChecks root=do
  -- Run both independent acceptance regressions even on the defective version.
  results<-mapM try [navigationChecks root,idChecks root] :: IO [Either SomeException ()]
  case [show e | Left e<-results] of
    []->putStrLn "computed-input repair: exact reviewer rule:0 and 120/128-byte regressions, semantic navigation and UTF-8 limits passed"
    errors->fail (unlines errors)

navigationChecks :: FilePath -> IO ()
navigationChecks root=do
  d<-load root "reviewer-rule0.document.json"
  e<-right (executeComputedInput d)
  p<-right (projectComputedInput e)
  let value=computedProjectionData p
  native<-maybe (fail "exact reviewer proof component absent") pure (computedProofProjection value)
  unrelated<-maybe (fail "exact reviewer rule:0 input absent") pure (find (\n->projectedNodeId n==objectProjectionId "rule:0" && projectedNodeKind n=="authored" && projectedNodeRole n=="input") (projectionNodes native))
  let bad=[l | l<-computedNavigation value,componentProjection l==projectionId native,componentNode l==projectedNodeId unrelated]
  check "exact original false rule:0 navigation must be absent" (null bad)
  check "unrelated input remains unevaluated" (projectedNodeComputed unrelated==Nothing && projectedNodeOccurrence unrelated==Nothing)
  check "correct projection accepted" (null (validateComputedProjection value))
  let source=computedSourceProjection value
  actor<-maybe (fail "reviewer actor:omar missing") pure (find (\n->typedNodeAuthoredId n=="actor:omar" && typedNodeKind n=="entity") (typedProjectionNodes source))
  integration<-maybe (fail "source expression card missing") pure (find ((=="typed_expression").projectedNodeRole) (computedProjectionNodes value))
  let poisoned=value {computedNavigation=[ComputedNavigation (projectedNodeId integration) (typedProjectionId source) (typedNodeId actor)]}
  check "exact reviewer structurally valid actor poison must be rejected" (not (null (validateComputedProjection poisoned)))
  semanticControls root d e p

idChecks :: FilePath -> IO ()
idChecks root=do
  original<-load root "reviewer-long-id.document.json"
  let source=computedTypedSource original;b=computedBinding original
  upstream<-right (compileTypedAnalysis source (computedSourceAnalysis b) >>= evaluateTypedAnalysis)
  let construct key=makeComputedInputBinding key upstream "expr:inspection" (computedDestination original) "expr:inspection"
        (ComputedStatusPolicy computedStatusMapping "not_determined") "Explicit admission" []
      keys=[T.replicate n "b" | n<-[1,119,120,127,128]] ++ [T.replicate 60 "é",T.replicate 64 "é",T.replicate 32 "😀","workflow:"<>T.replicate 64 "a","w","x"]
  forM_ keys $ \key->do
    binding<-right (construct key)
    check "binding ID preserved exactly" (computedBindingId binding==key)
    let d=original {computedDocumentId="caller-workflow",computedBinding=binding}
    check ("valid ID admitted: "<>show (BS.length (UTF8.encodeUtf8 key))) (null (validateComputedInput d))
    e<-right (executeComputedInputWith d upstream)
    check "long ID executes same technical conclusion" (reportConclusion (computedDownstreamReport (computedInputReport e))=="satisfied")
    replay<-right (decodeComputedInputDocument (encodeComputedInputDocument d))
    re<-right (executeComputedInput replay)
    check "long ID saved replay" (computedInputReport e==computedInputReport re)
  forM_ [T.replicate 129 "b",T.replicate 64 "é"<>"b",T.replicate 32 "😀"<>"b",""] $ \key->
    check "out-of-bound or empty binding ID rejected" (case construct key of Left errors->any ((=="CBID").diagnosticCode) errors;Right _->False)

-- All expected targets below come from public authored/observation records,
-- independently of the generator's private correspondence table.
semanticControls :: FilePath -> ComputedInputDocument -> ComputedInputEvaluation -> ComputedProjection -> IO ()
semanticControls root document evaluated projection=do
  let p=computedProjectionData projection
      report=computedInputReport evaluated
      binding=computedBinding document
      role key=case [n | n<-computedProjectionNodes p,projectedNodeRole n==key] of [n]->Right n;_->Left ("integration role absent/ambiguous: "<>show key)
      targets key=do
        n<-right (role key)
        pure [l | l<-computedNavigation p,integrationNode l==projectedNodeId n]
      rejectTarget label owner projectionIdValue node=do
        links<-targets owner
        original<-case links of x:_->pure x;_->fail "positive navigation absent"
        let wrong=original {componentProjection=projectionIdValue,componentNode=node}
            poisoned=p {computedNavigation=[if l==original then wrong else l | l<-computedNavigation p]}
        check label (any ((=="CBNAVIGATION").diagnosticCode) (validateComputedProjection poisoned))
  proof<-maybe (fail "proof control missing") pure (computedProofProjection p)
  sourceCard<-right (role "typed_expression")
  sourceLinks<-targets "typed_expression"
  check "same textual authored ID stays in typed namespace" (all ((==typedProjectionId (computedSourceProjection p)).componentProjection) sourceLinks
    && all ((/=objectProjectionId (computedDestinationInput binding)).componentNode) sourceLinks)
  sourceObservationLinks<-targets "typed_observation"
  check "actual named typed observation retained" (any ((==typedObservationId (computedOriginalObservation report)).componentNode) sourceObservationLinks)
  check "typed definition is not its run observation" (all ((/=typedObservationId (computedOriginalObservation report)).componentNode) sourceLinks)
  assignmentLinks<-targets "explicit_binding"
  check "mapping points exactly to overlay assessment" (map componentNode assignmentLinks==[objectProjectionId (assessmentId (computedGeneratedAssessment report))])
  inputLinks<-targets "destination_input"
  check "destination maps definition and generated assessment separately" (all (\key->key `elem` map componentNode inputLinks)
    [objectProjectionId (computedDestinationInput binding),objectProjectionId (assessmentId (computedGeneratedAssessment report))])
  forM_ (reportRequirements (computedDownstreamReport report)) $ \row->if observationNode row/=computedDestinationInput binding then pure () else do
    links<-targets ("requirement:"<>observationKernelId row)
    let expected=ObservationIdentity (computedDownstreamSnapshot report) evaluatorProfile "requirement" (observationNode row) (observationOccurrence row) (Just (observationKernelId row)) (Just (observationKernelBranch row))
    check "requirement maps the precise run observation" (observationProjectionId expected `elem` map componentNode links)
  forM_ (reportRules (computedDownstreamReport report)) $ \row->do
    links<-targets ("result:"<>ruleAuthoredId row)
    let expected=ObservationIdentity (computedDownstreamSnapshot report) evaluatorProfile "rule" (ruleAuthoredId row) [] (Just (ruleKernelId row)) (Just (ruleKernelBranch row))
    check "rule maps exact authored rule and run identity" (objectProjectionId (ruleAuthoredId row) `elem` map componentNode links && observationProjectionId expected `elem` map componentNode links)
  -- Each wrong target exists; replacing one link preserves all the others.
  rejectTarget "unrelated existing input rejected" "typed_expression" (projectionId proof) (objectProjectionId "rule:0")
  let typed=computedSourceProjection p
  actor<-maybe (fail "typed entity absent") pure (find ((=="entity").typedNodeKind) (typedProjectionNodes typed))
  rejectTarget "wrong category in correct component rejected" "typed_expression" (typedProjectionId typed) (typedNodeId actor)
  rejectTarget "wrong component rejected despite shared textual ID" "destination_input" (typedProjectionId typed)
    (case [typedNodeId n | n<-typedProjectionNodes typed,typedNodeKind n=="expression",typedNodeAuthoredId n==computedDestinationInput binding] of key:_->key;_->typedNodeId actor)
  rejectTarget "absent component node rejected" "typed_expression" (typedProjectionId typed) "absent"
  let resultRole="result:"<>reportTarget (computedDownstreamReport report)
  rejectTarget "kernel-like authored ID rejected" resultRole (projectionId proof) (objectProjectionId "rule:0")
  rejectTarget "wrong observation category rejected" resultRole (projectionId proof)
    (case [projectedNodeId n | n<-projectionNodes proof,projectedNodeKind n=="observation",Just i<-[projectedNodeObservation n],observationCategory i=="requirement"] of x:_->x;_->objectProjectionId "rule:0")
  let noLinks=p {computedNavigation=[]}
  check "required correspondences cannot all be discarded" (not (null (validateComputedProjection noLinks)))
  check "source card remains stable" (projectedNodeId sourceCard `elem` map integrationNode (computedNavigation p))
  upstream<-right (compileTypedAnalysis (computedTypedSource document) (computedSourceAnalysis binding) >>= evaluateTypedAnalysis)
  -- Author/kernel names remain legal even when they are not in the selected tree.
  let originalBase=case destinationProof (computedDestination document) of Just x->x;_->error "proof fixture"
      collisionIds=["requirement:0","branch:0",assessmentId (computedGeneratedAssessment report),"same-label-other-id"]
      extra label key=LawNode key "input" label Nothing Nothing []
      augmented=originalBase {documentLaw=(documentLaw originalBase) {lawNodes=lawNodes (documentLaw originalBase)++[extra (reportTarget (computedDownstreamReport report)) key | key<-collisionIds]}}
  changed<-renew document upstream (proofInputDestination augmented (computedDestinationAnalysis binding))
  ce<-right (executeComputedInputWith changed upstream);cp<-right (projectComputedInput ce)
  let c=computedProjectionData cp
  check "all additional authored/kernel/label collisions remain unrelated" (all (\l->componentNode l `notElem` map objectProjectionId collisionIds) (computedNavigation c))
  let cnative=case computedProofProjection c of Just x->x;_->error "proof component"
  check "colliding original nodes retained" (all (\key->any ((==objectProjectionId key).projectedNodeId) (projectionNodes cnative)) collisionIds)
  resultNode<-right (role resultRole)
  let wrongRepeated=p {computedProofProjection=Just proof {projectionNodes=[if projectedNodeId n==objectProjectionId "rule:0" then n {projectedNodeOrigin=(projectedNodeOrigin n) {originAuthoredObjects=["rule:0",reportTarget (computedDownstreamReport report),reportTarget (computedDownstreamReport report)]}} else n | n<-projectionNodes proof]},computedNavigation=computedNavigation p++[ComputedNavigation (projectedNodeId resultNode) (projectionId proof) (objectProjectionId "rule:0")]}
  check "repeated origins do not justify unrelated navigation" (not (null (validateComputedProjection wrongRepeated)))
  -- Same-status source revision: qualified component identity, not truth, changes.
  let revisedSource=(computedTypedSource document) {typedAssessments=[a {typedAssessmentReason=typedAssessmentReason a<>" (same-status revision)"} | a<-typedAssessments (computedTypedSource document)]}
  fresh<-right (compileTypedAnalysis revisedSource (computedSourceAnalysis binding) >>= evaluateTypedAnalysis)
  revised<-renew document {computedTypedSource=revisedSource} fresh (computedDestination document)
  re<-right (executeComputedInputWith revised fresh);rp<-right (projectComputedInput re)
  check "same-status revision has new snapshots" (typedObservedStatus (computedOriginalObservation report)==typedObservedStatus (computedOriginalObservation (computedInputReport re))
    && computedExecutionId report/=computedExecutionId (computedInputReport re) && computedSourceSnapshot binding/=computedSourceSnapshot (computedBinding revised))
  check "stale attachment still rejected" (case projectComputedInputOn revised evaluated of Left _->True;_->False)
  let foreignSource=computedSourceProjection (computedProjectionData rp)
      oldSource=computedSourceProjection p
      foreignProjection=p {computedSourceProjection=foreignSource,computedNavigation=[if componentProjection l/=typedProjectionId oldSource then l else l {componentProjection=typedProjectionId foreignSource,componentNode=if componentNode l==typedObservationId (computedOriginalObservation report) then typedObservationId (computedOriginalObservation (computedInputReport re)) else componentNode l} | l<-computedNavigation p]}
  check "structurally existing foreign-snapshot component rejected" (not (null (validateComputedProjection foreignProjection)))
  -- A second actual rule observation in the same component is also not interchangeable.
  let analysisScopeValue=reportScope (computedDownstreamReport report)
      guardAssessment=Assessment "guard-assessment" "guard-input" analysisScopeValue (Classification NotProved) "Fixture assumption" "Regression author" "synthetic_fixture" "assumption" [] []
      guarded=originalBase {documentLaw=(documentLaw originalBase) {lawNodes=lawNodes (documentLaw originalBase)++[LawNode "guard-rule" "rule" "Other rule" Nothing Nothing [],LawNode "guard-input" "input" "Other input" Nothing Nothing []],lawEdges=lawEdges (documentLaw originalBase)++[LawEdge "guard-edge" (analysisTarget (snapshotAnalysis (projectionSnapshot proof))) "guard-rule" "exception",LawEdge "guard-body" "guard-rule" "guard-input" "requires"]},documentAssessments=documentAssessments originalBase++[guardAssessment],documentAnalyses=[a {analysisAssessments=analysisAssessments a++[assessmentId guardAssessment]} | a<-documentAnalyses originalBase]}
  gd<-renew document upstream (proofInputDestination guarded (computedDestinationAnalysis binding));ge<-right (executeComputedInput gd);gp<-right (projectComputedInput ge)
  let g=computedProjectionData gp;gn=case computedProofProjection g of Just x->x;_->error "guard component"
  other<-maybe (fail "other evaluated rule observation absent") pure (find (\n->projectedNodeKind n=="observation" && maybe False (\i->observationCategory i=="rule" && observationAuthoredObject i=="guard-rule") (projectedNodeObservation n)) (projectionNodes gn))
  let mainLinks=[l | l<-computedNavigation g,n<-computedProjectionNodes g,projectedNodeRole n==resultRole,integrationNode l==projectedNodeId n]
  case mainLinks of
    original:_->check "wrong evaluated rule in same snapshot rejected" (not (null (validateComputedProjection g {computedNavigation=[if l==original then l {componentNode=projectedNodeId other} else l | l<-computedNavigation g]})))
    _->fail "main rule mapping absent"
  forM_ ["reviewer-trigger.document.json","reviewer-rebuttal.document.json","reviewer-skipped.document.json"] $ \file->do
    d<-load root file;e<-right (executeComputedInput d);pr<-right (projectComputedInput e)
    presumptionControls d e (computedProjectionData pr)
  v<-right (computedInputReferenceView projection)
  check "valid serialization and encoders retained" (all (either (const False) (not.BS.null)) [encodeComputedInputViewJson projection v,encodeComputedInputViewXml projection v,encodeComputedInputViewSvg projection v])
  replay<-right (decodeComputedInputDocument (encodeComputedInputDocument document))
  again<-right (executeComputedInput replay >>= projectComputedInput)
  check "complete projection replay identical" (encodeComputedProjection projection==encodeComputedProjection again)

renew :: ComputedInputDocument -> TypedEvaluation -> ComputedDestination -> IO ComputedInputDocument
renew d source destination=do
  let b=computedBinding d
  binding<-right (makeComputedInputBinding (computedBindingId b) source (computedSourceExpression b) destination (computedDestinationInput b) (computedPolicy b) (computedRationale b) (computedOriginalSources b))
  pure d {computedDestination=destination,computedBinding=binding}

presumptionControls :: ComputedInputDocument -> ComputedInputEvaluation -> ComputedProjectionData -> IO ()
presumptionControls d evaluated p=do
  let report=computedInputReport evaluated;binding=computedBinding d
  native<-maybe (fail "presumption control missing") pure (computedPresumptionProjection p)
  derivation<-maybe (fail "derivation control missing") pure (computedDerivationReport report)
  let nodes=presumptionProjectionNodes native
      targets role=[componentNode l | n<-computedProjectionNodes p,projectedNodeRole n==role,l<-computedNavigation p,integrationNode l==projectedNodeId n,presumptionProjectionId native==componentProjection l]
  forM_ (presumptionReportDerivations derivation) $ \r->do
    let registration=registrationAuthored r;role="route:"<>registeredId registration;keys=targets role
        condition key=any (\n->projectedNodeId n `elem` keys && maybe False (\i->observationCategory i=="registered_condition" && observationAuthoredObject i==key && observationRunSnapshot i==computedDownstreamSnapshot report) (projectedNodeObservation n)) nodes
    check "actual registration and exact derivation linked" (objectProjectionId (registeredId registration) `elem` keys && registrationObservationId r `elem` keys)
    check "actual trigger and rebuttal condition observations linked" (condition (registeredConditionId (registeredTrigger registration)) && condition (registeredConditionId (registeredRebuttal registration)))
    check "bound trigger/rebuttal correspondence is explicit" (computedDestinationInput binding `elem` (conditionLeaves (registeredTrigger registration)++conditionLeaves (registeredRebuttal registration)))
  forM_ (presumptionReportLeaves derivation) $ \leaf->if null (effectiveRoutes leaf) then pure () else do
    let keys=targets ("effective:"<>effectiveInput leaf)
    check "effective identity separated from supplied direct assessment" (all (`elem` keys) [effectiveObservationId leaf,objectProjectionId (effectiveInput leaf),objectProjectionId (assessmentId (effectiveDirectAssessment leaf))])
  check "presumption projection semantically accepted" (null (validateComputedProjection p))
