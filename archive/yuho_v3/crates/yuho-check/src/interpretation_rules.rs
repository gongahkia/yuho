/// Statutory Interpretation Rules
/// Implements common law interpretation canons
use yuho_core::ast::{Expr, Item, Program};

pub struct InterpretationRules {
    pub ejusdem_generis_contexts: Vec<EjusdemGenerisContext>,
    pub noscitur_contexts: Vec<NosciturContext>,
    pub expressio_contexts: Vec<ExpressioContext>,
}

#[derive(Debug, Clone)]
pub struct EjusdemGenerisContext {
    pub location: String,
    pub specific_items: Vec<String>,
    pub general_term: String,
}

#[derive(Debug, Clone)]
pub struct NosciturContext {
    pub location: String,
    pub ambiguous_term: String,
    pub context_terms: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct ExpressioContext {
    pub location: String,
    pub expressed_items: Vec<String>,
    pub note: String,
}

impl InterpretationRules {
    pub fn new() -> Self {
        Self {
            ejusdem_generis_contexts: Vec::new(),
            noscitur_contexts: Vec::new(),
            expressio_contexts: Vec::new(),
        }
    }

    pub fn analyze_program(&mut self, program: &Program) {
        for item in &program.items {
            self.visit_item(item);
        }
    }

    fn visit_item(&mut self, item: &Item) {
        match item {
            Item::Enum(e) => {
                // Check for ejusdem generis pattern
                if e.variants.len() >= 3 {
                    // Look for pattern: specific, specific, specific, general
                    self.check_ejusdem_generis(&e.name, &e.variants);
                }
            },
            Item::Struct(s) => {
                // Check field relationships for noscitur a sociis
                if s.fields.len() >= 2 {
                    self.check_noscitur_a_sociis(&s.name, &s.fields);
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

    fn check_ejusdem_generis(&mut self, enum_name: &str, variants: &[String]) {
        // Ejusdem generis: General terms following specific ones
        // should be interpreted in light of the specific terms
        if variants.len() >= 4 {
            let specific = variants[..variants.len() - 1].to_vec();
            let general = variants[variants.len() - 1].clone();

            self.ejusdem_generis_contexts.push(EjusdemGenerisContext {
                location: enum_name.to_string(),
                specific_items: specific,
                general_term: general,
            });
        }
    }

    fn check_noscitur_a_sociis(&mut self, struct_name: &str, fields: &[yuho_core::ast::Field]) {
        // Noscitur a sociis: Words are known by their companions
        let field_names: Vec<String> = fields.iter().map(|f| f.name.clone()).collect();

        if !field_names.is_empty() {
            self.noscitur_contexts.push(NosciturContext {
                location: struct_name.to_string(),
                ambiguous_term: field_names[0].clone(),
                context_terms: field_names[1..].to_vec(),
            });
        }
    }

    pub fn get_interpretation_guidance(&self, context: &str) -> Vec<String> {
        let mut guidance = Vec::new();

        for ej in &self.ejusdem_generis_contexts {
            if ej.location.contains(context) {
                guidance.push(format!(
                    "Ejusdem Generis: '{}' should be interpreted in light of: {}",
                    ej.general_term,
                    ej.specific_items.join(", ")
                ));
            }
        }

        for nos in &self.noscitur_contexts {
            if nos.location.contains(context) {
                guidance.push(format!(
                    "Noscitur a Sociis: '{}' should be interpreted with: {}",
                    nos.ambiguous_term,
                    nos.context_terms.join(", ")
                ));
            }
        }

        guidance
    }
}

impl Default for InterpretationRules {
    fn default() -> Self {
        Self::new()
    }
}
