-- | Experimental finite checked dependencies, separate from computed-input v0.1.
-- Unchecked authored records are public; checked plans and executions are opaque.
module Yuho.Authoring.Dependency
  ( module Yuho.Dependency.Types, CheckedPlan, checkDependencyPlan
  , DependencyExecution, executeDependencyPlan, reportDependencyPlan, dependencyExecutionId
  , DependencyArtifact, saveDependencyArtifact, encodeDependencyArtifact, decodeDependencyArtifact
  , checkDependencyArtifact, replayDependencyPlan, checkDependencyAttachment
  , encodeDependencyDocument, decodeDependencyDocument
  , validateDependencyViewBindings, validateDependencyProjection
  , dependencyComponentSources, recoverDependencyReference, dependencyOriginRecord
  , publishDependencyPlan
  , projectDependencyPlan, dependencyGraph, sourceMapDependencyPlan, dependencyViewBindings, exportDependencyPlan
  ) where
import Yuho.Dependency.Types
import Yuho.Dependency.Check (CheckedPlan,checkDependencyPlan)
import Yuho.Dependency.Run (DependencyExecution,executeDependencyPlan,reportDependencyPlan,dependencyExecutionId)
import Yuho.Dependency.Codec
import Yuho.Dependency.Source (dependencyComponentSources,recoverDependencyReference,dependencyOriginRecord)
import Yuho.Dependency.Publication (publishDependencyPlan)
import Yuho.Dependency.Projection
