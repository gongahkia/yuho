{-# LANGUAGE OverloadedStrings #-}
-- A consumer-authored law definition: no research-fixture loading or lexer tokens.
module Cheating (cheatingDocument, assessmentFor, withStatus, pendingDocument) where

import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import Data.Time.Calendar (fromGregorian)
import Yuho.Authoring

assessmentFor :: Text -> Text
assessmentFor input = "assessment:" <> Text.drop 2 input

cheatingDocument :: AuthoringDocument
cheatingDocument = AuthoringDocument authoringFormat "document:cheating-demo" law
  [SourceRecord "source:law" "law" (Just "bounded saved Penal Code ss 415 and 84 expression") Nothing,
   SourceRecord "source:interview" "synthetic" (Just "example interview")
     (Just "The seller described a valuable item. The buyer says the description induced delivery."),
   SourceRecord "source:message" "synthetic" (Just "example message")
     (Just "The message repeated the description.")]
  [CaseAssertion "assertion:description" "The seller described the item as valuable." scope
     [SourceRef "source:interview" Nothing],
   CaseAssertion "assertion:message" "A message repeated that description." scope
     [SourceRef "source:message" Nothing],
   CaseAssertion "assertion:delivery" "The buyer describes delivering property after the exchange." scope
     [SourceRef "source:interview" Nothing]]
  (map assessment inputs ++ [pending])
  [Analysis "analysis:cheating" "o:cheating" scope (map (assessmentFor . fst) inputs)
    (fromGregorian 2026 10 19)]
  [Relationship "relationship:sequence" "chronology" "assertion:description"
     "assertion:delivery" "Authored order only; no causal inference.",
   Relationship "relationship:challenge" "challenge" "assertion:message"
     (assessmentFor "f:deception") "Retained challenge; does not assert the opposite classification."]
  [Annotation "annotation:unfinished" ["o:cheating"]
    "Draft: consider whether additional legal questions should be modelled." "draft"]
  [Presentation "o:cheating" (Map.fromList [("x","120.5"),("colour","blue")])]
  where
    scope = Scope "actor:seller" "context:transaction-1"
    law = LawDefinition "law:bounded-cheating" "1" (rules ++ leaves ++ groups)
      (ruleEdges ++ memberEdges) ["Bounded s 415 alternatives and represented s 84 guard only.",
        "No claim of complete legal coverage; ss 24/25 interpretation and aggravated forms omitted."]
    rules = [node "o:cheating" "rule" "Cheating" Nothing (Just "Penal Code s 415"),
      node "x:section84" "rule" "Unsoundness of mind exception" Nothing (Just "Penal Code s 84")]
    node key kind label quote citation = LawNode key kind (maybe label id (lookup key labels)) quote citation [SourceRef "source:law" Nothing]
    leaves = [node key "input" key (Just quote) Nothing | (key,quote) <- quotations]
    groups = [node key kind key Nothing Nothing | (key,kind,_) <- structures]
    -- Display labels restate the retained quotations and represented grouping.
    -- IDs, relationship kinds, quotations and classifications remain unchanged.
    labels =
      [("f:deception","Deceiving a person"),
       ("f:property-fraudulent-or-dishonest","Fraudulent or dishonest inducement"),
       ("f:property-delivery-or-retention","Delivery of property or consent to retention"),
       ("f:intentional-inducement","Intentional inducement"),
       ("f:induced-act-or-omission","Induced act or omission"),
       ("f:damage-or-harm","Actual or likely damage or harm"),
       ("f:unsoundness-time","Unsoundness of mind at the time of the act"),
       ("f:nature-causation","By reason of unsoundness of mind (nature route)"),
       ("f:nature-incapacity","Incapable of knowing the nature of the act"),
       ("f:wrong-causation","By reason of unsoundness of mind (wrongfulness route)"),
       ("f:ordinary-wrongfulness-incapacity","Wrong by ordinary standards of reasonable and honest persons"),
       ("f:contrary-law-incapacity","Wrong as contrary to law"),
       ("f:control-causation","By reason of unsoundness of mind (control route)"),
       ("f:control-incapacity","Completely deprived of power to control actions"),
       ("g:cheating-requirements","Requirements for cheating"),
       ("g:cheating-forms","Alternative forms of cheating"),
       ("g:cheating-property-form","Property delivery or retention form"),
       ("g:cheating-act-harm-form","Act or omission with damage or harm"),
       ("g:section84-requirements","Requirements of the represented s 84 exception"),
       ("g:section84-routes","Alternative incapacity routes"),
       ("g:nature","Incapacity to know the nature of the act"),
       ("g:wrongfulness","Incapacity to know that the act is wrong"),
       ("g:control","Complete loss of control over actions")]
    ruleEdges = [LawEdge "edge:cheating-root" "o:cheating" "g:cheating-requirements" "requires",
      LawEdge "edge:exception-root" "x:section84" "g:section84-requirements" "requires",
      LawEdge "edge:section84-attachment" "o:cheating" "x:section84" "exception"]
    memberEdges = [LawEdge ("edge:" <> parent <> "/" <> child) parent child "member"
      | (parent,_,children) <- structures, child <- children]
    structures =
      [("g:cheating-property-form","all",["f:property-fraudulent-or-dishonest","f:property-delivery-or-retention"]),
       ("g:cheating-act-harm-form","all",["f:intentional-inducement","f:induced-act-or-omission","f:damage-or-harm"]),
       ("g:cheating-forms","any",["g:cheating-property-form","g:cheating-act-harm-form"]),
       ("g:cheating-requirements","all",["f:deception","g:cheating-forms"]),
       ("g:nature","all",["f:nature-causation","f:nature-incapacity"]),
       ("g:wrongfulness","all",["f:wrong-causation","f:ordinary-wrongfulness-incapacity","f:contrary-law-incapacity"]),
       ("g:control","all",["f:control-causation","f:control-incapacity"]),
       ("g:section84-routes","any",["g:nature","g:wrongfulness","g:control"]),
       ("g:section84-requirements","all",["f:unsoundness-time","g:section84-routes"])]
    quotations =
      [("f:deception","by deceiving any person"),
       ("f:property-fraudulent-or-dishonest","fraudulently or dishonestly induces the person so deceived"),
       ("f:property-delivery-or-retention","to deliver any property to any person, or to consent that any person shall retain any property"),
       ("f:intentional-inducement","intentionally induces the person so deceived"),
       ("f:induced-act-or-omission","to do or omit to do anything which he would not do or omit if he were not so deceived"),
       ("f:damage-or-harm","which act or omission causes or is likely to cause damage or harm to that person in body, mind, reputation or property"),
       ("f:unsoundness-time","at the time of doing it, by reason of unsoundness of mind"),
       ("f:nature-causation","at the time of doing it, by reason of unsoundness of mind"),
       ("f:nature-incapacity","incapable of knowing the nature of the act"),
       ("f:wrong-causation","at the time of doing it, by reason of unsoundness of mind"),
       ("f:ordinary-wrongfulness-incapacity","is wrong by the ordinary standards of reasonable and honest persons"),
       ("f:contrary-law-incapacity","is wrong as contrary to law"),
       ("f:control-causation","at the time of doing it, by reason of unsoundness of mind"),
       ("f:control-incapacity","completely deprived of any power to control his actions")]
    inputs = [(key, if key `elem` ["f:deception","f:property-fraudulent-or-dishonest",
      "f:property-delivery-or-retention"] then Proved else NotProved) | (key,_) <- quotations]
    assessment (key,status) = Assessment (assessmentFor key) key scope (Classification status)
      (if key == "f:deception" then "Caller classifies the described exchange as deception, considering both recorded descriptions."
       else "Explicit caller assumption for this synthetic demonstration.")
      "independent-demo-caller" "external_assertion"
      (if key == "f:deception" then "case_material" else "assumption")
      (if key == "f:deception" then ["assertion:description","assertion:message"] else []) []
    pending = Assessment "assessment:property-fault-pending" "f:property-fraudulent-or-dishonest"
      scope (Classification (Unresolved NotDetermined)) "Caller has not resolved this legal classification."
      "independent-demo-caller" "external_assertion" "assumption" [] []

withStatus :: Text -> SuppliedStatus -> AuthoringDocument -> AuthoringDocument
withStatus input status doc = doc { documentAssessments =
  [if assessmentId a == assessmentFor input then a { assessmentClassification = Classification status }
   else a | a <- documentAssessments doc] }

pendingDocument :: AuthoringDocument
pendingDocument = cheatingDocument { documentAnalyses =
  [a { analysisAssessments = [if key == assessmentFor "f:property-fraudulent-or-dishonest"
      then "assessment:property-fault-pending" else key | key <- analysisAssessments a] }
   | a <- documentAnalyses cheatingDocument] }
