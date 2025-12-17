use yuho_core::ast::*;
use yuho_core::parser::parse;

#[test]
fn test_parse_temporal_type() {
    let source = r#"
struct Contract {
    Temporal<string, valid_from="01-01-2020", valid_until="31-12-2025"> clause,
}
"#;
    let result = parse(source);
    assert!(result.is_ok());

    let program = result.unwrap();
    if let Item::Struct(s) = &program.items[0] {
        assert_eq!(s.name, "Contract");
        if let Type::TemporalValue { .. } = &s.fields[0].ty {
            // Correct temporal type
        } else {
            panic!("Expected TemporalValue type");
        }
    }
}

#[test]
fn test_parse_citation_type() {
    let source = r#"
struct Offense {
    Citation<section="415", subsection="1", act="Penal Code"> statute,
}
"#;
    let result = parse(source);
    assert!(result.is_ok());

    let program = result.unwrap();
    if let Item::Struct(s) = &program.items[0] {
        if let Type::Citation {
            section,
            subsection,
            act,
        } = &s.fields[0].ty
        {
            assert_eq!(section, "415");
            assert_eq!(subsection, "1");
            assert_eq!(act, "Penal Code");
        } else {
            panic!("Expected Citation type");
        }
    }
}

#[test]
fn test_parse_inheritance() {
    let source = r#"
struct DishonestAct {
    bool dishonest_intent,
}

struct Theft extends DishonestAct {
    bool permanent_deprivation,
}
"#;
    let result = parse(source);
    assert!(result.is_ok());

    let program = result.unwrap();
    if let Item::Struct(s) = &program.items[1] {
        assert_eq!(s.name, "Theft");
        assert_eq!(s.extends_from, Some("DishonestAct".to_string()));
    }
}

#[test]
fn test_parse_generic_struct() {
    let source = r#"
struct Container<T> {
    T value,
}
"#;
    let result = parse(source);
    assert!(result.is_ok());

    let program = result.unwrap();
    if let Item::Struct(s) = &program.items[0] {
        assert_eq!(s.type_params, vec!["T".to_string()]);
    }
}

#[test]
fn test_parse_type_alias() {
    let source = r#"
type UserId := int
type Age := BoundedInt<0, 150>
"#;
    let result = parse(source);
    assert!(result.is_ok());

    let program = result.unwrap();
    assert_eq!(program.items.len(), 2);
    assert!(matches!(program.items[0], Item::TypeAlias(_)));
}
