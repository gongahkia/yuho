{-# LANGUAGE OverloadedStrings #-}

module Euclid.Lang.Parser
    ( parseProgram
    , parseStatement
    ) where

import Data.Char (isAlphaNum)
import qualified Data.Set as Set
import Data.Functor (($>))
import qualified Data.List.NonEmpty as NE
import qualified Data.Map.Strict as Map
import Data.Maybe (isJust)
import Data.Text (Text)
import qualified Data.Text as T
import Data.Time (Day, defaultTimeLocale, parseTimeM)
import Data.Void (Void)
import Control.Monad.Combinators.Expr (Operator(..), makeExprParser)
import Euclid.Lang.AST
import Euclid.Model.Types
import Text.Megaparsec
import Text.Megaparsec.Char
import qualified Text.Megaparsec.Char.Lexer as L

type Parser = Parsec Void Text

parseProgram :: FilePath -> Text -> Either [Diagnostic] Program
parseProgram file input =
    case runParser (between sc eof (ProgramData file <$> many statementParser)) file input of
        Left bundle -> Left [parserDiagnostic bundle]
        Right program -> Right program

parseStatement :: FilePath -> Text -> Either [Diagnostic] Stmt
parseStatement file input =
    case runParser (between sc eof statementParser) file input of
        Left bundle -> Left [parserDiagnostic bundle]
        Right statement -> Right statement

statementParser :: Parser Stmt
statementParser =
    choice
        [ withStatementSpan (StmtTypeNode <$> typeDeclParser)
        , withStatementSpan (StmtSourceBundleNode <$> sourceBundleDeclParser)
        , withStatementSpan (StmtSourceLocatorNode <$> sourceLocatorDeclParser)
        , withStatementSpan (StmtRulesetNode <$> rulesetDeclParser)
        , withStatementSpan (StmtDeadlineRuleNode <$> deadlineRuleDeclParser)
        , withStatementSpan (StmtIssueNode <$> legalIssueDeclParser)
        , withStatementSpan (StmtIssueElementNode <$> issueElementDeclParser)
        , withStatementSpan (StmtSourceNode <$> sourceDeclParser)
        , withStatementSpan (StmtTimelineNode <$> timelineDeclParser)
        , withStatementSpan (StmtEntityNode <$> entityDeclParser)
        , withStatementSpan (StmtRelationshipTypeNode <$> relationshipTypeDeclParser)
        , withStatementSpan (StmtExprNode <$> try quantifierExprStmtParser)
        , withStatementSpan (StmtRelationshipNode <$> relationshipDeclParser)
        , withStatementSpan (StmtConstraintNode <$> constraintDeclParser)
        , withStatementSpan (StmtViewNode <$> viewDeclParser)
        , withStatementSpan (StmtScenarioNode <$> scenarioDeclParser)
        , withStatementSpan (StmtImportNode <$> importStmtParser)
        , withStatementSpan (StmtLetNode <$> letDeclParser)
        , withStatementSpan (StmtForNode <$> forDeclParser)
        , withStatementSpan (StmtRepeatNode <$> repeatDeclParser)
        , withStatementSpan (StmtWhileNode <$> whileDeclParser)
        , withStatementSpan (StmtFunctionNode <$> fnDeclParser)
        , withStatementSpan (StmtIfNode <$> ifDeclParser)
        , withStatementSpan (StmtMatchNode <$> matchDeclParser)
        , withStatementSpan (StmtReturnNode <$> returnStmtParser)
        , withStatementSpan (uncurry StmtAssignNode <$> try assignStmtParser)
        , withStatementSpan (StmtExprNode <$> exprStmtParser)
        ]

withStatementSpan :: Parser StmtNode -> Parser Stmt
withStatementSpan parser = do
    start <- getSourcePos
    stmtNodeValue <- parser
    end <- getSourcePos
    pure (StmtData (sourceSpanFromPositions start end) stmtNodeValue)

parserDiagnostic :: ParseErrorBundle Text Void -> Diagnostic
parserDiagnostic bundle =
    Diagnostic
        { diagnosticLevel = DiagnosticError
        , diagnosticSource = "parser"
        , diagnosticMessage = T.pack (errorBundlePretty bundle)
        , diagnosticSpan = Just (bundleSourceSpan bundle)
        }

bundleSourceSpan :: ParseErrorBundle Text Void -> SourceSpan
bundleSourceSpan bundle =
    sourceSpanFromPositions sourcePos sourcePos
  where
    offset = errorOffset (NE.head (bundleErrors bundle))
    (_, posState) = reachOffset offset (bundlePosState bundle)
    sourcePos = pstateSourcePos posState

sourceSpanFromPositions :: SourcePos -> SourcePos -> SourceSpan
sourceSpanFromPositions start end =
    SourceSpan
        { spanFile = sourceName start
        , spanStartLine = unPos (sourceLine start)
        , spanStartColumn = unPos (sourceColumn start)
        , spanEndLine = unPos (sourceLine end)
        , spanEndColumn = max (unPos (sourceColumn end)) (unPos (sourceColumn start) + 1)
        }

sc :: Parser ()
sc =
    L.space
        space1
        (L.skipLineComment "//")
        (L.skipBlockComment "/*" "*/")

lexeme :: Parser a -> Parser a
lexeme = L.lexeme sc

symbol :: Text -> Parser Text
symbol = L.symbol sc

keyword :: Text -> Parser Text
keyword word =
    lexeme (string word <* notFollowedBy identifierTailChar)
  where
    identifierTailChar = satisfy (\c -> isAlphaNum c || c == '_')

identifier :: Parser Text
identifier = lexeme $ do
    first <- letterChar <|> char '_'
    rest <- many (satisfy (\c -> isAlphaNum c || c == '_'))
    pure (T.pack (first : rest))

stringLiteral :: Parser Text
stringLiteral = T.pack <$> lexeme (char '"' *> manyTill L.charLiteral (char '"'))

dateLiteral :: Parser Day
dateLiteral = lexeme $ do
    textValue <- try $ do
        year <- count 4 digitChar
        _ <- char '-'
        month <- count 2 digitChar
        _ <- char '-'
        day <- count 2 digitChar
        pure (year <> "-" <> month <> "-" <> day)
    case parseTimeM True defaultTimeLocale "%F" textValue of
        Just parsedDay -> pure parsedDay
        Nothing -> fail ("invalid date literal: " <> textValue)

integerLiteral :: Parser Integer
integerLiteral = lexeme (L.signed sc L.decimal)

boolLiteral :: Parser Bool
boolLiteral =
    (symbol "true" $> True)
        <|> (symbol "false" $> False)

exprParser :: Parser Expr
exprParser = rangeExprParser

rangeExprParser :: Parser Expr
rangeExprParser = do
    startExpr <- nonRangeExprParser
    maybeEndExpr <- optional (try (symbol ".." *> rangeExprParser))
    pure $
        case maybeEndExpr of
            Nothing -> startExpr
            Just endExpr -> ExprRange startExpr endExpr

nonRangeExprParser :: Parser Expr
nonRangeExprParser = makeExprParser term operatorTable

term :: Parser Expr
term = do
    baseExpr <- primaryTerm
    suffixes <- many postfixSuffixParser
    pure (foldl applyPostfixSuffix baseExpr suffixes)

primaryTerm :: Parser Expr
primaryTerm =
    choice
        [ try closureExprParser
        , try quantifierExprParser
        , ExprValue <$> literalValueParser
        , ExprList <$> between (symbol "[") (symbol "]") (exprParser `sepBy` symbol ",")
        , ExprIdent <$> identifier
        , between (symbol "(") (symbol ")") exprParser
        ]

quantifierExprParser :: Parser Expr
quantifierExprParser = do
    quantifierValue <-
        (keyword "forall" $> QuantifierForAll)
            <|> (keyword "exists" $> QuantifierExists)
    variableName <- identifier
    _ <- symbol "in"
    iterable <- exprParser
    body <- braces exprParser
    pure (ExprQuantifier quantifierValue variableName iterable body)

closureExprParser :: Parser Expr
closureExprParser = do
    _ <- symbol "|"
    params <- paramParser `sepBy` symbol ","
    _ <- symbol "|"
    bodyExpr <- exprParser
    pure (ExprClosure params bodyExpr)

indexSuffixParser :: Parser Expr
indexSuffixParser =
    between (symbol "[") (symbol "]") exprParser

data PostfixSuffix
    = PostfixIndex Expr
    | PostfixField Text
    | PostfixCall [Expr]
    | PostfixTemporalField Text Expr -- .field @ time

postfixSuffixParser :: Parser PostfixSuffix
postfixSuffixParser =
    choice
        [ PostfixIndex <$> indexSuffixParser
        , try temporalFieldSuffixParser
        , PostfixField <$> fieldSuffixParser
        , PostfixCall <$> callSuffixParser
        ]

temporalFieldSuffixParser :: Parser PostfixSuffix
temporalFieldSuffixParser = do
    _ <- symbol "."
    field <- identifier
    _ <- symbol "@"
    timeExpr <- nonRangeExprParser
    pure (PostfixTemporalField field timeExpr)

fieldSuffixParser :: Parser Text
fieldSuffixParser = try $ do
    _ <- symbol "."
    identifier

callSuffixParser :: Parser [Expr]
callSuffixParser =
    between (symbol "(") (symbol ")") (exprParser `sepBy` symbol ",")

applyPostfixSuffix :: Expr -> PostfixSuffix -> Expr
applyPostfixSuffix expr suffix =
    case suffix of
        PostfixIndex indexExpr -> ExprIndex expr indexExpr
        PostfixField fieldName -> ExprField expr fieldName
        PostfixCall args -> ExprCall expr args
        PostfixTemporalField fieldName timeExpr -> ExprTemporalAccess expr fieldName timeExpr

durationLiteral :: Parser Value
durationLiteral = lexeme $ try $ do
    components <- some durationComponent
    let (y, m, d) = foldl (\(ay, am, ad) (vy, vm, vd) -> (ay+vy, am+vm, ad+vd)) (0,0,0) components
    pure (VDuration y m d)

durationComponent :: Parser (Integer, Integer, Integer)
durationComponent = do
    n <- L.decimal
    sc
    unit <- choice
        [ (n, 0, 0) <$ (symbol "years" <|> symbol "year")
        , (0, n, 0) <$ (symbol "months" <|> symbol "month")
        , (0, 0, n) <$ (symbol "days" <|> symbol "day")
        ]
    pure unit

literalValueParser :: Parser Value
literalValueParser =
    choice
        [ VDate <$> dateLiteral
        , try durationLiteral
        , VBool <$> boolLiteral
        , VInt <$> try integerLiteral
        , VString <$> stringLiteral
        ]

operatorTable :: [[Operator Parser Expr]]
operatorTable =
    [ [prefix "-" (ExprUnary OpNeg), prefix "!" (ExprUnary OpNot)]
    , [binary "*" (ExprBinary OpMul), binary "/" (ExprBinary OpDiv), binary "%" (ExprBinary OpMod)]
    , [binary "+" (ExprBinary OpAdd), binary "-" (ExprBinary OpSub), binary "++" (ExprBinary OpConcat)]
    , [ binary ">=" (ExprBinary OpGte)
      , binary "<=" (ExprBinary OpLte)
      , binary ">" (ExprBinary OpGt)
      , binary "<" (ExprBinary OpLt)
      , binary "==" (ExprBinary OpEq)
      , binary "!=" (ExprBinary OpNeq)
      ]
    , [binary "&&" (ExprBinary OpAnd)]
    , [binary "||" (ExprBinary OpOr)]
    ]

binary :: Text -> (Expr -> Expr -> Expr) -> Operator Parser Expr
binary name f = InfixL (f <$ symbol name)

prefix :: Text -> (Expr -> Expr) -> Operator Parser Expr
prefix name f = Prefix (f <$ symbol name)

typeDeclParser :: Parser TypeDecl
typeDeclParser = do
    _ <- symbol "type"
    name <- identifier
    parent <- optional (symbol ":" *> identifier)
    entries <- braces (many typeDeclEntryParser)
    let fields =
            [ field
            | TypeDeclField field <- entries
            ]
        metaFields =
            Map.fromList
                [ (metaName, metaValue)
                | TypeDeclMeta metaName metaValue <- entries
                ]
    pure
        TypeDecl
            { typeDeclName = name
            , typeDeclParent = parent
            , typeDeclFields = fields
            , typeDeclMeta = metaFields
            }

data TypeDeclEntry
    = TypeDeclField TypeField
    | TypeDeclMeta Text Expr

typeDeclEntryParser :: Parser TypeDeclEntry
typeDeclEntryParser =
    try typeMetaParser <|> typeFieldParser

typeFieldParser :: Parser TypeDeclEntry
typeFieldParser = do
    fieldName <- identifier
    _ <- symbol ":"
    fieldType <- identifier
    optionalFlag <- isJust <$> optional (symbol "?")
    _ <- optional (symbol ",")
    pure $
        TypeDeclField
            TypeField
                { typeFieldName = fieldName
                , typeFieldType = fieldType
                , typeFieldOptional = optionalFlag
                }

typeMetaParser :: Parser TypeDeclEntry
typeMetaParser = do
    _ <- symbol "@"
    metaName <- identifier
    _ <- symbol ":"
    metaValue <- exprParser
    _ <- optional (symbol ",")
    pure (TypeDeclMeta metaName metaValue)

timelineDeclParser :: Parser TimelineDecl
timelineDeclParser = do
    _ <- symbol "timeline"
    name <- identifier
    fields <- braces (many timelineFieldParser)
    let kindValue = extractField "kind" fields
        startValue = maybe (ExprValue (VInt 0)) id (extractField "start" fields)
        endValue = maybe (ExprValue (VInt 100)) id (extractField "end" fields)
        parentValue = extractField "parent" fields >>= asIdentifier
        jurisdictionValue = extractField "jurisdiction" fields
        courtValue = extractField "court" fields
        procedureValue = extractField "procedure" fields
        forkValue = extractField "fork_from" fields >>= asTimelineRef
        mergeValue = extractField "merge_into" fields >>= asTimelineRef
        loopValue = extractField "loop_count" fields
    pure
        TimelineDecl
            { timelineDeclName = name
            , timelineDeclKind = kindValue
            , timelineDeclStart = startValue
            , timelineDeclEnd = endValue
            , timelineDeclParent = parentValue
            , timelineDeclJurisdiction = jurisdictionValue
            , timelineDeclCourt = courtValue
            , timelineDeclProcedure = procedureValue
            , timelineDeclForkFrom = forkValue
            , timelineDeclMergeInto = mergeValue
            , timelineDeclLoopCount = loopValue
            }

sourceDeclParser :: Parser SourceDecl
sourceDeclParser = do
    _ <- keyword "source"
    name <- identifier
    kindValue <- optional (symbol ":" *> identifier)
    entries <- braces (many sourceFieldParser)
    pure
        SourceDecl
            { sourceDeclName = name
            , sourceDeclKind = maybe "source" id kindValue
            , sourceDeclFields = Map.fromList entries
            }

sourceFieldParser :: Parser (Text, Expr)
sourceFieldParser = do
    fieldName <- identifier
    _ <- symbol ":"
    value <- exprParser
    _ <- optional (symbol ",")
    pure (fieldName, value)

genericDeclFieldParser :: Parser (Text, Expr)
genericDeclFieldParser = sourceFieldParser

sourceBundleDeclParser :: Parser SourceBundleDecl
sourceBundleDeclParser = do
    _ <- keyword "source_bundle"
    name <- identifier
    entries <- braces (many sourceBundleFieldParser)
    pure
        SourceBundleDecl
            { sourceBundleDeclName = name
            , sourceBundleDeclSources =
                concat
                    [ sourceNames
                    | SourceBundleSources sourceNames <- entries
                    ]
            , sourceBundleDeclFields =
                Map.fromList
                    [ (fieldName, value)
                    | SourceBundleField fieldName value <- entries
                    ]
            }

data SourceBundleEntry
    = SourceBundleSources [Text]
    | SourceBundleField Text Expr

sourceBundleFieldParser :: Parser SourceBundleEntry
sourceBundleFieldParser =
    try sourceBundleSourcesParser <|> sourceBundleGenericFieldParser

sourceBundleSourcesParser :: Parser SourceBundleEntry
sourceBundleSourcesParser = do
    _ <- symbol "sources"
    _ <- symbol ":"
    sourceNames <- between (symbol "[") (symbol "]") (identifier `sepBy` symbol ",")
    _ <- optional (symbol ",")
    pure (SourceBundleSources sourceNames)

sourceBundleGenericFieldParser :: Parser SourceBundleEntry
sourceBundleGenericFieldParser = do
    fieldName <- identifier
    _ <- symbol ":"
    value <- exprParser
    _ <- optional (symbol ",")
    pure (SourceBundleField fieldName value)

sourceLocatorDeclParser :: Parser SourceLocatorDecl
sourceLocatorDeclParser = do
    _ <- keyword "locator"
    name <- identifier
    fields <- braces (many genericDeclFieldParser)
    pure
        SourceLocatorDecl
            { sourceLocatorDeclName = name
            , sourceLocatorDeclFields = Map.fromList fields
            }

rulesetDeclParser :: Parser RulesetDecl
rulesetDeclParser = do
    _ <- keyword "ruleset"
    name <- identifier
    fields <- braces (many genericDeclFieldParser)
    pure
        RulesetDecl
            { rulesetDeclName = name
            , rulesetDeclFields = Map.fromList fields
            }

deadlineRuleDeclParser :: Parser DeadlineRuleDecl
deadlineRuleDeclParser = do
    _ <- keyword "deadline_rule"
    name <- identifier
    fields <- braces (many genericDeclFieldParser)
    pure
        DeadlineRuleDecl
            { deadlineRuleDeclName = name
            , deadlineRuleDeclFields = Map.fromList fields
            }

legalIssueDeclParser :: Parser LegalIssueDecl
legalIssueDeclParser = do
    _ <- keyword "issue"
    name <- identifier
    fields <- braces (many genericDeclFieldParser)
    pure
        LegalIssueDecl
            { legalIssueDeclName = name
            , legalIssueDeclFields = Map.fromList fields
            }

issueElementDeclParser :: Parser IssueElementDecl
issueElementDeclParser = do
    _ <- keyword "element"
    name <- identifier
    fields <- braces (many genericDeclFieldParser)
    pure
        IssueElementDecl
            { issueElementDeclName = name
            , issueElementDeclFields = Map.fromList fields
            }

entityDeclParser :: Parser EntityDecl
entityDeclParser = do
    _ <- symbol "entity"
    name <- identifier
    entityTypeName <- optional (symbol ":" *> identifier)
    fields <- braces (many entityFieldParser)
    let allFields = [(fieldName, expr) | EntityField fieldName expr <- fields]
        reservedFieldNames = Set.fromList ["note", "source", "confidence", "tags", "recurrence", "skip"]
        customFields = Map.fromList [(n, e) | (n, e) <- allFields, Set.notMember n reservedFieldNames]
        annotFields = Map.fromList [(n, e) | (n, e) <- allFields, Set.member n (Set.fromList ["note", "source", "confidence", "tags"])]
        appearances = [appearance | AppearanceField appearance <- fields]
        stateChanges = [stateChange | StateChangeField stateChange <- fields]
        annot = AnnotationDecl
            { annotationDeclNote = Map.lookup "note" annotFields
            , annotationDeclSource = Map.lookup "source" annotFields
            , annotationDeclConfidence = Map.lookup "confidence" annotFields
            , annotationDeclTags = case Map.lookup "tags" annotFields of
                Just (ExprList ts) -> ts
                _ -> []
            }
    pure
        EntityDecl
            { entityDeclName = name
            , entityDeclType = entityTypeName
            , entityDeclFields = customFields
            , entityDeclAppearances = appearances
            , entityDeclStateChanges = stateChanges
            , entityDeclAnnotation = annot
            , entityDeclRecurrence = lookup "recurrence" allFields
            , entityDeclSkip = case lookup "skip" allFields of
                Just (ExprList es) -> es
                _ -> []
            }

relationshipDeclParser :: Parser RelationshipDecl
relationshipDeclParser = try causalRelParser <|> standardRelParser

relationshipTypeDeclParser :: Parser RelationshipTypeDecl
relationshipTypeDeclParser = do
    _ <- symbol "reltype"
    name <- identifier <|> stringLiteral
    entries <- braces (many relationshipTypeEntryParser)
    pure
        RelationshipTypeDecl
            { relationshipTypeDeclName = name
            , relationshipTypeDeclSources = concat [types | RelationshipTypeSources types <- entries]
            , relationshipTypeDeclTargets = concat [types | RelationshipTypeTargets types <- entries]
            , relationshipTypeDeclTemporalRule = firstJust [rule | RelationshipTypeTemporal rule <- entries]
            , relationshipTypeDeclRequired = or [value | RelationshipTypeRequired value <- entries]
            , relationshipTypeDeclMinInbound = firstJust [value | RelationshipTypeMinInbound value <- entries]
            , relationshipTypeDeclMaxInbound = firstJust [value | RelationshipTypeMaxInbound value <- entries]
            , relationshipTypeDeclMinOutbound = firstJust [value | RelationshipTypeMinOutbound value <- entries]
            , relationshipTypeDeclMaxOutbound = firstJust [value | RelationshipTypeMaxOutbound value <- entries]
            }

data RelationshipTypeEntry
    = RelationshipTypeSources [Text]
    | RelationshipTypeTargets [Text]
    | RelationshipTypeTemporal (Maybe RelationshipTemporalRule)
    | RelationshipTypeRequired Bool
    | RelationshipTypeMinInbound (Maybe Expr)
    | RelationshipTypeMaxInbound (Maybe Expr)
    | RelationshipTypeMinOutbound (Maybe Expr)
    | RelationshipTypeMaxOutbound (Maybe Expr)

relationshipTypeEntryParser :: Parser RelationshipTypeEntry
relationshipTypeEntryParser =
    choice
        [ try $ do
            _ <- symbol "source"
            _ <- symbol ":"
            types <- relationshipTypeListParser
            _ <- optional (symbol ",")
            pure (RelationshipTypeSources types)
        , try $ do
            _ <- symbol "target"
            _ <- symbol ":"
            types <- relationshipTypeListParser
            _ <- optional (symbol ",")
            pure (RelationshipTypeTargets types)
        , try $ do
            _ <- symbol "temporal"
            _ <- symbol ":"
            rule <- relationshipTemporalRuleParser
            _ <- optional (symbol ",")
            pure (RelationshipTypeTemporal rule)
        , try $ do
            _ <- symbol "required"
            _ <- symbol ":"
            requiredValue <- boolLiteral
            _ <- optional (symbol ",")
            pure (RelationshipTypeRequired requiredValue)
        , try $ do
            _ <- symbol "min_inbound"
            _ <- symbol ":"
            value <- exprParser
            _ <- optional (symbol ",")
            pure (RelationshipTypeMinInbound (Just value))
        , try $ do
            _ <- symbol "max_inbound"
            _ <- symbol ":"
            value <- exprParser
            _ <- optional (symbol ",")
            pure (RelationshipTypeMaxInbound (Just value))
        , try $ do
            _ <- symbol "min_outbound"
            _ <- symbol ":"
            value <- exprParser
            _ <- optional (symbol ",")
            pure (RelationshipTypeMinOutbound (Just value))
        , try $ do
            _ <- symbol "max_outbound"
            _ <- symbol ":"
            value <- exprParser
            _ <- optional (symbol ",")
            pure (RelationshipTypeMaxOutbound (Just value))
        ]

relationshipTypeListParser :: Parser [Text]
relationshipTypeListParser =
    identifier `sepBy1` symbol "|"

relationshipTemporalRuleParser :: Parser (Maybe RelationshipTemporalRule)
relationshipTemporalRuleParser = do
    ruleName <- identifier
    case ruleName of
        "source_before_target" -> pure (Just SourceBeforeTarget)
        "before" -> pure (Just SourceBeforeTarget)
        "source_after_target" -> pure (Just SourceAfterTarget)
        "after" -> pure (Just SourceAfterTarget)
        "none" -> pure Nothing
        _ -> fail ("invalid relationship temporal rule: " <> T.unpack ruleName)

firstJust :: [Maybe a] -> Maybe a
firstJust [] = Nothing
firstJust (Nothing : rest) = firstJust rest
firstJust (Just value : _) = Just value

standardRelParser :: Parser RelationshipDecl
standardRelParser = do
    _ <- symbol "rel"
    source <- identifier
    (labelValue, directedValue) <-
        try labeledArrow <|> unlabeledArrow
    target <- identifier
    temporalScope <- optional $ do
        _ <- symbol "@"
        startValue <- nonRangeExprParser
        _ <- symbol ".."
        endValue <- exprParser
        pure (startValue, endValue)
    _ <- symbol ";"
    pure
        RelationshipDecl
            { relationshipDeclSource = source
            , relationshipDeclLabel = labelValue
            , relationshipDeclTarget = target
            , relationshipDeclDirected = directedValue
            , relationshipDeclCausalKind = CausalDeclNone
            , relationshipDeclTemporalScope = temporalScope
            }

causalRelParser :: Parser RelationshipDecl
causalRelParser = do
    source <- identifier
    (causalKind, relationshipLabel) <- choice
        [ (CausalDeclCauses, "causes") <$ symbol "causes"
        , (CausalDeclEnables, "enables") <$ symbol "enables"
        ]
    target <- identifier
    _ <- symbol ";"
    pure RelationshipDecl
        { relationshipDeclSource = source
        , relationshipDeclLabel = Just relationshipLabel
        , relationshipDeclTarget = target
        , relationshipDeclDirected = True
        , relationshipDeclCausalKind = causalKind
        , relationshipDeclTemporalScope = Nothing
        }

viewDeclParser :: Parser ViewDecl
viewDeclParser = do
    _ <- symbol "view"
    name <- stringLiteral
    entries <- braces (many viewEntryParser)
    pure ViewDecl
        { viewDeclName = name
        , viewDeclTimelines = [t | ViewTimelines ts <- entries, t <- ts]
        , viewDeclFilter = case [f | ViewFilter f <- entries] of {(f:_) -> Just f; _ -> Nothing}
        , viewDeclTimeRange = case [r | ViewTimeRange r <- entries] of {(r:_) -> Just r; _ -> Nothing}
        , viewDeclHighlight = [h | ViewHighlight hs <- entries, h <- hs]
        }

data ViewEntry = ViewTimelines [Text] | ViewFilter Text | ViewTimeRange (Expr, Expr) | ViewHighlight [Text]

viewEntryParser :: Parser ViewEntry
viewEntryParser = choice
    [ try $ do { _ <- symbol "timelines"; _ <- symbol ":"; ts <- between (symbol "[") (symbol "]") (identifier `sepBy` symbol ","); _ <- optional (symbol ","); pure (ViewTimelines ts) }
    , try $ do { _ <- symbol "filter"; _ <- symbol ":"; t <- identifier; _ <- optional (symbol ","); pure (ViewFilter t) }
    , try $ do { _ <- symbol "time_range"; _ <- symbol ":"; s <- nonRangeExprParser; _ <- symbol ".."; e <- exprParser; _ <- optional (symbol ","); pure (ViewTimeRange (s, e)) }
    , try $ do { _ <- symbol "highlight"; _ <- symbol ":"; hs <- between (symbol "[") (symbol "]") (identifier `sepBy` symbol ","); _ <- optional (symbol ","); pure (ViewHighlight hs) }
    ]

scenarioDeclParser :: Parser ScenarioDecl
scenarioDeclParser = do
    _ <- symbol "scenario"
    name <- stringLiteral
    forkFrom <- optional (symbol "from" *> identifier)
    body <- braces (many statementParser)
    pure ScenarioDecl
        { scenarioDeclName = name
        , scenarioDeclForkFrom = forkFrom
        , scenarioDeclBody = body
        }

constraintDeclParser :: Parser ConstraintDecl
constraintDeclParser = do
    _ <- symbol "constraint"
    name <- stringLiteral
    body <- braces (many statementParser)
    pure ConstraintDecl
        { constraintDeclName = name
        , constraintDeclBody = body
        }

importStmtParser :: Parser Text
importStmtParser = do
    _ <- symbol "import"
    pathValue <- stringLiteral
    _ <- symbol ";"
    pure pathValue

letDeclParser :: Parser LetDecl
letDeclParser = do
    _ <- symbol "let"
    isMutable <- isJust <$> optional (symbol "mut")
    name <- identifier
    typeAnnotation <- optional (symbol ":" *> identifier)
    _ <- symbol "="
    value <- exprParser
    _ <- optional (symbol ";")
    pure
        LetDecl
            { letName = name
            , letMutable = isMutable
            , letTypeAnnotation = typeAnnotation
            , letValue = value
            }

assignStmtParser :: Parser (Text, Expr)
assignStmtParser = do
    name <- identifier
    _ <- symbol "="
    value <- exprParser
    _ <- optional (symbol ";")
    pure (name, value)

exprStmtParser :: Parser Expr
exprStmtParser = do
    value <- exprParser
    _ <- optional (symbol ";")
    pure value

quantifierExprStmtParser :: Parser Expr
quantifierExprStmtParser = do
    value <- quantifierExprParser
    _ <- optional (symbol ";")
    pure value

forDeclParser :: Parser ForDecl
forDeclParser = do
    _ <- keyword "for"
    loopVar <- identifier
    _ <- symbol "in"
    iterable <- forIterableParser
    body <- braces (many statementParser)
    pure
        ForDecl
            { forVar = loopVar
            , forIterable = iterable
            , forBody = body
            }

forIterableParser :: Parser ForIterable
forIterableParser =
    try forRangeParser <|> try forListParser <|> (ForExpr <$> exprParser)

forRangeParser :: Parser ForIterable
forRangeParser = do
    startExpr <- nonRangeExprParser
    _ <- symbol ".."
    endExpr <- exprParser
    pure (ForRange startExpr endExpr)

forListParser :: Parser ForIterable
forListParser =
    ForList <$> between (symbol "[") (symbol "]") (exprParser `sepBy` symbol ",")

repeatDeclParser :: Parser RepeatDecl
repeatDeclParser = do
    _ <- symbol "repeat"
    countExpr <- exprParser
    body <- braces (many statementParser)
    pure
        RepeatDecl
            { repeatCount = countExpr
            , repeatBody = body
            }

whileDeclParser :: Parser WhileDecl
whileDeclParser = do
    _ <- symbol "while"
    conditionExpr <- exprParser
    body <- braces (many statementParser)
    pure
        WhileDecl
            { whileCondition = conditionExpr
            , whileBody = body
            }

fnDeclParser :: Parser FnDecl
fnDeclParser = do
    _ <- symbol "fn"
    name <- identifier
    params <- parens (paramParser `sepBy` symbol ",")
    returnType <- optional (symbol "->" *> identifier)
    body <- braces (many statementParser)
    pure
        FnDecl
            { fnName = name
            , fnParams = params
            , fnReturnType = returnType
            , fnBody = body
            }

paramParser :: Parser (Text, Text)
paramParser = do
    name <- identifier
    _ <- symbol ":"
    paramTypeName <- identifier
    pure (name, paramTypeName)

ifDeclParser :: Parser IfDecl
ifDeclParser = do
    _ <- symbol "if"
    condition <- exprParser
    body <- braces (many statementParser)
    elseIfBlocks <- many (try elseIfParser)
    elseBlock <- optional elseBlockParser
    pure
        IfDecl
            { ifCondition = condition
            , ifThenBlock = body
            , ifElseIfBlocks = elseIfBlocks
            , ifElseBlock = elseBlock
            }

matchDeclParser :: Parser MatchDecl
matchDeclParser = do
    _ <- symbol "match"
    subjectExpr <- exprParser
    arms <- braces (many matchArmParser)
    pure
        MatchDecl
            { matchSubject = subjectExpr
            , matchArms = arms
            }

returnStmtParser :: Parser (Maybe Expr)
returnStmtParser = do
    _ <- symbol "return"
    valueExpr <- optional exprParser
    _ <- optional (symbol ";")
    pure valueExpr

matchArmParser :: Parser MatchArm
matchArmParser = do
    patternValue <- matchPatternParser
    _ <- symbol "=>"
    body <- braces (many statementParser)
    _ <- optional (symbol ",")
    pure
        MatchArm
            { matchArmPattern = patternValue
            , matchArmBody = body
            }

matchPatternParser :: Parser MatchPattern
matchPatternParser =
    choice
        [ symbol "_" $> MatchPatternWildcard
        , MatchPatternValue <$> try literalValueParser
        , MatchPatternBind <$> identifier
        ]

elseIfParser :: Parser (Expr, [Stmt])
elseIfParser = do
    _ <- symbol "else"
    _ <- symbol "if"
    condition <- exprParser
    body <- braces (many statementParser)
    pure (condition, body)

elseBlockParser :: Parser [Stmt]
elseBlockParser = do
    _ <- symbol "else"
    braces (many statementParser)

data EntityFieldEntry
    = EntityField Text Expr
    | AppearanceField AppearanceDecl
    | StateChangeField StateChangeDecl

entityFieldParser :: Parser EntityFieldEntry
entityFieldParser =
    try stateChangeFieldParser <|> try appearanceFieldParser <|> genericFieldParser

stateChangeFieldParser :: Parser EntityFieldEntry
stateChangeFieldParser = do
    _ <- symbol "at"
    timeExpr <- exprParser
    fields <- braces (many stateChangeEntryParser)
    pure $ StateChangeField StateChangeDecl
        { stateChangeDeclTime = timeExpr
        , stateChangeDeclFields = Map.fromList fields
        }

stateChangeEntryParser :: Parser (Text, Expr)
stateChangeEntryParser = do
    fieldName <- identifier
    _ <- symbol "="
    value <- exprParser
    _ <- optional (symbol ",")
    pure (fieldName, value)

genericFieldParser :: Parser EntityFieldEntry
genericFieldParser = do
    fieldName <- identifier
    _ <- symbol ":"
    value <- exprParser
    _ <- optional (symbol ",")
    pure (EntityField fieldName value)

appearanceFieldParser :: Parser EntityFieldEntry
appearanceFieldParser = do
    _ <- symbol "appears_on"
    _ <- symbol ":"
    appearanceTimelineName <- identifier
    _ <- symbol "@"
    startValue <- nonRangeExprParser
    _ <- symbol ".."
    endValue <- exprParser
    _ <- optional (symbol ",")
    pure $
        AppearanceField
            AppearanceDecl
                { appearanceDeclTimeline = appearanceTimelineName
                , appearanceDeclStart = startValue
                , appearanceDeclEnd = endValue
                }

timelineFieldParser :: Parser (Text, Expr)
timelineFieldParser = do
    fieldName <- identifier
    _ <- symbol ":"
    value <- try timelineRefExprParser <|> exprParser
    _ <- optional (symbol ",")
    pure (fieldName, value)

timelineRefExprParser :: Parser Expr
timelineRefExprParser = do
    timelineRefName <- identifier
    _ <- symbol "@"
    point <- exprParser
    pure (ExprBinary OpEq (ExprIdent timelineRefName) point)

labeledArrow :: Parser (Maybe Text, Bool)
labeledArrow = do
    _ <- symbol "-["
    labelValue <- stringLiteral
    _ <- symbol "]->"
    pure (Just labelValue, True)

unlabeledArrow :: Parser (Maybe Text, Bool)
unlabeledArrow = do
    _ <- symbol "-->"
    pure (Nothing, True)

braces :: Parser a -> Parser a
braces = between (symbol "{") (symbol "}")

parens :: Parser a -> Parser a
parens = between (symbol "(") (symbol ")")

extractField :: Text -> [(Text, Expr)] -> Maybe Expr
extractField fieldName = lookup fieldName

asIdentifier :: Expr -> Maybe Text
asIdentifier (ExprIdent name) = Just name
asIdentifier _ = Nothing

asTimelineRef :: Expr -> Maybe (Text, Expr)
asTimelineRef (ExprBinary OpEq (ExprIdent name) point) = Just (name, point)
asTimelineRef _ = Nothing
