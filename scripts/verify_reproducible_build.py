#!/usr/bin/env python3
"""Build wheel/sdist twice with fixed inputs and compare hashes."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
SOURCE_DATE_EPOCH = "1704067200"
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "build",
    "dist",
    "logs",
    "node_modules",
    ".pytest_cache",
    ".hypothesis",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_tree_digest(root: Path) -> str:
    """Hash the exact source files copied into an isolated build tree."""
    digest = hashlib.sha256()
    for relative in project_files(root):
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(root / relative).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def project_files(root: Path) -> list[Path]:
    """Return source files without build products or local virtualenv state."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
    )
    if result.returncode == 0:
        candidates = [Path(raw.decode()) for raw in result.stdout.split(b"\0") if raw]
    else:
        candidates = [path.relative_to(root) for path in root.rglob("*") if path.is_file()]
    return sorted(
        path
        for path in candidates
        if not any(part in EXCLUDED_PARTS for part in path.parts) and (root / path).is_file()
    )


def copy_project(source: Path, destination: Path) -> None:
    for relative in project_files(source):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)


def command_version(command: list[str], cwd: Path) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
    return (result.stdout or result.stderr).strip()


def build_once(source: Path, out_dir: Path, uv: str) -> tuple[dict[str, str], dict[str, str]]:
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(
        [uv, "sync", "--locked", "--all-extras", "--no-install-project"],
        cwd=source,
        env=env,
        check=True,
    )
    subprocess.run(
        [uv, "build", "--out-dir", str(out_dir), "--clear"],
        cwd=source,
        env=env,
        check=True,
    )
    artifacts = {
        path.name: sha256(path)
        for path in sorted(out_dir.iterdir())
        if path.suffix in {".whl", ".gz"}
    }
    inputs = {
        "cc": command_version(["cc", "--version"], source).splitlines()[0],
        "python": command_version(
            [uv, "run", "--locked", "--no-sync", "python", "--version"], source
        ),
        "uv": command_version([uv, "--version"], source),
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "pyproject_sha256": sha256(source / "pyproject.toml"),
        "uv_lock_sha256": sha256(source / "uv.lock"),
        "source_tree_sha256": source_tree_digest(source),
    }
    return artifacts, inputs


def verify_reproducible_build(uv: str = "uv") -> tuple[bool, dict[str, Any]]:
    """Build two clean source copies with separately synchronized environments."""
    with tempfile.TemporaryDirectory(prefix="yuho-repro-") as tmp:
        base = Path(tmp)
        first_source = base / "first-source"
        second_source = base / "second-source"
        copy_project(REPO, first_source)
        copy_project(REPO, second_source)
        first, first_inputs = build_once(first_source, base / "first-artifacts", uv)
        second, second_inputs = build_once(second_source, base / "second-artifacts", uv)
        return first == second and first_inputs == second_inputs, {
            "first": first,
            "second": second,
            "inputs": {"first": first_inputs, "second": second_inputs},
        }


def main() -> None:
    ok, report = verify_reproducible_build(os.environ.get("YUHO_UV", "uv"))
    if ok:
        print(f"reproducible build: {len(report['first'])} artifacts match")
        print("build inputs: " + json.dumps(report["inputs"]["first"], sort_keys=True))
        return
    print("FAIL: reproducible build mismatch")
    print(report)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
