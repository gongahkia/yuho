{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- Internal constructors. Public facade exports opaque validated projections.
module Yuho.Provenance.Types where
import qualified Data.Aeson as A
import Data.Text (Text)
import GHC.Generics (Generic)
import Yuho.Dependency.Types (qualifiedIdentity)

data Node = Node
  { identity :: Text, structuralIdentity :: [Text], category :: Text
  , label :: Text, evaluation :: Text, state :: Maybe Text
  , authority :: A.Value, record :: A.Value } deriving (Eq,Show,Generic)
instance A.ToJSON Node

data Edge = Edge
  { edgeIdentity :: Text, from :: Text, to :: Text, relationship :: Text
  , evidence :: A.Value } deriving (Eq,Show,Generic)
instance A.ToJSON Edge

data Projection = Projection
  { projectionIdentity :: Text, projectionMode :: Text, projectionAuthority :: Text
  , nodes :: [Node], edges :: [Edge], retained :: A.Value } deriving (Eq,Show)
instance A.ToJSON Projection where
  toJSON p=A.object ["format" A..= provenanceFormat,"identity" A..= projectionIdentity p
    ,"mode" A..= projectionMode p,"authority" A..= projectionAuthority p
    ,"domain" A..= domain,"nodes" A..= nodes p,"edges" A..= edges p,"retained" A..= retained p]

provenanceFormat, focusFormat, domain :: Text
provenanceFormat="yuho.typed-provenance/v0.1-experimental"
focusFormat="yuho.typed-provenance-focus/v0.1-experimental"
domain="Checked typed components: original sources, checked declarations, selected inputs, every actual finite read and backend observation, scoped uses, quantitative steps and filter reads, checked conversions and candidate availability. Existing proof/presumption/temporal specialised projections remain separate. Reads are eager evidence, not a proof of semantic decisiveness or legal sufficiency."

key :: [Text] -> Text
key xs="pv:"<>qualifiedIdentity xs

node :: [Text] -> Text -> Text -> Text -> Maybe Text -> A.Value -> A.Value -> Node
node xs=Node (key xs) xs
edge :: Text -> Text -> Text -> A.Value -> Edge
edge a b kind ev=Edge (key ["edge",a,b,kind]) a b kind ev

nodeCategories :: [Text]
nodeCategories=["source_reference","sdk_source_record","sdk_authored_object","authorisation_origin","authored_binding","authored_candidate","source_document","checked_component","checked_structure","authored_declaration","authored_use","checked_declaration"
  ,"component_execution","selected_classification","generated_condition_input","selected_scalar","expression_observation","rule_observation"
  ,"proposition_observation","evaluation_read","component","observation","unavailable_port","conversion","condition_slot","candidate"
  ,"shared_definition","definition_use","definition_occurrence","quantitative_definition","quantitative_use","supplied_quantity","exact_calculation"]

-- Closed relationship signatures. Existing focused vocabulary is retained only
-- for its established endpoint categories; the record still carries authority.
edgeSignature :: Text -> [(Text,Text)]
edgeSignature r=case r of
  "assesses_application"->[("sdk_authored_object","sdk_authored_object")]
  "supplies_declared_scalar"->[("sdk_authored_object","sdk_authored_object")]
  "declares_sdk_object"->pairs ["source_document"] ["sdk_source_record","sdk_authored_object"]
  "anchors_original"->[("sdk_source_record","source_reference")]
  "sdk_source_reference"->[("source_reference","sdk_authored_object")]
  "compiled_sdk_declaration"->[("sdk_authored_object","checked_declaration")]
  "selects_sdk_input"->pairs ["sdk_authored_object"] ["selected_classification","selected_scalar"]
  "authored_in"->pairs ["source_document"] ["authored_declaration","authored_use","shared_definition","definition_use","quantitative_definition","quantitative_use","authored_binding","authored_candidate"]
  "authorisation_rationale"->pairs ["authorisation_origin"] ["authored_binding","authored_candidate"]
  "executes_binding"->[("authored_binding","conversion")]
  "candidate_effect"->[("authored_candidate","candidate")]
  "lowered_as"->pairs ["authored_declaration","authored_use"] ["checked_declaration"]
  "checked_as"->pairs ["authored_declaration","authored_use"] ["checked_declaration"]
  "selected_declaration"->pairs ["authored_declaration"] ["authored_use"]
  "declares_checked"->pairs ["checked_component"] ["checked_declaration"]
  "has_checked_structure"->pairs ["checked_component"] ["checked_structure"]
  "executed_component"->pairs ["checked_component"] ["component_execution"]
  "retained_component"->pairs ["checked_component"] ["component"]
  "evaluated_as"->pairs ["checked_declaration","quantitative_use"] ["expression_observation","rule_observation","proposition_observation","exact_calculation"]
  "classifies_application"->pairs ["checked_declaration"] ["selected_classification","generated_condition_input"]
  "selects_scalar"->pairs ["checked_declaration"] ["selected_scalar","supplied_quantity","exact_calculation"]
  "selected_assessment"->pairs ["source_document"] ["selected_classification"]
  "selected_value"->pairs ["source_document"] ["selected_scalar","supplied_quantity"]
  "reads_classification"->pairs ["selected_classification","generated_condition_input"] ["evaluation_read"]
  "reads_scalar"->pairs ["selected_scalar","supplied_quantity","exact_calculation"] ["evaluation_read"]
  "expands_reference"->pairs ["checked_declaration"] ["evaluation_read"]
  "evaluated_operand"->[("evaluation_read","evaluation_read")]
  "evaluated_root"->pairs ["evaluation_read"] ["expression_observation","rule_observation"]
  "resolution_rule"->[("rule_observation","proposition_observation")]
  "blocks_by_priority"->[("rule_observation","rule_observation")]
  "selected_port"->pairs ["expression_observation","proposition_observation"] ["observation"]
  "filter_decision"->[("evaluation_read","exact_calculation")]
  "scoped_occurrence"->[("evaluation_read","definition_occurrence")]
  "generated_by_binding"->[("condition_slot","generated_condition_input")]
  "produces"->[("component","observation")]
  "blocked_port"->[("component","unavailable_port")]
  "converts"->pairs ["observation","unavailable_port"] ["conversion"]
  "supplies"->[("conversion","condition_slot")]
  "consumed_by"->[("condition_slot","component")]
  "required_by"->[("condition_slot","component")]
  "guards"->[("conversion","candidate")]
  "instantiates"->[("shared_definition","definition_use"),("quantitative_definition","quantitative_use")]
  "evaluates_as"->[("definition_use","definition_occurrence")]
  "produces_port"->[("definition_occurrence","observation")]
  "quantity_operand"->pairs ["supplied_quantity","exact_calculation"] ["exact_calculation"]
  "inclusion_operand"->pairs ["supplied_quantity","exact_calculation"] ["exact_calculation"]
  "arithmetic_operand"->[("exact_calculation","exact_calculation")]
  "excluded_evaluated_item"->[("exact_calculation","exact_calculation")]
  "comparison_operand"->pairs ["supplied_quantity","exact_calculation"] ["observation"]
  "inclusion_condition"->[("condition_slot","exact_calculation")]
  _->[]
 where pairs a b=[(x,y) | x<-a,y<-b]
