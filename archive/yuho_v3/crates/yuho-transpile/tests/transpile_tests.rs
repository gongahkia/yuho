use yuho_core::parse;
use yuho_transpile::*;

const SAMPLE_STRUCT: &str = r#"
struct Person {
    string name,
    BoundedInt<0, 150> age,
    money<SGD> salary,
}
"#;

const SAMPLE_ENUM: &str = r#"
enum Status {
    Active,
    Inactive,
    Pending,
}
"#;

const SAMPLE_MATCH: &str = r#"
scope decision {
    match value {
        case true := "yes"
        case false := "no"
        case _ := "unknown"
    }
}
"#;

const SAMPLE_FUNCTION: &str = r#"
int func add(int a, int b) {
    := a + b
}
"#;

#[test]
fn test_mermaid_struct_output() {
    let program = parse(SAMPLE_STRUCT).unwrap();
    let output = to_mermaid(&program);

    assert!(output.contains("graph TD"));
    assert!(output.contains("struct Person"));
    assert!(output.contains("name"));
    assert!(output.contains("age"));
    assert!(output.contains("salary"));
}

#[test]
fn test_mermaid_enum_output() {
    let program = parse(SAMPLE_ENUM).unwrap();
    let output = to_mermaid(&program);

    assert!(output.contains("enum Status"));
    assert!(output.contains("Active"));
    assert!(output.contains("Inactive"));
}

#[test]
fn test_mermaid_match_output() {
    let program = parse(SAMPLE_MATCH).unwrap();
    let output = to_mermaid(&program);

    assert!(output.contains("match"));
    assert!(output.contains("true"));
    assert!(output.contains("false"));
}

#[test]
fn test_alloy_struct_output() {
    let program = parse(SAMPLE_STRUCT).unwrap();
    let output = to_alloy(&program);

    assert!(output.contains("sig Person"));
    assert!(output.contains("name:"));
    assert!(output.contains("age:"));
}

#[test]
fn test_alloy_enum_output() {
    let program = parse(SAMPLE_ENUM).unwrap();
    let output = to_alloy(&program);

    assert!(output.contains("abstract sig Status"));
    assert!(output.contains("one sig Active"));
    assert!(output.contains("extends Status"));
}

#[test]
fn test_json_struct_output() {
    let program = parse(SAMPLE_STRUCT).unwrap();
    let output = to_json(&program);

    assert!(output.contains("Person"));
    assert!(output.contains("name"));
    assert!(output.contains("Struct"));
}

#[test]
fn test_json_valid_format() {
    let program = parse(SAMPLE_STRUCT).unwrap();
    let output = to_json(&program);

    // Should be valid JSON
    assert!(serde_json::from_str::<serde_json::Value>(&output).is_ok());
}

#[test]
fn test_latex_struct_output() {
    let program = parse(SAMPLE_STRUCT).unwrap();
    let output = to_latex(&program);

    assert!(output.contains("\\documentclass{article}"));
    assert!(output.contains("\\begin{document}"));
    assert!(output.contains("Person"));
    assert!(output.contains("\\end{document}"));
}

#[test]
fn test_latex_enum_output() {
    let program = parse(SAMPLE_ENUM).unwrap();
    let output = to_latex(&program);

    assert!(output.contains("\\begin{itemize}"));
    assert!(output.contains("Active"));
    assert!(output.contains("\\end{itemize}"));
}

#[test]
fn test_english_struct_output() {
    let program = parse(SAMPLE_STRUCT).unwrap();
    let output = to_english(&program);

    assert!(output.contains("consists of"));
    assert!(output.contains("name"));
    assert!(output.contains("text"));
}

#[test]
fn test_english_match_output() {
    let program = parse(SAMPLE_MATCH).unwrap();
    let output = to_english(&program);

    assert!(output.contains("DECISION"));
    assert!(output.contains("IF"));
    assert!(output.contains("OTHERWISE"));
}

#[test]
fn test_typescript_struct_output() {
    let program = parse(SAMPLE_STRUCT).unwrap();
    let output = to_typescript(&program);

    assert!(output.contains("export interface Person"));
    assert!(output.contains("name: string"));
    assert!(output.contains("age: number"));
}

#[test]
fn test_typescript_enum_output() {
    let program = parse(SAMPLE_ENUM).unwrap();
    let output = to_typescript(&program);

    assert!(output.contains("export type Status"));
    assert!(output.contains("\"Active\""));
    assert!(output.contains("\"Inactive\""));
}

#[test]
fn test_typescript_function_output() {
    let program = parse(SAMPLE_FUNCTION).unwrap();
    let output = to_typescript(&program);

    assert!(output.contains("export function add"));
    assert!(output.contains("a: number"));
    assert!(output.contains("b: number"));
}

#[test]
fn test_all_transpilers_handle_dependent_types() {
    let source = r#"
        struct Contract {
            BoundedInt<1, 100> percentage,
            Positive<money<USD>> amount,
            NonEmpty<Array<string>> parties,
        }
    "#;

    let program = parse(source).unwrap();

    // All transpilers should handle without panicking
    let _ = to_mermaid(&program);
    let _ = to_alloy(&program);
    let _ = to_json(&program);
    let _ = to_latex(&program);
    let _ = to_english(&program);
    let _ = to_typescript(&program);
}

#[test]
fn test_transpilers_empty_program() {
    let program = parse("").unwrap();

    // Should all handle empty programs gracefully
    let mermaid = to_mermaid(&program);
    assert!(mermaid.contains("graph TD"));

    let alloy = to_alloy(&program);
    assert!(alloy.contains("Alloy"));

    let json = to_json(&program);
    assert!(serde_json::from_str::<serde_json::Value>(&json).is_ok());

    let latex = to_latex(&program);
    assert!(latex.contains("\\documentclass"));

    let english = to_english(&program);
    assert!(english.contains("LEGAL SPECIFICATION"));

    let typescript = to_typescript(&program);
    assert!(typescript.contains("TypeScript"));
}

#[test]
fn test_mermaid_unicode_angle_brackets() {
    let source = "BoundedInt<0, 100> age := 25";
    let program = parse(source).unwrap();
    let output = to_mermaid(&program);

    // Should use Unicode angle brackets, not HTML entities
    assert!(output.contains("BoundedInt‹0, 100›"));
    assert!(!output.contains("&lt;"));
    assert!(!output.contains("&gt;"));
}
