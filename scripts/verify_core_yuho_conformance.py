#!/usr/bin/env python3
"""Build and compare independent Haskell and Lean Core Yuho evaluators.

This orchestrator enumerates semantic inputs and serializes them for each
implementation.  It does not calculate an expected technical result.
"""

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
VECTOR_PATH = ROOT / "mechanisation/conformance/core-yuho-v0.1.json"
LEAN_VECTOR_PATH = ROOT / "mechanisation/Yuho/CoreYuho/GeneratedVectors.lean"
HASKELL_RESULT_PATH = ROOT / "mechanisation/conformance/core-yuho-v0.1.haskell.json"
LEAN_RESULT_PATH = ROOT / "mechanisation/conformance/core-yuho-v0.1.lean.json"
STATUSES = ("satisfied", "not_satisfied", "unresolved")


def primitive(identifier: str) -> dict[str, object]:
    return {"id": identifier, "kind": "input"}


def group(kind: str, identifier: str, *members: dict[str, object]) -> dict[str, object]:
    return {"id": identifier, "kind": kind, "members": list(members)}


def scope_key(actor: str, instance: str, context: str = "principal-conduct") -> dict[str, str]:
    return {
        "actor": actor,
        "context": context,
        "instance": instance,
        "role": "principal",
    }


def vectors() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for operation in ("all", "any"):
        result.append({"id": f"{operation}-empty", "kind": operation, "values": []})
        for left, right in itertools.product(STATUSES, repeat=2):
            result.append(
                {
                    "id": f"{operation}-{left}-{right}",
                    "kind": operation,
                    "values": [left, right],
                }
            )

    for operation, samples in (
        ("branch", [[], ["not_satisfied"], ["unresolved", "not_satisfied"], ["satisfied", "unresolved"]]),
        ("guard", [[], ["not_satisfied"], ["unresolved"], ["satisfied", "unresolved"]]),
    ):
        for index, values in enumerate(samples):
            result.append({"id": f"{operation}-{index}", "kind": operation, "values": values})

    tree = group("all", "g:root", primitive("f:a"), group("any", "g:choice", primitive("f:b"), primitive("f:c")))
    for index, assignment in enumerate(itertools.product(STATUSES, repeat=3)):
        result.append(
            {
                "assignments": dict(zip(("f:a", "f:b", "f:c"), assignment, strict=True)),
                "expression": tree,
                "id": f"tree-{index:02d}",
                "kind": "requirement",
                "origin": "synthetic:all(a,any(b,c))",
            }
        )

    definition_shapes = [
        ("chain-satisfied", group("all", "d:chain", primitive("f:a"), primitive("f:b")), {"f:a": "satisfied", "f:b": "satisfied"}),
        ("chain-unresolved", group("all", "d:chain", primitive("f:a"), primitive("f:b")), {"f:a": "satisfied", "f:b": "unresolved"}),
        ("diamond-satisfied", group("all", "d:diamond", group("any", "d:left", primitive("f:a"), primitive("f:b")), group("any", "d:right", primitive("f:a"), primitive("f:c"))), {"f:a": "satisfied", "f:b": "not_satisfied", "f:c": "unresolved"}),
        ("diamond-failed", group("all", "d:diamond", group("any", "d:left", primitive("f:a"), primitive("f:b")), group("any", "d:right", primitive("f:a"), primitive("f:c"))), {"f:a": "not_satisfied", "f:b": "satisfied", "f:c": "not_satisfied"}),
        ("release-rash", group("all", "g:rash", primitive("f:act"), primitive("f:rashness"), primitive("f:endangerment")), {"f:act": "satisfied", "f:rashness": "satisfied", "f:endangerment": "satisfied"}),
        ("release-s84", group("all", "g:s84", primitive("f:unsoundness"), primitive("f:incapacity")), {"f:unsoundness": "satisfied", "f:incapacity": "unresolved"}),
    ]
    origins = {
        "release-rash": "research/singapore/research-release/scenarios/rash-endangerment/01_satisfied_primary.yh",
        "release-s84": "research/singapore/models/section84-explicit-attachments.yh",
    }
    for identifier, expression, assignments in definition_shapes:
        result.append(
            {
                "assignments": assignments,
                "expression": expression,
                "id": f"definition-{identifier}",
                "kind": "definition",
                "origin": origins.get(identifier, "synthetic:normalized-definition-dag"),
            }
        )

    for ordinary, guard in itertools.product(STATUSES, repeat=2):
        result.append(
            {
                "guards": [guard],
                "id": f"exception-{ordinary}-{guard}",
                "kind": "exception",
                "ordinary": ordinary,
            }
        )
    result.append({"guards": [], "id": "exception-no-guard", "kind": "exception", "ordinary": "satisfied"})

    for trigger, rebuttal in itertools.product(STATUSES, repeat=2):
        result.append(
            {
                "id": f"presumption-{trigger}-{rebuttal}",
                "kind": "presumption",
                "rebuttal": rebuttal,
                "trigger": trigger,
            }
        )

    selected = scope_key("actor:one", "xi:one")
    distractor = scope_key("actor:two", "xi:two", "attempt-conduct")
    for index, selected_status in enumerate(STATUSES):
        result.append(
            {
                "assignments": [
                    {"input": "f:guard", "key": distractor, "status": "satisfied"},
                    {"input": "f:guard", "key": selected, "status": selected_status},
                ],
                "id": f"scope-isolation-{index}",
                "input": "f:guard",
                "kind": "scope",
                "selected": selected,
            }
        )
    result.append(
        {
            "assignments": [
                {"input": "f:guard", "key": selected, "status": "not_satisfied"},
                {"input": "f:other", "key": selected, "status": "satisfied"},
            ],
            "id": "scope-input-isolation",
            "input": "f:guard",
            "kind": "scope",
            "selected": selected,
        }
    )

    allegation_a = {"assignments": {"f:a": "satisfied"}, "expression": primitive("f:a"), "id": "a:first"}
    allegation_b = {"assignments": {"f:b": "unresolved"}, "expression": primitive("f:b"), "id": "a:second"}
    allegation_c = {"assignments": {"f:c": "not_satisfied"}, "expression": primitive("f:c"), "id": "a:third"}
    result.extend(
        [
            {"allegations": [allegation_a, allegation_b], "id": "case-two", "kind": "case"},
            {"allegations": [allegation_b, allegation_a], "id": "case-reordered", "kind": "case"},
            {"allegations": [allegation_a, allegation_b, allegation_c], "id": "case-three", "kind": "case"},
        ]
    )

    adjacent = [
        {"expression": "e:old", "from": 10, "supersedes": None, "to": 20, "version": "1.0.0"},
        {"expression": "e:new", "from": 20, "supersedes": "e:old", "to": None, "version": "9.9.9"},
    ]
    gap = [
        {"expression": "e:left", "from": 10, "supersedes": None, "to": 20, "version": "2.0.0"},
        {"expression": "e:right", "from": 30, "supersedes": "e:left", "to": 40, "version": "1.0.0"},
    ]
    overlap = [
        {"expression": "e:first", "from": 10, "supersedes": None, "to": 30, "version": "1.0.0"},
        {"expression": "e:second", "from": 20, "supersedes": "e:first", "to": 40, "version": "99.0.0"},
    ]
    for identifier, date, intervals in (
        ("temporal-lower", 10, adjacent),
        ("temporal-before-boundary", 19, adjacent),
        ("temporal-boundary", 20, adjacent),
        ("temporal-open-end", 200, adjacent),
        ("temporal-before-all", 9, adjacent),
        ("temporal-gap", 25, gap),
        ("temporal-overlap", 25, overlap),
        ("temporal-version-ignored", 20, adjacent),
    ):
        result.append({"date": date, "id": identifier, "intervals": intervals, "kind": "temporal"})

    return result


