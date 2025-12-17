# yuho-config

Centralized configuration management for Yuho.

## Features

- Multi-source configuration loading (files, environment variables, defaults)
- Type-safe configuration with serde
- Support for TOML configuration files
- Environment variable overrides with `YUHO_` prefix
- Platform-specific config file locations

## Usage

```rust
use yuho_config::YuhoConfig;

// Load from default sources (file, env vars, defaults)
let config = YuhoConfig::load()?;

// Or load from specific file
let config = YuhoConfig::load_from_file("custom.toml")?;

// Access configuration
println!("Cache size: {}", config.cache.max_entries);
println!("Request timeout: {}s", config.http.request_timeout_seconds);
```

## Configuration Sources

Configuration is loaded in priority order:

1. **Environment variables** (highest priority)
   - Prefix: `YUHO_`
   - Separator: `__` (double underscore)
   - Example: `YUHO_CACHE__MAX_ENTRIES=2000`

2. **Configuration file**
   - Location: `~/.config/yuho/yuho.toml` (or platform equivalent)
   - Fallback: `./yuho.toml` in current directory

3. **Defaults** (lowest priority)
   - Built-in sensible defaults

## Configuration File

See `yuho.toml.example` in the repository root for a complete example.

Basic structure:

```toml
[cache]
max_entries = 1000
ttl_seconds = 3600

[http]
request_timeout_seconds = 30

[llm]
default_provider = "openai"

[llm.providers.openai]
base_url = "https://api.openai.com/v1"
```

## Environment Variables

Examples:

```bash
# Cache configuration
export YUHO_CACHE__MAX_ENTRIES=2000
export YUHO_CACHE__TTL_SECONDS=7200

# HTTP timeouts
export YUHO_HTTP__REQUEST_TIMEOUT_SECONDS=60

# LLM configuration
export YUHO_LLM__DEFAULT_PROVIDER=claude

# Provider-specific URLs (for testing/staging)
export YUHO_LLM__PROVIDERS__OPENAI__BASE_URL=http://localhost:8080
```

## Configuration Sections

### Cache

- `max_entries`: Maximum number of cache entries (default: 1000)
- `ttl_seconds`: Cache entry lifetime in seconds (default: 3600)
- `enable_persistence`: Save cache to disk (default: false)
- `persistence_path`: Where to save persistent cache

### HTTP

- `connect_timeout_seconds`: Connection timeout (default: 10)
- `request_timeout_seconds`: Request timeout (default: 30)
- `idle_timeout_seconds`: Idle connection timeout (default: 90)

### Documentation

- `base_url`: Base URL for documentation (default: GitHub wiki)
- `external_tools`: URLs for external tools (Mermaid, Alloy, etc.)

### Date Formats

- `default`: Default date format (default: "DD-MM-YYYY")
- `allowed`: List of allowed formats

### Precision

- `float_decimal_places`: Floating point precision (default: 4)
- `money_decimal_places`: Money precision (default: 2)
- `percent_decimal_places`: Percentage precision (default: 4)

### LLM

- `default_provider`: Default LLM provider (default: "openai")
- `fallback_providers`: List of fallback providers
- `token_limits`: Token limits per operation type
- `providers`: Provider-specific configuration (URLs, pricing)
- `rate_limits`: Rate limiting per provider
