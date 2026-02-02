"""
Configuration schema definitions.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class LLMSection:
    """[llm] configuration section."""

    provider: str = "ollama"
    model: str = "llama3"
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    huggingface_cache: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    fallback_providers: List[str] = field(default_factory=lambda: ["huggingface"])

    def to_llm_config(self):
        """Convert to LLMConfig."""
        from yuho.llm import LLMConfig
        return LLMConfig(
            provider=self.provider,
            model_name=self.model,
            ollama_host=self.ollama_host,
            ollama_port=self.ollama_port,
            huggingface_cache=self.huggingface_cache,
            api_key=self.openai_api_key or self.anthropic_api_key,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            fallback_providers=self.fallback_providers,
        )


@dataclass
class TranspileSection:
    """[transpile] configuration section."""

    default_target: str = "json"
    latex_compiler: str = "pdflatex"
    output_dir: Optional[str] = None
    include_source_locations: bool = True


@dataclass
class LSPSection:
    """[lsp] configuration section."""

    diagnostic_severity_error: bool = True
    diagnostic_severity_warning: bool = True
    diagnostic_severity_info: bool = True
    diagnostic_severity_hint: bool = True
    completion_trigger_chars: List[str] = field(default_factory=lambda: [".", ":"])


@dataclass
class MCPSection:
    """[mcp] configuration section."""

    host: str = "127.0.0.1"
    port: int = 8080
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    auth_token: Optional[str] = None


@dataclass
class LibrarySection:
    """[library] configuration section."""

    registry_url: str = "https://registry.yuho.dev"
    registry_api_version: str = "v1"
    auth_token: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True


@dataclass
class ConfigSchema:
    """Complete configuration schema."""

    llm: LLMSection = field(default_factory=LLMSection)
    transpile: TranspileSection = field(default_factory=TranspileSection)
    lsp: LSPSection = field(default_factory=LSPSection)
    mcp: MCPSection = field(default_factory=MCPSection)
    library: LibrarySection = field(default_factory=LibrarySection)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSchema":
        """Create config from dictionary."""
        llm_data = data.get("llm", {})
        transpile_data = data.get("transpile", {})
        lsp_data = data.get("lsp", {})
        mcp_data = data.get("mcp", {})
        library_data = data.get("library", {})

        return cls(
            llm=LLMSection(**{k: v for k, v in llm_data.items() if k in LLMSection.__dataclass_fields__}),
            transpile=TranspileSection(**{k: v for k, v in transpile_data.items() if k in TranspileSection.__dataclass_fields__}),
            lsp=LSPSection(**{k: v for k, v in lsp_data.items() if k in LSPSection.__dataclass_fields__}),
            mcp=MCPSection(**{k: v for k, v in mcp_data.items() if k in MCPSection.__dataclass_fields__}),
            library=LibrarySection(**{k: v for k, v in library_data.items() if k in LibrarySection.__dataclass_fields__}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "ollama_host": self.llm.ollama_host,
                "ollama_port": self.llm.ollama_port,
                "huggingface_cache": self.llm.huggingface_cache,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
                "fallback_providers": self.llm.fallback_providers,
            },
            "transpile": {
                "default_target": self.transpile.default_target,
                "latex_compiler": self.transpile.latex_compiler,
                "output_dir": self.transpile.output_dir,
                "include_source_locations": self.transpile.include_source_locations,
            },
            "lsp": {
                "diagnostic_severity_error": self.lsp.diagnostic_severity_error,
                "diagnostic_severity_warning": self.lsp.diagnostic_severity_warning,
                "diagnostic_severity_info": self.lsp.diagnostic_severity_info,
                "diagnostic_severity_hint": self.lsp.diagnostic_severity_hint,
                "completion_trigger_chars": self.lsp.completion_trigger_chars,
            },
            "mcp": {
                "host": self.mcp.host,
                "port": self.mcp.port,
                "allowed_origins": self.mcp.allowed_origins,
            },
            "library": {
                "registry_url": self.library.registry_url,
                "registry_api_version": self.library.registry_api_version,
                "timeout": self.library.timeout,
                "verify_ssl": self.library.verify_ssl,
            },
        }
