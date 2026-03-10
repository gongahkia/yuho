"""
Training pair export for LLM fine-tuning.

Generates JSONL pairs of (yuho_source, english_output) from library
statutes, suitable for training legal language models.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from yuho.cli.error_formatter import Colors, colorize


def run_export_training(
    output: str = "training_pairs.jsonl",
    directory: Optional[str] = None,
    include_mermaid: bool = False,
    verbose: bool = False,
) -> None:
    """
    Export statute source/English pairs as JSONL for LLM training.

    Each line is a JSON object with:
      - source: raw .yh file content
      - english: English transpiler output
      - section: section number
      - title: statute title
      - mermaid: (optional) Mermaid diagram output
    """
    from yuho.services.analysis import analyze_file
    from yuho.transpile import TranspileTarget, get_transpiler

    lib_dir = Path(directory) if directory else Path.cwd() / "library"
    if not lib_dir.is_dir():
        click.echo(colorize(f"Directory not found: {lib_dir}", Colors.RED), err=True)
        sys.exit(1)

    statute_files = sorted(lib_dir.rglob("statute.yh"))
    if not statute_files:
        click.echo(colorize("No statute.yh files found", Colors.RED), err=True)
        sys.exit(1)

    english_t = get_transpiler(TranspileTarget.ENGLISH)
    mermaid_t = get_transpiler(TranspileTarget.MERMAID) if include_mermaid else None

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for yh_file in statute_files:
            source_text = yh_file.read_text(encoding="utf-8")
            result = analyze_file(yh_file, run_semantic=False)
            if not result.ast or not result.ast.statutes:
                if verbose:
                    click.echo(f"  skip {yh_file} (no statutes)")
                continue

            english_text = english_t.transpile(result.ast)
            for statute in result.ast.statutes:
                pair = {
                    "source": source_text,
                    "english": english_text,
                    "section": statute.section_number,
                    "title": statute.title.value if statute.title else "",
                }
                if mermaid_t:
                    pair["mermaid"] = mermaid_t.transpile(result.ast)
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
                count += 1

            if verbose:
                click.echo(f"  {yh_file}")

    click.echo(f"Exported {count} training pairs to {out_path}")
