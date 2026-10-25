{-# LANGUAGE OverloadedStrings #-}
module Yuho.Diagram.Build
  ( programGraph, caseGraph, presumptionGraph, typedFiniteGraph
  , typedFiniteCaseGraph ) where

import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
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
    scalarNodes = [withObservation (CoreObservation "supplied" Nothing Nothing Nothing) $
      GraphNode (nodeId "scalar" (scalarName item)) "scalar"
      (scalarName item <> " : " <> scalarTypeLabel (scalarType item)
        <> maybe "" (("\nsupplied value: " <>) . scalarValueLabel)
             (Map.lookup (scalarName item) (finiteValues program))) Nothing
      (scalarStatus <$> Map.lookup (scalarName item) (finiteValues program)) Nothing
      | item <- finiteScalars program]
    factNodes = [GraphNode (nodeId "ground-fact" (groundIdentityText (groundPredicate item) (groundArguments item))) "ground-fact"
      key Nothing (Just (truthName (groundStatus item))) Nothing
      | item <- finiteFacts program,
        let key = groundKey (groundPredicate item) (groundArguments item)]
    requirementNodes = [withObservation (computed (truthName (expressionStatus item))) $
      GraphNode (nodeId "finite-requirement" (expressionLabel item))
      (expressionKind expression) (expressionLabel item <> "\n" <> expressionDetail item)
      Nothing (Just (truthName (expressionStatus item))) Nothing
      | item <- finiteResultExpressions result,
        Just expression <- [lookup (expressionLabel item) (finiteRequirements program)]]
    ruleNodes = [withObservation (computed (truthName (observedStatus item))) $
      GraphNode (nodeId "finite-rule" (observedRule item)) "finite-rule"
      (observedRule item <> "\n" <> polarityLabel (observedPolarity item))
      (ruleCitation =<< findRule (observedRule item))
      (Just (truthName (observedStatus item))) Nothing
      | item <- finiteResultRules result]
    propositionNodes = [withObservation (computed (truthName (propositionStatus item))) $
      GraphNode (nodeId "proposition" (observedPropositionId item))
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
      [[GraphEdge (nodeId "entity" argument) (nodeId "ground-fact" (groundIdentityText (groundPredicate item) (groundArguments item)))
          "ground-argument" (Text.pack (show position))
        | (position,argument) <- zip [1 :: Int ..] (groundArguments item)]
       ++ [GraphEdge (nodeId "predicate" (groundPredicate item)) (nodeId "ground-fact" (groundIdentityText (groundPredicate item) (groundArguments item)))
          "application" "classified application"]
      | item <- finiteFacts program]
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
    operandEdges = [GraphEdge (nodeId "scalar" operand)
        (nodeId "finite-requirement" identifier) "operand" "supplied scalar operand"
      | (identifier,expression) <- finiteRequirements program, operand <- scalarOperands expression]
    edges = moduleEdges ++ entityEdges ++ predicateEdges ++ factEdges ++ ruleEdges ++ operandEdges
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
  nodes (distinctEdges edges) notice
  where
    root = GraphNode (nodeId "case" caseId) "case"
      (caseId <> "\nindependent typed allegations") Nothing Nothing Nothing
    allegationNodes = [GraphNode (nodeId "allegation" identifier) "allegation"
      identifier Nothing Nothing Nothing | (identifier,_) <- results]
    sharedNodes = [GraphNode (nodeId "shared-ground-fact" identifier) "shared-fact"
      (identifier <> "\n" <> groundKey (groundPredicate fact) (groundArguments fact))
      Nothing (Just (truthName (groundStatus fact))) Nothing | (identifier,fact,_) <- shared]
    -- Checked cases have unique allegations and each backend result has unique
    -- proposition observations. Retain every occurrence, without deduplicating
    -- away evidence of an identity error. Nodes and edges share the same keys.
    scopedPropositions =
      [(typedCasePropositionId allegation (observedPropositionId row),allegation,row)
      | (allegation,result) <- results, row <- finiteResultPropositions result]
    propositionNodes = [GraphNode identifier
      (if propositionState row == "conflict" then "conflict" else "proposition")
      (observedPropositionId row <> "\n" <> propositionState row) Nothing
      (Just (truthName (propositionStatus row))) (Just allegation)
      | (identifier,allegation,row) <- scopedPropositions]
    nodes = root : allegationNodes ++ sharedNodes ++ propositionNodes
    edges = [GraphEdge (graphNodeId root) (nodeId "allegation" identifier)
        "contains" "independent allegation" | (identifier,_) <- results]
      ++ [GraphEdge (nodeId "shared-ground-fact" sharedId) (nodeId "allegation" allegation)
          "fact-binding" "explicit shared classification"
        | (sharedId,_,destinations) <- shared, allegation <- destinations]
      ++ [GraphEdge identifier
          (nodeId "allegation" allegation) "technical-result" "no aggregate status"
        | (identifier,allegation,_) <- scopedPropositions]

-- Canonical pair of Unicode scalar-count-prefixed Text values. Decode each
-- decimal length up to ':', then consume exactly that many characters; neither
-- embedded delimiters nor Unicode can change the boundary between components.
-- The fixed node kind separates this namespace from other graph identities.
typedCasePropositionId :: Text -> Text -> Text
typedCasePropositionId allegation proposition = nodeId "case-proposition"
  (component allegation <> component proposition)
  where component value = Text.pack (show (Text.length value)) <> ":" <> value

scalarTypeLabel :: ScalarType -> Text
scalarTypeLabel IntegerType = "integer"
scalarTypeLabel DateType = "date"
scalarTypeLabel (EnumType name _) = "enum " <> name
scalarTypeLabel (MoneyType currency) = "money " <> currency

scalarStatus :: ScalarValue -> Text
scalarStatus (ScalarUnresolved _ _) = "unresolved"
scalarStatus _ = "known"

scalarValueLabel :: ScalarValue -> Text
scalarValueLabel value = case value of
  IntegerValue number -> Text.pack (show number)
  DateValue day -> Text.pack (show day)
  EnumValue domain member -> domain <> ":" <> member
  MoneyValue currency minor -> currency <> " " <> Text.pack (show minor) <> " minor units"
  ScalarUnresolved reason _ -> "unresolved (" <> reason <> ")"

scalarOperands :: FiniteExpr -> [Text]
scalarOperands expression = case expression of
  ComparisonExpr _ left right upper -> left:right:maybe [] pure upper
  AllExpr children -> concatMap scalarOperands children
  AnyExpr children -> concatMap scalarOperands children
  NotExpr child -> scalarOperands child
  ForallExpr _ _ child -> scalarOperands child
  ExistsExpr _ _ child -> scalarOperands child
  CardinalityExpr _ _ children -> concatMap scalarOperands children
  _ -> []

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
        ++ penaltyNodes ++ actorNodes ++ relationNodes ++ guardNodes
    edges = distinctEdges $ case view of
      ModulesView -> moduleEdges ++ exportEdges ++ temporalEdges
      _ -> moduleEdges ++ temporalEdges ++ definitionEdges ++ ruleEdges
        ++ requirementEdges ++ attachmentEdges ++ penaltyEdges ++ relationEdges ++ guardEdges
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
    ruleNodes = [withOptionalObservation (Map.lookup (coreRuleTechnicalId item) (coreProgramObservations program)) $
      GraphNode (nodeId "rule" (coreRuleId item))
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
    elementNodes = [withOptionalObservation (supplied <$> Map.lookup (coreElementId item)
        (coreProgramAssignments program)) $ GraphNode (nodeId "element" (coreElementId item)) "input"
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
    ruleStatus item = Map.lookup (coreRuleTechnicalId item) (coreProgramObservations program)
      >>= coreObservationValue
    authoredId technical = case [coreRuleId rule | rule <- coreProgramRules program,
        coreRuleTechnicalId rule == technical] of
      [identifier] -> Just identifier
      _ -> Nothing
    guardNodes = map guardNode (coreProgramGuards program)
    guardEdges = concat
      [[GraphEdge (nodeId "rule" target) (guardNodeId guard) "guard-target" "target computation"
        | Just target <- [authoredId (coreGuardTarget guard)]]
       ++ [GraphEdge (guardNodeId guard) (nodeId "rule" parent) "exception-guard" "defeats if satisfied"
          | Just parent <- [authoredId (coreGuardRule guard)]]
      | guard <- coreProgramGuards program]

caseGraph :: DiagramView -> CoreCase -> SemanticGraph
caseGraph view item = SemanticGraph (coreCaseId item) view nodes edges notice
  where
    caseNode = GraphNode (nodeId "case" (coreCaseId item)) "case"
      (coreCaseId item <> "\nordered, independent allegations") Nothing Nothing Nothing
    actors = [GraphNode (nodeId "actor" (coreActorId actor)) "actor"
      (coreActorId actor <> "\n" <> coreActorRole actor) Nothing Nothing Nothing
      | actor <- coreCaseActors item]
    allegations = [withObservation (coreAllegationObservation allegation) $
      GraphNode (nodeId "allegation" (coreAllegationId allegation))
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
    scopedGuards = [(allegation,guard) | allegation <- coreCaseAllegations item,
      guard <- coreAllegationGuards allegation]
    scopedGuardId allegation guard = nodeId "case-guard"
      (coreAllegationId allegation <> "/" <> coreGuardIdentity guard)
    guardNodes = [(guardNode guard)
      { graphNodeId = scopedGuardId allegation guard
      , graphNodeBoundary = Just ("allegation " <> coreAllegationId allegation) }
      | (allegation,guard) <- scopedGuards]
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
      ++ [GraphEdge (scopedGuardId allegation guard)
          (nodeId "allegation" (coreAllegationId allegation)) "exception-guard" "defeats if satisfied"
        | (allegation,guard) <- scopedGuards]

presumptionGraph :: CorePresumptionProgram -> SemanticGraph
presumptionGraph program = SemanticGraph (corePresumptionProgramId program) TraceView nodes edges notice
  where
    root = withObservation (computed (corePresumptionFinalStatus program)) $
      GraphNode (nodeId "presumption-program" (corePresumptionProgramId program))
      "presumption-program" (Text.intercalate "\n"
        [corePresumptionProgramId program,
         "burden: " <> corePresumptionBurdenBearer program,
         "standard: " <> corePresumptionStandard program,
         "context: " <> corePresumptionContext program]) Nothing
      (Just (corePresumptionFinalStatus program)) Nothing
    rows = concatMap nodesFor (corePresumptions program)
    targets = [withObservation (CoreObservation state (Just value) Nothing Nothing) $
        GraphNode (nodeId kind target) kind (target <> "\n" <> label) Nothing (Just value)
          (Just "global support; separate from downstream guard execution")
      | (target,direct,effective) <- corePresumptionTargets program
      , (kind,label,state,value) <- [("direct-input","direct supplied classification","supplied",direct)
          ,("effective-input","effective technical value","evaluated",effective)]]
    downstream = [withObservation observation $ GraphNode (nodeId "downstream-rule" identifier)
        "rule" (identifier <> "\ndownstream rule") Nothing (coreObservationValue observation) Nothing
      | (identifier,observation) <- Map.toAscList (corePresumptionObservations program)]
    guards = corePresumptionGuards program
    nodes = distinctNodes (root : rows ++ targets ++ downstream ++ map guardNode guards)
    edges = distinctEdges (concatMap edgesFor (corePresumptions program)
      ++ [GraphEdge (nodeId "direct-input" target) (nodeId "effective-input" target)
            "direct-support" "direct support retained"
          | (target,_,_) <- corePresumptionTargets program]
      ++ [GraphEdge (nodeId "downstream-rule" (coreGuardTarget guard))
            (guardNodeId guard) "guard-target" "target computation" | guard <- guards]
      ++ [GraphEdge (guardNodeId guard) (nodeId "downstream-rule" (coreGuardRule guard))
            "exception-guard" "defeats if satisfied" | guard <- guards]
      ++ [GraphEdge (nodeId "downstream-rule" identifier) (graphNodeId root)
            "technical-result" "root rule result" | Just identifier <- [corePresumptionRootRule program]])
    nodesFor item =
      [conditionNode (corePresumptionTrigger item),conditionNode (corePresumptionRebuttal item),
       withObservation (computed (corePresumptionState item)) $
       GraphNode (nodeId "presumption" (corePresumptionId item)) "presumption"
        (Text.intercalate "\n" [corePresumptionId item,
          "target " <> corePresumptionTarget item]) (Just (corePresumptionSource item))
        (Just (corePresumptionState item)) Nothing]
    conditionNode identifier = withOptionalObservation
      (computed <$> Map.lookup identifier (corePresumptionConditions program)) $
      GraphNode (nodeId "input" identifier) "input" identifier Nothing
        (Map.lookup identifier (corePresumptionConditions program)) (Just "global presumption condition")
    edgesFor item =
      [GraphEdge (nodeId "input" (corePresumptionTrigger item))
        (nodeId "presumption" (corePresumptionId item)) "trigger" "trigger",
       GraphEdge (nodeId "input" (corePresumptionRebuttal item))
        (nodeId "presumption" (corePresumptionId item)) "rebuttal" "rebuttal",
       GraphEdge (nodeId "presumption" (corePresumptionId item))
        (nodeId "effective-input" (corePresumptionTarget item)) "derivation" (corePresumptionState item)]

requirementGraph :: CoreRequirement -> ([GraphNode],[GraphEdge])
requirementGraph requirement = case requirement of
  CoreInput identifier citation status ->
    ([withOptionalObservation (supplied <$> status) $ GraphNode (nodeId "requirement" identifier) "input" identifier
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

withObservation :: CoreObservation -> GraphNode -> GraphNode
withObservation value node = node { graphNodeObservation = Just value }

withOptionalObservation :: Maybe CoreObservation -> GraphNode -> GraphNode
withOptionalObservation value node = node { graphNodeObservation = value }

computed :: Text -> CoreObservation
computed value = CoreObservation "evaluated" (Just value) Nothing Nothing

supplied :: CoreTruth -> CoreObservation
supplied value = CoreObservation "supplied" (Just (truthText value)) Nothing Nothing

guardNodeId :: CoreGuard -> Text
guardNodeId = nodeId "guard" . coreGuardIdentity

guardNode :: CoreGuard -> GraphNode
guardNode guard = withObservation observation $
  GraphNode (guardNodeId guard) "guard"
    (coreGuardId guard <> "\nexception guard occurrence") (coreGuardSource guard)
    (coreObservationValue observation)
    (Just (coreGuardRule guard <> " / " <> coreGuardBranch guard))
  where observation = coreGuardObservation guard

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
