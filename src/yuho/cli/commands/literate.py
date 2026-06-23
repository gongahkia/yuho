"""Generate literate statute mapping reports."""

from __future__ import annotations

from html import escape
import re
import sys
from pathlib import Path
from typing import Optional

import click

from yuho.cli.commands.explain import _load_facts
from yuho.explain import DatalogExplainer
from yuho.services.analysis import analyze_file
from yuho.transpile.english_transpiler import EnglishTranspiler


def run_literate(
    *,
    statute_file: str,
    legal_text_file: str,
    facts_file: Optional[str] = None,
    output: Optional[str] = None,
    report_format: str = "markdown",
) -> None:
    statute_path = Path(statute_file)
    legal_text_path = Path(legal_text_file)
    source = statute_path.read_text(encoding="utf-8")
    legal_text = legal_text_path.read_text(encoding="utf-8")

    analysis = analyze_file(statute_path, run_semantic=True)
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

    trace_text = None
    if facts_file:
        facts = _load_facts(Path(facts_file))
        statute = analysis.ast.statutes[0]
        statutes = {st.section_number: st for st in analysis.ast.statutes}
        trace = DatalogExplainer().explain(statute, facts, statutes)
        trace_text = EnglishTranspiler().render_explain_trace(trace)

    anchors = _source_anchors(source)
    if report_format == "html":
        report = _render_html(legal_text, source, anchors, trace_text)
    else:
        report = _render_markdown(legal_text, source, anchors, trace_text)

    if output:
        Path(output).write_text(report, encoding="utf-8")
        click.echo(f"Wrote literate report: {output}")
        return
    click.echo(report)


def _source_anchors(source: str) -> list[str]:
    return re.findall(r"source:\s*([^\s]+)", source)


def _render_markdown(
    legal_text: str,
    source: str,
    anchors: list[str],
    trace_text: Optional[str],
) -> str:
    parts = [
        "# Yuho Literate Report",
        "",
        "## Legal Text",
        legal_text.rstrip(),
        "",
        "## Yuho Source",
        "```yuho",
        source.rstrip(),
        "```",
        "",
        "## Source Anchors",
    ]
    if anchors:
        parts.extend(f"- `{anchor}`" for anchor in anchors)
    else:
        parts.append("- none")
    if trace_text is not None:
        parts.extend(["", "## Result Trace", "```text", trace_text.rstrip(), "```"])
    return "\n".join(parts) + "\n"


def _render_html(
    legal_text: str,
    source: str,
    anchors: list[str],
    trace_text: Optional[str],
) -> str:
    anchor_items = "\n".join(f"<li><code>{escape(anchor)}</code></li>" for anchor in anchors)
    if not anchor_items:
        anchor_items = "<li>none</li>"
    trace = ""
    if trace_text is not None:
        trace = f"<h2>Result Trace</h2>\n<pre>{escape(trace_text.rstrip())}</pre>"
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Yuho Literate Report</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
pre {{ white-space: pre-wrap; border: 1px solid #ddd; padding: 1rem; }}
code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
</style>
<h1>Yuho Literate Report</h1>
<div class="grid">
<section><h2>Legal Text</h2><pre>{escape(legal_text.rstrip())}</pre></section>
<section><h2>Yuho Source</h2><pre>{escape(source.rstrip())}</pre></section>
</div>
<h2>Source Anchors</h2>
<ul>
{anchor_items}
</ul>
{trace}
</html>
"""
