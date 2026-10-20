{-# LANGUAGE OverloadedStrings #-}
-- Bounded research decomposition of PC 2020 RE ss 23–24, 378 and 403.
-- No incident, evidence weighing, legal currency or complete offence coverage.
module LinkedExample
  ( linkedDocument, flatDocument, revisedDefinition, setInput
  , scopeA, scopeB, definitionKey, gain, loss, ordinary, knowledge ) where

import Data.Text (Text)
import Data.Time.Calendar (fromGregorian)
import Yuho.Authoring

scopeA, scopeB :: Scope
scopeA = Scope "actor:A" "event:theft"
scopeB = Scope "actor:B" "event:misappropriation"

definitionKey, gain, loss, ordinary, knowledge :: Text
definitionKey = "definition:dishonesty"
gain = "f:intends-wrongful-gain"
loss = "f:intends-wrongful-loss"
ordinary = "f:act-dishonest-ordinary-standards"
knowledge = "f:knows-act-dishonest-ordinary-standards"

source24 :: SourceRecord
source24 = SourceRecord "source:pc2020-s24" "law"
  (Just "Penal Code 1871, 2020 RE, ss 23–24; https://assets.egazette.gov.sg/2021/Legislative%20Supplements/Revised%20Acts/21rs8334.pdf; printed pp 32–33")
  -- Exact short retained phrase, not the full source or a claimed PDF offset.
  (Just "intention of causing wrongful gain")

node :: Text -> Text -> Text -> Maybe Text -> [SourceRef] -> LawNode
node key kind label citation refs = LawNode key kind label Nothing citation refs

edge :: Text -> Text -> Text -> Text -> LawEdge
edge = LawEdge

linkedDocument :: Either [AuthoringDiagnostic] AuthoringDocument
linkedDocument = do
  anchor <- sourceAnchorCodePoints source24 0 34
  let shared = node definitionKey "definition" "Dishonesty — one reusable definition" (Just "PC 2020 RE s 24") [anchor,SourceRef "source:pc2020-s23" Nothing]
      body = [node "g:dishonestly" "any" "Dishonesty: either statutory route" (Just "PC 2020 RE s 24") [],
        node "g:section24-intention" "any" "Intention to cause wrongful gain or loss" (Just "s 24(a)") [],
        node "g:section24-ordinary" "all" "Ordinary standards and actor's knowledge" (Just "s 24(b)") [],
        node gain "input" "Intention to cause wrongful gain (not completed gain)" (Just "ss 23, 24(a)") [],
        node loss "input" "Intention to cause wrongful loss (not completed loss)" (Just "ss 23, 24(a)") [],
        node ordinary "input" "Act dishonest by ordinary standards" (Just "s 24(b)") [],
        node knowledge "input" "Actor knows act is dishonest by those standards" (Just "s 24(b)") []]
      bodyEdges = [edge "defines:dishonesty" definitionKey "g:dishonestly" "defines",
        edge "d:intention" "g:dishonestly" "g:section24-intention" "member",
        edge "d:ordinary" "g:dishonestly" "g:section24-ordinary" "member",
        edge "d:gain" "g:section24-intention" gain "member", edge "d:loss" "g:section24-intention" loss "member",
        edge "d:standards" "g:section24-ordinary" ordinary "member", edge "d:knowledge" "g:section24-ordinary" knowledge "member"]
      theftInputs = [("f:movable-property","Movable property"),("f:another-possession","Another person's possession"),
        ("f:without-consent","Without that person's consent"),("f:property-moved","Property moved"),("f:moved-for-taking","Movement for taking")]
      misInputs = [("f:mis-movable","Movable property"),("f:misappropriation","Misappropriation"),("f:conversion","Conversion to own use")]
      outer = [node "rule:theft" "rule" "Theft candidate — actor A" (Just "PC 2020 RE s 378") [SourceRef "source:pc2020-s378" Nothing],
        node "rule:misappropriation" "rule" "Misappropriation candidate — actor B" (Just "PC 2020 RE s 403") [SourceRef "source:pc2020-s403" Nothing],
        node "g:theft" "all" "Bounded theft requirements" (Just "s 378") [],
        node "g:misappropriation" "all" "Bounded misappropriation requirements" (Just "s 403") [],
        node "g:mis-conduct" "any" "Misappropriate or convert to own use" (Just "s 403") []]
        ++ [node k "input" label (Just "s 378") [] | (k,label) <- theftInputs]
        ++ [node k "input" label (Just "s 403") [] | (k,label) <- misInputs]
      outerEdges = [edge "root:theft" "rule:theft" "g:theft" "requires",
        edge "root:misappropriation" "rule:misappropriation" "g:misappropriation" "requires",
        edge "use:theft-dishonesty" "g:theft" definitionKey "use",
        edge "use:misappropriation-dishonesty" "g:misappropriation" definitionKey "use",
        edge "mis:movable" "g:misappropriation" "f:mis-movable" "member",
        edge "mis:conduct" "g:misappropriation" "g:mis-conduct" "member",
        edge "mis:misappropriation" "g:mis-conduct" "f:misappropriation" "member",
        edge "mis:conversion" "g:mis-conduct" "f:conversion" "member"]
        ++ [edge ("theft:" <> k) "g:theft" k "member" | (k,_) <- theftInputs]
      supplied scope key status = Assessment (scopeActor scope <> ":" <> key) key scope (Classification status)
        "Synthetic fixture assumption for this actor and event; no automated legal classification."
        "SDK example author" "synthetic_fixture" "assumption" [] [anchor]
      statusesA = [(gain,Proved),(loss,NotProved),(ordinary,Proved),(knowledge,NotProved)] ++ [(k,Proved) | (k,_) <- theftInputs]
      statusesB = [(gain,NotProved),(loss,NotProved),(ordinary,Proved),(knowledge,Unresolved NotDetermined)]
        ++ [("f:mis-movable",Proved),("f:misappropriation",Proved),("f:conversion",NotProved)]
      assessments = [supplied s k value | (s,values) <- [(scopeA,statusesA),(scopeB,statusesB)], (k,value) <- values]
      analysis key target scope = Analysis key target scope
        [assessmentId a | a <- assessments, assessmentScope a == scope] (fromGregorian 2021 12 31)
  pure (AuthoringDocument linkedAuthoringFormat "document:linked-dishonesty"
    (LawDefinition "law:pc2020-bounded-dishonesty-reuse" "research-v1" (shared:body ++ outer) (bodyEdges ++ outerEdges)
      ["Fixed PC 2020 RE expression, not a current-applicability determination.",
       "s 23 concepts are supplied mental-state targets; actual completed gain/loss is not a prerequisite.",
       "s 378 and s 403 are bounded research candidates; explanations, exceptions, punishment and all omitted doctrines are not implemented."])
    [source24, SourceRecord "source:pc2020-s23" "law" (Just "PC 2020 RE s 23, printed p 32; fixed eGazette 21rs8334") Nothing,
     SourceRecord "source:pc2020-s378" "law" (Just "PC 2020 RE s 378, fixed eGazette 21rs8334") Nothing,
     SourceRecord "source:pc2020-s403" "law" (Just "PC 2020 RE s 403, fixed eGazette 21rs8334") Nothing]
    [CaseAssertion "assertion:no-completed-gain" "Synthetic context: no completed gain is recorded; this does not negate gain-directed intention." scopeA []]
    assessments [analysis "analysis:A" "rule:theft" scopeA,analysis "analysis:B" "rule:misappropriation" scopeB] []
    [Annotation "annotation:bounded" [definitionKey] "Bounded ss 23–24 classifications and substantive candidates; no evidence assessment or complete legal coverage." "retained"] [])

-- Independently authored ordinary v0.1 tree. It is intentionally spelled out:
-- neither selectedOccurrences nor the new expander constructs this reference.
flatDocument :: SuppliedStatus -> SuppliedStatus -> SuppliedStatus -> SuppliedStatus -> AuthoringDocument
flatDocument a b c d = AuthoringDocument authoringFormat "flat:document"
  (LawDefinition "flat:law" "1"
    [node "flat:rule" "rule" "Independent reference" Nothing [],
     node "flat:root" "any" "Either route" Nothing [],
     node "flat:intention" "any" "Gain or loss intention" Nothing [],
     node "flat:ordinary" "all" "Standards and knowledge" Nothing [],
     node gain "input" "Gain intention" Nothing [],node loss "input" "Loss intention" Nothing [],
     node ordinary "input" "Ordinary standards" Nothing [],node knowledge "input" "Knowledge" Nothing []]
    [edge "flat:root-edge" "flat:rule" "flat:root" "requires",
     edge "flat:left" "flat:root" "flat:intention" "member",edge "flat:right" "flat:root" "flat:ordinary" "member",
     edge "flat:a" "flat:intention" gain "member",edge "flat:b" "flat:intention" loss "member",
     edge "flat:c" "flat:ordinary" ordinary "member",edge "flat:d" "flat:ordinary" knowledge "member"] []) [] []
  [Assessment ("flat:" <> k) k scopeA (Classification status) "Independent explicit fixture" "test author"
    "synthetic_fixture" "assumption" [] [] | (k,status) <- [(gain,a),(loss,b),(ordinary,c),(knowledge,d)]]
  [Analysis "flat:analysis" "flat:rule" scopeA (map ("flat:" <>) [gain,loss,ordinary,knowledge]) (fromGregorian 2021 12 31)] [] [] []

-- Hypothetical experiment, not a revised interpretation of s 24. One authored
-- group change changes every subsequent use; the original document is immutable.
revisedDefinition :: AuthoringDocument -> Either [AuthoringDiagnostic] AuthoringDocument
revisedDefinition doc = do
  edited <- editLawNode "g:dishonestly" (\n -> n {nodeKind="all",nodeLabel="SDK experiment: require both routes"}) doc
  pure edited {documentLaw=(documentLaw edited) {lawRevision="hypothetical-all-routes"}}

setInput :: Scope -> Text -> SuppliedStatus -> AuthoringDocument -> AuthoringDocument
setInput scope input status doc = doc {documentAssessments=
  [if assessmentScope a == scope && assessmentInput a == input
    then a {assessmentClassification=Classification status} else a | a <- documentAssessments doc]}
