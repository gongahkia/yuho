{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Navigation through original authorship. No evidence or legal inference.
module Yuho.Authoring.Projection.Inspect
  ( AssertionLinks(..), AssessmentApplication(..), AssessmentInspection(..)
  , OriginalSourceExcerpt(..), caseAssertionLinks, inspectAssessment
  , recoverOriginalSource ) where

import Data.Aeson (ToJSON(..), genericToJSON)
import qualified Data.ByteString as BS
import Data.List (find, nub)
import Data.Maybe (mapMaybe)
import Data.Text (Text)
import qualified Data.Text.Encoding as Encoding
import GHC.Generics (Generic)
import Yuho.Authoring.Projection
import Yuho.Authoring.Types
import Yuho.Authoring.Validate (issue, toCoreSpan)
import Yuho.Core.Source (validateSpan)
import qualified Yuho.Core.Types as Core

data AssertionLinks = AssertionLinks
  { linkedAssertion :: Text, linkedAssessments :: [Text]
  , linkedSelectedAssessments :: [Text]
  } deriving (Eq, Show, Generic)

data OriginalSourceExcerpt = OriginalSourceExcerpt
  { excerptSource :: SourceRecord, excerptReference :: SourceRef
  , excerptState :: Text, excerptText :: Maybe Text
  } deriving (Eq, Show, Generic)

data AssessmentApplication = AssessmentApplication
  { applicationOccurrence :: Text, applicationSelected :: Bool
  , applicationObservation :: Maybe Text, applicationEvaluation :: Text
  , applicationComputed :: Maybe Text, applicationSkipReason :: Maybe Text
  } deriving (Eq, Show, Generic)

data AssessmentInspection = AssessmentInspection
  { inspectionSnapshot :: Text, inspectionProjectedAssessment :: Text
  , inspectionAssessment :: Assessment, inspectionSelected :: Bool
  , inspectionResolution :: ProjectionResolution
  , inspectionApplications :: [AssessmentApplication]
  , inspectionOriginalSources :: [OriginalSourceExcerpt]
  } deriving (Eq, Show, Generic)

caseAssertionLinks :: Projection -> Text -> Either [AuthoringDiagnostic] AssertionLinks
caseAssertionLinks projection key = do
  let snapshot = projectionSnapshot (projectionData projection)
      doc = snapshotDocument snapshot
      selected = analysisAssessments (snapshotAnalysis snapshot)
  case find ((== key) . assertionId) (documentAssertions doc) of
    Nothing -> Left [issue "PASSERTION" "/documentAssertions" [key] "case assertion not found"]
    Just _ -> let allLinks = [assessmentId a | a <- documentAssessments doc,
                    elem key (assessmentAssertions a)]
              in Right (AssertionLinks key allLinks (filter (\a -> elem a selected) allLinks))

-- | A missing anchor is never converted into an invented original location.
-- Arbitrary caller-supplied anchors are checked with the existing UTF-8 rules.
recoverOriginalSource :: Projection -> SourceRef -> Either [AuthoringDiagnostic] OriginalSourceExcerpt
recoverOriginalSource projection ref = do
  let doc = snapshotDocument (projectionSnapshot (projectionData projection))
      invalid message = Left [issue "PSOURCE" "/originalSourceReference" [referenceSource ref] message]
  source <- maybe (invalid "original source does not exist") Right
    (find ((== referenceSource ref) . sourceId) (documentSources doc))
  case (sourceText source, referenceSpan ref) of
    (Just content, Just anchor) ->
      let bytes = Encoding.encodeUtf8 content
      in if validateSpan (Core.Source "original" content bytes "") (toCoreSpan anchor)
         then case Encoding.decodeUtf8' (BS.take (end anchor - start anchor) (BS.drop (start anchor) bytes)) of
           Right excerpt -> Right (OriginalSourceExcerpt source ref "anchored" (Just excerpt))
           Left _ -> invalid "anchor does not delimit UTF-8 text"
         else invalid "invalid original UTF-8 anchor"
    (Nothing, Just _) -> invalid "an original anchor requires retained source text"
    (Just _, Nothing) -> Right (OriginalSourceExcerpt source ref "retained_unanchored" Nothing)
    (Nothing, Nothing) -> Right (OriginalSourceExcerpt source ref
      (maybe "reference_only" (const "locator_only") (sourceLocator source)) Nothing)

inspectAssessment :: Projection -> Text -> Either [AuthoringDiagnostic] AssessmentInspection
inspectAssessment projection key = do
  let value = projectionData projection
      snapshot = projectionSnapshot value
      doc = snapshotDocument snapshot
      analysis = snapshotAnalysis snapshot
  assessment <- maybe (Left [issue "PASSESSMENT" "/documentAssessments" [key] "assessment not found"]) Right
    (find ((== key) . assessmentId) (documentAssessments doc))
  resolution <- maybe (Left [issue "PRESOLVE" "/projectionNodes" [key] "assessment handle missing"]) Right
    (resolveProjectedObject projection (objectProjectionId key))
  let targetNodes = [n | n <- projectionNodes value, Just o <- [projectedNodeOccurrence n],
        occurrenceAuthoredNode o == assessmentInput assessment,
        occurrenceScope o == assessmentScope assessment]
      application n =
        let active = (projectedNodeBinding n >>= bindingAssessment) == Just key
        in AssessmentApplication (projectedNodeId n) active
          (if active then observationProjectionId <$> projectedNodeObservation n else Nothing)
          (if active then projectedNodeEvaluation n else "not_applicable")
          (if active then projectedNodeComputed n else Nothing)
          (if active then projectedNodeSkipReason n else Nothing)
      refs = nub (assessmentSources assessment ++ concatMap assertionSources
        [a | a <- documentAssertions doc, elem (assertionId a) (assessmentAssertions assessment)])
      target = [n | n <- lawNodes (documentLaw doc), nodeId n == assessmentInput assessment]
      kernelIds = mapMaybe (\n -> projectedNodeObservation n >>= observationOriginalKernelId)
        [n | n <- targetNodes, (projectedNodeBinding n >>= bindingAssessment) == Just key]
      mappings = maybe [] (filter (\m -> elem (sourceMappingKernelId m) kernelIds
        || elem key (sourceMappingObjects m)) . projectionGeneratedSpans) (projectionCompiler value)
      resolved = resolution {resolvedLawNodes = target, resolvedGeneratedSpans = mappings,
        resolvedAuthoredIds = nub (resolvedAuthoredIds resolution ++ map nodeId target)}
  sources <- traverse (recoverOriginalSource projection) refs
  pure (AssessmentInspection (snapshotId snapshot) (objectProjectionId key) assessment
    (elem key (analysisAssessments analysis)) resolved (map application targetNodes) sources)

instance ToJSON AssertionLinks where toJSON = genericToJSON jsonOptions
instance ToJSON OriginalSourceExcerpt where toJSON = genericToJSON jsonOptions
instance ToJSON AssessmentApplication where toJSON = genericToJSON jsonOptions
instance ToJSON AssessmentInspection where toJSON = genericToJSON jsonOptions
