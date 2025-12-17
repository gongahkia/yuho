//! Natural language explanation generation
//!
//! Generate context-aware explanations of Yuho code for non-technical users

use crate::provider::{LLMRequest, Provider};
use crate::LLMResult;
use serde::{Deserialize, Serialize};

/// Explanation request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExplanationRequest {
    pub code: String,
    pub context: Option<String>,
    pub audience: Audience,
    pub detail_level: DetailLevel,
}

/// Target audience for explanation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Audience {
    Lawyer,
    Judge,
    Citizen,
    Developer,
}

/// Level of detail in explanation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DetailLevel {
    Brief,
    Standard,
    Detailed,
}

/// Generated explanation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Explanation {
    pub summary: String,
    pub detailed: String,
    pub examples: Vec<String>,
    pub key_points: Vec<String>,
}

/// Interactive Q&A system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Question {
    pub question: String,
    pub context_code: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Answer {
    pub answer: String,
    pub related_code: Vec<String>,
    pub confidence: f32,
}

/// Explanation generator
pub struct ExplanationGenerator<P: Provider> {
    provider: P,
}

impl<P: Provider> ExplanationGenerator<P> {
    pub fn new(provider: P) -> Self {
        Self { provider }
    }

    /// Generate explanation for Yuho code
    pub async fn explain(&self, request: &ExplanationRequest) -> LLMResult<Explanation> {
        let prompt = self.build_explanation_prompt(request);

        let llm_request = LLMRequest {
            prompt,
            max_tokens: 1500,
            temperature: 0.7,
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&llm_request).await?;

        self.parse_explanation(&response.text)
    }

    /// Build prompt based on audience and detail level
    fn build_explanation_prompt(&self, request: &ExplanationRequest) -> String {
        let audience_desc = match request.audience {
            Audience::Lawyer => "a legal professional",
            Audience::Judge => "a judge making legal decisions",
            Audience::Citizen => "an everyday person without legal background",
            Audience::Developer => "a software developer",
        };

        let detail_instruction = match request.detail_level {
            DetailLevel::Brief => "Provide a brief 2-3 sentence summary.",
            DetailLevel::Standard => "Provide a clear explanation with examples.",
            DetailLevel::Detailed => {
                "Provide a comprehensive explanation with multiple examples and edge cases."
            },
        };

        let context_section = if let Some(ctx) = &request.context {
            format!("\n\nContext:\n{}", ctx)
        } else {
            String::new()
        };

        format!(
            r#"Explain the following Yuho legal specification code to {}.

{}

Code:
```yuho
{}
```{}

Please explain:
1. What this code represents in plain language
2. The key legal concepts involved
3. Real-world examples where this applies
4. Important conditions or constraints

Focus on clarity and accessibility."#,
            audience_desc, detail_instruction, request.code, context_section
        )
    }

    /// Parse LLM response into structured explanation
    fn parse_explanation(&self, response: &str) -> LLMResult<Explanation> {
        // Simple parsing - in production would be more sophisticated
        let lines: Vec<&str> = response.lines().collect();

        let summary = lines.first().map(|s| s.to_string()).unwrap_or_default();

        let detailed = response.to_string();

        Ok(Explanation {
            summary,
            detailed,
            examples: self.extract_examples(response),
            key_points: self.extract_key_points(response),
        })
    }

    /// Extract examples from explanation
    fn extract_examples(&self, text: &str) -> Vec<String> {
        text.lines()
            .filter(|line| line.contains("example") || line.contains("Example"))
            .map(|s| s.to_string())
            .collect()
    }

    /// Extract key points from explanation
    fn extract_key_points(&self, text: &str) -> Vec<String> {
        text.lines()
            .filter(|line| line.trim_start().starts_with('-') || line.trim_start().starts_with('*'))
            .map(|s| {
                s.trim_start_matches('-')
                    .trim_start_matches('*')
                    .trim()
                    .to_string()
            })
            .collect()
    }

    /// Answer a specific question about code
    pub async fn answer_question(&self, question: &Question) -> LLMResult<Answer> {
        let prompt = format!(
            r#"Answer this question about the following Yuho code:

Code:
```yuho
{}
```

Question: {}

Provide a clear, concise answer that directly addresses the question."#,
            question.context_code, question.question
        );

        let request = LLMRequest {
            prompt,
            max_tokens: 800,
            temperature: 0.6,
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&request).await?;

        Ok(Answer {
            answer: response.text,
            related_code: vec![],
            confidence: 0.8,
        })
    }

    /// Simplify complex legal language
    pub async fn simplify(&self, code: &str) -> LLMResult<String> {
        let prompt = format!(
            r#"Simplify this Yuho legal code into plain, everyday language that anyone can understand:

```yuho
{}
```

Use simple words and short sentences. Avoid legal jargon."#,
            code
        );

        let request = LLMRequest {
            prompt,
            max_tokens: 1000,
            temperature: 0.7,
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&request).await?;

        Ok(response.text)
    }

    /// Generate example scenarios
    pub async fn generate_examples(&self, code: &str, count: usize) -> LLMResult<Vec<String>> {
        let prompt = format!(
            r#"Generate {} real-world example scenarios where this Yuho legal code would apply:

```yuho
{}
```

For each example, describe a concrete situation with specific details."#,
            count, code
        );

        let request = LLMRequest {
            prompt,
            max_tokens: 1500,
            temperature: 0.8,
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&request).await?;

        // Split response into individual examples
        Ok(response
            .text
            .split("\n\n")
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::provider::MockProvider;

    #[tokio::test]
    async fn test_explain_code() {
        let provider = MockProvider::new();
        let generator = ExplanationGenerator::new(provider);

        let request = ExplanationRequest {
            code: "int age := 25".to_string(),
            context: None,
            audience: Audience::Citizen,
            detail_level: DetailLevel::Standard,
        };

        let result = generator.explain(&request).await;
        assert!(result.is_ok());

        let explanation = result.unwrap();
        assert!(!explanation.summary.is_empty());
    }

    #[tokio::test]
    async fn test_answer_question() {
        let provider = MockProvider::new();
        let generator = ExplanationGenerator::new(provider);

        let question = Question {
            question: "What does this code do?".to_string(),
            context_code: "bool valid := true".to_string(),
        };

        let result = generator.answer_question(&question).await;
        assert!(result.is_ok());

        let answer = result.unwrap();
        assert!(!answer.answer.is_empty());
    }

    #[tokio::test]
    async fn test_simplify() {
        let provider = MockProvider::new();
        let generator = ExplanationGenerator::new(provider);

        let code = "BoundedInt<0, 100> age := 25";
        let result = generator.simplify(code).await;

        assert!(result.is_ok());
        assert!(!result.unwrap().is_empty());
    }

    #[tokio::test]
    async fn test_generate_examples() {
        let provider = MockProvider::new();
        let generator = ExplanationGenerator::new(provider);

        let code = "money amount := 1000.00";
        let result = generator.generate_examples(code, 3).await;

        assert!(result.is_ok());
        let examples = result.unwrap();
        assert!(!examples.is_empty());
    }
}
