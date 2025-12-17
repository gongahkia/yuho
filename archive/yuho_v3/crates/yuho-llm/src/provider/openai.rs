//! OpenAI GPT provider implementation

use super::{CostTracker, LLMRequest, LLMResponse, Provider, ProviderConfig, RateLimiter};
use crate::{LLMError, LLMResult};
use async_trait::async_trait;
use reqwest::Client;
use secrecy::ExposeSecret;
use serde::{Deserialize, Serialize};

/// OpenAI GPT API provider
pub struct OpenAIProvider {
    config: ProviderConfig,
    client: Client,
    rate_limiter: RateLimiter,
    cost_tracker: CostTracker,
}

/// OpenAI API request format
#[derive(Debug, Serialize)]
struct OpenAIRequest {
    model: String,
    messages: Vec<OpenAIMessage>,
    max_tokens: usize,
    temperature: f32,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    stop: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct OpenAIMessage {
    role: String,
    content: String,
}

/// OpenAI API response format
#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct OpenAIResponse {
    id: String,
    object: String,
    created: u64,
    model: String,
    choices: Vec<OpenAIChoice>,
    usage: OpenAIUsage,
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct OpenAIChoice {
    index: usize,
    message: OpenAIMessage,
    finish_reason: Option<String>,
}

#[derive(Debug, Deserialize)]
struct OpenAIUsage {
    prompt_tokens: usize,
    completion_tokens: usize,
    total_tokens: usize,
}

impl OpenAIProvider {
    /// Create a new OpenAI provider with configured timeouts
    pub fn new(config: ProviderConfig) -> Self {
        let rate_limiter = RateLimiter::new(config.rate_limit.clone());
        let cost_tracker = CostTracker::new(config.cost_budget.clone());

        // Configure HTTP client with timeouts
        let client = Client::builder()
            .timeout(std::time::Duration::from_secs(30)) // Request timeout
            .connect_timeout(std::time::Duration::from_secs(10)) // Connection timeout
            .pool_idle_timeout(std::time::Duration::from_secs(90)) // Idle connection timeout
            .build()
            .expect("Failed to build HTTP client");

        Self {
            config,
            client,
            rate_limiter,
            cost_tracker,
        }
    }

    /// Calculate cost for OpenAI API usage
    /// Pricing as of 2025 (approximate):
    /// - GPT-4 Turbo: $10/MTok input, $30/MTok output
    /// - GPT-4: $30/MTok input, $60/MTok output
    /// - GPT-3.5 Turbo: $0.50/MTok input, $1.50/MTok output
    fn calculate_cost(&self, input_tokens: usize, output_tokens: usize) -> f64 {
        let (input_cost, output_cost) = match self.config.model.as_str() {
            "gpt-4-turbo-preview" | "gpt-4-0125-preview" | "gpt-4-1106-preview" => (10.0, 30.0),
            "gpt-4" | "gpt-4-0613" => (30.0, 60.0),
            "gpt-3.5-turbo" | "gpt-3.5-turbo-0125" | "gpt-3.5-turbo-1106" => (0.50, 1.50),
            _ => (10.0, 30.0), // Default to GPT-4 Turbo pricing
        };

        let input_cost_usd = (input_tokens as f64 / 1_000_000.0) * input_cost;
        let output_cost_usd = (output_tokens as f64 / 1_000_000.0) * output_cost;

        input_cost_usd + output_cost_usd
    }
}

#[async_trait]
#[async_trait]
impl Provider for OpenAIProvider {
    async fn complete(&self, request: &LLMRequest) -> LLMResult<LLMResponse> {
        // Use retry logic with exponential backoff
        super::retry_with_backoff(&self.config.retry_config, || async {
            self.complete_once(request).await
        })
        .await
    }

    async fn stream(
        &self,
        request: &LLMRequest,
    ) -> LLMResult<Box<dyn futures::Stream<Item = LLMResult<String>> + Unpin + Send>> {
        // Streaming implementation would go here
        // For now, fall back to non-streaming
        let response = self.complete(request).await?;

        use futures::stream;
        let data = vec![Ok(response.text)];
        Ok(Box::new(stream::iter(data)))
    }

    fn name(&self) -> &str {
        "openai"
    }

