{-# LANGUAGE OverloadedStrings #-}
module LinkedDefinitionChecks (runLinkedDefinitionChecks) where

import Control.Monad (forM, forM_, unless)
import Data.Aeson (ToJSON, object, (.=))
import qualified Data.ByteString as BS
import Data.List (find)
import Data.Text (Text)
import qualified Data.Text as Text
import System.FilePath ((</>))
import System.Environment (lookupEnv)
import System.Directory (createDirectoryIfMissing)
import LinkedExample
import Yuho.Authoring
import Yuho.Protocol.Json (decodeJson)
import Yuho.SuppliedProofStatus.Decode (decodeProofRequest)
import Yuho.SuppliedProofStatus.Validate (validateProofRequest)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProof)
import qualified Yuho.SuppliedProofStatus.Types as Proof
import Yuho.Surface.Compile (compileSource)

require :: Show e => Either e a -> IO a
require = either (fail . show) pure

check :: String -> Bool -> IO ()
check label value = unless value (fail ("linked definitions: " <> label))

evaluate :: AuthoringDocument -> Text -> IO Evaluation
evaluate doc key = require (compileAnalysis doc key >>= evaluateAnalysis)

reject :: Text -> Text -> [AuthoringDiagnostic] -> IO ()
reject code owner diagnostics = check (Text.unpack code <> " linked to " <> Text.unpack owner)
  (any (\d -> diagnosticCode d == code && owner `elem` diagnosticObjects d) diagnostics)

