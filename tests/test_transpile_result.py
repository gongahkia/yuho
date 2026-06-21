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