    async fn health_check(&self) -> LLMResult<bool> {
        // Simple health check - try to list models
        let response = self
            .client
            .get("https://api.openai.com/v1/models")
            .header(
                "Authorization",
                format!("Bearer {}", self.config.api_key.expose_secret()),
            )
            .send()
            .await;

        match response {
            Ok(resp) => Ok(resp.status().is_success()),
            Err(_) => Ok(false),
        }
    }
}

impl OpenAIProvider {
    /// Single completion attempt (used by retry logic)
    async fn complete_once(&self, request: &LLMRequest) -> LLMResult<LLMResponse> {
        // Check rate limits
        self.rate_limiter.check_request(request.max_tokens).await?;

        // Build OpenAI API request
        let openai_req = OpenAIRequest {
            model: self.config.model.clone(),
            messages: vec![OpenAIMessage {
                role: "user".to_string(),
                content: request.prompt.clone(),
            }],
            max_tokens: request.max_tokens,
            temperature: request.temperature,
            stop: request.stop_sequences.clone(),
        };

        // Send request to OpenAI API
        // Note: api_key.expose_secret() only used here for HTTP header - never logged
        let response = self
            .client
            .post("https://api.openai.com/v1/chat/completions")
            .header(
                "Authorization",
                format!("Bearer {}", self.config.api_key.expose_secret()),
            )
            .header("content-type", "application/json")
            .json(&openai_req)
            .send()
            .await
            .map_err(|e| LLMError::ProviderError(format!("HTTP request failed: {}", e)))?;

        // Check for HTTP errors
        if !response.status().is_success() {
            let status = response.status();
            let error_text = response
                .text()
                .await
                .unwrap_or_else(|_| "Unknown error".to_string());
            return Err(LLMError::ProviderError(format!(
                "OpenAI API error ({}): {}",
                status, error_text
            )));
        }

        // Parse response
        let openai_resp: OpenAIResponse = response
            .json()
            .await
            .map_err(|e| LLMError::ProviderError(format!("Failed to parse response: {}", e)))?;

        // Extract text from response
        let text = openai_resp
            .choices
            .first()
            .map(|c| c.message.content.clone())
            .unwrap_or_default();

        // Calculate cost
        let cost = self.calculate_cost(
            openai_resp.usage.prompt_tokens,
            openai_resp.usage.completion_tokens,
        );

        // Track cost
        self.cost_tracker.record_cost(cost)?;

        Ok(LLMResponse {
            text,
            tokens_used: openai_resp.usage.total_tokens,
            cost,
            finish_reason: openai_resp
                .choices
                .first()
                .and_then(|c| c.finish_reason.clone())
                .unwrap_or_else(|| "unknown".to_string()),
        })
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use crate::provider::{CostBudget, RateLimit, RetryConfig};
    use secrecy::Secret;

    #[test]
    fn test_cost_calculation() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "gpt-4-turbo-preview".to_string(),
            max_tokens: 1000,
            temperature: 0.7,
            rate_limit: RateLimit {
                requests_per_minute: 10,
                tokens_per_minute: 100000,
            },
            cost_budget: CostBudget {
                max_cost: 10.0,
                cost_per_token: 0.001,
            },
            retry_config: RetryConfig::default(),
        };

        let provider = OpenAIProvider::new(config);

        // Test GPT-4 Turbo pricing: $10/MTok input, $30/MTok output
        // 1000 input tokens + 500 output tokens
        let cost = provider.calculate_cost(1000, 500);

        // Expected: (1000/1M * 10) + (500/1M * 30) = 0.01 + 0.015 = 0.025
        assert!((cost - 0.025).abs() < 0.0001);
    }

    #[test]
    fn test_gpt35_cost_calculation() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "gpt-3.5-turbo".to_string(),
            max_tokens: 1000,
            temperature: 0.7,
            rate_limit: RateLimit {
                requests_per_minute: 10,
                tokens_per_minute: 100000,
            },
            cost_budget: CostBudget {
                max_cost: 10.0,
                cost_per_token: 0.001,
            },
            retry_config: RetryConfig::default(),
        };

        let provider = OpenAIProvider::new(config);

        // Test GPT-3.5 Turbo pricing: $0.50/MTok input, $1.50/MTok output
        let cost = provider.calculate_cost(1000, 500);

        // Expected: (1000/1M * 0.5) + (500/1M * 1.5) = 0.0005 + 0.00075 = 0.00125
        assert!((cost - 0.00125).abs() < 0.0001);
    }

    #[test]
    fn test_gpt4_cost_calculation() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "gpt-4".to_string(),
            max_tokens: 1000,
            temperature: 0.7,
            rate_limit: RateLimit {
                requests_per_minute: 5,
                tokens_per_minute: 50000,
            },
            cost_budget: CostBudget {
                max_cost: 50.0,
                cost_per_token: 0.001,
            },
            retry_config: RetryConfig::default(),
        };

        let provider = OpenAIProvider::new(config);

        // Test GPT-4 pricing: $30/MTok input, $60/MTok output
        let cost = provider.calculate_cost(2000, 1000);

        // Expected: (2000/1M * 30) + (1000/1M * 60) = 0.06 + 0.06 = 0.12
        assert!((cost - 0.12).abs() < 0.0001);
    }

    #[test]
    fn test_zero_tokens_cost() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "gpt-4-turbo-preview".to_string(),
            max_tokens: 1000,
            temperature: 0.7,
            rate_limit: RateLimit {
                requests_per_minute: 10,
                tokens_per_minute: 100000,
            },
            cost_budget: CostBudget {
                max_cost: 10.0,
                cost_per_token: 0.001,
            },
            retry_config: RetryConfig::default(),
        };

        let provider = OpenAIProvider::new(config);

        // Zero tokens should cost zero
        let cost = provider.calculate_cost(0, 0);
        assert_eq!(cost, 0.0);
    }

    #[test]
    fn test_large_token_count_cost() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "gpt-4-turbo-preview".to_string(),
            max_tokens: 200000,
            temperature: 0.7,
            rate_limit: RateLimit {
                requests_per_minute: 10,
                tokens_per_minute: 200000,
            },
            cost_budget: CostBudget {
                max_cost: 100.0,
                cost_per_token: 0.001,
            },
            retry_config: RetryConfig::default(),
        };

        let provider = OpenAIProvider::new(config);

        // Test with large token counts
        // 50k input + 25k output
        let cost = provider.calculate_cost(50000, 25000);

        // Expected: (50k/1M * 10) + (25k/1M * 30) = 0.5 + 0.75 = 1.25
        assert!((cost - 1.25).abs() < 0.001);
    }

    #[test]
    fn test_provider_name() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "gpt-4-turbo-preview".to_string(),
            max_tokens: 1000,
            temperature: 0.7,
            rate_limit: RateLimit {
                requests_per_minute: 10,
                tokens_per_minute: 100000,
            },
            cost_budget: CostBudget {
                max_cost: 10.0,
                cost_per_token: 0.001,
            },
            retry_config: RetryConfig::default(),
        };

        let provider = OpenAIProvider::new(config);
        assert_eq!(provider.name(), "openai");
    }
}
