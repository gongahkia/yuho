{-# LANGUAGE OverloadedStrings #-}
-- | A focused view over retained exact observations, never an arithmetic engine.
module Yuho.Quantitative.Graph where
import qualified Data.Aeson as A
import qualified Data.Map.Strict as M
import Data.List (nub)
import Data.Text (Text)
import qualified Data.Text as T
import qualified Yuho.CoreYuho.TypedFinite as K
import Yuho.Dependency.Types (qualifiedIdentity)
import Yuho.Diagram.Types
import Yuho.Quantitative

valueLabel :: QValue -> Text
valueLabel v=case v of
  QKnown t n->typeLabel t<>" "<>T.pack (show n)
  QUnknown t reasons->typeLabel t<>" unresolved | "<>T.intercalate "; " reasons
typeLabel :: QType -> Text
typeLabel t=case t of QInteger->"integer";QMoney c->c<>" minor units";QCount d->"count["<>d<>"]";QDate->"date";QEnum n->"enum["<>n<>"]"
stepId :: [Text] -> QStep -> Text
stepId scope s=qualifiedIdentity (["quant-step"]++scope++[qOutput s,qualifiedIdentity (map (T.pack . show) (qPath s))])
inputId :: [Text] -> Text -> Text
inputId scope name=qualifiedIdentity (["quant-input"]++scope++[name])
useId :: [Text] -> Text -> Text
useId scope name=qualifiedIdentity (["quant-use"]++scope++[name])
definitionId :: QDefinition -> Text
definitionId d=qualifiedIdentity ("quant-definition":qDefinitionKey d)

quantitativeGraph :: [Text] -> QExecution -> ([(GraphNode,A.Value)],[GraphEdge])
quantitativeGraph scope execution=(definitionNodes++useNodes++inputs++steps,edges)
  where
    plan=qCheckedPlan execution
    boundary=Just (T.intercalate " / " scope)
    definitionNodes=[(GraphNode (definitionId d) "quantitative_definition"
      (qName d<>" | authored "<>typeLabel (qType d)) (Just (T.pack (qSource (qSite d)))) Nothing Nothing,A.toJSON (d {qUseSite=Nothing}))
      | d<-qDefinitions plan]
    useNodes=[(GraphNode (useId scope (qName d)) "quantitative_use"
      (qName d<>" | independent scoped calculation") Nothing Nothing boundary
      ,A.object ["definition" A..= qDefinitionKey d,"use_site" A..= qUseSite d,"scope_identity" A..= scope]) | d<-qDefinitions plan]
    inputs=[((GraphNode (inputId scope (qInputName i)) "supplied_quantity"
      (qInputName i<>" | supplied "<>T.pack (show (qInputType i))<>" | "<>suppliedLabel i)
      (Just (qInputReason i)) Nothing boundary) {graphNodeObservation=Just (CoreObservation "supplied" Nothing Nothing Nothing)},A.toJSON i)
      | i<-qInputs plan]
    suppliedLabel i=case M.lookup (qInputName i) (qValues execution) of
      Just v->valueLabel v
      Nothing->T.pack (show (qInputValue i))
    steps=[((GraphNode (stepId scope s) "exact_calculation"
      (qOutput s<>" | "<>qOperation s<>" | "<>valueLabel (qResult s)
       <>if null (qItems s) then "" else " | inclusion "<>T.intercalate ", " [i<>"="<>state | (i,state)<-qItems s])
      Nothing Nothing boundary) {graphNodeObservation=Just (CoreObservation "evaluated" Nothing Nothing Nothing)},A.toJSON s)
      | s<-qSteps execution]
    root name=case [s | s<-qSteps execution,qOutput s==name,null (qPath s)] of
      [s]->stepId scope s
      _->inputId scope name
    edges=nub $ [GraphEdge (definitionId d) (useId scope (qName d)) "instantiates" "same authored expression; scoped inputs" | d<-qDefinitions plan]
      ++[GraphEdge (useId scope (qName d)) (root (qName d)) "evaluated_as" "actual exact output" | d<-qDefinitions plan]
      ++[GraphEdge (root name) (stepId scope s) "quantity_operand" "actual arithmetic scalar reference"
         | s<-qSteps execution,QRef name<-[qNode s]]
      ++[GraphEdge (root name) (stepId scope s) "inclusion_operand" "scalar read by inclusion condition"
         | s<-qSteps execution,name<-filterScalars s]
      ++[GraphEdge (stepId scope child) (stepId scope parent) (operandKind parent index) (T.pack (show index))
         | child<-qSteps execution,index:reversed<- [reverse (qPath child)],parent<-qSteps execution
         ,qOutput parent==qOutput child,qPath parent==reverse reversed]
    filterScalars s=[i | (_,rs)<-qFilterReads s,r<-rs,K.ScalarInput i<-K.readInputs r]
    operandKind parent index=case qNode parent of
      QSum xs->case drop index xs of
        QItem name _ _:_->if lookup name (qItems parent)==Just "not_satisfied" then "excluded_evaluated_item" else "arithmetic_operand"
        _->"arithmetic_operand"
      _->"arithmetic_operand"

-- Native typed graphs label all frozen inputs as supplied. Replace only the
-- derived scalar cards in the new opt-in view and link real calculation roots.
nativeQuantitativeGraph :: [Text] -> QExecution -> SemanticGraph -> SemanticGraph
nativeQuantitativeGraph scope e graph=graph
  {semanticGraphNodes=map truthful (semanticGraphNodes graph)++map fst records
  ,semanticGraphEdges=map truthfulEdge (semanticGraphEdges graph)++edges++links}
  where
    (records,edges)=quantitativeGraph scope e
    derived=map qName (qDefinitions (qCheckedPlan e))
    scalarId=nodeId "scalar"
    truthful n | graphNodeKind n=="scalar",Just name<-lookup (graphNodeId n) [(scalarId i,i) | i<-derived]=
      n {graphNodeLabel=name<>" | derived "<>maybe "unknown" valueLabel (M.lookup name (qValues e))
        ,graphNodeObservation=Just (CoreObservation "evaluated" Nothing Nothing Nothing)}
    truthful n | graphNodeKind n=="scalar",Just (name,t)<-lookup (graphNodeId n)
      [(scalarId i,(i,ty)) | (i,ty@(QCount _))<-M.toList (qTypes (qCheckedPlan e))]=
      n {graphNodeLabel=name<>" | supplied "<>typeLabel t<>" | "<>maybe "unknown" valueLabel (M.lookup name (qValues e))}
    truthful n=n
    truthfulEdge edge | graphEdgeFrom edge `elem` map scalarId derived =
      edge {graphEdgeLabel="actual derived scalar operand"}
    truthfulEdge edge=edge
    links=[GraphEdge (stepId scope s) (scalarId (qOutput s)) "derived_value" "computed, not supplied"
      | s<-qSteps e,null (qPath s),qOutput s `elem` derived]
