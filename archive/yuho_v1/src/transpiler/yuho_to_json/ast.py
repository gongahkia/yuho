from typing import List, Tuple, Union

class Literal:
    pass

class LInt(Literal):
    def __init__(self, value: int):
        self.value = value

class LFloat(Literal):
    def __init__(self, value: float):
        self.value = value

class LString(Literal):
    def __init__(self, value: str):
        self.value = value

class LBoolean(Literal):
    def __init__(self, value: bool):
        self.value = value

class Type:
    pass

class TInt(Type):
    pass

class TFloat(Type):
    pass

class TString(Type):
    pass

class TBoolean(Type):
    pass

class TMoney(Type):
    pass

class TDate(Type):
    pass

class TDuration(Type):
    pass

class Expr:
    pass

class Var(Expr):
    def __init__(self, name: str):
        self.name = name

class Lit(Expr):
    def __init__(self, literal: Literal):
        self.literal = literal

class UnaryOp(Expr):
    def __init__(self, op: str, expr: Expr):
        self.op = op
        self.expr = expr

class BinaryOp(Expr):
    def __init__(self, op: str, left: Expr, right: Expr):
        self.op = op
        self.left = left
        self.right = right

class Stmt:
    pass

class VariableDeclaration(Stmt):
    def __init__(self, typ: Type, name: str, expr: Expr):
        self.typ = typ
        self.name = name
        self.expr = expr

class FunctionDeclaration(Stmt):
    def __init__(self, return_type: Type, name: str, params: List[Tuple[Type, str]], body: Expr):
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body

class Scope(Stmt):
    def __init__(self, name: str, statements: List[Stmt]):
        self.name = name
        self.statements = statements

class Struct(Stmt):
    def __init__(self, name: str, fields: List[Tuple[Type, str]]):
        self.name = name
        self.fields = fields

class Assertion(Stmt):
    def __init__(self, expr: Expr):
        self.expr = expr

Program = List[Stmt]
