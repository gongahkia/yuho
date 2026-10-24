{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
-- | One failure-safe publication path for CLI and programmatic consumers.
module Yuho.Dependency.Publication (publishDependencyPlan) where
import Control.Exception (IOException,evaluate,try)
import qualified Data.ByteString as BS
import qualified Data.Text as T
import Yuho.Dependency.Types
import Yuho.Dependency.Check (failure)
import Yuho.Dependency.Run (DependencyExecution)
import Yuho.Dependency.Projection (exportDependencyPlan)
import Yuho.Surface.Publication (publishExport)

publishDependencyPlan :: FilePath -> DependencyExecution -> IO (Either DependencyDiagnostic ())
publishDependencyPlan out execution=case exportDependencyPlan execution of
  Left diagnostic->pure (Left diagnostic)
  Right files->do
    attempted<-try (mapM_ (evaluate . BS.length . snd) files >> publishExport out files)
    pure $ case attempted of
      Left (issue::IOException)->failure "DEPPUBLISH" [T.pack out]
        ("could not atomically publish complete output: "<>T.pack (show issue))
      Right ()->Right ()
