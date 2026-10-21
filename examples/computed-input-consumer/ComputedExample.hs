{-# LANGUAGE OverloadedStrings #-}
-- Public-only fixtures, deliberately synthetic. References below are supplied
-- independently; they never call the bridge to determine their classifications.
module ComputedExample
  ( typedSource, scalarSource, workflowFrom, destinationDocument, presumptionDestination, workflow, proofReference, presumptionReference, scope, policy ) where

import Data.Time.Calendar (fromGregorian)
import Yuho.Authoring

scope :: Scope
scope = Scope "actor:one" "event:synthetic"
policy :: ComputedStatusPolicy
policy = ComputedStatusPolicy computedStatusMapping "not_determined"
source :: SourceRecord
source = SourceRecord "packet" "synthetic" (Just "Synthetic fixture packet, not legislative text") (Just "Zoë records access for Actor One to Resource R for read. No legal sufficiency is inferred.")

typedSource :: TechnicalClassification -> Either [AuthoringDiagnostic] TypedDocument
typedSource status = do
  anchor <- sourceAnchorCodePoints source 0 56
  let meta key label = TypedMeta key label Nothing [anchor]
      tuple = GroundTuple "authorised" ["actor:one","resource:r","action:read"]
      application = TypedApplication (meta "application" "Specified actor/resource/action tuple") tuple
      assessment = TypedAssessment (meta "typed-assessment" "Externally supplied tuple classification") "application" tuple scope status
        "Explicit synthetic classification; not inferred from this narrative." "Fixture author" "synthetic_fixture" "assumption" ["assertion"]
  pure TypedDocument
    {typedDocumentFormat=typedAuthoringFormat,typedDocumentId="typed-document",typedLawId="typed-law",typedLawRevision="synthetic-1"
    ,typedEntityTypes=[TypedEntityType (meta t t) | t <- ["actor","resource","action"]]
    ,typedEntities=[TypedEntity (meta key label) typ | (key,label,typ) <- [("actor:one","Actor One","actor"),("actor:two","Actor Two","actor"),("resource:r","Resource R","resource"),("action:read","Read","action"),("action:write","Write","action")]]
    ,typedPredicates=[TypedPredicate (meta "authorised" "Bounded technical relationship") [TypedArgument "actor" "actor",TypedArgument "resource" "resource",TypedArgument "action" "action"]]
    ,typedApplications=[application],typedScalars=[]
    ,typedExpressions=[TypedExpression (meta "expr:relationship" "Computed actor/resource/action relationship") (GroundApplication "application")]
    ,typedLinks=[TypedLink "typed-body" "typed-rule" "expr:relationship" "typed_body"]
    ,typedRules=[TypedRule (meta "typed-rule" "Synthetic typed rule") "typed-proposition"]
    ,typedPropositions=[TypedProposition (meta "typed-proposition" "Technical conclusion")]
    ,typedAssessments=[assessment],typedValues=[]
    ,typedAnalyses=[TypedAnalysis "typed-analysis" "typed-rule" "typed-proposition" scope ["typed-assessment"] []]
    ,typedOriginalSources=[source],typedCaseAssertions=[CaseAssertion "assertion" "A synthetic record describes this tuple." scope [anchor]]
    ,typedAnnotations=[],typedPresentation=[],typedLimitations=["Legally neutral composition fixture; no legal permission or liability determination."]}

destinationDocument :: Bool -> SuppliedStatus -> SuppliedStatus -> AuthoringDocument
destinationDocument guard direct rebuttal = AuthoringDocument authoringFormat "proof-document"
  (LawDefinition "proof-law" "synthetic-1" nodes edges ["Synthetic technical inputs only. No standard of proof or legal sufficiency is determined."])
  [source] [] assessments [Analysis "proof-analysis" "rule" scope (map assessmentId assessments) (fromGregorian 2026 1 1)] [] [] []
  where
    node key kind label = LawNode key kind label Nothing Nothing [SourceRef "packet" Nothing]
    nodes = [node "rule" "rule" "Synthetic selected rule",node "ordinary" "input" "Ordinary requirement",node "trigger" "input" "Bounded technical input",node "target" "input" "Presumption target",node "rebuttal" "input" "Externally classified rebuttal"]
      ++ [node "guard" "rule" "Synthetic exception guard" | guard]
    edges = if guard then [LawEdge "ordinary-requires" "rule" "ordinary" "requires",LawEdge "exception" "rule" "guard" "exception",LawEdge "guard-requires" "guard" "target" "requires"]
      else [LawEdge "main-requires" "rule" "target" "requires"]
    supplied key input status = Assessment key input scope (Classification status) "Explicit synthetic fixture assumption" "Fixture author" "synthetic_fixture" "assumption" [] [SourceRef "packet" Nothing]
    assessments = [supplied "direct-target" "target" direct,supplied "rebuttal-assessment" "rebuttal" rebuttal]
      ++ [supplied "ordinary-assessment" "ordinary" (Unresolved NotDetermined) | guard]

presumptionDestination :: Bool -> SuppliedStatus -> SuppliedStatus -> PresumptionDocument
presumptionDestination guard direct rebuttal = PresumptionDocument presumptionAuthoringFormat "presumption-document" (destinationDocument guard direct rebuttal)
  [AuthoredRegistration "registration" "Synthetic registered support" "target" ["proof-analysis"] [SourceRef "packet" Nothing]
    (RegisteredCondition "trigger-condition" "leaf_effective" (Just "trigger") [] [SourceRef "packet" Nothing])
    (RegisteredCondition "rebuttal-condition" "leaf_effective" (Just "rebuttal") [] [SourceRef "packet" Nothing])]
  ["Rebuttal adequacy is supplied, never assessed by the bridge."]

-- A proof destination must select only inputs in its own executable slice.
proofBase :: AuthoringDocument
proofBase = let d=destinationDocument False NotProved NotProved in d
  {documentLaw=(documentLaw d) {lawEdges=[LawEdge "proof-requires" "rule" "trigger" "requires"]},documentAssessments=[],documentAnalyses=[a {analysisAssessments=[]} | a<-documentAnalyses d]}

workflow :: TechnicalClassification -> Bool -> Bool -> SuppliedStatus -> SuppliedStatus -> Either [AuthoringDiagnostic] ComputedInputDocument
workflow status usePresumption guard direct rebuttal = typedSource status >>= \sourceDoc -> workflowFrom sourceDoc usePresumption guard direct rebuttal

workflowFrom :: TypedDocument -> Bool -> Bool -> SuppliedStatus -> SuppliedStatus -> Either [AuthoringDiagnostic] ComputedInputDocument
workflowFrom sourceDoc usePresumption guard direct rebuttal = do
  upstream <- compileTypedAnalysis sourceDoc "typed-analysis" >>= evaluateTypedAnalysis
  let dest=if usePresumption then presumptionInputDestination (presumptionDestination guard direct rebuttal) "proof-analysis" else proofInputDestination proofBase "proof-analysis"
  b <- makeComputedInputBinding "binding:relationship" upstream "expr:relationship" dest "trigger" policy
    "The fixture author explicitly admits this technical computation for this bounded input; no legal proof claim is made." [SourceRef "packet" Nothing,SourceRef "packet" Nothing]
  pure (ComputedInputDocument computedInputFormat "workflow" sourceDoc dest b)

-- Independent destination oracles: classifications are explicitly authored,
-- not extracted by invoking executeComputedInput or its mapping implementation.
proofReference :: SuppliedStatus -> Either [AuthoringDiagnostic] Evaluation
proofReference value = compileAnalysis doc "proof-analysis" >>= evaluateAnalysis
  where
    assessment=Assessment "reference-trigger" "trigger" scope (Classification value) "Independent supplied reference" "Reference author" "synthetic_fixture" "assumption" [] []
    doc=proofBase {documentAssessments=[assessment],documentAnalyses=[a {analysisAssessments=["reference-trigger"]} | a<-documentAnalyses proofBase]}
presumptionReference :: Bool -> SuppliedStatus -> SuppliedStatus -> SuppliedStatus -> Either [AuthoringDiagnostic] PresumptionEvaluation
presumptionReference guard trigger direct rebuttal = compilePresumptionAnalysis doc "proof-analysis" >>= evaluatePresumptionAnalysis
  where
    initial=presumptionDestination guard direct rebuttal
    base=presumptionProofDocument initial
    assessment=Assessment "reference-trigger" "trigger" scope (Classification trigger) "Independent supplied reference" "Reference author" "synthetic_fixture" "assumption" [] []
    doc=initial {presumptionProofDocument=base {documentAssessments=documentAssessments base++[assessment],documentAnalyses=[a {analysisAssessments=analysisAssessments a++["reference-trigger"]} | a<-documentAnalyses base]}}

-- Exact integer computation is also a named expression; no supplied pass/fail.
scalarSource :: ExactScalar -> Either [AuthoringDiagnostic] TypedDocument
scalarSource value = do
  d <- typedSource TechnicalTrue
  let meta key label = TypedMeta key label Nothing [SourceRef "packet" Nothing]
  pure d {typedDocumentId="typed-integer-document",typedPredicates=[],typedApplications=[],typedAssessments=[]
    ,typedScalars=[TypedScalar (meta "measurement" "Supplied exact integer") "integer" (Just "Synthetic dimensionless integers"),TypedScalar (meta "threshold" "Fixed threshold 35") "integer" (Just "Synthetic dimensionless integers")]
    ,typedValues=[TypedValue (meta "supply-measurement" "Exact value") "measurement" scope value "Explicit exact synthetic integer" "Fixture author",TypedValue (meta "supply-threshold" "Declared threshold") "threshold" scope (ExactInteger 35) "Fixed synthetic integer" "Fixture author"]
    ,typedExpressions=[TypedExpression (meta "expr:relationship" "Computed exact integer > 35") (IntegerComparison "gt" "measurement" "threshold")]
    ,typedAnalyses=[a {selectedTypedAssessments=[],selectedTypedValues=["supply-measurement","supply-threshold"]} | a<-typedAnalyses d]}
