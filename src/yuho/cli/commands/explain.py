"""Implementation for ``yuho explain``."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Sequence

import click

from yuho.ast import nodes
from yuho.explain import DatalogExplainer
from yuho.resolver import ModuleResolver
from yuho.services.analysis import analyze_file
from yuho.transpile.english_transpiler import EnglishTranspiler


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
    ast = _module_with_imported_definitions(analysis.ast, statute_path)
    statute = _select_statute(ast.statutes, section)
    statutes = {st.section_number: st for st in ast.statutes}
    trace = DatalogExplainer().explain(statute, facts, statutes)
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


def _module_with_imported_definitions(
    ast: nodes.ModuleNode,
    statute_path: Path,
) -> nodes.ModuleNode:
    if not ast.imports:
        return ast
    search_paths = [statute_path.parent, Path.cwd()]
    lib_path = Path.cwd() / "library"
    if lib_path.is_dir():
        search_paths.append(lib_path)
    resolver = ModuleResolver(search_paths=search_paths)
    try:
        return resolver.module_with_imported_definitions(ast, statute_path)
    except Exception as exc:
        click.echo(f"error: failed to resolve imports in {statute_path}: {exc}", err=True)
        sys.exit(1)


def _select_statute(
    statutes: Sequence[nodes.StatuteNode],
    section: str,
) -> nodes.StatuteNode:
    normal = section[1:] if section.lower().startswith("s") else section
    for statute in statutes:
        if getattr(statute, "section_number", None) == normal:
            return statute
    return statutes[0]


def _emit_text(trace) -> None:
    click.echo(EnglishTranspiler().render_explain_trace(trace))
