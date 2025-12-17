// Tests for mutually_exclusive enum feature

use yuho_core::ast::*;
use yuho_core::parse;

#[test]
fn test_parse_mutually_exclusive_enum() {
    let source = r#"
        mutually_exclusive enum Verdict {
            Guilty,
            NotGuilty,
        }
    "#;

    let program = parse(source).expect("Failed to parse mutually_exclusive enum");

    assert_eq!(program.items.len(), 1);

    if let Item::Enum(e) = &program.items[0] {
        assert_eq!(e.name, "Verdict");
        assert_eq!(e.variants.len(), 2);
        assert!(
            e.mutually_exclusive,
            "Should be marked as mutually exclusive"
        );
        assert!(e.variants.contains(&"Guilty".to_string()));
        assert!(e.variants.contains(&"NotGuilty".to_string()));
    } else {
        panic!("Expected Enum item");
    }
}

#[test]
fn test_parse_regular_enum_not_exclusive() {
    let source = r#"
        enum Status {
            Active,
            Inactive,
            Pending,
        }
    "#;

    let program = parse(source).expect("Failed to parse regular enum");

    if let Item::Enum(e) = &program.items[0] {
        assert_eq!(e.name, "Status");
        assert!(
            !e.mutually_exclusive,
            "Should NOT be marked as mutually exclusive"
        );
    } else {
        panic!("Expected Enum item");
    }
}

#[test]
fn test_mutually_exclusive_with_multiple_variants() {
    let source = r#"
        mutually_exclusive enum Color {
            Red,
            Green,
            Blue,
            Yellow,
            Purple,
        }
    "#;

    let program = parse(source).expect("Failed to parse");

    if let Item::Enum(e) = &program.items[0] {
        assert_eq!(e.name, "Color");
        assert_eq!(e.variants.len(), 5);
        assert!(e.mutually_exclusive);
    } else {
        panic!("Expected Enum item");
    }
}

#[test]
fn test_mutually_exclusive_in_scope() {
    let source = r#"
        scope criminal_law {
            mutually_exclusive enum Verdict {
                Guilty,
                NotGuilty,
            }
        }
    "#;

    let program = parse(source).expect("Failed to parse scoped enum");

    if let Item::Scope(scope) = &program.items[0] {
        assert_eq!(scope.items.len(), 1);

        if let Item::Enum(e) = &scope.items[0] {
            assert_eq!(e.name, "Verdict");
            assert!(e.mutually_exclusive);
        } else {
            panic!("Expected Enum inside scope");
        }
    } else {
        panic!("Expected Scope item");
    }
}

#[test]
fn test_mutually_exclusive_trailing_comma() {
    let source = r#"
        mutually_exclusive enum Test {
            A,
            B,
        }
    "#;

    let program = parse(source).expect("Failed to parse with trailing comma");

    if let Item::Enum(e) = &program.items[0] {
        assert!(e.mutually_exclusive);
        assert_eq!(e.variants.len(), 2);
    } else {
        panic!("Expected Enum item");
    }
}

#[test]
fn test_mutually_exclusive_no_trailing_comma() {
    let source = r#"
        mutually_exclusive enum Test {
            A,
            B
        }
    "#;

    let program = parse(source).expect("Failed to parse without trailing comma");

    if let Item::Enum(e) = &program.items[0] {
        assert!(e.mutually_exclusive);
        assert_eq!(e.variants.len(), 2);
    } else {
        panic!("Expected Enum item");
    }
}

#[test]
fn test_multiple_enums_mixed_exclusivity() {
    let source = r#"
        mutually_exclusive enum Verdict {
            Guilty,
            NotGuilty,
        }

        enum Priority {
            High,
            Medium,
            Low,
        }

        mutually_exclusive enum Result {
            Pass,
            Fail,
        }
    "#;

    let program = parse(source).expect("Failed to parse multiple enums");

    assert_eq!(program.items.len(), 3);

    // First enum: mutually exclusive
    if let Item::Enum(e) = &program.items[0] {
        assert_eq!(e.name, "Verdict");
        assert!(e.mutually_exclusive);
    }

    // Second enum: NOT mutually exclusive
    if let Item::Enum(e) = &program.items[1] {
        assert_eq!(e.name, "Priority");
        assert!(!e.mutually_exclusive);
    }

    // Third enum: mutually exclusive
    if let Item::Enum(e) = &program.items[2] {
        assert_eq!(e.name, "Result");
        assert!(e.mutually_exclusive);
    }
}
