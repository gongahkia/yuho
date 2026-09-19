"""Closed GP requests/results, proof-neutral vectors and persistent recovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

WORKSPACE = Path(__file__).resolve().parents[1]
FIXTURES = WORKSPACE / "test/penalty-fixtures"
sys.path.insert(0, str(FIXTURES))
from legacy_adapter import project  # noqa: E402


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode()


def verify_manifest() -> None:
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_bytes())
    assert manifest["schema"] == "yuho.penalty-fixture-manifest/v1"
    paths = [FIXTURES / name for name in (
        "CASES.json", "PROOF-VECTORS.json", "generate.py", "legacy_adapter.py")]
    paths.extend(sorted((FIXTURES / "requests").iterdir()))
    actual = {str(path.relative_to(FIXTURES)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in paths}
    assert actual == manifest["files"], "penalty fixture manifest mismatch"


def verify_regeneration() -> None:
    with tempfile.TemporaryDirectory(prefix="yuho-gp-fixtures-") as folder:
        sibling = Path(folder) / "test"
        source = sibling / "typed-fixtures" / "requests"
        source.mkdir(parents=True)
        for path in (WORKSPACE / "test/typed-fixtures/requests").iterdir():
            shutil.copy2(path, source / path.name)
        target = sibling / "penalty-fixtures"
        target.mkdir()
        for name in ("generate.py", "legacy_adapter.py"):
            shutil.copy2(FIXTURES / name, target / name)
        subprocess.run([sys.executable, str(target / "generate.py")], check=True)
        for expected in [FIXTURES / name for name in (
            "CASES.json", "PROOF-VECTORS.json", "MANIFEST.json")]:
            assert expected.read_bytes() == (target / expected.name).read_bytes(), expected
        for expected in sorted((FIXTURES / "requests").iterdir()):
            assert expected.read_bytes() == (target / "requests" / expected.name).read_bytes(), expected


def check_result(name: str, case: dict, vector: dict, request: bytes,
                 line: bytes, validator: Draft202012Validator) -> None:
    assert line.endswith(b"\n") and line.count(b"\n") == 1, name
    result = json.loads(line)
    try:
        validator.validate(result)
    except ValidationError as issue:
        details = [(part.json_path, part.message[:100]) for part in issue.context[:4]]
        raise AssertionError((name, details or [(issue.json_path,
                                                  issue.message[:100])])) from None
    assert line == canonical(result), f"noncanonical output: {name}"
    assert result["status"] == case["status"] == vector["expected_status"], name
    code = result["diagnostics"][0]["code"] if result["diagnostics"] else ""
    stage = result["diagnostics"][0]["stage"] if result["diagnostics"] else ""
    assert (code, stage) == (case["code"], case["stage"]), name
    assert code == vector["invalid_classification"], name
    if name != "GP34":
        assert result["fragment"] == "GuardedPenaltySelection-v1", name
        projected = json.loads(request)
        keys = ("input_schema", "fragment", "sources", "registry",
                "root_rule", "facts", "policy")
        digest = hashlib.sha256(canonical({key: projected[key] for key in keys}).rstrip(
            b"\n")).hexdigest()
        assert result["input_digest"] == digest, name
    if result["status"] == "rejected":
        assert not result.get("rules") and not result.get("selected_penalties"), name
        assert not result.get("penalty_selection_trace") and not result.get(
            "selection_warnings"), name
        return
    assert not result["diagnostics"], name
    assert case["selected"] == vector["selected_id_order"], name
    assert [item["penalty_id"] for item in result["selected_penalties"]] == case[
        "selected"], name
    selected = {item["penalty_id"]: item for item in result["selected_penalties"]}
    assert len(selected) == len(result["selected_penalties"]), name
    for identifier, paths in case["supports"].items():
        assert [item["path"] for item in selected[identifier]["supporting_branches"]] == paths, name
    assert case["supports"] == vector["supporting_paths"], name
    trace = result["penalty_selection_trace"]
    if case["trace"]:
        assert [[item["penalty_id"], item["branch_id"], item["result"]]
                for item in trace] == case["trace"] == vector["ordered_trace"], name
    assert case["warnings"] == vector["warning_penalty_ids"], name
    assert [item["penalty_ids"] for item in result["selection_warnings"]] == case[
        "warnings"], name
    assert all(item["code"] == "KSEL001" and item["stage"] == "select_penalties"
               and item["severity"] == "warning" for item in result["selection_warnings"]), name
    for item in result["selected_penalties"]:
        assert len(item["supporting_branches"]) == sum(
            edge["penalty_id"] == item["penalty_id"] and edge["result"] == "selected"
            for edge in trace), name
    declarations = {item["penalty_id"]: item for item in vector["declarations"]}
    for item in result["selected_penalties"]:
        declaration = declarations[item["penalty_id"]]
        for field in ("source_id", "span", "guard", "declaring_provision_path",
                      "declaration_index"):
            assert item[field] == declaration[field], (name, field)
    root = next(rule for rule in result["rules"] if rule["id"] == result["root_rule"])
    branch = {item["id"]: item for item in root["branches"]}
    assert [{"branch_id": item["id"], "path": item["path"],
             "status": item["status"], "reason": item["reason"]}
            for item in root["branches"]] == vector["final_root_branches"], name
    assert [{"paths": item["overlapping_branch_paths"],
             "guard_leaf_ids": item["guard_leaf_ids"]}
            for item in result["selection_warnings"]] == vector["overlap_warnings"], name
    leaf_trace = {(item["branch"], item["id"]): item["value"] for item in root["trace"]
                  if item["kind"] == "leaf"}
    for item in trace:
        declaration = declarations[item["penalty_id"]]
        final = branch[item["branch_id"]]
        assert (item["branch_status"], item["branch_reason"], item["branch_path"]) == (
            final["status"], final["reason"], final["path"]), name
        assert item["origin"] == ("direct" if declaration[
            "declaring_provision_path"] == item["branch_path"] else "inherited"), name
        if final["status"] == "true" and declaration["guard"]["kind"] == "leaf_true":
            expected = leaf_trace[(item["branch_id"], declaration["guard"]["leaf_id"])]
            assert item["guard_result"] == expected, name
        else:
            assert item["guard_result"] == "not_evaluated", name
    for item in result["selected_penalties"]:
        for support in item["supporting_branches"]:
            assert branch[support["branch_id"]]["status"] == "true", name
            matching = [edge for edge in trace if edge["penalty_id"] == item["penalty_id"]
                        and edge["branch_id"] == support["branch_id"]
                        and edge["result"] == "selected"]
            assert len(matching) == 1 and matching[0]["branch_path"] == support["path"], name
            assert matching[0]["origin"] == support["origin"], name
            assert support["guard_result"] == ({"true": True, "false": False}.get(
                matching[0]["guard_result"])), name


def verify_adapter() -> None:
    span = {"start": 0, "end": 1, "start_line": 1, "start_col": 1,
            "end_line": 1, "end_col": 2}
    projected = project([{"source_id": "src:main", "span": span, "guard": "rash"}],
                        ("root",), {"rash": "f:rash"})
    assert projected.declarations[0]["penalty_id"] == "pen:root:0"
    assert projected.declarations[0]["guard"]["leaf_id"] == "f:rash"
    assert projected.notices and not projected.rejections
    assert project([{"source_id": "src:main", "span": span, "guard": "unknown"}],
                   ("root",), {}).rejections
    assert project([{"source_id": "src:main", "span": span, "fine": 100}],
                   ("root",), {}).rejections


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    arguments = parser.parse_args()
    verify_manifest()
    verify_regeneration()
    verify_adapter()
    cases = json.loads((FIXTURES / "CASES.json").read_bytes())
    vectors = {item["case"]: item for item in json.loads(
        (FIXTURES / "PROOF-VECTORS.json").read_bytes())}
    assert len(cases) == 49 and set(cases) == set(vectors)
    request_schema = json.loads((WORKSPACE / "schema/request.schema.json").read_bytes())
    result_schema = json.loads((WORKSPACE / "schema/result.schema.json").read_bytes())
    Draft202012Validator.check_schema(request_schema)
    Draft202012Validator.check_schema(result_schema)
    req_validator = Draft202012Validator(request_schema)
    res_validator = Draft202012Validator(result_schema)
    requests = {name: (FIXTURES / item["request_file"]).read_bytes()
                for name, item in cases.items()}
    for name, case in cases.items():
        if case["status"] != "rejected":
            try:
                req_validator.validate(json.loads(requests[name]))
            except ValidationError as issue:
                details = [(part.json_path, part.message[:100]) for part in issue.context[:4]]
                raise AssertionError((name, details or [(issue.json_path,
                                                          issue.message[:100])])) from None
    sequence = []
    for name, case in cases.items():
        sequence.append(name)
        if case["status"] == "rejected":
            sequence.append("GP01")
    sequence.extend(["GP13", "GP14", "GP38", "GP01"])
    payload = b"".join(requests[name].rstrip(b"\n") + b"\n" for name in sequence)
    completed = subprocess.run([str(arguments.executable.resolve())], input=payload,
                               capture_output=True, check=True, timeout=90)
    assert not completed.stderr, completed.stderr
    lines = completed.stdout.splitlines(keepends=True)
    assert len(lines) == len(sequence), (len(lines), len(sequence))
    seen: dict[str, bytes] = {}
    for name, line in zip(sequence, lines, strict=True):
        assert line == seen.setdefault(name, line), f"nondeterministic bytes: {name}"
        check_result(name, cases[name], vectors[name], requests[name], line, res_validator)
    print(f"penalty protocol: {len(cases)} fixtures, {len(sequence)} persistent requests, "
          "schemas, vectors, deterministic bytes and recovery passed")


if __name__ == "__main__":
    main()
