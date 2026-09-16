{-# LANGUAGE OverloadedStrings #-}
module Yuho.CoreYuho.Normalize
  ( normalizeChecked, normalizeCase, normalizePresumption ) where

import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import Data.Map.Strict (Map)
import Data.Maybe (mapMaybe)
import Data.Text (Text)
import qualified Data.Text as Text
import Yuho.CoreYuho.Types
import Yuho.Exception.Types (Truth(..))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), decodeJson, lookupField, textValue)
import Yuho.Surface.AST
import Yuho.Surface.ActorExceptions (actContextToken, attachmentTargetToken)
import Yuho.Surface.Case (CheckedCase(..), CheckedIssue(..))
import Yuho.Surface.CaseFacts (ResolvedCaseFact(..))
import Yuho.Surface.Modules (AuthoredModel(..))
import Yuho.Surface.Presumption (PresumptionProgram(..))
import Yuho.Surface.Lower (lowerChecked)
import Yuho.Surface.Token (tokenText)

normalizeChecked :: AuthoredModel -> Checked -> CoreProgram
normalizeChecked authored checked@(Checked model scenario assignments first second) = CoreProgram
  { coreProgramId = tokenText (modelIdentifier model)
  , coreProgramJurisdiction = tokenText (modelJurisdiction model)
  , coreProgramRules = map coreRule (bodyRules (modelBody model))
  , coreProgramDefinitions = map coreDefinition (bodyDefinitions (modelBody model))
  , coreProgramAttachments = bodyAttachments scenario (modelBody model)
  , coreProgramPenalties = map corePenalty (modelCandidatePenalties model)
  , coreProgramActors = scenarioActors scenario
  , coreProgramRelations = bodyRelations (modelBody model)
  , coreProgramRoots = map (resolvedRequirement assignmentMap) (first : maybe [] (:[]) second)
  , coreProgramAssignments = assignmentMap
  , coreProgramRuleStatuses = fst evaluated
  , coreProgramBranchReasons = snd evaluated
  , coreProgramModules = modules
  , coreProgramTemporal = temporal
  , coreProgramLimitations = map tokenText (modelLimitations model)
  }
  where
    assignmentMap = Map.fromList [(tokenText item, proofTruth proof) | (item,proof) <- assignments]
    evaluated = case lowerChecked checked of
      Right request -> resultMaps (runLine request)
      Left _ -> (Map.empty,Map.empty)
    imports = authoredImports authored
    temporal = case imports of
      [("effective-expression", expression, reason)] ->
        Just (CoreTemporalSelection expression reason)
      _ -> Nothing
    modules = case temporal of
      Just _ -> []
      Nothing -> [CoreModule name version alias
        [kindValue <> " " <> item
        | (kindValue,selectedAlias,item) <- authoredSelections authored,
          selectedAlias == alias]
        | (name,version,alias) <- imports]

normalizeCase :: AuthoredModel -> CheckedCase -> CoreCase
normalizeCase authored (CheckedCase _ caseId _ facts issues) = CoreCase
  { coreCaseId = tokenText caseId
  , coreCaseModel = case issues of
      CheckedIssue _ checked _:_ -> normalizeChecked authored checked
      [] -> emptyProgram
  , coreCaseActors = orderedActors facts issues
  , coreCaseAllegations = map allegation issues
  , coreCaseFacts = map sharedFact facts
  }
  where
    emptyProgram = CoreProgram "invalid-empty-case" "" [] [] [] [] [] [] []
      Map.empty Map.empty Map.empty [] Nothing []
    allegation (CheckedIssue (CaseAllegation item kind target role _ _) _ request) =
      CoreAllegation (tokenText item) (caseKind kind) (tokenText target)
        (tokenText role) (allegationStatus (runLine request))
    orderedActors resolved rows = distinctActors
      ([CoreActor (factActor fact) "case-fact-subject"
       | ResolvedCaseFact fact _ <- resolved, factActor fact /= ""] ++
       [CoreActor (tokenText role) (tokenText role)
       | CheckedIssue (CaseAllegation _ _ _ role _ _) _ _ <- rows])

normalizePresumption :: PresumptionProgram -> CorePresumptionProgram
normalizePresumption program = CorePresumptionProgram
  { corePresumptionProgramId = tokenText (presumptionName program)
  , corePresumptionBurdenBearer = tokenText (presumptionBurdenBearer program)
  , corePresumptionStandard = tokenText (presumptionStandard program)
  , corePresumptionContext = tokenText (presumptionNote program)
  , corePresumptions = [CorePresumption item target source trigger rebuttal
      (Map.findWithDefault "not_evaluated" item states)
      | (item,target,source,trigger,rebuttal) <- presumptionRegistrations program]
  , corePresumptionFinalStatus = resultStatus (presumptionResult program)
  }
  where
    states = Map.fromList (presumptionStates (presumptionResult program))

