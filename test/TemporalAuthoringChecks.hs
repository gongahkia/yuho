{-# LANGUAGE OverloadedStrings #-}
module TemporalAuthoringChecks (runTemporalAuthoringChecks) where
import Control.Monad (forM_, unless)
import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as KM
import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as BL
import Data.List (find, sort)
import Data.Maybe (isNothing)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import System.FilePath ((</>))
import Yuho.Authoring
import Yuho.Surface.Temporal (loadAuthoredInput)
import Yuho.Surface.Modules (AuthoredModel(..))
import Yuho.Surface.Compile (compileParsed)
import qualified Yuho.Surface.Token as S
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProof)
import qualified Yuho.SuppliedProofStatus.Types as P
import Yuho.Protocol.Json (decodeJson)
import Yuho.Exception.Types (ExceptionTrace(..))
import TemporalExamples
check :: String -> Bool -> IO ()
check label ok=unless ok (fail ("temporal SDK: "<>label))
required :: Show e => Either e a -> IO a
required=either (fail . show) pure
runTemporalAuthoringChecks :: FilePath -> IO ()
runTemporalAuthoringChecks root=do
  let d=syntheticTemporal
      fixture=root</>"test/fixtures/temporal-sdk"
      path=fixture</>"model.yh"
      scenario date=UTF8.encodeUtf8 ("temporal-scenario Trial { conduct-date "<>date<>"; input \"classifications.yh\"; }")
      good=[("2020-01-01","expr:old","not_satisfied"),("2023-12-31","expr:old","not_satisfied"),("2024-01-01","expr:new","satisfied"),("2024-01-02","expr:new","satisfied"),("2040-02-29","expr:new","satisfied"),("2024-02-29","expr:new","satisfied")]
  model<-BS.readFile path
  forM_ good $ \(date,wanted,status)->do
    s<-required (selectTemporalExpression d (Just date))
    check "hand specified selection" (temporalExpressionId (selectionExpression s)==wanted && selectionConductDate s==date)
    (legacy,supplied)<-loadAuthoredInput path model (Just (fixture</>"scenario.yh",scenario date)) >>= required
    check "legacy identity and date metadata" (any (\(_,key,detail)->key==wanted && ("conduct-date="<>date) `T.isPrefixOf` detail) (authoredImports legacy))
    bytes<-required (compileParsed path (authoredModel legacy) supplied)
    json<-required (decodeJson bytes)
    decoded<-required (decodeProofRequest json)
    checked<-required (validateProofRequest decoded)
    reference<-required (evaluateProof checked)
    actual<-required (executeTemporal (guarded d) date)
    let report=evaluationReport (temporalEvaluationProof actual)
        traces=concatMap P.proofRuleTrace (P.proofResultRules reference)
    check "overall independent expectation and parity" (reportConclusion report==status && P.satisfactionText (P.proofResultStatus reference)==status)
    forM_ [("A","f:entry"),("B","f:no-authorization"),("C","f:knowledge"),("A-context","g:entry-with-context"),("group","g:offence-requirements"),("G","f:immediate-danger"),("H","f:rescue-purpose"),("guard-group","g:emergency-requirements")] $ \(key,old)->do
      o<-maybe (fail "SDK observation missing") pure (find ((==key) . observationNode) (reportRequirements report))
      let ref=find ((==old) . P.proofTraceId) traces
      check "requirement status/evaluation parity" (observationComputed o==(P.satisfactionText . P.proofTraceStatus <$> ref) && observationEvaluation o==if isNothing ref then "not_evaluated" else "evaluated")
    check "branch reason parity" (all (\o -> ruleBranchReason o == (reasonName . P.proofBranchReason <$> (find ((== (if ruleAuthoredId o=="rule" then "p:entry" else "p:rescue")) . P.proofBranchId) (concatMap P.proofRuleBranches (P.proofResultRules reference))))) (reportRules report))
    check "guard execution and skip reason" (case reportExceptions report of
      [x] -> if status=="satisfied" then exceptionEvaluation x=="evaluated" && exceptionComputed x==Just "not_satisfied" && exceptionFired x==Just False
        else exceptionEvaluation x=="not_evaluated" && exceptionComputed x==Nothing && exceptionSkipReason x==Just "exception guard skipped because main branch: requirements_not_satisfied"
      _ -> False)
    p<-required (projectTemporalEvaluation actual)
    check "complete projection valid" (null (validateTemporalProjection (temporalProjectionData p)))
    forM_ [TemporalSetView,TemporalProvenanceView] $ \mode->do
      v<-required (temporalReferenceView p mode)
      check "view partition" (null (validateTemporalView p v))
      _<-required (encodeTemporalViewJson p v); _<-required (encodeTemporalViewXml p v); _<-required (encodeTemporalViewSvg p v)
      pure ()
    replay<-required (decodeTemporalDocument (encodeTemporalDocument d))
    again<-required (executeTemporal (guarded replay) date) >>= required . projectTemporalEvaluation
    check "saved replay exact projection" (temporalProjectionData p==temporalProjectionData again)
    putStrLn ("temporal parity "<>T.unpack date<>": legacy=SDK "<>T.unpack wanted<>" "<>T.unpack status)
  forM_ [("ordinary-unresolved","2023-12-31",Unresolved NotDetermined,NotProved,NotProved,"unresolved","requirements_unresolved"),
    ("guard-defeat","2024-01-01",NotProved,Proved,Proved,"not_satisfied","defeated"),
    ("guard-unresolved","2024-01-01",NotProved,Unresolved NotDetermined,Proved,"unresolved","exception_unresolved")] $ \(name,date,b,g,h,wanted,reason)->do
      let changed=(guarded d) {temporalExpressions=[e {temporalExpressionDocument=let doc=temporalExpressionDocument e in doc {documentAssessments=[a {assessmentClassification=Classification (case assessmentInput a of "B"->b;"G"->g;"H"->h;_->classificationStatus (assessmentClassification a))} | a<-documentAssessments doc]}} | e<-temporalExpressions (guarded d)]}
          input=T.replace "classifications.yh" (T.pack name<>".yh") (UTF8.decodeUtf8 (scenario date))
      (legacy,supplied)<-loadAuthoredInput path model (Just (fixture</>"scenario.yh",UTF8.encodeUtf8 input)) >>= required
      bytes<-required (compileParsed path (authoredModel legacy) supplied)
      reference<-required (decodeJson bytes) >>= required . decodeProofRequest >>= required . validateProofRequest >>= required . evaluateProof
      actual<-required (executeTemporal changed date)
      let report=evaluationReport (temporalEvaluationProof actual)
          traces=concatMap P.proofRuleTrace (P.proofResultRules reference)
          guards=[x | r<-P.proofResultRules reference,branch<-P.proofRuleBranches r,x<-P.proofBranchGuards branch]
      check "independent uncertainty/exception outcome" (reportConclusion report==wanted && P.satisfactionText (P.proofResultStatus reference)==wanted)
      forM_ [("A","f:entry"),("B","f:no-authorization"),("C","f:knowledge"),("A-context","g:entry-with-context"),("group","g:offence-requirements"),("G","f:immediate-danger"),("H","f:rescue-purpose"),("guard-group","g:emergency-requirements")] $ \(key,old)->do
        row<-maybe (fail "observation missing") pure (find ((==key) . observationNode) (reportRequirements report))
        let ref=find ((==old) . P.proofTraceId) traces
        check "uncertain and skipped requirement parity" (observationComputed row==(P.satisfactionText . P.proofTraceStatus <$> ref) && observationEvaluation row==if isNothing ref then "not_evaluated" else "evaluated")
      check "uncertainty branch reason" (any (\r->ruleAuthoredId r=="rule" && ruleBranchReason r==Just reason) (reportRules report))
      check "exception attachment parity" (case (guards,reportExceptions report) of
        ([],[x])->exceptionComputed x==Nothing && exceptionEvaluation x=="not_evaluated" && exceptionSkipReason x==Just ("exception guard skipped because main branch: "<>reason)
        ([ref],[x])->exceptionComputed x==Just (P.satisfactionText (exceptionTraceGuardStatus ref)) && exceptionFired x==Just (exceptionTraceFired ref) && exceptionEvaluation x=="evaluated"
        _->False)
      putStrLn ("temporal uncertainty/guard parity "<>name<>": legacy=SDK "<>T.unpack wanted<>" "<>T.unpack reason)
  forM_ ["2019-12-31","2023-02-29","2024-13-01","bad","2024-04-31"] $ \date->do
    check "SDK bad date rejected" (case selectTemporalExpression d (Just date) of Left _->True;Right _->False)
    result<-loadAuthoredInput path model (Just (fixture</>"scenario.yh",scenario date))
    check "legacy bad date rejected" (case result of Left _->True;Right _->False)
  forM_ ["2024-01-01 ","10000-01-01","2024-1-1"] $ \date->check "complete ISO JSON spelling" (case selectTemporalExpression d (Just date) of Left _->True;Right _->False)
  check "missing date" (case selectTemporalExpression d Nothing of Left x->any ((=="TACONDUCT") . diagnosticCode) x;Right _->False)
  let edits=[("gap",\e->e {temporalEffectiveTo=Just "2023-12-31"},"effective-to 2024-01-01","effective-to 2023-12-31"),
        ("overlap",\e->e {temporalEffectiveTo=Just "2024-01-02"},"effective-to 2024-01-01","effective-to 2024-01-02"),
        ("open-before-later",\e->e {temporalEffectiveTo=Nothing},"effective-to 2024-01-01","open-end"),
        ("end-before-start",\e->e {temporalEffectiveTo=Just "2019-01-01"},"effective-to 2024-01-01","effective-to 2019-01-01")]
  forM_ edits $ \(name,f,from,to)->do
    let invalid=updateExpression "expr:old" f d
    check (name<>" SDK rejects") (not (null (validateTemporalDocument invalid)))
    old<-loadAuthoredInput path (UTF8.encodeUtf8 (T.replace from to (UTF8.decodeUtf8 model))) (Just (fixture</>"scenario.yh",scenario "2024-01-01"))
    check (name<>" legacy rejects") (case old of Left x->S.diagnosticCode x `elem` ["SFT004","SFT005"];Right _->False)
  let editDoc f=updateExpression "expr:old" (\e->e {temporalExpressionDocument=f (temporalExpressionDocument e)})
      duplicate=updateExpression "expr:new" (\e->e {temporalExpressionId="expr:old"}) d
      wrongProfile=editDoc (\doc->doc {documentFormat=linkedAuthoringFormat}) d
      wrongAnalysis=updateExpression "expr:old" (\e->e {temporalExpressionAnalysis="unknown"}) d
      dangling=updateExpression "expr:old" (\e->e {temporalDateSources=[SourceRef "unknown" Nothing]}) d
      badSpan=updateExpression "expr:old" (\e->e {temporalDateSources=[SourceRef "source:dates" (Just (TextSpan 0 9999 1 1 1 10000))]}) d
  forM_ [duplicate,wrongProfile,wrongAnalysis,dangling,badSpan,d {temporalExpressions=[]},d {temporalExpressions=take 1 (temporalExpressions d)},d {temporalExpressions=concat (replicate 40 (temporalExpressions d))}] $ \invalid->check "object linked validation failure" (any (not . null . diagnosticObjects) (validateTemporalDocument invalid))
  let reversed=d {temporalExpressions=reverse (temporalExpressions d)}
  chosen<-required (selectTemporalExpression reversed (Just "2024-01-01"))
  check "declaration order follows legacy sorting" (temporalExpressionId (selectionExpression chosen)=="expr:new")
  let finite=updateExpression "expr:new" (\e->e {temporalEffectiveTo=Just "2025-01-01"}) d
  check "after finite final interval" (case selectTemporalExpression finite (Just "2025-01-01") of Left _->True;Right _->False)
  let missing=editDoc (\doc->doc {documentAnalyses=[a {analysisAssessments=[]} | a<-documentAnalyses doc]}) d
  _<-required (projectTemporalAuthored missing (Just "2023-12-31"))
  check "selected incomplete analysis cannot compile" (case compileTemporalAnalysis missing (Just "2023-12-31") of Left _->True;Right _->False)
  let wrongScope=editDoc (\doc->doc {documentAssessments=[a {assessmentScope=Scope "wrong-actor" "wrong-event"} | a<-documentAssessments doc]}) d
  check "selected scope mismatch cannot compile" (case compileTemporalAnalysis wrongScope (Just "2023-12-31") of Left errors->any (elem "expr:old" . diagnosticObjects) errors;Right _->False)
  let tooMany=d {temporalExpressions=[e {temporalExpressionId="budget:"<>T.pack (show i)} | (i,e)<-zip [1::Int ..] (take 65 (cycle (temporalExpressions d)))]}
  check "explicit expression budget" (any ((=="TALIMIT") . diagnosticCode) (validateTemporalDocument tooMany))
  let changed=editDoc (\doc->doc {documentAssessments=[a {assessmentClassification=Classification (Unresolved NotDetermined)} | a<-documentAssessments doc]}) d
  selected<-required (selectTemporalExpression changed (Just "2023-12-31"))
  check "assessment-independent selection" (temporalExpressionId (selectionExpression selected)=="expr:old")
  let mutate f=A.encode (f (A.toJSON d))
      inject (A.Object o)=A.Object (KM.insert "typo" (A.Bool True) o); inject x=x
      nested (A.Object o)=case KM.lookup "temporalExpressions" o of Just (A.Array xs)->A.Object (KM.insert "temporalExpressions" (A.toJSON (map inject (foldr (:) [] xs))) o);_->A.Object o
      nested x=x
  forM_ [inject,nested] $ \f->check "closed constructors" (case decodeTemporalDocument (BL.toStrict (mutate f)) of Left _->True;Right _->False)
  initial<-required (executeTemporal d "2023-12-31")
  within<-required (executeTemporal d "2023-12-30")
  boundary<-required (executeTemporal d "2024-01-01")
  let revised=updateExpression "expr:old" (\e->e {temporalEffectiveTo=Just "2023-12-31"}) (updateExpression "expr:new" (\e->e {temporalEffectiveFrom="2023-12-31"}) d)
      lawRevised=editDoc (\doc->let l=documentLaw doc in doc {documentLaw=l {lawRevision="new-label-revision"}}) d
      snapshot=temporalSnapshotId . temporalEvaluationSnapshot
  check "date snapshots independent of proof snapshot" (snapshot initial/=snapshot within && evaluationSnapshot (temporalEvaluationProof initial)==evaluationSnapshot (temporalEvaluationProof within))
  forM_ [(revised,"2023-12-31"),(lawRevised,"2023-12-31"),(d,"2024-01-01")] $ \(doc,date)->check "stale temporal attachment rejects" (case projectTemporalEvaluationOn doc (Just date) initial of Left _->True;Right _->False)
  check "cross law comparison not loosened" (case compareAnalyses (temporalEvaluationProof initial) (temporalEvaluationProof boundary) of Left _->True;Right _->False)
  oldProjection<-required (projectTemporalEvaluation initial)
  _<-required (temporalReferenceView oldProjection TemporalProvenanceView)
  check "focus and source display preserve snapshot" (temporalProjectionSelection (temporalProjectionData oldProjection)==temporalEvaluationSelection initial)
  let repeated=updateExpression "expr:old" (\e->e {temporalDateSources=temporalDateSources e++temporalDateSources e}) d
  repeatedProjection<-required (executeTemporal repeated "2023-12-31") >>= required . projectTemporalEvaluation
  let provenanceEdges=[x | x<-temporalProjectionEdges (temporalProjectionData repeatedProjection),projectedEdgeKind x=="effective_date_evidence"]
  check "repeated provenance preserved as distinct edges" (length provenanceEdges==3 && length (sort (map projectedEdgeId provenanceEdges))==3 && null (validateTemporalProjection (temporalProjectionData repeatedProjection)))
  statutory<-required section24Temporal
  forM_ [("2019-12-31","not_satisfied"),("2020-01-01","satisfied")] $ \(date,wanted)->do
    e<-required (executeTemporal statutory date)
    check "bounded s24 authored outcome" (reportConclusion (evaluationReport (temporalEvaluationProof e))==wanted)
  let firstDoc=map temporalExpressionDocument (temporalExpressions d)
  check "two independent law identities" (length (sort (map (lawId . documentLaw) firstDoc))==2)
  putStrLn "temporal SDK: interval parity, strict decoding, snapshots, projections and historical bounded expression checks passed"

