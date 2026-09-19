{-# LANGUAGE OverloadedStrings #-}
module TypedFiniteChecks (runTypedFiniteChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import Yuho.CoreYuho.TypedFinite
import Yuho.Diagram.Build (typedFiniteCaseGraph, typedFiniteGraph)
import Yuho.Diagram.Encode (encodeSemanticGraph, encodeSvg)
import Yuho.Diagram.Types (DiagramView(..))
import Yuho.Exception.Types (Truth(..))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (decodeJson, lookupField, textValue)
import Yuho.Surface.Token (Diagnostic(..))
import Yuho.Surface.TypedFinite

runTypedFiniteChecks :: FilePath -> IO ()
runTypedFiniteChecks root = do
  semanticMatrices
  fixtureChecks root
  diagramChecks root
  refusalChecks root
  putStrLn "typed finite rules: exhaustive bounded semantics, fixtures and refusals passed"

semanticMatrices :: IO ()
semanticMatrices = do
  let domain = [TrueValue,FalseValue,UnresolvedValue]
      lists = concat [sequence (replicate size domain) | size <- [0..4]]
  forM_ domain $ \truth -> check "negation involution"
    (negateTruth (negateTruth truth) == truth)
  forM_ lists $ \values -> forM_ [0..5] $ \threshold -> do
    let satisfied = length (filter (== TrueValue) values)
        unresolved = length (filter (== UnresolvedValue) values)
        upper = satisfied + unresolved
    check "at-least interval semantics" (cardinalityTruth AtLeast threshold values ==
      if satisfied >= threshold then TrueValue else if upper < threshold
        then FalseValue else UnresolvedValue)
    check "at-most interval semantics" (cardinalityTruth AtMost threshold values ==
      if upper <= threshold then TrueValue else if satisfied > threshold
        then FalseValue else UnresolvedValue)
    check "exactly interval semantics" (cardinalityTruth Exactly threshold values ==
      if satisfied == threshold && unresolved == 0 then TrueValue
      else if satisfied > threshold || upper < threshold then FalseValue else UnresolvedValue)
    check "cardinality order independence"
      (all (\kindValue -> cardinalityTruth kindValue threshold values ==
        cardinalityTruth kindValue threshold (reverse values)) [AtLeast,AtMost,Exactly])
  check "same-currency money comparison"
    (compareScalar LessEqual (MoneyValue "SGD" 100) (MoneyValue "SGD" 101) Nothing
      == Right TrueValue)
  check "cross-currency comparison rejects"
    (compareScalar Equal (MoneyValue "SGD" 100) (MoneyValue "USD" 100) Nothing
      == Left "incompatible scalar comparison")
  check "explicit unresolved comparison propagates"
    (compareScalar Equal (ScalarUnresolved "pending" IntegerType) (IntegerValue 1) Nothing
      == Right UnresolvedValue)
  check "capture-free variable substitution"
    (substituteTerm (Map.singleton "var:item" "item:laptop") (VariableTerm "var:item")
      == Right "item:laptop")

fixtureChecks :: FilePath -> IO ()
fixtureChecks root = do
  let base = root </> "rewrite/frontend/fixtures/typed-finite"
      fixtures =
        [(base </> "fictional-typed-rules.yh",base </> "fictional-typed-rules-satisfied.yh")
        ,(base </> "multi-person-property.yh",base </> "multi-person-property-scenario.yh")
        ,(base </> "modular-typed-rules.yh",base </> "modular-typed-rules-scenario.yh")
        ,(root </> "research/singapore/research-release/typed-section82-showcase.yh",
          root </> "research/singapore/research-release/typed-section82-showcase-scenario.yh")]
  forM_ fixtures $ \(modelPath,scenarioPath) -> do
    model <- BS.readFile modelPath
    scenario <- BS.readFile scenarioPath
    program <- loadTypedFiniteProgram modelPath model (Just (scenarioPath,scenario))
      >>= either (const (failed "typed fixture check")) pure
    result <- either (const (failed "typed fixture evaluation")) pure (evaluateTypedFinite program)
    let first = encodeTypedFiniteRequest "typed-fixture-request" program
        second = encodeTypedFiniteRequest "typed-fixture-request" program
        response = runLine first
    check "typed finite compile deterministic" (first == second)
    check "typed finite kernel evaluates" (status response == Just "evaluated")
    check "typed finite result has propositions" (not (null (finiteResultPropositions result)))
  caseSource <- BS.readFile (base </> "multi-person-property-case.yh")
  declaration <- loadTypedFiniteCase (base </> "multi-person-property-case.yh") caseSource
    >>= either (const (failed "typed finite case")) pure
  check "typed finite case has two independent allegations"
    (length (typedCaseAllegations declaration) == 2)
  check "typed finite case retains one explicit shared fact"
    (length (typedCaseShared declaration) == 1)

diagramChecks :: FilePath -> IO ()
diagramChecks root = do
  let base = root </> "rewrite/frontend/fixtures/typed-finite"
      retained = root </> "docs/rewrite/typed-finite-diagram-fixtures"
      fictionalModel = base </> "fictional-typed-rules.yh"
      fictionalScenario = base </> "fictional-typed-rules-satisfied.yh"
      modularModel = base </> "modular-typed-rules.yh"
      modularScenario = base </> "modular-typed-rules-scenario.yh"
  fictional <- load "fictional graph" fictionalModel fictionalScenario
  modular <- load "module graph" modularModel modularScenario
  caseSource <- BS.readFile (base </> "multi-person-property-case.yh")
  declaration <- loadTypedFiniteCase (base </> "multi-person-property-case.yh") caseSource
    >>= either (const (failed "typed case graph")) pure
  let fictionalResult = evaluated "fictional graph" fictional
      modularResult = evaluated "module graph" modular
      caseResults = [(typedAllegationId item,typedAllegationResult item)
        | item <- typedCaseAllegations declaration]
      artifacts =
        [("fictional-rule",typedFiniteGraph RuleView fictional fictionalResult)
        ,("module-composition",typedFiniteGraph ModulesView modular modularResult)
        ,("multi-allegation-case",typedFiniteCaseGraph CaseView (typedCaseId declaration)
            caseResults (typedCaseShared declaration))
        ,("conflict-trace",typedFiniteGraph TraceView fictional fictionalResult)]
  forM_ artifacts $ \(name,graph) -> do
    expectedJson <- BS.readFile (retained </> name <> ".json")
    expectedSvg <- BS.readFile (retained </> name <> ".svg")
    check (name <> " retained JSON") (encodeSemanticGraph graph == expectedJson)
    check (name <> " retained SVG") (encodeSvg graph == expectedSvg)
  check "typed diagram exposes conflict and priority"
    (all (`BS.isInfixOf` encodeSemanticGraph (typedFiniteGraph TraceView fictional fictionalResult))
      ["\"kind\":\"conflict\"","\"kind\":\"priority\""])
  where
    load label modelPath scenarioPath = do
      model <- BS.readFile modelPath
      scenario <- BS.readFile scenarioPath
      loadTypedFiniteProgram modelPath model (Just (scenarioPath,scenario))
        >>= either (const (failed label)) pure
    evaluated label program = either (const (error (label <> " evaluation failed"))) id
      (evaluateTypedFinite program)

refusalChecks :: FilePath -> IO ()
refusalChecks root = do
  let base = root </> "rewrite/frontend/fixtures/typed-finite"
      modelPath = base </> "fictional-typed-rules.yh"
      scenarioPath = base </> "fictional-typed-rules-satisfied.yh"
  model <- BS.readFile modelPath
  scenario <- BS.readFile scenarioPath
  let missing = Encoding.encodeUtf8 (Text.replace
        "  classify assists(actor:blair,actor:alex) as proved reason \"synthetic supplied classification\";\n"
        "" (Encoding.decodeUtf8 scenario))
      wrongType = Encoding.encodeUtf8 (Text.replace
        "takes(actor:alex,item:laptop)" "takes(item:laptop,actor:alex)"
        (Encoding.decodeUtf8 scenario))
      priorityCycle = Encoding.encodeUtf8 (Text.replace
        "  priority r:minor-exception over r:general;"
        "  priority r:minor-exception over r:general;\n  priority r:general over r:minor-exception;"
        (Encoding.decodeUtf8 model))
  assertDiagnostic "missing ground fact refuses" "SFT011" =<<
    loadTypedFiniteProgram modelPath model (Just (scenarioPath,missing))
  assertDiagnostic "wrong nominal type refuses" "SFT005" =<<
    loadTypedFiniteProgram modelPath model (Just (scenarioPath,wrongType))
  assertDiagnostic "priority cycle refuses" "SFT007" =<<
    loadTypedFiniteProgram modelPath priorityCycle (Just (scenarioPath,scenario))

status :: BS.ByteString -> Maybe Text.Text
status bytes = either (const Nothing) (\value -> lookupField "status" value >>= textValue)
  (decodeJson bytes)

assertDiagnostic :: String -> Text.Text -> Either Diagnostic a -> IO ()
assertDiagnostic label code result = check label $ case result of
  Left issue -> diagnosticCode issue == code
  Right _ -> False

check :: String -> Bool -> IO ()
check label value = unless value (failed label)

failed :: String -> IO a
failed label = putStrLn ("typed finite checks failed: " <> label) >> exitFailure
