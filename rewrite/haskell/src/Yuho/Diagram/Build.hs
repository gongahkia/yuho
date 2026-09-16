{-# LANGUAGE OverloadedStrings #-}
module Yuho.Diagram.Build
  ( programGraph, caseGraph, presumptionGraph ) where

import qualified Data.Map.Strict as Map
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.CoreYuho.Semantics (evaluateRequirement)
import Yuho.CoreYuho.Types
import Yuho.Diagram.Types
import Yuho.Exception.Types (Truth(..))

notice :: Text
notice = "Technical research statuses only; no guilt, conviction, acquittal, liability or sentence."

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
