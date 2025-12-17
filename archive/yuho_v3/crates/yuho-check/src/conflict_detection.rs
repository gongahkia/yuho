use std::collections::HashMap;
/// Conflict detection module for multi-file analysis
///
/// This module analyzes multiple Yuho programs to detect logical contradictions
/// between legal provisions defined in different files.
use yuho_core::ast::*;

#[derive(Debug, Clone)]
pub struct ConflictReport {
    pub file1: String,
    pub file2: String,
    pub conflicts: Vec<Conflict>,
}

impl ConflictReport {
    /// Format the report as human-readable text
    pub fn format(&self) -> String {
        if self.conflicts.is_empty() {
            return format!(
                "No conflicts detected between {} and {}",
                self.file1, self.file2
            );
        }

        let mut output = String::new();
        output.push_str(&format!("┌─ CONFLICT REPORT\n"));
        output.push_str(&format!("│\n"));
        output.push_str(&format!("│  Files: {} and {}\n", self.file1, self.file2));
        output.push_str(&format!("│  Conflicts found: {}\n", self.conflicts.len()));
        output.push_str(&format!("│\n"));
        output.push_str(&format!("├─ DETAILS\n"));

        for (i, conflict) in self.conflicts.iter().enumerate() {
            output.push_str(&format!("│\n"));
            output.push_str(&format!("│  [{}] {}\n", i + 1, conflict.description));
            output.push_str(&format!(
                "│      {} at {}:{}\n",
                self.file1, conflict.location1.start, conflict.location1.end
            ));
            output.push_str(&format!(
                "│      {} at {}:{}\n",
                self.file2, conflict.location2.start, conflict.location2.end
            ));
        }

        output.push_str(&format!("│\n"));
        output.push_str(&format!("└─ END OF REPORT\n"));
        output
    }

    /// Export report as JSON
    pub fn to_json(&self) -> String {
        format!(
            r#"{{"file1":"{}","file2":"{}","conflict_count":{},"conflicts":[{}]}}"#,
            self.file1,
            self.file2,
            self.conflicts.len(),
            self.conflicts.iter()
                .map(|c| format!(
                    r#"{{"description":"{}","loc1_start":{},"loc1_end":{},"loc2_start":{},"loc2_end":{}}}"#,
                    c.description, c.location1.start, c.location1.end,
                    c.location2.start, c.location2.end
                ))
                .collect::<Vec<_>>()
                .join(",")
        )
    }
}

#[derive(Debug, Clone)]
pub struct Conflict {
    pub description: String,
    pub location1: Span,
    pub location2: Span,
}

/// Logical model extracted from a program for conflict analysis
#[derive(Debug, Clone)]
struct LogicalModel {
    /// Enum definitions: name -> (variants, span)
    enums: HashMap<String, (Vec<String>, Span)>,
    /// Struct definitions: name -> (field names, span)
    structs: HashMap<String, (Vec<String>, Span)>,
    /// Legal test definitions: name -> (requirement names, span)
    legal_tests: HashMap<String, (Vec<String>, Span)>,
}

pub struct ConflictDetector {
    // Maps file names to their programs
    programs: HashMap<String, Program>,
    // Enable Z3 verification for deep semantic checks
    use_z3: bool,
}

impl ConflictDetector {
    pub fn new() -> Self {
        Self {
            programs: HashMap::new(),
            use_z3: false,
        }
    }

    /// Create a detector with Z3 verification enabled
    pub fn with_z3() -> Self {
        Self {
            programs: HashMap::new(),
            use_z3: true,
        }
    }

    /// Register a program from a specific file
    pub fn add_program(&mut self, file_name: String, program: Program) {
        self.programs.insert(file_name, program);
    }

    /// Check for conflicts between two files
    pub fn check_conflict(&self, file1: &str, file2: &str) -> Option<ConflictReport> {
        let prog1 = self.programs.get(file1)?;
        let prog2 = self.programs.get(file2)?;

        let conflicts = self.detect_conflicts(prog1, prog2);

        if conflicts.is_empty() {
            None
        } else {
            Some(ConflictReport {
                file1: file1.to_string(),
                file2: file2.to_string(),
                conflicts,
            })
        }
    }

