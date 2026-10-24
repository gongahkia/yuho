{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Opt-in finite dependency authoring records. Decoding is not checking.
module Yuho.Dependency.Types where

import Data.Aeson (ToJSON(..), FromJSON(..), Options(..), defaultOptions, genericParseJSON, genericToJSON)
import qualified Data.Aeson
import qualified Data.Text
import Data.Map.Strict (Map)
import Data.Text (Text)
import GHC.Generics (Generic)

-- Closed records: unknown fields never silently change the supported capability.
options :: Options
options = defaultOptions { rejectUnknownFields=True }

planFormat, projectionFormat, reportFormat :: Text
planFormat="yuho.dependency-plan/v0.1-experimental"
projectionFormat="yuho.dependency-projection/v0.1-experimental"
reportFormat="yuho.dependency-report/v0.1-experimental"

data Location = Location { locationPath :: FilePath, locationLine :: Int, locationColumn :: Int
  , locationStart :: Int, locationEnd :: Int } deriving (Eq,Show,Generic)
instance ToJSON Location where toJSON=genericToJSON options
instance FromJSON Location where parseJSON=genericParseJSON options

data DependencyDiagnostic = DependencyDiagnostic { dependencyCode :: Text, dependencyMessage :: Text
  , dependencyObjects :: [Text], dependencyLocation :: Maybe Location, dependencyRelated :: [Location] } deriving (Eq,Show,Generic)
instance ToJSON DependencyDiagnostic where toJSON=genericToJSON options
instance FromJSON DependencyDiagnostic where parseJSON=genericParseJSON options

data PlanScope = PlanScope { scopeIdentity :: Text, scopeActor :: Text, scopeContext :: Text
  , scopeCase :: Maybe Text, scopeAllegation :: Maybe Text, scopeEntities :: [(Text,Text)] }
  deriving (Eq,Ord,Show,Generic)
instance ToJSON PlanScope where toJSON=genericToJSON options
instance FromJSON PlanScope where parseJSON=genericParseJSON options

data SourceOrigin = SourceOrigin { originIdentity :: Text, originLocator :: Text }
  deriving (Eq,Show,Generic)
instance ToJSON SourceOrigin where toJSON=genericToJSON options
instance FromJSON SourceOrigin where parseJSON=genericParseJSON options

data TechnicalValue = Satisfied | NotSatisfied | Unresolved deriving (Eq,Ord,Show,Generic)
instance ToJSON TechnicalValue where toJSON=genericToJSON options
instance FromJSON TechnicalValue where parseJSON=genericParseJSON options

data TemplateExpr = TemplateAtom Text [Text] | TemplateCondition Text
  | TemplateAll [TemplateExpr] | TemplateAny [TemplateExpr] | TemplateNot TemplateExpr
  | TemplateReference Text deriving (Eq,Show,Generic)
instance ToJSON TemplateExpr where toJSON=genericToJSON options
instance FromJSON TemplateExpr where parseJSON=genericParseJSON options

-- | A checked high-level ground template builder, not a raw Core request. Native
-- source components additionally retain the full existing finite source language.
data TechnicalTemplate = TechnicalTemplate
  { templateIdentity :: Text, templateEntityTypes :: [Text], templateEntities :: [(Text,Text)]
  , templatePredicates :: [(Text,[Text])], templateConditions :: [Text]
  , templateRequirements :: [(Text,TemplateExpr)], templatePropositions :: [Text]
  , templateRules :: [(Text,Text,Text)] -- establishing rule, proposition, named requirement
  , templateFacts :: [(Text,[Text],TechnicalValue,Text)], templateLimitations :: [Text]
  } deriving (Eq,Show,Generic)
instance ToJSON TechnicalTemplate where toJSON=genericToJSON options
instance FromJSON TechnicalTemplate where parseJSON=genericParseJSON options

data PlanComponent = PlanComponent
  { componentIdentity :: Text, componentProfile :: Text, componentModel :: FilePath
  , componentScenario :: Maybe FilePath, componentEntry :: Maybe (Text,Text)
  , componentScope :: Text, componentNominals :: [(Text,Text)], componentEntities :: [(Text,Text)]
  , componentRationale :: Text, componentTemplate :: Maybe TechnicalTemplate
  , componentLocation :: Maybe Location } deriving (Eq,Show,Generic)
instance ToJSON PlanComponent where toJSON=genericToJSON options
instance FromJSON PlanComponent where parseJSON=genericParseJSON options

data ObservationPort = ObservationPort { portComponent :: Text, portCategory :: Text, portObject :: Text }
  deriving (Eq,Ord,Show,Generic)
instance ToJSON ObservationPort where toJSON=genericToJSON options
instance FromJSON ObservationPort where parseJSON=genericParseJSON options

data PlanBinding = PlanBinding
  { bindingIdentity :: Text, bindingPort :: ObservationPort, bindingComponent :: Text, bindingSlot :: Text
  , bindingPolicy :: Text, bindingRationale :: Text, bindingReferences :: [Text]
  , bindingLocation :: Maybe Location } deriving (Eq,Show,Generic)
instance ToJSON PlanBinding where toJSON=genericToJSON options
instance FromJSON PlanBinding where parseJSON=genericParseJSON options

data PlanCandidate = PlanCandidate
  { candidateIdentity :: Text, candidateScope :: Text, candidateGuard :: ObservationPort
  , candidatePolicy :: Text, candidateModality :: Text, candidateRationale :: Text
  , candidateReferences :: [Text], candidateTerm :: DataTerm
  , candidateLocation :: Maybe Location } deriving (Eq,Show,Generic)
instance ToJSON PlanCandidate where toJSON=genericToJSON options
instance FromJSON PlanCandidate where parseJSON=genericParseJSON options

-- Same admitted term tree/endpoint vocabulary as PenaltyTerms-v1; modality and
-- guards live outside it. Validation delegates to that profile's term validator.
data DataTerm = DataTerm { termValue :: Data.Aeson.Value } deriving (Eq,Show,Generic)
instance ToJSON DataTerm where toJSON=genericToJSON options
instance FromJSON DataTerm where parseJSON=genericParseJSON options

data DependencyPlan = DependencyPlan { planIdentity :: Text, planOrigins :: [SourceOrigin]
  , planScopes :: [PlanScope], planComponents :: [PlanComponent], planBindings :: [PlanBinding]
  , planCandidates :: [PlanCandidate] } deriving (Eq,Show,Generic)
instance ToJSON DependencyPlan where toJSON=genericToJSON options
instance FromJSON DependencyPlan where parseJSON=genericParseJSON options

data DependencyDocument = DependencyDocument { dependencyFormat :: Text, dependencyPlan :: DependencyPlan
  , dependencySources :: Map FilePath Text, dependencyProjectSource :: Maybe FilePath } deriving (Eq,Show,Generic)
instance ToJSON DependencyDocument where toJSON=genericToJSON options
instance FromJSON DependencyDocument where parseJSON=genericParseJSON options

-- Reversible tuple encoding; Unicode length counts code points consistently.
-- Hashes below identify bytes, never replace this structural identity contract.
qualifiedIdentity :: [Text] -> Text
qualifiedIdentity = Data.Text.concat . map (\x->Data.Text.pack (show (Data.Text.length x))<> ":"<>x)
