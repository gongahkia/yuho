#!/usr/bin/env python3
"""Run release gates from a temporary clean working-tree copy."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXCLUDE_PARTS = {
    ".git",
    ".venv",
    ".release-audit-venv",
    "logs",
    ".pytest_cache",
    ".hypothesis",
    "dist",
    "build",
}


def git_project_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=REPO,
        capture_output=True,
    )
    if result.returncode != 0:
        return filesystem_project_files()
    files = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        rel = Path(raw.decode())
        if any(part in EXCLUDE_PARTS for part in rel.parts):
            continue
        source = REPO / rel
        if source.is_file():
            files.append(rel)
    return files


def filesystem_project_files() -> list[Path]:
    files: list[Path] = []
    for source in REPO.rglob("*"):
        if not source.is_file():
            continue
        rel = source.relative_to(REPO)
        if any(part in EXCLUDE_PARTS for part in rel.parts):
            continue
        files.append(rel)
    return sorted(files)


def copy_worktree(dest: Path) -> None:
    for rel in git_project_files():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, target)


def venv_bin(root: Path, name: str) -> Path:
    return root / ".release-audit-venv" / ("Scripts" if os.name == "nt" else "bin") / name


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def audit_commands(root: Path, full: bool) -> list[list[str]]:
    py = str(venv_bin(root, "python"))
    yuho = str(venv_bin(root, "yuho"))
    commands = [
        [py, "-m", "pip", "install", "--upgrade", "pip", "build", "twine", "pip-audit"],
        [py, "-m", "pip", "install", "--no-cache-dir", ".[dev]"],
        [py, "-m", "pytest", "tests/test_security_baseline.py", "tests/test_release_audit.py"],
        [
            py,
            "-c",
            "import pathlib, tree_sitter_yuho; "
            "p=pathlib.Path(tree_sitter_yuho.__file__).parent; "
            "print('parser package:', p); "
            "print('parser language:', tree_sitter_yuho.language())",
        ],
        [py, "scripts/verify_action_pins.py"],
        [py, "scripts/verify_corpus_provenance.py"],
        [py, "scripts/verify_dsl_spec.py"],
        [py, "scripts/verify_backend_parity.py"],
        [py, "scripts/verify_reproducible_build.py"],
        [py, "-m", "pip_audit", "--strict"],
    ]
    if full:
        commands.extend(
            [
                [py, "-m", "pytest"],
                ["make", "verify-core", f"PYTHON={py}", f"YUHO={yuho}"],
            ]
        )
    return commands


def run_release_audit(full: bool, python: str) -> None:
    with tempfile.TemporaryDirectory(prefix="yuho-release-audit-") as tmp:
        root = Path(tmp) / "yuho"
        root.mkdir()
        copy_worktree(root)
        run([python, "-m", "venv", str(root / ".release-audit-venv")], cwd=root)
        py = str(venv_bin(root, "python"))
        for cmd in audit_commands(root, full=full):
            run(cmd, cwd=root)
    print("release audit: PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Run full pytest and verify-core")
    parser.add_argument("--python", default=sys.executable, help="Interpreter used to launch audit")
    args = parser.parse_args()
    run_release_audit(full=args.full, python=args.python)


if __name__ == "__main__":
    main()
