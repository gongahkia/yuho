#!/usr/bin/env python3
"""Fail closed when a mechanical-proof claim lacks a built Lean theorem."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REGISTRIES = (
    (ROOT / "mechanisation/core-yuho-theorems-v0.1.json",
     ROOT / "mechanisation/Yuho/CoreYuho/TheoremRegistry.lean",
     "yuho.core-theorem-coverage-v0.1"),
    (ROOT / "mechanisation/core-yuho-theorems-v0.2.json",
     ROOT / "mechanisation/Yuho/CoreYuho/TypedFiniteTheoremRegistry.lean",
     "yuho.core-theorem-coverage-v0.2"),
    (ROOT / "mechanisation/core-yuho-theorems-v0.3.json",
     ROOT / "mechanisation/Yuho/CoreYuho/ReleaseV03TheoremRegistry.lean",
     "yuho.core-theorem-coverage-v0.3"),
)
CORE_FILES = tuple((ROOT / "mechanisation/Yuho/CoreYuho").glob("*.lean"))


def main() -> int:
    registry_rows = []
    for registry, lean_registry, schema in REGISTRIES:
        document = json.loads(registry.read_text())
        if document.get("schema") != schema:
            raise SystemExit(f"unsupported theorem registry schema: {registry}")
        proved = {
            row["theorem"]
            for row in document.get("properties", [])
            if row.get("evidence") == "mechanically_proved"
        }
        checks = set(re.findall(r"^#check\s+(\S+)\s*$", lean_registry.read_text(), re.MULTILINE))
        if proved != checks:
            missing = sorted(proved - checks)
            extra = sorted(checks - proved)
            raise SystemExit(f"theorem registry drift in {registry.name}: missing={missing}, extra={extra}")
        registry_rows.append((lean_registry, len(proved)))
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
    for lean_registry, count in registry_rows:
        subprocess.run(
            ["lake", "env", "lean", str(lean_registry.relative_to(ROOT / "mechanisation"))],
            cwd=ROOT / "mechanisation",
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        print(f"Core Yuho theorem registry {lean_registry.stem}: "
              f"{count} mechanically proved properties resolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
