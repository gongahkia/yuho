module Yuho.Surface.AST
  ( Combinator(..), Category(..), RuleKind(..), Proof(..), Assignment(..), SourceDecl(..)
  , ScopeAssumption(..), ScopeAcknowledgement(..), GeneralException(..), Attachment(..)
  , StatutorySection(..)
  , DefinitionKind(..), DefinitionInput(..), DefinitionOutput(..), DefinitionReference(..)
  , MentalStateKind(..), MentalStateInput(..), StatutoryDefinition(..)
  , PartyRoleKind(..), PartyRole(..), ActorBinding(..), RelationEndpoint(..)
  , ActorAttributedFact(..), ActorAttributedMentalState(..), ActorAssignment(..)
  , RelationAssignment(..), ParticipationTarget(..), ParticipationRelation(..)
  , ParticipationRoute(..), StatutoryInstrument(..), AuthorityReference(..)
  , Abetment(..), AbetmentRoute(..), PursuantConduct(..)
  , AttemptTarget(..), AttemptActor(..), TargetDirectedMentalState(..)
  , ConductStageDefinition(..), AttemptDefinition(..), AttemptScopeAssumption(..)
  , AttemptTechnicalOutput(..), ConductStage(..), ConductStageAssignment(..)
  , TargetCompletion(..)
  , ExceptionSubject(..), ActorExceptionDefinition(..), AttachmentTargetKind(..)
  , ActContext(..), ActorExceptionAttachment(..), ScopedExceptionAssignment(..)
  , ExceptionTechnicalStatus(..), ActorScopedExceptionResult(..)
  , CaseTargetKind(..), CaseAllegation(..), AnalysisCase(..)
  , CaseFactId(..), CaseFactKind(..), CaseFactSubject(..)
  , CaseFactClassification(..), CaseFact(..), CaseInputTarget(..), CaseFactBinding(..)
  , BurdenAnnotation(..), TechnicalOutput(..), Proposition(..), Element(..), Rule(..), Body(..), Model(..), Scenario(..)
  , Resolved(..), Checked(..), identifier, leafTokens ) where

import Data.Text (Text)
import Yuho.Surface.Token (Token(..))

data Combinator = All | Any deriving (Eq, Show)
data Category = Conduct | Circumstance | Fault | Purpose | Result | Causation
  | Intention | Knowledge | Unsoundness | NatureIncapacity
  | OrdinaryWrongfulness | ContraryLawWrongfulness | ControlIncapacity
  | MovableProperty | Possession | ConsentAbsence | DishonestIntention
  | Movement | MovementForTaking
  | AidAct | IllegalOmission | Consequence | SubstantialStep
  | PursuantAct | PursuantIllegalOmission
  deriving (Eq, Ord, Show)
data RuleKind = OffenceKind | ExceptionKind | ParticipationKind | AttemptKind deriving (Eq, Show)
data Proof = Proved | NotProved | Unresolved Text deriving (Eq, Show)
data Assignment = Assignment Token Token (Maybe Token) deriving (Eq, Show)
data SourceDecl = SourceDecl Token Token Token deriving (Eq, Show)
data ScopeAssumption = ScopeAssumption Token | TargetScopeAssumption Token Token
  deriving (Eq, Show)
newtype ScopeAcknowledgement = ScopeAcknowledgement Token deriving (Eq, Show)
newtype GeneralException = GeneralException Rule deriving (Eq, Show)
data Attachment = Attachment Token Token Token deriving (Eq, Show)
newtype StatutorySection = StatutorySection Token deriving (Eq, Show)
data BurdenAnnotation = BurdenAnnotation Token Token Token Token deriving (Eq, Show)
data TechnicalOutput = TechnicalOutput Token Token deriving (Eq, Show)
data DefinitionKind = HurtResult | VoluntaryHurt | WrongfulGain | WrongfulLoss
  | Dishonesty deriving (Eq, Ord, Show)