runLinkedDefinitionChecks :: FilePath -> IO ()
runLinkedDefinitionChecks root = do
  doc <- require linkedDocument
  check "single authored object and two explicit references" (null (validateDocument doc)
    && length (filter ((== "definition") . nodeKind) (lawNodes (documentLaw doc))) == 1)
  let originalSource = SourceRecord "original:duplicate-reference" "law" Nothing (Just "é")
  ref <- require (sourceAnchorCodePoints originalSource 0 1)
  duplicated <- require (editLawNode gain (\n -> n {nodeSources=[ref,ref]})
    ((flatDocument Proved NotProved NotProved NotProved) {documentSources=[originalSource]}))
  oldProfile <- require (compileAnalysis duplicated "flat:analysis")
  check "v0.1 original-reference order/multiplicity preserved"
    (any (\m -> sourceMappingObjects m == [gain] && sourceMappingOriginals m == [ref,ref]) (compiledSourceMappings oldProfile))
  check "strict round trip" (decodeDocument (encodeDocument doc) == Right doc)
  a <- evaluate doc "analysis:A"
  b <- evaluate doc "analysis:B"
  check "different scoped assessments" (conclusion a == "satisfied" && conclusion b == "unresolved")
  pa <- require (projectEvaluation a)
  pb <- require (projectEvaluation b)
  ia <- require (inspectDefinition pa definitionKey)
  ib <- require (inspectDefinition pb definitionKey)
  check "shared meaning and all referencing rules" (sharedDefinition ia == sharedDefinition ib
    && sharedDefinitionDigest ia == sharedDefinitionDigest ib && length (sharedUses ia) == 2
    && length (sharedReferencingRules ia) == 2)
  let focus p = require (focusRequirement p (AuthoredRequirement gain))
  fa <- focus pa; fb <- focus pb
  check "occurrence/observation/assessment identities remain distinct and isolated"
    (projectedNodeId (explanationOccurrence fa) /= projectedNodeId (explanationOccurrence fb)
      && projectedNodeObservation (explanationOccurrence fa) /= projectedNodeObservation (explanationOccurrence fb)
      && fmap (assessmentScope . contextAssessment) (explanationSelected fa) == Just scopeA
      && fmap (assessmentScope . contextAssessment) (explanationSelected fb) == Just scopeB
      && map mappedKernelRequirement (evaluationMappings a) /= map mappedKernelRequirement (evaluationMappings b))
  forM_ [pa,pb] $ \p -> do
    detail <- require (focusRequirement p (AuthoredRequirement gain))
    let handle = projectedNodeId (explanationOccurrence detail)
    links <- require (inspectDefinitionOccurrence p handle)
    check "use/body path and generated mapping" (length links == 1
      && any ((== "use") . edgeKind) (concatMap linkedReferencePath links)
      && any ((== "defines") . edgeKind) (concatMap linkedReferencePath links)
      && all (not . null . linkedKernelMappings) links)
    resolved <- maybe (fail "resolution missing") pure (resolveProjectedObject p handle)
    check "resolver reaches shared definition" (definitionKey `elem` resolvedAuthoredIds resolved)
    forM_ [definitionView p definitionKey, definitionOccurrenceView p handle,lawOccurrenceView p] $ \operation -> do
      view <- require operation
      check "valid complete bindings" (null (validateProjectionView p view))
      _ <- require (encodeViewSvg p view); _ <- require (encodeViewXml p view); _ <- require (encodeViewJson p view)
      pure ()
  let unselectedLaw = documentLaw (expansionBomb doc)
      withUnused = doc {documentLaw=(documentLaw doc)
        {lawNodes=lawNodes (documentLaw doc) ++ lawNodes unselectedLaw, lawEdges=lawEdges (documentLaw doc) ++ lawEdges unselectedLaw}}
  unusedProjection <- require (projectAuthored withUnused "analysis:A")
  unusedInfo <- require (inspectDefinition unusedProjection "definition:bomb:0")
  check "unselected authored definitions are inspected without expansion or bindings"
    (null (sharedOccurrences unusedInfo) && length (sharedBodyNodes unusedInfo) == 24)
  changed <- require (revisedDefinition doc)
  ra <- evaluate changed "analysis:A"; rb <- evaluate changed "analysis:B"
  check "one edit changes both compiled bodies" (conclusion ra == "not_satisfied" && conclusion rb == "not_satisfied"
    && snapshotDocument (evaluationSnapshot a) == doc && snapshotDocument (evaluationSnapshot b) == doc)
  reject "PSTALE" (documentId doc) (either id (const []) (projectEvaluationOn changed a))
  check "law revisions remain incompatible" (case compareAnalyses a ra of Left _ -> True; _ -> False)
  b2 <- evaluate (setInput scopeA gain NotProved doc) "analysis:B"
  check "actor A edit cannot change B" (conclusion b2 == conclusion b
    && map observationComputed (reportRequirements (evaluationReport b2)) == map observationComputed (reportRequirements (evaluationReport b)))
  reject "IFOCUS" "analysis:A" (either id (const [])
    (focusRequirement pa (RequirementOccurrence (projectedNodeId (explanationOccurrence fb)))))
  reject "DDEFINITION" "missing:definition" (either id (const []) (inspectDefinition pa "missing:definition"))
  let draft = doc {documentAnalyses=[x {analysisAssessments=[]} | x <- documentAnalyses doc]}
  draftProjection <- require (projectAuthored draft "analysis:A")
  draftInfo <- require (inspectDefinition draftProjection definitionKey)
  check "definition inspection without bindings invents no computation"
    (not (null (sharedOccurrences draftInfo)) && all ((== Nothing) . projectedNodeComputed . explanationOccurrence . linkedRequirement) (sharedOccurrences draftInfo))
  refusals doc
  forM_ [(Proved,"satisfied"),(NotProved,"not_satisfied"),(Unresolved NotDetermined,"unresolved")] $ \(status,expected) -> do
    let base = flatDocument status NotProved NotProved NotProved
        law = documentLaw base
        single = base {documentFormat=linkedAuthoringFormat,documentLaw=law
          {lawNodes=[n | n <- lawNodes law, nodeId n `elem` ["flat:rule",gain]] ++
            [LawNode "definition:leaf" "definition" "Single primitive definition" Nothing Nothing []],
           lawEdges=[LawEdge "use:root" "flat:rule" "definition:leaf" "use",LawEdge "defines:leaf" "definition:leaf" gain "defines"]},
          documentAssessments=filter ((== gain) . assessmentInput) (documentAssessments base),
          documentAnalyses=[x {analysisAssessments=["flat:" <> gain]} | x <- documentAnalyses base]}
    leafResult <- evaluate single "flat:analysis"
    leafProjection <- require (projectEvaluation leafResult)
    _ <- require (lawOccurrenceView leafProjection)
    check "rule-root use and primitive definition body" (reportConclusion (evaluationReport leafResult) == expected)
  conformance doc
  legacy root doc
  putStrLn "linked definitions: 81 independent flat parity cases, legacy definition parity, scopes, revision, references/cycles/sharing/limits and projection passed"
  where conclusion = reportConclusion . evaluationReport

