"""
Transpile command - convert Yuho files to other formats.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.transpile import TranspileTarget, get_transpiler
from yuho.cli.error_formatter import Colors, colorize


ALL_TARGETS = ["json", "jsonld", "english", "mermaid", "alloy"]


def run_transpile(
    file: str,
    target: str = "json",
    output: Optional[str] = None,
    output_dir: Optional[str] = None,
    all_targets: bool = False,
    json_output: bool = False,
    verbose: bool = False
) -> None:
    """
    Transpile a Yuho file to another format.

    Args:
        file: Path to the .yh file
        target: Target format (json, jsonld, english, mermaid, alloy)
        output: Output file path
        output_dir: Output directory for multiple files
        all_targets: Generate all targets
        json_output: Output metadata as JSON
        verbose: Enable verbose output
    """
    file_path = Path(file)

    if verbose:
        click.echo(f"Parsing {file_path}...")

    # Parse and build AST
    parser = Parser()
    try:
        result = parser.parse_file(file_path)
    except FileNotFoundError:
        click.echo(colorize(f"error: File not found: {file}", Colors.RED), err=True)
        sys.exit(1)

    if result.errors:
        click.echo(colorize(f"error: Parse errors in {file}", Colors.RED), err=True)
        for err in result.errors:
            click.echo(f"  {err.location}: {err.message}", err=True)
        sys.exit(1)

    builder = ASTBuilder(result.source, str(file_path))
    ast = builder.build(result.root_node)

    # Determine targets
    targets: List[str] = ALL_TARGETS if all_targets else [target]

    # Determine output directory
    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = None

    results = []

    for tgt in targets:
        if verbose:
            click.echo(f"Transpiling to {tgt}...")

        try:
            transpile_target = TranspileTarget.from_string(tgt)
            transpiler = get_transpiler(transpile_target)
            output_text = transpiler.transpile(ast)
        except ValueError as e:
            click.echo(colorize(f"error: {e}", Colors.RED), err=True)
            sys.exit(1)

        # Determine output path
        if all_targets or output_dir:
            # Multiple targets -> use directory
            if out_dir:
                out_path = out_dir / f"{file_path.stem}{transpile_target.file_extension}"
            else:
                out_path = file_path.parent / f"{file_path.stem}{transpile_target.file_extension}"

            out_path.write_text(output_text, encoding="utf-8")
            results.append({"target": tgt, "output": str(out_path)})

            if not json_output:
                click.echo(f"  -> {out_path}")

        elif output:
            # Single target with explicit output
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output_text, encoding="utf-8")
            results.append({"target": tgt, "output": str(out_path)})

            if not json_output:
                click.echo(f"  -> {out_path}")

        else:
            # Single target to stdout
            print(output_text)
            results.append({"target": tgt, "output": "stdout"})

    if json_output:
        print(json.dumps({
            "source": str(file_path),
            "results": results,
        }, indent=2))
