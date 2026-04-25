"""Counter-example explorer for encoded statutes.

Given an encoded section, surface the kinds of fact patterns the
verifier can construct over its element / exception structure:

* **satisfying** -- patterns where every element is satisfied and no
  exception fires (conviction is reachable);
* **borderline** -- patterns where everything but one element holds
  (shows the element is load-bearing);
* **exception coverage** -- patterns where the elements are satisfied
  *and* a named exception fires (proves the exception is reachable);
* **dead exceptions** -- exceptions whose firing is unreachable under
  any element-satisfying assignment (likely-overconstrained or unused).

The explorer is a thin layer on top of ``yuho.verify.z3_solver`` --
it reuses the Z3Generator's existing translation of statutes into
Bool variables and Or/And/Implies assertions, then asks new
questions of the resulting solver.

This module is *not* a legal adjudicator. The ``model_to_scenario``
output is a structural witness over the encoded grammar -- it tells
you *that* a fact pattern can satisfy/exempt the offence, not what
actually happens in court. See ``simulator/`` for the user-supplied-
facts dual.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple

try:
    import z3  # type: ignore
    _Z3_AVAILABLE = True
except Exception:
    _Z3_AVAILABLE = False


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass
class Scenario:
    """One satisfying assignment from the solver, projected onto element /
    exception variables we care about."""
    elements: Dict[str, bool] = field(default_factory=dict)
    exceptions_fired: List[str] = field(default_factory=list)
    conviction: Optional[bool] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExplorerReport:
    section: str
    title: str
    available: bool                                 # Z3 available + statute parsed
    reason: Optional[str] = None                    # populated when not available
    satisfying: List[Scenario] = field(default_factory=list)
    borderline: List[Scenario] = field(default_factory=list)
    exception_coverage: List[Dict[str, Any]] = field(default_factory=list)
    dead_exceptions: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["satisfying"]   = [s if isinstance(s, dict) else s.to_dict() for s in self.satisfying]
        d["borderline"]   = [s if isinstance(s, dict) else s.to_dict() for s in self.borderline]
        return d


# ---------------------------------------------------------------------------
# Explorer
# ---------------------------------------------------------------------------


class CounterexampleExplorer:
    """Build an ExplorerReport for a single statute section.

    The constructor accepts a parsed ``ModuleNode`` (from
    ``yuho.services.analysis.analyze_file``). All public methods are pure
    queries; no side effects on the AST.
    """

    def __init__(self, module, *, timeout_ms: int = 5000):
        self._module = module
        self._timeout_ms = timeout_ms

    # -- public API ---------------------------------------------------------

    def explore_section(
        self,
        section: str,
        *,
        max_satisfying: int = 5,
        include_borderline: bool = True,
        include_exception_coverage: bool = True,
    ) -> ExplorerReport:
        """Run all scenario queries against ``section`` and return a report."""
        statute = self._find_statute(section)
        if statute is None:
            return ExplorerReport(
                section=section, title="", available=False,
                reason=f"section {section!r} not found in module",
            )
        if not _Z3_AVAILABLE:
            return ExplorerReport(
                section=section,
                title=getattr(statute, "marginal_note", "") or "",
                available=False,
                reason="z3 is not installed; counter-example exploration is unavailable",
            )

        # Build generator state (constraints + named consts) once.
        from yuho.verify.z3_solver import Z3Generator  # local import keeps z3 lazy
        gen = Z3Generator()
        _solver, base_assertions = gen.generate(self._module)

        statute_id = section.replace(".", "_")
        report = ExplorerReport(
            section=section,
            title=getattr(statute, "marginal_note", "") or "",
            available=True,
        )

        # --- satisfying scenarios ----------------------------------------
        report.satisfying = self._enumerate_satisfying(
            gen, statute, statute_id, base_assertions, max_satisfying
        )

        # --- borderline scenarios ----------------------------------------
        if include_borderline:
            report.borderline = self._enumerate_borderline(
                gen, statute, statute_id, base_assertions
            )

        # --- exception coverage + dead exceptions -----------------------
        if include_exception_coverage:
            cov, dead = self._exception_coverage(
                gen, statute, statute_id, base_assertions
            )
            report.exception_coverage = cov
            report.dead_exceptions = dead

        # --- summary -----------------------------------------------------
        n_elems = self._count_leaf_elements(statute)
        n_exc = len(getattr(statute, "exceptions", ()) or ())
        report.summary = {
            "n_leaf_elements":       n_elems,
            "n_exceptions":          n_exc,
            "conviction_reachable":  bool(report.satisfying),
            "n_load_bearing":        sum(1 for s in report.borderline if s.elements),
            "n_dead_exceptions":     len(report.dead_exceptions),
        }
        return report

    # -- scenario builders --------------------------------------------------

    def _enumerate_satisfying(
        self, gen, statute, statute_id, base_assertions, max_models
    ) -> List[Scenario]:
        conviction_key = f"{statute_id}_conviction"
        conviction_var = gen._consts.get(conviction_key)
        if conviction_var is None:
            return []

        solver = z3.Solver()
        solver.set("timeout", self._timeout_ms)
        for a in base_assertions:
            solver.add(a)
        solver.add(conviction_var == True)

        elem_vars = self._element_vars(gen, statute_id)
        if not elem_vars:
            return []

        out: List[Scenario] = []
        for _ in range(max_models):
            if solver.check() != z3.sat:
                break
            model = solver.model()
            scen = self._scenario_from_model(model, elem_vars, statute, statute_id, gen)
            scen.description = "elements satisfied; no exception fires; conviction reachable"
            out.append(scen)
            # Block this assignment over the element vars only — we don't
            # care about other Bool variations producing duplicate scenarios.
            block = z3.Or(*[v != model[v] for _, v in elem_vars if model[v] is not None])
            solver.add(block)
        return out

    def _enumerate_borderline(
        self, gen, statute, statute_id, base_assertions
    ) -> List[Scenario]:
        elem_vars = self._element_vars(gen, statute_id)
        if not elem_vars:
            return []
        out: List[Scenario] = []
        for name, focus_var in elem_vars:
            solver = z3.Solver()
            solver.set("timeout", self._timeout_ms)
            for a in base_assertions:
                solver.add(a)
            # Every other element satisfied, this one not.
            for other_name, other_var in elem_vars:
                if other_name == name:
                    solver.add(other_var == False)
                else:
                    solver.add(other_var == True)
            if solver.check() != z3.sat:
                continue
            model = solver.model()
            scen = self._scenario_from_model(model, elem_vars, statute, statute_id, gen)
            scen.description = f"all elements except {name!r} satisfied — {name!r} is load-bearing"
            out.append(scen)
        return out

    def _exception_coverage(
        self, gen, statute, statute_id, base_assertions
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        elem_vars = self._element_vars(gen, statute_id)
        all_elems_true = z3.And(*[v for _, v in elem_vars]) if elem_vars else z3.BoolVal(True)
        coverage: List[Dict[str, Any]] = []
        dead: List[str] = []
        exceptions = getattr(statute, "exceptions", ()) or ()
        for i, exc in enumerate(exceptions):
            exc_label = exc.label or f"exception_{i}"
            safe = exc_label.replace(" ", "_").replace("-", "_")
            fires_key = f"{statute_id}_exc_{safe}_fires"
            sat_key = f"{statute_id}_exc_{safe}"
            fires_var = gen._consts.get(fires_key) or gen._consts.get(sat_key)
            if fires_var is None:
                # No constraint generated; nothing to check.
                continue
            solver = z3.Solver()
            solver.set("timeout", self._timeout_ms)
            for a in base_assertions:
                solver.add(a)
            solver.add(all_elems_true)
            solver.add(fires_var == True)
            res = solver.check()
            if res == z3.sat:
                model = solver.model()
                scen = self._scenario_from_model(model, elem_vars, statute, statute_id, gen)
                coverage.append({
                    "exception": exc_label,
                    "reachable": True,
                    "scenario": scen.to_dict(),
                })
            elif res == z3.unsat:
                coverage.append({"exception": exc_label, "reachable": False})
                dead.append(exc_label)
            else:
                coverage.append({"exception": exc_label, "reachable": None,
                                 "note": "solver timed out"})
        return coverage, dead

    # -- helpers -----------------------------------------------------------

    def _find_statute(self, section: str):
        for s in getattr(self._module, "statutes", []):
            if s.section_number == section:
                return s
        return None

    def _element_vars(self, gen, statute_id) -> List[Tuple[str, Any]]:
        """Return [(human_name, z3_bool)] for every leaf element in the statute."""
        prefix = f"{statute_id}_"
        suffix = "_satisfied"
        out: List[Tuple[str, Any]] = []
        for key, var in gen._consts.items():
            if key.startswith(prefix) and key.endswith(suffix):
                stem = key[len(prefix):-len(suffix)]
                out.append((stem, var))
        return out

    def _count_leaf_elements(self, statute) -> int:
        from yuho.ast import nodes as ast_nodes
        n = 0
        def _walk(node):
            nonlocal n
            if isinstance(node, ast_nodes.ElementNode):
                n += 1
            elif isinstance(node, ast_nodes.ElementGroupNode):
                for m in node.members:
                    _walk(m)
        for e in getattr(statute, "elements", ()) or ():
            _walk(e)
        for sub in getattr(statute, "subsections", ()) or ():
            for e in getattr(sub, "elements", ()) or ():
                _walk(e)
        return n

    def _scenario_from_model(
        self, model, elem_vars, statute, statute_id, gen
    ) -> Scenario:
        elements = {}
        for name, var in elem_vars:
            val = model[var]
            if val is None:
                continue
            elements[name] = bool(val)
        conviction_var = gen._consts.get(f"{statute_id}_conviction")
        conviction = bool(model[conviction_var]) if conviction_var is not None and model[conviction_var] is not None else None
        # Which exceptions fired in this model?
        fired = []
        prefix = f"{statute_id}_exc_"
        for key, var in gen._consts.items():
            if not key.startswith(prefix):
                continue
            if not key.endswith("_fires") and not key.startswith(prefix):
                continue
            v = model[var]
            if v is not None and bool(v):
                # Strip prefix/suffix to recover label.
                label = key[len(prefix):]
                if label.endswith("_fires"):
                    label = label[: -len("_fires")]
                # Skip the bare guard var if a `_fires` companion exists for the same label.
                fires_companion = f"{prefix}{label}_fires" in gen._consts
                if not key.endswith("_fires") and fires_companion:
                    continue
                if label not in fired:
                    fired.append(label)
        return Scenario(
            elements=elements,
            exceptions_fired=fired,
            conviction=conviction,
        )


# ---------------------------------------------------------------------------
# CLI / MCP convenience
# ---------------------------------------------------------------------------


def explore_file(file: str, section: str, **kwargs) -> Dict[str, Any]:
    """One-shot helper: parse ``file`` and explore ``section``. Returns a
    JSON-shaped dict suitable for the CLI / MCP tool."""
    from yuho.services.analysis import analyze_file
    analysis = analyze_file(file, run_semantic=False)
    if analysis.parse_errors or analysis.ast is None:
        return {
            "ok": False,
            "section": section,
            "error": "parse_errors",
            "details": [str(e) for e in (analysis.parse_errors or [])][:5],
        }
    explorer = CounterexampleExplorer(analysis.ast)
    report = explorer.explore_section(section, **kwargs)
    return {"ok": True, "report": report.to_dict()}


def render_report_text(report: ExplorerReport) -> str:
    """Pretty-print an ExplorerReport for terminal output."""
    lines: List[str] = []
    lines.append(f"s{report.section} — {report.title}")
    if not report.available:
        lines.append(f"  unavailable: {report.reason}")
        return "\n".join(lines)
    s = report.summary
    lines.append(f"  elements: {s['n_leaf_elements']}, exceptions: {s['n_exceptions']}, "
                 f"conviction reachable: {s['conviction_reachable']}, "
                 f"load-bearing: {s['n_load_bearing']}, dead exceptions: {s['n_dead_exceptions']}")
    if report.satisfying:
        lines.append(f"\n  Satisfying scenarios ({len(report.satisfying)}):")
        for i, scen in enumerate(report.satisfying, 1):
            tagged = ", ".join(f"{k}={'T' if v else 'F'}" for k, v in scen.elements.items())
            lines.append(f"    [{i}] {tagged}")
    if report.borderline:
        lines.append(f"\n  Borderline (load-bearing) elements:")
        for scen in report.borderline:
            f_keys = [k for k, v in scen.elements.items() if not v]
            if f_keys:
                lines.append(f"    fails-when-missing: {', '.join(f_keys)}")
    if report.exception_coverage:
        lines.append(f"\n  Exception coverage:")
        for entry in report.exception_coverage:
            mark = "REACHABLE" if entry.get("reachable") is True else (
                "DEAD" if entry.get("reachable") is False else "UNKNOWN"
            )
            lines.append(f"    {entry['exception']}: {mark}")
    return "\n".join(lines)
