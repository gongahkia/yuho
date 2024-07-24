type literal =
  | LInt of int
  | LFloat of float
  | LString of string
  | LBoolean of bool

type typ =
  | TInt
  | TFloat
  | TString
  | TBoolean
  | TMoney
  | TDate
  | TDuration

type expr =
  | Var of string
  | Lit of literal
  | UnaryOp of string * expr
  | BinaryOp of string * expr * expr

type stmt =
  | VariableDeclaration of typ * string * expr
  | FunctionDeclaration of typ * string * (typ * string) list * expr
  | Scope of string * stmt list
  | Struct of string * (typ * string) list
  | Assertion of expr

type program = stmt list
