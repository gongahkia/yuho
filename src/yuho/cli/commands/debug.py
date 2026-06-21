"""Implementation for ``yuho debug``."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from yuho.ast import ASTBuilder
from yuho.eval.debugger import ElementBreakpointHit, debug_element_breakpoints
from yuho.eval.interpreter import Interpreter, StructInstance, Value
from yuho.parser import get_parser


def run_debug(
    facts_file: str,
    statute_file: str,
    break_on: str,
    json_output: bool = False,
) -> None:
    break_on = break_on.lower()
    if break_on != "element":
        click.echo(f"error: unsupported breakpoint target: {break_on}", err=True)
        sys.exit(1)

    statute = _load_statute(Path(statute_file))
    facts = _load_facts(Path(facts_file))
    result, hits = debug_element_breakpoints(statute, facts)
    if json_output:
        click.echo(json.dumps(_json_payload(result, hits), indent=2, sort_keys=True))
        return
    _emit_text(result, hits)


def _load_statute(path: Path):
    ast = _parse_file(path)
    if not ast.statutes:
        click.echo(f"error: no statute in {path}", err=True)
        sys.exit(1)
    return ast.statutes[0]


def _load_facts(path: Path) -> StructInstance:
    if path.suffix.lower() == ".json":
        return _load_json_facts(path)
    ast = _parse_file(path)
    interp = Interpreter()
    interp.interpret(ast)
    struct_values = [
        value.raw for value in interp.env.bindings.values() if value.type_tag == "struct"
    ]
    if len(struct_values) == 1:
        return struct_values[0]
    return StructInstance(type_name="Facts", fields=dict(interp.env.bindings))


def _load_json_facts(path: Path) -> StructInstance:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        click.echo(f"error: failed to read facts file: {exc}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        click.echo(f"error: facts file must be a JSON object: {exc}", err=True)
        sys.exit(1)
    if not isinstance(data, dict):
        click.echo("error: facts file must be a JSON object", err=True)
        sys.exit(1)
    return StructInstance(
        type_name="Facts",
        fields={str(key): Value(raw=value) for key, value in data.items()},
    )


def _parse_file(path: Path):
    parser = get_parser()
    try:
        parse_result = parser.parse_file(path)
    except Exception as exc:
        click.echo(f"error: failed to parse {path}: {exc}", err=True)
        sys.exit(1)
    if parse_result.errors:
        click.echo(f"error: parse errors in {path}", err=True)
        for error in parse_result.errors:
            click.echo(f"  {error.location}: {error.message}", err=True)
        sys.exit(1)
    return ASTBuilder(parse_result.source, str(path)).build(parse_result.root_node)


def _emit_text(result: Any, hits: list[ElementBreakpointHit]) -> None:
    click.echo(f"debug: section {result.statute_section} ({result.statute_title})")
    for hit in hits:
        status = "satisfied" if hit.satisfied else "not satisfied"
        click.echo(f"{hit.breakpoint}: {hit.element_type} {hit.element_name} -> {status}")
        if hit.fact_value is None:
            click.echo("  fact: <missing>")
        else:
            click.echo(f"  fact: {hit.element_name}={hit.fact_value.raw!r}")
        if hit.description:
            click.echo(f"  rule: {hit.description}")
    overall = "satisfied" if result.overall_satisfied else "not satisfied"
    click.echo(f"overall: {overall}")


def _json_payload(result: Any, hits: list[ElementBreakpointHit]) -> dict[str, Any]:
    return {
        "statute": {
            "section": result.statute_section,
            "title": result.statute_title,
            "overall_satisfied": result.overall_satisfied,
        },
        "break_on": "element",
        "hits": [
            {
                "breakpoint": hit.breakpoint.id,
                "hit_count": hit.breakpoint.hit_count,
                "element": hit.element_name,
                "type": hit.element_type,
                "satisfied": hit.satisfied,
                "fact": _json_value(hit.fact_value),
                "description": hit.description,
            }
            for hit in hits
        ],
    }


def _json_value(value: Value | None) -> Any:
    if value is None:
        return None
    raw = value.raw
    if hasattr(raw, "isoformat"):
        return raw.isoformat()
    return raw
