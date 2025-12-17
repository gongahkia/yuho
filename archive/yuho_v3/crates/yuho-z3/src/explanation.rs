//! Explanation generation for Z3 verification results
//!
//! This module provides functionality to generate human-readable explanations
//! for why a condition is SAT or UNSAT, including execution traces and
//! natural language descriptions.

use std::collections::HashMap;
use yuho_core::ast::*;

/// Execution trace for tracking decision points
#[derive(Debug, Clone)]
pub struct ExecutionTrace {
    pub steps: Vec<TraceStep>,
    pub coverage: Coverage,
}

/// Individual step in an execution trace
#[derive(Debug, Clone)]
pub struct TraceStep {
    pub expression: String,
    pub result: StepResult,
    pub line: Option<usize>,
    pub description: String,
}

/// Result of evaluating a trace step
#[derive(Debug, Clone)]
pub enum StepResult {
    Satisfied,
    Unsatisfied,
    Unknown,
}

/// Coverage information for branch analysis
#[derive(Debug, Clone)]
pub struct Coverage {
    pub total_branches: usize,
    pub covered_branches: usize,
    pub uncovered_branches: Vec<String>,
}

/// Natural language explanation generator
pub struct ExplanationGenerator {
    variables: HashMap<String, String>,
}

impl ExplanationGenerator {
    pub fn new() -> Self {
        Self {
            variables: HashMap::new(),
        }
    }

    /// Generate a "why" explanation for SAT results
    pub fn explain_why_sat(&self, expr: &Expr, model: &str) -> String {
        let mut explanation = String::from("The condition is satisfiable because:\n\n");

        explanation.push_str(&format!("Expression: {}\n\n", self.format_expr(expr)));
        explanation.push_str(&format!("Model found:\n{}\n\n", model));
        explanation.push_str(&self.generate_reasoning(expr, true));

        explanation
    }

    /// Generate a "why not" explanation for UNSAT results
    pub fn explain_why_not_sat(&self, expr: &Expr) -> String {
        let mut explanation = String::from("The condition is unsatisfiable because:\n\n");

        explanation.push_str(&format!("Expression: {}\n\n", self.format_expr(expr)));
        explanation.push_str(&self.generate_reasoning(expr, false));
        explanation.push_str("\nNo assignment of variables can make this condition true.");

        explanation
    }

    /// Generate detailed reasoning for an expression
    fn generate_reasoning(&self, expr: &Expr, is_sat: bool) -> String {
        match expr {
            Expr::Binary(left, op, right) => {
                let op_str = self.format_binop(op);
                let left_str = self.format_expr(left);
                let right_str = self.format_expr(right);

                if is_sat {
                    format!(
                        "- {} {} {} evaluates to true\n",
                        left_str, op_str, right_str
                    )
                } else {
                    format!(
                        "- {} {} {} cannot be satisfied\n",
                        left_str, op_str, right_str
                    )
                }
            },
            Expr::Literal(lit) => {
                format!("- Literal value: {}\n", self.format_literal(lit))
            },
            Expr::Identifier(name) => {
                format!("- Variable: {}\n", name)
            },
            _ => String::from("- Complex expression\n"),
        }
    }

    /// Format an expression as a string
    fn format_expr(&self, expr: &Expr) -> String {
        match expr {
            Expr::Literal(lit) => self.format_literal(lit),
            Expr::Identifier(name) => name.clone(),
            Expr::Binary(left, op, right) => {
                format!(
                    "({} {} {})",
                    self.format_expr(left),
                    self.format_binop(op),
                    self.format_expr(right)
                )
            },
            Expr::Unary(op, expr) => {
                format!("({}{})", self.format_unop(op), self.format_expr(expr))
            },
            _ => String::from("..."),
        }
    }

    /// Format a literal value
    fn format_literal(&self, lit: &Literal) -> String {
        match lit {
            Literal::Int(n) => n.to_string(),
            Literal::Float(f) => f.to_string(),
            Literal::Bool(b) => b.to_string(),
            Literal::String(s) => format!("\"{}\"", s),
            Literal::Money(m) => format!("${:.2}", m),
            Literal::Date(d) => d.clone(),
            Literal::Duration(d) => d.clone(),
            Literal::Percent(p) => format!("{}%", p * 100.0),
            Literal::Pass => "pass".to_string(),
        }
    }

