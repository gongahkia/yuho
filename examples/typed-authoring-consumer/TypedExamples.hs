{-# LANGUAGE OverloadedStrings #-}
-- Public-only authored fixtures. Independent legacy conformance inputs live in
-- test/fixtures/typed-authoring; this module never parses or lowers them.
module TypedExamples (permissionDocument, thresholdDocument, normalisedThreshold, meta, caseReference, evaluate, ruleStatus) where

import Data.Text (Text)
import qualified Data.Text as T
import Yuho.Authoring

meta :: Text -> Text -> TypedMeta
meta key label = TypedMeta key label Nothing []

caseReference :: Either [AuthoringDiagnostic] SourceRef
caseReference = sourceAnchorCodePoints caseSource 0 33

caseSource :: SourceRecord
caseSource = SourceRecord "source:synthetic" "synthetic" (Just "Synthetic permission packet")
  (Just "Zoë permits Ada to read Server R. Ben's corresponding permission is not determined.")

permissionDocument :: Either [AuthoringDiagnostic] TypedDocument
permissionDocument = do
  anchor <- caseReference
  let law = SourceRef "source:cma" Nothing
      lawMeta key label = (meta key label) {typedCitation=Just "CMA 2007 RE, s 2(5); bounded positive relationship only",typedSources=[law]}
      tuple who kind = GroundTuple "permission" [who,"resource:r",kind]
      app key who kind = TypedApplication (lawMeta key ("Recorded permission for " <> who <> " / " <> kind)) (tuple who kind)
      assessment key appKey who kind status reason = TypedAssessment ((meta key "Supplied permission assessment") {typedSources=[anchor]}) appKey
        (tuple who kind) (Scope who ("access:" <> who)) status reason "Synthetic fixture author" "synthetic_fixture" "case_material" ["case:permission","case:arrangement"]
      analysis key rule who selected = TypedAnalysis key rule "p:permission" (Scope who ("access:" <> who)) [selected] []
  pure TypedDocument
    { typedDocumentFormat=typedAuthoringFormat,typedDocumentId="document:permission",typedLawId="law:permission",typedLawRevision="CMA-2007RE-bounded-1"
    , typedEntityTypes=map (TypedEntityType . uncurry meta) [("actor","Person"),("resource","Computer resource"),("access-kind","Kind of access")]
    , typedEntities=[TypedEntity (meta "actor:ada" "Ada") "actor",TypedEntity (meta "actor:ben" "Ben") "actor",
        TypedEntity (meta "actor:zoe" "Zoë") "actor",TypedEntity (meta "resource:r" "Server R") "resource",
        TypedEntity (meta "kind:read" "Read access") "access-kind",TypedEntity (meta "kind:write" "Write access") "access-kind"]
    , typedPredicates=[TypedPredicate (lawMeta "permission" "Relevant permission relationship") [TypedArgument "recipient" "actor",TypedArgument "computer" "resource",TypedArgument "access kind" "access-kind"]]
    , typedApplications=[app "application:ada-read" "actor:ada" "kind:read",app "application:ben-read" "actor:ben" "kind:read"]
    , typedScalars=[]
    , typedExpressions=[TypedExpression (lawMeta "q:ada" "Ada's particular read-access permission") (GroundApplication "application:ada-read"),
        TypedExpression (lawMeta "q:ben" "Ben's particular read-access permission") (GroundApplication "application:ben-read")]
    , typedLinks=[TypedLink "body:ada" "rule:ada" "q:ada" "typed_body",TypedLink "body:ben" "rule:ben" "q:ben" "typed_body"]
    , typedRules=[TypedRule (lawMeta "rule:ada" "Ada: positive permission research question") "p:permission",TypedRule (lawMeta "rule:ben" "Ben: positive permission research question") "p:permission"]
    , typedPropositions=[TypedProposition (meta "p:permission" "Represented positive permission condition")]
    , typedAssessments=[assessment "assessment:ada" "application:ada-read" "actor:ada" "kind:read" TechnicalTrue "Explicit fixture classification of this tuple; not an automatic interpretation of the packet.",
        assessment "assessment:ada-alternative" "application:ada-read" "actor:ada" "kind:read" TechnicalFalse "Retained alternative assumption; not selected.",
        assessment "assessment:ben" "application:ben-read" "actor:ben" "kind:read" (TechnicalUnresolved "not_determined") "No determination is supplied for Ben's tuple."]
    , typedValues=[],typedAnalyses=[analysis "analysis:ada" "rule:ada" "actor:ada" "assessment:ada",analysis "analysis:ben" "rule:ben" "actor:ben" "assessment:ben"]
    , typedOriginalSources=[caseSource,SourceRecord "source:cma" "law" (Just "https://sso.agc.gov.sg/Act-Rev/50A/Published?DocDate=20070731&ProvIds=pr2-") Nothing]
    , typedCaseAssertions=[CaseAssertion "case:permission" "The synthetic packet records Ada's read permission." (Scope "actor:ada" "access:actor:ada") [anchor],
        CaseAssertion "case:arrangement" "Zoë records an earlier arrangement; the relationship to legal entitlement is explicitly supplied, not inferred." (Scope "actor:zoe" "arrangement") [SourceRef "source:synthetic" Nothing]]
    , typedAnnotations=[Annotation "draft:entitlement" ["law:permission"] "Controller entitlement and complete offence elements are outside this bounded relationship question." "draft"]
    , typedPresentation=[],typedLimitations=["Fixed CMA 2007 Revised Edition research context. Positive supplied permission relation only; not the complete s 2(5) or s 3 test.",
        "No inference of unauthorised access from missing or negative permission. Concrete tuple identity and explicit actor/context scope only."] }

thresholdDocument :: ExactScalar -> Integer -> TypedDocument
thresholdDocument amount threshold = TypedDocument
  { typedDocumentFormat=typedAuthoringFormat,typedDocumentId="document:threshold",typedLawId="law:threshold",typedLawRevision="RTA-2004RE-bounded-1"
  , typedEntityTypes=[TypedEntityType (meta "person" "Person")],typedEntities=[TypedEntity (meta "driver:one" "Synthetic driver") "person"]
  , typedPredicates=[],typedApplications=[]
  , typedScalars=[scalar "value:measurement" "Externally normalised breath value",scalar "value:threshold" "Declared fixed threshold"]
  , typedExpressions=[TypedExpression (sourced "q:threshold" "Does the supplied integer strictly exceed the threshold?") (IntegerComparison "gt" "value:measurement" "value:threshold")]
  , typedLinks=[TypedLink "body:threshold" "rule:threshold" "q:threshold" "typed_body"]
  , typedRules=[TypedRule (sourced "rule:threshold" "Bounded strict-threshold research question") "p:threshold"]
  , typedPropositions=[TypedProposition (meta "p:threshold" "Technical strict-threshold condition")]
  , typedAssessments=[]
  , typedValues=[TypedValue (meta "supply:measurement" "Supplied measurement integer") "value:measurement" scope amount "Synthetic externally normalised value; no pass/fail classification supplied." "Synthetic fixture author",
      TypedValue (meta "supply:threshold" "Supplied fixed threshold integer") "value:threshold" scope (ExactInteger threshold) "Declared fixed threshold in the same external profile." "Synthetic fixture author"]
  , typedAnalyses=[TypedAnalysis "analysis:threshold" "rule:threshold" "p:threshold" scope [] ["supply:measurement","supply:threshold"]]
  , typedOriginalSources=[SourceRecord "source:rta" "law" (Just "https://sso.agc.gov.sg/Act-Rev/276/Published?DocDate=20041231&ProvIds=pr72-") Nothing]
  , typedCaseAssertions=[],typedAnnotations=[],typedPresentation=[]
  , typedLimitations=["Fixed RTA 2004 Revised Edition ss 67/72 research context; breath strict exceedance 35 microgrammes per 100 mL. Not a complete offence or applicable-law selection.",
      "Caller must validate specimen=breath, unit=microgrammes per 100 mL and a common exact integer scale before constructing these values. The SDK checks integer types, not physical quantities."] }
  where
    scope = Scope "driver:one" "measurement:one"
    sourced key label = (meta key label) {typedSources=[SourceRef "source:rta" Nothing],typedCitation=Just "RTA 2004 RE, ss 67/72 (bounded threshold)"}
    scalar key label = TypedScalar (sourced key label) "integer" (Just "External breath/microgrammes-per-100mL; caller-declared common integer scale. No native medium or unit validation.")

evaluate :: TypedDocument -> Text -> Either [AuthoringDiagnostic] TypedEvaluation
evaluate document key = compileTypedAnalysis document key >>= evaluateTypedAnalysis

ruleStatus :: TypedEvaluation -> [Text]
ruleStatus = map typedObservedStatus . typedReportRules . typedEvaluationReport

-- Caller policy, deliberately outside the SDK. This validates a declared
-- external profile; it cannot authenticate a physical sample or its units.
normalisedThreshold :: Text -> Text -> Integer -> ExactScalar -> Either Text TypedDocument
normalisedThreshold medium unit scale amount
  | medium /= "breath" = Left "caller measurement profile: expected breath"
  | unit /= "microgrammes/100mL" = Left "caller measurement profile: expected microgrammes/100mL"
  | scale <= 0 = Left "caller measurement profile: exact common scale must be positive"
  | otherwise = Right ((thresholdDocument amount (35 * scale)) {typedScalars=
      [s {scalarNormalisation=Just ("Declared external profile: breath, microgrammes/100mL; exact integer scale " <> T.pack (show scale) <> ". Caller assertion, no sample authentication.")} | s <- typedScalars (thresholdDocument amount (35 * scale))]})
