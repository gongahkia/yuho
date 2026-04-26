#!/usr/bin/env python3
"""Synthesise LLM-eval fixtures from the encoded library.

For every encoded section with at least one illustration AND at least
one leaf element, produce one fixture per illustration. The
illustration text is the scenario; the leaf element names are the
ground-truth satisfied elements. Tagged ``synth:true`` so the
generated fixtures are distinguishable from hand-authored ones.

Output target: the ``evals/`` LLM-evaluation harness (scenario-shape
fixtures + scoring runner). Distinct from the older ``benchmarks/``
JSONL dataset pack — see each directory's README for the difference.

Usage::

    python scripts/synthesise_eval_fixtures.py
    python scripts/synthesise_eval_fixtures.py --max-sections 30
    python scripts/synthesise_eval_fixtures.py --out-dir evals/fixtures

Caveats
-------

The Singapore Penal Code's illustrations are deliberately chosen as
canonical *positive* examples — they satisfy the section's elements
by construction. A small minority are explicit *negative* examples
("Illustration (b): A is not guilty of theft if …"); a polarity
keyword scan tags those as ``polarity:negative`` so a downstream
filter can skip them.

Generated fixtures cover the structural baseline. Hand-authored
fixtures (existing 22 in ``evals/fixtures/``) cover the
edge-case + multi-section + exception-fires variants the
illustrations don't naturally exercise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from yuho.ast import nodes  # noqa: E402
from yuho.services.analysis import analyze_file  # noqa: E402

OUT_DIR_DEFAULT = REPO / "evals" / "fixtures"

_NEGATIVE_HINTS = (
    "is not", "would not", "no theft", "no offence", "is not guilty",
    "does not commit",
)

# Illustrations whose text is a cross-reference, deletion notice, or
# placeholder are not real fact patterns and would corrupt the
# benchmark — the LLM cannot reason from them, and two fixtures with
# the same boilerplate text resolve to the same prompt with different
# expected sections (an unsolvable structural ambiguity).
_DROP_PATTERNS = (
    re.compile(r"^\s*\([a-z]\)\s*\[\s*deleted", re.IGNORECASE),
    re.compile(r"\[\s*deleted by act\b", re.IGNORECASE),
    re.compile(r"^\s*same\b.*\billustration\b.*\bsection\b", re.IGNORECASE),
    re.compile(r"^\s*see\s+(?:illustration|section)\b", re.IGNORECASE),
    re.compile(r"^\s*the\s+last\s+section\s+is\s+subject\s+to\s+the\s+same\b",
               re.IGNORECASE),
)


def _is_useful_illustration(text: str) -> bool:
    """Drop placeholder / cross-reference / deletion-notice illustrations."""
    if not text or len(text.strip()) < 20:
        return False
    for pat in _DROP_PATTERNS:
        if pat.search(text):
            return False
    return True


def _flatten_element_names(elements) -> List[str]:
    out: List[str] = []
    stack = list(elements or ())
    while stack:
        item = stack.pop(0)
        if isinstance(item, nodes.ElementNode):
            out.append(item.name)
        elif isinstance(item, nodes.ElementGroupNode):
            stack[:0] = list(item.members)
    return out


def _all_element_names(statute: nodes.StatuteNode) -> List[str]:
    """Top-level + every subsection's leaf element names, deduped."""
    seen: set[str] = set()
    out: List[str] = []
    for n in _flatten_element_names(statute.elements or ()):
        if n not in seen:
            seen.add(n)
            out.append(n)
    for sub in (statute.subsections or ()):
        for n in _flatten_element_names(getattr(sub, "elements", ()) or ()):
            if n not in seen:
                seen.add(n)
                out.append(n)
    return out


def _illustration_text(illus) -> str:
    desc_node = getattr(illus, "description", None)
    if hasattr(desc_node, "value"):
        return desc_node.value
    return str(desc_node or "").strip()


def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "ill"


