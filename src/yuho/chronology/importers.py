"""Chronology import helpers."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


def import_chronology(path: str | Path, source_format: str) -> str:
    if source_format == "csv":
        return import_csv(path)
    if source_format == "jsonld":
        return import_jsonld(path)
    raise ValueError(f"Unsupported chronology import format: {source_format}")


def import_csv(path: str | Path) -> str:
    rows = list(csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines()))
    sources: list[str] = []
    timelines: dict[str, dict[str, str]] = {}
    entities: list[str] = []
    relationships: list[str] = []
    for row in rows:
        kind = (row.get("declaration") or row.get("kind") or "").strip().lower()
        if _is_relationship_row(row, kind):
            source = _ident(row.get("source") or row.get("from") or "")
            target = _ident(row.get("target") or row.get("to") or "")
            label = row.get("label") or row.get("relationship") or row.get("reltype")
            if source and target:
                relationships.append(_relationship_line(source, target, label))
            continue
        name = _ident(row.get("name") or row.get("id") or "")
        if not name:
            continue
        if kind == "source":
            source_kind = _ident(row.get("source_kind") or row.get("type") or "document")
            block = [f"source {name}: {source_kind} {{"]
            _emit_field(block, "citation", row.get("citation"))
            _emit_field(block, "title", row.get("title"))
            _emit_field(block, "url", row.get("url"))
            _emit_field(block, "path", row.get("path"))
            block.append("}")
            sources.append("\n".join(block))
        elif kind == "timeline":
            timeline = timelines.setdefault(name, {})
            _merge_bound(timeline, "start", row.get("start"))
            _merge_bound(timeline, "end", row.get("end"))
            for field in ("jurisdiction", "procedure", "court", "kind", "parent"):
                if row.get(field):
                    timeline[field] = str(row[field])
        else:
            type_name = _ident(row.get("type") or row.get("entity_type") or "fact")
            block = [f"entity {name}: {type_name} {{"]
            _emit_field(block, "summary", row.get("summary") or row.get("description"))
            _emit_field(block, "source_ref", row.get("source_ref"), symbolic=True)
            _emit_field(block, "locator_ref", row.get("locator_ref"), symbolic=True)
            _emit_field(block, "citation", row.get("citation"))
            _emit_field(block, "narrative", row.get("narrative"), symbolic=True)
            timeline_name = row.get("timeline")
            start = row.get("start") or row.get("date")
            end = row.get("end") or start
            if timeline_name and start and end:
                timeline_id = _ident(timeline_name)
                timeline = timelines.setdefault(timeline_id, {})
                _merge_bound(timeline, "start", start)
                _merge_bound(timeline, "end", end)
                block.append(f"  appears_on := {timeline_id} @ {_literal(start)}..{_literal(end)};")
            block.append("}")
            entities.append("\n".join(block))
    timeline_blocks = [_timeline_block(name, fields) for name, fields in sorted(timelines.items())]
    lines = sources + timeline_blocks + entities + relationships
    return "\n\n".join(lines) + ("\n" if lines else "")


def import_jsonld(path: str | Path) -> str:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    graph = payload.get("@graph", payload if isinstance(payload, list) else [])
    lines: list[str] = []
    relationships: list[str] = []
    ids: set[str] = set()
    items = [item for item in graph if isinstance(item, dict)]
    for item in items:
        name = _ident(item.get("@id") or item.get("id") or item.get("name") or "")
        if name:
            ids.add(name)
    for item in items:
        raw_type = item.get("@type", "fact")
        type_name = raw_type[-1] if isinstance(raw_type, list) else raw_type
        name = _ident(item.get("@id") or item.get("id") or item.get("name") or "")
        if not name:
            continue
        if str(type_name).lower() == "source":
            block = [f"source {name}: document {{"]
            _emit_field(block, "citation", item.get("citation"))
            _emit_field(block, "title", item.get("title") or item.get("name"))
            _emit_field(block, "url", item.get("url"))
            _emit_field(block, "path", item.get("path"))
            block.append("}")
            lines.append("\n".join(block))
            continue
        block = [f"entity {name}: {_ident(str(type_name).lower())} {{"]
        _emit_field(block, "summary", item.get("summary") or item.get("description") or item.get("name"))
        _emit_field(block, "source_ref", item.get("source_ref"), symbolic=True)
        _emit_field(block, "citation", item.get("citation"))
        for key, value in sorted(item.items()):
            if key in {"@id", "id", "name", "@type", "type", "summary", "description", "source_ref", "citation", "@context", "@graph"}:
                continue
            refs = _jsonld_refs(value)
            if refs:
                for ref in refs:
                    target = _ident(ref)
                    if target:
                        relationships.append(_relationship_line(name, target, key))
            elif _is_scalar(value):
                _emit_field(block, _ident(key), value)
        block.append("}")
        lines.append("\n".join(block))
    lines.extend(relationships)
    return "\n\n".join(lines) + ("\n" if lines else "")


def _is_relationship_row(row: dict[str, Any], kind: str) -> bool:
    return kind in {"rel", "relationship"} or bool((row.get("source") or row.get("from")) and (row.get("target") or row.get("to")) and (row.get("label") or row.get("relationship") or row.get("reltype")))


def _relationship_line(source: str, target: str, label: Any) -> str:
    if label:
        return f"rel {source} -[{json.dumps(str(label))}]-> {target};"
    return f"rel {source} --> {target};"


def _timeline_block(name: str, fields: dict[str, str]) -> str:
    block = [f"timeline {name} {{"]
    for field in ("kind", "parent", "jurisdiction", "procedure", "court"):
        _emit_field(block, field, fields.get(field), symbolic=True)
    _emit_field(block, "start", fields.get("start"))
    _emit_field(block, "end", fields.get("end"))
    block.append("}")
    return "\n".join(block)


def _merge_bound(fields: dict[str, str], key: str, value: Any) -> None:
    if not value:
        return
    text = str(value)
    if key not in fields:
        fields[key] = text
    elif key == "start" and text < fields[key]:
        fields[key] = text
    elif key == "end" and text > fields[key]:
        fields[key] = text


def _jsonld_refs(value: Any) -> list[str]:
    if isinstance(value, dict):
        ref = value.get("@id") or value.get("id")
        return [str(ref)] if ref else []
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(_jsonld_refs(item))
        return refs
    return []


def _is_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def _emit_field(lines: list[str], name: str, value: Any, symbolic: bool = False) -> None:
    if value in (None, ""):
        return
    lines.append(f"  {name} := {_literal(value, symbolic=symbolic)};")


def _literal(value: Any, symbolic: bool = False) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).strip()
    if symbolic and text:
        return _ident(text)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    return json.dumps(text)


def _ident(value: Any) -> str:
    text = re.sub(r"\W+", "_", str(value).strip())
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        return ""
    if text[0].isdigit():
        text = f"_{text}"
    return text
