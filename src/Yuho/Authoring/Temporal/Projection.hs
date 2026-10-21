{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Temporal.Projection
  ( TemporalProjection, TemporalProjectionData(..), temporalProjectionData
  , projectTemporalAuthored, projectTemporalEvaluation, projectTemporalEvaluationOn
  , validateTemporalProjection, encodeTemporalProjection
  , TemporalView(..), temporalReferenceView, validateTemporalView
  , temporalSelectedProjection, encodeTemporalViewJson, encodeTemporalViewXml, encodeTemporalViewSvg ) where
import Data.Aeson (ToJSON(..), genericToJSON)
import qualified Data.ByteString as BS
import Data.List (nub, sort)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import GHC.Generics (Generic)
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Projection
import Yuho.Authoring.Projection.Inspect (OriginalSourceExcerpt(..))
import Yuho.Authoring.Projection.Render (escape, wrap, number, xmlCharacter, computedLabel, evaluationLabel)
import Yuho.Authoring.Temporal.Types
import Yuho.Authoring.Temporal.Run
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue)
import Yuho.Authoring.Report (evaluationReport, reportConclusion)
import qualified Yuho.Diagram.Types as L
import qualified Yuho.Diagram.Encode as L

data TemporalProjectionData = TemporalProjectionData
  { temporalProjectionVersion :: Text, temporalProjectionId :: Text
  , temporalProjectionSelection :: TemporalSelection, temporalProjectionProof :: ProjectionData
  , temporalProjectionNodes :: [ProjectionNode], temporalProjectionEdges :: [ProjectionEdge]
  } deriving (Eq, Show, Generic)
data TemporalProjection = TemporalProjection TemporalProjectionData Projection
temporalProjectionData :: TemporalProjection -> TemporalProjectionData
temporalProjectionData (TemporalProjection x _) = x
-- | The selected proof's complete projection remains available with unchanged
-- identities, source mappings and its independent underlying snapshot.
temporalSelectedProjection :: TemporalProjection -> Projection
temporalSelectedProjection (TemporalProjection _ x) = x
instance ToJSON TemporalProjectionData where toJSON = genericToJSON jsonOptions

projectTemporalAuthored :: TemporalDocument -> Maybe Text -> Either [AuthoringDiagnostic] TemporalProjection
projectTemporalAuthored d date = do
  s <- selectTemporalExpression d date
  let e=selectionExpression s
  p <- projectAuthored (temporalExpressionDocument e) (temporalExpressionAnalysis e)
  build s p Nothing
projectTemporalEvaluation :: TemporalEvaluation -> Either [AuthoringDiagnostic] TemporalProjection
projectTemporalEvaluation e = do
  p <- projectEvaluation (temporalEvaluationProof e)
  build (temporalEvaluationSelection e) p (Just (reportConclusion (evaluationReport (temporalEvaluationProof e))))
projectTemporalEvaluationOn :: TemporalDocument -> Maybe Text -> TemporalEvaluation -> Either [AuthoringDiagnostic] TemporalProjection
projectTemporalEvaluationOn d date e
  | d == temporalSnapshotDocument snapshot && date == Just (temporalSnapshotConductDate snapshot) = projectTemporalEvaluation e
  | otherwise = Left [issue "TASTALE" "/temporalSnapshot" [temporalDocumentId d] "wrapper or conduct date differs from retained temporal snapshot"]
  where snapshot=temporalEvaluationSnapshot e

