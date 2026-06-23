"""Generate literate statute mapping reports."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import re
import sys
from pathlib import Path
from typing import Optional

import click

from yuho.ast import nodes
from yuho.cli.commands.explain import _load_facts, _module_with_imported_definitions
from yuho.explain import DatalogExplainer
from yuho.services.analysis import analyze_file
from yuho.transpile.english_transpiler import EnglishTranspiler


@dataclass(frozen=True)
class ParagraphAlignment:
    element_name: str
    paragraph_index: int
    text: str
    confidence: float
    matched_terms: tuple[str, ...]


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
        ast = _module_with_imported_definitions(analysis.ast, statute_path)
        statute = ast.statutes[0]
        statutes = {st.section_number: st for st in ast.statutes}
        trace = DatalogExplainer().explain(statute, facts, statutes)
        trace_text = EnglishTranspiler().render_explain_trace(trace)

    anchors = _source_anchors(source)
    element_spans = _element_spans(analysis.ast, source)
    paragraph_alignments = [] if anchors else _paragraph_alignments(legal_text, analysis.ast)
    if report_format == "html":
        report = _render_html(
            legal_text,
            source,
            anchors,
            element_spans,
            paragraph_alignments,
            trace_text,
        )
    else:
        report = _render_markdown(
            legal_text,
            source,
            anchors,
            element_spans,
            paragraph_alignments,
            trace_text,
        )

    if output:
        Path(output).write_text(report, encoding="utf-8")
        click.echo(f"Wrote literate report: {output}")
        return
    click.echo(report)


def _source_anchors(source: str) -> list[str]:
    return re.findall(r"source:\s*([^\s]+)", source)


def _element_spans(
    ast: nodes.ModuleNode,
    source: str,
) -> list[tuple[str, int, int, str]]:
    lines = source.splitlines()
    spans: list[tuple[str, int, int, str]] = []

    def walk(member: nodes.ASTNode) -> None:
        if isinstance(member, nodes.ElementNode):
            loc = member.source_location
            if loc is None:
                return
            start = max(loc.line, 1)
            end = max(loc.end_line, start)
            snippet = "\n".join(lines[start - 1 : end]).strip()
            spans.append((member.name, start, end, snippet))
            return
        if isinstance(member, nodes.ElementGroupNode):
            for child in member.members:
                walk(child)

    for statute in ast.statutes:
        for member in statute.elements:
            walk(member)
    return spans


def _paragraph_alignments(
    legal_text: str,
    ast: nodes.ModuleNode,
) -> list[ParagraphAlignment]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", legal_text) if p.strip()]
    if not paragraphs:
        return []
    result: list[ParagraphAlignment] = []
    for name, description in _element_descriptions(ast):
        element_tokens = _tokens(f"{name} {description}")
        if not element_tokens:
            continue
        best_index = 1
        best_terms: set[str] = set()
        for index, paragraph in enumerate(paragraphs, start=1):
            matched = element_tokens & _tokens(paragraph)
            if len(matched) > len(best_terms):
                best_index = index
                best_terms = matched
        confidence = len(best_terms) / len(element_tokens)
        result.append(
            ParagraphAlignment(
                element_name=name,
                paragraph_index=best_index,
                text=paragraphs[best_index - 1],
                confidence=confidence,
                matched_terms=tuple(sorted(best_terms)),
            )
        )
    return result


def _element_descriptions(ast: nodes.ModuleNode) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []

    def walk(member: nodes.ASTNode) -> None:
        if isinstance(member, nodes.ElementNode):
            description = (
                member.description.value
                if isinstance(member.description, nodes.StringLit)
                else type(member.description).__name__
            )
            result.append((member.name, description))
            return
        if isinstance(member, nodes.ElementGroupNode):
            for child in member.members:
                walk(child)

    for statute in ast.statutes:
        for member in statute.elements:
            walk(member)
    return result


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 3
    }


def _render_markdown(
    legal_text: str,
    source: str,
    anchors: list[str],
    element_spans: list[tuple[str, int, int, str]],
    paragraph_alignments: list[ParagraphAlignment],
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
    parts.extend(["", "## Executable Element Spans"])
    if element_spans:
        for name, start, end, snippet in element_spans:
            parts.extend(
                [
                    f"- `{name}`: lines {start}-{end}",
                    "  ```yuho",
                    f"  {snippet}",
                    "  ```",
                ]
            )
    else:
        parts.append("- none")
    parts.extend(["", "## Paragraph Alignment"])
    if paragraph_alignments:
        for alignment in paragraph_alignments:
            parts.extend(
                [
                    (
                        f"- `{alignment.element_name}`: paragraph "
                        f"{alignment.paragraph_index} "
                        f"(confidence {alignment.confidence:.2f})"
                    ),
                    f"  matched terms: {', '.join(alignment.matched_terms) or 'none'}",
                    f"  {alignment.text}",
                ]
            )
    else:
        parts.append("- none")
    if trace_text is not None:
        parts.extend(["", "## Result Trace", "```text", trace_text.rstrip(), "```"])
    return "\n".join(parts) + "\n"


def _render_html(
    legal_text: str,
    source: str,
    anchors: list[str],
    element_spans: list[tuple[str, int, int, str]],
    paragraph_alignments: list[ParagraphAlignment],
    trace_text: Optional[str],
) -> str:
    anchor_items = "\n".join(f"<li><code>{escape(anchor)}</code></li>" for anchor in anchors)
    if not anchor_items:
        anchor_items = "<li>none</li>"
    span_rows = "\n".join(
        "<tr>"
        f"<td><code>{escape(name)}</code></td>"
        f"<td>{start}-{end}</td>"
        f"<td><pre>{escape(snippet)}</pre></td>"
        "</tr>"
        for name, start, end, snippet in element_spans
    )
    if not span_rows:
        span_rows = '<tr><td colspan="3">none</td></tr>'
    alignment_rows = "\n".join(
        "<tr>"
        f"<td><code>{escape(alignment.element_name)}</code></td>"
        f"<td>{alignment.paragraph_index}</td>"
        f"<td>{alignment.confidence:.2f}</td>"
        f"<td>{escape(', '.join(alignment.matched_terms))}</td>"
        f"<td>{escape(alignment.text)}</td>"
        "</tr>"
        for alignment in paragraph_alignments
    )
    if not alignment_rows:
        alignment_rows = '<tr><td colspan="5">none</td></tr>'
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
<h2>Executable Element Spans</h2>
<table>
<thead><tr><th>Element</th><th>Lines</th><th>Source</th></tr></thead>
<tbody>
{span_rows}
</tbody>
</table>
<h2>Paragraph Alignment</h2>
<table>
<thead><tr><th>Element</th><th>Paragraph</th><th>Confidence</th><th>Matched Terms</th><th>Legal Text</th></tr></thead>
<tbody>
{alignment_rows}
</tbody>
</table>
{trace}
</html>
"""
