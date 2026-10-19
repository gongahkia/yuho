{-# LANGUAGE OverloadedStrings #-}
-- | Pure snapshot construction shared by compilation and non-executing views.
module Yuho.Authoring.Snapshot (makeSnapshot) where

import Data.List (nub)
import Yuho.Authoring.Codec (encodeRecord)
import Yuho.Authoring.Types
import Yuho.Protocol.Decode (sha256Text)

makeSnapshot :: AuthoringDocument -> Analysis -> Snapshot
makeSnapshot doc analysis = Snapshot
  (sha256Text (encodeRecord (doc,analysis,evaluatorProfile)))
  (sha256Text (encodeRecord (law,originalSources))) evaluatorProfile analysis doc
  where
    law = documentLaw doc
    referenced = nub [referenceSource ref | n <- lawNodes law, ref <- nodeSources n]
    originalSources = [s | s <- documentSources doc, sourceId s `elem` referenced]
