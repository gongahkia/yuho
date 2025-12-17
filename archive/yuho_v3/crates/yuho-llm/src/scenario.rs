//! Test scenario and edge case generation
//!
//! Generate comprehensive test scenarios for legal code

use crate::provider::{LLMRequest, Provider};
use crate::LLMResult;
use serde::{Deserialize, Serialize};

/// Test scenario
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestScenario {
    pub id: String,
    pub description: String,
    pub scenario_type: ScenarioType,
    pub inputs: Vec<TestInput>,
    pub expected_outcome: String,
    pub reasoning: String,
}

/// Type of test scenario
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ScenarioType {
    Normal,
    EdgeCase,
    BoundaryCondition,
    Adversarial,
    Invalid,
}

/// Test input value
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestInput {
    pub name: String,
    pub value: String,
    pub value_type: String,
}

/// Coverage analysis result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoverageAnalysis {
    pub total_scenarios: usize,
    pub normal_cases: usize,
    pub edge_cases: usize,
    pub boundary_cases: usize,
    pub adversarial_cases: usize,
    pub coverage_percentage: f32,
    pub uncovered_paths: Vec<String>,
}

/// Scenario generator
pub struct ScenarioGenerator<P: Provider> {
    provider: P,
}

impl<P: Provider> ScenarioGenerator<P> {
    pub fn new(provider: P) -> Self {
        Self { provider }
    }

    /// Generate comprehensive test scenarios
    pub async fn generate_scenarios(
        &self,
        code: &str,
        count: usize,
    ) -> LLMResult<Vec<TestScenario>> {
        let mut scenarios = Vec::new();

        // Generate normal test cases
        scenarios.extend(self.generate_normal_cases(code, count / 4).await?);

        // Generate edge cases
        scenarios.extend(self.generate_edge_cases(code, count / 4).await?);

        // Generate boundary conditions
        scenarios.extend(self.generate_boundary_cases(code, count / 4).await?);

        // Generate adversarial examples
        scenarios.extend(self.generate_adversarial_cases(code, count / 4).await?);

        Ok(scenarios)
    }

    /// Generate normal test cases
    async fn generate_normal_cases(
        &self,
        code: &str,
        count: usize,
    ) -> LLMResult<Vec<TestScenario>> {
        let prompt = format!(
            r#"Generate {} normal, typical test cases for this Yuho legal code:

```yuho
{}
```

For each test case, provide:
1. A unique ID
2. Description of the scenario
3. Input values
4. Expected outcome
5. Legal reasoning

Format as JSON array."#,
            count, code
        );

        self.request_scenarios(&prompt, ScenarioType::Normal).await
    }

    /// Generate edge cases
    async fn generate_edge_cases(&self, code: &str, count: usize) -> LLMResult<Vec<TestScenario>> {
        let prompt = format!(
            r#"Generate {} edge case test scenarios for this Yuho legal code:

```yuho
{}
```

Focus on:
- Unusual but valid situations
- Rare combinations
- Limit cases that are still valid
- Special circumstances

Format as JSON array."#,
            count, code
        );

        self.request_scenarios(&prompt, ScenarioType::EdgeCase)
            .await
    }

    /// Generate boundary condition tests
    async fn generate_boundary_cases(
        &self,
        code: &str,
        count: usize,
    ) -> LLMResult<Vec<TestScenario>> {
        let prompt = format!(
            r#"Generate {} boundary condition tests for this Yuho legal code:

```yuho
{}
```

Focus on:
- Minimum and maximum values
- Zero and negative numbers where applicable
- Empty vs non-empty collections
- Date/time boundaries
- Threshold values

Format as JSON array."#,
            count, code
        );

        self.request_scenarios(&prompt, ScenarioType::BoundaryCondition)
            .await
    }

    /// Generate adversarial test cases
    async fn generate_adversarial_cases(
        &self,
        code: &str,
        count: usize,
    ) -> LLMResult<Vec<TestScenario>> {
        let prompt = format!(
            r#"Generate {} adversarial test cases for this Yuho legal code:

```yuho
{}
```

Focus on:
- Attempts to circumvent the law
- Malicious actors
- Loopholes and edge cases that might be exploited
- Invalid or illegal inputs
- Contradictory conditions

Format as JSON array."#,
            count, code
        );

        self.request_scenarios(&prompt, ScenarioType::Adversarial)
            .await
    }

