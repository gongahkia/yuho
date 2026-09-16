#!/usr/bin/env python3
"""Fail closed when a mechanical-proof claim lacks a built Lean theorem."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "mechanisation/core-yuho-theorems-v0.1.json"
LEAN_REGISTRY = ROOT / "mechanisation/Yuho/CoreYuho/TheoremRegistry.lean"
CORE_FILES = tuple((ROOT / "mechanisation/Yuho/CoreYuho").glob("*.lean"))


def main() -> int:
    document = json.loads(REGISTRY.read_text())
    if document.get("schema") != "yuho.core-theorem-coverage-v0.1":
        raise SystemExit("unsupported theorem registry schema")
    proved = {
        row["theorem"]
        for row in document.get("properties", [])
        if row.get("evidence") == "mechanically_proved"
    }
    checks = set(re.findall(r"^#check\s+(\S+)\s*$", LEAN_REGISTRY.read_text(), re.MULTILINE))
    if proved != checks:
        missing = sorted(proved - checks)
        extra = sorted(checks - proved)
        raise SystemExit(f"theorem registry drift: missing={missing}, extra={extra}")
    forbidden = re.compile(r"\b(sorry|admit|axiom)\b")
    violations = []
    for path in CORE_FILES:
        if path.name == "Audit.lean":
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if forbidden.search(line) and not line.lstrip().startswith("/-"):
                violations.append(f"{path.relative_to(ROOT)}:{number}")
    if violations:
        raise SystemExit("forbidden proof placeholder: " + ", ".join(violations))
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(
        [str(Path.home() / ".elan/bin"), env.get("PATH", "")]
    )
    subprocess.run(
        ["lake", "env", "lean", "Yuho/CoreYuho/TheoremRegistry.lean"],
        cwd=ROOT / "mechanisation",
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    print(f"Core Yuho theorem registry: {len(proved)} mechanically proved properties resolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
