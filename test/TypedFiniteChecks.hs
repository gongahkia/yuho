{-# LANGUAGE OverloadedStrings #-}
module TypedFiniteChecks (runTypedFiniteChecks) where

import Control.Monad (forM_, unless)
import Control.Exception (evaluate)
import qualified Data.ByteString as BS
import qualified Data.Map.Strict as Map
import qualified Data.Text as Text
import qualified Data.Text.Encoding as Encoding
import System.Exit (exitFailure)
import System.FilePath ((</>))
import System.Timeout (timeout)
import Yuho.CoreYuho.TypedFinite
import Yuho.Diagram.Build (typedFiniteCaseGraph, typedFiniteGraph)
import Yuho.Diagram.Encode (encodeSemanticGraph, encodeNativeSemanticGraph, encodeNativeSvg)
import Yuho.Diagram.Types (DiagramView(..), SemanticGraph(..), GraphNode(..), GraphEdge(..))
import Yuho.Exception.Types (Truth(..))
import Yuho.Kernel.Run (runLine)
import Yuho.Protocol.Json (J(..), arrayValue, decodeJson, lookupField, textValue)
import Yuho.Surface.Token (Diagnostic(..))
import Yuho.Surface.TypedFinite

runTypedFiniteChecks :: FilePath -> IO ()
runTypedFiniteChecks root = do
  semanticMatrices
  primitiveIdentityChecks
  boundedGraphChecks
  registryCheck root
  fixtureChecks root
  diagramChecks root
  scopedIdentityChecks
  refusalChecks root
  putStrLn "typed finite rules: exhaustive bounded semantics, fixtures and refusals passed"

-- Independent closed-form size oracle: E(0)=1, E(n)=1+2*(1+E(n-1)).
-- Computing this bound must not allocate the exponentially expanded tree.
boundedGraphChecks :: IO ()
boundedGraphChecks = do
  let name i = "q:" <> Text.pack (show (i :: Int))
      program n = TypedFiniteProgram "bounded" [EntityTypeDecl "t"] [EntityDecl "a" "t"]
        [PredicateDecl "p" ["t"] PredicateConduct] [] []
        ((name 0,PredicateExpr "p" [EntityTerm "a"]) :
          [(name i,AllExpr [ReferenceExpr (name (i-1)),ReferenceExpr (name (i-1))]) | i <- [1..n]])
        [] [] [] [] [GroundFact "p" ["a"] TrueValue "synthetic"] Map.empty [] ["fictional"]
  forM_ [0,1,5,29,100] $ \n -> do
    let expected = Right (4 + sum [4 * (2 ^ i :: Integer) - 3 | i <- [0..n]])
    bounded <- timeout 5000000 (evaluate (expandedNodeEstimate (program n) == expected))
    check "exact memoized expansion estimate" (bounded == Just True)
  let rule i = "r:" <> Text.pack (show (i :: Int))
      priorities = [PriorityDecl (rule i) (rule j) | i <- [0..39], j <- [i+1,i+2], j < 40]
      observations = [RuleObservation (rule 39) Establish "p:x" TrueValue [] []
        ,RuleObservation "r:unrelated" Defeat "p:x" TrueValue [] []]
      expected = Right (PropositionObservation "p:x" UnresolvedValue "conflict" [rule 39,"r:unrelated"])
  bounded <- timeout 5000000 (evaluate (resolveProposition priorities observations "p:x" == expected))
  check "unrelated opposing rule remains conflict in bounded priority DAG" (bounded == Just True)

-- Direct shared-evaluator and scalar/read-category controls. Literal tuples
-- and expected observations are the oracle, not rendered keys.
primitiveIdentityChecks :: IO ()
primitiveIdentityChecks = do
  let dep="dep_collision"
      printed="dep_collision(dep_template_entity)"
      tuples=[("p",["a(b"],TrueValue),("p(a",["b"],FalseValue),
        ("pair",["x,y","z"],TrueValue),("pair",["x","y,z"],UnresolvedValue)]
      facts=[GroundFact p args v "independent tuple" | (p,args,v)<-tuples]
      program=TypedFiniteProgram "identity-control" [EntityTypeDecl "person"]
        [EntityDecl i "person" | i<-["a(b","b","x,y","z","x","y,z","dep_template_entity"]]
        [PredicateDecl "p" ["person"] PredicateRelationship,PredicateDecl "p(a" ["person"] PredicateRelationship,
         PredicateDecl "pair" ["person","person"] PredicateRelationship,PredicateDecl dep ["person"] PredicateCircumstance]
        [ScalarDecl printed IntegerType,ScalarDecl "upper" IntegerType] []
        ([("q:"<>Text.pack (show i),PredicateExpr p (map EntityTerm args)) | (i,(p,args,_))<-zip [0::Int ..] tuples]
         ++[(printed,PredicateExpr "p(a" [EntityTerm "b"]),("q:ref",ReferenceExpr printed),
            ("q:scalar",ComparisonExpr LessThan printed "upper" Nothing),
            ("q:dep",PredicateExpr dep [EntityTerm "dep_template_entity"]),
            ("q:mixed",AllExpr [PredicateExpr "p(a" [EntityTerm "b"],ReferenceExpr "q:dep"])])
        [] [] [] [] (facts++[GroundFact dep ["dep_template_entity"] UnresolvedValue "real conflicting technical input"])
        (Map.fromList [(printed,IntegerValue 0),("upper",IntegerValue 1)]) [] ["fictional identity test"]
  (result,ledger)<-either (fail . Text.unpack) pure (evaluateTypedFiniteObserved program)
  check "structurally distinct facts retain distinct values"
    (take 4 (map expressionStatus (finiteResultExpressions result))==[TrueValue,FalseValue,TrueValue,UnresolvedValue])
  let inputs q=concatMap readInputs [r | r<-ledger,readRoot r==["expression",q]]
      grounds q=[(groundPredicate f,groundArguments f) | GroundInput f<-inputs q]
  check "reference expansion preserves exact local read" (grounds "q:ref"==[("p(a",["b"])])
  check "reference name does not become a primitive read" (RequirementInput printed `elem` inputs "q:ref" && (dep,["dep_template_entity"]) `notElem` grounds "q:ref")
  check "scalar name does not become a primitive read" (inputs "q:scalar"==[ScalarInput printed,ScalarInput "upper"] && null (grounds "q:scalar"))
  check "decisive F still reads its actual U operand" (grounds "q:mixed"==[("p(a",["b"]),(dep,["dep_template_entity"])])
  let missing=program {finiteFacts=filter (\f->(groundPredicate f,groundArguments f)/=("p(a",["b"])) (finiteFacts program)}
  check "missing colliding tuple is not supplied by an alias" (case checkTypedFiniteInputs missing of Left _->True;_->False)
  check "shared evaluator refuses missing tuple" (case evaluateTypedFinite missing of Left _->True;_->False)
  check "shared evaluator refuses identical duplicate" (case evaluateTypedFinite program {finiteFacts=facts++finiteFacts program} of Left _->True;_->False)
  let graph=typedFiniteGraph TraceView program result
      ids=[graphNodeId n | n<-semanticGraphNodes graph,graphNodeKind n=="ground-fact"]
  check "ground graph identities retain colliding observations" (length ids==5 && Map.size (Map.fromList [(i,()) | i<-ids])==5)

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
  let emptyProgram = TypedFiniteProgram "empty-domain"
        [EntityTypeDecl "empty"] [] [PredicateDecl "holds" ["empty"] PredicateCircumstance]
        [] []
        [("q:forall-empty",ForallExpr "var:item" "empty"
            (PredicateExpr "holds" [VariableTerm "var:item"]))
        ,("q:exists-empty",ExistsExpr "var:item" "empty"
            (PredicateExpr "holds" [VariableTerm "var:item"]))]
        [] [] [] [] [] Map.empty [] ["fictional empty-domain identity fixture"]
      emptyStatuses = evaluateTypedFinite emptyProgram >>= \result ->
        Right (map expressionStatus (finiteResultExpressions result))
  check "empty-domain quantifier identities"
    (emptyStatuses == Right [TrueValue,FalseValue])

registryCheck :: FilePath -> IO ()
registryCheck root = do
  bytes <- BS.readFile (root </> "schema/core-yuho-conformance-v0.2.json")
  value <- either (const (failed "typed construct registry JSON")) pure (decodeJson bytes)
  check "typed construct registry schema"
    ((lookupField "schema" value >>= textValue) == Just "yuho.core-conformance/v0.2")
  let registered = case lookupField "constructs" value >>= arrayValue of
        Nothing -> []
        Just rows -> [name | row <- rows,
          Just name <- [lookupField "construct" row >>= textValue]]
      publicConstructs =
        ["typed-rules-model","entity-type","entity","predicate","ground-classification"
        ,"typed-scalar","comparison","technical-negation","finite-quantifier","cardinality"
        ,"technical-proposition","named-rule","rule-priority","typed-rules-module"
        ,"typed-rules-case","limitation"]
  check "every typed public construct has one conformance entry"
    (registered == publicConstructs)

fixtureChecks :: FilePath -> IO ()
fixtureChecks root = do
  let base = root </> "examples/typed-finite"
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
  let base = root </> "examples/typed-finite"
      retained = root </> "docs/artifacts/typed-finite-diagrams"
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
    -- v0.1 artifacts remain immutable. v0.2 intentionally adds exact scalar
    -- labels/operand links and a repaired layout: compare every retained semantic
    -- field/edge, rather than updating old files or demanding the defective SVG.
    historical <- either (const (failed (name <> " retained JSON parse"))) pure (decodeJson expectedJson)
    current <- either (const (failed (name <> " native JSON parse"))) pure
      (decodeJson (encodeNativeSemanticGraph graph))
    let rows field value = maybe [] (maybe [] id . arrayValue) (lookupField field value)
        oldNodes = rows "nodes" historical
        newNodes = rows "nodes" current
        scoped row = name == "multi-allegation-case" &&
          lookupField "kind" row `elem` [Just (JStr "proposition"),Just (JStr "conflict")]
        -- Retained v0.1 case IDs used an ambiguous concatenation. Join these
        -- observations by their independently retained scope and authored label.
        byId row = [n | n <- newNodes, if scoped row then all (\field ->
          lookupField field n == lookupField field row) ["kind","boundary","label"]
          else lookupField "id" n == lookupField "id" row]
        currentId identifier = case [n | old <- oldNodes,
            lookupField "id" old == Just identifier, n <- byId old] of
          [n] -> maybe identifier id (lookupField "id" n)
          _ -> identifier
        mappedEdge (JObj fields) = JObj [(k,if k `elem` ["from","to"]
          then currentId v else v) | (k,v) <- fields]
        mappedEdge value = value
    check (name <> " same retained node identities")
      (length oldNodes == length newNodes && all ((==1) . length . byId) oldNodes)
    forM_ oldNodes $ \old -> case byId old of
      [new] -> do
        check (name <> " retained node semantics") (all (\field ->
          lookupField field old == lookupField field new)
          ((if scoped old then [] else ["id"]) ++ ["kind","status","citation","boundary"]))
        let label row = maybe "" id (lookupField "label" row >>= textValue)
        if lookupField "kind" old == Just (JStr "scalar") then
          check (name <> " scalar detail is additive")
            (label old `Text.isPrefixOf` label new && "supplied value:" `Text.isInfixOf` label new)
        else check (name <> " non-scalar labels retained") (label old == label new)
      _ -> failed (name <> " retained node identity")
    let oldEdges = map mappedEdge (rows "edges" historical)
        newEdges = rows "edges" current
    check (name <> " every retained relationship preserved") (all (`elem` newEdges) oldEdges)
    check (name <> " only explicit scalar operand relationships added")
      (all (\e -> e `elem` oldEdges || lookupField "kind" e == Just (JStr "operand")) newEdges)
    check (name <> " native format explicitly versioned")
      (lookupField "format" current == Just (JStr "yuho.semantic-graph/v0.2"))
    check (name <> " corrected SVG deterministic and intentional")
      (encodeNativeSvg graph == encodeNativeSvg graph && encodeNativeSvg graph /= expectedSvg)
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
  let base = root </> "examples/typed-finite"
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
      lowLimit = Encoding.encodeUtf8 (Text.replace "  limit 2048;" "  limit 1;"
        (Encoding.decodeUtf8 model))
      tooManyParameters = Encoding.encodeUtf8 (Text.replace
        "rule r:general establishes"
        "rule r:general(var:a as person,var:b as person,var:c as person,var:d as person,var:e as person) establishes"
        (Encoding.decodeUtf8 model))
  assertDiagnostic "missing ground fact refuses" "SFT011" =<<
    loadTypedFiniteProgram modelPath model (Just (scenarioPath,missing))
  assertDiagnostic "wrong nominal type refuses" "SFT005" =<<
    loadTypedFiniteProgram modelPath model (Just (scenarioPath,wrongType))
  assertDiagnostic "priority cycle refuses" "SFT007" =<<
    loadTypedFiniteProgram modelPath priorityCycle (Just (scenarioPath,scenario))
  assertDiagnostic "generated-node limit refuses before evaluation" "SFT010" =<<
    loadTypedFiniteProgram modelPath lowLimit (Just (scenarioPath,scenario))
  assertDiagnostic "rule parameter limit refuses" "SFT010" =<<
    loadTypedFiniteProgram modelPath tooManyParameters (Just (scenarioPath,scenario))
  modular <- BS.readFile (base </> "modular-typed-rules.yh")
  modularScenario <- BS.readFile (base </> "modular-typed-rules-scenario.yh")
  let privateUse = Encoding.encodeUtf8 (Text.replace
        "  use entity vocab::item:modular-item;"
        "  use entity vocab::item:private;" (Encoding.decodeUtf8 modular))
  assertDiagnostic "private module declaration refuses" "SFT014" =<<
    loadTypedFiniteProgram (base </> "modular-typed-rules.yh") privateUse
      (Just (base </> "modular-typed-rules-scenario.yh",modularScenario))

-- The graph API accepts Text identities, including Unicode beyond the native
-- source identifier grammar. Expected tuples below do not use the key helper.
scopedIdentityChecks :: IO ()
scopedIdentityChecks = do
  let inputs = [("a", "b--c", TrueValue, "established")
        ,("a--b", "c", FalseValue, "not_established")
        ,("案:é", "p:同--名", UnresolvedValue, "unresolved")
        ,("案:é--p:同", "名", TrueValue, "established")]
      graph = typedFiniteCaseGraph CaseView "case:unicode"
        [(a,TypedFiniteResult [] [] [PropositionObservation p value state []])
        | (a,p,value,state) <- inputs] []
      rows = [n | n <- semanticGraphNodes graph, graphNodeKind n == "proposition"]
  check "all scoped API observations retained" (length rows == 4)
  check "scoped API identities unique"
    (length (Map.fromList [(graphNodeId n,()) | n <- rows]) == 4)
  forM_ inputs $ \(a,p,value,state) -> do
    let matches = [n | n <- rows, graphNodeBoundary n == Just a,
          graphNodeLabel n == p <> "\n" <> state,
          graphNodeStatus n == Just (truthName value)]
    check "scoped API tuple preserved" (length matches == 1)
    forM_ matches $ \n -> check "scoped API relationship preserved"
      ([graphEdgeTo e | e <- semanticGraphEdges graph, graphEdgeFrom e == graphNodeId n]
        == ["allegation:" <> a])

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