def vector_document() -> dict[str, object]:
    return {"schema": "yuho.core-conformance-v0.1", "vectors": vectors()}


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def lean_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def lean_status(value: str) -> str:
    return {"satisfied": ".satisfied", "not_satisfied": ".notSatisfied", "unresolved": ".unresolved"}[value]


def lean_requirement(value: dict[str, object]) -> str:
    kind = value["kind"]
    identifier = lean_string(str(value["id"]))
    if kind == "input":
        return f".input {identifier}"
    members = ", ".join(lean_requirement(item) for item in value["members"])
    return f".{kind} {identifier} [{members}]"


def lean_pairs(assignments: dict[str, str]) -> str:
    return "[" + ", ".join(
        f"({lean_string(identifier)}, {lean_status(status)})"
        for identifier, status in sorted(assignments.items())
    ) + "]"


def lean_key(value: dict[str, str]) -> str:
    return (
        "{ actor := " + lean_string(value["actor"])
        + ", role := " + lean_string(value["role"])
        + ", context := " + lean_string(value["context"])
        + ", instanceId := " + lean_string(value["instance"]) + " }"
    )


def lean_interval(value: dict[str, object]) -> str:
    upper = "none" if value["to"] is None else f"some {value['to']}"
    supersedes = "none" if value["supersedes"] is None else f"some {lean_string(str(value['supersedes']))}"
    return (
        "{ expression := " + lean_string(str(value["expression"]))
        + f", effectiveFrom := {value['from']}, effectiveTo := {upper}"
        + ", version := " + lean_string(str(value["version"]))
        + f", supersedes := {supersedes} }}"
    )