build :: TemporalSelection -> Projection -> Maybe Text -> Either [AuthoringDiagnostic] TemporalProjection
build s proof status = do
  let d=temporalSnapshotDocument (selectionSnapshot s); base=projectionData proof
      obj role key=projectionIdentity ("temporal-"<>role) (temporalDocumentId d,key)
      dateId=projectionIdentity "conduct-date" (temporalSnapshotId (selectionSnapshot s))
      selectedId=temporalExpressionId (selectionExpression s)
      plain key role label origins=ProjectionNode key "authored" role label (ProjectionOrigin "authored" role origins) Nothing Nothing Nothing Nothing Nothing "not_applicable" Nothing Nothing
      edge role from to origins anchor index=ProjectionEdge (projectionIdentity "temporal-edge" (role,from,to,index::Int)) from to role "temporal_selection_or_provenance" (ProjectionOrigin "projection_generated" role origins) anchor
      nodes=[(plain dateId "conduct_date" ("Supplied conduct date: "<>selectionConductDate s) [temporalDocumentId d]) {projectedNodeKind="selection",projectedNodeOrigin=ProjectionOrigin "projection_generated" "supplied_conduct_date" [temporalDocumentId d]}]
        ++ [(plain (obj "expression" (temporalExpressionId e)) "temporal_expression" (temporalExpressionId e<>" | "<>temporalExpressionVersion e<>" | ["<>temporalEffectiveFrom e<>", "<>maybe "open-end" id (temporalEffectiveTo e)<>")") [temporalExpressionId e]) {projectedNodeSelected=Just (temporalExpressionId e==selectedId)} | e <- temporalExpressions d]
        ++ [(plain (obj "result" selectedId) "selected_result" ("Selected rule: "<>analysisTarget (selectionAnalysis s)) [selectedId,analysisTarget (selectionAnalysis s)]) {projectedNodeKind="selection",projectedNodeOrigin=ProjectionOrigin "projection_generated" "selected_report_summary" [selectedId,analysisId (selectionAnalysis s)],projectedNodeComputed=status,projectedNodeEvaluation=if status==Nothing then "not_requested" else "evaluated"}]
        ++ [plain (obj "source" (sourceId source)) "temporal_original_source" (maybe (sourceId source) id (sourceLocator source)) [sourceId source] | source <- temporalSources d]
      edges=[edge (if temporalExpressionId e==selectedId then "selected_interval" else "authored_alternative_not_evaluated") dateId (obj "expression" (temporalExpressionId e)) [temporalExpressionId e] Nothing i | (i,e) <- zip [0..] (temporalExpressions d)]
        ++ [edge "selected_rule_result" (obj "expression" selectedId) (obj "result" selectedId) [selectedId] Nothing 0]
        ++ [edge "selected_underlying_occurrence" (obj "result" selectedId) (projectedNodeId n) [selectedId] Nothing i | (i,n) <- zip [0..] (projectionNodes base), Just o <- [projectedNodeOccurrence n],null (occurrenceEdges o)]
        ++ [edge role (obj "expression" (temporalExpressionId e)) (obj "source" (referenceSource ref)) [temporalExpressionId e,referenceSource ref] (Just ref) i | e <- temporalExpressions d,(role,refs) <- [("expression_original_source",temporalExpressionSources e),("effective_date_evidence",temporalDateSources e)],(i,ref) <- zip [0..] refs]
      value=TemporalProjectionData temporalProjectionFormat (projectionIdentity "temporal-projection" (s,projectionId base)) s base (nodes++projectionNodes base) (edges++projectionEdges base)
  case validateTemporalProjection value of
    [] -> Right (TemporalProjection value proof)
    errors -> Left errors
validateTemporalProjection :: TemporalProjectionData -> [AuthoringDiagnostic]
validateTemporalProjection value = validateProjection (temporalProjectionProof value) ++
  [issue "TAPROJECTION" "/temporalProjectionNodes" ids "duplicate projection identities or absent edge endpoints" | length ids/=length (nub ids) || length edgeIds/=length (nub edgeIds) || any (\e -> projectedEdgeFrom e `notElem` ids || projectedEdgeTo e `notElem` ids) edges]
  where ids=map projectedNodeId (temporalProjectionNodes value); edges=temporalProjectionEdges value; edgeIds=map projectedEdgeId edges
encodeTemporalProjection :: TemporalProjection -> Either [AuthoringDiagnostic] BS.ByteString
encodeTemporalProjection p=case validateTemporalProjection (temporalProjectionData p) of [] -> Right (encodeRecord (temporalProjectionData p)); errors -> Left errors

