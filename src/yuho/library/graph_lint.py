"""Library-level lint diagnostics over the cross-section reference graph.

The per-statute linter (``yuho.ast.statute_lint``) operates one module at a
time and so cannot see cycles that span sections. This module fills that
gap: it consumes a built ``ReferenceGraph`` and emits warnings for
structural issues that only manifest in the global view.

Current diagnostics:

* ``cross_section_cycle`` — non-trivial SCC in the implicit/subsumes
  reference graph. Pure amendment chains are excluded by default since
  legitimate "amends" history is naturally chain-like and benign.

Run via ``yuho refs --scc`` or programmatically::

    from yuho.library.reference_graph import build_reference_graph
    from yuho.library.graph_lint import lint_reference_graph
    g = build_reference_graph(Path("library/penal_code"))
    for w in lint_reference_graph(g):
        print(w)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from yuho.library.reference_graph import ReferenceGraph


_DEFAULT_KINDS = ("implicit", "subsumes")  # exclude "amends" by default


@dataclass(frozen=True)
class GraphLintWarning:
    """A library-wide reference-graph diagnostic."""

    code: str            # e.g. "cross_section_cycle"
    sections: tuple      # the sections involved (ordered)
    message: str
    severity: str        # "warning" or "info"


def _check_cross_section_cycles(
    graph: ReferenceGraph,
    kinds: Iterable[str],
) -> List[GraphLintWarning]:
    out: List[GraphLintWarning] = []
    for component in graph.cycles(kinds):
        sections = tuple(sorted(component))
        if len(sections) == 1:
            msg = (
                f"section s{sections[0]} has a self-referential cross-reference "
                f"(kind filter: {','.join(sorted(set(kinds)))})"
            )
        else:
            msg = (
                f"cross-section reference cycle ({len(sections)} sections): "
                f"{' ↔ '.join('s' + s for s in sections)}"
            )
        out.append(
            GraphLintWarning(
                code="cross_section_cycle",
                sections=sections,
                message=msg,
                severity="warning",
            )
        )
    return out


def lint_reference_graph(
    graph: ReferenceGraph,
    *,
    kinds: Optional[Iterable[str]] = None,
) -> List[GraphLintWarning]:
    """Run all library-level diagnostics on a built reference graph.

    ``kinds`` defaults to ``("implicit", "subsumes")``; pass an explicit
    iterable to include or exclude further edge kinds.
    """
    edge_kinds = tuple(kinds) if kinds else _DEFAULT_KINDS
    warnings: List[GraphLintWarning] = []
    warnings.extend(_check_cross_section_cycles(graph, edge_kinds))
    return warnings
