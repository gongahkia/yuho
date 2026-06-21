"""Regression tests for CLI transpile target coverage."""

import json
from pathlib import Path
from types import SimpleNamespace

from yuho.cli.commands.transpile import ALL_TARGETS, run_transpile
from yuho.transpile.base import TranspileResult, TranspileTarget


def test_transpile_all_generates_every_target_output(tmp_path: Path, monkeypatch) -> None:
    """`yuho transpile --all` should emit one artifact per configured target."""
    import yuho.cli.commands.transpile as transpile_cmd

    def fake_analyze_file(_path: Path, run_semantic: bool = False):
        return SimpleNamespace(parse_errors=[], errors=[], ast=object())

    class DummyTranspiler:
        def __init__(self, target: TranspileTarget):
            self._target = target

        def transpile(self, _ast: object) -> TranspileResult:
            output = f"generated:{self._target.name.lower()}"
            return TranspileResult(
                output,
                manifest={"target": self._target.name.lower()},
            )

    def fake_get_transpiler(target: TranspileTarget) -> DummyTranspiler:
        return DummyTranspiler(target)

    monkeypatch.setattr(transpile_cmd, "analyze_file", fake_analyze_file)
    monkeypatch.setattr(transpile_cmd, "get_transpiler", fake_get_transpiler)

    # Also mock the PDF pipeline so it doesn't invoke the real LaTeX transpiler
    def fake_generate_pdf(ast, output_path, **kwargs):
        Path(output_path).write_text("generated:pdf", encoding="utf-8")
        return str(Path(output_path).resolve())

    monkeypatch.setattr("yuho.transpile.pdf_pipeline.generate_pdf", fake_generate_pdf)

    # DOCX is a binary special-case (like PDF). Mock the writer so it doesn't
    # need a real AST to produce output.
    class DummyDocx:
        def write_docx(self, _ast, path):
            Path(path).write_text("generated:docx", encoding="utf-8")

    monkeypatch.setattr("yuho.transpile.docx_transpiler.DOCXTranspiler", lambda: DummyDocx())

    source_path = tmp_path / "sample.yh"
    source_path.write_text('statute 1 "Dummy" { elements { } }', encoding="utf-8")
    output_dir = tmp_path / "all-targets"

    run_transpile(
        file=str(source_path),
        all_targets=True,
        output_dir=str(output_dir),
        json_output=False,
        verbose=False,
    )

    # "pdf" is a special-case pipeline target, not a TranspileTarget enum member
    SPECIAL_TARGETS = {"pdf": ".pdf"}
    expected_outputs = set()
    for target in ALL_TARGETS:
        if target in SPECIAL_TARGETS:
            expected_outputs.add(output_dir / f"{source_path.stem}{SPECIAL_TARGETS[target]}")
        else:
            expected_outputs.add(
                output_dir
                / f"{source_path.stem}{TranspileTarget.from_string(target).file_extension}"
            )

    for artifact in expected_outputs:
        assert artifact.exists(), f"Missing transpile output: {artifact.name}"
        assert artifact.read_text(
            encoding="utf-8"
        ).strip(), f"Empty transpile output: {artifact.name}"


def test_transpile_writes_source_map_sidecar(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.yh"
    source_path.write_text(
        """
        statute 1 "Demo" {
            elements {
                actus_reus taking := "takes";
            }
        }
        """,
        encoding="utf-8",
    )
    output_path = tmp_path / "sample.txt"

    run_transpile(
        file=str(source_path),
        target="english",
        output=str(output_path),
        json_output=False,
        verbose=False,
    )

    sidecar_path = tmp_path / "sample.txt.map"
    source_map = json.loads(sidecar_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert source_map["version"] == 3
    assert source_map["file"] == output_path.name
    assert source_map["sources"] == [str(source_path.resolve())]
    assert isinstance(source_map["mappings"], str)
    assert source_map["x_yuho_spans"]
