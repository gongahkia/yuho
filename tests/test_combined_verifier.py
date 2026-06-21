from __future__ import annotations

import json
import logging

from yuho.ast import ASTBuilder
from yuho.parser import get_parser
from yuho.verify.alloy import AlloyCounterexample
from yuho.verify.combined import CombinedVerifier
from yuho.verify.z3_solver import Z3Diagnostic


SOURCE = """
statute 1 "Demo" {
    elements {
        actus_reus act := "act";
    }
}
"""


def _parse_source(source: str):
    parser = get_parser()
    result = parser.parse(source, "<test>")
    builder = ASTBuilder(result.source, "<test>")
    return builder.build(result.root_node)


class _AlloyAnalyzer:
    def __init__(self, results):
        self.results = results

    def is_available(self):
        return True

    def analyze(self, model):
        return self.results


class _Z3Solver:
    def __init__(self, diagnostics):
        self.diagnostics = diagnostics

    def is_available(self):
        return True

    def check_statute_consistency(self, ast):
        return (all(d.passed for d in self.diagnostics), self.diagnostics)


def test_combined_verifier_logs_fixture_disagreement_as_json(caplog):
    verifier = CombinedVerifier()
    verifier.alloy_analyzer = _AlloyAnalyzer(
        [AlloyCounterexample("alloy_check", violated=False, message="valid")]
    )
    verifier.z3_solver = _Z3Solver(
        [Z3Diagnostic("z3_check", passed=False, counterexample={"x": True}, message="failed")]
    )
    caplog.set_level(logging.WARNING, logger="yuho.verify.combined")

    result = verifier.verify(_parse_source(SOURCE), fixture="fixtures/demo.yh")

    assert not result.agreement
    assert result.disagreements[0].fixture == "fixtures/demo.yh"
    assert result.to_dict()["disagreements"][0]["z3_failures"] == [
        {"check": "z3_check", "message": "failed", "counterexample": {"x": True}}
    ]

    payload = next(
        json.loads(r.message) for r in caplog.records if r.name == "yuho.verify.combined"
    )
    assert payload["event"] == "verification_disagreement"
    assert payload["fixture"] == "fixtures/demo.yh"
    assert payload["alloy_status"] == "PASS"
    assert payload["z3_status"] == "FAIL"


def test_combined_verifier_has_no_disagreement_when_backends_match():
    verifier = CombinedVerifier()
    verifier.alloy_analyzer = _AlloyAnalyzer(
        [AlloyCounterexample("alloy_check", violated=True, message="invalid")]
    )
    verifier.z3_solver = _Z3Solver([Z3Diagnostic("z3_check", passed=False, message="failed")])

    result = verifier.verify(_parse_source(SOURCE), fixture="fixtures/demo.yh")

    assert result.agreement
    assert result.disagreements == []
