module Main (main) where

import DependencyChecks (runDependencyChecks)
import Control.Monad (unless)
import System.Directory (doesFileExist, getCurrentDirectory)
import System.FilePath ((</>))
import CaseViewChecks (runCaseViewChecks)
import ComputedInputChecks (runComputedInputChecks)
import ComputedInputRepairChecks (runComputedInputRepairChecks)
import EditingChecks (runEditingChecks)
import IndependentLinkedRegressions (runIndependentLinkedRegressions)
import InteractionChecks (runInteractionChecks)
import PresumptionAuthoringChecks (runPresumptionAuthoringChecks)
import ProjectionChecks (runProjectionChecks)
import SourceAnchorChecks (runSourceAnchorChecks)
import TemporalAuthoringChecks (runTemporalAuthoringChecks)
import TypedAuthoringChecks (runTypedAuthoringChecks)
import TypedBoundaryChecks (runTypedBoundaryChecks)

-- Reuse accepted regressions without requiring the bulk research corpus.
-- Cabal runs the suite from the package root, including in an extracted sdist.
main :: IO ()
main = do
  root <- getCurrentDirectory
  present <- doesFileExist (root </> "test/fixtures/computed-input-repair/reviewer-rule0.document.json")
  unless present (fail "SDK test fixtures absent; run from the package root")
  runDependencyChecks
  runComputedInputRepairChecks root
  runComputedInputChecks
  runTemporalAuthoringChecks root
  runProjectionChecks
  runCaseViewChecks
  runEditingChecks
  runSourceAnchorChecks
  runInteractionChecks root
  runIndependentLinkedRegressions
  runTypedAuthoringChecks root
  runTypedBoundaryChecks root
  runPresumptionAuthoringChecks root
  putStrLn "SDK distribution: accepted profile, provenance, snapshot and source regressions passed"
