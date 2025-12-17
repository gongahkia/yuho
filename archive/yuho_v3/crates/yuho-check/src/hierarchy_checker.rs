/// Statutory Hierarchy Checker
/// Validates legal hierarchies and subordination relationships
use std::collections::HashMap;
use yuho_core::ast::{Annotation, Item, Program};

pub struct HierarchyChecker {
    pub hierarchy_graph: HashMap<String, HierarchyNode>,
}

#[derive(Debug, Clone)]
pub struct HierarchyNode {
    pub name: String,
    pub level: String,
    pub subordinate_to: Option<String>,
    pub children: Vec<String>,
}

impl HierarchyChecker {
    pub fn new() -> Self {
        Self {
            hierarchy_graph: HashMap::new(),
        }
    }

    pub fn check_program(&mut self, program: &Program) {
        for item in &program.items {
            self.visit_item(item);
        }
        self.validate_hierarchy();
    }

    fn visit_item(&mut self, item: &Item) {
        match item {
            Item::Struct(s) => {
                for field in &s.fields {
                    for annotation in &field.annotations {
                        if let Annotation::Hierarchy {
                            level,
                            subordinate_to,
                        } = annotation
                        {
                            let node_name = format!("{}.{}", s.name, field.name);
                            self.hierarchy_graph.insert(
                                node_name.clone(),
                                HierarchyNode {
                                    name: node_name,
                                    level: level.clone(),
                                    subordinate_to: subordinate_to.clone(),
                                    children: Vec::new(),
                                },
                            );
                        }
                    }
                }
            },
            Item::Scope(sc) => {
                for inner in &sc.items {
                    self.visit_item(inner);
                }
            },
            _ => {},
        }
    }

    fn validate_hierarchy(&mut self) {
        // Build parent-child relationships
        let nodes: Vec<_> = self.hierarchy_graph.values().cloned().collect();
        for node in nodes {
            if let Some(parent) = &node.subordinate_to {
                if let Some(parent_node) = self.hierarchy_graph.get_mut(parent) {
                    parent_node.children.push(node.name.clone());
                }
            }
        }
    }

    pub fn check_conflicts(&self) -> Vec<String> {
        let mut errors = Vec::new();
        // Check for circular dependencies
        // Check for invalid subordination
        // Check level consistency
        errors
    }

    pub fn get_hierarchy_levels(&self) -> Vec<(String, usize)> {
        // Return all nodes with their depth in hierarchy
        let mut levels = Vec::new();
        for (name, node) in &self.hierarchy_graph {
            levels.push((name.clone(), self.get_depth(node)));
        }
        levels
    }

    fn get_depth(&self, node: &HierarchyNode) -> usize {
        if let Some(parent) = &node.subordinate_to {
            if let Some(parent_node) = self.hierarchy_graph.get(parent) {
                return 1 + self.get_depth(parent_node);
            }
        }
        0
    }
}

impl Default for HierarchyChecker {
    fn default() -> Self {
        Self::new()
    }
}
