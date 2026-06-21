#!/usr/bin/env python3
"""Round-trip encoded statutes through LegalRuleML and structural validation."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from yuho.services.analysis import analyze_file  # noqa: E402
from yuho.transpile import TranspileTarget, get_transpiler  # noqa: E402

XSD_PATH = REPO / "src" / "yuho" / "transpile" / "lrml_schema" / "compact" / "lrml-compact.xsd"
LRML_NS = "{http://docs.oasis-open.org/legalruleml/ns/v1.0/}"


def _validate_lrml(xml: str) -> tuple[bool, list[str]]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        return False, [str(exc)]
    if root.tag != LRML_NS + "LegalRuleML":
        return False, [f"root is {root.tag!r}, expected LegalRuleML"]
    if root.find(LRML_NS + "Statements") is None:
        return False, ["missing lrml:Statements"]
    return True, []


def _xsd_validate(xml: str, xsd: Path) -> tuple[bool, list[str]]:
    if not shutil.which("xmllint"):
        return True, []
    with tempfile.NamedTemporaryFile("w", suffix=".lrml", delete=False) as fh:
        fh.write(xml)
        path = fh.name
    try:
        result = subprocess.run(
            ["xmllint", "--noout", "--schema", str(xsd), path],
            capture_output=True,
            text=True,
            timeout=30,
        )
    finally:
        Path(path).unlink(missing_ok=True)
    if result.returncode == 0:
        return True, []
    return False, [line for line in (result.stderr or "").splitlines() if line.strip()][:5]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", default=str(REPO / "library" / "penal_code"))
    parser.add_argument("--json", dest="json_out", action="store_true")
    parser.add_argument("--max-errors", type=int, default=20)
    parser.add_argument(
        "--xsd",
        action="store_true",
        help="Also validate every doc against the vendored LegalRuleML compact XSD.",
    )
    args = parser.parse_args()

    lib = Path(args.library)
    if not lib.exists():
        print(f"error: library not found at {lib}", file=sys.stderr)
        return 2

    transpiler = get_transpiler(TranspileTarget.LEGALRULEML)
    n_total = 0
    n_pass = 0
    failures: list[dict] = []

    for yh in sorted(lib.glob("*/statute.yh")):
        n_total += 1
        result = analyze_file(yh, run_semantic=False)
        if result.ast is None:
            failures.append(
                {
                    "section": yh.parent.name,
                    "stage": "parse",
                    "errors": [str(e) for e in result.parse_errors][:3],
                }
            )
            continue
        try:
            xml = transpiler.transpile(result.ast)
        except Exception as exc:
            failures.append({"section": yh.parent.name, "stage": "transpile", "errors": [str(exc)]})
            continue
        ok, errors = _validate_lrml(xml)
        if not ok:
            failures.append(
                {
                    "section": yh.parent.name,
                    "stage": "validate",
                    "errors": errors[: args.max_errors],
                }
            )
            continue
        if args.xsd:
            ok, errors = _xsd_validate(xml, XSD_PATH)
            if not ok:
                failures.append(
                    {
                        "section": yh.parent.name,
                        "stage": "xsd",
                        "errors": errors[: args.max_errors],
                    }
                )
                continue
        n_pass += 1

    summary = {
        "n_total": n_total,
        "n_pass": n_pass,
        "n_fail": len(failures),
        "failures": failures[: args.max_errors],
    }

    if args.json_out:
        print(json.dumps(summary, indent=2))
    else:
        print(f"LRML round-trip: {n_pass}/{n_total} validate clean")
        if failures:
            print(f"\nFirst {min(len(failures), 5)} failures:")
            for failure in failures[:5]:
                print(
                    f"  {failure['section']:60s}  {failure['stage']:10s}  "
                    f"{failure['errors'][0] if failure['errors'] else ''}"[:160]
                )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