data TemporalView = TemporalSetView | TemporalProvenanceView deriving (Eq,Show)
-- | Bounded selection companion; use temporalSelectedProjection with existing
-- lawOccurrenceView/encoders for the selected rule's detailed dependencies.
temporalReferenceView :: TemporalProjection -> TemporalView -> Either [AuthoringDiagnostic] ProjectionView
temporalReferenceView p mode = do
  let value=temporalProjectionData p
      allNodes=temporalProjectionNodes value
      selectedExpressions=[projectedNodeId n | n<-allNodes,projectedNodeRole n=="temporal_expression",projectedNodeSelected n==Just True]
      relatedSources=[projectedEdgeTo e | e<-temporalProjectionEdges value,projectedEdgeFrom e `elem` selectedExpressions,projectedEdgeKind e `elem` ["expression_original_source","effective_date_evidence"]]
      keys role=[projectedNodeId n | n<-allNodes,projectedNodeRole n==role]
      ns=keys "conduct_date" ++ selectedExpressions ++ keys "selected_result"
        ++ case mode of
          TemporalSetView -> [projectedNodeId n | n<-allNodes,projectedNodeRole n=="temporal_expression",projectedNodeSelected n==Just False]
          TemporalProvenanceView -> [key | key<-keys "temporal_original_source",key `elem` relatedSources]
      es=[projectedEdgeId e | e <- temporalProjectionEdges value,projectedEdgeFrom e `elem` ns,projectedEdgeTo e `elem` ns]
      view=ProjectionView projectionViewFormat (projectionIdentity "temporal-view" (temporalProjectionId value,T.pack (show mode))) (temporalProjectionId value)
        "Technical conduct-date interval selection; sources are retained authorship, not an applicability ruling. Detailed selected law tree is a separately bound view."
        ns es [projectedNodeId n | n <- temporalProjectionNodes value,projectedNodeId n `notElem` ns] [projectedEdgeId e | e <- temporalProjectionEdges value,projectedEdgeId e `notElem` es]
        [ViewBinding key ("node-"<>key) | key <- ns] [EdgeBinding i key ("edge-"<>key) | (i,key) <- zip [0..] es]
  if length ns>64 || length es>128 then Left [issue "TAVIEWLIMIT" "/view" [] "reference view exceeds 64 objects or 128 relationships; no truncation performed"] else pure ()
  case validateTemporalView p view of [] -> Right view; errors -> Left errors
validateTemporalView :: TemporalProjection -> ProjectionView -> [AuthoringDiagnostic]
validateTemporalView p v = validateTemporalProjection value ++ [issue "TAVIEW" "/view" [] "view identity, partition, endpoints or bindings invalid" | not valid]
  where
    value=temporalProjectionData p; ns=map projectedNodeId (temporalProjectionNodes value); es=map projectedEdgeId (temporalProjectionEdges value)
    partition included omitted whole=sort (included++omitted)==sort whole && length (nub (included++omitted))==length whole
    valid=viewProjectionId v==temporalProjectionId value && partition (viewIncludedNodes v) (viewOmittedNodes v) ns && partition (viewIncludedEdges v) (viewOmittedEdges v) es
      && viewNodeBindings v==[ViewBinding key ("node-"<>key) | key <- viewIncludedNodes v]
      && viewEdgeBindings v==[EdgeBinding i key ("edge-"<>key) | (i,key) <- zip [0..] (viewIncludedEdges v)]
      && all (\e -> projectedEdgeId e `notElem` viewIncludedEdges v || (projectedEdgeFrom e `elem` viewIncludedNodes v && projectedEdgeTo e `elem` viewIncludedNodes v)) (temporalProjectionEdges value)

objects :: TemporalProjection -> ProjectionView -> ([ProjectionNode],[ProjectionEdge])
objects p v=([n | key <- viewIncludedNodes v,n <- temporalProjectionNodes value,projectedNodeId n==key],[e | key <- viewIncludedEdges v,e <- temporalProjectionEdges value,projectedEdgeId e==key]) where value=temporalProjectionData p
checked :: TemporalProjection -> ProjectionView -> Either [AuthoringDiagnostic] ()
checked p v=case validateTemporalView p v of [] -> Right (); errors -> Left errors
legacy :: TemporalProjection -> ProjectionView -> L.SemanticGraph
legacy p v=let (ns,es)=objects p v in L.SemanticGraph (viewId v) L.TraceView [L.GraphNode (projectedNodeId n) (projectedNodeRole n) (projectedNodeLabel n) Nothing (projectedNodeComputed n) Nothing | n<-ns] [L.GraphEdge (projectedEdgeFrom e) (projectedEdgeTo e) (projectedEdgeKind e) (projectedEdgeKind e) | e<-es] (viewScope v)
encodeTemporalViewJson :: TemporalProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeTemporalViewJson p v=checked p v >> pure (L.encodeSemanticGraph (legacy p v))
encodeTemporalViewXml :: TemporalProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeTemporalViewXml p v=do
  checked p v
  either (\e -> Left [issue "TAXML" "/view" [] e]) Right (L.encodeSemanticGraphXml (legacy p v))
