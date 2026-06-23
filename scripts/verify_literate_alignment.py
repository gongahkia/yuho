#!/usr/bin/env python3
"""Validate literate paragraph alignment heuristics over the Penal Code corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from yuho.cli.commands.literate import _element_descriptions, _paragraph_alignments
from yuho.services.analysis import analyze_file


def _section_text(section: dict) -> str:
    parts: list[str] = []
    if section.get("marginal_note"):
        parts.append(str(section["marginal_note"]))
    if section.get("text"):
        parts.append(str(section["text"]))
    for item in section.get("sub_items") or []:
        if isinstance(item, dict):
            label = str(item.get("label") or "").strip()
            text = str(item.get("text") or "").strip()
            if label and text:
                parts.append(f"{label} {text}")
            elif text:
                parts.append(text)
        elif item:
            parts.append(str(item))
    return "\n\n".join(parts)


def _load_raw_sections(raw_json: Path) -> dict[str, dict]:
    data = json.loads(raw_json.read_text(encoding="utf-8"))
    return {str(section["number"]): section for section in data.get("sections", [])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library-root", default="library/penal_code")
    parser.add_argument("--raw-json", default="library/penal_code/_raw/act.json")
    parser.add_argument("--report-threshold", type=float, default=0.2)
    parser.add_argument("--min-confidence", type=float)
    args = parser.parse_args(argv)

    library_root = Path(args.library_root)
    raw_sections = _load_raw_sections(Path(args.raw_json))
    files = sorted(library_root.glob("s*/statute.yh"))
    errors: list[str] = []
    low: list[tuple[str, str, float]] = []
    confidences: list[float] = []
    element_count = 0
    aligned_count = 0

    for statute_file in files:
        analysis = analyze_file(statute_file, run_semantic=False)
        if analysis.parse_errors or analysis.ast is None:
            errors.append(f"{statute_file}: parse failed")
            continue
        if not analysis.ast.statutes:
            continue
        statute = analysis.ast.statutes[0]
        raw = raw_sections.get(statute.section_number)
        if raw is None:
            errors.append(f"{statute_file}: missing raw text for s{statute.section_number}")
            continue
        elements = _element_descriptions(analysis.ast)
        element_count += len(elements)
        if not elements:
            continue
        alignments = _paragraph_alignments(_section_text(raw), analysis.ast)
        aligned_count += len(alignments)
        if len(alignments) != len(elements):
            errors.append(
                f"{statute_file}: aligned {len(alignments)}/{len(elements)} executable elements"
            )
        for alignment in alignments:
            confidences.append(alignment.confidence)
            if alignment.confidence < args.report_threshold:
                low.append((str(statute_file), alignment.element_name, alignment.confidence))
            if args.min_confidence is not None and alignment.confidence < args.min_confidence:
                errors.append(
                    f"{statute_file}: {alignment.element_name} confidence "
                    f"{alignment.confidence:.3f} < {args.min_confidence:.3f}"
                )

    average = sum(confidences) / len(confidences) if confidences else 0.0
    summary = (
        "Literate alignment: "
        f"files={len(files)} elements={element_count} aligned={aligned_count}/{element_count} "
        f"avg_confidence={average:.3f} "
        f"low_confidence(<{args.report_threshold:g})={len(low)}"
    )
    if low:
        for filename, element, confidence in low[:20]:
            print(f"  low: {filename}::{element} confidence={confidence:.3f}")
        if len(low) > 20:
            print(f"  low: ... {len(low) - 20} more")
    print(summary)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
