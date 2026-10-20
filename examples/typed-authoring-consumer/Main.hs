{-# LANGUAGE OverloadedStrings #-}
module Main (main) where

import Control.Monad (forM_, unless)
import Data.Aeson (ToJSON, object, (.=))
import qualified Data.ByteString as BS
import System.Directory (createDirectoryIfMissing)
import System.Environment (getArgs)
import System.FilePath ((</>))
import TypedExamples
import Yuho.Authoring

require :: Show e => Either e a -> IO a
require = either (fail . show) pure

main :: IO ()
main = do
  args <- getArgs
  out <- case args of [folder] -> pure folder; _ -> fail "usage: yuho-typed-authoring OUTPUT-DIRECTORY"
  createDirectoryIfMissing True out
  permission <- require permissionDocument
  let write name bytes = BS.writeFile (out </> name) bytes
      record :: ToJSON a => FilePath -> a -> IO ()
      record name = write name . encodeRecord
      run name document key focus sources = do
        let validation = validateTypedAnalysis document key
        unless (typedAnalysisReady validation) (fail (show validation))
        write (name <> ".document.json") (encodeTypedDocument document)
        decoded <- require (decodeTypedDocument (encodeTypedDocument document))
        unless (decoded == document) (fail "typed authored round trip differs")
        compiled <- require (compileTypedAnalysis decoded key)
        result <- require (evaluateTypedAnalysis compiled)
        replay <- require (evaluate decoded key)
        unless (typedEvaluationReport result == typedEvaluationReport replay) (fail "saved-document replay differs")
        write (name <> ".request.json") (typedCompiledRequest compiled)
        write (name <> ".response.json") (typedEvaluationResponse result)
        record (name <> ".report.json") (typedEvaluationReport result)
        projection <- require (projectTypedEvaluation result)
        encoded <- require (encodeTypedProjection projection)
        write (name <> ".projection.json") encoded
        view <- require (typedReferenceView projection focus sources)
        record (name <> ".bindings.json") view
        require (encodeTypedViewJson projection view) >>= write (name <> ".view.json")
        require (encodeTypedViewXml projection view) >>= write (name <> ".xml")
        require (encodeTypedViewSvg projection view) >>= write (name <> ".svg")
        pure (result,projection)
  (ada,adaProjection) <- run "permission-ada" permission "analysis:ada" (TypedExpressionFocus "q:ada") []
  (ben,_) <- run "permission-ben-unresolved" permission "analysis:ben" (TypedExpressionFocus "q:ben") []
  inspection <- require (inspectTypedExpression adaProjection "q:ada")
  record "permission-inspection.json" inspection
  anchor <- require caseReference
  recovered <- require (recoverTypedSource adaProjection anchor)
  record "permission-source-recovery.json" recovered
  sourceView <- require (typedReferenceView adaProjection (TypedExpressionFocus "q:ada") ["source:synthetic"])
  record "permission-source.bindings.json" sourceView
  require (encodeTypedProjection adaProjection) >>= write "permission-source.projection.json"
  require (encodeTypedViewSvg adaProjection sourceView) >>= write "permission-source.svg"
  let revised = permission {typedAssessments=[if typedId (typedAssessmentMeta a) == "assessment:ben"
        then a {typedClassification=TechnicalFalse,typedAssessmentReason="Explicit negative fixture classification for this exact Ben tuple."} else a | a <- typedAssessments permission]}
  (negative,_) <- run "permission-ben-false" revised "analysis:ben" (TypedExpressionFocus "q:ben") []
  stale <- case projectTypedEvaluationOn revised ben of Left errors -> pure errors; Right _ -> fail "stale overlay admitted"
  record "permission-revision.json" (object ["oldSnapshot" .= typedSnapshotId (typedEvaluationSnapshot ben),
    "newSnapshot" .= typedSnapshotId (typedEvaluationSnapshot negative),"oldResult" .= ruleStatus ben,"newResult" .= ruleStatus negative,
    "adaRemains" .= ruleStatus ada,"staleDiagnostics" .= stale])
  let draft = permission {typedAnalyses=[a {selectedTypedAssessments=[]} | a <- typedAnalyses permission]}
  draftProjection <- require (projectTypedAuthored draft "analysis:ada")
  require (encodeTypedProjection draftProjection) >>= write "permission-draft.projection.json"
  record "permission-draft.validation.json" (validateTypedAnalysis draft "analysis:ada")
  forM_ [("34",ExactInteger 34,1),("35",ExactInteger 35,1),("36",ExactInteger 36,1),
      ("unresolved",UnknownInteger "integer" "not_determined",1),("scaled-3501",ExactInteger 3501,100)] $ \(label,amount,scale) -> do
    measured <- require (normalisedThreshold "breath" "microgrammes/100mL" scale amount)
    _ <- run ("threshold-" <> label) measured "analysis:threshold" (TypedExpressionFocus "q:threshold") []
    pure ()
  oldNumeric <- require (normalisedThreshold "breath" "microgrammes/100mL" 1 (ExactInteger 34))
  newNumeric <- require (normalisedThreshold "breath" "microgrammes/100mL" 1 (ExactInteger 36))
  oldRun <- require (evaluate oldNumeric "analysis:threshold")
  newRun <- require (evaluate newNumeric "analysis:threshold")
  scalarStale <- case projectTypedEvaluationOn newNumeric oldRun of Left errors -> pure errors; Right _ -> fail "stale scalar overlay admitted"
  record "threshold-revision.json" (object ["oldSnapshot" .= typedSnapshotId (typedEvaluationSnapshot oldRun),
    "newSnapshot" .= typedSnapshotId (typedEvaluationSnapshot newRun),"oldResult" .= ruleStatus oldRun,
    "newResult" .= ruleStatus newRun,"fixedThreshold" .= (35::Integer),"staleDiagnostics" .= scalarStale])
  let threshold = thresholdDocument (ExactInteger 36) 35
  _ <- run "threshold-rule" threshold "analysis:threshold" TypedRuleFocus []
  let failures = [("missing-assessment",draft,"analysis:ada"),
        ("wrong-scope",permission {typedAnalyses=[a {selectedTypedAssessments=["assessment:ada"]} | a <- typedAnalyses permission]},"analysis:ben"),
        ("wrong-scalar",threshold {typedScalars=[s {scalarDeclaredType="date"} | s <- typedScalars threshold]},"analysis:threshold"),
        ("tuple-edited",permission {typedApplications=[if typedId (applicationMeta a) == "application:ada-read" then a {applicationTuple=(applicationTuple a) {tupleArguments=["actor:ada","resource:r","kind:write"]}} else a | a <- typedApplications permission]},"analysis:ada")]
  forM_ failures $ \(name,document,key) -> do
    record (name <> ".validation.json") (validateTypedAnalysis document key)
    case compileTypedAnalysis document key of Left errors -> record (name <> ".rejection.json") errors; Right _ -> fail "invalid example compiled"
  putStrLn "typed public consumer: exact tuples, scopes, revisions, scalar boundaries, projections, replay and stale checks passed"
