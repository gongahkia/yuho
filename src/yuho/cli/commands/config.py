"""
Config command - Display and modify Yuho configuration.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import click

from yuho.config.loader import get_config, load_config, DEFAULT_CONFIG_PATH, create_default_config
from yuho.cli.error_formatter import Colors, colorize


class ConfigValidationError(Exception):
    """Raised when configuration values are invalid."""
    pass


def validate_config_value(section: str, key: str, value: str) -> Any:
    """
    Validate and convert a configuration value.
    
    Args:
        section: Config section (llm, transpile, lsp, mcp)
        key: Configuration key
        value: String value to validate
        
    Returns:
        Converted and validated value
        
    Raises:
        ConfigValidationError: If value is invalid
    """
    # Type mappings for validation
    int_fields = {
        "llm": ["ollama_port", "max_tokens"],
        "transpile": [],
        "lsp": [],
        "mcp": ["port"],
    }
    
    float_fields = {
        "llm": ["temperature"],
        "transpile": [],
        "lsp": [],
        "mcp": [],
    }
    
    bool_fields = {
        "llm": [],
        "transpile": ["include_source_locations"],
        "lsp": ["diagnostic_severity_error", "diagnostic_severity_warning",
                "diagnostic_severity_info", "diagnostic_severity_hint"],
        "mcp": [],
    }
    
    list_fields = {
        "llm": ["fallback_providers"],
        "transpile": [],
        "lsp": ["completion_trigger_chars"],
        "mcp": ["allowed_origins"],
    }
    
    # Enum validations
    enum_fields = {
        ("llm", "provider"): ["ollama", "huggingface", "openai", "anthropic"],
        ("transpile", "default_target"): ["json", "jsonld", "english", "mermaid", "alloy", "latex"],
        ("transpile", "latex_compiler"): ["pdflatex", "xelatex", "lualatex"],
    }
    
    # Range validations
    range_fields = {
        ("llm", "ollama_port"): (1, 65535),
        ("llm", "max_tokens"): (1, 100000),
        ("llm", "temperature"): (0.0, 2.0),
        ("mcp", "port"): (1, 65535),
    }
    
    if section not in ["llm", "transpile", "lsp", "mcp"]:
        raise ConfigValidationError(f"Unknown configuration section: '{section}'. Valid sections: llm, transpile, lsp, mcp")
    
    # Check if key exists in section
    valid_keys = {
        "llm": ["provider", "model", "ollama_host", "ollama_port", "huggingface_cache",
                "openai_api_key", "anthropic_api_key", "max_tokens", "temperature", "fallback_providers"],
        "transpile": ["default_target", "latex_compiler", "output_dir", "include_source_locations"],
        "lsp": ["diagnostic_severity_error", "diagnostic_severity_warning",
                "diagnostic_severity_info", "diagnostic_severity_hint", "completion_trigger_chars"],
        "mcp": ["host", "port", "allowed_origins", "auth_token"],
    }
    
    if key not in valid_keys.get(section, []):
        raise ConfigValidationError(
            f"Unknown key '{key}' in section [{section}]. Valid keys: {', '.join(valid_keys[section])}"
        )
    
    # Type conversion and validation
    if key in int_fields.get(section, []):
        try:
            converted = int(value)
        except ValueError:
            raise ConfigValidationError(f"'{key}' must be an integer, got: '{value}'")
        
        # Range check
        if (section, key) in range_fields:
            min_val, max_val = range_fields[(section, key)]
            if not (min_val <= converted <= max_val):
                raise ConfigValidationError(f"'{key}' must be between {min_val} and {max_val}, got: {converted}")
        
        return converted
    
    elif key in float_fields.get(section, []):
        try:
            converted = float(value)
        except ValueError:
            raise ConfigValidationError(f"'{key}' must be a number, got: '{value}'")
        
        # Range check
        if (section, key) in range_fields:
            min_val, max_val = range_fields[(section, key)]
            if not (min_val <= converted <= max_val):
                raise ConfigValidationError(f"'{key}' must be between {min_val} and {max_val}, got: {converted}")
        
        return converted
    
    elif key in bool_fields.get(section, []):
        lower = value.lower()
        if lower in ("true", "1", "yes", "on"):
            return True
        elif lower in ("false", "0", "no", "off"):
            return False
        else:
            raise ConfigValidationError(f"'{key}' must be a boolean (true/false), got: '{value}'")
    
    elif key in list_fields.get(section, []):
        # Parse comma-separated list
        items = [item.strip() for item in value.split(",") if item.strip()]
        if not items:
            raise ConfigValidationError(f"'{key}' must be a non-empty list")
        return items
    
    else:
        # String field - check enum if applicable
        if (section, key) in enum_fields:
            valid_values = enum_fields[(section, key)]
            if value not in valid_values:
                raise ConfigValidationError(
                    f"'{key}' must be one of: {', '.join(valid_values)}. Got: '{value}'"
                )
        
        return value


def run_config_show(section: Optional[str] = None, format: str = "toml", verbose: bool = False) -> None:
    """
    Display current configuration.
    
    Args:
        section: Optional section to show (llm, transpile, lsp, mcp)
        format: Output format (toml, json)
        verbose: Show additional info
    """
    config = get_config()
    config_dict = config.to_dict()
    
    # Filter to specific section if requested
    if section:
        if section not in config_dict:
            click.echo(colorize(f"error: Unknown section '{section}'", Colors.RED), err=True)
            click.echo(f"Valid sections: {', '.join(config_dict.keys())}", err=True)
            sys.exit(1)
        config_dict = {section: config_dict[section]}
    
    if verbose:
        click.echo(colorize(f"# Config loaded from: {DEFAULT_CONFIG_PATH}", Colors.DIM))
        click.echo()
    
    if format == "json":
        import json
        click.echo(json.dumps(config_dict, indent=2))
    else:
        # TOML format
        for sect_name, sect_values in config_dict.items():
            click.echo(colorize(f"[{sect_name}]", Colors.CYAN + Colors.BOLD))
            for key, value in sect_values.items():
                if isinstance(value, list):
                    value_str = f"[{', '.join(repr(v) for v in value)}]"
                elif isinstance(value, str):
                    value_str = f'"{value}"'
                elif isinstance(value, bool):
                    value_str = "true" if value else "false"
                elif value is None:
                    value_str = colorize("# not set", Colors.DIM)
                else:
                    value_str = str(value)
                click.echo(f"{key} = {value_str}")
            click.echo()


def run_config_set(key_path: str, value: str, verbose: bool = False) -> None:
    """
    Set a configuration value.
    
    Args:
        key_path: Key path like "llm.provider" or "mcp.port"
        value: Value to set
        verbose: Enable verbose output
    """
    # Parse key path
    parts = key_path.split(".")
    if len(parts) != 2:
        click.echo(colorize(
            f"error: Key must be in format 'section.key' (e.g., 'llm.provider')",
            Colors.RED
        ), err=True)
        sys.exit(1)
    
    section, key = parts
    
    # Validate the value
    try:
        validated_value = validate_config_value(section, key, value)
    except ConfigValidationError as e:
        click.echo(colorize(f"error: {e}", Colors.RED), err=True)
        sys.exit(1)
    
    # Load or create config file
    if not DEFAULT_CONFIG_PATH.exists():
        if verbose:
            click.echo(colorize(f"Creating config file: {DEFAULT_CONFIG_PATH}", Colors.YELLOW))
        create_default_config()
    
    # Read current config
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            click.echo(colorize("error: tomllib/tomli not available", Colors.RED), err=True)
            sys.exit(1)
    
    with open(DEFAULT_CONFIG_PATH, "rb") as f:
        config_data = tomllib.load(f)
    
    # Update value
    if section not in config_data:
        config_data[section] = {}
    config_data[section][key] = validated_value
    
    # Write back using tomlkit for formatting preservation
    try:
        import tomlkit
        with open(DEFAULT_CONFIG_PATH, "r") as f:
            doc = tomlkit.parse(f.read())
        
        if section not in doc:
            doc[section] = tomlkit.table()
        doc[section][key] = validated_value
        
        with open(DEFAULT_CONFIG_PATH, "w") as f:
            f.write(tomlkit.dumps(doc))
    except ImportError:
        # Fall back to basic TOML writing
        _write_config_basic(config_data)
    
    if verbose:
        click.echo(colorize(f"Updated {key_path} = {validated_value}", Colors.GREEN))
    else:
        click.echo(f"Set {key_path} = {validated_value}")


def run_config_init(force: bool = False, verbose: bool = False) -> None:
    """
    Create a default configuration file.
    
    Args:
        force: Overwrite existing file
        verbose: Enable verbose output
    """
    if DEFAULT_CONFIG_PATH.exists() and not force:
        click.echo(colorize(f"Config file already exists: {DEFAULT_CONFIG_PATH}", Colors.YELLOW))
        click.echo("Use --force to overwrite.")
        sys.exit(1)
    
    path = create_default_config()
    click.echo(colorize(f"Created config file: {path}", Colors.GREEN))


def _write_config_basic(config_data: Dict[str, Any]) -> None:
    """Write config using basic TOML formatting."""
    lines = []
    
    for section, values in config_data.items():
        lines.append(f"[{section}]")
        for key, value in values.items():
            if isinstance(value, list):
                value_str = f"[{', '.join(repr(v) for v in value)}]"
            elif isinstance(value, str):
                value_str = f'"{value}"'
            elif isinstance(value, bool):
                value_str = "true" if value else "false"
            elif value is None:
                continue  # Skip None values
            else:
                value_str = str(value)
            lines.append(f"{key} = {value_str}")
        lines.append("")
    
    DEFAULT_CONFIG_PATH.write_text("\n".join(lines))
