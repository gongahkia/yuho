{-# LANGUAGE OverloadedStrings #-}
-- Ordinary consumer-authored updates over the retained cheating example.
module CaseApplication
  ( caseDocument, caseDraft, revisedCase, pendingCase, runCaseApplicationDemo ) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import Data.List (find)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import Cheating
import Yuho.Authoring

caseDocument :: AuthoringDocument
caseDocument = cheatingDocument
  { documentSources = documentSources cheatingDocument ++
      [SourceRecord "source:case-note" "synthetic" (Just "supplied synthetic note")
        (Just "Note: 猫 item.\nDelivery reported."),
       SourceRecord "source:registry" "other" (Just "https://example.invalid/record") Nothing]
  , documentAssertions = [case assertionId a of
        "assertion:description" -> a {assertionSources=assertionSources a ++ [noteAnchor]}
        "assertion:message" -> a {assertionScope=Scope "actor:buyer" "context:message-exchange"}
        _ -> a | a <- documentAssertions cheatingDocument] ++
      [CaseAssertion "assertion:weather" "The observer records rain during the later interview."
        (Scope "actor:observer" "context:later-interview") [SourceRef "source:registry" Nothing]]
  , documentAssessments = [if assessmentInput a == "f:deception"
        then a {assessmentSources=[noteAnchor]} else a | a <- documentAssessments cheatingDocument] ++
      [Assessment "assessment:deception-alternative" "f:deception" scope (Classification Proved)
        "Alternative reading retained for review; this assessment is not selected."
        "second-demo-caller" "external_assertion" "case_material"
        ["assertion:description","assertion:message"] [noteAnchor],
       Assessment "assessment:deception-other-context" "f:deception"
        (Scope "actor:other" "context:other-analysis") (Classification Proved)
        "An explicit assumption for a different actor and context."
        "other-demo-caller" "external_assertion" "assumption" [] []]
  , documentAnnotations = documentAnnotations cheatingDocument ++
      [Annotation "annotation:case-draft" ["assertion:description","assertion:weather"]
        "Draft: obtain fuller wording of the recorded descriptions." "draft"]
  , documentRelationships = documentRelationships cheatingDocument ++
      [Relationship "relationship:case-support" "support" "assertion:description" "assertion:message"
        "Author-recorded support only; no evidence aggregation."]
  }
  where
    scope = Scope "actor:seller" "context:transaction-1"
    noteAnchor = SourceRef "source:case-note" (Just (TextSpan 6 15 1 7 1 16))

caseDraft :: AuthoringDocument
caseDraft = caseDocument {documentAnalyses=[a {analysisAssessments=[]} | a <- documentAnalyses caseDocument]}

revisedCase :: AuthoringDocument
revisedCase = caseDocument {documentAssertions=
  [if assertionId a == "assertion:description"
    then a {assertionDescription="The seller described the item as valuable; the buyer records this as an estimate."}
    else a | a <- documentAssertions caseDocument]}

pendingCase :: AuthoringDocument
pendingCase = revisedCase {documentAnalyses=[a {analysisAssessments=
  [if key == assessmentFor "f:property-fraudulent-or-dishonest"
    then "assessment:property-fault-pending" else key | key <- analysisAssessments a]}
  | a <- documentAnalyses revisedCase]}

runCaseApplicationDemo :: IO [(FilePath,BS.ByteString)]
runCaseApplicationDemo = do
  decoded <- require (decodeDocument (encodeDocument caseDocument))
  unless (decoded == caseDocument) (fail "case authorship round-trip changed content")
  before <- require (projectAuthored caseDraft "analysis:cheating")
  beforeView <- require (caseView before)
  original <- run caseDocument
  applied <- require (projectEvaluation original)
  appliedView <- require (applicationView applied (FocusInput "f:deception"))
  stale <- case projectEvaluationOn revisedCase original of
    Left diagnostics | any ((== "PSTALE") . diagnosticCode) diagnostics -> pure diagnostics
    _ -> fail "old evaluation accepted revised narrative"
  revised <- run revisedCase
  revisedProjection <- require (projectEvaluation revised)
  revisedView <- require (applicationView revisedProjection (FocusInput "f:deception"))
  narrativeComparison <- require (projectComparison original revised)
  unless (not (projectedConclusionChanged narrativeComparison)
    && null (projectedChangedObservations narrativeComparison)
    && any (changeReferencedMaterial . assessmentChange) (projectedAssessmentChanges narrativeComparison)
    && documentAssessments caseDocument == documentAssessments revisedCase
    && snapshotDocument (evaluationSnapshot original) == caseDocument)
    (fail "narrative edit silently changed classification or computation")
  pending <- run pendingCase
  pendingProjection <- require (projectEvaluation pending)
  pendingView <- require (applicationView pendingProjection (FocusInput "f:property-fraudulent-or-dishonest"))
  skippedView <- require (applicationView pendingProjection (FocusInput "f:unsoundness-time"))
  pendingComparison <- require (projectComparison revised pending)
  unless (projectedConclusionChanged pendingComparison) (fail "explicit assessment change was lost")
  detail <- require (inspectAssessment applied (assessmentFor "f:deception"))
  alternative <- require (inspectAssessment applied "assessment:deception-alternative")
  skipped <- require (inspectAssessment pendingProjection (assessmentFor "f:unsoundness-time"))
  links <- traverse (require . caseAssertionLinks before . assertionId) (documentAssertions caseDraft)
  rendered <- concat <$> mapM (\(name,projection,view) -> viewFiles name projection view)
    [("case-before",before,beforeView),("application-selected",applied,appliedView),
     ("application-revised",revisedProjection,revisedView),("application-pending",pendingProjection,pendingView),
     ("application-skipped",pendingProjection,skippedView)]
  let resolutionExcerpt = Map.fromList
        [("authoredAssessment" :: Text,assessmentId (inspectionAssessment detail)),
         ("projectedAssessment",inspectionProjectedAssessment detail),
         ("targetInput",assessmentInput (inspectionAssessment detail)),
         ("selected","true"),("supplied","proved"),
         ("assertions",Text.intercalate ", " (map assertionId (resolvedAssertions (inspectionResolution detail)))),
         ("occurrence",Text.intercalate ", " (map applicationOccurrence (inspectionApplications detail))),
         ("originalExcerpt",Text.intercalate " | " [s | x <- inspectionOriginalSources detail, Just s <- [excerptText x]])]
      revisionExcerpt = Map.fromList
        [("oldSnapshot" :: Text,snapshotId (evaluationSnapshot original)),
         ("newSnapshot",snapshotId (evaluationSnapshot revised)),
         ("authoredAssertion","assertion:description"),
         ("oldDescription",description caseDocument),("newDescription",description revisedCase),
         ("assessmentSelectionChanged","false"),("suppliedClassificationsChanged","false"),
         ("referencedMaterialChanges",count (filter (changeReferencedMaterial . assessmentChange) (projectedAssessmentChanges narrativeComparison))),
         ("computedObservationChanges",count (projectedChangedObservations narrativeComparison)),
         ("unchangedObservations",count (projectedUnchangedObservations narrativeComparison)),
         ("oldConclusion",reportConclusion (evaluationReport original)),
         ("newConclusion",reportConclusion (evaluationReport revised)),
         ("explicitSelectionChanges",count (filter (changeSelection . assessmentChange) (projectedAssessmentChanges pendingComparison))),
         ("explicitChangedObservations",count (projectedChangedObservations pendingComparison)),
         ("explicitNewConclusion",reportConclusion (evaluationReport pending))]
  pure (rendered ++
    [("assessment-resolution.json",encodeRecord detail),("alternative-resolution.json",encodeRecord alternative),
     ("skipped-resolution.json",encodeRecord skipped),("resolution-excerpt.json",encodeRecord resolutionExcerpt),
     ("case-assertion-links.json",encodeRecord links),("revision-excerpt.json",encodeRecord revisionExcerpt),
     ("narrative.comparison-projection.json",encodeRecord narrativeComparison),
     ("explicit-selection.comparison-projection.json",encodeRecord pendingComparison),
     ("revision-stale-diagnostics.json",encodeRecord stale)])
  where
    run doc = require (compileAnalysis doc "analysis:cheating" >>= evaluateAnalysis)
    count = Text.pack . show . length
    description doc = maybe "" assertionDescription (find ((== "assertion:description") . assertionId) (documentAssertions doc))

viewFiles :: String -> Projection -> ProjectionView -> IO [(FilePath,BS.ByteString)]
viewFiles name projection view = do
  complete <- require (encodeProjection projection)
  json <- require (encodeViewJson projection view)
  xml <- require (encodeViewXml projection view)
  svg <- require (encodeViewSvg projection view)
  pure [(name <> ".projection.json",complete),(name <> ".view-bindings.json",encodeRecord view),
    (name <> ".view.json",json),(name <> ".view.xml",xml),(name <> ".svg",svg)]

require :: Show a => Either a b -> IO b
require = either (fail . show) pure
