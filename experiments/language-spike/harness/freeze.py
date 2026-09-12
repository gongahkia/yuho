#!/usr/bin/env python3
"""Freeze the shared language-spike inputs and independently expected outputs."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from yuho.ast import ASTBuilder, nodes
from yuho.eval import StatuteEvaluator, StructInstance, Value
from yuho.parser import get_parser
from yuho.services.analysis import analyze_source

ROOT = Path(__file__).resolve().parents[3]
SPIKE = ROOT / "experiments/language-spike"
FIXTURES = SPIKE / "fixtures"
TESTS = ROOT / "tests"
FRAGMENT = "ClosedBooleanBranches-v1"
PROTOCOL = "yuho.kernel-protocol/v1"
INPUT_SCHEMA = "yuho.kernel-input/v1"
RESULT_SCHEMA = "yuho.kernel-result/v1"
B06_SHA = "880553fca8fcea94e325ee2cfb48e5a985cc797f39a14cc6d3cedecfeb2ae4d2"
SOURCE_TESTS = {
    "alternatives": "test_sibling_subsection_leaves_are_alternative_branches",
    "nested": "test_nested_branch_inherits_ancestor_requirements_conjunctively",
    "definition": "test_definition_only_provision_is_not_an_empty_satisfied_offence",
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def source_in_test(file: Path, symbol: str) -> str:
    tree = ast.parse(file.read_text(encoding="utf-8"))
    matches = [item for item in ast.walk(tree) if isinstance(item, ast.FunctionDef) and item.name == symbol]
    assert len(matches) == 1, (file, symbol)
    assignments = [
        item.value.value
        for item in matches[0].body
        if isinstance(item, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "source" for target in item.targets)
        and isinstance(item.value, ast.Constant)
        and isinstance(item.value.value, str)
    ]
    assert len(assignments) == 1, (file, symbol)
    return assignments[0]


def span(location: Any) -> dict[str, int]:
    assert location is not None and location.offset is not None and location.end_offset is not None
    return {
        "start": location.offset,
        "end": location.end_offset,
        "start_line": location.line,
        "start_col": location.col,
        "end_line": location.end_line,
        "end_col": location.end_col,
    }


def requirement(member: Any, path: list[str]) -> dict[str, Any]:
    if isinstance(member, nodes.ElementNode):
        return {
            "kind": "leaf",
            "id": member.name,
            "path": path,
            "span": span(member.source_location),
        }
    if isinstance(member, nodes.ElementGroupNode):
        assert member.combinator in ("all_of", "any_of")
        return {
            "kind": "all" if member.combinator == "all_of" else "any",
            "id": f"group:{member.source_location.offset}",
            "path": path,
            "span": span(member.source_location),
            "members": [requirement(child, path) for child in member.members],
        }
    raise ValueError(f"unsupported legacy requirement: {type(member).__name__}")


def provision(node: Any, path: list[str]) -> dict[str, Any]:
    children = []
    for child in node.subsections:
        children.append(provision(child, [*path, child.number]))
    return {
        "id": "s" + "".join(path),
        "path": path,
        "span": span(node.source_location),
        "requirements": [requirement(item, path) for item in node.elements],
        "children": children,
        "definitions": bool(node.definitions),
    }


def source_object(path: str, text: str) -> dict[str, str]:
    return {"path": path, "text": text, "sha256": digest(text.encode("utf-8"))}


def request(case_id: str, source: dict[str, str], *, program: Any = None,
            facts: Any = None, parser_result: Any = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "protocol": PROTOCOL,
        "request_id": case_id,
        "operation": "validate" if parser_result is not None else "evaluate",
        "input_schema": INPUT_SCHEMA,
        "fragment": FRAGMENT,
        "source": source,
        "policy": {"reference_date": "2026-09-12", "max_nodes": 1024},
    }
    if parser_result is None:
        result["program"] = program
        result["facts"] = facts
    else:
        result["parser_result"] = parser_result
    return result


def input_digest(req: dict[str, Any]) -> str:
    fields = ("input_schema", "fragment", "source", "policy")
    inner = {key: req[key] for key in fields}
    if req["operation"] == "evaluate":
        inner["program"] = req["program"]
        inner["facts"] = req["facts"]
    else:
        inner["parser_result"] = req["parser_result"]
    return digest(canonical(inner))


def diagnostic(code: str, stage: str, path: str, location: Any,
               parameters: dict[str, str]) -> dict[str, Any]:
    return {
        "code": code,
        "stage": stage,
        "severity": "error",
        "path": path,
        "span": location,
        "parameters": parameters,
    }


def validate(req: dict[str, Any]) -> list[dict[str, Any]]:
    if req["protocol"] != PROTOCOL:
        return [diagnostic("KPROT001", "protocol", "/protocol", None,
                           {"received": req["protocol"]})]
    if req["operation"] == "validate":
        return []
    seen: set[str] = set()
    required: dict[str, tuple[dict[str, int], str]] = {}

    def visit_requirement(item: dict[str, Any], pointer: str) -> list[dict[str, Any]]:
        kind = item["kind"]
        if kind not in ("leaf", "all", "any"):
            return [diagnostic("KCAP001", "capability", pointer + "/kind",
                               item["span"], {"kind": kind})]
        identifier = item["id"]
        if identifier in seen:
            return [diagnostic("KINV002", "validate", pointer + "/id",
                               item["span"], {"id": identifier})]
        seen.add(identifier)
        if kind == "leaf":
            required[identifier] = (item["span"], "/facts/" + identifier)
            return []
        for index, child in enumerate(item["members"]):
            errors = visit_requirement(child, f"{pointer}/members/{index}")
            if errors:
                return errors
        return []

    def visit_provision(item: dict[str, Any], pointer: str) -> list[dict[str, Any]]:
        for index, value in enumerate(item["requirements"]):
            errors = visit_requirement(value, f"{pointer}/requirements/{index}")
            if errors:
                return errors
        for index, child in enumerate(item["children"]):
            errors = visit_provision(child, f"{pointer}/children/{index}")
            if errors:
                return errors
        return []

    errors = visit_provision(req["program"], "/program")
    if errors:
        return errors
    for identifier, (location, pointer) in required.items():
        if identifier not in req["facts"]:
            return [diagnostic("KINV001", "validate", pointer, location,
                               {"id": identifier})]
    return []


def branches(node: dict[str, Any], inherited: list[dict[str, Any]]) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    direct = [*inherited, *node["requirements"]]
    descendants = [
        branch
        for child in node["children"]
        for branch in branches(child, direct)
    ]
    if descendants:
        return descendants
    if direct:
        return [(node, direct)]
    return []


def evaluate_requirement(item: dict[str, Any], facts: dict[str, bool],
                         branch_id: str) -> tuple[bool, list[dict[str, Any]]]:
    kind = item["kind"]
    children: list[dict[str, Any]] = []
    values: list[bool] = []
    if kind == "leaf":
        value = facts[item["id"]]
    else:
        for child in item["members"]:
            child_value, child_trace = evaluate_requirement(child, facts, branch_id)
            values.append(child_value)
            children.extend(child_trace)
        value = all(values) if kind == "all" else any(values)
    record = {
        "branch": branch_id,
        "id": item["id"],
        "kind": kind,
        "path": item["path"],
        "span": item["span"],
        "value": "true" if value else "false",
        "children": [child["id"] for child in item.get("members", [])],
    }
    return value, [record, *children]


def expected(req: dict[str, Any]) -> dict[str, Any]:
    common: dict[str, Any] = {
        "protocol": PROTOCOL,
        "request_id": req["request_id"],
        "result_schema": RESULT_SCHEMA,
        "fragment": FRAGMENT,
        "input_digest": input_digest(req),
        "branches": [],
        "trace": [],
        "diagnostics": [],
        "provision_kind": "none",
    }
    errors = validate(req)
    if errors:
        common["status"] = "rejected"
        common["diagnostics"] = errors
        return common
    if req["operation"] == "validate":
        parsed = req["parser_result"]
        common["status"] = "true" if parsed["accepted"] else "rejected"
        common["diagnostics"] = parsed["diagnostics"]
        return common
    leaf_branches = branches(req["program"], [])
    common["provision_kind"] = "executable" if leaf_branches else "definition_only"
    overall = False
    for node, requirements in leaf_branches:
        pieces = [evaluate_requirement(item, req["facts"], node["id"]) for item in requirements]
        value = all(result for result, _ in pieces)
        overall |= value
        trace = [record for _, subtrace in pieces for record in subtrace]
        common["trace"].extend(trace)
        common["branches"].append({
            "id": node["id"],
            "path": node["path"],
            "status": "true" if value else "false",
            "trace_ids": [record["id"] for record in trace],
        })
    common["status"] = "true" if overall else "false"
    return common


def parser_result(source: str, path: str) -> dict[str, Any]:
    analysis = analyze_source(source, file=path, run_semantic=False)
    diagnostics = []
    for error in analysis.errors:
        if error.stage != "parse":
            continue
        diagnostics.append(diagnostic(
            error.error_code, error.stage, path,
            span(error.location) if error.location is not None else None,
            {"node_type": error.node_type or ""},
        ))
    return {"accepted": not analysis.parse_errors, "diagnostics": diagnostics,
            "source_version": "yuho-5.1"}


def main() -> None:
    assert not (FIXTURES / "MANIFEST.json").exists(), "fixtures already frozen"
    section_sources = {
        name: source_in_test(TESTS / "test_runtime_subsections.py", symbol)
        for name, symbol in SOURCE_TESTS.items()
    }
    p04 = source_in_test(TESTS / "test_hardening.py",
                         "test_comment_before_typed_struct_literal_is_rejected")
    sources = {
        **section_sources,
        "closed-boolean": "a\nb\nc\n",
        "P01": 'string label := "café"\n',
        "P02": 'statute 1 "Café" {\n',
        "P03": 'statute 1 "Bad" {',
        "P04": p04,
    }
    source_paths = {
        name: f"experiments/language-spike/fixtures/sources/{name}.yh"
        for name in sources
    }
    for name, text in sources.items():
        (ROOT / source_paths[name]).write_bytes(text.encode("utf-8"))
    assert digest(sources["closed-boolean"].encode()) == B06_SHA

    programs = {}
    statutes = {}
    for name in SOURCE_TESTS:
        text = sources[name]
        parsed = get_parser().parse(text, file=source_paths[name])
        assert parsed.is_valid, (name, parsed.errors)
        module = ASTBuilder(text, file=source_paths[name]).build(parsed.root_node)
        assert len(module.statutes) == 1
        statute = module.statutes[0]
        statutes[name] = statute
        programs[name] = provision(statute, [statute.section_number])

    closed_span = {"start": 0, "end": 5, "start_line": 1, "start_col": 1,
                   "end_line": 3, "end_col": 2}
    any_span = {"start": 2, "end": 5, "start_line": 2, "start_col": 1,
                "end_line": 3, "end_col": 2}
    def leaf(name: str, start: int, line: int) -> dict[str, Any]:
        return {"kind": "leaf", "id": name, "path": ["S"],
                "span": {"start": start, "end": start + 1, "start_line": line,
                         "start_col": 1, "end_line": line, "end_col": 2}}
    closed = {
        "id": "synthetic:S", "path": ["S"], "span": closed_span, "definitions": False,
        "children": [],
        "requirements": [{
            "kind": "all", "id": "group:all", "path": ["S"], "span": closed_span,
            "members": [
                leaf("a", 0, 1),
                {"kind": "any", "id": "group:any", "path": ["S"], "span": any_span,
                 "members": [leaf("b", 2, 2), leaf("c", 4, 3)]},
            ],
        }],
    }
    cases = {
        "B01": request("B01", source_object(source_paths["alternatives"], sources["alternatives"]),
                       program=programs["alternatives"], facts={"first": True, "second": False}),
        "B02": request("B02", source_object(source_paths["alternatives"], sources["alternatives"]),
                       program=programs["alternatives"], facts={"first": False, "second": False}),
        "B03": request("B03", source_object(source_paths["nested"], sources["nested"]),
                       program=programs["nested"], facts={"common": False, "first": True, "second": False}),
        "B04": request("B04", source_object(source_paths["nested"], sources["nested"]),
                       program=programs["nested"], facts={"common": True, "first": False, "second": True}),
        "B05": request("B05", source_object(source_paths["definition"], sources["definition"]),
                       program=programs["definition"], facts={}),
        "B06": request("B06", source_object(source_paths["closed-boolean"], sources["closed-boolean"]),
                       program=closed, facts={"a": True, "b": False, "c": True}),
        "B07": request("B07", source_object(source_paths["closed-boolean"], sources["closed-boolean"]),
                       program=closed, facts={"a": True, "b": False, "c": False}),
    }
    cases["R01"] = copy.deepcopy(cases["B06"])
    cases["R01"]["request_id"] = "R01"
    del cases["R01"]["facts"]["c"]
    cases["R02"] = copy.deepcopy(cases["B06"])
    cases["R02"]["request_id"] = "R02"
    cases["R02"]["program"]["requirements"][0]["members"][1]["members"][1]["id"] = "b"
    cases["R03"] = copy.deepcopy(cases["B06"])
    cases["R03"]["request_id"] = "R03"
    cases["R03"]["program"]["requirements"][0]["members"][1]["kind"] = "opaque"
    cases["R04"] = copy.deepcopy(cases["B06"])
    cases["R04"]["request_id"] = "R04"
    cases["R04"]["protocol"] = "yuho.kernel-protocol/v2"
    for case_id in ("P01", "P02", "P03", "P04"):
        path = source_paths[case_id]
        text = sources[case_id]
        cases[case_id] = request(case_id, source_object(path, text),
                                 parser_result=parser_result(text, path))

    assert [expected(cases[case])["status"] for case in ("B01", "B02", "B03", "B04", "B05", "B06", "B07")] == [
        "true", "false", "false", "true", "false", "true", "false"
    ]
    assert [expected(cases[case])["diagnostics"][0]["code"] for case in ("R01", "R02", "R03", "R04")] == [
        "KINV001", "KINV002", "KCAP001", "KPROT001"
    ]
    assert [expected(cases[case])["status"] for case in ("P01", "P02", "P03", "P04")] == [
        "true", "rejected", "rejected", "rejected"
    ]
    for case_id, name, facts in (
        ("B01", "alternatives", {"first": True, "second": False}),
        ("B02", "alternatives", {"first": False, "second": False}),
        ("B03", "nested", {"common": False, "first": True, "second": False}),
        ("B04", "nested", {"common": True, "first": False, "second": True}),
        ("B05", "definition", {}),
    ):
        actual = StatuteEvaluator().evaluate(
            statutes[name],
            StructInstance("Facts", {key: Value(raw=value, type_tag="bool")
                                     for key, value in facts.items()}),
        )
        assert actual.overall_satisfied is (expected(cases[case_id])["status"] == "true"), case_id

    manifest: dict[str, Any] = {
        "repository_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protocol": PROTOCOL, "input_schema": INPUT_SCHEMA, "result_schema": RESULT_SCHEMA,
        "fragment": FRAGMENT, "cases": {}, "sources": {},
        "source_test_symbols": SOURCE_TESTS,
        "parser_test_symbol": "test_comment_before_typed_struct_literal_is_rejected",
    }
    for name, path in source_paths.items():
        manifest["sources"][name] = {"path": path, "sha256": digest((ROOT / path).read_bytes())}
    for case_id, req in sorted(cases.items()):
        req_bytes = canonical(req) + b"\n"
        out_bytes = canonical(expected(req)) + b"\n"
        (FIXTURES / "requests" / f"{case_id}.json").write_bytes(req_bytes)
        (FIXTURES / "expected" / f"{case_id}.json").write_bytes(out_bytes)
        manifest["cases"][case_id] = {
            "request_sha256": digest(req_bytes),
            "expected_sha256": digest(out_bytes),
            "input_digest": expected(req)["input_digest"],
        }
    (FIXTURES / "MANIFEST.json").write_bytes(canonical(manifest) + b"\n")
    print("frozen", len(cases), "cases at", manifest["repository_head"])


if __name__ == "__main__":
    main()
