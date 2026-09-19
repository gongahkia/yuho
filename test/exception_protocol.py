"""Check the exception protocol, schemas, vectors, and persistent recovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator


WORKSPACE = Path(__file__).resolve().parents[1]
FIXTURES = WORKSPACE / "test/exception-fixtures"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def check_manifest() -> None:
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_bytes())
    assert manifest["schema"] == "yuho.exception-fixture-manifest/v1"
    actual = {str(path.relative_to(FIXTURES)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [FIXTURES / "CASES.json", FIXTURES / "PROOF-VECTORS.json",
                           *sorted((FIXTURES / "requests").iterdir())]}
    assert actual == manifest["files"], "exception fixture manifest mismatch"


def verify_vector(vector: dict, result: dict) -> None:
    assert vector["expected_status"] == result["status"], vector["case"]
    assert vector["expected_diagnostic_code"] == (
        result["diagnostics"][0]["code"] if result["diagnostics"] else ""), vector["case"]
    if result["status"] == "rejected":
        assert not result.get("rules", []), vector["case"]
        assert vector["expected_diagnostic_class"] in {
            "decode", "invariant", "capability"
        }, vector["case"]
        return
    rules = result["rules"]
    rule_map = {rule["id"]: rule for rule in rules}
    assert {key: rule["status"] for key, rule in rule_map.items()} == vector[
        "expected_rule_statuses"], vector["case"]
    assert {key: [branch["path"] for branch in rule["branches"]]
            for key, rule in rule_map.items()} == vector[
                "expected_rule_branch_paths"], vector["case"]
    root = rule_map[result["root_rule"]]
    assert [branch["path"] for branch in root["branches"]] == vector[
        "expected_root_branch_paths"], vector["case"]
    assert [branch["status"] for branch in root["branches"]] == vector[
        "expected_branch_statuses"], vector["case"]
    fired = [identifier for branch in root["branches"]
             for identifier in branch["applicable_exceptions"]]
    assert fired == vector["expected_fired_exception_ids"], vector["case"]
    observations = []
    order = {}
    for rule in rules:
        order[rule["id"]] = []
        for branch in rule["branches"]:
            for exception in branch["exceptions"]:
                order[rule["id"]].append(exception["id"])
                observations.append({
                    "rule": rule["id"], "branch": branch["id"],
                    "branch_path": branch["path"], "exception": exception["id"],
                    "source_id": exception["source_id"],
                    "target": exception["target_rule"],
                    "target_status": exception["target_status"],
                    "guard_status": exception["guard_status"],
                    "applicable": exception["applicable"],
                })
                assert exception["target_rule"] in rule_map, vector["case"]
                assert rule_map[exception["target_rule"]]["status"] == exception[
                    "target_status"], vector["case"]
    assert observations == vector["expected_guard_observations"], vector["case"]
    assert order == vector["expected_trace_order"], vector["case"]
    declared_edges = {(edge["rule"], edge["branch"], edge["exception"],
                       edge["target"], edge["source_id"])
                      for edge in vector["dependency_edges"]}
    assert all((item["rule"], item["branch"], item["exception"],
                item["target"], item["source_id"]) in declared_edges
               for item in observations), vector["case"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    check_manifest()
    cases = json.loads((FIXTURES / "CASES.json").read_bytes())
    vectors = {item["case"]: item for item in json.loads(
        (FIXTURES / "PROOF-VECTORS.json").read_bytes())}
    assert set(cases) == set(vectors)
    request_schema = Draft202012Validator(json.loads(
        (WORKSPACE / "schema/request.schema.json").read_bytes()))
    result_schema = Draft202012Validator(json.loads(
        (WORKSPACE / "schema/result.schema.json").read_bytes()))
    Draft202012Validator.check_schema(request_schema.schema)
    Draft202012Validator.check_schema(result_schema.schema)
    requests = {}
    for name in sorted(cases):
        extension = ".txt" if name in {"E32", "E33", "E35"} else ".json"
        requests[name] = (FIXTURES / "requests" / f"{name}{extension}").read_bytes()
        if cases[name]["status"] != "rejected":
            request_schema.validate(json.loads(requests[name]))
    sequence = []
    for name in sorted(cases):
        sequence.append(name)
        if cases[name]["status"] == "rejected":
            sequence.append("E01")
    sequence.extend(["E02", "E04", "E06", "E18", "E34"] * 3)
    payload = b"".join(requests[name].rstrip(b"\n") + b"\n" for name in sequence)
    completed = subprocess.run([str(args.executable.resolve())], input=payload,
                               capture_output=True, check=True, timeout=30)
    assert not completed.stderr, completed.stderr
    lines = completed.stdout.splitlines(keepends=True)
    assert len(lines) == len(sequence), (len(lines), len(sequence))
    seen = {}
    for name, line in zip(sequence, lines, strict=True):
        assert line.endswith(b"\n") and line.count(b"\n") == 1, name
        assert line == seen.setdefault(name, line), f"nondeterministic bytes: {name}"
        result = json.loads(line)
        result_schema.validate(result)
        assert line == canonical(result), f"noncanonical bytes: {name}"
        expected = cases[name]
        assert result["status"] == expected["status"], name
        diagnostics = result["diagnostics"]
        assert (diagnostics[0]["code"] if diagnostics else "") == expected["code"], name
        assert (diagnostics[0]["stage"] if diagnostics else "") == expected["stage"], name
        verify_vector(vectors[name], result)
        if result["status"] != "rejected":
            request = json.loads(requests[name])
            keys = ("input_schema", "fragment", "sources", "registry",
                    "root_rule", "facts", "policy")
            digest = hashlib.sha256(canonical({key: request[key] for key in keys}).rstrip(
                b"\n")).hexdigest()
            assert result["input_digest"] == digest, name
    print(f"exception protocol: {len(cases)} fixtures, {len(sequence)} persistent requests, "
          "schema, vectors, canonical bytes, and recovery passed")


if __name__ == "__main__":
    main()
