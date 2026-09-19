"""Sixth-fragment schema, proof-vector, byte and persistent-protocol checks."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

WORKSPACE = Path(__file__).resolve().parents[1]
FIXTURES = WORKSPACE / "test/proof-fixtures"
TERMS = WORKSPACE / "test/term-fixtures/requests"
INPUT_KEYS = ("input_schema", "fragment", "sources", "registry",
              "root_rule", "facts", "policy")


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode()


def wire(path):
    data = path.read_bytes()
    return canonical(json.loads(data)) if path.suffix == ".json" else data


def integrity():
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_bytes())
    assert manifest["format"] == "yuho.ps-fixtures/v1"
    files = [FIXTURES / "CASES.json", FIXTURES / "PROOF-VECTORS.json",
             FIXTURES / "generate.py", *sorted((FIXTURES / "requests").iterdir())]
    actual = {str(path.relative_to(FIXTURES)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in files}
    assert actual == manifest["files"], "proof fixture manifest mismatch"
    with tempfile.TemporaryDirectory(prefix="yuho-ps-regeneration-") as folder:
        target = Path(folder) / "test/proof-fixtures"
        sibling = target.parent / "term-fixtures/requests"
        sibling.mkdir(parents=True)
        for name in ("PT01", "PT17", "PT18", "PT20"):
            shutil.copy2(TERMS / f"{name}.json", sibling / f"{name}.json")
        target.mkdir()
        shutil.copy2(FIXTURES / "generate.py", target / "generate.py")
        subprocess.run([sys.executable, str(target / "generate.py")], check=True)
        for path in files + [FIXTURES / "MANIFEST.json"]:
            assert path.read_bytes() == (target / path.relative_to(FIXTURES)).read_bytes(), path


def observations(result):
    return {row["leaf_id"]: row for rule in result["rules"]
            for row in rule["proof_observations"]}


def check_vector(name, case, vector, result):
    assert vector["expected_status"] == case["status"] == result["status"], name
    code = result["diagnostics"][0]["code"] if result["diagnostics"] else ""
    assert code == case["code"] == vector["invalid_classification"], name
    assert vector["selected_ids"] == case["selected"] == [row["penalty_id"]
        for row in result.get("selected_penalties", [])], name
    if result["status"] == "rejected":
        assert not result.get("rules") and not result.get("selected_penalties"), name
        assert not result.get("penalty_selection_trace") and not result.get("selection_warnings"), name
        return
    assert result["fragment"] == "SuppliedProofStatus-v1", name
    observed = observations(result)
    for leaf, row in observed.items():
        assert row["proof_status"] == vector["bindings"][leaf]["proof_status"], name
        assert row["status_source"] == vector["bindings"][leaf]["status_source"], name
        assert row["satisfaction"] == vector["projection"][leaf], name
    assert all(row["satisfaction"] in ("satisfied", "not_satisfied", "unresolved")
               for row in observed.values()), name
    for rule in result["rules"]:
        assert [row["leaf_id"] for row in rule["proof_observations"]] == [edge["id"]
            for edge in rule["trace"] if edge["kind"] == "leaf"], name
        assert [edge["id"] for edge in rule["trace"]] == [identifier
            for branch in rule["branches"] for identifier in branch["trace_ids"]], name
        assert ({branch["id"]: branch["trace_ids"] for branch in rule["branches"]} ==
                vector["expected_trace_order"][rule["id"]]), name
        for branch in rule["branches"]:
            assert branch["applicable_exceptions"] == [row["id"] for row in branch["exceptions"]
                if row["applicable"]], name
            assert branch["exceptions"] == [] or branch["reason"] not in (
                "requirements_not_satisfied", "requirements_unresolved"), name
    for row in result["selected_penalties"]:
        assert row["term"]["term_id"] in vector["term_ids"], name
        assert row["penalty_id"] in vector["declaration_order"], name
    assert len(result["selected_penalties"]) == len({row["penalty_id"]
        for row in result["selected_penalties"]}), name
    if "expected_branch_statuses" in vector:
        root = next(rule for rule in result["rules"] if rule["id"] == result["root_rule"])
        assert ([[branch["id"], branch["status"]] for branch in root["branches"]] ==
                vector["expected_branch_statuses"]), name
    if "expected_exception_statuses" in vector:
        root = next(rule for rule in result["rules"] if rule["id"] == result["root_rule"])
        assert ([item["guard_status"] for branch in root["branches"]
                 for item in branch["exceptions"]] == vector["expected_exception_statuses"]), name
    if "expected_selection_trace" in vector:
        assert ([[row["penalty_id"], row["branch_id"], row["result"]]
                 for row in result["penalty_selection_trace"]] ==
                vector["expected_selection_trace"]), name
    if name == "PS31":
        root = next(rule for rule in result["rules"] if rule["id"] == result["root_rule"])
        guards = root["branches"][0]["exceptions"]
        assert [row["guard_status"] for row in guards] == ["satisfied", "unresolved"]
        assert root["branches"][0]["applicable_exceptions"] == ["x:root:1"]
    if name == "PS33":
        assert result["status"] == "satisfied"
        assert [row["result"] for row in result["penalty_selection_trace"]] == ["guard_unresolved"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    executable = parser.parse_args().executable.resolve()
    integrity()
    cases = json.loads((FIXTURES / "CASES.json").read_bytes())
    vectors = json.loads((FIXTURES / "PROOF-VECTORS.json").read_bytes())
    assert len(cases) == 72 and set(cases) == set(vectors)
    request_schema = json.loads((WORKSPACE / "schema/request.schema.json").read_bytes())
    result_schema = json.loads((WORKSPACE / "schema/result.schema.json").read_bytes())
    Draft202012Validator.check_schema(request_schema)
    Draft202012Validator.check_schema(result_schema)
    request_validator = Draft202012Validator(request_schema)
    result_validator = Draft202012Validator(result_schema)
    requests = {name: wire(FIXTURES / case["file"]) for name, case in cases.items()}
    for name, case in cases.items():
        if case["status"] != "rejected":
            request_validator.validate(json.loads(requests[name]))
    sequence = []
    for name, case in cases.items():
        sequence.append(name)
        if case["status"] == "rejected":
            sequence.append("PS01")
    sequence.extend(["PS16", "PS31", "PS33", "PS57", "PS01"])
    completed = subprocess.run([str(executable)], input=b"".join(requests[name]
        for name in sequence), capture_output=True, check=True, timeout=120)
    assert not completed.stderr, completed.stderr
    lines = completed.stdout.splitlines(keepends=True)
    assert len(lines) == len(sequence), (len(lines), len(sequence))
    seen = {}
    for name, line in zip(sequence, lines, strict=True):
        assert line.endswith(b"\n") and line.count(b"\n") == 1, name
        result = json.loads(line)
        result_validator.validate(result)
        assert line == canonical(result), f"noncanonical result: {name}"
        assert seen.setdefault(name, line) == line, f"unstable result bytes: {name}"
        check_vector(name, cases[name], vectors[name], result)
        if result["status"] != "rejected":
            request = json.loads(requests[name])
            digest = hashlib.sha256(canonical({key: request[key]
                for key in INPUT_KEYS}).rstrip(b"\n")).hexdigest()
            assert result["input_digest"] == digest, name
    print(f"proof protocol: {len(cases)} fixtures, {len(sequence)} persistent requests, "
          "schemas, vectors, canonical bytes, regeneration and rejection recovery passed")


if __name__ == "__main__":
    main()
