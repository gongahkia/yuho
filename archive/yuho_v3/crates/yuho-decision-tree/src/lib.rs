//! Decision Tree Visualization for Yuho
//!
//! Extracts decision logic from match expressions and generates
//! interactive visualizations using HTML/D3.js.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use thiserror::Error;
use yuho_core::ast::{Expr, MatchCase, Pattern, Program};

#[derive(Error, Debug)]
pub enum DecisionTreeError {
    #[error("No match expressions found in program")]
    NoMatchExpressions,
    #[error("Invalid tree structure: {0}")]
    InvalidStructure(String),
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, DecisionTreeError>;

/// A node in the decision tree
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionNode {
    pub id: String,
    pub label: String,
    pub node_type: NodeType,
    pub children: Vec<DecisionNode>,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum NodeType {
    /// Root of the decision tree
    Root,
    /// Decision point (match condition)
    Decision,
    /// Outcome/action (case body)
    Action,
    /// Wildcard catch-all
    Default,
}

/// Decision tree builder
pub struct DecisionTreeBuilder {
    trees: Vec<DecisionNode>,
    node_counter: usize,
}

impl DecisionTreeBuilder {
    pub fn new() -> Self {
        Self {
            trees: Vec::new(),
            node_counter: 0,
        }
    }

    fn next_id(&mut self) -> String {
        let id = format!("node_{}", self.node_counter);
        self.node_counter += 1;
        id
    }

    /// Extract decision trees from a program
    pub fn extract_from_program(&mut self, program: &Program) -> Result<Vec<DecisionNode>> {
        for item in &program.items {
            self.visit_item(item);
        }

        if self.trees.is_empty() {
            Err(DecisionTreeError::NoMatchExpressions)
        } else {
            Ok(self.trees.clone())
        }
    }

    fn visit_item(&mut self, item: &yuho_core::ast::Item) {
        use yuho_core::ast::{Item, Statement};
        match item {
            Item::Function(f) => {
                // Traverse function body for match expressions
                for stmt in &f.body {
                    match stmt {
                        Statement::Match(match_expr) => {
                            let tree =
                                self.build_match_tree(&match_expr.scrutinee, &match_expr.cases);
                            self.trees.push(tree);
                        },
                        Statement::Return(expr)
                        | Statement::Declaration(yuho_core::ast::Declaration {
                            value: expr, ..
                        }) => {
                            self.visit_expr(expr);
                        },
                        _ => {},
                    }
                }
            },
            Item::Scope(s) => {
                for inner in &s.items {
                    self.visit_item(inner);
                }
            },
            Item::Declaration(decl) => {
                self.visit_expr(&decl.value);
            },
            _ => {},
        }
    }

    fn visit_expr(&mut self, expr: &Expr) {
        match expr {
            Expr::Match(match_expr) => {
                let tree = self.build_match_tree(&match_expr.scrutinee, &match_expr.cases);
                self.trees.push(tree);
            },
            _ => {},
        }
    }

    fn build_match_tree(&mut self, scrutinee: &Expr, cases: &[MatchCase]) -> DecisionNode {
        let root_id = self.next_id();
        let scrutinee_label = format!("Match: {}", self.expr_to_string(scrutinee));

        let mut children = Vec::new();
        for case in cases {
            let case_node = self.build_case_node(case);
            children.push(case_node);
        }

        DecisionNode {
            id: root_id,
            label: scrutinee_label,
            node_type: NodeType::Root,
            children,
            metadata: HashMap::new(),
        }
    }

    fn build_case_node(&mut self, case: &MatchCase) -> DecisionNode {
        let node_id = self.next_id();
        let pattern_label = self.pattern_to_string(&case.pattern);

        let node_type = if matches!(case.pattern, Pattern::Wildcard) {
            NodeType::Default
        } else {
            NodeType::Decision
        };

        let mut metadata = HashMap::new();
        if let Some(guard) = &case.guard {
            metadata.insert("guard".to_string(), self.expr_to_string(guard));
        }

        let action_child = DecisionNode {
            id: self.next_id(),
            label: self.expr_to_string(&case.consequence),
            node_type: NodeType::Action,
            children: Vec::new(),
            metadata: HashMap::new(),
        };

        DecisionNode {
            id: node_id,
            label: pattern_label,
            node_type,
            children: vec![action_child],
            metadata,
        }
    }

    fn expr_to_string(&self, expr: &Expr) -> String {
        match expr {
            Expr::Literal(lit) => format!("{:?}", lit),
            Expr::Identifier(id) => id.clone(),
            Expr::FieldAccess(object, field) => {
                format!("{}.{}", self.expr_to_string(object), field)
            },
            Expr::Binary(left, op, right) => {
                format!(
                    "{} {:?} {}",
                    self.expr_to_string(left),
                    op,
                    self.expr_to_string(right)
                )
            },
            Expr::Call(name, _) => format!("{}()", name),
            _ => "<expr>".to_string(),
        }
    }

    fn pattern_to_string(&self, pattern: &Pattern) -> String {
        match pattern {
            Pattern::Literal(lit) => format!("{:?}", lit),
            Pattern::Identifier(id) => id.clone(),
            Pattern::Wildcard => "_".to_string(),
            Pattern::Satisfies(_) => "<satisfies>".to_string(),
        }
    }
}

impl Default for DecisionTreeBuilder {
    fn default() -> Self {
        Self::new()
    }
}

/// Generate HTML visualization
pub fn generate_html(trees: &[DecisionNode]) -> Result<String> {
    let json_data = serde_json::to_string_pretty(trees)?;

    // Use include_str! with external HTML template would be better,
    // but for now we inline a simple HTML template
    let html = include_str!("template.html").replace("{{TREE_DATA}}", &json_data);

    Ok(html)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decision_node_creation() {
        let node = DecisionNode {
            id: "node_0".to_string(),
            label: "Test Node".to_string(),
            node_type: NodeType::Root,
            children: Vec::new(),
            metadata: HashMap::new(),
        };
        assert_eq!(node.id, "node_0");
        assert_eq!(node.node_type, NodeType::Root);
    }

    #[test]
    fn test_builder_initialization() {
        let builder = DecisionTreeBuilder::new();
        assert_eq!(builder.trees.len(), 0);
        assert_eq!(builder.node_counter, 0);
    }
}
