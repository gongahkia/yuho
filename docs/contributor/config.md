# Yuho Configuration Guide

Yuho uses a layered configuration system with the following precedence (later overrides earlier):

1. Default values
2. Config file (`~/.config/yuho/config.toml`)
3. Environment variables (`YUHO_*`)
4. CLI flags

## Quick Start

Create a config file:

```bash
yuho config init
```

View current configuration:

```bash
yuho config show
yuho config show --format json
```

Set a value:

```bash
yuho config set llm.provider ollama
yuho config set llm.max_tokens 4096
```

## Config File Location

- **Linux/macOS**: `~/.config/yuho/config.toml`
- **Windows**: `%APPDATA%\yuho\config.toml`

## Complete Config File Example

```toml
# ~/.config/yuho/config.toml

[llm]
# LLM provider: "ollama", "huggingface", "openai", "anthropic"
provider = "ollama"

# Model name (depends on provider)
model = "llama3"

# Ollama server settings
ollama_host = "localhost"
ollama_port = 11434

# HuggingFace cache directory (optional)
# huggingface_cache = "~/.cache/huggingface"

# API keys for cloud providers (keep these secret!)
# openai_api_key = "sk-..."
# anthropic_api_key = "sk-ant-..."

# Generation settings
max_tokens = 2048
temperature = 0.7

# Fallback providers if primary fails
fallback_providers = ["huggingface"]

[transpile]
# Default transpilation target: "json", "jsonld", "english", "mermaid", "alloy", "latex", "graphql", "blocks"
default_target = "json"

# LaTeX compiler for PDF generation
latex_compiler = "pdflatex"

# Output directory for transpiled files (optional)
# output_dir = "./output"

# Include source locations in transpiled output
include_source_locations = true

[lsp]
# Diagnostic severity levels to report
diagnostic_severity_error = true
diagnostic_severity_warning = true
diagnostic_severity_info = true
diagnostic_severity_hint = true

# Characters that trigger completions
completion_trigger_chars = [".", ":"]

[mcp]
# MCP server bind address
host = "127.0.0.1"
port = 8080

# Allowed CORS origins
allowed_origins = ["*"]

# Authentication token (optional, for secure deployments)
# auth_token = "your-secret-token"

[library]
# Package registry URL
registry_url = "https://registry.yuho.dev"
registry_api_version = "v1"

# Registry authentication (for publishing)
# auth_token = "your-publish-token"

# HTTP timeout in seconds
timeout = 30

# SSL verification
verify_ssl = true
```

## Configuration Sections

### [llm] - Language Model Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `provider` | string | `"ollama"` | LLM provider to use |
| `model` | string | `"llama3"` | Model name |
| `ollama_host` | string | `"localhost"` | Ollama server hostname |
| `ollama_port` | int | `11434` | Ollama server port |
| `huggingface_cache` | string | `null` | HuggingFace cache directory |
| `openai_api_key` | string | `null` | OpenAI API key |
| `anthropic_api_key` | string | `null` | Anthropic API key |
| `max_tokens` | int | `2048` | Max tokens for generation |
| `temperature` | float | `0.7` | Generation temperature |
| `fallback_providers` | list | `["huggingface"]` | Fallback providers |

### [transpile] - Transpilation Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default_target` | string | `"json"` | Default output format (json, jsonld, english, mermaid, alloy, latex, graphql, blocks) |
| `latex_compiler` | string | `"pdflatex"` | LaTeX compiler command |
| `output_dir` | string | `null` | Output directory |
| `include_source_locations` | bool | `true` | Include source locations |

### [lsp] - Language Server Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `diagnostic_severity_error` | bool | `true` | Report errors |
| `diagnostic_severity_warning` | bool | `true` | Report warnings |
| `diagnostic_severity_info` | bool | `true` | Report info |
| `diagnostic_severity_hint` | bool | `true` | Report hints |
| `completion_trigger_chars` | list | `[".", ":"]` | Completion triggers |

### [mcp] - MCP Server Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `host` | string | `"127.0.0.1"` | Server bind address |
| `port` | int | `8080` | Server port |
| `allowed_origins` | list | `["*"]` | CORS allowed origins |
| `auth_token` | string | `null` | Authentication token |

### [library] - Package Library Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `registry_url` | string | `"https://registry.yuho.dev"` | Registry URL |
| `registry_api_version` | string | `"v1"` | API version |
| `auth_token` | string | `null` | Publishing auth token |
| `timeout` | int | `30` | HTTP timeout (seconds) |
| `verify_ssl` | bool | `true` | Verify SSL certificates |

## Environment Variables

All config values can be set via environment variables with the `YUHO_` prefix:

```bash
# Format: YUHO_{SECTION}_{KEY}
export YUHO_LLM_PROVIDER=openai
export YUHO_LLM_OPENAI_API_KEY=sk-...
export YUHO_LLM_MAX_TOKENS=4096
export YUHO_TRANSPILE_DEFAULT_TARGET=mermaid
export YUHO_MCP_PORT=9000
export YUHO_LIBRARY_AUTH_TOKEN=your-token
```

## Provider-Specific Examples

### Ollama (Local, Default)

```toml
[llm]
provider = "ollama"
model = "llama3"
ollama_host = "localhost"
ollama_port = 11434
```

### OpenAI

```toml
[llm]
provider = "openai"
model = "gpt-4"
openai_api_key = "sk-..."
max_tokens = 4096
```

### Anthropic

```toml
[llm]
provider = "anthropic"
model = "claude-3-opus-20240229"
anthropic_api_key = "sk-ant-..."
max_tokens = 4096
```

### HuggingFace (Local)

```toml
[llm]
provider = "huggingface"
model = "mistralai/Mistral-7B-Instruct-v0.2"
huggingface_cache = "~/.cache/huggingface"
```

## Security Notes

- **Never commit API keys** to version control
- Use environment variables for sensitive values in CI/CD
- The config file should have restricted permissions (600)
- Use `yuho config show` to verify keys are not exposed (they are redacted)