proofTruth :: Proof -> Truth
proofTruth Proved = TrueValue
proofTruth NotProved = FalseValue
proofTruth Unresolved {} = UnresolvedValue

resolvedRequirement :: Map Text Truth -> Resolved -> CoreRequirement
resolvedRequirement supplied resolved = case resolved of
  ResolvedLeaf item quote -> CoreInput (tokenText item) (tokenText quote)
    (Map.lookup (tokenText item) supplied)
  ResolvedGroup item All members -> CoreAll (tokenText item)
    (map (resolvedRequirement supplied) members)
  ResolvedGroup item Any members -> CoreAny (tokenText item)
    (map (resolvedRequirement supplied) members)

coreRule :: Rule -> CoreRule
coreRule rule = CoreRule
  { coreRuleId = tokenText (ruleIdentifier rule)
  , coreRuleTechnicalId = tokenText (ruleId rule)
  , coreRuleKind = ruleKindValue (ruleKind rule)
  , coreRuleSections = [tokenText item | StatutorySection item <- ruleSections rule]
  , coreRuleElements = map coreElement (ruleElements rule)
  , coreRuleRequirements = propositionRequirements
      (ruleElements rule) (ruleGroups rule)
  }

coreElement :: Element -> CoreElement
coreElement element = CoreElement (tokenText (elementId element))
  (categoryText (elementCategory element)) (tokenText (elementQuote element))

coreDefinition :: StatutoryDefinition -> CoreDefinition
coreDefinition definition = CoreDefinition
  { coreDefinitionId = tokenText (definitionId definition)
  , coreDefinitionKind = definitionKindText (definitionKind definition)
  , coreDefinitionSections = [tokenText item
      | StatutorySection item <- definitionSections definition]
  , coreDefinitionRequirements = propositionRequirements elements
      (definitionGroups definition)
  , coreDefinitionDependencies = [tokenText target
      | DefinitionReference _ target _ <- definitionReferences definition]
  , coreDefinitionOutputs = [tokenText item
      | DefinitionOutput item <- definitionOutputs definition]
  }
  where
    elements = [item | DefinitionInput item <- definitionInputs definition]
      ++ [item | MentalStateInput item _ _ _ <- definitionMentalStates definition]

propositionRequirements :: [Element] -> [Proposition] -> [CoreRequirement]
propositionRequirements elements propositions = mapMaybe build roots
  where
    leaves = Map.fromList [(tokenText (elementId item),item) | item <- elements]
    groups = Map.fromList [(tokenText (identifier item),item) | item <- propositions]
    referenced = [tokenText child | Group _ _ children <- propositions, child <- children]
    roots = [tokenText (identifier item) | item <- propositions,
      tokenText (identifier item) `notElem` referenced]
    build item = case (Map.lookup item leaves, Map.lookup item groups) of
      (Just element,_) -> Just (CoreInput item (tokenText (elementQuote element)) Nothing)
      (_,Just (Leaf token _ quote _)) -> Just (CoreInput (tokenText token) (tokenText quote) Nothing)
      (_,Just (Group token combinator children)) ->
        let members = mapMaybe (build . tokenText) children
        in Just $ case combinator of
          All -> CoreAll (tokenText token) members
          Any -> CoreAny (tokenText token) members
      _ -> Nothing

bodyRules :: Body -> [Rule]
bodyRules body = case body of
  Section {} -> []
  Synthetic offence exception _ -> [offence,exception]
  Legal _ offence exception _ -> [offence,exception]
  MultiLegal _ offences exceptions _ _ -> offences ++ exceptionRules exceptions
  DefinitionsLegal _ _ offences exceptions _ _ -> offences ++ exceptionRules exceptions
  ParticipationLegal _ _ _ _ _ offence (IntentionalAidRoute route _) _ _ -> [offence,route]
  AttemptLegal _ _ _ offence attempt _ _ -> [offence,attemptRule attempt]
  ActorScopedLegal _ _ _ _ offence (IntentionalAidRoute route _) attempt
    (ActorExceptionDefinition _ exception) _ _ _ -> [offence,route,attemptRule attempt,exception]
  AbetmentLegal _ _ _ _ offence abetment attempt
    (ActorExceptionDefinition _ exception) _ _ _ ->
      [offence,abetmentRule abetment,attemptRule attempt,exception]
  where exceptionRules values = [rule | GeneralException rule <- values]

