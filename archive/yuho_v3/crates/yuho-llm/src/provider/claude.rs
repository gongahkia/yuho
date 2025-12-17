//! Anthropic Claude provider implementation

use super::{CostTracker, LLMRequest, LLMResponse, Provider, ProviderConfig, RateLimiter};
use crate::{LLMError, LLMResult};
use async_trait::async_trait;
use reqwest::Client;
use secrecy::ExposeSecret;
use serde::{Deserialize, Serialize};

/// Anthropic Claude API provider
pub struct ClaudeProvider {
    config: ProviderConfig,
    client: Client,
    rate_limiter: RateLimiter,
    cost_tracker: CostTracker,
}

/// Claude API request format
#[derive(Debug, Serialize)]
struct ClaudeRequest {
    model: String,
    max_tokens: usize,
    messages: Vec<ClaudeMessage>,
    temperature: f32,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    stop_sequences: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ClaudeMessage {
    role: String,
    content: String,
}

/// Claude API response format
#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct ClaudeResponse {
    id: String,
    #[serde(rename = "type")]
    response_type: String,
    role: String,
    content: Vec<ClaudeContent>,
    model: String,
    stop_reason: Option<String>,
    stop_sequence: Option<String>,
    usage: ClaudeUsage,
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct ClaudeContent {
    #[serde(rename = "type")]
    content_type: String,
    text: String,
}

#[derive(Debug, Deserialize)]
struct ClaudeUsage {
    input_tokens: usize,
    output_tokens: usize,
}

impl ClaudeProvider {
    /// Create a new Claude provider with configured timeouts
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

    /// Calculate cost for Claude API usage
    /// Pricing as of 2025 (approximate):
    /// - Claude 3.5 Sonnet: $3/MTok input, $15/MTok output
    /// - Claude 3 Opus: $15/MTok input, $75/MTok output
    /// - Claude 3 Haiku: $0.25/MTok input, $1.25/MTok output
    fn calculate_cost(&self, input_tokens: usize, output_tokens: usize) -> f64 {
        let (input_cost, output_cost) = match self.config.model.as_str() {
            "claude-3-5-sonnet-20241022" | "claude-3-5-sonnet-20240620" => (3.0, 15.0),
            "claude-3-opus-20240229" => (15.0, 75.0),
            "claude-3-haiku-20240307" => (0.25, 1.25),
            _ => (3.0, 15.0), // Default to Sonnet pricing
        };

        let input_cost_usd = (input_tokens as f64 / 1_000_000.0) * input_cost;
        let output_cost_usd = (output_tokens as f64 / 1_000_000.0) * output_cost;

        input_cost_usd + output_cost_usd
    }
}

#[async_trait]
impl Provider for ClaudeProvider {
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
        "claude"
    }

    async fn health_check(&self) -> LLMResult<bool> {
        // Simple health check - try to list models (or a minimal request)
        let test_req = ClaudeRequest {
            model: self.config.model.clone(),
            max_tokens: 10,
            messages: vec![ClaudeMessage {
                role: "user".to_string(),
                content: "test".to_string(),
            }],
            temperature: 0.0,
            stop_sequences: vec![],
        };

        let response = self
            .client
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", self.config.api_key.expose_secret())
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&test_req)
            .send()
            .await;

        match response {
            Ok(resp) => Ok(resp.status().is_success()),
            Err(_) => Ok(false),
        }
    }
}

