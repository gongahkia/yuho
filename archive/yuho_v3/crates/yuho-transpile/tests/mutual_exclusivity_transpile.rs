// Transpilation tests for mutually_exclusive enums

use yuho_core::parse;
use yuho_transpile::{to_alloy, to_english, to_json, to_latex, to_mermaid, to_typescript};

#[test]
fn test_typescript_mutually_exclusive() {
    let source = r#"
        mutually_exclusive enum Verdict {
            Guilty,
            NotGuilty,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_typescript(&program);

    assert!(output.contains("export type Verdict"));
    assert!(output.contains("MUTUALLY EXCLUSIVE"));
    assert!(output.contains("Static analysis"));
}

#[test]
fn test_english_mutually_exclusive() {
    let source = r#"
        mutually_exclusive enum Status {
            Active,
            Inactive,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_english(&program);

    assert!(output.contains("Status"));
    assert!(output.contains("MUTUALLY EXCLUSIVE"));
    assert!(output.contains("Only ONE"));
}

#[test]
fn test_alloy_mutually_exclusive() {
    let source = r#"
        mutually_exclusive enum Color {
            Red,
            Green,
            Blue,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_alloy(&program);

    assert!(output.contains("abstract sig Color"));
    assert!(output.contains("fact MutuallyExclusiveColor"));
    assert!(output.contains("disjoint"));
    assert!(output.contains("no (Red & Green)"));
    assert!(output.contains("no (Red & Blue)"));
    assert!(output.contains("no (Green & Blue)"));
}

#[test]
fn test_mermaid_mutually_exclusive() {
    let source = r#"
        mutually_exclusive enum Result {
            Pass,
            Fail,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_mermaid(&program);

    assert!(output.contains("enum Result"));
    assert!(output.contains("[MUTUALLY EXCLUSIVE]"));
}

#[test]
fn test_json_mutually_exclusive() {
    let source = r#"
        mutually_exclusive enum Answer {
            Yes,
            No,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_json(&program);

    assert!(
        output.contains("\"mutually_exclusive\": true") || output.contains("mutually_exclusive")
    );
    assert!(output.contains("Answer"));
}

#[test]
fn test_latex_mutually_exclusive() {
    let source = r#"
        mutually_exclusive enum Decision {
            Approve,
            Reject,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_latex(&program);

    assert!(output.contains("\\textbf{MUTUALLY EXCLUSIVE}"));
    assert!(output.contains("Decision"));
}

#[test]
fn test_regular_enum_no_exclusive_markers() {
    let source = r#"
        enum Priority {
            High,
            Medium,
            Low,
        }
    "#;

    let program = parse(source).expect("Failed to parse");

    let ts = to_typescript(&program);
    let en = to_english(&program);
    let al = to_alloy(&program);
    let mm = to_mermaid(&program);

    // Regular enums should NOT have exclusive markers
    assert!(!ts.contains("MUTUALLY EXCLUSIVE"));
    assert!(!en.contains("MUTUALLY EXCLUSIVE"));
    assert!(!al.contains("MutuallyExclusive"));
    assert!(!mm.contains("[MUTUALLY EXCLUSIVE]"));
}

#[test]
fn test_mixed_enums_transpilation() {
    let source = r#"
        mutually_exclusive enum Verdict {
            Guilty,
            NotGuilty,
        }

        enum Priority {
            High,
            Low,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_typescript(&program);

    // Should have markers for Verdict but not Priority
    assert!(output.contains("// MUTUALLY EXCLUSIVE: Verdict"));
    assert!(!output.contains("// MUTUALLY EXCLUSIVE: Priority"));
}
