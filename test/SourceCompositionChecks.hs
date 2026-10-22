{-# LANGUAGE OverloadedStrings #-}
module SourceCompositionChecks (runSourceCompositionChecks) where

import Control.Monad (forM_,unless)
import qualified Data.Aeson as J
import qualified Data.ByteString as BS
import Data.List (sortOn)
import Data.Text (Text)
import qualified Data.Text as T
import Data.Time.Calendar (fromGregorian)
import System.FilePath ((</>))
import qualified Yuho.Authoring as A
import Yuho.Surface.Computed
import qualified ComputedExample as Independent

right :: Show e => Either e a -> IO a
right = either (fail . show) pure
check :: String -> Bool -> IO ()
check name value = unless value (fail ("source composition: " <> name))

-- Independently authored public SDK reference, not populated from parsed source
-- or from either new source adapter. Only generated IDs/spans are normalised.
reference :: A.SuppliedStatus -> Bool -> Text -> A.SuppliedStatus -> A.SuppliedStatus -> Bool
  -> Either [A.AuthoringDiagnostic] (A.ApplicationReport,Maybe A.PresumptionReport)
reference supplied presumption bound direct rebuttal skipped =
  if presumption then do
    e<-A.compilePresumptionAnalysis registered "reference-analysis" >>= A.evaluatePresumptionAnalysis
    pure (A.presumptionReportProof (A.presumptionEvaluationReport e),Just (A.presumptionEvaluationReport e))
  else do e<-A.compileAnalysis doc "reference-analysis" >>= A.evaluateAnalysis; pure (A.evaluationReport e,Nothing)
  where
    fixed=[("f:entry",if skipped then A.Unresolved A.NotDetermined else A.Proved)
          ,("f:no-authorization",direct),("f:knowledge",A.Proved)
          ,("f:immediate-danger",A.NotProved),("f:rescue-purpose",rebuttal)]
    inputs=[(i,if i==bound then supplied else s) | (i,s)<-fixed]
    node i kind = A.LawNode i kind i Nothing Nothing []
    assessments=[A.Assessment ("reference:"<>i) i scope (A.Classification s) "Independent explicit reference classification"
      "Independent native test" "synthetic_fixture" "assumption" [] [] | (i,s)<-inputs]
    scope=A.Scope "actor:one" "event:fictional"
    edge i a b kind=A.LawEdge i a b kind
    doc=A.AuthoringDocument A.authoringFormat "reference-document"
      (A.LawDefinition "reference-law" "1"
        ([node "o:entry" "rule",node "x:emergency-rescue" "rule",node "g:offence-requirements" "all",node "g:emergency-requirements" "all"]++[node i "input" | (i,_)<-fixed])
        [edge "main" "o:entry" "g:offence-requirements" "requires"
        ,edge "exception" "o:entry" "x:emergency-rescue" "exception"
        ,edge "guard" "x:emergency-rescue" "g:emergency-requirements" "requires"
        ,edge "entry" "g:offence-requirements" "f:entry" "member"
        ,edge "target" "g:offence-requirements" "f:no-authorization" "member"
        ,edge "trigger" "g:offence-requirements" "f:knowledge" "member"
        ,edge "danger" "g:emergency-requirements" "f:immediate-danger" "member"
        ,edge "rebuttal" "g:emergency-requirements" "f:rescue-purpose" "member"] ["Independent fictional reference"])
      [] [] assessments [A.Analysis "reference-analysis" "o:entry" scope (map A.assessmentId assessments) (fromGregorian 2026 9 13)] [] [] []
    registered=A.PresumptionDocument A.presumptionAuthoringFormat "reference-presumptions" doc
      [A.AuthoredRegistration "pres:technical" "Technical support" "f:no-authorization" ["reference-analysis"] []
        (A.RegisteredCondition "reference-trigger" "leaf_effective" (Just "f:knowledge") [] [])
        (A.RegisteredCondition "reference-rebuttal" "leaf_effective" (Just "f:rescue-purpose") [] [])]
      ["No legal sufficiency claim"]

semantic :: A.ApplicationReport -> J.Value
semantic r=J.toJSON (A.reportConclusion r
  ,sortOn (\(a,_,_,_)->a) [(A.observationNode x,A.observationComputed x,A.observationEvaluation x,A.observationSkipReason x) | x<-A.reportRequirements r]
  ,sortOn (\(a,_,_,_)->a) [(A.ruleAuthoredId x,A.ruleComputed x,A.ruleEvaluation x,A.ruleBranchReason x) | x<-A.reportRules r]
  ,[(A.exceptionComputed x,A.exceptionEvaluation x,A.exceptionFired x,A.exceptionSkipReason x) | x<-A.reportExceptions r])
derivations :: A.PresumptionReport -> J.Value
derivations r=J.toJSON
  ([(A.registeredId (A.registrationAuthored x),A.registrationRouteState x,A.registrationEvaluation x
    ,A.resolvedConditionValue (A.registrationTriggerResult x),A.resolvedConditionValue (A.registrationRebuttalResult x)) | x<-A.presumptionReportDerivations r]
  ,sortOn (\(a,_,_,_)->a) [(A.effectiveInput x,A.effectiveDirectValue x,A.effectiveValue x,A.effectiveRoutes x) | x<-A.presumptionReportLeaves r])

runSourceCompositionChecks :: FilePath -> IO ()
runSourceCompositionChecks root = do
  let cases =
        [("proof/true",A.TechnicalTrue,A.Proved,False,"f:no-authorization",A.NotProved,A.NotProved,False,"satisfied",Nothing)
        ,("proof/false",A.TechnicalFalse,A.NotProved,False,"f:no-authorization",A.NotProved,A.NotProved,False,"not_satisfied",Nothing)
        ,("proof/unresolved",A.TechnicalUnresolved "pending",A.Unresolved A.NotDetermined,False,"f:no-authorization",A.NotProved,A.NotProved,False,"unresolved",Nothing)
        ,("presumption/active",A.TechnicalTrue,A.Proved,True,"f:knowledge",A.NotProved,A.NotProved,False,"satisfied",Just "active")
        ,("presumption/inactive",A.TechnicalFalse,A.NotProved,True,"f:knowledge",A.NotProved,A.NotProved,False,"not_satisfied",Just "inactive")
        ,("presumption/unresolved",A.TechnicalUnresolved "pending",A.Unresolved A.NotDetermined,True,"f:knowledge",A.NotProved,A.NotProved,False,"unresolved",Just "unresolved")
        ,("presumption/rebutted",A.TechnicalTrue,A.Proved,True,"f:knowledge",A.NotProved,A.Proved,False,"not_satisfied",Just "rebutted")
        ,("presumption/dominance",A.TechnicalTrue,A.Proved,True,"f:knowledge",A.Proved,A.Proved,False,"satisfied",Just "rebutted")
        ,("presumption/skipped",A.TechnicalTrue,A.Proved,True,"f:knowledge",A.NotProved,A.NotProved,True,"unresolved",Just "active")
        ,("presumption/computed-rebuttal",A.TechnicalTrue,A.Proved,True,"f:rescue-purpose",A.NotProved,A.NotProved,False,"not_satisfied",Just "rebutted")
        ,("presumption/computed-rebuttal-false",A.TechnicalFalse,A.NotProved,True,"f:rescue-purpose",A.NotProved,A.NotProved,False,"satisfied",Just "active")]
  forM_ cases $ \(name,technical,supplied,isPres,bound,direct,rebuttal,skipped,expected,route) -> do
    plan<-loadComposition (root</>"examples/source-composition"</>name<>".project.yh") >>= right
    execution<-right (executeComposition plan)
    let report=A.computedInputReport execution
        input=compositionDocument plan
        source=A.computedTypedSource input
    (referenceProof,referencePresumption)<-right (reference supplied isPres bound direct rebuttal skipped)
    check (name<>" independent proof observations/branches/skips")
      (semantic (A.computedDownstreamReport report)==semantic referenceProof)
    check (name<>" explicit expected conclusion") (A.reportConclusion (A.computedDownstreamReport report)==expected)
    sourceRef<-right (Independent.typedSource technical >>= \d->A.compileTypedAnalysis d "typed-analysis" >>= A.evaluateTypedAnalysis)
    check (name<>" independent named expression status")
      (map A.typedObservedStatus (A.typedReportExpressions (A.computedUpstreamReport report)) ==
       map A.typedObservedStatus (A.typedReportExpressions (A.typedEvaluationReport sourceRef)))
    check (name<>" explicit mapped classification") (A.computedMappedClassification report==A.Classification supplied)
    case (A.computedDerivationReport report,referencePresumption,route) of
      (Just a,Just b,Just expectedRoute) -> do
        check (name<>" route/direct/effective parity") (derivations a==derivations b)
        check (name<>" expected route") (map A.registrationRouteState (A.presumptionReportDerivations a)==[expectedRoute])
      (Nothing,Nothing,Nothing)->pure ()
      _->fail "missing derivation report"
    BS.putStr ("source-composition-parity " <> A.encodeRecord (J.object
      ["project" J..= name,"actual_proof" J..= semantic (A.computedDownstreamReport report)
      ,"reference_proof" J..= semantic referenceProof
      ,"actual_derivations" J..= fmap derivations (A.computedDerivationReport report)
      ,"reference_derivations" J..= fmap derivations referencePresumption
      ,"expected_conclusion" J..= expected,"expected_route" J..= route]) <> "\n")
    check "two same-labelled actors preserve identity"
      (length [() | e<-A.typedEntities source,A.typedLabel (A.entityMeta e)=="Alex"]==2)
    check "other actor tuple retained unselected"
      (length (A.typedAssessments source)==2 && map (length . A.selectedTypedAssessments) (A.typedAnalyses source)==[1])
    check "no generated assessment in authored destination" $ case A.computedDestinationDocument (A.computedDestination input) of
      Right d->A.assessmentId (A.computedGeneratedAssessment report) `notElem` map A.assessmentId (A.documentAssessments d)
      _->False
    replay<-right (A.decodeComputedInputDocument (A.encodeComputedInputDocument input) >>= \d->Right d)
    replayed<-right (A.executeComputedInput replay)
    check "immutable artifact replay" (A.computedInputReport replayed==report)
    _<-right (checkCompositionAttachment plan replay)
    projection<-right (A.projectComputedInput execution)
    check "semantic navigation validation" (null (A.validateComputedProjection (A.computedProjectionData projection)))
    forM_ (A.typedCaseAssertions source) $ \a->forM_ (A.assertionSources a) $ \ref->do
      excerpt<-right (A.recoverComputedInputSource execution "source" ref)
      check "exact Unicode original source" (maybe False (T.isPrefixOf "Zoë records") (A.excerptText excerpt))
  forM_ [("boundary",A.ExactInteger 35,A.NotProved,"not_satisfied"),("above",A.ExactInteger 36,A.Proved,"satisfied")
        ,("unknown",A.UnknownInteger "integer" "pending",A.Unresolved A.NotDetermined,"unresolved")] $ \(name,value,supplied,expected) -> do
    plan<-loadComposition (root</>"examples/source-composition/proof/integer-"<>name<>".project.yh") >>= right
    execution<-right (executeComposition plan)
    independent<-right (Independent.scalarSource value >>= \d->A.compileTypedAnalysis d "typed-analysis" >>= A.evaluateTypedAnalysis)
    let report=A.computedInputReport execution
    check "integer independent computation parity" (map A.typedObservedStatus (A.typedReportExpressions (A.computedUpstreamReport report))==map A.typedObservedStatus (A.typedReportExpressions (A.typedEvaluationReport independent)))
    (ref,_)<-right (reference supplied False "f:no-authorization" A.NotProved A.NotProved False)
    check "integer explicit expected and full proof parity" (A.reportConclusion (A.computedDownstreamReport report)==expected && semantic (A.computedDownstreamReport report)==semantic ref)
    BS.putStr ("source-composition-parity " <> A.encodeRecord (J.object
      ["project" J..= ("proof/integer-"<>name),"actual_proof" J..= semantic (A.computedDownstreamReport report)
      ,"reference_proof" J..= semantic ref,"expected_conclusion" J..= expected]) <> "\n")
  putStrLn "source composition: fourteen source projects match independently authored public SDK references; observations, route/direct/effective values, skipped guards, exact sources and replay passed"
