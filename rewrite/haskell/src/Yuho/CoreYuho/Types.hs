{-# LANGUAGE OverloadedStrings #-}
module Yuho.CoreYuho.Types
  ( CoreTruth, CoreRequirement(..), CoreElement(..), CoreRuleKind(..)
  , CoreRule(..), CoreDefinition(..), CoreAttachment(..), CorePenaltyTerm(..)
  , CorePenalty(..), CoreActor(..), CoreRelation(..), CoreModule(..)
  , CoreTemporalSelection(..), CorePresumption(..), CoreAllegation(..)
  , CoreScopeKey(..), CoreInterval(..), CoreSharedFact(..), CoreProgram(..)
  , CoreCase(..), CorePresumptionProgram(..)
  ) where

import Data.Map.Strict (Map)
import Data.Text (Text)
import Yuho.Exception.Types (Truth)

-- | Core Yuho uses the kernel's exact three-valued proof domain.
type CoreTruth = Truth

data CoreRequirement
  = CoreInput Text Text (Maybe CoreTruth)
  | CoreAll Text [CoreRequirement]
  | CoreAny Text [CoreRequirement]
  deriving (Eq, Show)

data CoreElement = CoreElement
  { coreElementId :: Text
  , coreElementCategory :: Text
  , coreElementCitation :: Text
  } deriving (Eq, Show)

data CoreRuleKind = CoreOffence | CoreException | CoreParticipation | CoreAttempt
  deriving (Eq, Ord, Show)

data CoreRule = CoreRule
  { coreRuleId :: Text
  , coreRuleTechnicalId :: Text
  , coreRuleKind :: CoreRuleKind
  , coreRuleSections :: [Text]
  , coreRuleElements :: [CoreElement]
  , coreRuleRequirements :: [CoreRequirement]
  } deriving (Eq, Show)

data CoreDefinition = CoreDefinition
  { coreDefinitionId :: Text
  , coreDefinitionKind :: Text
  , coreDefinitionSections :: [Text]
  , coreDefinitionRequirements :: [CoreRequirement]
  , coreDefinitionDependencies :: [Text]
  , coreDefinitionOutputs :: [Text]
  } deriving (Eq, Show)

data CoreAttachment = CoreAttachment
  { coreAttachmentId :: Text
  , coreAttachmentException :: Text
  , coreAttachmentTarget :: Text
  , coreAttachmentActor :: Maybe Text
  , coreAttachmentRole :: Maybe Text
  , coreAttachmentContext :: Maybe Text
  } deriving (Eq, Show)

data CorePenaltyTerm
  = CoreImprisonment Text Text Text Text
  | CoreFine Text Text Text Text
  | CoreAllTerms Text [CorePenaltyTerm]
  | CoreExactlyOneTerm Text [CorePenaltyTerm]
  | CoreOneOrMoreTerms Text [CorePenaltyTerm]
  deriving (Eq, Show)

data CorePenalty = CorePenalty
  { corePenaltyId :: Text
  , corePenaltyTarget :: Text
  , corePenaltySource :: Text
  , corePenaltyProvision :: Text
  , corePenaltyTerm :: CorePenaltyTerm
  } deriving (Eq, Show)

data CoreActor = CoreActor
  { coreActorId :: Text
  , coreActorRole :: Text
  } deriving (Eq, Show)

data CoreRelation = CoreRelation
  { coreRelationId :: Text
  , coreRelationFrom :: Text
  , coreRelationTo :: Text
  , coreRelationTarget :: Text
  } deriving (Eq, Show)

data CoreModule = CoreModule
  { coreModuleName :: Text
  , coreModuleVersion :: Text
  , coreModuleAlias :: Text
  , coreModuleExports :: [Text]
  } deriving (Eq, Show)

data CoreTemporalSelection = CoreTemporalSelection
  { coreTemporalExpression :: Text
  , coreTemporalReason :: Text
  } deriving (Eq, Show)

data CoreScopeKey = CoreScopeKey
  { coreScopeActor :: Text
  , coreScopeRole :: Text
  , coreScopeContext :: Text
  , coreScopeInstance :: Text
  } deriving (Eq, Ord, Show)

data CoreInterval = CoreInterval
  { coreIntervalExpression :: Text
  , coreIntervalFrom :: Integer
  , coreIntervalTo :: Maybe Integer
  , coreIntervalVersion :: Text
  , coreIntervalSupersedes :: Maybe Text
  } deriving (Eq, Show)

data CorePresumption = CorePresumption
  { corePresumptionId :: Text
  , corePresumptionTarget :: Text
  , corePresumptionSource :: Text
  , corePresumptionTrigger :: Text
  , corePresumptionRebuttal :: Text
  , corePresumptionState :: Text
  } deriving (Eq, Show)

data CoreAllegation = CoreAllegation
  { coreAllegationId :: Text
  , coreAllegationKind :: CoreRuleKind
  , coreAllegationTarget :: Text
  , coreAllegationRole :: Text
  , coreAllegationStatus :: Text
  } deriving (Eq, Show)

data CoreSharedFact = CoreSharedFact
  { coreSharedFactId :: Text
  , coreSharedFactKind :: Text
  , coreSharedFactSubject :: Text
  , coreSharedFactStatus :: Text
  , coreSharedFactDestinations :: [(Text, Text)]
  } deriving (Eq, Show)

data CoreProgram = CoreProgram
  { coreProgramId :: Text
  , coreProgramJurisdiction :: Text
  , coreProgramRules :: [CoreRule]
  , coreProgramDefinitions :: [CoreDefinition]
  , coreProgramAttachments :: [CoreAttachment]
  , coreProgramPenalties :: [CorePenalty]
  , coreProgramActors :: [CoreActor]
  , coreProgramRelations :: [CoreRelation]
  , coreProgramRoots :: [CoreRequirement]
  , coreProgramAssignments :: Map Text CoreTruth
  , coreProgramRuleStatuses :: Map Text Text
  , coreProgramBranchReasons :: Map Text Text
  , coreProgramModules :: [CoreModule]
  , coreProgramTemporal :: Maybe CoreTemporalSelection
  , coreProgramLimitations :: [Text]
  } deriving (Eq, Show)

data CoreCase = CoreCase
  { coreCaseId :: Text
  , coreCaseModel :: CoreProgram
  , coreCaseActors :: [CoreActor]
  , coreCaseAllegations :: [CoreAllegation]
  , coreCaseFacts :: [CoreSharedFact]
  } deriving (Eq, Show)

data CorePresumptionProgram = CorePresumptionProgram
  { corePresumptionProgramId :: Text
  , corePresumptionBurdenBearer :: Text
  , corePresumptionStandard :: Text
  , corePresumptionContext :: Text
  , corePresumptions :: [CorePresumption]
  , corePresumptionFinalStatus :: Text
  } deriving (Eq, Show)
