use std::collections::HashMap;

#[derive(Debug)]
enum Type {
    TInt,
    TFloat,
    TString,
    TBoolean,
    TDuration,
    TMoney,
    TPass,
    TStruct(String),
    TUnion(Box<Type>, Box<Type>),
}

#[derive(Debug)]
enum Literal {
    LInt(i32),
    LFloat(f64),
    LString(String),
    LBoolean(bool),
    LDuration(String),
    LMoney(String),
    LPass,
}

#[derive(Debug)]
enum Expr {
    ELiteral(Literal),
    EVar(String),
    EBinaryOp(String, Box<Expr>, Box<Expr>),
    EStructAccess(Box<Expr>, String),
    EStructLit(String, HashMap<String, Expr>),
}

#[derive(Debug)]
struct VarDecl {
    typ: Type,
    name: String,
    expr: Expr,
}

fn transpile_type(t: &Type) -> String {
    match t {
        Type::TInt => "int".to_string(),
        Type::TFloat => "float".to_string(),
        Type::TString => "string".to_string(),
        Type::TBoolean => "bool".to_string(),
        Type::TDuration => "duration".to_string(),
        Type::TMoney => "money".to_string(),
        Type::TPass => "unit".to_string(),
        Type::TStruct(name) => name.clone(),
        Type::TUnion(t1, t2) => format!("({} | {})", transpile_type(t1), transpile_type(t2)),
    }
}

fn transpile_literal(lit: &Literal) -> String {
    match lit {
        Literal::LInt(i) => i.to_string(),
        Literal::LFloat(f) => f.to_string(),
        Literal::LString(s) => format!("\"{}\"", s),
        Literal::LBoolean(b) => if *b { "true".to_string() } else { "false".to_string() },
        Literal::LDuration(d) => d.clone(),
        Literal::LMoney(m) => m.clone(),
        Literal::LPass => "()".to_string(),
    }
}

fn transpile_expr(expr: &Expr) -> String {
    match expr {
        Expr::ELiteral(lit) => transpile_literal(lit),
        Expr::EVar(v) => v.clone(),
        Expr::EBinaryOp(op, e1, e2) => format!("({} {} {})", transpile_expr(e1), op, transpile_expr(e2)),
        Expr::EStructAccess(e, field) => format!("{}.{}", transpile_expr(e), field),
        Expr::EStructLit(name, fields) => {
            let fields_str = fields.iter()
                .map(|(f, e)| format!("{} = {}", f, transpile_expr(e)))
                .collect::<Vec<String>>()
                .join("; ");
            format!("{{ {} with {} }}", name, fields_str)
        }
    }
}

fn transpile_var_decl(var_decl: &VarDecl) -> String {
    format!("let {} : {} = {};", var_decl.name, transpile_type(&var_decl.typ), transpile_expr(&var_decl.expr))
}

// main execution code

fn main() {
    let statutes: HashMap<String, Expr> = [
        ("sectionNumber".to_string(), Expr::ELiteral(Literal::LInt(378))),
        ("sectionDescription".to_string(), Expr::ELiteral(Literal::LString("Theft".to_string()))),
        ("definition".to_string(), Expr::ELiteral(Literal::LString("Whoever, intending to take dishonestly any movable property out of the possession of any person without that person’s consent, moves that property in order to such taking, is said to commit theft.".to_string()))),
        ("result".to_string(), Expr::EStructLit(
            "punishmentForTheft".to_string(),
            [
                ("ofGeneric".to_string(), Expr::EStructLit(
                    "punishment".to_string(),
                    [
                        ("imprisonmentDuration".to_string(), Expr::ELiteral(Literal::LDuration("3 year".to_string()))),
                        ("fine".to_string(), Expr::ELiteral(Literal::LPass)),
                        ("supplementaryPunishment".to_string(), Expr::ELiteral(Literal::LPass)),
                    ].iter().cloned().collect()
                )),
                ("ofMotorVehicle".to_string(), Expr::EStructLit(
                    "punishment".to_string(),
                    [
                        ("imprisonmentDuration".to_string(), Expr::ELiteral(Literal::LDuration("7 year".to_string()))),
                        ("fine".to_string(), Expr::ELiteral(Literal::LPass)),
                        ("supplementaryPunishment".to_string(), Expr::ELiteral(Literal::LString("A person convicted of an offence under this section shall, unless the court for special reasons thinks fit to order otherwise, be disqualified for such period as the court may order from the date of his release from imprisonment from holding or obtaining a driving licence under the Road Traffic Act 1961.".to_string()))),
                    ].iter().cloned().collect()
                )),
                ("ofDwellingHouse".to_string(), Expr::EStructLit(
                    "punishment".to_string(),
                    [
                        ("imprisonmentDuration".to_string(), Expr::ELiteral(Literal::LDuration("7 year".to_string()))),
                        ("fine".to_string(), Expr::ELiteral(Literal::LPass)),
                        ("supplementaryPunishment".to_string(), Expr::ELiteral(Literal::LPass)),
                    ].iter().cloned().collect()
                )),
                ("ofClerkOrServant".to_string(), Expr::EStructLit(
                    "punishment".to_string(),
                    [
                        ("imprisonmentDuration".to_string(), Expr::ELiteral(Literal::LDuration("7 year".to_string()))),
                        ("fine".to_string(), Expr::ELiteral(Literal::LPass)),
                        ("supplementaryPunishment".to_string(), Expr::ELiteral(Literal::LPass)),
                    ].iter().cloned().collect()
                )),
                ("afterPreparationCausingDeath".to_string(), Expr::EStructLit(
                    "punishment".to_string(),
                    [
                        ("imprisonmentDuration".to_string(), Expr::ELiteral(Literal::LDuration("10 year".to_string()))),
                        ("fine".to_string(), Expr::ELiteral(Literal::LPass)),
                        ("supplementaryPunishment".to_string(), Expr::ELiteral(Literal::LString("caning with not less than 3 strokes".to_string()))),
                    ].iter().cloned().collect()
                )),
            ].iter().cloned().collect()
        )),
    ].iter().cloned().collect();

    let statute_var = VarDecl {
        typ: Type::TStruct("statute".to_string()),
        name: "aStatuteOnTheft".to_string(),
        expr: Expr::EStructLit("statute".to_string(), statutes),
    };

    let fstar_code = transpile_var_decl(&statute_var);
    println!("{}", fstar_code);
}
