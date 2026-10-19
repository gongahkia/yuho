{-# LANGUAGE OverloadedStrings #-}
-- | Derived diagrams; none of these operations compile or evaluate a model.
module Yuho.Authoring.Projection
  ( Projection, projectionData, projectAuthored, projectEvaluation
  , projectEvaluationOn, projectComparison, validateProjection
  , resolveProjectedObject
  , objectProjectionId, occurrenceProjectionId, observationProjectionId
  , projectionIdentity, module Yuho.Authoring.Projection.Types ) where

import Data.Aeson (ToJSON)
import Data.Char (isAsciiLower, isDigit)
import Data.List (find, group, nub, sort)
import Data.Maybe (mapMaybe)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Compile
import Yuho.Authoring.Projection.Types
import Yuho.Authoring.Report
import Yuho.Authoring.Snapshot (makeSnapshot)
import Yuho.Authoring.Types
import Yuho.Authoring.Validate
import Yuho.Protocol.Decode (sha256Text)

-- Hidden constructor and ordinary getters prevent unchecked record updates.
newtype Projection = Projection ProjectionData
projectionData :: Projection -> ProjectionData
projectionData (Projection value) = value

projectionIdentity :: ToJSON a => Text -> a -> Text
projectionIdentity category value = "p-" <> category <> "-" <> sha256Text (encodeRecord value)

objectProjectionId :: Text -> Text
objectProjectionId = projectionIdentity "object"
occurrenceProjectionId :: OccurrenceIdentity -> Text
occurrenceProjectionId = projectionIdentity "occurrence"
observationProjectionId :: ObservationIdentity -> Text
observationProjectionId = projectionIdentity "observation"

authoredObjects :: AuthoringDocument -> [(Text,Text,Text)]
authoredObjects doc =
  [(documentId doc,"document",documentId doc),(lawId law,"law",lawId law)]
  ++ [(nodeId n,nodeKind n,nodeLabel n) | n <- lawNodes law]
  ++ [(edgeId e,"law_relationship",edgeKind e) | e <- lawEdges law]
  ++ [(sourceId s,"original_source",maybe (sourceId s) id (sourceLocator s)) | s <- documentSources doc]
  ++ [(assertionId a,"assertion",assertionDescription a) | a <- documentAssertions doc]
  ++ [(assessmentId a,"assessment",assessmentId a) | a <- documentAssessments doc]
  ++ [(analysisId a,"analysis",analysisId a) | a <- documentAnalyses doc]
  ++ [(relationshipId r,"descriptive_relationship",relationshipComment r) | r <- documentRelationships doc]
  ++ [(annotationId a,"annotation",annotationText a) | a <- documentAnnotations doc]
  where law = documentLaw doc

origin :: Text -> Text -> [Text] -> ProjectionOrigin
origin kind role objects = ProjectionOrigin kind role (nub objects)

plainNode :: Text -> Text -> Text -> Text -> ProjectionOrigin -> ProjectionNode
plainNode identifier kind role label provenance = ProjectionNode identifier kind role label provenance
  Nothing Nothing Nothing Nothing Nothing "not_applicable" Nothing Nothing

projectAuthored :: AuthoringDocument -> Text -> Either [AuthoringDiagnostic] Projection
projectAuthored doc key = do
  let validation = validateBindings doc key
      errors = filter ((/= "AMISSING") . diagnosticCode) (validationDiagnostics validation)
  if null errors then pure () else Left errors
  analysis <- maybe (Left [issue "PTARGET" "/documentAnalyses" [key] "analysis not found"])
    Right (findAnalysis doc key)
  let occurrences = selectedOccurrences doc analysis
  -- The SDK's bounded traversal must never silently truncate a diagram.
  if length occurrences >= 1025 then Left [issue "PLIMIT" "/documentLaw" [key]
    "projection exceeds 1024 structural requirement occurrences"] else pure ()
  let snapshot = makeSnapshot doc analysis
      law = documentLaw doc
      selected = analysisAssessments analysis
      guards = [e | e <- lawEdges law, edgeFrom e == analysisTarget analysis, edgeKind e == "exception"]
      rulePath r = case [edgeId e | e <- guards, edgeTo e == r] of
        [e] -> [e]
        _ -> []
      ruleOccurrences = [(n,rulePath r,r) | r <- nub (analysisTarget analysis : map occurrenceRule occurrences),
        n <- lawNodes law, nodeId n == r]
      allOccurrences = ruleOccurrences ++ [(occurrenceNode o,occurrencePath o,occurrenceRule o) | o <- occurrences]
      identity n path rule = OccurrenceIdentity (snapshotLawDigest snapshot) (analysisTarget analysis)
        (analysisScope analysis) (nodeId n) rule path
      assessmentById identifier = find ((== identifier) . assessmentId) (documentAssessments doc)
      active input = find ((== input) . assessmentInput) (mapMaybe assessmentById selected)
      binding Nothing = ProjectedBinding "missing" Nothing Nothing Nothing
      binding (Just a) = ProjectedBinding "selected" (Just (assessmentId a))
        (Just (assessmentClassification a)) (Just (assessmentReason a))
      objects = [let base = plainNode (objectProjectionId identifier) "authored" role label
                        (origin "authored" role [identifier])
                 in case assessmentById identifier of
                   Just a -> base { projectedNodeSelected = Just (identifier `elem` selected),
                     projectedNodeBinding = Just ((binding (Just a))
                       { bindingState = if identifier `elem` selected then "selected" else "alternative" }) }
                   Nothing -> base
        | (identifier,role,label) <- authoredObjects doc]
      occurrenceNodes = [let occurrence = identity n path rule
        in (plainNode (occurrenceProjectionId occurrence) "occurrence" (nodeKind n) (nodeLabel n)
          (origin "projection_generated" "structural_occurrence" (nodeId n : rule : path)))
          { projectedNodeOccurrence = Just occurrence, projectedNodeEvaluation = "not_requested",
            projectedNodeBinding = if nodeKind n == "input" then Just (binding (active (nodeId n))) else Nothing }
        | (n,path,rule) <- allOccurrences]
      makeEdge kind semantics from to provenance anchor discriminator = ProjectionEdge
        (projectionIdentity "edge" (kind,from,to,discriminator)) from to kind semantics provenance anchor
      authoredEdge identifier from to kind semantics = ProjectionEdge
        (projectionIdentity "relationship" identifier) (objectProjectionId from) (objectProjectionId to)
        kind semantics (origin "authored" "relationship" [identifier]) Nothing
      lawEdgesProjected = [authoredEdge (edgeId e) (edgeFrom e) (edgeTo e) (edgeKind e) "law_structure" | e <- lawEdges law]
      descriptive = [authoredEdge (relationshipId r) (relationshipFrom r) (relationshipTo r)
        (relationshipKind r) "descriptive" | r <- documentRelationships doc]
      membership = [makeEdge (edgeKind edge) "occurrence_structure"
          (occurrenceProjectionId (identity parent parentPath parentRule))
          (occurrenceProjectionId (identity n path rule))
          (origin "projection_generated" "structural_connection" [edgeId edge]) Nothing path
        | (n,path,rule) <- allOccurrences, not (null path),
          edge <- lawEdges law, edgeId edge == last path,
          (parent,parentPath,parentRule) <- allOccurrences,
          parentPath == init path, nodeId parent == edgeFrom edge]
      definitionLinks = [makeEdge "instance_of" "projection"
        (occurrenceProjectionId (identity n path rule)) (objectProjectionId (nodeId n))
        (origin "projection_generated" "definition_reference" [nodeId n]) Nothing path
        | (n,path,rule) <- allOccurrences]
      selectionLinks = [makeEdge "selected_assessment" "assessment_selection"
        (objectProjectionId (assessmentId a)) (occurrenceProjectionId (identity n path rule))
        (origin "projection_generated" "explicit_assessment_selection" [key,assessmentId a,nodeId n]) Nothing path
        | (n,path,rule) <- allOccurrences, nodeKind n == "input", Just a <- [active (nodeId n)]]
      reference :: Text -> Text -> Text -> Text -> Int -> Maybe SourceRef -> ProjectionEdge
      reference kind semantics owner target index anchor = makeEdge kind semantics
        (objectProjectionId owner) (objectProjectionId target)
        (origin "projection_generated" kind [owner,target]) anchor [owner,Text.pack (show index)]
      indexed values = zip [0 :: Int ..] values
      sourceReferences kind owner refs = [reference kind "provenance" owner (referenceSource ref) i (Just ref)
        | (i,ref) <- indexed refs]
      assessmentLinks = concat
        [[reference "assessment_input" "assessment_binding" (assessmentId a) (assessmentInput a) 0 Nothing]
          ++ [reference "assessment_assertion" "provenance" (assessmentId a) target i Nothing
              | (i,target) <- indexed (assessmentAssertions a)]
          ++ sourceReferences "assessment_source" (assessmentId a) (assessmentSources a)
        | a <- documentAssessments doc]
      sourceLinks = concat [sourceReferences "law_source" (nodeId n) (nodeSources n) | n <- lawNodes law]
        ++ concat [sourceReferences "assertion_source" (assertionId a) (assertionSources a) | a <- documentAssertions doc]
      annotationLinks = [reference "annotation_about" "descriptive" (annotationId a) target i Nothing
        | a <- documentAnnotations doc, (i,target) <- indexed (annotationAbout a)]
      analysisLinks = concat [[reference "analysis_target" "projection" (analysisId a) (analysisTarget a) 0 Nothing]
        ++ [reference "analysis_selection" "assessment_selection" (analysisId a) target i Nothing
           | (i,target) <- indexed (analysisAssessments a)] | a <- documentAnalyses doc]
      relationshipLinks = concat [[reference "relationship_subject" "projection" identifier from 0 Nothing,
        reference "relationship_object" "projection" identifier to 1 Nothing]
        | (identifier,from,to) <- [(edgeId e,edgeFrom e,edgeTo e) | e <- lawEdges law]
            ++ [(relationshipId r,relationshipFrom r,relationshipTo r) | r <- documentRelationships doc]]
      contents = [reference "contains" "projection" (documentId doc) identifier i Nothing
        | (i,(identifier,_,_)) <- indexed (authoredObjects doc), identifier /= documentId doc]
      result = ProjectionData projectionFormat (projectionIdentity "analysis" (snapshotId snapshot,"authored" :: Text))
        "authored" snapshot Nothing Nothing (objects ++ occurrenceNodes)
        (lawEdgesProjected ++ descriptive ++ membership ++ definitionLinks ++ selectionLinks ++ assessmentLinks
          ++ sourceLinks ++ annotationLinks ++ analysisLinks ++ relationshipLinks ++ contents)
        (validationDiagnostics validation) (openInputs validation)
        "Derived projection, not an authoring import. Law connections, supplied assessments, provenance and descriptive relationships have separate meanings."
  checked result

-- | Uses the evaluation's own immutable snapshot and existing observations.
projectEvaluation :: Evaluation -> Either [AuthoringDiagnostic] Projection
projectEvaluation evaluated = do
  let snapshot = evaluationSnapshot evaluated
      doc = snapshotDocument snapshot
      report = evaluationReport evaluated
      analysis = snapshotAnalysis snapshot
      compiled = evaluationCompilation evaluated
  authored <- projectAuthored doc (analysisId analysis)
  if snapshot == projectionSnapshot (projectionData authored)
      && reportSnapshot report == snapshotId snapshot && reportAnalysis report == analysisId analysis
      && reportScope report == analysisScope analysis && reportTarget report == analysisTarget analysis
    then pure () else Left [issue "PSNAPSHOT" "/projectionApplication" [analysisId analysis]
      "application report does not match its retained snapshot"]
  let dataValue = projectionData authored
      occurrenceFor node path rule = find (\n -> case projectedNodeOccurrence n of
        Just o -> occurrenceAuthoredNode o == node && occurrenceEdges o == path && occurrenceAuthoredRule o == rule
        Nothing -> False) (projectionNodes dataValue)
      ruleFor key = find (\n -> maybe False (\o -> occurrenceAuthoredNode o == key
        && occurrenceAuthoredRule o == key) (projectedNodeOccurrence n)) (projectionNodes dataValue)
      guardKernel key = case [identityKernelId m | m <- compiledIdentities compiled,
          identityKind m == "exception", key `elem` identityAuthoredIds m] of
        [identifier] -> Just identifier
        _ -> Nothing
      requirementRows = [("requirement",observationNode r,observationOccurrence r,
          Just (observationKernelId r),Just (observationKernelBranch r),observationComputed r,
          observationEvaluation r,observationSkipReason r,Nothing,
          projectedNodeId <$> occurrenceFor (observationNode r) (observationOccurrence r) (observationRule r))
        | r <- reportRequirements report]
      ruleRows = [("rule",ruleAuthoredId r,[],Just (ruleKernelId r),Just (ruleKernelBranch r),
          ruleComputed r,ruleEvaluation r,
          (if ruleEvaluation r == "not_evaluated" then
            find ((== ruleAuthoredId r) . exceptionGuardRule) (reportExceptions report) >>= exceptionSkipReason
           else Nothing),ruleBranchReason r,projectedNodeId <$> ruleFor (ruleAuthoredId r))
        | r <- reportRules report]
      exceptionRows = [("exception",exceptionRelationship r,[],guardKernel (exceptionRelationship r),Nothing,
          exceptionComputed r,exceptionEvaluation r,exceptionSkipReason r,Nothing,
          Just (objectProjectionId (exceptionRelationship r))) | r <- reportExceptions report]
      rows = requirementRows ++ ruleRows ++ exceptionRows
      identities = [(ObservationIdentity (snapshotId snapshot) (reportProfile report) category key path kernel branch,
        computed,state,skip,reason,target) | (category,key,path,kernel,branch,computed,state,skip,reason,target) <- rows]
      expected = [projectedNodeId n | n <- projectionNodes dataValue, projectedNodeKind n == "occurrence"]
      actual = [target | (i,_,_,_,_,Just target) <- identities, observationCategory i /= "exception"]
  if sort expected == sort actual && all (\(_,_,_,_,_,target) -> target /= Nothing) identities
    then pure () else Left [issue "POBSERVATION" "/projectionApplication" [analysisId analysis]
      "report occurrence coverage is incomplete or ambiguous"]
  let observations = [(plainNode (observationProjectionId identity) "observation" (observationCategory identity)
          (observationAuthoredObject identity) (origin "projection_generated" "run_observation"
            [observationAuthoredObject identity])) { projectedNodeObservation = Just identity,
            projectedNodeComputed = computed, projectedNodeEvaluation = state,
            projectedNodeSkipReason = skip, projectedNodeBranchReason = reason }
        | (identity,computed,state,skip,reason,_) <- identities]
      overlay n = case [(identity,computed,state,skip,reason) | (identity,computed,state,skip,reason,Just target) <- identities,
            target == projectedNodeId n, projectedNodeKind n == "occurrence"] of
        [(identity,computed,state,skip,reason)] -> n { projectedNodeObservation = Just identity,
          projectedNodeComputed = computed, projectedNodeEvaluation = state,
          projectedNodeSkipReason = skip, projectedNodeBranchReason = reason }
        _ -> n
      generatedSources = [plainNode (projectionIdentity "kernel-source" (snapshotId snapshot,generatedSourceId s))
        "generated_source" (generatedSourceKind s) (generatedSourceId s)
        (origin "projection_generated" "generated_kernel_source" (generatedSourceObjects s)) | s <- compiledSources compiled]
      observationLinks = [ProjectionEdge (projectionIdentity "observation-link" (observationProjectionId identity,target))
        (observationProjectionId identity) target "observes" "observation"
        (origin "projection_generated" "existing_report_observation" [observationAuthoredObject identity]) Nothing
        | (identity,_,_,_,_,Just target) <- identities]
      generatedLinks = [ProjectionEdge (projectionIdentity "generated-link" (observationProjectionId identity,i :: Int))
        (observationProjectionId identity) (projectionIdentity "kernel-source" (snapshotId snapshot,sourceMappingSource mapping))
        "generated_span" "generated_provenance"
        (origin "projection_generated" "generated_span" (sourceMappingObjects mapping)) Nothing
        | (identity,_,_,_,_,_) <- identities, Just kernel <- [observationOriginalKernelId identity],
          (i,mapping) <- zip [0..] (compiledSourceMappings compiled), sourceMappingKernelId mapping == kernel]
  checked dataValue { projectionId = projectionIdentity "analysis" (snapshotId snapshot,"evaluated" :: Text),
    projectionMode = "evaluated", projectionApplication = Just report,
    projectionCompiler = Just (CompilerProvenance (compiledSources compiled) (compiledIdentities compiled) (compiledSourceMappings compiled)),
    projectionNodes = map overlay (projectionNodes dataValue) ++ observations ++ generatedSources,
    projectionEdges = projectionEdges dataValue ++ observationLinks ++ generatedLinks }

-- | Any changed retained input, even a reason or presentation property, fails.
projectEvaluationOn :: AuthoringDocument -> Evaluation -> Either [AuthoringDiagnostic] Projection
projectEvaluationOn doc evaluated
  | doc == snapshotDocument (evaluationSnapshot evaluated) = projectEvaluation evaluated
  | otherwise = Left [issue "PSTALE" "/projectionSnapshot" [documentId doc]
      "separate document differs from the evaluation's immutable authored snapshot"]

-- | Resolve a displayed node or relationship, keeping generated anchors in a
-- separate field from original references. No inference follows these links.
resolveProjectedObject :: Projection -> Text -> Maybe ProjectionResolution
resolveProjectedObject projection identifier = do
  let value = projectionData projection
      doc = snapshotDocument (projectionSnapshot value)
      node = find ((== identifier) . projectedNodeId) (projectionNodes value)
      edge = find ((== identifier) . projectedEdgeId) (projectionEdges value)
  provenance <- case (node,edge) of
    (Just n,_) -> Just (projectedNodeOrigin n)
    (_,Just e) -> Just (projectedEdgeOrigin e)
    _ -> Nothing
  let observedTargets = [n | e <- projectionEdges value, projectedEdgeFrom e == identifier,
        projectedEdgeKind e == "observes", n <- projectionNodes value, projectedNodeId n == projectedEdgeTo e]
      bindings = mapMaybe projectedNodeBinding (maybe [] (:[]) node ++ observedTargets)
      initialIds = originAuthoredObjects provenance ++ mapMaybe bindingAssessment bindings
      assessments = [a | a <- documentAssessments doc, assessmentId a `elem` initialIds]
      assertionIds = concatMap assessmentAssertions assessments
      assertions = [a | a <- documentAssertions doc, assertionId a `elem` initialIds ++ assertionIds]
      lawNodesResolved = [n | n <- lawNodes (documentLaw doc), nodeId n `elem` initialIds]
      originalReferences = concatMap nodeSources lawNodesResolved ++ concatMap assessmentSources assessments
        ++ concatMap assertionSources assertions ++ maybe [] (maybe [] (:[]) . projectedEdgeOriginalSource) edge
      allAuthoredIds = nub (initialIds ++ assertionIds ++ map referenceSource originalReferences)
      kernelIds = mapMaybe (\n -> projectedNodeObservation n >>= observationOriginalKernelId)
        (maybe [] (:[]) node ++ observedTargets)
      generated = maybe [] (filter (\m -> sourceMappingKernelId m `elem` kernelIds) . projectionGeneratedSpans)
        (projectionCompiler value)
  pure (ProjectionResolution (snapshotId (projectionSnapshot value)) allAuthoredIds lawNodesResolved
    [e | e <- lawEdges (documentLaw doc), edgeId e `elem` allAuthoredIds]
    assessments assertions [s | s <- documentSources doc, sourceId s `elem` allAuthoredIds]
    originalReferences
    [r | r <- documentRelationships doc, any (`elem` allAuthoredIds)
      [relationshipId r,relationshipFrom r,relationshipTo r]]
    [a | a <- documentAnnotations doc, annotationId a `elem` allAuthoredIds
      || any (`elem` allAuthoredIds) (annotationAbout a)] generated)

checked :: ProjectionData -> Either [AuthoringDiagnostic] Projection
checked value = case validateProjection value of
  [] -> Right (Projection value)
  diagnostics -> Left diagnostics

validateProjection :: ProjectionData -> [AuthoringDiagnostic]
validateProjection value = version ++ duplicates ++ endpoints ++ origins ++ identifiers
  where
    nodes = projectionNodes value
    edges = projectionEdges value
    nodeIds = Set.fromList (map projectedNodeId nodes)
    allIds = map projectedNodeId nodes ++ map projectedEdgeId edges
    authored = Set.fromList [key | (key,_,_) <- authoredObjects (snapshotDocument (projectionSnapshot value))]
    version = [issue "PVERSION" "/projectionVersion" [] "unsupported projection version"
      | projectionVersion value /= projectionFormat]
    duplicates = [issue "PDUPLICATE" "/" [key] "duplicate projected identity"
      | (key:_:_) <- group (sort allIds)]
    endpoints = [issue "PENDPOINT" "/projectionEdges" [projectedEdgeId e,target] "projected endpoint is absent"
      | e <- edges, target <- [projectedEdgeFrom e,projectedEdgeTo e], Set.notMember target nodeIds]
    provenance = [(projectedNodeId n,projectedNodeOrigin n) | n <- nodes]
      ++ [(projectedEdgeId e,projectedEdgeOrigin e) | e <- edges]
    origins = [issue "PORIGIN" "/" [key] "projection origin must identify existing authored objects"
      | (key,o) <- provenance, originKind o `notElem` ["authored","projection_generated"]
        || null (originAuthoredObjects o) || any (`Set.notMember` authored) (originAuthoredObjects o)]
    -- Fixed ASCII identities survive legacy SVG/XML sanitization injectively.
    identifiers = [issue "PID" "/" [key] "projected ID is not render-safe ASCII"
      | key <- projectionId value : allIds, not (Text.isPrefixOf "p-" key)
        || not (Text.all (\c -> isAsciiLower c || isDigit c && c <= '9' || c == '-') key)]

projectComparison :: Evaluation -> Evaluation -> Either [AuthoringDiagnostic] ProjectionComparison
projectComparison old new = do
  comparison <- compareAnalyses old new
  left <- projectEvaluation old
  right <- projectEvaluation new
  let a = projectionData left
      b = projectionData right
      observation value row = find (\n -> case projectedNodeObservation n of
        Just identity -> projectedNodeKind n == "observation"
          && observationCategory identity == changeObservationKind row
          && observationAuthoredObject identity == changeObject row && observationAuthoredPath identity == changePath row
        Nothing -> False) (projectionNodes value)
      align value n = case projectedNodeObservation n of
        Nothing -> Nothing
        Just identity -> case [projectedEdgeTo e | e <- projectionEdges value,
              projectedEdgeFrom e == observationProjectionId identity, projectedEdgeKind e == "observes"] of
          [target] -> Just target
          _ -> Nothing
      attach row = case (observation a row,observation b row) of
        (Just x,Just y) | Just i <- projectedNodeObservation x, Just j <- projectedNodeObservation y,
          Just alignment <- align a x, align b y == Just alignment ->
            Right (ProjectedObservationChange row alignment (projectedNodeId x) (projectedNodeId y) i j
              (changeOldComputed row /= changeNewComputed row)
              (changeOldEvaluation row == "evaluated" && changeNewEvaluation row == "evaluated"
                && changeOldComputed row /= changeNewComputed row)
              (changeOldEvaluation row /= changeNewEvaluation row)
              (changeOldReason row /= changeNewReason row)
              (changeObservationKind row == "rule" && changeOldReason row /= changeNewReason row))
        _ -> Left [issue "PALIGNMENT" "/comparison" [changeObject row] "comparison observation cannot be aligned"]
      assessmentRow row = case [projectedNodeId n | n <- projectionNodes a,
          Just o <- [projectedNodeOccurrence n], occurrenceAuthoredNode o == changeInput row,
          occurrenceEdges o == changeOccurrence row] of
        [occurrence] -> Right (ProjectedAssessmentChange row occurrence
          (objectProjectionId . assessmentId <$> changeOldAssessment row)
          (objectProjectionId . assessmentId <$> changeNewAssessment row))
        _ -> Left [issue "PALIGNMENT" "/comparison" [changeInput row] "assessment occurrence cannot be aligned"]
  assessments <- traverse assessmentRow (comparisonAssessments comparison)
  changed <- traverse attach (comparisonChanged comparison)
  unchanged <- traverse attach (comparisonUnchanged comparison)
  pure (ProjectionComparison projectionComparisonFormat (projectionId a) (projectionId b) assessments changed unchanged
    (comparisonOldConclusion comparison) (comparisonNewConclusion comparison) (comparisonConclusionChanged comparison))
