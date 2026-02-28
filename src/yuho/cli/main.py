"""
Main CLI entry point using Click.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

import click

from yuho import __version__
from yuho.cli.commands_registry import register_group_commands


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
@click.option(
    "--offline",
    is_flag=True,
    help="Disable network operations and use local-only data paths where supported",
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: bool,
    use_color: Optional[bool],
    quiet: bool,
    offline: bool,
) -> None:
    """
    Yuho - A domain-specific language for encoding legal statutes.

    Use 'yuho <command> --help' for command-specific help.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose and not quiet  # Quiet overrides verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["offline"] = offline
    
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
# Verify command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option(
    "--engine",
    type=click.Choice(["combined", "alloy", "z3"], case_sensitive=False),
    default="combined",
    show_default=True,
    help="Verification backend",
)
@click.option("--alloy-jar", type=click.Path(exists=True), help="Path to Alloy analyzer JAR")
@click.option(
    "--alloy-timeout",
    type=int,
    default=30,
    show_default=True,
    help="Alloy timeout in seconds",
)
@click.option(
    "--z3-timeout-ms",
    type=int,
    default=5000,
    show_default=True,
    help="Z3 timeout in milliseconds",
)
@click.option(
    "--capabilities",
    "capabilities_only",
    is_flag=True,
    help="Show verification backend availability and exit",
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def verify(
    ctx: click.Context,
    file: Optional[str],
    engine: str,
    alloy_jar: Optional[str],
    alloy_timeout: int,
    z3_timeout_ms: int,
    capabilities_only: bool,
    json_output: bool,
) -> None:
    """
    Run formal verification checks (Alloy, Z3, or combined).

    Use --capabilities to inspect available verifier backends and
    explicit unavailability reasons in your current environment.
    """
    from yuho.cli.commands.verify import run_verify

    run_verify(
        file,
        engine=engine,
        alloy_jar=alloy_jar,
        alloy_timeout=alloy_timeout,
        z3_timeout_ms=z3_timeout_ms,
        capabilities_only=capabilities_only,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


# =============================================================================
# Check command
# =============================================================================


@cli.command()
@click.argument("file", type=str)
@click.option("--json", "json_output", is_flag=True, help="Output errors as JSON")
@click.option("--explain-error", "explain_errors", is_flag=True,
              help="Show detailed explanations for errors with common causes and fixes")
@click.option("--metrics", is_flag=True, help="Include code_scale and clock_load_scale metrics")
@click.pass_context
def check(
    ctx: click.Context,
    file: str,
    json_output: bool,
    explain_errors: bool,
    metrics: bool,
) -> None:
    """
    Parse and validate a Yuho source file.

    Runs syntax checking and semantic analysis, reporting any errors found.
    """
    from yuho.cli.commands.check import run_check
    run_check(
        file,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
        explain_errors=explain_errors,
        metrics=metrics,
    )


# =============================================================================
# AST command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--tree", "show_tree", is_flag=True, default=True, help="Show tree visualization (default)")
@click.option("--stats", is_flag=True, help="Show AST statistics")
@click.option("--depth", type=int, default=0, help="Max depth (0 = unlimited)")
@click.option("--ascii", "no_unicode", is_flag=True, help="Use ASCII-only characters")
@click.pass_context
def ast(
    ctx: click.Context,
    file: str,
    output: Optional[str],
    show_tree: bool,
    stats: bool,
    depth: int,
    no_unicode: bool,
) -> None:
    """
    Visualize AST structure as tree.

    Displays the abstract syntax tree of a Yuho statute using
    tree-like ASCII art in the terminal.

    Examples:
        yuho ast statute.yh
        yuho ast statute.yh --stats
        yuho ast statute.yh --ascii -o tree.txt
    """
    from yuho.cli.commands.ast_viz import run_ast_viz
    run_ast_viz(
        file=file,
        output=output,
        stats=stats,
        depth=depth,
        no_unicode=no_unicode,
        verbose=ctx.obj["verbose"],
        color=ctx.obj["color"],
    )


# =============================================================================
# Transpile command
# =============================================================================


@cli.command()
@click.argument("file", type=str)
@click.option(
    "-t", "--target",
    type=click.Choice(["json", "jsonld", "english", "latex", "mermaid", "alloy", "graphql", "blocks"], case_sensitive=False),
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

    Supported targets: json, jsonld, english, latex, mermaid, alloy, graphql, blocks
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
# Preview command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-t", "--target",
    type=click.Choice(["english", "mermaid"], case_sensitive=False),
    default="english",
    help="Preview format (english or mermaid)"
)
@click.option("-p", "--port", type=int, default=8000, help="Server port")
@click.option("--no-browser", is_flag=True, help="Don't auto-open browser")
@click.pass_context
def preview(
    ctx: click.Context,
    file: str,
    target: str,
    port: int,
    no_browser: bool,
) -> None:
    """
    Live preview with auto-reload on file changes.

    Watches the file for changes, transpiles to the target format,
    and serves a live-reloading preview in your browser.

    Examples:
        yuho preview statute.yh
        yuho preview statute.yh --target mermaid
        yuho preview statute.yh --port 3000 --no-browser
    """
    from yuho.cli.commands.preview import run_preview
    run_preview(
        file=file,
        target=target.lower(),
        port=port,
        no_browser=no_browser,
        verbose=ctx.obj["verbose"],
        color=ctx.obj["color"],
    )


# =============================================================================
# REPL command
# =============================================================================


@cli.command()
@click.pass_context
def repl(ctx: click.Context) -> None:
    """
    Start interactive REPL for statute experimentation.

    The REPL provides an interactive environment for:
    - Parsing and validating Yuho code snippets
    - Transpiling to various targets (json, english, mermaid, etc.)
    - Exploring statute definitions and AST structure
    - Testing legal logic interactively

    Type 'help' within the REPL for available commands.
    """
    from yuho.cli.commands.repl import run_repl
    sys.exit(run_repl(color=ctx.obj["color"], verbose=ctx.obj["verbose"]))


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
@click.option("--offline", is_flag=True, help="Disallow cloud providers and run local-only")
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
    offline: bool,
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
        offline=offline,
        verbose=ctx.obj["verbose"],
        stream=stream,
    )


# =============================================================================
# Diff command
# =============================================================================


@cli.command()
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def diff(ctx: click.Context, file1: str, file2: str, json_output: bool) -> None:
    """
    Compare two Yuho files and show semantic differences.

    Shows added, removed, and modified statutes, definitions, elements,
    penalties, and illustrations between two versions.

    Examples:
        yuho diff old.yh new.yh
        yuho diff v1/statute.yh v2/statute.yh --json
    """
    from yuho.cli.commands.diff import run_diff
    run_diff(
        file1,
        file2,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
        color=ctx.obj["color"],
    )


# =============================================================================
# Graph command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-f", "--format",
    type=click.Choice(["dot", "mermaid"], case_sensitive=False),
    default="mermaid",
    help="Output format"
)
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.pass_context
def graph(ctx: click.Context, file: str, format: str, output: Optional[str]) -> None:
    """
    Visualize statute dependencies as a graph.

    Generates a dependency graph showing:
    - Statute cross-references
    - Import relationships
    - Type and function definitions

    Examples:
        yuho graph statute.yh
        yuho graph statute.yh --format dot -o deps.dot
        yuho graph statute.yh --format mermaid > deps.md
    """
    from yuho.cli.commands.graph import run_graph
    run_graph(
        file,
        format=format,
        output=output,
        verbose=ctx.obj["verbose"],
        color=ctx.obj["color"],
    )


