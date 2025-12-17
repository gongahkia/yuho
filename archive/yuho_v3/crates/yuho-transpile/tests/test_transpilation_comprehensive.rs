use yuho_core::parse;
use yuho_transpile::alloy::to_alloy;
use yuho_transpile::english::to_english;
use yuho_transpile::latex::to_latex;
use yuho_transpile::typescript::to_typescript;

#[test]
fn test_transpile_struct_to_typescript() {
    let source = r#"
struct Person {
    string name,
    int age,
}
"#;
    let program = parse(source).unwrap();
    let typescript = to_typescript(&program);
    assert!(
        typescript.contains("interface Person"),
        "Expected TypeScript interface"
    );
    assert!(typescript.contains("name: string"), "Expected name field");
    assert!(typescript.contains("age: number"), "Expected age field");
}

#[test]
fn test_transpile_enum_to_typescript() {
    let source = r#"
enum Status {
    Active,
    Inactive,
    Pending,
}
"#;
    let program = parse(source).unwrap();
    let typescript = to_typescript(&program);
    assert!(
        typescript.contains("enum Status") || typescript.contains("type Status"),
        "Expected TypeScript enum or union type"
    );
}

#[test]
fn test_transpile_to_alloy_signature() {
    let source = r#"
struct Contract {
    string id,
    date start_date,
}
"#;
    let program = parse(source).unwrap();
    let alloy = to_alloy(&program);
    assert!(alloy.contains("sig Contract"), "Expected Alloy signature");
    assert!(
        alloy.contains("id: String") || alloy.contains("id:"),
        "Expected id field"
    );
}

#[test]
fn test_transpile_principle_to_latex() {
    let source = r#"
principle PropertyRights {
    forall property in assets {
        exists owner where owner.has_rights(property)
    }
    citations [
        { text := "Property Act s.47", url := "https://example.com" }
    ]
}
"#;
    let program = parse(source).unwrap();
    let latex = to_latex(&program);
    assert!(
        latex.contains("\\textbf{PropertyRights}") || latex.contains("PropertyRights"),
        "Expected principle name in LaTeX"
    );
    assert!(
        latex.contains("\\forall") || latex.contains("forall"),
        "Expected quantifier in LaTeX"
    );
    assert!(
        latex.contains("cite") || latex.contains("Property Act"),
        "Expected citation in LaTeX"
    );
}

#[test]
fn test_transpile_match_to_typescript() {
    let source = r#"
match status {
    case "active" := true
    case "inactive" := false
    case _ := false
}
"#;
    let program = parse(source).unwrap();
    let typescript = to_typescript(&program);
    assert!(
        typescript.contains("switch") || typescript.contains("if"),
        "Expected switch or if statement"
    );
}

#[test]
fn test_transpile_legal_test_to_english() {
    let source = r#"
legal_test Theft {
    requires bool dishonest_intent,
    requires bool property_taken,
}
"#;
    let program = parse(source).unwrap();
    let english = to_english(&program);
    assert!(
        english.contains("Theft") || english.contains("theft"),
        "Expected legal test name in English"
    );
    assert!(
        english.contains("dishonest") || english.contains("intent"),
        "Expected requirements in English"
    );
}

#[test]
fn test_transpile_gazette_format() {
    let source = r#"
legal_test SectionTest {
    requires bool condition,
    citations [
        { text := "Act s.10(1)(a)", url := "https://example.com" }
    ]
}
"#;
    let program = parse(source).unwrap();
    let latex = to_latex(&program);
    // Check that gazette-style citations are properly formatted
    assert!(
        latex.contains("s.10") || latex.contains("section") || latex.contains("Act"),
        "Expected gazette citation format"
    );
}

#[test]
fn test_transpile_generic_type_to_typescript() {
    let source = r#"
struct Container<T> {
    T value,
}
"#;
    let program = parse(source).unwrap();
    let typescript = to_typescript(&program);
    assert!(
        typescript.contains("<T>") || typescript.contains("generic"),
        "Expected generic type parameter"
    );
}

#[test]
fn test_transpile_bounded_int_to_typescript() {
    let source = r#"
struct Person {
    BoundedInt<0, 150> age,
}
"#;
    let program = parse(source).unwrap();
    let typescript = to_typescript(&program);
    assert!(
        typescript.contains("number") || typescript.contains("age"),
        "Expected TypeScript number type for BoundedInt"
    );
}

#[test]
fn test_transpile_currency_to_typescript() {
    let source = r#"
struct Product {
    money<SGD> price,
}
"#;
    let program = parse(source).unwrap();
    let typescript = to_typescript(&program);
    assert!(
        typescript.contains("number")
            || typescript.contains("price")
            || typescript.contains("Money"),
        "Expected currency type transpilation"
    );
}
