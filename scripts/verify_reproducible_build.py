#!/usr/bin/env python3
"""Build wheel/sdist twice with fixed inputs and compare hashes."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE_DATE_EPOCH = "1704067200"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_once(out_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
    env["PYTHONHASHSEED"] = "0"
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(out_dir), "."],
        cwd=REPO,
        env=env,
        check=True,
    )
    return {
        path.name: sha256(path)
        for path in sorted(out_dir.iterdir())
        if path.suffix in {".whl", ".gz"}
    }


def verify_reproducible_build() -> tuple[bool, dict[str, dict[str, str]]]:
    with tempfile.TemporaryDirectory(prefix="yuho-repro-") as tmp:
        base = Path(tmp)
        first_dir = base / "first"
        second_dir = base / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        first = build_once(first_dir)
        second = build_once(second_dir)
        return first == second, {"first": first, "second": second}


def main() -> None:
    ok, report = verify_reproducible_build()
    if ok:
        print(f"reproducible build: {len(report['first'])} artifacts match")
        return
    print("FAIL: reproducible build mismatch")
    print(report)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
