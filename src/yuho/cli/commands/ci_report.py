"""Aggregate Yuho diagnostics for CI systems.

The single-file ``check`` command remains the interactive interface.  This
module owns the directory-level JSON/SARIF contract used by the published
GitHub composite action and CI templates.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from yuho.output.sarif import make_sarif_result, to_sarif
from yuho.services.analysis import analyze_file


REPORT_VERSION = "yuho-ci-report-v1"


def collect_yuho_files(directory: Path) -> list[Path]:
    """Return deterministic source inputs under a supplied directory."""
    if not directory.exists():
        raise ValueError(f"directory does not exist: {directory}")
    if not directory.is_dir():
        raise ValueError(f"not a directory: {directory}")
    return sorted(path for path in directory.rglob("*.yh") if path.is_file())


def build_report(directory: Path, *, syntax_only: bool = False) -> dict[str, Any]:
    """Analyze every source file and return a stable machine-readable report."""
    files = collect_yuho_files(directory)
    if not files:
        raise ValueError(f"no .yh files found under {directory}")

    file_reports: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    error_count = 0
    warning_count = 0

    for path in files:
        analysis = analyze_file(path, run_semantic=not syntax_only)
        payload = analysis.validation_payload()
        relative = path.relative_to(directory).as_posix()
        file_reports.append(
            {
                "path": relative,
                "valid": payload["valid"],
                "phases": payload["phases"],
            }
        )
        for severity_key, severity in (("errors", "error"), ("warnings", "warning")):
            for diagnostic in payload[severity_key]:
                diagnostics.append(_diagnostic(relative, diagnostic, severity))
                if severity == "error":
                    error_count += 1
                else:
                    warning_count += 1
        for diagnostic in payload["lint_warnings"]:
            diagnostics.append(_diagnostic(relative, diagnostic, "warning"))
            warning_count += 1

    return {
        "version": REPORT_VERSION,
        "root": str(directory),
        "mode": "syntax-only" if syntax_only else "full",
        "ok": error_count == 0,
        "summary": {
            "files": len(files),
            "valid_files": sum(1 for report in file_reports if report["valid"]),
            "invalid_files": sum(1 for report in file_reports if not report["valid"]),
            "errors": error_count,
            "warnings": warning_count,
        },
        "files": file_reports,
        "diagnostics": diagnostics,
    }


def render_report(report: dict[str, Any], output_format: str) -> str:
    """Render a report as the documented JSON or SARIF interchange format."""
    if output_format == "json":
        return json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output_format != "sarif":
        raise ValueError(f"unsupported report format: {output_format}")
    results = [
        make_sarif_result(
            rule_id=f"yuho/{item['stage']}",
            message=item["message"],
            file=item["file"],
            line=item["line"],
            col=item["column"],
            level=item["severity"],
        )
        for item in report["diagnostics"]
    ]
    return to_sarif(results) + "\n"


def _diagnostic(path: str, diagnostic: dict[str, Any], severity: str) -> dict[str, Any]:
    return {
        "file": path,
        "stage": diagnostic.get("stage", "analysis"),
        "severity": severity,
        "message": diagnostic["message"],
        "error_code": diagnostic.get("error_code"),
        "line": diagnostic.get("line") or 1,
        "column": diagnostic.get("column") or 1,
    }
