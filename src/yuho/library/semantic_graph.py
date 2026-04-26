"""Library-wide semantic graph: definitions ↔ elements ↔ exceptions.

The cross-section reference graph in :mod:`yuho.library.reference_graph`
carries one node per encoded section and one edge per cross-section
reference (subsumes / amends / implicit textual mention). Useful, but
section-granular: it cannot answer "which sections share the term
``deceive``?" or "which exceptions defeat which other exceptions?".

This module fills that layer in. Nodes carry **kind**:

* ``section``    — one per encoded ``statute N``
* ``definition`` — one per ``definitions { term := "..." }`` entry
* ``element``    — one per ``element_type name := "..."`` entry
                   (flattened across nested ``all_of`` / ``any_of`` groups)
* ``exception``  — one per ``exception <label> { ... }`` block

Edges carry **kind**:

* ``contains``    — section → (definition | element | exception); the
                    structural ownership backbone.
* ``mentions``    — element/exception description text mentions a
                    definition's term (≥ 3 chars, word-bounded). Surfaces
                    where defined terms are actually used.
* ``defeats``     — exception → exception (same section), reflecting the
                    G13 priority DAG.
* ``shares_term`` — definition ↔ definition across sections sharing the
                    same term name. Catches "every section that defines
                    'dishonestly'".

The graph is built once per library and dumped to JSON for client-side
rendering on ``/semantic-graph.html``.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

from yuho.ast import nodes


_NODE_KINDS = ("section", "definition", "element", "exception")
_EDGE_KINDS = ("contains", "mentions", "defeats", "shares_term")
_MIN_TERM_LEN = 3
_WORD_BOUNDARY = re.compile(r"[^A-Za-z0-9_]")


@dataclass(frozen=True)
class SemanticNode:
    """One node in the semantic graph."""
    id: str               # globally unique, e.g. "elem:415:deception"
    kind: str             # one of _NODE_KINDS
    section: str          # owning section number (or "" for cross-cutting nodes)
    label: str            # display label
    element_type: Optional[str] = None  # only for kind="element"


@dataclass(frozen=True)
class SemanticEdge:
    src: str
    dst: str
    kind: str
    snippet: Optional[str] = None  # short context for `mentions` edges


@dataclass
class SemanticGraph:
    """Adjacency-list semantic graph. No networkx dependency."""
    nodes: List[SemanticNode] = field(default_factory=list)
    edges: List[SemanticEdge] = field(default_factory=list)
    _seen: Set[str] = field(default_factory=set)

    def add_node(self, node: SemanticNode) -> None:
        if node.kind not in _NODE_KINDS:
            raise ValueError(f"unknown node kind: {node.kind}")
        if node.id in self._seen:
            return
        self._seen.add(node.id)
        self.nodes.append(node)

    def add_edge(self, edge: SemanticEdge) -> None:
        if edge.kind not in _EDGE_KINDS:
            raise ValueError(f"unknown edge kind: {edge.kind}")
        self.edges.append(edge)

    def stats(self) -> Dict[str, int]:
        out: Dict[str, int] = defaultdict(int)
        for n in self.nodes:
            out[f"n_{n.kind}"] += 1
        for e in self.edges:
            out[f"n_{e.kind}"] += 1
        return dict(out)

    def to_dict(self) -> Dict:
        return {
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [asdict(e) for e in self.edges],
            "stats": self.stats(),
        }


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _flatten_elements(elements) -> List[nodes.ElementNode]:
    out: List[nodes.ElementNode] = []
    stack = list(elements)
    while stack:
        item = stack.pop(0)
        if isinstance(item, nodes.ElementNode):
            out.append(item)
        elif isinstance(item, nodes.ElementGroupNode):
            stack[:0] = list(item.members)
    return out


_KIND_PREFIX = {
    "section": "sec",
    "definition": "def",
    "element": "elem",
    "exception": "exc",
}


def _node_id(kind: str, section: str, name: str) -> str:
    """Build a stable node id like `elem:415:deception`. Section + element
    name combine for uniqueness; the short kind prefix keeps payloads
    compact for the cytoscape render."""
    prefix = _KIND_PREFIX[kind]
    safe = re.sub(r"[^A-Za-z0-9_]", "_", name) if name else ""
    return f"{prefix}:{section}:{safe}" if name else f"{prefix}:{section}"


def _string_value(maybe_node) -> str:
    if hasattr(maybe_node, "value") and isinstance(maybe_node.value, str):
        return maybe_node.value
    return str(maybe_node or "")


def add_statute_to_graph(g: SemanticGraph, stat: nodes.StatuteNode) -> None:
    """Add one statute's nodes + intra-section edges to the graph."""
    section = stat.section_number
    title = stat.title.value if stat.title else "(untitled)"
    sec_id = _node_id("section", section, "")
    g.add_node(SemanticNode(
        id=sec_id, kind="section", section=section, label=f"s{section} {title}",
    ))

    # --- Definitions ---
    defs_by_term: Dict[str, str] = {}
    for d in stat.definitions:
        term = getattr(d, "term", None) or getattr(d, "name", "")
        if not term:
            continue
        node_id = _node_id("definition", section, term)
        g.add_node(SemanticNode(
            id=node_id, kind="definition", section=section, label=str(term),
        ))
        g.add_edge(SemanticEdge(src=sec_id, dst=node_id, kind="contains"))
        defs_by_term[str(term)] = node_id

    # --- Elements (flattened across combinator nesting) ---
    elem_id_by_name: Dict[str, str] = {}
    for el in _flatten_elements(stat.elements):
        node_id = _node_id("element", section, el.name)
        g.add_node(SemanticNode(
            id=node_id, kind="element", section=section, label=el.name,
            element_type=el.element_type,
        ))
        g.add_edge(SemanticEdge(src=sec_id, dst=node_id, kind="contains"))
        elem_id_by_name[el.name] = node_id
        # Mentions: description text references a defined term?
        desc = _string_value(getattr(el, "description", None))
        for term, def_id in defs_by_term.items():
            if len(term) < _MIN_TERM_LEN:
                continue
            if _word_in(desc, term):
                g.add_edge(SemanticEdge(
                    src=node_id, dst=def_id, kind="mentions",
                    snippet=desc[:120],
                ))

    # --- Exceptions ---
    exc_id_by_label: Dict[str, str] = {}
    for exc in stat.exceptions:
        label = getattr(exc, "label", None) or "(unlabeled)"
        node_id = _node_id("exception", section, label)
        g.add_node(SemanticNode(
            id=node_id, kind="exception", section=section, label=label,
        ))
        g.add_edge(SemanticEdge(src=sec_id, dst=node_id, kind="contains"))
        exc_id_by_label[label] = node_id

    # Defeats edges (intra-section, exc -> exc).
    for exc in stat.exceptions:
        defeats = getattr(exc, "defeats", None)
        if defeats and exc.label and defeats in exc_id_by_label:
            g.add_edge(SemanticEdge(
                src=exc_id_by_label[exc.label],
                dst=exc_id_by_label[defeats],
                kind="defeats",
            ))


