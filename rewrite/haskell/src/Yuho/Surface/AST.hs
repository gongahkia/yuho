module Yuho.Surface.AST
  ( Combinator(..), Category(..), RuleKind(..), Proof(..), Assignment(..), SourceDecl(..)
  , ScopeAssumption(..), ScopeAcknowledgement(..), GeneralException(..), Attachment(..)
  , StatutorySection(..)
  , DefinitionKind(..), DefinitionInput(..), DefinitionOutput(..), DefinitionReference(..)
  , MentalStateKind(..), MentalStateInput(..), StatutoryDefinition(..)
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
  deriving (Eq, Ord, Show)
data RuleKind = OffenceKind | ExceptionKind deriving (Eq, Show)
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
