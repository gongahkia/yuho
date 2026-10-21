{-# LANGUAGE OverloadedStrings #-}
-- Only public SDK types: independent kernel reference programs are in test/fixtures.
module PresumptionExamples (synthetic, multipleRoutes, matrix, chained, skippedGuard, mdaDocument, revise, execute) where

import Data.Text (Text)
import qualified Data.Text as T
import Data.Time.Calendar (fromGregorian)
import Yuho.Authoring

matrix :: [(Text,SuppliedStatus,SuppliedStatus,SuppliedStatus,Text,Text)]
matrix = [("P1-active",Proved,NotProved,NotProved,"active","satisfied"),
  ("P2-rebutted",Proved,Proved,NotProved,"rebutted","not_satisfied"),
  ("P3-direct-dominance",Proved,Proved,Proved,"rebutted","satisfied"),
  ("P4-inactive",NotProved,Unresolved NotDetermined,NotProved,"inactive","not_satisfied"),
  ("P5-unresolved",Unresolved NotDetermined,NotProved,NotProved,"unresolved","unresolved")]

synthetic :: SuppliedStatus -> SuppliedStatus -> SuppliedStatus -> PresumptionDocument
synthetic t r k = PresumptionDocument presumptionAuthoringFormat "document:registered" base [reg] ["Synthetic technical semantics only; no evidential or burden inference."]
  where
    scope=Scope "person:synthetic" "event:synthetic"
    ref=SourceRef "source:synthetic" Nothing
    leaf key label=LawNode key "input" label Nothing Nothing [ref]
    assessment input value=Assessment ("assessment:" <> input) input scope (Classification value)
      "Explicit synthetic fixture assumption; not inferred from narrative." "Fixture author" "synthetic_fixture" "assumption" [] [ref]
    reg=AuthoredRegistration "registration:knowledge" "Synthetic target support" "K" ["analysis:synthetic"] [ref]
      (RegisteredCondition "condition:T" "leaf_effective" (Just "T") [] [ref])
      (RegisteredCondition "condition:R" "leaf_effective" (Just "R") [] [ref])
    base=AuthoringDocument authoringFormat "document:proof" (LawDefinition "law:synthetic" "synthetic-v1"
      [LawNode "rule:selected" "rule" "Bounded downstream target" Nothing Nothing [],leaf "K" "Target knowledge condition",leaf "T" "Trigger condition",leaf "R" "Adequate rebuttal condition"]
      [LawEdge "edge:target" "rule:selected" "K" "requires"] ["No legal proposition is established by this synthetic fixture."])
      [SourceRecord "source:synthetic" "synthetic" (Just "Synthetic registered-presumption fixture") (Just "T and R are explicitly classified assumptions; é猫 remain original text.")]
      [] [assessment "K" k,assessment "T" t,assessment "R" r]
      [Analysis "analysis:synthetic" "rule:selected" scope (map ("assessment:" <>) ["K","T","R"]) (fromGregorian 2021 12 31)]
      [] [Annotation "note:burden" ["K"] "No computed burden transfer or standard-of-proof assessment." "retained"] []

multipleRoutes :: PresumptionDocument
multipleRoutes = d {presumptionRegistrations=presumptionRegistrations d ++
    [r {registeredId="registration:alternative",registeredLabel="Second independently identified route",registeredSources=[SourceRef "source:second" Nothing],
      registeredTrigger=(registeredTrigger r) {registeredConditionId="condition:second-T"},registeredRebuttal=(registeredRebuttal r) {registeredConditionId="condition:second-R"}} | r <- presumptionRegistrations d],
  presumptionProofDocument=base {documentSources=documentSources base ++ [SourceRecord "source:second" "synthetic" (Just "Independent second route") (Just "An independent registration source; no evidential weight is computed.")]}}
  where d=synthetic Proved NotProved NotProved; base=presumptionProofDocument d

revise :: Text -> SuppliedStatus -> PresumptionDocument -> PresumptionDocument
revise input status d = d {presumptionProofDocument=base {documentAssessments=map update (documentAssessments base)}}
  where base=presumptionProofDocument d
        update a | assessmentInput a == input = a {assessmentClassification=Classification status}
                 | otherwise = a

chained :: SuppliedStatus -> SuppliedStatus -> SuppliedStatus -> PresumptionDocument
chained t r k = d {presumptionProofDocument=base {documentSources=documentSources base ++ [SourceRecord "source:chain" "synthetic" (Just "Authored synthetic two-step registration statement") (Just "Technical registration A links effective T to P, subject to explicit R. Technical registration B links effective P to K, subject to explicit R. Direct proof remains independently supplied; this is not a statutory chain.")],documentLaw=law {lawNodes=lawNodes law ++ [LawNode "P" "input" "Intermediate effective proposition" Nothing Nothing []]},
  documentAssessments=documentAssessments base ++ [Assessment "assessment:P" "P" scope (Classification NotProved) "Direct P not proved; technical chain only." "Fixture author" "synthetic_fixture" "assumption" [] []],
  documentAnalyses=[a {analysisAssessments=analysisAssessments a ++ ["assessment:P"]} | a <- documentAnalyses base]},
  presumptionRegistrations=[upstream,downstream]}
  where
    d=synthetic t r k; base=presumptionProofDocument d; law=documentLaw base; scope=Scope "person:synthetic" "event:synthetic"
    upstream=AuthoredRegistration "registration:possession" "Synthetic first route: T to P" "P" ["analysis:synthetic"] [SourceRef "source:chain" Nothing]
      (RegisteredCondition "condition:up-T" "leaf_effective" (Just "T") [] []) (RegisteredCondition "condition:up-R" "leaf_effective" (Just "R") [] [])
    downstream=AuthoredRegistration "registration:knowledge" "Synthetic second route: P to K" "K" ["analysis:synthetic"] [SourceRef "source:chain" Nothing]
      (RegisteredCondition "condition:down-P" "leaf_effective" (Just "P") [] []) (RegisteredCondition "condition:down-R" "leaf_effective" (Just "R") [] [])

skippedGuard :: PresumptionDocument
skippedGuard = d {presumptionProofDocument=base {documentLaw=law {lawNodes=lawNodes law ++ [LawNode "main" "input" "Unresolved main requirement" Nothing Nothing [],LawNode "rule:guard" "rule" "Represented exception guard" Nothing Nothing []],
    lawEdges=[LawEdge "edge:main" "rule:selected" "main" "requires",LawEdge "edge:guard" "rule:guard" "K" "requires",LawEdge "edge:exception" "rule:selected" "rule:guard" "exception"]},
  documentAssessments=documentAssessments base ++ [Assessment "assessment:main" "main" scope (Classification (Unresolved NotDetermined)) "Main classification explicitly unresolved." "Fixture author" "synthetic_fixture" "assumption" [] []],
  documentAnalyses=[a {analysisAssessments=analysisAssessments a ++ ["assessment:main"]} | a <- documentAnalyses base]}}
  where d=synthetic Proved NotProved NotProved; base=presumptionProofDocument d; law=documentLaw base; scope=Scope "person:synthetic" "event:synthetic"

mdaDocument :: Either [AuthoringDiagnostic] PresumptionDocument
mdaDocument = do
  anchor <- sourceAnchorCodePoints source 0 (toInteger (length (T.unpack section2)))
  let d=synthetic Proved NotProved NotProved
      base=presumptionProofDocument d
      scope=Scope "person:Lin" "event:packet-Q-drug-D"
      reference=SourceRef "source:mda18" Nothing
      law=documentLaw base
      label n = n {nodeLabel=case nodeId n of
        "K" -> "Knowledge of the nature of identified controlled drug D"
        "T" -> "Possession of drug D proved or presumed for Lin at event Q"
        "R" -> "Externally assessed sufficient contrary proof, subject to s 18(3)"
        _ -> "Bounded knowledge requirement, not an offence conclusion",nodeSources=[reference],nodeCitation=Just "MDA 1973, 2020 RE, s 18(2)–(3)"}
      update a = a {assessmentScope=scope,assessmentReason=case assessmentInput a of
        "T" -> "Synthetic supplied possession classification for Lin / drug D / event Q. No upstream statutory route is implemented."
        "R" -> "Synthetic admission: legally sufficient contrary proof is not proved. This is not inferred from missing evidence or a denial of physical possession."
        _ -> "Direct knowledge is not proved; operative support is evaluated separately.",assessmentSources=[anchor,reference]}
  pure d {presumptionDocumentId="document:mda18",presumptionProofDocument=base {documentLaw=law {lawId="law:mda18",lawRevision="2020-RE-published-20211231-bounded",lawNodes=map label (lawNodes law),lawScope=limitations},
    documentSources=source:documentSources base,documentAssessments=map update (documentAssessments base),
    documentAnalyses=[a {analysisScope=scope} | a <- documentAnalyses base]},
    presumptionRegistrations=[r {registeredLabel="MDA s 18(2): presumed knowledge of drug nature",registeredSources=[anchor,reference],
      registeredTrigger=(registeredTrigger r) {registeredConditionSources=[anchor]},registeredRebuttal=(registeredRebuttal r) {registeredConditionSources=[reference]}} | r <- presumptionRegistrations d],presumptionContext=limitations}
  where
    -- Retained historical statutory extraction; no external fetching at runtime.
    section2="Any person who is proved or presumed to have had a controlled drug in his or her possession is presumed, until the contrary is proved, to have known the nature of that drug."
    section3="The presumptions provided for in this section are not to be rebutted by proof that the accused never had physical possession of the controlled drug."
    source=SourceRecord "source:mda18" "law" (Just "https://sso.agc.gov.sg/Act-Rev/MDA1973/Published/20211231?DocDate=20211231&ProvIds=P13-") (Just (section2 <> "\n" <> section3))
    limitations=["Fixed MDA 2020 Revised Edition, published 31 December 2021; one person Lin, controlled drug D, event Q. Historical research fixture, no current applicability claim.",
      "Section 18(3): no-physical-possession proof alone is not admitted as sufficient rebuttal. The R input explicitly means externally reviewed legally adequate contrary proof; SDK validation cannot determine that adequacy.",
      "No s 18(1) statutory chain admitted: backend effective leaves do not impose direct-only proof. Synthetic chaining is demonstrated separately.",
      "Excludes complete offences, s 17 trafficking, sentencing, s 18(4) multi-person deeming, full evidential sufficiency and automatic burden transfer."]

execute :: PresumptionDocument -> Either [AuthoringDiagnostic] PresumptionEvaluation
execute d = compilePresumptionAnalysis d "analysis:synthetic" >>= evaluatePresumptionAnalysis
