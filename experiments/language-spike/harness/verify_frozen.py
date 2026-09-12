#!/usr/bin/env python3
"""Read-only integrity, shape and provenance checks for the frozen spike corpus."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SPIKE = ROOT / "experiments/language-spike"
FIXTURES = SPIKE / "fixtures"
CASES = {f"{prefix}{index:02d}" for prefix, last in (("B", 7), ("R", 4), ("P", 4))
         for index in range(1, last + 1)}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def assert_keys(value: Any, expected: set[str]) -> None:
    assert isinstance(value, dict) and set(value) == expected, (value, expected)


def check_span(value: Any) -> None:
    assert_keys(value, {"start", "end", "start_line", "start_col", "end_line", "end_col"})
    assert all(type(item) is int for item in value.values())
    assert 0 <= value["start"] <= value["end"]
    assert value["start_line"] >= 1 and value["end_line"] >= value["start_line"]
    assert value["start_col"] >= 1 and value["end_col"] >= 1


def check_req(value: Any) -> None:
    expected = {"kind", "id", "path", "span"}
    if "members" in value:
        expected.add("members")
    assert_keys(value, expected)
    assert isinstance(value["kind"], str) and isinstance(value["id"], str)
    assert isinstance(value["path"], list) and all(isinstance(part, str) for part in value["path"])
    check_span(value["span"])
    if "members" in value:
        assert isinstance(value["members"], list)
        for child in value["members"]:
            check_req(child)


def check_provision(value: Any) -> None:
    assert_keys(value, {"id", "path", "span", "definitions", "requirements", "children"})
    assert isinstance(value["id"], str) and isinstance(value["path"], list)
    assert type(value["definitions"]) is bool
    check_span(value["span"])
    for item in value["requirements"]:
        check_req(item)
    for child in value["children"]:
        check_provision(child)


def check_diag(value: Any) -> None:
    assert_keys(value, {"code", "stage", "severity", "path", "span", "parameters"})
    assert all(isinstance(value[key], str) for key in ("code", "stage", "severity", "path"))
    assert value["severity"] in ("error", "warning", "info")
    assert isinstance(value["parameters"], dict)
    assert all(isinstance(v, str) for v in value["parameters"].values())
    if value["span"] is not None:
        check_span(value["span"])


def check_request(value: Any) -> None:
    common = {"protocol", "request_id", "operation", "input_schema", "fragment", "source", "policy"}
    operation = value["operation"]
    assert operation in ("evaluate", "validate")
    assert_keys(value, common | ({"program", "facts"} if operation == "evaluate" else {"parser_result"}))
    assert value["input_schema"] == "yuho.kernel-input/v1"
    assert value["fragment"] == "ClosedBooleanBranches-v1"
    assert_keys(value["source"], {"path", "text", "sha256"})
    assert value["source"]["sha256"] == sha(value["source"]["text"].encode("utf-8"))
    assert_keys(value["policy"], {"reference_date", "max_nodes"})
    assert value["policy"]["reference_date"] == "2026-09-12"
    assert value["policy"]["max_nodes"] == 1024
    if operation == "evaluate":
        check_provision(value["program"])
        assert isinstance(value["facts"], dict)
        assert all(type(fact) is bool for fact in value["facts"].values())
    else:
        assert_keys(value["parser_result"], {"accepted", "diagnostics", "source_version"})
        assert type(value["parser_result"]["accepted"]) is bool
        assert value["parser_result"]["source_version"] == "yuho-5.1"
        for item in value["parser_result"]["diagnostics"]:
            check_diag(item)


def check_result(value: Any) -> None:
    assert_keys(value, {"protocol", "request_id", "result_schema", "fragment", "input_digest",
                        "status", "provision_kind", "branches", "trace", "diagnostics"})
    assert value["protocol"] == "yuho.kernel-protocol/v1"
    assert value["result_schema"] == "yuho.kernel-result/v1"
    assert value["fragment"] == "ClosedBooleanBranches-v1"
    assert value["status"] in ("true", "false", "rejected")
    assert value["provision_kind"] in ("none", "executable", "definition_only")
    assert re.fullmatch(r"[0-9a-f]{64}", value["input_digest"])
    for branch in value["branches"]:
        assert_keys(branch, {"id", "path", "status", "trace_ids"})
        assert branch["status"] in ("true", "false")
    for item in value["trace"]:
        assert_keys(item, {"branch", "id", "kind", "path", "span", "value", "children"})
        assert item["kind"] in ("leaf", "all", "any")
        assert item["value"] in ("true", "false")
        check_span(item["span"])
    for item in value["diagnostics"]:
        check_diag(item)


def test_symbols(manifest: dict[str, Any]) -> None:
    for symbol in manifest["source_test_symbols"].values():
        tree = ast.parse((ROOT / "tests/test_runtime_subsections.py").read_text())
        assert sum(isinstance(item, ast.FunctionDef) and item.name == symbol
                   for item in ast.walk(tree)) == 1, symbol
    tree = ast.parse((ROOT / "tests/test_hardening.py").read_text())
    symbol = manifest["parser_test_symbol"]
    assert sum(isinstance(item, ast.FunctionDef) and item.name == symbol
               for item in ast.walk(tree)) == 1, symbol
    for name in ("test_incremental_edit_points_count_utf8_columns_as_bytes",):
        tree = ast.parse((ROOT / "tests/test_parser_incremental.py").read_text())
        assert any(isinstance(item, ast.FunctionDef) and item.name == name
                   for item in ast.walk(tree))
    tree = ast.parse((ROOT / "tests/test_lsp_server.py").read_text())
    assert any(isinstance(item, ast.FunctionDef) and item.name == "test_server_parse_source_caches_parse_errors"
               for item in ast.walk(tree))


def doc_links() -> None:
    for document in (ROOT / "docs/rewrite").glob("*.md"):
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", text):
            target = target.split("#", 1)[0]
            if target and not re.match(r"^[a-z]+://", target):
                assert (document.parent / target).exists(), (document, target)


def main() -> None:
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_bytes())
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["repository_head"])
    assert set(manifest["cases"]) == CASES
    assert {item.stem for item in (FIXTURES / "requests").glob("*.json")} == CASES
    assert {item.stem for item in (FIXTURES / "expected").glob("*.json")} == CASES
    for name in ("request", "result"):
        json.loads((SPIKE / "schema" / f"{name}.schema.json").read_bytes())
    for name, record in manifest["sources"].items():
        source_path = ROOT / record["path"]
        assert source_path.is_file() and sha(source_path.read_bytes()) == record["sha256"], name
    assert manifest["sources"]["closed-boolean"]["sha256"] == (
        "880553fca8fcea94e325ee2cfb48e5a985cc797f39a14cc6d3cedecfeb2ae4d2"
    )
    for case_id in sorted(CASES):
        request_bytes = (FIXTURES / "requests" / f"{case_id}.json").read_bytes()
        expected_bytes = (FIXTURES / "expected" / f"{case_id}.json").read_bytes()
        record = manifest["cases"][case_id]
        assert sha(request_bytes) == record["request_sha256"], case_id
        assert sha(expected_bytes) == record["expected_sha256"], case_id
        req = json.loads(request_bytes)
        result = json.loads(expected_bytes)
        assert request_bytes == canonical(req) + b"\n", case_id
        assert expected_bytes == canonical(result) + b"\n", case_id
        check_request(req)
        check_result(result)
        assert req["request_id"] == result["request_id"] == case_id
        assert req["source"]["text"].encode("utf-8") == (ROOT / req["source"]["path"]).read_bytes()
        inner_keys = {"input_schema", "fragment", "source", "policy"}
        inner_keys |= {"program", "facts"} if req["operation"] == "evaluate" else {"parser_result"}
        assert result["input_digest"] == record["input_digest"] == sha(canonical({
            key: req[key] for key in inner_keys
        })), case_id
    test_symbols(manifest)
    doc_links()
    print(f"frozen fixtures: {len(CASES)} canonical requests/responses, source hashes, schemas, test symbols and links OK")


if __name__ == "__main__":
    main()
