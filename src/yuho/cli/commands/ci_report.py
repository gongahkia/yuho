"""Unified CI report command - runs check+lint+test, outputs SARIF/JSON."""

import json
import sys
import time
from pathlib import Path
from typing import List, Optional

import click

from yuho.services.analysis import analyze_file
from yuho.output.sarif import make_sarif_result, to_sarif
from yuho.output.junit import TestResult, to_junit_xml


def _find_yh_files(directory: str) -> List[Path]:
    """Recursively find .yh files."""
    return sorted(Path(directory).rglob("*.yh"))


def run_ci_report(
    directory: str = ".",
    output: Optional[str] = None,
    format: str = "json",
) -> int:
    """Run check+lint on all .yh files, produce unified report. Returns exit code."""
    files = _find_yh_files(directory)
    if not files:
        click.echo("No .yh files found", err=True)
        return 0
    all_errors = []
    all_sarif_results = []
    t0 = time.monotonic()
    for f in files:
        result = analyze_file(str(f))
        for err in result.errors:
            entry = {
                "file": str(f),
                "stage": err.stage,
                "message": err.message,
                "line": err.location.line if err.location else None,
                "col": err.location.col if err.location else None,
            }
            all_errors.append(entry)
            all_sarif_results.append(
                make_sarif_result(
                    rule_id=f"yuho/{err.stage}",
                    message=err.message,
                    file=str(f),
                    line=err.location.line if err.location else 1,
                    col=err.location.col if err.location else 1,
                )
            )
        for pe in result.parse_errors:
            entry = {
                "file": str(f),
                "stage": "parse",
                "message": pe.message,
                "line": pe.location.line if pe.location else None,
                "col": pe.location.col if pe.location else None,
            }
            all_errors.append(entry)
            all_sarif_results.append(
                make_sarif_result(
                    rule_id="yuho/parse",
                    message=pe.message,
                    file=str(f),
                    line=pe.location.line if pe.location else 1,
                    col=pe.location.col if pe.location else 1,
                )
            )
    elapsed = time.monotonic() - t0
    if format == "sarif":
        text = to_sarif(all_sarif_results)
    elif format == "junit":
        junit_results = []
        for f in files:
            errors_for_file = [e for e in all_errors if e["file"] == str(f)]
            passed = len(errors_for_file) == 0
            fail_msg = (
                "; ".join(str(error.get("message", "")) for error in errors_for_file)
                if not passed
                else None
            )
            junit_results.append(
                TestResult(
                    name=str(f), classname="yuho.ci", passed=passed, failure_message=fail_msg
                )
            )
        text = to_junit_xml(junit_results, suite_name="yuho-ci", suite_time=elapsed)
    else:
        text = json.dumps(
            {
                "files_checked": len(files),
                "errors": len(all_errors),
                "elapsed_s": round(elapsed, 3),
                "results": all_errors,
            },
            indent=2,
        )
    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Report written to {output}")
    else:
        click.echo(text)
    return 1 if all_errors else 0
