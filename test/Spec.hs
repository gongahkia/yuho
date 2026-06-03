{-# LANGUAGE OverloadedStrings #-}

module Main (main) where

import qualified Data.Map.Strict as Map
import qualified Data.Aeson as Aeson
import qualified Data.Aeson.Key as Key
import qualified Data.Aeson.KeyMap as KeyMap
import qualified Data.Text as T
import qualified Data.Text.IO as TIO
import Data.Time (fromGregorian)
import Euclid.CLI.Options
import Euclid.Config.Loader
import Euclid.Core.Diff
import Euclid.Core.Eval
import Euclid.Core.Validation
import Euclid.Import.CSV
import Euclid.Import.GEDCOM
import Euclid.Import.JSONLD
import Euclid.Lang.AST
import Euclid.Lang.Parser
import Euclid.Model.Types
import Euclid.Tooling.LSP
import System.Directory (removeFile)
import Test.Hspec

main :: IO ()
main = hspec spec

lookupJsonObject :: T.Text -> Aeson.Object -> Maybe Aeson.Object
lookupJsonObject keyName obj =
    case KeyMap.lookup (Key.fromText keyName) obj of
        Just (Aeson.Object nestedObj) -> Just nestedObj
        _ -> Nothing

lookupJsonInt :: T.Text -> Aeson.Object -> Maybe Int
lookupJsonInt keyName obj =
    case KeyMap.lookup (Key.fromText keyName) obj of
        Just (Aeson.Number numberValue) ->
            case Aeson.fromJSON (Aeson.Number numberValue) of
                Aeson.Success value -> Just value
                Aeson.Error _ -> Nothing
        _ -> Nothing

spec :: Spec
spec = do
    describe "parser and evaluator" $
        it "loads the LOTR example into a world" $ do
            source <- TIO.readFile "examples/generative/lotr.euclid"
            case parseProgram "examples/generative/lotr.euclid" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            Map.size (worldTimelines worldValue) `shouldBe` 1
                            Map.size (worldEntities worldValue) `shouldBe` 4
                            length (worldRelationships worldValue) `shouldBe` 3

    describe "validation" $
        it "accepts the LOTR example without hard errors" $ do
            source <- TIO.readFile "examples/generative/lotr.euclid"
            case parseProgram "examples/generative/lotr.euclid" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            any ((== DiagnosticError) . diagnosticLevel) (validateWorld worldValue)
                                `shouldBe` False

    describe "lsp tooling" $ do
        it "maps diagnostic source spans to concrete LSP ranges" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: nonsense,"
                        , "  start: 1,"
                        , "  end: 2,"
                        , "}"
                        ]
                diagnostics = getDiagnostics "<inline>" source
            case diagnostics of
                [] ->
                    expectationFailure "expected diagnostics for invalid timeline kind"
                diagnostic : _ ->
                    case diagnosticToLsp diagnostic of
                        Aeson.Object diagnosticObj -> do
                            let maybeRangeObj = lookupJsonObject "range" diagnosticObj
                                maybeStartObj = maybeRangeObj >>= lookupJsonObject "start"
                                maybeEndObj = maybeRangeObj >>= lookupJsonObject "end"
                            case (maybeStartObj, maybeEndObj) of
                                (Just startObj, Just endObj) -> do
                                    lookupJsonInt "line" startObj `shouldBe` Just 0
                                    lookupJsonInt "line" endObj `shouldSatisfy` maybe False (> 0)
                                _ ->
                                    expectationFailure "expected concrete LSP range objects"
                        other ->
                            expectationFailure ("expected diagnostic object, got " <> show other)

        it "offers document symbols, fields, and local bindings in completions" $ do
            let source =
                    T.unlines
                        [ "type leader {"
                        , "  nation: string,"
                        , "}"
                        , ""
                        , "timeline main {"
                        , "  start: 1,"
                        , "  end: 10,"
                        , "}"
                        , ""
                        , "entity churchill : leader {"
                        , "  nation: \"United Kingdom\","
                        , "  appears_on: main @ 1..2,"
                        , "}"
                        , ""
                        , "let mut counter = 0;"
                        , ""
                        , "fn summarize(count: int) {"
                        , "  let total = count;"
                        , "  coun"
                        , "}"
                        ]
                globalLabels = map completionLabel (getDocumentCompletions "<inline>" source 0 0)
                scopedLabels =
                    map
                        completionLabel
                        (getDocumentCompletions "<inline>" source 18 (T.length "  coun"))
            globalLabels `shouldSatisfy` elem "leader"
            globalLabels `shouldSatisfy` elem "main"
            globalLabels `shouldSatisfy` elem "churchill"
            globalLabels `shouldSatisfy` elem "appears_on"
            scopedLabels `shouldSatisfy` elem "counter"
            scopedLabels `shouldSatisfy` elem "count"

    describe "timeline and temporal validation" $ do
        it "rejects invalid explicit timeline kinds" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: nonsense,"
                        , "  start: 1,"
                        , "  end: 2,"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            diagnosticMessage diag `shouldSatisfy` T.isInfixOf "invalid timeline kind"
                        Right _ ->
                            expectationFailure "expected invalid timeline kind failure"

        it "flags entity appearances that exceed timeline bounds" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  start: 1,"
                        , "  end: 10,"
                        , "}"
                        , "entity late : event {"
                        , "  appears_on: main @ 11..12,"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            any (T.isInfixOf "outside the bounds of timeline" . diagnosticMessage) (validateWorld worldValue)
                                `shouldBe` True

        it "flags reversed relationship temporal scopes" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  start: 1,"
                        , "  end: 10,"
                        , "}"
                        , "entity a : event {"
                        , "  appears_on: main @ 1..2,"
                        , "}"
                        , "entity b : event {"
                        , "  appears_on: main @ 3..4,"
                        , "}"
                        , "rel a -[\"x\"]-> b @ 9..2;"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            any (T.isInfixOf "relationship temporal scope has start after end" . diagnosticMessage) (validateWorld worldValue)
                                `shouldBe` True

        it "accepts built-in legal relationship labels with valid direction" $ do
            let source =
                    T.unlines
                        [ "timeline case_file {"
                        , "  start: 1,"
                        , "  end: 30,"
                        , "}"
                        , "entity record : evidence {"
                        , "  citation: \"Record A\","
                        , "  source: \"Archive\","
                        , "  appears_on: case_file @ 2..2,"
                        , "}"
                        , "entity claim_a : claim {"
                        , "  appears_on: case_file @ 5..10,"
                        , "}"
                        , "entity fact_a : fact {"
                        , "  appears_on: case_file @ 6..6,"
                        , "}"
                        , "entity witness_a : witness {"
                        , "  appears_on: case_file @ 7..7,"
                        , "}"
                        , "entity old_order : fact {"
                        , "  appears_on: case_file @ 8..8,"
                        , "}"
                        , "entity new_order : fact {"
                        , "  appears_on: case_file @ 12..12,"
                        , "}"
                        , "entity prep_step : fact {"
                        , "  appears_on: case_file @ 14..14,"
                        , "}"
                        , "entity result_step : fact {"
                        , "  appears_on: case_file @ 18..18,"
                        , "}"
                        , "rel record -[\"cites\"]-> claim_a;"
                        , "rel record -[\"cites\"]-> fact_a;"
                        , "rel record -[\"impeaches\"]-> witness_a;"
                        , "rel claim_a -[\"contradicts\"]-> fact_a;"
                        , "rel fact_a -[\"corroborates\"]-> claim_a;"
                        , "rel new_order -[\"supersedes\"]-> old_order;"
                        , "rel prep_step -[\"caused\"]-> result_step;"
                        , "rel prep_step -[\"enabled\"]-> result_step;"
                        , "rel prep_step -[\"preceded\"]-> result_step;"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            any (T.isInfixOf "legal relationship" . diagnosticMessage) (validateWorld worldValue)
                                `shouldBe` False

        it "warns when built-in legal relationship direction is malformed" $ do
            let source =
                    T.unlines
                        [ "timeline case_file {"
                        , "  start: 1,"
                        , "  end: 30,"
                        , "}"
                        , "entity record : evidence {"
                        , "  citation: \"Record A\","
                        , "  source: \"Archive\","
                        , "  appears_on: case_file @ 20..20,"
                        , "}"
                        , "entity claim_a : claim {"
                        , "  appears_on: case_file @ 5..5,"
                        , "}"
                        , "entity witness_a : witness {"
                        , "  appears_on: case_file @ 7..7,"
                        , "}"
                        , "entity late_fact : fact {"
                        , "  appears_on: case_file @ 24..24,"
                        , "}"
                        , "rel claim_a -[\"cites\"]-> record;"
                        , "rel record -[\"impeaches\"]-> claim_a;"
                        , "rel late_fact -[\"preceded\"]-> claim_a;"
                        , "rel claim_a -[\"supersedes\"]-> late_fact;"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            let diagnostics = validateWorld worldValue
                                messages = map diagnosticMessage diagnostics
                            any ((== DiagnosticError) . diagnosticLevel) diagnostics `shouldBe` False
                            any (T.isInfixOf "legal relationship 'cites' expects source type evidence") messages `shouldBe` True
                            any (T.isInfixOf "legal relationship 'cites' expects target type claim or fact") messages `shouldBe` True
                            any (T.isInfixOf "legal relationship 'impeaches' expects target type witness") messages `shouldBe` True
                            any (T.isInfixOf "legal relationship 'preceded' expects source to appear before target") messages `shouldBe` True
                            any (T.isInfixOf "legal relationship 'supersedes' expects source to appear after target") messages `shouldBe` True

    describe "declared entity type validation" $
        it "enforces required fields and declared field value types" $ do
            let source =
                    T.unlines
                        [ "type leader {"
                        , "  nation: string,"
                        , "  rank: string,"
                        , "}"
                        , "timeline main {"
                        , "  start: 1,"
                        , "  end: 10,"
                        , "}"
                        , "entity churchill : leader {"
                        , "  nation: 1,"
                        , "  appears_on: main @ 1..2,"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            let messages = map diagnosticMessage (validateWorld worldValue)
                            any (T.isInfixOf "missing required field rank") messages `shouldBe` True
                            any (T.isInfixOf "field nation does not match declared type string") messages `shouldBe` True

    describe "built-in legal entity type validation" $ do
        it "recognizes legal entity types and accepts their declared fields" $ do
            let source =
                    T.unlines
                        [ "timeline case_file {"
                        , "  start: 1951-01-01,"
                        , "  end: 1955-12-31,"
                        , "}"
                        , ""
                        , "entity archive_opinion : evidence {"
                        , "  citation: \"347 U.S. 483\","
                        , "  source: \"National Archives\","
                        , "  bates: \"NA-001\","
                        , "  admissibility: \"public record\","
                        , "  appears_on: case_file @ 1954-05-17..1954-05-17,"
                        , "}"
                        , ""
                        , "entity thurgood_marshall : witness {"
                        , "  affiliation: \"NAACP Legal Defense Fund\","
                        , "  credibility: 100,"
                        , "  appears_on: case_file @ 1952-12-09..1953-12-08,"
                        , "}"
                        , ""
                        , "entity contested_segregation : claim {"
                        , "  summary: \"segregation denies equal protection\","
                        , "  appears_on: case_file @ 1951-02-01..1954-05-17,"
                        , "}"
                        , ""
                        , "entity decision_date : fact {"
                        , "  summary: \"Brown was decided on 1954-05-17\","
                        , "  appears_on: case_file @ 1954-05-17..1954-05-17,"
                        , "}"
                        , ""
                        , "entity opinion_exhibit : exhibit {"
                        , "  number: \"Ex. 12\","
                        , "  description: \"Supreme Court opinion\","
                        , "  appears_on: case_file @ 1954-05-17..1954-05-17,"
                        , "}"
                        , ""
                        , "entity marshall_deposition : deposition {"
                        , "  deponent: \"Thurgood Marshall\","
                        , "  date: 1953-12-08,"
                        , "  appears_on: case_file @ 1953-12-08..1953-12-08,"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            let diagnostics = validateWorld worldValue
                                messages = map diagnosticMessage diagnostics
                            any ((== DiagnosticError) . diagnosticLevel) diagnostics `shouldBe` False
                            any (T.isInfixOf "uses unknown type") messages `shouldBe` False

        it "enforces required and optional fields on legal entity types" $ do
            let source =
                    T.unlines
                        [ "timeline case_file {"
                        , "  start: 1951-01-01,"
                        , "  end: 1955-12-31,"
                        , "}"
                        , ""
                        , "entity incomplete_evidence : evidence {"
                        , "  source: \"National Archives\","
                        , "  bates: 100,"
                        , "  appears_on: case_file @ 1954-05-17..1954-05-17,"
                        , "}"
                        , ""
                        , "entity weak_witness : witness {"
                        , "  credibility: \"high\","
                        , "  appears_on: case_file @ 1952-12-09..1952-12-09,"
                        , "}"
                        , ""
                        , "entity bad_exhibit : exhibit {"
                        , "  number: 12,"
                        , "  appears_on: case_file @ 1954-05-17..1954-05-17,"
                        , "}"
                        , ""
                        , "entity bad_deposition : deposition {"
                        , "  deponent: \"Witness\","
                        , "  date: \"1953-12-08\","
                        , "  appears_on: case_file @ 1953-12-08..1953-12-08,"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            let messages = map diagnosticMessage (validateWorld worldValue)
                            any (T.isInfixOf "missing required field citation") messages `shouldBe` True
                            any (T.isInfixOf "field bates does not match declared type string") messages `shouldBe` True
                            any (T.isInfixOf "field credibility does not match declared type int") messages `shouldBe` True
                            any (T.isInfixOf "missing required field description") messages `shouldBe` True
                            any (T.isInfixOf "field number does not match declared type string") messages `shouldBe` True
                            any (T.isInfixOf "field date does not match declared type date") messages `shouldBe` True

    describe "csv import" $
        it "creates euclid entity declarations from a CSV schema" $ do
            let csvInput =
                    "name,type,timeline,start,end,age\nfrodo,character,main,2968-09-22,3019-09-29,50\n"
            case importCsvToEuclid csvInput of
                Left diags ->
                    expectationFailure ("csv import failed: " <> show diags)
                Right output ->
                    output `shouldSatisfy` T.isInfixOf "entity frodo"

    describe "csv import enrichment" $
        it "synthesizes timelines and sanitizes identifiers for entity-style CSV inputs" $ do
            let csvInput =
                    T.unlines
                        [ "Name,Type,Timeline,Timeline_Kind,Start,End,Is Active"
                        , "\"Frodo Baggins\",character,\"Shire Story\",branch,2968-09-22,3019-09-29,true"
                        ]
            case importCsvToEuclid csvInput of
                Left diags ->
                    expectationFailure ("csv import failed: " <> show diags)
                Right output -> do
                    output `shouldSatisfy` T.isInfixOf "timeline Shire_Story {"
                    output `shouldSatisfy` T.isInfixOf "kind: branch,"
                    output `shouldSatisfy` T.isInfixOf "entity Frodo_Baggins : character {"
                    output `shouldSatisfy` T.isInfixOf "is_active: true,"

    describe "gedcom import enrichment" $
        it "preserves family relationships as spouse and parent_of edges" $ do
            let gedcomInput =
                    T.unlines
                        [ "0 @I1@ INDI"
                        , "1 NAME John /Doe/"
                        , "1 SEX M"
                        , "0 @I2@ INDI"
                        , "1 NAME Jane /Doe/"
                        , "1 SEX F"
                        , "0 @I3@ INDI"
                        , "1 NAME Sam /Doe/"
                        , "0 @F1@ FAM"
                        , "1 HUSB @I1@"
                        , "1 WIFE @I2@"
                        , "1 CHIL @I3@"
                        ]
            case importGedcomToEuclid gedcomInput of
                Left diags ->
                    expectationFailure ("gedcom import failed: " <> show diags)
                Right output -> do
                    output `shouldSatisfy` T.isInfixOf "entity John_Doe : person {"
                    output `shouldSatisfy` T.isInfixOf "rel John_Doe -[\"spouse\"]-> Jane_Doe;"
                    output `shouldSatisfy` T.isInfixOf "rel John_Doe -[\"parent_of\"]-> Sam_Doe;"
                    output `shouldSatisfy` T.isInfixOf "rel Jane_Doe -[\"parent_of\"]-> Sam_Doe;"

    describe "json-ld import enrichment" $
        it "turns @id references into Euclid relationships" $ do
            let jsonldInput =
                    T.unlines
                        [ "{"
                        , "  \"@graph\": ["
                        , "    {"
                        , "      \"@id\": \"https://example.com/people/alice\","
                        , "      \"@type\": \"person\","
                        , "      \"name\": \"Alice\","
                        , "      \"knows\": { \"@id\": \"https://example.com/people/bob\" }"
                        , "    },"
                        , "    {"
                        , "      \"@id\": \"https://example.com/people/bob\","
                        , "      \"@type\": \"person\","
                        , "      \"name\": \"Bob\""
                        , "    }"
                        , "  ]"
                        , "}"
                        ]
            case importJsonLdToEuclid jsonldInput of
                Left diags ->
                    expectationFailure ("json-ld import failed: " <> show diags)
                Right output -> do
                    output `shouldSatisfy` T.isInfixOf "entity Alice : person {"
                    output `shouldSatisfy` T.isInfixOf "entity Bob : person {"
                    output `shouldSatisfy` T.isInfixOf "rel Alice -[\"knows\"]-> Bob;"

    describe "config loading" $
        it "reads export defaults and theme settings from a TOML-like file" $ do
            let configPath = "/tmp/euclid-config.toml"
                configSource =
                    T.unlines
                        [ "[export]"
                        , "default_width = 2048"
                        , "default_height = 1152"
                        , "default_format = \"pdf\""
                        , ""
                        , "[theme]"
                        , "name = \"light\""
                        , "background = \"#ffffff\""
                        ]
            TIO.writeFile configPath configSource
            configValue <- loadConfig (Just configPath)
            resolvedTheme <- resolveSvgTheme Nothing configValue
            removeFile configPath
            configDefaultWidth configValue `shouldBe` Just 2048
            configDefaultHeight configValue `shouldBe` Just 1152
            configDefaultFormat configValue `shouldBe` Just "pdf"
            configThemeName configValue `shouldBe` Just "light"
            themeBackground resolvedTheme `shouldBe` "#ffffff"

    describe "export format parsing" $ do
        it "accepts svg as the only supported export format" $ do
            parseExportFormat "svg" `shouldBe` Right ExportSvg

        it "rejects unsupported export formats at the parser boundary" $ do
            parseExportFormat "png" `shouldSatisfy` either (T.isInfixOf "supported: svg" . T.pack) (const False)
            parseExportFormat "pdf" `shouldSatisfy` either (T.isInfixOf "supported: svg" . T.pack) (const False)

    describe "import parsing" $
        it "accepts import statements in the current frontend" $ do
            case parseProgram "<inline>" "import \"shared.euclid\";\n" of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program statements) ->
                    statements `shouldBe` [StmtImport "shared.euclid"]

    describe "conditional parsing and evaluation" $ do
        it "parses else-if and else branches into the AST" $ do
            let source =
                    T.unlines
                        [ "if false {"
                        , "  let branch = 0;"
                        , "} else if true {"
                        , "  let branch = 1;"
                        , "} else {"
                        , "  let branch = 2;"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtIf decl]) -> do
                    length (ifElseIfBlocks decl) `shouldBe` 1
                    ifElseBlock decl `shouldSatisfy` (/= Nothing)
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "evaluates the first matching branch in a conditional chain" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2001-01-01,"
                        , "}"
                        , ""
                        , "if false {"
                        , "  entity alpha : event {"
                        , "    appears_on: main @ 2000-01-01..2000-02-01,"
                        , "  }"
                        , "} else if true {"
                        , "  entity beta : event {"
                        , "    appears_on: main @ 2000-03-01..2000-04-01,"
                        , "  }"
                        , "} else {"
                        , "  entity gamma : event {"
                        , "    appears_on: main @ 2000-05-01..2000-06-01,"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            Map.member "alpha" (worldEntities worldValue) `shouldBe` False
                            Map.member "beta" (worldEntities worldValue) `shouldBe` True
                            Map.member "gamma" (worldEntities worldValue) `shouldBe` False

    describe "match parsing and evaluation" $ do
        it "parses literal, binding, and wildcard match arms into the AST" $ do
            let source =
                    T.unlines
                        [ "match status {"
                        , "  \"active\" => { let running = true; },"
                        , "  state => { let seen = state; },"
                        , "  _ => { let running = false; },"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtMatch decl]) ->
                    matchArms decl
                        `shouldBe`
                            [ MatchArm
                                { matchArmPattern = MatchPatternValue (VString "active")
                                , matchArmBody =
                                    [ StmtLet
                                        LetDecl
                                            { letName = "running"
                                            , letMutable = False
                                            , letTypeAnnotation = Nothing
                                            , letValue = ExprValue (VBool True)
                                            }
                                    ]
                                }
                            , MatchArm
                                { matchArmPattern = MatchPatternBind "state"
                                , matchArmBody =
                                    [ StmtLet
                                        LetDecl
                                            { letName = "seen"
                                            , letMutable = False
                                            , letTypeAnnotation = Nothing
                                            , letValue = ExprIdent "state"
                                            }
                                    ]
                                }
                            , MatchArm
                                { matchArmPattern = MatchPatternWildcard
                                , matchArmBody =
                                    [ StmtLet
                                        LetDecl
                                            { letName = "running"
                                            , letMutable = False
                                            , letTypeAnnotation = Nothing
                                            , letValue = ExprValue (VBool False)
                                            }
                                    ]
                                }
                            ]
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "executes the first matching arm and exposes identifier bindings inside that arm" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "let status = \"paused\";"
                        , "match status {"
                        , "  \"active\" => {"
                        , "    entity wrong_branch : event {"
                        , "      appears_on: main @ 2000-01-01..2000-01-02,"
                        , "    }"
                        , "  },"
                        , "  state => {"
                        , "    if state == \"paused\" {"
                        , "      entity bound_branch : event {"
                        , "        appears_on: main @ 2000-02-01..2000-02-02,"
                        , "      }"
                        , "    }"
                        , "  },"
                        , "  _ => {"
                        , "    entity wildcard_branch : event {"
                        , "      appears_on: main @ 2000-03-01..2000-03-02,"
                        , "    }"
                        , "  },"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            Map.member "wrong_branch" (worldEntities worldValue) `shouldBe` False
                            Map.member "bound_branch" (worldEntities worldValue) `shouldBe` True
                            Map.member "wildcard_branch" (worldEntities worldValue) `shouldBe` False

    describe "list and range expression parsing and evaluation" $ do
        it "parses list and range expressions without collapsing appearance ranges" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "entity sample : event {"
                        , "  values: [1, 2, 3],"
                        , "  appears_on: main @ 2000-01-01..2000-02-01,"
                        , "}"
                        , ""
                        , "let days = 1..3;"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtTimeline _, StmtEntity decl, StmtLet letDecl]) -> do
                    Map.lookup "values" (entityDeclFields decl)
                        `shouldBe`
                            Just
                                ( ExprList
                                    [ ExprValue (VInt 1)
                                    , ExprValue (VInt 2)
                                    , ExprValue (VInt 3)
                                    ]
                                )
                    entityDeclAppearances decl
                        `shouldBe`
                            [ AppearanceDecl
                                { appearanceDeclTimeline = "main"
                                , appearanceDeclStart = ExprValue (VDate (fromGregorian 2000 1 1))
                                , appearanceDeclEnd = ExprValue (VDate (fromGregorian 2000 2 1))
                                }
                            ]
                    letValue letDecl `shouldBe` ExprRange (ExprValue (VInt 1)) (ExprValue (VInt 3))
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "evaluates bound list and range expressions as loop iterables" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "let days = 1..3;"
                        , "let labels = [\"one\", \"two\"];"
                        , ""
                        , "for day in days {"
                        , "  if day == 2 {"
                        , "    entity range_hit : event {"
                        , "      appears_on: main @ 2000-04-01..2000-04-02,"
                        , "    }"
                        , "  }"
                        , "}"
                        , ""
                        , "for label in labels {"
                        , "  if label == \"two\" {"
                        , "    entity list_hit : event {"
                        , "      appears_on: main @ 2000-05-01..2000-05-02,"
                        , "    }"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            Map.member "range_hit" (worldEntities worldValue) `shouldBe` True
                            Map.member "list_hit" (worldEntities worldValue) `shouldBe` True

    describe "assignment parsing and evaluation" $ do
        it "parses mutable lets and reassignment statements" $ do
            let source =
                    T.unlines
                        [ "let mut counter = 0;"
                        , "counter = counter + 1;"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtLet decl, StmtAssign name expr]) -> do
                    decl
                        `shouldBe`
                            LetDecl
                                { letName = "counter"
                                , letMutable = True
                                , letTypeAnnotation = Nothing
                                , letValue = ExprValue (VInt 0)
                                }
                    name `shouldBe` "counter"
                    expr
                        `shouldBe`
                            ExprBinary
                                OpAdd
                                (ExprIdent "counter")
                                (ExprValue (VInt 1))
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "rejects assignment to immutable let bindings" $ do
            case parseProgram "<inline>" "let counter = 0;\ncounter = 1;\n" of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            diagnosticMessage diag `shouldSatisfy` T.isInfixOf "immutable variable"
                        Right _ ->
                            expectationFailure "expected immutable assignment failure"

        it "reassigns loop state inside while-blocks so the condition can change" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "let mut counter = 0;"
                        , "while counter < 3 {"
                        , "  counter = counter + 1;"
                        , "  if counter == 2 {"
                        , "    entity assigned_while_hit : event {"
                        , "      appears_on: main @ 2000-09-01..2000-09-02,"
                        , "    }"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            Map.member "assigned_while_hit" (worldEntities worldValue) `shouldBe` True

    describe "typed let parsing and shallow type enforcement" $ do
        it "parses optional type annotations on let bindings" $ do
            let source =
                    T.unlines
                        [ "let count: int = 42;"
                        , "let label: string = \"test\";"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtLet countDecl, StmtLet labelDecl]) -> do
                    letTypeAnnotation countDecl `shouldBe` Just "int"
                    letTypeAnnotation labelDecl `shouldBe` Just "string"
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "accepts matching let, parameter, and return annotations" $ do
            let source =
                    T.unlines
                        [ "fn add(a: int, b: int) -> int {"
                        , "  a + b"
                        , "}"
                        , ""
                        , "let count: int = 42;"
                        , "let sum: int = add(count, 1);"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right _ ->
                            pure ()

        it "rejects obvious let annotation mismatches" $ do
            case parseProgram "<inline>" "let count: int = \"wrong\";\n" of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            diagnosticMessage diag `shouldSatisfy` T.isInfixOf "type mismatch"
                        Right _ ->
                            expectationFailure "expected type mismatch but evaluation succeeded"

    describe "function and field access parsing and evaluation" $ do
        it "parses explicit return statements inside function bodies" $ do
            let source =
                    T.unlines
                        [ "fn add(a: int, b: int) -> int {"
                        , "  return a + b;"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtFunction decl]) ->
                    fnBody decl
                        `shouldBe`
                            [ StmtReturn
                                ( Just
                                    (ExprBinary OpAdd (ExprIdent "a") (ExprIdent "b"))
                                )
                            ]
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "parses function return types, expression bodies, calls, and field access" $ do
            let source =
                    T.unlines
                        [ "fn add(a: int, b: int) -> int {"
                        , "  a + b"
                        , "}"
                        , ""
                        , "let sum = add(1, 2);"
                        , "let age = frodo.age;"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtFunction decl, StmtLet sumDecl, StmtLet ageDecl]) -> do
                    fnReturnType decl `shouldBe` Just "int"
                    fnBody decl
                        `shouldBe`
                            [ StmtExpr
                                ( ExprBinary
                                    OpAdd
                                (ExprIdent "a")
                                (ExprIdent "b")
                                )
                            ]
                    letValue sumDecl
                        `shouldBe`
                            ExprCall
                                (ExprIdent "add")
                                [ExprValue (VInt 1), ExprValue (VInt 2)]
                    letTypeAnnotation sumDecl `shouldBe` Nothing
                    letValue ageDecl
                        `shouldBe`
                            ExprField
                                (ExprIdent "frodo")
                                "age"
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "evaluates function return values and statement-form function calls" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "fn add(a: int, b: int) -> int {"
                        , "  a + b"
                        , "}"
                        , ""
                        , "fn spawn(label: string) {"
                        , "  entity scripted : event {"
                        , "    note: label,"
                        , "    appears_on: main @ 2000-06-01..2000-06-02,"
                        , "  }"
                        , "}"
                        , ""
                        , "let sum = add(1, 2);"
                        , "spawn(\"alpha\");"
                        , ""
                        , "if sum == 3 {"
                        , "  entity return_hit : event {"
                        , "    appears_on: main @ 2000-06-03..2000-06-04,"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            Map.member "return_hit" (worldEntities worldValue) `shouldBe` True
                            case Map.lookup "scripted" (worldEntities worldValue) of
                                Nothing ->
                                    expectationFailure "expected scripted entity from function call"
                                Just entityValue ->
                                    annotationNote (entityAnnotation entityValue) `shouldBe` Just "alpha"

        it "honors explicit early returns inside function control flow" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "fn first_match() -> int {"
                        , "  for value in 1..3 {"
                        , "    return value;"
                        , "  }"
                        , "  return 0;"
                        , "}"
                        , ""
                        , "let picked = first_match();"
                        , "if picked == 1 {"
                        , "  entity explicit_return_hit : event {"
                        , "    appears_on: main @ 2000-07-01..2000-07-02,"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            Map.member "explicit_return_hit" (worldEntities worldValue) `shouldBe` True

        it "resolves entity and timeline field access against world values" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "entity frodo : character {"
                        , "  age: 50,"
                        , "  appears_on: main @ 2000-01-01..2000-12-31,"
                        , "}"
                        , ""
                        , "if frodo.name == \"frodo\" && frodo.type == \"character\" && frodo.age == 50 && main.kind == \"linear\" && main.start == 2000-01-01 {"
                        , "  entity field_access_hit : event {"
                        , "    appears_on: main @ 2000-12-05..2000-12-06,"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            Map.member "field_access_hit" (worldEntities worldValue) `shouldBe` True

    describe "identifier resolution" $
        it "rejects unresolved identifiers instead of coercing them to strings" $ do
            case parseProgram "<inline>" "let value = missing_name;\n" of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            diagnosticMessage diag `shouldSatisfy` T.isInfixOf "unresolved identifier"
                        Right _ ->
                            expectationFailure "expected unresolved identifier failure"

    describe "closure and builtin parsing and evaluation" $ do
        it "parses typed closure expressions and closure-backed calls" $ do
            let source =
                    T.unlines
                        [ "let offset = 1;"
                        , "let add_offset = |x: int| x + offset;"
                        , "let sum = add_offset(2);"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtLet _, StmtLet closureDecl, StmtLet callDecl]) -> do
                    letValue closureDecl
                        `shouldBe`
                            ExprClosure
                                [("x", "int")]
                                ( ExprBinary
                                    OpAdd
                                    (ExprIdent "x")
                                    (ExprIdent "offset")
                                )
                    letValue callDecl
                        `shouldBe`
                            ExprCall
                                (ExprIdent "add_offset")
                                [ExprValue (VInt 2)]
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "evaluates captured closures and core builtins against runtime values" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "entity frodo : character {"
                        , "  appears_on: main @ 2000-01-01..2000-12-31,"
                        , "}"
                        , ""
                        , "let offset = 1;"
                        , "let add_offset = |x: int| x + offset;"
                        , "let names = [\"frodo\", \"sam\", \"merry\"];"
                        , "let sum = add_offset(2);"
                        , ""
                        , "if sum == 3 && len(names) == 3 && before(1, 2) && after(3, 2) && type_of(frodo) == \"character\" {"
                        , "  entity closure_builtin_hit : event {"
                        , "    appears_on: main @ 2000-12-07..2000-12-08,"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            Map.member "closure_builtin_hit" (worldEntities worldValue) `shouldBe` True

    describe "type metadata parsing and inherited field access" $ do
        it "parses optional type fields and @meta entries into the AST" $ do
            let source =
                    T.unlines
                        [ "type leader {"
                        , "  @title: \"Leader\","
                        , "  name: string,"
                        , "  age: int?,"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtType decl]) -> do
                    typeDeclMeta decl `shouldBe` Map.fromList [("title", ExprValue (VString "Leader"))]
                    typeDeclFields decl
                        `shouldBe`
                            [ TypeField
                                { typeFieldName = "name"
                                , typeFieldType = "string"
                                , typeFieldOptional = False
                                }
                            , TypeField
                                { typeFieldName = "age"
                                , typeFieldType = "int"
                                , typeFieldOptional = True
                                }
                            ]
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "inherits type metadata during entity field access fallback" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "type leader {"
                        , "  @banner: \"statecraft\","
                        , "}"
                        , ""
                        , "type prime_minister : leader {"
                        , "  @title: \"Prime Minister\","
                        , "}"
                        , ""
                        , "entity churchill : prime_minister {"
                        , "  appears_on: main @ 2000-01-01..2000-12-31,"
                        , "}"
                        , ""
                        , "if churchill.title == \"Prime Minister\" && churchill.banner == \"statecraft\" {"
                        , "  entity inherited_meta_hit : event {"
                        , "    appears_on: main @ 2000-12-09..2000-12-10,"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            Map.member "inherited_meta_hit" (worldEntities worldValue) `shouldBe` True

    describe "boolean and comparison operator evaluation" $
        it "evaluates precedence-sensitive boolean logic with extended comparison operators" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "if true || false && false {"
                        , "  entity precedence_hit : event {"
                        , "    appears_on: main @ 2000-10-01..2000-10-02,"
                        , "  }"
                        , "}"
                        , ""
                        , "if 2 <= 2 && 3 >= 3 && 4 != 5 {"
                        , "  entity comparison_hit : event {"
                        , "    appears_on: main @ 2000-11-01..2000-11-02,"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            Map.member "precedence_hit" (worldEntities worldValue) `shouldBe` True
                            Map.member "comparison_hit" (worldEntities worldValue) `shouldBe` True

    describe "index expression parsing and evaluation" $ do
        it "parses postfix index expressions against identifiers" $ do
            let source =
                    T.unlines
                        [ "let labels = [\"one\", \"two\"];"
                        , "let second = labels[1];"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtLet _, StmtLet decl]) ->
                    letValue decl
                        `shouldBe`
                            ExprIndex
                                (ExprIdent "labels")
                                (ExprValue (VInt 1))
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "indexes into bound lists and string literals during evaluation" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "let labels = [\"one\", \"two\"];"
                        , "if labels[1] == \"two\" {"
                        , "  entity list_index_hit : event {"
                        , "    appears_on: main @ 2000-12-01..2000-12-02,"
                        , "  }"
                        , "}"
                        , ""
                        , "if \"abc\"[1] == \"b\" {"
                        , "  entity string_index_hit : event {"
                        , "    appears_on: main @ 2000-12-03..2000-12-04,"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            Map.member "list_index_hit" (worldEntities worldValue) `shouldBe` True
                            Map.member "string_index_hit" (worldEntities worldValue) `shouldBe` True

    describe "for-loop parsing and evaluation" $ do
        it "parses list and range iterables for for-loops" $ do
            let source =
                    T.unlines
                        [ "for item in [1, 2, 3] {"
                        , "  let seen = item;"
                        , "}"
                        , ""
                        , "for day in 1..3 {"
                        , "  let seen = day;"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtFor listLoop, StmtFor rangeLoop]) -> do
                    forIterable listLoop `shouldBe` ForList [ExprValue (VInt 1), ExprValue (VInt 2), ExprValue (VInt 3)]
                    forIterable rangeLoop `shouldBe` ForRange (ExprValue (VInt 1)) (ExprValue (VInt 3))
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "iterates integer ranges and exposes the loop variable to the body" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "for i in 1..3 {"
                        , "  if i == 2 {"
                        , "    entity middle : event {"
                        , "      appears_on: main @ 2000-02-01..2000-02-02,"
                        , "    }"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            Map.member "middle" (worldEntities worldValue) `shouldBe` True

    describe "repeat-loop parsing and evaluation" $ do
        it "parses repeat-loops into the AST" $ do
            case parseProgram "<inline>" "repeat 3 { let seen = 1; }\n" of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtRepeat decl]) ->
                    repeatCount decl `shouldBe` ExprValue (VInt 3)
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "replays the repeat body the requested number of times" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "let target = 2;"
                        , "for i in 1..3 {"
                        , "  repeat 1 {"
                        , "    if i == target {"
                        , "      entity repeated_hit : event {"
                        , "        appears_on: main @ 2000-07-01..2000-07-02,"
                        , "      }"
                        , "    }"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            Map.member "repeated_hit" (worldEntities worldValue) `shouldBe` True

    describe "while-loop parsing and evaluation" $ do
        it "parses while-loops into the AST" $ do
            case parseProgram "<inline>" "while true { let seen = 1; }\n" of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right (Program [StmtWhile decl]) ->
                    whileCondition decl `shouldBe` ExprValue (VBool True)
                Right other ->
                    expectationFailure ("unexpected parse result: " <> show other)

        it "re-evaluates the condition until the while-loop becomes false" $ do
            let source =
                    T.unlines
                        [ "timeline main {"
                        , "  kind: linear,"
                        , "  start: 2000-01-01,"
                        , "  end: 2000-12-31,"
                        , "}"
                        , ""
                        , "let counter = 0;"
                        , "while counter < 3 {"
                        , "  let counter = counter + 1;"
                        , "  if counter == 2 {"
                        , "    entity while_hit : event {"
                        , "      appears_on: main @ 2000-08-01..2000-08-02,"
                        , "    }"
                        , "  }"
                        , "}"
                        ]
            case parseProgram "<inline>" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue ->
                            Map.member "while_hit" (worldEntities worldValue) `shouldBe` True

    describe "diffing" $ do
        it "reports entity deltas between worlds" $ do
            source <- TIO.readFile "examples/generative/lotr.euclid"
            case parseProgram "examples/generative/lotr.euclid" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            let smallerWorld = worldValue{worldEntities = Map.delete "ring" (worldEntities worldValue)}
                                diffText = diffWorlds smallerWorld worldValue
                            diffText `shouldSatisfy` T.isInfixOf "ring"

        it "reports changed entity details when shared names diverge" $ do
            source <- TIO.readFile "examples/generative/lotr.euclid"
            case parseProgram "examples/generative/lotr.euclid" source of
                Left diags ->
                    expectationFailure ("parse failed: " <> show diags)
                Right program ->
                    case evalProgram program of
                        Left diag ->
                            expectationFailure ("eval failed: " <> show diag)
                        Right worldValue -> do
                            let updatedRing =
                                    fmap (\entity -> entity{entityType = "object"}) (Map.lookup "ring" (worldEntities worldValue))
                                changedWorld =
                                    case updatedRing of
                                        Nothing -> worldValue
                                        Just ringEntity ->
                                            worldValue{worldEntities = Map.insert "ring" ringEntity (worldEntities worldValue)}
                                diffText = diffWorlds worldValue changedWorld
                            diffText `shouldSatisfy` T.isInfixOf "~ changed ring"
