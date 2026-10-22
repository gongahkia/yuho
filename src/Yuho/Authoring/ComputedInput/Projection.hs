{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Small integration overlay; component projections retain their own contracts.
module Yuho.Authoring.ComputedInput.Projection
  ( ComputedProjection, ComputedProjectionData(..), ComputedNavigation(..)
  , projectComputedInput, projectComputedInputOn, computedProjectionData, encodeComputedProjection, validateComputedProjection
  , computedInputReferenceView, validateComputedInputView
  , encodeComputedInputViewJson, encodeComputedInputViewXml, encodeComputedInputViewSvg ) where

import Data.Aeson (ToJSON(..), genericToJSON)
import qualified Data.ByteString as BS
import Data.List (nub,sort,sortOn)
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import GHC.Generics (Generic)
import Yuho.Authoring.Codec
import Yuho.Authoring.ComputedInput
import Yuho.Authoring.Types
import Yuho.Authoring.Report
import Yuho.Authoring.Typed
import Yuho.Authoring.Presumption
import Yuho.Authoring.Projection
import Yuho.Authoring.Projection.Render (escape,wrap,number,xmlCharacter,computedLabel,evaluationLabel)
import Yuho.Authoring.Validate (issue,findAnalysis)
import Yuho.Authoring.Snapshot (makeSnapshot)
import Yuho.Protocol.Decode (sha256Text)
import qualified Yuho.Diagram.Types as L
import qualified Yuho.Diagram.Encode as L

-- Namespaced native references: no matching strings or kernel-ID parsing needed.
data ComputedNavigation = ComputedNavigation
  { integrationNode :: Text, componentProjection :: Text, componentNode :: Text
  } deriving (Eq, Show, Generic)
data ComputedProjectionData = ComputedProjectionData
  { computedProjectionVersion :: Text, computedProjectionId :: Text, computedProjectionReport :: ComputedInputReport
  , computedSourceProjection :: TypedProjectionData, computedSourceInspection :: TypedInspection
  , computedProofProjection :: Maybe ProjectionData, computedPresumptionProjection :: Maybe PresumptionProjectionData
  , computedProjectionNodes :: [ProjectionNode], computedProjectionEdges :: [ProjectionEdge]
  , computedNavigation :: [ComputedNavigation]
  } deriving (Eq, Show, Generic)
newtype ComputedProjection = ComputedProjection ComputedProjectionData
computedProjectionData :: ComputedProjection -> ComputedProjectionData
computedProjectionData (ComputedProjection x) = x
encodeComputedProjection :: ComputedProjection -> BS.ByteString
encodeComputedProjection = encodeRecord . computedProjectionData

projectComputedInputOn :: ComputedInputDocument -> ComputedInputEvaluation -> Either [AuthoringDiagnostic] ComputedProjection
projectComputedInputOn d e = inspectComputedInputOn d e >> projectComputedInput e

projectComputedInput :: ComputedInputEvaluation -> Either [AuthoringDiagnostic] ComputedProjection
projectComputedInput e = do
  source <- projectTypedEvaluation (computedEvaluationSource e)
  let report = computedInputReport e; d = computedReportDocument report; b = computedBinding d
      upstream = typedProjectionData source
  inspection <- inspectTypedExpression source (computedSourceExpression b)
  proof <- traverse projectEvaluation (computedEvaluationProof e)
  presumption <- traverse projectPresumptionEvaluation (computedEvaluationPresumption e)
  let dp = projectionData <$> proof
      pp = presumptionProjectionData <$> presumption
      key :: Text -> Text
      key role = projectionIdentity "computed-input-object" (computedExecutionId report,role)
      n role kind label origins status state = ProjectionNode (key role) kind role label
        (ProjectionOrigin (if kind == "authored" then "authored" else "projection_generated") role origins)
        Nothing Nothing Nothing Nothing status state Nothing Nothing
      sourceObs = computedOriginalObservation report
      expression = typedFocusExpression inspection
      classification = UTF8.decodeUtf8 (encodeRecord (computedMappedClassification report))
      baseNodes = [n "typed_expression" "authored" (typedLabel (expressionMeta expression)) [computedSourceExpression b] Nothing "not_applicable",
        n "typed_observation" "computed" ("Typed technical computation: " <> typedObservedStatus sourceObs) [computedSourceExpression b] (Just (typedObservedStatus sourceObs)) "evaluated",
        n "explicit_binding" "authored" ("Author-authorised technical mapping: " <> computedRationale b) [computedBindingId b] Nothing "not_applicable",
        n "destination_input" "generated" ("Execution-only input: " <> computedDestinationInput b <> "; mapped " <> classification <> ". Not a human-supplied assessment.") [computedDestinationInput b,computedBindingId b] Nothing "not_applicable"]
      routeNodes = [n ("route:" <> registeredId (registrationAuthored r)) "derived"
        (registeredLabel (registrationAuthored r) <> "; route " <> registrationRouteState r <> "; trigger " <> resolvedConditionValue (registrationTriggerResult r) <> "; rebuttal " <> resolvedConditionValue (registrationRebuttalResult r))
        [registeredId (registrationAuthored r)] Nothing (registrationEvaluation r)
        | r <- maybe [] presumptionReportDerivations (computedDerivationReport report)]
      effectiveNodes = [n ("effective:" <> effectiveInput x) "derived" ("Target " <> effectiveInput x <> "; direct technical " <> effectiveDirectValue x <> "; effective technical " <> effectiveValue x)
        [effectiveInput x] (Just (effectiveValue x)) "evaluated"
        | x <- maybe [] presumptionReportLeaves (computedDerivationReport report), not (null (effectiveRoutes x))]
      requirements = [ (n ("requirement:" <> observationKernelId x) "computed" ("Downstream requirement " <> observationNode x)
          [observationNode x] (observationComputed x) (observationEvaluation x)) {projectedNodeSkipReason=observationSkipReason x}
        | x <- reportRequirements (computedDownstreamReport report), observationNode x == computedDestinationInput b]
      results = [(n ("result:" <> ruleAuthoredId r) "computed" ("Downstream rule " <> ruleAuthoredId r)
          [ruleAuthoredId r] (ruleComputed r) (ruleEvaluation r)) {projectedNodeBranchReason=ruleBranchReason r,projectedNodeSkipReason=case [exceptionSkipReason x | x<-reportExceptions (computedDownstreamReport report),exceptionGuardRule x==ruleAuthoredId r,exceptionEvaluation x=="not_evaluated"] of reason:_->reason; []->Nothing}
        | r <- reportRules (computedDownstreamReport report)]
      nodes = baseNodes ++ routeNodes ++ effectiveNodes ++ requirements ++ results
      edge role from to = ProjectionEdge (projectionIdentity "computed-input-edge" (role,from,to)) from to role (if role=="selected_execution_context" then "same_execution_context_not_independent_support" else "explicit_technical_execution_dependency")
        (ProjectionOrigin "projection_generated" role [computedBindingId b]) Nothing
      edges = [edge "actual_named_expression_observation" (key "typed_expression") (key "typed_observation"),
        edge "authorised_status_mapping" (key "typed_observation") (key "explicit_binding"),
        edge "execution_overlay_input" (key "explicit_binding") (key "destination_input")]
        ++ [edge "downstream_requirement_observation" (key "destination_input") (projectedNodeId x) | x <- requirements]
        ++ [edge role (key "destination_input") (key ("route:" <> registeredId (registrationAuthored r)))
          | r <- maybe [] presumptionReportDerivations (computedDerivationReport report),
            (role,c) <- [("trigger_effective_input",registeredTrigger (registrationAuthored r)),("rebuttal_effective_input",registeredRebuttal (registrationAuthored r))],computedDestinationInput b `elem` conditionLeaves c]
        ++ [edge "registration_route_to_effective_target" (key ("route:" <> reg)) (projectedNodeId x)
          | x <- effectiveNodes, leaf <- maybe [] presumptionReportLeaves (computedDerivationReport report),
            projectedNodeId x == key ("effective:" <> effectiveInput leaf),reg <- effectiveRoutes leaf]
        ++ [edge "selected_execution_context" (projectedNodeId x) (projectedNodeId y) | x <- requirements ++ effectiveNodes, y <- results]
      value = ComputedProjectionData "yuho.computed-input-projection/v0.1-experimental" (key "projection") report upstream inspection dp pp nodes edges []
  links <- expectedNavigation value
  let linked = value {computedNavigation=links}
  case validateComputedProjection linked of [] -> Right (ComputedProjection linked); errors -> Left errors

validateComputedProjection :: ComputedProjectionData -> [AuthoringDiagnostic]
validateComputedProjection p = validateTypedProjection (computedSourceProjection p)
  ++ maybe [] validateProjection (computedProofProjection p)
  ++ maybe [] validatePresumptionProjection (computedPresumptionProjection p)
  ++ [issue "CBPROJECTION" "/computedProjection" [] "unsupported projection version, duplicate identity, missing endpoint or invalid component navigation"
  | computedProjectionVersion p /= "yuho.computed-input-projection/v0.1-experimental" || length ids /= length (nub ids) || any (not . validId) ids
    || any (\e -> projectedEdgeFrom e `notElem` ns || projectedEdgeTo e `notElem` ns) es
    || any invalidLink (computedNavigation p)]
  ++ case expectedNavigation p of
    Left errors -> errors
    Right expected -> [issue "CBNAVIGATION" "/computedNavigation" [computedBindingId (computedBinding (computedReportDocument (computedProjectionReport p)))]
      "navigation must exactly match the selected binding, component snapshots and role-specific authored/observation identities; endpoint existence or origin-string overlap is insufficient"
      | sortOn navigationKey (computedNavigation p) /= sortOn navigationKey expected]
  where
    validId x = let (prefix,digest)=T.splitAt (T.length x-64) x in T.isPrefixOf "p-" prefix && T.isSuffixOf "-" prefix && T.all (\c->(c>='a' && c<='z') || c=='-') prefix && T.length digest==64 && T.all (\c->(c>='0' && c<='9') || (c>='a' && c<='f')) digest
    ns=map projectedNodeId (computedProjectionNodes p);es=computedProjectionEdges p;ids=ns++map projectedEdgeId es
    source=computedSourceProjection p
    native=[(typedProjectionId source,map typedNodeId (typedProjectionNodes source))]
      ++ maybe [] (\x -> [(projectionId x,map projectedNodeId (projectionNodes x))]) (computedProofProjection p)
      ++ maybe [] (\x -> [(presumptionProjectionId x,map projectedNodeId (presumptionProjectionNodes x))]) (computedPresumptionProjection p)
    invalidLink l = integrationNode l `notElem` ns || not (any (\(pId,keys) -> componentProjection l == pId && componentNode l `elem` keys) native)

-- The correspondence table is shared by construction and validation. It reads
-- actual typed/proof/presumption identities, never origin intersections or labels.
navigationKey :: ComputedNavigation -> (Text,Text,Text)
navigationKey l = (integrationNode l,componentProjection l,componentNode l)

expectedNavigation :: ComputedProjectionData -> Either [AuthoringDiagnostic] [ComputedNavigation]
expectedNavigation p = do
  let report = computedProjectionReport p
      document = computedReportDocument report
      binding = computedBinding document
      upstream = computedSourceProjection p
      sourceSnapshot = computedTypedSnapshot report
      sourceAnalysis = typedSnapshotAnalysis sourceSnapshot
      original = computedOriginalObservation report
      sourceReport = computedUpstreamReport report
      key role = projectionIdentity "computed-input-object" (computedExecutionId report,role :: Text)
      problem role message = Left [issue "CBNAVIGATION" "/computedNavigation" [computedBindingId binding,role] message]
      ensure role condition message = if condition then Right () else problem role message
      unique role candidates = case candidates of
        [x] -> Right x
        _ -> problem role "required semantic correspondence is absent or ambiguous in the selected component"
      card role kind = do
        n <- unique role [n | n <- computedProjectionNodes p, projectedNodeId n == key role,
          projectedNodeRole n == role, projectedNodeKind n == kind]
        pure (projectedNodeId n)
      typedLink role kind candidates = do
        owner <- card role kind
        n <- unique role candidates
        pure (ComputedNavigation owner (typedProjectionId upstream) (typedNodeId n))
  ensure "execution_identity" (computedExecutionId report == sha256Text (encodeRecord
    (document,typedSnapshotId sourceSnapshot,original,computedGeneratedAssessment report,computedDownstreamSnapshot report)))
    "retained binding, source observation or downstream snapshot differs from the combined execution identity"
  ensure "source_snapshot" (typedProjectionSnapshot upstream == sourceSnapshot
    && typedSnapshotDocument sourceSnapshot == computedTypedSource document
    && typedSnapshotFor (typedSnapshotDocument sourceSnapshot) sourceAnalysis == sourceSnapshot
    && typedProjectionId upstream == projectionIdentity "typed-projection" (typedSnapshotId sourceSnapshot,True)
    && typedProjectionReport upstream == Just sourceReport
    && typedReportSnapshot sourceReport == typedSnapshotId sourceSnapshot
    && typedReportAnalysis sourceReport == computedSourceAnalysis binding
    && typedReportScope sourceReport == computedSourceScope binding
    && typedReportProfile sourceReport == typedEvaluatorProfile
    && computedSourceSnapshot binding == typedSnapshotId sourceSnapshot)
    "source projection/report does not belong to the binding's exact typed snapshot and analysis"
  expression <- unique "typed_expression" [x | x <- typedExpressions (typedSnapshotDocument sourceSnapshot),
    typedId (expressionMeta x) == computedSourceExpression binding]
  ensure "typed_observation" ([o | o <- typedReportExpressions sourceReport, typedObservedObject o == computedSourceExpression binding] == [original]
    && typedObservationCategory original == "expression" && typedObservedState original == "evaluated")
    "source must be the actual unique named expression observation in this typed execution"
  sourceObject <- typedLink "typed_expression" "authored" [n | n <- typedProjectionNodes upstream,
    typedNodeKind n == "expression", typedNodeAuthoredId n == computedSourceExpression binding, typedNodeRecord n == toJSON expression]
  sourceObservation <- typedLink "typed_observation" "computed" [n | n <- typedProjectionNodes upstream,
    typedNodeKind n == "observation", typedNodeId n == typedObservationId original, typedNodeObservation n == Just original, typedNodeRecord n == toJSON original]
  occurrence <- maybe (problem "typed_observation" "selected named expression has no structural occurrence") Right (typedObservationOccurrence original)
  ensure "typed_occurrence" (typedOccurrenceScope occurrence == typedAnalysisScope sourceAnalysis
    && typedOccurrenceExpression occurrence == computedSourceExpression binding && typedOccurrenceRule occurrence == typedAnalysisRule sourceAnalysis
    && typedOccurrenceLaw occurrence == typedLawDigest sourceSnapshot)
    "typed occurrence differs from selected expression, law, rule or scope"
  sourceOccurrence <- typedLink "typed_observation" "computed" [n | n <- typedProjectionNodes upstream,
    typedNodeKind n == "occurrence", typedNodeOccurrence n == Just occurrence, typedNodeObservation n == Just original]
  base <- computedDestinationDocument (computedExecutionOverlay report)
  selected <- maybe (problem "destination_analysis" "execution-overlay analysis absent") Right
    (findAnalysis base (computedDestinationAnalysis binding))
  ensure "destination_analysis" (analysisScope selected == computedDestinationScope binding
    && computedSourceScope binding == computedDestinationScope binding
    && reportSnapshot (computedDownstreamReport report) == computedDownstreamSnapshot report
    && reportAnalysis (computedDownstreamReport report) == analysisId selected
    && reportScope (computedDownstreamReport report) == analysisScope selected
    && reportTarget (computedDownstreamReport report) == analysisTarget selected)
    "destination report/analysis/scope does not match the binding and execution overlay"
  let generated = computedGeneratedAssessment report
  ensure "generated_assessment" ([x | x <- documentAssessments base, assessmentId x == assessmentId generated] == [generated]
    && assessmentId generated `elem` analysisAssessments selected
    && assessmentInput generated == computedDestinationInput binding && assessmentScope generated == analysisScope selected
    && assessmentClassification generated == computedMappedClassification report)
    "generated assessment is not the exact selected execution-overlay input"
  (component,native,compiler,lawDigest,isProof) <- case (computedProofProjection p,computedPresumptionProjection p,destinationProof (computedExecutionOverlay report),destinationPresumption (computedExecutionOverlay report)) of
    (Just nativeProof,Nothing,Just overlay,Nothing) -> do
      let snapshot = projectionSnapshot nativeProof
      ensure "proof_snapshot" (snapshot == makeSnapshot overlay selected
        && snapshotId snapshot == computedDownstreamSnapshot report
        && projectionId nativeProof == projectionIdentity "analysis" (snapshotId snapshot,"evaluated" :: Text)
        && projectionApplication nativeProof == Just (computedDownstreamReport report)
        && computedDerivationReport report == Nothing && reportProfile (computedDownstreamReport report) == evaluatorProfile)
        "proof component is not the selected downstream snapshot/report"
      pure (projectionId nativeProof,projectionNodes nativeProof,projectionCompiler nativeProof,snapshotLawDigest snapshot,True)
    (Nothing,Just nativePresumption,Nothing,Just overlay) -> do
      let snapshot = presumptionProjectionSnapshot nativePresumption
      ensure "presumption_snapshot" (snapshot == presumptionSnapshotFor overlay selected
        && presumptionSnapshotId snapshot == computedDownstreamSnapshot report
        && presumptionProjectionId nativePresumption == projectionIdentity "presumption-projection" (presumptionSnapshotId snapshot,True)
        && presumptionProjectionReport nativePresumption == computedDerivationReport report
        && fmap presumptionReportProof (computedDerivationReport report) == Just (computedDownstreamReport report)
        && reportProfile (computedDownstreamReport report) == presumptionProfile)
        "presumption component is not the selected downstream snapshot/report"
      pure (presumptionProjectionId nativePresumption,presumptionProjectionNodes nativePresumption,
        presumptionProjectionCompiler nativePresumption,snapshotLawDigest (makeSnapshot base selected),False)
    _ -> problem "destination_profile" "exactly one matching proof or presumption component is required"
  let nativeLink role kind candidates = do
        owner <- card role kind
        n <- unique role candidates
        pure (ComputedNavigation owner component (projectedNodeId n))
      authored role kind category identifier = nativeLink role kind [n | n <- native,
        projectedNodeKind n == "authored", projectedNodeRole n == category, projectedNodeId n == objectProjectionId identifier]
      observed role kind expected = nativeLink role kind [n | n <- native,
        projectedNodeKind n == "observation", projectedNodeObservation n == Just expected,
        projectedNodeId n == observationProjectionId expected]
      identity category identifier path kernel branch = ObservationIdentity (computedDownstreamSnapshot report)
        (reportProfile (computedDownstreamReport report)) category identifier path kernel branch
      mapped category kernel authoredId = any (\m -> identityKind m == category && identityKernelId m == kernel
        && authoredId `elem` identityAuthoredIds m) (maybe [] projectionCompilerIdentities compiler)
      conditionLinks role condition path = do
        object <- authored role "derived" "condition" (registeredConditionId (resolvedConditionObject condition))
        observation <- observed role "derived" (identity "registered_condition" (registeredConditionId (resolvedConditionObject condition)) path Nothing Nothing)
        children <- sequence [conditionLinks role child (path ++ [T.pack (show i)]) | (i,child) <- zip [0 :: Int ..] (resolvedConditionChildren condition)]
        pure (object:observation:concat children)
  target <- authored "destination_input" "generated" "input" (computedDestinationInput binding)
  ensure "generated_assessment" (any (\n -> projectedNodeId n == objectProjectionId (assessmentId generated)
    && projectedNodeSelected n == Just True
    && maybe False (\x -> bindingAssessment x == Just (assessmentId generated)
      && bindingSupplied x == Just (computedMappedClassification report)) (projectedNodeBinding n)) native)
    "native generated assessment selection/classification differs from the execution overlay"
  assignment <- authored "destination_input" "generated" "assessment" (assessmentId generated)
  mapping <- authored "explicit_binding" "authored" "assessment" (assessmentId generated)
  requirements <- sequence [do
      let role = "requirement:" <> observationKernelId row
          occurrenceId = OccurrenceIdentity lawDigest (analysisTarget selected) (analysisScope selected)
            (observationNode row) (observationRule row) (observationOccurrence row)
      ensure role (mapped "requirement" (observationKernelId row) (observationNode row)) "requirement lacks its authoritative compiler identity mapping"
      definition <- authored role "computed" "input" (observationNode row)
      location <- nativeLink role "computed" [n | n <- native,projectedNodeKind n == "occurrence",projectedNodeOccurrence n == Just occurrenceId]
      -- Presumption projections retain skipped occurrences without fabricating
      -- downstream run-observation nodes. Ordinary proof projections have both.
      observation <- if isProof || observationEvaluation row == "evaluated"
        then (:[]) <$> observed role "computed" (identity "requirement" (observationNode row) (observationOccurrence row) (Just (observationKernelId row)) (Just (observationKernelBranch row)))
        else pure []
      pure (definition:location:observation)
    | row <- reportRequirements (computedDownstreamReport report),observationNode row == computedDestinationInput binding]
  results <- sequence [do
      let role = "result:" <> ruleAuthoredId row
      ensure role (mapped "rule" (ruleKernelId row) (ruleAuthoredId row)) "rule lacks its authoritative compiler identity mapping"
      definition <- authored role "computed" "rule" (ruleAuthoredId row)
      location <- nativeLink role "computed" [n | n <- native,projectedNodeKind n == "occurrence",Just o <- [projectedNodeOccurrence n],
        occurrenceLawDigest o == lawDigest, occurrenceTarget o == analysisTarget selected, occurrenceScope o == analysisScope selected,
        occurrenceAuthoredNode o == ruleAuthoredId row, occurrenceAuthoredRule o == ruleAuthoredId row]
      observation <- if isProof || ruleEvaluation row == "evaluated"
        then (:[]) <$> observed role "computed" (identity "rule" (ruleAuthoredId row) [] (Just (ruleKernelId row)) (if isProof then Just (ruleKernelBranch row) else Nothing))
        else pure []
      pure (definition:location:observation)
    | row <- reportRules (computedDownstreamReport report)]
  routes <- sequence [do
      let registration = registrationAuthored row
          role = "route:" <> registeredId registration
      ensure role (registration `elem` (maybe [] presumptionRegistrations (destinationPresumption (computedExecutionOverlay report)))
        && analysisId selected `elem` registeredAnalyses registration) "registration is not selected in the downstream execution"
      definition <- authored role "derived" "registration" (registeredId registration)
      observation <- nativeLink role "derived" [n | n <- native,projectedNodeKind n == "observation",projectedNodeId n == registrationObservationId row,
        projectedNodeObservation n == Just (identity "derivation" (registeredId registration) [] Nothing Nothing)]
      trigger <- conditionLinks role (registrationTriggerResult row) [registeredId registration,"trigger"]
      rebuttal <- conditionLinks role (registrationRebuttalResult row) [registeredId registration,"rebuttal"]
      pure (definition:observation:trigger++rebuttal)
    | row <- maybe [] presumptionReportDerivations (computedDerivationReport report)]
  effective <- sequence [do
      let role = "effective:" <> effectiveInput row
      definition <- authored role "derived" "input" (effectiveInput row)
      direct <- authored role "derived" "assessment" (assessmentId (effectiveDirectAssessment row))
      observation <- nativeLink role "derived" [n | n <- native,projectedNodeKind n == "observation",projectedNodeId n == effectiveObservationId row,
        projectedNodeObservation n == Just (identity "effective_leaf" (effectiveInput row) [] Nothing Nothing)]
      pure [definition,direct,observation]
    | row <- maybe [] presumptionReportLeaves (computedDerivationReport report),not (null (effectiveRoutes row))]
  pure (nub ([sourceObject,sourceObservation,sourceOccurrence,mapping,target,assignment]
    ++ concat requirements ++ concat results ++ concat routes ++ concat effective))

computedInputReferenceView :: ComputedProjection -> Either [AuthoringDiagnostic] ProjectionView
computedInputReferenceView p = do
  let value=computedProjectionData p;ns=map projectedNodeId (computedProjectionNodes value);es=map projectedEdgeId (computedProjectionEdges value)
      view=ProjectionView projectionViewFormat (projectionIdentity "computed-input-view" (computedProjectionId value)) (computedProjectionId value)
        "Explicit technical computation → binding → execution overlay → downstream result. Complete component context remains in the companion projection."
        ns es [] [] [ViewBinding x ("node-"<>x) | x<-ns] [EdgeBinding i x ("edge-"<>x) | (i,x)<-zip [0..] es]
  if length ns>64 || length es>128 then Left [issue "CBVIEWLIMIT" "/view" [] "reference view exceeds 64 nodes/128 edges; no truncation performed"] else pure ()
  checked p view
  pure view
validateComputedInputView :: ComputedProjection -> ProjectionView -> [AuthoringDiagnostic]
validateComputedInputView p v = validateComputedProjection value ++ [issue "CBVIEW" "/viewVersion" [viewVersion v,projectionViewFormat] "unsupported viewVersion" | viewVersion v/=projectionViewFormat]
  ++ [issue "CBVIEW" "/view" [] "view partition, endpoints, bindings or projection mismatch" | not valid]
  where
    value=computedProjectionData p;ns=map projectedNodeId (computedProjectionNodes value);es=map projectedEdgeId (computedProjectionEdges value)
    partition a b allIds=sort (a++b)==sort allIds && length (nub (a++b))==length allIds
    valid=viewProjectionId v==computedProjectionId value && partition (viewIncludedNodes v) (viewOmittedNodes v) ns
      && partition (viewIncludedEdges v) (viewOmittedEdges v) es
      && viewNodeBindings v==[ViewBinding x ("node-"<>x) | x<-viewIncludedNodes v]
      && viewEdgeBindings v==[EdgeBinding i x ("edge-"<>x) | (i,x)<-zip [0..] (viewIncludedEdges v)]
      && all (\e -> projectedEdgeId e `notElem` viewIncludedEdges v || (projectedEdgeFrom e `elem` viewIncludedNodes v && projectedEdgeTo e `elem` viewIncludedNodes v)) (computedProjectionEdges value)
checked :: ComputedProjection -> ProjectionView -> Either [AuthoringDiagnostic] ()
checked p v=case validateComputedInputView p v of [] -> Right (); errors -> Left errors
objects :: ComputedProjection -> ProjectionView -> ([ProjectionNode],[ProjectionEdge])
objects p v=([n | key<-viewIncludedNodes v,n<-computedProjectionNodes x,projectedNodeId n==key],[e | key<-viewIncludedEdges v,e<-computedProjectionEdges x,projectedEdgeId e==key]) where x=computedProjectionData p
legacy :: ComputedProjection -> ProjectionView -> L.SemanticGraph
legacy p v=let (ns,es)=objects p v in L.SemanticGraph (viewId v) L.TraceView [L.GraphNode (projectedNodeId n) (projectedNodeRole n) (projectedNodeLabel n) Nothing (projectedNodeComputed n) Nothing | n<-ns] [L.GraphEdge (projectedEdgeFrom e) (projectedEdgeTo e) (projectedEdgeKind e) (projectedEdgeKind e) | e<-es] (viewScope v)
encodeComputedInputViewJson :: ComputedProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeComputedInputViewJson p v=checked p v >> pure (L.encodeSemanticGraph (legacy p v))
encodeComputedInputViewXml :: ComputedProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeComputedInputViewXml p v=checked p v >> either (\e -> Left [issue "CBXML" "/view" [] e]) Right (L.encodeSemanticGraphXml (legacy p v))
encodeComputedInputViewSvg :: ComputedProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeComputedInputViewSvg p v=do
  checked p v
  let (ns,es)=objects p v
      chunks t | T.length t<=108=[t] | otherwise=let (a,b)=T.splitAt 108 t in a:chunks b
      linesFor n=concatMap (concatMap (concatMap chunks . wrap 108) . T.lines)
        [projectedNodeLabel n,"Computed: "<>computedLabel (projectedNodeComputed n),evaluationLabel (projectedNodeEvaluation n),maybe "" id (projectedNodeSkipReason n),maybe "" id (projectedNodeBranchReason n)]
      rows=[(n,filter (not . T.null) (linesFor n)) | n<-ns]
      ys=scanl (\y (_,ls)->y+50+22*length ls) 108 rows
      positions=[(projectedNodeId n,(y,32+22*length ls)) | ((n,ls),y)<-zip rows ys]
      text x y size t="<text x=\""<>number x<>"\" y=\""<>number y<>"\" font-size=\""<>number size<>"\">"<>escape t<>"</text>"
      card ((n,ls),y)="<g id=\"node-"<>projectedNodeId n<>"\"><rect x=\"180\" y=\""<>number y<>"\" width=\"1080\" height=\""<>number (32+22*length ls)<>"\" rx=\"8\" fill=\"#f2f6fa\" stroke=\"#416481\"/>"<>T.concat [text 198 (y+25+22*i) 17 l | (i,l)<-zip [0..] ls]<>"</g>"
      connection (i,e)=case (lookup (projectedEdgeFrom e) positions,lookup (projectedEdgeTo e) positions) of
        (Just (a,ha),Just (b,hb))->let lane=28+7*(i `mod` 18) in "<path id=\"edge-"<>projectedEdgeId e<>"\" d=\"M180 "<>number (a+ha `div` 2)<>" H"<>number lane<>" V"<>number (b+hb `div` 2)<>" H180\" fill=\"none\" stroke=\"#8496a6\" marker-end=\"url(#arrow)\"/>"
        _ -> ""
      height=130+sum [50+22*length ls | (_,ls)<-rows]
      svg="<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1300\" height=\""<>number height<>"\" viewBox=\"0 0 1300 "<>number height<>"\" font-family=\"sans-serif\"><defs><marker id=\"arrow\" markerWidth=\"8\" markerHeight=\"8\" refX=\"7\" refY=\"4\" orient=\"auto\"><path d=\"M0 0 L8 4 L0 8\" fill=\"#8496a6\"/></marker></defs><rect width=\"100%\" height=\"100%\" fill=\"white\"/>"<>text 30 35 23 "Explicit computed technical input"<>text 30 67 16 "Author-authorised mapping; technical satisfaction does not establish legal proof."<>T.concat (map connection (zip [0..] es))<>T.concat (map card (zip rows ys))<>"</svg>"
  if T.all xmlCharacter svg then Right (UTF8.encodeUtf8 svg) else Left [issue "CBXML" "/view" [] "invalid XML character"]

instance ToJSON ComputedNavigation where toJSON=genericToJSON jsonOptions
instance ToJSON ComputedProjectionData where toJSON=genericToJSON jsonOptions