refusals :: AuthoringDocument -> IO ()
refusals doc = do
  let law = documentLaw doc
      modifyEdges f = doc {documentLaw=law {lawEdges=f (lawEdges law)}}
      diagnostics candidate = validationDiagnostics (validateAnalysis candidate "analysis:A")
      unknown = modifyEdges (map (\e -> if edgeId e == "use:theft-dishonesty" then e {edgeTo="definition:unknown"} else e))
      dup = doc {documentLaw=law {lawNodes=take 1 (lawNodes law) ++ lawNodes law}}
      direct = modifyEdges (++ [LawEdge "cycle:direct" "g:dishonestly" definitionKey "use"])
      indirect = doc {documentLaw=law {lawNodes=lawNodes law ++
        [LawNode "definition:second" "definition" "Second" Nothing Nothing [],
         LawNode "group:second" "all" "Second group" Nothing Nothing [],LawNode "input:second" "input" "Second input" Nothing Nothing []],
        lawEdges=lawEdges law ++ [LawEdge "cycle:to-second" "g:dishonestly" "definition:second" "use",
          LawEdge "cycle:second-body" "definition:second" "group:second" "defines",
          LawEdge "cycle:back" "group:second" definitionKey "use",LawEdge "second:member" "group:second" "input:second" "member"]}}
      repeated = modifyEdges (++ [LawEdge "use:again" "g:theft" definitionKey "use"])
      sharing = modifyEdges (++ [LawEdge "accidental:share" "g:theft" gain "member"])
      wrong = modifyEdges (map (\e -> if edgeId e == "use:theft-dishonesty" then e {edgeTo=gain} else e))
      missing = doc {documentAnalyses=[if analysisId x == "analysis:A" then x
        {analysisAssessments=filter (/= "actor:A:f:intends-wrongful-gain") (analysisAssessments x)} else x | x <- documentAnalyses doc]}
      wrongScope = doc {documentAssessments=[if assessmentId x == "actor:A:f:intends-wrongful-gain"
        then x {assessmentScope=scopeB} else x | x <- documentAssessments doc]}
      ambiguous = doc {documentAssessments=[a {assessmentId="assessment:extra"} | a <- take 1 (documentAssessments doc)] ++ documentAssessments doc,
        documentAnalyses=[if analysisId x == "analysis:A" then x {analysisAssessments="assessment:extra":analysisAssessments x} else x
          | x <- documentAnalyses doc]}
  forM_ [("AREFERENCE","use:theft-dishonesty",unknown),("ADUPLICATE",definitionKey,dup),
    ("ACYCLE","cycle:direct",direct),("ACYCLE","cycle:back",indirect),("AREUSE",gain,repeated),
    ("ASHARING",gain,sharing),("ASHAPE","use:theft-dishonesty",wrong),
    ("AMISSING",gain,missing),("ASCOPE","actor:A:f:intends-wrongful-gain",wrongScope),
    ("AAMBIGUOUS",gain,ambiguous)] $ \(code,owner,candidate) -> do
      emit (Text.unpack code <> "-" <> Text.unpack (Text.replace ":" "-" owner) <> ".diagnostics.json") (diagnostics candidate)
      reject code owner (diagnostics candidate)
      check "invalid definition never evaluates" (case compileAnalysis candidate "analysis:A" of Left _ -> True; _ -> False)
  check "old profile cannot reinterpret use" (any ((== "AUNSUPPORTED") . diagnosticCode)
    (validateDocument doc {documentFormat=authoringFormat}))
  originalDefinition <- maybe (fail "definition missing") pure (find ((== definitionKey) . nodeId) (lawNodes law))
  forM_ [("ASOURCE",SourceRef "missing:source" Nothing),
    ("ASPAN",SourceRef "source:pc2020-s24" (Just (TextSpan 0 999 1 1 1 1000)))] $ \(code,ref) -> do
      bad <- require (editLawNode definitionKey (const originalDefinition {nodeSources=[ref]}) doc)
      emit (Text.unpack code <> ".source-validation.json") (validateDocument bad)
      reject code definitionKey (validateDocument bad)
  let expanded = expansionBomb doc
  emit "expansion.diagnostics.json" (diagnostics expanded)
  reject "AEXPANSION" "analysis:A" (diagnostics expanded)
  check "overflow is an otherwise valid compact authored graph" (null (validateDocument expanded))
  let wide = wideTree 510
  check "kernel budget differs from occurrence count" (null (validateDocument wide))
  reject "AEXPANSION" "flat:analysis" (validationDiagnostics (validateAnalysis wide "flat:analysis"))
  let nearBase = wideTree 509
      nearLaw = documentLaw nearBase
      exact = nearBase {documentLaw=nearLaw {lawNodes=lawNodes nearLaw ++ [LawNode "wide:nested" "all" "Nested" Nothing Nothing []],
        lawEdges=[if edgeTo e `elem` ["input:0","input:1"] then e {edgeFrom="wide:nested"} else e | e <- lawEdges nearLaw]
          ++ [LawEdge "wide:nested-member" "wide:all" "wide:nested" "member"]}}
  nearLimit <- evaluate exact "flat:analysis"
  check "exact kernel identity budget admitted" (reportConclusion (evaluationReport nearLimit) == "satisfied")
  -- Empty source-only anchor and missing bindings remain distinct from supplied uncertainty.
  unresolved <- evaluate (setInput scopeA gain (Unresolved NotDetermined) doc) "analysis:A"
  check "missing vs explicitly unresolved" (any ((== "missing") . openState) (openInputs (validateAnalysis missing "analysis:A"))
    && reportConclusion (evaluationReport unresolved) == "unresolved")
  -- Acyclic nested reference with disjoint leaves is admitted.
  let nested = doc {documentLaw=law {lawNodes=lawNodes law ++
        [LawNode "definition:outer" "definition" "Outer" Nothing Nothing [],LawNode "group:outer" "all" "Outer group" Nothing Nothing []],
        lawEdges=map (\e -> if edgeId e == "use:theft-dishonesty" then e {edgeTo="definition:outer"}
          else if edgeId e == "theft:f:movable-property" then e {edgeFrom="group:outer"} else e) (lawEdges law)
          ++ [LawEdge "outer:body" "definition:outer" "group:outer" "defines",LawEdge "outer:use" "group:outer" definitionKey "use"]}}
  nestedEvaluation <- evaluate nested "analysis:A"
  check "acyclic nested use" (reportConclusion (evaluationReport nestedEvaluation) == "satisfied")

