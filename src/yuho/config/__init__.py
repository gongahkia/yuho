"""
Yuho configuration module.

Handles configuration loading from:
1. Default values
2. Config file (~/.config/yuho/config.toml)
3. Environment variables (YUHO_*)
4. CLI flags

Later sources override earlier ones.
"""

from yuho.config.loader import Config, load_config, get_config
from yuho.config.schema import (
    LLMSection,
    TranspileSection,
    LSPSection,
    MCPSection,
)
from yuho.config.mask import (
    mask_value,
    mask_dict,
    mask_string,
    mask_error,
    mask_url,
    safe_repr,
    is_sensitive_key,
)

__all__ = [
    "Config",
    "load_config",
    "get_config",
    "LLMSection",
    "TranspileSection",
    "LSPSection",
    "MCPSection",
    # Masking utilities
    "mask_value",
    "mask_dict",
    "mask_string",
    "mask_error",
    "mask_url",
    "safe_repr",
    "is_sensitive_key",
]
