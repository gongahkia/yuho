/// Citation Validation Module
/// Validates legal citations and builds citation index
use std::collections::{HashMap, HashSet};
use yuho_core::ast::{Item, Program, Type};

#[derive(Debug, Clone)]
pub enum CitationError {
    /// Citation format is invalid
    InvalidFormat { citation: String, reason: String },
    /// Section number is invalid (not numeric or out of range)
    InvalidSection { section: String, act: String },
    /// Subsection is invalid (not a valid subsection identifier)
    InvalidSubsection {
        subsection: String,
        section: String,
        act: String,
    },
    /// Referenced act/statute doesn't exist in the program
    UnresolvedReference {
        act: String,
        section: String,
        location: String,
    },
    /// Circular citation detected
    CircularReference { chain: Vec<String> },
}

pub struct CitationValidator {
    /// All citations found in the program
    pub citations: Vec<CitationRef>,
    /// Index of cited acts
    pub act_index: HashMap<String, Vec<CitationRef>>,
    /// Validation errors
    pub errors: Vec<CitationError>,
    /// All defined acts/statutes in the program
    pub defined_acts: HashSet<String>,
}

#[derive(Debug, Clone)]
pub struct CitationRef {
    pub section: String,
    pub subsection: String,
    pub act: String,
    pub location: String, // Where the citation appears
}

impl CitationValidator {
    pub fn new() -> Self {
        Self {
            citations: Vec::new(),
            act_index: HashMap::new(),
            errors: Vec::new(),
            defined_acts: HashSet::new(),
        }
    }

    /// Validate section number format and value
    fn validate_section(&self, section: &str, act: &str) -> Result<(), CitationError> {
        // Section should be numeric (optionally with letters like "415A")
        if section.is_empty() {
            return Err(CitationError::InvalidSection {
                section: section.to_string(),
                act: act.to_string(),
            });
        }

        // Extract numeric part
        let numeric_part: String = section.chars().take_while(|c| c.is_numeric()).collect();
        if numeric_part.is_empty() {
            return Err(CitationError::InvalidSection {
                section: section.to_string(),
                act: act.to_string(),
            });
        }

        // Check if numeric part is valid
        match numeric_part.parse::<u32>() {
            Ok(num) => {
                // Section numbers should be reasonable (1-10000)
                if num < 1 || num > 10000 {
                    return Err(CitationError::InvalidSection {
                        section: section.to_string(),
                        act: act.to_string(),
                    });
                }
            },
            Err(_) => {
                return Err(CitationError::InvalidSection {
                    section: section.to_string(),
                    act: act.to_string(),
                });
            },
        }

        Ok(())
    }

    /// Validate subsection identifier
    fn validate_subsection(
        &self,
        subsection: &str,
        section: &str,
        act: &str,
    ) -> Result<(), CitationError> {
        // Subsection can be empty (meaning the entire section)
        if subsection.is_empty() {
            return Ok(());
        }

        // Valid subsection formats:
        // - Numeric: "1", "2", "3"
        // - Alphabetic: "a", "b", "c" or "A", "B", "C"
        // - Roman numerals: "i", "ii", "iii", "iv", "v"
        // - Combined: "1a", "2b"

        let valid_formats = vec![
            subsection.chars().all(|c| c.is_numeric()), // Pure numeric
            subsection.chars().all(|c| c.is_alphabetic()), // Pure alphabetic
            subsection.len() >= 2
                && subsection.chars().next().unwrap().is_numeric()
                && subsection.chars().skip(1).all(|c| c.is_alphabetic()), // Numeric + alpha
        ];

        if !valid_formats.iter().any(|&v| v) {
            return Err(CitationError::InvalidSubsection {
                subsection: subsection.to_string(),
                section: section.to_string(),
                act: act.to_string(),
            });
        }

        Ok(())
    }

    /// Check if a cited act exists in the program
    fn check_reference(&self, citation: &CitationRef) -> Result<(), CitationError> {
        // For now, we only warn if the act is not in our defined_acts set
        // In the future, this could check against an external database
        if !self.defined_acts.is_empty() && !self.defined_acts.contains(&citation.act) {
            return Err(CitationError::UnresolvedReference {
                act: citation.act.clone(),
                section: citation.section.clone(),
                location: citation.location.clone(),
            });
        }
        Ok(())
    }

    pub fn validate_program(&mut self, program: &Program) {
        // First pass: collect all defined acts/statutes
        for item in &program.items {
            self.collect_defined_acts(item);
        }

        // Second pass: collect all citations
        for item in &program.items {
            self.visit_item(item);
        }

        // Build index
        self.build_index();

        // Third pass: validate all citations
        for citation in &self.citations.clone() {
            // Validate section format
            if let Err(e) = self.validate_section(&citation.section, &citation.act) {
                self.errors.push(e);
            }

            // Validate subsection format
            if let Err(e) =
                self.validate_subsection(&citation.subsection, &citation.section, &citation.act)
            {
                self.errors.push(e);
            }

            // Check if reference exists
            if let Err(e) = self.check_reference(citation) {
                self.errors.push(e);
            }
        }
    }

    /// Collect all acts defined in the program
    fn collect_defined_acts(&mut self, item: &Item) {
        match item {
            Item::Struct(s) => {
                // Structs might represent statutes/acts
                // For now, we consider any struct with "Act" or "Statute" in the name
                if s.name.contains("Act") || s.name.contains("Statute") || s.name.contains("Code") {
                    self.defined_acts.insert(s.name.clone());
                }
            },
            Item::Scope(sc) => {
                // Scopes often represent statutory sections
                // The scope name might be like "s415_cheating" or "PenalCode"
                self.defined_acts.insert(sc.name.clone());
                for inner in &sc.items {
                    self.collect_defined_acts(inner);
                }
            },
            _ => {},
        }
    }

    fn visit_item(&mut self, item: &Item) {
        match item {
            Item::Struct(s) => {
                for field in &s.fields {
                    self.check_type(&field.ty, &format!("struct {}.{}", s.name, field.name));
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

    fn check_type(&mut self, ty: &Type, location: &str) {
        match ty {
            Type::Citation {
                section,
                subsection,
                act,
            } => {
                self.citations.push(CitationRef {
                    section: section.clone(),
                    subsection: subsection.clone(),
                    act: act.clone(),
                    location: location.to_string(),
                });
            },
            Type::Array(inner) => self.check_type(inner, location),
            _ => {},
        }
    }

    fn build_index(&mut self) {
        for citation in &self.citations {
            self.act_index
                .entry(citation.act.clone())
                .or_insert_with(Vec::new)
                .push(citation.clone());
        }
    }

    pub fn get_citations_by_act(&self, act: &str) -> Vec<&CitationRef> {
        self.act_index
            .get(act)
            .map(|v| v.iter().collect())
            .unwrap_or_default()
    }

    /// Get all validation errors
    pub fn get_errors(&self) -> &[CitationError] {
        &self.errors
    }

    /// Check if validation found any errors
    pub fn has_errors(&self) -> bool {
        !self.errors.is_empty()
    }

    /// Get a summary of validation results
    pub fn summary(&self) -> String {
        format!(
            "Citations: {}, Errors: {}, Defined Acts: {}",
            self.citations.len(),
            self.errors.len(),
            self.defined_acts.len()
        )
    }
}

impl Default for CitationValidator {
    fn default() -> Self {
        Self::new()
    }
}
