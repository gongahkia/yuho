# Yuho LLM Integration

AI-powered features for the Yuho legal specification language using Large Language Models.

## Features

### 1. Statute Parsing
Automatically parse legal statutes and generate Yuho code:

```rust
use yuho_llm::{statute::StatuteParser, provider::MockProvider};

let provider = MockProvider::new();
let parser = StatuteParser::new(provider);

let statute_text = "Section 415: Cheating...";
let parsed = parser.parse(statute_text).await?;

println!("Generated code:\n{}", parsed.generated_code);
```

**Features:**
- Section extraction with structure detection
- Entity recognition (persons, amounts, dates, etc.)
- Automatic Yuho code generation
- Human review interface for validation

### 2. Natural Language Explanations
Generate context-aware explanations for non-technical audiences:

```rust
use yuho_llm::explanation::{ExplanationGenerator, ExplanationRequest, Audience, DetailLevel};

let generator = ExplanationGenerator::new(provider);

let request = ExplanationRequest {
    code: "BoundedInt<0, 100> age := 25".to_string(),
    context: None,
    audience: Audience::Citizen,
    detail_level: DetailLevel::Standard,
};

let explanation = generator.explain(&request).await?;
println!("{}", explanation.summary);
```

**Audiences:**
- `Lawyer` - Legal professionals
- `Judge` - Judicial decision-makers
- `Citizen` - General public
- `Developer` - Software engineers

**Features:**
- Context-aware explanations
- Simplification of complex legal language
- Real-world example generation
- Interactive Q&A system

### 3. Test Scenario Generation
Automatically generate comprehensive test scenarios:

```rust
use yuho_llm::scenario::ScenarioGenerator;

let generator = ScenarioGenerator::new(provider);

let scenarios = generator.generate_scenarios(code, 20).await?;
let coverage = generator.analyze_coverage(&scenarios);

println!("Coverage: {}%", coverage.coverage_percentage);
```

**Scenario Types:**
- **Normal cases** - Typical, everyday situations
- **Edge cases** - Unusual but valid scenarios
- **Boundary conditions** - Min/max values, thresholds
- **Adversarial cases** - Attempts to exploit loopholes

**Features:**
- Comprehensive coverage analysis
- Gap identification
- Automatic test data generation
- Validation and quality metrics

### 4. Provider Abstraction
Unified interface for multiple LLM providers with **retry logic** and **real API calls**:

```rust
use yuho_llm::provider::{
    Provider, LLMRequest, ProviderConfig, RateLimit, CostBudget, RetryConfig,
    OpenAIProvider, ClaudeProvider
};
use secrecy::Secret;

let config = ProviderConfig {
    api_key: Secret::new("your-key".to_string()),
    model: "claude-3-5-sonnet-20241022".to_string(),
    max_tokens: 2000,
    temperature: 0.7,
    rate_limit: RateLimit {
        requests_per_minute: 10,
        tokens_per_minute: 100000,
    },
    cost_budget: CostBudget {
        max_cost: 10.0,
        cost_per_token: 0.001,
    },
    retry_config: RetryConfig {
        max_retries: 3,
        initial_delay_ms: 1000,
        max_delay_ms: 30000,
        backoff_multiplier: 2.0,
    },
};

// Use OpenAI GPT-4
let openai_provider = OpenAIProvider::new(config.clone());

// Or use Anthropic Claude
let claude_provider = ClaudeProvider::new(config);

// Make a request with automatic retry on transient errors
let request = LLMRequest {
    prompt: "Explain this Yuho code...".to_string(),
    max_tokens: 1000,
    temperature: 0.7,
    stop_sequences: vec![],
};

let response = claude_provider.complete(&request).await?;
println!("Response: {}", response.text);
println!("Cost: ${:.4}", response.cost);
println!("Tokens: {}", response.tokens_used);
```

**Supported Providers:**
- ✅ **OpenAI GPT** - GPT-4 Turbo, GPT-4, GPT-3.5 Turbo
  - Endpoint: `https://api.openai.com/v1/chat/completions`
  - Pricing: $10-60/MTok depending on model
  
- ✅ **Anthropic Claude** - Claude 3.5 Sonnet, Opus, Haiku
  - Endpoint: `https://api.anthropic.com/v1/messages`
  - Pricing: $0.25-75/MTok depending on model

- ✅ **Mock Provider** - For testing without API calls

**Features:**
- ✅ **Real HTTP API Calls** - Full reqwest-based HTTP client
- ✅ **Retry Logic with Exponential Backoff** - Automatic retry on transient errors
  - Configurable max retries (default: 3)
  - Exponential backoff (default: 1s → 2s → 4s → max 30s)
  - Only retries `ProviderError` and `RateLimitExceeded`
