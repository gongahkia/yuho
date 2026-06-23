"""Source map generation for Yuho transpiler outputs."""

from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from html import escape as html_escape
from typing import Any, Iterable

from yuho.ast import nodes


_BASE64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def build_source_map(
    output: str,
    ast: nodes.ModuleNode,
    *,
    generated_file: str = "",
    max_mappings: int = 2000,
) -> dict[str, Any]:
    """Build a Source Map V3-shaped object with Yuho output-span extensions."""
    line_starts = _line_starts(output)
    sources: list[str] = []
    source_indexes: dict[str, int] = {}
    names: list[str] = []
    name_indexes: dict[str, int] = {}
    spans: list[dict[str, Any]] = []
    mapping_entries: list[dict[str, int]] = []
    used_output_spans: set[tuple[int, int]] = set()

    for path, node in _walk(ast):
        if len(spans) >= max_mappings:
            break
        loc = getattr(node, "source_location", None)
        if loc is None or loc.line <= 0:
            continue

        token = _first_output_token(output, node, used_output_spans)
        if token is None:
            continue

        token_text, start_offset = token
        end_offset = start_offset + len(token_text)
        used_output_spans.add((start_offset, end_offset))
        source_index = _index_for(sources, source_indexes, loc.file)
        name = _node_name(node)
        name_index = _index_for(names, name_indexes, name)
        gen_start_line, gen_start_col = _line_col(line_starts, start_offset)
        gen_end_line, gen_end_col = _line_col(line_starts, end_offset)
        original_line = max(loc.line - 1, 0)
        original_col = max(loc.col - 1, 0)

        mapping_entries.append(
            {
                "generated_line": gen_start_line,
                "generated_col": gen_start_col,
                "source": source_index,
                "original_line": original_line,
                "original_col": original_col,
                "name": name_index,
            }
        )
        spans.append(
            {
                "name": name,
                "node": type(node).__name__,
                "path": path,
                "generated": {
                    "line": gen_start_line,
                    "column": gen_start_col,
                    "endLine": gen_end_line,
                    "endColumn": gen_end_col,
                    "offset": start_offset,
                    "endOffset": end_offset,
                },
                "source": source_index,
                "original": {
                    "line": original_line,
                    "column": original_col,
                    "endLine": max(loc.end_line - 1, 0),
                    "endColumn": max(loc.end_col - 1, 0),
                    "offset": loc.offset,
                    "endOffset": loc.end_offset,
                },
                "source_location": {
                    "file": loc.file,
                    "line": loc.line,
                    "col": loc.col,
                    "end_line": loc.end_line,
                    "end_col": loc.end_col,
                    "offset": loc.offset,
                    "end_offset": loc.end_offset,
                },
            }
        )

    mapping_entries.sort(key=lambda entry: (entry["generated_line"], entry["generated_col"]))
    spans.sort(key=lambda span: (span["generated"]["line"], span["generated"]["column"]))
    return {
        "version": 3,
        "file": generated_file,
        "sourceRoot": "",
        "sources": sources,
        "names": names,
        "mappings": _encode_mappings(mapping_entries),
        "x_yuho_spans": spans,
    }


def required_source_nodes(ast: nodes.ModuleNode) -> list[dict[str, str]]:
    """Return AST nodes that must be traceable in legal-facing exports."""
    required: list[dict[str, str]] = []
    for path, node in _walk(ast):
        if isinstance(node, nodes.ElementNode):
            required.append(
                {
                    "path": path,
                    "node": "ElementNode",
                    "name": node.name,
                }
            )
        elif isinstance(node, nodes.ExceptionNode):
            required.append(
                {
                    "path": path,
                    "node": "ExceptionNode",
                    "name": node.label or "unlabeled",
                }
            )
    return required


def source_map_coverage(
    source_map: dict[str, Any] | None,
    ast: nodes.ModuleNode,
) -> dict[str, Any]:
    """Report required element/exception source-map coverage for one output."""
    required = required_source_nodes(ast)
    spans = (source_map or {}).get("x_yuho_spans", [])
    covered = {(span.get("path"), span.get("node")) for span in spans}
    missing = [item for item in required if (item["path"], item["node"]) not in covered]
    return {
        "required": len(required),
        "covered": len(required) - len(missing),
        "missing": missing,
    }


def _walk(root: nodes.ASTNode) -> Iterable[tuple[str, nodes.ASTNode]]:
    stack: list[tuple[str, nodes.ASTNode]] = [("$", root)]
    while stack:
        path, node = stack.pop()
        yield path, node
        children = list(node.children())
        for index, child in reversed(list(enumerate(children))):
            stack.append((f"{path}.children[{index}]", child))


