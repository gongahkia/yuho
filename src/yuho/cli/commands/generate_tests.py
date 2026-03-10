"""
Generate test cases for statutes using Z3 model enumeration.

Uses Z3 constraint solving to produce concrete fact patterns
that exercise different code paths through statute elements.
"""

import json as json_mod
from pathlib import Path
from typing import Optional

import click

from yuho.services.analysis import analyze_file


def run_generate_tests(
    file: str,
    *,
    output: Optional[str] = None,
    max_cases: int = 10,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """Generate test cases from a statute file using Z3."""
    result = analyze_file(file)
    if not result.is_valid or result.ast is None:
        for err in result.errors:
            click.echo(f"  {err}", err=True)
        raise SystemExit(1)

    try:
        from yuho.verify.z3_solver import Z3Solver, Z3Generator, Z3_AVAILABLE
    except ImportError:
        Z3_AVAILABLE = False

    if not Z3_AVAILABLE:
        click.echo("error: z3-solver not installed. Install with: pip install z3-solver", err=True)
        raise SystemExit(1)

    ast = result.ast
    generator = Z3Generator()
    solver = Z3Solver()

    all_cases = []
    for statute in ast.statutes:
        section = statute.section_number
        title = statute.title.value if statute.title else "Untitled"

        interpretations = solver.enumerate_statute_interpretations(ast, max_interpretations=max_cases)
        for i, interp in enumerate(interpretations):
            case = {
                "case_id": f"s{section}_case_{i+1}",
                "section": section,
                "title": title,
                "facts": interp,
            }
            all_cases.append(case)

        if not interpretations:
            # fallback: generate from element names
            pos_facts = {}
            neg_facts = {}
            for elem in statute.elements:
                from yuho.ast.nodes import ElementNode, ElementGroupNode
                if isinstance(elem, ElementNode):
                    pos_facts[elem.name] = True
                    neg_facts[elem.name] = False
                elif isinstance(elem, ElementGroupNode):
                    for member in elem.members:
                        if isinstance(member, ElementNode):
                            pos_facts[member.name] = True
                            neg_facts[member.name] = False

            all_cases.append({
                "case_id": f"s{section}_positive",
                "section": section,
                "title": title,
                "facts": pos_facts,
                "expected": "all_elements_satisfied",
            })
            all_cases.append({
                "case_id": f"s{section}_negative",
                "section": section,
                "title": title,
                "facts": neg_facts,
                "expected": "no_elements_satisfied",
            })

    if json_output:
        text = json_mod.dumps(all_cases, indent=2)
    else:
        lines = []
        for case in all_cases:
            lines.append(f"--- {case['case_id']} (Section {case['section']}: {case['title']}) ---")
            facts = case.get("facts", {})
            for k, v in facts.items():
                lines.append(f"  {k} = {v}")
            if "expected" in case:
                lines.append(f"  expected: {case['expected']}")
            lines.append("")
        text = "\n".join(lines)

    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Generated {len(all_cases)} test case(s) → {output}")
    else:
        click.echo(text)
        click.echo(f"\n{len(all_cases)} test case(s) generated.")
