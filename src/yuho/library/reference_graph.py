"""Cross-section reference graph for the encoded library (G10).

Walks every encoded statute and emits a typed directed edge for each
explicit cross-section reference (`subsumes`, `amends`) plus implicit
references (mentions like ``s415`` or ``section 415`` inside element
descriptions, doc comments, and case-law holdings).

The resulting :class:`ReferenceGraph` answers reachability queries used by
LSP goto-definition, the public explorer's cross-reference graph page,
Tarjan-SCC analysis (planned), and the lam4-style ``IS_INFRINGED``
predicate (planned).

Implementation note: we do not depend on networkx; the graph is small
(524 nodes, low-thousand edges) and a hand-written adjacency-list
representation is enough.
"""

from __future__ import annotations

import re
import json
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from yuho.ast import nodes


_EDGE_KINDS = ("subsumes", "amends", "implicit")

# Matches "s415", "s.415", "s. 415", "s.415A", "s. 376AA", "section 415",
# "section 415A", and "Section 415" with optional trailing alpha suffix.
# Conservative: requires a token boundary on the left and digits on the right.
_IMPLICIT_REF_RE = re.compile(
    r"\b(?:[Ss]ection\s+|s\.?\s*)(\d+[A-Z]{0,3})\b"
)


@dataclass(frozen=True)
class ReferenceEdge:
    """A typed directed edge from one statute section to another."""

    src: str            # the section where the reference originates (e.g. "415")
    dst: str            # the section being referenced (e.g. "300")
    kind: str           # one of _EDGE_KINDS
    source_path: str    # repository-relative .yh file path
    snippet: Optional[str] = None  # short textual context (implicit edges only)


