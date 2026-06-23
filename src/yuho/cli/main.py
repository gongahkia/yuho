"""Core CLI for the Yuho statute DSL compiler."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Literal, Optional, cast

import click

from yuho import __version__
from yuho.caselaw import TREATMENT_EDGE_KINDS


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def _detect_color_support() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    return os.environ.get("TERM", "") != "dumb"


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="yuho")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("--color/--no-color", "use_color", default=None, help="Force color output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-error output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, use_color: Optional[bool], quiet: bool) -> None:
    """Yuho - statute-core DSL compiler and corpus tooling."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose and not quiet
    ctx.obj["quiet"] = quiet
    ctx.obj["color"] = _detect_color_support() if use_color is None else use_color

    from yuho.cli import error_formatter

    error_formatter.COLOR_ENABLED = ctx.obj["color"]
    log_level = os.environ.get("YUHO_LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.WARNING),
        format="%(name)s %(levelname)s %(message)s",
    )


@cli.command()
@click.option("--sample", type=click.Path(), help="Sample .yh file to validate")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON")
@click.option("--strict", is_flag=True, help="Exit 1 on warnings as well as failures")
def doctor(sample: Optional[str], json_output: bool, strict: bool) -> None:
    """Check local install readiness."""
    from yuho.cli.commands.doctor import run_doctor

    run_doctor(sample=sample, json_output=json_output, strict=strict)


@cli.command()
@click.argument("directory", required=False, default="yuho-starter")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--no-run", "no_run", is_flag=True, help="Skip starter smoke checks")
@click.option(
    "--template",
    "template",
    type=click.Choice(
        [
            "basic",
            "statute-literate",
            "statute-exceptions",
            "statute-cross-reference",
        ]
    ),
    default="basic",
    show_default=True,
    help="Starter template",
)
@click.option("--guided", is_flag=True, help="Prompt for starter template and title")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON")
def init(
    directory: str,
    force: bool,
    no_run: bool,
    template: str,
    guided: bool,
    json_output: bool,
) -> None:
    """Create a runnable starter workspace."""
    from yuho.cli.commands.init import run_init

    run_init(
        directory=directory,
        force=force,
        run_smoke=not no_run,
        template=template,
        guided=guided,
        json_output=json_output,
    )


@cli.command()
@click.argument("file", type=str)
@click.option("--json", "json_output", is_flag=True, help="Output errors as JSON")
@click.option("--explain-error", "explain_errors", is_flag=True, help="Explain diagnostics")
@click.option("--metrics", is_flag=True, help="Include code_scale and clock_load_scale metrics")
@click.option("--watch", is_flag=True, help="Re-run when FILE changes")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "sarif"]),
    default="text",
    help="Output format",
)
@click.option("--syntax-only", is_flag=True, help="Skip semantic analysis")
@click.option(
    "--feature",
    "features",
    multiple=True,
    type=click.Choice(["civil"]),
    help="Enable experimental language feature",
)
@click.pass_context
def check(
    ctx: click.Context,
    file: str,
    json_output: bool,
    explain_errors: bool,
    metrics: bool,
    watch: bool,
    output_format: str,
    syntax_only: bool,
    features: tuple[str, ...],
) -> None:
    """Parse and validate a Yuho source file."""
    from yuho.cli.commands.check import run_check

    run_check(
        file,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
        explain_errors=explain_errors,
        metrics=metrics,
        watch=watch,
        output_format=output_format,
        syntax_only=syntax_only,
        features=set(features),
    )


