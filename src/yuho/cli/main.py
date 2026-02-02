"""
Main CLI entry point using Click.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

import click

from yuho import __version__


def _detect_color_support() -> bool:
    """
    Auto-detect terminal color support.
    
    Checks for:
    - TTY attached to stdout
    - NO_COLOR environment variable (force disable)
    - FORCE_COLOR environment variable (force enable)
    - TERM environment variable
    """
    # NO_COLOR spec: https://no-color.org/
    if os.environ.get("NO_COLOR"):
        return False
    
    # FORCE_COLOR always wins
    if os.environ.get("FORCE_COLOR"):
        return True
    
    # Check if stdout is a TTY
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    
    # Check TERM variable
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False
    
    return True


# Click context settings
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="yuho")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "--color/--no-color",
    "use_color",
    default=None,
    help="Force color output on/off (auto-detected by default)"
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress non-error output"
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, use_color: Optional[bool], quiet: bool) -> None:
    """
    Yuho - A domain-specific language for encoding legal statutes.

    Use 'yuho <command> --help' for command-specific help.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose and not quiet  # Quiet overrides verbose
    ctx.obj["quiet"] = quiet
    
    # Determine color setting
    if use_color is None:
        # Auto-detect
        ctx.obj["color"] = _detect_color_support()
    else:
        ctx.obj["color"] = use_color
    
    # Set global color state for error_formatter
    from yuho.cli import error_formatter
    error_formatter.COLOR_ENABLED = ctx.obj["color"]


# =============================================================================
# Check command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output errors as JSON")
@click.pass_context
def check(ctx: click.Context, file: str, json_output: bool) -> None:
    """
    Parse and validate a Yuho source file.

    Runs syntax checking and semantic analysis, reporting any errors found.
    """
    from yuho.cli.commands.check import run_check
    run_check(file, json_output=json_output, verbose=ctx.obj["verbose"])


# =============================================================================
# Transpile command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-t", "--target",
    type=click.Choice(["json", "jsonld", "english", "latex", "mermaid", "alloy"], case_sensitive=False),
    default="json",
    help="Transpilation target format"
)
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--dir", "output_dir", type=click.Path(), help="Output directory for multiple files")
@click.option("--all", "all_targets", is_flag=True, help="Generate all targets")
@click.option("--json", "json_output", is_flag=True, help="Output metadata as JSON")
@click.pass_context
def transpile(
    ctx: click.Context,
    file: str,
    target: str,
    output: Optional[str],
    output_dir: Optional[str],
    all_targets: bool,
    json_output: bool
) -> None:
    """
    Transpile a Yuho source file to another format.

    Supported targets: json, jsonld, english, latex, mermaid, alloy
    """
    from yuho.cli.commands.transpile import run_transpile
    run_transpile(
        file,
        target=target,
        output=output,
        output_dir=output_dir,
        all_targets=all_targets,
        json_output=json_output,
        verbose=ctx.obj["verbose"]
    )


# =============================================================================
# Explain command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-s", "--section", help="Explain specific section only")
@click.option("-i", "--interactive", is_flag=True, help="Interactive REPL mode")
@click.option("--provider", type=click.Choice(["ollama", "huggingface", "openai", "anthropic"]),
              help="LLM provider to use")
@click.option("--model", help="Model name to use")
@click.option("--stream/--no-stream", "stream", default=True,
              help="Enable/disable streaming output for real-time response")
@click.pass_context
def explain(
    ctx: click.Context,
    file: str,
    section: Optional[str],
    interactive: bool,
    provider: Optional[str],
    model: Optional[str],
    stream: bool,
) -> None:
    """
    Generate natural language explanation of a Yuho file.

    Uses LLM to explain statutes in plain language.
    """
    from yuho.cli.commands.explain import run_explain
    run_explain(
        file,
        section=section,
        interactive=interactive,
        provider=provider,
        model=model,
        verbose=ctx.obj["verbose"],
        stream=stream,
    )


# =============================================================================
# Serve command
# =============================================================================


@cli.command()
@click.option("-p", "--port", type=int, default=8080, help="Port to listen on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--stdio", is_flag=True, help="Use stdio transport (for editor integration)")
@click.pass_context
def serve(ctx: click.Context, port: int, host: str, stdio: bool) -> None:
    """
    Start the MCP (Model Context Protocol) server.

    Exposes Yuho functionality to AI assistants and editors.
    """
    from yuho.cli.commands.serve import run_serve
    run_serve(port=port, host=host, stdio=stdio, verbose=ctx.obj["verbose"])


