// Transpilation tests for legal_test feature

use yuho_core::parse;
use yuho_transpile::{to_alloy, to_english, to_json, to_latex, to_mermaid, to_typescript};

#[test]
fn test_typescript_transpile_legal_test() {
    let source = r#"
        legal_test Cheating {
            requires deception: bool,
            requires dishonest_intent: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_typescript(&program);

    // Should generate interface
    assert!(output.contains("export interface CheatingTest"));
    assert!(output.contains("deception: boolean"));
    assert!(output.contains("dishonest_intent: boolean"));

    // Should generate validation function
    assert!(output.contains("export function satisfiesCheatingTest"));
    assert!(output.contains("return"));
    assert!(output.contains("values.deception && values.dishonest_intent"));
}

#[test]
fn test_english_transpile_legal_test() {
    let source = r#"
        legal_test Theft {
            requires taking: bool,
            requires dishonest_intent: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_english(&program);

    assert!(output.contains("LEGAL TEST"));
    assert!(output.contains("Theft"));
    assert!(output.contains("ALL"));
    assert!(output.contains("taking"));
    assert!(output.contains("dishonest_intent"));
    assert!(output.contains("satisfied"));
}

#[test]
fn test_alloy_transpile_legal_test() {
    let source = r#"
        legal_test Murder {
            requires killing: bool,
            requires malice: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_alloy(&program);

    // Should generate predicate
    assert!(output.contains("pred Murder"));
    assert!(output.contains("killing: Bool"));
    assert!(output.contains("malice: Bool"));
    assert!(output.contains("and"));
}

#[test]
fn test_mermaid_transpile_legal_test() {
    let source = r#"
        legal_test Test {
            requires a: bool,
            requires b: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_mermaid(&program);

    assert!(output.contains("graph TD"));
    assert!(output.contains("legal_test Test"));
    assert!(output.contains("a: Bool"));
    assert!(output.contains("b: Bool"));
}

#[test]
fn test_json_transpile_legal_test() {
    let source = r#"
        legal_test Fraud {
            requires deception: bool,
            requires benefit: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_json(&program);

    assert!(output.contains("legal_test") || output.contains("LegalTest"));
    assert!(output.contains("Fraud"));
    assert!(output.contains("deception"));
    assert!(output.contains("benefit"));
}

#[test]
fn test_latex_transpile_legal_test() {
    let source = r#"
        legal_test Contract {
            requires offer: bool,
            requires acceptance: bool,
            requires consideration: bool,
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_latex(&program);

    assert!(output.contains("\\documentclass"));
    assert!(output.contains("Legal Test"));
    assert!(output.contains("Contract"));
    assert!(output.contains("offer"));
    assert!(output.contains("acceptance"));
    assert!(output.contains("consideration"));
    assert!(output.contains("\\textbf{All}") || output.contains("All"));
}

#[test]
fn test_typescript_satisfies_pattern() {
    let source = r#"
        legal_test Test {
            requires a: bool,
        }

        string result := match case {
            case satisfies Test := "pass"
            case _ := "fail"
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_typescript(&program);

    // Should reference the satisfies function
    assert!(output.contains("satisfiesTestTest(value)") || output.contains("satisfiesTest"));
}

#[test]
fn test_english_satisfies_pattern() {
    let source = r#"
        legal_test Offense {
            requires element: bool,
        }

        string verdict := match case {
            case satisfies Offense := "guilty"
            case _ := "not guilty"
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_english(&program);

    assert!(output.contains("Offense"));
    assert!(output.contains("satisfied") || output.contains("requirements"));
}

#[test]
fn test_transpile_empty_legal_test() {
    let source = r#"
        legal_test Empty {
        }
    "#;

    let program = parse(source).expect("Failed to parse");

    // All transpilers should handle empty legal tests gracefully
    let ts = to_typescript(&program);
    let en = to_english(&program);
    let al = to_alloy(&program);
    let mm = to_mermaid(&program);

    assert!(!ts.is_empty());
    assert!(!en.is_empty());
    assert!(!al.is_empty());
    assert!(!mm.is_empty());
}

#[test]
fn test_transpile_legal_test_in_scope() {
    let source = r#"
        scope criminal {
            legal_test Burglary {
                requires breaking: bool,
                requires entering: bool,
                requires intent: bool,
            }
        }
    "#;

    let program = parse(source).expect("Failed to parse");
    let output = to_typescript(&program);

    // Should be in namespace
    assert!(output.contains("namespace criminal") || output.contains("Burglary"));
}
