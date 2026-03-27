"""
Boolean logic engine for statute analysis.

Provides:
- Boolean minimization (simplify complex logical expressions)
- Tautology detection (always-true formulas)
- Contradiction detection (always-false formulas)
- Circular reasoning detection (A depends on B depends on A)
- Formula equivalence checking
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


class FormulaType(Enum):
    VAR = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    TRUE = auto()
    FALSE = auto()
    IMPLIES = auto()


@dataclass(frozen=True)
class Formula:
    """Immutable boolean formula node."""

    kind: FormulaType
    name: str = ""  # for VAR
    children: Tuple["Formula", ...] = ()

    def __repr__(self) -> str:
        if self.kind == FormulaType.VAR:
            return self.name
        elif self.kind == FormulaType.TRUE:
            return "TRUE"
        elif self.kind == FormulaType.FALSE:
            return "FALSE"
        elif self.kind == FormulaType.NOT:
            return f"!{self.children[0]}"
        elif self.kind == FormulaType.AND:
            return f"({' && '.join(str(c) for c in self.children)})"
        elif self.kind == FormulaType.OR:
            return f"({' || '.join(str(c) for c in self.children)})"
        elif self.kind == FormulaType.IMPLIES:
            return f"({self.children[0]} => {self.children[1]})"
        return "?"


def var(name: str) -> Formula:
    return Formula(FormulaType.VAR, name=name)


def and_(*args: Formula) -> Formula:
    if not args:
        return Formula(FormulaType.TRUE)
    if len(args) == 1:
        return args[0]
    return Formula(FormulaType.AND, children=args)


def or_(*args: Formula) -> Formula:
    if not args:
        return Formula(FormulaType.FALSE)
    if len(args) == 1:
        return args[0]
    return Formula(FormulaType.OR, children=args)


def not_(f: Formula) -> Formula:
    return Formula(FormulaType.NOT, children=(f,))


def implies(a: Formula, b: Formula) -> Formula:
    return Formula(FormulaType.IMPLIES, children=(a, b))


TRUE = Formula(FormulaType.TRUE)
FALSE = Formula(FormulaType.FALSE)


def variables(f: Formula) -> Set[str]:
    """Extract all variable names from a formula."""
    if f.kind == FormulaType.VAR:
        return {f.name}
    result: Set[str] = set()
    for child in f.children:
        result.update(variables(child))
    return result


def evaluate(f: Formula, assignment: Dict[str, bool]) -> bool:
    """Evaluate a formula under a truth assignment."""
    if f.kind == FormulaType.TRUE:
        return True
    elif f.kind == FormulaType.FALSE:
        return False
    elif f.kind == FormulaType.VAR:
        return assignment.get(f.name, False)
    elif f.kind == FormulaType.NOT:
        return not evaluate(f.children[0], assignment)
    elif f.kind == FormulaType.AND:
        return all(evaluate(c, assignment) for c in f.children)
    elif f.kind == FormulaType.OR:
        return any(evaluate(c, assignment) for c in f.children)
    elif f.kind == FormulaType.IMPLIES:
        return (not evaluate(f.children[0], assignment)) or evaluate(f.children[1], assignment)
    return False


def _all_assignments(vars_list: List[str]):
    """Generate all possible truth assignments for given variables."""
    n = len(vars_list)
    for i in range(2**n):
        assignment = {}
        for j, v in enumerate(vars_list):
            assignment[v] = bool((i >> j) & 1)
        yield assignment


def is_tautology(f: Formula) -> bool:
    """Check if formula is always true (tautology)."""
    vars_list = sorted(variables(f))
    if not vars_list:
        return evaluate(f, {})
    for assignment in _all_assignments(vars_list):
        if not evaluate(f, assignment):
            return False
    return True


def is_contradiction(f: Formula) -> bool:
    """Check if formula is always false (contradiction)."""
    vars_list = sorted(variables(f))
    if not vars_list:
        return not evaluate(f, {})
    for assignment in _all_assignments(vars_list):
        if evaluate(f, assignment):
            return False
    return True


def is_satisfiable(f: Formula) -> Optional[Dict[str, bool]]:
    """Find satisfying assignment or return None."""
    vars_list = sorted(variables(f))
    if not vars_list:
        if evaluate(f, {}):
            return {}
        return None
    for assignment in _all_assignments(vars_list):
        if evaluate(f, assignment):
            return assignment
    return None


def simplify(f: Formula) -> Formula:
    """Simplify a boolean formula using algebraic rules."""
    if f.kind in (FormulaType.VAR, FormulaType.TRUE, FormulaType.FALSE):
        return f
    children = tuple(simplify(c) for c in f.children)
    f = Formula(f.kind, f.name, children)
    if f.kind == FormulaType.NOT:
        inner = f.children[0]
        if inner.kind == FormulaType.TRUE:  # !TRUE = FALSE
            return FALSE
        if inner.kind == FormulaType.FALSE:  # !FALSE = TRUE
            return TRUE
        if inner.kind == FormulaType.NOT:  # !!x = x
            return inner.children[0]
    elif f.kind == FormulaType.AND:
        flat: List[Formula] = []
        for c in f.children:
            if c.kind == FormulaType.FALSE:  # x && FALSE = FALSE
                return FALSE
            if c.kind == FormulaType.TRUE:  # x && TRUE = x
                continue
            if c.kind == FormulaType.AND:  # flatten nested AND
                flat.extend(c.children)
            else:
                flat.append(c)
        # remove duplicates preserving order
        seen: Set[Formula] = set()
        deduped: List[Formula] = []
        for c in flat:
            if c not in seen:
                seen.add(c)
                deduped.append(c)
        # check for x && !x = FALSE
        for c in deduped:
            neg = not_(c) if c.kind != FormulaType.NOT else c.children[0]
            if neg in seen:
                return FALSE
        if not deduped:
            return TRUE
        if len(deduped) == 1:
            return deduped[0]
        return Formula(FormulaType.AND, children=tuple(deduped))
    elif f.kind == FormulaType.OR:
        flat = []
        for c in f.children:
            if c.kind == FormulaType.TRUE:  # x || TRUE = TRUE
                return TRUE
            if c.kind == FormulaType.FALSE:  # x || FALSE = x
                continue
            if c.kind == FormulaType.OR:  # flatten nested OR
                flat.extend(c.children)
            else:
                flat.append(c)
        seen = set()
        deduped = []
        for c in flat:
            if c not in seen:
                seen.add(c)
                deduped.append(c)
        # check for x || !x = TRUE
        for c in deduped:
            neg = not_(c) if c.kind != FormulaType.NOT else c.children[0]
            if neg in seen:
                return TRUE
        if not deduped:
            return FALSE
        if len(deduped) == 1:
            return deduped[0]
        return Formula(FormulaType.OR, children=tuple(deduped))
    elif f.kind == FormulaType.IMPLIES:
        a, b = f.children
        if (
            a.kind == FormulaType.FALSE or b.kind == FormulaType.TRUE
        ):  # FALSE => x = TRUE, x => TRUE = TRUE
            return TRUE
        if a.kind == FormulaType.TRUE:  # TRUE => x = x
            return b
        if a == b:  # x => x = TRUE
            return TRUE
    return f


def detect_circular_dependencies(deps: Dict[str, Set[str]]) -> List[List[str]]:
    """
    Detect circular dependencies in a dependency graph.

    Args:
        deps: mapping from name -> set of names it depends on

    Returns:
        List of cycles found (each cycle is a list of names)
    """
    cycles: List[List[str]] = []
    visited: Set[str] = set()
    rec_stack: Set[str] = set()
    path: List[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        for dep in deps.get(node, set()):
            if dep not in visited:
                dfs(dep)
            elif dep in rec_stack:
                # found cycle: extract from dep to current
                idx = path.index(dep)
                cycle = path[idx:] + [dep]
                cycles.append(cycle)
        path.pop()
        rec_stack.discard(node)

    for node in deps:
        if node not in visited:
            dfs(node)
    return cycles


@dataclass
class LogicAnalysisResult:
    """Result of analyzing a set of formulas."""

    tautologies: List[Tuple[str, Formula]] = field(default_factory=list)
    contradictions: List[Tuple[str, Formula]] = field(default_factory=list)
    simplified: Dict[str, Formula] = field(default_factory=dict)
    circular_deps: List[List[str]] = field(default_factory=list)
    satisfiable: Dict[str, Optional[Dict[str, bool]]] = field(default_factory=dict)


def analyze_formulas(
    named_formulas: Dict[str, Formula], deps: Optional[Dict[str, Set[str]]] = None
) -> LogicAnalysisResult:
    """
    Comprehensive analysis of named boolean formulas.

    Args:
        named_formulas: mapping from name to formula
        deps: optional dependency graph for circular reasoning detection

    Returns:
        LogicAnalysisResult with tautologies, contradictions, simplifications, cycles
    """
    result = LogicAnalysisResult()
    for name, formula in named_formulas.items():
        simplified = simplify(formula)
        result.simplified[name] = simplified
        if is_tautology(formula):
            result.tautologies.append((name, formula))
        elif is_contradiction(formula):
            result.contradictions.append((name, formula))
        result.satisfiable[name] = is_satisfiable(formula)
    if deps:
        result.circular_deps = detect_circular_dependencies(deps)
    return result


def statute_to_formulas(statute) -> Dict[str, Formula]:
    """
    Convert a StatuteNode's elements into boolean formulas.

    Each element becomes a variable. Element groups become AND/OR formulas.
    The guilt formula is the conjunction of all top-level elements.
    """
    from yuho.ast import nodes

    def _elements_to_formula(elements) -> Formula:
        parts: List[Formula] = []
        for elem in elements:
            if isinstance(elem, nodes.ElementGroupNode):
                sub = _elements_to_formula(elem.members)
                if elem.combinator == "any_of":
                    sub = Formula(
                        FormulaType.OR,
                        children=sub.children if sub.kind == FormulaType.AND else (sub,),
                    )
                parts.append(sub)
            elif isinstance(elem, nodes.ElementNode):
                parts.append(var(elem.name))
        if not parts:
            return TRUE
        return and_(*parts)

    formulas: Dict[str, Formula] = {}
    guilt = _elements_to_formula(statute.elements)
    formulas["guilt"] = guilt
    # add exception formulas
    for exc in getattr(statute, "exceptions", ()):
        label = exc.label or "exception"
        formulas[f"exception_{label}"] = var(f"exc_{label}")
    # effective guilt = guilt && !exceptions
    if statute.exceptions:
        exc_vars = [not_(var(f"exc_{e.label or 'exception'}")) for e in statute.exceptions]
        formulas["effective_guilt"] = and_(guilt, *exc_vars)
    return formulas
