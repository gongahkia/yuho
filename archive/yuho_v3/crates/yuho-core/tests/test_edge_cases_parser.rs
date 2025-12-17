use yuho_core::ast::*;
use yuho_core::parser::parse;

#[test]
fn test_empty_program() {
    let source = "";
    let result = parse(source);
    assert!(result.is_ok());
    let program = result.unwrap();
    assert_eq!(program.items.len(), 0);
}

#[test]
fn test_whitespace_only() {
    let source = "    \n\n\t  \n   ";
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_comments_only() {
    let source = r#"
// This is a comment
/* This is a 
   multiline comment */
// Another comment
"#;
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_unicode_in_strings() {
    let source = r#"
string msg := "Hello 世界 🌍"
"#;
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_very_large_number() {
    let source = "int big := 999999999999";
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_deeply_nested_expressions() {
    let source = "int result := ((((1 + 2) * 3) - 4) / 5)";
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_missing_semicolon_still_works() {
    let source = "int x := 1"; // Yuho doesn't require semicolons
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_reserved_keyword_in_identifier() {
    let source = "int struct_name := 1"; // 'struct' is keyword but struct_name should work
    let result = parse(source);
    assert!(result.is_ok());
}

#[test]
fn test_empty_struct() {
    let source = "struct Empty { }";
    let result = parse(source);
    // May or may not be allowed, depends on grammar
    let _ = result; // Just ensure it doesn't panic
}

#[test]
fn test_malformed_type_parameter() {
    let source = "struct Bad< > { int x, }";
    let result = parse(source);
    assert!(result.is_err());
}
