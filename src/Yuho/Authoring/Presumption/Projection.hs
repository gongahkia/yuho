{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Presumption.Projection
  ( PresumptionProjection, PresumptionProjectionData(..), presumptionProjectionData
  , projectPresumptionAuthored, projectPresumptionEvaluation, projectPresumptionEvaluationOn
  , validatePresumptionProjection, encodePresumptionProjection
  , PresumptionInspection(..), inspectPresumptionTarget, inspectRegistration, recoverPresumptionSource
  , presumptionReferenceView, validatePresumptionView
  , encodePresumptionViewJson, encodePresumptionViewXml, encodePresumptionViewSvg ) where

import Data.Aeson (ToJSON(..), genericToJSON)
import qualified Data.ByteString as BS
import Data.List (find, isPrefixOf, nub, sort)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import GHC.Generics (Generic)
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Compile
import Yuho.Authoring.Presumption.Types
import Yuho.Authoring.Presumption.Run
import Yuho.Authoring.Presumption.Validate
import Yuho.Authoring.Projection
import Yuho.Authoring.Projection.Inspect (OriginalSourceExcerpt(..), recoverSourceReference)
import Yuho.Authoring.Projection.Render (escape, number, wrap, xmlCharacter, computedLabel, evaluationLabel)
import Yuho.Authoring.Report
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (findAnalysis, issue)
import qualified Yuho.SuppliedProofStatus.Types as P
import qualified Yuho.Diagram.Types as Legacy
import qualified Yuho.Diagram.Encode as Legacy

data PresumptionProjectionData = PresumptionProjectionData
  { presumptionProjectionVersion :: Text, presumptionProjectionId :: Text
  , presumptionProjectionSnapshot :: PresumptionSnapshot, presumptionProjectionReport :: Maybe PresumptionReport
  , presumptionProjectionMappings :: [PresumptionMapping], presumptionProjectionCompiler :: Maybe CompilerProvenance
  , presumptionProjectionNodes :: [ProjectionNode], presumptionProjectionEdges :: [ProjectionEdge]
  , presumptionProjectionDiagnostics :: [AuthoringDiagnostic], presumptionProjectionOpenInputs :: [OpenInput]
  } deriving (Eq, Show, Generic)
newtype PresumptionProjection = PresumptionProjection PresumptionProjectionData
presumptionProjectionData :: PresumptionProjection -> PresumptionProjectionData
presumptionProjectionData (PresumptionProjection x) = x

data PresumptionInspection = PresumptionInspection
  { presumptionFocusSnapshot :: Text, presumptionFocusAnalysis :: Analysis
  , presumptionFocusInput :: LawNode, presumptionFocusSelected :: Maybe Assessment
  , presumptionFocusAlternatives :: [Assessment], presumptionFocusAssertions :: [CaseAssertion]
  , presumptionFocusEffective :: Maybe EffectiveLeafObservation
  , presumptionFocusRegistrations :: [AuthoredRegistration]
  , presumptionFocusDerivations :: [RegistrationObservation]
  , presumptionFocusOccurrences :: [ProjectionNode], presumptionFocusDownstream :: [RequirementObservation]
  , presumptionFocusAncestors :: [RequirementObservation], presumptionFocusRules :: [RuleObservation]
  , presumptionFocusExceptions :: [ExceptionObservation]
  , presumptionFocusSources :: [SourceRef]
  } deriving (Eq, Show, Generic)

projectPresumptionAuthored :: PresumptionDocument -> Text -> Either [AuthoringDiagnostic] PresumptionProjection
projectPresumptionAuthored d key = do
  let validation = validatePresumptionBindings d key
      errors = filter ((/= "PAMISSING") . diagnosticCode) (presumptionDiagnostics validation)
  if null errors then pure () else Left errors
  a <- maybe (Left [issue "PAANALYSIS" "/documentAnalyses" [key] "analysis not found"]) Right (findAnalysis (presumptionProofDocument d) key)
  build (presumptionSnapshotFor d a) Nothing Nothing validation

projectPresumptionEvaluation :: PresumptionEvaluation -> Either [AuthoringDiagnostic] PresumptionProjection
projectPresumptionEvaluation e = let snapshot = presumptionEvaluationSnapshot e in
  build snapshot (Just (presumptionEvaluationReport e)) (Just (presumptionEvaluationCompilation e))
    (validatePresumptionBindings (presumptionSnapshotDocument snapshot) (analysisId (presumptionSnapshotAnalysis snapshot)))
projectPresumptionEvaluationOn :: PresumptionDocument -> PresumptionEvaluation -> Either [AuthoringDiagnostic] PresumptionProjection
projectPresumptionEvaluationOn d e
  | d == presumptionSnapshotDocument (presumptionEvaluationSnapshot e) = projectPresumptionEvaluation e
  | otherwise = Left [issue "PASTALE" "/presumptionProjectionSnapshot" [presumptionDocumentId d] "document differs from retained presumption snapshot"]

build :: PresumptionSnapshot -> Maybe PresumptionReport -> Maybe PresumptionCompilation -> PresumptionValidation
      -> Either [AuthoringDiagnostic] PresumptionProjection
build snapshot report compilation validation = do
  let d = presumptionSnapshotDocument snapshot
      doc = presumptionProofDocument d
      a = presumptionSnapshotAnalysis snapshot
      key = analysisId a
      sid = presumptionSnapshotId snapshot
  proof <- projectAuthored (proofSliceDocument d key) key
  let base = projectionData proof
      obj = objectProjectionId
      plain identifier role label authored = ProjectionNode identifier "authored" role label
        (ProjectionOrigin "authored" role authored) Nothing Nothing Nothing Nothing Nothing "not_applicable" Nothing Nothing
      computedNode identifier role label authored = (plain identifier role label authored)
        {projectedNodeKind="observation",projectedNodeOrigin=ProjectionOrigin "projection_generated" role authored}
      edge :: Text -> Text -> Text -> [Text] -> Maybe SourceRef -> String -> ProjectionEdge
      edge role from to ids anchor index = ProjectionEdge (projectionIdentity "presumption-edge" (role,from,to,index))
        from to role (if role == "original_source" then "provenance" else "registered_derivation")
        (ProjectionOrigin "projection_generated" role ids) anchor
      refs owner sources = [edge "original_source" (obj owner) (obj (referenceSource ref)) [owner,referenceSource ref] (Just ref) (show i) | (i,ref) <- zip [0 :: Int ..] sources]
      regs = presumptionRegistrations d
      conditions = concat [conditionObjects (registeredTrigger r) ++ conditionObjects (registeredRebuttal r) | r <- regs]
      registeredNodes = [plain (obj (registeredId r)) "registration" (registeredLabel r) [registeredId r] | r <- regs]
        ++ [plain (obj (registeredConditionId c)) "condition" (registeredConditionKind c) [registeredConditionId c] | c <- conditions]
      registeredEdges = concat [[edge "presumption_target" (obj (registeredId r)) (obj (registeredTarget r)) [registeredId r,registeredTarget r] Nothing "target",
          edge "trigger" (obj (registeredId r)) (obj (registeredConditionId (registeredTrigger r))) [registeredId r,registeredConditionId (registeredTrigger r)] Nothing "trigger",
          edge "rebuttal" (obj (registeredId r)) (obj (registeredConditionId (registeredRebuttal r))) [registeredId r,registeredConditionId (registeredRebuttal r)] Nothing "rebuttal"]
          ++ refs (registeredId r) (registeredSources r)
          ++ [edge "registration_analysis" (obj (registeredId r)) (obj analysis) [registeredId r,analysis] Nothing (T.unpack analysis) | analysis <- registeredAnalyses r] | r <- regs]
        ++ concat [[edge "condition_member" (obj (registeredConditionId c)) (obj (registeredConditionId child)) [registeredConditionId c,registeredConditionId child] Nothing (show i)
            | (i,child) <- zip [0 :: Int ..] (registeredConditionMembers c)]
          ++ [edge "leaf_effective_reference" (obj (registeredConditionId c)) (obj leaf) [registeredConditionId c,leaf] Nothing "leaf" | Just leaf <- [registeredConditionLeaf c]]
          ++ refs (registeredConditionId c) (registeredConditionSources c) | c <- conditions]
      leafRows = maybe [] presumptionReportLeaves report
      routeRows = maybe [] presumptionReportDerivations report
      effectiveNodes = [(computedNode (effectiveObservationId x) "effective_observation" (effectiveInput x) [effectiveInput x])
          {projectedNodeKind="observation",projectedNodeComputed=Just (effectiveValue x),projectedNodeEvaluation="evaluated",
           projectedNodeObservation=Just (ObservationIdentity sid presumptionProfile "effective_leaf" (effectiveInput x) [] Nothing Nothing)} | x <- leafRows]
      routeNodes = [(computedNode (registrationObservationId r) "derivation_observation" (registeredLabel (registrationAuthored r)) [registeredId (registrationAuthored r)])
          {projectedNodeKind="observation",projectedNodeEvaluation="evaluated",projectedNodeBranchReason=Just (registrationRouteState r),
           projectedNodeObservation=Just (ObservationIdentity sid presumptionProfile "derivation" (registeredId (registrationAuthored r)) [] Nothing Nothing)} | r <- routeRows]
      conditionTraces = concat [flatten [registeredId (registrationAuthored r),role] tree
        | r <- routeRows, (role,tree) <- [("trigger",registrationTriggerResult r),("rebuttal",registrationRebuttalResult r)]]
      flatten path tree = (path,tree) : concat [flatten (path ++ [T.pack (show i)]) child | (i,child) <- zip [0 :: Int ..] (resolvedConditionChildren tree)]
      conditionNodes = [(computedNode (observationProjectionId identity) "condition_observation" (registeredConditionKind c) [registeredConditionId c])
          {projectedNodeObservation=Just identity,projectedNodeComputed=Just (resolvedConditionValue tree),projectedNodeEvaluation="evaluated"}
        | (path,tree) <- conditionTraces, let c=resolvedConditionObject tree,
          let identity=ObservationIdentity sid presumptionProfile "registered_condition" (registeredConditionId c) path Nothing Nothing]
      conditionEdges = [edge "observes_condition" (projectedNodeId n) (obj (registeredConditionId (resolvedConditionObject tree))) [registeredConditionId (resolvedConditionObject tree)] Nothing (show path)
        | (n,(path,tree)) <- zip conditionNodes conditionTraces]
      downstream = maybe [] (reportRequirements . presumptionReportProof) report
      occurrence input path = find (\n -> case projectedNodeOccurrence n of
        Just o -> occurrenceAuthoredNode o == input && occurrenceEdges o == path
        _ -> False) (projectionNodes base)
      downstreamNodes = [(computedNode (observationProjectionId identity) "proof_observation" (observationNode o) [observationNode o])
          {projectedNodeKind="observation",projectedNodeComputed=observationComputed o,projectedNodeEvaluation=observationEvaluation o,
            projectedNodeSkipReason=observationSkipReason o,projectedNodeObservation=Just identity}
        | o <- downstream, observationEvaluation o == "evaluated", let identity = ObservationIdentity sid presumptionProfile "requirement" (observationNode o) (observationOccurrence o) (Just (observationKernelId o)) (Just (observationKernelBranch o))]
      otherRows = maybe [] (\r ->
        [("rule",ruleAuthoredId x,ruleKernelId x,ruleComputed x,ruleEvaluation x,ruleBranchReason x) | x <- reportRules (presumptionReportProof r),ruleEvaluation x == "evaluated"]
        ++ [("exception",exceptionRelationship x,"",exceptionComputed x,exceptionEvaluation x,Nothing) | x <- reportExceptions (presumptionReportProof r),exceptionEvaluation x == "evaluated"]) report
      otherNodes = [(computedNode (observationProjectionId identity) (category <> "_observation") authored [authored])
          {projectedNodeKind="observation",projectedNodeComputed=computed,projectedNodeEvaluation=state,projectedNodeBranchReason=reason,projectedNodeObservation=Just identity}
        | (category,authored,kernelId,computed,state,reason) <- otherRows,
          let identity=ObservationIdentity sid presumptionProfile category authored [] (if T.null kernelId then Nothing else Just kernelId) Nothing]
      otherEdges = [edge "observes_downstream" (projectedNodeId n) (obj authored) [authored] Nothing (T.unpack category)
        | (n,(category,authored,_,_,_,_)) <- zip otherNodes otherRows]
      observeEdges = concat [[edge "effective_input" (effectiveObservationId x) (obj (effectiveInput x)) [effectiveInput x] Nothing "input",
          edge "direct_assessment" (obj (assessmentId (effectiveDirectAssessment x))) (effectiveObservationId x)
            [assessmentId (effectiveDirectAssessment x),effectiveInput x] Nothing "direct"]
          ++ [edge "effective_to_downstream" (effectiveObservationId x) (projectedNodeId n) [effectiveInput x] Nothing (show (observationOccurrence o))
            | o <- effectiveDownstream x, Just n <- [occurrence (observationNode o) (observationOccurrence o)]] | x <- leafRows]
        ++ concat [[edge "registration_derivation" (obj (registeredId (registrationAuthored r))) (registrationObservationId r) [registeredId (registrationAuthored r)] Nothing "route",
            edge "route_to_effective" (registrationObservationId r) (effectiveObservationId x) [registeredId (registrationAuthored r),effectiveInput x] Nothing "support"]
          | r <- routeRows, x <- leafRows, effectiveInput x == registeredTarget (registrationAuthored r)]
        ++ [edge "resolved_condition_input" (obj (registeredConditionId c)) (effectiveObservationId x) [registeredConditionId c,effectiveInput x] Nothing "value"
          | c <- conditions, Just leaf <- [registeredConditionLeaf c], x <- leafRows, effectiveInput x == leaf]
        ++ [edge "observes_downstream" (projectedNodeId n) (projectedNodeId occurrenceNode) [observationNode o] Nothing (show (observationOccurrence o))
          | (n,o) <- zip downstreamNodes (filter ((== "evaluated") . observationEvaluation) downstream), Just occurrenceNode <- [occurrence (observationNode o) (observationOccurrence o)]]
      overlay n = case projectedNodeOccurrence n of
        Just occ -> case find (\o -> observationNode o == occurrenceAuthoredNode occ && observationOccurrence o == occurrenceEdges occ) downstream of
          Just o -> n {projectedNodeComputed=observationComputed o,projectedNodeEvaluation=observationEvaluation o,projectedNodeSkipReason=observationSkipReason o,
            projectedNodeObservation=if observationEvaluation o == "evaluated" then Just (ObservationIdentity sid presumptionProfile "requirement" (observationNode o) (observationOccurrence o) (Just (observationKernelId o)) (Just (observationKernelBranch o))) else Nothing}
          Nothing -> n
        Nothing -> case [x | x <- documentAssessments doc, objectProjectionId (assessmentId x) == projectedNodeId n] of
          [x] -> n {projectedNodeSelected=Just (assessmentId x `elem` analysisAssessments a),
            projectedNodeBinding=Just (ProjectedBinding (if assessmentId x `elem` analysisAssessments a then "selected" else "alternative")
              (Just (assessmentId x)) (Just (assessmentClassification x)) (Just (assessmentReason x)))}
          _ -> n
      conditionalSelections = [edge "analysis_selection" (obj key) (obj ref) [key,ref] Nothing (show i)
        | (i,ref) <- zip [0 :: Int ..] (analysisAssessments a),
          not (any (\e -> projectedEdgeKind e == "analysis_selection" && projectedEdgeFrom e == obj key && projectedEdgeTo e == obj ref) (projectionEdges base))]
      compiler = fmap (\c -> let p = presumptionProofCompilation c in CompilerProvenance
        (compiledSources p ++ presumptionCompiledSources c) (compiledIdentities p ++ [IdentityMapping (presumptionMappingKernel m) (presumptionMappingKind m) [presumptionMappingAuthored m] | m <- presumptionCompiledMappings c,presumptionMappingKind m /= "condition"])
        (compiledSourceMappings p ++ [SourceMapping (presumptionMappingKernel m) (presumptionMappingSource m)
          (presumptionMappingSpan m) [presumptionMappingAuthored m] (presumptionMappingOriginals m) | m <- presumptionCompiledMappings c])) compilation
      result = PresumptionProjectionData presumptionProjectionFormat (projectionIdentity "presumption-projection" (sid,maybe False (const True) report)) snapshot report
        (maybe [] presumptionCompiledMappings compilation) compiler
        (map overlay (projectionNodes base) ++ registeredNodes ++ effectiveNodes ++ routeNodes ++ downstreamNodes ++ otherNodes ++ conditionNodes)
        (projectionEdges base ++ registeredEdges ++ observeEdges ++ otherEdges ++ conditionEdges ++ conditionalSelections) (presumptionDiagnostics validation) (presumptionOpenInputs validation)
  case validatePresumptionProjection result of [] -> Right (PresumptionProjection result); errors -> Left errors

validatePresumptionProjection :: PresumptionProjectionData -> [AuthoringDiagnostic]
validatePresumptionProjection p =
  [issue "PAPVERSION" "/presumptionProjectionVersion" [] "unsupported presumption projection version" | presumptionProjectionVersion p /= presumptionProjectionFormat]
  ++ [issue "PAPDUPLICATE" "/presumptionProjection" [] "duplicate projected identity" | length allIds /= length (nub allIds)]
  ++ [issue "PAPENDPOINT" "/presumptionProjectionEdges" [projectedEdgeId e,key] "missing projected endpoint" | e <- presumptionProjectionEdges p, key <- [projectedEdgeFrom e,projectedEdgeTo e], key `notElem` ids]
  ++ [issue "PAPSNAPSHOT" "/presumptionProjectionReport" [] "report differs from retained snapshot" | Just r <- [presumptionProjectionReport p], presumptionReportSnapshot r /= presumptionSnapshotId (presumptionProjectionSnapshot p)]
  where ids = map projectedNodeId (presumptionProjectionNodes p); allIds = ids ++ map projectedEdgeId (presumptionProjectionEdges p)

encodePresumptionProjection :: PresumptionProjection -> Either [AuthoringDiagnostic] BS.ByteString
encodePresumptionProjection p = case validatePresumptionProjection (presumptionProjectionData p) of
  [] -> Right (encodeRecord (presumptionProjectionData p)); errors -> Left errors

inspectPresumptionTarget :: PresumptionProjection -> Text -> Either [AuthoringDiagnostic] PresumptionInspection
inspectPresumptionTarget p key = do
  let value = presumptionProjectionData p; snapshot=presumptionProjectionSnapshot value
      d=presumptionSnapshotDocument snapshot; doc=presumptionProofDocument d; a=presumptionSnapshotAnalysis snapshot
      nodes=presumptionProjectionNodes value
      resolved = case find ((== key) . projectedNodeId) nodes >>= projectedNodeOccurrence of
        Just o -> occurrenceAuthoredNode o
        Nothing -> key
      failure = Left [issue "PAFOCUS" "/presumptionFocus" [key,analysisId a] "focus must identify a primitive input in this analysis's proof or registration slice, or its structural occurrence"]
  input <- maybe failure Right (find (\n -> nodeId n == resolved && nodeKind n == "input" && resolved `elem` requiredPresumptionInputs d a) (lawNodes (documentLaw doc)))
  let selected = find (\x -> assessmentInput x == resolved && assessmentId x `elem` analysisAssessments a) (documentAssessments doc)
      assertions = [x | x <- documentAssertions doc, assertionId x `elem` maybe [] assessmentAssertions selected]
      regs=filter ((== resolved) . registeredTarget) (registrationsFor d (analysisId a))
      report=presumptionProjectionReport value
      leaf=report >>= find ((== resolved) . effectiveInput) . presumptionReportLeaves
      sources=nodeSources input ++ maybe [] assessmentSources selected ++ concatMap assertionSources assertions
        ++ concat [registeredSources r ++ concatMap registeredConditionSources (conditionObjects (registeredTrigger r) ++ conditionObjects (registeredRebuttal r)) | r <- regs]
  pure (PresumptionInspection (presumptionSnapshotId snapshot) a input selected
    [x | x <- documentAssessments doc, assessmentInput x == resolved, assessmentScope x == analysisScope a, Just (assessmentId x) /= (assessmentId <$> selected)] assertions leaf regs
    [r | r <- maybe [] presumptionReportDerivations report, registeredTarget (registrationAuthored r) == resolved]
    [n | n <- nodes, Just o <- [projectedNodeOccurrence n], occurrenceAuthoredNode o == resolved]
    (maybe [] effectiveDownstream leaf)
    [parent | proofReport <- maybe [] ((:[]) . presumptionReportProof) report, parent <- reportRequirements proofReport,
      child <- maybe [] effectiveDownstream leaf, observationRule parent == observationRule child,
      observationOccurrence parent /= observationOccurrence child, observationOccurrence parent `isPrefixOf` observationOccurrence child]
    [r | proofReport <- maybe [] ((:[]) . presumptionReportProof) report, r <- reportRules proofReport,
      ruleAuthoredId r `elem` map observationRule (maybe [] effectiveDownstream leaf)]
    [e | proofReport <- maybe [] ((:[]) . presumptionReportProof) report, e <- reportExceptions proofReport,
      exceptionGuardRule e `elem` map observationRule (maybe [] effectiveDownstream leaf)] sources)

inspectRegistration :: PresumptionProjection -> Text -> Either [AuthoringDiagnostic] (AuthoredRegistration, Maybe RegistrationObservation)
inspectRegistration p key = let v=presumptionProjectionData p; d=presumptionSnapshotDocument (presumptionProjectionSnapshot v) in
  case find ((== key) . registeredId) (presumptionRegistrations d) of
    Nothing -> Left [issue "PAREGISTRATION" "/presumptionRegistrations" [key] "registration not found"]
    Just r -> Right (r,presumptionProjectionReport v >>= find ((== key) . registeredId . registrationAuthored) . presumptionReportDerivations)

recoverPresumptionSource :: PresumptionProjection -> SourceRef -> Either [AuthoringDiagnostic] OriginalSourceExcerpt
recoverPresumptionSource p = recoverSourceReference (documentSources (presumptionProofDocument (presumptionSnapshotDocument (presumptionProjectionSnapshot (presumptionProjectionData p)))))

-- | Target first, then direct assessment, route, conditions and their resolved
-- leaves. Source expansion is explicit and never runs compilation/evaluation.
presumptionReferenceView :: PresumptionProjection -> Text -> [Text] -> Either [AuthoringDiagnostic] ProjectionView
presumptionReferenceView p key expanded = do
  initial <- inspectPresumptionTarget p key
  let value=presumptionProjectionData p; report=presumptionProjectionReport value
      obj=objectProjectionId
      visit seen x | nodeId (presumptionFocusInput x) `elem` seen = []
                   | otherwise = x : concat [visit (nodeId (presumptionFocusInput x):seen) child
                       | r <- presumptionFocusRegistrations x, leaf <- nub (conditionLeaves (registeredTrigger r) ++ conditionLeaves (registeredRebuttal r)),
                         Right child <- [inspectPresumptionTarget p leaf]]
      details=visit [] initial
      sources=concatMap presumptionFocusSources details
  if length (nub expanded) == length expanded && all (`elem` map referenceSource sources) expanded then pure ()
    else Left [issue "PASOURCE" "/presumptionView" expanded "expand distinct original source IDs referenced by this target/derivation chain"]
  let forDetail x = [obj (nodeId (presumptionFocusInput x))]
        ++ maybe [] ((:[]) . obj . assessmentId) (presumptionFocusSelected x)
        ++ maybe [] ((:[]) . effectiveObservationId) (presumptionFocusEffective x)
        ++ concat [[obj (registeredId r)] ++ [registrationObservationId t | t <- maybe [] presumptionReportDerivations report, registeredId (registrationAuthored t) == registeredId r]
          ++ map (obj . registeredConditionId) (conditionObjects (registeredTrigger r) ++ conditionObjects (registeredRebuttal r)) | r <- presumptionFocusRegistrations x]
        ++ map (obj . assertionId) (presumptionFocusAssertions x)
        ++ map projectedNodeId (presumptionFocusOccurrences x)
      requested=nub (concatMap forDetail details ++ map obj expanded)
      edges=[e | e <- presumptionProjectionEdges value, projectedEdgeFrom e `elem` requested, projectedEdgeTo e `elem` requested]
      edgeIds=map projectedEdgeId edges
      view=ProjectionView projectionViewFormat (projectionIdentity "presumption-view" (presumptionProjectionId value,key,expanded)) (presumptionProjectionId value)
        "Registered presumption focus: supplied direct, globally resolved effective and downstream evaluation remain separate; all omitted context retained in complete projection."
        requested edgeIds [projectedNodeId n | n <- presumptionProjectionNodes value, projectedNodeId n `notElem` requested]
        [projectedEdgeId e | e <- presumptionProjectionEdges value, projectedEdgeId e `notElem` edgeIds]
        [ViewBinding x ("node-" <> x) | x <- requested] [EdgeBinding i x ("edge-" <> x) | (i,x) <- zip [0..] edgeIds]
  case validatePresumptionView p view of [] -> Right view; errors -> Left errors

validatePresumptionView :: PresumptionProjection -> ProjectionView -> [AuthoringDiagnostic]
validatePresumptionView p view =
  [issue "PAVIEW" "/presumptionView" [] "invalid view identity, partition, bindings or endpoints"
    | viewProjectionId view /= presumptionProjectionId v || not (partition nodes (viewIncludedNodes view) (viewOmittedNodes view))
      || not (partition edges (viewIncludedEdges view) (viewOmittedEdges view))
      || map viewBindingProjectedId (viewNodeBindings view) /= viewIncludedNodes view
      || map edgeBindingProjectedId (viewEdgeBindings view) /= viewIncludedEdges view
      || any (\x -> viewBindingRenderedId x /= "node-" <> viewBindingProjectedId x) (viewNodeBindings view)
      || any (\(i,x) -> edgeBindingIndex x /= i || edgeBindingRenderedId x /= "edge-" <> edgeBindingProjectedId x) (zip [0..] (viewEdgeBindings view))
      || any (\e -> projectedEdgeId e `elem` viewIncludedEdges view && (projectedEdgeFrom e `notElem` viewIncludedNodes view || projectedEdgeTo e `notElem` viewIncludedNodes view)) (presumptionProjectionEdges v)]
  ++ [issue "PAVIEWLIMIT" "/presumptionView" [] "reference view exceeds 64 objects or 128 relationships; no truncation"
    | length (viewIncludedNodes view) > 64 || length (viewIncludedEdges view) > 128]
  where v=presumptionProjectionData p; nodes=map projectedNodeId (presumptionProjectionNodes v); edges=map projectedEdgeId (presumptionProjectionEdges v)
        partition allIds yes no = length (yes++no) == length (nub (yes++no)) && sort allIds == sort (yes++no)

instance ToJSON PresumptionProjectionData where toJSON = genericToJSON jsonOptions
instance ToJSON PresumptionInspection where toJSON = genericToJSON jsonOptions

checkedView :: PresumptionProjection -> ProjectionView -> Either [AuthoringDiagnostic] ()
checkedView p view = case validatePresumptionProjection (presumptionProjectionData p) ++ validatePresumptionView p view of [] -> Right (); errors -> Left errors

viewObjects :: PresumptionProjection -> ProjectionView -> ([ProjectionNode],[ProjectionEdge])
viewObjects p view = ([n | key <- viewIncludedNodes view, n <- presumptionProjectionNodes v, projectedNodeId n == key],
  [e | key <- viewIncludedEdges view, e <- presumptionProjectionEdges v, projectedEdgeId e == key])
  where v=presumptionProjectionData p
legacy :: PresumptionProjection -> ProjectionView -> Legacy.SemanticGraph
legacy p view = let (nodes,edges)=viewObjects p view in Legacy.SemanticGraph (viewId view) Legacy.TraceView
  [Legacy.GraphNode (projectedNodeId n) (projectedNodeRole n) (projectedNodeLabel n) Nothing (projectedNodeComputed n) Nothing | n <- nodes]
  [Legacy.GraphEdge (projectedEdgeFrom e) (projectedEdgeTo e) (projectedEdgeKind e) (projectedEdgeKind e) | e <- edges] (viewScope view)

encodePresumptionViewJson :: PresumptionProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodePresumptionViewJson p v = checkedView p v >> pure (Legacy.encodeSemanticGraph (legacy p v))
encodePresumptionViewXml :: PresumptionProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodePresumptionViewXml p v = do
  checkedView p v
  either (\message -> Left [issue "PAXML" "/presumptionView" [] message]) Right (Legacy.encodeSemanticGraphXml (legacy p v))

encodePresumptionViewSvg :: PresumptionProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodePresumptionViewSvg p view = do
  checkedView p view
  let v=presumptionProjectionData p; snapshot=presumptionProjectionSnapshot v
      d=presumptionProofDocument (presumptionSnapshotDocument snapshot)
      (nodes,edges)=viewObjects p view
      input key = find ((== key) . nodeId) (lawNodes (documentLaw d))
      authored n = case originAuthoredObjects (projectedNodeOrigin n) of x:_ -> x; [] -> ""
      classificationLabel (Classification value) = case value of
        P.Proved -> "proved"
        P.NotProved -> "not_proved"
        P.Unresolved reason -> "unresolved (" <> (case reason of P.NotDetermined -> "not_determined"; P.ExternalDecisionPending -> "external_decision_pending") <> ")"
      body n | projectedNodeKind n == "occurrence" = ["Downstream requirement occurrence", "Computed: " <> computedLabel (projectedNodeComputed n),evaluationLabel (projectedNodeEvaluation n)] ++ maybe [] (:[]) (projectedNodeSkipReason n)
             | otherwise = case projectedNodeRole n of
        "input" -> ["Authored legal input; supplied direct and effective values are separate."] ++ summary (authored n)
        "assessment" -> case find ((== authored n) . assessmentId) (documentAssessments d) of
          Nothing -> []
          Just a -> [if projectedNodeSelected n == Just True then "SELECTED direct assessment" else "UNSELECTED alternative assessment",
            "Supplied direct classification: " <> classificationLabel (assessmentClassification a),
            "Reason: " <> assessmentReason a,"Issuer: " <> assessmentIssuer a <> " | Basis: " <> assessmentBasis a,
            "Scope actor: " <> scopeActor (assessmentScope a) <> " | Context: " <> scopeContext (assessmentScope a)]
        "registration" -> ["Authored operative registration; its evaluated route is separate."]
        "derivation_observation" -> ["Derivation evaluated globally | Route: " <> maybe "" id (projectedNodeBranchReason n)]
        "effective_observation" -> ["Effective technical satisfaction: " <> computedLabel (projectedNodeComputed n),"Globally resolved; downstream proof may be skipped."]
        "condition" -> case [c | r <- presumptionRegistrations (presumptionSnapshotDocument snapshot), c <- conditionObjects (registeredTrigger r) ++ conditionObjects (registeredRebuttal r), registeredConditionId c == authored n] of
          [c] -> ["Condition: " <> registeredConditionKind c] ++ maybe [] (\leaf -> ["Uses effective input: " <> maybe leaf nodeLabel (input leaf)]) (registeredConditionLeaf c)
            ++ ["Resolved condition: " <> resolvedConditionValue cResult | r <- maybe [] presumptionReportDerivations (presumptionProjectionReport v), cResult <- resolvedObjects (registrationTriggerResult r) ++ resolvedObjects (registrationRebuttalResult r), registeredConditionId (resolvedConditionObject cResult) == authored n]
          _ -> []
        "original_source" -> ["Original source; generated kernel spans are separate."]
          ++ nub ["Original anchored excerpt: " <> text | e <- edges, Just ref <- [projectedEdgeOriginalSource e], referenceSource ref == authored n,
                  Right recovered <- [recoverPresumptionSource p ref], Just text <- [excerptText recovered]]
        "assertion" -> ["Authored case material; no computed legal status."]
        _ -> ["Downstream: " <> computedLabel (projectedNodeComputed n),evaluationLabel (projectedNodeEvaluation n)] ++ maybe [] (:[]) (projectedNodeSkipReason n)
      summary key = case presumptionProjectionReport v >>= find ((== key) . effectiveInput) . presumptionReportLeaves of
        Nothing -> ["No computed result | Evaluation not requested"]
        Just x -> ["Supplied direct: " <> classificationLabel (assessmentClassification (effectiveDirectAssessment x)),
          "Direct technical: " <> effectiveDirectValue x <> " | Effective technical: " <> effectiveValue x]
          ++ ["Downstream: " <> computedLabel (observationComputed o) <> " | " <> evaluationLabel (observationEvaluation o) <> maybe "" (" | " <>) (observationSkipReason o) | o <- effectiveDownstream x]
      resolvedObjects x = x : concatMap resolvedObjects (resolvedConditionChildren x)
      rows=[(n,concatMap (concatMap (wrap 108) . T.lines) (projectedNodeLabel n:body n)) | n <- nodes]
      starts=scanl (\y (_,ls) -> y+68+21*length ls) 130 rows
      positions=Map.fromList [(projectedNodeId n,(y,50+21*length ls)) | ((n,ls),y) <- zip rows starts]
      left=100+7*length edges; width=left+1000
      legendY=150+sum [68+21*length ls | (_,ls) <- rows]
      legend=concatMap (wrap 140 . edgeLabel) edges
      height=legendY+20*length legend+45
      txt x y size weight text="<text x=\"" <> number x <> "\" y=\"" <> number y <> "\" font-size=\"" <> number size <> "\" font-weight=\"" <> weight <> "\">" <> escape text <> "</text>"
      card (n,ls)=let (y,h)=Map.findWithDefault (0,0) (projectedNodeId n) positions in
        "<g id=\"node-" <> projectedNodeId n <> "\"><title>" <> escape (authored n) <> "</title><rect x=\"" <> number left <> "\" y=\"" <> number y <> "\" width=\"970\" height=\"" <> number h <> "\" rx=\"5\" fill=\"white\" stroke=\"#b8c7d9\"/>"
          <> txt (left+15) (y+20) 12 "bold" (projectedNodeKind n <> " " <> projectedNodeRole n <> " · " <> authored n)
          <> T.concat [txt (left+15) (y+43+21*i) 15 "normal" line | (i,line) <- zip [0..] ls] <> "</g>"
      connection (i,e)=let (fy,fh)=Map.findWithDefault (0,0) (projectedEdgeFrom e) positions
                           (ty,th)=Map.findWithDefault (0,0) (projectedEdgeTo e) positions
                           lane=22+7*i
                       in "<path id=\"edge-" <> projectedEdgeId e <> "\" d=\"M " <> number left <> " " <> number (fy+fh `div` 2) <> " H " <> number lane <> " V " <> number (ty+th `div` 2) <> " H " <> number left <> "\" stroke=\"#718096\" fill=\"none\" marker-end=\"url(#arrow)\"/>"
      label key=maybe key projectedNodeLabel (find ((== key) . projectedNodeId) nodes)
      edgeLabel e=projectedEdgeKind e <> ": " <> label (projectedEdgeFrom e) <> " → " <> label (projectedEdgeTo e)
      svg="<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"" <> number width <> "\" height=\"" <> number height <> "\" viewBox=\"0 0 " <> number width <> " " <> number height <> "\"><defs><marker id=\"arrow\" markerWidth=\"6\" markerHeight=\"6\" refX=\"5\" refY=\"3\" orient=\"auto\"><path d=\"M0,0 L6,3 L0,6\" fill=\"#718096\"/></marker></defs><rect width=\"100%\" height=\"100%\" fill=\"#f5f8fc\"/><g font-family=\"Arial, sans-serif\" fill=\"#172638\">"
        <> txt 22 32 22 "bold" "Registered presumption — direct, effective and downstream"
        <> txt 22 63 14 "normal" ("Analysis: " <> analysisId (presumptionSnapshotAnalysis snapshot))
        <> txt 22 92 13 "normal" "Technical support; no independent evidence assessment or burden transfer. Original sources expand only on request."
        <> T.concat (map connection (zip [0..] edges)) <> T.concat (map card rows)
        <> T.concat [txt 22 (legendY+20*i) 12 "normal" line | (i,line) <- zip [0..] legend] <> "</g></svg>"
  if T.all xmlCharacter svg then Right (UTF8.encodeUtf8 svg) else Left [issue "PAXML" "/presumptionView" [] "XML 1.0 forbids a character in this view"]
