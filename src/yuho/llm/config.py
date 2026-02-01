"""
LLM configuration dataclass.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class ProviderType(Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """
    Configuration for LLM provider.

    Attributes:
        provider: The provider type (ollama, huggingface, openai, anthropic)
        model_name: Model identifier (e.g., "llama3", "gpt-4", "claude-3-opus")
        api_key: API key for cloud providers
        base_url: Base URL for API (useful for custom endpoints)
        ollama_host: Ollama server host (default: localhost)
        ollama_port: Ollama server port (default: 11434)
        huggingface_cache: Cache directory for HuggingFace models
        max_tokens: Default max tokens for generation
        temperature: Generation temperature
        fallback_providers: List of fallback providers to try
    """

    provider: str = "ollama"
    model_name: str = "llama3"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    huggingface_cache: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    fallback_providers: List[str] = field(default_factory=list)

    @property
    def provider_type(self) -> ProviderType:
        """Get provider type enum."""
        return ProviderType(self.provider.lower())

    @property
    def ollama_url(self) -> str:
        """Get full Ollama API URL."""
        return f"http://{self.ollama_host}:{self.ollama_port}"

    @classmethod
    def from_dict(cls, data: dict) -> "LLMConfig":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "api_key": "***" if self.api_key else None,  # Redact API key
            "base_url": self.base_url,
            "ollama_host": self.ollama_host,
            "ollama_port": self.ollama_port,
            "huggingface_cache": self.huggingface_cache,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "fallback_providers": self.fallback_providers,
        }