@dataclass
class ReferenceGraph:
    """Adjacency-list representation of the cross-section reference graph."""

    out_edges: dict = field(default_factory=lambda: defaultdict(list))
    in_edges: dict = field(default_factory=lambda: defaultdict(list))
    nodes: Set[str] = field(default_factory=set)

    def add(self, edge: ReferenceEdge) -> None:
        """Add an edge, registering both endpoints as nodes."""
        if edge.kind not in _EDGE_KINDS:
            raise ValueError(f"unknown edge kind: {edge.kind}")
        self.nodes.add(edge.src)
        self.nodes.add(edge.dst)
        self.out_edges[edge.src].append(edge)
        self.in_edges[edge.dst].append(edge)

    # -----------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------

    def outgoing(self, section: str, kinds: Optional[Iterable[str]] = None) -> List[ReferenceEdge]:
        """Edges leaving ``section``."""
        edges = self.out_edges.get(section, [])
        if kinds is None:
            return list(edges)
        kset = set(kinds)
        return [e for e in edges if e.kind in kset]

    def incoming(self, section: str, kinds: Optional[Iterable[str]] = None) -> List[ReferenceEdge]:
        """Edges entering ``section``."""
        edges = self.in_edges.get(section, [])
        if kinds is None:
            return list(edges)
        kset = set(kinds)
        return [e for e in edges if e.kind in kset]

    def neighbours_out(self, section: str, kinds: Optional[Iterable[str]] = None) -> List[str]:
        """Section numbers reachable from ``section`` in one step."""
        seen: List[str] = []
        for e in self.outgoing(section, kinds):
            if e.dst not in seen:
                seen.append(e.dst)
        return seen

    def neighbours_in(self, section: str, kinds: Optional[Iterable[str]] = None) -> List[str]:
        """Section numbers that point into ``section`` in one step."""
        seen: List[str] = []
        for e in self.incoming(section, kinds):
            if e.src not in seen:
                seen.append(e.src)
        return seen

    def reachable_from(
        self, section: str, kinds: Optional[Iterable[str]] = None
    ) -> Set[str]:
        """Transitive forward closure (BFS) from ``section``."""
        return self._closure(section, kinds, direction="out")

    def reachable_to(
        self, section: str, kinds: Optional[Iterable[str]] = None
    ) -> Set[str]:
        """Transitive backward closure (BFS) from ``section``."""
        return self._closure(section, kinds, direction="in")

    def _closure(self, start: str, kinds: Optional[Iterable[str]], direction: str) -> Set[str]:
        seen: Set[str] = set()
        queue: deque = deque([start])
        kset = set(kinds) if kinds else None
        edge_table = self.out_edges if direction == "out" else self.in_edges
        attr = "dst" if direction == "out" else "src"
        while queue:
            cur = queue.popleft()
            for edge in edge_table.get(cur, []):
                if kset is not None and edge.kind not in kset:
                    continue
                nxt = getattr(edge, attr)
                if nxt in seen:
                    continue
                seen.add(nxt)
                queue.append(nxt)
        seen.discard(start)
        return seen

    # -----------------------------------------------------------------
    # Stats and serialisation
    # -----------------------------------------------------------------

    def edge_count(self, kind: Optional[str] = None) -> int:
        if kind is None:
            return sum(len(v) for v in self.out_edges.values())
        return sum(1 for edges in self.out_edges.values() for e in edges if e.kind == kind)

    def to_dict(self) -> dict:
        """Serialise to a JSON-friendly dict."""
        edges: List[dict] = []
        for src_edges in self.out_edges.values():
            for edge in src_edges:
                edges.append(asdict(edge))
        return {
            "nodes": sorted(self.nodes),
            "edges": edges,
            "stats": {
                "n_nodes": len(self.nodes),
                "n_edges": self.edge_count(),
                "n_subsumes": self.edge_count("subsumes"),
                "n_amends": self.edge_count("amends"),
                "n_implicit": self.edge_count("implicit"),
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


# ---------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------


def _normalise_section(raw: str) -> str:
    """Canonicalise a section reference like ``s.415A`` to ``415A``."""
    if not raw:
        return raw
    s = raw.strip().strip(".").strip()
    # Drop leading "s" or "section" if present (case-insensitive).
    lower = s.lower()
    if lower.startswith("section"):
        s = s[len("section"):].strip().strip(".").strip()
    elif lower.startswith("s."):
        s = s[2:].strip()
    elif lower.startswith("s") and len(s) > 1 and s[1].isdigit():
        s = s[1:]
    return s


def _gather_strings(node: nodes.ASTNode, depth: int = 0) -> List[str]:
    """Recursively pull every str-typed field from an AST subtree."""
    if depth > 24:  # defensive cap; AST depth is well below this
        return []
    out: List[str] = []
    if isinstance(node, nodes.StringLit):
        out.append(node.value)
    # Element doc comments and descriptions
    desc = getattr(node, "description", None)
    if isinstance(desc, str):
        out.append(desc)
    doc = getattr(node, "doc_comment", None)
    if isinstance(doc, str):
        out.append(doc)
    holding = getattr(node, "holding", None)
    if isinstance(holding, nodes.StringLit):
        out.append(holding.value)
    for child in node.children() if hasattr(node, "children") else []:
        if isinstance(child, nodes.ASTNode):
            out.extend(_gather_strings(child, depth + 1))
    return out


def _scan_implicit_refs(text: str) -> List[str]:
    """Find every implicit section reference inside a string."""
    if not text:
        return []
    return [m.group(1) for m in _IMPLICIT_REF_RE.finditer(text)]


def add_edges_from_module(
    graph: ReferenceGraph,
    module: nodes.ModuleNode,
    *,
    source_path: str,
) -> int:
    """Walk a parsed module and emit edges for every cross-section reference.

    Returns the number of edges added.
    """
    added = 0
    for stat in module.statutes:
        src_section = stat.section_number
        # Explicit edges
        if stat.subsumes:
            graph.add(ReferenceEdge(
                src=src_section,
                dst=_normalise_section(stat.subsumes),
                kind="subsumes",
                source_path=source_path,
            ))
            added += 1
        if stat.amends:
            graph.add(ReferenceEdge(
                src=src_section,
                dst=_normalise_section(stat.amends),
                kind="amends",
                source_path=source_path,
            ))
            added += 1

        # Implicit edges from every string-bearing node under the statute.
        seen_pairs: Set[Tuple[str, str]] = set()
        for text in _gather_strings(stat):
            for ref in _scan_implicit_refs(text):
                dst = _normalise_section(ref)
                if dst == src_section:
                    continue  # self-reference; skip
                pair = (src_section, dst)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                snippet = text[:120].strip().replace("\n", " ")
                graph.add(ReferenceEdge(
                    src=src_section,
                    dst=dst,
                    kind="implicit",
                    source_path=source_path,
                    snippet=snippet,
                ))
                added += 1
    return added


def build_reference_graph(library_dir: Path) -> ReferenceGraph:
    """Build a reference graph by parsing every ``statute.yh`` under ``library_dir``."""
    from yuho.services.analysis import analyze_file

    graph = ReferenceGraph()
    for yh_file in sorted(library_dir.glob("*/statute.yh")):
        try:
            analysis = analyze_file(yh_file, run_semantic=False)
        except Exception:
            continue
        if analysis.parse_errors or analysis.ast is None:
            continue
        rel = yh_file.relative_to(library_dir.parent) if library_dir.parent in yh_file.parents else yh_file
        add_edges_from_module(graph, analysis.ast, source_path=str(rel))
    return graph
