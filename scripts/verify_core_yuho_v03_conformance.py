#!/usr/bin/env python3
"""Run independent Haskell and Lean Core Yuho v0.3 evaluators and compare bytes."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "mechanisation/conformance/core-yuho-v0.3.json"
HASKELL = ROOT / "mechanisation/conformance/core-yuho-v0.3.haskell.json"
LEAN = ROOT / "mechanisation/conformance/core-yuho-v0.3.lean.json"


def run(command: list[str], cwd: Path, env: dict[str, str]) -> bytes:
    completed = subprocess.run(command, cwd=cwd, env=env, capture_output=True, check=False)
    if completed.returncode:
        raise SystemExit(completed.stdout.decode() + completed.stderr.decode())
    return completed.stdout


def main() -> int:
    document = json.loads(VECTORS.read_text())
    if document.get("schema") != "yuho.core-conformance-v0.3":
        raise SystemExit("unsupported v0.3 conformance schema")
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([
        str(Path.home() / ".ghcup/bin"), str(Path.home() / ".elan/bin"),
        env.get("PATH", "")])
    haskell_dir = ROOT / "rewrite/haskell"
    run(["cabal", "v2-build", "exe:yuho-core-conformance", "--offline", "-j1"],
        haskell_dir, env)
    executable = run(["cabal", "list-bin", "exe:yuho-core-conformance"],
                     haskell_dir, env).decode().strip()
    run(["lake", "build", "release_v03_conformance"], ROOT / "mechanisation", env)
    haskell = run([executable, str(VECTORS)], ROOT, env)
    lean = run(["lake", "env", "lean", "--run", "scripts/ReleaseV03Conformance.lean"],
               ROOT / "mechanisation", env)
    if haskell != lean:
        raise SystemExit("Core Yuho v0.3 Haskell/Lean conformance mismatch")
    if haskell != HASKELL.read_bytes().rstrip(b"\n") or lean != LEAN.read_bytes().rstrip(b"\n"):
        raise SystemExit("stale retained Core Yuho v0.3 conformance result")
    print(f"Core Yuho v0.3 conformance: {len(document['vectors'])} vectors passed")
    print(f"input sha256: {hashlib.sha256(VECTORS.read_bytes()).hexdigest()}")
    print(f"result sha256: {hashlib.sha256(haskell).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
