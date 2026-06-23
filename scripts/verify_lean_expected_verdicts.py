"""Compare Lean expected verdict fixtures with the Python runtime evaluator."""

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

from scripts.verify_structural_diff import fixtures as python_fixtures
from yuho.ast import nodes
from yuho.eval.interpreter import StructInstance, Value
from yuho.eval.statute_evaluator import StatuteEvaluator


@dataclass(frozen=True)
class VerdictMismatch:
    name: str
    statute: str
    expected: bool
    actual: bool


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


def _verdict_statutes() -> dict[str, nodes.StatuteNode]:
    statutes = python_fixtures()
    out: dict[str, nodes.StatuteNode] = {}
    for name, statute in statutes.items():
        exceptions = tuple(
            replace(exc, guard=nodes.IdentifierNode(f"exc_{exc.label}"))
            if exc.label else exc
            for exc in statute.exceptions
        )
        out[name] = replace(statute, exceptions=exceptions)
    return out


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
        actual = evaluator.evaluate(statutes[statute_name], _facts_struct(facts)).overall_satisfied
        if actual != expected:
            mismatches.append(
                VerdictMismatch(
                    name=name,
                    statute=statute_name,
                    expected=expected,
                    actual=actual,
                )
            )
    return mismatches


def main() -> int:
    print("lean expected verdicts: exporting smoke rows...")
    try:
        rows = _run_lean_verdict_export()
    except subprocess.CalledProcessError as exc:
        print("Lean verdict exporter failed:", exc.stderr or exc.stdout, file=sys.stderr)
        return 2
    mismatches = compare_verdicts(rows)
    print(
        "lean expected verdicts: "
        f"CHECKED={len(rows)} MISMATCH={len(mismatches)}"
    )
    if mismatches:
        for mismatch in mismatches:
            print(
                f"  {mismatch.name} ({mismatch.statute}): "
                f"lean={mismatch.expected} runtime={mismatch.actual}",
                file=sys.stderr,
            )
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