- ✅ **Rate Limiting** - Per-minute request and token limits
- ✅ **Cost Tracking** - Real-time budget enforcement
- ✅ **Streaming Support** - Fallback implementation (wraps complete())
- ✅ **HTTP Timeouts** - 30s request, 10s connect, 90s idle
- ✅ **Secure API Keys** - Uses `secrecy` crate, never logged

### 5. Response Caching
Reduce API costs with intelligent caching:

```rust
use yuho_llm::cache::{ResponseCache, CacheConfig};
use std::time::Duration;

let cache = ResponseCache::new(CacheConfig {
    max_entries: 1000,
    ttl: Duration::from_secs(3600),
    enable_persistence: true,
});

if let Some(cached) = cache.get("prompt_hash") {
    return Ok(cached);
}

let response = provider.complete(&request).await?;
cache.set("prompt_hash", response.text.clone());
```

**Features:**
- LRU eviction policy
- Configurable TTL
- Hit rate tracking
- Memory-efficient storage

## Architecture

```
yuho-llm/
├── provider/       # LLM provider abstraction
│   ├── mod.rs     # Provider trait, retry logic, rate limiting
│   ├── openai.rs  # OpenAI GPT implementation (real API)
│   ├── claude.rs  # Anthropic Claude implementation (real API)
│   └── mock.rs    # Mock provider for testing
├── statute/        # Statute parsing & code generation
├── explanation/    # Natural language explanations
├── scenario/       # Test scenario generation
├── cache/          # Response caching layer
└── cost.rs         # Cost tracking and budget enforcement
```

## Tests

Run the full test suite:

```bash
cargo test -p yuho-llm
```

Test coverage includes:
- ✅ 36 passing tests
- ✅ Provider abstraction (Mock, OpenAI, Claude)
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting enforcement
- ✅ Cost tracking and budget limits
- ✅ Cache functionality (LRU, TTL, persistence)
- ✅ Statute parsing and code generation
- ✅ Explanation generation
- ✅ Scenario generation

## Configuration

### Environment Variables

```bash
# Provider selection
export YUHO_LLM_PROVIDER=claude  # or openai

# API credentials (stored securely, never logged)
export YUHO_OPENAI_API_KEY=sk-...
export YUHO_CLAUDE_API_KEY=sk-ant-...

# Model configuration
export YUHO_LLM_MODEL=claude-3-5-sonnet-20241022
export YUHO_LLM_MAX_TOKENS=4000
export YUHO_LLM_TEMPERATURE=0.7

# Cost and rate limits
export YUHO_LLM_MAX_COST=10.0
export YUHO_LLM_RATE_LIMIT_RPM=10
export YUHO_LLM_RATE_LIMIT_TPM=100000

# Retry configuration
export YUHO_LLM_MAX_RETRIES=3
export YUHO_LLM_INITIAL_DELAY_MS=1000
export YUHO_LLM_MAX_DELAY_MS=30000
```

### Programmatic Configuration

```rust
use yuho_llm::provider::{ProviderConfig, RateLimit, CostBudget, RetryConfig};
use secrecy::Secret;

let config = ProviderConfig {
    api_key: Secret::new(std::env::var("YUHO_CLAUDE_API_KEY")?),
    model: "claude-3-5-sonnet-20241022".to_string(),
    max_tokens: 4000,
    temperature: 0.7,
    rate_limit: RateLimit {
        requests_per_minute: 10,
        tokens_per_minute: 100000,
    },
    cost_budget: CostBudget {
        max_cost: 10.0,
        cost_per_token: 0.00003, // $3/MTok input for Claude 3.5 Sonnet
    },
    retry_config: RetryConfig::default(),
};
```

## Examples

See the `examples/` directory for complete, runnable examples:

### 1. LLM Provider Usage (`examples/llm_usage.rs`)

Demonstrates real API calls with retry logic:

```bash
# Set API keys
export YUHO_CLAUDE_API_KEY=sk-ant-...
export YUHO_OPENAI_API_KEY=sk-...

# Run example
cargo run --example llm_usage -p yuho-llm
```

Shows:
- Configuring OpenAI and Claude providers
- Making API calls with automatic retry
- Cost tracking and rate limiting  
- Handling different error types
- Exponential backoff behavior

### 2. Statute Parsing (`examples/statute_parsing.rs`)

Parse legal statutes and generate Yuho code:

```bash
cargo run --example statute_parsing -p yuho-llm
```

Shows:
- Parsing Singapore Penal Code Section 415
- Extracting entities and structure
- Generating Yuho code
- Validation workflow

### Quick Start Example

