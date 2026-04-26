"""``yuho explain`` — plain-language summary of an encoded section.

The english transpiler emits a complete machine-readable rendering
(every definition, every assertion, every fn body) — useful for
provenance, less useful when a reader just wants "what is this section
about?". ``yuho explain`` is the prose-first surface for that question.

Output structure (5 fixed sections):

    Section <N>: <title>
    ============================================
    Effective: <date(s)>

    What it covers
    --------------
    <metadata.toml summary, or fallback marginal note>

    Elements
    --------
    To prove this offence, the prosecution must show:
      - <element-type> <name>: <description>
      ...

    Penalty
    -------
    <prose penalty rendering, multi-block aware>

    Worked example
    --------------
    <first illustration verbatim>

    -- NOT LEGAL ADVICE --
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import click

from yuho.ast import nodes
from yuho.cli.error_formatter import Colors, colorize
from yuho.services.analysis import analyze_file


_DISCLAIMER = (
    "-- NOT LEGAL ADVICE — this is a structural summary of the encoded "
    "statute. Cross-reference Singapore Statutes Online for any "
    "decision that matters. --"
)


def _flatten_elements(elements) -> List[nodes.ElementNode]:
    out: List[nodes.ElementNode] = []
    stack = list(elements)
    while stack:
        item = stack.pop(0)
        if isinstance(item, nodes.ElementNode):
            out.append(item)
        elif isinstance(item, nodes.ElementGroupNode):
            stack[:0] = list(item.members)
    return out


def _penalty_prose(pen: nodes.PenaltyNode) -> str:
    parts: List[str] = []
    if pen.death_penalty:
        parts.append("death")
    if pen.imprisonment_max:
        if pen.imprisonment_min:
            parts.append(
                f"imprisonment of {pen.imprisonment_min} to {pen.imprisonment_max}"
            )
        else:
            parts.append(f"imprisonment of up to {pen.imprisonment_max}")
    if pen.fine_max:
        if pen.fine_min:
            parts.append(
                f"a fine of ${pen.fine_min.amount} to ${pen.fine_max.amount}"
            )
        else:
            parts.append(f"a fine of up to ${pen.fine_max.amount}")
    elif getattr(pen, "fine_unlimited", False):
        parts.append("a fine (no statutory cap specified)")
    if pen.caning_max:
        if pen.caning_min:
            parts.append(f"caning of {pen.caning_min}-{pen.caning_max} strokes")
        else:
            parts.append(f"caning of up to {pen.caning_max} strokes")
    elif getattr(pen, "caning_unspecified", False):
        parts.append("caning (no stroke count specified)")
    if not parts:
        if pen.supplementary:
            return pen.supplementary.value
        return "(penalty not encoded as structured fields)"
    combinator = getattr(pen, "combinator", None) or "cumulative"
    join = " and " if combinator == "cumulative" else " or "
    body = join.join(parts)
    if pen.supplementary:
        body = f"{body}. Note: {pen.supplementary.value}"
    return body


def _read_summary(yh_path: Path) -> Optional[str]:
    """Pull the prose summary from the section's metadata.toml if present."""
    meta = yh_path.parent / "metadata.toml"
    if not meta.exists():
        return None
    try:
        import tomllib
        data = tomllib.loads(meta.read_text(encoding="utf-8"))
        summary = (data.get("description") or {}).get("summary")
        return summary if summary else None
    except Exception:
        return None


