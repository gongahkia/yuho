{-# LANGUAGE OverloadedStrings #-}
module TypedAuthoringChecks (runTypedAuthoringChecks) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import Data.List (find)
import qualified Data.Text as T
import qualified Data.Text.Encoding as UTF8
import System.Environment (lookupEnv)
import System.Directory (createDirectoryIfMissing)
import System.FilePath ((</>))
import TypedExamples
import Yuho.Authoring
import Yuho.Kernel.Run (runLine)
import qualified Yuho.Protocol.Json as J
import qualified Yuho.Surface.TypedFinite as Legacy

check :: String -> Bool -> IO ()
check name value = unless value (fail ("typed authoring: " <> name))
right :: Show e => Either e a -> IO a
right = either (fail . show) pure

runTypedAuthoringChecks :: FilePath -> IO ()
runTypedAuthoringChecks root = do
  d <- right permissionDocument
  check "document valid" (null (validateTypedDocument d))
  ada <- right (evaluate d "analysis:ada")
  ben <- right (evaluate d "analysis:ben")
  check "independent actor tuples" (ruleStatus ada == ["satisfied"] && ruleStatus ben == ["unresolved"])
  let revise status = d {typedAssessments=[if typedId (typedAssessmentMeta x) == "assessment:ada" then x {typedClassification=status} else x | x <- typedAssessments d]}
  forM_ [(TechnicalTrue,"satisfied"),(TechnicalFalse,"not_satisfied"),(TechnicalUnresolved "not_determined","unresolved")] $ \(status,expected) -> do
    r <- right (evaluate (revise status) "analysis:ada")
    b <- right (evaluate (revise status) "analysis:ben")
    check "technical classifications and isolation" (ruleStatus r == [expected] && ruleStatus b == ["unresolved"])
  forM_ [(ExactInteger 34,35,"not_satisfied"),(ExactInteger 35,35,"not_satisfied"),(ExactInteger 36,35,"satisfied"),
      (UnknownInteger "integer" "not_determined",35,"unresolved"),(ExactInteger 3501,3500,"satisfied")] $ \(value,threshold,expected) -> do
    let model = thresholdDocument value threshold
    result <- right (evaluate model "analysis:threshold")
    check "independent comparator expectation" (ruleStatus result == [expected] && map typedObservedStatus (typedReportExpressions (typedEvaluationReport result)) == [expected])
    conformanceThreshold root model value threshold
  forM_ [(34,"not_satisfied"),(35,"satisfied"),(36,"not_satisfied")] $ \(value,expected) -> do
    let eq = (thresholdDocument (ExactInteger value) 35) {typedExpressions=[TypedExpression (meta "q:threshold" "Exact equality") (IntegerComparison "eq" "value:measurement" "value:threshold")]}
    result <- right (evaluate eq "analysis:threshold")
    check "integer equality" (ruleStatus result == [expected])
  conformancePermission root d
  legacyRefusals root
  projectionChecks d ada ben
  validationChecks d
  groupChecks
  check "caller medium rejection" (case normalisedThreshold "blood" "microgrammes/100mL" 1 (ExactInteger 36) of Left _ -> True; _ -> False)
  check "caller unit rejection" (case normalisedThreshold "breath" "mg/100mL" 1 (ExactInteger 36) of Left _ -> True; _ -> False)
  check "caller scale rejection" (case normalisedThreshold "breath" "microgrammes/100mL" 0 (ExactInteger 36) of Left _ -> True; _ -> False)
  check "strict unknown typed constructor" (isLeft (decodeTypedDocument (replaceBytes "\"GroundApplication\"" "\"TechnicalNot\"" (encodeTypedDocument d))))
  check "strict unknown record field" (isLeft (decodeTypedDocument (BS.cons 123 ("\"unexpected\":1," <> BS.drop 1 (encodeTypedDocument d)))))
  check "duplicate JSON keys rejected" (isLeft (decodeTypedDocument (BS.cons 123 ("\"typedDocumentId\":\"x\"," <> BS.drop 1 (encodeTypedDocument d)))))
  check "typed document rejected by proof decoder" (isLeft (decodeDocument (encodeTypedDocument d)))
  check "v0.1 tag rejected by typed loader" (isLeft (decodeTypedDocument (encodeTypedDocument d {typedDocumentFormat=authoringFormat})))
  putStrLn "typed authoring: scoped tuples, scalar boundaries, independent legacy conformance, identity/projection/source and invalid-input matrix passed"
  where isLeft (Left _) = True; isLeft _ = False

replaceBytes :: BS.ByteString -> BS.ByteString -> BS.ByteString -> BS.ByteString
replaceBytes old new = UTF8.encodeUtf8 . T.replace (UTF8.decodeUtf8 old) (UTF8.decodeUtf8 new) . UTF8.decodeUtf8

-- The reference is independently parsed .yh, encoded by the unchanged legacy
-- frontend, then run through the production kernel. Align only explicit named
-- expression/rule/proposition IDs. Request IDs, digests, spans and rule citation
-- strings are intentionally excluded; truth and proposition resolution remain.
legacyResponse :: FilePath -> String -> BS.ByteString -> IO J.J
legacyResponse root modelName scenario = do
  let path = root </> "test/fixtures/typed-authoring" </> (modelName <> ".yh")
  source <- BS.readFile path
  program <- Legacy.loadTypedFiniteProgram path source (Just ("independent-scenario.yh",scenario)) >>= right
  response <- right (J.decodeJson (runLine (Legacy.encodeTypedFiniteRequest "independent-reference" program)))
  check "legacy kernel evaluated" (J.lookupField "status" response == Just (J.JStr "evaluated"))
  pure response

semanticRow :: J.J -> T.Text -> T.Text -> Maybe [(T.Text,J.J)]
semanticRow response category key = do
  values <- J.lookupField category response >>= J.arrayValue
  row <- find ((== Just (J.JStr key)) . J.lookupField "id") values
  pure [(field,value) | field <- ["status","state"], Just value <- [J.lookupField field row]]

match :: J.J -> TypedEvaluation -> IO ()
match legacy sdk = do
  actual <- right (J.decodeJson (typedEvaluationResponse sdk))
  let report = typedEvaluationReport sdk
  forM_ [("expressions",typedReportExpressions report),("rules",typedReportRules report),("propositions",typedReportPropositions report)] $ \(category,rows) ->
    do
      check ("equal named observation category coverage " <> T.unpack category) (fmap length (J.lookupField category legacy >>= J.arrayValue) == Just (length rows))
      forM_ rows $ \row -> do
        let key = typedObservedObject row
        check ("legacy/SDK status+resolution parity " <> T.unpack key)
          (semanticRow legacy category key == semanticRow actual category key && semanticRow legacy category key /= Nothing)

conformancePermission :: FilePath -> TypedDocument -> IO ()
conformancePermission root d = do
  scenario <- BS.readFile (root </> "test/fixtures/typed-authoring/permission.yhs")
  forM_ ["analysis:ada","analysis:ben"] $ \key -> do
    -- The grounded reference selects precisely one rule, as the SDK does. This
    -- explicit text omission prevents another rule influencing its proposition.
    let dropped = if key == "analysis:ada" then "rule:ben" else "rule:ada"
        unusedExpression = if key == "analysis:ada" then "q:ben" else "q:ada"
        unusedActor = if key == "analysis:ada" then "actor:ben" else "actor:ada"
        path = root </> "test/fixtures/typed-authoring/permission.yh"
    source <- BS.readFile path
    let selectedSource = UTF8.encodeUtf8 (T.unlines [line | line <- T.lines (UTF8.decodeUtf8 source), not ((" rule " <> dropped <> " ") `T.isPrefixOf` line), not ((" requirement " <> unusedExpression <> " ") `T.isPrefixOf` line)])
        selectedScenario = UTF8.encodeUtf8 (T.unlines [line | line <- T.lines (UTF8.decodeUtf8 scenario), not ((" classify permission(" <> unusedActor <> ",") `T.isPrefixOf` line)])
    program <- Legacy.loadTypedFiniteProgram path selectedSource (Just ("reference",selectedScenario)) >>= right
    reference <- right (J.decodeJson (runLine (Legacy.encodeTypedFiniteRequest "independent" program)))
    sdk <- right (evaluate d key)
    compiled <- right (compileTypedAnalysis d key)
    bindingParity (Legacy.encodeTypedFiniteRequest "independent" program) (typedCompiledRequest compiled)
    match reference sdk
    emit key reference sdk
  -- Same-role entity/access-kind swaps are independent missing tuples, never
  -- actor Ada's fact. Wrong-type arguments fail before execution.
  source <- BS.readFile (root </> "test/fixtures/typed-authoring/permission.yh")
  let swapped = replaceBytes "q:ada = permission(actor:ada,resource:r,kind:read)" "q:ada = permission(actor:ada,resource:r,kind:write)" source
  result <- Legacy.loadTypedFiniteProgram "swapped" swapped (Just ("reference",scenario))
  case result of Left _ -> pure (); Right p -> check "legacy tuple swap missing is not false" ((J.lookupField "status" =<< either (const Nothing) Just (J.decodeJson (runLine (Legacy.encodeTypedFiniteRequest "swap" p)))) == Just (J.JStr "rejected"))

conformanceThreshold :: FilePath -> TypedDocument -> ExactScalar -> Integer -> IO ()
conformanceThreshold root model value threshold = do
  let amount = case value of ExactInteger n -> "integer " <> T.pack (show n); UnknownInteger _ _ -> "unresolved reason \"not_determined\""
      scenario = UTF8.encodeUtf8 ("typed-rules-scenario Inputs for ThresholdReference { value value:measurement = " <> amount <> "; value value:threshold = integer " <> T.pack (show threshold) <> "; }")
  legacy <- legacyResponse root "threshold" scenario
  sdk <- right (evaluate model "analysis:threshold")
  let referencePath = root </> "test/fixtures/typed-authoring/threshold.yh"
  source <- BS.readFile referencePath
  program <- Legacy.loadTypedFiniteProgram referencePath source (Just ("independent-scenario",scenario)) >>= right
  compiled <- right (compileTypedAnalysis model "analysis:threshold")
  bindingParity (Legacy.encodeTypedFiniteRequest "independent" program) (typedCompiledRequest compiled)
  match legacy sdk
  emit ("threshold-" <> T.pack (show value) <> "-" <> T.pack (show threshold)) legacy sdk

projectionChecks :: TypedDocument -> TypedEvaluation -> TypedEvaluation -> IO ()
projectionChecks d ada ben = do
  p <- right (projectTypedEvaluation ada)
  q <- right (projectTypedEvaluation ben)
  info <- right (inspectTypedExpression p "q:ada")
  check "tuple roles and multi-assertion cross-context provenance" (length (typedFocusArguments info) == 3 && length (typedFocusAssertions info) == 2 && any ((== "actor:zoe") . scopeActor . assertionScope) (typedFocusAssertions info))
  check "selected and alternative distinct" (fmap (typedId . typedAssessmentMeta) (typedFocusSelected info) == Just "assessment:ada" && map (typedId . typedAssessmentMeta) (typedFocusAlternatives info) == ["assessment:ada-alternative"])
  check "no invented input or alternative computation" (all (\n -> typedNodeKind n `notElem` ["assessment","application","scalar","value","entity","source","assertion"] || typedNodeObservation n == Nothing) (typedProjectionNodes (typedProjectionData p)))
  ref <- right caseReference
  recovered <- right (recoverTypedSource p ref)
  check "UTF8 original recovery" (excerptText recovered == Just "Zoë permits Ada to read Server R.")
  locator <- right (recoverTypedSource p (SourceRef "source:cma" Nothing))
  check "locator only remains unanchored" (excerptText locator == Nothing)
  let revised = d {typedAssessments=[x {typedClassification=TechnicalFalse} | x <- typedAssessments d]}
  revisedRun <- right (evaluate revised "analysis:ada")
  check "snapshots change" (typedSnapshotId (typedEvaluationSnapshot revisedRun) /= typedSnapshotId (typedEvaluationSnapshot ada))
  check "stale overlay rejects" (case projectTypedEvaluationOn revised ada of Left _ -> True; _ -> False)
  check "original inspectable" (typedFocusSnapshot info == typedSnapshotId (typedEvaluationSnapshot ada))
  check "different scoped occurrences" (map typedNodeId (filter ((== "occurrence") . typedNodeKind) (typedProjectionNodes (typedProjectionData p))) /= map typedNodeId (filter ((== "occurrence") . typedNodeKind) (typedProjectionNodes (typedProjectionData q))))
  revisedProjection <- right (projectTypedEvaluation revisedRun)
  check "stable same-law occurrence alignment" (map typedNodeId (filter ((== "occurrence") . typedNodeKind) (typedProjectionNodes (typedProjectionData p))) == map typedNodeId (filter ((== "occurrence") . typedNodeKind) (typedProjectionNodes (typedProjectionData revisedProjection))))
  let metadataOnly = d {typedAssessments=[x {typedAssessmentReason=typedAssessmentReason x <> " Editorial clarification."} | x <- typedAssessments d]}
  metadataResult <- right (evaluate metadataOnly "analysis:ada")
  check "authorship-only snapshot revision preserves computed consequences" (typedSnapshotId (typedEvaluationSnapshot metadataResult) /= typedSnapshotId (typedEvaluationSnapshot ada) && ruleStatus metadataResult == ruleStatus ada)
  forM_ [[],["source:synthetic"]] $ \sources -> do
    view <- right (typedReferenceView p (TypedExpressionFocus "q:ada") sources)
    check "validated endpoints and partitions" (null (validateTypedView p view) && null (validateTypedProjection (typedProjectionData p)))
    _ <- right (encodeTypedViewSvg p view)
    _ <- right (encodeTypedViewXml p view)
    _ <- right (encodeTypedViewJson p view)
    check "view leaves snapshot untouched" (typedFocusSnapshot info == typedSnapshotId (typedProjectionSnapshot (typedProjectionData p)))
  let draft = d {typedAnalyses=[a {selectedTypedAssessments=[]} | a <- typedAnalyses d]}
  dp <- right (projectTypedAuthored draft "analysis:ada")
  check "draft not implicitly evaluated" (all ((== Nothing) . typedNodeObservation) (typedProjectionNodes (typedProjectionData dp)) && typedProjectionReport (typedProjectionData dp) == Nothing)
  _ <- right (decodeTypedDocument (encodeTypedDocument d)) >>= \r -> check "round trip" (r == d)
  check "unknown focus actionable" (case inspectTypedExpression p "does-not-exist" of Left [e] -> "does-not-exist" `elem` diagnosticObjects e; _ -> False)
  check "wrong analysis scope focus rejects" (case inspectTypedExpression q "q:ada" of Left _ -> True; _ -> False)

validationChecks :: TypedDocument -> IO ()
validationChecks d = do
  let reject code model key = check ("reject " <> T.unpack code) (not (typedAnalysisReady r) && code `elem` map diagnosticCode (typedDiagnostics r)) where r = validateTypedAnalysis model key
      changeApps f = d {typedApplications=map f (typedApplications d)}
      missing = d {typedAnalyses=[a {selectedTypedAssessments=[]} | a <- typedAnalyses d]}
  reject "TMISSING" missing "analysis:ada"
  check "missing not unresolved inventory" (map typedOpenState (typedOpenInputs (validateTypedAnalysis missing "analysis:ada")) == ["missing"] && map typedOpenState (typedOpenInputs (validateTypedAnalysis d "analysis:ben")) == ["unresolved"])
  forM_ [d {typedEntityTypes=typedEntityTypes d ++ typedEntityTypes d},
      d {typedEntities=typedEntities d ++ typedEntities d}, d {typedPredicates=typedPredicates d ++ typedPredicates d},
      d {typedApplications=typedApplications d ++ typedApplications d}, d {typedExpressions=typedExpressions d ++ typedExpressions d},
      d {typedRules=typedRules d ++ typedRules d},d {typedPropositions=typedPropositions d ++ typedPropositions d}]
    (\model -> reject "TDUPLICATE" model "analysis:ada")
  reject "TTYPE" d {typedEntities=[x {entityNominalType="unknown"} | x <- typedEntities d]} "analysis:ada"
  reject "TARITY" (changeApps (\a -> a {applicationTuple=(applicationTuple a) {tupleArguments=[]}})) "analysis:ada"
  reject "TTYPE" (changeApps (\a -> a {applicationTuple=(applicationTuple a) {tupleArguments=["resource:r","actor:ada","kind:read"]}})) "analysis:ada"
  reject "TTUPLE" (changeApps (\a -> a {applicationTuple=(applicationTuple a) {tupleArguments=["actor:ada","resource:r","kind:write"]}})) "analysis:ada"
  let swapped = d {typedApplications=typedApplications d ++ [TypedApplication (meta "application:ada-write" "Different access kind") (GroundTuple "permission" ["actor:ada","resource:r","kind:write"])],
        typedExpressions=[if typedId (expressionMeta e) == "q:ada" then e {expressionForm=GroundApplication "application:ada-write"} else e | e <- typedExpressions d]}
  reject "TMISSING" swapped "analysis:ada"
  reject "TPREDICATE" (changeApps (\a -> a {applicationTuple=(applicationTuple a) {tuplePredicate="unknown"}})) "analysis:ada"
  reject "TSCOPE" d {typedAnalyses=[a {selectedTypedAssessments=["assessment:ada"]} | a <- typedAnalyses d]} "analysis:ben"
  reject "TAMBIGUOUS" d {typedAnalyses=[a {selectedTypedAssessments=["assessment:ada","assessment:ada-alternative"]} | a <- typedAnalyses d]} "analysis:ada"
  reject "TTARGET" d "unknown-analysis"
  reject "TLINK" d {typedLinks=TypedLink "bad:use" "q:ada" "q:ben" "use":typedLinks d} "analysis:ada"
  reject "TSHARING" d {typedLinks=TypedLink "shared" "rule:ben" "q:ada" "typed_body":typedLinks d} "analysis:ada"
  reject "TMETADATA" d {typedAssessments=[x {typedAssessmentReason="  "} | x <- typedAssessments d]} "analysis:ada"
  reject "TSOURCE" d {typedOriginalSources=[]} "analysis:ada"
  reject "TSOURCE" d {typedAssessments=[x {typedAssessmentMeta=(typedAssessmentMeta x) {typedSources=[SourceRef "source:synthetic" (Just (TextSpan 2 3 1 3 1 4))]}} | x <- typedAssessments d]} "analysis:ada"
  let threshold = thresholdDocument (ExactInteger 36) 35
  reject "TDUPLICATE" threshold {typedScalars=typedScalars threshold ++ typedScalars threshold} "analysis:threshold"
  reject "TSCALAR" threshold {typedScalars=[x {scalarDeclaredType="date"} | x <- typedScalars threshold]} "analysis:threshold"
  reject "TVALUE" threshold {typedValues=[x {valueExact=UnknownInteger "date" "uncertain"} | x <- typedValues threshold]} "analysis:threshold"
  reject "TOPERATOR" threshold {typedExpressions=[TypedExpression (meta "q:threshold" "not supported") (IntegerComparison "lt" "value:measurement" "value:threshold")]} "analysis:threshold"
  reject "TVERSION" d {typedDocumentFormat=linkedAuthoringFormat} "analysis:ada"
  reject "TLIMIT" d {typedLimitations=[T.replicate 1048577 "x"]} "analysis:ada"
  -- Editing the tuple together with its assessment's target copy but omitting
  -- an explicit classification selection still fails rather than borrowing A.
  reject "TMISSING" (d {typedAnalyses=typedAnalyses missing}) "analysis:ada"

groupChecks :: IO ()
groupChecks = do
  let base = thresholdDocument (ExactInteger 36) 35
      leaf key op = TypedExpression (meta key key) (IntegerComparison op "value:measurement" "value:threshold")
      group kind = base {typedExpressions=[TypedExpression (meta "q:root" "Group") kind,leaf "q:gt" "gt",leaf "q:eq" "eq"],typedLinks=[TypedLink "body" "rule:threshold" "q:root" "typed_body",TypedLink "child:gt" "q:root" "q:gt" "typed_member",TypedLink "child:eq" "q:root" "q:eq" "typed_member"]}
  forM_ [(TypedAll,"not_satisfied"),(TypedAny,"satisfied")] $ \(kind,status) -> do
    r <- right (evaluate (group kind) "analysis:threshold")
    check "backend finite group truth and real named-child coverage" (ruleStatus r == [status] && length (typedReportExpressions (typedEvaluationReport r)) == 3)
  let cyclic = (group TypedAll) {typedLinks=typedLinks (group TypedAll) ++ [TypedLink "cycle" "q:root" "q:root" "typed_member"]}
  check "cycle diagnostic" ("TCYCLE" `elem` map diagnosticCode (validateTypedDocument cyclic))
  -- Full binary tree depth: authored depth four admitted, five rejected. Each
  -- occurrence compiles to a named observation; protocol expansion counts them.
  let tree depth = base {typedExpressions=map fst nodes,typedLinks=TypedLink "body" "rule:threshold" "n" "typed_body":concatMap snd nodes}
        where nodes = build depth "n"
              build 0 key = [(leaf key "gt",[])]
              build n key = (TypedExpression (meta key key) TypedAll,[TypedLink (key<>"-l") key (key<>"l") "typed_member",TypedLink (key<>"-r") key (key<>"r") "typed_member"]):build (n-1) (key<>"l") ++ build (n-1) (key<>"r")
  check "depth four admitted" (typedAnalysisReady (validateTypedAnalysis (tree (4::Int)) "analysis:threshold"))
  check "depth five rejected" ("TDEPTH" `elem` map diagnosticCode (typedDiagnostics (validateTypedAnalysis (tree (5::Int)) "analysis:threshold")))
  -- 511 legal expression nodes at depth <=4 using wide groups: authored size
  -- fits the limits but repeated named expansion exceeds kernel max_nodes.
  let wide = base {typedExpressions=TypedExpression (meta "root" "Wide root") TypedAll:
          [TypedExpression (meta ("g"<>t i) "Subgroup") TypedAll | i <- [1..10::Int]] ++ [leaf ("v"<>t i) "gt" | i <- [1..500::Int]],
        typedLinks=TypedLink "body" "rule:threshold" "root" "typed_body":
          [TypedLink ("edge:g"<>t i) "root" ("g"<>t i) "typed_member" | i <- [1..10::Int]] ++
          [TypedLink ("edge:v"<>t i) ("g"<>t (1+(i-1) `div` 50)) ("v"<>t i) "typed_member" | i <- [1..500::Int]]}
      t = T.pack . show
  check "expanded budget delegates real kernel rejection" ("TBACKEND" `elem` map diagnosticCode (typedDiagnostics (validateTypedAnalysis wide "analysis:threshold")))

-- Optional review evidence does not alter semantic assertions or fixture inputs.
emit :: T.Text -> J.J -> TypedEvaluation -> IO ()
emit label reference sdk = do
  output <- lookupEnv "YUHO_TYPED_EVIDENCE"
  case output of
    Nothing -> pure ()
    Just folder -> do
      createDirectoryIfMissing True folder
      let name = T.unpack (T.map (\c -> if c `elem` (": /\\\"" :: String) then '-' else c) label)
      BS.writeFile (folder </> name <> ".legacy.json") (J.encodeJson reference)
      BS.writeFile (folder </> name <> ".sdk.json") (typedEvaluationResponse sdk)
      BS.writeFile (folder </> name <> ".report.json") (encodeRecord (typedEvaluationReport sdk))

legacyRefusals :: FilePath -> IO ()
legacyRefusals root = do
  source <- BS.readFile (root </> "test/fixtures/typed-authoring/permission.yh")
  scenario <- BS.readFile (root </> "test/fixtures/typed-authoring/permission.yhs")
  let rejected name model inputs = do
        program <- Legacy.loadTypedFiniteProgram "independent-invalid-model" model (Just ("independent-invalid-inputs",inputs))
        case program of
          Left _ -> pure ()
          Right value -> do
            response <- right (J.decodeJson (runLine (Legacy.encodeTypedFiniteRequest "invalid-reference" value)))
            check name (J.lookupField "status" response == Just (J.JStr "rejected"))
  rejected "legacy wrong argument type" (replaceBytes "q:ada = permission(actor:ada,resource:r,kind:read)" "q:ada = permission(resource:r,actor:ada,kind:read)" source) scenario
  rejected "legacy wrong arity" (replaceBytes "q:ada = permission(actor:ada,resource:r,kind:read)" "q:ada = permission(actor:ada,resource:r)" source) scenario
  rejected "legacy missing classification" source "typed-rules-scenario Missing for PermissionReference {}"
  let onlyBen = UTF8.encodeUtf8 (T.unlines [line | line <- T.lines (UTF8.decodeUtf8 source), not (" rule rule:ada " `T.isPrefixOf` line), not (" requirement q:ada " `T.isPrefixOf` line)])
      negative = replaceBytes "as unresolved" "as not_proved" (UTF8.encodeUtf8 (T.unlines [line | line <- T.lines (UTF8.decodeUtf8 scenario), not (" classify permission(actor:ada," `T.isPrefixOf` line)]))
  program <- Legacy.loadTypedFiniteProgram "independent-negative" onlyBen (Just ("negative",negative)) >>= right
  response <- right (J.decodeJson (runLine (Legacy.encodeTypedFiniteRequest "negative-reference" program)))
  d <- right permissionDocument
  let revised = d {typedAssessments=[if typedId (typedAssessmentMeta a) == "assessment:ben" then a {typedClassification=TechnicalFalse} else a | a <- typedAssessments d]}
  result <- right (evaluate revised "analysis:ben")
  match response result
  emit "analysis-ben-negative" response result
  scalarSource <- BS.readFile (root </> "test/fixtures/typed-authoring/threshold.yh")
  scalarScenario <- BS.readFile (root </> "test/fixtures/typed-authoring/threshold.yhs")
  rejected "legacy incompatible scalar type" (replaceBytes "value:measurement type integer" "value:measurement type date" scalarSource) scalarScenario

-- Compare concrete tuple identities/types and exact scalar payloads independently
-- of the adapter's reports. Fixture reasons are authored separately and differ.
bindingParity :: BS.ByteString -> BS.ByteString -> IO ()
bindingParity reference actual = do
  left <- right (J.decodeJson reference)
  rightValue <- right (J.decodeJson actual)
  let program field value = J.lookupField "program" value >>= J.lookupField field >>= J.arrayValue
      facts value = maybe [] (map (\row -> (J.lookupField "predicate" row,J.lookupField "arguments" row,J.lookupField "status" row))) (program "facts" value)
      selectedFacts = facts rightValue
  check "independent ground predicate+arguments+classification parity" (selectedFacts == facts left)
  check "independent exact scalar value/type payload parity" (program "values" left == program "values" rightValue)
  check "ground rules have no parameter aggregation" (all ((== Just (J.JArr [])) . J.lookupField "parameters") (maybe [] id (program "rules" rightValue)))
