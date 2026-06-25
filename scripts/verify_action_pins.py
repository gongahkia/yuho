#!/usr/bin/env python3
"""Fail if GitHub Actions uses remote actions without immutable SHA pins."""

from __future__ import annotations

import re
from pathlib import Path

USES_RE = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
SHA_RE = re.compile(r"^[^@]+@[0-9a-f]{40}$")

WORKFLOW_FILES = sorted(Path(".github").glob("**/*.yml")) + sorted(
    Path(".github").glob("**/*.yaml")
)


def find_unpinned_actions() -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    for path in WORKFLOW_FILES:
        text = path.read_text(encoding="utf-8")
        for match in USES_RE.finditer(text):
            ref = match.group(1).strip("'\"")
            if ref.startswith("./"):
                continue
            if not SHA_RE.match(ref):
                failures.append((str(path), ref))
    return failures


def main() -> None:
    failures = find_unpinned_actions()
    if not failures:
        print(f"action pins: {len(WORKFLOW_FILES)} files checked")
        return
    for path, ref in failures:
        print(f"FAIL: {path}: {ref}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
