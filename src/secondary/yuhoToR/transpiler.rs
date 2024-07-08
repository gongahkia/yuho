mod ast;
use ast::{Expr, Literal, Program, Stmt, Type};

fn transpile_literal(lit: &Literal) -> String {
    match lit {
        Literal::Int(i) => i.to_string(),
        Literal::Float(f) => f.to_string(),
        Literal::String(s) => format!("\"{}\"", s),
        Literal::Boolean(b) => b.to_string(),
    }
}

fn transpile_type(typ: &Type) -> String {
    match typ {
        Type::TInt => "numeric".to_string(),
        Type::TFloat => "numeric".to_string(),
        Type::TString => "character".to_string(),
        Type::TBoolean => "logical".to_string(),
        Type::TMoney => "numeric".to_string(),
        Type::TDate => "Date".to_string(),
        Type::TDuration => "numeric".to_string(),
    }
}

fn transpile_expr(expr: &Expr) -> String {
    match expr {
        Expr::Var(v) => v.clone(),
        Expr::Lit(lit) => transpile_literal(lit),
        Expr::UnaryOp(op, e) => format!("({}{})", op, transpile_expr(e)),
        Expr::BinaryOp(op, e1, e2) => format!("({} {} {})", transpile_expr(e1), op, transpile_expr(e2)),
    }
}

fn transpile_stmt(stmt: &Stmt) -> String {
    match stmt {
        Stmt::VariableDeclaration(_, name, expr) => {
            format!("{} <- {}", name, transpile_expr(expr))
        }
        Stmt::FunctionDeclaration(_, name, params, body) => {
            let params_str = params
                .iter()
                .map(|(_, n)| n.clone())
                .collect::<Vec<String>>()
                .join(", ");
            format!(
                "{} <- function({}) {{ return({}) }}",
                name,
                params_str,
                transpile_expr(body)
            )
        }
        Stmt::Scope(name, stmts) => {
            let stmts_str = stmts.iter().map(transpile_stmt).collect::<Vec<String>>().join("\n");
            format!("{} <- {{\n{}\n}}", name, stmts_str)
        }
        Stmt::Struct(name, fields) => {
            let fields_str = fields
                .iter()
                .map(|(_, n)| format!("{} = NULL", n))
                .collect::<Vec<String>>()
                .join(", ");
            format!("{} <- list({})", name, fields_str)
        }
        Stmt::Assertion(expr) => {
            format!("stopifnot({})", transpile_expr(expr))
        }
    }
}

fn transpile_program(prog: &Program) -> String {
    prog.iter().map(transpile_stmt).collect::<Vec<String>>().join("\n")
}

fn main() {
    let example_program: Program = vec![
        Stmt::VariableDeclaration(Type::TInt, "x".to_string(), Expr::Lit(Literal::Int(42))),
        Stmt::FunctionDeclaration(
            Type::TInt,
            "add".to_string(),
            vec![(Type::TInt, "a".to_string()), (Type::TInt, "b".to_string())],
            Expr::BinaryOp("+".to_string(), Box::new(Expr::Var("a".to_string())), Box::new(Expr::Var("b".to_string())))
        ),
        Stmt::Assertion(Expr::BinaryOp("==".to_string(), Box::new(Expr::Var("x".to_string())), Box::new(Expr::Lit(Literal::Int(42))))),
    ];
    let r_code = transpile_program(&example_program);
    println!("{}", r_code);
}
