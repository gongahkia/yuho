//! Statute parsing and Yuho code generation
//!
//! This module uses LLMs to parse legal statutes and generate Yuho code

use crate::provider::{LLMRequest, Provider};
use crate::LLMResult;
use serde::{Deserialize, Serialize};

/// Parsed statute structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedStatute {
    pub title: String,
    pub sections: Vec<StatuteSection>,
    pub entities: Vec<Entity>,
    pub generated_code: String,
    pub confidence: f32,
}

/// Individual section of a statute
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatuteSection {
    pub section_number: String,
    pub title: String,
    pub content: String,
    pub clauses: Vec<Clause>,
}

/// Clause within a section
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Clause {
    pub clause_id: String,
    pub text: String,
    pub clause_type: ClauseType,
}

/// Type of legal clause
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ClauseType {
    Definition,
    Condition,
    Requirement,
    Exception,
    Penalty,
    Procedure,
}

/// Recognized entity in statute
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entity {
    pub name: String,
    pub entity_type: EntityType,
    pub description: String,
}

/// Types of legal entities
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EntityType {
    Person,
    Organization,
    Amount,
    Date,
    Duration,
    Percentage,
    Condition,
}

/// Statute parser using LLM
pub struct StatuteParser<P: Provider> {
    provider: P,
}

impl<P: Provider> StatuteParser<P> {
    pub fn new(provider: P) -> Self {
        Self { provider }
    }

    /// Parse a statute text and generate Yuho code
    pub async fn parse(&self, statute_text: &str) -> LLMResult<ParsedStatute> {
        // Step 1: Extract structure
        let sections = self.extract_sections(statute_text).await?;

        // Step 2: Extract entities
        let entities = self.extract_entities(statute_text).await?;

        // Step 3: Generate Yuho code
        let code = self.generate_code(&sections, &entities).await?;

        Ok(ParsedStatute {
            title: self.extract_title(statute_text),
            sections,
            entities,
            generated_code: code,
            confidence: 0.85, // Would be calculated based on LLM response
        })
    }

    /// Extract title from statute
    fn extract_title(&self, statute_text: &str) -> String {
        statute_text
            .lines()
            .next()
            .unwrap_or("Untitled Statute")
            .to_string()
    }

    /// Extract sections using LLM
    async fn extract_sections(&self, statute_text: &str) -> LLMResult<Vec<StatuteSection>> {
        let prompt = format!(
            r#"Extract all sections from this legal statute. For each section, provide:
1. Section number
2. Section title
3. Main content
4. Individual clauses

Statute:
{}

Respond in JSON format with an array of sections."#,
            statute_text
        );

        let request = LLMRequest {
            prompt,
            max_tokens: 2000,
            temperature: 0.3, // Lower temperature for structured extraction
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&request).await?;

        // Parse JSON response (simplified - real implementation would be more robust)
        self.parse_sections_from_response(&response.text)
    }

    /// Extract entities using LLM
    async fn extract_entities(&self, statute_text: &str) -> LLMResult<Vec<Entity>> {
        let prompt = format!(
            r#"Extract all legal entities from this statute. Identify:
- Persons (accused, victim, witness, etc.)
- Amounts (fines, damages, limits)
- Dates and durations
- Percentages
- Conditions and requirements

Statute:
{}

Respond in JSON format with an array of entities."#,
            statute_text
        );

        let request = LLMRequest {
            prompt,
            max_tokens: 1000,
            temperature: 0.3,
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&request).await?;

        self.parse_entities_from_response(&response.text)
    }

