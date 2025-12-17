//! LLM integration for Yuho
//!
//! This crate provides Large Language Model integration for:
//! - Statute parsing and code generation
//! - Natural language explanations
//! - Test scenario generation
//! - Interactive Q&A

pub mod cache;
pub mod explanation;
pub mod provider;
pub mod scenario;
pub mod statute;

use thiserror::Error;

#[derive(Error, Debug)]
pub enum LLMError {
    #[error("Provider error: {0}")]
    ProviderError(String),

    #[error("API error: {0}")]
    ApiError(String),

    #[error("Rate limit exceeded")]
    RateLimitExceeded,

    #[error("Cost budget exceeded: ${0}")]
    CostBudgetExceeded(f64),

    #[error("Parsing error: {0}")]
    ParsingError(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Request error: {0}")]
    RequestError(#[from] reqwest::Error),
}

pub type LLMResult<T> = Result<T, LLMError>;