impl ClaudeProvider {
    /// Single completion attempt (used by retry logic)
    async fn complete_once(&self, request: &LLMRequest) -> LLMResult<LLMResponse> {
        // Check rate limits
        self.rate_limiter.check_request(request.max_tokens).await?;

        // Build Claude API request
        let claude_req = ClaudeRequest {
            model: self.config.model.clone(),
            max_tokens: request.max_tokens,
            messages: vec![ClaudeMessage {
                role: "user".to_string(),
                content: request.prompt.clone(),
            }],
            temperature: request.temperature,
            stop_sequences: request.stop_sequences.clone(),
        };

        // Send request to Claude API
        // Note: api_key.expose_secret() only used here for HTTP header - never logged
        let response = self
            .client
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", self.config.api_key.expose_secret())
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&claude_req)
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
                "Claude API error ({}): {}",
                status, error_text
            )));
        }

        // Parse response
        let claude_resp: ClaudeResponse = response
            .json()
            .await
            .map_err(|e| LLMError::ProviderError(format!("Failed to parse response: {}", e)))?;

        // Extract text from response
        let text = claude_resp
            .content
            .first()
            .map(|c| c.text.clone())
            .unwrap_or_default();

        // Calculate cost
        let cost = self.calculate_cost(
            claude_resp.usage.input_tokens,
            claude_resp.usage.output_tokens,
        );

        // Track cost
        self.cost_tracker.record_cost(cost)?;

        Ok(LLMResponse {
            text,
            tokens_used: claude_resp.usage.input_tokens + claude_resp.usage.output_tokens,
            cost,
            finish_reason: claude_resp
                .stop_reason
                .unwrap_or_else(|| "unknown".to_string()),
        })
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
        "claude"
    }

    async fn health_check(&self) -> LLMResult<bool> {
        // Simple health check - try to list models (or a minimal request)
        let test_req = ClaudeRequest {
            model: self.config.model.clone(),
            max_tokens: 10,
            messages: vec![ClaudeMessage {
                role: "user".to_string(),
                content: "test".to_string(),
            }],
            temperature: 0.0,
            stop_sequences: vec![],
        };

        let response = self
            .client
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", self.config.api_key.expose_secret())
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&test_req)
            .send()
            .await;

        match response {
            Ok(resp) => Ok(resp.status().is_success()),
            Err(_) => Ok(false),
        }
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
            model: "claude-3-5-sonnet-20241022".to_string(),
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

        let provider = ClaudeProvider::new(config);

        // Test Sonnet pricing: $3/MTok input, $15/MTok output
        // 1000 input tokens + 500 output tokens
        let cost = provider.calculate_cost(1000, 500);

        // Expected: (1000/1M * 3) + (500/1M * 15) = 0.003 + 0.0075 = 0.0105
        assert!((cost - 0.0105).abs() < 0.0001);
    }

    #[test]
    fn test_haiku_cost_calculation() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "claude-3-haiku-20240307".to_string(),
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

        let provider = ClaudeProvider::new(config);

        // Test Haiku pricing: $0.25/MTok input, $1.25/MTok output
        let cost = provider.calculate_cost(1000, 500);

        // Expected: (1000/1M * 0.25) + (500/1M * 1.25) = 0.00025 + 0.000625 = 0.000875
        assert!((cost - 0.000875).abs() < 0.0001);
    }

    #[test]
    fn test_opus_cost_calculation() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "claude-3-opus-20240229".to_string(),
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

        let provider = ClaudeProvider::new(config);

        // Test Opus pricing: $15/MTok input, $75/MTok output
        let cost = provider.calculate_cost(2000, 1000);

        // Expected: (2000/1M * 15) + (1000/1M * 75) = 0.03 + 0.075 = 0.105
        assert!((cost - 0.105).abs() < 0.0001);
    }

    #[test]
    fn test_zero_tokens_cost() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "claude-3-5-sonnet-20241022".to_string(),
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

        let provider = ClaudeProvider::new(config);

        // Zero tokens should cost zero
        let cost = provider.calculate_cost(0, 0);
        assert_eq!(cost, 0.0);
    }

    #[test]
    fn test_large_token_count_cost() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "claude-3-5-sonnet-20241022".to_string(),
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

        let provider = ClaudeProvider::new(config);

        // Test with large token counts
        // 100k input + 50k output
        let cost = provider.calculate_cost(100000, 50000);

        // Expected: (100k/1M * 3) + (50k/1M * 15) = 0.3 + 0.75 = 1.05
        assert!((cost - 1.05).abs() < 0.001);
    }

    #[test]
    fn test_provider_name() {
        let config = ProviderConfig {
            api_key: Secret::new("test-key".to_string()),
            model: "claude-3-5-sonnet-20241022".to_string(),
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

        let provider = ClaudeProvider::new(config);
        assert_eq!(provider.name(), "claude");
    }
}
