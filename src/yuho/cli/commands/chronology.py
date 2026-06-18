"""Chronology command implementations."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from yuho.chronology import build_world, validate_world
from yuho.chronology.importers import import_chronology
from yuho.chronology.renderers import diagnostics_to_dict, render_diff, render_world
from yuho.chronology.reports import (
    render_contradictions_report,
    render_deadlines_report,
    render_exhibits_report,
    render_issues_report,
    render_review_report,
    render_scenario_diff,
    render_scenario_report,
    render_sources_report,
)
from yuho.services.analysis import analyze_file


def run_chronology_check(file: str, json_output: bool = False) -> None:
    world, diagnostics = _load_world(file)
    errors = [diag for diag in diagnostics if diag.severity == "error"]
    if json_output:
        click.echo(
            json.dumps(
                {
                    "valid": not errors,
                    "diagnostics": diagnostics_to_dict(diagnostics),
                    "world": _summary(world),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        click.echo(f"{'VALID' if not errors else 'INVALID'}: {file}")
        for diag in diagnostics:
            loc = f"{diag.line}:{diag.column}" if diag.line else "?:?"
            click.echo(f"{diag.severity}: {loc}: {diag.message}", err=diag.severity == "error")
    sys.exit(1 if errors else 0)


def run_chronology_export(
    file: str,
    target: str,
    output: Optional[str] = None,
    narrative: Optional[str] = None,
) -> None:
    world, diagnostics = _load_world(file)
    errors = [diag for diag in diagnostics if diag.severity == "error"]
    if errors:
        for diag in errors:
            click.echo(f"error: {diag.message}", err=True)
        sys.exit(1)
    text = render_world(world, target, narrative=narrative)
    _write_or_echo(text, output)


def run_chronology_diff(
    left: str,
    right: str,
    target: str,
    output: Optional[str] = None,
) -> None:
    left_world, left_diagnostics = _load_world(left)
    right_world, right_diagnostics = _load_world(right)
    errors = [diag for diag in left_diagnostics + right_diagnostics if diag.severity == "error"]
    if errors:
        for diag in errors:
            click.echo(f"error: {diag.message}", err=True)
        sys.exit(1)
    _write_or_echo(render_diff(left_world, right_world, target=target), output)


def run_chronology_sources(file: str) -> None:
    world, _ = _load_world(file)
    click.echo(render_sources_report(world), nl=False)


def run_chronology_deadlines(file: str) -> None:
    world, _ = _load_world(file)
    click.echo(render_deadlines_report(world), nl=False)


def run_chronology_issues(file: str) -> None:
    world, _ = _load_world(file)
    click.echo(render_issues_report(world), nl=False)


def run_chronology_contradictions(file: str) -> None:
    world, _ = _load_world(file)
    click.echo(render_contradictions_report(world), nl=False)


def run_chronology_review(file: str) -> None:
    world, diagnostics = _load_world(file)
    click.echo(render_review_report(world, diagnostics), nl=False)


def run_chronology_exhibits(file: str, output_format: str = "text") -> None:
    world, _ = _load_world(file)
    click.echo(render_exhibits_report(world, output_format=output_format), nl=False)


def run_chronology_scenario_report(file: str, scenario: Optional[str] = None) -> None:
    world, diagnostics = _load_world(file)
    _exit_on_errors(diagnostics)
    if scenario and scenario not in world.scenarios:
        click.echo(f"error: unknown scenario '{scenario}'", err=True)
        sys.exit(1)
    click.echo(render_scenario_report(world, scenario_name=scenario), nl=False)


def run_chronology_scenario_diff(
    file: str,
    scenario: str,
    target: str,
    output: Optional[str] = None,
) -> None:
    world, diagnostics = _load_world(file)
    _exit_on_errors(diagnostics)
    try:
        text = render_scenario_diff(world, scenario_name=scenario, target=target)
    except ValueError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)
    _write_or_echo(text, output)


def run_chronology_import(file: str, source_format: str, output: Optional[str] = None) -> None:
    _write_or_echo(import_chronology(file, source_format), output)


def _load_world(file: str):
    analysis = analyze_file(file, run_semantic=False)
    payload = analysis.validation_payload()
    parse_ast_errors = [
        item for item in payload["errors"] if item["stage"] in ("parse", "ast")
    ]
    if parse_ast_errors:
        for item in parse_ast_errors:
            line = item.get("line") or "?"
            column = item.get("column") or "?"
            click.echo(f"error: {line}:{column}: {item['message']}", err=True)
        sys.exit(1)
    if not analysis.ast:
        click.echo("error: AST unavailable", err=True)
        sys.exit(1)
    world = build_world(analysis.ast)
    return world, validate_world(world)


def _write_or_echo(text: str, output: Optional[str]) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        click.echo(text, nl=False)


def _exit_on_errors(diagnostics) -> None:
    errors = [diag for diag in diagnostics if diag.severity == "error"]
    if errors:
        for diag in errors:
            click.echo(f"error: {diag.message}", err=True)
        sys.exit(1)


def _summary(world) -> dict[str, int]:
    return {
        "sources": len(world.sources),
        "timelines": len(world.timelines),
        "entities": len(world.entities),
        "relationships": len(world.relationships),
        "issues": len(world.issues),
        "deadline_rules": len(world.deadline_rules),
    }