bodyDefinitions :: Body -> [StatutoryDefinition]
bodyDefinitions body = case body of
  DefinitionsLegal values _ _ _ _ _ -> values
  ParticipationLegal _ values _ _ _ _ _ _ _ -> values
  AttemptLegal _ values _ _ _ _ _ -> values
  _ -> []

bodyAttachments :: Maybe Scenario -> Body -> [CoreAttachment]
bodyAttachments scenario body = case body of
  MultiLegal _ _ _ values _ -> map simple values
  DefinitionsLegal _ _ _ _ values _ -> map simple values
  ActorScopedLegal _ _ _ _ _ _ _ _ values _ _ -> map scoped values
  AbetmentLegal _ _ _ _ _ _ _ _ values _ _ -> map scoped values
  _ -> []
  where
    simple (Attachment item exception target) = CoreAttachment (tokenText item)
      (tokenText exception) (tokenText target) Nothing Nothing Nothing
    scoped item = CoreAttachment (tokenText (attachmentInstanceId item))
      (tokenText (attachmentDefinition item))
      (tokenText (attachmentTargetToken (attachmentTargetKind item)))
      (actorFor (attachmentSubjectRole item))
      (Just (tokenText (attachmentSubjectRole item)))
      (Just (tokenText (actContextToken (attachmentContext item))))
    actorFor role = case scenario of
      Just (ActorScopedScenario _ _ _ _ bindings _ _ _ _ _ _ _) -> findActor role bindings
      Just (ParticipationScenario _ _ bindings _ _ _ _ _) -> findActor role bindings
      Just (AttemptScenario _ _ bindings _ _ _ _ _ _) -> findActor role bindings
      _ -> Nothing
    findActor role bindings = case [tokenText actor | ActorBinding declared actor <- bindings,
      tokenText declared == tokenText role] of
      [actor] -> Just actor
      _ -> Nothing

scenarioActors :: Maybe Scenario -> [CoreActor]
scenarioActors scenario = distinctActors [CoreActor (tokenText actor) (tokenText role)
  | ActorBinding role actor <- bindings]
  where
    bindings = case scenario of
      Just (ParticipationScenario _ _ values _ _ _ _ _) -> values
      Just (AttemptScenario _ _ values _ _ _ _ _ _) -> values
      Just (ActorScopedScenario _ _ _ _ values _ _ _ _ _ _ _) -> values
      _ -> []

bodyRelations :: Body -> [CoreRelation]
bodyRelations body = map relation values
  where
    values = case body of
      ParticipationLegal _ _ _ _ _ _ (IntentionalAidRoute _ item) _ _ -> [item]
      ActorScopedLegal _ _ _ _ _ (IntentionalAidRoute _ item) _ _ _ _ _ -> [item]
      AbetmentLegal _ _ _ _ _ abetment _ _ _ _ _ ->
        [item | route <- abetmentRoutes abetment, item <- routeRelations route]
      _ -> []
    routeRelations route = case route of
      InstigationRoute _ item -> [item]
      ConspiracyRoute _ _ item _ _ _ _ -> [item]
      AidRoute _ item _ _ _ -> [item]
    relation item = CoreRelation (tokenText (relationIdentifier item))
      (endpointText (relationFrom item)) (endpointText (relationTo item))
      (case relationTarget item of ParticipationTarget target -> tokenText target)
    endpointText endpoint = case endpoint of
      RoleEndpoint item -> tokenText item
      RelationEndpoint item -> tokenText item

corePenalty :: CandidatePenalty -> CorePenalty
corePenalty item = CorePenalty (tokenText (candidatePenaltyId item))
  (tokenText (candidatePenaltyTarget item)) (tokenText (candidatePenaltySource item))
  (tokenText (candidatePenaltyProvision item)) (penaltyTerm (candidatePenaltyTerm item))

penaltyTerm :: PenaltyTerm -> CorePenaltyTerm
penaltyTerm term = case term of
  ImprisonmentTerm item minimumValue maximumValue unit ->
    CoreImprisonment (tokenText item) (endpoint minimumValue) (endpoint maximumValue)
      (tokenText unit)
  FineTerm item currency minimumValue maximumValue ->
    CoreFine (tokenText item) (tokenText currency) (endpoint minimumValue)
      (endpoint maximumValue)
  PenaltyAllOf item children -> CoreAllTerms (tokenText item) (map penaltyTerm children)
  PenaltyExactlyOneOf item children ->
    CoreExactlyOneTerm (tokenText item) (map penaltyTerm children)
  PenaltyOneOrMoreOf item children ->
    CoreOneOrMoreTerms (tokenText item) (map penaltyTerm children)
  where
    endpoint value = case value of
      PenaltyNotStated item -> tokenText item
      PenaltyUnbounded item -> tokenText item
      PenaltySpecified item -> tokenText item

