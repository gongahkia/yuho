"""Conformance matrix coverage for Yuho grammar constructs."""

from __future__ import annotations

import json
import re
from pathlib import Path


GRAMMAR_PATH = Path("src/tree-sitter-yuho/grammar.js")
MATRIX_PATH = Path("tests/fixtures/conformance/constructs.json")
GRAMMAR_METADATA_RULES = {"externals", "extras", "word", "conflicts", "inline"}


def _public_grammar_rules() -> set[str]:
    grammar = GRAMMAR_PATH.read_text(encoding="utf-8")
    rules = set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*\$\s*=>", grammar, re.M))
    return {
        rule
        for rule in rules
        if not rule.startswith("_") and rule not in GRAMMAR_METADATA_RULES
    }


def test_construct_matrix_covers_public_grammar_rules() -> None:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    constructs = matrix["constructs"]

    missing = _public_grammar_rules() - set(constructs)
    stale = set(constructs) - _public_grammar_rules()

    assert not missing, sorted(missing)
    assert not stale, sorted(stale)


def test_construct_matrix_rows_have_semantic_status_fields() -> None:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    required = matrix["required_fields"]

    incomplete: list[tuple[str, str]] = []
    for rule, row in matrix["constructs"].items():
        for field in required:
            value = row.get(field)
            if value in (None, "", []):
                incomplete.append((rule, field))

    assert not incomplete, incomplete
