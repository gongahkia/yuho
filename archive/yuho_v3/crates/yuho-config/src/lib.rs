//! Configuration system for Yuho
//!
//! This crate provides centralized configuration management for all Yuho components.
//! Configuration can be loaded from multiple sources (in priority order):
//! 1. Command-line arguments (highest priority)
//! 2. Environment variables
//! 3. Configuration file (yuho.toml)
//! 4. Defaults (lowest priority)

use config::{Config, ConfigError, Environment, File};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

/// Main configuration structure for Yuho
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct YuhoConfig {
    /// LLM provider configuration
    #[serde(default)]
    pub llm: LlmConfig,

    /// Cache configuration
    #[serde(default)]
    pub cache: CacheConfig,

    /// HTTP client configuration
    #[serde(default)]
    pub http: HttpConfig,

    /// Documentation URLs
    #[serde(default)]
    pub docs: DocsConfig,

    /// Date format configuration
    #[serde(default)]
    pub date_formats: DateFormatConfig,

    /// Precision configuration
    #[serde(default)]
    pub precision: PrecisionConfig,
}

/// LLM provider configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmConfig {
    /// Provider configurations by name
    #[serde(default)]
    pub providers: HashMap<String, ProviderConfig>,

    /// Default provider to use
    #[serde(default = "default_provider")]
    pub default_provider: String,

    /// Fallback providers in order
    #[serde(default)]
    pub fallback_providers: Vec<String>,

    /// Token limits per operation
    #[serde(default)]
    pub token_limits: TokenLimits,

    /// Rate limiting configuration
    #[serde(default)]
    pub rate_limits: HashMap<String, RateLimitConfig>,
}

/// Configuration for a specific LLM provider
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProviderConfig {
    /// Base URL for API
    pub base_url: String,

    /// API version
    #[serde(default)]
    pub api_version: Option<String>,

    /// Pricing per model
    #[serde(default)]
    pub pricing: HashMap<String, ModelPricing>,
}

/// Pricing for a specific model
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelPricing {
    /// Cost per million input tokens (USD)
    pub input_price_per_mtok: f64,

    /// Cost per million output tokens (USD)
    pub output_price_per_mtok: f64,

    /// Effective date of pricing
    #[serde(default)]
    pub effective_date: Option<String>,
}

/// Token limits for different operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenLimits {
    #[serde(default = "default_explanation_tokens")]
    pub explanation_max_tokens: usize,

    #[serde(default = "default_statute_tokens")]
    pub statute_parsing_max_tokens: usize,

    #[serde(default = "default_test_gen_tokens")]
    pub test_generation_max_tokens: usize,

    #[serde(default = "default_contract_tokens")]
    pub contract_generation_max_tokens: usize,

    #[serde(default = "default_reasoning_tokens")]
    pub legal_reasoning_max_tokens: usize,
}

/// Rate limiting configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RateLimitConfig {
    /// Requests per minute
    #[serde(default = "default_rpm")]
    pub requests_per_minute: u32,

    /// Tokens per minute
    #[serde(default = "default_tpm")]
    pub tokens_per_minute: u32,

    /// Burst size
    #[serde(default = "default_burst")]
    pub burst_size: u32,
}

/// Cache configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheConfig {
    /// Maximum number of entries
    #[serde(default = "default_cache_size")]
    pub max_entries: usize,

    /// TTL in seconds
    #[serde(default = "default_cache_ttl")]
    pub ttl_seconds: u64,

    /// Enable persistence
    #[serde(default)]
    pub enable_persistence: bool,

    /// Path for persistent cache
    #[serde(default)]
    pub persistence_path: Option<PathBuf>,
}

/// HTTP client configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpConfig {
    /// Connection timeout in seconds
    #[serde(default = "default_connect_timeout")]
    pub connect_timeout_seconds: u64,

    /// Request timeout in seconds
    #[serde(default = "default_request_timeout")]
    pub request_timeout_seconds: u64,

    /// Idle timeout in seconds
    #[serde(default = "default_idle_timeout")]
    pub idle_timeout_seconds: u64,
}

/// Documentation configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocsConfig {
    /// Base URL for documentation
    #[serde(default = "default_docs_url")]
    pub base_url: String,

    /// External tool URLs
    #[serde(default)]
    pub external_tools: HashMap<String, String>,
}

