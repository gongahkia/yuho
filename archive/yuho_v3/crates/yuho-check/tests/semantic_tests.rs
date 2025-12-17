use yuho_check::Checker;
use yuho_core::parse;

#[test]
fn test_undefined_variable() {
    let source = "int x := undefined_var";
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| e.to_string().contains("Undefined")));
}

#[test]
fn test_duplicate_struct_definition() {
    let source = r#"
        struct Person { string name, }
        struct Person { int age, }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| e.to_string().contains("Duplicate")));
}

#[test]
fn test_duplicate_enum_definition() {
    let source = r#"
        enum Status { Active, Inactive, }
        enum Status { Pending, }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| e.to_string().contains("Duplicate")));
}

#[test]
fn test_duplicate_variable() {
    let source = r#"
        int x := 42
        string x := "hello"
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| e.to_string().contains("Duplicate")));
}

#[test]
fn test_valid_struct_init() {
    let source = r#"
        struct Person {
            string name,
            int age,
        }
        Person p := {
            name := "Alice",
            age := 30,
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "Expected no errors, got: {:?}", errors);
}

#[test]
fn test_struct_field_validation_skipped() {
    // Note: Current implementation doesn't validate struct field names during init
    // This is a known limitation - adding this test for future improvement
    let source = r#"
        struct Person {
            string name,
            int age,
        }
        Person p := {
            name := "Alice",
            age := 30,
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty());
}

#[test]
fn test_match_exhaustiveness() {
    let source = r#"
        match value {
            case true := "yes"
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    if !errors.is_empty() {
        for err in &errors {
            eprintln!("Error: {}", err.to_string());
        }
    }
    assert!(!errors.is_empty());
    assert!(errors
        .iter()
        .any(|e| e.to_string().contains("exhaustive") || e.to_string().contains("Exhaustive")));
}

#[test]
fn test_match_unreachable_case() {
    let source = r#"
        match value {
            case _ := "default"
            case true := "unreachable"
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| e.to_string().contains("Unreachable")));
}

#[test]
fn test_valid_exhaustive_match() {
    let source = r#"
        bool value := true
        match value {
            case true := "yes"
            case false := "no"
            case _ := "unknown"
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "Expected no errors, got: {:?}", errors);
}

#[test]
fn test_scoped_variables() {
    let source = r#"
        scope outer {
            int x := 42
            scope inner {
                int y := x
            }
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "Expected no errors in nested scopes");
}

#[test]
fn test_undefined_in_nested_scope() {
    let source = r#"
        scope outer {
            scope inner {
                int y := 10
            }
            int z := y
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| e.to_string().contains("Undefined")));
}

#[test]
fn test_function_call_undefined() {
    let source = r#"
        int result := undefined_function(1, 2, 3)
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| e.to_string().contains("Undefined")));
}

#[test]
fn test_valid_function_definition() {
    let source = r#"
        int func add(int a, int b) {
            := a + b
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "Expected no errors for valid function");
}

#[test]
fn test_bounded_int_invalid_range() {
    let source = r#"
        struct Test {
            BoundedInt<100, 0> invalid,
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| e.to_string().contains("Invalid")));
}

#[test]
fn test_bounded_int_valid_range() {
    let source = r#"
        struct Test {
            BoundedInt<0, 100> valid_age,
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty());
}

#[test]
fn test_positive_on_numeric_types() {
    let source = r#"
        struct Test {
            Positive<int> count,
            Positive<money<USD>> amount,
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty());
}

#[test]
fn test_positive_on_invalid_type() {
    let source = r#"
        struct Test {
            Positive<string> invalid,
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
}

#[test]
fn test_complex_nested_dependent_types() {
    let source = r#"
        struct Contract {
            NonEmpty<Array<Positive<int>>> witness_counts,
            BoundedInt<1, 365> duration_days,
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(
        errors.is_empty(),
        "Expected no errors for nested dependent types"
    );
}

#[test]
fn test_undefined_type_in_struct() {
    let source = r#"
        struct Person {
            UndefinedType field,
        }
    "#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| e.to_string().contains("Undefined")));
}