    /// Send request to LLM and parse scenarios
    async fn request_scenarios(
        &self,
        prompt: &str,
        scenario_type: ScenarioType,
    ) -> LLMResult<Vec<TestScenario>> {
        let request = LLMRequest {
            prompt: prompt.to_string(),
            max_tokens: 2000,
            temperature: 0.8, // Higher creativity for diverse scenarios
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&request).await?;

        // Parse response into scenarios
        self.parse_scenarios(&response.text, scenario_type)
    }

    /// Parse LLM response into test scenarios
    fn parse_scenarios(
        &self,
        _response: &str,
        scenario_type: ScenarioType,
    ) -> LLMResult<Vec<TestScenario>> {
        // In production, would parse JSON properly
        // For now, create mock scenarios
        Ok(vec![TestScenario {
            id: format!("test_{:?}_1", scenario_type),
            description: "Generated test scenario".to_string(),
            scenario_type,
            inputs: vec![],
            expected_outcome: "Expected result".to_string(),
            reasoning: "Legal reasoning".to_string(),
        }])
    }

    /// Analyze coverage of test scenarios
    pub fn analyze_coverage(&self, scenarios: &[TestScenario]) -> CoverageAnalysis {
        let total = scenarios.len();
        let normal = scenarios
            .iter()
            .filter(|s| matches!(s.scenario_type, ScenarioType::Normal))
            .count();
        let edge = scenarios
            .iter()
            .filter(|s| matches!(s.scenario_type, ScenarioType::EdgeCase))
            .count();
        let boundary = scenarios
            .iter()
            .filter(|s| matches!(s.scenario_type, ScenarioType::BoundaryCondition))
            .count();
        let adversarial = scenarios
            .iter()
            .filter(|s| matches!(s.scenario_type, ScenarioType::Adversarial))
            .count();

        // Calculate coverage based on scenario distribution
        let coverage = if total > 0 {
            let balance =
                (normal.min(edge).min(boundary).min(adversarial) as f32) / (total as f32 / 4.0);
            (balance * 100.0).min(100.0)
        } else {
            0.0
        };

        CoverageAnalysis {
            total_scenarios: total,
            normal_cases: normal,
            edge_cases: edge,
            boundary_cases: boundary,
            adversarial_cases: adversarial,
            coverage_percentage: coverage,
            uncovered_paths: vec![],
        }
    }

    /// Generate test data for a specific scenario
    pub async fn generate_test_data(&self, scenario: &TestScenario) -> LLMResult<Vec<TestInput>> {
        let prompt = format!(
            r#"Generate specific test input data for this scenario:

Scenario: {}
Expected outcome: {}

Provide concrete values for all required inputs."#,
            scenario.description, scenario.expected_outcome
        );

        let request = LLMRequest {
            prompt,
            max_tokens: 500,
            temperature: 0.7,
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&request).await?;

        Ok(vec![TestInput {
            name: "value".to_string(),
            value: response.text,
            value_type: "string".to_string(),
        }])
    }

    /// Identify gaps in test coverage
    pub async fn identify_gaps(
        &self,
        code: &str,
        scenarios: &[TestScenario],
    ) -> LLMResult<Vec<String>> {
        let scenario_descriptions: Vec<String> = scenarios
            .iter()
            .map(|s| format!("- {}", s.description))
            .collect();

        let prompt = format!(
            r#"Analyze this Yuho legal code and the existing test scenarios.
Identify any gaps in test coverage - situations that are not covered by the existing tests.

Code:
```yuho
{}
```

Existing test scenarios:
{}

List any uncovered situations, edge cases, or conditions."#,
            code,
            scenario_descriptions.join("\n")
        );

        let request = LLMRequest {
            prompt,
            max_tokens: 1000,
            temperature: 0.6,
            stop_sequences: vec![],
        };

        let response = self.provider.complete(&request).await?;

        // Parse gaps from response
        Ok(response
            .text
            .lines()
            .filter(|line| line.trim_start().starts_with('-'))
            .map(|line| line.trim_start_matches('-').trim().to_string())
            .collect())
    }
}

