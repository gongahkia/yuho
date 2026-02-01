"""
Configuration loader with multi-source override support.

Load order (later overrides earlier):
1. Built-in defaults
2. Config file (~/.config/yuho/config.toml)
3. Environment variables (YUHO_*)
4. CLI flags
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from yuho.config.schema import ConfigSchema

logger = logging.getLogger(__name__)

# Default config file location
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "yuho" / "config.toml"

# Singleton config instance
_config: Optional["Config"] = None


class Config:
    """
    Yuho configuration manager.

    Handles loading and accessing configuration from multiple sources.
    """

    def __init__(self, schema: ConfigSchema):
        self._schema = schema

    @property
    def llm(self):
        """Get LLM configuration section."""
        return self._schema.llm

    @property
    def transpile(self):
        """Get transpile configuration section."""
        return self._schema.transpile

    @property
    def lsp(self):
        """Get LSP configuration section."""
        return self._schema.lsp

    @property
    def mcp(self):
        """Get MCP configuration section."""
        return self._schema.mcp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._schema.to_dict()


def load_config(
    config_path: Optional[Path] = None,
    env_prefix: str = "YUHO_",
    cli_overrides: Optional[Dict[str, Any]] = None,
) -> Config:
    """
    Load configuration from all sources.

    Args:
        config_path: Path to config file (default: ~/.config/yuho/config.toml)
        env_prefix: Prefix for environment variables
        cli_overrides: Dictionary of CLI flag overrides

    Returns:
        Loaded Config instance
    """
    # Start with defaults
    config_data: Dict[str, Any] = {}

    # Load from file
    file_path = config_path or DEFAULT_CONFIG_PATH
    if file_path.exists():
        config_data = _load_from_file(file_path)
        logger.debug(f"Loaded config from {file_path}")

    # Override from environment
    env_data = _load_from_env(env_prefix)
    config_data = _merge_dicts(config_data, env_data)

    # Override from CLI
    if cli_overrides:
        config_data = _merge_dicts(config_data, cli_overrides)

    # Create schema
    schema = ConfigSchema.from_dict(config_data)

    return Config(schema)


def get_config() -> Config:
    """
    Get the global config instance.

    Loads config on first call, then returns cached instance.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def _load_from_file(path: Path) -> Dict[str, Any]:
    """Load config from TOML file."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            logger.warning("tomllib/tomli not available, skipping config file")
            return {}

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.warning(f"Failed to load config file: {e}")
        return {}


def _load_from_env(prefix: str) -> Dict[str, Any]:
    """Load config from environment variables."""
    config: Dict[str, Any] = {}

    # Map environment variables to config paths
    env_mapping = {
        f"{prefix}LLM_PROVIDER": ("llm", "provider"),
        f"{prefix}LLM_MODEL": ("llm", "model"),
        f"{prefix}LLM_OLLAMA_HOST": ("llm", "ollama_host"),
        f"{prefix}LLM_OLLAMA_PORT": ("llm", "ollama_port"),
        f"{prefix}LLM_HUGGINGFACE_CACHE": ("llm", "huggingface_cache"),
        f"{prefix}LLM_OPENAI_API_KEY": ("llm", "openai_api_key"),
        f"{prefix}LLM_ANTHROPIC_API_KEY": ("llm", "anthropic_api_key"),
        f"{prefix}LLM_MAX_TOKENS": ("llm", "max_tokens"),
        f"{prefix}LLM_TEMPERATURE": ("llm", "temperature"),
        f"{prefix}TRANSPILE_DEFAULT_TARGET": ("transpile", "default_target"),
        f"{prefix}TRANSPILE_LATEX_COMPILER": ("transpile", "latex_compiler"),
        f"{prefix}TRANSPILE_OUTPUT_DIR": ("transpile", "output_dir"),
        f"{prefix}MCP_HOST": ("mcp", "host"),
        f"{prefix}MCP_PORT": ("mcp", "port"),
        f"{prefix}MCP_AUTH_TOKEN": ("mcp", "auth_token"),
    }

    for env_var, (section, key) in env_mapping.items():
        value = os.environ.get(env_var)
        if value is not None:
            if section not in config:
                config[section] = {}

            # Type conversion
            if key in ("ollama_port", "max_tokens", "port"):
                value = int(value)
            elif key == "temperature":
                value = float(value)

            config[section][key] = value

    return config


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def create_default_config(path: Optional[Path] = None) -> Path:
    """
    Create a default config file.

    Args:
        path: Path to create file at (default: ~/.config/yuho/config.toml)

    Returns:
        Path to created file
    """
    file_path = path or DEFAULT_CONFIG_PATH
    file_path.parent.mkdir(parents=True, exist_ok=True)

    default_config = """# Yuho Configuration
# https://yuho.dev/docs/configuration

[llm]
# LLM provider: ollama, huggingface, openai, anthropic
provider = "ollama"
model = "llama3"
ollama_host = "localhost"
ollama_port = 11434
# huggingface_cache = "~/.cache/huggingface"
# openai_api_key = ""
# anthropic_api_key = ""
max_tokens = 2048
temperature = 0.7
fallback_providers = ["huggingface"]

[transpile]
default_target = "json"
latex_compiler = "pdflatex"
# output_dir = "./output"
include_source_locations = true

[lsp]
diagnostic_severity_error = true
diagnostic_severity_warning = true
diagnostic_severity_info = true
diagnostic_severity_hint = true
completion_trigger_chars = [".", ":"]

[mcp]
host = "127.0.0.1"
port = 8080
allowed_origins = ["*"]
# auth_token = ""
"""

    file_path.write_text(default_config)
    return file_path