newtype DefinitionInput = DefinitionInput Element deriving (Eq, Show)
newtype DefinitionOutput = DefinitionOutput Token deriving (Eq, Show)
data DefinitionReference = DefinitionReference Token Token DefinitionKind
  deriving (Eq, Show)
data MentalStateKind = MentalIntention | MentalKnowledge deriving (Eq, Show)
data MentalStateInput = MentalStateInput Element MentalStateKind Token DefinitionKind
  deriving (Eq, Show)
data StatutoryDefinition = StatutoryDefinition
  { definitionId :: Token, definitionKind :: DefinitionKind
  , definitionSections :: [StatutorySection]
  , definitionInputs :: [DefinitionInput]
  , definitionMentalStates :: [MentalStateInput]
  , definitionReferences :: [DefinitionReference]
  , definitionGroups :: [Proposition]
  , definitionOutputs :: [DefinitionOutput] }
  deriving (Eq, Show)
data PartyRoleKind = PrincipalParty | AllegedAbettorParty | AllegedAttempterParty
  | CoConspiratorParty
  deriving (Eq, Show)
data PartyRole = PartyRole Token PartyRoleKind deriving (Eq, Show)
data ActorBinding = ActorBinding Token Token deriving (Eq, Show)
data RelationEndpoint = RoleEndpoint Token | RelationEndpoint Token deriving (Eq, Show)
data ActorAttributedFact = ActorAttributedFact Token RelationEndpoint deriving (Eq, Show)
data ActorAttributedMentalState = ActorAttributedMentalState Token RelationEndpoint
  deriving (Eq, Show)
data ActorAssignment = ActorAssignment Token Token Token (Maybe Token) deriving (Eq, Show)
data RelationAssignment = RelationAssignment Token Token Token Token (Maybe Token)
  deriving (Eq, Show)
newtype ParticipationTarget = ParticipationTarget Token deriving (Eq, Show)
data ParticipationRelation = ParticipationRelation
  { relationIdentifier :: Token, relationFrom :: RelationEndpoint
  , relationTo :: RelationEndpoint, relationTarget :: ParticipationTarget
  , relationStatusId :: Token, relationQuote :: Token }
  deriving (Eq, Show)
data ParticipationRoute = IntentionalAidRoute Rule ParticipationRelation deriving (Eq, Show)
data PursuantConduct = PursuantConduct Token Token Element Element deriving (Eq, Show)
data AbetmentRoute
  = InstigationRoute Token ParticipationRelation
  | ConspiracyRoute Token Token ParticipationRelation PursuantConduct
      Element Proposition Proposition
  | AidRoute Token ParticipationRelation [Element] Proposition Proposition
  deriving (Eq, Show)
data Abetment = Abetment
  { abetmentRule :: Rule, abetmentActor :: Token, abetmentPrincipal :: Token
  , abetmentRoutes :: [AbetmentRoute], abetmentOverall :: Proposition
  , abetmentConsequence :: Element, abetmentConsequenceRelation :: ParticipationRelation
  , abetmentCandidate :: Proposition }
  deriving (Eq, Show)
data StatutoryInstrument = PenalCode1871 | EvidenceAct1893 deriving (Eq, Show)
data AuthorityReference = AuthorityReference Token StatutoryInstrument Token Token
  deriving (Eq, Show)
newtype AttemptTarget = AttemptTarget Token deriving (Eq, Show)
newtype AttemptActor = AttemptActor Token deriving (Eq, Show)
data TargetDirectedMentalState = TargetDirectedMentalState
  { attemptIntentionId :: Token, attemptIntentionActor :: AttemptActor
  , attemptIntentionTarget :: AttemptTarget, attemptIntentionQuote :: Token }
  deriving (Eq, Show)
data ConductStageDefinition = ConductStageDefinition
  { attemptStageId :: Token, attemptStageActor :: AttemptActor
  , attemptStageOutput :: Token, attemptStageQuote :: Token }
  deriving (Eq, Show)
