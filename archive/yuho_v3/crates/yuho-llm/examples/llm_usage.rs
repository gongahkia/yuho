//! Example: Using LLM providers with retry logic
//!
//! This example demonstrates:
//! 1. Configuring OpenAI and Claude providers
//! 2. Making API calls with automatic retry on errors
//! 3. Cost tracking and rate limiting
//! 4. Handling different error types
//!
//! Run with:
//!   cargo run --example llm_usage
//!
//! Requires environment variables:
//!   export YUHO_OPENAI_API_KEY=sk-...
//!   export YUHO_CLAUDE_API_KEY=sk-ant-...

use secrecy::Secret;
use std::env;
use yuho_llm::provider::{
    ClaudeProvider, CostBudget, LLMRequest, OpenAIProvider, Provider, ProviderConfig, RateLimit,
    RetryConfig,
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Yuho LLM Provider Example ===\n");

    // Example 1: Using Claude with retry logic
    println!("Example 1: Claude API with Retry Logic");
    println!("----------------------------------------");

    if let Ok(api_key) = env::var("YUHO_CLAUDE_API_KEY") {
        let config = ProviderConfig {
            api_key: Secret::new(api_key),
            model: "claude-3-5-sonnet-20241022".to_string(),
            max_tokens: 1000,
            temperature: 0.7,
            rate_limit: RateLimit {
                requests_per_minute: 5,
                tokens_per_minute: 50000,
            },
            cost_budget: CostBudget {
                max_cost: 1.0,
                cost_per_token: 0.00003, // $3/MTok
            },
            retry_config: RetryConfig {
                max_retries: 3,
                initial_delay_ms: 1000,
                max_delay_ms: 10000,
                backoff_multiplier: 2.0,
            },
        };

        let provider = ClaudeProvider::new(config);

        let request = LLMRequest {
            prompt: r#"Explain this Yuho legal code in simple terms:

struct CheatingCase {
    string accused_name,
    string victim_name,
    money amount,
    bool induced_delivery,
}

What does this represent in legal terms?"#
                .to_string(),
            max_tokens: 500,
            temperature: 0.7,
            stop_sequences: vec![],
        };

        println!("Sending request to Claude...");
        match provider.complete(&request).await {
            Ok(response) => {
                println!("\n✅ Response received:");
                println!("{}", response.text);
                println!("\n📊 Metrics:");
                println!("  - Tokens used: {}", response.tokens_used);
                println!("  - Cost: ${:.6}", response.cost);
                println!("  - Finish reason: {}", response.finish_reason);
            },
            Err(e) => {
                println!("\n❌ Error: {}", e);
                println!("The retry logic attempted up to 3 times with exponential backoff");
            },
        }
    } else {
        println!("⚠️  YUHO_CLAUDE_API_KEY not set, skipping Claude example");
    }

    println!("\n");

    // Example 2: Using OpenAI GPT-4
    println!("Example 2: OpenAI GPT-4 with Cost Tracking");
    println!("-------------------------------------------");

    if let Ok(api_key) = env::var("YUHO_OPENAI_API_KEY") {
        let config = ProviderConfig {
            api_key: Secret::new(api_key),
            model: "gpt-4-turbo-preview".to_string(),
            max_tokens: 500,
            temperature: 0.5,
            rate_limit: RateLimit {
                requests_per_minute: 3,
                tokens_per_minute: 30000,
            },
            cost_budget: CostBudget {
                max_cost: 0.50,          // $0.50 budget
                cost_per_token: 0.00001, // $10/MTok
            },
            retry_config: RetryConfig::default(),
        };

        let provider = OpenAIProvider::new(config);

        let request = LLMRequest {
            prompt: "Generate a test case for a Yuho legal contract specification.".to_string(),
            max_tokens: 300,
            temperature: 0.8,
            stop_sequences: vec![],
        };

        println!("Sending request to OpenAI GPT-4...");
        match provider.complete(&request).await {
            Ok(response) => {
                println!("\n✅ Response received:");
                println!("{}", response.text);
                println!("\n📊 Metrics:");
                println!("  - Tokens used: {}", response.tokens_used);
                println!("  - Cost: ${:.6}", response.cost);
                println!("  - Remaining budget: ${:.6}", 0.50 - response.cost);
            },
            Err(e) => {
                println!("\n❌ Error: {}", e);
            },
        }
    } else {
        println!("⚠️  YUHO_OPENAI_API_KEY not set, skipping OpenAI example");
    }

    println!("\n");

    // Example 3: Demonstrating retry behavior with mock failures
    println!("Example 3: Retry Logic Demonstration");
    println!("-------------------------------------");
    println!("The retry logic will:");
    println!("  1. Retry on ProviderError (HTTP failures, timeouts)");
    println!("  2. Retry on RateLimitExceeded");
    println!("  3. NOT retry on other errors (invalid API key, bad request)");
    println!("  4. Use exponential backoff: 1s → 2s → 4s → 8s (up to max)");
    println!("\nRetry delays:");

    let config = RetryConfig {
        max_retries: 3,
        initial_delay_ms: 1000,
        max_delay_ms: 10000,
        backoff_multiplier: 2.0,
    };

    let mut delay = config.initial_delay_ms;
    for attempt in 1..=config.max_retries {
        println!("  Attempt {}: wait {}ms before retry", attempt, delay);
        delay = ((delay as f64) * config.backoff_multiplier) as u64;
        delay = delay.min(config.max_delay_ms);
    }

    println!("\n=== Example Complete ===");
    println!("\nTo run with real API calls:");
    println!("  export YUHO_CLAUDE_API_KEY=sk-ant-...");
    println!("  export YUHO_OPENAI_API_KEY=sk-...");
    println!("  cargo run --example llm_usage");

    Ok(())
}
