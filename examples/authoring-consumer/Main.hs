{-# LANGUAGE OverloadedStrings #-}
module Main (main) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import System.Directory (createDirectoryIfMissing)
import System.Environment (getArgs)
import System.FilePath ((</>))
import Cheating
import Yuho.Authoring

main :: IO ()
main = do
  args <- getArgs
  document <- require (decodeDocument (encodeDocument cheatingDocument))
  unless (document == cheatingDocument) (fail "authoring round-trip changed content")
  let validation = validateAnalysis document "analysis:cheating"
  unless (analysisReady validation) (fail (show validation))
  compiled <- require (compileAnalysis document "analysis:cheating")
  original <- require (evaluateAnalysis compiled)
  changed <- require (compileAnalysis pendingDocument "analysis:cheating" >>= evaluateAnalysis)
  comparison <- require (compareAnalyses original changed)
  let application = evaluationReport original
      records = [("document.json",encodeDocument document),
        ("pending-document.json",encodeDocument pendingDocument),
        ("validation.json",encodeRecord validation),
        ("application.json",encodeRecord application),
        ("pending-application.json",encodeRecord (evaluationReport changed)),
        ("open-inputs.json",encodeRecord (reportOpenInputs (evaluationReport changed))),
        ("comparison.json",encodeRecord comparison),
        ("request.json",compiledRequest compiled),
        ("result.json",evaluationKernelResponse original),
        ("snapshot.json",encodeRecord (evaluationSnapshot original)),
        ("mappings.json",encodeRecord (compiledRequirements compiled)),
        ("generated-sources.json",encodeRecord (compiledSources compiled)),
        ("source-mappings.json",encodeRecord (compiledSourceMappings compiled))]
  case args of
    [] -> pure ()
    ["--artifacts",directory] -> do
      createDirectoryIfMissing True directory
      mapM_ (\(name,bytes) -> BS.writeFile (directory </> name) bytes) records
    _ -> fail "usage: yuho-authoring-consumer [--artifacts DIRECTORY]"
  mapM_ (\bytes -> BS.putStr bytes >> BS.putStr "\n")
    [encodeRecord application,encodeRecord comparison]
  where
    require :: Show a => Either a b -> IO b
    require = either (fail . show) pure
