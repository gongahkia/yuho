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
    subsume_target: Optional[str] = None,
    json_output: bool = False,
) -> None:
    if subsume_target:
        # Subsumption mode (#4): compare two sections rather than explore one.
        from yuho.services.analysis import analyze_file
        from yuho.explore.counterexamples import CounterexampleExplorer
        analysis = analyze_file(file, run_semantic=False)
        if analysis.parse_errors or analysis.ast is None:
            err = {"ok": False, "error": "parse_errors",
                   "details": [str(e) for e in (analysis.parse_errors or [])][:5]}
            click.echo(_json.dumps(err, indent=2) if json_output else f"error: {err['error']}",
                       err=not json_output)
            sys.exit(1)
        explorer = CounterexampleExplorer(analysis.ast)
        report = explorer.explore_subsumption(section, subsume_target)
        if json_output:
            click.echo(_json.dumps({"ok": True, "subsumption": report.to_dict()},
                                   indent=2, ensure_ascii=False))
        else:
            click.echo(f"s{section} vs s{subsume_target}: {report.relation or '(unknown)'}")
            if not report.available:
                click.echo(f"  unavailable: {report.reason}")
            else:
                if report.overlap_witness:
                    click.echo(f"  overlap witness: {report.overlap_witness['elements']}")
                if report.a_only_witness:
                    click.echo(f"  a-only witness:  {report.a_only_witness['elements']}")
                if report.b_only_witness:
                    click.echo(f"  b-only witness:  {report.b_only_witness['elements']}")
        sys.exit(0 if report.available else 2)

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
