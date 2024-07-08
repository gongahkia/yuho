module Token where

data Token
    = TIdentifier String
    | TIntLiteral Int
    | TFloatLiteral Double
    | TStringLiteral String
    | TBooleanLiteral Bool
    | TPercent Int
    | TMoney Double
    | TDate String
    | TDuration String
    | TPass
    | TScope
    | TUnion
    | TColonEquals
    | TComma
    | TDot
    | TPlus
    | TMinus
    | TMultiply
    | TDivide
    | TIntDivide
    | TModulo
    | TEquals
    | TNotEquals
    | TGreaterThan
    | TLessThan
    | TGreaterOrEqual
    | TLessOrEqual
    | TAnd
    | TOr
    | TNot
    | TMatch
    | TCase
    | TConsequence
    | TFunc
    | TLParen
    | TRParen
    | TLBrace
    | TRBrace
    | TAssert
    | TEOF
    deriving (Show, Eq)
