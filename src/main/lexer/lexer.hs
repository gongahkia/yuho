module Lexer (tokenize) where

import ../token/token
import Text.Parsec
import Text.Parsec.String (Parser)
import qualified Text.Parsec.Token as P
import Text.Parsec.Language (emptyDef)
import Data.Functor.Identity (Identity)

lexer :: P.TokenParser ()
lexer = P.makeTokenParser emptyDef
    { P.reservedNames = ["true", "false", "pass", "scope", "func", "match", "case", "assert"]
    , P.reservedOpNames = [":=", "|", "+", "-", "*", "/", "//", "%", "==", "!=", ">", "<", ">=", "<=", "and", "or", "not", "."]
    }

identifier :: Parser Token
identifier = TIdentifier <$> P.identifier lexer

intLiteral :: Parser Token
intLiteral = TIntLiteral . fromInteger <$> P.integer lexer

floatLiteral :: Parser Token
floatLiteral = TFloatLiteral <$> P.float lexer

stringLiteral :: Parser Token
stringLiteral = TStringLiteral <$> P.stringLiteral lexer

booleanLiteral :: Parser Token
booleanLiteral = (P.reserved lexer "true" *> pure (TBooleanLiteral True))
             <|> (P.reserved lexer "false" *> pure (TBooleanLiteral False))

percentLiteral :: Parser Token
percentLiteral = do
    num <- P.integer lexer
    _ <- P.symbol lexer "%"
    return $ TPercent (fromInteger num)

moneyLiteral :: Parser Token
moneyLiteral = do
    _ <- P.symbol lexer "$"
    num <- P.float lexer
    return $ TMoney num

dateLiteral :: Parser Token
dateLiteral = do
    date <- many1 (digit <|> char '-')
    return $ TDate date

durationLiteral :: Parser Token
durationLiteral = do
    duration <- many1 (letter <|> char ' ')
    return $ TDuration duration

reserved :: String -> Parser ()
reserved = P.reserved lexer

reservedOp :: String -> Parser ()
reservedOp = P.reservedOp lexer

symbol :: String -> Parser String
symbol = P.symbol lexer

parens :: Parser a -> Parser a
parens = P.parens lexer

braces :: Parser a -> Parser a
braces = P.braces lexer

commaSep :: Parser a -> Parser [a]
commaSep = P.commaSep lexer

lexeme :: Parser a -> Parser a
lexeme = P.lexeme lexer

token :: Parser Token
token = choice
    [ identifier
    , intLiteral
    , floatLiteral
    , stringLiteral
    , booleanLiteral
    , percentLiteral
    , moneyLiteral
    , dateLiteral
    , durationLiteral
    , reserved "pass" *> pure TPass
    , reserved "scope" *> pure TScope
    , reservedOp ":=" *> pure TColonEquals
    , reservedOp "|" *> pure TUnion
    , reservedOp "." *> pure TDot
    , reservedOp "+" *> pure TPlus
    , reservedOp "-" *> pure TMinus
    , reservedOp "*" *> pure TMultiply
    , reservedOp "/" *> pure TDivide
    , reservedOp "//" *> pure TIntDivide
    , reservedOp "%" *> pure TModulo
    , reservedOp "==" *> pure TEquals
    , reservedOp "!=" *> pure TNotEquals
    , reservedOp ">" *> pure TGreaterThan
    , reservedOp "<" *> pure TLessThan
    , reservedOp ">=" *> pure TGreaterOrEqual
    , reservedOp "<=" *> pure TLessOrEqual
    , reservedOp "and" *> pure TAnd
    , reservedOp "or" *> pure TOr
    , reservedOp "not" *> pure TNot
    , reserved "match" *> pure TMatch
    , reserved "case" *> pure TCase
    , reserved "consequence" *> pure TConsequence
    , reserved "func" *> pure TFunc
    , symbol "(" *> pure TLParen
    , symbol ")" *> pure TRParen
    , symbol "{" *> pure TLBrace
    , symbol "}" *> pure TRBrace
    , reserved "assert" *> pure TAssert
    , eof *> pure TEOF
    ]

tokenize :: String -> Either ParseError [Token]
tokenize = parse (many token) ""
