from __future__ import annotations

from yuho.services.analysis import analyze_source
from yuho.transpile.akomantoso_transpiler import AkomaNtosoTranspiler
from yuho.transpile.alloy_transpiler import AlloyTranspiler
from yuho.transpile.json_transpiler import JSONTranspiler
from yuho.transpile.legalruleml_transpiler import LegalRuleMLTranspiler
from yuho.transpile.source_map import required_source_nodes, source_map_coverage


SOURCE = """
statute 99 "Source Map Demo" {
    elements {
        actus_reus act := "Physical act";
        mens_rea intent := "Intent";
    }
    exception defence {
        "Defence applies"
        "No conviction"
    }
}
"""


def test_required_source_nodes_include_elements_and_exceptions() -> None:
    analysis = analyze_source(SOURCE, file="<source-map>", run_semantic=False)
    assert analysis.ast is not None

    required = required_source_nodes(analysis.ast)

    assert [item["node"] for item in required] == [
        "ElementNode",
        "ElementNode",
        "ExceptionNode",
    ]
    assert [item["name"] for item in required] == ["act", "intent", "defence"]


def test_legal_exports_cover_required_source_nodes() -> None:
    analysis = analyze_source(SOURCE, file="<source-map>", run_semantic=False)
    assert analysis.ast is not None

    for transpiler in (
        JSONTranspiler(include_locations=False),
        AkomaNtosoTranspiler(),
        LegalRuleMLTranspiler(),
        AlloyTranspiler(),
    ):
        result = transpiler.transpile(analysis.ast)
        coverage = source_map_coverage(result.source_map, analysis.ast)
        assert coverage["missing"] == []
        assert coverage["covered"] == coverage["required"]
