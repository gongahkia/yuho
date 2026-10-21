{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Temporal.Run
  ( encodeTemporalDocument, decodeTemporalDocument, validateTemporalDocument
  , selectTemporalExpression, TemporalCompilation, compileTemporalAnalysis
  , temporalCompiledSelection, temporalProofCompilation
  , TemporalEvaluation, evaluateTemporalAnalysis, temporalEvaluationSelection
  , temporalEvaluationProof, temporalEvaluationSnapshot, temporalEvaluationCompilation
  , recoverTemporalSource ) where
import qualified Data.Aeson as A
import qualified Data.ByteString as BS
import Data.List (group, sort)
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Compile
import Yuho.Authoring.Report
import Yuho.Authoring.Snapshot (makeSnapshot)
import Yuho.Authoring.Types
import Yuho.Authoring.Temporal.Types
import Yuho.Authoring.Validate (issue, findAnalysis, validateDocument)
import Yuho.Authoring.Projection.Inspect (OriginalSourceExcerpt, recoverSourceReference)
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Protocol.Json (J(..), decodeJson, lookupField)
import qualified Yuho.Temporal.Interval as I

encodeTemporalDocument :: TemporalDocument -> BS.ByteString
encodeTemporalDocument = encodeRecord
decodeTemporalDocument :: BS.ByteString -> Either AuthoringDiagnostic TemporalDocument
decodeTemporalDocument bytes = do
  wire <- either (Left . issue "TAJSON" "/" []) Right (decodeJson bytes)
  case lookupField "temporalDocumentFormat" wire of
    Just (JStr v) | v == temporalAuthoringFormat -> pure ()
    _ -> Left (issue "TAVERSION" "/temporalDocumentFormat" [] "expected explicit v0.5 temporal wrapper")
  either (Left . issue "TAJSON" "/" [] . T.pack) Right (A.eitherDecodeStrict' bytes)

interval :: TemporalExpression -> Either [AuthoringDiagnostic] (I.Interval TemporalExpression)
interval e = do
  from <- date "/temporalEffectiveFrom" (temporalEffectiveFrom e)
  to <- traverse (date "/temporalEffectiveTo") (temporalEffectiveTo e)
  if maybe False (<= from) to then Left [err "TAINTERVAL" "effective interval must end after it starts"]
    else Right (I.Interval e from to)
  where
    err code message = issue code "/temporalExpressions" [temporalExpressionId e] message
    date path value = maybe (Left [issue "TADATE" ("/temporalExpressions/" <> temporalExpressionId e <> path) [temporalExpressionId e] "invalid ISO calendar date"]) Right (I.parseDate value)

validateTemporalDocument :: TemporalDocument -> [AuthoringDiagnostic]
validateTemporalDocument d = version ++ ids ++ limits ++ concatMap source sources ++ concatMap expression es ++ intervals
  where
    es=temporalExpressions d; sources=temporalSources d
    named=temporalDocumentId d:temporalWorkId d:map temporalExpressionId es ++ map sourceId sources
    version=[issue "TAVERSION" "/temporalDocumentFormat" [] "expected v0.5 temporal wrapper" | temporalDocumentFormat d /= temporalAuthoringFormat]
    ids=[issue "TAID" "/" [key] "identity must contain 1..128 UTF-8 bytes" | key <- named,T.null (T.strip key) || BS.length (UTF8.encodeUtf8 key)>128]
      ++ [issue "TADUPLICATE" "/temporalExpressions" [key] "duplicate temporal wrapper identity" | (key:_:_) <- group (sort named)]
    limits=[issue "TALIMIT" "/" [temporalDocumentId d] "temporal document exceeds one MiB, 64 expressions or 4096 wrapper identities" | BS.length (encodeRecord d)>1048576 || length es>64 || length named>4096]
    source s = [issue "TASOURCE" "/temporalSources" [sourceId s] "source kind required" | T.null (T.strip (sourceKind s))]
    refs owner rs=concat [either (map (\x -> x {diagnosticLocation="/temporalExpressions/"<>owner,diagnosticObjects=owner:diagnosticObjects x})) (const []) (recoverSourceReference sources r) | r <- rs]
    expression e = let doc=temporalExpressionDocument e; key=temporalExpressionId e in
      [issue "TAPROFILE" "/temporalExpressionDocument/documentFormat" [key,documentId doc] "temporal candidates must be complete v0.1 proof documents; linked, typed, presumption and nested temporal profiles are unsupported" | documentFormat doc /= authoringFormat]
      ++ [x {diagnosticLocation="/temporalExpressions/"<>key<>"/temporalExpressionDocument"<>diagnosticLocation x,diagnosticObjects=key:diagnosticObjects x} | x <- validateDocument doc]
      ++ [issue "TAANALYSIS" "/temporalExpressionAnalysis" [key,temporalExpressionAnalysis e] "selected underlying analysis not found" | findAnalysis doc (temporalExpressionAnalysis e)==Nothing]
      ++ [issue "TAMETADATA" "/temporalExpressionVersion" [key] "nonempty authored version (at most 128 UTF-8 bytes) required" | T.null (T.strip (temporalExpressionVersion e)) || BS.length (UTF8.encodeUtf8 (temporalExpressionVersion e))>128]
      ++ [issue "TAMETADATA" "/temporalSupersedes" [key] "supersedes is descriptive but must be a nonempty bounded identity" | Just x <- [temporalSupersedes e],T.null (T.strip x) || BS.length (UTF8.encodeUtf8 x)>128]
      ++ refs key (temporalExpressionSources e ++ temporalDateSources e)
    intervals=[issue "TAINTERVAL" "/temporalExpressions" [temporalDocumentId d] "temporal model requires at least two complete expressions" | length es<2]
      ++ case traverse interval es of
        Left errors -> errors
        Right xs -> case I.intervalProblem (I.orderIntervals xs) of
          Nothing -> []
          Just (e,message) -> [issue "TAINTERVAL" "/temporalExpressions" [temporalExpressionId e] message]

-- | Pure selection, no compilation/evaluation and no assessment defaulting.
-- Reference date remains an independent proof-policy input; it is not overwritten.
selectTemporalExpression :: TemporalDocument -> Maybe Text -> Either [AuthoringDiagnostic] TemporalSelection
selectTemporalExpression d supplied = do
  case validateTemporalDocument d of [] -> pure (); errors -> Left errors
  text <- maybe (Left [issue "TACONDUCT" "/conductDate" [temporalDocumentId d] "explicit conduct date required"]) Right supplied
  day <- maybe (Left [issue "TADATE" "/conductDate" [temporalDocumentId d] "invalid ISO conduct date"]) Right (I.parseDate text)
  xs <- traverse interval (temporalExpressions d)
  e <- case I.matchIntervals day (I.orderIntervals xs) of
    [x] -> Right x
    [] -> Left [issue "TANOMATCH" "/conductDate" [temporalDocumentId d] "conduct-date falls in no authored effective interval"]
    _ -> Left [issue "TAAMBIGUOUS" "/conductDate" [temporalDocumentId d] "conduct-date matches multiple authored effective intervals"]
  let doc=temporalExpressionDocument e
  a <- maybe (Left [issue "TAANALYSIS" "/temporalExpressionAnalysis" [temporalExpressionId e] "analysis not found"]) Right (findAnalysis doc (temporalExpressionAnalysis e))
  let snapshot=TemporalSnapshot (sha256Text (encodeRecord (d,text,temporalExpressionId e,evaluatorProfile))) d text (temporalExpressionId e)
  pure (TemporalSelection (temporalDocumentId d) (temporalWorkId d) text e snapshot a (snapshotId (makeSnapshot doc a)) Nothing
    "Technical authored-interval matching only; not legal applicability, commencement verification, savings analysis or current-law selection. Analysis reference date is retained separately as proof policy.")

data TemporalCompilation = TemporalCompilation TemporalSelection CompiledAnalysis
temporalCompiledSelection :: TemporalCompilation -> TemporalSelection
temporalCompiledSelection (TemporalCompilation x _) = x
temporalProofCompilation :: TemporalCompilation -> CompiledAnalysis
temporalProofCompilation (TemporalCompilation _ x) = x
compileTemporalAnalysis :: TemporalDocument -> Maybe Text -> Either [AuthoringDiagnostic] TemporalCompilation
compileTemporalAnalysis d date = do
  selected <- selectTemporalExpression d date
  let e=selectionExpression selected
  compiled <- compileAnalysis (temporalExpressionDocument e) (temporalExpressionAnalysis e)
  pure (TemporalCompilation selected {selectionCompilation=Just (sha256Text (compiledRequest compiled))} compiled)
data TemporalEvaluation = TemporalEvaluation TemporalCompilation Evaluation
temporalEvaluationCompilation :: TemporalEvaluation -> TemporalCompilation
temporalEvaluationCompilation (TemporalEvaluation x _) = x
temporalEvaluationSelection :: TemporalEvaluation -> TemporalSelection
temporalEvaluationSelection = temporalCompiledSelection . temporalEvaluationCompilation
temporalEvaluationSnapshot :: TemporalEvaluation -> TemporalSnapshot
temporalEvaluationSnapshot = selectionSnapshot . temporalEvaluationSelection
temporalEvaluationProof :: TemporalEvaluation -> Evaluation
temporalEvaluationProof (TemporalEvaluation _ x) = x
evaluateTemporalAnalysis :: TemporalCompilation -> Either [AuthoringDiagnostic] TemporalEvaluation
evaluateTemporalAnalysis c = TemporalEvaluation c <$> evaluateAnalysis (temporalProofCompilation c)
recoverTemporalSource :: TemporalDocument -> SourceRef -> Either [AuthoringDiagnostic] OriginalSourceExcerpt
recoverTemporalSource d = recoverSourceReference (temporalSources d)
