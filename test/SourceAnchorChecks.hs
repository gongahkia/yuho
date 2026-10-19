{-# LANGUAGE OverloadedStrings #-}
module SourceAnchorChecks (runSourceAnchorChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import CaseApplication
import Hurt
import SourceAnchors
import Yuho.Authoring
import qualified Yuho.Core.Types as Core
import Yuho.Core.Source (validateSpan)
import Yuho.Authoring.Validate (toCoreSpan)

runSourceAnchorChecks :: IO ()
runSourceAnchorChecks = do
  forM_ anchorExamples $ \example -> do
    let source = exampleSource (exampleText example)
        (a,b) = exampleBytes example
        (c,d) = exampleCodePoints example
    bytes <- require (sourceAnchorBytes source a b)
    points <- require (sourceAnchorCodePoints source c d)
    check ("independent numeric expectation " <> Text.unpack (exampleName example))
      (bytes == SourceRef (sourceId source) (Just (exampleExpected example)) && points == bytes)
    let content = exampleText example
        raw = Encoding.encodeUtf8 content
        expected = exampleExpected example
    check "existing core coordinates and independent literal excerpt"
      (validateSpan (Core.Source "original" content raw "") (toCoreSpan expected)
        && Encoding.decodeUtf8 (BS.take (end expected-start expected) (BS.drop (start expected) raw)) == exampleExcerpt example)
  forM_ invalidAnchorExamples $ \example -> check (Text.unpack (invalidName example))
    (case constructInvalid example of
      Left ds -> any (\d -> diagnosticCode d == invalidExpectedCode example
        && sourceId (invalidSource example) `elem` diagnosticObjects d) ds
      Right _ -> False)
  -- Keep exported byteSpan's historical coordinate-only behaviour, including
  -- invalid offsets; only the new original-source constructors validate ranges.
  check "byteSpan contract preserved"
    (byteSpan "é猫\nx" 2 5 == TextSpan 2 5 1 3 1 6
      && byteSpan "x" (-1) 99 == TextSpan (-1) 99 1 1 1 2)
  cheatingAnchor <- require caseNoteAnchor
  hurtAnchor <- require hurtNoteAnchor
  check "consumer anchors identical to retained stored references"
    (cheatingAnchor == SourceRef "source:case-note" (Just (TextSpan 6 15 1 7 1 16))
      && hurtAnchor == SourceRef "source:hurt-note" (Just (TextSpan 11 60 1 12 1 61)))
  forM_ [(caseDocument cheatingAnchor,"analysis:cheating",cheatingAnchor,"猫 item."),
         (hurtDocument hurtAnchor,hurtAnalysis,hurtAnchor,"Mei reports pain (痛) in her arm after the push.")] $ \(doc,key,ref,excerpt) -> do
    decoded <- require (decodeDocument (encodeDocument doc))
    check "validated-anchor document round-trip" (doc == decoded && analysisReady (validateAnalysis doc key))
    result <- require (compileAnalysis decoded key >>= evaluateAnalysis)
    projection <- require (projectEvaluation result)
    original <- require (recoverOriginalSource projection ref)
    check "consumer exact recovered original" (excerptText original == Just excerpt)
  revision hurtAnchor
  putStrLn "source anchors: 14 literal coordinate/excerpt cases, 14 refusals, identical consumer anchors, source replacement and snapshot boundaries passed"

revision :: SourceRef -> IO ()
revision fixtureAnchor = do
  let source = exampleSource "é猫\nx"
      base = hurtDocument fixtureAnchor
  ref <- require (sourceAnchorCodePoints source 1 2)
  oldDoc <- require (editCaseAssertion "assertion:pain" (\a -> a {assertionSources=assertionSources a ++ [ref]})
    (base {documentSources=source:documentSources base}))
  old <- require (compileAnalysis oldDoc hurtAnalysis >>= evaluateAnalysis)
  oldP <- require (projectEvaluation old)
  let replace content = oldDoc {documentSources=[if sourceId s == sourceId source then s {sourceText=Just content} else s
        | s <- documentSources oldDoc]}
      sameLength = replace "é犬\nx"
      shifted = replace "!é猫\nx"
  new <- require (compileAnalysis sameLength hurtAnalysis >>= evaluateAnalysis)
  newP <- require (projectEvaluation new)
  before <- require (recoverOriginalSource oldP ref)
  after <- require (recoverOriginalSource newP ref)
  check "same-length replacement is structurally valid, changes excerpt, preserves previous snapshot"
    (null (validateDocument sameLength) && excerptText before == Just "猫" && excerptText after == Just "犬"
      && snapshotDocument (evaluationSnapshot old) == oldDoc
      && map assertionSources (documentAssertions oldDoc) == map assertionSources (documentAssertions sameLength))
  check "stale source attachment rejected" (case projectEvaluationOn sameLength old of
    Left ds -> any ((== "PSTALE") . diagnosticCode) ds; Right _ -> False)
  check "source shifts do not relocate references"
    (any (\d -> diagnosticCode d == "ASPAN" && "assertion:pain" `elem` diagnosticObjects d) (validateDocument shifted)
      && case compileAnalysis shifted hurtAnalysis of Left _ -> True; Right _ -> False)
  rebuilt <- require (sourceAnchorCodePoints (source {sourceText=Just "!é猫\nx"}) 2 3)
  check "explicit new selection required after shift" (referenceSpan rebuilt == Just (TextSpan 3 6 1 4 1 7))
  comparison <- require (compareAnalyses old new)
  check "source revision alone is not a computed legal change"
    (null (comparisonChanged comparison) && any changeReferencedMaterial (comparisonAssessments comparison)
      && not (comparisonConclusionChanged comparison))
  let duplicate = oldDoc {documentSources=source:documentSources oldDoc}
  check "local anchor validity does not establish document identities"
    (any ((== "ADUPLICATE") . diagnosticCode) (validateDocument duplicate))

require :: Show a => Either a b -> IO b
require = either (fail . show) pure

check :: String -> Bool -> IO ()
check label value = unless value (fail ("source anchors: " <> label))
