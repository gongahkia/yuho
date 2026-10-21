{-# LANGUAGE OverloadedStrings #-}
module TemporalExamples (syntheticTemporal, section24Temporal, executeTemporal, updateExpression) where
import Data.Text (Text)
import qualified Data.Text as T
import Data.Time.Calendar (fromGregorian)
import Yuho.Authoring

executeTemporal :: TemporalDocument -> Text -> Either [AuthoringDiagnostic] TemporalEvaluation
executeTemporal d date=compileTemporalAnalysis d (Just date) >>= evaluateTemporalAnalysis
updateExpression :: Text -> (TemporalExpression -> TemporalExpression) -> TemporalDocument -> TemporalDocument
updateExpression key f d=d {temporalExpressions=[if temporalExpressionId e==key then f e else e | e<-temporalExpressions d]}

proof :: Text -> Text -> [LawNode] -> [LawEdge] -> [(Text,SuppliedStatus)] -> AuthoringDocument
proof version kind extra edges inputs=AuthoringDocument authoringFormat ("document:"<>version)
  (LawDefinition ("law:"<>version) version ([LawNode "rule" "rule" "Fictional selected rule" Nothing Nothing [ref],LawNode "group" kind (if kind=="all" then "All required" else "At least one required") Nothing Nothing [ref]]++extra)
    (LawEdge "requires" "rule" "group" "requires":edges) ["Fictional technical fixture only."])
  [SourceRecord "law-source" "synthetic" (Just "Explicit fictional rule expression") (Just ("Fictional "<>version<>" expression."))] []
  [Assessment ("assessment:"<>input) input scope (Classification value) "Explicit synthetic assumption; no evidence aggregation." "Fixture author" "synthetic_fixture" "assumption" [] [ref] | (input,value)<-inputs]
  [Analysis "analysis" "rule" scope ["assessment:"<>input | (input,_)<-inputs] (fromGregorian 2021 12 31)] [] [] []
  where scope=Scope "actor:fixture" "event:fixed"; ref=SourceRef "law-source" Nothing
syntheticTemporal :: TemporalDocument
syntheticTemporal=TemporalDocument temporalAuthoringFormat "temporal:fictional" "work:fictional" [old,new]
  [SourceRecord "source:dates" "synthetic" (Just "Fictional amendment schedule") (Just "Fictional version B begins on 2024-01-01; this is no real statute.")]
  ["Fictional A AND B becomes A OR B. No assertion of statutory applicability."] []
  where
    doc version kind=proof version kind [LawNode input "input" ("Synthetic requirement "<>input) Nothing Nothing [] | input<-["A","B"]]
      [LawEdge ("member:"<>input) "group" input "member" | input<-["A","B"]] [("A",Proved),("B",NotProved)]
    old=TemporalExpression "expr:old" "fictional-v1" "2020-01-01" (Just "2024-01-01") (doc "old" "all") "analysis" [] [SourceRef "source:dates" Nothing] Nothing
    new=TemporalExpression "expr:new" "fictional-v2" "2024-01-01" Nothing (doc "new" "any") "analysis" [] [SourceRef "source:dates" Nothing] (Just "expr:old")

-- Bounded expression research, not a whole offence or an applicability opinion.
-- 2019-01-01 is an intentionally limited coverage start, NOT commencement of
-- old s 24. The 2020 transition is supported by S 849/2019 paragraph 2.
section24Temporal :: Either [AuthoringDiagnostic] TemporalDocument
section24Temporal=do
  oldRef<-sourceAnchorCodePoints oldSource 0 (toInteger (T.length oldText))
  newRef<-sourceAnchorCodePoints newSource 0 (toInteger (T.length newText))
  dateRef<-sourceAnchorCodePoints dateSource 0 (toInteger (T.length dateText))
  let oldDoc=law "pc24-2008RE-bounded" "any" [leaf "gain-intent" "Intention to cause wrongful gain",leaf "loss-intent" "Intention to cause wrongful loss"]
        [LawEdge "gain-route" "group" "gain-intent" "member",LawEdge "loss-route" "group" "loss-intent" "member"] [("gain-intent",NotProved),("loss-intent",NotProved)] oldSource oldRef
      newDoc=law "pc24-2019-s7-bounded" "any" [leaf "intent" "Intention route",leaf "ordinary" "Ordinary standards and knowledge route",leaf "gain-intent" "Intention to cause wrongful gain",leaf "loss-intent" "Intention to cause wrongful loss",leaf "standards" "Dishonest by ordinary standards of reasonable and honest persons",leaf "knows" "Actor knows act is dishonest by those standards"]
        [LawEdge "intention-alternative" "group" "intent" "member",LawEdge "ordinary-alternative" "group" "ordinary" "member",LawEdge "gain-route" "intent" "gain-intent" "member",LawEdge "loss-route" "intent" "loss-intent" "member",LawEdge "standards-member" "ordinary" "standards" "member",LawEdge "knows-member" "ordinary" "knows" "member"]
        [("gain-intent",NotProved),("loss-intent",NotProved),("standards",Proved),("knows",Proved)] newSource newRef
  pure (TemporalDocument temporalAuthoringFormat "temporal:pc24" "work:pc24" [TemporalExpression "pc24:old" "2008-RE-published-20081130" "2019-01-01" (Just "2020-01-01") oldDoc "analysis" [oldRef] [SourceRef "source:coverage" Nothing] Nothing,
      TemporalExpression "pc24:new" "Act15-2019-s7-published-20190604" "2020-01-01" Nothing newDoc "analysis" [newRef] [dateRef] (Just "pc24:old")]
    [oldSource,newSource,dateSource,SourceRecord "source:coverage" "synthetic" (Just "Author-declared limited research coverage starts 2019-01-01; not old provision commencement") Nothing]
    ["Bounded s 24 expression only; intention directed at wrongful gain/loss does not require completed gain/loss.","Wrongfulness, entitlement and intention classifications are externally supplied, including s 23 context; no offence or guilt determined.","Act 15/2019 s 191 addresses other sections and event histories; no exhaustive savings, retroactivity, continuing-conduct, intervening-law or incident-specific review.","End-open is authored research coverage, not a warranty that this expression remains current."]
    ["Caller must review applicability to any incident independently; synthetic assessments do not establish legal sufficiency."])
  where
    oldText="Whoever does anything with the intention of causing wrongful gain to one person, or wrongful loss to another person, is said to do that thing dishonestly."
    newText="A person (A) is said to do an act dishonestly if — (a) A does that act with the intention of causing wrongful gain to A or another person, or wrongful loss to another person, regardless of whether such gain or loss is temporary or permanent; or (b) that act done by A is dishonest by the ordinary standards of reasonable and honest persons and A knows that that act is dishonest by such standards."
    dateText="The Criminal Law Reform Act 2019, except sections 3, 8, 11, 14, 25, 26, 30, 139, 169(1)(i) and (j) and 171(f), comes into operation on 1 January 2020."
    oldSource=SourceRecord "source:old24" "legislation" (Just "https://sso.agc.gov.sg/Act-Rev/PC1871/Published/20211231?DocDate=20081130&ProvIds=P4II_6- | Penal Code 2008 RE s 24; whitespace-normalised retained extract") (Just oldText)
    newSource=SourceRecord "source:new24" "legislation" (Just "https://sso.agc.gov.sg/Acts-Supp/15-2019/Published?DocDate=20190604&ProvIds=pr7- | Act 15/2019 s 7; whitespace-normalised retained extract") (Just newText)
    dateSource=SourceRecord "source:commencement" "legislation" (Just "https://sso.agc.gov.sg/SL-Supp/S849-2019/Published/20191227?DocDate=20191227 | S 849/2019 paragraph 2, published 27 December 2019; whitespace-normalised retained extract") (Just dateText)
    leaf key label=LawNode key (if key=="intent" then "any" else if key=="ordinary" then "all" else "input") label Nothing (Just "Penal Code s 24 (bounded)") []
    law version kind nodes edges inputs source ref=let d=proof version kind nodes edges inputs; l=documentLaw d in d {documentSources=[source],documentLaw=l {lawScope=["Bounded historical s 24 expression; no determination of applicable law."],lawNodes=[n {nodeSources=[ref],nodeLabel=if nodeId n=="rule" then "Bounded dishonesty expression — s 24" else nodeLabel n} | n<-lawNodes l]},documentAssessments=[a {assessmentSources=[ref],assessmentReason="Synthetic supplied interpretation of this primitive input; no completed gain/loss requirement inferred."} | a<-documentAssessments d]}
