#!/usr/bin/env python3
"""Generate input-only v0.2 vectors and compare independent Haskell/Lean evaluation."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VECTOR_PATH = ROOT / "mechanisation/conformance/core-yuho-v0.2.json"
HASKELL_RESULT = ROOT / "mechanisation/conformance/core-yuho-v0.2.haskell.json"
LEAN_RESULT = ROOT / "mechanisation/conformance/core-yuho-v0.2.lean.json"
LEAN_VECTORS = ROOT / "mechanisation/Yuho/CoreYuho/GeneratedTypedFiniteVectors.lean"
STATUSES = ("satisfied", "not_satisfied", "unresolved")


def scalar(kind: str, value: object | None = None, **extra: object) -> dict[str, object]:
    row: dict[str, object] = {"kind": kind}
    if value is not None:
        row["value"] = value
    row.update(extra)
    return row


def rule(identifier: str, polarity: str, status: str, proposition: str = "p:target") -> dict[str, str]:
    return {"id": identifier, "polarity": polarity, "proposition": proposition, "status": status}


def vectors() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for status in STATUSES:
        rows.append({"id": f"negation-{status}", "kind": "negation", "status": status})

    for size in range(5):
        for assignment in itertools.product(STATUSES, repeat=size):
            suffix = "-".join(assignment) if assignment else "empty"
            for operation in ("forall", "exists"):
                rows.append({"id": f"{operation}-{size}-{suffix}", "kind": "quantifier",
                             "operation": operation, "values": list(assignment)})
            for operation in ("at-least", "at-most", "exactly"):
                for threshold in range(6):
                    rows.append({"id": f"{operation}-{threshold}-{size}-{suffix}",
                                 "kind": "cardinality", "operation": operation,
                                 "threshold": threshold, "values": list(assignment)})

    comparisons = ("eq", "neq", "lt", "lte", "gt", "gte")
    for operation in comparisons:
        for left, right in itertools.product(range(3), repeat=2):
            rows.append({"id": f"integer-{operation}-{left}-{right}", "kind": "comparison",
                         "operation": operation, "left": scalar("integer", left),
                         "right": scalar("integer", right)})
        rows.append({"id": f"unresolved-{operation}", "kind": "comparison",
                     "operation": operation, "left": scalar("unresolved"),
                     "right": scalar("integer", 1)})
    for operation in comparisons:
        rows.append({"id": f"date-{operation}", "kind": "comparison", "operation": operation,
                     "left": scalar("date", 20000), "right": scalar("date", 20001)})
        rows.append({"id": f"money-{operation}", "kind": "comparison", "operation": operation,
                     "left": scalar("money", 5000, currency="SGD"),
                     "right": scalar("money", 5001, currency="SGD")})
    for operation in ("eq", "neq"):
        rows.append({"id": f"enum-{operation}", "kind": "comparison", "operation": operation,
                     "left": scalar("enum", "high", type="risk"),
                     "right": scalar("enum", "low", type="risk")})

    priority_samples = [
        ("higher-defeat", rule("r:high", "defeat", "satisfied"),
         rule("r:low", "establish", "satisfied"), True),
        ("higher-establish", rule("r:high", "establish", "satisfied"),
         rule("r:low", "defeat", "satisfied"), True),
        ("higher-unresolved", rule("r:high", "defeat", "unresolved"),
         rule("r:low", "establish", "satisfied"), True),
        ("higher-fails", rule("r:high", "defeat", "not_satisfied"),
         rule("r:low", "establish", "satisfied"), True),
        ("incomparable-conflict", rule("r:left", "establish", "satisfied"),
         rule("r:right", "defeat", "satisfied"), False),
        ("diamond-left-edge", rule("r:top-left", "defeat", "satisfied"),
         rule("r:base", "establish", "satisfied"), True),
        ("diamond-right-edge", rule("r:top-right", "defeat", "unresolved"),
         rule("r:base", "establish", "satisfied"), True),
        ("chain-top-edge", rule("r:top", "defeat", "satisfied"),
         rule("r:middle", "establish", "satisfied"), True),
        ("chain-middle-edge", rule("r:middle", "establish", "satisfied"),
         rule("r:bottom", "defeat", "satisfied"), True),
    ]
    for identifier, higher, lower, ordered in priority_samples:
        rows.append({"id": f"priority-{identifier}", "kind": "priority",
                     "higher": higher, "lower": lower, "ordered": ordered})

    for term_kind, term_id in (("variable", "var:item"), ("entity", "item:fixed")):
        rows.append({"id": f"substitution-{term_kind}", "kind": "substitution",
                     "binding": {"variable": "var:item", "entity": "item:laptop"},
                     "term": {"kind": term_kind, "id": term_id}})
    for selected_status in STATUSES:
        rows.append({"id": f"actor-isolation-{selected_status}", "kind": "isolation",
                     "selected": "actor:one/p:fact",
                     "assignments": {"actor:one/p:fact": selected_status,
                                     "actor:two/p:fact": "satisfied"}})
        rows.append({"id": f"allegation-isolation-{selected_status}", "kind": "isolation",
                     "selected": "a:one/p:fact",
                     "assignments": {"a:one/p:fact": selected_status,
                                     "a:two/p:fact": "not_satisfied"}})
    return rows


def document() -> dict[str, object]:
    return {"schema": "yuho.core-conformance-v0.2", "vectors": vectors()}


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def lean_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def lean_status(value: str) -> str:
    return {"satisfied": ".satisfied", "not_satisfied": ".notSatisfied",
            "unresolved": ".unresolved"}[value]


def lean_scalar(value: dict[str, object]) -> str:
    kind = value["kind"]
    if kind == "integer":
        return f".integer {value['value']}"
    if kind == "date":
        return f".date {value['value']}"
    if kind == "enum":
        return f".enumValue {lean_string(str(value['type']))} {lean_string(str(value['value']))}"
    if kind == "money":
        return f".money {lean_string(str(value['currency']))} {value['value']}"
    if kind == "unresolved":
        return ".unresolved"
    raise ValueError(kind)


def lean_rule(value: dict[str, str]) -> str:
    polarity = ".establish" if value["polarity"] == "establish" else ".defeat"
    return ("{ identifier := " + lean_string(value["id"])
            + ", proposition := " + lean_string(value["proposition"])
            + f", polarity := {polarity}, status := {lean_status(value['status'])} }}")


def lean_vector(value: dict[str, object]) -> str:
    identifier = lean_string(str(value["id"]))
    kind = value["kind"]
    if kind == "negation":
        return f".negation {identifier} {lean_status(str(value['status']))}"
    if kind == "quantifier":
        statuses = ", ".join(lean_status(str(item)) for item in value["values"])
        return f".quantifier {identifier} .{value['operation']} [{statuses}]"
    if kind == "cardinality":
        names = {"at-least": "atLeast", "at-most": "atMost", "exactly": "exactly"}
        statuses = ", ".join(lean_status(str(item)) for item in value["values"])
        return f".cardinality {identifier} .{names[str(value['operation'])]} {value['threshold']} [{statuses}]"
    if kind == "comparison":
        names = {"eq": "equal", "neq": "notEqual", "lt": "lessThan", "lte": "lessEqual",
                 "gt": "greaterThan", "gte": "greaterEqual"}
        return (f".comparison {identifier} .{names[str(value['operation'])]} "
                f"({lean_scalar(value['left'])}) ({lean_scalar(value['right'])})")
    if kind == "priority":
        ordered = "true" if value["ordered"] else "false"
        return f".priority {identifier} ({lean_rule(value['higher'])}) ({lean_rule(value['lower'])}) {ordered}"
    if kind == "substitution":
        binding = value["binding"]
        term = value["term"]
        return (f".substitution {identifier} {lean_string(str(binding['variable']))} "
                f"{lean_string(str(binding['entity']))} "
                "{ identifier := " + lean_string(str(term["id"]))
                + ", typeName := \"property\" }")
    if kind == "isolation":
        assignments = ", ".join(
            f"({lean_string(key)}, {lean_status(status)})"
            for key, status in sorted(value["assignments"].items()))
        return f".isolation {identifier} {lean_string(str(value['selected']))} [{assignments}]"
    raise ValueError(str(kind))


def generated_lean(doc: dict[str, object]) -> bytes:
    rendered = [lean_vector(item) for item in doc["vectors"]]
    chunks = [rendered[index:index + 16] for index in range(0, len(rendered), 16)]
    definitions = "\n\n".join(
        f"def vectorChunk{index} : List Vector := [\n  " + ",\n  ".join(chunk) + "\n]"
        for index, chunk in enumerate(chunks))
    joined = " ++ ".join(f"vectorChunk{index}" for index in range(len(chunks)))
    return ("/- Generated input-only Core Yuho v0.2 vectors; no expected results. -/\n"
            "import Yuho.CoreYuho.TypedFiniteConformance\n\n"
            "namespace Yuho.CoreYuho.TypedFinite.Conformance\n\n"
            "set_option maxHeartbeats 4000000\n\n" + definitions
            + "\n\ndef vectors : List Vector := " + joined
            + "\n\nend Yuho.CoreYuho.TypedFinite.Conformance\n").encode()


def run(command: list[str], cwd: Path, env: dict[str, str]) -> bytes:
    completed = subprocess.run(command, cwd=cwd, env=env, capture_output=True)
    if completed.returncode:
        sys.stdout.buffer.write(completed.stdout)
        sys.stderr.buffer.write(completed.stderr)
        raise SystemExit(f"command failed: {' '.join(command)}")
    return completed.stdout


def checked(path: Path, expected: bytes) -> None:
    if not path.exists() or path.read_bytes() != expected:
        raise SystemExit(f"stale generated artifact: {path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--inputs-only", action="store_true")
    args = parser.parse_args()
    doc = document()
    vector_bytes = canonical(doc)
    lean_bytes = generated_lean(doc)
    if args.update:
        VECTOR_PATH.write_bytes(vector_bytes)
        LEAN_VECTORS.write_bytes(lean_bytes)
    else:
        checked(VECTOR_PATH, vector_bytes)
        checked(LEAN_VECTORS, lean_bytes)
    if args.inputs_only:
        return 0
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([str(Path.home() / ".ghcup/bin"),
                                   str(Path.home() / ".elan/bin"), env.get("PATH", "")])
    run(["cabal", "v2-build", "exe:yuho-core-conformance", "--offline", "-j1"],
        ROOT / "rewrite/haskell", env)
    executable = run(["cabal", "list-bin", "exe:yuho-core-conformance"],
                     ROOT / "rewrite/haskell", env).decode().strip()
    run(["lake", "build", "typed_finite_conformance"], ROOT / "mechanisation", env)
    haskell = run([executable, str(VECTOR_PATH)], ROOT, env)
    lean = run(["lake", "env", "lean", "--run", "scripts/TypedFiniteConformance.lean"],
               ROOT / "mechanisation", env)
    if haskell != lean:
        raise SystemExit("Core Yuho v0.2 Haskell/Lean conformance mismatch")
    if args.update:
        HASKELL_RESULT.write_bytes(haskell)
        LEAN_RESULT.write_bytes(lean)
    else:
        checked(HASKELL_RESULT, haskell)
        checked(LEAN_RESULT, lean)
    print(f"Core Yuho v0.2 conformance: {len(doc['vectors'])} vectors passed")
    print(f"input sha256: {hashlib.sha256(vector_bytes).hexdigest()}")
    print(f"result sha256: {hashlib.sha256(haskell).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
