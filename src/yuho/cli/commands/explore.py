"""``yuho explore`` — counter-example explorer for offences.

Surfaces structural fact patterns that satisfy a section's elements,
trigger its exceptions, or expose load-bearing elements. Reuses the
existing Z3 verifier; no new constraint translation.
"""

from __future__ import annotations

import json as _json
import sys
from typing import Optional

import click

from yuho.explore.counterexamples import explore_file, render_report_text


def run_explore(
    file: str,
    section: str,
    *,
    max_satisfying: int = 5,
    no_borderline: bool = False,
    no_exceptions: bool = False,
    json_output: bool = False,
) -> None:
    result = explore_file(
        file,
        section,
        max_satisfying=max_satisfying,
        include_borderline=not no_borderline,
        include_exception_coverage=not no_exceptions,
    )
    if json_output:
        click.echo(_json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result.get("ok") else 1)

    if not result.get("ok"):
        click.echo(f"error: {result.get('error', 'unknown')}", err=True)
        for d in result.get("details", []):
            click.echo(f"  {d}", err=True)
        sys.exit(1)

    rep = result["report"]
    # Rehydrate a lightweight structure compatible with render_report_text
    # without round-tripping through the dataclass.
    from yuho.explore.counterexamples import ExplorerReport, Scenario
    report = ExplorerReport(
        section=rep["section"],
        title=rep["title"],
        available=rep["available"],
        reason=rep.get("reason"),
        satisfying=[Scenario(**s) for s in rep.get("satisfying") or []],
        borderline=[Scenario(**s) for s in rep.get("borderline") or []],
        exception_coverage=rep.get("exception_coverage") or [],
        dead_exceptions=rep.get("dead_exceptions") or [],
        summary=rep.get("summary") or {},
    )
    click.echo(render_report_text(report))
    sys.exit(0 if report.available else 2)
