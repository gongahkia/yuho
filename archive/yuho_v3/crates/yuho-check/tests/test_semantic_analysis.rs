use yuho_check::{CheckError, Checker};
use yuho_core::ast::*;
use yuho_core::parser::parse;

#[test]
fn test_check_bounded_int_valid() {
    let source = r#"
BoundedInt<0, 100> age := 50
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(
        errors.is_empty(),
        "Should not have errors for valid BoundedInt"
    );
}

#[test]
fn test_check_bounded_int_invalid_range() {
    let source = r#"
BoundedInt<100, 0> invalid := 50
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty(), "Should have error for invalid range");
}

#[test]
fn test_check_positive_constraint() {
    let source = r#"
Positive<int> count := 5
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty());
}

#[test]
fn test_check_undefined_variable() {
    let source = r#"
int x := y + 1
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| matches!(e, CheckError::Undefined(_))));
}

#[test]
fn test_check_duplicate_definition() {
    let source = r#"
int x := 1
int x := 2
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
    assert!(errors.iter().any(|e| matches!(e, CheckError::Duplicate(_))));
}

#[test]
fn test_check_struct_field_access() {
    let source = r#"
struct Person {
    string name,
    int age,
}

Person p := Person { name := "Alice", age := 30 }
string n := p.name
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty());
}

#[test]
fn test_check_invalid_field_access() {
    let source = r#"
struct Person {
    string name,
}

Person p := Person { name := "Alice" }
int invalid := p.nonexistent
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(!errors.is_empty());
}

#[test]
fn test_check_generic_type_arity() {
    let source = r#"
struct Container<T> {
    T value,
}

Container<int, string> invalid := Container { value := 5 }
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    // Should have arity mismatch error
    assert!(!errors.is_empty());
}
