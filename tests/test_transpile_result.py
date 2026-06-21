from __future__ import annotations

from yuho.services.analysis import analyze_source
from yuho.transpile import TranspileResult, TranspileTarget, get_transpiler


SOURCE = """
statute 1 "Demo" {
    elements {
        actus_reus taking := "takes";
        mens_rea intent := "intends";
    }
}
"""


def test_transpiler_returns_string_compatible_result():
    analysis = analyze_source(SOURCE, run_semantic=False)
    result = get_transpiler(TranspileTarget.JSON).transpile(analysis.ast)

    assert isinstance(result, TranspileResult)
    assert isinstance(result, str)
    assert result.output == str(result)
    assert result.warnings == ()
    assert result.manifest["target"] == "json"
    assert result.manifest["extension"] == ".json"
    assert result.manifest["source_map"]["version"] == 3
    assert result.source_map is not None
    assert result.source_map["version"] == 3
    assert result.source_map["sources"] == ["<string>"]
    assert isinstance(result.source_map["mappings"], str)
    assert result.source_map["x_yuho_spans"]


def test_transpile_result_to_dict():
    result = TranspileResult(
        "body",
        warnings=("warn",),
        manifest={"target": "demo"},
    )

    assert result.to_dict() == {
        "output": "body",
        "warnings": ["warn"],
        "manifest": {"target": "demo"},
    }


def test_transpile_result_to_dict_includes_source_map_when_present():
    source_map = {
        "version": 3,
        "file": "out.json",
        "sources": ["in.yh"],
        "names": [],
        "mappings": "",
        "x_yuho_spans": [],
    }
    result = TranspileResult("body", manifest={"target": "demo"}, source_map=source_map)

    assert result.to_dict()["source_map"] == source_map
