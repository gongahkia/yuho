"""
Static analysis linter for statute completeness.

Checks for common issues in statute definitions:
- missing penalties, actus_reus, mens_rea
- empty/None exception guards
- duplicate exception conditions
- subsumption element-superset invariant
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set, Tuple, Union

from yuho.ast.nodes import (
    ElementGroupNode,
    ElementNode,
    ExceptionNode,
    IntLit,
    FloatLit,
    ModuleNode,
    RefinementTypeNode,
    StatuteNode,
    StringLit,
    VariableDecl,
)


@dataclass
class LintWarning:
    statute_section: str
    message: str
    severity: str  # "warning" or "info"


def _flatten_elements(
    elements: Tuple[Union[ElementNode, ElementGroupNode], ...],
) -> List[ElementNode]:
    """Recursively flatten ElementGroupNodes into a flat list of ElementNode."""
    out: List[ElementNode] = []
    stack = list(elements)
    while stack:
        item = stack.pop()
        if isinstance(item, ElementNode):
            out.append(item)
        elif isinstance(item, ElementGroupNode):
            stack.extend(item.members)
    return out


def _element_names(statute: StatuteNode) -> Set[str]:
    """Return set of element names for a statute."""
    return {e.name for e in _flatten_elements(statute.elements)}


def _element_types(statute: StatuteNode) -> Set[str]:
    """Return set of element_type values for a statute."""
    return {e.element_type for e in _flatten_elements(statute.elements)}


def _has_strict_liability_marker(statute: StatuteNode) -> bool:
    """Check if a statute is marked strict_liability via doc_comment or element naming."""
    if statute.doc_comment and "strict_liability" in statute.doc_comment.lower():
        return True
    flat = _flatten_elements(statute.elements)
    for el in flat:
        if el.element_type == "strict_liability":
            return True
        if el.name and "strict_liability" in el.name.lower():
            return True
    return False


def _check_no_penalty(statute: StatuteNode) -> List[LintWarning]:
    """Warn if statute has elements but no penalty."""
    if statute.elements and statute.penalty is None:
        return [
            LintWarning(
                statute_section=statute.section_number,
                message="statute has elements but no penalty defined",
                severity="warning",
            )
        ]
    return []


def _check_missing_actus_reus(statute: StatuteNode) -> List[LintWarning]:
    """Warn if statute has no actus_reus element and is not strict_liability."""
    if _has_strict_liability_marker(statute):
        return []
    types = _element_types(statute)
    if statute.elements and "actus_reus" not in types:
        return [
            LintWarning(
                statute_section=statute.section_number,
                message="statute has no actus_reus element and is not marked strict_liability",
                severity="warning",
            )
        ]
    return []


def _check_missing_mens_rea(statute: StatuteNode) -> List[LintWarning]:
    """Warn if statute has no mens_rea element and is not strict_liability."""
    if _has_strict_liability_marker(statute):
        return []
    types = _element_types(statute)
    if statute.elements and "mens_rea" not in types:
        return [
            LintWarning(
                statute_section=statute.section_number,
                message="statute has no mens_rea element and is not marked strict_liability",
                severity="warning",
            )
        ]
    return []


def _check_exception_guards(statute: StatuteNode) -> List[LintWarning]:
    """Check that exception guards are not empty/None."""
    warnings: List[LintWarning] = []
    for exc in statute.exceptions:
        if exc.guard is None:
            warnings.append(
                LintWarning(
                    statute_section=statute.section_number,
                    message=f"exception '{exc.label or '<unlabeled>'}' has no guard expression",
                    severity="info",
                )
            )
        elif isinstance(exc.guard, StringLit) and not exc.guard.value.strip():
            warnings.append(
                LintWarning(
                    statute_section=statute.section_number,
                    message=f"exception '{exc.label or '<unlabeled>'}' has empty guard expression",
                    severity="warning",
                )
            )
    return warnings


def _check_duplicate_exceptions(statute: StatuteNode) -> List[LintWarning]:
    """Check that multiple exceptions don't have identical conditions (likely copy-paste)."""
    warnings: List[LintWarning] = []
    seen: dict[str, str] = {}  # condition_value -> label
    for exc in statute.exceptions:
        cond_val = exc.condition.value if isinstance(exc.condition, StringLit) else None
        if cond_val is None:
            continue
        if cond_val in seen:
            warnings.append(
                LintWarning(
                    statute_section=statute.section_number,
                    message=(
                        f"exception '{exc.label or '<unlabeled>'}' has identical condition "
                        f"to '{seen[cond_val]}' (possible copy-paste error)"
                    ),
                    severity="warning",
                )
            )
        else:
            seen[cond_val] = exc.label or "<unlabeled>"
    return warnings


