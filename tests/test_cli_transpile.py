"""Regression tests for CLI transpile target coverage."""

from pathlib import Path
from types import SimpleNamespace

from yuho.cli.commands.transpile import ALL_TARGETS, run_transpile
from yuho.transpile.base import TranspileTarget


def test_transpile_all_generates_every_target_output(tmp_path: Path, monkeypatch) -> None:
    """`yuho transpile --all` should emit one artifact per configured target."""
    import yuho.cli.commands.transpile as transpile_cmd

    def fake_analyze_file(_path: Path, run_semantic: bool = False):
        return SimpleNamespace(parse_errors=[], errors=[], ast=object())

    class DummyTranspiler:
        def __init__(self, target: TranspileTarget):
            self._target = target

        def transpile(self, _ast: object) -> str:
            return f"generated:{self._target.name.lower()}"

    def fake_get_transpiler(target: TranspileTarget) -> DummyTranspiler:
        return DummyTranspiler(target)

    monkeypatch.setattr(transpile_cmd, "analyze_file", fake_analyze_file)
    monkeypatch.setattr(transpile_cmd, "get_transpiler", fake_get_transpiler)

    source_path = tmp_path / "sample.yh"
    source_path.write_text("statute 1 \"Dummy\" { elements { } }", encoding="utf-8")
    output_dir = tmp_path / "all-targets"

    run_transpile(
        file=str(source_path),
        all_targets=True,
        output_dir=str(output_dir),
        json_output=False,
        verbose=False,
    )

    expected_outputs = {
        output_dir / f"{source_path.stem}{TranspileTarget.from_string(target).file_extension}"
        for target in ALL_TARGETS
    }

    for artifact in expected_outputs:
        assert artifact.exists(), f"Missing transpile output: {artifact.name}"
        assert artifact.read_text(encoding="utf-8").strip(), (
            f"Empty transpile output: {artifact.name}"
        )
