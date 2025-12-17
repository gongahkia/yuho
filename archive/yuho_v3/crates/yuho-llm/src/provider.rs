//! LLM provider abstraction
//!
//! Supports multiple LLM providers with unified interface

pub mod claude;
pub mod openai;

pub use claude::ClaudeProvider;
pub use openai::OpenAIProvider;

use crate::{LLMError, LLMResult};
use async_trait::async_trait;
use secrecy::Secret;
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

/// Retry configuration for transient errors
#[derive(Debug, Clone)]
pub struct RetryConfig {
    pub max_retries: usize,
    pub initial_delay_ms: u64,
    pub max_delay_ms: u64,
    pub backoff_multiplier: f64,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_retries: 3,
            initial_delay_ms: 1000,  // 1 second
            max_delay_ms: 30000,     // 30 seconds
            backoff_multiplier: 2.0, // Exponential backoff
        }
    }
}

/// LLM provider configuration
#[derive(Clone)]
pub struct ProviderConfig {
    /// API key stored securely (never logged or printed)
    pub api_key: Secret<String>,
    pub model: String,
    pub max_tokens: usize,
    pub temperature: f32,
    pub rate_limit: RateLimit,
    pub cost_budget: CostBudget,
    pub retry_config: RetryConfig,
}

impl std::fmt::Debug for ProviderConfig {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ProviderConfig")
            .field("api_key", &"[REDACTED]")
            .field("model", &self.model)
            .field("max_tokens", &self.max_tokens)
            .field("temperature", &self.temperature)
            .field("rate_limit", &self.rate_limit)
            .field("cost_budget", &self.cost_budget)
            .field("retry_config", &self.retry_config)
            .finish()
    }
}

/// Rate limiting configuration
#[derive(Debug, Clone)]
pub struct RateLimit {
    pub requests_per_minute: usize,
    pub tokens_per_minute: usize,
}

/// Cost budget tracking
#[derive(Debug, Clone)]
pub struct CostBudget {
    pub max_cost: f64,
    pub cost_per_token: f64,
}

/// LLM request
#[derive(Debug, Clone, Serialize)]
pub struct LLMRequest {
    pub prompt: String,
    pub max_tokens: usize,
    pub temperature: f32,
    pub stop_sequences: Vec<String>,
}

/// LLM response
#[derive(Debug, Clone, Deserialize)]
pub struct LLMResponse {
    pub text: String,
    pub tokens_used: usize,
    pub cost: f64,
    pub finish_reason: String,
}

/// Provider trait for LLM backends
#[async_trait]
pub trait Provider: Send + Sync {
    /// Send a completion request
    async fn complete(&self, request: &LLMRequest) -> LLMResult<LLMResponse>;

    /// Stream a completion response
    async fn stream(
        &self,
        request: &LLMRequest,
    ) -> LLMResult<Box<dyn futures::Stream<Item = LLMResult<String>> + Unpin + Send>>;

    /// Get provider name
    fn name(&self) -> &str;

    /// Check if provider is available
    async fn health_check(&self) -> LLMResult<bool>;
}

/// Retry a future with exponential backoff
pub async fn retry_with_backoff<F, Fut, T>(config: &RetryConfig, mut operation: F) -> LLMResult<T>
where
    F: FnMut() -> Fut,
    Fut: std::future::Future<Output = LLMResult<T>>,
{
    let mut attempt = 0;
    let mut delay_ms = config.initial_delay_ms;

    loop {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) => {
                attempt += 1;

                // Check if error is retryable
                let is_retryable =
                    matches!(e, LLMError::ProviderError(_) | LLMError::RateLimitExceeded);

                if !is_retryable || attempt >= config.max_retries {
                    return Err(e);
                }

                // Sleep with exponential backoff
                tokio::time::sleep(Duration::from_millis(delay_ms)).await;

                // Calculate next delay
                delay_ms = (delay_ms as f64 * config.backoff_multiplier) as u64;
                delay_ms = delay_ms.min(config.max_delay_ms);
            },
        }
    }
}

/// Rate limiter implementation
pub struct RateLimiter {
    config: RateLimit,
    requests: Arc<Mutex<VecDeque<Instant>>>,
    tokens: Arc<Mutex<VecDeque<(Instant, usize)>>>,
}

impl RateLimiter {
    pub fn new(config: RateLimit) -> Self {
        Self {
            config,
            requests: Arc::new(Mutex::new(VecDeque::new())),
            tokens: Arc::new(Mutex::new(VecDeque::new())),
        }
    }

    /// Check if request is allowed under rate limits
    pub async fn check_request(&self, tokens: usize) -> LLMResult<()> {
        let now = Instant::now();
        let minute_ago = now - Duration::from_secs(60);

        // Clean old requests
        {
            let mut reqs = self.requests.lock()
                .expect("Rate limiter request mutex poisoned - this should never happen in single-threaded context");
            while let Some(&first) = reqs.front() {
                if first < minute_ago {
                    reqs.pop_front();
                } else {
                    break;
                }
            }

            if reqs.len() >= self.config.requests_per_minute {
                return Err(LLMError::RateLimitExceeded);
            }
        }

        // Clean old tokens
        {
            let mut toks = self.tokens.lock()
                .expect("Rate limiter token mutex poisoned - this should never happen in single-threaded context");
            while let Some(&(first, _)) = toks.front() {
                if first < minute_ago {
                    toks.pop_front();
                } else {
                    break;
                }
            }

            let total_tokens: usize = toks.iter().map(|(_, t)| t).sum();
            if total_tokens + tokens > self.config.tokens_per_minute {
                return Err(LLMError::RateLimitExceeded);
            }
        }

        // Record this request
        self.requests.lock()
            .expect("Rate limiter request mutex poisoned - this should never happen in single-threaded context")
            .push_back(now);
        self.tokens.lock()
            .expect("Rate limiter token mutex poisoned - this should never happen in single-threaded context")
            .push_back((now, tokens));

        Ok(())
    }
}

