{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
-- | Additive scoped requirement compilation records. Source authorship is shared;
-- evaluation and assessment selection are qualified by the checked component.
module Yuho.ScopedDefinitions.Types where
import Data.Aeson (ToJSON(..),genericToJSON,defaultOptions,Value)
import Data.Text (Text)
import GHC.Generics (Generic)

data ScopedDefinition = ScopedDefinition
  { definitionKey :: [Text], definitionSource :: FilePath, definitionSnapshot :: Text
  , definitionName :: Text, definitionFormals :: [(Text,Text)], definitionExpression :: Value
  , definitionLine :: Int, definitionColumn :: Int
  } deriving (Eq,Show,Generic)
instance ToJSON ScopedDefinition where toJSON=genericToJSON defaultOptions

data ScopedUse = ScopedUse
  { useIdentity :: Text, useDefinition :: [Text], useArguments :: [(Text,Text)]
  , useSource :: FilePath, useLine :: Int, useColumn :: Int
  , useScenario :: Text, useScenarioSource :: FilePath
  , useAssessmentPolicy :: Text
  } deriving (Eq,Show,Generic)
instance ToJSON ScopedUse where toJSON=genericToJSON defaultOptions

data ScopedAssessment = ScopedAssessment
  { selectedPredicate :: Text, selectedArguments :: [Text], selectedClassification :: Value
  , selectedSource :: FilePath, selectedLine :: Int, selectedColumn :: Int
  } deriving (Eq,Show,Generic)
instance ToJSON ScopedAssessment where toJSON=genericToJSON defaultOptions

data ScopedCompilation = ScopedCompilation
  { scopedDefinitions :: [ScopedDefinition], scopedUses :: [ScopedUse]
  , scopedAssessments :: [ScopedAssessment] }
  deriving (Eq,Show,Generic)
instance ToJSON ScopedCompilation where toJSON=genericToJSON defaultOptions

emptyScopedCompilation :: ScopedCompilation
emptyScopedCompilation=ScopedCompilation [] [] []
