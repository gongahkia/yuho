{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Report
  ( Evaluation, evaluateAnalysis, evaluationReport, evaluationSnapshot
  , evaluationKernelResponse, evaluationMappings, evaluationCompilation
  , ApplicationReport(..), RequirementObservation(..), RuleObservation(..)
  , ExceptionObservation(..), Comparison(..), AssessmentChange(..)
  , ObservationChange(..), compareAnalyses ) where

import Data.Aeson (ToJSON(..), genericToJSON)
import qualified Data.ByteString as BS
import Data.List (find, nub)
import Data.Text (Text)
import GHC.Generics (Generic)
import Yuho.Authoring.Compile
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue, validateBindings)
import Yuho.Protocol.Decode (inputDigest)
import Yuho.Protocol.Json (decodeJson)
import Yuho.SuppliedProofStatus.Encode (encodeProofResult)
import Yuho.SuppliedProofStatus.Evaluate (evaluateProof)
import Yuho.SuppliedProofStatus.Select (selectProofPenalties)
import qualified Yuho.SuppliedProofStatus.Types as Proof

data RequirementObservation = RequirementObservation
  { observationNode :: Text, observationOccurrence :: [Text], observationRule :: Text
  , observationKind :: Text, observationLaw :: Maybe LawNode
  , observationRelationships :: [Text]
  , observationKernelId :: Text, observationKernelBranch :: Text
  , observationAssessment :: Maybe Assessment, observationAssertions :: [CaseAssertion]
  , observationSources :: [SourceRecord], observationComputed :: Maybe Text
  , observationEvaluation :: Text, observationSkipReason :: Maybe Text
  } deriving (Eq, Show, Generic)

data RuleObservation = RuleObservation
  { ruleAuthoredId :: Text, ruleKernelId :: Text, ruleKernelBranch :: Text
  , ruleComputed :: Maybe Text, ruleEvaluation :: Text, ruleBranchReason :: Maybe Text
  } deriving (Eq, Show, Generic)

data ExceptionObservation = ExceptionObservation
  { exceptionRelationship :: Text, exceptionMainRule :: Text, exceptionGuardRule :: Text
  , exceptionEvaluation :: Text, exceptionComputed :: Maybe Text
  , exceptionFired :: Maybe Bool, exceptionSkipReason :: Maybe Text
  } deriving (Eq, Show, Generic)

data ApplicationReport = ApplicationReport
  { reportSnapshot :: Text, reportRequestDigest :: Text, reportProfile :: Text
  , reportAnalysis :: Text
  , reportTarget :: Text, reportScope :: Scope, reportConclusion :: Text
  , reportRequirements :: [RequirementObservation], reportRules :: [RuleObservation]
  , reportExceptions :: [ExceptionObservation], reportOpenInputs :: [OpenInput]
  , reportNotice :: Text
  } deriving (Eq, Show, Generic)

data Evaluation = Evaluation ApplicationReport CompiledAnalysis BS.ByteString

evaluationReport :: Evaluation -> ApplicationReport
evaluationReport (Evaluation value _ _) = value
evaluationSnapshot :: Evaluation -> Snapshot
evaluationSnapshot = compiledSnapshot . evaluationCompilation
evaluationKernelResponse :: Evaluation -> BS.ByteString
evaluationKernelResponse (Evaluation _ _ value) = value
evaluationMappings :: Evaluation -> [RequirementMapping]
evaluationMappings = compiledRequirements . evaluationCompilation
evaluationCompilation :: Evaluation -> CompiledAnalysis
evaluationCompilation (Evaluation _ value _) = value

