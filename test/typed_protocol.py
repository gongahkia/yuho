"""Replay typed bindings through one persistent subprocess and production schemas."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

WORKSPACE = Path(__file__).resolve().parents[1]
FIXTURES = WORKSPACE / "test/typed-fixtures"
sys.path.insert(0, str(FIXTURES))
from legacy_adapter import project  # noqa: E402


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode()


def verify_manifest() -> None:
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_bytes())
    assert manifest["schema"] == "yuho.typed-fixture-manifest/v1"
    paths = [FIXTURES / "CASES.json", FIXTURES / "PROOF-VECTORS.json",
             FIXTURES / "MIGRATION-PROBES.json", FIXTURES / "legacy_adapter.py",
             FIXTURES / "generate.py",
             *sorted((FIXTURES / "requests").iterdir())]
    actual = {str(path.relative_to(FIXTURES)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in paths}
    assert actual == manifest["files"], "typed fixture manifest mismatch"


def verify_vector(vector: dict, result: dict) -> None:
    name = vector["case"]
    assert result["status"] == vector["expected_status"], name
    assert (result["diagnostics"][0]["code"] if result["diagnostics"] else "") == (
        vector["expected_diagnostic_code"]), name
    if result["status"] == "rejected":
        assert not result.get("rules", []), name
        assert vector["classification"] == "rejection", name
        if "expected_binding_error" in vector:
            issue = result["diagnostics"][0]
            assert issue["stage"] == "validate" and issue["severity"] == "error", name
            assert issue["parameters"] == vector["expected_binding_error"], name
            assert issue["path"].endswith("/declared_metadata/" +
                                          issue["parameters"]["field"]), name
            assert issue["span"] is not None, name
        return
    assert result["fragment"] == "TypedBooleanFacts-v1", name
    rules = result["rules"]
    rule_map = {rule["id"]: rule for rule in rules}
    assert {key: rule["status"] for key, rule in rule_map.items()} == vector[
        "expected_rule_statuses"], name
    assert [branch["status"] for branch in rule_map[result["root_rule"]]["branches"]] == (
        vector["expected_root_branch_statuses"]), name
    assert {key: [branch["path"] for branch in rule["branches"]]
            for key, rule in rule_map.items()} == vector["expected_rule_branch_paths"], name
    assert {key: item["value"] for key, item in vector["leaf_bindings"].items()} == vector[
        "boolean_projection"], name
    for rule in rules:
        expected = [trace for trace in rule["trace"] if trace["kind"] == "leaf"]
        observations = rule["fact_observations"]
        assert len(observations) == len(expected), name
        for trace, observation in zip(expected, observations, strict=True):
            binding = vector["leaf_bindings"][trace["id"]]
            declaration = vector["leaf_declarations"][trace["id"]]
            assert (observation["rule_id"], observation["branch_id"], observation["leaf_id"]) == (
                rule["id"], trace["branch"], trace["id"]), name
            assert observation["value"] == binding["value"], name
            assert trace["value"] == str(binding["value"]).lower(), name
            assert observation.get("provenance") == binding.get("provenance"), name
            assert observation["burden_check"] == (
                "matched" if "burden" in declaration else "not_declared"), name
            assert observation["standard_check"] == (
                "matched" if "standard_of_proof" in declaration else "not_declared"), name
            if trace["id"] in vector["expected_binding_checks"]:
                assert [observation["burden_check"], observation["standard_check"]] == (
                    vector["expected_binding_checks"][trace["id"]]), name
        assert [item["leaf_id"] for item in observations] == (
            vector["expected_fact_observation_order"][rule["id"]]), name
        guard_order = [[item["id"], item["guard_status"]]
                       for branch in rule["branches"] for item in branch["exceptions"]]
        assert guard_order == vector["expected_guard_trace_order"].get(rule["id"], []), name
        fired = [identifier for branch in rule["branches"]
                 for identifier in branch["applicable_exceptions"]]
        assert fired == vector["expected_fired_exception_ids"].get(rule["id"], []), name
    for edge in vector["dependency_edges"]:
        if edge["rule"] not in rule_map:
            continue
        source = rule_map[edge["rule"]]
        matching = [observation for branch in source["branches"]
                    for observation in branch["exceptions"]
                    if observation["id"] == edge["exception"]]
        for item in matching:
            assert item["target_rule"] == edge["target"], name
            assert item["target_status"] == rule_map[edge["target"]]["status"], name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    verify_manifest()
    verify_migration_adapter()
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
    for name, item in sorted(cases.items()):
        requests[name] = (FIXTURES / item["request_file"]).read_bytes()
        if item["status"] != "rejected":
            request_schema.validate(json.loads(requests[name]))
    sequence = []
    for name in sorted(cases):
        sequence.append(name)
        if cases[name]["status"] == "rejected":
            sequence.append("T01")
    sequence.extend(["T03", "T08", "T15", "T16", "T44"] * 3)
    payload = b"".join(requests[name].rstrip(b"\n") + b"\n" for name in sequence)
    completed = subprocess.run([str(args.executable.resolve())], input=payload,
                               capture_output=True, check=True, timeout=45)
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
        assert result["status"] == cases[name]["status"], name
        assert (result["diagnostics"][0]["stage"] if result["diagnostics"] else "") == (
            cases[name]["stage"]), name
        verify_vector(vectors[name], result)
        if result["status"] != "rejected":
            request = json.loads(requests[name])
            keys = ("input_schema", "fragment", "sources", "registry",
                    "root_rule", "facts", "policy")
            digest = hashlib.sha256(canonical({key: request[key] for key in keys}).rstrip(
                b"\n")).hexdigest()
            assert result["input_digest"] == digest, name
    print(f"typed protocol: {len(cases)} fixtures, {len(sequence)} persistent requests, "
          "schemas, vectors, bytes and recovery passed")


def verify_migration_adapter() -> None:
    mapping = {"taking": "f:taking"}
    primitive = project({"taking": True}, mapping)
    assert primitive.bindings == {"f:taking": {"type": "bool", "value": True}}
    assert primitive.notices and not primitive.rejections
    burden = project({"taking": {"value": True, "burden": "defence"}}, mapping)
    assert burden.bindings["f:taking"]["burden"]["kind"] == "unspecified"
    assert burden.notices and not burden.rejections
    assert project({"taking": "true"}, mapping).rejections
    assert project({"taking": {"value": True, "confidence": 0.9}}, mapping).rejections
    collision = project({"f-root": True, "f_root": False},
                        {"f-root": "f:one", "f_root": "f:one"})
    assert collision.rejections
    probes = json.loads((FIXTURES / "MIGRATION-PROBES.json").read_bytes())
    assert len(probes) == 5


if __name__ == "__main__":
    main()