expansionBomb :: AuthoringDocument -> AuthoringDocument
expansionBomb doc = doc {documentLaw=(documentLaw doc) {lawNodes=
  LawNode "rule:bomb" "rule" "Expansion budget fixture" Nothing Nothing [] : concat
    [[LawNode (d i) "definition" "Definition" Nothing Nothing [], LawNode (g i) "all" "Group" Nothing Nothing []] | i <- [0..10]] ++
    [LawNode "bomb:leaf-1" "input" "One" Nothing Nothing [],LawNode "bomb:leaf-2" "input" "Two" Nothing Nothing []],
  lawEdges=LawEdge "bomb:start" "rule:bomb" (d 0) "use" : concat
    [[LawEdge ("body:" <> t i) (d i) (g i) "defines"] ++
     [LawEdge ("ref:" <> t i <> ":" <> t j) (g i) (d (i+1)) "use" | j <- [0,1]] | i <- [0..9]] ++
    [LawEdge "bomb:last-body" (d 10) (g 10) "defines",
     LawEdge "bomb:leaf1" (g 10) "bomb:leaf-1" "member",LawEdge "bomb:leaf2" (g 10) "bomb:leaf-2" "member"]},
  documentAnalyses=[a {analysisTarget="rule:bomb",analysisAssessments=[]} | a <- take 1 (documentAnalyses doc)],
  documentAssessments=[],documentAnnotations=[]}
  where t :: Int -> Text; t = Text.pack . show
        d i = "definition:bomb:" <> t i
        g i = "group:bomb:" <> t i

