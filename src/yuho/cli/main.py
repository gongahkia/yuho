"""
Main CLI entry point using Click.
"""

import sys
from pathlib import Path
from typing import Optional, List

import click

from yuho import __version__


# Click context settings
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="yuho")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """
    Yuho - A domain-specific language for encoding legal statutes.

    Use 'yuho <command> --help' for command-specific help.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


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
@click.pass_context
def explain(
    ctx: click.Context,
    file: str,
    section: Optional[str],
    interactive: bool,
    provider: Optional[str],
    model: Optional[str]
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
        verbose=ctx.obj["verbose"]
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


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
