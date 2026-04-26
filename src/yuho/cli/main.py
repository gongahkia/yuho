"""
Main CLI entry point using Click.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Literal, Optional, cast

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
    help="Force color output on/off (auto-detected by default)",
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-error output")
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

    # Wire YUHO_LOG_LEVEL env var
    log_level = os.environ.get("YUHO_LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.WARNING),
        format="%(name)s %(levelname)s %(message)s",
    )


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
# Explore command (counter-example explorer)
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.argument("section", type=str)
@click.option("--max-satisfying", type=int, default=5, show_default=True,
              help="Cap on satisfying scenarios returned")
@click.option("--no-borderline", is_flag=True,
              help="Skip the per-element load-bearing analysis")
@click.option("--no-exceptions", is_flag=True,
              help="Skip the exception coverage / dead-exception scan")
@click.option("--subsume", "subsume_target", default=None,
              help="Compare with another section: report disjoint / overlap / "
                   "subsumes / equal relation. Pass the other section number.")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def explore(
    file: str,
    section: str,
    max_satisfying: int,
    no_borderline: bool,
    no_exceptions: bool,
    subsume_target: Optional[str],
    json_output: bool,
):
    """Counter-example explorer: surface fact patterns over a section.

    Reuses the Z3 verifier to enumerate (a) satisfying scenarios where the
    section's elements are all met, (b) borderline scenarios showing which
    elements are load-bearing, and (c) which exceptions are reachable.

    With --subsume <n>, compares the two sections and reports their
    relation (disjoint / overlap / one subsumes the other / equal),
    along with witness fact-bindings for each direction.

    Examples:
        yuho explore library/penal_code/s415_cheating/statute.yh 415
        yuho explore module.yh 415 --subsume 420 --json
    """
    from yuho.cli.commands.explore import run_explore

    run_explore(
        file,
        section,
        max_satisfying=max_satisfying,
        no_borderline=no_borderline,
        no_exceptions=no_exceptions,
        subsume_target=subsume_target,
        json_output=json_output,
    )


# =============================================================================
# Recommend command (charge recommender)
# =============================================================================


@cli.command()
@click.argument("facts_path", type=click.Path(exists=True))
@click.option("--top-k", type=int, default=5, show_default=True,
              help="How many ranked candidates to return")
@click.option("--max-candidates", type=int, default=60, show_default=True,
              help="Cap on sections whose simulator trace gets run")
@click.option("--min-coverage", type=float, default=0.0, show_default=True,
              help="Drop candidates below this coverage fraction (0.0 .. 1.0)")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def recommend(
    facts_path: str,
    top_k: int,
    max_candidates: int,
    min_coverage: float,
    json_output: bool,
):
    """Charge-recommender: rank Penal Code sections that structurally fit a fact pattern.

    NOT LEGAL ADVICE — every output carries an explicit disclaimer. The
    recommender re-uses the existing fact-pattern simulator for per-element
    traces, then sorts by coverage. No external LLM, no scraping.

    Example:
        yuho recommend simulator/fixtures/s415_classic.yaml
    """
    from yuho.cli.commands.recommend import run_recommend

    run_recommend(
        facts_path,
        top_k=top_k,
        max_candidates=max_candidates,
        min_coverage=min_coverage,
        json_output=json_output,
    )


# =============================================================================
# Check command
# =============================================================================


@cli.command()
@click.argument("file", type=str)
@click.option("--json", "json_output", is_flag=True, help="Output errors as JSON")
@click.option(
    "--explain-error",
    "explain_errors",
    is_flag=True,
    help="Show detailed explanations for errors with common causes and fixes",
)
@click.option("--metrics", is_flag=True, help="Include code_scale and clock_load_scale metrics")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "sarif"]),
    default="text",
    help="Output format",
)
@click.option(
    "--syntax-only",
    is_flag=True,
    help="Skip semantic analysis and report only parse/AST validity",
)
@click.pass_context
def check(
    ctx: click.Context,
    file: str,
    json_output: bool,
    explain_errors: bool,
    metrics: bool,
    output_format: str,
    syntax_only: bool,
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
        output_format=output_format,
        syntax_only=syntax_only,
    )


# =============================================================================
# AST command
# =============================================================================


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option(
    "--tree", "show_tree", is_flag=True, default=True, help="Show tree visualization (default)"
)
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
    "-t",
    "--target",
    type=click.Choice(
        [
            "json",
            "english",
            "latex",
            "pdf",
            "mermaid",
            "svg",
            "png",
            "alloy",
            "docx",
            "akomantoso",
            "akn",
            "legaldocml",
        ],
        case_sensitive=False,
    ),
    default="json",
    help="Transpilation target format",
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
    json_output: bool,
) -> None:
    """
    Transpile a Yuho source file to another format.

    Supported targets: json, english, latex, pdf, mermaid, alloy
    """
    from yuho.cli.commands.transpile import run_transpile

    run_transpile(
        file,
        target=target,
        output=output,
        output_dir=output_dir,
        all_targets=all_targets,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
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


# =============================================================================
# Diff command
# =============================================================================
# (The LLM-backed `explain` command was cut in the Phase D endpoint trim.
# For narrative output, use `yuho transpile <file> --target english`.
# For interactive AI explanation, connect via the MCP server.)


@cli.command()
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--score", is_flag=True, help="Score file2 against file1 as model answer")
@click.pass_context
def diff(ctx: click.Context, file1: str, file2: str, json_output: bool, score: bool) -> None:
    """
    Compare two Yuho files and show semantic differences.

    Shows added, removed, and modified statutes, definitions, elements,
    penalties, and illustrations between two versions.

    Use --score to grade file2 against file1 as a model answer, showing
    element coverage percentage.

    Examples:
        yuho diff old.yh new.yh
        yuho diff v1/statute.yh v2/statute.yh --json
        yuho diff model.yh student.yh --score
    """
    if score:
        from yuho.cli.commands.diff import run_diff_score

        run_diff_score(
            file1,
            file2,
            json_output=json_output,
            verbose=ctx.obj["verbose"],
            color=ctx.obj["color"],
        )
    else:
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
    "-f",
    "--format",
    type=click.Choice(["dot", "mermaid"], case_sensitive=False),
    default="mermaid",
    help="Output format",
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
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "sarif"]),
    default="text",
    help="Output format",
)
@click.pass_context
def lint(
    ctx: click.Context,
    files: tuple,
    rules: tuple,
    exclude_rules: tuple,
    json_output: bool,
    fix: bool,
    output_format: str,
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
        yuho lint src/ --format sarif
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
        output_format=output_format,
    )


# =============================================================================
# Generate command
# =============================================================================
# (The REST `api` command was cut in the Phase D endpoint trim.
# The CLI is now the primary interface; for AI integration use the MCP server.)


@cli.command()
@click.argument("section")
@click.option("-t", "--title", required=True, help="Statute title")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option(
    "--template",
    type=click.Choice(["standard", "minimal", "full"], case_sensitive=False),
    default="standard",
    help="Scaffold template type",
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
@click.option(
    "-p", "--port", type=int, default=None, help="Port to listen on (defaults to config mcp.port)"
)
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
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "junit"]),
    default="text",
    help="Output format",
)
@click.pass_context
def test(
    ctx: click.Context,
    file: Optional[str],
    run_all: bool,
    json_output: bool,
    coverage: bool,
    coverage_html: Optional[str],
    output_format: str,
) -> None:
    """
    Run tests for a Yuho statute file.

    Looks for test_<filename>.yh or tests/<filename>_test.yh

    Examples:
        yuho test statute.yh
        yuho test --all
        yuho test --all --format junit
    """
    from yuho.cli.commands.test import run_test

    run_test(
        file,
        run_all=run_all,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
        coverage=coverage or bool(coverage_html),
        coverage_html=coverage_html,
        output_format=output_format,
    )


# =============================================================================
# LSP command
# =============================================================================


@cli.command()
@click.option("--tcp", type=int, help="Start LSP server on TCP port")
@click.option(
    "--workspace",
    is_flag=True,
    help="On startup, walk every .yh file in each workspace folder and "
    "publish diagnostics. Editor's 'problems' panel will show issues "
    "from the entire library, not just open documents.",
)
@click.pass_context
def lsp(ctx: click.Context, tcp: Optional[int], workspace: bool) -> None:
    """
    Start the Language Server Protocol server.

    For editor integration (VS Code, Neovim, etc.).
    """
    from yuho.cli.commands.lsp import run_lsp

    run_lsp(tcp=tcp, verbose=ctx.obj["verbose"], workspace=workspace)


# =============================================================================
# Completion command
# =============================================================================


@cli.command()
@click.argument(
    "shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
)
@click.option("--install", "show_install", is_flag=True, help="Show installation instructions")
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
    shell_name = cast(Literal["bash", "zsh", "fish"], shell_lower)

    if show_install:
        click.echo(get_install_instructions(shell_name))
    else:
        click.echo(get_completion_script(shell_name))


register_group_commands(cli)


@cli.command()
@click.option("-o", "--output", type=click.Path(), help="Output file path")
def schema(output: Optional[str]) -> None:
    """
    Print JSON Schema for Yuho JSON transpiler output.

    Useful for validating transpiler output or integrating with
    downstream tools that consume Yuho JSON.

    Examples:
        yuho schema
        yuho schema -o yuho-ast.schema.json
    """
    from yuho.transpile.json_schema import generate_json_schema

    text = generate_json_schema()
    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Schema written to {output}")
    else:
        print(text)


@cli.command("compliance-matrix")
@click.argument("file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def compliance_matrix(
    ctx: click.Context, file: str, output: Optional[str], json_output: bool
) -> None:
    """
    Generate a compliance checklist from statute elements.

    Produces a table of all statutory requirements with checkboxes
    for compliance officers to audit.

    Examples:
        yuho compliance-matrix statute.yh
        yuho compliance-matrix statute.yh -o matrix.md
        yuho compliance-matrix statute.yh --json
    """
    from yuho.cli.commands.compliance import run_compliance_matrix

    run_compliance_matrix(
        file=file,
        output=output,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@cli.command("generate-tests")
@click.argument("file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option(
    "-n",
    "--max-cases",
    type=int,
    default=10,
    show_default=True,
    help="Maximum test cases to generate",
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def generate_tests(
    ctx: click.Context, file: str, output: Optional[str], max_cases: int, json_output: bool
) -> None:
    """
    Generate test cases using Z3 constraint solving.

    Uses Z3 model enumeration to produce concrete fact patterns
    that exercise different code paths through statute elements.

    Examples:
        yuho generate-tests statute.yh
        yuho generate-tests statute.yh -n 20 --json -o tests.json
    """
    from yuho.cli.commands.generate_tests import run_generate_tests

    run_generate_tests(
        file=file,
        output=output,
        max_cases=max_cases,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@cli.command("verify-report")
@click.argument("file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output .tex file path")
@click.pass_context
def verify_report(ctx: click.Context, file: str, output: Optional[str]) -> None:
    """
    Generate a LaTeX verification report for statute completeness.

    Checks structural elements (title, actus reus, mens rea, penalty,
    definitions, illustrations, exceptions, jurisdiction, doc-comments)
    and produces a color-coded PASS/WARN/FAIL table.

    Examples:
        yuho verify-report statute.yh
        yuho verify-report statute.yh -o report.tex
    """
    from yuho.services.analysis import analyze_file
    from yuho.transpile.verification_report import generate_verification_report

    result = analyze_file(file)
    if not result.is_valid or result.ast is None:
        for err in result.errors:
            click.echo(f"  {err}", err=True)
        sys.exit(1)
    tex = generate_verification_report(result.ast)
    if output:
        Path(output).write_text(tex, encoding="utf-8")
        click.echo(f"Report written to {output}")
    else:
        print(tex)


@cli.command("ci-report")
@click.argument("directory", default=".", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "sarif", "junit"]),
    default="json",
    help="Output format",
)
@click.pass_context
def ci_report(ctx: click.Context, directory: str, output: Optional[str], fmt: str) -> None:
    """Run check+lint on all .yh files and produce a unified report."""
    from yuho.cli.commands.ci_report import run_ci_report

    sys.exit(run_ci_report(directory=directory, output=output, format=fmt))


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def deps(ctx: click.Context, file: str, json_output: bool) -> None:
    """
    Show statute dependencies for a Yuho file.

    Lists all imports, references, and subsumption relations.

    Examples:
        yuho deps statute.yh
        yuho deps statute.yh --json
    """
    import json as json_mod
    from yuho.services.analysis import analyze_file

    result = analyze_file(file)
    if not result.is_valid or result.ast is None:
        for err in result.errors:
            click.echo(f"  {err}", err=True)
        sys.exit(1)
    ast = result.ast
    imports = [imp.path for imp in ast.imports]
    refs = [ref.path for ref in ast.references]
    subsumes: List[Dict[str, str]] = []
    for statute in ast.statutes:
        subsumed_section = getattr(statute, "subsumes", None)
        if isinstance(subsumed_section, str):
            subsumes.append({"from": statute.section_number, "subsumes": subsumed_section})
    if json_output:
        print(
            json_mod.dumps({"imports": imports, "references": refs, "subsumes": subsumes}, indent=2)
        )
    else:
        click.echo(f"Dependencies for {file}:")
        if imports:
            click.echo(f"  Imports: {', '.join(imports)}")
        if refs:
            click.echo(f"  References: {', '.join(refs)}")
        if subsumes:
            for relation in subsumes:
                click.echo(f"  s{relation['from']} subsumes s{relation['subsumes']}")
        if not imports and not refs and not subsumes:
            click.echo("  No dependencies")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def eval(ctx: click.Context, file: str, json_output: bool) -> None:
    """
    Evaluate a Yuho file through the interpreter.

    Parses, analyzes, and evaluates the file, reporting
    registered statutes, structs, functions, and bindings.

    Examples:
        yuho eval statute.yh
        yuho eval statute.yh --json
    """
    import json as json_mod
    from yuho.services.analysis import analyze_file
    from yuho.eval.interpreter import Interpreter

    result = analyze_file(file)
    if not result.is_valid or result.ast is None:
        for err in result.errors:
            click.echo(f"  {err}", err=True)
        sys.exit(1)
    interp = Interpreter()
    env = interp.interpret(result.ast)
    if json_output:
        data = {
            "statutes": list(env.statutes.keys()),
            "struct_defs": list(env.struct_defs.keys()),
            "function_defs": (
                [k for k in env.function_defs.keys()] if hasattr(env, "function_defs") else []
            ),
            "enum_defs": list(env.enum_defs.keys()) if hasattr(env, "enum_defs") else [],
            "bindings": {k: str(v) for k, v in env.bindings.items()},
        }
        print(json_mod.dumps(data, indent=2))
    else:
        click.echo(f"Evaluated {file}")
        click.echo(f"  Statutes: {', '.join(env.statutes.keys()) or 'none'}")
        click.echo(f"  Structs: {', '.join(env.struct_defs.keys()) or 'none'}")
        if hasattr(env, "enum_defs") and env.enum_defs:
            click.echo(f"  Enums: {', '.join(env.enum_defs.keys())}")
        if env.bindings:
            click.echo(f"  Bindings: {len(env.bindings)}")


@cli.command()
@click.argument("section", required=False)
@click.option("--library", "library_dir", type=click.Path(), default=None,
              help="Library root (default: library/penal_code)")
@click.option("--in", "in_only", is_flag=True, help="Only show edges entering the section")
@click.option("--out", "out_only", is_flag=True, help="Only show edges leaving the section")
@click.option("--kind", "kinds", multiple=True,
              type=click.Choice(["subsumes", "amends", "implicit"]),
              help="Filter to specific edge kinds (repeatable)")
@click.option("--transitive", is_flag=True, help="Follow edges transitively (BFS closure)")
@click.option("--graph", "show_graph", is_flag=True,
              help="Print the full graph summary when no section is given")
@click.option("--scc", "scc", is_flag=True,
              help="Run SCC analysis: list non-trivial cycles + lint warnings")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON instead of human text")
@click.pass_context
def refs(
    ctx: click.Context,
    section: Optional[str],
    library_dir: Optional[str],
    in_only: bool,
    out_only: bool,
    kinds: tuple,
    transitive: bool,
    show_graph: bool,
    scc: bool,
    json_output: bool,
) -> None:
    """Query the cross-section reference graph (G10).

    With a section number, prints the edges entering and/or leaving that
    section. Without a section, prints aggregate stats; pass --graph to dump
    the full graph.

    Examples:
        yuho refs s415               # in + out for s415
        yuho refs s415 --out --transitive
        yuho refs s415 --kind subsumes
        yuho refs                    # full-graph stats
        yuho refs --graph            # full graph summary
        yuho refs s415 --json
    """
    from yuho.cli.commands.refs import run_refs

    if in_only and out_only:
        direction = "both"
    elif in_only:
        direction = "in"
    elif out_only:
        direction = "out"
    else:
        direction = "both"

    norm = section
    if norm and norm.lower().startswith("s") and len(norm) > 1 and norm[1].isdigit():
        norm = norm[1:]

    run_refs(
        section=norm,
        library_dir=library_dir,
        direction=direction,
        kinds=kinds,
        transitive=transitive,
        json_output=json_output,
        show_graph=show_graph,
        scc=scc,
    )


def main() -> None:
    """Main entry point with global error handling."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nInterrupted.", err=True)
        sys.exit(130)
    except MemoryError:
        click.echo("error: out of memory", err=True)
        sys.exit(1)
    except ImportError as e:
        click.echo(f"error: missing dependency: {e}", err=True)
        click.echo(
            "hint: run 'pip install yuho[all]' to install all optional dependencies", err=True
        )
        sys.exit(1)
    except (ValueError, FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"error: unexpected failure: {type(e).__name__}: {e}", err=True)
        click.echo(
            "hint: run with -v for verbose output, or report at github.com/gongahkia/yuho/issues",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