/// Cost tracker
pub struct CostTracker {
    config: CostBudget,
    spent: Arc<Mutex<f64>>,
}

impl CostTracker {
    pub fn new(config: CostBudget) -> Self {
        Self {
            config,
            spent: Arc::new(Mutex::new(0.0)),
        }
    }

    /// Record cost and check budget
    pub fn record_cost(&self, cost: f64) -> LLMResult<()> {
        let mut spent = self.spent.lock().expect(
            "Cost tracker mutex poisoned - this should never happen in single-threaded context",
        );
        *spent += cost;

        if *spent > self.config.max_cost {
            Err(LLMError::CostBudgetExceeded(*spent))
        } else {
            Ok(())
        }
    }

    /// Get total spent
    pub fn get_spent(&self) -> f64 {
        *self.spent.lock().expect(
            "Cost tracker mutex poisoned - this should never happen in single-threaded context",
        )
    }

    /// Get remaining budget
    pub fn get_remaining(&self) -> f64 {
        self.config.max_cost - self.get_spent()
    }
}

/// Mock provider for testing
pub struct MockProvider {
    name: String,
}

impl MockProvider {
    pub fn new() -> Self {
        Self {
            name: "mock".to_string(),
        }
    }
}

#[async_trait]
impl Provider for MockProvider {
    async fn complete(&self, request: &LLMRequest) -> LLMResult<LLMResponse> {
        Ok(LLMResponse {
            text: format!(
                "Mock response to: {}",
                &request.prompt[..50.min(request.prompt.len())]
            ),
            tokens_used: 100,
            cost: 0.01,
            finish_reason: "stop".to_string(),
        })
    }

    async fn stream(
        &self,
        _request: &LLMRequest,
    ) -> LLMResult<Box<dyn futures::Stream<Item = LLMResult<String>> + Unpin + Send>> {
        use futures::stream;
        let data = vec![Ok("Mock".to_string()), Ok(" stream".to_string())];
        Ok(Box::new(stream::iter(data)))
    }

    fn name(&self) -> &str {
        &self.name
    }

    async fn health_check(&self) -> LLMResult<bool> {
        Ok(true)
    }
}

impl Default for MockProvider {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mock_provider() {
        let provider = MockProvider::new();
        let request = LLMRequest {
            prompt: "Test prompt".to_string(),
            max_tokens: 100,
            temperature: 0.7,
            stop_sequences: vec![],
        };

        let response = provider.complete(&request).await.unwrap();
        assert!(!response.text.is_empty());
        assert!(response.tokens_used > 0);
    }

    #[tokio::test]
    async fn test_rate_limiter() {
        let limiter = RateLimiter::new(RateLimit {
            requests_per_minute: 10,
            tokens_per_minute: 1000,
        });

        // Should allow first request
        assert!(limiter.check_request(100).await.is_ok());

        // Should allow within limits
        for _ in 0..9 {
            assert!(limiter.check_request(50).await.is_ok());
        }

        // Should deny when limit exceeded
        assert!(matches!(
            limiter.check_request(100).await,
            Err(LLMError::RateLimitExceeded)
        ));
    }

    #[test]
    fn test_cost_tracker() {
        let tracker = CostTracker::new(CostBudget {
            max_cost: 10.0,
            cost_per_token: 0.001,
        });

        assert!(tracker.record_cost(5.0).is_ok());
        assert_eq!(tracker.get_spent(), 5.0);
        assert_eq!(tracker.get_remaining(), 5.0);

        assert!(tracker.record_cost(6.0).is_err());
    }

    #[tokio::test]
    async fn test_retry_logic_success() {
        let config = RetryConfig::default();

        let result = retry_with_backoff(&config, || {
            static mut ATTEMPT: i32 = 0;
            async {
                unsafe {
                    ATTEMPT += 1;
                    if ATTEMPT < 2 {
                        Err(LLMError::ProviderError("Temporary error".to_string()))
                    } else {
                        ATTEMPT = 0; // Reset for next test
                        Ok("Success".to_string())
                    }
                }
            }
        })
        .await;

        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_retry_logic_max_retries() {
        let config = RetryConfig {
            max_retries: 2,
            initial_delay_ms: 10,
            max_delay_ms: 100,
            backoff_multiplier: 2.0,
        };

        let result = retry_with_backoff(&config, || async {
            Err::<(), _>(LLMError::ProviderError("Persistent error".to_string()))
        })
        .await;

        assert!(result.is_err());
    }

    #[tokio::test]
    async fn test_retry_logic_non_retryable() {
        let config = RetryConfig::default();

        let result = retry_with_backoff(&config, || async {
            Err::<(), _>(LLMError::ParsingError("Bad request".to_string()))
        })
        .await;

        assert!(result.is_err());
    }

    #[test]
    fn test_retry_config_defaults() {
        let config = RetryConfig::default();
        assert_eq!(config.max_retries, 3);
        assert_eq!(config.initial_delay_ms, 1000);
        assert_eq!(config.max_delay_ms, 30000);
        assert_eq!(config.backoff_multiplier, 2.0);
    }
}
