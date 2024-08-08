use std::fmt;

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

impl fmt::Display for Type {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Type::TInt => write!(f, "Int"),
            Type::TFloat => write!(f, "Float"),
            Type::TString => write!(f, "String"),
            Type::TBoolean => write!(f, "Boolean"),
            Type::TMoney => write!(f, "Money"),
            Type::TDate => write!(f, "Date"),
            Type::TDuration => write!(f, "Duration"),
        }
    }
}

impl fmt::Display for Literal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Literal::Int(v) => write!(f, "{}", v),
            Literal::Float(v) => write!(f, "{}", v),
            Literal::String(v) => write!(f, "\"{}\"", v),
            Literal::Boolean(v) => write!(f, "{}", v),
        }
    }
}

impl fmt::Display for Expr {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Expr::Var(v) => write!(f, "{}", v),
            Expr::Lit(lit) => write!(f, "{}", lit),
            Expr::UnaryOp(op, expr) => write!(f, "{}({})", op, expr),
            Expr::BinaryOp(op, left, right) => write!(f, "({} {} {})", left, op, right),
        }
    }
}

impl fmt::Display for Stmt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Stmt::VariableDeclaration(t, name, expr) => write!(f, "var {}: {} = {};", name, t, expr),
            Stmt::FunctionDeclaration(t, name, params, body) => {
                let params_str = params.iter().map(|(t, n)| format!("{}: {}", n, t)).collect::<Vec<_>>().join(", ");
                write!(f, "fun {}({}): {} = {};", name, params_str, t, body)
            },
            Stmt::Scope(name, stmts) => {
                let stmts_str = stmts.iter().map(|stmt| format!("{}", stmt)).collect::<Vec<_>>().join("\n");
                write!(f, "scope {} {{\n{}\n}}", name, stmts_str)
            },
            Stmt::Struct(name, fields) => {
                let fields_str = fields.iter().map(|(t, n)| format!("{}: {}", n, t)).collect::<Vec<_>>().join(", ");
                write!(f, "struct {} {{ {} }}", name, fields_str)
            },
            Stmt::Assertion(expr) => write!(f, "assert {};", expr),
        }
    }
}

fn transpile_program(program: Program) -> String {
    program.iter().map(|stmt| format!("{}", stmt)).collect::<Vec<_>>().join("\n")
}

fn main() {
    let program = vec![
        Stmt::VariableDeclaration(Type::TInt, "x".to_string(), Expr::Lit(Literal::Int(42))),
        Stmt::FunctionDeclaration(Type::TInt, "add".to_string(), vec![(Type::TInt, "a".to_string()), (Type::TInt, "b".to_string())], Expr::BinaryOp("+".to_string(), Box::new(Expr::Var("a".to_string())), Box::new(Expr::Var("b".to_string())))),
        Stmt::Scope("main".to_string(), vec![
            Stmt::VariableDeclaration(Type::TInt, "result".to_string(), Expr::BinaryOp("*".to_string(), Box::new(Expr::Var("x".to_string())), Box::new(Expr::Var("x".to_string())))),
        ]),
        Stmt::Struct("Person".to_string(), vec![(Type::TString, "name".to_string()), (Type::TInt, "age".to_string())]),
        Stmt::Assertion(Expr::BinaryOp("==".to_string(), Box::new(Expr::Var("result".to_string())), Box::new(Expr::Lit(Literal::Int(1764))))),
    ];

    let alloy_code = transpile_program(program);
    println!("{}", alloy_code);
}
