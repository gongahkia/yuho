{-# LANGUAGE OverloadedStrings #-}
-- An independent public-SDK consumer, not a Surface AST or fixture loader.
module Hurt
  ( hurtDocument, hurtDraft, hurtScenarios, hurtAnalysis, hurtScope
  , hurtAssessmentId, hurtNoteAnchor, hurtRequiredAssumptions, hurtExampleAcknowledgements
  , runHurtConsumer ) where

import Control.Monad (forM, unless)
import qualified Data.ByteString as BS
import Data.List (find)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import Data.Time.Calendar (fromGregorian)
import System.Directory (createDirectoryIfMissing)
import System.FilePath ((</>))
import Yuho.Authoring
import Acknowledgements

hurtAnalysis :: Text
hurtAnalysis = "analysis:hurt"

hurtScope :: Scope
hurtScope = Scope "actor:alex" "context:synthetic-yard-incident"

-- Exact scenario names provide an explicit correspondence with retained tests.
-- These classifications are consumer-authored data, not parsed from .yh files.
hurtScenarios :: SourceRef -> [(String,AuthoringDocument)]
hurtScenarios anchor = [(name,select overrides) | (name,overrides) <-
  [("01_intention_no_exception",[]),
   ("02_knowledge_no_exception",[("f:intention-to-cause-hurt",NotProved),("f:knowledge-hurt-likely",Proved)]),
   ("03_hurt_not_proved",[("f:hurt-caused",NotProved)]),
   ("05_offence_causation_unresolved",[("f:hurt-caused-by-act",Unresolved NotDetermined)]),
   ("06_nature_route",[("f:unsoundness-time",Proved),("f:nature-causation",Proved),("f:nature-incapacity",Proved)]),
   ("11_section84_unresolved",[("f:unsoundness-time",Proved),("f:nature-causation",Proved),
     ("f:nature-incapacity",Unresolved NotDetermined)])]]
  where
    base = hurtDocument anchor
    select overrides = base {documentAnalyses=[a {analysisAssessments=
      [hurtAssessmentId key (maybe (baseline key) id (lookup key overrides)) | (key,_,_,_) <- inputs]}
      | a <- documentAnalyses base]}

hurtDraft :: SourceRef -> AuthoringDocument
hurtDraft ref = let doc = hurtDocument ref in
  doc {documentAnalyses=[a {analysisAssessments=[]} | a <- documentAnalyses doc]}

hurtAssessmentId :: Text -> SuppliedStatus -> Text
hurtAssessmentId input status = "assessment:hurt:" <> Text.drop 2 input <> ":" <> statusName status

statusName :: SuppliedStatus -> Text
statusName status = case status of
  Proved -> "proved"
  NotProved -> "not_proved"
  Unresolved NotDetermined -> "unresolved-not-determined"
  Unresolved ExternalDecisionPending -> "unresolved-external-decision-pending"

baseline :: Text -> SuppliedStatus
baseline key = if key `elem` ["f:act-performed","f:hurt-caused","f:hurt-caused-by-act",
  "f:intention-to-cause-hurt"] then Proved else NotProved

noteExcerpt :: Text
noteExcerpt = "Mei reports pain (痛) in her arm after the push."

-- Original anchor in this explicitly synthetic retained note, not a statute span.
hurtNoteAnchor :: Either [AuthoringDiagnostic] SourceRef
hurtNoteAnchor = sourceAnchorCodePoints hurtNoteSource 11 58

hurtNoteSource :: SourceRecord
hurtNoteSource = SourceRecord "source:hurt-note" "synthetic" (Just "consumer-authored synthetic case note")
  (Just ("Synthetic: " <> noteExcerpt))

hurtDocument :: SourceRef -> AuthoringDocument
hurtDocument anchor = AuthoringDocument authoringFormat "document:hurt-demo" law sources assertions assessments
  [Analysis hurtAnalysis "o:voluntary-hurt" hurtScope
    [hurtAssessmentId key (baseline key) | (key,_,_,_) <- inputs] (fromGregorian 2026 9 13)]
  [Relationship "relationship:hurt-sequence" "chronology" "assertion:push" "assertion:pain"
    "Recorded sequence only; this edge does not establish causation.",
   Relationship "relationship:hurt-challenge" "challenge" "assertion:account"
    (hurtAssessmentId "f:hurt-caused-by-act" Proved)
    "Retained question about attribution; no opposite conclusion is asserted."]
  (scopeAnnotations ++
   [Annotation "annotation:hurt-draft" ["assertion:push","assertion:weather"]
      "Draft: obtain fuller accounts of the yard incident." "draft",
    Annotation "annotation:hurt-burden" ["x:section84"]
      "Retained model annotation: section107 defence legal balance_of_probabilities. No weighing or proof-standard determination is implemented." "retained",
    Annotation "annotation:hurt-section323-scope" ["o:voluntary-hurt"]
      "Retained quotation q:section323-scope: except in the case provided for by section 323A or 334" "retained",
    Annotation "annotation:wrongfulness-operator" ["f:ordinary-wrongfulness-incapacity","f:contrary-law-incapacity"]
      "Retained supporting quotation q:wrong_operator: incapable of knowing that what he is doing is wrong" "retained"])
  []
  where
    law = LawDefinition "law:bounded-voluntary-hurt" "retained-research-1"
      (rules ++ leaves ++ groups) (rootEdges ++ memberEdges)
      (["Bounded saved ss 319/321/323 structure and represented s 84 expression; synthetic classifications only.",
        "No evidence assessment, diagnosis, offence adjudication, legal completeness or sentence determination.",
        "No case-specific temporal selection, section 323A or section 334 doctrine."] ++ map snd scopeAssumptions)
    lawRef = [SourceRef "source:hurt-law" Nothing]
    node key kind label quote citation = LawNode key kind label quote (Just citation) lawRef
    rules = [node "o:voluntary-hurt" "rule" "Voluntarily causing hurt (bounded candidate)" Nothing "Penal Code ss 319, 321, 323",
      node "x:section84" "rule" "Unsoundness of mind exception" Nothing "Penal Code s 84"]
    leaves = [node key "input" label (Just quote) citation | (key,label,quote,citation) <- inputs]
    groups = [node key kind label Nothing citation | (key,kind,label,citation,_) <- structures]
    rootEdges = [LawEdge "edge:hurt-root" "o:voluntary-hurt" "g:voluntary-hurt" "requires",
      LawEdge "edge:exception-root" "x:section84" "g:section84-requirements" "requires",
      LawEdge "edge:section84-attachment" "o:voluntary-hurt" "x:section84" "exception"]
    memberEdges = [LawEdge ("edge:" <> key <> "/" <> child) key child "member"
      | (key,_,_,_,children) <- structures, child <- children]
    sources = [SourceRecord "source:hurt-law" "law"
        (Just "retained research/singapore/section-84-pilot/hurt-offence/section323-with-section84.yh; saved quotations, not a complete current statute") Nothing,
      hurtNoteSource,
      SourceRecord "source:hurt-account" "synthetic" (Just "consumer-authored synthetic incident account")
        (Just "Alex is recorded as pushing Mei in the yard. The account does not resolve legal intention or causation."),
      SourceRecord "source:hurt-register" "other" (Just "synthetic register locator; text not supplied") Nothing]
    assertions = [CaseAssertion "assertion:push" "Alex is recorded as pushing Mei in the yard." hurtScope
        [SourceRef "source:hurt-account" Nothing],
      CaseAssertion "assertion:pain" noteExcerpt (Scope "actor:mei" "context:synthetic-clinic-note") [anchor],
      CaseAssertion "assertion:account" "The recorded account leaves attribution of the reported pain open." hurtScope
        [SourceRef "source:hurt-account" Nothing],
      CaseAssertion "assertion:weather" "A later observer records rain; no assessment cites this assertion."
        (Scope "actor:observer" "context:later-observation") [SourceRef "source:hurt-register" Nothing]]
    assessments = [assessment key label status | (key,label,_,_) <- inputs,
      status <- if key `elem` ["f:hurt-caused-by-act","f:nature-incapacity"]
        then [Proved,NotProved,Unresolved NotDetermined] else [Proved,NotProved]]
    assessment key label status = Assessment (hurtAssessmentId key status) key hurtScope (Classification status)
      (if status == Unresolved NotDetermined
        then "Synthetic caller leaves '" <> label <> "' explicitly not determined. " <>
          (if contextual key then "Cited material does not select the legal classification."
           else "Explicit fixture assumption; no case assertion or source is supplied.")
        else (if contextual key then "Synthetic supplied classification: " else "Explicit synthetic fixture assumption: ") <>
          label <> " is supplied as " <> statusName status <> ". " <>
          (if contextual key then "References provide context, not evidence aggregation."
           else "No case assertion or source is supplied."))
      "hurt-example-caller" "synthetic_fixture" (if contextual key then "case_material" else "assumption")
      (if key == "f:hurt-caused-by-act" then ["assertion:push","assertion:pain","assertion:account"]
       else if key == "f:act-performed" then ["assertion:push"]
       else if key == "f:hurt-caused" then ["assertion:pain"] else [])
      (if key `elem` ["f:hurt-caused-by-act","f:hurt-caused"] then [anchor] else [])
    contextual key = key `elem` ["f:act-performed","f:hurt-caused","f:hurt-caused-by-act"]
    scopeAnnotations = [Annotation key ["o:voluntary-hurt",hurtAnalysis]
      ("Synthetic scenario acknowledgement: " <> meaning <> " Retained context, not a computed conclusion.") "retained"
      | (key,meaning) <- scopeAssumptions]

scopeAssumptions :: [(Text,Text)]
scopeAssumptions =
  [("a:outside-section-323A","Assume the case is outside section 323A."),
   ("a:outside-section-334","Assume the case is outside section 334."),
   ("a:post-2022-section-84-expression-applicable","Assume applicability of the represented post-2022 section 84 expression.")]

-- Explicit caller policy input, separate from retained annotation content.
hurtRequiredAssumptions :: [Text]
hurtRequiredAssumptions = ["a:outside-section-323A","a:outside-section-334",
  "a:post-2022-section-84-expression-applicable"]

-- This demonstration caller explicitly accepts these assumptions. Do not copy
-- the required set: a newly added requirement must still need a caller choice.
hurtExampleAcknowledgements :: [Text]
hurtExampleAcknowledgements = ["a:outside-section-323A","a:outside-section-334",
  "a:post-2022-section-84-expression-applicable"]

inputs :: [(Text,Text,Text,Text)]
inputs =
  [("f:act-performed","Doing an act","does any act","Penal Code s 321"),
   ("f:hurt-caused","Bodily pain, disease or infirmity","bodily pain, disease or infirmity to any person","Penal Code s 319"),
   ("f:hurt-caused-by-act","The act causes the hurt","and does thereby cause hurt","Penal Code s 321"),
   ("f:intention-to-cause-hurt","Intention to cause hurt","intention of thereby causing hurt","Penal Code s 321"),
   ("f:knowledge-hurt-likely","Knowledge that hurt is likely","knowledge that he is likely thereby to cause hurt","Penal Code s 321"),
   ("f:unsoundness-time","Unsoundness of mind at the time of the act",timeQuote,"Penal Code s 84"),
   ("f:nature-causation","By reason of unsoundness (nature route)",timeQuote,"Penal Code s 84"),
   ("f:nature-incapacity","Incapable of knowing the nature of the act","incapable of knowing the nature of the act","Penal Code s 84"),
   ("f:wrong-causation","By reason of unsoundness (wrongfulness route)",timeQuote,"Penal Code s 84"),
   ("f:ordinary-wrongfulness-incapacity","Wrong by ordinary standards of reasonable and honest persons",
     "is wrong by the ordinary standards of reasonable and honest persons","Penal Code s 84"),
   ("f:contrary-law-incapacity","Wrong as contrary to law","is wrong as contrary to law","Penal Code s 84"),
   ("f:control-causation","By reason of unsoundness (control route)",timeQuote,"Penal Code s 84"),
   ("f:control-incapacity","Completely deprived of power to control actions","completely deprived of any power to control his actions","Penal Code s 84")]
  where timeQuote = "at the time of doing it, by reason of unsoundness of mind"

structures :: [(Text,Text,Text,Text,[Text])]
structures =
  [("g:section321-fault","any","Intention or knowledge","Penal Code s 321",["f:intention-to-cause-hurt","f:knowledge-hurt-likely"]),
   ("g:voluntary-hurt","all","Requirements for voluntarily causing hurt","Penal Code ss 319, 321, 323",
     ["f:act-performed","f:hurt-caused","f:hurt-caused-by-act","g:section321-fault"]),
   ("g:nature","all","Incapacity to know the nature of the act","Penal Code s 84",["f:nature-causation","f:nature-incapacity"]),
   ("g:wrongfulness","all","Incapacity to know that the act is wrong","Penal Code s 84",
     ["f:wrong-causation","f:ordinary-wrongfulness-incapacity","f:contrary-law-incapacity"]),
   ("g:control","all","Complete loss of control over actions","Penal Code s 84",["f:control-causation","f:control-incapacity"]),
   ("g:section84-routes","any","Alternative incapacity routes","Penal Code s 84",["g:nature","g:wrongfulness","g:control"]),
   ("g:section84-requirements","all","Requirements of the represented s 84 exception","Penal Code s 84",["f:unsoundness-time","g:section84-routes"])]

runHurtConsumer :: [String] -> IO ()
runHurtConsumer args = do
  anchor <- require hurtNoteAnchor
  let document = hurtDocument anchor
      draftDocument = hurtDraft anchor
      scenarios = hurtScenarios anchor
  destination <- case args of
    [] -> pure Nothing
    ["--artifacts",directory] -> pure (Just directory)
    _ -> fail "usage: yuho-authoring-consumer --model hurt [--artifacts DIRECTORY]"
  context <- require (acknowledgementContext document hurtAnalysis)
  let policy = AcknowledgementPolicy context hurtRequiredAssumptions
      acknowledgements = Acknowledgements context hurtExampleAcknowledgements
  draft <- require (projectAuthored draftDocument hurtAnalysis)
  draftView <- require (caseView draft)
  draftFiles <- exportView "hurt-case-before" draft draftView
  let draftValidation = validateAnalysis draftDocument hurtAnalysis
  unless (documentValid draftValidation && not (analysisReady draftValidation))
    (fail "incomplete hurt case unexpectedly executable")
  missing <- case compileAnalysis draftDocument hurtAnalysis of
    Left diagnostics -> pure diagnostics
    Right _ -> fail "incomplete hurt case compiled"
  runs <- forM scenarios $ \(name,doc) -> do
    decoded <- require (decodeDocument (encodeDocument doc))
    unless (decoded == doc) (fail "hurt document round-trip failed")
    (result,receipt) <- require (evaluateAcknowledged policy acknowledgements decoded hurtAnalysis)
    let compiled = evaluationCompilation result
    projection <- require (projectEvaluation result)
    files <- exportLaw ("hurt-" <> name) projection
    pure (name,result,projection,files ++
      [("data/hurt-" <> name <> ".document.json",encodeDocument decoded),
       ("data/hurt-" <> name <> ".application.json",encodeRecord (evaluationReport result)),
       ("data/hurt-" <> name <> ".validation.json",encodeRecord (validateAnalysis decoded hurtAnalysis)),
       ("data/hurt-" <> name <> ".request.json",compiledRequest compiled),
       ("data/hurt-" <> name <> ".result.json",evaluationKernelResponse result),
       ("data/hurt-" <> name <> ".acknowledgements.json",encodeRecord receipt)])
  let get name = case find (\(key,_,_,_) -> key == name) runs of
        Just (_,result,projection,_) -> pure (result,projection)
        Nothing -> fail "missing hurt scenario"
  (intention,intentionP) <- get "01_intention_no_exception"
  (knowledge,_) <- get "02_knowledge_no_exception"
  (ordinaryPending,ordinaryP) <- get "05_offence_causation_unresolved"
  (guardPending,guardP) <- get "11_section84_unresolved"
  routes <- require (projectComparison intention knowledge)
  uncertainties <- require (projectComparison ordinaryPending guardPending)
  -- Resolve the selected binding from this run, not from retained array order.
  selected <- case [row | row <- reportRequirements (evaluationReport ordinaryPending),
      observationNode row == "f:hurt-caused-by-act"] of
    [row] -> maybe (fail "causation observation has no selected assessment") pure
      (observationAssessment row)
    _ -> fail "expected exactly one causation occurrence in the hurt analysis"
  selectedView <- require (applicationView ordinaryP (FocusAssessments [assessmentId selected]))
  ordinaryView <- require (applicationView ordinaryP (FocusInput "f:hurt-caused-by-act"))
  -- A narrow assumption focus avoids expanding every satisfied guard prerequisite.
  guardView <- require (applicationView guardP (FocusAssessments
    [hurtAssessmentId "f:nature-incapacity" (Unresolved NotDetermined)]))
  focused <- concat <$> sequence
    [exportView "hurt-05-application" ordinaryP ordinaryView,
     exportView "hurt-05-selected-application" ordinaryP selectedView,
     exportView "hurt-11-application" guardP guardView]
  detail <- require (inspectAssessment ordinaryP (assessmentId selected))
  alternative <- require (inspectAssessment ordinaryP (hurtAssessmentId "f:hurt-caused-by-act" Proved))
  skipped <- require (inspectAssessment ordinaryP (hurtAssessmentId "f:unsoundness-time" NotProved))
  assumption <- require (inspectAssessment guardP (hurtAssessmentId "f:nature-incapacity" (Unresolved NotDetermined)))
  excerpt <- require (recoverOriginalSource ordinaryP anchor)
  locator <- require (recoverOriginalSource ordinaryP (SourceRef "source:hurt-law" Nothing))
  links <- traverse (require . caseAssertionLinks draft . assertionId) (documentAssertions draftDocument)
  let revised = document {documentAssertions=[if assertionId a == "assertion:pain"
        then a {assertionDescription=assertionDescription a <> " The note records a later recollection."} else a
        | a <- documentAssertions document]}
  stale <- case projectEvaluationOn revised intention of
    Left diagnostics -> pure diagnostics
    Right _ -> fail "stale hurt evaluation attached to revised narrative"
  (revisedRun,_) <- require (evaluateAcknowledged policy acknowledgements revised hurtAnalysis)
  revision <- require (projectComparison intention revisedRun)
  let summaries = [Map.fromList [("scenario" :: Text,Text.pack name),
        ("conclusion",reportConclusion (evaluationReport result)),
        ("snapshot",snapshotId (evaluationSnapshot result))] | (name,result,_,_) <- runs]
      records = draftFiles ++ concat [files | (_,_,_,files) <- runs] ++ focused ++
        [("data/hurt-case-before.document.json",encodeDocument draftDocument),
         ("data/hurt-case-before.validation.json",encodeRecord draftValidation),
         ("data/hurt-case-before.compile-diagnostics.json",encodeRecord missing),
         ("data/hurt-case-before.assertion-links.json",encodeRecord links),
         ("data/hurt-01-vs-02.comparison.json",encodeRecord routes),
         ("data/hurt-05-vs-11.comparison.json",encodeRecord uncertainties),
         ("data/hurt-05.assessment-inspection.json",encodeRecord detail),
         ("data/hurt-05.alternative-inspection.json",encodeRecord alternative),
         ("data/hurt-05.skipped-inspection.json",encodeRecord skipped),
         ("data/hurt-11.assumption-inspection.json",encodeRecord assumption),
         ("data/hurt-original-excerpt.json",encodeRecord excerpt),
         ("data/hurt-locator-only.json",encodeRecord locator),
         ("data/hurt-revised.document.json",encodeDocument revised),
         ("data/hurt-revised.application.json",encodeRecord (evaluationReport revisedRun)),
         ("data/hurt-revision.comparison.json",encodeRecord revision),
         ("data/hurt-stale-diagnostics.json",encodeRecord stale),
         ("data/hurt-summary.json",encodeRecord summaries),
         ("data/hurt-resolution-excerpt.json",encodeRecord (resolutionExcerpt detail)),
         ("data/hurt-comparison-excerpt.json",encodeRecord
           (comparisonExcerpt "01-vs-02" routes ++ comparisonExcerpt "05-vs-11" uncertainties)),
         ("INDEX.md",Encoding.encodeUtf8 artifactIndex)]
  -- Recover the same repeated section 84 input within the correct retained snapshot.
  _ <- require (inspectAssessment intentionP (hurtAssessmentId "f:unsoundness-time" NotProved))
  case destination of
    Nothing -> pure ()
    Just directory -> do
      createDirectoryIfMissing True (directory </> "data")
      mapM_ (\(name,bytes) -> BS.writeFile (directory </> name) bytes) records
  mapM_ (\bytes -> BS.putStr bytes >> BS.putStr "\n")
    [encodeRecord summaries,encodeRecord routes,encodeRecord uncertainties]

exportView :: String -> Projection -> ProjectionView -> IO [(FilePath,BS.ByteString)]
exportView name projection view = do
  complete <- require (encodeProjection projection)
  json <- require (encodeViewJson projection view)
  xml <- require (encodeViewXml projection view)
  svg <- require (encodeViewSvg projection view)
  pure [("data/" <> name <> ".projection.json",complete),
    ("data/" <> name <> ".view-bindings.json",encodeRecord view),
    ("data/" <> name <> ".view.json",json),("data/" <> name <> ".view.xml",xml),(name <> ".svg",svg)]

-- The law table has a dedicated reference encoder; case/application cards use
-- encodeViewSvg. Both carry the same complete projection and view bindings.
exportLaw :: String -> Projection -> IO [(FilePath,BS.ByteString)]
exportLaw name projection = do
  complete <- require (encodeProjection projection)
  view <- require (lawOccurrenceView projection)
  json <- require (encodeProjectionLegacyJson projection)
  xml <- require (encodeProjectionLegacyXml projection)
  svg <- require (encodeProjectionSvg projection)
  pure [("data/" <> name <> ".projection.json",complete),
    ("data/" <> name <> ".view-bindings.json",encodeRecord view),
    ("data/" <> name <> ".view.json",json),("data/" <> name <> ".view.xml",xml),(name <> ".svg",svg)]

resolutionExcerpt :: AssessmentInspection -> Map.Map Text Text
resolutionExcerpt detail = Map.fromList
  [("assessment",assessmentId (inspectionAssessment detail)),
   ("projectedAssessment",inspectionProjectedAssessment detail),
   ("input",assessmentInput (inspectionAssessment detail)),
   ("scopeActor",scopeActor (assessmentScope (inspectionAssessment detail))),
   ("context",scopeContext (assessmentScope (inspectionAssessment detail))),
   ("assertions",Text.intercalate ", " (map assertionId (resolvedAssertions (inspectionResolution detail)))),
   ("occurrences",Text.intercalate ", " (map applicationOccurrence (inspectionApplications detail))),
   ("originalExcerpt",Text.intercalate " | " [s | x <- inspectionOriginalSources detail, Just s <- [excerptText x]])]

comparisonExcerpt :: Text -> ProjectionComparison -> [Map.Map Text Text]
comparisonExcerpt label comparison =
  [Map.fromList [("comparison",label),("authoredObject",changeObject row),
    ("projectedAlignment",observationChangeAlignment mapped),
    ("oldObservation",observationChangeOldNode mapped),("newObservation",observationChangeNewNode mapped),
    ("oldComputed",maybe "absent" id (changeOldComputed row)),("newComputed",maybe "absent" id (changeNewComputed row)),
    ("oldEvaluation",changeOldEvaluation row),("newEvaluation",changeNewEvaluation row),
    ("oldReason",maybe "absent" id (changeOldReason row)),("newReason",maybe "absent" id (changeNewReason row))]
  | mapped <- projectedChangedObservations comparison, let row = observationChange mapped]

artifactIndex :: Text
artifactIndex = Text.unlines
  ["# Bounded hurt SDK example", "", "Synthetic classifications; retained research model, not complete current law.",
   "Scope acknowledgements are retained annotations/context; the legacy checker separately requires their presence.",
   "", "Each hurt-NN_NAME.svg is the existing law-occurrence view (including the represented guard).",
   "01: intention route satisfied; 02: knowledge route, same conclusion; 03: hurt not proved, guard skipped;",
   "05: ordinary causation unresolved, guard skipped; 06: evaluated exception defeat; 11: evaluated unresolved exception.",
   "hurt-case-before.svg: independent case before completed bindings, with unmapped assertion and draft.",
   "hurt-05-selected-application.svg: FocusAssessments of the selected causation assessment, resolved from the existing application report; explains that assessment and its cross-context provenance.",
   "hurt-05-application.svg: FocusInput of causation; includes that selected unresolved assessment plus retained unselected alternatives.",
   "Both 05 views use the same evaluation and complete projection; each has its own included/omitted view bindings.",
   "hurt-11-application.svg: the selected unresolved assumption in the evaluated section 84 nature route; other prerequisites are explicitly omitted from this focus.",
   "", "data/ contains complete authored documents, application reports, validated kernel requests/results,",
   "complete projections and explicit included/omitted view bindings, JSON/XML views, two comparisons,",
   "inspection and UTF-8 source-recovery records, stale-attachment diagnostics and a narrative revision comparison.",
   "All full identities and omitted context remain in the complete projection; no view adds legal semantics.",
   "PNG previews can be generated with rsvg-convert --output FILE.png FILE.svg."]

require :: Show a => Either a b -> IO b
require = either (fail . show) pure
