"""Implementation for ``yuho irac``."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from yuho.cli.commands.explain import _load_facts
from yuho.explain import DatalogExplainer
from yuho.services.analysis import analyze_file
from yuho.transpile.english_transpiler import EnglishTranspiler


def run_irac(
    statute_file: str,
    facts_file: str,
    features: Optional[set[str]] = None,
) -> None:
    analysis = analyze_file(statute_file, run_semantic=True, features=features)
    if analysis.parse_errors or analysis.ast is None:
        click.echo(f"error: failed to parse {statute_file}", err=True)
        for error in analysis.parse_errors:
            click.echo(str(error), err=True)
        sys.exit(1)
    if analysis.semantic_summary and analysis.semantic_summary.has_errors:
        click.echo(f"error: semantic errors in {statute_file}", err=True)
        for issue in analysis.semantic_summary.issues:
            if issue.severity == "error":
                click.echo(issue.message, err=True)
        sys.exit(1)
    if not analysis.ast.statutes:
        click.echo(f"error: no statute in {statute_file}", err=True)
        sys.exit(1)

    facts = _load_facts(Path(facts_file))
    statute = analysis.ast.statutes[0]
    statutes = {st.section_number: st for st in analysis.ast.statutes}
    trace = DatalogExplainer().explain(statute, facts, statutes)
    click.echo(EnglishTranspiler().render_irac(statute, trace))
