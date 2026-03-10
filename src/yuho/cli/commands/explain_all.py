"""
Pre-built explainer generator.

Generates English explanations for all library statutes and writes them
as standalone .txt files alongside the statute sources.
"""

import sys
from pathlib import Path

import click

from yuho.cli.error_formatter import Colors, colorize


def run_explain_all(
    directory: str = "library",
    output_dir: str = "doc/explanations",
    verbose: bool = False,
) -> None:
    """Generate English explanations for all library statutes."""
    from yuho.services.analysis import analyze_file
    from yuho.transpile import TranspileTarget, get_transpiler

    lib_dir = Path(directory)
    if not lib_dir.is_dir():
        click.echo(colorize(f"Directory not found: {lib_dir}", Colors.RED), err=True)
        sys.exit(1)

    statute_files = sorted(lib_dir.rglob("statute.yh"))
    if not statute_files:
        click.echo(colorize("No statute.yh files found", Colors.RED), err=True)
        sys.exit(1)

    english_t = get_transpiler(TranspileTarget.ENGLISH)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for f in statute_files:
        result = analyze_file(f, run_semantic=False)
        if not result.ast or not result.ast.statutes:
            if verbose:
                click.echo(f"  skip {f}")
            continue
        text = english_t.transpile(result.ast)
        rel = f.relative_to(lib_dir)
        out_path = out_dir / rel.with_suffix(".txt")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        count += 1
        if verbose:
            click.echo(f"  {f} -> {out_path}")

    click.echo(f"Generated {count} explanations in {out_dir}")
