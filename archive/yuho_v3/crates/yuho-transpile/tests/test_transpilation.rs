use yuho_core::parser::parse;
use yuho_transpile::{to_english, to_json, to_typescript};

#[test]
fn test_typescript_enum_generation() {
    let source = r#"
enum Status {
    Active,
    Inactive,
    Pending,
}
"#;
    let program = parse(source).unwrap();
    let ts_output = to_typescript(&program);

    assert!(ts_output.contains("export type Status"));
    assert!(ts_output.contains("Active"));
    assert!(ts_output.contains("Inactive"));
    assert!(ts_output.contains("Pending"));
}

#[test]
fn test_typescript_generic_struct() {
    let source = r#"
struct Container<T> {
    T value,
}
"#;
    let program = parse(source).unwrap();
    let ts_output = to_typescript(&program);

    assert!(ts_output.contains("interface Container<T>"));
    assert!(ts_output.contains("value: T"));
}

#[test]
fn test_json_export_roundtrip() {
    let source = r#"
struct Person {
    string name,
    int age,
}
"#;
    let program = parse(source).unwrap();
    let json_output = to_json(&program);

    assert!(json_output.contains("Person"));
    assert!(json_output.contains("name"));
    assert!(json_output.contains("age"));
}

#[test]
fn test_english_explanation_struct() {
    let source = r#"
struct Contract {
    string parties,
    money consideration,
}
"#;
    let program = parse(source).unwrap();
    let english = to_english(&program);

    assert!(english.contains("Contract"));
    assert!(english.contains("parties"));
    assert!(english.contains("consideration"));
}

#[test]
fn test_english_explanation_match() {
    let source = r#"
enum Verdict {
    Guilty,
    NotGuilty,
}

string func getOutcome(Verdict v) {
    := match v {
        case Verdict::Guilty := "Convicted"
        case Verdict::NotGuilty := "Acquitted"
    }
}
"#;
    let program = parse(source).unwrap();
    let english = to_english(&program);

    assert!(english.contains("Verdict"));
    assert!(english.contains("Guilty") || english.contains("guilty"));
}

#[test]
fn test_typescript_mutually_exclusive_enum() {
    let source = r#"
@mutually_exclusive
enum PaymentMethod {
    Cash,
    Card,
    Online,
}
"#;
    let program = parse(source).unwrap();
    let ts_output = to_typescript(&program);

    assert!(ts_output.contains("MUTUALLY EXCLUSIVE"));
}
