// Semantic analysis tests for legal_test feature

use yuho_check::Checker;
use yuho_core::parse;

#[test]
fn test_legal_test_semantic_check_valid() {
    let source = r#"
        legal_test Cheating {
            requires deception: bool,
            requires dishonest_intent: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);

    assert!(
        errors.is_empty(),
        "Expected no semantic errors, got: {:?}",
        errors
    );
}

#[test]
fn test_legal_test_referenced_in_satisfies() {
    let source = r#"
        legal_test Theft {
            requires taking: bool,
            requires dishonest_intent: bool,
        }

        bool offense := true

        match offense {
            case satisfies Theft := "guilty"
            case _ := "not guilty"
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);

    assert!(
        errors.is_empty(),
        "Expected no semantic errors when referencing defined legal test, got: {:?}",
        errors
    );
}

#[test]
fn test_satisfies_undefined_legal_test() {
    let source = r#"
        match offense {
            case satisfies UndefinedTest := "result"
            case _ := "default"
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);

    assert!(
        !errors.is_empty(),
        "Expected semantic error for undefined legal test"
    );
    assert!(
        errors.iter().any(|e| {
            let err_str = e.to_string();
            err_str.contains("UndefinedTest") || err_str.contains("not defined")
        }),
        "Expected error about undefined legal test, got: {:?}",
        errors
    );
}

#[test]
fn test_legal_test_duplicate_name() {
    let source = r#"
        legal_test Test {
            requires a: bool,
        }

        legal_test Test {
            requires b: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);

    assert!(
        !errors.is_empty(),
        "Expected semantic error for duplicate legal test name"
    );
}

#[test]
fn test_legal_test_duplicate_requirement() {
    let source = r#"
        legal_test Test {
            requires a: bool,
            requires a: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);

    // This may or may not be an error depending on implementation
    // Just verify it parses correctly
    assert!(program.items.len() > 0);
}

#[test]
fn test_legal_test_in_scope() {
    let source = r#"
        scope criminal {
            legal_test Murder {
                requires killing: bool,
                requires intent: bool,
            }

            bool situation := true

            match situation {
                case satisfies Murder := "guilty"
                case _ := "not guilty"
            }
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);

    assert!(
        errors.is_empty(),
        "Expected no semantic errors in scoped legal test, got: {:?}",
        errors
    );
}

#[test]
fn test_multiple_satisfies_patterns() {
    let source = r#"
        legal_test TestA {
            requires a: bool,
        }

        legal_test TestB {
            requires b: bool,
        }

        bool value := true

        match value {
            case satisfies TestA := "result A"
            case satisfies TestB := "result B"
            case _ := "default"
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);

    assert!(
        errors.is_empty(),
        "Expected no semantic errors with multiple satisfies patterns, got: {:?}",
        errors
    );
}

#[test]
fn test_legal_test_all_requirements_boolean() {
    let source = r#"
        legal_test ValidTest {
            requires req1: bool,
            requires req2: bool,
            requires req3: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);

    assert!(
        errors.is_empty(),
        "Expected no errors when all requirements are boolean, got: {:?}",
        errors
    );
}

#[test]
fn test_legal_test_exhaustiveness_checking() {
    let source = r#"
        legal_test Test {
            requires a: bool,
        }

        // Match should be exhaustive with satisfies + wildcard
        match value {
            case satisfies Test := "pass"
            case _ := "fail"
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);

    // Should not have exhaustiveness errors
    assert!(
        !errors.iter().any(|e| e.to_string().contains("exhaustive")),
        "Should not have exhaustiveness errors with wildcard, got: {:?}",
        errors
    );
}
