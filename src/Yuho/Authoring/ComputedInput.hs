{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | One explicit, snapshot-pinned, technical dependency. Never edits source authorship.
module Yuho.Authoring.ComputedInput
  ( computedInputFormat, computedStatusMapping
  , ComputedDestination(..), ComputedStatusPolicy(..), ComputedInputBinding(..), ComputedInputDocument(..)
  , proofInputDestination, presumptionInputDestination, makeComputedInputBinding
  , encodeComputedInputDocument, decodeComputedInputDocument, validateComputedInput
  , ComputedInputEvaluation, executeComputedInput, executeComputedInputWith
  , computedEvaluationDocument, computedEvaluationSource, computedEvaluationProof, computedEvaluationPresumption
  , ComputedInputReport(..), computedInputReport, inspectComputedInputOn
  , computedDestinationDocument, computedDestinationDigest, recoverComputedInputSource
  ) where

import Data.Aeson
import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import GHC.Generics (Generic)
import Yuho.Authoring.Codec
import Yuho.Authoring.Compile
import Yuho.Authoring.Report
import Yuho.Authoring.Types
import Yuho.Authoring.Typed
import Yuho.Authoring.Presumption
import Yuho.Authoring.Presumption.Validate (requiredPresumptionInputs, validatePresumptionBindings)
import Yuho.Authoring.Typed.Validate (typedOccurrences)
import Yuho.Authoring.Projection.Inspect (OriginalSourceExcerpt, recoverSourceReference)
import Yuho.Authoring.Validate (findAnalysis, issue, validateBindings, selectedOccurrences, Occurrence(..))
import Yuho.Protocol.Decode (sha256Text)
import Yuho.Protocol.Json (decodeJson)
import Yuho.SuppliedProofStatus.Types (SuppliedStatus(..), UnresolvedReason(..))

computedInputFormat, computedStatusMapping :: Text
computedInputFormat = "yuho.computed-input/v0.1-experimental"
computedStatusMapping = "yuho.technical-status-to-proof/v1"

-- Exactly one payload is admitted, matching destinationProfile. No recursive dependencies.
data ComputedDestination = ComputedDestination
  { destinationProfile :: Text, destinationAnalysis :: Text
  , destinationProof :: Maybe AuthoringDocument, destinationPresumption :: Maybe PresumptionDocument
  } deriving (Eq, Show, Generic)
data ComputedStatusPolicy = ComputedStatusPolicy
  { mappingPolicy :: Text, mappingUnresolvedReason :: Text } deriving (Eq, Show, Generic)
data ComputedInputBinding = ComputedInputBinding
  { computedBindingId :: Text
  , computedSourceDocument :: Text, computedSourceAnalysis :: Text, computedSourceExpression :: Text
  , computedSourceScope :: Scope, computedSourceSnapshot :: Text
  , computedDestinationId :: Text, computedDestinationAnalysis :: Text, computedDestinationInput :: Text
  , computedDestinationScope :: Scope, computedDestinationFingerprint :: Text
  , computedPolicy :: ComputedStatusPolicy, computedRationale :: Text
  , computedOriginalSources :: [SourceRef]
  } deriving (Eq, Show, Generic)
data ComputedInputDocument = ComputedInputDocument
  { computedDocumentFormat :: Text, computedDocumentId :: Text
  , computedTypedSource :: TypedDocument, computedDestination :: ComputedDestination
  , computedBinding :: ComputedInputBinding
  } deriving (Eq, Show, Generic)

proofInputDestination :: AuthoringDocument -> Text -> ComputedDestination
proofInputDestination d key = ComputedDestination evaluatorProfile key (Just d) Nothing
presumptionInputDestination :: PresumptionDocument -> Text -> ComputedDestination
presumptionInputDestination d key = ComputedDestination presumptionProfile key Nothing (Just d)
computedDestinationDocument :: ComputedDestination -> Either [AuthoringDiagnostic] AuthoringDocument
computedDestinationDocument d = case (destinationProfile d,destinationProof d,destinationPresumption d) of
  (p,Just doc,Nothing) | p == evaluatorProfile && documentFormat doc == authoringFormat -> Right doc
  (p,Nothing,Just doc) | p == presumptionProfile && presumptionDocumentFormat doc == presumptionAuthoringFormat
    && documentFormat (presumptionProofDocument doc) == authoringFormat -> Right (presumptionProofDocument doc)
  _ -> failure "CBPROFILE" "/computedDestination" [] "expected exactly one v0.1 proof or v0.4 presumption payload; reverse, recursive, linked, typed and temporal destinations are unsupported"
computedDestinationDigest :: ComputedDestination -> Text
computedDestinationDigest = sha256Text . encodeRecord

destinationId :: ComputedDestination -> Text
destinationId d = maybe (maybe "" documentId (destinationProof d)) presumptionDocumentId (destinationPresumption d)
failure :: Text -> Text -> [Text] -> Text -> Either [AuthoringDiagnostic] a
failure code path ids message = Left [issue code path ids message]

-- | Authorise the actual observation, exact source snapshot and exact destination.
-- Source references here are in the typed document's original-source namespace.
makeComputedInputBinding :: Text -> TypedEvaluation -> Text -> ComputedDestination -> Text
  -> ComputedStatusPolicy -> Text -> [SourceRef] -> Either [AuthoringDiagnostic] ComputedInputBinding
makeComputedInputBinding key source expression dest input policy rationale refs = do
  base <- computedDestinationDocument dest
  a <- maybe (failure "CBANALYSIS" "/destinationAnalysis" [destinationAnalysis dest] "destination analysis not found") Right (findAnalysis base (destinationAnalysis dest))
  let snapshot = typedEvaluationSnapshot source
      upstream = typedSnapshotAnalysis snapshot
      b = ComputedInputBinding key (typedDocumentId (typedSnapshotDocument snapshot)) (typedAnalysisId upstream)
        expression (typedAnalysisScope upstream) (typedSnapshotId snapshot) (destinationId dest)
        (destinationAnalysis dest) input (analysisScope a) (computedDestinationDigest dest) policy rationale refs
      -- Constructor validation is independent of the caller's eventual document
      -- ID. A one-byte temporary ID cannot consume the binding's byte budget or
      -- reject an otherwise admissible near-limit artifact. It is never saved.
      temporaryId = if key == "w" then "x" else "w"
      doc = ComputedInputDocument computedInputFormat temporaryId (typedSnapshotDocument snapshot) dest b
  _ <- resolveBinding doc source
  pure b

encodeComputedInputDocument :: ComputedInputDocument -> BS.ByteString
encodeComputedInputDocument = encodeRecord
decodeComputedInputDocument :: BS.ByteString -> Either AuthoringDiagnostic ComputedInputDocument
decodeComputedInputDocument bytes = do
  _ <- either (Left . issue "CBJSON" "/" []) Right (decodeJson bytes)
  d <- either (Left . issue "CBJSON" "/" [] . T.pack) Right (eitherDecodeStrict' bytes)
  if computedDocumentFormat d == computedInputFormat then Right d
    else Left (issue "CBVERSION" "/computedDocumentFormat" [] "unsupported computed-input format")

-- | Validation compiles both profiles but performs no evaluation. The local
-- validation placeholder never leaves this function and is never a run result.
validateComputedInput :: ComputedInputDocument -> [AuthoringDiagnostic]
validateComputedInput d = either id (const []) $ do
  c <- compileTypedAnalysis (computedTypedSource d) (computedSourceAnalysis (computedBinding d))
  validateContract d (typedCompiledSnapshot c)
  _ <- compileDestination d (generatedAssessment d (Classification (Unresolved NotDetermined)))
  pure ()

validateContract :: ComputedInputDocument -> TypedSnapshot -> Either [AuthoringDiagnostic] ()
validateContract d upstream = do
  let b = computedBinding d; dest = computedDestination d
      bad code field ids = failure code field (computedBindingId b:ids)
      demand condition code field ids message = if condition then Right () else bad code field ids message
      bounded t = not (T.null (T.strip t)) && BS.length (UTF8.encodeUtf8 t) <= 128
      source = computedTypedSource d
  demand (computedDocumentFormat d == computedInputFormat) "CBVERSION" "/computedDocumentFormat" [] "unsupported computed-input format"
  demand (BS.length (encodeRecord d) <= 1048576) "CBLIMIT" "/" [] "integration artifact exceeds one MiB; backend limits also apply independently"
  demand (bounded (computedDocumentId d) && bounded (computedBindingId b) && computedDocumentId d /= computedBindingId b)
    "CBID" "/computedBindingId" [] "document and binding IDs must be nonempty, distinct and at most 128 UTF-8 bytes"
  demand (not (T.null (T.strip (computedRationale b)))) "CBRATIONALE" "/computedRationale" [] "explicit author admission rationale required"
  demand (mappingPolicy (computedPolicy b) == computedStatusMapping && mappingUnresolvedReason (computedPolicy b) `elem` ["not_determined","external_decision_pending"])
    "CBMAPPING" "/computedPolicy" [] "expected technical-status-to-proof/v1 with an explicit supported destination unresolved reason"
  demand (typedSnapshotDocument upstream == source && computedSourceDocument b == typedDocumentId source
    && computedSourceAnalysis b == typedAnalysisId (typedSnapshotAnalysis upstream)
    && computedSourceSnapshot b == typedSnapshotId upstream) "CBSTALE" "/computedSourceSnapshot" [computedSourceExpression b] "typed source document, analysis or exact snapshot differs from explicit binding"
  demand (computedSourceScope b == typedAnalysisScope (typedSnapshotAnalysis upstream)) "CBSCOPE" "/computedSourceScope" [] "source scope differs from selected typed analysis"
  demand (length [() | (x,_) <- typedOccurrences source (typedSnapshotAnalysis upstream), typedId (expressionMeta x) == computedSourceExpression b] == 1)
    "CBOBSERVATION" "/computedSourceExpression" [computedSourceExpression b] "source must be one named expression in the selected closure; rule/proposition and absent/unevaluated expressions are unsupported"
  base <- computedDestinationDocument dest
  a <- maybe (bad "CBANALYSIS" "/destinationAnalysis" [destinationAnalysis dest] "destination analysis not found") Right (findAnalysis base (destinationAnalysis dest))
  demand (computedDestinationId b == destinationId dest && computedDestinationAnalysis b == analysisId a
    && computedDestinationFingerprint b == computedDestinationDigest dest) "CBSTALE" "/computedDestinationFingerprint" [] "destination identity, analysis or authored payload differs from binding"
  demand (computedSourceScope b == computedDestinationScope b && computedDestinationScope b == analysisScope a)
    "CBSCOPE" "/computedDestinationScope" [] "bridge requires exact actor/context equality; scope conversion is unsupported"
  demand (any (\n -> nodeId n == computedDestinationInput b && nodeKind n == "input") (lawNodes (documentLaw base)))
    "CBTARGET" "/computedDestinationInput" [computedDestinationInput b] "destination must be an existing primitive input"
  let required = case destinationPresumption dest of
        Just p -> requiredPresumptionInputs p a
        Nothing -> [nodeId (occurrenceNode o) | o <- selectedOccurrences base a, nodeKind (occurrenceNode o) == "input"]
  demand (computedDestinationInput b `elem` required) "CBTARGET" "/computedDestinationInput" [computedDestinationInput b] "input is outside selected proof/registration closure"
  demand (null [x | x <- documentAssessments base, assessmentId x `elem` analysisAssessments a, assessmentInput x == computedDestinationInput b])
    "CBCONFLICT" "/computedDestinationInput" [computedDestinationInput b] "a selected direct assessment already supplies this input; no replacement or overwrite is permitted"
  -- Run the ordinary validators on the original document, exempting ONLY the
  -- explicitly bound missing input. Unselected retained alternatives stay intact.
  let errors = case destinationPresumption dest of
        Just p -> presumptionDiagnostics (validatePresumptionBindings p (analysisId a))
        Nothing -> validationDiagnostics (validateBindings base (analysisId a))
      unexpected e = not (diagnosticCode e `elem` ["AMISSING","PAMISSING"] && computedDestinationInput b `elem` diagnosticObjects e)
  case filter unexpected errors of [] -> pure (); es -> Left es
  _ <- traverse (recoverSourceReference (typedOriginalSources source)) (computedOriginalSources b)
  let generatedId = assessmentId (generatedAssessment d (Classification Proved))
      ids = documentId base : lawId (documentLaw base) : map nodeId (lawNodes (documentLaw base)) ++ map edgeId (lawEdges (documentLaw base))
        ++ map sourceId (documentSources base) ++ map assertionId (documentAssertions base) ++ map assessmentId (documentAssessments base)
        ++ map analysisId (documentAnalyses base) ++ map relationshipId (documentRelationships base) ++ map annotationId (documentAnnotations base)
        ++ maybe [] (\p -> presumptionDocumentId p : map registeredId (presumptionRegistrations p) ++ concatMap (map registeredConditionId . conditionObjects . registeredTrigger) (presumptionRegistrations p) ++ concatMap (map registeredConditionId . conditionObjects . registeredRebuttal) (presumptionRegistrations p)) (destinationPresumption dest)
  demand (generatedId `notElem` ids) "CBCOLLISION" "/generatedAssessment" [generatedId] "generated bridge identity collides with authored destination material"

resolveBinding :: ComputedInputDocument -> TypedEvaluation -> Either [AuthoringDiagnostic] (TypedObservation,Classification)
resolveBinding d source = do
  validateContract d (typedEvaluationSnapshot source)
  let b = computedBinding d
  observation <- case [o | o <- typedReportExpressions (typedEvaluationReport source), typedObservedObject o == computedSourceExpression b,
      typedObservationCategory o == "expression", typedObservedState o == "evaluated"] of
    [o] -> Right o
    _ -> failure "CBOBSERVATION" "/computedSourceExpression" [computedBindingId b,computedSourceExpression b] "actual named expression observation missing or ambiguous"
  classification <- case typedObservedStatus observation of
    "satisfied" -> Right (Classification Proved)
    "not_satisfied" -> Right (Classification NotProved)
    "unresolved" -> Right (Classification (Unresolved (if mappingUnresolvedReason (computedPolicy b) == "not_determined" then NotDetermined else ExternalDecisionPending)))
    value -> failure "CBMAPPING" "/computedPolicy" [computedBindingId b] ("unsupported actual typed status: " <> value)
  pure (observation,classification)

generatedAssessment :: ComputedInputDocument -> Classification -> Assessment
generatedAssessment d classification = let b = computedBinding d in
  Assessment ("bridge-assessment:" <> sha256Text (encodeRecord b)) (computedDestinationInput b) (computedDestinationScope b)
    classification ("GENERATED execution-only technical mapping. " <> computedRationale b)
    "Yuho explicit computed-input adapter" "external_assertion" "assumption" [] []
-- Original source refs remain in their original namespace in the binding/report;
-- never copy upstream refs into an unrelated destination source registry.
withOverlay :: ComputedInputDocument -> Assessment -> Either [AuthoringDiagnostic] ComputedDestination
withOverlay d assessment = do
  let dest = computedDestination d
  base <- computedDestinationDocument dest
  let overlay = base {documentAssessments=documentAssessments base ++ [assessment], documentAnalyses=
        [if analysisId a == destinationAnalysis dest then a {analysisAssessments=analysisAssessments a ++ [assessmentId assessment]} else a | a <- documentAnalyses base]}
  pure $ case destinationPresumption dest of
    Just p -> dest {destinationPresumption=Just p {presumptionProofDocument=overlay}}
    Nothing -> dest {destinationProof=Just overlay}
data CompiledDestination = ProofDestination CompiledAnalysis | PresumptionDestination PresumptionCompilation
compileDestination :: ComputedInputDocument -> Assessment -> Either [AuthoringDiagnostic] CompiledDestination
compileDestination d assessment = do
  overlay <- withOverlay d assessment
  case (destinationProof overlay,destinationPresumption overlay) of
    (Just base,Nothing) -> ProofDestination <$> compileAnalysis base (destinationAnalysis overlay)
    (Nothing,Just base) -> PresumptionDestination <$> compilePresumptionAnalysis base (destinationAnalysis overlay)
    _ -> failure "CBPROFILE" "/computedDestination" [] "unsupported destination"

data ComputedDownstream = ProofExecution Evaluation | PresumptionExecution PresumptionEvaluation
data ComputedInputEvaluation = ComputedInputEvaluation ComputedInputDocument TypedEvaluation TypedObservation Assessment ComputedDestination ComputedDownstream
computedEvaluationDocument :: ComputedInputEvaluation -> ComputedInputDocument
computedEvaluationDocument (ComputedInputEvaluation x _ _ _ _ _) = x
computedEvaluationSource :: ComputedInputEvaluation -> TypedEvaluation
computedEvaluationSource (ComputedInputEvaluation _ x _ _ _ _) = x
computedEvaluationProof :: ComputedInputEvaluation -> Maybe Evaluation
computedEvaluationProof (ComputedInputEvaluation _ _ _ _ _ (ProofExecution x)) = Just x
computedEvaluationProof _ = Nothing
computedEvaluationPresumption :: ComputedInputEvaluation -> Maybe PresumptionEvaluation
computedEvaluationPresumption (ComputedInputEvaluation _ _ _ _ _ (PresumptionExecution x)) = Just x
computedEvaluationPresumption _ = Nothing

executeComputedInput :: ComputedInputDocument -> Either [AuthoringDiagnostic] ComputedInputEvaluation
executeComputedInput d = do
  source <- compileTypedAnalysis (computedTypedSource d) (computedSourceAnalysis (computedBinding d)) >>= evaluateTypedAnalysis
  executeComputedInputWith d source
-- | Reuse an actual opaque evaluation only if its exact retained source matches.
executeComputedInputWith :: ComputedInputDocument -> TypedEvaluation -> Either [AuthoringDiagnostic] ComputedInputEvaluation
executeComputedInputWith d source = do
  (observation,classification) <- resolveBinding d source
  let assessment = generatedAssessment d classification
  compiled <- compileDestination d assessment
  downstream <- case compiled of
    ProofDestination c -> ProofExecution <$> evaluateAnalysis c
    PresumptionDestination c -> PresumptionExecution <$> evaluatePresumptionAnalysis c
  overlay <- withOverlay d assessment
  pure (ComputedInputEvaluation d source observation assessment overlay downstream)

data ComputedInputReport = ComputedInputReport
  { computedReportVersion :: Text, computedExecutionId :: Text, computedReportDocument :: ComputedInputDocument
  , computedTypedSnapshot :: TypedSnapshot, computedOriginalObservation :: TypedObservation
  , computedUpstreamReport :: TypedReport, computedMappedClassification :: Classification
  , computedGeneratedOrigin :: Text, computedGeneratedAssessment :: Assessment, computedExecutionOverlay :: ComputedDestination
  , computedDownstreamSnapshot :: Text, computedDownstreamReport :: ApplicationReport
  , computedDerivationReport :: Maybe PresumptionReport, computedReportNotice :: Text
  } deriving (Eq, Show, Generic)
computedInputReport :: ComputedInputEvaluation -> ComputedInputReport
computedInputReport (ComputedInputEvaluation d source observation assessment overlay downstream) =
  let (snapshot,proof,derivations) = case downstream of
        ProofExecution e -> (snapshotId (evaluationSnapshot e),evaluationReport e,Nothing)
        PresumptionExecution e -> (presumptionSnapshotId (presumptionEvaluationSnapshot e),presumptionReportProof (presumptionEvaluationReport e),Just (presumptionEvaluationReport e))
      snapshotSource = typedEvaluationSnapshot source
      identity = sha256Text (encodeRecord (d,typedSnapshotId snapshotSource,observation,assessment,snapshot))
  in ComputedInputReport computedInputFormat identity d snapshotSource observation (typedEvaluationReport source)
      (assessmentClassification assessment) "generated_computed_input_bridge" assessment overlay snapshot proof derivations
      "Explicit authorised technical mapping, not a human-supplied assessment or determination of legal proof, factual absence, evidential sufficiency, liability or rebuttal adequacy. Original destination authorship is unchanged; generated assessment exists only in the recorded execution overlay."

-- | Attachment check only; does not rerun either evaluator or alter view state.
inspectComputedInputOn :: ComputedInputDocument -> ComputedInputEvaluation -> Either [AuthoringDiagnostic] ComputedInputReport
inspectComputedInputOn d e
  | d == computedEvaluationDocument e = Right (computedInputReport e)
  | otherwise = failure "CBSTALE" "/computedSnapshot" [computedDocumentId d] "integration document differs from the exact retained execution snapshot"
recoverComputedInputSource :: ComputedInputEvaluation -> Text -> SourceRef -> Either [AuthoringDiagnostic] OriginalSourceExcerpt
recoverComputedInputSource e side ref = do
  let d = computedEvaluationDocument e
  sources <- case side of
    "source" -> Right (typedOriginalSources (computedTypedSource d))
    "destination" -> documentSources <$> computedDestinationDocument (computedDestination d)
    _ -> failure "CBSOURCE" "/sourceNamespace" [side] "expected source or destination original-source namespace"
  recoverSourceReference sources ref

instance ToJSON ComputedDestination where toJSON = genericToJSON jsonOptions
instance FromJSON ComputedDestination where parseJSON = genericParseJSON jsonOptions
instance ToJSON ComputedStatusPolicy where toJSON = genericToJSON jsonOptions
instance FromJSON ComputedStatusPolicy where parseJSON = genericParseJSON jsonOptions
instance ToJSON ComputedInputBinding where toJSON = genericToJSON jsonOptions
instance FromJSON ComputedInputBinding where parseJSON = genericParseJSON jsonOptions
instance ToJSON ComputedInputDocument where toJSON = genericToJSON jsonOptions
instance FromJSON ComputedInputDocument where parseJSON = genericParseJSON jsonOptions
instance ToJSON ComputedInputReport where toJSON = genericToJSON jsonOptions