@cli.command()
@click.argument("file", type=str)
@click.option("-i", "--in-place", is_flag=True, help="Rewrite FILE in place")
@click.option("--check", "check_only", is_flag=True, help="Exit 1 if FILE needs upgrade")
@click.option("--from", "from_version", help="Expected source grammar version")
@click.option("--to", "to_version", default="5.1", show_default=True, help="Target grammar version")
@click.pass_context
def upgrade(
    ctx: click.Context,
    file: str,
    in_place: bool,
    check_only: bool,
    from_version: Optional[str],
    to_version: str,
) -> None:
    """Rewrite Yuho source to the requested grammar version."""
    from yuho.cli.commands.upgrade import run_upgrade

    run_upgrade(
        file,
        in_place=in_place,
        check=check_only,
        from_version=from_version,
        to_version=to_version,
        quiet=ctx.obj["quiet"],
    )


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--rule", "-r", "rules", multiple=True, help="Specific rules to run")
@click.option("--exclude", "-e", "exclude_rules", multiple=True, help="Rules to exclude")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--fix", is_flag=True, help="Auto-fix issues where supported")
@click.option(
    "--mode",
    "lint_mode",
    type=click.Choice(["transcription", "executable"]),
    default="transcription",
    show_default=True,
    help="Lint posture",
)
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
    files: tuple[str, ...],
    rules: tuple[str, ...],
    exclude_rules: tuple[str, ...],
    json_output: bool,
    fix: bool,
    lint_mode: str,
    output_format: str,
) -> None:
    """Run statute-core lint and fidelity diagnostics."""
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
        mode=lint_mode,
    )


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-i", "--in-place", is_flag=True, help="Format file in place")
@click.option("--check", is_flag=True, help="Check formatting")
@click.pass_context
def fmt(ctx: click.Context, file: str, in_place: bool, check: bool) -> None:
    """Format a Yuho source file."""
    from yuho.cli.commands.fmt import run_fmt

    run_fmt(file, in_place=in_place, check=check, verbose=ctx.obj["verbose"])


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--stats", is_flag=True, help="Show AST statistics")
@click.option("--depth", type=int, default=0, help="Max depth; 0 means unlimited")
@click.option("--ascii", "no_unicode", is_flag=True, help="Use ASCII-only tree output")
@click.pass_context
def ast(
    ctx: click.Context,
    file: str,
    output: Optional[str],
    stats: bool,
    depth: int,
    no_unicode: bool,
) -> None:
    """Visualize the parsed AST."""
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
            "mindmap",
            "mermaid-mindmap",
            "svg",
            "png",
            "alloy",
            "docx",
            "akomantoso",
            "akn",
            "legaldocml",
            "legalruleml",
            "lrml",
        ],
        case_sensitive=False,
    ),
    default="json",
    help="Transpilation target format",
)
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--dir", "output_dir", type=click.Path(), help="Output directory")
@click.option("--all", "all_targets", is_flag=True, help="Generate all retained targets")
@click.option(
    "--shape",
    type=click.Choice(["statute", "schema", "verbose"], case_sensitive=False),
    default="statute",
    help="Mermaid flowchart shape",
)
@click.option("--json", "json_output", is_flag=True, help="Output metadata as JSON")
@click.pass_context
def transpile(
    ctx: click.Context,
    file: str,
    target: str,
    output: Optional[str],
    output_dir: Optional[str],
    all_targets: bool,
    shape: str,
    json_output: bool,
) -> None:
    """Transpile a Yuho source file."""
    from yuho.cli.commands.transpile import run_transpile

    run_transpile(
        file,
        target=target,
        shape=shape,
        output=output,
        output_dir=output_dir,
        all_targets=all_targets,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@cli.command()
@click.argument("targets", nargs=-1)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--score", is_flag=True, help="Score file2 against file1")
@click.option(
    "--jurisdictions",
    help="Comma-separated jurisdiction codes for corpus section diff, e.g. sg,my,pk",
)
@click.pass_context
def diff(
    ctx: click.Context,
    targets: tuple[str, ...],
    json_output: bool,
    score: bool,
    jurisdictions: Optional[str],
) -> None:
    """Compare Yuho statute files or corpus sections."""
    if jurisdictions:
        if score:
            raise click.UsageError("--score cannot be combined with --jurisdictions")
        if len(targets) != 1:
            raise click.UsageError("--jurisdictions requires exactly one SECTION argument")
        from yuho.cli.commands.diff import run_jurisdiction_diff

        run_jurisdiction_diff(
            targets[0],
            jurisdictions=jurisdictions.split(","),
            json_output=json_output,
            verbose=ctx.obj["verbose"],
            color=ctx.obj["color"],
        )
        return

    if len(targets) != 2:
        raise click.UsageError(
            "diff requires FILE1 FILE2, or --jurisdictions JURISDICTIONS SECTION"
        )
    file1, file2 = targets
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
    """Run legal tests embedded in Yuho files."""
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
@click.option("--alloy-timeout", type=int, default=30, show_default=True)
@click.option("--z3-timeout-ms", type=int, default=5000, show_default=True)
@click.option("--reference-date", default=None, help="YYYY-MM-DD date for exact calendar durations")
@click.option("--capabilities", "capabilities_only", is_flag=True, help="Show backend status")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def verify(
    ctx: click.Context,
    file: Optional[str],
    engine: str,
    alloy_jar: Optional[str],
    alloy_timeout: int,
    z3_timeout_ms: int,
    reference_date: Optional[str],
    capabilities_only: bool,
    json_output: bool,
) -> None:
    """Run retained formal verification backends."""
    from yuho.cli.commands.verify import run_verify

    run_verify(
        file,
        engine=engine,
        alloy_jar=alloy_jar,
        alloy_timeout=alloy_timeout,
        z3_timeout_ms=z3_timeout_ms,
        reference_date=reference_date,
        capabilities_only=capabilities_only,
        json_output=json_output,
        verbose=ctx.obj["verbose"],
    )


@cli.command(name="debug")
@click.argument("facts_file", type=click.Path(exists=True))
@click.argument("statute_file", type=click.Path(exists=True))
@click.option(
    "--break-on",
    "break_on",
    type=click.Choice(["element"], case_sensitive=False),
    required=True,
    help="Breakpoint target",
)
@click.option("--json", "json_output", is_flag=True, help="Emit JSON")
def debug_cmd(
    facts_file: str,
    statute_file: str,
    break_on: str,
    json_output: bool,
) -> None:
    """Debug statute evaluation against facts."""
    from yuho.cli.commands.debug import run_debug

    run_debug(
        facts_file=facts_file,
        statute_file=statute_file,
        break_on=break_on,
        json_output=json_output,
    )


@cli.command()
@click.argument("section")
@click.option("--facts", "facts_file", type=click.Path(exists=True), required=True)
@click.option("--library", "library_dir", type=click.Path(), default=None, help="Library root")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON")
@click.option(
    "--feature",
    "features",
    multiple=True,
    type=click.Choice(["civil"]),
    help="Enable experimental language feature",
)
def explain(
    section: str,
    facts_file: str,
    library_dir: Optional[str],
    json_output: bool,
    features: tuple[str, ...],
) -> None:
    """Explain element-by-element statute satisfaction."""
    from yuho.cli.commands.explain import run_explain

    run_explain(
        section=section,
        facts_file=facts_file,
        library_dir=library_dir,
        json_output=json_output,
        features=set(features),
    )


@cli.command()
@click.argument("statute_file", type=click.Path(exists=True))
@click.option("--facts", "facts_file", type=click.Path(exists=True), required=True)
@click.option(
    "--feature",
    "features",
    multiple=True,
    type=click.Choice(["civil"]),
    help="Enable experimental language feature",
)
def irac(
    statute_file: str,
    facts_file: str,
    features: tuple[str, ...],
) -> None:
    """Emit IRAC-structured English for a statute and facts."""
    from yuho.cli.commands.irac import run_irac

    run_irac(
        statute_file=statute_file,
        facts_file=facts_file,
        features=set(features),
    )


@cli.command()
@click.argument("statute_file", type=click.Path(exists=True))
@click.option("--legal-text", "legal_text_file", type=click.Path(exists=True), required=True)
@click.option("--facts", "facts_file", type=click.Path(exists=True), default=None)
@click.option("-o", "--output", type=click.Path(), default=None)
@click.option(
    "--format",
    "report_format",
    type=click.Choice(["markdown", "html"]),
    default="markdown",
    show_default=True,
    help="Report format",
)
def literate(
    statute_file: str,
    legal_text_file: str,
    facts_file: Optional[str],
    output: Optional[str],
    report_format: str,
) -> None:
    """Generate a literate statute mapping report."""
    from yuho.cli.commands.literate import run_literate

    run_literate(
        statute_file=statute_file,
        legal_text_file=legal_text_file,
        facts_file=facts_file,
        output=output,
        report_format=report_format,
    )


@cli.command()
@click.argument("section", required=False)
@click.option("--library", "library_dir", type=click.Path(), default=None, help="Library root")
@click.option("--in", "in_only", is_flag=True, help="Only show incoming edges")
@click.option("--out", "out_only", is_flag=True, help="Only show outgoing edges")
@click.option(
    "--kind",
    "kinds",
    multiple=True,
    type=click.Choice(
        [
            "subsumes",
            "amends",
            "implicit",
            "authority",
            *TREATMENT_EDGE_KINDS,
        ]
    ),
    help="Filter edge kind",
)
@click.option("--treatment", is_flag=True, help="Query case-law treatment edges")
@click.option("--overruled", is_flag=True, help="Query overruled case-law edges")
@click.option("--transitive", is_flag=True, help="Follow edges transitively")
@click.option("--graph", "show_graph", is_flag=True, help="Print full graph summary")
@click.option("--scc", "scc", is_flag=True, help="Run SCC analysis")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON")
def refs(
    section: Optional[str],
    library_dir: Optional[str],
    in_only: bool,
    out_only: bool,
    kinds: tuple[str, ...],
    treatment: bool,
    overruled: bool,
    transitive: bool,
    show_graph: bool,
    scc: bool,
    json_output: bool,
) -> None:
    """Query the checked-in corpus reference graph."""
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
        treatment=treatment,
        overruled=overruled,
        transitive=transitive,
        json_output=json_output,
        show_graph=show_graph,
        scc=scc,
    )


@cli.command()
@click.option("-o", "--output", type=click.Path(), help="Output file path")
def schema(output: Optional[str]) -> None:
    """Emit the JSON Schema for Yuho JSON transpiler output."""
    from yuho.transpile.json_schema import generate_json_schema

    text = generate_json_schema()
    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Schema written to {output}")
    else:
        print(text)


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False))
@click.option("--install", "show_install", is_flag=True, help="Show installation instructions")
def completion(shell: str, show_install: bool) -> None:
    """Emit a shell completion script for bash, zsh, or fish."""
    from yuho.cli.completions import get_completion_script, get_install_instructions

    shell_name = cast(Literal["bash", "zsh", "fish"], shell.lower())
    if show_install:
        click.echo(get_install_instructions(shell_name))
    else:
        click.echo(get_completion_script(shell_name))


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
        click.echo("hint: install the optional dependency for this retained target", err=True)
        sys.exit(1)
    except (ValueError, FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"error: unexpected failure: {type(e).__name__}: {e}", err=True)
        click.echo("hint: run with -v or file an issue with a minimal .yh input", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
