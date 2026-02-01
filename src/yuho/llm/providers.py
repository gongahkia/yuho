"""
LLM provider implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Iterator
import logging

from yuho.llm.config import LLMConfig

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement the generate() method.
    """

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate (uses config default if None)

        Returns:
            Generated text
        """
        pass

    def stream(self, prompt: str, max_tokens: Optional[int] = None) -> Iterator[str]:
        """
        Stream generated text token by token.

        Default implementation just yields the full response.
        Override for true streaming support.
        """
        yield self.generate(prompt, max_tokens)

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass


class OllamaProvider(LLMProvider):
    """
    Ollama provider for local LLM inference.

    Uses the Ollama HTTP API at configurable host:port.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        """Lazy-initialize HTTP client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(
                    base_url=self.config.ollama_url,
                    timeout=120.0,
                )
            except ImportError:
                raise ImportError("httpx required for Ollama. Install with: pip install httpx")
        return self._client

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using Ollama API."""
        client = self._get_client()

        max_tokens = max_tokens or self.config.max_tokens

        try:
            response = client.post(
                "/api/generate",
                json={
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": self.config.temperature,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise RuntimeError(f"Ollama error: {e}") from e

    def stream(self, prompt: str, max_tokens: Optional[int] = None) -> Iterator[str]:
        """Stream generated text from Ollama."""
        client = self._get_client()

        max_tokens = max_tokens or self.config.max_tokens

        try:
            with client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": self.config.temperature,
                    },
                },
            ) as response:
                response.raise_for_status()
                import json as json_module
                for line in response.iter_lines():
                    if line:
                        data = json_module.loads(line)
                        if "response" in data:
                            yield data["response"]

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise RuntimeError(f"Ollama error: {e}") from e

    def is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            client = self._get_client()
            response = client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    def check_model(self) -> bool:
        """Check if the configured model is available."""
        try:
            client = self._get_client()
            response = client.get("/api/tags")
            if response.status_code != 200:
                return False

            data = response.json()
            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            return self.config.model_name.split(":")[0] in models

        except Exception:
            return False

    def pull_model(self) -> bool:
        """Pull the configured model if missing."""
        try:
            client = self._get_client()
            logger.info(f"Pulling Ollama model: {self.config.model_name}")

            response = client.post(
                "/api/pull",
                json={"name": self.config.model_name},
                timeout=600.0,  # 10 minute timeout for model download
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False


class HuggingFaceProvider(LLMProvider):
    """
    HuggingFace Transformers provider for local inference.

    Supports automatic model download and device selection.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._model = None
        self._tokenizer = None
        self._device = None

    def _load_model(self):
        """Lazy-load the model and tokenizer."""
        if self._model is not None:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Device selection
            if torch.cuda.is_available():
                self._device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self._device = "mps"
            else:
                self._device = "cpu"

            logger.info(f"Loading HuggingFace model {self.config.model_name} on {self._device}")

            # Set cache directory if configured
            cache_dir = self.config.huggingface_cache

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                cache_dir=cache_dir,
            )

            self._model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                cache_dir=cache_dir,
                torch_dtype=torch.float16 if self._device != "cpu" else torch.float32,
                device_map="auto" if self._device == "cuda" else None,
            )

            if self._device != "cuda":
                self._model = self._model.to(self._device)

        except ImportError:
            raise ImportError(
                "transformers and torch required for HuggingFace. "
                "Install with: pip install transformers torch"
            )

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using HuggingFace Transformers."""
        self._load_model()

        max_tokens = max_tokens or self.config.max_tokens

        try:
            import torch

            inputs = self._tokenizer(prompt, return_tensors="pt").to(self._device)

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=self.config.temperature,
                    do_sample=self.config.temperature > 0,
                    pad_token_id=self._tokenizer.eos_token_id,
                )

            # Decode only the new tokens
            generated = self._tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            )

            return generated

        except Exception as e:
            logger.error(f"HuggingFace generation error: {e}")
            raise RuntimeError(f"HuggingFace error: {e}") from e

    def is_available(self) -> bool:
        """Check if transformers and torch are available."""
        try:
            import torch
            from transformers import AutoModelForCausalLM
            return True
        except ImportError:
            return False

    def download_model(self) -> bool:
        """Download and cache the model."""
        try:
            from huggingface_hub import snapshot_download

            cache_dir = self.config.huggingface_cache
            logger.info(f"Downloading HuggingFace model: {self.config.model_name}")

            snapshot_download(
                self.config.model_name,
                cache_dir=cache_dir,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            return False


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider.

    Also works with OpenAI-compatible APIs via base_url.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        """Lazy-initialize OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
            except ImportError:
                raise ImportError("openai required. Install with: pip install openai")
        return self._client

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using OpenAI API."""
        client = self._get_client()

        max_tokens = max_tokens or self.config.max_tokens

        try:
            response = client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=self.config.temperature,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise RuntimeError(f"OpenAI error: {e}") from e

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.config.api_key)


class AnthropicProvider(LLMProvider):
    """
    Anthropic API provider.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        """Lazy-initialize Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic

                self._client = Anthropic(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("anthropic required. Install with: pip install anthropic")
        return self._client

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using Anthropic API."""
        client = self._get_client()

        max_tokens = max_tokens or self.config.max_tokens

        try:
            response = client.messages.create(
                model=self.config.model_name,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise RuntimeError(f"Anthropic error: {e}") from e

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.config.api_key)
