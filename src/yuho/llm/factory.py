"""
LLM provider factory with fallback support.
"""

import logging
from typing import Optional, List

from yuho.llm.config import LLMConfig, ProviderType
from yuho.llm.providers import (
    LLMProvider,
    OllamaProvider,
    HuggingFaceProvider,
    OpenAIProvider,
    AnthropicProvider,
)

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    Factory for creating LLM providers from config.

    Supports automatic fallback to alternative providers.
    """

    _provider_classes = {
        ProviderType.OLLAMA: OllamaProvider,
        ProviderType.HUGGINGFACE: HuggingFaceProvider,
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.ANTHROPIC: AnthropicProvider,
    }

    @classmethod
    def create(cls, config: LLMConfig) -> LLMProvider:
        """
        Create a provider from config.

        Args:
            config: LLM configuration

        Returns:
            An LLMProvider instance

        Raises:
            ValueError: If provider type is unknown
        """
        provider_type = config.provider_type
        provider_class = cls._provider_classes.get(provider_type)

        if not provider_class:
            raise ValueError(f"Unknown provider type: {config.provider}")

        return provider_class(config)

    @classmethod
    def create_with_fallback(cls, config: LLMConfig) -> LLMProvider:
        """
        Create a provider with automatic fallback.

        Tries the primary provider first, then falls back to
        configured alternatives if unavailable.
        """
        # Try primary provider
        try:
            primary = cls.create(config)
            if primary.is_available():
                logger.info(f"Using {config.provider} provider")
                return primary
        except Exception as e:
            logger.warning(f"Primary provider {config.provider} failed: {e}")

        # Try fallback providers
        for fallback_name in config.fallback_providers:
            try:
                fallback_config = LLMConfig(
                    provider=fallback_name,
                    model_name=config.model_name,
                    api_key=config.api_key,
                    base_url=config.base_url,
                    ollama_host=config.ollama_host,
                    ollama_port=config.ollama_port,
                    huggingface_cache=config.huggingface_cache,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                )
                fallback = cls.create(fallback_config)
                if fallback.is_available():
                    logger.info(f"Falling back to {fallback_name} provider")
                    return fallback
            except Exception as e:
                logger.warning(f"Fallback provider {fallback_name} failed: {e}")

        # Last resort: try Ollama with default settings
        try:
            default_ollama = OllamaProvider(LLMConfig(provider="ollama", model_name="llama3"))
            if default_ollama.is_available():
                logger.info("Falling back to default Ollama")
                return default_ollama
        except Exception:
            pass

        raise RuntimeError(
            "No LLM provider available. Install and configure at least one of: "
            "Ollama, HuggingFace, OpenAI, or Anthropic"
        )


def get_provider(config: Optional[LLMConfig] = None) -> LLMProvider:
    """
    Get an LLM provider, using fallback if needed.

    Args:
        config: Optional config. Uses defaults if not provided.

    Returns:
        An LLMProvider instance
    """
    if config is None:
        config = LLMConfig()

    return LLMProviderFactory.create_with_fallback(config)
