"""``yuho refs`` — query the cross-section reference graph (G10)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click

from yuho.cli.error_formatter import Colors, colorize
from yuho.library.graph_lint import lint_reference_graph
from yuho.library.reference_graph import (
    ReferenceGraph,
    build_reference_graph,
)


_DEFAULT_LIBRARY = Path("library/penal_code")
_DEFAULT_COMPARE_LIBRARIES: Tuple[Path, ...] = (
    Path("library/penal_code"),
    Path("library/indian_penal_code"),
)


def run_refs(
    section: Optional[str],
    library_dir: Optional[str],
    direction: str,
    kinds: tuple,
    transitive: bool,
    json_output: bool,
    show_graph: bool,
    scc: bool = False,
) -> None:
    """Implementation of ``yuho refs``.

    Args:
        section: section number to query, or None for full graph.
        library_dir: alternative library root; defaults to library/penal_code.
        direction: "out" (what this section refers to), "in" (what refers to
            this section), or "both".
        kinds: subset of ("subsumes", "amends", "implicit"); empty = all.
        transitive: follow edges transitively (BFS closure).
        json_output: emit JSON instead of human-readable text.
        show_graph: emit the entire graph (only meaningful when section is None).
    """
    root = Path(library_dir) if library_dir else _DEFAULT_LIBRARY
    if not root.exists():
        click.echo(colorize(f"error: library dir not found: {root}", Colors.RED), err=True)
        sys.exit(1)

    graph = build_reference_graph(root)
    edge_kinds = list(kinds) if kinds else None

    if scc:
        _emit_scc(graph, edge_kinds, json_output)
        return

    if section is None:
        if show_graph and json_output:
            click.echo(graph.to_json())
            return
        if show_graph:
            _print_graph_summary(graph)
            return
        # Print stats only.
        d = graph.to_dict()
        if json_output:
            click.echo(json.dumps(d["stats"], indent=2, sort_keys=True))
        else:
            stats = d["stats"]
            click.echo(f"{stats['n_nodes']} nodes")
            click.echo(f"{stats['n_edges']} edges total")
            click.echo(f"  subsumes: {stats['n_subsumes']}")
            click.echo(f"  amends:   {stats['n_amends']}")
            click.echo(f"  implicit: {stats['n_implicit']}")
        return

    if section not in graph.nodes:
        click.echo(
            colorize(f"warning: section {section!r} not found in graph; reporting empty result.",
                     Colors.YELLOW),
            err=True,
        )

    if json_output:
        out = _query_to_dict(graph, section, direction, edge_kinds, transitive)
        click.echo(json.dumps(out, indent=2, sort_keys=True))
        return

    _print_query(graph, section, direction, edge_kinds, transitive)


def _query_to_dict(graph, section, direction, kinds, transitive):
    out = {"section": section, "direction": direction, "kinds": kinds, "transitive": transitive}
    if direction in ("out", "both"):
        if transitive:
            out["outgoing"] = sorted(graph.reachable_from(section, kinds))
        else:
            out["outgoing"] = [
                {"dst": e.dst, "kind": e.kind, "source": e.source_path, "snippet": e.snippet}
                for e in graph.outgoing(section, kinds)
            ]
    if direction in ("in", "both"):
        if transitive:
            out["incoming"] = sorted(graph.reachable_to(section, kinds))
        else:
            out["incoming"] = [
                {"src": e.src, "kind": e.kind, "source": e.source_path, "snippet": e.snippet}
                for e in graph.incoming(section, kinds)
            ]
    return out


def _print_query(graph, section, direction, kinds, transitive):
    klabel = "/".join(kinds) if kinds else "all"
    if direction in ("out", "both"):
        click.echo(colorize(f"=== outgoing from s{section} ({klabel}) ===", Colors.BOLD))
        if transitive:
            for tgt in sorted(graph.reachable_from(section, kinds)):
                click.echo(f"  → s{tgt}")
            click.echo(f"  ({len(graph.reachable_from(section, kinds))} reachable)")
        else:
            edges = graph.outgoing(section, kinds)
            for e in edges:
                tag = colorize(f"[{e.kind}]", _kind_color(e.kind))
                line = f"  s{section} {tag} → s{e.dst}"
                if e.snippet:
                    line += f"  ({_short(e.snippet)})"
                click.echo(line)
            if not edges:
                click.echo("  (none)")
    if direction in ("in", "both"):
        click.echo(colorize(f"=== incoming to s{section} ({klabel}) ===", Colors.BOLD))
        if transitive:
            for src in sorted(graph.reachable_to(section, kinds)):
                click.echo(f"  s{src} →")
            click.echo(f"  ({len(graph.reachable_to(section, kinds))} reverse-reachable)")
        else:
            edges = graph.incoming(section, kinds)
            for e in edges:
                tag = colorize(f"[{e.kind}]", _kind_color(e.kind))
                line = f"  s{e.src} {tag} → s{section}"
                if e.snippet:
                    line += f"  ({_short(e.snippet)})"
                click.echo(line)
            if not edges:
                click.echo("  (none)")


def _print_graph_summary(graph: ReferenceGraph) -> None:
    d = graph.to_dict()
    stats = d["stats"]
    click.echo(colorize("=== reference graph ===", Colors.BOLD))
    click.echo(f"{stats['n_nodes']} sections, {stats['n_edges']} edges")
    click.echo(f"  subsumes: {stats['n_subsumes']}")
    click.echo(f"  amends:   {stats['n_amends']}")
    click.echo(f"  implicit: {stats['n_implicit']}")
    # Top 5 most-referenced sections (by incoming edge count).
    top_in = sorted(
        ((s, len(graph.in_edges.get(s, []))) for s in graph.nodes),
        key=lambda x: -x[1],
    )[:5]
    click.echo(colorize("\ntop 5 most-referenced sections:", Colors.BOLD))
    for s, n in top_in:
        if n == 0:
            break
        click.echo(f"  s{s:<6}  ← {n} incoming")


def _emit_scc(graph: ReferenceGraph, kinds, json_output: bool) -> None:
    """Print SCC analysis: condensation stats + non-trivial cycles + lint warnings."""
    components = graph.find_sccs(kinds)
    cycles = graph.cycles(kinds)
    warnings = lint_reference_graph(
        graph,
        kinds=kinds if kinds else None,
    )
    if json_output:
        payload = {
            "kinds": kinds or ["implicit", "subsumes", "amends"],
            "n_components": len(components),
            "n_cycles": len(cycles),
            "cycles": [sorted(c) for c in cycles],
            "warnings": [
                {
                    "code": w.code,
                    "sections": list(w.sections),
                    "message": w.message,
                    "severity": w.severity,
                }
                for w in warnings
            ],
        }
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    klabel = "/".join(kinds) if kinds else "implicit/subsumes (default)"
    click.echo(colorize(f"=== reference-graph SCC analysis ({klabel}) ===", Colors.BOLD))
    click.echo(f"{len(components)} strongly-connected components")
    click.echo(f"{len(cycles)} non-trivial cycle(s)")
    if not cycles:
        click.echo(colorize("  (no cycles found)", Colors.GREEN))
        return
    click.echo("")
    for i, comp in enumerate(cycles, 1):
        members = ", ".join(f"s{s}" for s in sorted(comp))
        click.echo(colorize(f"  cycle {i} ({len(comp)} sections):", Colors.YELLOW))
        click.echo(f"    {members}")
    if warnings:
        click.echo("")
        click.echo(colorize("lint warnings:", Colors.BOLD))
        for w in warnings:
            tag = colorize(f"[{w.severity}]", Colors.YELLOW if w.severity == "warning" else Colors.RESET)
            click.echo(f"  {tag} {w.message}")


def _kind_color(kind: str) -> str:
    return {"subsumes": Colors.BLUE, "amends": Colors.CYAN, "implicit": Colors.YELLOW}.get(
        kind, Colors.RESET
    )


def _short(text: str, width: int = 60) -> str:
    if len(text) <= width:
        return text
    return text[: width - 1].rstrip() + "…"


# =====================================================================
# §8 cross-jurisdiction comparative-analysis surface (`--compare-libraries`)
# ---------------------------------------------------------------------
# Phase 1 (this skeleton, 2026-04-30): structural-overlap + divergence
# at the bare-section-number level. Works against any library shape:
# * an encoded library (`library/penal_code/sN_*/statute.yh`) — full
#   reference-graph + SCC analysis is available;
# * a raw scrape (`library/indian_penal_code/_raw/act.json`) — only
#   the section-number set is available; SCC/edge comparison is
#   skipped with a documented note.
#
# Phase 2 (deferred until IPC encoding lands): SCC-overlap diff,
# divergent-amendment-paths surfacing, sections renumbered/added/
# repealed comparison. Requires both libraries to be encoded as `.yh`
# so `build_reference_graph` can run on each.
# =====================================================================


_RAW_ACT_RELPATH = Path("_raw") / "act.json"


def _enumerate_library_sections(root: Path) -> Tuple[List[str], str]:
    """Return (sorted_section_numbers, library_kind) for a library
    root.

    Recognised shapes:
      * ``encoded``         — `<root>/sN_*/statute.yh` directory layout;
      * ``raw_act``         — `<root>/_raw/act.json` produced by the
        scrape pipelines (e.g. ``scrape_indiacode.py act``);
      * ``encoded+raw_act`` — both present (proof-of-concept encoding
        plus the wider raw scrape; section-number set is the union);
      * ``empty``           — directory exists but matches neither shape.

    Section numbers are normalised to the bare ``<num>[<suffix>]``
    form with no leading ``s`` (matching `ReferenceGraph.nodes`)."""
    if not root.exists() or not root.is_dir():
        return [], "missing"

    encoded: List[str] = []
    pattern = re.compile(r"^s(\d+[A-Z]*)_")
    for child in root.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue
        m = pattern.match(child.name)
        if m and (child / "statute.yh").exists():
            encoded.append(m.group(1))

    raw_nums: List[str] = []
    raw_path = root / _RAW_ACT_RELPATH
    raw_unreadable = False
    if raw_path.exists():
        try:
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            for s in raw.get("sections", []) or []:
                n = str(s.get("number", "")).strip()
                if n:
                    raw_nums.append(n)
        except (OSError, json.JSONDecodeError):
            raw_unreadable = True

    # Both shapes coexist (e.g. IPC: 8 sections encoded as
    # proof-of-concept + 493-section raw scrape) — union the section-
    # number sets so phase-1 overlap analysis sees the wider corpus.
    if encoded and raw_nums:
        merged = sorted(set(encoded) | set(raw_nums), key=_section_sort_key)
        return merged, "encoded+raw_act"
    if encoded:
        return sorted(set(encoded), key=_section_sort_key), "encoded"
    if raw_nums:
        return sorted(set(raw_nums), key=_section_sort_key), "raw_act"
    if raw_unreadable:
        return [], "raw_act_unreadable"
    return [], "empty"


def _section_sort_key(num: str) -> Tuple[int, str]:
    """Sort `123` < `123A` < `124`. Falls back to lexicographic on
    parse failure."""
    m = re.match(r"^(\d+)([A-Z]*)$", num)
    if m:
        return (int(m.group(1)), m.group(2))
    return (10**9, num)


def run_compare_libraries(
    libraries: Tuple[Path, ...],
    json_output: bool,
) -> int:
    """Implementation of ``yuho refs --compare-libraries``.

    Returns the process exit code (0 = success even when libraries
    are partial, 1 = no usable libraries found at all)."""
    enumerated: Dict[str, Dict[str, Any]] = {}
    for lib in libraries:
        sections, kind = _enumerate_library_sections(lib)
        enumerated[str(lib)] = {
            "kind": kind,
            "n_sections": len(sections),
            "sections": sections,
        }

    usable = [k for k, v in enumerated.items()
              if v["kind"] in {"encoded", "raw_act", "encoded+raw_act"}]
    if not usable:
        click.echo(
            colorize(
                "no usable library found — pass --library-path for each "
                "or run scripts/scrape_*.py first",
                Colors.RED,
            ),
            err=True,
        )
        return 1

    # Pairwise overlap on section-number sets. With two libraries we
    # report a single overlap; with N>2 we emit each pair plus the
    # full-intersection count.
    lib_keys = list(enumerated.keys())
    pairs: List[Dict[str, Any]] = []
    for i in range(len(lib_keys)):
        for j in range(i + 1, len(lib_keys)):
            a, b = lib_keys[i], lib_keys[j]
            sa = set(enumerated[a]["sections"])
            sb = set(enumerated[b]["sections"])
            pairs.append({
                "a": a,
                "b": b,
                "shared": sorted(sa & sb, key=_section_sort_key),
                "only_a": sorted(sa - sb, key=_section_sort_key),
                "only_b": sorted(sb - sa, key=_section_sort_key),
            })
    full_intersection = sorted(
        set.intersection(*(set(enumerated[k]["sections"]) for k in lib_keys))
        if lib_keys else set(),
        key=_section_sort_key,
    )

    payload: Dict[str, Any] = {
        "libraries": enumerated,
        "pairs": pairs,
        "full_intersection_count": len(full_intersection),
        "full_intersection": full_intersection,
        "phase": "phase-1-section-number-overlap",
        "phase_2_pending": (
            "SCC-overlap, divergent-amendment-paths, renumbered/added/"
            "repealed analysis pending IPC corpus encoding (deferred per "
            "TODO §8 — months of agent runs to encode 493 IPC sections)"
        ),
    }

    if json_output:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    click.echo(colorize("=== cross-library section overlap (Phase 1) ===",
                        Colors.BOLD))
    click.echo("")
    for k, v in enumerated.items():
        kind = v["kind"]
        tag_color = (Colors.GREEN if kind == "encoded"
                     else Colors.CYAN if kind == "raw_act"
                     else Colors.YELLOW)
        click.echo(f"  {colorize('['+kind+']', tag_color)} {k}: "
                   f"{v['n_sections']} sections")
    click.echo("")
    for p in pairs:
        click.echo(colorize(f"--- {p['a']}  ↔  {p['b']} ---", Colors.BOLD))
        click.echo(f"  shared:  {len(p['shared'])}")
        click.echo(f"  only-a:  {len(p['only_a'])}")
        click.echo(f"  only-b:  {len(p['only_b'])}")
        if p["shared"]:
            sample = ", ".join("s" + n for n in p["shared"][:10])
            tail = "" if len(p["shared"]) <= 10 else f"  (+{len(p['shared']) - 10} more)"
            click.echo(f"    sample shared: {sample}{tail}")
    click.echo("")
    click.echo(colorize(
        f"full intersection across {len(lib_keys)} libraries: "
        f"{len(full_intersection)} sections",
        Colors.BOLD,
    ))
    click.echo("")
    click.echo(colorize(
        "Phase 2 (SCC-overlap, amendment paths, renumbered/added/"
        "repealed) pending IPC corpus encoding.",
        Colors.YELLOW,
    ))
    return 0