def _explain_statute(stat: nodes.StatuteNode, *, summary: Optional[str], color: bool) -> str:
    """Render the 5-section prose explanation for one statute."""
    def _h(text: str) -> str:
        return colorize(text, Colors.BOLD + Colors.CYAN) if color else text

    def _muted(text: str) -> str:
        return colorize(text, Colors.RESET) if color else text

    title = stat.title.value if stat.title else "(untitled)"
    lines: List[str] = []

    # Header
    header = f"Section {stat.section_number}: {title}"
    lines.append(_h(header))
    lines.append("=" * len(header))
    if stat.effective_dates:
        lines.append(f"Effective: {', '.join(stat.effective_dates)}")
    elif stat.effective_date:
        lines.append(f"Effective: {stat.effective_date}")
    lines.append("")

    # What it covers
    lines.append(_h("What it covers"))
    lines.append("-" * 14)
    if summary:
        lines.append(summary)
    elif stat.doc_comment:
        lines.append(stat.doc_comment.strip())
    else:
        lines.append("(No prose summary recorded for this section.)")
    lines.append("")

    # Elements
    lines.append(_h("Elements"))
    lines.append("-" * 8)
    flat = _flatten_elements(stat.elements)
    if flat:
        lines.append("To prove this offence, the prosecution must show:")
        for el in flat:
            desc_node = getattr(el, "description", None)
            desc = desc_node.value if hasattr(desc_node, "value") else (desc_node or "")
            lines.append(f"  - {el.element_type} {el.name}: {desc}")
    else:
        lines.append("(This section defines a term or carves out an exception "
                     "rather than declaring an offence.)")
    lines.append("")

    # Penalty (multi-penalty G12 aware)
    all_penalties: List[nodes.PenaltyNode] = []
    if stat.penalty is not None:
        all_penalties.append(stat.penalty)
    all_penalties.extend(getattr(stat, "additional_penalties", ()) or ())
    lines.append(_h("Penalty"))
    lines.append("-" * 7)
    if not all_penalties:
        lines.append("No penalty defined in the encoded statute.")
    elif len(all_penalties) == 1:
        lines.append(_penalty_prose(all_penalties[0]))
    else:
        lines.append("This section carries multiple penalty clauses:")
        for i, pen in enumerate(all_penalties, 1):
            lines.append(f"  {i}. {_penalty_prose(pen)}")
    lines.append("")

    # Worked example
    if stat.illustrations:
        lines.append(_h("Worked example"))
        lines.append("-" * 14)
        first = stat.illustrations[0]
        desc_node = getattr(first, "description", None)
        text = desc_node.value if hasattr(desc_node, "value") else str(desc_node or "")
        lines.append(text.strip())
        if len(stat.illustrations) > 1:
            lines.append("")
            lines.append(_muted(
                f"({len(stat.illustrations) - 1} further illustration(s) "
                f"omitted; run `yuho transpile -t english` for the full set.)"
            ))
        lines.append("")

    lines.append(_muted(_DISCLAIMER))
    return "\n".join(lines)


def explain_module(
    module: nodes.ModuleNode,
    *,
    section: Optional[str] = None,
    summary: Optional[str] = None,
    color: bool = False,
) -> str:
    """Render a prose explanation for one or all statutes in a module.

    Pure function — separate from :func:`run_explain` so the MCP server
    can reuse the same renderer without duplicating the prose layout.
    """
    statutes = list(module.statutes)
    if section:
        section_norm = section.lstrip("sS").lstrip(".").strip()
        statutes = [s for s in statutes if s.section_number == section_norm]
    blocks: List[str] = []
    for stat in statutes:
        blocks.append(_explain_statute(stat, summary=summary, color=color))
    return "\n\n".join(blocks)


def run_explain(file: str, *, section: Optional[str] = None, color: bool = True) -> None:
    """Implementation of ``yuho explain``."""
    from yuho.parser.wrapper import validate_file_path

    try:
        path = validate_file_path(file)
    except (ValueError, FileNotFoundError) as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)

    result = analyze_file(path, run_semantic=False)
    if result.parse_errors:
        click.echo(colorize(f"error: parse errors in {file}", Colors.RED), err=True)
        for err in result.parse_errors[:3]:
            click.echo(f"  {err.message}", err=True)
        sys.exit(1)
    if result.ast is None or not result.ast.statutes:
        click.echo(colorize(f"error: no statute blocks in {file}", Colors.RED), err=True)
        sys.exit(1)

    summary = _read_summary(path)
    statutes = list(result.ast.statutes)
    if section:
        section = section.lstrip("sS").lstrip(".").strip()
        statutes = [s for s in statutes if s.section_number == section]
        if not statutes:
            click.echo(colorize(f"error: section s{section} not found in {file}", Colors.RED), err=True)
            sys.exit(1)

    blocks: List[str] = []
    for stat in statutes:
        blocks.append(_explain_statute(stat, summary=summary, color=color))
    click.echo("\n\n".join(blocks))
