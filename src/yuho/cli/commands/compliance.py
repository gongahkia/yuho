"""
Compliance matrix generator.

Produces a markdown checklist from statute elements, useful for
compliance officers auditing whether each statutory requirement is met.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List

import click

from yuho.ast import nodes
from yuho.cli.error_formatter import Colors, colorize


def run_compliance_matrix(
    file: str,
    output: Optional[str] = None,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """Generate a compliance checklist from statute elements."""
    from yuho.services.analysis import analyze_file

    result = analyze_file(Path(file), run_semantic=False)
    if not result.ast:
        click.echo(colorize("error: failed to parse file", Colors.RED), err=True)
        sys.exit(1)

    matrix = []
    for statute in result.ast.statutes:
        title = statute.title.value if statute.title else "Untitled"
        entry = {
            "section": statute.section_number,
            "title": title,
            "jurisdiction": statute.jurisdiction or "unspecified",
            "requirements": [],
        }
        for elem in statute.elements:
            if isinstance(elem, nodes.ElementGroupNode):
                _flatten_group(elem, entry["requirements"])
            elif isinstance(elem, nodes.ElementNode):
                entry["requirements"].append({
                    "type": elem.element_type,
                    "name": elem.name,
                    "description": elem.description.value if isinstance(elem.description, nodes.StringLit) else str(elem.description),
                    "compliant": None, # to be filled by user
                })
        if statute.exceptions:
            for exc in statute.exceptions:
                entry["requirements"].append({
                    "type": "exception",
                    "name": exc.label or "exception",
                    "description": exc.condition.value if isinstance(exc.condition, nodes.StringLit) else "exception condition",
                    "compliant": None,
                })
        matrix.append(entry)

    if json_output:
        print(json.dumps(matrix, indent=2))
        return

    lines = _render_markdown(matrix)
    text = "\n".join(lines) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Compliance matrix written to {output}")
    else:
        print(text)


def _flatten_group(group: nodes.ElementGroupNode, reqs: list) -> None:
    """Recursively flatten element groups into requirements list."""
    for member in group.members:
        if isinstance(member, nodes.ElementGroupNode):
            _flatten_group(member, reqs)
        elif isinstance(member, nodes.ElementNode):
            reqs.append({
                "type": member.element_type,
                "name": member.name,
                "description": member.description.value if isinstance(member.description, nodes.StringLit) else str(member.description),
                "compliant": None,
            })


def _render_markdown(matrix: list) -> List[str]:
    """Render compliance matrix as markdown checklist."""
    lines = ["# Compliance Matrix", ""]
    for entry in matrix:
        lines.append(f"## Section {entry['section']}: {entry['title']}")
        lines.append(f"Jurisdiction: {entry['jurisdiction']}")
        lines.append("")
        lines.append("| # | Type | Requirement | Status |")
        lines.append("|---|------|-------------|--------|")
        for i, req in enumerate(entry["requirements"], 1):
            status = "[ ]" # unchecked
            lines.append(f"| {i} | {req['type']} | {req['description'][:80]} | {status} |")
        lines.append("")
    return lines
