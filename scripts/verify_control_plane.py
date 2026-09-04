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


def verify_named_pipeline_failure(name: str) -> None:
    """Prove a failing formatter/test-like process cannot be masked by tee."""
    with tempfile.TemporaryDirectory(prefix=f"yuho-control-{name}-") as temp:
        log = Path(temp) / f"{name}.log"
        result = subprocess.run(
            [
                "bash",
                "--noprofile",
                "--norc",
                "-euo",
                "pipefail",
                "-c",
                f"false | tee {log}",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            _fail(f"{name} negative control was masked by tee")
        if not log.is_file():
            _fail(f"{name} negative control did not retain its log")


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


def verify_make_source_map_failure() -> None:
    """Prove source-map verifier failures reach Make's process exit status."""
    with tempfile.TemporaryDirectory(prefix="yuho-control-source-maps-") as temp:
        logs = Path(temp) / "logs"
        result = subprocess.run(
            [
                "make",
                "--no-print-directory",
                "--silent",
                "verify-source-maps",
                "PYTHON=false",
                f"LOGS={logs}",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            _fail("make verify-source-maps returned success after a forced verifier failure")
        if not (logs / "source-maps.log").is_file():
            _fail("make verify-source-maps did not retain the source-map log")


def verify_workflow_shells() -> None:
    for relative in WORKFLOWS:
        text = (REPO / relative).read_text(encoding="utf-8")
        if STRICT_SHELL not in text:
            _fail(f"{relative} does not declare strict Bash defaults")
    ci_text = (REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for command in ("black --check", "pytest tests/"):
        if command not in ci_text:
            _fail(f"CI workflow does not run the expected {command!r} gate")


def verify_release_gate_wiring() -> None:
    release_text = (REPO / ".github/workflows/release.yml").read_text(encoding="utf-8")
    ci_text = (REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    workflow_required = (
        "release-gate:",
        "scripts/release_audit.py --full",
        "needs: [release-gate]",
    )
    missing = [item for item in workflow_required if item not in release_text]
    if missing:
        _fail(f"release workflow is missing gate wiring: {', '.join(missing)}")
    ci_required = ("release-audit:", "name: Clean Release Gate", "scripts/release_audit.py --full")
    missing_ci = [item for item in ci_required if item not in ci_text]
    if missing_ci:
        _fail(f"CI workflow is missing clean release-gate wiring: {', '.join(missing_ci)}")
    audit_text = (REPO / "scripts" / "release_audit.py").read_text(encoding="utf-8")
    audit_required = (
        '"make", "verify-core"',
        '"make", "verify-grammar-generated"',
    )
    missing_audit = [item for item in audit_required if item not in audit_text]
    if missing_audit:
        _fail(f"full release audit is missing required gates: {', '.join(missing_audit)}")


def main() -> None:
    verify_bash_pipeline_failure()
    verify_named_pipeline_failure("formatter")
    verify_named_pipeline_failure("tests")
    verify_make_coverage_failure()
    verify_make_source_map_failure()
    verify_workflow_shells()
    verify_release_gate_wiring()
    print("control plane: negative controls and release-gate wiring pass")


if __name__ == "__main__":
    main()
