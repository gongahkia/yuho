"""Contracts for isolated, locked reproducibility checks."""

from __future__ import annotations

from pathlib import Path

from scripts.verify_reproducible_build import copy_project, source_tree_digest


def test_copy_project_excludes_local_build_state(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
    (source / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source / ".venv").mkdir()
    (source / ".venv" / "local-state").write_text("ignore", encoding="utf-8")
    destination = tmp_path / "destination"

    copy_project(source, destination)

    assert (destination / "module.py").is_file()
    assert not (destination / ".venv").exists()


def test_source_tree_digest_captures_copied_build_inputs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
    module = source / "module.py"
    module.write_text("VALUE = 1\n", encoding="utf-8")
    destination = tmp_path / "destination"

    copy_project(source, destination)

    assert source_tree_digest(source) == source_tree_digest(destination)
    module.write_text("VALUE = 2\n", encoding="utf-8")
    assert source_tree_digest(source) != source_tree_digest(destination)


def test_dockerfile_uses_pinned_images_and_locked_uv() -> None:
    dockerfile = (Path(__file__).resolve().parent.parent / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.12-slim@sha256:" in dockerfile
    assert "ghcr.io/astral-sh/uv:0.11.14@sha256:" in dockerfile
    assert "uv sync --locked --all-extras" in dockerfile
    assert "npm install -g" not in dockerfile
    assert "pip install" not in dockerfile
    assert "/usr/share/yuho/build-inputs.txt" in dockerfile