def add_shares_term_edges(g: SemanticGraph) -> None:
    """Cross-section ``shares_term`` edges: link every pair of definition
    nodes that share the same term name. The graph remains undirected
    in semantics (we emit one edge per pair); cytoscape renders both
    endpoints as a single line."""
    by_term: Dict[str, List[str]] = defaultdict(list)
    for n in g.nodes:
        if n.kind == "definition":
            by_term[n.label].append(n.id)
    for term, ids in by_term.items():
        if len(ids) < 2:
            continue
        # Emit one edge per unordered pair.
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                g.add_edge(SemanticEdge(
                    src=ids[i], dst=ids[j], kind="shares_term",
                    snippet=term,
                ))


def _word_in(haystack: str, needle: str) -> bool:
    """Word-bounded case-insensitive substring check."""
    if not haystack or not needle:
        return False
    lo_h = haystack.lower()
    lo_n = needle.lower()
    idx = 0
    while True:
        i = lo_h.find(lo_n, idx)
        if i < 0:
            return False
        before_ok = i == 0 or _WORD_BOUNDARY.match(haystack[i - 1])
        end = i + len(needle)
        after_ok = end == len(haystack) or _WORD_BOUNDARY.match(haystack[end])
        if before_ok and after_ok:
            return True
        idx = i + 1


# ---------------------------------------------------------------------------
# Library entrypoint
# ---------------------------------------------------------------------------


def build_semantic_graph(library_dir: Path) -> SemanticGraph:
    """Build the full semantic graph for an encoded library directory."""
    from yuho.services.analysis import analyze_file
    g = SemanticGraph()
    for yh_file in sorted(library_dir.glob("*/statute.yh")):
        try:
            analysis = analyze_file(yh_file, run_semantic=False)
        except Exception:
            continue
        if analysis.parse_errors or analysis.ast is None:
            continue
        for stat in analysis.ast.statutes:
            add_statute_to_graph(g, stat)
    add_shares_term_edges(g)
    return g
