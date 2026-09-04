#!/usr/bin/env python3
"""Verify that generated Tree-sitter artifacts match the checked-in grammar.

Generation happens in a temporary copy so local verification cannot mutate the
working tree.  The command intentionally accepts only the repository-local
CLI installed by ``npm ci``; a global CLI is not a reproducible build input.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
GRAMMAR_DIR = REPO / "src" / "tree-sitter-yuho"
GENERATED = (
    Path("src/parser.c"),
    Path("src/grammar.json"),
    Path("src/node-types.json"),
)


def main() -> None:
    cli = GRAMMAR_DIR / "node_modules" / ".bin" / "tree-sitter"
    if not cli.is_file():
        raise SystemExit(
            "missing repository-local Tree-sitter CLI; run "
            "`npm ci --ignore-scripts` in src/tree-sitter-yuho first"
        )

    with tempfile.TemporaryDirectory(prefix="yuho-grammar-") as temp:
        copy = Path(temp) / "tree-sitter-yuho"
        shutil.copytree(GRAMMAR_DIR, copy, ignore=shutil.ignore_patterns("node_modules", "build"))
        before = {
            relative: (copy / relative).read_bytes() if (copy / relative).exists() else None
            for relative in GENERATED
        }
        subprocess.run([str(cli), "generate"], cwd=copy, check=True)
        changed: list[str] = []
        for relative, original in before.items():
            generated = copy / relative
            current = generated.read_bytes() if generated.exists() else None
            if current != original:
                changed.append(relative.as_posix())
        if changed:
            raise SystemExit(
                "generated Tree-sitter artifacts are stale; run `npm ci --ignore-scripts && "
                "npx --no-install tree-sitter generate` in src/tree-sitter-yuho: "
                + ", ".join(changed)
            )
    print("generated grammar: current")


if __name__ == "__main__":
    main()
