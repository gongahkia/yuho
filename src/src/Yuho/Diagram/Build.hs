{-# LANGUAGE OverloadedStrings #-}
module Yuho.Diagram.Build
  ( programGraph, caseGraph, presumptionGraph, typedFiniteGraph
  , typedFiniteCaseGraph ) where

import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.CoreYuho.Semantics (evaluateRequirement)
import Yuho.CoreYuho.Types
import Yuho.CoreYuho.TypedFinite
import Yuho.Diagram.Types
import Yuho.Exception.Types (Truth(..))

notice :: Text
notice = "Technical research statuses only; no guilt, conviction, acquittal, liability or sentence."

typedFiniteGraph :: DiagramView -> TypedFiniteProgram -> TypedFiniteResult -> SemanticGraph
typedFiniteGraph view program result = SemanticGraph (finiteProgramId program) view
  (distinctNodes nodes) (distinctEdges edges) notice
  where
    root = GraphNode (nodeId "program" (finiteProgramId program)) "program"
      (finiteProgramId program <> "\n" <> coreVersion) Nothing Nothing Nothing
    moduleNodes = [GraphNode (nodeId "module" (finiteModuleAlias item)) "module"
      (finiteModuleAlias item <> " = " <> finiteModuleName item <> "@" <>
        finiteModuleVersion item) Nothing Nothing (Just (finiteModuleAlias item))
      | item <- finiteModules program]
    typeNodes = [GraphNode (nodeId "entity-type" name) "entity-type" name Nothing Nothing Nothing
      | EntityTypeDecl name <- finiteEntityTypes program]
    entityNodes = [GraphNode (nodeId "entity" identifier) "entity"
      (identifier <> " : " <> kindValue) Nothing Nothing (Just kindValue)
      | EntityDecl identifier kindValue <- finiteEntities program]
    predicateNodes = [GraphNode (nodeId "predicate" (predicateName item)) "predicate"
      (predicateName item <> "(" <> Text.intercalate ", " (predicateArguments item) <> ")")
      Nothing Nothing Nothing | item <- finitePredicates program]
    scalarNodes = [GraphNode (nodeId "scalar" (scalarName item)) "scalar"
      (scalarName item <> " : " <> scalarTypeLabel (scalarType item)) Nothing
      (scalarStatus <$> Map.lookup (scalarName item) (finiteValues program)) Nothing
      | item <- finiteScalars program]
    factNodes = [GraphNode (nodeId "ground-fact" key) "ground-fact"
      key Nothing (Just (truthName (groundStatus item))) Nothing
      | item <- finiteFacts program,
        let key = groundKey (groundPredicate item) (groundArguments item)]
    requirementNodes = [GraphNode (nodeId "finite-requirement" (expressionLabel item))
      (expressionKind expression) (expressionLabel item <> "\n" <> expressionDetail item)
      Nothing (Just (truthName (expressionStatus item))) Nothing
      | item <- finiteResultExpressions result,
        Just expression <- [lookup (expressionLabel item) (finiteRequirements program)]]
    ruleNodes = [GraphNode (nodeId "finite-rule" (observedRule item)) "finite-rule"
      (observedRule item <> "\n" <> polarityLabel (observedPolarity item))
      (ruleCitation =<< findRule (observedRule item))
      (Just (truthName (observedStatus item))) Nothing
      | item <- finiteResultRules result]
    propositionNodes = [GraphNode (nodeId "proposition" (observedPropositionId item))
      (if propositionState item == "conflict" then "conflict" else "proposition")
      (observedPropositionId item <> "\n" <> propositionState item) Nothing
      (Just (truthName (propositionStatus item))) Nothing
      | item <- finiteResultPropositions result]
    normNodes = [GraphNode (nodeId "norm" (normName item)) "norm"
      (normName item <> "\n" <> normModalityLabel (normModality item)
        <> " — " <> normSubject item) (normCitation item)
      (ruleObservationStatus ("r:norm:" <> normName item)) (Just (normSubject item))
      | item <- finiteNorms program]
    routeNodes = [GraphNode (nodeId "responsibility-route" (routeName item))
      "responsibility-route" (routeName item <> "\n" <> responsibilityKindLabel (routeKind item)
        <> " — " <> routeSubject item) (routeCitation item)
      (ruleObservationStatus ("r:route:" <> routeName item)) (Just (routeSubject item))
      | item <- finiteRoutes program]
    nodes = root : moduleNodes ++ typeNodes ++ entityNodes ++ predicateNodes ++ scalarNodes
      ++ factNodes ++ requirementNodes ++ ruleNodes ++ normNodes ++ routeNodes ++ propositionNodes
    entityEdges = [GraphEdge (nodeId "entity-type" kindValue) (nodeId "entity" identifier)
      "instance" "nominal member" | EntityDecl identifier kindValue <- finiteEntities program]
    predicateEdges = [GraphEdge (nodeId "entity-type" kindValue)
      (nodeId "predicate" (predicateName predicate)) "argument-type"
      (Text.pack (show position)) | predicate <- finitePredicates program,
      (position,kindValue) <- zip [1 :: Int ..] (predicateArguments predicate)]
    factEdges = concat
      [[GraphEdge (nodeId "entity" argument) (nodeId "ground-fact" key)
          "ground-argument" (Text.pack (show position))
        | (position,argument) <- zip [1 :: Int ..] (groundArguments item)]
       ++ [GraphEdge (nodeId "predicate" (groundPredicate item)) (nodeId "ground-fact" key)
          "application" "classified application"]
      | item <- finiteFacts program,
        let key = groundKey (groundPredicate item) (groundArguments item)]
    ruleEdges = [GraphEdge (nodeId "finite-rule" (observedRule item))
      (nodeId "proposition" (observedProposition item)) "concludes"
      (polarityLabel (observedPolarity item)) | item <- finiteResultRules result]
    priorityEdges = [GraphEdge (nodeId "finite-rule" high) (nodeId "finite-rule" low)
      "priority" "explicitly over" | PriorityDecl high low <- finitePriorities program]
    moduleEdges = concat
      [[GraphEdge (nodeId "module" (finiteModuleAlias item))
          (nodeId "program" (finiteProgramId program)) "import" "exact-version import"]
       ++ [GraphEdge (nodeId "module" (finiteModuleAlias item))
          (nodeId (exportNodeKind kindValue) identifier) "export" kindValue
          | (kindValue,identifier) <- finiteModuleExports item]
      | item <- finiteModules program]
    rootEdges = [GraphEdge (nodeId "proposition" proposition)
      (graphNodeId root) "technical-result" "independent proposition"
      | proposition <- finitePropositions program]
    normEdges = [GraphEdge (nodeId "norm" (normName item))
      (nodeId "proposition" (normAction item)) "normative-position"
      (normModalityLabel (normModality item)) | item <- finiteNorms program]
    routeEdges = [GraphEdge (nodeId "responsibility-route" (routeName item))
      (nodeId "proposition" (routeTarget item)) "responsibility-target"
      "explicit authored route" | item <- finiteRoutes program]
    edges = moduleEdges ++ entityEdges ++ predicateEdges ++ factEdges ++ ruleEdges
      ++ priorityEdges ++ normEdges ++ routeEdges ++ rootEdges
    findRule identifier = case filter ((== identifier) . ruleName) (finiteRules program) of
      item:_ -> Just item
      [] -> Nothing
    exportNodeKind kindValue = case kindValue of
      "entity-type" -> "entity-type"; "entity" -> "entity"; "predicate" -> "predicate"
      "scalar" -> "scalar"; "proposition" -> "proposition"
      "requirement" -> "finite-requirement"; "rule" -> "finite-rule"
      _ -> "export"
    coreVersion | null (finiteNorms program) && null (finiteRoutes program) = "Core Yuho v0.2"
                | otherwise = "Core Yuho v0.3"
    ruleObservationStatus identifier = case
        [truthName (observedStatus item) | item <- finiteResultRules result,
          observedRule item == identifier] of
      value:_ -> Just value
      [] -> Nothing

typedFiniteCaseGraph :: DiagramView -> Text -> [(Text,TypedFiniteResult)]
  -> [(Text,GroundFact,[Text])] -> SemanticGraph
typedFiniteCaseGraph view caseId results shared = SemanticGraph caseId view
  (distinctNodes nodes) (distinctEdges edges) notice
  where
    root = GraphNode (nodeId "case" caseId) "case"
      (caseId <> "\nindependent typed allegations") Nothing Nothing Nothing
    allegationNodes = [GraphNode (nodeId "allegation" identifier) "allegation"
      identifier Nothing Nothing Nothing | (identifier,_) <- results]
    sharedNodes = [GraphNode (nodeId "shared-ground-fact" identifier) "shared-fact"
      (identifier <> "\n" <> groundKey (groundPredicate fact) (groundArguments fact))
      Nothing (Just (truthName (groundStatus fact))) Nothing | (identifier,fact,_) <- shared]
    propositionNodes = [GraphNode (nodeId "case-proposition" (allegation <> "--" <> observedPropositionId row))
      (if propositionState row == "conflict" then "conflict" else "proposition")
      (observedPropositionId row <> "\n" <> propositionState row) Nothing
      (Just (truthName (propositionStatus row))) (Just allegation)
      | (allegation,result) <- results, row <- finiteResultPropositions result]
    nodes = root : allegationNodes ++ sharedNodes ++ propositionNodes
    edges = [GraphEdge (graphNodeId root) (nodeId "allegation" identifier)
        "contains" "independent allegation" | (identifier,_) <- results]
      ++ [GraphEdge (nodeId "shared-ground-fact" sharedId) (nodeId "allegation" allegation)
          "fact-binding" "explicit shared classification"
        | (sharedId,_,destinations) <- shared, allegation <- destinations]
      ++ [GraphEdge (nodeId "case-proposition" (allegation <> "--" <> observedPropositionId row))
          (nodeId "allegation" allegation) "technical-result" "no aggregate status"
        | (allegation,result) <- results, row <- finiteResultPropositions result]

scalarTypeLabel :: ScalarType -> Text
scalarTypeLabel IntegerType = "integer"
scalarTypeLabel DateType = "date"
scalarTypeLabel (EnumType name _) = "enum " <> name
scalarTypeLabel (MoneyType currency) = "money " <> currency

scalarStatus :: ScalarValue -> Text
scalarStatus (ScalarUnresolved _ _) = "unresolved"
scalarStatus _ = "known"

expressionKind :: FiniteExpr -> Text
expressionKind expression = case expression of
  PredicateExpr _ _ -> "predicate-application"
  ComparisonExpr _ _ _ _ -> "comparison"
  AllExpr _ -> "all"
  AnyExpr _ -> "any"
  NotExpr _ -> "negation"
  ForallExpr _ _ _ -> "forall"
  ExistsExpr _ _ _ -> "exists"
  CardinalityExpr _ _ _ -> "cardinality"
  ReferenceExpr _ -> "requirement-reference"

polarityLabel :: RulePolarity -> Text
polarityLabel Establish = "establishes"
polarityLabel Defeat = "defeats"

normModalityLabel :: NormModality -> Text
normModalityLabel Required = "required"
normModalityLabel Prohibited = "prohibited"
normModalityLabel Permitted = "permitted"

responsibilityKindLabel :: ResponsibilityKind -> Text
responsibilityKindLabel PrincipalConduct = "principal-conduct"
responsibilityKindLabel JointConduct = "joint-conduct"
responsibilityKindLabel Instigation = "instigation"
responsibilityKindLabel Conspiracy = "conspiracy"
responsibilityKindLabel IntentionalAid = "intentional-aid"
responsibilityKindLabel AttemptRoute = "attempt"
responsibilityKindLabel (AuthoredContribution value) = "other:" <> value

programGraph :: DiagramView -> CoreProgram -> SemanticGraph
programGraph view program = SemanticGraph (coreProgramId program) view nodes edges notice
  where
    (requirementNodes,requirementEdges) = foldMap requirementGraph
      (coreProgramRoots program
        ++ concatMap coreRuleRequirements (coreProgramRules program)
        ++ concatMap coreDefinitionRequirements (coreProgramDefinitions program))
    nodes = distinctNodes $ case view of
      ModulesView -> moduleNodes ++ exportNodes ++ [programNode] ++ temporalNodes
      _ -> [programNode] ++ moduleNodes ++ temporalNodes ++ definitionNodes
        ++ ruleNodes ++ elementNodes ++ requirementNodes ++ attachmentNodes
        ++ penaltyNodes ++ actorNodes ++ relationNodes
    edges = distinctEdges $ case view of
      ModulesView -> moduleEdges ++ exportEdges ++ temporalEdges
      _ -> moduleEdges ++ temporalEdges ++ definitionEdges ++ ruleEdges
        ++ requirementEdges ++ attachmentEdges ++ penaltyEdges ++ relationEdges
    programNode = GraphNode (nodeId "program" (coreProgramId program)) "program"
      (coreProgramId program) Nothing Nothing Nothing
    moduleNodes = [GraphNode (nodeId "module" (coreModuleAlias item)) "module"
      (coreModuleAlias item <> " = " <> coreModuleName item <> "@" <>
        coreModuleVersion item) Nothing Nothing (Just (coreModuleAlias item))
      | item <- coreProgramModules program]
    moduleEdges = [GraphEdge (nodeId "module" (coreModuleAlias item))
      (graphNodeId programNode) "import" "exact import"
      | item <- coreProgramModules program]
    exportNodes = [GraphNode (nodeId "export" (coreModuleAlias item <> "::" <> exported))
      "export" exported Nothing Nothing (Just (coreModuleAlias item))
      | item <- coreProgramModules program, exported <- coreModuleExports item]
    exportEdges = concat
      [[GraphEdge (nodeId "module" (coreModuleAlias item))
          (nodeId "export" (coreModuleAlias item <> "::" <> exported)) "export" "exports",
        GraphEdge (nodeId "export" (coreModuleAlias item <> "::" <> exported))
          (graphNodeId programNode) "compose" "explicit use"]
      | item <- coreProgramModules program, exported <- coreModuleExports item]
    temporalNodes = case coreProgramTemporal program of
      Nothing -> []
      Just item -> [GraphNode (nodeId "temporal" (coreTemporalExpression item))
        "temporal" (coreTemporalExpression item <> "\n" <> coreTemporalReason item)
        Nothing (Just "selected") Nothing]
    temporalEdges = case coreProgramTemporal program of
      Nothing -> []
      Just item -> [GraphEdge (nodeId "temporal" (coreTemporalExpression item))
        (graphNodeId programNode) "selects" "mechanical interval match"]
    definitionNodes = [GraphNode (nodeId "definition" (coreDefinitionId item))
      "definition" (coreDefinitionId item) (sectionCitation (coreDefinitionSections item))
      Nothing Nothing | item <- coreProgramDefinitions program]
    definitionEdges = concat
      [ [GraphEdge (nodeId "definition" dependency) (nodeId "definition" (coreDefinitionId item))
          "definition-reference" "derives"
        | dependency <- coreDefinitionDependencies item]
        ++ [GraphEdge (nodeId "requirement" (requirementId requirement))
          (nodeId "definition" (coreDefinitionId item)) "defines" "requirement"
        | requirement <- coreDefinitionRequirements item]
      | item <- coreProgramDefinitions program]
    ruleNodes = [GraphNode (nodeId "rule" (coreRuleId item))
      (ruleKindText (coreRuleKind item)) (coreRuleId item)
      (sectionCitation (coreRuleSections item)) (ruleStatus item) Nothing
      | item <- coreProgramRules program]
    ruleEdges = concat
      [ [GraphEdge (nodeId "element" (coreElementId element))
          (nodeId "rule" (coreRuleId item)) "element" (coreElementCategory element)
        | element <- coreRuleElements item]
        ++ [GraphEdge (nodeId "requirement" (requirementId requirement))
          (nodeId "rule" (coreRuleId item)) "requires" "root requirement"
        | requirement <- coreRuleRequirements item]
      | item <- coreProgramRules program]
    elementNodes = [GraphNode (nodeId "element" (coreElementId item)) "input"
      (coreElementId item <> "\n" <> coreElementCategory item)
      (nonEmpty (coreElementCitation item)) (assignmentStatus (coreElementId item)) Nothing
      | rule <- coreProgramRules program, item <- coreRuleElements rule]
    attachmentNodes = [GraphNode (nodeId "attachment" (coreAttachmentId item))
      "attachment" (Text.intercalate "\n" (filter (not . Text.null)
        [coreAttachmentId item,maybe "" ("actor " <>) (coreAttachmentActor item),
         maybe "" ("role " <>) (coreAttachmentRole item),
         maybe "" ("context " <>) (coreAttachmentContext item)])) Nothing Nothing Nothing
      | item <- coreProgramAttachments program]
    attachmentEdges = concat
      [[GraphEdge (nodeId "rule" (coreAttachmentException item))
          (nodeId "attachment" (coreAttachmentId item)) "exception" "guard",
        GraphEdge (nodeId "attachment" (coreAttachmentId item))
          (nodeId "rule" (coreAttachmentTarget item)) "attaches" "defeats if satisfied"]
      | item <- coreProgramAttachments program]
    penaltyNodes = [GraphNode (nodeId "penalty" (corePenaltyId item)) "penalty"
      (corePenaltyId item <> "\n" <> termLabel (corePenaltyTerm item))
      (Just (corePenaltyProvision item)) Nothing Nothing
      | item <- coreProgramPenalties program]
    penaltyEdges = [GraphEdge (nodeId "rule" (corePenaltyTarget item))
      (nodeId "penalty" (corePenaltyId item)) "candidate-penalty" "candidate only"
      | item <- coreProgramPenalties program]
    actorNodes = [GraphNode (nodeId "actor" (coreActorId item)) "actor"
      (coreActorId item <> "\n" <> coreActorRole item) Nothing Nothing Nothing
      | item <- coreProgramActors program]
    relationNodes = [GraphNode (nodeId "relation" (coreRelationId item)) "relation"
      (Text.intercalate "\n" [coreRelationId item,coreRelationFrom item <> " -> " <>
        coreRelationTo item,"target " <> coreRelationTarget item]) Nothing Nothing Nothing
      | item <- coreProgramRelations program]
    relationEdges = [GraphEdge (nodeId "relation" (coreRelationId item))
      (nodeId "rule" (coreRelationTarget item)) "participation-target" "targets"
      | item <- coreProgramRelations program]
    assignmentStatus identifier = truthText <$> Map.lookup identifier
      (coreProgramAssignments program)
    ruleStatus item = case Map.lookup (coreRuleTechnicalId item)
        (coreProgramBranchReasons program) of
      Just reason -> Just reason
      Nothing -> case Map.lookup (coreRuleTechnicalId item) (coreProgramRuleStatuses program) of
          Just status -> Just status
          Nothing -> case coreRuleRequirements item of
            [root] -> either (const Nothing) (Just . truthText)
              (evaluateRequirement (coreProgramAssignments program) root)
            _ -> Nothing

caseGraph :: DiagramView -> CoreCase -> SemanticGraph
caseGraph view item = SemanticGraph (coreCaseId item) view nodes edges notice
  where
    caseNode = GraphNode (nodeId "case" (coreCaseId item)) "case"
      (coreCaseId item <> "\nordered, independent allegations") Nothing Nothing Nothing
    actors = [GraphNode (nodeId "actor" (coreActorId actor)) "actor"
      (coreActorId actor <> "\n" <> coreActorRole actor) Nothing Nothing Nothing
      | actor <- coreCaseActors item]
    allegations = [GraphNode (nodeId "allegation" (coreAllegationId allegation))
      "allegation" (Text.intercalate "\n"
        [coreAllegationId allegation,ruleKindText (coreAllegationKind allegation)
          <> " " <> coreAllegationTarget allegation,
         "role " <> coreAllegationRole allegation]) Nothing
      (Just (coreAllegationStatus allegation)) Nothing
      | allegation <- coreCaseAllegations item]
    facts = [GraphNode (nodeId "fact" (coreSharedFactId fact)) "shared-fact"
      (Text.intercalate "\n" [coreSharedFactId fact,coreSharedFactKind fact,
        coreSharedFactSubject fact]) Nothing (Just (coreSharedFactStatus fact)) Nothing
      | fact <- coreCaseFacts item]
    guardNodes = [GraphNode (nodeId "trace" (coreAllegationId allegation <> "--exception"))
      "exception" "attached exception guard" Nothing (Just "satisfied") Nothing
      | allegation <- coreCaseAllegations item, coreAllegationStatus allegation == "defeated"]
    nodes = distinctNodes (caseNode : actors ++ facts ++ allegations ++ guardNodes)
    edges = distinctEdges $
      [GraphEdge (graphNodeId caseNode) (nodeId "allegation" (coreAllegationId allegation))
        "contains" "authored order" | allegation <- coreCaseAllegations item]
      ++ [GraphEdge (nodeId "actor" (coreActorId actor))
          (nodeId "allegation" (coreAllegationId allegation)) "role" (coreAllegationRole allegation)
        | actor <- coreCaseActors item, allegation <- coreCaseAllegations item,
          coreActorRole actor == coreAllegationRole allegation]
      ++ [GraphEdge (nodeId "fact" (coreSharedFactId fact))
          (nodeId "allegation" allegation) "fact-binding" destination
        | fact <- coreCaseFacts item, (allegation,destination) <- coreSharedFactDestinations fact]
      ++ [GraphEdge (nodeId "trace" (coreAllegationId allegation <> "--exception"))
          (nodeId "allegation" (coreAllegationId allegation)) "defeats" "guard satisfied"
        | allegation <- coreCaseAllegations item, coreAllegationStatus allegation == "defeated"]

presumptionGraph :: CorePresumptionProgram -> SemanticGraph
presumptionGraph program = SemanticGraph (corePresumptionProgramId program) TraceView nodes edges notice
  where
    root = GraphNode (nodeId "presumption-program" (corePresumptionProgramId program))
      "presumption-program" (Text.intercalate "\n"
        [corePresumptionProgramId program,
         "burden: " <> corePresumptionBurdenBearer program,
         "standard: " <> corePresumptionStandard program]) Nothing
      (Just (corePresumptionFinalStatus program)) Nothing
    rows = concatMap nodesFor (corePresumptions program)
    nodes = distinctNodes (root : rows)
    edges = distinctEdges (concatMap edgesFor (corePresumptions program))
    nodesFor item =
      [GraphNode (nodeId "input" (corePresumptionTrigger item)) "input"
        (corePresumptionTrigger item) Nothing Nothing Nothing,
       GraphNode (nodeId "input" (corePresumptionRebuttal item)) "input"
        (corePresumptionRebuttal item) Nothing Nothing Nothing,
       GraphNode (nodeId "presumption" (corePresumptionId item)) "presumption"
        (Text.intercalate "\n" [corePresumptionId item,
          "target " <> corePresumptionTarget item]) (Just (corePresumptionSource item))
        (Just (corePresumptionState item)) Nothing]
    edgesFor item =
      [GraphEdge (nodeId "input" (corePresumptionTrigger item))
        (nodeId "presumption" (corePresumptionId item)) "trigger" "trigger",
       GraphEdge (nodeId "input" (corePresumptionRebuttal item))
        (nodeId "presumption" (corePresumptionId item)) "rebuttal" "rebuttal",
       GraphEdge (nodeId "presumption" (corePresumptionId item))
        (graphNodeId root) "derives" (corePresumptionState item)]

requirementGraph :: CoreRequirement -> ([GraphNode],[GraphEdge])
requirementGraph requirement = case requirement of
  CoreInput identifier citation status ->
    ([GraphNode (nodeId "requirement" identifier) "input" identifier
      (nonEmpty citation) (truthText <$> status) Nothing],[])
  CoreAll identifier members -> group "all" identifier members
  CoreAny identifier members -> group "any" identifier members
  where
    group kindValue identifier members =
      let parts = map requirementGraph members
          nodes = concatMap fst parts
          edges = concatMap snd parts
          parent = nodeId "requirement" identifier
      in (GraphNode parent kindValue identifier Nothing Nothing Nothing : nodes,
          [GraphEdge (nodeId "requirement" (requirementId member)) parent
            "member" kindValue | member <- members] ++ edges)

requirementId :: CoreRequirement -> Text
requirementId requirement = case requirement of
  CoreInput identifier _ _ -> identifier
  CoreAll identifier _ -> identifier
  CoreAny identifier _ -> identifier

ruleKindText :: CoreRuleKind -> Text
ruleKindText kindValue = case kindValue of
  CoreOffence -> "offence"
  CoreException -> "exception"
  CoreParticipation -> "participation"
  CoreAttempt -> "attempt"

truthText :: CoreTruth -> Text
truthText value = case value of
  TrueValue -> "satisfied"
  FalseValue -> "not_satisfied"
  UnresolvedValue -> "unresolved"

sectionCitation :: [Text] -> Maybe Text
sectionCitation [] = Nothing
sectionCitation values = Just ("provisions " <> Text.intercalate ", " values)

nonEmpty :: Text -> Maybe Text
nonEmpty value | Text.null value = Nothing
nonEmpty value = Just value

termLabel :: CorePenaltyTerm -> Text
termLabel term = case term of
  CoreImprisonment _ low high unit -> "imprisonment " <> low <> ".." <> high <> " " <> unit
  CoreFine _ currency low high -> "fine " <> currency <> " " <> low <> ".." <> high
  CoreLifeImprisonment _ -> "life imprisonment"
  CoreCaning _ low high -> "caning " <> low <> ".." <> high <> " strokes"
  CoreDeath _ -> "death"
  CoreAllTerms _ values -> "all of: " <> Text.intercalate ", " (map termLabel values)
  CoreExactlyOneTerm _ values -> "exactly one: " <> Text.intercalate ", " (map termLabel values)
  CoreOneOrMoreTerms _ values -> "one or more: " <> Text.intercalate ", " (map termLabel values)

distinctNodes :: [GraphNode] -> [GraphNode]
distinctNodes = go []
  where
    go _ [] = []
    go seen (item:rest)
      | graphNodeId item `elem` seen = go seen rest
      | otherwise = item : go (graphNodeId item : seen) rest

distinctEdges :: [GraphEdge] -> [GraphEdge]
distinctEdges = go []
  where
    key item = (graphEdgeFrom item,graphEdgeTo item,graphEdgeKind item)
    go _ [] = []
    go seen (item:rest)
      | key item `elem` seen = go seen rest
      | otherwise = item : go (key item : seen) rest
