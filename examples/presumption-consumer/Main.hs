{-# LANGUAGE OverloadedStrings #-}
module Main (main) where
import Control.Monad (forM_, unless)
import qualified Data.Aeson as A
import qualified Data.Aeson.KeyMap as KM
import qualified Data.ByteString as BS
import qualified Data.Text as T
import System.Directory (createDirectoryIfMissing)
import System.Environment (getArgs)
import System.FilePath ((</>))
import Yuho.Authoring
import PresumptionExamples

required :: Show e => Either e a -> IO a
required = either (fail . show) pure
check :: String -> Bool -> IO ()
check label condition = unless condition (fail label)
main :: IO ()
main = do
  args <- getArgs
  out <- case args of [directory] -> pure directory; _ -> fail "usage: yuho-presumption-consumer OUTPUT_DIRECTORY"
  createDirectoryIfMissing True out
  let save name value = BS.writeFile (out </> name) (encodeRecord value)
      export name doc expanded = do
        let validation=validatePresumptionAnalysis doc "analysis:synthetic"
        check "analysis ready" (presumptionAnalysisReady validation)
        save (name <> ".validation.json") validation
        BS.writeFile (out </> name <> ".document.json") (encodePresumptionDocument doc)
        replay <- required (decodePresumptionDocument (encodePresumptionDocument doc))
        check "round trip" (replay == doc)
        compiled <- required (compilePresumptionAnalysis replay "analysis:synthetic")
        evaluated <- required (evaluatePresumptionAnalysis compiled)
        save (name <> ".report.json") (presumptionEvaluationReport evaluated)
        BS.writeFile (out </> name <> ".request.json") (presumptionCompiledRequest compiled)
        BS.writeFile (out </> name <> ".response.json") (presumptionEvaluationResponse evaluated)
        p <- required (projectPresumptionEvaluation evaluated)
        BS.writeFile (out </> name <> ".projection.json") =<< required (encodePresumptionProjection p)
        focused <- required (inspectPresumptionTarget p "K")
        save (name <> ".inspection.json") focused
        view <- required (presumptionReferenceView p "K" expanded)
        save (name <> ".bindings.json") view
        BS.writeFile (out </> name <> ".view.json") =<< required (encodePresumptionViewJson p view)
        BS.writeFile (out </> name <> ".view.xml") =<< required (encodePresumptionViewXml p view)
        BS.writeFile (out </> name <> ".svg") =<< required (encodePresumptionViewSvg p view)
        pure evaluated
  forM_ matrix $ \(name,t,r,k,state,conclusion) -> do
    e <- export (T.unpack name) (synthetic t r k) []
    check "independent route expectation" (map registrationRouteState (presumptionReportDerivations (presumptionEvaluationReport e)) == [state])
    check "independent downstream expectation" (reportConclusion (presumptionReportProof (presumptionEvaluationReport e)) == conclusion)
  forM_ [("chain-active",Proved,NotProved,NotProved),("chain-rebutted",Proved,Proved,NotProved),
    ("chain-uncertain",Unresolved NotDetermined,NotProved,NotProved),("chain-direct",Proved,Proved,Proved)] $ \(name,t,r,k) -> do
    _ <- export name (chained t r k) []; pure ()
  _ <- export "P6-multiple" multipleRoutes []
  _ <- export "P7-skipped-guard" skippedGuard []
  let initial=synthetic Proved NotProved NotProved
      omitRebuttal initialDoc=let b=presumptionProofDocument initialDoc in initialDoc {presumptionProofDocument=b {documentAnalyses=[a {analysisAssessments=filter (/= "assessment:R") (analysisAssessments a)} | a <- documentAnalyses b]}}
      mapRegs f d=d {presumptionRegistrations=map f (presumptionRegistrations d)}
      mapBase f d=d {presumptionProofDocument=f (presumptionProofDocument d)}
      invalids=[("unknown-trigger",mapRegs (\r -> r {registeredTrigger=(registeredTrigger r) {registeredConditionLeaf=Just "unknown"}}) initial),
        ("unknown-rebuttal",mapRegs (\r -> r {registeredRebuttal=(registeredRebuttal r) {registeredConditionLeaf=Just "unknown"}}) initial),
        ("duplicate-registration",initial {presumptionRegistrations=presumptionRegistrations initial ++ presumptionRegistrations initial}),
        ("unsupported-burden",mapRegs (\r -> r {registeredTrigger=(registeredTrigger r) {registeredConditionKind="burden_shift"}}) initial),
        ("invalid-source",mapRegs (\r -> r {registeredSources=[SourceRef "unknown" Nothing]}) initial),
        ("invalid-span",mapRegs (\r -> r {registeredSources=[SourceRef "source:synthetic" (Just (TextSpan 0 9999 1 1 1 10000))]}) initial),
        ("wrong-scope",mapBase (\b -> b {documentAssessments=[a {assessmentScope=Scope "wrong" "wrong"} | a <- documentAssessments b]}) initial),
        ("mixed-profile",mapBase (\b -> b {documentFormat=linkedAuthoringFormat}) initial),("missing-rebuttal",omitRebuttal initial),
        ("unknown-target",initial {presumptionRegistrations=[r {registeredTarget="unknown"} | r <- presumptionRegistrations initial]}),
        ("cycle",initial {presumptionRegistrations=[r {registeredTrigger=(registeredTrigger r) {registeredConditionLeaf=Just "K"}} | r <- presumptionRegistrations initial]})]
  forM_ invalids $ \(name,invalid) -> do
    save (name <> ".invalid-document.json") invalid
    save (name <> ".diagnostics.json") (validatePresumptionAnalysis invalid "analysis:synthetic")
    check "invalid draft never evaluates" (case execute invalid of Left _ -> True; Right _ -> False)
  let unknown=case A.toJSON initial of A.Object o -> A.Object (KM.insert "burden_effect" (A.String "transfer") o); value -> value
  BS.writeFile (out </> "unknown-field.input.json") (encodeRecord unknown)
  case decodePresumptionDocument (encodeRecord unknown) of
    Left diagnostic -> save "unknown-field.diagnostic.json" diagnostic
    Right _ -> fail "unknown closed field accepted"
  draft <- required (projectPresumptionAuthored (omitRebuttal initial) "analysis:synthetic")
  BS.writeFile (out </> "draft.projection.json") =<< required (encodePresumptionProjection draft)
  doc <- required mdaDocument
  original <- export "mda18-active" doc ["source:mda18"]
  let revised=revise "R" Proved doc
  fresh <- export "mda18-rebutted" revised []
  oldProjection <- required (projectPresumptionEvaluation original)
  check "stale attachment rejected" (case projectPresumptionEvaluationOn revised original of Left _ -> True; Right _ -> False)
  source <- case filter ((/= Nothing) . referenceSpan) . presumptionFocusSources <$> inspectPresumptionTarget oldProjection "K" of
    Right (ref:_) -> required (recoverPresumptionSource oldProjection ref)
    _ -> fail "source not recoverable"
  check "exact original excerpt" (excerptText source == Just "Any person who is proved or presumed to have had a controlled drug in his or her possession is presumed, until the contrary is proved, to have known the nature of that drug.")
  save "mda18-source-recovery.json" source
  save "revision.json" (A.object ["originalSnapshot" A..= presumptionSnapshotId (presumptionEvaluationSnapshot original),
    "revisedSnapshot" A..= presumptionSnapshotId (presumptionEvaluationSnapshot fresh),
    "original" A..= presumptionEvaluationReport original,"revised" A..= presumptionEvaluationReport fresh])
  putStrLn "presumption consumer: P1–P5, four chains, skipped guard, MDA revision/replay/source recovery passed"
