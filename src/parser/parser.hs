module Parser (parseProgram) where

import ../token/token
import ../ast/ast
import Text.Parsec
import Text.Parsec.String (Parser)
import qualified Text.Parsec.Expr as Ex
import qualified Text.Parsec.Token as P
import Text.Parsec.Language (emptyDef)
import Data.Functor.Identity (Identity)

lexer :: P.TokenParser ()
lexer = P.makeTokenParser emptyDef

identifier :: Parser String
identifier = P.identifier lexer

integer :: Parser Int
integer = fromInteger <$> P.integer lexer

float :: Parser Double
float = P.float lexer

stringLiteral :: Parser String
stringLiteral = P.stringLiteral lexer

boolean :: Parser Bool
boolean = (P.reserved lexer "true" *> pure True)
      <|> (P.reserved lexer "false" *> pure False)

reserved :: String -> Parser ()
reserved = P.reserved lexer

reservedOp :: String -> Parser ()
reservedOp = P.reservedOp lexer

parens :: Parser a -> Parser a
parens = P.parens lexer

braces :: Parser a -> Parser a
braces = P.braces lexer

commaSep :: Parser a -> Parser [a]
commaSep = P.commaSep lexer

lexeme :: Parser a -> Parser a
lexeme = P.lexeme lexer

parseLiteral :: Parser Literal
parseLiteral = choice
    [ LInt <$> integer
    , LFloat <$> float
    , LString <$> stringLiteral
    , LBoolean <$> boolean
    ]

parseType :: Parser Type
parseType = choice
    [ reserved "int" *> pure TInt
    , reserved "float" *> pure TFloat
    , reserved "string" *> pure TString
    , reserved "boolean" *> pure TBoolean
    , reserved "money" *> pure TMoney
    , reserved "date" *> pure TDate
    , reserved "duration" *> pure TDuration
    ]

parseExpression :: Parser Expression
parseExpression = Ex.buildExpressionParser table term
  where
    table = [ [Ex.Prefix (reservedOp "-" *> pure (UnaryOp Neg))]
            , [Ex.Infix  (reservedOp "*" *> pure (BinaryOp Mul)) Ex.AssocLeft
              , Ex.Infix  (reservedOp "/" *> pure (BinaryOp Div)) Ex.AssocLeft]
            , [Ex.Infix  (reservedOp "+" *> pure (BinaryOp Add)) Ex.AssocLeft
              , Ex.Infix  (reservedOp "-" *> pure (BinaryOp Sub)) Ex.AssocLeft]
            ]
    term = parens parseExpression
       <|> Var <$> identifier
       <|> Lit <$> parseLiteral

parseVariableDeclaration :: Parser Statement
parseVariableDeclaration = do
    typ <- parseType
    name <- identifier
    reservedOp ":="
    value <- parseExpression
    return $ VariableDeclaration typ name value

parseFunctionDeclaration :: Parser Statement
parseFunctionDeclaration = do
    retType <- parseType
    reserved "func"
    name <- identifier
    params <- parens (commaSep parseParameter)
    body <- braces parseExpression
    return $ FunctionDeclaration retType name params body
  where
    parseParameter = do
        typ <- parseType
        name <- identifier
        return (typ, name)

parseScope :: Parser Statement
parseScope = do
    reserved "scope"
    name <- identifier
    body <- braces (many parseStatement)
    return $ Scope name body

parseStruct :: Parser Statement
parseStruct = do
    reserved "struct"
    name <- identifier
    fields <- braces (commaSep parseField)
    return $ Struct name fields
  where
    parseField = do
        typ <- parseType
        name <- identifier
        return (typ, name)

parseAssertion :: Parser Statement
parseAssertion = do
    reserved "assert"
    expr <- parseExpression
    return $ Assertion expr

parseStatement :: Parser Statement
parseStatement = choice
    [ try parseVariableDeclaration
    , try parseFunctionDeclaration
    , try parseScope
    , try parseStruct
    , try parseAssertion
    ]

parseProgram :: Parser [Statement]
parseProgram = many parseStatement
