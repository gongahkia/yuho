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

__all__ = [
    "Config",
    "load_config",
    "get_config",
    "LLMSection",
    "TranspileSection",
    "LSPSection",
    "MCPSection",
]