    /// Internal method to detect conflicts between two programs
    fn detect_conflicts(&self, prog1: &Program, prog2: &Program) -> Vec<Conflict> {
        let mut conflicts = Vec::new();

        // Extract logical models from both programs
        let model1 = self.extract_logical_model(prog1);
        let model2 = self.extract_logical_model(prog2);

        // Check for overlapping enum definitions with different variants
        for (name, (variants1, span1)) in &model1.enums {
            if let Some((variants2, span2)) = model2.enums.get(name) {
                if variants1 != variants2 {
                    conflicts.push(Conflict {
                        description: format!(
                            "Enum '{}' has conflicting definitions: {:?} vs {:?}",
                            name, variants1, variants2
                        ),
                        location1: span1.clone(),
                        location2: span2.clone(),
                    });
                }
            }
        }

        // Check for struct conflicts (same name, different fields)
        for (name, (fields1, span1)) in &model1.structs {
            if let Some((fields2, span2)) = model2.structs.get(name) {
                if fields1 != fields2 {
                    conflicts.push(Conflict {
                        description: format!("Struct '{}' has conflicting field definitions", name),
                        location1: span1.clone(),
                        location2: span2.clone(),
                    });
                }
            }
        }

        // Check for legal test conflicts
        for (name, (reqs1, span1)) in &model1.legal_tests {
            if let Some((reqs2, span2)) = model2.legal_tests.get(name) {
                if reqs1 != reqs2 {
                    conflicts.push(Conflict {
                        description: format!("Legal test '{}' has conflicting requirements", name),
                        location1: span1.clone(),
                        location2: span2.clone(),
                    });
                }
            }
        }

        // If Z3 is enabled, perform deeper semantic analysis
        if self.use_z3 {
            conflicts.extend(self.detect_z3_conflicts(&model1, &model2));
        }

        conflicts
    }

    /// Use Z3 to detect deeper semantic conflicts (placeholder for future implementation)
    fn detect_z3_conflicts(&self, _model1: &LogicalModel, _model2: &LogicalModel) -> Vec<Conflict> {
        // TODO: Implement Z3-based semantic conflict detection
        // This would check for:
        // - Mutually exclusive enum variants that could both be satisfied
        // - Contradictory legal test requirements
        // - Incompatible struct constraints
        Vec::new()
    }

    /// Extract logical model from a program
    fn extract_logical_model(&self, program: &Program) -> LogicalModel {
        let mut model = LogicalModel {
            enums: HashMap::new(),
            structs: HashMap::new(),
            legal_tests: HashMap::new(),
        };

        for item in &program.items {
            self.collect_model_from_item(item, &mut model);
        }

        model
    }

    /// Recursively collect logical model elements from items
    fn collect_model_from_item(&self, item: &Item, model: &mut LogicalModel) {
        match item {
            Item::Enum(e) => {
                model
                    .enums
                    .insert(e.name.clone(), (e.variants.clone(), e.span.clone()));
            },
            Item::Struct(s) => {
                let field_names: Vec<String> = s.fields.iter().map(|f| f.name.clone()).collect();
                model
                    .structs
                    .insert(s.name.clone(), (field_names, s.span.clone()));
            },
            Item::LegalTest(lt) => {
                let req_names: Vec<String> =
                    lt.requirements.iter().map(|r| r.name.clone()).collect();
                model
                    .legal_tests
                    .insert(lt.name.clone(), (req_names, lt.span.clone()));
            },
            Item::Scope(s) => {
                for inner in &s.items {
                    self.collect_model_from_item(inner, model);
                }
            },
            _ => {},
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_no_conflicts() {
        let mut detector = ConflictDetector::new();

        let prog1 = Program {
            imports: vec![],
            items: vec![],
        };

        let prog2 = Program {
            imports: vec![],
            items: vec![],
        };

        detector.add_program("file1.yh".to_string(), prog1);
        detector.add_program("file2.yh".to_string(), prog2);

        let report = detector.check_conflict("file1.yh", "file2.yh");
        assert!(report.is_none());
    }

    #[test]
    fn test_enum_conflict() {
        let mut detector = ConflictDetector::new();

        let prog1 = Program {
            imports: vec![],
            items: vec![Item::Enum(EnumDefinition {
                name: "Status".to_string(),
                variants: vec!["Active".to_string(), "Inactive".to_string()],
                mutually_exclusive: false,
                span: Span { start: 0, end: 10 },
            })],
        };

        let prog2 = Program {
            imports: vec![],
            items: vec![Item::Enum(EnumDefinition {
                name: "Status".to_string(),
                variants: vec!["Running".to_string(), "Stopped".to_string()],
                mutually_exclusive: false,
                span: Span { start: 0, end: 10 },
            })],
        };

        detector.add_program("file1.yh".to_string(), prog1);
        detector.add_program("file2.yh".to_string(), prog2);

        let report = detector.check_conflict("file1.yh", "file2.yh");
        assert!(report.is_some());
        let report = report.unwrap();
        assert_eq!(report.conflicts.len(), 1);
        assert!(report.conflicts[0].description.contains("Status"));
    }
}
