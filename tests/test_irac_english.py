"""IRAC English rendering tests."""

from __future__ import annotations

from yuho.ast import nodes
from yuho.explain import DatalogExplainer
from yuho.transpile.english_transpiler import EnglishTranspiler


def test_english_transpiler_renders_irac_trace():
    statute = nodes.StatuteNode(
        section_number="1",
        title=nodes.StringLit("Demo"),
        definitions=(),
        elements=(nodes.ElementNode("actus_reus", "taking", nodes.StringLit("takes")),),
        penalty=None,
        illustrations=(),
    )
    trace = DatalogExplainer().explain(statute, {"taking": True})

    rendered = EnglishTranspiler().render_irac(statute, trace)

    assert "ISSUE" in rendered
    assert "The rule requires actus_reus: taking." in rendered
    assert "The actus_reus element taking is satisfied" in rendered
    assert "Section 1 is satisfied." in rendered