/// Date format configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DateFormatConfig {
    /// Default date format
    #[serde(default = "default_date_format")]
    pub default: String,

    /// Allowed date formats
    #[serde(default = "default_allowed_formats")]
    pub allowed: Vec<String>,
}

/// Precision configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PrecisionConfig {
    /// Decimal places for floats
    #[serde(default = "default_float_precision")]
    pub float_decimal_places: usize,

    /// Decimal places for money
    #[serde(default = "default_money_precision")]
    pub money_decimal_places: usize,

    /// Decimal places for percentages
    #[serde(default = "default_percent_precision")]
    pub percent_decimal_places: usize,
}

// Default value functions
fn default_provider() -> String {
    "openai".to_string()
}

fn default_explanation_tokens() -> usize {
    1000
}

fn default_statute_tokens() -> usize {
    2000
}

fn default_test_gen_tokens() -> usize {
    1500
}

fn default_contract_tokens() -> usize {
    3000
}

fn default_reasoning_tokens() -> usize {
    2500
}

fn default_rpm() -> u32 {
    60
}

fn default_tpm() -> u32 {
    90000
}

fn default_burst() -> u32 {
    10
}

fn default_cache_size() -> usize {
    1000
}

fn default_cache_ttl() -> u64 {
    3600
}

fn default_connect_timeout() -> u64 {
    10
}

fn default_request_timeout() -> u64 {
    30
}

fn default_idle_timeout() -> u64 {
    90
}

fn default_docs_url() -> String {
    "https://github.com/gongahkia/yuho-2/wiki".to_string()
}

fn default_date_format() -> String {
    "DD-MM-YYYY".to_string()
}

fn default_allowed_formats() -> Vec<String> {
    vec![
        "DD-MM-YYYY".to_string(),
        "YYYY-MM-DD".to_string(),
        "MM/DD/YYYY".to_string(),
    ]
}

fn default_float_precision() -> usize {
    4
}

fn default_money_precision() -> usize {
    2
}

fn default_percent_precision() -> usize {
    4
}

impl Default for YuhoConfig {
    fn default() -> Self {
        Self {
            llm: LlmConfig::default(),
            cache: CacheConfig::default(),
            http: HttpConfig::default(),
            docs: DocsConfig::default(),
            date_formats: DateFormatConfig::default(),
            precision: PrecisionConfig::default(),
        }
    }
}

impl Default for LlmConfig {
    fn default() -> Self {
        Self {
            providers: HashMap::new(),
            default_provider: default_provider(),
            fallback_providers: Vec::new(),
            token_limits: TokenLimits::default(),
            rate_limits: HashMap::new(),
        }
    }
}

impl Default for TokenLimits {
    fn default() -> Self {
        Self {
            explanation_max_tokens: default_explanation_tokens(),
            statute_parsing_max_tokens: default_statute_tokens(),
            test_generation_max_tokens: default_test_gen_tokens(),
            contract_generation_max_tokens: default_contract_tokens(),
            legal_reasoning_max_tokens: default_reasoning_tokens(),
        }
    }
}

impl Default for CacheConfig {
    fn default() -> Self {
        Self {
            max_entries: default_cache_size(),
            ttl_seconds: default_cache_ttl(),
            enable_persistence: false,
            persistence_path: None,
        }
    }
}

impl Default for HttpConfig {
    fn default() -> Self {
        Self {
            connect_timeout_seconds: default_connect_timeout(),
            request_timeout_seconds: default_request_timeout(),
            idle_timeout_seconds: default_idle_timeout(),
        }
    }
}

impl Default for DocsConfig {
    fn default() -> Self {
        let mut external_tools = HashMap::new();
        external_tools.insert("mermaid".to_string(), "https://mermaid.live".to_string());
        external_tools.insert("alloy".to_string(), "http://alloytools.org".to_string());

        Self {
            base_url: default_docs_url(),
            external_tools,
        }
    }
}

impl Default for DateFormatConfig {
    fn default() -> Self {
        Self {
            default: default_date_format(),
            allowed: default_allowed_formats(),
        }
    }
}

impl Default for PrecisionConfig {
    fn default() -> Self {
        Self {
            float_decimal_places: default_float_precision(),
            money_decimal_places: default_money_precision(),
            percent_decimal_places: default_percent_precision(),
        }
    }
}

