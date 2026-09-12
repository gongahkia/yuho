"""Seventh-fragment schema, vectors, canonical bytes and persistent protocol."""

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
FIXTURES = WORKSPACE / "test/presumption-fixtures"
PROOF = WORKSPACE / "test/proof-fixtures/requests"
INPUT_KEYS = ("input_schema", "fragment", "sources", "registry",
              "root_rule", "facts", "policy", "presumptions")


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode()


def wire(path):
    data = path.read_bytes()
    return canonical(json.loads(data)) if path.suffix == ".json" else data


def integrity():
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_bytes())
    assert manifest["format"] == "yuho.rd-fixtures/v1"
    files = [FIXTURES / "CASES.json", FIXTURES / "PROOF-VECTORS.json",
             FIXTURES / "generate.py", *sorted((FIXTURES / "requests").iterdir())]
    actual = {str(path.relative_to(FIXTURES)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in files}
    assert actual == manifest["files"], "RD fixture manifest mismatch"
    with tempfile.TemporaryDirectory(prefix="yuho-rd-regeneration-") as folder:
        target = Path(folder) / "test/presumption-fixtures"
        sibling = target.parent / "proof-fixtures/requests"
        sibling.mkdir(parents=True)
        for name in ("PS01", "PS28", "PS33"):
            shutil.copy2(PROOF / f"{name}.json", sibling / f"{name}.json")
        target.mkdir()
        shutil.copy2(FIXTURES / "generate.py", target / "generate.py")
        subprocess.run([sys.executable, str(target / "generate.py")], check=True)
        for path in files + [FIXTURES / "MANIFEST.json"]:
            assert path.read_bytes() == (target / path.relative_to(FIXTURES)).read_bytes(), path


def projected(status):
    return {"proved":"satisfied", "not_proved":"not_satisfied",
            "unresolved":"unresolved"}[status["kind"]]


def expected_effective(direct, states):
    if direct == "satisfied" or "active" in states:
        return "satisfied"
    if direct == "unresolved" or "unresolved" in states:
        return "unresolved"
    return "not_satisfied"


def check_trace(shape, trace):
    assert trace["kind"] == shape["kind"] and trace["span"] == shape["span"]
    children = shape.get("members", [])
    assert len(trace["children"]) == len(children)
    assert trace["leaf_id"] == shape.get("leaf_id")
    for original, observed in zip(children, trace["children"], strict=True):
        check_trace(original, observed)
    values = [item["value"] for item in trace["children"]]
    if shape["kind"] == "all_of":
        expected = ("not_satisfied" if "not_satisfied" in values else
                    "unresolved" if "unresolved" in values else "satisfied")
        assert trace["value"] == expected
    if shape["kind"] == "any_of":
        expected = ("satisfied" if "satisfied" in values else
                    "unresolved" if "unresolved" in values else "not_satisfied")
        assert trace["value"] == expected


def check_vector(name, case, vector, request, result):
    assert vector["expected_status"] == case["status"] == result["status"], name
    code = result["diagnostics"][0]["code"] if result["diagnostics"] else ""
    assert vector["invalid_classification"] == case["code"] == code, name
    if request is None:
        assert result["status"] == "rejected" and not result.get("rules")
        assert not result.get("selected_penalties") and not result.get("presumption_derivations")
        return
    assert [item["penalty_id"] for item in result["selected_penalties"]] == case["selected"]
    if result["status"] == "rejected":
        assert all(result[key] == [] for key in ("rules","presumption_derivations",
            "selected_penalties","penalty_selection_trace","selection_warnings")), name
        if vector["graph_kind"]:
            assert result["diagnostics"][0]["parameters"]["graph_kind"] == vector["graph_kind"]
        return
    assert result["fragment"] == "RegisteredPresumptionDerivations-v1"
    assert [item["presumption_id"] for item in result["presumption_derivations"]] == [
        item["presumption_id"] for item in request["presumptions"]], name
    assert [item["state"] for item in result["presumption_derivations"]] == case["route_states"]
    by_target = {}
    for original, observed in zip(request["presumptions"],
                                  result["presumption_derivations"], strict=True):
        assert observed["source_id"] == original["source_id"]
        assert observed["span"] == original["span"]
        for key in ("trigger", "rebuttal"):
            check_trace(original[key], observed[key])
            assert observed[key+"_value"] == observed[key]["value"]
        target = original["target_leaf_id"]
        by_target.setdefault(target, []).append(observed["state"])
    for observed in result["presumption_derivations"]:
        target = observed["target_leaf_id"]
        direct = projected(request["facts"][target]["proof_status"])
        assert observed["target_direct_satisfaction"] == direct
        assert observed["target_effective_satisfaction"] == expected_effective(
            direct, by_target[target])
        assert observed["target_effective_satisfaction"] == vector["expected_effective"][target]
    for rule in result["rules"]:
        assert [item["leaf_id"] for item in rule["proof_observations"]] == [
            edge["id"] for edge in rule["trace"] if edge["kind"] == "leaf"]
        for row in rule["proof_observations"]:
            leaf = row["leaf_id"]
            assert row["proof_status"] == request["facts"][leaf]["proof_status"]
            assert row["status_source"] == request["facts"][leaf]["status_source"]
            assert row["direct_satisfaction"] == projected(row["proof_status"])
            assert row["effective_satisfaction"] == row["satisfaction"]
            assert row["effective_satisfaction"] == expected_effective(
                row["direct_satisfaction"], by_target.get(leaf, []))
            assert row["effective_satisfaction"] == vector["expected_effective"][leaf]
            assert row["active_presumption_ids"] == [item["presumption_id"]
                for item in result["presumption_derivations"]
                if item["target_leaf_id"] == leaf and item["state"] == "active"]
            assert row["unresolved_presumption_ids"] == ([item["presumption_id"]
                for item in result["presumption_derivations"]
                if item["target_leaf_id"] == leaf and item["state"] == "unresolved"]
                if row["effective_satisfaction"] == "unresolved"
                and row["direct_satisfaction"] == "not_satisfied" else [])
    assert len(result["selected_penalties"]) == len({item["penalty_id"]
        for item in result["selected_penalties"]})
    for item in result["selected_penalties"]:
        assert [row["path"] for row in item["supporting_branches"]] == vector[
            "selected_support_paths"][item["penalty_id"]]
        assert [item["penalty_id"],item["term"]["term_id"]] in vector["term_roots"]
    if name == "RD38":
        assert [item["state"] for item in result["presumption_derivations"]] == [
            "active", "active"]  # duplicate shapes retain distinct technical routes
    if name == "RD39":
        assert result["rules"][0]["branches"][0]["reason"] == "defeated"
    if name == "RD41":
        assert result["penalty_selection_trace"][0]["result"] == "guard_unresolved"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    binary = parser.parse_args().executable.resolve()
    integrity()
    cases = json.loads((FIXTURES / "CASES.json").read_bytes())
    vectors = json.loads((FIXTURES / "PROOF-VECTORS.json").read_bytes())
    assert len(cases) == 77 and set(cases) == set(vectors)
    request_schema = json.loads((WORKSPACE / "schema/request.schema.json").read_bytes())
    result_schema = json.loads((WORKSPACE / "schema/result.schema.json").read_bytes())
    Draft202012Validator.check_schema(request_schema)
    Draft202012Validator.check_schema(result_schema)
    request_validator = Draft202012Validator(request_schema)
    result_validator = Draft202012Validator(result_schema)
    requests = {name: wire(FIXTURES / case["file"]) for name,case in cases.items()}
    for name,case in cases.items():
        if case["status"] != "rejected":
            request_validator.validate(json.loads(requests[name]))
    sequence = []
    for name,case in cases.items():
        sequence.append(name)
        if case["status"] == "rejected":
            sequence.append("RD01")
    sequence.extend(["RD08", "RD36", "RD39", "RD40", "RD59", "RD01"])
    completed = subprocess.run([str(binary)], input=b"".join(requests[name]
        for name in sequence), capture_output=True, check=True, timeout=120)
    assert not completed.stderr, completed.stderr
    lines = completed.stdout.splitlines(keepends=True)
    assert len(lines) == len(sequence), (len(lines),len(sequence))
    seen = {}
    for name,line in zip(sequence, lines, strict=True):
        assert line.endswith(b"\n") and line.count(b"\n") == 1
        result = json.loads(line)
        result_validator.validate(result)
        assert line == canonical(result), name
        assert seen.setdefault(name,line) == line, name
        request = json.loads(requests[name]) if cases[name]["file"].endswith(".json") else None
        check_vector(name,cases[name],vectors[name],request,result)
        if result["status"] != "rejected":
            digest = hashlib.sha256(canonical({key:request[key]
                for key in INPUT_KEYS}).rstrip(b"\n")).hexdigest()
            assert result["input_digest"] == digest, name
    print(f"presumption protocol: {len(cases)} fixtures, {len(sequence)} persistent "
          "requests, schemas, vectors, canonical bytes and regeneration passed")


if __name__ == "__main__":
    main()