    /// Format a binary operator
    fn format_binop(&self, op: &BinaryOp) -> &'static str {
        match op {
            BinaryOp::Add => "+",
            BinaryOp::Sub => "-",
            BinaryOp::Mul => "*",
            BinaryOp::Div => "/",
            BinaryOp::Mod => "%",
            BinaryOp::Eq => "==",
            BinaryOp::Neq => "!=",
            BinaryOp::Lt => "<",
            BinaryOp::Gt => ">",
            BinaryOp::Lte => "<=",
            BinaryOp::Gte => ">=",
            BinaryOp::And => "&&",
            BinaryOp::Or => "||",
        }
    }

    /// Format a unary operator
    fn format_unop(&self, op: &UnaryOp) -> &'static str {
        match op {
            UnaryOp::Not => "!",
            UnaryOp::Neg => "-",
        }
    }

    /// Generate an execution trace for an expression
    pub fn trace_execution(&self, expr: &Expr) -> ExecutionTrace {
        let mut steps = Vec::new();
        self.trace_expr(expr, &mut steps, 0);

        let coverage = Coverage {
            total_branches: steps.len(),
            covered_branches: steps
                .iter()
                .filter(|s| matches!(s.result, StepResult::Satisfied))
                .count(),
            uncovered_branches: steps
                .iter()
                .filter(|s| matches!(s.result, StepResult::Unsatisfied))
                .map(|s| s.expression.clone())
                .collect(),
        };

        ExecutionTrace { steps, coverage }
    }

    /// Recursively trace expression evaluation
    fn trace_expr(&self, expr: &Expr, steps: &mut Vec<TraceStep>, depth: usize) {
        let indent = "  ".repeat(depth);

        match expr {
            Expr::Binary(left, op, right) => {
                let description = format!(
                    "{}Evaluating: {} {} {}",
                    indent,
                    self.format_expr(left),
                    self.format_binop(op),
                    self.format_expr(right)
                );

                steps.push(TraceStep {
                    expression: self.format_expr(expr),
                    result: StepResult::Unknown,
                    line: None,
                    description,
                });

                // Trace sub-expressions
                self.trace_expr(left, steps, depth + 1);
                self.trace_expr(right, steps, depth + 1);
            },
            Expr::Literal(_) => {
                let description = format!("{}Literal: {}", indent, self.format_expr(expr));
                steps.push(TraceStep {
                    expression: self.format_expr(expr),
                    result: StepResult::Satisfied,
                    line: None,
                    description,
                });
            },
            Expr::Identifier(name) => {
                let description = format!("{}Variable: {}", indent, name);
                steps.push(TraceStep {
                    expression: name.clone(),
                    result: StepResult::Unknown,
                    line: None,
                    description,
                });
            },
            _ => {},
        }
    }

    /// Generate minimal explanation by removing redundant steps
    pub fn minimize_explanation(&self, trace: &ExecutionTrace) -> ExecutionTrace {
        // Filter out redundant or trivial steps
        let essential_steps: Vec<TraceStep> = trace
            .steps
            .iter()
            .filter(|step| !step.description.contains("Literal:"))
            .cloned()
            .collect();

        ExecutionTrace {
            steps: essential_steps,
            coverage: trace.coverage.clone(),
        }
    }

    /// Format trace as human-readable text
    pub fn format_trace(&self, trace: &ExecutionTrace) -> String {
        let mut output = String::from("Execution Trace:\n");
        output.push_str(&"=".repeat(50));
        output.push('\n');

        for (i, step) in trace.steps.iter().enumerate() {
            output.push_str(&format!("{}. {}\n", i + 1, step.description));
        }

        output.push('\n');
        output.push_str(&format!(
            "Coverage: {}/{} branches covered\n",
            trace.coverage.covered_branches, trace.coverage.total_branches
        ));

        if !trace.coverage.uncovered_branches.is_empty() {
            output.push_str("\nUncovered branches:\n");
            for branch in &trace.coverage.uncovered_branches {
                output.push_str(&format!("  - {}\n", branch));
            }
        }

        output
    }
}

impl Default for ExplanationGenerator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_expr() {
        let gen = ExplanationGenerator::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Int(5))),
            BinaryOp::Gt,
            Box::new(Expr::Literal(Literal::Int(3))),
        );

        let formatted = gen.format_expr(&expr);
        assert!(formatted.contains("5"));
        assert!(formatted.contains("3"));
        assert!(formatted.contains(">"));
    }

    #[test]
    fn test_trace_execution() {
        let gen = ExplanationGenerator::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Int(2))),
            BinaryOp::Add,
            Box::new(Expr::Literal(Literal::Int(3))),
        );

        let trace = gen.trace_execution(&expr);
        assert!(!trace.steps.is_empty());
    }

    #[test]
    fn test_explain_why_sat() {
        let gen = ExplanationGenerator::new();
        let expr = Expr::Literal(Literal::Bool(true));
        let explanation = gen.explain_why_sat(&expr, "model: x = 5");

        assert!(explanation.contains("satisfiable"));
        assert!(explanation.contains("model"));
    }

    #[test]
    fn test_minimize_explanation() {
        let gen = ExplanationGenerator::new();
        let expr = Expr::Binary(
            Box::new(Expr::Literal(Literal::Int(2))),
            BinaryOp::Add,
            Box::new(Expr::Literal(Literal::Int(3))),
        );

        let trace = gen.trace_execution(&expr);
        let minimized = gen.minimize_explanation(&trace);

        // Minimized trace should have fewer steps (literals removed)
        assert!(minimized.steps.len() <= trace.steps.len());
    }
}