```rust
use yuho_llm::{
    provider::{ClaudeProvider, ProviderConfig, RateLimit, CostBudget, RetryConfig},
    statute::StatuteParser,
};
use secrecy::Secret;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Configure provider with retry logic
    let config = ProviderConfig {
        api_key: Secret::new(std::env::var("YUHO_CLAUDE_API_KEY")?),
        model: "claude-3-5-sonnet-20241022".to_string(),
        max_tokens: 4000,
        temperature: 0.7,
        rate_limit: RateLimit {
            requests_per_minute: 5,
            tokens_per_minute: 50000,
        },
        cost_budget: CostBudget {
            max_cost: 5.0,
            cost_per_token: 0.00003,
        },
        retry_config: RetryConfig::default(), // 3 retries with exponential backoff
    };

    let provider = ClaudeProvider::new(config);
    let parser = StatuteParser::new(provider);

    // Parse statute
    let statute = r#"
        Section 415: Cheating
        Whoever by deceiving any person fraudulently or dishonestly
        induces the person so deceived to deliver any property...
    "#;

    let parsed = parser.parse(statute).await?;
    println!("Generated code:\n{}", parsed.generated_code);

    // Validate
    let errors = parser.validate_code(&parsed.generated_code)?;
    if errors.is_empty() {
        println!("✓ Code is valid!");
    }

    Ok(())
}
```

## Cost Management

Track and limit API costs:

```rust
use yuho_llm::provider::{CostTracker, CostBudget};

let tracker = CostTracker::new(CostBudget {
    max_cost: 10.0,
    cost_per_token: 0.00001, // $10/MTok
});

// Automatically tracked by providers
// Each API call records its cost
// Will return CostBudgetExceeded error when limit reached

println!("Spent: ${:.4}", tracker.get_spent());
println!("Remaining: ${:.4}", tracker.get_remaining());
```

## Error Handling

The retry logic automatically handles transient errors:

```rust
use yuho_llm::LLMError;

match parser.parse(statute).await {
    Ok(parsed) => println!("Success!"),
    Err(LLMError::RateLimitExceeded) => {
        // Automatically retried with exponential backoff
        // This error means all retries failed
        println!("Rate limit persistent after retries");
    }
    Err(LLMError::CostBudgetExceeded(spent)) => {
        println!("Budget exceeded: ${:.4}", spent);
    }
    Err(LLMError::ProviderError(msg)) => {
        // Automatically retried up to max_retries
        // This error means all retries failed
        println!("Provider error after retries: {}", msg);
    }
    Err(e) => println!("Non-retryable error: {}", e),
}
```

## Testing

Run the full test suite:

```bash
# All tests (36 passing)
cargo test -p yuho-llm

# Specific test categories
cargo test -p yuho-llm retry      # Retry logic tests
cargo test -p yuho-llm provider   # Provider tests
cargo test -p yuho-llm cost       # Cost tracking tests
```

Test coverage:
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting enforcement
- ✅ Cost tracking and budget limits
- ✅ OpenAI and Claude providers
- ✅ Statute parsing workflow
- ✅ Cache functionality

## Production Checklist

Before deploying LLM features:

- [ ] Set API keys securely (use environment variables or secrets management)
- [ ] Configure appropriate rate limits for your tier
- [ ] Set realistic cost budgets with monitoring
- [ ] Enable response caching to reduce costs
- [ ] Test retry logic with mock failures
- [ ] Implement logging for API costs and errors
- [ ] Monitor token usage and adjust limits
- [ ] Have fallback behavior for API outages

## Security

- **API Keys**: Uses `secrecy` crate, never logged or printed
- **HTTP Timeouts**: Prevents hanging requests (30s timeout)
- **Rate Limiting**: Protects against quota exhaustion
- **Cost Limits**: Hard caps prevent runaway costs
- **Retry Limits**: Prevents infinite retry loops (max 3 by default)

## Pricing Reference (as of 2025)

### OpenAI GPT
- **GPT-4 Turbo**: $10/MTok input, $30/MTok output
- **GPT-4**: $30/MTok input, $60/MTok output  
- **GPT-3.5 Turbo**: $0.50/MTok input, $1.50/MTok output

### Anthropic Claude
- **Claude 3.5 Sonnet**: $3/MTok input, $15/MTok output
- **Claude 3 Opus**: $15/MTok input, $75/MTok output
- **Claude 3 Haiku**: $0.25/MTok input, $1.25/MTok output

Cost per typical statute parse (~2K input, ~500 output):
- Claude 3.5 Sonnet: ~$0.014
- GPT-4 Turbo: ~$0.035
- GPT-3.5 Turbo: ~$0.002

## Contributing

When adding new LLM features:

1. Implement the feature with the MockProvider first
2. Add comprehensive unit tests
3. Update the Provider trait if needed
4. Add real API implementation for OpenAI/Claude
5. Document cost implications
6. Add example usage

## License

MIT License - see root LICENSE file


## License

MIT

## Contributing

Contributions welcome! See CONTRIBUTING.md for guidelines.