# =============================================================================
# Contribute command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--package", is_flag=True, help="Create distributable .yhpkg archive")
@click.option("-o", "--output", type=click.Path(), help="Output path for package")
@click.pass_context
def contribute(ctx: click.Context, file: str, package: bool, output: Optional[str]) -> None:
    """
    Validate a statute file for contribution to the library.

    Checks that the file parses correctly and has associated tests.
    """
    from yuho.cli.commands.contribute import run_contribute
    run_contribute(file, package=package, output=output, verbose=ctx.obj["verbose"])


# =============================================================================
# Init command
# =============================================================================


@cli.command()
@click.argument("name", required=False)
@click.option("-d", "--dir", "directory", type=click.Path(), help="Directory to create project in")
@click.pass_context
def init(ctx: click.Context, name: Optional[str], directory: Optional[str]) -> None:
    """
    Initialize a new Yuho statute project.

    Creates a directory structure with template files.
    """
    from yuho.cli.commands.init import run_init
    run_init(name=name, directory=directory, verbose=ctx.obj["verbose"])


# =============================================================================
# Format command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-i", "--in-place", is_flag=True, help="Format file in place")
@click.option("--check", is_flag=True, help="Check if file is formatted (exit 1 if not)")
@click.pass_context
def fmt(ctx: click.Context, file: str, in_place: bool, check: bool) -> None:
    """
    Format a Yuho source file.

    Applies canonical formatting to the file.
    """
    from yuho.cli.commands.fmt import run_fmt
    run_fmt(file, in_place=in_place, check=check, verbose=ctx.obj["verbose"])


# =============================================================================
# Test command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option("--all", "run_all", is_flag=True, help="Run all tests in directory")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
@click.pass_context
def test(ctx: click.Context, file: Optional[str], run_all: bool, json_output: bool) -> None:
    """
    Run tests for a Yuho statute file.

    Looks for test_<filename>.yh or tests/<filename>_test.yh
    """
    from yuho.cli.commands.test import run_test
    run_test(file, run_all=run_all, json_output=json_output, verbose=ctx.obj["verbose"])


# =============================================================================
# LSP command
# =============================================================================


@cli.command()
@click.option("--tcp", type=int, help="Start LSP server on TCP port")
@click.pass_context
def lsp(ctx: click.Context, tcp: Optional[int]) -> None:
    """
    Start the Language Server Protocol server.

    For editor integration (VS Code, Neovim, etc.).
    """
    from yuho.cli.commands.lsp import run_lsp
    run_lsp(tcp=tcp, verbose=ctx.obj["verbose"])


# =============================================================================
# Completion command
# =============================================================================


@cli.command()
@click.argument(
    "shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
)
@click.option(
    "--install", "show_install",
    is_flag=True,
    help="Show installation instructions"
)
@click.pass_context
def completion(ctx: click.Context, shell: str, show_install: bool) -> None:
    """
    Generate shell completion script.

    Outputs a completion script for the specified shell that can be
    sourced or saved to the appropriate location.

    Examples:
        # Bash: Add to ~/.bashrc
        eval "$(yuho completion bash)"

        # Zsh: Add to ~/.zshrc
        eval "$(yuho completion zsh)"

        # Fish: Save to completions directory
        yuho completion fish > ~/.config/fish/completions/yuho.fish

    Use --install to see detailed installation instructions.
    """
    from yuho.cli.completions import get_completion_script, get_install_instructions

    shell_lower = shell.lower()

    if show_install:
        click.echo(get_install_instructions(shell_lower))
    else:
        click.echo(get_completion_script(shell_lower))


# =============================================================================
# Config command
# =============================================================================


@cli.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    """
    Manage Yuho configuration.

    View and modify configuration settings for all Yuho components.
    """
    pass


@config.command("show")
@click.option("-s", "--section", type=click.Choice(["llm", "transpile", "lsp", "mcp"]),
              help="Show only specific section")
@click.option("-f", "--format", "fmt", type=click.Choice(["toml", "json"]),
              default="toml", help="Output format")
@click.pass_context
def config_show(ctx: click.Context, section: Optional[str], fmt: str) -> None:
    """
    Display current configuration.

    Shows all configuration values from file and environment.

    Examples:
        yuho config show
        yuho config show -s llm
        yuho config show -f json
    """
    from yuho.cli.commands.config import run_config_show
    run_config_show(section=section, format=fmt, verbose=ctx.obj["verbose"])


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """
    Set a configuration value.

    KEY must be in format 'section.key' (e.g., 'llm.provider').

    Examples:
        yuho config set llm.provider ollama
        yuho config set llm.model llama3
        yuho config set mcp.port 9000
    """
    from yuho.cli.commands.config import run_config_set
    run_config_set(key, value, verbose=ctx.obj["verbose"])