def _fixture_yaml(
    fixture_id: str, section: str, scenario: str,
    elements: List[str], polarity_negative: bool,
) -> str:
    """Render a single fixture as YAML (string output)."""
    # Hand-roll YAML — fewer install deps + we control quoting.
    scenario_lines = scenario.strip().splitlines() or [""]
    scenario_block = "  " + "\n  ".join(scenario_lines)
    if polarity_negative:
        # Negative-polarity fixtures: ground-truth elements is empty
        # because the scenario doesn't satisfy the section. The LLM
        # is graded on identifying that no elements fire.
        elements_inline = "[]"
        fact_facts = "\n".join(f"  {n}: false" for n in elements) or "  {}"
    else:
        elements_inline = "[" + ", ".join(elements) + "]"
        fact_facts = "\n".join(f"  {n}: true" for n in elements) or "  {}"
    tags = ["synth:true"]
    if polarity_negative:
        tags.append("polarity:negative")
    tags_inline = "[" + ", ".join(tags) + "]"
    return (
        f"id: {fixture_id}\n"
        f"section: \"{section}\"\n"
        f"scenario: |\n{scenario_block}\n"
        f"ground_truth:\n"
        f"  section: \"{section}\"\n"
        f"  satisfied_elements: {elements_inline}\n"
        f"  fired_exception: null\n"
        f"fact_facts:\n{fact_facts}\n"
        f"tags: {tags_inline}\n"
    )


def synthesise(
    library: Path, out_dir: Path,
    *, max_sections: int = 0, dry_run: bool = False,
) -> dict:
    """Generate fixtures. Returns a summary dict."""
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = {fp.stem for fp in out_dir.glob("*.yaml")}

    n_sections = n_skipped = n_written = n_negative = 0
    skipped_reasons: dict = {}
    written: List[str] = []

    sections = sorted(library.glob("s*/statute.yh"))
    if max_sections:
        sections = sections[:max_sections]

    for stat_path in sections:
        n_sections += 1
        try:
            r = analyze_file(stat_path, run_semantic=False)
        except Exception as exc:
            skipped_reasons[f"parse-error:{type(exc).__name__}"] = \
                skipped_reasons.get(f"parse-error:{type(exc).__name__}", 0) + 1
            continue
        if not r.ast or not r.ast.statutes:
            skipped_reasons["no-ast"] = skipped_reasons.get("no-ast", 0) + 1
            continue
        statute = r.ast.statutes[0]
        elements = _all_element_names(statute)
        if not elements:
            skipped_reasons["no-elements"] = skipped_reasons.get("no-elements", 0) + 1
            continue
        if not statute.illustrations:
            skipped_reasons["no-illustrations"] = skipped_reasons.get("no-illustrations", 0) + 1
            continue

        section = statute.section_number
        for i, illus in enumerate(statute.illustrations):
            scenario = _illustration_text(illus)
            if not _is_useful_illustration(scenario):
                continue
            label = getattr(illus, "label", None) or getattr(illus, "name", None)
            slug = _slugify(label) if label else f"ill-{i}"
            fixture_id = f"s{section}-{slug}"
            if fixture_id in existing:
                # Hand-authored hand-wins; skip silently.
                n_skipped += 1
                continue

            polarity_negative = any(h in scenario.lower() for h in _NEGATIVE_HINTS)
            if polarity_negative:
                n_negative += 1

            yaml_text = _fixture_yaml(
                fixture_id, section, scenario, elements, polarity_negative,
            )
            if dry_run:
                print(f"--- {fixture_id}.yaml ---\n{yaml_text}")
            else:
                (out_dir / f"{fixture_id}.yaml").write_text(yaml_text, encoding="utf-8")
            n_written += 1
            written.append(fixture_id)

    return {
        "n_sections_walked": n_sections,
        "n_fixtures_written": n_written,
        "n_negative_polarity": n_negative,
        "n_skipped_existing": n_skipped,
        "skipped_section_reasons": skipped_reasons,
        "out_dir": str(out_dir),
        "written": written[:5],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--library", default=str(REPO / "library" / "penal_code"))
    p.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    p.add_argument("--max-sections", type=int, default=0,
                   help="Cap sections walked (0 = no cap)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print fixtures to stdout instead of writing")
    args = p.parse_args()

    summary = synthesise(
        Path(args.library), args.out_dir,
        max_sections=args.max_sections, dry_run=args.dry_run,
    )
    import json as _json
    print(_json.dumps(summary, indent=2, ensure_ascii=False), file=sys.stderr)
    return 0 if summary["n_fixtures_written"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
