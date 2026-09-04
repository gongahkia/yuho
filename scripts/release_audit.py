#!/usr/bin/env python3
"""Run release gates from a temporary clean working-tree copy.

The audit deliberately uses the project's locked uv environment. Installing
fresh, unconstrained build and audit tools in the audit itself would make a
passing release result depend on inputs that are absent from ``uv.lock``.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
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
    "node_modules",
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


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def audit_commands(root: Path, full: bool, uv: str = "uv") -> list[list[str]]:
    """Return the exact commands used to audit a clean copy."""
    locked = [uv, "run", "--locked"]
    commands = [
        [uv, "lock", "--check"],
        [uv, "sync", "--locked", "--all-extras"],
        [*locked, "pytest", "tests/test_security_baseline.py", "tests/test_release_audit.py"],
        [
            *locked,
            "python",
            "-c",
            "import pathlib, tree_sitter_yuho; "
            "p=pathlib.Path(tree_sitter_yuho.__file__).parent; "
            "print('parser package:', p); "
            "print('parser language:', tree_sitter_yuho.language())",
        ],
        [*locked, "python", "scripts/verify_action_pins.py"],
        [*locked, "python", "scripts/verify_corpus_provenance.py"],
        [*locked, "python", "scripts/verify_capability_claims.py"],
        [*locked, "python", "scripts/verify_dsl_spec.py"],
        [*locked, "python", "scripts/verify_backend_parity.py"],
        [*locked, "python", "scripts/verify_reproducible_build.py"],
        [*locked, "pip-audit", "--strict"],
    ]
    if full:
        commands.extend(
            [
                [*locked, "pytest"],
                [*locked, "make", "verify-grammar-generated"],
                [*locked, "make", "verify-core"],
            ]
        )
    return commands


def run_release_audit(full: bool, uv: str) -> None:
    with tempfile.TemporaryDirectory(prefix="yuho-release-audit-") as tmp:
        root = Path(tmp) / "yuho"
        root.mkdir()
        copy_worktree(root)
        for cmd in audit_commands(root, full=full, uv=uv):
            run(cmd, cwd=root)
    print("release audit: PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Run full pytest and verify-core")
    parser.add_argument(
        "--uv",
        default=os.environ.get("YUHO_UV", "uv"),
        help="locked uv executable used for the audit (default: %(default)s)",
    )
    args = parser.parse_args()
    run_release_audit(full=args.full, uv=args.uv)


if __name__ == "__main__":
    main()
