use yuho_core::ast::*;
use yuho_core::parser::parse;

#[test]
fn test_parse_type_alias_simple() {
    let source = "type UserId := int";
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();
    assert_eq!(program.items.len(), 1);

    if let Item::TypeAlias(alias) = &program.items[0] {
        assert_eq!(alias.name, "UserId");
        assert_eq!(alias.target, Type::Int);
    } else {
        panic!("Expected TypeAlias");
    }
}

#[test]
fn test_parse_type_alias_generic() {
    let source = "type Result<T, E> := T";
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();

    if let Item::TypeAlias(alias) = &program.items[0] {
        assert_eq!(alias.name, "Result");
        assert_eq!(alias.type_params.len(), 2);
        assert!(alias.type_params.contains(&"T".to_string()));
        assert!(alias.type_params.contains(&"E".to_string()));
    } else {
        panic!("Expected TypeAlias");
    }
}

#[test]
fn test_parse_struct_with_constraints() {
    let source = r#"
struct Person {
    string name,
    BoundedInt<0, 150> age where age >= 18,
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();

    if let Item::Struct(s) = &program.items[0] {
        assert_eq!(s.fields.len(), 2);
        assert_eq!(s.fields[1].name, "age");
        assert!(!s.fields[1].constraints.is_empty());
    } else {
        panic!("Expected Struct");
    }
}

#[test]
fn test_parse_struct_inheritance() {
    let source = r#"
struct Employee extends Person {
    string job_title,
    money<SGD> salary,
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();

    if let Item::Struct(s) = &program.items[0] {
        assert_eq!(s.name, "Employee");
        assert_eq!(s.extends_from, Some("Person".to_string()));
        assert_eq!(s.fields.len(), 2);
    } else {
        panic!("Expected Struct");
    }
}

#[test]
fn test_parse_enum_with_mutually_exclusive() {
    let source = r#"
@mutually_exclusive
enum Status {
    Active,
    Inactive,
    Pending,
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();

    if let Item::Enum(e) = &program.items[0] {
        assert_eq!(e.name, "Status");
        assert!(e.mutually_exclusive);
        assert_eq!(e.variants.len(), 3);
    } else {
        panic!("Expected Enum");
    }
}

#[test]
fn test_parse_function_with_generics() {
    let source = r#"
T func identity<T>(T value) {
    := value
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();

    if let Item::Function(f) = &program.items[0] {
        assert_eq!(f.name, "identity");
        assert_eq!(f.type_params.len(), 1);
        assert_eq!(f.type_params[0], "T");
    } else {
        panic!("Expected Function");
    }
}

#[test]
fn test_parse_match_with_guards() {
    let source = r#"
match age {
    case x where x >= 18 := "adult"
    case _ := "minor"
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_parse_legal_test_definition() {
    let source = r#"
legal_test Theft {
    requires bool dishonest_intent,
    requires bool property_taken,
    requires bool without_consent,
}
"#;
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();

    if let Item::LegalTest(lt) = &program.items[0] {
        assert_eq!(lt.name, "Theft");
        assert_eq!(lt.requirements.len(), 3);
    } else {
        panic!("Expected LegalTest");
    }
}
