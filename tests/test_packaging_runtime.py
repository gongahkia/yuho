"""Integration test for parser runtime after editable package install."""

from __future__ import annotations

import os
import subprocess
import tempfile
import venv
from pathlib import Path

import pytest


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def test_parser_runtime_after_editable_install() -> None:
    """Verify parser runtime works after installing yuho in a clean venv."""
    if os.environ.get("YUHO_RUN_PACKAGING_RUNTIME_TEST") != "1":
        pytest.skip("Set YUHO_RUN_PACKAGING_RUNTIME_TEST=1 to run packaging integration tests")

    repo_root = Path(__file__).resolve().parents[1]
    sample_file = repo_root / "examples" / "simple_statute.yh"
    if not sample_file.exists():
        pytest.fail(f"Missing sample statute file: {sample_file}")

    with tempfile.TemporaryDirectory(prefix="yuho-packaging-runtime-") as tmp_dir:
        venv_dir = Path(tmp_dir) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
        python_bin = _venv_python(venv_dir)

        env = os.environ.copy()
        env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

        subprocess.run(
            [str(python_bin), "-m", "pip", "install", "--upgrade", "pip"],
            cwd=repo_root,
            env=env,
            check=True,
        )
        subprocess.run(
            [str(python_bin), "-m", "pip", "install", "-e", "./src"],
            cwd=repo_root,
            env=env,
            check=True,
        )

        runtime_check = (
            "from pathlib import Path\n"
            "from yuho.parser import get_parser\n"
            f"sample = Path(r'{sample_file}')\n"
            "source = sample.read_text(encoding='utf-8')\n"
            "result = get_parser().parse(source, file=str(sample))\n"
            "assert result.is_valid, f'Unexpected parse errors: {result.errors}'\n"
        )
        subprocess.run(
            [str(python_bin), "-c", runtime_check],
            cwd=repo_root,
            env=env,
            check=True,
        )