def _first_output_token(
    output: str,
    node: nodes.ASTNode,
    used_output_spans: set[tuple[int, int]],
) -> tuple[str, int] | None:
    for candidate in _candidate_tokens(node):
        start = output.find(candidate)
        while start != -1:
            span = (start, start + len(candidate))
            if span not in used_output_spans:
                return (candidate, start)
            start = output.find(candidate, start + 1)
    return None


def _candidate_tokens(node: nodes.ASTNode) -> Iterable[str]:
    values: list[str] = []

    if isinstance(node, nodes.StatuteNode):
        values.extend(
            [
                f"Section {node.section_number}",
                f"section {node.section_number}",
                f"s{node.section_number}",
                node.section_number,
            ]
        )
        if node.title:
            values.append(node.title.value)
    elif isinstance(node, nodes.ElementNode):
        values.extend(
            [
                node.name,
                node.element_type,
                node.element_type.replace("_", " "),
            ]
        )
        if isinstance(node.description, nodes.StringLit):
            values.append(node.description.value)
    elif isinstance(node, nodes.ElementGroupNode):
        values.extend([node.combinator, node.combinator.replace("_", " ").upper()])
    elif isinstance(node, nodes.ExceptionNode):
        values.append(node.label or "unlabeled")
        values.append(node.condition.value)
        if node.effect:
            values.append(node.effect.value)
    elif isinstance(node, nodes.StringLit):
        values.append(node.value)
    elif isinstance(node, nodes.IntLit):
        values.append(str(node.value))
    elif isinstance(node, nodes.FloatLit):
        values.append(str(node.value))
    elif isinstance(node, nodes.BoolLit):
        values.extend(["TRUE" if node.value else "FALSE", "true" if node.value else "false"])

    for attr in (
        "name",
        "label",
        "field_name",
        "identifier",
        "operator",
        "term",
        "number",
        "jurisdiction",
        "effective_date",
        "repealed_date",
    ):
        value = getattr(node, attr, None)
        if isinstance(value, str):
            values.append(value)

    seen: set[str] = set()
    for value in values:
        for candidate in _token_variants(value):
            if len(candidate) < 2 or candidate in seen:
                continue
            seen.add(candidate)
            yield candidate


def _token_variants(value: str) -> Iterable[str]:
    text = value.strip()
    if not text:
        return ()
    variants = [text, html_escape(text, quote=True)]
    if "_" in text:
        variants.extend([text.replace("_", " "), text.replace("_", " ").upper()])
    return tuple(variants)


def _node_name(node: nodes.ASTNode) -> str:
    for attr in ("section_number", "name", "label", "field_name", "identifier", "number"):
        value = getattr(node, attr, None)
        if isinstance(value, str) and value:
            return f"{type(node).__name__}:{value}"
    if isinstance(node, nodes.StringLit):
        return f"StringLit:{node.value[:40]}"
    return type(node).__name__


def _index_for(values: list[str], indexes: dict[str, int], value: str) -> int:
    if value not in indexes:
        indexes[value] = len(values)
        values.append(value)
    return indexes[value]


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for index, char in enumerate(text):
        if char == "\n":
            starts.append(index + 1)
    return starts


def _line_col(line_starts: list[int], offset: int) -> tuple[int, int]:
    line = bisect_right(line_starts, offset) - 1
    return (line, offset - line_starts[line])


def _encode_mappings(entries: list[dict[str, int]]) -> str:
    if not entries:
        return ""

    by_line: dict[int, list[dict[str, int]]] = defaultdict(list)
    for entry in entries:
        by_line[entry["generated_line"]].append(entry)

    lines: list[str] = []
    prev_source = 0
    prev_original_line = 0
    prev_original_col = 0
    prev_name = 0

    for line in range(max(by_line) + 1):
        segments: list[str] = []
        prev_generated_col = 0
        for entry in sorted(by_line.get(line, ()), key=lambda e: e["generated_col"]):
            fields = [
                entry["generated_col"] - prev_generated_col,
                entry["source"] - prev_source,
                entry["original_line"] - prev_original_line,
                entry["original_col"] - prev_original_col,
                entry["name"] - prev_name,
            ]
            segments.append("".join(_encode_vlq(field) for field in fields))
            prev_generated_col = entry["generated_col"]
            prev_source = entry["source"]
            prev_original_line = entry["original_line"]
            prev_original_col = entry["original_col"]
            prev_name = entry["name"]
        lines.append(",".join(segments))

    return ";".join(lines)


def _encode_vlq(value: int) -> str:
    vlq = ((-value) << 1) + 1 if value < 0 else value << 1
    chars: list[str] = []
    while True:
        digit = vlq & 31
        vlq >>= 5
        if vlq:
            digit |= 32
        chars.append(_BASE64[digit])
        if not vlq:
            break
    return "".join(chars)
