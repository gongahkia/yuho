#!/usr/bin/env python3
"""Generate or verify the deterministic Haskell Yuho v1 release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "release/yuho-haskell-research-v1.0.0.json"
EXACT = [
    "README.md",
    "CHANGELOG.md",
    "docs/rewrite/ADR-0003-V1-GAP-TRIAGE.md",
    "docs/rewrite/CORE-YUHO-LANGUAGE-REPORT-v0.1.md",
    "docs/rewrite/CORE-YUHO-LANGUAGE-REPORT-v0.2.md",
    "docs/rewrite/CORE-YUHO-LANGUAGE-REPORT-v0.3.md",
    "docs/rewrite/CORE-YUHO-MECHANISATION-v0.1.md",
    "docs/rewrite/CORE-YUHO-MECHANISATION-v0.2.md",
    "docs/rewrite/CORE-YUHO-MECHANISATION-v0.3.md",
    "docs/rewrite/HASKELL-YUHO-RESEARCH-LANGUAGE-v1.0.md",
    "docs/rewrite/HASKELL-YUHO-v1-OPTIONAL-ROADMAP.md",
    "schema/core-yuho-conformance-v0.1.json",
    "schema/core-yuho-conformance-v0.2.json",
    "schema/core-yuho-conformance-v0.3.json",
    "mechanisation/core-yuho-theorems-v0.1.json",
    "mechanisation/core-yuho-theorems-v0.2.json",
    "mechanisation/core-yuho-theorems-v0.3.json",
    "mechanisation/conformance/core-yuho-v0.1.json",
    "mechanisation/conformance/core-yuho-v0.1.haskell.json",
    "mechanisation/conformance/core-yuho-v0.1.lean.json",
    "mechanisation/conformance/core-yuho-v0.2.json",
    "mechanisation/conformance/core-yuho-v0.2.haskell.json",
    "mechanisation/conformance/core-yuho-v0.2.lean.json",
    "mechanisation/conformance/core-yuho-v0.3.json",
    "mechanisation/conformance/core-yuho-v0.3.haskell.json",
    "mechanisation/conformance/core-yuho-v0.3.lean.json",
    "release/capabilities-v1.0.json",
    "release/diagnostic-codes-v1.0.json",
    "release/schema-versions-v1.0.json",
    "research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json",
    "research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.schema.json",
    "research/singapore/section-84-pilot/prototype/request.json",
    "examples/synthetic/request.json",
    "examples/synthetic/response.json",
    "examples/temporal/pre-request.json",
    "examples/temporal/pre-response.json",
    "examples/temporal/post-request.json",
    "examples/temporal/post-response.json",
    "examples/typed-finite-v0.3/normative-responsibility.yh",
    "examples/typed-finite-v0.3/normative-responsibility-satisfied.yh",
    "examples/typed-finite-v0.3/modular-normative-responsibility.yh",
    "examples/typed-finite-v0.3/modular-normative-responsibility-satisfied.yh",
    "examples/typed-finite-v0.3/modules/fictional.normative-routes@1.0.0.yh",
    "examples/synthetic/rich-candidate-sanctions.yh",
    "examples/synthetic/scenario-rich-candidate-sanctions.yh",
    "schema/request.schema.json",
    "schema/result.schema.json",
    "schema/typed-finite-rules-request.schema.json",
    "schema/typed-finite-rules-result.schema.json",
]
GLOBS = [
    "docs/artifacts/release-protocol/*.json",
    "docs/artifacts/core-diagrams/*.json",
    "docs/artifacts/core-diagrams/*.svg",
    "docs/artifacts/typed-finite-diagrams/*.json",
    "docs/artifacts/typed-finite-diagrams/*.svg",
    "docs/artifacts/release-diagrams/*.json",
    "docs/artifacts/release-diagrams/*.svg",
]


def paths() -> list[str]:
    selected = set(EXACT)
    for pattern in GLOBS:
        selected.update(str(path.relative_to(ROOT)) for path in ROOT.glob(pattern))
    missing = [path for path in sorted(selected) if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("release artifact missing: " + ", ".join(missing))
    return sorted(selected)


def manifest_bytes() -> bytes:
    rows = [
        {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
        for path in paths()
    ]
    document = {
        "artifacts": rows,
        "release": "Haskell Yuho Research Language v1.0.0",
        "schema": "yuho.release-manifest/v1.0",
    }
    return (json.dumps(document, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = manifest_bytes()
    if args.check:
        if not MANIFEST.is_file() or MANIFEST.read_bytes() != expected:
            raise SystemExit("release manifest is stale; run generator without --check")
        print(f"Haskell Yuho v1 release manifest: {len(paths())} artifacts verified")
    else:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_bytes(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