/// Error type for configuration loading
#[derive(Debug, thiserror::Error)]
pub enum ConfigLoadError {
    #[error("Failed to load configuration: {0}")]
    LoadError(#[from] ConfigError),

    #[error("Invalid configuration: {0}")]
    InvalidConfig(String),
}

impl YuhoConfig {
    /// Load configuration from multiple sources
    ///
    /// Priority order:
    /// 1. Environment variables (YUHO_*)
    /// 2. Configuration file
    /// 3. Defaults
    pub fn load() -> Result<Self, ConfigLoadError> {
        let config_path = Self::get_config_path();

        let builder = Config::builder()
            // Start with defaults
            .add_source(config::File::from_str(
                include_str!("../default_config.toml"),
                config::FileFormat::Toml,
            ))
            // Add config file if it exists
            .add_source(
                File::with_name(config_path.to_str().unwrap_or("yuho"))
                    .required(false)
            )
            // Add environment variables with YUHO_ prefix
            .add_source(
                Environment::with_prefix("YUHO")
                    .separator("__")
                    .try_parsing(true)
            );

        let config = builder.build()?;
        let yuho_config: YuhoConfig = config.try_deserialize()?;

        Ok(yuho_config)
    }

    /// Load configuration from a specific file
    pub fn load_from_file(path: &str) -> Result<Self, ConfigLoadError> {
        let builder = Config::builder().add_source(File::with_name(path));

        let config = builder.build()?;
        let yuho_config: YuhoConfig = config.try_deserialize()?;

        Ok(yuho_config)
    }

    /// Get the default config file path
    fn get_config_path() -> PathBuf {
        if let Some(proj_dirs) = directories::ProjectDirs::from("org", "yuho", "yuho") {
            proj_dirs.config_dir().join("yuho.toml")
        } else {
            PathBuf::from("yuho.toml")
        }
    }

    /// Get provider configuration
    pub fn get_provider_config(&self, provider: &str) -> Option<&ProviderConfig> {
        self.llm.providers.get(provider)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = YuhoConfig::default();
        assert_eq!(config.cache.max_entries, 1000);
        assert_eq!(config.cache.ttl_seconds, 3600);
        assert_eq!(config.http.request_timeout_seconds, 30);
    }

    #[test]
    fn test_token_limits() {
        let limits = TokenLimits::default();
        assert_eq!(limits.explanation_max_tokens, 1000);
        assert_eq!(limits.statute_parsing_max_tokens, 2000);
    }

    #[test]
    fn test_http_config_defaults() {
        let http = HttpConfig::default();
        assert_eq!(http.connect_timeout_seconds, 10);
        assert_eq!(http.request_timeout_seconds, 30);
        assert_eq!(http.idle_timeout_seconds, 90);
    }

    #[test]
    fn test_cache_config_defaults() {
        let cache = CacheConfig::default();
        assert_eq!(cache.max_entries, 1000);
        assert_eq!(cache.ttl_seconds, 3600);
        assert!(!cache.enable_persistence);
        assert!(cache.persistence_path.is_none());
    }

    #[test]
    fn test_docs_config() {
        let docs = DocsConfig::default();
        assert!(docs.base_url.contains("github"));
        assert!(docs.external_tools.contains_key("mermaid"));
        assert!(docs.external_tools.contains_key("alloy"));
    }

    #[test]
    fn test_precision_config() {
        let precision = PrecisionConfig::default();
        assert_eq!(precision.float_decimal_places, 4);
        assert_eq!(precision.money_decimal_places, 2);
        assert_eq!(precision.percent_decimal_places, 4);
    }

    #[test]
    fn test_date_format_config() {
        let date_formats = DateFormatConfig::default();
        assert_eq!(date_formats.default, "DD-MM-YYYY");
        assert_eq!(date_formats.allowed.len(), 3);
        assert!(date_formats.allowed.contains(&"DD-MM-YYYY".to_string()));
    }

    #[test]
    fn test_rate_limit_config_defaults() {
        let rate_limit = RateLimitConfig {
            requests_per_minute: default_rpm(),
            tokens_per_minute: default_tpm(),
            burst_size: default_burst(),
        };
        assert_eq!(rate_limit.requests_per_minute, 60);
        assert_eq!(rate_limit.tokens_per_minute, 90000);
        assert_eq!(rate_limit.burst_size, 10);
    }
}
