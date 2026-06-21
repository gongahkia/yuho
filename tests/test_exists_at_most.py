"""Bounded quantification primitive coverage."""

from __future__ import annotations

import json

import pytest

from yuho.ast import ExistsAtMostNode
from yuho.eval.interpreter import Interpreter, InterpreterError
from yuho.services.analysis import analyze_source
from yuho.transpile import JSONTranspiler


SOURCE = """
statute 1 "Sentencing aggravator" {
    elements {
        circumstance limited_repetition := exists_at_most 2 within 30 days;
    }
}
"""


def test_exists_at_most_lowers_to_ast_and_type_checks():
    result = analyze_source(SOURCE, run_semantic=True)

    assert not result.parse_errors
    assert result.ast is not None
    assert result.semantic_summary is not None
    assert not result.semantic_summary.has_errors
    expr = result.ast.statutes[0].elements[0].description
    assert isinstance(expr, ExistsAtMostNode)
    assert expr.limit.value == 2
    assert expr.window.days == 30


def test_exists_at_most_serializes_to_json():
    result = analyze_source(SOURCE, run_semantic=False)
    assert result.ast is not None

    payload = json.loads(JSONTranspiler(include_locations=False).transpile(result.ast))
    expr = payload["statutes"][0]["elements"][0]["description"]
    assert expr["_type"] == "ExistsAtMostNode"
    assert expr["limit"]["value"] == 2
    assert expr["window"]["days"] == 30


def test_exists_at_most_runtime_fails_fast_until_event_facts_exist():
    result = analyze_source(SOURCE, run_semantic=False)
    assert result.ast is not None
    expr = result.ast.statutes[0].elements[0].description

    with pytest.raises(InterpreterError, match="event fact support"):
        Interpreter().visit_exists_at_most(expr)
