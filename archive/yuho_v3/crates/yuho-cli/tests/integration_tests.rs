use yuho_check::Checker;
use yuho_core::parse;
use yuho_transpile::{to_alloy, to_english, to_json, to_latex, to_mermaid, to_typescript};

#[test]
fn test_dependent_types_example() {
    let source = r#"
        struct Person {
            string name,
            BoundedInt<0, 150> age,
            money<SGD> salary,
        }

        Person alice := {
            name := "Alice",
            age := 30,
            salary := $50000,
        }
    "#;

    let program = parse(source).expect("Should parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "No errors expected: {:?}", errors);
}

#[test]
fn test_bounded_int_validation() {
    let source = r#"
        struct Test {
            BoundedInt<100, 0> invalid,
        }
    "#;

    let program = parse(source).expect("Should parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty(), "Should have BoundedInt range error");
}

#[test]
fn test_positive_type_validation() {
    let source = r#"
        struct Test {
            Positive<string> invalid,
        }
    "#;

    let program = parse(source).expect("Should parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty(), "Should have Positive constraint error");
}

#[test]
fn test_all_transpilers_with_dependent_types() {
    let source = r#"
        struct Person {
            BoundedInt<0, 100> age,
            Positive<money<SGD>> salary,
        }
    "#;

    let program = parse(source).expect("Should parse");

    // All transpilers should handle dependent types
    let mermaid = to_mermaid(&program);
    assert!(mermaid.contains("Person"));

    let alloy = to_alloy(&program);
    assert!(alloy.contains("sig Person"));

    let json = to_json(&program);
    assert!(json.contains("Person"));

    let latex = to_latex(&program);
    assert!(latex.contains("Person"));

    let english = to_english(&program);
    assert!(english.contains("Person"));

    let typescript = to_typescript(&program);
    assert!(typescript.contains("Person"));
}

#[test]
fn test_currency_types() {
    let source = r#"
        money<SGD> sgd_amount := $1000
        money<USD> usd_amount := $750
        money<EUR> eur_amount := $900
    "#;

    let program = parse(source).expect("Should parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "No errors expected for currency types");
}

#[test]
fn test_array_types() {
    let source = r#"
        struct Document {
            Array<string> pages,
            NonEmpty<string> authors,
        }
    "#;

    let program = parse(source).expect("Should parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "No errors expected for array types");
}

#[test]
fn test_complex_dependent_types_composition() {
    let source = r#"
        struct Contract {
            NonEmpty<Array<Positive<int>>> witness_counts,
            BoundedInt<1, 365> duration_days,
        }
    "#;

    let program = parse(source).expect("Should parse");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "No errors for nested dependent types");
}

#[test]
fn test_parse_cheating_example() {
    // Path relative to workspace root
    let path = concat!(env!("CARGO_MANIFEST_DIR"), "/../../examples/cheating.yh");
    let source = std::fs::read_to_string(path).expect("Should read cheating.yh");

    let program = parse(&source).expect("Should parse cheating.yh");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    // Original example should still work
    assert!(errors.iter().all(|e| !e.to_string().contains("Undefined")));
}

#[test]
fn test_parse_dependent_types_example() {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../examples/dependent_types.yh"
    );
    let source = std::fs::read_to_string(path).expect("Should read dependent_types.yh");

    let program = parse(&source).expect("Should parse dependent_types.yh");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "Dependent types example should be valid");
}

#[test]
fn test_parse_currency_types_example() {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../examples/currency_types.yh"
    );
    let source = std::fs::read_to_string(path).expect("Should read currency_types.yh");

    let program = parse(&source).expect("Should parse currency_types.yh");
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "Currency types example should be valid");
}
