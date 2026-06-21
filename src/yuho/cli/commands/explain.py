"""Implementation for ``yuho explain``."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import click

from yuho.explain import DatalogExplainer, ElementTrace
from yuho.services.analysis import analyze_file


def run_explain(
    section: str,
    facts_file: str,
    library_dir: Optional[str] = None,
    json_output: bool = False,
    features: Optional[set[str]] = None,
) -> None:
    root = Path(library_dir) if library_dir else Path("library/penal_code")
    statute_path = _resolve_statute(root, section)
    if statute_path is None:
        click.echo(f"error: section not found in {root}: {section}", err=True)
        sys.exit(1)

    analysis = analyze_file(statute_path, run_semantic=True, features=features)
    if analysis.parse_errors or analysis.ast is None:
        click.echo(f"error: failed to parse {statute_path}", err=True)
        for error in analysis.parse_errors:
            click.echo(str(error), err=True)
        sys.exit(1)
    if analysis.semantic_summary and analysis.semantic_summary.has_errors:
        click.echo(f"error: semantic errors in {statute_path}", err=True)
        for issue in analysis.semantic_summary.issues:
            if issue.severity == "error":
                click.echo(issue.message, err=True)
        sys.exit(1)

    facts = _load_facts(Path(facts_file))
    statute = analysis.ast.statutes[0]
    trace = DatalogExplainer().explain(statute, facts)
    if json_output:
        click.echo(json.dumps(asdict(trace), indent=2, sort_keys=True))
        return
    _emit_text(trace)


def _resolve_statute(root: Path, section: str) -> Optional[Path]:
    direct = Path(section)
    if direct.exists():
        return direct
    normal = section[1:] if section.lower().startswith("s") else section
    candidates = sorted(root.glob(f"s{normal}_*/statute.yh"))
    if candidates:
        return candidates[0]
    exact = root / f"s{normal}" / "statute.yh"
    if exact.exists():
        return exact
    return None


def _load_facts(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        click.echo(f"error: failed to read facts file: {exc}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        click.echo(f"error: facts file must be a JSON object: {exc}", err=True)
        sys.exit(1)
    if not isinstance(data, dict):
        click.echo("error: facts file must be a JSON object", err=True)
        sys.exit(1)
    return data


def _emit_text(trace) -> None:
    status = "SATISFIED" if trace.overall_satisfied else "NOT SATISFIED"
    click.echo(f"Section {trace.statute_section}: {status}")
    for element in trace.elements:
        _emit_element(element, indent=0)


def _emit_element(element: ElementTrace, indent: int) -> None:
    pad = "  " * indent
    mark = "[x]" if element.satisfied else "[ ]"
    click.echo(f"{pad}{mark} {element.element_type}: {element.name}")
    click.echo(f"{pad}    {element.reason}")
    for child in element.children:
        _emit_element(child, indent + 1)