    /// Generate Yuho code from parsed structure
    async fn generate_code(
        &self,
        sections: &[StatuteSection],
        entities: &[Entity],
    ) -> LLMResult<String> {
        let prompt = format!(
            r#"Generate Yuho code for this legal statute.

Sections:
{}

Entities:
{}

Generate valid Yuho code that includes:
1. Struct definitions for entities
2. Enum definitions for categories
3. Scope definitions for sections
4. Pattern matching for conditions
5. Type constraints where applicable

Use Yuho syntax with dependent types like BoundedInt, Positive, NonEmpty, money<Currency>."#,
            serde_json::to_string_pretty(sections).unwrap_or_default(),
            serde_json::to_string_pretty(entities).unwrap_or_default()
        );

        let request = LLMRequest {
            prompt,
            max_tokens: 3000,
            temperature: 0.5,
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&request).await?;

        Ok(self.clean_generated_code(&response.text))
    }

    /// Parse sections from LLM response
    fn parse_sections_from_response(&self, _response: &str) -> LLMResult<Vec<StatuteSection>> {
        // In real implementation, would parse JSON
        // For now, return mock data
        Ok(vec![StatuteSection {
            section_number: "s1".to_string(),
            title: "General Provisions".to_string(),
            content: "Extracted content".to_string(),
            clauses: vec![],
        }])
    }

    /// Parse entities from LLM response
    fn parse_entities_from_response(&self, _response: &str) -> LLMResult<Vec<Entity>> {
        // In real implementation, would parse JSON
        Ok(vec![Entity {
            name: "amount".to_string(),
            entity_type: EntityType::Amount,
            description: "Monetary amount".to_string(),
        }])
    }

    /// Clean and format generated code
    fn clean_generated_code(&self, code: &str) -> String {
        // Remove markdown code blocks if present
        let cleaned = code
            .trim()
            .trim_start_matches("```yuho")
            .trim_start_matches("```")
            .trim_end_matches("```")
            .trim();

        cleaned.to_string()
    }

    /// Validate generated code
    pub fn validate_code(&self, code: &str) -> LLMResult<Vec<String>> {
        match yuho_core::parse(code) {
            Ok(_) => Ok(vec![]),
            Err(e) => Ok(vec![format!("Parse error: {}", e)]),
        }
    }
}

/// Review interface for human validation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReviewRequest {
    pub statute_text: String,
    pub parsed_statute: ParsedStatute,
    pub validation_errors: Vec<String>,
}

impl ReviewRequest {
    pub fn new(statute_text: String, parsed_statute: ParsedStatute) -> Self {
        Self {
            statute_text,
            parsed_statute,
            validation_errors: vec![],
        }
    }

    pub fn with_errors(mut self, errors: Vec<String>) -> Self {
        self.validation_errors = errors;
        self
    }

    pub fn needs_review(&self) -> bool {
        !self.validation_errors.is_empty() || self.parsed_statute.confidence < 0.8
    }

    pub fn to_json(&self) -> String {
        serde_json::to_string_pretty(self).unwrap_or_default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::provider::MockProvider;

    #[tokio::test]
    async fn test_statute_parser() {
        let provider = MockProvider::new();
        let parser = StatuteParser::new(provider);

        let statute = "Section 415: Cheating\nWhoever deceives...";
        let result = parser.parse(statute).await;

        assert!(result.is_ok());
        let parsed = result.unwrap();
        assert!(!parsed.title.is_empty());
        assert!(!parsed.sections.is_empty());
    }

    #[tokio::test]
    async fn test_code_validation() {
        let provider = MockProvider::new();
        let parser = StatuteParser::new(provider);

        let valid_code = "int x := 42";
        let errors = parser.validate_code(valid_code).unwrap();
        assert!(errors.is_empty());

        let invalid_code = "invalid syntax!!!";
        let errors = parser.validate_code(invalid_code).unwrap();
        assert!(!errors.is_empty());
    }

    #[test]
    fn test_review_request() {
        let statute = ParsedStatute {
            title: "Test".to_string(),
            sections: vec![],
            entities: vec![],
            generated_code: "int x := 42".to_string(),
            confidence: 0.9,
        };

        let review = ReviewRequest::new("Test statute".to_string(), statute);
        assert!(!review.needs_review()); // High confidence

        let review_with_errors = review.with_errors(vec!["Error".to_string()]);
        assert!(review_with_errors.needs_review()); // Has errors
    }
}
