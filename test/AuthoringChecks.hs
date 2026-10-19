{-# LANGUAGE OverloadedStrings #-}
module AuthoringChecks (runAuthoringChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.List (find, sort)
import qualified Data.Map.Strict as Map
import Data.Maybe (isNothing)
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Data.Time.Calendar (fromGregorian)
import System.FilePath ((</>))
import Cheating
import Yuho.Authoring
import qualified Yuho.Core.Source as Core
import qualified Yuho.Core.Types as Core
import Yuho.Authoring.Validate (toCoreSpan)
import Yuho.Protocol.Json (decodeJson)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProof)
import qualified Yuho.SuppliedProofStatus.Types as Proof
import Yuho.Surface.Compile (compileSource)
import Yuho.Exception.Types (ExceptionTrace(..))

runAuthoringChecks :: FilePath -> IO ()
runAuthoringChecks root = do
  parity root
  reporting
  genericFragment
  refusals
  provenance
  putStrLn "authoring SDK: independent legacy parity, reports, comparisons, validation, snapshots and UTF-8 provenance passed"

runDoc :: AuthoringDocument -> IO Evaluation
runDoc doc = require (compileAnalysis doc "analysis:cheating" >>= evaluateAnalysis)

fault :: Text
fault = "f:property-fraudulent-or-dishonest"

genericFragment :: IO ()
genericFragment = do
  let scope = Scope "independent-actor" "independent-context"
      node key kind = LawNode key kind "display only" Nothing Nothing []
      law = LawDefinition "law:fixture" "arbitrary-revision"
        [node "selected-rule" "rule",node "choice" "any",node "input-α" "input",node "input-β" "input"]
        [LawEdge "root-edge" "selected-rule" "choice" "requires",
         LawEdge "left-edge" "choice" "input-α" "member",LawEdge "right-edge" "choice" "input-β" "member"] []
      assessment key input status = Assessment key input scope (Classification status)
        "explicit fixture assumption" "test caller" "synthetic_fixture" "assumption" [] []
      doc = AuthoringDocument authoringFormat "document:fixture" law [] []
        [assessment "assessment:left" "input-α" Proved,assessment "assessment:right" "input-β" NotProved]
        [Analysis "analysis:fixture" "selected-rule" scope ["assessment:left","assessment:right"]
          (fromGregorian 2027 1 1)] [] [] []
  result <- require (compileAnalysis doc "analysis:fixture" >>= evaluateAnalysis)
  check "fragment is general, with optional guard and arbitrary IDs/date"
    (reportConclusion (evaluationReport result) == "satisfied" && null (reportExceptions (evaluationReport result))
      && length (reportRequirements (evaluationReport result)) == 3)

parity :: FilePath -> IO ()
parity root = do
  let base = root </> "research/singapore/offence-corpus-pilot"
      modelPath = base </> "cheating-mischief.yh"
      defeat = foldl (\doc input -> withStatus input Proved doc) cheatingDocument
        ["f:unsoundness-time","f:nature-causation","f:nature-incapacity"]
      cases = [("01_property_form_satisfied",cheatingDocument),
        ("08_property_fault_unresolved",withStatus fault (Unresolved NotDetermined) cheatingDocument),
        ("10_section84_defeats",defeat),
        ("05_property_fault_not_proved",withStatus fault NotProved cheatingDocument)]
  model <- BS.readFile modelPath
  forM_ cases $ \(name,doc) -> do
    let scenarioPath = base </> "scenarios/cheating" </> name <> ".yh"
    scenario <- BS.readFile scenarioPath
    -- Independent legacy checking/lowering oracle; never adapter output.
    legacyBytes <- require (compileSource modelPath model (Just (scenarioPath,scenario)))
    value <- require (decodeJson legacyBytes)
    decoded <- require (decodeProofRequest value)
    validated <- require (validateProofRequest decoded)
    legacy <- require (evaluateProof validated)
    adapted <- runDoc (doc {documentAnalyses=[a {analysisReferenceDate=fromGregorian 2026 9 13}
      | a <- documentAnalyses doc]})
    let report = evaluationReport adapted
    check (name <> " overall parity") (reportConclusion report == Proof.satisfactionText (Proof.proofResultStatus legacy))
    forM_ legacyRequirementMap $ \(authored,legacyId) -> do
      observation <- requireMaybe "authored observation" (find ((== authored) . observationNode) (reportRequirements report))
      let old = find ((== legacyId) . Proof.proofTraceId)
            (concatMap Proof.proofRuleTrace (Proof.proofResultRules legacy))
      check (name <> " requirement parity " <> Text.unpack authored)
        (observationComputed observation == (Proof.satisfactionText . Proof.proofTraceStatus <$> old)
         && observationEvaluation observation == if isNothing old then "not_evaluated" else "evaluated")
    forM_ [("o:cheating","r:section415-candidate"),("x:section84","r:section84")] $ \(authored,legacyId) -> do
      observation <- requireMaybe "authored rule" (find ((== authored) . ruleAuthoredId) (reportRules report))
      let old = find ((== legacyId) . Proof.proofRuleId) (Proof.proofResultRules legacy)
          reasons = fmap (map Proof.proofBranchReason . Proof.proofRuleBranches) old
      check (name <> " rule and branch parity")
        (ruleComputed observation == (Proof.satisfactionText . Proof.proofRuleStatus <$> old)
         && fmap (:[]) (ruleBranchReason observation) == fmap (map reasonName) reasons)
    check (name <> " explicit requirement coverage")
      (sort (map observationNode (reportRequirements report)) == sort (map fst legacyRequirementMap))
    let oldGuards = [g | r <- Proof.proofResultRules legacy, Proof.proofRuleId r == "r:section415-candidate",
          branch <- Proof.proofRuleBranches r, g <- Proof.proofBranchGuards branch]
    check (name <> " guard behaviour parity") (case (oldGuards,reportExceptions report) of
      ([],[g]) -> exceptionEvaluation g == "not_evaluated" && exceptionFired g == Nothing
      ([old],[g]) -> exceptionComputed g == Just (Proof.satisfactionText (exceptionTraceGuardStatus old))
        && exceptionFired g == Just (exceptionTraceFired old)
      _ -> False)
  where
    reasonName r = case r of
      Proof.ProofSatisfied -> "satisfied"
      Proof.ProofRequirementsNotSatisfied -> "requirements_not_satisfied"
      Proof.ProofRequirementsUnresolved -> "requirements_unresolved"
      Proof.ProofDefeated -> "defeated"
      Proof.ProofExceptionUnresolved -> "exception_unresolved"

-- Explicit correspondence for this independently authored example. Generated
-- IDs, source offsets, penalties and digests are intentionally not compared.
legacyRequirementMap :: [(Text,Text)]
legacyRequirementMap = [(key,key) | key <-
  ["f:deception","f:property-fraudulent-or-dishonest","f:property-delivery-or-retention",
   "f:intentional-inducement","f:induced-act-or-omission","f:damage-or-harm",
   "g:cheating-property-form","g:cheating-act-harm-form","g:cheating-forms","g:cheating-requirements",
   "f:unsoundness-time","f:nature-causation","f:nature-incapacity","f:wrong-causation",
   "f:ordinary-wrongfulness-incapacity","f:contrary-law-incapacity","f:control-causation","f:control-incapacity",
   "g:nature","g:wrongfulness","g:control","g:section84-routes","g:section84-requirements"]]

reporting :: IO ()
reporting = do
  base <- runDoc cheatingDocument
  pending <- runDoc pendingDocument
  negative <- runDoc (withStatus fault NotProved cheatingDocument)
  check "explicit uncertainty inventory" (map openState (reportOpenInputs (evaluationReport pending)) == ["unresolved"])
  externalPending <- runDoc (withStatus fault (Unresolved ExternalDecisionPending) cheatingDocument)
  check "unresolved reason preserved" (any (\o -> observationNode o == fault &&
    (assessmentClassification <$> observationAssessment o) == Just (Classification (Unresolved ExternalDecisionPending)))
    (reportRequirements (evaluationReport externalPending)))
  let unresolvedGuard = withStatus "f:unsoundness-time" (Unresolved NotDetermined)
        (withStatus "f:nature-causation" Proved (withStatus "f:nature-incapacity" Proved cheatingDocument))
  guardResult <- runDoc unresolvedGuard
  check "evaluated unresolved exception differs from skipped guard"
    (any (\g -> exceptionEvaluation g == "evaluated" && exceptionComputed g == Just "unresolved"
      && exceptionSkipReason g == Nothing) (reportExceptions (evaluationReport guardResult)))
  let missing = selectAssessments (filter (/= assessmentFor fault)) cheatingDocument
      draft = validateAnalysis missing "analysis:cheating"
  check "draft document-valid but cannot execute" (documentValid draft && not (analysisReady draft)
    && map openState (openInputs draft) == ["missing"])
  check "missing does not compile" (case compileAnalysis missing "analysis:cheating" of Left _ -> True; Right _ -> False)
  let pendingReport = evaluationReport pending
  check "skipped guard retains assessments without computed values"
    (all (\o -> observationEvaluation o == "not_evaluated" && observationComputed o == Nothing
       && observationSkipReason o /= Nothing
       && (observationKind o /= "input" || observationAssessment o /= Nothing))
      [o | o <- reportRequirements pendingReport, observationRule o == "x:section84"])
  check "groups have no invented assessments"
    (all (isNothing . observationAssessment) [o | o <- reportRequirements pendingReport, observationKind o /= "input"])
  check "not_proved retained beside evaluated non-satisfaction"
    (any (\o -> observationNode o == fault && observationComputed o == Just "not_satisfied"
      && (assessmentClassification <$> observationAssessment o) == Just (Classification NotProved)
      && observationEvaluation o == "evaluated") (reportRequirements (evaluationReport negative)))
  comparison <- require (compareAnalyses base pending)
  check "comparison separates selection and classification"
    (comparisonConclusionChanged comparison && any (\c -> changeInput c == fault && changeSelection c
      && changeClassification c) (comparisonAssessments comparison))
  let both = foldl (\d input -> withStatus input Proved d) cheatingDocument
        ["f:intentional-inducement","f:induced-act-or-omission","f:damage-or-harm"]
  bothResult <- runDoc both
  alternative <- runDoc (withStatus fault NotProved both)
  unchanged <- require (compareAnalyses bothResult alternative)
  check "changed input need not change conclusion"
    (not (comparisonConclusionChanged unchanged) && not (null (comparisonChanged unchanged))
     && any ((== "o:cheating") . changeObject) (comparisonUnchanged unchanged))
  metadata <- runDoc (modifyAssessment (assessmentFor fault) (\a -> a {assessmentReason="revised reason",assessmentIssuer="second caller"}) cheatingDocument)
  metadataDiff <- require (compareAnalyses base metadata)
  check "metadata-only change has no computed change"
    (null (comparisonChanged metadataDiff) && not (comparisonConclusionChanged metadataDiff)
     && any (\c -> changeAuthorship c && not (changeClassification c)) (comparisonAssessments metadataDiff)
     && snapshotId (evaluationSnapshot base) /= snapshotId (evaluationSnapshot metadata))
  reordered <- runDoc (selectAssessments reverse cheatingDocument)
  reorderedDiff <- require (compareAnalyses base reordered)
  check "selection is independent of array order" (null (comparisonAssessments reorderedDiff)
    && null (comparisonChanged reorderedDiff))
  let alteredCase = cheatingDocument {documentAssertions = [a {assertionDescription=assertionDescription a <> " (amended)"}
        | a <- documentAssertions cheatingDocument]}
  a <- require (compileAnalysis cheatingDocument "analysis:cheating")
  b <- require (compileAnalysis alteredCase "analysis:cheating")
  changedCase <- require (evaluateAnalysis b)
  caseDiff <- require (compareAnalyses base changedCase)
  check "snapshot retains content absent from kernel digest"
    (compiledRequest a == compiledRequest b && snapshotId (compiledSnapshot a) /= snapshotId (compiledSnapshot b)
      && any changeReferencedMaterial (comparisonAssessments caseDiff) && null (comparisonChanged caseDiff))
  let incompatible = cheatingDocument {documentLaw=(documentLaw cheatingDocument) {lawRevision="2"}}
  other <- runDoc incompatible
  check "incompatible revisions rejected" (case compareAnalyses base other of
    Left diagnostics -> any ((== "AINCOMPATIBLE") . diagnosticCode) diagnostics; Right _ -> False)
  forM_ [\d -> d {documentLaw=(documentLaw d) {lawScope=["different definition"]}},
         \d -> d {documentAnalyses=[a' {analysisReferenceDate=succ (analysisReferenceDate a')} | a' <- documentAnalyses d]},
         \d -> d {documentAssessments=[a' {assessmentScope=Scope "actor:other" "context:other"} | a' <- documentAssessments d],
           documentAssertions=[a' {assertionScope=Scope "actor:other" "context:other"} | a' <- documentAssertions d],
           documentAnalyses=[a' {analysisScope=Scope "actor:other" "context:other"} | a' <- documentAnalyses d]}] $ \change -> do
    result <- runDoc (change cheatingDocument)
    check "comparison definition/date/scope guard" (case compareAnalyses base result of Left _ -> True; Right _ -> False)

refusals :: IO ()
refusals = do
  let doc = cheatingDocument
      law = documentLaw doc
      changeLaw f = doc {documentLaw=f law}
      refused label code object changed = do
        let diagnostics = validationDiagnostics (validateAnalysis changed "analysis:cheating")
        check label (any (\d -> diagnosticCode d == code && object `elem` diagnosticObjects d) diagnostics)
  refused "duplicate identity" "ADUPLICATE" "o:cheating"
    (changeLaw (\l -> l {lawNodes=take 1 (lawNodes l) ++ lawNodes l}))
  refused "dangling edge" "AREFERENCE" "edge:bad"
    (changeLaw (\l -> l {lawEdges=LawEdge "edge:bad" "g:cheating-forms" "missing" "member":lawEdges l}))
  refused "cycle" "ACYCLE" "edge:cycle"
    (changeLaw (\l -> l {lawEdges=LawEdge "edge:cycle" "g:cheating-forms" "g:cheating-requirements" "member":lawEdges l}))
  refused "sharing" "ASHARING" "f:deception"
    (changeLaw (\l -> l {lawEdges=LawEdge "edge:shared" "g:cheating-property-form" "f:deception" "member":lawEdges l}))
  refused "unknown executable edge" "AUNSUPPORTED" "edge:unknown"
    (changeLaw (\l -> l {lawEdges=LawEdge "edge:unknown" "f:deception" "f:damage-or-harm" "supports":lawEdges l}))
  refused "unknown executable node" "AUNSUPPORTED" "f:deception"
    (changeLaw (\l -> l {lawNodes=[if nodeId n == "f:deception" then n {nodeKind="causal"} else n | n <- lawNodes l]}))
  refused "wrong target" "ATARGET" (assessmentFor fault)
    (modifyAssessment (assessmentFor fault) (\a -> a {assessmentInput="g:cheating-forms"}) doc)
  refused "wrong context" "ASCOPE" (assessmentFor fault)
    (modifyAssessment (assessmentFor fault) (\a -> a {assessmentScope=Scope "actor:seller" "wrong-context"}) doc)
  refused "wrong actor" "ASCOPE" (assessmentFor fault)
    (modifyAssessment (assessmentFor fault) (\a -> a {assessmentScope=Scope "actor:other" "context:transaction-1"}) doc)
  refused "ambiguous selection" "AAMBIGUOUS" fault (selectAssessments (++ ["assessment:property-fault-pending"]) doc)
  refused "duplicate selection" "AAMBIGUOUS" fault (selectAssessments (++ [assessmentFor fault]) doc)
  refused "missing skipped-guard assessment" "AMISSING" "f:nature-causation"
    (selectAssessments (filter (/= assessmentFor "f:nature-causation")) pendingDocument)
  refused "source reference" "ASOURCE" (assessmentFor fault)
    (modifyAssessment (assessmentFor fault) (\a -> a {assessmentSources=[SourceRef "source:absent" Nothing]}) doc)
  refused "issuer" "AMETADATA" (assessmentFor fault) (modifyAssessment (assessmentFor fault) (\a -> a {assessmentIssuer=""}) doc)
  refused "assumption without basis" "AMETADATA" (assessmentFor fault)
    (modifyAssessment (assessmentFor fault) (\a -> a {assessmentBasis="case_material"}) doc)
  let unrelated = changeLaw (\l -> l {lawNodes=LawNode "f:unrelated-draft" "input" "unfinished" Nothing Nothing []:lawNodes l})
  check "unrelated unassessed material allowed" (analysisReady (validateAnalysis unrelated "analysis:cheating"))
  check "unsupported version located" (case decodeDocument (encodeDocument (doc {documentFormat="future"})) of
    Left d -> diagnosticCode d == "AVERSION" && diagnosticLocation d == "/documentFormat"; Right _ -> False)
  check "duplicate JSON keys refused" (case decodeDocument "{\"documentFormat\":\"x\",\"documentFormat\":\"y\"}" of Left _ -> True; Right _ -> False)
  let unsupportedStatus = Encoding.encodeUtf8 (Text.replace "\"kind\":\"proved\"" "\"kind\":\"presumed\""
        (Encoding.decodeUtf8 (encodeDocument doc)))
  check "unsupported supplied status refused" (case decodeDocument unsupportedStatus of Left _ -> True; Right _ -> False)

provenance :: IO ()
provenance = do
  let doc = cheatingDocument
      multibyte = doc {documentSources=SourceRecord "source:utf8" "law" Nothing (Just "é猫\nx") : documentSources doc,
        documentLaw=(documentLaw doc) {lawNodes=[if nodeId n == "f:deception"
          then n {nodeQuotation=Just "é猫",nodeSources=[SourceRef "source:utf8" (Just (TextSpan 2 5 1 3 1 6))]} else n
          | n <- lawNodes (documentLaw doc)]}}
  check "complete round-trip" (decodeDocument (encodeDocument doc) == Right doc)
  check "multibyte original span accepted" (analysisReady (validateAnalysis multibyte "analysis:cheating"))
  let invalid = multibyte {documentLaw=(documentLaw multibyte) {lawNodes=[if nodeId n == "f:deception"
        then n {nodeSources=[SourceRef "source:utf8" (Just (TextSpan 1 2 1 2 1 3))]} else n
        | n <- lawNodes (documentLaw multibyte)]}}
  check "mid-codepoint span refused on object" (any (\d -> diagnosticCode d == "ASPAN"
    && "f:deception" `elem` diagnosticObjects d) (validateDocument invalid))
  compiled <- require (compileAnalysis multibyte "analysis:cheating")
  forM_ (compiledSourceMappings compiled) $ \mapping -> do
    source <- requireMaybe "generated source" (find ((== sourceMappingSource mapping) . generatedSourceId) (compiledSources compiled))
    let text = generatedSourceText source
    check "generated UTF-8 spans valid" (Core.validateSpan (Core.Source "generated" text (Encoding.encodeUtf8 text) "")
      (toCoreSpan (sourceMappingSpan mapping)))
    if sourceMappingObjects mapping == ["f:deception"] then do
      let anchor = sourceMappingSpan mapping
          extracted = BS.take (end anchor - start anchor) (BS.drop (start anchor) (Encoding.encodeUtf8 text))
      check "generated multibyte offsets locate the right authored quotation" (extracted == Encoding.encodeUtf8 "f:deception\né猫\n")
      check "original anchor remains independently mapped" (sourceMappingOriginals mapping ==
        [SourceRef "source:utf8" (Just (TextSpan 2 5 1 3 1 6))])
    else pure ()
  check "generated source separated" (all (Text.isPrefixOf "generated_" . generatedSourceKind) (compiledSources compiled)
    && "source:utf8" `notElem` map generatedSourceId (compiledSources compiled))
  check "occurrences distinct from generated IDs" (all (\m -> mappedNode m /= mappedKernelRequirement m
    && not (null (mappedOccurrence m))) (compiledRequirements compiled))
  baseline <- runDoc doc
  let rows = reportRequirements (evaluationReport baseline)
  check "multiple assertions retained" (any (\o -> observationNode o == "f:deception" && length (observationAssertions o) == 2) rows)
  check "assumption has no fabricated assertion" (any (\o -> observationNode o == fault && null (observationAssertions o)
    && (assessmentBasis <$> observationAssessment o) == Just "assumption") rows)
  synthetic <- runDoc (modifyAssessment (assessmentFor fault) (\a' -> a' {assessmentOrigin="synthetic_fixture"}) doc)
  check "external and synthetic assessment origins remain distinct"
    ("\"origin\":\"external_assertion\"" `BS.isInfixOf` evaluationKernelResponse baseline
      && "\"origin\":\"synthetic_fixture\"" `BS.isInfixOf` evaluationKernelResponse synthetic)
  let presented = doc {documentPresentation=[Presentation "o:cheating" (Map.fromList [("x","999.2"),("colour","red")])]}
  a <- require (compileAnalysis doc "analysis:cheating")
  b <- require (compileAnalysis presented "analysis:cheating")
  presentedResult <- require (evaluateAnalysis b)
  check "presentation does not affect execution" (compiledRequest a == compiledRequest b
    && reportRequirements (evaluationReport baseline) == reportRequirements (evaluationReport presentedResult)
    && snapshotId (compiledSnapshot a) /= snapshotId (compiledSnapshot b))
  check "draft/non-executable context recoverable" (snapshotDocument (evaluationSnapshot baseline) == doc
    && not (null (documentAnnotations doc)) && not (null (documentRelationships doc)))
  let otherActor = doc {documentAssertions=[a' {assertionScope=Scope "actor:buyer" "context:earlier-interview"}
        | a' <- documentAssertions doc]}
  check "assertion links remain provenance across actors/contexts"
    (analysisReady (validateAnalysis otherActor "analysis:cheating"))

selectAssessments :: ([Text] -> [Text]) -> AuthoringDocument -> AuthoringDocument
selectAssessments change doc = doc {documentAnalyses=[a {analysisAssessments=change (analysisAssessments a)} | a <- documentAnalyses doc]}

modifyAssessment :: Text -> (Assessment -> Assessment) -> AuthoringDocument -> AuthoringDocument
modifyAssessment key change doc = doc {documentAssessments=[if assessmentId a == key then change a else a | a <- documentAssessments doc]}

require :: Show a => Either a b -> IO b
require = either (fail . show) pure

requireMaybe :: String -> Maybe a -> IO a
requireMaybe label = maybe (fail label) pure

check :: String -> Bool -> IO ()
check label ok = unless ok (fail ("authoring SDK: " <> label))
