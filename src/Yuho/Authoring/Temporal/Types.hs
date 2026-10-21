{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}
module Yuho.Authoring.Temporal.Types where
import Data.Aeson
import Data.Text (Text)
import GHC.Generics (Generic)
import Yuho.Authoring.Types

-- Complete embedded documents have independent identity/source namespaces.
temporalAuthoringFormat, temporalProjectionFormat :: Text
temporalAuthoringFormat = "yuho.authoring/v0.5-experimental"
temporalProjectionFormat = "yuho.temporal-projection/v0.5-experimental"
data TemporalExpression = TemporalExpression
  { temporalExpressionId :: Text, temporalExpressionVersion :: Text
  , temporalEffectiveFrom :: Text, temporalEffectiveTo :: Maybe Text
  , temporalExpressionDocument :: AuthoringDocument, temporalExpressionAnalysis :: Text
  , temporalExpressionSources :: [SourceRef], temporalDateSources :: [SourceRef]
  , temporalSupersedes :: Maybe Text
  } deriving (Eq, Show, Generic)
data TemporalDocument = TemporalDocument
  { temporalDocumentFormat :: Text, temporalDocumentId :: Text, temporalWorkId :: Text
  , temporalExpressions :: [TemporalExpression], temporalSources :: [SourceRecord]
  , temporalScope :: [Text], temporalAssumptions :: [Text]
  } deriving (Eq, Show, Generic)
data TemporalSnapshot = TemporalSnapshot
  { temporalSnapshotId :: Text, temporalSnapshotDocument :: TemporalDocument
  , temporalSnapshotConductDate :: Text, temporalSnapshotExpression :: Text
  } deriving (Eq, Show, Generic)
data TemporalSelection = TemporalSelection
  { selectionWrapper :: Text, selectionWork :: Text, selectionConductDate :: Text
  , selectionExpression :: TemporalExpression, selectionSnapshot :: TemporalSnapshot
  , selectionAnalysis :: Analysis, selectionUnderlyingSnapshot :: Text
  , selectionCompilation :: Maybe Text, selectionNotice :: Text
  } deriving (Eq, Show, Generic)
instance ToJSON TemporalExpression where toJSON = genericToJSON jsonOptions
instance FromJSON TemporalExpression where parseJSON = genericParseJSON jsonOptions
instance ToJSON TemporalDocument where toJSON = genericToJSON jsonOptions
instance FromJSON TemporalDocument where parseJSON = genericParseJSON jsonOptions
instance ToJSON TemporalSnapshot where toJSON = genericToJSON jsonOptions
instance ToJSON TemporalSelection where toJSON = genericToJSON jsonOptions
