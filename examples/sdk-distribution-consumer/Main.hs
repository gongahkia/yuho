{-# LANGUAGE OverloadedStrings #-}
module Main (main) where
import Control.Monad (unless, forM_)
import qualified Data.ByteString as BS
import Data.Text (Text)
import Data.Time.Calendar (fromGregorian)
import System.Directory (createDirectoryIfMissing)
import System.Environment (getArgs)
import System.FilePath ((</>))
import Yuho.Authoring

require :: Show e => Either e a -> IO a
require = either (fail . show) pure
check :: String -> Bool -> IO ()
check label ok = unless ok (fail label)
sc :: Scope
sc = Scope "actor:A" "context:review"
original :: SourceRecord
original = SourceRecord "source:review" "synthetic" Nothing (Just "é猫\nreview")
node :: Text -> Text -> LawNode
node key kind = LawNode key kind key Nothing Nothing []
supplied :: Text -> Scope -> Text -> SuppliedStatus -> Assessment
supplied key scope input status = Assessment key input scope (Classification status)
  "Explicit synthetic assumption" "SDK distribution consumer" "synthetic_fixture" "assumption" [] []
proof :: SourceRef -> SuppliedStatus -> AuthoringDocument
proof ref status = AuthoringDocument authoringFormat "document:proof"
  (LawDefinition "law:proof" "research-1" [node "rule" "rule",node "target" "input"]
    [LawEdge "requires" "rule" "target" "requires"] ["Synthetic SDK test; no legal claim"])
  [original] [CaseAssertion "assertion" "Initial narrative" sc [ref]]
  [supplied "assessment:target" sc "target" status]
  [Analysis "analysis" "rule" sc ["assessment:target"] (fromGregorian 2026 1 1)] [] [] []
linked :: SourceRef -> AuthoringDocument
linked ref = (proof ref Proved) { documentFormat=linkedAuthoringFormat,documentId="document:linked"
  ,documentLaw=LawDefinition "law:linked" "research-1"
    [node "rule" "rule",node "rule:B" "rule",node "definition" "definition",node "target" "input"]
    [LawEdge "use:A" "rule" "definition" "use",LawEdge "use:B" "rule:B" "definition" "use",LawEdge "defines" "definition" "target" "defines"] []
  ,documentAssessments=[supplied "assessment:A" sc "target" Proved,supplied "assessment:B" (Scope "actor:B" "context:review") "target" NotProved]
  ,documentAnalyses=[Analysis "analysis:A" "rule" sc ["assessment:A"] (fromGregorian 2026 1 1),Analysis "analysis:B" "rule:B" (Scope "actor:B" "context:review") ["assessment:B"] (fromGregorian 2026 1 1)] }
typed :: SourceRef -> TypedDocument
typed ref = TypedDocument typedAuthoringFormat "document:typed" "law:typed" "research-1"
  [TypedEntityType (m "person"),TypedEntityType (m "resource")]
  [TypedEntity (m "actor:A") "person",TypedEntity (m "resource:R") "resource"]
  [TypedPredicate (m "relationship") [TypedArgument "person" "person",TypedArgument "resource" "resource"]]
  [TypedApplication (m "application") tuple]
  [TypedScalar (m "measurement") "integer" (Just "Dimensionless common scale 1"),TypedScalar (m "threshold") "integer" (Just "Dimensionless common scale 1")]
  [TypedExpression (m "expr:root") TypedAll,TypedExpression (m "expr:relationship") (GroundApplication "application"),TypedExpression (m "expr:comparison") (IntegerComparison "gt" "measurement" "threshold")]
  [TypedLink "typed:body" "typed:rule" "expr:root" "typed_body",TypedLink "typed:left" "expr:root" "expr:relationship" "typed_member",TypedLink "typed:right" "expr:root" "expr:comparison" "typed_member"]
  [TypedRule (m "typed:rule") "proposition"] [TypedProposition (m "proposition")]
  [TypedAssessment (m "assessment:relationship") "application" tuple sc TechnicalTrue "Synthetic relationship supplied" "SDK consumer" "synthetic_fixture" "assumption" []]
  [TypedValue (m "value:measurement") "measurement" sc (ExactInteger 36) "Exact synthetic integer" "SDK consumer",TypedValue (m "value:threshold") "threshold" sc (ExactInteger 35) "Exact synthetic integer" "SDK consumer"]
  [TypedAnalysis "typed:analysis" "typed:rule" "proposition" sc ["assessment:relationship"] ["value:measurement","value:threshold"]]
  [original] [] [] [] ["Technical test only; no physical conversion or legal conclusion"]
  where m key=TypedMeta key key Nothing [ref]
        tuple=GroundTuple "relationship" ["actor:A","resource:R"]
presumption :: SourceRef -> SuppliedStatus -> PresumptionDocument
presumption ref rebuttal = PresumptionDocument presumptionAuthoringFormat "document:presumption"
  base [AuthoredRegistration "registration" "Synthetic support" "target" ["analysis"] [ref]
    (RegisteredCondition "condition:trigger" "leaf_effective" (Just "trigger") [] [ref])
    (RegisteredCondition "condition:rebuttal" "leaf_effective" (Just "rebuttal") [] [ref])]
  ["Rebuttal adequacy is supplied by caller"]
  where p=proof ref NotProved
        extra=[supplied "assessment:trigger" sc "trigger" Proved,supplied "assessment:rebuttal" sc "rebuttal" rebuttal]
        base=p {documentLaw=(documentLaw p) {lawNodes=lawNodes (documentLaw p)++[node "trigger" "input",node "rebuttal" "input"]},documentAssessments=documentAssessments p++extra,documentAnalyses=[a {analysisAssessments=analysisAssessments a++map assessmentId extra} | a<-documentAnalyses p]}

main :: IO ()
main = do
  args <- getArgs
  out <- case args of [x] -> pure x; _ -> fail "one explicit output directory required"
  createDirectoryIfMissing True out
  let save name bytes=BS.writeFile (out </> name) bytes
  ref <- require (sourceAnchorCodePoints original 1 2)
  let p=proof ref Proved
  check "proof ready" (analysisReady (validateAnalysis p "analysis"))
  save "proof.document.json" (encodeDocument p)
  pr <- require (decodeDocument (encodeDocument p))
  check "proof roundtrip" (p==pr)
  pe <- require (compileAnalysis pr "analysis" >>= evaluateAnalysis)
  check "proof satisfied" (reportConclusion (evaluationReport pe)=="satisfied")
  pp <- require (projectEvaluation pe)
  require (encodeProjection pp) >>= save "proof.projection.json"
  save "proof.report.json" (encodeRecord (evaluationReport pe))
  require (inspectAssessment pp "assessment:target") >>= save "proof.inspection.json" . encodeRecord
  excerpt <- require (recoverOriginalSource pp ref)
  check "exact Unicode source" (excerptText excerpt==Just "猫")
  save "source-recovery.json" (encodeRecord excerpt)
  pv <- require (applicationView pp (FocusInput "target"))
  save "proof.bindings.json" (encodeRecord pv)
  require (encodeViewSvg pp pv) >>= save "proof.svg"
  require (encodeViewXml pp pv) >>= save "proof.xml"
  require (encodeViewJson pp pv) >>= save "proof.view.json"
  changed <- require (editCaseAssertion "assertion" (\a -> a {assertionDescription="Explicitly revised narrative"}) p)
  ce <- require (compileAnalysis changed "analysis" >>= evaluateAnalysis)
  check "new snapshot" (snapshotId (evaluationSnapshot pe)/=snapshotId (evaluationSnapshot ce))
  check "stale refused" (case projectEvaluationOn changed pe of Left ds -> any ((=="PSTALE").diagnosticCode) ds; _ -> False)
  require (compareAnalyses pe ce) >>= save "proof.comparison.json" . encodeRecord
  let ld=linked ref
  save "linked.document.json" (encodeDocument ld)
  lr <- require (decodeDocument (encodeDocument ld))
  forM_ ["analysis:A","analysis:B"] $ \key -> do
    le <- require (compileAnalysis lr key >>= evaluateAnalysis)
    lp <- require (projectEvaluation le)
    info <- require (inspectDefinition lp "definition")
    check "two uses, one selected occurrence" (length (sharedUses info)==2 && length (sharedOccurrences info)==1)
    save (if key=="analysis:A" then "linked-A.inspection.json" else "linked-B.inspection.json") (encodeRecord info)
    focus <- require (focusRequirement lp (AuthoredRequirement "target"))
    require (inspectDefinitionOccurrence lp (projectedNodeId (explanationOccurrence focus))) >>= save (if key=="analysis:A" then "linked-A.occurrence.json" else "linked-B.occurrence.json") . encodeRecord
    require (encodeProjection lp) >>= save (if key=="analysis:A" then "linked-A.projection.json" else "linked-B.projection.json")
  let td=typed ref
  check "typed ready" (typedAnalysisReady (validateTypedAnalysis td "typed:analysis"))
  save "typed.document.json" (encodeTypedDocument td)
  tr <- require (decodeTypedDocument (encodeTypedDocument td))
  te <- require (compileTypedAnalysis tr "typed:analysis" >>= evaluateTypedAnalysis)
  check "all grounded observations satisfied" (length (typedReportExpressions (typedEvaluationReport te))==3 && all ((=="satisfied").typedObservedStatus) (typedReportExpressions (typedEvaluationReport te)))
  tp <- require (projectTypedEvaluation te)
  require (encodeTypedProjection tp) >>= save "typed.projection.json"
  save "typed.report.json" (encodeRecord (typedEvaluationReport te))
  require (inspectTypedExpression tp "expr:comparison") >>= save "typed.inspection.json" . encodeRecord
  tv <- require (typedReferenceView tp (TypedExpressionFocus "expr:comparison") [])
  require (encodeTypedViewSvg tp tv) >>= save "typed.svg"
  forM_ [("active",NotProved,"active","satisfied"),("rebutted",Proved,"rebutted","not_satisfied")] $ \(name,status,route,conclusion) -> do
    let pd=presumption ref status
    check "presumption ready" (presumptionAnalysisReady (validatePresumptionAnalysis pd "analysis"))
    save (name<>".document.json") (encodePresumptionDocument pd)
    reloaded <- require (decodePresumptionDocument (encodePresumptionDocument pd))
    ev <- require (compilePresumptionAnalysis reloaded "analysis" >>= evaluatePresumptionAnalysis)
    let report=presumptionEvaluationReport ev
    check "registration state" (map registrationRouteState (presumptionReportDerivations report)==[route])
    check "presumption conclusion" (reportConclusion (presumptionReportProof report)==conclusion)
    check "direct classification retained" (all ((=="not_satisfied").effectiveDirectValue) [l | l<-presumptionReportLeaves report,effectiveInput l=="target"])
    projection <- require (projectPresumptionEvaluation ev)
    require (encodePresumptionProjection projection) >>= save (name<>".projection.json")
    save (name<>".report.json") (encodeRecord report)
    require (inspectPresumptionTarget projection "target") >>= save (name<>".inspection.json") . encodeRecord
  let old=TemporalExpression "expression:old" "old" "2024-01-01" (Just "2025-01-01") p "analysis" [ref] [ref] Nothing
      new=TemporalExpression "expression:new" "new" "2025-01-01" Nothing (proof ref NotProved) "analysis" [ref] [ref] (Just "expression:old")
      temporal=TemporalDocument temporalAuthoringFormat "document:temporal" "work:synthetic" [old,new] [original] ["Authored historical intervals"] ["No applicability determination"]
  save "temporal.document.json" (encodeTemporalDocument temporal)
  temporalReload <- require (decodeTemporalDocument (encodeTemporalDocument temporal))
  forM_ [("2024-12-31","expression:old"),("2025-01-01","expression:new")] $ \(date,expected) -> do
    ev <- require (compileTemporalAnalysis temporalReload (Just date) >>= evaluateTemporalAnalysis)
    check "adjacent date selection" (temporalExpressionId (selectionExpression (temporalEvaluationSelection ev))==expected)
    projection <- require (projectTemporalEvaluation ev)
    require (encodeTemporalProjection projection) >>= save (if expected=="expression:old" then "temporal-old.projection.json" else "temporal-new.projection.json")
  let incomplete=p {documentAssessments=[],documentAnalyses=[a {analysisAssessments=[]} | a<-documentAnalyses p]}
      destination=proofInputDestination incomplete "analysis"
  binding <- require (makeComputedInputBinding "binding:independent" te "expr:relationship" destination "target" (ComputedStatusPolicy computedStatusMapping "not_determined") "Explicit technical status mapping; no evidential conclusion" [ref])
  let bridge=ComputedInputDocument computedInputFormat "workflow:independent" td destination binding
  check "bridge valid" (null (validateComputedInput bridge))
  save "computed.document.json" (encodeComputedInputDocument bridge)
  br <- require (decodeComputedInputDocument (encodeComputedInputDocument bridge))
  be <- require (executeComputedInputWith br te)
  check "computed proof result" (reportConclusion (computedDownstreamReport (computedInputReport be))=="satisfied")
  bp <- require (projectComputedInput be)
  check "navigation valid" (null (validateComputedProjection (computedProjectionData bp)))
  save "computed.projection.json" (encodeComputedProjection bp)
  save "computed.report.json" (encodeRecord (computedInputReport be))
  bv <- require (computedInputReferenceView bp)
  save "computed.bindings.json" (encodeRecord bv)
  require (encodeComputedInputViewSvg bp bv) >>= save "computed.svg"
  replay <- require (executeComputedInput br >>= projectComputedInput)
  check "deterministic replay" (encodeComputedProjection replay==encodeComputedProjection bp)
  save "summary.json" (encodeRecord (["proof","linked-two-scopes","ground-relationship","exact-integer","active-and-rebutted","adjacent-temporal","computed-proof","source-recovery","projection","focused-view","stale-refusal","comparison","save-reload","deterministic-replay"] :: [Text]))
  putStrLn "Independent public-facade consumer: all asserted workflows passed"
