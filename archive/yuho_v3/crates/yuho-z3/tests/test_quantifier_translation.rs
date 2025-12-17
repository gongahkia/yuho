//! Test suite for Z3 quantifier translation

use yuho_core::ast::*;
use yuho_z3::quantifier::translate_principle_to_z3;

#[test]
fn test_simple_forall_translation() {
    let principle = PrincipleDefinition {
        name: "SimpleForall".to_string(),
        body: Expr::Forall {
            var: "x".to_string(),
            ty: Type::Int,
            body: Box::new(Expr::Binary(
                Box::new(Expr::Identifier("x".to_string())),
                BinaryOp::Gt,
                Box::new(Expr::Literal(Literal::Int(0))),
            )),
        },
        span: Span { start: 0, end: 0 },
    };

    let result = translate_principle_to_z3(&principle);
    assert!(result.is_ok());
    let smt = result.unwrap();
    assert!(smt.contains("forall"));
    assert!(smt.contains("Int"));
    assert!(smt.contains(">"));
}

#[test]
fn test_simple_exists_translation() {
    let principle = PrincipleDefinition {
        name: "SimpleExists".to_string(),
        body: Expr::Exists {
            var: "y".to_string(),
            ty: Type::Bool,
            body: Box::new(Expr::Identifier("y".to_string())),
        },
        span: Span { start: 0, end: 0 },
    };

    let result = translate_principle_to_z3(&principle);
    assert!(result.is_ok());
    let smt = result.unwrap();
    assert!(smt.contains("exists"));
    assert!(smt.contains("Bool"));
}

#[test]
fn test_nested_forall_forall() {
    let principle = PrincipleDefinition {
        name: "NestedForall".to_string(),
        body: Expr::Forall {
            var: "x".to_string(),
            ty: Type::Int,
            body: Box::new(Expr::Forall {
                var: "y".to_string(),
                ty: Type::Int,
                body: Box::new(Expr::Binary(
                    Box::new(Expr::Identifier("x".to_string())),
                    BinaryOp::Eq,
                    Box::new(Expr::Identifier("y".to_string())),
                )),
            }),
        },
        span: Span { start: 0, end: 0 },
    };

    let result = translate_principle_to_z3(&principle);
    assert!(result.is_ok());
    let smt = result.unwrap();
    // Should have two nested forall quantifiers
    assert_eq!(smt.matches("forall").count(), 2);
}

#[test]
fn test_mixed_quantifiers() {
    let principle = PrincipleDefinition {
        name: "MixedQuantifiers".to_string(),
        body: Expr::Forall {
            var: "x".to_string(),
            ty: Type::Int,
            body: Box::new(Expr::Exists {
                var: "y".to_string(),
                ty: Type::Int,
                body: Box::new(Expr::Binary(
                    Box::new(Expr::Identifier("x".to_string())),
                    BinaryOp::Lt,
                    Box::new(Expr::Identifier("y".to_string())),
                )),
            }),
        },
        span: Span { start: 0, end: 0 },
    };

    let result = translate_principle_to_z3(&principle);
    assert!(result.is_ok());
    let smt = result.unwrap();
    assert!(smt.contains("forall"));
    assert!(smt.contains("exists"));
}

#[test]
fn test_boolean_operators() {
    let principle = PrincipleDefinition {
        name: "BooleanOps".to_string(),
        body: Expr::Forall {
            var: "p".to_string(),
            ty: Type::Bool,
            body: Box::new(Expr::Binary(
                Box::new(Expr::Identifier("p".to_string())),
                BinaryOp::And,
                Box::new(Expr::Literal(Literal::Bool(true))),
            )),
        },
        span: Span { start: 0, end: 0 },
    };

    let result = translate_principle_to_z3(&principle);
    assert!(result.is_ok());
    let smt = result.unwrap();
    assert!(smt.contains("and"));
}

#[test]
fn test_arithmetic_operators() {
    let principle = PrincipleDefinition {
        name: "Arithmetic".to_string(),
        body: Expr::Forall {
            var: "n".to_string(),
            ty: Type::Int,
            body: Box::new(Expr::Binary(
                Box::new(Expr::Binary(
                    Box::new(Expr::Identifier("n".to_string())),
                    BinaryOp::Add,
                    Box::new(Expr::Literal(Literal::Int(1))),
                )),
                BinaryOp::Gt,
                Box::new(Expr::Identifier("n".to_string())),
            )),
        },
        span: Span { start: 0, end: 0 },
    };

    let result = translate_principle_to_z3(&principle);
    assert!(result.is_ok());
    let smt = result.unwrap();
    assert!(smt.contains("+"));
    assert!(smt.contains(">"));
}