# =============================================================================
# Lint command
# =============================================================================


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--rule", "-r", "rules", multiple=True, help="Specific rules to run")
@click.option("--exclude", "-e", "exclude_rules", multiple=True, help="Rules to exclude")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--fix", is_flag=True, help="Auto-fix issues where possible")
@click.pass_context
def lint(
    ctx: click.Context,
    files: tuple,
    rules: tuple,
    exclude_rules: tuple,
    json_output: bool,
    fix: bool,
) -> None:
    """
    Check Yuho files for style and best practice issues.

    Analyzes files for:
    - Missing statute titles, elements, or penalties
    - Naming convention violations
    - Unused definitions
    - Duplicate section numbers

    Examples:
        yuho lint statute.yh
        yuho lint *.yh --exclude missing-penalty
        yuho lint src/ --json
    """
    from yuho.cli.commands.lint import run_lint
    run_lint(
        list(files),
        rules=list(rules) if rules else None,
        exclude_rules=list(exclude_rules) if exclude_rules else None,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
        color=ctx.obj["color"],
        fix=fix,
    )


# =============================================================================
# API command
# =============================================================================


@cli.command()
@click.option("-p", "--port", type=int, default=None, help="Port to listen on (defaults to config mcp.port)")
@click.option("--host", default=None, help="Host to bind to (defaults to config mcp.host)")
@click.pass_context
def api(ctx: click.Context, port: Optional[int], host: Optional[str]) -> None:
    """
    Start the REST API server for remote operations.

    Provides HTTP endpoints for:
    - Parsing and validating Yuho source code
    - Transpiling to various formats
    - Running lint checks

    Examples:
        yuho api
        yuho api --port 3000 --host 0.0.0.0
    """
    from yuho.cli.commands.api import run_api
    run_api(
        host=host,
        port=port,
        verbose=ctx.obj["verbose"],
        color=ctx.obj["color"],
    )


