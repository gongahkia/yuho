module AST where

type Identifier = String

data Literal
    = LInt Int
    | LFloat Double
    | LString String
    | LBoolean Bool
    | LPercent Int
    | LMoney Double
    | LDate String
    | LDuration String
    | LPass
    deriving (Show, Eq)

data Type
    = TInt
    | TFloat
    | TString
    | TBoolean
    | TPercent
    | TMoney
    | TDate
    | TDuration
    | TPass
    | TUnion [Type]
    | TScope
    | TStruct [(Type, Identifier)]
    deriving (Show, Eq)

data Expr
    = EVar Identifier
    | ELit Literal
    | EBinOp BinOp Expr Expr
    | EFuncCall Identifier [Expr]
    | EMatch Expr [(Pattern, Expr)]
    deriving (Show, Eq)

data BinOp
    = Add
    | Subtract
    | Multiply
    | Divide
    | IntDivide
    | Modulo
    | Equals
    | NotEquals
    | GreaterThan
    | LessThan
    | GreaterOrEqual
    | LessOrEqual
    | And
    | Or
    | Not
    deriving (Show, Eq)

data Pattern
    = PInt Int
    | PFloat Double
    | PString String
    | PBoolean Bool
    | PPercent Int
    | PMoney Double
    | PDate String
    | PDuration String
    | PPass
    | PDefault
    deriving (Show, Eq)

data Statement
    = SVarDecl Type Identifier Expr
    | SFuncDecl Type Identifier [(Type, Identifier)] Expr
    | SAssert Expr
    | SScope Identifier [Statement]
    deriving (Show, Eq)

data Program = Program [Statement]
    deriving (Show, Eq)