data AttemptDefinition = AttemptDefinition
  { attemptRule :: Rule, attemptActor :: AttemptActor
  , attemptTarget :: AttemptTarget
  , attemptMentalState :: TargetDirectedMentalState
  , attemptConductStage :: ConductStageDefinition }
  deriving (Eq, Show)
newtype AttemptScopeAssumption = AttemptScopeAssumption ScopeAssumption deriving (Eq, Show)
newtype AttemptTechnicalOutput = AttemptTechnicalOutput TechnicalOutput deriving (Eq, Show)
data ConductStage = PreparationOnly Token | ActTowardsCommission Token
  | StageUnresolved Token Token deriving (Eq, Show)
data ConductStageAssignment = ConductStageAssignment Token Token ConductStage
  deriving (Eq, Show)
data TargetCompletion = TargetNotCompleted Token Token | TargetCompleted Token Token
  deriving (Eq, Show)
newtype ExceptionSubject = ActorSubject Token deriving (Eq, Show)
data ActorExceptionDefinition = ActorExceptionDefinition ExceptionSubject Rule
  deriving (Eq, Show)
data AttachmentTargetKind = CandidateOffenceTarget Token
  | ParticipationAttachmentTarget Token | AttemptAttachmentTarget Token
  deriving (Eq, Show)
data ActContext = PrincipalConductContext Token | AidConductContext Token
  | AttemptConductContext Token deriving (Eq, Show)
data ActorExceptionAttachment = ActorExceptionAttachment
  { attachmentDefinition :: Token, attachmentTargetKind :: AttachmentTargetKind
  , attachmentSubjectRole :: Token, attachmentContext :: ActContext
  , attachmentInstanceId :: Token }
  deriving (Eq, Show)
data ScopedExceptionAssignment = ScopedExceptionAssignment
  { scopedAssignmentInstance :: Token, scopedAssignmentFact :: Token
  , scopedAssignmentActor :: Token, scopedAssignmentContext :: ActContext
  , scopedAssignmentStatus :: Token, scopedAssignmentReason :: Maybe Token }
  deriving (Eq, Show)
data ExceptionTechnicalStatus = ExceptionSatisfied | ExceptionNotSatisfied
  | ExceptionUnresolved | ExceptionNotEvaluated deriving (Eq, Show)
data ActorScopedExceptionResult = ActorScopedExceptionResult
  ActorExceptionAttachment ExceptionTechnicalStatus deriving (Eq, Show)
data CaseTargetKind = CaseOffence | CaseParticipation | CaseAttempt
  deriving (Eq, Ord, Show)
newtype CaseFactId = CaseFactId Token deriving (Eq, Show)
data CaseFactKind = FactConduct | FactCircumstance | FactMentalState
  | FactRelationship deriving (Eq, Ord, Show)
data CaseFactSubject = CaseActorSubject Token (Maybe Token)
  | CaseRelationSubject Token Token Token
  | CaseExceptionSubject Token Token ActContext deriving (Eq, Show)
data CaseFactClassification = CaseFactClassification Token (Maybe Token) Token
  deriving (Eq, Show)
data CaseFact = CaseFact CaseFactId CaseFactKind CaseFactSubject
  CaseFactClassification deriving (Eq, Show)
data CaseInputTarget = CasePrimitiveInput Token | CaseRelationInput Token
  | CaseExceptionInput Token Token deriving (Eq, Show)
data CaseFactBinding = CaseFactBinding CaseFactId CaseInputTarget deriving (Eq, Show)
data CaseAllegation = CaseAllegation Token CaseTargetKind Token Token Scenario
  [CaseFactBinding]
  deriving (Eq, Show)
data AnalysisCase = AnalysisCase Token Token [ActorBinding] [CaseFact] [CaseAllegation]
  deriving (Eq, Show)
data Proposition = Leaf Token (Maybe Token) Token (Maybe Token)
  | Group Token Combinator [Token] deriving (Eq, Show)
