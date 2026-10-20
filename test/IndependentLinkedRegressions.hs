{-# LANGUAGE OverloadedStrings #-}
-- Retained from the independent review's IndependentProbe.hs / BoundaryProbe.hs.
-- No LinkedExample or existing implementation-test helper supplies expectations.
module IndependentLinkedRegressions (runIndependentLinkedRegressions) where

import Control.Monad (forM_, unless)
import Data.List (find)
import Data.Text (Text)
import Data.Time.Calendar (fromGregorian)
import Yuho.Authoring

node :: Text -> Text -> LawNode
node k t = LawNode k t k Nothing Nothing []

sa, sb :: Scope
sa = Scope "person:A" "event:A"
sb = Scope "person:B" "event:B"

assessment :: Text -> Text -> Scope -> SuppliedStatus -> Assessment
assessment k input scope status = Assessment k input scope (Classification status)
  "independent stipulated class" "reviewer" "synthetic_fixture" "assumption" [] []

inputs :: [Text]
inputs = ["gain","loss","ordinary","knowledge"]

base :: AuthoringDocument
base = AuthoringDocument linkedAuthoringFormat "probe:document"
  (LawDefinition "probe:law" "1"
    (map (uncurry node) [("def","definition"),("root","any"),("intent","any"),("standards","all"),("rA","rule"),("rB","rule")]
      ++ map (`node` "input") inputs)
    [LawEdge "body" "def" "root" "defines",LawEdge "route1" "root" "intent" "member",LawEdge "route2" "root" "standards" "member",
     LawEdge "gain-edge" "intent" "gain" "member",LawEdge "loss-edge" "intent" "loss" "member",
     LawEdge "ordinary-edge" "standards" "ordinary" "member",LawEdge "knowledge-edge" "standards" "knowledge" "member",
     LawEdge "useA" "rA" "def" "use",LawEdge "useB" "rB" "def" "use"] []) [] []
  (supplied "A:" sa [Proved,NotProved,Proved,NotProved]
    ++ supplied "B:" sb [NotProved,NotProved,Proved,Unresolved NotDetermined]
    ++ [assessment "alt:gain" "gain" sa NotProved])
  [Analysis "A" "rA" sa (map ("A:" <>) inputs) date,Analysis "B" "rB" sb (map ("B:" <>) inputs) date] [] [] []
  where date = fromGregorian 2021 12 31
        supplied label scope = zipWith (\k status -> assessment (label <> k) k scope status) inputs

must :: Show e => Either e a -> IO a
must = either (fail . show) pure
check :: String -> Bool -> IO ()
check label ok = unless ok (fail ("independent linked regression: " <> label))
eval :: AuthoringDocument -> Text -> IO Evaluation
eval doc key = must (compileAnalysis doc key >>= evaluateAnalysis)
set :: Text -> SuppliedStatus -> AuthoringDocument -> AuthoringDocument
set key status doc = doc {documentAssessments=[if assessmentId a == key
  then a {assessmentClassification=Classification status} else a | a <- documentAssessments doc]}

runIndependentLinkedRegressions :: IO ()
runIndependentLinkedRegressions = do
  a <- eval base "A"; b <- eval base "B"
  b2 <- eval (set "A:gain" NotProved base) "B"
  let conclusion = reportConclusion . evaluationReport
      semantic e = [(observationNode r,observationComputed r,observationEvaluation r,observationSkipReason r,
        assessmentClassification <$> observationAssessment r) | r <- reportRequirements (evaluationReport e)]
  check "explicit independent A/B outcomes" (conclusion a == "satisfied" && conclusion b == "unresolved")
  check "no cross-scope leakage at any requirement" (semantic b == semantic b2 && conclusion b == conclusion b2)
  pa <- must (projectEvaluation a); pb <- must (projectEvaluation b)
  fa <- must (focusRequirement pa (AuthoredRequirement "gain")); fb <- must (focusRequirement pb (AuthoredRequirement "gain"))
  check "different scoped occurrences and observations" (projectedNodeId (explanationOccurrence fa) /= projectedNodeId (explanationOccurrence fb)
    && projectedNodeObservation (explanationOccurrence fa) /= projectedNodeObservation (explanationOccurrence fb))
  let same = base {documentAnalyses=documentAnalyses base ++ [Analysis "A-alternative" "rA" sa
        ["alt:gain","A:loss","A:ordinary","A:knowledge"] (fromGregorian 2021 12 31)]}
  original <- eval same "A"; alternative <- eval same "A-alternative"
  po <- must (projectEvaluation original); pt <- must (projectEvaluation alternative)
  fo <- must (focusRequirement po (AuthoredRequirement "gain")); ft <- must (focusRequirement pt (AuthoredRequirement "gain"))
  check "same scope structural alignment without result alias" (conclusion original == "satisfied" && conclusion alternative == "not_satisfied"
    && projectedNodeId (explanationOccurrence fo) == projectedNodeId (explanationOccurrence ft)
    && projectedNodeObservation (explanationOccurrence fo) /= projectedNodeObservation (explanationOccurrence ft))
  check "selected assessments remain independent" (fmap (assessmentId . contextAssessment) (explanationSelected fo) == Just "A:gain"
    && fmap (assessmentId . contextAssessment) (explanationSelected ft) == Just "alt:gain")
  retained <- must (inspectAssessment po "alt:gain")
  check "unselected alternative has no computation" (not (inspectionSelected retained)
    && all (\x -> applicationComputed x == Nothing && applicationObservation x == Nothing && applicationEvaluation x == "not_applicable") (inspectionApplications retained))
  -- Reviewer BoundaryProbe: the same definition in main and attached guard.
  -- Preserve AREUSE even when main false/unresolved would otherwise skip guard.
  forM_ [Proved,NotProved,Unresolved NotDetermined] $ \mainStatus -> do
    let doc = set "A:gain" mainStatus base
        law = documentLaw doc
        reuse = doc {documentLaw=law {lawNodes=node "guard" "rule":lawNodes law,
          lawEdges=lawEdges law ++ [LawEdge "exception" "rA" "guard" "exception",LawEdge "guard-use" "guard" "def" "use"]}}
        diagnostics = validationDiagnostics (validateAnalysis reuse "A")
    check "main/guard repeated primitive explicitly rejected" (any (\d -> diagnosticCode d == "AREUSE"
      && "A" `elem` diagnosticObjects d && "gain" `elem` diagnosticObjects d
      && "guard-use" `elem` diagnosticObjects d) diagnostics)
    check "invalid repeated use cannot compile" (case compileAnalysis reuse "A" of Left _ -> True; _ -> False)
  -- Independent admitted boundary: a disjoint guard input remains allowed.
  let law = documentLaw base
      disjoint = base {documentLaw=law {lawNodes=lawNodes law ++ [node "guard" "rule",node "guard-input" "input"],
        lawEdges=lawEdges law ++ [LawEdge "exception" "rA" "guard" "exception",LawEdge "guard-root" "guard" "guard-input" "requires"]},
        documentAssessments=documentAssessments base ++ [assessment "guard-class" "guard-input" sa Proved],
        documentAnalyses=[if analysisId x == "A" then x {analysisAssessments=analysisAssessments x ++ ["guard-class"]} else x | x <- documentAnalyses base]}
  defeated <- eval disjoint "A"
  check "disjoint guard admitted with unchanged policy" (conclusion defeated == "not_satisfied"
    && (ruleBranchReason =<< find ((== "rA") . ruleAuthoredId) (reportRules (evaluationReport defeated))) == Just "defeated")
  putStrLn "independent review regressions: scoped/same-scope assessment isolation and main/guard AREUSE boundary passed"