reasonName :: P.ProofReason -> T.Text
reasonName r=case r of
  P.ProofSatisfied -> "satisfied"
  P.ProofRequirementsNotSatisfied -> "requirements_not_satisfied"
  P.ProofRequirementsUnresolved -> "requirements_unresolved"
  P.ProofDefeated -> "defeated"
  P.ProofExceptionUnresolved -> "exception_unresolved"
-- Explicit hand-authored equivalent to the legacy grammar's required exception.
-- The primary synthetic consumer remains precisely A AND/OR B, without a guard.
guarded :: TemporalDocument -> TemporalDocument
guarded d=d {temporalExpressions=[e {temporalExpressionDocument=add (temporalExpressionDocument e)} | e<-temporalExpressions d]}
  where
    add doc=doc {documentLaw=law {lawNodes=lawNodes law++[LawNode "A-context" "all" "A with always-proved synthetic context" Nothing Nothing [],LawNode "C" "input" "Synthetic always-proved knowledge" Nothing Nothing [],LawNode "guard" "rule" "Synthetic exception" Nothing Nothing [],LawNode "guard-group" "all" "All guard requirements" Nothing Nothing [],LawNode "G" "input" "Synthetic guard G" Nothing Nothing [],LawNode "H" "input" "Synthetic guard H" Nothing Nothing []],
        lawEdges=[if edgeId e=="member:A" then e {edgeTo="A-context"} else e | e<-lawEdges law]++[LawEdge "context:A" "A-context" "A" "member",LawEdge "member:C" "A-context" "C" "member",LawEdge "exception" "rule" "guard" "exception",LawEdge "guard-requires" "guard" "guard-group" "requires",LawEdge "guard-G" "guard-group" "G" "member",LawEdge "guard-H" "guard-group" "H" "member"]},
      documentAssessments=documentAssessments doc++[Assessment ("assessment:"<>key) key (Scope "actor:fixture" "event:fixed") (Classification value) "Explicit independent synthetic guard assumption" "Fixture author" "synthetic_fixture" "assumption" [] [] | (key,value)<-[("C",Proved),("G",NotProved),("H",NotProved)]],
      documentAnalyses=[a {analysisAssessments=analysisAssessments a++["assessment:C","assessment:G","assessment:H"]} | a<-documentAnalyses doc]}
      where law=documentLaw doc
