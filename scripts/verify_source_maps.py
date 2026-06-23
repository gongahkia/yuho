#!/usr/bin/env python3
"""Verify required element/exception source-map coverage for legal exports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

from yuho.services.analysis import analyze_file
from yuho.transpile.akomantoso_transpiler import AkomaNtosoTranspiler
from yuho.transpile.alloy_transpiler import AlloyTranspiler
from yuho.transpile.json_transpiler import JSONTranspiler
from yuho.transpile.legalruleml_transpiler import LegalRuleMLTranspiler
from yuho.transpile.source_map import source_map_coverage


REPO = Path(__file__).resolve().parents[1]
DEFAULT_LIBRARY = REPO / "library" / "penal_code"
TARGETS: dict[str, Callable[[], object]] = {
    "json": lambda: JSONTranspiler(include_locations=False),
    "akomantoso": AkomaNtosoTranspiler,
    "legalruleml": LegalRuleMLTranspiler,
    "alloy": AlloyTranspiler,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--target", action="append", choices=sorted(TARGETS))
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    targets = args.target or list(TARGETS)
    files = args.files or sorted(args.library.glob("*/statute.yh"))
    matrix: dict[str, dict[str, object]] = {}
    failures: list[dict[str, object]] = []

    for target in targets:
        required = 0
        covered = 0
        file_count = 0
        first_missing: list[dict[str, object]] = []
        for path in files:
            analysis = analyze_file(path, run_semantic=False)
            if analysis.ast is None or not analysis.is_valid:
                raise SystemExit(f"invalid statute fixture: {path}")
            result = TARGETS[target]().transpile(analysis.ast)
            coverage = source_map_coverage(result.source_map, analysis.ast)
            required += coverage["required"]
            covered += coverage["covered"]
            file_count += 1
            if coverage["missing"]:
                missing = {
                    "target": target,
                    "file": str(path),
                    "missing": coverage["missing"][:10],
                }
                failures.append(missing)
                if len(first_missing) < 5:
                    first_missing.append(missing)
        matrix[target] = {
            "files": file_count,
            "required": required,
            "covered": covered,
            "coverage": 1.0 if required == 0 else covered / required,
            "first_missing": first_missing,
        }

    payload = {"ok": not failures, "targets": matrix}
    if args.json_output:
        print(json.dumps(payload, indent=2))
    else:
        print("source-map conformance:")
        for target, row in matrix.items():
            print(
                f"  {target}: {row['covered']}/{row['required']} "
                f"element/exception nodes covered across {row['files']} file(s)"
            )
        if failures:
            print("missing source-map coverage:")
            for failure in failures[:10]:
                print(f"  {failure['target']} {failure['file']}: {failure['missing']}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