conformance :: AuthoringDocument -> IO ()
conformance original = do
  let statuses = [Proved,NotProved,Unresolved NotDetermined]
      mapping = [(gain,gain),(loss,loss),(ordinary,ordinary),(knowledge,knowledge),
        ("g:section24-intention","flat:intention"),("g:section24-ordinary","flat:ordinary"),("g:dishonestly","flat:root")]
      value key e = (\r -> (assessmentClassification <$> observationAssessment r, observationComputed r, observationEvaluation r, observationSkipReason r))
        <$> find ((== key) . observationNode) (reportRequirements (evaluationReport e))
  parityRows <- forM [(a,b,c,d) | a <- statuses,b <- statuses,c <- statuses,d <- statuses] $ \(a,b,c,d) -> do
    let linked = foldl (\doc (input,status) -> setInput scopeA input status doc) original [(gain,a),(loss,b),(ordinary,c),(knowledge,d)]
    actual <- evaluate linked "analysis:A"
    flat <- evaluate (flatDocument a b c d) "flat:analysis"
    check "independent flat/linked conclusion and grouped statuses"
      (reportConclusion (evaluationReport actual) == reportConclusion (evaluationReport flat)
        && all (\(x,y) -> value x actual == value y flat) mapping
        && map ruleBranchReason (reportRules (evaluationReport actual)) == map ruleBranchReason (reportRules (evaluationReport flat)))
    pure (object ["supplied" .= map Classification [a,b,c,d], "flat" .= evaluationReport flat,"linked" .= evaluationReport actual])
  emit "flat-linked-conformance.json" parityRows
  -- Independently authored flat and linked bodies with the same explicit,
  -- synthetic guard: compare evaluated, defeated, unresolved and skipped cases.
  guardRows <- forM [(Proved,NotProved,NotProved,Proved,"not_satisfied","evaluated","defeated"),
    (Proved,NotProved,NotProved,Unresolved NotDetermined,"unresolved","evaluated","exception_unresolved"),
    (NotProved,NotProved,NotProved,Proved,"not_satisfied","not_evaluated","requirements_not_satisfied"),
    (Unresolved NotDetermined,NotProved,NotProved,NotProved,"unresolved","not_evaluated","requirements_unresolved"),
    (NotProved,Proved,Proved,NotProved,"satisfied","evaluated","satisfied")] $ \(a,c,d,guardStatus,expected,state,reason) -> do
      let linked = foldl (\doc (input,status) -> setInput scopeA input status doc) original
            [(gain,a),(loss,NotProved),(ordinary,c),(knowledge,d)]
      actual <- evaluate (withGuard "analysis:A" "rule:theft" guardStatus linked) "analysis:A"
      flat <- evaluate (withGuard "flat:analysis" "flat:rule" guardStatus (flatDocument a NotProved c d)) "flat:analysis"
      let ar = evaluationReport actual
          fr = evaluationReport flat
          mainReason report = ruleBranchReason =<< find ((/= "synthetic:guard-rule") . ruleAuthoredId) (reportRules report)
      check "flat/linked exception policy parity and independent expectations"
        (reportConclusion ar == expected && reportConclusion fr == expected
          && mainReason ar == Just reason && mainReason fr == Just reason
          && map exceptionEvaluation (reportExceptions ar) == [state]
          && map exceptionEvaluation (reportExceptions fr) == [state]
          && map exceptionComputed (reportExceptions ar) == map exceptionComputed (reportExceptions fr)
          && map exceptionFired (reportExceptions ar) == map exceptionFired (reportExceptions fr)
          && map exceptionSkipReason (reportExceptions ar) == map exceptionSkipReason (reportExceptions fr)
          && value "synthetic:guard-input" actual == value "synthetic:guard-input" flat)
      pure (object ["expectedConclusion" .= (expected :: Text),"expectedGuardState" .= (state :: Text),
        "flat" .= fr,"linked" .= ar])
  emit "flat-linked-exceptions.json" guardRows
  let flatBase = flatDocument Proved NotProved Proved NotProved
      missingIn key document = document {documentAnalyses=[a {analysisAssessments=filter (/= key) (analysisAssessments a)}
        | a <- documentAnalyses document]}
      badScope key document = document {documentAssessments=[if assessmentId a == key then a {assessmentScope=scopeB} else a
        | a <- documentAssessments document]}
  forM_ [("AMISSING",missingIn "actor:A:f:intends-wrongful-gain" original,missingIn "flat:f:intends-wrongful-gain" flatBase),
    ("ASCOPE",badScope "actor:A:f:intends-wrongful-gain" original,badScope "flat:f:intends-wrongful-gain" flatBase)] $ \(code,linked,flat) -> do
      let left = validateAnalysis linked "analysis:A"
          right = validateAnalysis flat "flat:analysis"
      check "flat/linked negative binding parity" (not (analysisReady left) && not (analysisReady right)
        && any ((== code) . diagnosticCode) (validationDiagnostics left)
        && any ((== code) . diagnosticCode) (validationDiagnostics right))
      emit (Text.unpack code <> ".flat-linked-validation.json") (object ["linked" .= left,"flat" .= right])
  forM_ [(Proved,NotProved,NotProved,NotProved,"satisfied"),
    (NotProved,Proved,NotProved,NotProved,"satisfied"),(NotProved,NotProved,Proved,Proved,"satisfied"),
    (NotProved,NotProved,Proved,Unresolved NotDetermined,"unresolved"),
    (NotProved,NotProved,NotProved,NotProved,"not_satisfied")] $ \(a,b,c,d,expected) -> do
      e <- evaluate (flatDocument a b c d) "flat:analysis"
      check "independently specified expected outcome" (reportConclusion (evaluationReport e) == expected)

