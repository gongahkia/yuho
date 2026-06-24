"""Compare Lean expected verdict fixtures with runtime and Z3 verdicts."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.verify_structural_diff import (
    fixtures as smoke_python_fixtures,
    fixtures_from_corpus,
)
from yuho.ast import nodes
from yuho.eval.interpreter import StructInstance, Value
from yuho.eval.statute_evaluator import StatuteEvaluator
from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE


@dataclass(frozen=True)
class VerdictMismatch:
    name: str
    statute: str
    expected: bool
    runtime: bool
    z3: bool | None

    @property
    def actual(self) -> bool:
        return self.runtime


def _run_lean_verdict_export() -> list[dict[str, Any]]:
    subprocess.run(
        ["lake", "build", "scripts"],
        cwd=REPO / "mechanisation",
        capture_output=True,
        text=True,
        check=True,
    )
    proc = subprocess.run(
        ["lake", "env", "lean", "--run", "scripts/ExportSpec.lean", "--", "--verdicts"],
        cwd=REPO / "mechanisation",
        capture_output=True,
        text=True,
        check=True,
    )
    out_lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not out_lines:
        raise RuntimeError("Lean verdict exporter produced no output")
    payload = json.loads(out_lines[-1])
    if not isinstance(payload, list):
        raise RuntimeError("Lean verdict exporter did not return a JSON list")
    return payload


def _facts_struct(values: dict[str, Any]) -> StructInstance:
    return StructInstance(
        type_name="Facts",
        fields={key: Value(bool(value), "bool") for key, value in values.items()},
    )


def _walk_ast(node: Any):
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        children = current.children() if hasattr(current, "children") else []
        stack.extend(child for child in children if isinstance(child, nodes.ASTNode))


def _safe(name: str) -> str:
    return name.replace(" ", "_").replace("-", "_")


def _verdict_statutes() -> dict[str, nodes.StatuteNode]:
    out: dict[str, nodes.StatuteNode] = {}
    statutes = fixtures_from_corpus()
    statutes.update(smoke_python_fixtures())
    for name, statute in statutes.items():
        exceptions = tuple(
            replace(exc, guard=nodes.IdentifierNode(f"exc_{exc.label}"))
            if exc.label else exc
            for exc in statute.exceptions
        )
        out[name] = replace(statute, exceptions=exceptions)
    return out


def _module_for(statute: nodes.StatuteNode) -> nodes.ModuleNode:
    return nodes.ModuleNode(
        imports=(),
        type_defs=(),
        function_defs=(),
        statutes=(statute,),
        variables=(),
    )


def _add_fact_bindings(solver: Any, gen: Z3Generator, statute: nodes.StatuteNode, facts: dict[str, Any]) -> None:
    import z3

    statute_id = statute.section_number.replace(".", "_")
    element_names = {
        node.name for node in _walk_ast(statute) if isinstance(node, nodes.ElementNode)
    }
    identifier_names = {
        node.name for node in _walk_ast(statute) if isinstance(node, nodes.IdentifierNode)
    }
    for name in element_names:
        const = gen._consts.get(f"{statute_id}_leaf_{_safe(name)}")
        if const is not None:
            solver.add(const == z3.BoolVal(bool(facts.get(name, False))))
    for name in identifier_names | set(facts):
        const = gen._consts.get(f"{statute_id}_{_safe(name)}")
        if const is not None:
            solver.add(const == z3.BoolVal(bool(facts.get(name, False))))


def _z3_verdict(statute: nodes.StatuteNode, facts: dict[str, Any]) -> bool | None:
    if not Z3_AVAILABLE:
        return None
    import z3

    gen = Z3Generator()
    solver, _ = gen.generate(_module_for(statute))
    if solver is None:
        raise RuntimeError("Z3 generator returned no solver")
    _add_fact_bindings(solver, gen, statute, facts)
    if solver.check() != z3.sat:
        raise RuntimeError("Z3 model is unsatisfiable after fact bindings")
    statute_id = statute.section_number.replace(".", "_")
    conviction = gen._consts.get(f"{statute_id}_conviction")
    if conviction is None:
        raise RuntimeError(f"missing Z3 conviction atom for s{statute.section_number}")
    return z3.is_true(solver.model().eval(conviction, model_completion=True))


def compare_verdicts(rows: list[dict[str, Any]]) -> list[VerdictMismatch]:
    statutes = _verdict_statutes()
    evaluator = StatuteEvaluator()
    mismatches: list[VerdictMismatch] = []

    for row in rows:
        name = str(row["name"])
        statute_name = str(row["statute"])
        if statute_name not in statutes:
            raise RuntimeError(f"unknown Python fixture for Lean verdict row: {statute_name}")
        expected = row["expected"]
        if not isinstance(expected, bool):
            raise RuntimeError(f"verdict row {name} has non-boolean expected value")
        facts = row.get("factValues")
        if not isinstance(facts, dict):
            raise RuntimeError(f"verdict row {name} has no factValues object")
        statute = statutes[statute_name]
        runtime_actual = evaluator.evaluate(statute, _facts_struct(facts)).overall_satisfied
        z3_actual = _z3_verdict(statute, facts)
        if runtime_actual != expected or (
            z3_actual is not None and z3_actual != expected
        ):
            mismatches.append(
                VerdictMismatch(
                    name=name,
                    statute=statute_name,
                    expected=expected,
                    runtime=runtime_actual,
                    z3=z3_actual,
                )
            )
    return mismatches


def main() -> int:
    print("lean expected verdicts: exporting verdict rows...")
    try:
        rows = _run_lean_verdict_export()
    except subprocess.CalledProcessError as exc:
        print("Lean verdict exporter failed:", exc.stderr or exc.stdout, file=sys.stderr)
        return 2
    mismatches = compare_verdicts(rows)
    print(
        "lean expected verdicts: "
        f"CHECKED={len(rows)} TRIPLE={len(rows) if Z3_AVAILABLE else 'SKIP'} "
        f"MISMATCH={len(mismatches)}"
    )
    if mismatches:
        for mismatch in mismatches:
            print(
                f"  {mismatch.name} ({mismatch.statute}): "
                f"lean={mismatch.expected} runtime={mismatch.runtime} z3={mismatch.z3}",
                file=sys.stderr,
            )
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
