{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Typed.Projection
  ( TypedProjection, TypedProjectionData(..), TypedProjectedNode(..), TypedProjectedEdge(..)
  , typedProjectionData, projectTypedAuthored, projectTypedEvaluation, projectTypedEvaluationOn
  , validateTypedProjection, encodeTypedProjection, TypedInspection(..), inspectTypedExpression
  , recoverTypedSource, TypedFocus(..), typedReferenceView, validateTypedView
  , encodeTypedViewJson, encodeTypedViewXml, encodeTypedViewSvg ) where

import Data.Aeson (ToJSON(..), Value, genericToJSON)
import qualified Data.ByteString as BS
import Data.List (find, mapAccumL, nub, sort)
import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import GHC.Generics (Generic)
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Projection (projectionIdentity)
import Yuho.Authoring.Projection.Inspect (OriginalSourceExcerpt(..), recoverSourceReference)
import Yuho.Authoring.Projection.Render (escape, number, wrap, xmlCharacter)
import Yuho.Authoring.Projection.Types (ProjectionView(..), ViewBinding(..), EdgeBinding(..), projectionViewFormat)
import Yuho.Authoring.Types
import Yuho.Authoring.Typed.Types
import Yuho.Authoring.Typed.Run
import Yuho.Authoring.Typed.Validate
import Yuho.Authoring.Validate (issue)
import qualified Yuho.Diagram.Types as Legacy
import qualified Yuho.Diagram.Encode as Legacy

data TypedProjectedNode = TypedProjectedNode
  { typedNodeId :: Text, typedNodeKind :: Text, typedNodeAuthoredId :: Text, typedNodeLabel :: Text
  , typedNodeOccurrence :: Maybe TypedOccurrence, typedNodeObservation :: Maybe TypedObservation
  , typedNodeSelected :: Maybe Bool, typedNodeRecord :: Value } deriving (Eq, Show, Generic)
data TypedProjectedEdge = TypedProjectedEdge
  { typedEdgeId :: Text, typedEdgeFrom :: Text, typedEdgeTo :: Text, typedEdgeKind :: Text
  , typedEdgeOrigins :: [Text], typedEdgePosition :: Maybe Int, typedEdgeRole :: Maybe Text
  , typedEdgeOriginal :: Maybe SourceRef } deriving (Eq, Show, Generic)
data TypedProjectionData = TypedProjectionData
  { typedProjectionVersion :: Text, typedProjectionId :: Text, typedProjectionMode :: Text
  , typedProjectionSnapshot :: TypedSnapshot, typedProjectionReport :: Maybe TypedReport
  , typedProjectionMappings :: [TypedKernelMapping], typedProjectionNodes :: [TypedProjectedNode]
  , typedProjectionEdges :: [TypedProjectedEdge], typedProjectionDiagnostics :: [AuthoringDiagnostic]
  , typedProjectionOpenInputs :: [TypedOpenInput], typedProjectionNotice :: Text } deriving (Eq, Show, Generic)
newtype TypedProjection = TypedProjection TypedProjectionData

typedProjectionData :: TypedProjection -> TypedProjectionData
typedProjectionData (TypedProjection x) = x

objectId :: TypedDocument -> Text -> Text
objectId d key = projectionIdentity "typed-object" (typedLawId d,key)
occurrenceId :: TypedOccurrence -> Text
occurrenceId = projectionIdentity "typed-occurrence"

-- Reuse compilation's immutable snapshot construction without compiling a
-- draft: only hashing and structural traversal are performed by this function.
projectTypedAuthored :: TypedDocument -> Text -> Either [AuthoringDiagnostic] TypedProjection
projectTypedAuthored d key = do
  let report = validateTypedBindings d key
      errors = filter ((/= "TMISSING") . diagnosticCode) (typedDiagnostics report)
  if null errors then pure () else Left errors
  a <- maybe (Left [issue "TTARGET" "/typedAnalyses" [key] "analysis not found"]) Right (typedAnalysisById d key)
  -- Identical snapshot operation shared with compilation, including law digest.
  let snapshot = typedSnapshotFor d a
  buildProjection snapshot Nothing [] report

projectTypedEvaluation :: TypedEvaluation -> Either [AuthoringDiagnostic] TypedProjection
projectTypedEvaluation evaluation =
  let snapshot = typedEvaluationSnapshot evaluation
      d = typedSnapshotDocument snapshot
      a = typedSnapshotAnalysis snapshot
  in buildProjection snapshot (Just (typedEvaluationReport evaluation)) (typedEvaluationMappings evaluation)
      (validateTypedBindings d (typedAnalysisId a))

projectTypedEvaluationOn :: TypedDocument -> TypedEvaluation -> Either [AuthoringDiagnostic] TypedProjection
projectTypedEvaluationOn d evaluation
  | d == typedSnapshotDocument (typedEvaluationSnapshot evaluation) = projectTypedEvaluation evaluation
  | otherwise = Left [issue "TSTALE" "/typedProjectionSnapshot" [typedDocumentId d]
      "document differs from the typed evaluation's exact retained snapshot"]

buildProjection :: TypedSnapshot -> Maybe TypedReport -> [TypedKernelMapping] -> TypedValidation
                -> Either [AuthoringDiagnostic] TypedProjection
buildProjection snapshot report mappings validation = do
  let d = typedSnapshotDocument snapshot
      a = typedSnapshotAnalysis snapshot
      obj = objectId d
      occurrences = typedOccurrences d a
      occ e path = TypedOccurrence (typedLawDigest snapshot) (typedAnalysisRule a) (typedAnalysisScope a) (typedId (expressionMeta e)) path
      observations = maybe [] (\r -> typedReportExpressions r ++ typedReportRules r ++ typedReportPropositions r) report
      observation category key = find (\o -> typedObservationCategory o == category && typedObservedObject o == key) observations
      node role metadata payload = TypedProjectedNode (obj (typedId metadata)) role (typedId metadata) (typedLabel metadata) Nothing Nothing Nothing payload
      metas = Map.fromList [(typedId m,m) | (_,m) <- typedObjects d]
      meta key label = TypedMeta key label Nothing []
      mFor key = Map.findWithDefault (meta key key) key metas
      ordinary = [node "document" (meta (typedDocumentId d) (typedDocumentId d)) (toJSON (typedDocumentId d)),
        node "law" (meta (typedLawId d) (typedLawId d)) (toJSON (typedLawId d,typedLawRevision d))]
        ++ [node "entity_type" (entityTypeMeta x) (toJSON x) | x <- typedEntityTypes d]
        ++ [node "entity" (entityMeta x) (toJSON x) | x <- typedEntities d]
        ++ [node "predicate" (predicateMeta x) (toJSON x) | x <- typedPredicates d]
        ++ [node "application" (applicationMeta x) (toJSON x) | x <- typedApplications d]
        ++ [node "scalar" (scalarMeta x) (toJSON x) | x <- typedScalars d]
        ++ [node "expression" (expressionMeta x) (toJSON x) | x <- typedExpressions d]
        ++ [(node "rule" (typedRuleMeta x) (toJSON x)) {typedNodeObservation=observation "rule" (typedId (typedRuleMeta x))} | x <- typedRules d]
        ++ [(node "proposition" (propositionMeta x) (toJSON x)) {typedNodeObservation=observation "proposition" (typedId (propositionMeta x))} | x <- typedPropositions d]
        ++ [(node "assessment" (typedAssessmentMeta x) (toJSON x))
          {typedNodeSelected=Just (typedId (typedAssessmentMeta x) `elem` selectedTypedAssessments a)} | x <- typedAssessments d]
        ++ [(node "value" (valueMeta x) (toJSON x))
          {typedNodeSelected=Just (typedId (valueMeta x) `elem` selectedTypedValues a)} | x <- typedValues d]
        ++ [node "source" (meta (sourceId x) (maybe (sourceId x) id (sourceLocator x))) (toJSON x) | x <- typedOriginalSources d]
        ++ [node "assertion" (meta (assertionId x) (assertionDescription x)) (toJSON x) | x <- typedCaseAssertions d]
        ++ [node "annotation" (meta (annotationId x) (annotationText x)) (toJSON x) | x <- typedAnnotations d]
        ++ [node "relationship" (meta (typedLinkId x) (typedLinkKind x)) (toJSON x) | x <- typedLinks d]
        ++ [node "analysis" (meta (typedAnalysisId x) (typedAnalysisId x)) (toJSON x) | x <- typedAnalyses d]
      occurrenceNodes = [(node "occurrence" (expressionMeta x) (toJSON x))
        {typedNodeId=occurrenceId (occ x path),typedNodeOccurrence=Just (occ x path),typedNodeObservation=observation "expression" (typedId (expressionMeta x))} | (x,path) <- occurrences]
      observationNodes = [(node "observation" (mFor (typedObservedObject o)) (toJSON o))
        {typedNodeId=typedObservationId o,typedNodeObservation=Just o} | o <- observations]
      edge kind from to originals position role anchor discriminator = TypedProjectedEdge
        (projectionIdentity "typed-edge" (kind,from,to,discriminator)) from to kind originals position role anchor
      ref kind owner target discriminator = edge kind (obj owner) (obj target) [owner,target] Nothing Nothing Nothing discriminator
      -- Reference arrays are authored provenance, not set-valued evidence.
      -- Keep the legacy ID for the first entry; disambiguate later occurrences
      -- of the same target without changing any previously successful output.
      references kind owner = snd . mapAccumL (\seen target ->
        let occurrence = Map.findWithDefault (0 :: Int) target seen
            suffix = if occurrence == 0 then [] else ["reference-occurrence",T.pack (show occurrence)]
        in (Map.insert target (occurrence+1) seen,ref kind owner target ([owner,target] ++ suffix))) Map.empty
      direct = [edge (typedLinkKind e) (obj (typedLinkFrom e)) (obj (typedLinkTo e)) [typedLinkId e]
          Nothing Nothing Nothing [typedLinkId e] | e <- typedLinks d]
      instanceEdges = [edge "instance_of" (occurrenceId (occ x path)) (obj (typedId (expressionMeta x)))
        (typedId (expressionMeta x):path) Nothing Nothing Nothing path | (x,path) <- occurrences]
      occurrenceEdges = [let parent = case [occurrenceId (occ p pp) | (p,pp) <- occurrences, pp == init path] of
                                  [p] -> p
                                  _ -> obj (typedAnalysisRule a)
                         in edge "typed_dependency" parent (occurrenceId (occ x path)) path Nothing Nothing Nothing path
        | (x,path) <- occurrences, not (null path)]
      appEdges = [ref "predicate_declaration" (typedId (applicationMeta application)) (tuplePredicate (applicationTuple application)) [typedId (applicationMeta application)] | application <- typedApplications d]
        ++ [ref "application_expression" (typedId (expressionMeta e)) key [key,typedId (expressionMeta e)]
        | e <- typedExpressions d, GroundApplication key <- [expressionForm e]]
      occurrenceOperands = concat [case expressionForm e of
        GroundApplication app -> [edge "ground_application" (occurrenceId (occ e path)) (obj app) [typedId (expressionMeta e),app] Nothing Nothing Nothing path]
        IntegerComparison _ l r -> [edge kind (occurrenceId (occ e path)) (obj target) [typedId (expressionMeta e),target] Nothing Nothing Nothing (path ++ [kind]) | (kind,target) <- [("left_operand",l),("right_operand",r)]]
        _ -> [] | (e,path) <- occurrences]
      argumentEdges = [edge "argument" (obj (typedId (applicationMeta x))) (obj arg)
          [typedId (applicationMeta x),tuplePredicate (applicationTuple x),arg] (Just i) (Just (argumentRole role)) Nothing
          [typedId (applicationMeta x),T.pack (show i)]
        | x <- typedApplications d, p <- typedPredicates d, typedId (predicateMeta p) == tuplePredicate (applicationTuple x),
          (i,(arg,role)) <- zip [0 :: Int ..] (zip (tupleArguments (applicationTuple x)) (predicateRoles p))]
      nominal = [ref "nominal_type" (typedId (entityMeta x)) (entityNominalType x) [typedId (entityMeta x)] | x <- typedEntities d]
        ++ [edge "argument_type" (obj (typedId (predicateMeta x))) (obj (argumentType role)) [typedId (predicateMeta x),argumentType role]
            (Just i) (Just (argumentRole role)) Nothing [typedId (predicateMeta x),T.pack (show i)]
          | x <- typedPredicates d, (i,role) <- zip [0 :: Int ..] (predicateRoles x)]
      operands = concat [[ref "left_operand" key l [key,l],ref "right_operand" key r [key,r]]
        | x <- typedExpressions d, let key = typedId (expressionMeta x), IntegerComparison _ l r <- [expressionForm x]]
      assessmentEdges = concat [[ref "assessment_tuple" key (assessedApplication x) [key]]
          ++ references "assessment_assertion" key (typedAssertionRefs x)
        | x <- typedAssessments d, let key = typedId (typedAssessmentMeta x)]
      selected = [edge "selected_assessment" (obj (typedId (typedAssessmentMeta x))) (occurrenceId (occ e path))
          [typedId (typedAssessmentMeta x),app] Nothing Nothing Nothing path
        | (e,path) <- occurrences, GroundApplication app <- [expressionForm e], x <- typedAssessments d,
          typedId (typedAssessmentMeta x) `elem` selectedTypedAssessments a, assessedApplication x == app]
      valueEdges = [ref (if typedId (valueMeta x) `elem` selectedTypedValues a then "selected_value" else "alternative_value")
        (typedId (valueMeta x)) (valueScalar x) [typedId (valueMeta x)] | x <- typedValues d]
      sourceEdges = [edge "original_source" (obj owner) (obj (referenceSource source)) [owner,referenceSource source]
          Nothing Nothing (Just source) [owner,T.pack (show i)]
        | (owner,sources) <- [(typedId m,typedSources m) | (_,m) <- typedObjects d]
            ++ [(assertionId x,assertionSources x) | x <- typedCaseAssertions d], (i,source) <- zip [0 :: Int ..] sources]
      conclusions = [ref "concludes" (typedId (typedRuleMeta x)) (typedRuleConclusion x) [typedId (typedRuleMeta x)] | x <- typedRules d]
      observationEdges = [edge "observes" (typedObservationId o)
        (maybe (obj (typedObservedObject o)) occurrenceId (typedObservationOccurrence o)) [typedObservedObject o]
        Nothing Nothing Nothing [typedObservationId o] | o <- observations]
      annotations = concat [references "annotation_about" (annotationId x)
        [target | target <- annotationAbout x, any ((== target) . typedNodeAuthoredId) ordinary]
        | x <- typedAnnotations d]
      value = TypedProjectionData typedProjectionFormat (projectionIdentity "typed-projection" (typedSnapshotId snapshot,maybe False (const True) report))
        (maybe "authored" (const "evaluated") report) snapshot report mappings (ordinary ++ occurrenceNodes ++ observationNodes)
        (direct ++ instanceEdges ++ occurrenceEdges ++ appEdges ++ argumentEdges ++ nominal ++ operands ++ assessmentEdges
          ++ occurrenceOperands ++ selected ++ valueEdges ++ sourceEdges ++ conclusions ++ observationEdges ++ annotations)
        (typedDiagnostics validation) (typedOpenInputs validation)
        "Derived typed output. Original/supplied objects and real expression/rule/proposition observations are separate; legacy views are not authoring interchange."
  case validateTypedProjection value of
    [] -> Right (TypedProjection value)
    errors -> Left errors

validateTypedProjection :: TypedProjectionData -> [AuthoringDiagnostic]
validateTypedProjection p =
  [issue "TPVERSION" "/typedProjectionVersion" [] "unsupported typed projection" | typedProjectionVersion p /= typedProjectionFormat]
  ++ [issue "TPDUPLICATE" "/typedProjection" [] "duplicate projection identity" | length allIds /= length (nub allIds)]
  ++ [issue "TPENDPOINT" "/typedProjectionEdges" [typedEdgeId e,key] "projected endpoint missing"
      | e <- typedProjectionEdges p, key <- [typedEdgeFrom e,typedEdgeTo e], key `notElem` ids]
  ++ [issue "TPSNAPSHOT" "/typedProjectionReport" [] "report and retained snapshot differ"
      | Just report <- [typedProjectionReport p], typedReportSnapshot report /= typedSnapshotId (typedProjectionSnapshot p)]
  where ids = map typedNodeId (typedProjectionNodes p)
        allIds = ids ++ map typedEdgeId (typedProjectionEdges p)

encodeTypedProjection :: TypedProjection -> Either [AuthoringDiagnostic] BS.ByteString
encodeTypedProjection p = case validateTypedProjection (typedProjectionData p) of
  [] -> Right (encodeRecord (typedProjectionData p))
  errors -> Left errors

recoverTypedSource :: TypedProjection -> SourceRef -> Either [AuthoringDiagnostic] OriginalSourceExcerpt
recoverTypedSource p = recoverSourceReference (typedOriginalSources (typedSnapshotDocument (typedProjectionSnapshot (typedProjectionData p))))

data TypedInspection = TypedInspection
  { typedFocusSnapshot :: Text, typedFocusAnalysis :: TypedAnalysis, typedFocusExpression :: TypedExpression
  , typedFocusOccurrence :: TypedProjectedNode, typedFocusObservation :: Maybe TypedObservation
  , typedFocusApplication :: Maybe TypedApplication, typedFocusPredicate :: Maybe TypedPredicate
  , typedFocusArguments :: [(TypedArgument,TypedEntity)], typedFocusSelected :: Maybe TypedAssessment
  , typedFocusAlternatives :: [TypedAssessment], typedFocusScalars :: [TypedScalar], typedFocusValues :: [TypedValue]
  , typedFocusAssertions :: [CaseAssertion], typedFocusSources :: [SourceRef]
  , typedFocusParents :: [TypedLink], typedFocusChildren :: [TypedLink] } deriving (Eq, Show, Generic)

inspectTypedExpression :: TypedProjection -> Text -> Either [AuthoringDiagnostic] TypedInspection
inspectTypedExpression p key = do
  let value = typedProjectionData p
      snapshot = typedProjectionSnapshot value
      d = typedSnapshotDocument snapshot
      a = typedSnapshotAnalysis snapshot
      nodes = [n | n <- typedProjectionNodes value, typedNodeKind n == "occurrence",
        typedNodeAuthoredId n == key || typedNodeId n == key]
      failure = Left [issue "TFOCUS" "/typedFocus" [key,typedAnalysisId a] "focus must identify one selected typed expression or its scoped occurrence"]
  occurrence <- case nodes of [n] -> Right n; _ -> failure
  expression <- maybe failure Right (find ((== typedNodeAuthoredId occurrence) . typedId . expressionMeta) (typedExpressions d))
  let app = case expressionForm expression of
        GroundApplication target -> find ((== target) . typedId . applicationMeta) (typedApplications d)
        _ -> Nothing
      predicate = app >>= \x -> find ((== tuplePredicate (applicationTuple x)) . typedId . predicateMeta) (typedPredicates d)
      arguments = case (app,predicate) of
        (Just x,Just declaration) -> [(role,e) | (role,target) <- zip (predicateRoles declaration) (tupleArguments (applicationTuple x)),
          e <- typedEntities d, typedId (entityMeta e) == target]
        _ -> []
      compatible = [x | x <- typedAssessments d, Just (assessedApplication x) == (typedId . applicationMeta <$> app), typedAssessmentScope x == typedAnalysisScope a]
      selected = find ((`elem` selectedTypedAssessments a) . typedId . typedAssessmentMeta) compatible
      alternatives = [x | x <- compatible, typedId (typedAssessmentMeta x) `notElem` selectedTypedAssessments a]
      scalarIds = case expressionForm expression of IntegerComparison _ l r -> nub [l,r]; _ -> []
      scalars = [x | x <- typedScalars d, typedId (scalarMeta x) `elem` scalarIds]
      values = [x | x <- typedValues d, valueScalar x `elem` scalarIds, typedId (valueMeta x) `elem` selectedTypedValues a]
      assertions = [x | x <- typedCaseAssertions d, assertionId x `elem` maybe [] typedAssertionRefs selected]
      sources = nub (typedSources (expressionMeta expression) ++ maybe [] (typedSources . applicationMeta) app
        ++ maybe [] (typedSources . predicateMeta) predicate ++ maybe [] (typedSources . typedAssessmentMeta) selected
        ++ concatMap (typedSources . scalarMeta) scalars ++ concatMap (typedSources . valueMeta) values ++ concatMap assertionSources assertions)
      parents = filter ((== typedId (expressionMeta expression)) . typedLinkTo) (typedLinks d)
      children = filter ((== typedId (expressionMeta expression)) . typedLinkFrom) (typedLinks d)
  pure (TypedInspection (typedSnapshotId snapshot) a expression occurrence (typedNodeObservation occurrence) app predicate arguments
    selected alternatives scalars values assertions sources parents children)

data TypedFocus = TypedExpressionFocus Text | TypedRuleFocus deriving (Eq, Show, Generic)

typedReferenceView :: TypedProjection -> TypedFocus -> [Text] -> Either [AuthoringDiagnostic] ProjectionView
typedReferenceView p focus expandedSources = do
  let value = typedProjectionData p
      snapshot = typedProjectionSnapshot value
      d = typedSnapshotDocument snapshot
      a = typedSnapshotAnalysis snapshot
      obj = objectId d
      occurrences = [n | n <- typedProjectionNodes value, typedNodeKind n == "occurrence"]
  details <- case focus of
    TypedExpressionFocus key -> (:[]) <$> inspectTypedExpression p key
    TypedRuleFocus -> traverse (inspectTypedExpression p . typedNodeId) occurrences
  let sources = nub (concatMap typedFocusSources details)
  if length (nub expandedSources) == length expandedSources && all (`elem` map referenceSource sources) expandedSources
    then pure () else Left [issue "TSOURCE" "/typedView" expandedSources "expand distinct original sources referenced by this focus"]
  let forDetail x = typedNodeId (typedFocusOccurrence x) : map obj
        (maybe [] ((:[]) . typedId . applicationMeta) (typedFocusApplication x)
          ++ maybe [] ((:[]) . typedId . typedAssessmentMeta) (typedFocusSelected x)
          ++ maybe [] ((:[]) . typedId . predicateMeta) (typedFocusPredicate x)
          ++ map (typedId . entityMeta . snd) (typedFocusArguments x)
          ++ map (typedId . scalarMeta) (typedFocusScalars x) ++ map (typedId . valueMeta) (typedFocusValues x)
          ++ map assertionId (typedFocusAssertions x))
      requested = nub ((case focus of TypedRuleFocus -> [obj (typedAnalysisRule a),obj (typedAnalysisProposition a)]; _ -> [])
        ++ concatMap forDetail details ++ map obj expandedSources)
      edges = [e | e <- typedProjectionEdges value, typedEdgeFrom e `elem` requested, typedEdgeTo e `elem` requested]
      edgeIds = map typedEdgeId edges
      view = ProjectionView projectionViewFormat (projectionIdentity "typed-view" (typedProjectionId value,focus,expandedSources))
        (typedProjectionId value) "Typed grounded reference view: supplied tuples/values and actual expression/rule/proposition observations remain distinct. Omitted context is in the complete typed projection."
        requested edgeIds [typedNodeId n | n <- typedProjectionNodes value, typedNodeId n `notElem` requested]
        [typedEdgeId e | e <- typedProjectionEdges value, typedEdgeId e `notElem` edgeIds]
        [ViewBinding key ("node-" <> key) | key <- requested]
        [EdgeBinding i key ("edge-" <> key) | (i,key) <- zip [0..] edgeIds]
  case validateTypedView p view of [] -> Right view; errors -> Left errors

validateTypedView :: TypedProjection -> ProjectionView -> [AuthoringDiagnostic]
validateTypedView p view =
  [issue "TVIEW" "/typedView" [] "view belongs to another projection or has invalid identity partitions/endpoints"
    | viewProjectionId view /= typedProjectionId value || not (partition nodes (viewIncludedNodes view) (viewOmittedNodes view))
      || not (partition edges (viewIncludedEdges view) (viewOmittedEdges view))
      || sort (map viewBindingProjectedId (viewNodeBindings view)) /= sort (viewIncludedNodes view)
      || map edgeBindingProjectedId (viewEdgeBindings view) /= viewIncludedEdges view
      || any (\binding -> viewBindingRenderedId binding /= "node-" <> viewBindingProjectedId binding) (viewNodeBindings view)
      || any (\(i,binding) -> edgeBindingIndex binding /= i || edgeBindingRenderedId binding /= "edge-" <> edgeBindingProjectedId binding) (zip [0..] (viewEdgeBindings view))
      || any (\e -> typedEdgeId e `elem` viewIncludedEdges view &&
        (typedEdgeFrom e `notElem` viewIncludedNodes view || typedEdgeTo e `notElem` viewIncludedNodes view)) (typedProjectionEdges value)]
  ++ [issue "TVIEWLIMIT" "/typedView" [] "reference view exceeds 64 objects or 128 connections; no truncation"
    | length (viewIncludedNodes view) > 64 || length (viewIncludedEdges view) > 128]
  where value = typedProjectionData p
        nodes = map typedNodeId (typedProjectionNodes value)
        edges = map typedEdgeId (typedProjectionEdges value)
        partition allIds yes no = length (yes ++ no) == length (nub (yes ++ no)) && sort allIds == sort (yes ++ no)

instance ToJSON TypedProjectedNode where toJSON = genericToJSON jsonOptions
instance ToJSON TypedProjectedEdge where toJSON = genericToJSON jsonOptions
instance ToJSON TypedProjectionData where toJSON = genericToJSON jsonOptions
instance ToJSON TypedInspection where toJSON = genericToJSON jsonOptions
instance ToJSON TypedFocus where toJSON = genericToJSON jsonOptions

checkedTypedView :: TypedProjection -> ProjectionView -> Either [AuthoringDiagnostic] ()
checkedTypedView p view = case validateTypedProjection (typedProjectionData p) ++ validateTypedView p view of
  [] -> Right ()
  errors -> Left errors

legacyTypedView :: TypedProjection -> ProjectionView -> Legacy.SemanticGraph
legacyTypedView p view = Legacy.SemanticGraph (viewId view) Legacy.CaseView
  [Legacy.GraphNode (typedNodeId n) (typedNodeKind n) (typedNodeLabel n) Nothing Nothing Nothing
    | key <- viewIncludedNodes view, n <- typedProjectionNodes value, typedNodeId n == key]
  [Legacy.GraphEdge (typedEdgeFrom e) (typedEdgeTo e) (typedEdgeKind e) (typedEdgeKind e)
    | key <- viewIncludedEdges view, e <- typedProjectionEdges value, typedEdgeId e == key]
  "Selected typed reference view; complete typed operands, supplied inputs and actual observations are in the typed projection companion."
  where value = typedProjectionData p

encodeTypedViewJson :: TypedProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeTypedViewJson p view = checkedTypedView p view >> pure (Legacy.encodeSemanticGraph (legacyTypedView p view))

encodeTypedViewXml :: TypedProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeTypedViewXml p view = do
  checkedTypedView p view
  either (\reason -> Left [issue "TXML" "/typedView" [] reason]) Right (Legacy.encodeSemanticGraphXml (legacyTypedView p view))

-- Reference presentation only: uses the existing wrap/XML primitives, semantic
-- graph JSON/XML encoder and view/edge-binding contracts, not a canvas engine.
encodeTypedViewSvg :: TypedProjection -> ProjectionView -> Either [AuthoringDiagnostic] BS.ByteString
encodeTypedViewSvg p view = do
  checkedTypedView p view
  let value = typedProjectionData p
      snapshot = typedProjectionSnapshot value
      d = typedSnapshotDocument snapshot
      a = typedSnapshotAnalysis snapshot
      nodes = [n | key <- viewIncludedNodes view, n <- typedProjectionNodes value, typedNodeId n == key]
      edges = [e | key <- viewIncludedEdges view, e <- typedProjectionEdges value, typedEdgeId e == key]
      line key select list = maybe [] select (find ((== key) . fst) list)
      supplied TechnicalTrue = "technical true (explicitly supplied)"
      supplied TechnicalFalse = "technical false (explicitly supplied; no absence inference)"
      supplied (TechnicalUnresolved reason) = "unresolved: " <> reason
      exact (ExactInteger n) = T.pack (show n)
      exact (UnknownInteger expected reason) = "unresolved (expected " <> expected <> "): " <> reason
      scope s = "Scope actor: " <> scopeActor s <> " | Context: " <> scopeContext s
      observed n = case typedNodeObservation n of
        Just o -> ["Computed " <> typedObservationCategory o <> ": " <> typedObservedStatus o,
          "Evaluation: " <> typedObservedState o] ++ maybe [] (\x -> ["Proposition resolution: " <> x]) (typedPropositionResolution o)
        Nothing -> if typedNodeKind n == "occurrence" then ["No computed result", "Evaluation not requested"] else []
      body n = let key = typedNodeAuthoredId n in case typedNodeKind n of
        "assessment" -> line key (\(_,x) -> [if typedNodeSelected n == Just True then "SELECTED for this analysis" else "UNSELECTED; no attributed computation",
          "Supplied classification: " <> supplied (typedClassification x),scope (typedAssessmentScope x),
          "Reason: " <> typedAssessmentReason x,"Issuer: " <> typedIssuer x,
          "Origin: " <> typedOrigin x <> " | Basis: " <> typedBasis x]) [(typedId (typedAssessmentMeta x),x) | x <- typedAssessments d]
        "value" -> line key (\(_,x) -> [if typedNodeSelected n == Just True then "SELECTED supplied value" else "UNSELECTED supplied value",
          "Exact supplied integer: " <> exact (valueExact x),scope (valueScope x),"Reason: " <> valueReason x,"Issuer: " <> valueIssuer x]) [(typedId (valueMeta x),x) | x <- typedValues d]
        "scalar" -> line key (\(_,x) -> ["Declared scalar type: " <> scalarDeclaredType x] ++ maybe [] (\s -> ["External normalisation: " <> s]) (scalarNormalisation x)) [(typedId (scalarMeta x),x) | x <- typedScalars d]
        "predicate" -> line key (\(_,x) -> ["Typed predicate declaration"] ++ ["Argument " <> T.pack (show i) <> " (" <> argumentRole r <> "): " <> argumentType r | (i,r) <- zip [0 :: Int ..] (predicateRoles x)]) [(typedId (predicateMeta x),x) | x <- typedPredicates d]
        "application" -> line key (\(_,x) -> ["Ground tuple: " <> tuplePredicate (applicationTuple x) <> "(" <> T.intercalate ", " (tupleArguments (applicationTuple x)) <> ")",
          "Authored ground application; supplied selection and computed expression remain separate."]) [(typedId (applicationMeta x),x) | x <- typedApplications d]
        "entity" -> line key (\(_,x) -> ["Concrete entity | Nominal type: " <> entityNominalType x]) [(typedId (entityMeta x),x) | x <- typedEntities d]
        "occurrence" -> line key (\(_,x) -> case expressionForm x of
            GroundApplication app -> ["Ground predicate expression | Application: " <> app]
            IntegerComparison op l r -> ["Integer comparison: " <> l <> " " <> op <> " " <> r,"Result is computed from supplied operands."]
            TypedAll -> ["All required (ground typed expressions)"]
            TypedAny -> ["At least one required (ground typed expressions)"])
          [(typedId (expressionMeta x),x) | x <- typedExpressions d] ++ observed n
        "rule" -> ["Selected grounded establish rule; no parameters or actor aggregation."] ++ observed n
        "proposition" -> ["Technical proposition, not a legal disposition."] ++ observed n
        "assertion" -> line key (\(_,x) -> [scope (assertionScope x),"Authored case material; no computed status."]) [(assertionId x,x) | x <- typedCaseAssertions d]
        "source" -> line key (\(_,x) -> ["Original source kind: " <> sourceKind x,maybe "No locator" id (sourceLocator x)]
          ++ ["Original anchored excerpt: " <> excerpt | edge <- edges, Just ref <- [typedEdgeOriginal edge], referenceSource ref == key,
            Right recovered <- [recoverTypedSource p ref], Just excerpt <- [excerptText recovered]]
          ++ ["Locator/unanchored references do not invent an excerpt."]) [(sourceId x,x) | x <- typedOriginalSources d]
        _ -> []
      citation n = ["Source/citation: " <> cited | (_,m) <- typedObjects d, typedId m == typedNodeAuthoredId n, Just cited <- [typedCitation m]]
      cardLines n = concatMap (concatMap (wrap 112) . T.lines) (typedNodeLabel n : body n ++ citation n)
      rows = [(n,cardLines n) | n <- nodes]
      starts = scanl (\y (_,ls) -> y + 54 + 21 * length ls + 20) 160 rows
      positions = Map.fromList [(typedNodeId n,(y,54 + 21 * length ls)) | ((n,ls),y) <- zip rows starts]
      gutter = 90 + 8 * length edges
      left = gutter + 45
      width = left + 1010
      legendTop = 175 + sum [74 + 21 * length ls | (_,ls) <- rows]
      legendLines = concatMap (wrap 155 . label) edges
      height = legendTop + 22 * length legendLines + 80
      text x y size weight content = "<text x=\"" <> number x <> "\" y=\"" <> number y <> "\" font-size=\"" <> number size <> "\" font-weight=\"" <> weight <> "\">" <> escape content <> "</text>"
      card (n,ls) = let (y,h) = Map.findWithDefault (0,0) (typedNodeId n) positions in
        "<g id=\"node-" <> typedNodeId n <> "\" data-authored-id=\"" <> escape (typedNodeAuthoredId n) <> "\">"
        <> "<rect x=\"" <> number left <> "\" y=\"" <> number y <> "\" width=\"980\" height=\"" <> number h <> "\" rx=\"5\" fill=\"white\" stroke=\"#c5d2e2\"/>"
        <> text (left+16) (y+22) 12 "bold" (T.toUpper (typedNodeKind n) <> " · " <> typedNodeAuthoredId n)
        <> T.concat [text (left+16) (y+46+i*21) 15 "normal" s | (i,s) <- zip [0..] ls] <> "</g>"
      connection (i,e) = let (fy,fh) = Map.findWithDefault (0,0) (typedEdgeFrom e) positions
                             (ty,th) = Map.findWithDefault (0,0) (typedEdgeTo e) positions
                             lane = 25 + i * 8
                             y1 = fy + div fh 2; y2 = ty + div th 2
                         in "<path id=\"edge-" <> typedEdgeId e <> "\" d=\"M " <> number left <> " " <> number y1 <> " H " <> number lane <> " V " <> number y2 <> " H " <> number left
                           <> "\" fill=\"none\" stroke=\"#72839b\" marker-end=\"url(#arrow)\"/>"
      label e = typedEdgeKind e <> maybe "" (\i -> " [argument " <> T.pack (show i) <> "]") (typedEdgePosition e)
        <> maybe "" (" " <>) (typedEdgeRole e) <> " · "
        <> maybe "?" typedNodeLabel (find ((== typedEdgeFrom e) . typedNodeId) nodes) <> " → "
        <> maybe "?" typedNodeLabel (find ((== typedEdgeTo e) . typedNodeId) nodes)
      svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"" <> number width <> "\" height=\"" <> number height <> "\" viewBox=\"0 0 " <> number width <> " " <> number height <> "\">"
        <> "<defs><marker id=\"arrow\" markerWidth=\"6\" markerHeight=\"6\" refX=\"5\" refY=\"3\" orient=\"auto\"><path d=\"M0,0 L6,3 L0,6\" fill=\"#72839b\"/></marker></defs>"
        <> "<rect width=\"100%\" height=\"100%\" fill=\"#f6f8fc\"/><g font-family=\"Arial, sans-serif\" fill=\"#142038\">"
        <> text 24 32 22 "bold" "Ground typed analysis — explicit inputs and computed results"
        <> text 24 62 14 "normal" ("Analysis: " <> typedAnalysisId a <> " | " <> scope (typedAnalysisScope a))
        <> text 24 91 13 "normal" "Integer comparison is not physical-unit checking. Supplied classifications are not evidence assessments."
        <> text 24 120 13 "normal" "Original sources and all omitted context remain addressable through the complete typed projection."
        <> "<g id=\"connections\">" <> T.concat (map connection (zip [0..] edges)) <> "</g><g id=\"objects\">" <> T.concat (map card rows) <> "</g>"
        <> T.concat [text 24 (legendTop+22*i) 12 "normal" content | (i,content) <- zip [0..] legendLines] <> "</g></svg>"
  if T.all xmlCharacter svg then Right (UTF8.encodeUtf8 svg)
    else Left [issue "TXML" "/typedView" [] "XML 1.0 forbids a character in this view"]