# =============================================================================
# Generate command
# =============================================================================


@cli.command()
@click.argument("section")
@click.option("-t", "--title", required=True, help="Statute title")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option(
    "--template",
    type=click.Choice(["standard", "minimal", "full"], case_sensitive=False),
    default="standard",
    help="Scaffold template type"
)
@click.option("--no-definitions", is_flag=True, help="Skip definitions block")
@click.option("--no-penalty", is_flag=True, help="Skip penalty block")
@click.option("--no-illustrations", is_flag=True, help="Skip illustrations block")
@click.option("-f", "--force", is_flag=True, help="Overwrite existing file")
@click.pass_context
def generate(
    ctx: click.Context,
    section: str,
    title: str,
    output: Optional[str],
    template: str,
    no_definitions: bool,
    no_penalty: bool,
    no_illustrations: bool,
    force: bool,
) -> None:
    """
    Generate statute scaffold with proper structure.

    Creates a boilerplate .yh file with the specified section number
    and title. Fill in the TODO markers to complete your statute.

    Examples:
        yuho generate 500 --title "Theft"
        yuho generate s299 --title "Culpable Homicide" --template full
        yuho generate 420 -t "Cheating" -o cheating.yh
    """
    from yuho.cli.commands.generate import run_generate
    run_generate(
        section=section,
        title=title,
        output=output,
        template=template.lower(),
        no_definitions=no_definitions,
        no_penalty=no_penalty,
        no_illustrations=no_illustrations,
        force=force,
        verbose=ctx.obj["verbose"],
        color=ctx.obj["color"],
    )


# =============================================================================
# Wizard command
# =============================================================================


@cli.command()
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--section", help="Pre-set section number")
@click.option("--title", help="Pre-set statute title")
@click.pass_context
def wizard(
    ctx: click.Context,
    output: Optional[str],
    section: Optional[str],
    title: Optional[str],
) -> None:
    """
    Interactive wizard for statute creation.

    Guides you through building a Yuho statute step-by-step using
    inquirer-style prompts. Generates valid .yh source files.

    Examples:
        yuho wizard
        yuho wizard -o my_statute.yh
        yuho wizard --section 299 --title "Culpable Homicide"
    """
    from yuho.cli.commands.wizard import run_wizard
    run_wizard(
        output=output,
        section=section,
        title=title,
        verbose=ctx.obj["verbose"],
        color=ctx.obj["color"],
    )


# =============================================================================
# Serve command
# =============================================================================


@cli.command()
@click.option("-p", "--port", type=int, default=None, help="Port to listen on (defaults to config mcp.port)")
@click.option("--host", default=None, help="Host to bind to (defaults to config mcp.host)")
@click.option("--stdio", is_flag=True, help="Use stdio transport (for editor integration)")
@click.pass_context
def serve(ctx: click.Context, port: Optional[int], host: Optional[str], stdio: bool) -> None:
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
@click.option("--coverage", is_flag=True, help="Enable coverage tracking")
@click.option("--coverage-html", type=click.Path(), help="Generate HTML coverage report")
@click.pass_context
def test(
    ctx: click.Context,
    file: Optional[str],
    run_all: bool,
    json_output: bool,
    coverage: bool,
    coverage_html: Optional[str],
) -> None:
    """
    Run tests for a Yuho statute file.

    Looks for test_<filename>.yh or tests/<filename>_test.yh

    Examples:
        yuho test statute.yh
        yuho test --all
        yuho test --all --coverage
        yuho test --all --coverage-html coverage.html
    """
    from yuho.cli.commands.test import run_test
    run_test(
        file,
        run_all=run_all,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
        coverage=coverage or bool(coverage_html),
        coverage_html=coverage_html,
    )


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


register_group_commands(cli)


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
