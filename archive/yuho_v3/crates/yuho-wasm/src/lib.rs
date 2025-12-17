//! WASM bindings for Yuho
//!
//! This crate provides WebAssembly bindings for the Yuho language,
//! allowing it to run in web browsers and other WASM environments.

use wasm_bindgen::prelude::*;

/// Maximum allowed source code size (1MB)
const MAX_SOURCE_SIZE: usize = 1_000_000;

/// Maximum allowed line count
const MAX_LINE_COUNT: usize = 10_000;

/// Validate input size and content
fn validate_input(source: &str) -> Result<(), String> {
    // Check total size
    if source.len() > MAX_SOURCE_SIZE {
        return Err(format!(
            "Input too large: {} bytes (max: {} bytes)",
            source.len(),
            MAX_SOURCE_SIZE
        ));
    }

    // Check line count
    let line_count = source.lines().count();
    if line_count > MAX_LINE_COUNT {
        return Err(format!(
            "Too many lines: {} (max: {})",
            line_count, MAX_LINE_COUNT
        ));
    }

    // Ensure valid UTF-8 (already guaranteed by &str, but document it)
    // No null bytes (would be weird in source code)
    if source.contains('\0') {
        return Err("Input contains null bytes".to_string());
    }

    Ok(())
}

/// Parse Yuho source code and return JSON AST
#[wasm_bindgen]
pub fn parse(source: &str) -> Result<String, String> {
    // Validate input first
    validate_input(source)?;

    match yuho_core::parse(source) {
        Ok(program) => {
            serde_json::to_string(&program).map_err(|e| format!("Serialization error: {}", e))
        },
        Err(e) => Err(format!("Parse error: {}", e)),
    }
}

/// Check Yuho source for semantic errors
/// Returns JSON array of error messages
#[wasm_bindgen]
pub fn check(source: &str) -> Result<String, String> {
    validate_input(source)?;

    let program = yuho_core::parse(source).map_err(|e| format!("Parse error: {}", e))?;

    let mut checker = yuho_check::Checker::new();
    let errors = checker.check_program(&program);

    // Convert errors to strings since CheckError doesn't impl Serialize
    let error_strings: Vec<String> = errors.iter().map(|e| e.to_string()).collect();

    serde_json::to_string(&error_strings).map_err(|e| format!("Serialization error: {}", e))
}

/// Transpile Yuho to Mermaid diagram
#[wasm_bindgen]
pub fn to_mermaid(source: &str) -> Result<String, String> {
    validate_input(source)?;

    let program = yuho_core::parse(source).map_err(|e| format!("Parse error: {}", e))?;

    Ok(yuho_transpile::to_mermaid(&program))
}

/// Transpile Yuho to Alloy specification
#[wasm_bindgen]
pub fn to_alloy(source: &str) -> Result<String, String> {
    validate_input(source)?;

    let program = yuho_core::parse(source).map_err(|e| format!("Parse error: {}", e))?;

    Ok(yuho_transpile::to_alloy(&program))
}

/// Transpile Yuho to JSON
#[wasm_bindgen]
pub fn to_json(source: &str) -> Result<String, String> {
    validate_input(source)?;

    let program = yuho_core::parse(source).map_err(|e| format!("Parse error: {}", e))?;

    Ok(yuho_transpile::to_json(&program))
}

/// Transpile Yuho to LaTeX
#[wasm_bindgen]
pub fn to_latex(source: &str) -> Result<String, String> {
    validate_input(source)?;

    let program = yuho_core::parse(source).map_err(|e| format!("Parse error: {}", e))?;

    Ok(yuho_transpile::to_latex(&program))
}

/// Transpile Yuho to natural English
#[wasm_bindgen]
pub fn to_english(source: &str) -> Result<String, String> {
    validate_input(source)?;

    let program = yuho_core::parse(source).map_err(|e| format!("Parse error: {}", e))?;

    Ok(yuho_transpile::to_english(&program))
}

/// Transpile Yuho to TypeScript type definitions
#[wasm_bindgen]
pub fn to_typescript(source: &str) -> Result<String, String> {
    validate_input(source)?;

    let program = yuho_core::parse(source).map_err(|e| format!("Parse error: {}", e))?;

    Ok(yuho_transpile::to_typescript(&program))
}

/// Get version information
#[wasm_bindgen]
pub fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use wasm_bindgen_test::*;

    #[wasm_bindgen_test]
    fn test_parse_valid() {
        let source = "int x := 42";
        assert!(parse(source).is_ok());
    }

    #[wasm_bindgen_test]
    fn test_parse_invalid() {
        let source = "invalid syntax!!!";
        assert!(parse(source).is_err());
    }

    #[wasm_bindgen_test]
    fn test_version() {
        assert!(!version().is_empty());
    }

    #[wasm_bindgen_test]
    fn test_to_mermaid() {
        let source = "int x := 42";
        assert!(to_mermaid(source).is_ok());
    }

    #[wasm_bindgen_test]
    fn test_input_too_large() {
        let large_source = "x".repeat(MAX_SOURCE_SIZE + 1);
        let result = parse(&large_source);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("too large"));
    }

    #[wasm_bindgen_test]
    fn test_too_many_lines() {
        let many_lines = "int x := 1\n".repeat(MAX_LINE_COUNT + 1);
        let result = parse(&many_lines);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Too many lines"));
    }

    #[wasm_bindgen_test]
    fn test_null_bytes_rejected() {
        let source_with_null = "int x := 42\0";
        let result = parse(source_with_null);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("null bytes"));
    }

    #[wasm_bindgen_test]
    fn test_valid_large_input() {
        // Test that we can handle files up to the limit
        let valid_large = "int x := 1\n".repeat(5000);
        let result = parse(&valid_large);
        // May fail parsing but shouldn't fail validation
        assert!(!result.unwrap_err().contains("too large"));
    }
}