evaluateAnalysis :: CompiledAnalysis -> Either [AuthoringDiagnostic] Evaluation
evaluateAnalysis compiled = do
  result <- kernel (evaluateProof (compiledValidated compiled))
  selection <- kernel (selectProofPenalties (compiledValidated compiled) result)
  response <- kernel (encodeProofResult (compiledValidated compiled) result selection)
  request <- either (\_ -> Left [issue "AINTERNAL" "/" [] "compiled request unavailable"])
    Right (decodeJson (compiledRequest compiled))
  let snapshot = compiledSnapshot compiled
      doc = snapshotDocument snapshot
      law = documentLaw doc
      analysis = snapshotAnalysis snapshot
      mappings = compiledRequirements compiled
      nodeFor key = find ((== key) . nodeId) (lawNodes law)
      assessed m = mappedAssessment m >>= \key -> find ((== key) . assessmentId) (documentAssessments doc)
      ruleFor key = find ((== key) . Proof.proofRuleId) (Proof.proofResultRules result)
      branchFor r = case Proof.proofRuleBranches r of
        [b] -> Just b
        _ -> Nothing
      rootBranch = ruleFor (maybe "" mappedKernelRule (find ((== analysisTarget analysis) . mappedRule) mappings)) >>= branchFor
      rootReason = reasonText . Proof.proofBranchReason <$> rootBranch
      whySkipped = case rootReason of
        Just reason -> Just ("exception guard skipped because main branch: " <> reason)
        Nothing -> Just "exception guard was not reached by the evaluator"
      observations = [
        let n = nodeFor (mappedNode m)
            assessment = assessed m
            assertions = [a | a <- documentAssertions doc,
              assertionId a `elem` maybe [] assessmentAssertions assessment]
            originalSourceIds = nub (map referenceSource
              (maybe [] nodeSources n ++ maybe [] assessmentSources assessment
                ++ concatMap assertionSources assertions))
            trace = ruleFor (mappedKernelRule m) >>= \r ->
              find ((== mappedKernelRequirement m) . Proof.proofTraceId) (Proof.proofRuleTrace r)
        in RequirementObservation (mappedNode m) (mappedOccurrence m) (mappedRule m)
          (maybe "unknown" nodeKind n) n
          [edgeId e | e <- lawEdges law, edgeFrom e == mappedNode m, edgeKind e == "member"]
          (mappedKernelRequirement m) (mappedKernelBranch m) assessment assertions
          [s | s <- documentSources doc, sourceId s `elem` originalSourceIds]
          (Proof.satisfactionText . Proof.proofTraceStatus <$> trace)
          (maybe "not_evaluated" (const "evaluated") trace)
          (maybe whySkipped (const Nothing) trace)
        | m <- mappings]
      rules = [let evaluated = ruleFor kernelId
        in RuleObservation authored kernelId branchId
          (Proof.satisfactionText . Proof.proofRuleStatus <$> evaluated)
          (maybe "not_evaluated" (const "evaluated") evaluated)
          (evaluated >>= branchFor >>= Just . reasonText . Proof.proofBranchReason)
        | authored <- nub (map mappedRule mappings),
          Just m <- [find ((== authored) . mappedRule) mappings],
          let kernelId = mappedKernelRule m, let branchId = mappedKernelBranch m]
      exceptions = [let guard = find ((== edgeTo e) . ruleAuthoredId) rules
                        status = guard >>= ruleComputed
                    in ExceptionObservation (edgeId e) (edgeFrom e) (edgeTo e)
                      (maybe "not_evaluated" ruleEvaluation guard) status
                      ((== "satisfied") <$> status)
                      (if status == Nothing then whySkipped else Nothing)
        | e <- lawEdges law, edgeFrom e == analysisTarget analysis, edgeKind e == "exception"]
      report = ApplicationReport (snapshotId snapshot) (inputDigest request) (snapshotProfile snapshot)
        (analysisId analysis) (analysisTarget analysis) (analysisScope analysis)
        (Proof.satisfactionText (Proof.proofResultStatus result)) observations rules exceptions
        (openInputs (validateBindings doc (analysisId analysis)))
        "Technical evaluation of the selected model and supplied classifications; no evidence weighing, legal interpretation selection, factual falsity, guilt or sentence finding."
  pure (Evaluation report compiled response)
  where kernel = either (\_ -> Left [issue "AKERNEL" "/evaluation"
          [analysisId (snapshotAnalysis (compiledSnapshot compiled))]
          "existing evaluator or result encoder rejected the validated artifact"]) Right

reasonText :: Proof.ProofReason -> Text
reasonText reason = case reason of
  Proof.ProofSatisfied -> "satisfied"
  Proof.ProofRequirementsNotSatisfied -> "requirements_not_satisfied"
  Proof.ProofRequirementsUnresolved -> "requirements_unresolved"
  Proof.ProofDefeated -> "defeated"
  Proof.ProofExceptionUnresolved -> "exception_unresolved"

data AssessmentChange = AssessmentChange
  { changeInput :: Text, changeOccurrence :: [Text]
  , changeOldAssessment :: Maybe Assessment, changeNewAssessment :: Maybe Assessment
  , changeSelection :: Bool, changeClassification :: Bool, changeAuthorship :: Bool
  , changeReferencedMaterial :: Bool
  } deriving (Eq, Show, Generic)

data ObservationChange = ObservationChange
  { changeObservationKind :: Text, changeObject :: Text, changePath :: [Text]
  , changeOldComputed :: Maybe Text, changeNewComputed :: Maybe Text
  , changeOldEvaluation :: Text, changeNewEvaluation :: Text
  , changeOldReason :: Maybe Text, changeNewReason :: Maybe Text
  } deriving (Eq, Show, Generic)

