{-# LANGUAGE OverloadedStrings #-}
module DiagramChecks (runDiagramChecks) where

import Control.Monad (unless)
import qualified Data.ByteString as BS
import qualified Data.ByteString.Char8 as Char8
import qualified Data.Text as Text
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.CoreYuho.Normalize (normalizeCase, normalizeChecked, normalizePresumption)
import Yuho.Diagram.Build (caseGraph, presumptionGraph, programGraph)
import Yuho.Diagram.Encode (encodeSemanticGraph, encodeSvg)
import Yuho.Diagram.Types (DiagramView(..), GraphNode(..), semanticGraphNodes)
import Yuho.Protocol.Json (decodeJson)
import Yuho.Surface.Case (caseModelFile, checkAnalysisCase)
import Yuho.Surface.Compile (checkParsed)
import Yuho.Surface.Modules (AuthoredModel(..), loadAuthoredModel)
import Yuho.Surface.Parser (parseAnalysisCase)
import Yuho.Surface.Presumption (loadPresumptionProgram)

runDiagramChecks :: FilePath -> IO ()
runDiagramChecks root = do
  programChecks root
  caseChecks root
  presumptionChecks root
  putStrLn "diagrams: deterministic Core-derived JSON/SVG views passed"

programChecks :: FilePath -> IO ()
programChecks root = do
  let base = root </> "research/singapore/research-release"
      modelPath = base </> "modular-singapore-criminal-law-release.yh"
      scenarioPath = base </> "scenarios/rash-endangerment/08_exception_defeats_unresolved_offence.yh"
  modelSource <- BS.readFile modelPath
  scenario <- BS.readFile scenarioPath
  authored <- loadAuthoredModel modelPath modelSource >>= right "model load"
  checked <- either (const (failed "model check")) pure
    (checkParsed modelPath (authoredModel authored) (Just (scenarioPath,scenario)))
  let core = normalizeChecked authored checked
      graph = programGraph TraceView core
      json = encodeSemanticGraph graph
      svg = encodeSvg graph
  check "semantic graph JSON decodes" (either (const False) (const True) (decodeJson json))
  check "JSON generation deterministic" (json == encodeSemanticGraph graph)
  check "SVG generation deterministic" (svg == encodeSvg graph)
  check "SVG is standalone XML-shaped output"
    ("<?xml" `BS.isPrefixOf` svg && "<svg xmlns=" `BS.isInfixOf` svg
      && "marker-end:url(#arrow)" `BS.isInfixOf` svg)
  check "stable semantic IDs are retained"
    (all (not . Text.null . graphNodeId) (semanticGraphNodes graph))
  check "rule trace includes satisfied and unresolved technical states"
    (all (`BS.isInfixOf` json) ["\"satisfied\"","\"unresolved\""])
  artifactSafety root json
  artifactSafety root svg

caseChecks :: FilePath -> IO ()
caseChecks root = do
  let path = root </> "research/singapore/research-release/case-property-deception-showcase.yh"
  source <- BS.readFile path
  declaration <- either (const (failed "case parse")) pure (parseAnalysisCase path source)
  modelPath <- either (const (failed "case model path")) pure (caseModelFile path declaration)
  modelSource <- BS.readFile modelPath
  authored <- loadAuthoredModel modelPath modelSource >>= right "case model load"
  checked <- either (const (failed "case check")) pure
    (checkAnalysisCase path declaration modelPath (authoredModel authored))
  let json = encodeSemanticGraph (caseGraph CaseView (normalizeCase authored checked))
  check "case graph has allegations and shared facts"
    ("\"kind\":\"allegation\"" `BS.isInfixOf` json
      && "\"kind\":\"shared-fact\"" `BS.isInfixOf` json
      && "\"kind\":\"fact-binding\"" `BS.isInfixOf` json)
  let tracePath = root </> "research/singapore/research-release/case-person-harm-showcase.yh"
  traceSource <- BS.readFile tracePath
  traceDeclaration <- either (const (failed "trace case parse")) pure
    (parseAnalysisCase tracePath traceSource)
  traceModelPath <- either (const (failed "trace case model path")) pure
    (caseModelFile tracePath traceDeclaration)
  traceModelSource <- BS.readFile traceModelPath
  traceAuthored <- loadAuthoredModel traceModelPath traceModelSource >>= right "trace model load"
  traceChecked <- either (const (failed "trace case check")) pure
    (checkAnalysisCase tracePath traceDeclaration traceModelPath (authoredModel traceAuthored))
  let trace = encodeSemanticGraph
        (caseGraph TraceView (normalizeCase traceAuthored traceChecked))
  check "execution trace contains satisfied, defeated and unresolved nodes"
    (all (`BS.isInfixOf` trace) ["\"satisfied\"","\"defeated\"","\"unresolved\""])

presumptionChecks :: FilePath -> IO ()
presumptionChecks root = do
  let path = root </> "rewrite/frontend/fixtures/synthetic/presumption_active.yh"
  source <- BS.readFile path
  program <- loadPresumptionProgram path source >>= right "presumption load"
  let json = encodeSemanticGraph (presumptionGraph (normalizePresumption program))
  check "presumption graph retains active derivation"
    ("\"kind\":\"presumption\"" `BS.isInfixOf` json
      && "\"status\":\"active\"" `BS.isInfixOf` json)

artifactSafety :: FilePath -> BS.ByteString -> IO ()
artifactSafety root bytes = do
  check "artifact contains no absolute checkout path"
    (not (Char8.pack root `BS.isInfixOf` bytes))
  check "artifact contains no timestamp field"
    (not ("timestamp" `BS.isInfixOf` bytes) && not ("generated_at" `BS.isInfixOf` bytes))

right :: String -> Either a b -> IO b
right label value = case value of
  Left _ -> failed label
  Right item -> pure item

check :: String -> Bool -> IO ()
check label value = unless value (failed label)

failed :: String -> IO a
failed label = putStrLn ("diagram checks failed: " <> label) >> exitFailure
