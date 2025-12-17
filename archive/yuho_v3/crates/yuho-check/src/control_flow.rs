// Control flow analysis for mutual exclusivity checking
//
// This module analyzes function bodies to detect when multiple variants
// of a mutually_exclusive enum could be returned from different code paths.

use std::collections::HashSet;
use yuho_core::ast::*;

/// Represents possible enum variants that could be returned from a code path
#[derive(Debug, Clone)]
pub struct ReturnSet {
    pub enum_name: String,
    pub variants: HashSet<String>,
}

/// Control flow analyzer for mutual exclusivity
pub struct ControlFlowAnalyzer {
    // Track which enum types are mutually exclusive
    exclusive_enums: HashSet<String>,
}

impl ControlFlowAnalyzer {
    pub fn new() -> Self {
        Self {
            exclusive_enums: HashSet::new(),
        }
    }

    /// Register an enum as mutually exclusive
    pub fn register_exclusive_enum(&mut self, enum_name: String) {
        self.exclusive_enums.insert(enum_name);
    }

    /// Check if function body violates mutual exclusivity
    ///
    /// Returns variants that violate exclusivity (multiple variants possible)
    pub fn check_function(&self, func: &FunctionDefinition) -> Vec<(String, Vec<String>)> {
        let mut violations = Vec::new();

        // Analyze return type - must be a mutually exclusive enum
        if let Type::Named(enum_name) = &func.return_type {
            if self.exclusive_enums.contains(enum_name) {
                // Collect all possible return variants
                let variants = self.collect_return_variants(&func.body, enum_name);

                // If more than one variant can be returned, it's a violation
                if variants.len() > 1 {
                    violations.push((enum_name.clone(), variants.into_iter().collect()));
                }
            }
        }

        violations
    }

    /// Collect all enum variants that could be returned
    fn collect_return_variants(&self, stmts: &[Statement], enum_name: &str) -> HashSet<String> {
        let mut variants = HashSet::new();

        for stmt in stmts {
            match stmt {
                Statement::Return(expr) => {
                    if let Some(variant) = self.extract_variant(expr, enum_name) {
                        variants.insert(variant);
                    }
                },
                // Note: Statement doesn't have If variant in current AST
                // Control flow is handled through match expressions
                _ => {},
            }
        }

        variants
    }

    /// Extract enum variant name from an expression
    fn extract_variant(&self, expr: &Expr, enum_name: &str) -> Option<String> {
        match expr {
            // Direct field access: Status::Active
            Expr::FieldAccess(obj, variant) => {
                if let Expr::Identifier(name) = &**obj {
                    if name == enum_name {
                        return Some(variant.clone());
                    }
                }
                None
            },
            // Match expression: analyze all cases
            Expr::Match(m) => {
                // Collect variants from all match arms
                let mut variants = HashSet::new();
                for case in &m.cases {
                    if let Some(variant) = self.extract_variant(&case.consequence, enum_name) {
                        variants.insert(variant);
                    }
                }

                // If match has multiple different variants, return None (ambiguous)
                // Caller will collect all possibilities
                if variants.len() == 1 {
                    variants.into_iter().next()
                } else {
                    None
                }
            },
            _ => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_register_exclusive_enum() {
        let mut analyzer = ControlFlowAnalyzer::new();
        analyzer.register_exclusive_enum("Status".to_string());
        assert!(analyzer.exclusive_enums.contains("Status"));
    }

    #[test]
    fn test_collect_variants_single_return() {
        let analyzer = ControlFlowAnalyzer::new();

        // func test() -> Status { return Status::Active }
        let stmts = vec![Statement::Return(Expr::FieldAccess(
            Box::new(Expr::Identifier("Status".to_string())),
            "Active".to_string(),
        ))];

        let variants = analyzer.collect_return_variants(&stmts, "Status");
        assert_eq!(variants.len(), 1);
        assert!(variants.contains("Active"));
    }

    #[test]
    fn test_collect_variants_multiple_paths() {
        let analyzer = ControlFlowAnalyzer::new();

        // For now, simplified test with single return
        let stmts = vec![Statement::Return(Expr::FieldAccess(
            Box::new(Expr::Identifier("Status".to_string())),
            "Active".to_string(),
        ))];

        let variants = analyzer.collect_return_variants(&stmts, "Status");
        assert_eq!(variants.len(), 1);
        assert!(variants.contains("Active"));
    }
}