data Comparison = Comparison
  { comparisonOldSnapshot :: Text, comparisonNewSnapshot :: Text
  , comparisonAssessments :: [AssessmentChange]
  , comparisonChanged :: [ObservationChange], comparisonUnchanged :: [ObservationChange]
  , comparisonOldConclusion :: Text, comparisonNewConclusion :: Text
  , comparisonConclusionChanged :: Bool
  } deriving (Eq, Show, Generic)

compareAnalyses :: Evaluation -> Evaluation -> Either [AuthoringDiagnostic] Comparison
compareAnalyses old new = do
  let a = evaluationSnapshot old
      b = evaluationSnapshot new
      scopeKey snapshot = let analysis = snapshotAnalysis snapshot in
        (snapshotLawDigest snapshot,snapshotProfile snapshot,analysisTarget analysis,
          analysisScope analysis,analysisReferenceDate analysis)
  if scopeKey a == scopeKey b then pure () else Left
    [issue "AINCOMPATIBLE" "/comparison" [analysisId (snapshotAnalysis a),analysisId (snapshotAnalysis b)]
      "comparison requires identical law definition/sources/revision, target, actor/context, reference date and profile"]
  let left = evaluationReport old
      right = evaluationReport new
      key o = (observationNode o,observationOccurrence o,observationRule o)
      pairs = [(o,n) | o <- reportRequirements left,
        Just n <- [find ((== key o) . key) (reportRequirements right)]]
      material doc assessment =
        let assertions = [x | x <- documentAssertions doc,
              assertionId x `elem` maybe [] assessmentAssertions assessment]
            refs = maybe [] assessmentSources assessment ++ concatMap assertionSources assertions
        in (assertions,[s | s <- documentSources doc, sourceId s `elem` map referenceSource refs])
      changes = [AssessmentChange (observationNode o) (observationOccurrence o) x y
          ((assessmentId <$> x) /= (assessmentId <$> y))
          ((assessmentClassification <$> x) /= (assessmentClassification <$> y))
          (fmap authorship x /= fmap authorship y) materialChanged
        | (o,n) <- pairs, let x = observationAssessment o, let y = observationAssessment n,
          let materialChanged = material (snapshotDocument a) x /= material (snapshotDocument b) y,
          x /= y || materialChanged]
      requirements = [ObservationChange "requirement" (observationNode o) (observationOccurrence o)
          (observationComputed o) (observationComputed n) (observationEvaluation o)
          (observationEvaluation n) (observationSkipReason o) (observationSkipReason n) | (o,n) <- pairs]
      rules = [ObservationChange "rule" (ruleAuthoredId o) [] (ruleComputed o) (ruleComputed n)
          (ruleEvaluation o) (ruleEvaluation n) (ruleBranchReason o) (ruleBranchReason n)
        | o <- reportRules left, Just n <- [find ((== ruleAuthoredId o) . ruleAuthoredId) (reportRules right)]]
      exceptions = [ObservationChange "exception" (exceptionRelationship o) []
          (exceptionComputed o) (exceptionComputed n) (exceptionEvaluation o) (exceptionEvaluation n)
          (exceptionSkipReason o) (exceptionSkipReason n)
        | o <- reportExceptions left,
          Just n <- [find ((== exceptionRelationship o) . exceptionRelationship) (reportExceptions right)]]
      observations = requirements ++ rules ++ exceptions
      changed row = (changeOldComputed row,changeOldEvaluation row,changeOldReason row)
        /= (changeNewComputed row,changeNewEvaluation row,changeNewReason row)
  pure (Comparison (snapshotId a) (snapshotId b) changes (filter changed observations)
    (filter (not . changed) observations) (reportConclusion left) (reportConclusion right)
    (reportConclusion left /= reportConclusion right))
  where
    authorship assessment = (assessmentReason assessment,assessmentIssuer assessment,
      assessmentOrigin assessment,assessmentBasis assessment,assessmentAssertions assessment,
      assessmentSources assessment)

instance ToJSON RequirementObservation where toJSON = genericToJSON jsonOptions
instance ToJSON RuleObservation where toJSON = genericToJSON jsonOptions
instance ToJSON ExceptionObservation where toJSON = genericToJSON jsonOptions
instance ToJSON ApplicationReport where toJSON = genericToJSON jsonOptions
instance ToJSON AssessmentChange where toJSON = genericToJSON jsonOptions
instance ToJSON ObservationChange where toJSON = genericToJSON jsonOptions
instance ToJSON Comparison where toJSON = genericToJSON jsonOptions
