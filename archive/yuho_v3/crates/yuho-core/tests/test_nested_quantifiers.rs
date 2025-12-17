use yuho_core::ast::*;
use yuho_core::parser::parse;

#[test]
fn test_simple_forall() {
    let source = r#"
principle TestPrinciple {
    forall x: int, x > 0
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();
    assert_eq!(program.items.len(), 1);
}

#[test]
fn test_simple_exists() {
    let source = r#"
principle TestPrinciple {
    exists x: int, x == 42
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_nested_forall_forall() {
    let source = r#"
principle NestedForall {
    forall x: int, forall y: int, x + y > 0
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();

    if let Item::Principle(p) = &program.items[0] {
        // Check it's a nested Forall expression
        if let Expr::Forall {
            var: var1,
            ty: ty1,
            body,
        } = &p.body
        {
            assert_eq!(var1, "x");
            assert_eq!(ty1, &Type::Int);

            // Check inner forall
            if let Expr::Forall {
                var: var2,
                ty: ty2,
                body: _,
            } = &**body
            {
                assert_eq!(var2, "y");
                assert_eq!(ty2, &Type::Int);
            } else {
                panic!("Expected nested Forall");
            }
        } else {
            panic!("Expected Forall expression");
        }
    }
}

#[test]
fn test_nested_forall_exists() {
    let source = r#"
principle MixedQuantifiers {
    forall person: Person, exists evidence: Evidence, evidence.person_id == person.id
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_triple_nested_quantifiers() {
    let source = r#"
principle TripleNested {
    forall a: int, forall b: int, exists c: int, a + b == c
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_quantifier_depth_limit() {
    // Test that parser rejects > 10 nested quantifiers
    let mut source = String::from("principle TooDeep {\n    ");
    for i in 0..12 {
        source.push_str(&format!("forall x{}: int, ", i));
    }
    source.push_str("true\n}");

    let result = parse(&source);
    assert!(
        result.is_err(),
        "Should reject quantifiers nested > 10 levels"
    );
}

#[test]
fn test_quantifier_with_complex_body() {
    let source = r#"
principle ComplexBody {
    forall case: CriminalCase, 
    case.status == Status::Closed && case.verdict != Verdict::Pending
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_quantifiers_in_match_patterns() {
    let source = r#"
func checkEvidence(Case c) -> bool {
    := match c {
        case satisfies HasEvidence := forall e: Evidence, e.case_id == c.id
        case _ := false
    }
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
}
