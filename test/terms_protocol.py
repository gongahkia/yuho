"""Fifth-fragment wire, schema, vector, regeneration and recovery checks."""

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
FIXTURES = WORKSPACE / "test/term-fixtures"
GP = WORKSPACE / "test/penalty-fixtures"
INPUT_KEYS = ("input_schema", "fragment", "sources", "registry",
              "root_rule", "facts", "policy")


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode()


def wire_bytes(path):
    raw = path.read_bytes()
    if path.suffix == ".json":
        return canonical(json.loads(raw))
    return raw.replace(b"\n", b"") + b"\n"


def manifest_and_regeneration():
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_bytes())
    assert manifest["format"] == "yuho.pt-fixtures/v1"
    files = [FIXTURES / name for name in ("CASES.json", "PROOF-VECTORS.json",
             "MIGRATION-PROBES.json", "generate.py")]
    files += sorted((FIXTURES / "requests").iterdir())
    actual = {str(path.relative_to(FIXTURES)):
              hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    assert actual == manifest["files"], "PT manifest mismatch"
    with tempfile.TemporaryDirectory(prefix="yuho-pt-regeneration-") as folder:
        target = Path(folder) / "test/term-fixtures"
        sibling = target.parent / "penalty-fixtures"
        sibling.mkdir(parents=True)
        shutil.copy2(GP / "CASES.json", sibling / "CASES.json")
        shutil.copy2(GP / "PROOF-VECTORS.json", sibling / "PROOF-VECTORS.json")
        shutil.copytree(GP / "requests", sibling / "requests")
        target.mkdir()
        shutil.copy2(FIXTURES / "generate.py", target / "generate.py")
        subprocess.run([sys.executable, str(target / "generate.py")], check=True)
        for path in files:
            assert path.read_bytes() == (target / path.relative_to(FIXTURES)).read_bytes(), path
        assert (FIXTURES / "MANIFEST.json").read_bytes() == (target / "MANIFEST.json").read_bytes()


def term_nodes(term):
    yield term["term_id"]
    for child in term.get("terms", []):
        yield from term_nodes(child)


def term_edges(term):
    yield from ([term["term_id"], child["term_id"], position]
                for position, child in enumerate(term.get("terms", [])))
    for child in term.get("terms", []):
        yield from term_edges(child)


def check_vector(name, case, vector, result):
    assert vector["status"] == case["status"] == result["status"], name
    code = result["diagnostics"][0]["code"] if result["diagnostics"] else ""
    assert code == case["code"] == vector["invalid_classification"], name
    assert vector["selected_ids"] == case["selected"], name
    assert vector["declaration_order"] == [item["penalty_id"]
            for item in vector["declarations"]] or name == "PT45", name
    assert vector["term_preorder"] == [identifier for item in vector["declarations"]
            for identifier in term_nodes(item["term"])], name
    assert vector["combinator_edges"] == [edge for item in vector["declarations"]
            for edge in term_edges(item["term"])], name
    if result["status"] == "rejected":
        assert not result.get("rules") and not result.get("selected_penalties"), name
        assert not result.get("penalty_selection_trace"), name
        return
    assert not result["diagnostics"], name
    selected = result["selected_penalties"]
    assert [item["penalty_id"] for item in selected] == vector["selected_ids"], name
    by_id = {item["penalty_id"]: item for item in vector["declarations"]}
    assert len(by_id) == len(vector["declarations"]), name
    for item in selected:
        expected = by_id[item["penalty_id"]]
        assert item["term"] == expected["canonical_term"], name
        assert json.dumps(item["term"], sort_keys=True, ensure_ascii=False,
                          separators=(",", ":")) == expected["canonical_json"], name
        assert item["term"]["term_id"] == vector["selected_term_ids"][item["penalty_id"]], name
        assert item["span"] == expected["span"], name
        assert [support["path"] for support in item["supporting_branches"]] == \
            vector["supporting_paths"][item["penalty_id"]], name
    assert [[row["penalty_id"], row["branch_id"], row["result"]]
            for row in result["penalty_selection_trace"]] == vector["selection_trace"], name
    assert [row["penalty_ids"] for row in result["selection_warnings"]] == vector["warnings"], name
    root = next(rule for rule in result["rules"] if rule["id"] == result["root_rule"])
    assert [{"branch_id": row["id"], "path": row["path"], "status": row["status"],
             "reason": row["reason"]} for row in root["branches"]] == vector["branch_statuses"], name


def strip_terms(program):
    program = dict(program)
    program["penalties"] = [{key: value for key, value in declaration.items()
                             if key != "term"} for declaration in program["penalties"]]
    program["children"] = [strip_terms(child) for child in program["children"]]
    return program


def compare_fourth(executable, request, fifth):
    fourth_request = dict(request)
    fourth_request["fragment"] = "GuardedPenaltySelection-v1"
    fourth_request["registry"] = [{**rule, "program": strip_terms(rule["program"])}
                                  for rule in request["registry"]]
    fourth = json.loads(subprocess.run([str(executable)], input=canonical(fourth_request),
                                       capture_output=True, check=True, timeout=10).stdout)
    assert fourth["status"] == fifth["status"]
    assert fourth["rules"] == fifth["rules"]
    for field in ("penalty_selection_trace", "selection_warnings"):
        assert fourth[field] == fifth[field], field
    assert fourth["selected_penalties"] == [
        {key: value for key, value in row.items() if key != "term"}
        for row in fifth["selected_penalties"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve()
    manifest_and_regeneration()
    cases = json.loads((FIXTURES / "CASES.json").read_bytes())
    vectors = json.loads((FIXTURES / "PROOF-VECTORS.json").read_bytes())
    assert len(cases) == 68 and set(cases) == set(vectors)
    req_schema = json.loads((WORKSPACE / "schema/request.schema.json").read_bytes())
    res_schema = json.loads((WORKSPACE / "schema/result.schema.json").read_bytes())
    Draft202012Validator.check_schema(req_schema)
    Draft202012Validator.check_schema(res_schema)
    request_validator = Draft202012Validator(req_schema)
    result_validator = Draft202012Validator(res_schema)
    requests = {name: wire_bytes(FIXTURES / case["request_file"])
                for name, case in cases.items()}
    for name, case in cases.items():
        if case["status"] != "rejected":
            request_validator.validate(json.loads(requests[name]))
    sequence = []
    for name, case in cases.items():
        sequence.append(name)
        if case["status"] == "rejected":
            sequence.append("PT01")
    sequence.extend(["PT03", "PT17", "PT19", "PT01"])
    completed = subprocess.run([str(executable)],
                               input=b"".join(requests[name] for name in sequence),
                               capture_output=True, check=True, timeout=120)
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
            assert result["fragment"] == "PenaltyTerms-v1", name
            compare_fourth(executable, request, result)
    print(f"terms protocol: {len(cases)} fixtures, {len(sequence)} persistent requests, "
          "schemas, proof-neutral vectors, manifest/regeneration, canonical bytes, "
          "prior-selection invariance and rejection recovery passed")


if __name__ == "__main__":
    main()
