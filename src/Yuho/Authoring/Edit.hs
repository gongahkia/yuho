{-# LANGUAGE OverloadedStrings #-}
-- | Small experimental ID-addressed conveniences, not a patch language.
-- Updates preserve the ID and list position. They may return a structurally
-- invalid candidate: call validateDocument/validateAnalysis before execution.
module Yuho.Authoring.Edit
  ( editLawNode, editLawEdge, editCaseAssertion, selectAssessment ) where

import Data.Text (Text)
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue, selectedOccurrences, Occurrence(..))

editLawNode :: Text -> (LawNode -> LawNode) -> AuthoringDocument
            -> Either [AuthoringDiagnostic] AuthoringDocument
editLawNode = edit "/documentLaw/lawNodes" nodeId (lawNodes . documentLaw)
  (\xs doc -> doc {documentLaw=(documentLaw doc) {lawNodes=xs}})

editLawEdge :: Text -> (LawEdge -> LawEdge) -> AuthoringDocument
            -> Either [AuthoringDiagnostic] AuthoringDocument
editLawEdge = edit "/documentLaw/lawEdges" edgeId (lawEdges . documentLaw)
  (\xs doc -> doc {documentLaw=(documentLaw doc) {lawEdges=xs}})

editCaseAssertion :: Text -> (CaseAssertion -> CaseAssertion) -> AuthoringDocument
                  -> Either [AuthoringDiagnostic] AuthoringDocument
editCaseAssertion = edit "/documentAssertions" assertionId documentAssertions
  (\xs doc -> doc {documentAssertions=xs})

-- | Select a retained assessment for its input, replacing the one existing
-- binding in place or appending if missing. Alternatives are never removed.
-- Reject ambiguous existing bindings, dangling selections, wrong scope or a
-- target outside the selected slice. Other missing bindings remain drafts.
selectAssessment :: Text -> Text -> AuthoringDocument
                 -> Either [AuthoringDiagnostic] AuthoringDocument
selectAssessment analysisKey assessmentKey doc = do
  analysis <- locate "/documentAnalyses" analysisId documentAnalyses analysisKey doc
  assessment <- locate "/documentAssessments" assessmentId documentAssessments assessmentKey doc
  input <- locate "/documentLaw/lawNodes" nodeId (lawNodes . documentLaw) (assessmentInput assessment) doc
  let refs = [analysisKey,assessmentKey,assessmentInput assessment]
      failure code message = Left [issue code "/documentAnalyses" refs message]
  if nodeKind input /= "input" then failure "ETARGET" "assessment target is not a legal input" else pure ()
  if assessmentScope assessment /= analysisScope analysis
    then failure "ESCOPE" "assessment actor/context differs from analysis" else pure ()
  if assessmentInput assessment `notElem`
      [nodeId (occurrenceNode o) | o <- selectedOccurrences doc analysis, nodeKind (occurrenceNode o) == "input"]
    then failure "ETARGET" "assessment input is outside the selected executable slice" else pure ()
  selected <- traverse (\key -> locate "/documentAssessments" assessmentId documentAssessments key doc)
    (analysisAssessments analysis)
  let active = filter ((== assessmentInput assessment) . assessmentInput) selected
  next <- case active of
    [] -> Right (analysisAssessments analysis ++ [assessmentKey])
    [old] -> Right [if key == assessmentId old then assessmentKey else key | key <- analysisAssessments analysis]
    _ -> Left [issue "EAMBIGUOUS" "/documentAnalyses" (refs ++ map assessmentId active)
      "multiple existing selections for this input; resolve them explicitly before selecting"]
  edit "/documentAnalyses" analysisId documentAnalyses (\xs d -> d {documentAnalyses=xs})
    analysisKey (\a -> a {analysisAssessments=next}) doc

edit :: Text -> (a -> Text) -> (AuthoringDocument -> [a])
     -> ([a] -> AuthoringDocument -> AuthoringDocument)
     -> Text -> (a -> a) -> AuthoringDocument -> Either [AuthoringDiagnostic] AuthoringDocument
edit path identify objects replace key update doc = do
  original <- locate path identify objects key doc
  let changed = update original
  if identify changed /= key
    then Left [issue "EIDENTITY" path [key,identify changed]
      "updates must preserve the authored ID; adding an object requires a distinct explicit ID"]
    else Right (replace [if identify x == key then changed else x | x <- objects doc] doc)

locate :: Text -> (a -> Text) -> (AuthoringDocument -> [a]) -> Text -> AuthoringDocument
       -> Either [AuthoringDiagnostic] a
locate path identify objects key doc =
  case length (filter (== key) (identities doc)) of
    0 -> bad "ENOTFOUND" "authored ID not found"
    1 -> case filter ((== key) . identify) (objects doc) of
      [x] -> Right x
      _ -> bad "ETYPE" "authored ID belongs to a different object kind"
    _ -> bad "EDUPLICATE" "authored ID is ambiguous; repair duplicate identities first"
  where bad code message = Left [issue code path [key] message]

-- Count the document-wide namespace, not just the requested record collection.
-- Presentation rows are references, not independently identified objects.
identities :: AuthoringDocument -> [Text]
identities doc = [documentId doc,lawId law] ++ map nodeId (lawNodes law) ++ map edgeId (lawEdges law)
  ++ map sourceId (documentSources doc) ++ map assertionId (documentAssertions doc)
  ++ map assessmentId (documentAssessments doc) ++ map analysisId (documentAnalyses doc)
  ++ map relationshipId (documentRelationships doc) ++ map annotationId (documentAnnotations doc)
  where law = documentLaw doc
