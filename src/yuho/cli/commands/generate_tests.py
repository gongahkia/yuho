"""
Generate test cases for statutes using Z3 model enumeration.

Uses Z3 constraint solving to produce concrete fact patterns
that exercise different code paths through statute elements.
"""

import json as json_mod
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, TypedDict

import click

from yuho.ast.nodes import ElementGroupNode, ElementNode, ExceptionNode, StatuteNode
from yuho.services.analysis import analyze_file


class GeneratedCase(TypedDict, total=False):
    """Machine-readable study case emitted by `yuho generate-tests`."""

    case_id: str
    section: str
    title: str
    kind: str
    focus: str
    expected: str
    explanation: str
    doctrinal_note: str
    facts: Dict[str, object]


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

    solver_interpretations: List[Dict[str, object]] = []
    if ast.statutes:
        solver_interpretations = list(
            solver.enumerate_statute_interpretations(ast, max_interpretations=max_cases)
        )

    all_cases: List[GeneratedCase] = []
    for statute in ast.statutes:
        study_cases = _build_study_cases(statute, max_cases=max_cases)
        if solver_interpretations:
            study_cases.extend(
                _wrap_solver_cases(
                    statute,
                    solver_interpretations[: max(0, max_cases - len(study_cases))],
                )
            )

        all_cases.extend(_limit_cases(study_cases, max_cases=max_cases))

    if json_output:
        text = json_mod.dumps(all_cases, indent=2)
    else:
        lines: List[str] = []
        for case in all_cases:
            lines.append(f"--- {case['case_id']} (Section {case['section']}: {case['title']}) ---")
            if "kind" in case:
                lines.append(f"  kind: {case['kind']}")
            if "focus" in case:
                lines.append(f"  focus: {case['focus']}")
            facts = case.get("facts", {})
            for k, v in facts.items():
                lines.append(f"  {k} = {v}")
            if "expected" in case:
                lines.append(f"  expected: {case['expected']}")
            if "explanation" in case:
                lines.append(f"  explanation: {case['explanation']}")
            if "doctrinal_note" in case:
                lines.append(f"  doctrinal_note: {case['doctrinal_note']}")
            lines.append("")
        text = "\n".join(lines)

    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Generated {len(all_cases)} test case(s) → {output}")
    else:
        click.echo(text)
        click.echo(f"\n{len(all_cases)} test case(s) generated.")


def _build_study_cases(statute: StatuteNode, *, max_cases: int) -> List[GeneratedCase]:
    """Create pedagogical happy-path, boundary, and exception-flip cases."""
    section = statute.section_number
    title = statute.title.value if statute.title else "Untitled"
    flat_elements = _flatten_elements(statute.elements)
    base_facts: Dict[str, object] = {elem.name: True for elem in flat_elements}

    priority_cases: List[GeneratedCase] = [
        {
            "case_id": f"s{section}_conviction_path",
            "section": section,
            "title": title,
            "kind": "happy_path",
            "focus": "all required elements",
            "facts": dict(base_facts),
            "expected": "conviction_path_open",
            "explanation": "Every listed element is satisfied and no exception has been activated.",
        }
    ]

    boundary_cases: List[GeneratedCase] = []
    exception_cases: List[GeneratedCase] = []
    near_miss_cases: List[GeneratedCase] = []

    for elem in flat_elements:
        facts = dict(base_facts)
        facts[elem.name] = False
        near_miss_cases.append(
            {
                "case_id": f"s{section}_missing_{_slug(elem.name)}",
                "section": section,
                "title": title,
                "kind": "near_miss",
                "focus": elem.name,
                "facts": facts,
                "expected": "element_missing",
                "explanation": f"Near-miss: liability fails because `{elem.name}` is not proved.",
                "doctrinal_note": _element_note(elem),
            }
        )

    for group in _collect_groups(statute.elements):
        if group.combinator == "any_of":
            member_elements = _flatten_elements(group.members)
            if len(member_elements) > 1:
                chosen = member_elements[0]
                facts = dict(base_facts)
                for member in member_elements:
                    facts[member.name] = member is chosen
                boundary_cases.append(
                    {
                        "case_id": f"s{section}_minimal_any_of_{_slug(chosen.name)}",
                        "section": section,
                        "title": title,
                        "kind": "boundary_case",
                        "focus": "any_of",
                        "facts": facts,
                        "expected": "minimal_group_satisfied",
                        "explanation": (
                            f"Boundary case: only `{chosen.name}` is proved inside an `any_of` limb, "
                            "and that single limb is enough."
                        ),
                    }
                )
        elif group.combinator == "all_of":
            member_elements = _flatten_elements(group.members)
            if member_elements:
                missing = member_elements[0]
                facts = dict(base_facts)
                facts[missing.name] = False
                boundary_cases.append(
                    {
                        "case_id": f"s{section}_all_of_gap_{_slug(missing.name)}",
                        "section": section,
                        "title": title,
                        "kind": "boundary_case",
                        "focus": "all_of",
                        "facts": facts,
                        "expected": "group_unsatisfied",
                        "explanation": (
                            f"Boundary case: an `all_of` limb fails once `{missing.name}` drops out, "
                            "even though the surrounding facts remain strong."
                        ),
                    }
                )

    for exc in statute.exceptions:
        facts = dict(base_facts)
        facts[_exception_fact_key(exc)] = True
        label = exc.label or "exception"
        exception_cases.append(
            {
                "case_id": f"s{section}_exception_{_slug(label)}",
                "section": section,
                "title": title,
                "kind": "exception_flip",
                "focus": label,
                "facts": facts,
                "expected": "exception_applies",
                "explanation": (
                    f"All offence elements are present, but the `{label}` exception defeats the ordinary "
                    "conviction path."
                ),
                "doctrinal_note": exc.effect.value if exc.effect else exc.condition.value,
            }
        )

    return _limit_cases(
        [*priority_cases, *boundary_cases, *exception_cases, *near_miss_cases],
        max_cases=max_cases,
    )


