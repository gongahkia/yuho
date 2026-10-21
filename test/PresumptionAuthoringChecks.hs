{-# LANGUAGE OverloadedStrings #-}
module PresumptionAuthoringChecks (runPresumptionAuthoringChecks) where

import Control.Monad (forM_, unless)
import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as KM
import qualified Data.ByteString as BS
import Data.List (find, sort, sortOn)
import qualified Data.Map.Strict as Map
import qualified Data.Text as T
import System.FilePath ((</>))
import Yuho.Authoring
import qualified Yuho.Core.Types as C
import Yuho.Kernel.Run (runLine)
import qualified Yuho.Presumption.Decode as Backend
import qualified Yuho.Presumption.Validate as Backend
import Yuho.Protocol.Json (J(..), decodeJson, lookupField, textValue, encodeJson)
import PresumptionExamples

check :: String -> Bool -> IO ()
check label passed = unless passed (fail ("presumption authoring: " <> label))
required :: Show e => Either e a -> IO a
required = either (fail . show) pure

first :: [a] -> a
first (x:_) = x
first [] = error "test fixture unexpectedly empty"


runPresumptionAuthoringChecks :: FilePath -> IO ()
runPresumptionAuthoringChecks root = do
  forM_ matrix $ \(name,t,r,k,state,value) -> do
    e <- required (execute (synthetic t r k))
    let report=presumptionEvaluationReport e
    check (T.unpack name) (map registrationRouteState (presumptionReportDerivations report) == [state]
      && reportConclusion (presumptionReportProof report) == value)
    parity name (synthetic t r k)
  forM_ [("chain-active",Proved,NotProved,NotProved,["active","active"],"satisfied"),
    ("chain-rebutted",Proved,Proved,NotProved,["rebutted","inactive"],"not_satisfied"),
    ("chain-uncertain",Unresolved NotDetermined,NotProved,NotProved,["unresolved","unresolved"],"unresolved"),
    ("chain-direct",Proved,Proved,Proved,["rebutted","inactive"],"satisfied")] $ \(name,t,r,k,states,value) -> do
      let d=chained t r k
      artifact <- required (compilePresumptionAnalysis d "analysis:synthetic")
      check "both chain registrations retain original source mappings" (all (not . null . presumptionMappingOriginals) [m | m <- presumptionCompiledMappings artifact,presumptionMappingKind m == "registration"])
      e <- required (evaluatePresumptionAnalysis artifact)
      check (T.unpack name) (map registrationRouteState (presumptionReportDerivations (presumptionEvaluationReport e)) == states
        && reportConclusion (presumptionReportProof (presumptionEvaluationReport e)) == value)
      parity name d
  parity "P6-multiple" multipleRoutes
  parity "P7-skipped-guard" skippedGuard
  parity "guard-defeat" (revise "main" Proved skippedGuard)
  parity "guard-unresolved" (revise "T" (Unresolved NotDetermined) (revise "main" Proved skippedGuard))
  guardE <- required (execute skippedGuard)
  let guardReport=presumptionEvaluationReport guardE
  check "global derivation evaluated despite skipped guard" (map registrationEvaluation (presumptionReportDerivations guardReport) == ["evaluated"])
  check "effective resolved despite downstream skipped" ([(effectiveValue x,map observationComputed (effectiveDownstream x),map observationEvaluation (effectiveDownstream x)) | x <- presumptionReportLeaves guardReport,effectiveInput x == "K"] == [("satisfied",[Nothing],["not_evaluated"])])
  guardP <- required (projectPresumptionEvaluation guardE)
  check "no fabricated skipped proof observation" (not (any (\n -> projectedNodeRole n == "proof_observation" && originAuthoredObjects (projectedNodeOrigin n) == ["K"]) (presumptionProjectionNodes (presumptionProjectionData guardP))))
  check "actual skip reason" (all (maybe False (T.isInfixOf "requirements_unresolved") . exceptionSkipReason) (reportExceptions (presumptionReportProof guardReport)))
  let initial=synthetic Proved NotProved NotProved
      base=presumptionProofDocument initial
      reg=first (presumptionRegistrations initial)
      editBase f d=d {presumptionProofDocument=f (presumptionProofDocument d)}
      editReg f d=d {presumptionRegistrations=map f (presumptionRegistrations d)}
      changedConditions f=editReg (\r -> r {registeredTrigger=f (registeredTrigger r)})
      missing key=editBase (\b -> b {documentAnalyses=[a {analysisAssessments=filter (/= key) (analysisAssessments a)} | a <- documentAnalyses b]})
      wrongScope=editBase (\b -> b {documentAssessments=[a {assessmentScope=Scope "wrong" "wrong"} | a <- documentAssessments b]})
      selfCycle=changedConditions (\c -> c {registeredConditionLeaf=Just "K"}) initial
      indirect=(chained Proved NotProved NotProved) {presumptionRegistrations=[r {registeredTrigger=(registeredTrigger r) {registeredConditionLeaf=Just (if registeredTarget r == "P" then "K" else "P")}} | r <- presumptionRegistrations (chained Proved NotProved NotProved)]}
      invalids=[("target",editReg (\r -> r {registeredTarget="absent"}) initial,"PATARGET"),
        ("trigger",changedConditions (\c -> c {registeredConditionLeaf=Just "absent"}) initial,"PACONDITION"),
        ("rebuttal",editReg (\r -> r {registeredRebuttal=(registeredRebuttal r) {registeredConditionLeaf=Just "absent"}}) initial,"PACONDITION"),
        ("duplicate",initial {presumptionRegistrations=[reg,reg]},"PADUPLICATE"),
        ("unsupported kind",changedConditions (\c -> c {registeredConditionKind="burden_shift"}) initial,"PACONDITION"),
        ("malformed group",changedConditions (\c -> c {registeredConditionKind="all_of",registeredConditionLeaf=Nothing}) initial,"PACONDITION"),
        ("direct cycle",selfCycle,"PACYCLE"),("indirect cycle",indirect,"PACYCLE"),
        ("source",editReg (\r -> r {registeredSources=[SourceRef "absent" Nothing]}) initial,"PSOURCE"),
        ("span",editReg (\r -> r {registeredSources=[SourceRef "source:synthetic" (Just (TextSpan 0 9999 1 1 1 10000))]}) initial,"PSOURCE"),
        ("missing target",missing "assessment:K" initial,"PAMISSING"),
        ("missing rebuttal",missing "assessment:R" initial,"PAMISSING"),
        ("wrong scope",wrongScope initial,"PASCOPE"),
        ("mixed profile",editBase (\b -> b {documentFormat=linkedAuthoringFormat}) initial,"PAPROFILE")]
  forM_ invalids $ \(label,d,code) -> do
    let v=validatePresumptionAnalysis d "analysis:synthetic"
    putStrLn ("presumption negative " <> label <> ": " <> show (presumptionDiagnostics v))
    check (label <> " rejection") (not (presumptionAnalysisReady v) && code `elem` map diagnosticCode (presumptionDiagnostics v))
    check (label <> " compile rejects") (case execute d of Left _ -> True; Right _ -> False)
    check (label <> " object diagnostic") (any (not . null . diagnosticObjects) (presumptionDiagnostics v))
  let over=changedConditions (\c -> c {registeredConditionKind="all_of",registeredConditionLeaf=Nothing,registeredConditionMembers=[RegisteredCondition ("condition:budget:" <> T.pack (show i)) "leaf_effective" (Just "T") [] [] | i <- [1..1100 :: Int]]}) initial
  check "expanded backend identity budget" (any ((== "PABACKEND/KINV004") . diagnosticCode) (presumptionDiagnostics (validatePresumptionAnalysis over "analysis:synthetic")))
  let deep n=if n == (0 :: Int) then RegisteredCondition "deep:leaf" "leaf_effective" (Just "T") [] [] else RegisteredCondition ("deep:"<>T.pack (show n)) "all_of" Nothing [deep (n-1),RegisteredCondition ("side:"<>T.pack (show n)) "leaf_effective" (Just "R") [] []] []
  check "depth before backend" (any ((== "PADEPTH") . diagnosticCode) (validatePresumptionDocument (changedConditions (const (deep 16)) initial)))
  -- Closed constructors: use public decoder, including source, scope, classification.
  let json=A.toJSON initial
      inject key (A.Object o)=A.Object (KM.insert key (A.Bool True) o)
      inject _ x=x
      mutateFirst key f (A.Object o)=case KM.lookup key o of
        Just (A.Array xs) -> A.Object (KM.insert key (A.toJSON (case A.fromJSON (A.Array xs) of A.Success (x:rest) -> f x:rest; _ -> [] :: [A.Value])) o)
        _ -> A.Object o
      mutateFirst _ _ x=x
      mutate key f (A.Object o)=A.Object (maybe o (\x -> KM.insert key (f x) o) (KM.lookup key o))
      mutate _ _ x=x
      malformed=[inject "unknown" json,mutateFirst "presumptionRegistrations" (inject "burden_effect") json,
        mutateFirst "presumptionRegistrations" (mutate "registeredTrigger" (inject "typo")) json,
        mutate "presumptionProofDocument" (mutateFirst "documentAssessments" (mutate "assessmentClassification" (inject "typo"))) json,
        mutate "presumptionProofDocument" (mutateFirst "documentSources" (inject "typo")) json]
  forM_ malformed $ \x -> check "unknown nested field rejected by public decoder" (case decodePresumptionDocument (encodeRecord x) of Left _ -> True; Right _ -> False)
  -- Positive group trees and parity; no adapter truth tables.
  let grouped=editBase (\b -> b {documentLaw=(documentLaw b) {lawNodes=lawNodes (documentLaw b) ++ [LawNode "group" "all" "Both downstream conditions" Nothing Nothing [],LawNode "extra" "input" "Additional direct condition" Nothing Nothing []],
          lawEdges=[LawEdge "edge:group" "rule:selected" "group" "requires",LawEdge "edge:K" "group" "K" "member",LawEdge "edge:extra" "group" "extra" "member"]},
        documentAssessments=documentAssessments b ++ [(first (documentAssessments b)) {assessmentId="assessment:extra",assessmentInput="extra",assessmentClassification=Classification Proved}],
        documentAnalyses=[a {analysisAssessments=analysisAssessments a ++ ["assessment:extra"]} | a <- documentAnalyses b]}) initial
  parity "group" grouped
  forM_ ["all_of","any_of"] $ \kind -> do
    let c=RegisteredCondition "condition:group" kind Nothing [registeredTrigger reg,(registeredTrigger reg) {registeredConditionId="condition:T2"}] []
    e <- required (execute (changedConditions (const c) initial))
    check "all/any condition trace children retained" (map (length . resolvedConditionChildren . registrationTriggerResult) (presumptionReportDerivations (presumptionEvaluationReport e)) == [2])
  -- Wrong-scope inputs are not reused across independent analyses.
  let scopeB=Scope "person:B" "event:B"
      b=base {documentAnalyses=documentAnalyses base ++ [a {analysisId="analysis:B",analysisScope=scopeB,analysisAssessments=map (<>"-B") (analysisAssessments a)} | a <- documentAnalyses base],
        documentAssessments=documentAssessments base ++ [x {assessmentId=assessmentId x<>"-B",assessmentScope=scopeB,assessmentClassification=Classification NotProved} | x <- documentAssessments base]}
      scoped=initial {presumptionProofDocument=b,presumptionRegistrations=[reg {registeredAnalyses=["analysis:synthetic","analysis:B"]}]}
  aResult <- required (execute scoped)
  bResult <- required (compilePresumptionAnalysis scoped "analysis:B" >>= evaluatePresumptionAnalysis)
  check "actor isolation" (reportConclusion (presumptionReportProof (presumptionEvaluationReport aResult)) == "satisfied" && reportConclusion (presumptionReportProof (presumptionEvaluationReport bResult)) == "not_satisfied")
  -- Drafts have inventory and no invented computed values; repeated provenance retained.
  draft <- required (projectPresumptionAuthored (missing "assessment:R" initial) "analysis:synthetic")
  check "draft missing is not unresolved" (map openState (presumptionProjectionOpenInputs (presumptionProjectionData draft)) == ["missing"])
  check "draft no computation" (all ((== Nothing) . projectedNodeComputed) (presumptionProjectionNodes (presumptionProjectionData draft)))
  let repeated=editBase (\d -> d {documentAssertions=[CaseAssertion "assertion:case" "Independent synthetic assertion" (Scope "other" "other") [SourceRef "source:synthetic" Nothing,SourceRef "source:synthetic" Nothing]],
        documentAssessments=[x {assessmentBasis="case_material",assessmentAssertions=["assertion:case","assertion:case"]} | x <- documentAssessments d],
        documentAnnotations=[Annotation "annotation:repeat" ["K","K"] "Repeated retained reference, no evidence weight." "draft"]})
        (editReg (\r -> r {registeredSources=[SourceRef "source:synthetic" Nothing,SourceRef "source:synthetic" Nothing]}) initial)
  forM_ [initial,multipleRoutes,repeated,skippedGuard,grouped] $ \d -> do
    replay <- required (decodePresumptionDocument (encodePresumptionDocument d))
    check "exact document round trip" (replay == d)
    e <- required (execute d); e2 <- required (execute replay)
    p <- required (projectPresumptionEvaluation e); p2 <- required (projectPresumptionEvaluation e2)
    check "projection deterministic replay" (encodePresumptionProjection p == encodePresumptionProjection p2)
    if d == repeated then do
      let allEdges=presumptionProjectionEdges (presumptionProjectionData p)
          count kind owner target=length [edgeRow | edgeRow <- allEdges,projectedEdgeKind edgeRow == kind,projectedEdgeFrom edgeRow == objectProjectionId owner,projectedEdgeTo edgeRow == objectProjectionId target]
      check "repeated assertion/provenance entries preserved" (count "assessment_assertion" "assessment:K" "assertion:case" == 2)
      check "repeated annotation entries preserved" (count "annotation_about" "annotation:repeat" "K" == 2)
      check "repeated registration sources preserved" (count "original_source" "registration:knowledge" "source:synthetic" == 2)
    else pure ()
    check "projection endpoint/ID integrity" (null (validatePresumptionProjection (presumptionProjectionData p)))
    focus <- required (inspectPresumptionTarget p "K")
    if d == grouped then check "downstream grouped ancestor recovered" (map observationNode (presumptionFocusAncestors focus) == ["group"]) else pure ()
    if d == repeated then check "cross-context assertion preserved" (map assertionScope (presumptionFocusAssertions focus) == [Scope "other" "other"]) else pure ()
    forM_ (presumptionFocusOccurrences focus) $ \o -> do
      f <- required (inspectPresumptionTarget p (projectedNodeId o))
      check "occurrence focus" (presumptionFocusInput f == presumptionFocusInput focus)
    view <- required (presumptionReferenceView p "K" [])
    check "view partitions" (null (validatePresumptionView p view))
    _ <- required (encodePresumptionViewJson p view); _ <- required (encodePresumptionViewXml p view); _ <- required (encodePresumptionViewSvg p view)
    check "unknown focus object diagnostic" (case inspectPresumptionTarget p "unknown" of Left errors -> "unknown" `elem` concatMap diagnosticObjects errors; Right _ -> False)
    let revision=revise "R" Proved d
    check "stale snapshot rejected" (case projectPresumptionEvaluationOn revision e of Left _ -> True; Right _ -> False)
    e3 <- required (execute revision)
    check "revision creates snapshot" (presumptionSnapshotId (presumptionEvaluationSnapshot e) /= presumptionSnapshotId (presumptionEvaluationSnapshot e3))
  mda <- required mdaDocument
  mdaE <- required (execute mda); mdaP <- required (projectPresumptionEvaluation mdaE)
  inspection <- required (inspectPresumptionTarget mdaP "K")
  let anchored=[ref | ref <- presumptionFocusSources inspection, referenceSpan ref /= Nothing]
  excerpts <- traverse (required . recoverPresumptionSource mdaP) anchored
  check "original MDA text recovered" (not (null excerpts) && all (maybe False (T.isPrefixOf "Any person who is proved or presumed") . excerptText) excerpts)
  let sid=presumptionSnapshotId (presumptionEvaluationSnapshot mdaE)
  expanded <- required (presumptionReferenceView mdaP "K" ["source:mda18"])
  check "source expansion no authored change" (presumptionSnapshotId (presumptionProjectionSnapshot (presumptionProjectionData mdaP)) == sid && null (validatePresumptionView mdaP expanded))
  -- Existing backend rejects spans outside registration owner; adapter generates
  -- contained spans and maps original anchors separately.
  raw <- BS.readFile (root </> "test/fixtures/presumption-authoring/P1-active.reference.json") >>= required . decodeJson
  let alter (JObj fields)=JObj [(key,if key=="presumptions" then case value of
              JArr [JObj parts] -> JArr [JObj [(k,if k=="span" then JObj [("start",JNum 0),("end",JNum 0),("start_line",JNum 1),("start_col",JNum 1),("end_line",JNum 1),("end_col",JNum 1)] else v) | (k,v) <- parts]]
              _ -> value else value) | (key,value) <- fields]
      alter x=x
  check "condition span outside registration rejected by authoritative decoder" (case Backend.decodePresumptionRequest (alter raw) >>= Backend.validatePresumptionRequest of Left e -> C.diagCode e == "KINV003"; Right _ -> False)
  putStrLn "presumption authoring: 14 independent request parity cases; P1–P7, chains, scope, strict JSON, negatives, replay/projection/source/snapshot checks passed"
  where
    parity name d = do
      compiled <- required (compilePresumptionAnalysis d "analysis:synthetic")
      e <- required (evaluatePresumptionAnalysis compiled)
      refBytes <- BS.readFile (root </> "test/fixtures/presumption-authoring" </> T.unpack name <> ".reference.json")
      reference <- required (decodeJson (runLine refBytes))
      actual <- required (decodeJson (presumptionEvaluationResponse e))
      let mappings=presumptionCompiledMappings compiled
          proof=presumptionProofCompilation compiled
          ids=Map.fromList ([(presumptionMappingKernel m,presumptionMappingAuthored m) | m <- mappings,presumptionMappingKind m `elem` ["registration","condition_input"]]
            ++ [(mappedKernelRequirement m,mappedNode m) | m <- compiledRequirements proof]
            ++ [(identityKernelId m,authored) | m <- compiledIdentities proof,identityKind m == "rule",authored:_ <- [identityAuthoredIds m]])
          normal (JStr value)=JStr (Map.findWithDefault value value ids)
          normal (JArr xs)=JArr (map normal xs)
          normal (JObj xs)=JObj [(key,normal value) | (key,value) <- xs,key `notElem` ["span","source_id"]]
          normal x=x
          list key value=case lookupField key value of Just (JArr xs) -> xs; _ -> []
          text key value=lookupField key value >>= textValue
          routeSemantic value=sortOnId [normal x | x <- list "presumption_derivations" value]
          sortOnId xs=map snd (sortOn fst [(maybe "" id (text "presumption_id" x),x) | x <- xs])
          -- Sort JSON objects through bytes, preserving all semantic condition rows.
          routeBytes value=map encodeJson (routeSemantic value)
      putStrLn ("presumption independent parity " <> T.unpack name <> ": reference=" <> show (text "status" reference) <> ", SDK=" <> show (text "status" actual) <> ", routes=" <> show (map registrationRouteState (presumptionReportDerivations (presumptionEvaluationReport e))))
      check (T.unpack name <> " overall parity") (text "status" actual == text "status" reference)
      check (T.unpack name <> " full condition/route/direct/effective parity") (routeBytes actual == routeBytes reference)
      forM_ (reportRules (presumptionReportProof (presumptionEvaluationReport e))) $ \r -> do
        let found expectedKey wanted value=find ((== Just wanted) . text expectedKey) (list "rules" value)
        case (found "id" (ruleKernelId r) actual,found "id" (ruleAuthoredId r) reference) of
          (Just x,Just y) -> do
            check "rule status parity" (text "status" x == text "status" y)
            let observations z=sort [encodeJson (normal (JObj [(field,value) | (field,value) <- fields, field `elem`
                      ["leaf_id","proof_status","satisfaction","direct_satisfaction","effective_satisfaction","active_presumption_ids","unresolved_presumption_ids"]]))
                      | JObj fields <- list "proof_observations" z]
                guards z=sort [encodeJson (normal (JObj [(field,value) | (field,value) <- fields,field `elem` ["target_rule","target_status","guard_status","applicable"]])) | branch <- list "branches" z,JObj fields <- list "exceptions" branch]
                branches z=[(text "status" b,text "reason" b) | b <- list "branches" z]
                traces z=sort [(text "id" (normal tr),text "kind" tr,text "value" tr) | tr <- list "trace" z]
            check "proof direct/effective/active-unresolved IDs parity" (observations x == observations y)
            check "exception behavior parity" (guards x == guards y)
            check "branch reason and trace parity" (branches x == branches y && traces x == traces y)
          (Nothing,Nothing) -> check "absent guard trace corresponds to not_evaluated" (ruleEvaluation r == "not_evaluated")
          _ -> fail "different evaluated rule sets"