sharedFact :: ResolvedCaseFact -> CoreSharedFact
sharedFact (ResolvedCaseFact fact destinations) = case fact of
  CaseFact (CaseFactId item) kind subject (CaseFactClassification status _ _) ->
    CoreSharedFact (tokenText item) (factKind kind) (subjectText subject)
      (tokenText status) [(tokenText allegation,targetText target)
        | (allegation,target) <- destinations]

factActor :: CaseFact -> Text
factActor (CaseFact _ _ subject _) = case subject of
  CaseActorSubject actor _ -> tokenText actor
  CaseRelationSubject actor _ _ -> tokenText actor
  CaseExceptionSubject actor _ _ -> tokenText actor

subjectText :: CaseFactSubject -> Text
subjectText subject = case subject of
  CaseActorSubject actor target -> tokenText actor <>
    maybe "" (" / " <>) (tokenText <$> target)
  CaseRelationSubject from to target -> Text.intercalate " / "
    [tokenText from <> " -> " <> tokenText to,tokenText target]
  CaseExceptionSubject actor instanceId context -> Text.intercalate " / "
    [tokenText actor,tokenText instanceId,tokenText (actContextToken context)]

targetText :: CaseInputTarget -> Text
targetText target = case target of
  CasePrimitiveInput item -> tokenText item
  CaseRelationInput item -> tokenText item
  CaseExceptionInput instanceId item -> tokenText instanceId <> "/" <> tokenText item

factKind :: CaseFactKind -> Text
factKind kind = case kind of
  FactConduct -> "conduct"
  FactCircumstance -> "circumstance"
  FactMentalState -> "mental-state"
  FactRelationship -> "relationship"

caseKind :: CaseTargetKind -> CoreRuleKind
caseKind kind = case kind of
  CaseOffence -> CoreOffence
  CaseParticipation -> CoreParticipation
  CaseAttempt -> CoreAttempt

ruleKindValue :: RuleKind -> CoreRuleKind
ruleKindValue kind = case kind of
  OffenceKind -> CoreOffence
  ExceptionKind -> CoreException
  ParticipationKind -> CoreParticipation
  AttemptKind -> CoreAttempt

resultStatus :: BS.ByteString -> Text
resultStatus bytes = case decodeJson bytes of
  Right value -> maybe "unavailable" id (lookupField "status" value >>= textValue)
  Left _ -> "unavailable"

allegationStatus :: BS.ByteString -> Text
allegationStatus bytes = case decodeJson bytes of
  Right value | hasDefeated value -> "defeated"
  _ -> resultStatus bytes
  where
    hasDefeated value = case value of
      JObj fields -> any (\(key,item) ->
        (key == "reason" && textValue item == Just "defeated") || hasDefeated item) fields
      JArr values -> any hasDefeated values
      _ -> False

presumptionStates :: BS.ByteString -> [(Text,Text)]
presumptionStates bytes = case decodeJson bytes of
  Right value -> case lookupField "presumption_derivations" value of
    Just (JArr rows) -> mapMaybe row rows
    _ -> []
  Left _ -> []
  where
    row value = (,) <$> (lookupField "presumption_id" value >>= textValue)
      <*> (lookupField "state" value >>= textValue)

resultMaps :: BS.ByteString -> (Map Text Text,Map Text Text)
resultMaps bytes = case decodeJson bytes of
  Left _ -> (Map.empty,Map.empty)
  Right value -> case lookupField "rules" value of
    Just (JArr rows) -> (Map.fromList (mapMaybe ruleStatus rows),
      Map.fromList (mapMaybe ruleReason rows))
    _ -> (Map.empty,Map.empty)
  where
    ruleStatus value = (,) <$> (lookupField "id" value >>= textValue)
      <*> (lookupField "status" value >>= textValue)
    ruleReason value = do
      ruleIdentifierText <- lookupField "id" value >>= textValue
      JArr rows <- lookupField "branches" value
      let reasons = mapMaybe (\row -> lookupField "reason" row >>= textValue) rows
      if "defeated" `elem` reasons then Just (ruleIdentifierText,"defeated")
      else if "exception_unresolved" `elem` reasons
        then Just (ruleIdentifierText,"unresolved")
        else Nothing

distinctActors :: [CoreActor] -> [CoreActor]
distinctActors = go []
  where
    go _ [] = []
    go seen (item:rest)
      | coreActorId item `elem` seen = go seen rest
      | otherwise = item : go (coreActorId item : seen) rest

categoryText :: Category -> Text
categoryText = Text.toLower . Text.pack . show

definitionKindText :: DefinitionKind -> Text
definitionKindText = Text.toLower . Text.pack . show
