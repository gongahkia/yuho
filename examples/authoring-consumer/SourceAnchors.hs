{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module SourceAnchors
  ( AnchorExample(..), InvalidAnchorExample(..), anchorExamples, invalidAnchorExamples
  , exampleSource, constructInvalid, runSourceAnchorsConsumer ) where

import Control.Monad (forM, unless)
import Data.Aeson (ToJSON)
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import GHC.Generics (Generic)
import System.Directory (createDirectoryIfMissing)
import System.FilePath ((</>))
import Hurt
import Yuho.Authoring

-- Handwritten numeric expectations, independent of either constructor.
data AnchorExample = AnchorExample
  { exampleName :: Text, exampleText :: Text
  , exampleBytes :: (Integer,Integer), exampleCodePoints :: (Integer,Integer)
  , exampleExpected :: TextSpan, exampleExcerpt :: Text }
  deriving (Eq, Show, Generic)
instance ToJSON AnchorExample

anchorExamples :: [AnchorExample]
anchorExamples =
  [AnchorExample "ASCII" "abc" (1,3) (1,3) (TextSpan 1 3 1 2 1 4) "bc",
   AnchorExample "multibyte" "é猫\nx" (2,5) (1,2) (TextSpan 2 5 1 3 1 6) "猫",
   AnchorExample "cheating-note" "Note: 猫 item.\nDelivery reported." (6,15) (6,13) (TextSpan 6 15 1 7 1 16) "猫 item.",
   AnchorExample "hurt-note" "Synthetic: Mei reports pain (痛) in her arm after the push." (11,60) (11,58)
     (TextSpan 11 60 1 12 1 61) "Mei reports pain (痛) in her arm after the push.",
   AnchorExample "four-byte" "A😀B" (1,5) (1,2) (TextSpan 1 5 1 2 1 6) "😀",
   AnchorExample "multiline" "é猫\nx" (2,7) (1,4) (TextSpan 2 7 1 3 2 2) "猫\nx",
   AnchorExample "LF" "a\n猫" (1,2) (1,2) (TextSpan 1 2 1 2 2 1) "\n",
   AnchorExample "CRLF" "a\r\n猫" (1,3) (1,3) (TextSpan 1 3 1 2 2 1) "\r\n",
   AnchorExample "CR-is-byte" "a\r\n猫" (1,2) (1,2) (TextSpan 1 2 1 2 1 3) "\r",
   AnchorExample "after-CRLF" "a\r\n猫" (3,6) (3,4) (TextSpan 3 6 2 1 2 4) "猫",
   AnchorExample "combining-code-point" "e\x0301" (1,3) (1,2) (TextSpan 1 3 1 2 1 4) "\x0301",
   AnchorExample "empty-start" "é猫\nx" (0,0) (0,0) (TextSpan 0 0 1 1 1 1) "",
   AnchorExample "empty-EOF" "é猫\nx" (7,7) (4,4) (TextSpan 7 7 2 2 2 2) "",
   AnchorExample "empty-source" "" (0,0) (0,0) (TextSpan 0 0 1 1 1 1) ""]

data InvalidAnchorExample = InvalidAnchorExample
  { invalidName :: Text, invalidSource :: SourceRecord, invalidUnits :: Text
  , invalidRange :: (Integer,Integer), invalidExpectedCode :: Text }
  deriving (Eq, Show, Generic)
instance ToJSON InvalidAnchorExample

exampleSource :: Text -> SourceRecord
exampleSource content = SourceRecord "source:anchor-example" "synthetic" (Just "explicit retained anchor example") (Just content)

invalidAnchorExamples :: [InvalidAnchorExample]
invalidAnchorExamples = [bad label "bytes" range code | (label,range,code) <-
  [("negative-start",(-1,2),"AANCHORRANGE"),("negative-end",(0,-1),"AANCHORRANGE"),
   ("reversed",(5,2),"AANCHORRANGE"),("past-EOF",(0,8),"AANCHORRANGE"),
   ("start-past-EOF",(8,8),"AANCHORRANGE"),("inside-é",(1,2),"AANCHORBOUNDARY"),
   ("inside-猫",(2,4),"AANCHORBOUNDARY"),("huge-byte-offset",(0,10^(100::Int)),"AANCHORRANGE")]] ++
  [bad label "code_points" range "AANCHORRANGE" | (label,range) <-
    [("negative-code-point",(-1,2)),("reversed-code-points",(2,1)),
     ("past-code-point-EOF",(0,5)),("huge-code-point-offset",(10^(100::Int),10^(100::Int)))]] ++
  [InvalidAnchorExample "locator-only" (SourceRecord "source:locator" "other" (Just "locator only") Nothing)
      units (0,0) "AANCHORTEXT" | units <- ["bytes","code_points"]]
  where bad label units range code = InvalidAnchorExample label (exampleSource "é猫\nx") units range code

constructInvalid :: InvalidAnchorExample -> Either [AuthoringDiagnostic] SourceRef
constructInvalid example = let (first,lastOffset) = invalidRange example in
  (if invalidUnits example == "bytes" then sourceAnchorBytes else sourceAnchorCodePoints)
    (invalidSource example) first lastOffset

data AnchorOutcome = AnchorOutcome
  { anchorInput :: AnchorExample, byteReference :: SourceRef, codePointReference :: SourceRef
  , recoveredOriginal :: OriginalSourceExcerpt }
  deriving (Show, Generic)
instance ToJSON AnchorOutcome

runSourceAnchorsConsumer :: [String] -> IO ()
runSourceAnchorsConsumer args = do
  output <- case args of
    [] -> pure Nothing
    ["--artifacts",path] -> pure (Just path)
    _ -> fail "usage: yuho-authoring-consumer --anchors-demo [--artifacts DIRECTORY]"
  fixtureAnchor <- require hurtNoteAnchor
  let base = hurtDocument fixtureAnchor
      attach source ref = editCaseAssertion "assertion:pain"
        (\a -> a {assertionSources=assertionSources a ++ [ref]})
        (base {documentSources=documentSources base ++ [source]})
  successes <- forM anchorExamples $ \example -> do
    let source = exampleSource (exampleText example)
        (first,lastOffset) = exampleBytes example
        (pointFirst,pointLast) = exampleCodePoints example
    -- Construct before a document or projection is involved.
    bytes <- require (sourceAnchorBytes source first lastOffset)
    points <- require (sourceAnchorCodePoints source pointFirst pointLast)
    unless (bytes == points && referenceSpan bytes == Just (exampleExpected example))
      (fail ("anchor numeric expectation failed: " <> Text.unpack (exampleName example)))
    doc <- require (attach source bytes)
    projection <- require (projectAuthored doc hurtAnalysis)
    recovered <- require (recoverOriginalSource projection bytes)
    unless (excerptText recovered == Just (exampleExcerpt example)) (fail "anchor excerpt mismatch")
    pure (AnchorOutcome example bytes points recovered)
  failures <- forM invalidAnchorExamples $ \example -> case constructInvalid example of
    Right _ -> fail ("invalid anchor accepted: " <> Text.unpack (invalidName example))
    Left diagnostics -> pure (example,diagnostics)
  let source = exampleSource "é猫\nx"
  ref <- require (sourceAnchorCodePoints source 1 2)
  oldDoc <- require (attach source ref)
  old <- run oldDoc
  oldProjection <- require (projectEvaluation old)
  let replacement = source {sourceText=Just "é犬\nx"}
      revise s = oldDoc {documentSources=[if sourceId x == sourceId s then s else x | x <- documentSources oldDoc]}
      newDoc = revise replacement
      shiftedDoc = revise (source {sourceText=Just "!é猫\nx"})
  new <- run newDoc
  newProjection <- require (projectEvaluation new)
  oldExcerpt <- require (recoverOriginalSource oldProjection ref)
  newExcerpt <- require (recoverOriginalSource newProjection ref)
  stale <- case projectEvaluationOn newDoc old of Left ds -> pure ds; Right _ -> fail "stale source snapshot accepted"
  shifted <- case compileAnalysis shiftedDoc hurtAnalysis of Left ds -> pure ds; Right _ -> fail "shifted invalid anchor accepted"
  comparison <- require (projectComparison old new)
  unless (null (projectedChangedObservations comparison)
    && oldExcerpt /= newExcerpt && assertionRefs oldDoc == assertionRefs newDoc)
    (fail "source replacement did not preserve the intended boundary")
  oldView <- require (applicationView oldProjection (FocusAssessments [hurtAssessmentId "f:hurt-caused" Proved]))
  newView <- require (applicationView newProjection (FocusAssessments [hurtAssessmentId "f:hurt-caused" Proved]))
  views <- (++) <$> viewFiles "source-before" oldProjection oldView <*> viewFiles "source-replaced" newProjection newView
  let records = views ++
        [("anchors-success.json",encodeRecord successes),("anchors-invalid.json",encodeRecord failures),
         ("source-before.document.json",encodeDocument oldDoc),("source-replaced.document.json",encodeDocument newDoc),
         ("source-shifted.document.json",encodeDocument shiftedDoc),
         ("source-before.application.json",encodeRecord (evaluationReport old)),
         ("source-replaced.application.json",encodeRecord (evaluationReport new)),
         ("source-revision.comparison.json",encodeRecord comparison),
         ("source-revision-excerpts.json",encodeRecord (oldExcerpt,newExcerpt)),
         ("source-stale-diagnostics.json",encodeRecord stale),("source-shifted-diagnostics.json",encodeRecord shifted),
         ("INDEX.md",Encoding.encodeUtf8 index)]
  case output of
    Nothing -> pure ()
    Just path -> do
      createDirectoryIfMissing True path
      mapM_ (\(name,bytes) -> BS.writeFile (path </> name) bytes) records
  putStrLn "anchors: 14 independently specified coordinate cases, 14 invalid requests; old excerpt 猫, replacement 犬; no automatic relocation"
  where
    run doc = require (compileAnalysis doc hurtAnalysis >>= evaluateAnalysis)
    assertionRefs doc = [(assertionId a,assertionSources a) | a <- documentAssertions doc]

viewFiles :: String -> Projection -> ProjectionView -> IO [(FilePath,BS.ByteString)]
viewFiles name projection view = do
  complete <- require (encodeProjection projection)
  svg <- require (encodeViewSvg projection view)
  json <- require (encodeViewJson projection view)
  xml <- require (encodeViewXml projection view)
  pure [(name <> ".projection.json",complete),(name <> ".view-bindings.json",encodeRecord view),
    (name <> ".svg",svg),(name <> ".view.json",json),(name <> ".view.xml",xml)]

index :: Text
index = Text.unlines ["# Original-source anchors", "",
  "anchors-success.json: literal input/expected coordinates, actual byte/code-point references and recovered original excerpts.",
  "anchors-invalid.json: invalid ranges and source-linked diagnostics, including enormous Integer offsets and locator-only sources.",
  "source-before.svg / source-replaced.svg: original 猫 and same-length replacement 犬, with complete projections and view bindings.",
  "source-revision-excerpts.json: each projection retains its own source; unchanged references select different text after replacement.",
  "source-stale-diagnostics.json: old evaluation cannot annotate the revised source snapshot.",
  "source-shifted-diagnostics.json: prefix insertion leaves references unchanged and invalid here; no automatic reanchoring.",
  "This validates coordinate structure in supplied text, not quotation identity, reliability, legal meaning or document-wide validity."]

require :: Show a => Either a b -> IO b
require = either (fail . show) pure