def _check_subsumption(statutes: Tuple[StatuteNode, ...]) -> List[LintWarning]:
    """If statute A subsumes statute B (same module), verify A's elements superset B's."""
    warnings: List[LintWarning] = []
    by_section = {s.section_number: s for s in statutes}
    for statute in statutes:
        if not statute.subsumes:
            continue
        target = by_section.get(statute.subsumes)
        if target is None:
            continue  # target not in this module, can't check
        a_names = _element_names(statute)
        b_names = _element_names(target)
        if not a_names.issuperset(b_names):
            missing = b_names - a_names
            warnings.append(
                LintWarning(
                    statute_section=statute.section_number,
                    message=(
                        f"statute subsumes s{statute.subsumes} but is missing elements: "
                        f"{', '.join(sorted(missing))}"
                    ),
                    severity="warning",
                )
            )
    return warnings


def _check_deontic_conflict(statute: StatuteNode) -> List[LintWarning]:
    """Warn if obligation+prohibition share same name. Info if permission has no matching obligation/prohibition."""
    warnings: List[LintWarning] = []
    flat = _flatten_elements(statute.elements)
    by_type: dict[str, set[str]] = {}
    for e in flat:
        by_type.setdefault(e.element_type, set()).add(e.name)
    obligations = by_type.get("obligation", set())
    prohibitions = by_type.get("prohibition", set())
    permissions = by_type.get("permission", set())
    conflict = obligations & prohibitions
    for name in sorted(conflict):
        warnings.append(
            LintWarning(
                statute_section=statute.section_number,
                message=f"deontic conflict: '{name}' is both obligation and prohibition",
                severity="warning",
            )
        )
    orphans = permissions - obligations - prohibitions
    for name in sorted(orphans):
        warnings.append(
            LintWarning(
                statute_section=statute.section_number,
                message=f"orphan permission: '{name}' has no corresponding obligation or prohibition",
                severity="info",
            )
        )
    return warnings


def _check_defeats_target(statute: StatuteNode) -> List[LintWarning]:
    """Verify defeats label references an existing exception in the same statute."""
    warnings: List[LintWarning] = []
    labels = {exc.label for exc in statute.exceptions if exc.label}
    for exc in statute.exceptions:
        if exc.defeats and exc.defeats not in labels:
            warnings.append(
                LintWarning(
                    statute_section=statute.section_number,
                    message=f"exception '{exc.label or '<unlabeled>'}' defeats unknown label '{exc.defeats}'",
                    severity="warning",
                )
            )
    return warnings


def lint_statute(statute: StatuteNode) -> List[LintWarning]:
    """Run all single-statute lint checks."""
    warnings: List[LintWarning] = []
    warnings.extend(_check_no_penalty(statute))
    warnings.extend(_check_missing_actus_reus(statute))
    warnings.extend(_check_missing_mens_rea(statute))
    warnings.extend(_check_exception_guards(statute))
    warnings.extend(_check_duplicate_exceptions(statute))
    warnings.extend(_check_defeats_target(statute))
    warnings.extend(_check_deontic_conflict(statute))
    return warnings


def _check_refinement_bounds(module: ModuleNode) -> List[LintWarning]:
    """For VariableDecl with RefinementTypeNode + literal value, check value in range."""
    warnings: List[LintWarning] = []
    for var in module.variables:
        if not isinstance(var.type_annotation, RefinementTypeNode):
            continue
        rt = var.type_annotation
        lo = rt.lower_bound.value if isinstance(rt.lower_bound, (IntLit, FloatLit)) else None
        hi = rt.upper_bound.value if isinstance(rt.upper_bound, (IntLit, FloatLit)) else None
        if lo is None or hi is None:
            continue
        val: int | float | None = None
        if isinstance(var.value, IntLit):
            val = var.value.value
        elif isinstance(var.value, FloatLit):
            val = var.value.value
        if val is None:
            continue
        if not (lo <= val <= hi):
            warnings.append(
                LintWarning(
                    statute_section="<module>",
                    message=f"variable '{var.name}' value {val} outside refinement bounds [{lo}..{hi}]",
                    severity="warning",
                )
            )
    return warnings


def lint_module(module: ModuleNode) -> List[LintWarning]:
    """Run all lint checks across a module's statutes."""
    warnings: List[LintWarning] = []
    for statute in module.statutes:
        warnings.extend(lint_statute(statute))
    warnings.extend(_check_subsumption(module.statutes))
    warnings.extend(_check_refinement_bounds(module))
    return warnings