def _wrap_solver_cases(
    statute: StatuteNode, interpretations: Sequence[Dict[str, object]]
) -> List[GeneratedCase]:
    """Wrap raw Z3 interpretations in the study-case schema."""
    section = statute.section_number
    title = statute.title.value if statute.title else "Untitled"
    cases: List[GeneratedCase] = []
    for index, interpretation in enumerate(interpretations, start=1):
        cases.append(
            {
                "case_id": f"s{section}_solver_{index}",
                "section": section,
                "title": title,
                "kind": "solver_model",
                "focus": "z3 interpretation",
                "facts": dict(interpretation),
                "expected": "solver_generated",
                "explanation": "Concrete interpretation enumerated by Z3 for the current module.",
            }
        )
    return cases


def _limit_cases(cases: Sequence[GeneratedCase], *, max_cases: int) -> List[GeneratedCase]:
    """Trim duplicate study cases while preserving pedagogical priority."""
    seen_ids = set()
    limited: List[GeneratedCase] = []
    for case in cases:
        case_id = case["case_id"]
        if case_id in seen_ids:
            continue
        limited.append(case)
        seen_ids.add(case_id)
        if len(limited) >= max_cases:
            break
    return limited


def _collect_groups(elements: Sequence[ElementNode | ElementGroupNode]) -> List[ElementGroupNode]:
    """Collect nested element groups for boundary-case generation."""
    groups: List[ElementGroupNode] = []
    for elem in elements:
        if isinstance(elem, ElementGroupNode):
            groups.append(elem)
            groups.extend(_collect_groups(elem.members))
    return groups


def _flatten_elements(elements: Iterable[ElementNode | ElementGroupNode]) -> List[ElementNode]:
    """Flatten nested element groups into a list of leaf elements."""
    flat: List[ElementNode] = []
    for elem in elements:
        if isinstance(elem, ElementNode):
            flat.append(elem)
        else:
            flat.extend(_flatten_elements(elem.members))
    return flat


def _element_note(element: ElementNode) -> str:
    """Explain the doctrinal role of an element in student-facing terms."""
    note = element.element_type.replace("_", " ")
    if element.burden and element.burden_standard:
        return f"{note}; burden on {element.burden} at {element.burden_standard.replace('_', ' ')}."
    if element.burden:
        return f"{note}; burden on {element.burden}."
    return note


def _exception_fact_key(exception: ExceptionNode) -> str:
    """Name the boolean fact used to activate an exception-flip case."""
    return f"exception_{_slug(exception.label or 'applies')}"


def _slug(value: str) -> str:
    """Convert labels to stable ASCII identifiers."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "case"