data Element = Element
  { elementCategory :: Category, elementCategorySource :: Token
  , elementId :: Token, elementQuote :: Token, elementSupport :: Maybe Token }
  deriving (Eq, Show)
data Rule = Rule
  { ruleKind :: RuleKind, ruleKindSource :: Token, ruleIdentifier :: Token, ruleTarget :: Maybe Token
  , ruleId :: Token, ruleProgram :: Token, rulePath :: Token
  , ruleSections :: [StatutorySection]
  , ruleElements :: [Element], ruleGroups :: [Proposition]
  , ruleDefinitionReferences :: [DefinitionReference] }
  deriving (Eq, Show)
data Body = Section Token Token Token Token Token [Proposition] [Assignment]
  | Synthetic Rule Rule [TechnicalOutput]
  | Legal [ScopeAssumption] Rule Rule [TechnicalOutput]
  | MultiLegal [ScopeAssumption] [Rule] [GeneralException] [Attachment] [TechnicalOutput]
  | DefinitionsLegal [StatutoryDefinition] [ScopeAssumption] [Rule]
      [GeneralException] [Attachment] [TechnicalOutput]
  | ParticipationLegal [PartyRole] [StatutoryDefinition]
      [ActorAttributedFact] [ActorAttributedMentalState]
      [ScopeAssumption] Rule ParticipationRoute [AuthorityReference] [TechnicalOutput]
  | AttemptLegal [PartyRole] [StatutoryDefinition] [AttemptScopeAssumption]
      Rule AttemptDefinition [AuthorityReference] [AttemptTechnicalOutput]
  | ActorScopedLegal [PartyRole] [ActorAttributedFact] [ActorAttributedMentalState]
      [ScopeAssumption] Rule ParticipationRoute AttemptDefinition
      ActorExceptionDefinition [ActorExceptionAttachment]
      [AuthorityReference] [TechnicalOutput]
  | AbetmentLegal [PartyRole] [ActorAttributedFact] [ActorAttributedMentalState]
      [ScopeAssumption] Rule Abetment AttemptDefinition
      ActorExceptionDefinition [ActorExceptionAttachment]
      [AuthorityReference] [TechnicalOutput]
  deriving (Eq, Show)
data Model = Model
  { modelIdentifier :: Token
  , modelVariant :: Token
  , modelJurisdiction :: Token
  , modelPurpose :: Token
  , modelRequest :: Token
  , modelDate :: Token
  , modelLimit :: Token
  , modelSources :: [SourceDecl]
  , modelQuotes :: [(Token, Token)]
  , modelBurden :: BurdenAnnotation
  , modelBody :: Body
  , modelLimitations :: [Token]
  } deriving (Eq, Show)
data Scenario = Scenario Token Token [Assignment] [ScopeAcknowledgement] [Token]
  | ParticipationScenario Token Token [ActorBinding] [ActorAssignment]
      [RelationAssignment] [Assignment] [ScopeAcknowledgement] [Token]
  | AttemptScenario Token Token [ActorBinding] [ActorAssignment]
      [ConductStageAssignment] [TargetCompletion] [Assignment]
      [ScopeAcknowledgement] [Token]
  | ActorScopedScenario Token Token [Token] [Token] [ActorBinding]
      [ActorAssignment] [RelationAssignment] [ConductStageAssignment]
      [TargetCompletion] [ScopedExceptionAssignment] [Assignment]
      [ScopeAcknowledgement]
  deriving (Eq, Show)
data Resolved = ResolvedLeaf Token Token | ResolvedGroup Token Combinator [Resolved]
  deriving (Eq, Show)
data Checked = Checked Model (Maybe Scenario) [(Token, Proof)] Resolved (Maybe Resolved)
  deriving (Eq, Show)

identifier :: Proposition -> Token
identifier (Leaf token _ _ _) = token
identifier (Group token _ _) = token

leafTokens :: Resolved -> [Token]
leafTokens (ResolvedLeaf token _) = [token]
leafTokens (ResolvedGroup _ _ members) = concatMap leafTokens members
