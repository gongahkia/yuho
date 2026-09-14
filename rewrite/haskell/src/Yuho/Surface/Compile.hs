module Yuho.Surface.Compile (checkSource, compileSource) where

import qualified Data.ByteString as BS
import Yuho.Surface.AST (Checked)
import Yuho.Surface.Check (checkModel)
import Yuho.Surface.Lower (lowerChecked)
import Yuho.Surface.Parser (parseModel, parseScenario)
import Yuho.Surface.Token (Diagnostic)

checkSource :: FilePath -> BS.ByteString -> Maybe (FilePath, BS.ByteString)
  -> Either Diagnostic Checked
checkSource path source scenario = do
  model <- parseModel path source
  supplied <- traverse (\(scenarioPath, bytes) -> do
    parsed <- parseScenario scenarioPath bytes
    pure (scenarioPath, parsed)) scenario
  checkModel path model supplied

compileSource :: FilePath -> BS.ByteString -> Maybe (FilePath, BS.ByteString)
  -> Either Diagnostic BS.ByteString
compileSource path source scenario = checkSource path source scenario >>= lowerChecked
