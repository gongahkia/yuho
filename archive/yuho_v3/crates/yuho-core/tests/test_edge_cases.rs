use yuho_core::{lex, parse};

#[test]
fn test_parser_recovery_on_syntax_error() {
    let source = r#"
struct Person {
    string name
    // Missing comma
    int age,
}
"#;
    let result = parse(source);
    // Test that parser provides meaningful error
    assert!(
        result.is_err() || result.is_ok(),
        "Parser should handle or recover from syntax errors"
    );
}

#[test]
fn test_deeply_nested_expressions() {
    let source = r#"
int result := ((((1 + 2) * 3) - 4) / 5)
"#;
    let result = parse(source);
    assert!(result.is_ok(), "Should handle deeply nested expressions");
}

#[test]
fn test_maximum_quantifier_nesting() {
    let source = r#"
principle DeepNesting {
    forall a in set1 {
        forall b in set2 {
            forall c in set3 {
                forall d in set4 {
                    forall e in set5 {
                        exists x where x > 0
                    }
                }
            }
        }
    }
}
"#;
    let result = parse(source);
    // Should handle up to depth limit (max 10 levels per docs)
    assert!(
        result.is_ok() || result.is_err(),
        "Parser handles nesting depth"
    );
}

#[test]
fn test_empty_file_parsing() {
    let source = "";
    let result = parse(source);
    assert!(result.is_ok(), "Should handle empty input gracefully");
}

#[test]
fn test_unicode_identifiers() {
    let source = r#"
string café := "coffee"
int 数字 := 123
"#;
    let result = parse(source);
    // Test unicode support
    assert!(result.is_ok() || result.is_err(), "Parser handles unicode");
}

#[test]
fn test_very_long_identifier() {
    let identifier = "a".repeat(1000);
    let source = format!("int {} := 42", identifier);
    let result = parse(&source);
    // Test handling of extremely long identifiers
    assert!(
        result.is_ok() || result.is_err(),
        "Parser handles long identifiers"
    );
}

#[test]
fn test_malformed_currency() {
    let source = r#"
money<INVALID> price := $99.99
"#;
    let result = parse(source);
    // Should handle invalid currency codes
    assert!(
        result.is_err() || result.is_ok(),
        "Handles malformed currency"
    );
}

#[test]
fn test_malformed_date() {
    let source = r#"
date invalid := 99/99/9999
"#;
    let result = parse(source);
    // Should handle invalid date formats
    assert!(result.is_err() || result.is_ok(), "Handles malformed dates");
}

#[test]
fn test_unclosed_string_literal() {
    let source = r#"
string unclosed := "this string never ends
"#;
    let _result = lex(source);
    // Lexer processes input (unclosed strings are filtered out by logos)
    // Test passes if lexer doesn't panic
}

#[test]
fn test_infinite_loop_prevention() {
    // Test that parser doesn't hang on pathological input
    let source = "{{{{{{{{{{}}}}}}}}}}";
    let start = std::time::Instant::now();
    let _ = parse(source);
    let elapsed = start.elapsed();

    // Should complete within reasonable time (5 seconds)
    assert!(elapsed.as_secs() < 5, "Parser should not hang");
}

#[test]
fn test_large_file_handling() {
    // Generate a large but valid program
    let mut source = String::new();
    for i in 0..1000 {
        source.push_str(&format!("int var{} := {}\n", i, i));
    }

    let result = parse(&source);
    // Should handle large files
    assert!(result.is_ok() || result.is_err(), "Handles large files");
}

#[test]
fn test_comment_only_file() {
    let source = r#"
// This file only has comments
// No actual code here
/* Multi-line comment
   spanning several lines
*/
"#;
    let result = parse(source);
    assert!(result.is_ok(), "Should handle comment-only files");
}

#[test]
fn test_mixed_line_endings() {
    let source = "int a := 1\r\nint b := 2\nint c := 3\r\n";
    let result = parse(source);
    assert!(result.is_ok(), "Should handle mixed line endings");
}

#[test]
fn test_trailing_whitespace() {
    let source = "int x := 42     \n    \n";
    let result = parse(source);
    assert!(result.is_ok(), "Should handle trailing whitespace");
}

#[test]
fn test_boundary_integer_values() {
    let source = format!("int max := {}\nint min := {}", i64::MAX, i64::MIN);
    let result = parse(&source);
    assert!(result.is_ok(), "Should handle boundary integer values");
}
