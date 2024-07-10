#[derive(Debug)]
pub enum Literal {
    Int(i64),
    Float(f64),
    String(String),
    Boolean(bool),
}

#[derive(Debug)]
pub enum Type {
    TInt,
    TFloat,
    TString,
    TBoolean,
    TMoney,
    TDate,
    TDuration,
}

#[derive(Debug)]
pub enum Expr {
    Var(String),
    Lit(Literal),
    UnaryOp(String, Box<Expr>),
    BinaryOp(String, Box<Expr>, Box<Expr>),
}

#[derive(Debug)]
pub enum Stmt {
    VariableDeclaration(Type, String, Expr),
    FunctionDeclaration(Type, String, Vec<(Type, String)>, Expr),
    Scope(String, Vec<Stmt>),
    Struct(String, Vec<(Type, String)>),
    Assertion(Expr),
}

pub type Program = Vec<Stmt>;
