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
import Data.List (nub,sort)
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
import Yuho.Authoring.Validate (issue)
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
      nativeNodes = maybe [] projectionNodes dp ++ maybe [] presumptionProjectionNodes pp
      nativeId = maybe (maybe "" presumptionProjectionId pp) projectionId dp
      key role = projectionIdentity "computed-input-object" (computedExecutionId report,role)
      n role kind label origins status state = ProjectionNode (key role) kind role label
        (ProjectionOrigin (if kind == "authored" then "authored" else "projection_generated") role origins)
        Nothing Nothing Nothing Nothing status state Nothing Nothing
      sourceObs = computedOriginalObservation report
      expression = typedFocusExpression inspection
      classification = UTF8.decodeUtf8 (encodeRecord (computedMappedClassification report))
      baseNodes = [n "typed_expression" "authored" (typedLabel (expressionMeta expression)) [computedSourceExpression b] Nothing "not_applicable",
        n "typed_observation" "computed" ("Typed technical computation: " <> typedObservedStatus sourceObs) [typedObservationId sourceObs] (Just (typedObservedStatus sourceObs)) "evaluated",
        n "explicit_binding" "authored" ("Author-authorised technical mapping: " <> computedRationale b) [computedBindingId b] Nothing "not_applicable",
        n "destination_input" "generated" ("Execution-only input: " <> computedDestinationInput b <> "; mapped " <> classification <> ". Not a human-supplied assessment.") [computedDestinationInput b,assessmentId (computedGeneratedAssessment report)] Nothing "not_applicable"]
      routeNodes = [n ("route:" <> registeredId (registrationAuthored r)) "derived"
        (registeredLabel (registrationAuthored r) <> "; route " <> registrationRouteState r <> "; trigger " <> resolvedConditionValue (registrationTriggerResult r) <> "; rebuttal " <> resolvedConditionValue (registrationRebuttalResult r))
        [registeredId (registrationAuthored r),registrationObservationId r] Nothing (registrationEvaluation r)
        | r <- maybe [] presumptionReportDerivations (computedDerivationReport report)]
      effectiveNodes = [n ("effective:" <> effectiveInput x) "derived" ("Target " <> effectiveInput x <> "; direct technical " <> effectiveDirectValue x <> "; effective technical " <> effectiveValue x)
        [effectiveInput x,effectiveObservationId x] (Just (effectiveValue x)) "evaluated"
        | x <- maybe [] presumptionReportLeaves (computedDerivationReport report), not (null (effectiveRoutes x))]
      requirements = [ (n ("requirement:" <> observationKernelId x) "computed" ("Downstream requirement " <> observationNode x)
          [observationNode x,observationKernelId x] (observationComputed x) (observationEvaluation x)) {projectedNodeSkipReason=observationSkipReason x}
        | x <- reportRequirements (computedDownstreamReport report), observationNode x == computedDestinationInput b]
      results = [(n ("result:" <> ruleAuthoredId r) "computed" ("Downstream rule " <> ruleAuthoredId r)
          [ruleAuthoredId r,ruleKernelId r] (ruleComputed r) (ruleEvaluation r)) {projectedNodeBranchReason=ruleBranchReason r,projectedNodeSkipReason=case [exceptionSkipReason x | x<-reportExceptions (computedDownstreamReport report),exceptionGuardRule x==ruleAuthoredId r,exceptionEvaluation x=="not_evaluated"] of reason:_->reason; []->Nothing}
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
      links = [ComputedNavigation (key "typed_expression") (typedProjectionId upstream) (typedNodeId x) | x <- typedProjectionNodes upstream,typedNodeKind x == "expression",typedNodeAuthoredId x == computedSourceExpression b]
        ++ [ComputedNavigation (key "typed_observation") (typedProjectionId upstream) (typedNodeId x) | x <- typedProjectionNodes upstream, Just o <- [typedNodeObservation x],typedObservationId o == typedObservationId sourceObs]
        ++ [ComputedNavigation (projectedNodeId x) nativeId (projectedNodeId y) | x <- drop 3 nodes,y <- nativeNodes,
          not (null (filter (`elem` originAuthoredObjects (projectedNodeOrigin y)) (originAuthoredObjects (projectedNodeOrigin x))))]
      value = ComputedProjectionData "yuho.computed-input-projection/v0.1-experimental" (key "projection") report upstream inspection dp pp nodes edges links
  case validateComputedProjection value of [] -> Right (ComputedProjection value); errors -> Left errors

validateComputedProjection :: ComputedProjectionData -> [AuthoringDiagnostic]
validateComputedProjection p = validateTypedProjection (computedSourceProjection p)
  ++ maybe [] validateProjection (computedProofProjection p)
  ++ maybe [] validatePresumptionProjection (computedPresumptionProjection p)
  ++ [issue "CBPROJECTION" "/computedProjection" [] "unsupported projection version, duplicate identity, missing endpoint or invalid component navigation"
  | computedProjectionVersion p /= "yuho.computed-input-projection/v0.1-experimental" || length ids /= length (nub ids)
    || any (\e -> projectedEdgeFrom e `notElem` ns || projectedEdgeTo e `notElem` ns) es
    || any invalidLink (computedNavigation p)]
  where
    ns=map projectedNodeId (computedProjectionNodes p);es=computedProjectionEdges p;ids=ns++map projectedEdgeId es
    source=computedSourceProjection p
    native=[(typedProjectionId source,map typedNodeId (typedProjectionNodes source))]
      ++ maybe [] (\x -> [(projectionId x,map projectedNodeId (projectionNodes x))]) (computedProofProjection p)
      ++ maybe [] (\x -> [(presumptionProjectionId x,map projectedNodeId (presumptionProjectionNodes x))]) (computedPresumptionProjection p)
    invalidLink l = integrationNode l `notElem` ns || not (any (\(pId,keys) -> componentProjection l == pId && componentNode l `elem` keys) native)

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
