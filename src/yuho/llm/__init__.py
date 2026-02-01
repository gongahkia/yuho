"""
Yuho LLM module - local-first LLM integration.

Supports:
- Ollama (local)
- HuggingFace Transformers (local)
- OpenAI API (cloud)
- Anthropic API (cloud)

Local providers are preferred, with cloud fallback.
"""

from yuho.llm.config import LLMConfig
from yuho.llm.providers import (
    LLMProvider,
    OllamaProvider,
    HuggingFaceProvider,
)
from yuho.llm.factory import get_provider, LLMProviderFactory
from yuho.llm.prompts import (
    STATUTE_EXPLANATION_PROMPT,
    STATUTE_TO_YUHO_PROMPT,
)

__all__ = [
    "LLMConfig",
    "LLMProvider",
    "OllamaProvider",
    "HuggingFaceProvider",
    "get_provider",
    "LLMProviderFactory",
    "STATUTE_EXPLANATION_PROMPT",
    "STATUTE_TO_YUHO_PROMPT",
]
