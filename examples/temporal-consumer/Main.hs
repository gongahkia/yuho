{-# LANGUAGE OverloadedStrings #-}
module Main (main) where
import Control.Monad (forM_, unless)
import Data.Aeson (ToJSON, object, (.=))
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as T
import System.Directory (createDirectoryIfMissing)
import System.Environment (getArgs)
import System.FilePath ((</>))
import Yuho.Authoring
import TemporalExamples
required :: Show e => Either e a -> IO a
required=either (fail . show) pure
save :: ToJSON a => FilePath -> a -> IO ()
save path=BS.writeFile path . encodeRecord
check :: String -> Bool -> IO ()
check label value=unless value (fail label)
main :: IO ()
main=do
  args<-getArgs
  out<-case args of [path]->pure path; _->fail "usage: yuho-temporal-consumer OUTPUT_DIRECTORY"
  createDirectoryIfMissing True (out</>"data")
  let dataDir=out</>"data"
  BS.writeFile (dataDir</>"synthetic-authored.json") (encodeTemporalDocument syntheticTemporal)
  replay<-required (decodeTemporalDocument (encodeTemporalDocument syntheticTemporal))
  check "round trip" (replay==syntheticTemporal)
  statutory<-required section24Temporal
  BS.writeFile (dataDir</>"pc24-authored.json") (encodeTemporalDocument statutory)
  forM_ [("before","2023-12-31"),("boundary","2024-01-01"),("after","2024-01-02")] $ \(name,date)->export out ("synthetic-"<>name) syntheticTemporal date
  forM_ [("old","2019-12-31"),("new","2020-01-01")] $ \(name,date)->export out ("pc24-"<>name) statutory date
  let dates=[Nothing,Just "2019-12-31",Just "2020-01-01",Just "2023-12-31",Just "2024-01-01",Just "2024-01-02",Just "2040-02-29",Just "2023-02-29",Just "2024-02-29"]
  save (dataDir</>"boundary-matrix.json") [object ["conductDate".=date,"selection".=either (\e->object ["diagnostics".=e]) (\s->object ["expression".=temporalExpressionId (selectionExpression s)]) (selectTemporalExpression replay date)] | date<-dates]
  let negatives=[("gap",updateExpression "expr:old" (\e->e {temporalEffectiveTo=Just "2023-12-31"}) replay),
        ("overlap",updateExpression "expr:old" (\e->e {temporalEffectiveTo=Just "2024-01-02"}) replay),
        ("open-before-later",updateExpression "expr:old" (\e->e {temporalEffectiveTo=Nothing}) replay),
        ("duplicate",updateExpression "expr:new" (\e->e {temporalExpressionId="expr:old"}) replay)]
  forM_ negatives $ \(name,d)->do
    save (dataDir</>(name<>"-authored.json")) d
    let errors=validateTemporalDocument d
    check "invalid interval admitted" (not (null errors))
    save (dataDir</>(name<>"-diagnostics.json")) errors
  initial<-required (executeTemporal replay "2023-12-31")
  boundary<-required (executeTemporal replay "2024-01-01")
  within<-required (executeTemporal replay "2023-12-30")
  let intervalEdit=updateExpression "expr:old" (\e->e {temporalEffectiveTo=Just "2023-12-31"}) (updateExpression "expr:new" (\e->e {temporalEffectiveFrom="2023-12-31"}) replay)
      lawEdit=updateExpression "expr:old" (\e->let doc=temporalExpressionDocument e;l=documentLaw doc in e {temporalExpressionDocument=doc {documentLaw=l {lawNodes=[if nodeId n=="group" then n {nodeKind="any",nodeLabel="Hypothetical at least one required"} else n | n<-lawNodes l],lawRevision="hypothetical-revision"}}}) replay
  revisedInterval<-required (executeTemporal intervalEdit "2023-12-31")
  revisedLaw<-required (executeTemporal lawEdit "2023-12-31")
  BS.writeFile (dataDir</>"interval-revision-authored.json") (encodeTemporalDocument intervalEdit)
  BS.writeFile (dataDir</>"law-revision-authored.json") (encodeTemporalDocument lawEdit)
  expanded<-required (projectTemporalEvaluation initial)
  _<-required (temporalReferenceView expanded TemporalProvenanceView)
  let snapshot e=temporalSnapshotId (temporalEvaluationSnapshot e)
      stale d date=case projectTemporalEvaluationOn d (Just date) initial of Left _->True;Right _->False
      result=reportConclusion . evaluationReport . temporalEvaluationProof
  check "source expansion isolation" (snapshot initial==temporalSnapshotId (selectionSnapshot (temporalProjectionSelection (temporalProjectionData expanded))))
  check "stale attachment" (stale intervalEdit "2023-12-31" && stale lawEdit "2023-12-31" && stale replay "2024-01-01")
  check "same interval new temporal snapshot same proof snapshot" (snapshot initial/=snapshot within && evaluationSnapshot (temporalEvaluationProof initial)==evaluationSnapshot (temporalEvaluationProof within))
  check "versions incompatible" (case compareAnalyses (temporalEvaluationProof initial) (temporalEvaluationProof boundary) of Left _->True;Right _->False)
  save (dataDir</>"revision-lifecycle.json") (object ["initial".=temporalEvaluationSelection initial,"acrossBoundary".=temporalEvaluationSelection boundary,"withinInterval".=temporalEvaluationSelection within,"intervalRevision".=temporalEvaluationSelection revisedInterval,"lawRevision".=temporalEvaluationSelection revisedLaw,"outcomes".=map result [initial,boundary,within,revisedInterval,revisedLaw],"sourceExpansionSnapshotUnchanged".=True,"staleAttachmentRejected".=True,"crossVersionComparisonRejected".=True])
  putStrLn "temporal consumer: round trip, five exports, boundary matrix, revisions, source recovery and stale attachment passed"
export :: FilePath -> String -> TemporalDocument -> Text -> IO ()
export out name d date=do
  compiled<-required (compileTemporalAnalysis d (Just date))
  e<-required (evaluateTemporalAnalysis compiled)
  p<-required (projectTemporalEvaluation e)
  let path suffix=out</>name<>suffix; dataPath suffix=out</>"data"</>name<>suffix
  save (dataPath "-selection.json") (temporalEvaluationSelection e)
  save (dataPath "-application-report.json") (evaluationReport (temporalEvaluationProof e))
  BS.writeFile (dataPath "-kernel-request.json") (compiledRequest (temporalProofCompilation compiled))
  BS.writeFile (dataPath "-kernel-result.json") (evaluationKernelResponse (temporalEvaluationProof e))
  required (encodeTemporalProjection p) >>= BS.writeFile (dataPath "-projection.json")
  forM_ [("selection",TemporalSetView),("provenance",TemporalProvenanceView)] $ \(viewName,mode)->do
    v<-required (temporalReferenceView p mode)
    save (dataPath ("-"<>viewName<>"-bindings.json")) v
    required (encodeTemporalViewJson p v) >>= BS.writeFile (dataPath ("-"<>viewName<>"-view.json"))
    required (encodeTemporalViewXml p v) >>= BS.writeFile (path ("-"<>viewName<>".xml"))
    required (encodeTemporalViewSvg p v) >>= BS.writeFile (path ("-"<>viewName<>".svg"))
  let proof=temporalSelectedProjection p
  lawView<-required (lawOccurrenceView proof)
  save (dataPath "-law-bindings.json") lawView
  required (encodeProjection proof) >>= BS.writeFile (dataPath "-selected-law-projection.json")
  required (encodeProjectionLegacyJson proof) >>= BS.writeFile (dataPath "-law-view.json")
  required (encodeProjectionLegacyXml proof) >>= BS.writeFile (path "-law.xml")
  required (encodeProjectionSvg proof) >>= BS.writeFile (path "-law.svg")
  excerpts<-mapM (required . recoverTemporalSource d) (temporalExpressionSources (selectionExpression (temporalEvaluationSelection e))++temporalDateSources (selectionExpression (temporalEvaluationSelection e)))
  save (dataPath "-source-recovery.json") excerpts
  putStrLn (name<>" "<>T.unpack date<>" -> "<>T.unpack (temporalExpressionId (selectionExpression (temporalEvaluationSelection e)))<>" "<>T.unpack (reportConclusion (evaluationReport (temporalEvaluationProof e))))