legacy :: FilePath -> AuthoringDocument -> IO ()
legacy root original = do
  let base = root </> "research/singapore/section-84-pilot/statutory-definitions"
      modelPath = base </> "section323-section379-definitions.yh"
      rows = [("14_theft_no_actual_gain",Proved,NotProved,NotProved,NotProved,"satisfied"),
        ("11_theft_loss_intent",NotProved,Proved,NotProved,NotProved,"satisfied"),
        ("12_theft_no_dishonest_intent",NotProved,NotProved,NotProved,NotProved,"not_satisfied"),
        ("13_theft_unresolved_intent",Unresolved NotDetermined,NotProved,NotProved,NotProved,"unresolved"),
        ("16_theft_ordinary_route",NotProved,NotProved,Proved,Proved,"satisfied")]
  model <- BS.readFile modelPath
  legacyRows <- forM rows $ \(name,a,b,c,d,expected) -> do
    let path = base </> "scenarios" </> name <> ".yh"
    scenario <- BS.readFile path
    bytes <- require (compileSource modelPath model (Just (path,scenario)))
    value <- require (decodeJson bytes)
    decoded <- require (decodeProofRequest value)
    validated <- require (validateProofRequest decoded)
    legacyValue <- require (evaluateProof validated)
    sdk <- evaluate (foldl (\doc (input,status) -> setInput scopeA input status doc) original
      [(gain,a),(loss,b),(ordinary,c),(knowledge,d)]) "analysis:A"
    check "unchanged legacy definition path agrees on candidate outcome"
      (reportConclusion (evaluationReport sdk) == expected && Proof.satisfactionText (Proof.proofResultStatus legacyValue) == expected)
    -- The legacy model additionally wraps definitions in singleton all groups
    -- and attaches the explicitly false retained section 84 fixture. Those are
    -- not asserted identical to the fixed-edition SDK candidate's surroundings.
    let traces = concatMap Proof.proofRuleTrace (Proof.proofResultRules legacyValue)
    forM_ [gain,loss,ordinary,knowledge,"g:section24-intention","g:section24-ordinary","g:dishonestly"] $ \key -> do
      old <- maybe (fail ("legacy trace missing: " <> Text.unpack key)) pure (find ((== key) . Proof.proofTraceId) traces)
      new <- maybe (fail "SDK trace missing") pure (find ((== key) . observationNode) (reportRequirements (evaluationReport sdk)))
      check "explicit legacy group/leaf mapping" (Just (Proof.satisfactionText (Proof.proofTraceStatus old)) == observationComputed new
        && observationEvaluation new == "evaluated")
    let expectedBranch = case expected of
          "satisfied" -> Proof.ProofSatisfied
          "unresolved" -> Proof.ProofRequirementsUnresolved
          _ -> Proof.ProofRequirementsNotSatisfied
    legacyRule <- maybe (fail "legacy main rule missing") pure
      (find ((== "r:section379-candidate") . Proof.proofRuleId) (Proof.proofResultRules legacyValue))
    check "legacy main branch reason parity" (case Proof.proofRuleBranches legacyRule of
      [branch] -> Proof.proofBranchReason branch == expectedBranch
      _ -> False)
    putStrLn ("linked legacy " <> name <> ": " <> Text.unpack expected <> "; 7 mapped requirement rows agree")
    pure (object ["scenario" .= name,"expectedAndActual" .= (expected :: Text),
      "mappedRequirements" .= (7 :: Int),"SDK" .= evaluationReport sdk])
  emit "legacy-linked-conformance.json" legacyRows

