"""``yuho refs`` — query the cross-section reference graph (G10)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from yuho.cli.error_formatter import Colors, colorize
from yuho.library.graph_lint import lint_reference_graph
from yuho.library.reference_graph import (
    ReferenceGraph,
    build_reference_graph,
)


_DEFAULT_LIBRARY = Path("library/penal_code")


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