@config.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing config file")
@click.pass_context
def config_init(ctx: click.Context, force: bool) -> None:
    """
    Create a default configuration file.

    Creates ~/.config/yuho/config.toml with sensible defaults.
    """
    from yuho.cli.commands.config import run_config_init
    run_config_init(force=force, verbose=ctx.obj["verbose"])


# =============================================================================
# Library command
# =============================================================================


@cli.group()
@click.pass_context
def library(ctx: click.Context) -> None:
    """
    Manage Yuho statute packages.

    Search, install, update, and manage statute packages from the library.
    """
    pass


@library.command("search")
@click.argument("query")
@click.option("-j", "--jurisdiction", help="Filter by jurisdiction")
@click.option("-t", "--tag", "tags", multiple=True, help="Filter by tag")
@click.option("-n", "--limit", type=int, default=20, help="Max results")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def library_search(
    ctx: click.Context,
    query: str,
    jurisdiction: Optional[str],
    tags: tuple,
    limit: int,
    json_output: bool,
) -> None:
    """
    Search for packages in the library.

    Examples:
        yuho library search theft
        yuho library search S403 --jurisdiction singapore
    """
    from yuho.cli.commands.library import run_library_search
    run_library_search(
        query,
        jurisdiction=jurisdiction,
        tags=list(tags) if tags else None,
        limit=limit,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@library.command("install")
@click.argument("package")
@click.option("-f", "--force", is_flag=True, help="Overwrite existing")
@click.option("--no-deps", is_flag=True, help="Skip dependencies")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def library_install(
    ctx: click.Context,
    package: str,
    force: bool,
    no_deps: bool,
    json_output: bool,
) -> None:
    """
    Install a package from registry or local path.

    Examples:
        yuho library install S403
        yuho library install ./my-statute.yhpkg
    """
    from yuho.cli.commands.library import run_library_install
    run_library_install(
        package,
        force=force,
        no_deps=no_deps,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@library.command("uninstall")
@click.argument("package")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def library_uninstall(
    ctx: click.Context,
    package: str,
    json_output: bool,
) -> None:
    """
    Uninstall an installed package.

    Examples:
        yuho library uninstall S403
    """
    from yuho.cli.commands.library import run_library_uninstall
    run_library_uninstall(
        package,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@library.command("list")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def library_list(ctx: click.Context, json_output: bool) -> None:
    """
    List all installed packages.
    """
    from yuho.cli.commands.library import run_library_list
    run_library_list(json_output=json_output, verbose=ctx.obj["verbose"])


@library.command("update")
@click.argument("package", required=False)
@click.option("--all", "all_packages", is_flag=True, help="Update all packages")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def library_update(
    ctx: click.Context,
    package: Optional[str],
    all_packages: bool,
    json_output: bool,
) -> None:
    """
    Update one or all packages.

    Without arguments, shows available updates.
    Use --all to apply all updates.

    Examples:
        yuho library update           # Show updates
        yuho library update --all     # Apply all updates
        yuho library update S403      # Update specific package
    """
    from yuho.cli.commands.library import run_library_update
    run_library_update(
        package,
        all_packages=all_packages,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@library.command("publish")
@click.argument("path", type=click.Path(exists=True))
@click.option("--registry", help="Registry URL")
@click.option("--token", help="Auth token")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def library_publish(
    ctx: click.Context,
    path: str,
    registry: Optional[str],
    token: Optional[str],
    json_output: bool,
) -> None:
    """
    Publish a package to the registry.

    Examples:
        yuho library publish ./my-statute --token $YUHO_TOKEN
    """
    from yuho.cli.commands.library import run_library_publish
    run_library_publish(
        path,
        registry=registry,
        token=token,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@library.command("info")
@click.argument("package")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def library_info(
    ctx: click.Context,
    package: str,
    json_output: bool,
) -> None:
    """
    Show detailed package information.

    Examples:
        yuho library info S403
    """
    from yuho.cli.commands.library import run_library_info
    run_library_info(
        package,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@library.command("outdated")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def library_outdated(
    ctx: click.Context,
    json_output: bool,
) -> None:
    """
    Show packages with updates available.

    Displays installed packages that have newer versions in the registry,
    along with the type of update (major, minor, patch) and deprecation warnings.

    Examples:
        yuho library outdated
        yuho library outdated --json
    """
    from yuho.cli.commands.library import run_library_outdated
    run_library_outdated(
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
