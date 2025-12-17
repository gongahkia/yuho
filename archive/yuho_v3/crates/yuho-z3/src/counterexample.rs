//! Counterexample generation for principle verification
//!
//! When a principle fails verification, Z3 can generate a concrete counterexample
//! showing why the principle doesn't hold.

use crate::{Z3Error, Z3Result};

/// Counterexample information from Z3
#[derive(Debug, Clone)]
pub struct Counterexample {
    pub variables: Vec<(String, String)>, // (var_name, value)
    pub explanation: String,
}

/// Extract counterexample from Z3 model
pub fn extract_counterexample(model_str: &str) -> Z3Result<Counterexample> {
    // Parse Z3 model string to extract variable assignments
    let mut variables = Vec::new();

    for line in model_str.lines() {
        if let Some((var, val)) = parse_model_line(line) {
            variables.push((var, val));
        }
    }

    let explanation = if variables.is_empty() {
        "No counterexample found (principle may be valid)".to_string()
    } else {
        format!(
            "Found counterexample with {} variable assignments",
            variables.len()
        )
    };

    Ok(Counterexample {
        variables,
        explanation,
    })
}

fn parse_model_line(line: &str) -> Option<(String, String)> {
    // Parse lines like: (define-fun x () Int 42)
    let trimmed = line.trim();

    if !trimmed.starts_with("(define-fun") {
        return None;
    }

    let parts: Vec<&str> = trimmed.split_whitespace().collect();
    if parts.len() >= 5 {
        let var_name = parts[1].to_string();
        let value = parts[4].trim_end_matches(')').to_string();
        Some((var_name, value))
    } else {
        None
    }
}

/// Format counterexample for human readability
pub fn format_counterexample(ce: &Counterexample) -> String {
    let mut output = String::from("Counterexample found:\n");

    for (var, val) in &ce.variables {
        output.push_str(&format!("  {} = {}\n", var, val));
    }

    output.push_str(&format!("\n{}\n", ce.explanation));
    output
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_model() {
        let model = r#"
(define-fun x () Int 42)
(define-fun y () Bool true)
        "#;

        let ce = extract_counterexample(model).unwrap();
        assert_eq!(ce.variables.len(), 2);
        assert_eq!(ce.variables[0].0, "x");
        assert_eq!(ce.variables[0].1, "42");
    }

    #[test]
    fn test_format_counterexample() {
        let ce = Counterexample {
            variables: vec![
                ("x".to_string(), "5".to_string()),
                ("y".to_string(), "false".to_string()),
            ],
            explanation: "Test explanation".to_string(),
        };

        let formatted = format_counterexample(&ce);
        assert!(formatted.contains("x = 5"));
        assert!(formatted.contains("y = false"));
    }
}