def lean_vector(value: dict[str, object]) -> str:
    kind = str(value["kind"])
    identifier = lean_string(str(value["id"]))
    if kind in {"all", "any", "branch", "guard"}:
        values = ", ".join(lean_status(item) for item in value["values"])
        return f".aggregate {identifier} .{kind} [{values}]"
    if kind in {"requirement", "definition"}:
        return (
            f".requirement {identifier} {lean_string(kind)} "
            + "(" + lean_requirement(value["expression"]) + ")"
            + " " + lean_pairs(value["assignments"])
        )
    if kind == "exception":
        guards = ", ".join(lean_status(item) for item in value["guards"])
        return f".exception {identifier} {lean_status(str(value['ordinary']))} [{guards}]"
    if kind == "presumption":
        return f".presumption {identifier} {lean_status(str(value['trigger']))} {lean_status(str(value['rebuttal']))}"
    if kind == "scope":
        assignments = ", ".join(
            "{ key := " + lean_key(item["key"])
            + ", input := " + lean_string(str(item["input"]))
            + ", status := " + lean_status(str(item["status"])) + " }"
            for item in value["assignments"]
        )
        return f".scope {identifier} {lean_key(value['selected'])} {lean_string(str(value['input']))} [{assignments}]"
    if kind == "case":
        allegations = ", ".join(
            "{ identifier := " + lean_string(str(item["id"]))
            + ", requirement := " + lean_requirement(item["expression"])
            + ", assignments := " + lean_pairs(item["assignments"]) + " }"
            for item in value["allegations"]
        )
        return f".caseAnalysis {identifier} [{allegations}]"
    if kind == "temporal":
        intervals = ", ".join(lean_interval(item) for item in value["intervals"])
        return f".temporal {identifier} {value['date']} [{intervals}]"
    raise ValueError(f"unsupported vector kind: {kind}")


def generated_lean(document: dict[str, object]) -> bytes:
    rendered = [lean_vector(item) for item in document["vectors"]]
    chunks = [rendered[index : index + 12] for index in range(0, len(rendered), 12)]
    definitions = "\n\n".join(
        f"def vectorChunk{index} : List Vector := [\n  "
        + ",\n  ".join(chunk) + "\n]"
        for index, chunk in enumerate(chunks)
    )
    joined = " ++ ".join(f"vectorChunk{index}" for index in range(len(chunks)))
    source = (
        "/- Generated input-only conformance vectors. Do not add expected results. -/\n"
        "import Yuho.CoreYuho.Conformance\n\n"
        "namespace Yuho.CoreYuho.Conformance\n\n"
        "set_option maxHeartbeats 1000000\n\n"
        + definitions + "\n\n"
        "def vectors : List Vector := " + joined + "\n\n"
        "end Yuho.CoreYuho.Conformance\n"
    )
    return source.encode()


def checked_file(path: Path, expected: bytes) -> None:
    if not path.exists() or path.read_bytes() != expected:
        raise SystemExit(f"generated conformance input is stale: {path.relative_to(ROOT)}")


def run(command: list[str], cwd: Path, env: dict[str, str]) -> bytes:
    completed = subprocess.run(
        command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if completed.returncode:
        sys.stdout.buffer.write(completed.stdout)
        sys.stderr.buffer.write(completed.stderr)
        raise SystemExit(f"command failed ({completed.returncode}): {' '.join(command)}")
    return completed.stdout


def executable_path(env: dict[str, str]) -> str:
    return run(
        ["cabal", "list-bin", "exe:yuho-core-conformance"],
        ROOT,
        env,
    ).decode().strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="update generated inputs and retained equal results")
    parser.add_argument("--inputs-only", action="store_true", help="only update/check serialized input files")
    args = parser.parse_args()

    document = vector_document()
    vector_bytes = canonical_json(document)
    lean_bytes = generated_lean(document)
    if args.update:
        VECTOR_PATH.write_bytes(vector_bytes)
        LEAN_VECTOR_PATH.write_bytes(lean_bytes)
    else:
        checked_file(VECTOR_PATH, vector_bytes)
        checked_file(LEAN_VECTOR_PATH, lean_bytes)
    if args.inputs_only:
        return 0

    env = os.environ.copy()
    home = Path.home()
    env["PATH"] = os.pathsep.join(
        [str(home / ".ghcup/bin"), str(home / ".elan/bin"), env.get("PATH", "")]
    )
    run(["cabal", "v2-build", "exe:yuho-core-conformance", "--offline", "-j1"], ROOT, env)
    run(["lake", "build", "core_conformance"], ROOT / "mechanisation", env)
    haskell = run([executable_path(env), str(VECTOR_PATH)], ROOT, env)
    lean = run(["lake", "env", "lean", "--run", "scripts/CoreConformance.lean"], ROOT / "mechanisation", env)
    if haskell != lean:
        raise SystemExit("Haskell/Lean conformance mismatch")
    if args.update:
        HASKELL_RESULT_PATH.write_bytes(haskell)
        LEAN_RESULT_PATH.write_bytes(lean)
    else:
        checked_file(HASKELL_RESULT_PATH, haskell)
        checked_file(LEAN_RESULT_PATH, lean)

    schema_hash = hashlib.sha256(vector_bytes).hexdigest()
    result_hash = hashlib.sha256(haskell).hexdigest()
    print(f"Core Yuho conformance: {len(document['vectors'])} vectors passed")
    print(f"input sha256: {schema_hash}")
    print(f"result sha256: {result_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
