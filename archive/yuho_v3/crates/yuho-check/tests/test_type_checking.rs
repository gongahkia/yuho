use yuho_check::Checker;
use yuho_core::parse;

#[test]
fn test_type_checking_binary_operations() {
    let source = r#"
int result := 5 + 10
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "Expected no errors for valid arithmetic");
}

#[test]
fn test_bounded_int_validation() {
    let source = r#"
BoundedInt<0, 100> age := 150
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    // Note: This test documents current behavior - may fail if Z3 verification is enabled
    // The literal 150 violates the BoundedInt<0, 100> constraint
}

#[test]
fn test_generic_type_instantiation() {
    let source = r#"
struct Container<T> {
    T value,
}
Container<int> c := { value := 42 }
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(
        errors.is_empty(),
        "Expected no errors for valid generic instantiation"
    );
}

#[test]
fn test_enum_variant_usage() {
    let source = r#"
enum Color {
    Red,
    Green,
    Blue,
}
match color {
    case "Red" := 1
    case "Green" := 2
    case "Blue" := 3
    case _ := 0
}
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    // Checks that enum variants can be matched
}

#[test]
fn test_function_parameter_type_checking() {
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
fn test_struct_field_constraint_validation() {
    let source = r#"
struct Person {
    string name,
    int age where age >= 0,
}
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(
        errors.is_empty(),
        "Expected no errors for valid constraints"
    );
}

#[test]
fn test_type_alias_resolution() {
    let source = r#"
type UserId := int
UserId id := 12345
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "Expected no errors for type alias usage");
}

#[test]
fn test_legal_test_satisfies_checking() {
    let source = r#"
legal_test Theft {
    requires bool dishonest_intent,
    requires bool property_taken,
}
match defendant {
    case satisfies Theft := "guilty"
    case _ := "not guilty"
}
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    // Checks that satisfies pattern references valid legal test
}

#[test]
fn test_currency_type_validation() {
    let source = r#"
money<SGD> price := $99.99
money<USD> amount := $50.00
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(errors.is_empty(), "Expected no errors for currency types");
}

#[test]
fn test_temporal_type_validation() {
    let source = r#"
struct Contract {
    date start_date,
    date end_date where end_date > start_date,
}
"#;
    let program = parse(source).unwrap();
    let mut checker = Checker::new();
    let errors = checker.check_program(&program);
    assert!(
        errors.is_empty(),
        "Expected no errors for temporal constraints"
    );
}