encodeTemporalViewSvg :: TemporalProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeTemporalViewSvg p v=do
  checked p v
  let (ns,es)=objects p v
      document=temporalSnapshotDocument (selectionSnapshot (temporalProjectionSelection (temporalProjectionData p)))
      chunks limit textValue | T.length textValue<=limit = [textValue]
                             | otherwise = let (a,b)=T.splitAt limit textValue in a:chunks limit b
      safeWrap limit=concatMap (chunks limit) . wrap limit
      row n=concatMap (concatMap (safeWrap 96) . T.lines) ([projectedNodeLabel n] ++ case projectedNodeRole n of
        "temporal_expression" -> [if projectedNodeSelected n==Just True then "SELECTED by half-open interval membership" else "NOT SELECTED; no computation attributed"]
        "selected_result" -> ["Computed: "<>computedLabel (projectedNodeComputed n),evaluationLabel (projectedNodeEvaluation n)]
        "temporal_original_source" -> ["Original evidence/locator; generated kernel sources remain separate."]
          ++ nub ["Retained anchored excerpt: "<>value | e<-es,projectedEdgeTo e==projectedNodeId n,Just ref<-[projectedEdgeOriginalSource e],Right recovered<-[recoverTemporalSource document ref],Just value<-[excerptText recovered]]
        _ -> ["Supplied date; distinct from retained analysis reference date."])
      rows=[(n,row n) | n<-ns]
      ys=scanl (\y (_,ls)->y+64+22*length ls) 108 rows
      positions=Map.fromList [(projectedNodeId n,(y,48+22*length ls)) | ((n,ls),y)<-zip rows ys]
      left=80+9*length es; width=left+1000
      legend=concatMap (safeWrap 122 . (\e -> projectedEdgeKind e<>" ("<>label (projectedEdgeFrom e)<>" → "<>label (projectedEdgeTo e)<>")")) es
      label key=case [projectedNodeLabel n | n<-ns,projectedNodeId n==key] of x:_ -> x; [] -> key
      legendY=128+sum [64+22*length ls | (_,ls)<-rows]; height=legendY+20*length legend+48
      text x y size value="<text x=\""<>number x<>"\" y=\""<>number y<>"\" font-size=\""<>number size<>"\">"<>escape value<>"</text>"
      card ((n,ls),y)="<g id=\"node-"<>projectedNodeId n<>"\"><rect x=\""<>number left<>"\" y=\""<>number y<>"\" width=\"940\" height=\""<>number (48+22*length ls)<>"\" rx=\"8\" fill=\"#f2f6fa\" stroke=\"#416481\"/>"<>T.concat [text (left+18) (y+29+i*22) 17 l | (i,l)<-zip [0..] ls]<>"</g>"
      connection (i,e)=case (Map.lookup (projectedEdgeFrom e) positions,Map.lookup (projectedEdgeTo e) positions) of
        (Just (a,ha),Just (b,hb))->let lane=40+i*9 in "<path id=\"edge-"<>projectedEdgeId e<>"\" d=\"M "<>number left<>" "<>number (a+ha `div` 2)<>" H "<>number lane<>" V "<>number (b+hb `div` 2)<>" H "<>number left<>"\" fill=\"none\" stroke=\"#8496a6\" marker-end=\"url(#arrow)\"/>"
        _ -> ""
      svg="<svg xmlns=\"http://www.w3.org/2000/svg\" width=\""<>number width<>"\" height=\""<>number height<>"\" viewBox=\"0 0 "<>number width<>" "<>number height<>"\" font-family=\"sans-serif\"><defs><marker id=\"arrow\" markerWidth=\"8\" markerHeight=\"8\" refX=\"7\" refY=\"4\" orient=\"auto\"><path d=\"M0 0 L8 4 L0 8\" fill=\"#8496a6\"/></marker></defs><rect width=\"100%\" height=\"100%\" fill=\"white\"/>"<>text 32 35 23 "Authored temporal expression selection"<>text 32 67 15 "Technical interval matching; legal applicability remains externally reviewed."<>T.concat (map connection (zip [0..] es))<>T.concat (map card (zip rows ys))<>T.concat [text 32 (legendY+i*20) 13 line | (i,line)<-zip [0..] legend]<>"</svg>"
  if T.all xmlCharacter svg then Right (UTF8.encodeUtf8 svg) else Left [issue "TAXML" "/view" [] "invalid XML character"]