-- Explicit synthetic guard solely for adapter conformance, not a legal claim.
withGuard :: Text -> Text -> SuppliedStatus -> AuthoringDocument -> AuthoringDocument
withGuard analysisKey rule status doc = doc {documentLaw=law {lawNodes=lawNodes law ++
  [LawNode "synthetic:guard-rule" "rule" "Synthetic conformance guard" Nothing Nothing [],
   LawNode "synthetic:guard-input" "input" "Explicit guard assessment" Nothing Nothing []],
  lawEdges=lawEdges law ++ [LawEdge "synthetic:attachment" rule "synthetic:guard-rule" "exception",
    LawEdge "synthetic:guard-root" "synthetic:guard-rule" "synthetic:guard-input" "requires"]},
  documentAssessments=documentAssessments doc ++ [Assessment "synthetic:guard-assessment" "synthetic:guard-input" scopeA
    (Classification status) "Conformance assumption" "test" "synthetic_fixture" "assumption" [] []],
  documentAnalyses=[if analysisId a == analysisKey then a {analysisAssessments=analysisAssessments a ++ ["synthetic:guard-assessment"]}
    else a | a <- documentAnalyses doc]}
  where law = documentLaw doc

-- Optional explicit review destination; normal native tests do not write fixtures.
emit :: ToJSON a => String -> a -> IO ()
emit name value = do
  destination <- lookupEnv "YUHO_LINKED_EVIDENCE"
  case destination of
    Nothing -> pure ()
    Just folder -> do
      createDirectoryIfMissing True folder
      BS.writeFile (folder </> name) (encodeRecord value)

wideTree :: Int -> AuthoringDocument
wideTree width = base {documentFormat=linkedAuthoringFormat, documentLaw=(documentLaw base)
  {lawNodes=[LawNode "wide:rule" "rule" "Budget" Nothing Nothing [],LawNode "wide:all" "all" "All" Nothing Nothing []]
    ++ [LawNode (key i) "input" "Input" Nothing Nothing [] | i <- indices],
   lawEdges=LawEdge "wide:root" "wide:rule" "wide:all" "requires" :
     [LawEdge ("edge:" <> key i) "wide:all" (key i) "member" | i <- indices]},
  documentAssessments=[Assessment ("assessment:" <> key i) (key i) scopeA (Classification Proved)
    "Fixture" "test" "synthetic_fixture" "assumption" [] [] | i <- indices],
  documentAnalyses=[a {analysisTarget="wide:rule",analysisAssessments=["assessment:" <> key i | i <- indices]}
    | a <- documentAnalyses base]}
  where base = flatDocument Proved NotProved Proved NotProved
        indices = [0..width-1]
        key i = "input:" <> Text.pack (show i)
