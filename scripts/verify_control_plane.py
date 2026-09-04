#!/usr/bin/env python3
"""Exercise the verification control plane's failure semantics.

This is deliberately a negative-control gate.  It makes the corpus checker
fail through a harmless command override and verifies that Make returns a
non-zero status.  A release gate that cannot demonstrate this property is not
evidence for the checks it reports.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
STRICT_SHELL = "bash --noprofile --norc -euo pipefail {0}"
WORKFLOWS = (
    ".github/workflows/ci.yml",
    ".github/workflows/integration.yml",
    ".github/workflows/release.yml",
    ".github/workflows/security.yml",
)


def _fail(message: str) -> None:
    raise RuntimeError(message)


def verify_bash_pipeline_failure() -> None:
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-euo", "pipefail", "-c", "false | tee /dev/null"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        _fail("strict Bash accepted a failed pipeline")


def verify_make_coverage_failure() -> None:
    """Prove that a corpus-check failure reaches Make's process exit status."""
    with tempfile.TemporaryDirectory(prefix="yuho-control-plane-") as temp:
        logs = Path(temp) / "logs"
        result = subprocess.run(
            [
                "make",
                "--no-print-directory",
                "--silent",
                "verify-coverage",
                "YUHO=false",
                f"LOGS={logs}",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            _fail("make verify-coverage returned success after forced checker failures")
        coverage_log = logs / "coverage.log"
        if not coverage_log.is_file():
            _fail("make verify-coverage did not retain the coverage log")
        summary = coverage_log.read_text(encoding="utf-8")
        if "failures: 0" in summary or "failures:" not in summary:
            _fail(f"forced checker failures produced an invalid summary: {summary!r}")


def verify_workflow_shells() -> None:
    for relative in WORKFLOWS:
        text = (REPO / relative).read_text(encoding="utf-8")
        if STRICT_SHELL not in text:
            _fail(f"{relative} does not declare strict Bash defaults")


def verify_release_gate_wiring() -> None:
    text = (REPO / ".github/workflows/release.yml").read_text(encoding="utf-8")
    required = (
        "release-gate:",
        "make verify-core",
        "make verify-grammar-generated",
        "needs: [release-gate]",
    )
    missing = [item for item in required if item not in text]
    if missing:
        _fail(f"release workflow is missing gate wiring: {', '.join(missing)}")


def main() -> None:
    verify_bash_pipeline_failure()
    verify_make_coverage_failure()
    verify_workflow_shells()
    verify_release_gate_wiring()
    print("control plane: negative controls and release-gate wiring pass")


if __name__ == "__main__":
    main()