/// Scenario validation
pub struct ScenarioValidator;

impl ScenarioValidator {
    /// Validate that a scenario is well-formed
    pub fn validate(scenario: &TestScenario) -> Vec<String> {
        let mut errors = Vec::new();

        if scenario.description.is_empty() {
            errors.push("Description is empty".to_string());
        }

        if scenario.expected_outcome.is_empty() {
            errors.push("Expected outcome is empty".to_string());
        }

        if scenario.inputs.is_empty() {
            errors.push("No inputs provided".to_string());
        }

        errors
    }

    /// Check if scenarios provide good coverage
    pub fn check_coverage(coverage: &CoverageAnalysis) -> bool {
        coverage.coverage_percentage >= 80.0
            && coverage.normal_cases > 0
            && coverage.edge_cases > 0
            && coverage.boundary_cases > 0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::provider::MockProvider;

    #[tokio::test]
    async fn test_generate_scenarios() {
        let provider = MockProvider::new();
        let generator = ScenarioGenerator::new(provider);

        let code = "int age := 25";
        let scenarios = generator.generate_scenarios(code, 8).await;

        assert!(scenarios.is_ok());
        let scenarios = scenarios.unwrap();
        assert!(!scenarios.is_empty());
    }

    #[tokio::test]
    async fn test_generate_normal_cases() {
        let provider = MockProvider::new();
        let generator = ScenarioGenerator::new(provider);

        let code = "bool valid := true";
        let scenarios = generator.generate_normal_cases(code, 2).await;

        assert!(scenarios.is_ok());
    }

    #[test]
    fn test_analyze_coverage() {
        let provider = MockProvider::new();
        let generator = ScenarioGenerator::new(provider);

        let scenarios = vec![
            TestScenario {
                id: "1".to_string(),
                description: "Test".to_string(),
                scenario_type: ScenarioType::Normal,
                inputs: vec![],
                expected_outcome: "Pass".to_string(),
                reasoning: "Valid".to_string(),
            },
            TestScenario {
                id: "2".to_string(),
                description: "Edge".to_string(),
                scenario_type: ScenarioType::EdgeCase,
                inputs: vec![],
                expected_outcome: "Pass".to_string(),
                reasoning: "Valid".to_string(),
            },
        ];

        let coverage = generator.analyze_coverage(&scenarios);
        assert_eq!(coverage.total_scenarios, 2);
        assert_eq!(coverage.normal_cases, 1);
        assert_eq!(coverage.edge_cases, 1);
    }

    #[test]
    fn test_scenario_validation() {
        let valid_scenario = TestScenario {
            id: "1".to_string(),
            description: "Test scenario".to_string(),
            scenario_type: ScenarioType::Normal,
            inputs: vec![TestInput {
                name: "x".to_string(),
                value: "5".to_string(),
                value_type: "int".to_string(),
            }],
            expected_outcome: "Success".to_string(),
            reasoning: "Valid input".to_string(),
        };

        let errors = ScenarioValidator::validate(&valid_scenario);
        assert!(errors.is_empty());

        let invalid_scenario = TestScenario {
            id: "2".to_string(),
            description: "".to_string(),
            scenario_type: ScenarioType::Normal,
            inputs: vec![],
            expected_outcome: "".to_string(),
            reasoning: "".to_string(),
        };

        let errors = ScenarioValidator::validate(&invalid_scenario);
        assert!(!errors.is_empty());
    }

    #[test]
    fn test_coverage_check() {
        let good_coverage = CoverageAnalysis {
            total_scenarios: 20,
            normal_cases: 5,
            edge_cases: 5,
            boundary_cases: 5,
            adversarial_cases: 5,
            coverage_percentage: 85.0,
            uncovered_paths: vec![],
        };

        assert!(ScenarioValidator::check_coverage(&good_coverage));

        let bad_coverage = CoverageAnalysis {
            total_scenarios: 5,
            normal_cases: 5,
            edge_cases: 0,
            boundary_cases: 0,
            adversarial_cases: 0,
            coverage_percentage: 25.0,
            uncovered_paths: vec![],
        };

        assert!(!ScenarioValidator::check_coverage(&bad_coverage));
    }
}
