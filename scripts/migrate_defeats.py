#!/usr/bin/env python3
"""Migrate Yuho exception relation clauses from `defeats` to `rebuts`."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO / "library"
CLAUSE_RE = re.compile(r"(?m)^([ \t]*)defeats([ \t]+[A-Za-z_][A-Za-z0-9_]*)")


def migrate_text(text: str) -> tuple[str, int]:
    return CLAUSE_RE.subn(r"\1rebuts\2", text)


def iter_yuho_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if root.suffix == ".yh":
                files.append(root)
            continue
        files.extend(root.rglob("*.yh"))
    return sorted(set(files))


def migrate_file(path: Path, *, write: bool) -> int:
    text = path.read_text(encoding="utf-8")
    migrated, count = migrate_text(text)
    if write and migrated != text:
        path.write_text(migrated, encoding="utf-8")
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roots",
        nargs="*",
        type=Path,
        default=[DEFAULT_ROOT],
        help="files or directories to scan; defaults to library/",
    )
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    parser.add_argument("--check", action="store_true", help="fail if any file would change")
    args = parser.parse_args(argv)

    changed = 0
    clauses = 0
    for path in iter_yuho_files([p.resolve() for p in args.roots]):
        count = migrate_file(path, write=not args.dry_run and not args.check)
        if count:
            changed += 1
            clauses += count
            print(f"{path.relative_to(REPO)}: {count}")

    print(f"{changed} files, {clauses} clauses")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
