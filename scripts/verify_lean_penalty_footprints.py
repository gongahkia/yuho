"""Compare Lean penalty footprint rows with Python Z3 footprint constraints."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yuho.ast import ASTBuilder
from yuho.parser import get_parser
from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE


PENALTY_SOURCES = {
    "imprisonment_admits": "imprisonment := 1 days .. 5 days;",
    "imprisonment_rejects_hi": "imprisonment := 1 days .. 5 days;",
    "fine_admits": "fine := $10.00 .. $20.00;",
    "fine_unlimited_admits": "fine := unlimited;",
    "fine_unlimited_finite_admits": "fine := unlimited;",
    "caning_admits": "caning := 3 .. 6 strokes;",
    "caning_unspecified_admits": "caning := unspecified;",
    "caning_unspecified_finite_admits": "caning := unspecified;",
    "death_admits": "death := TRUE;",
    "death_rejects": "death := TRUE;",
    "cumulative_admits": """
        imprisonment := 1 days .. 5 days;
        fine := $10.00 .. $20.00;
        caning := 3 .. 6 strokes;
        death := TRUE;
    """,
}


def _run_lean_export() -> list[dict[str, Any]]:
    subprocess.run(
        ["lake", "build", "scripts"],
        cwd=REPO / "mechanisation",
        capture_output=True,
        text=True,
        check=True,
    )
    proc = subprocess.run(
        [
            "lake", "env", "lean", "--run", "scripts/ExportSpec.lean",
            "--", "--penalty-footprints",
        ],
        cwd=REPO / "mechanisation",
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("Lean penalty footprint exporter produced no output")
    payload = json.loads(lines[-1])
    if not isinstance(payload, list):
        raise RuntimeError("Lean penalty footprint exporter did not return a JSON list")
    return payload


def _parse_penalty_source(body: str):
    source = f"""
    statute 1 "Penalty footprint" {{
        elements {{ actus_reus act := "act"; }}
        penalty {{
            {body}
        }}
    }}
    """
    parser = get_parser()
    result = parser.parse(source, "<lean-penalty-footprint>")
    if result.errors:
        raise RuntimeError("; ".join(str(error) for error in result.errors))
    return ASTBuilder(result.source, "<lean-penalty-footprint>").build(result.root_node)


def _add_footprint_equalities(solver: Any, gen: Z3Generator, footprint: dict[str, Any]) -> None:
    import z3

    int_fields = {
        "imp_lo": "1_imprisonment_lo",
        "imp_hi": "1_imprisonment_hi",
        "fine_lo": "1_fine_lo",
        "fine_hi": "1_fine_hi",
        "caning_lo": "1_caning_lo",
        "caning_hi": "1_caning_hi",
    }
    bool_fields = {
        "fine_unlimited": "1_fine_unlimited",
        "caning_unspecified": "1_caning_unspecified",
        "death": "1_death_penalty",
    }
    for field, const_name in int_fields.items():
        const = gen._consts.get(const_name)
        if const is not None:
            solver.add(const == z3.IntVal(int(footprint[field])))
    for field, const_name in bool_fields.items():
        const = gen._consts.get(const_name)
        if const is not None:
            solver.add(const == z3.BoolVal(bool(footprint[field])))


def compare_penalty_footprints(rows: list[dict[str, Any]]) -> tuple[int, list[str]]:
    import z3

    mismatches: list[str] = []
    checked = 0
    for row in rows:
        name = str(row["name"])
        if name not in PENALTY_SOURCES:
            raise RuntimeError(f"no Python source mapped for Lean penalty fixture {name}")
        expected = row["expected"]
        if not isinstance(expected, bool):
            raise RuntimeError(f"fixture {name} expected is not boolean")
        footprint = row.get("footprint")
        if not isinstance(footprint, dict):
            raise RuntimeError(f"fixture {name} footprint is not an object")
        ast = _parse_penalty_source(PENALTY_SOURCES[name])
        gen = Z3Generator()
        solver, _ = gen.generate(ast)
        if solver is None:
            raise RuntimeError(f"Z3 generator returned no solver for {name}")
        _add_footprint_equalities(solver, gen, footprint)
        sat = solver.check() == z3.sat
        if sat != expected:
            mismatches.append(f"{name}: lean={expected} z3_sat={sat}")
        checked += 1
    return checked, mismatches


def main() -> int:
    if not Z3_AVAILABLE:
        print("lean penalty footprints: SKIP (z3-solver not installed)")
        return 0
    print("lean penalty footprints: exporting rows...")
    try:
        rows = _run_lean_export()
    except subprocess.CalledProcessError as exc:
        print("Lean penalty footprint exporter failed:", exc.stderr or exc.stdout, file=sys.stderr)
        return 2
    checked, mismatches = compare_penalty_footprints(rows)
    print(f"lean penalty footprints: CHECKED={checked} MISMATCH={len(mismatches)}")
    for mismatch in mismatches:
        print(f"  {mismatch}", file=sys.stderr)
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
