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
from typing import Iterable, List, Mapping, Optional

from yuho.ast import nodes
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


def _walk_is_infringed(root: nodes.ASTNode) -> List[nodes.IsInfringedNode]:
    """Collect every IsInfringedNode reachable from ``root``."""
    out: List[nodes.IsInfringedNode] = []
    stack: List[nodes.ASTNode] = [root]
    while stack:
        n = stack.pop()
        if isinstance(n, nodes.IsInfringedNode):
            out.append(n)
        children = n.children() if hasattr(n, "children") else []
        for c in children:
            if isinstance(c, nodes.ASTNode):
                stack.append(c)
    return out


def _walk_apply_scope(root: nodes.ASTNode) -> List[nodes.ApplyScopeNode]:
    """Collect every ApplyScopeNode reachable from ``root``."""
    out: List[nodes.ApplyScopeNode] = []
    stack: List[nodes.ASTNode] = [root]
    while stack:
        n = stack.pop()
        if isinstance(n, nodes.ApplyScopeNode):
            out.append(n)
        children = n.children() if hasattr(n, "children") else []
        for c in children:
            if isinstance(c, nodes.ASTNode):
                stack.append(c)
    return out


def check_apply_scope_resolution(
    module: nodes.ModuleNode,
    known_sections: Iterable[str],
) -> List[GraphLintWarning]:
    """Verify every ``apply_scope(<section>, ...)`` references a known section."""
    known = {str(s) for s in known_sections}
    warnings: List[GraphLintWarning] = []
    for node in _walk_apply_scope(module):
        if node.section_ref not in known:
            warnings.append(
                GraphLintWarning(
                    code="apply_scope_unresolved",
                    sections=(node.section_ref,),
                    message=(
                        f"apply_scope(s{node.section_ref}, ...) does not "
                        f"resolve to any encoded section in the library"
                    ),
                    severity="warning",
                )
            )
    return warnings


def _flatten_element_names(elements) -> List[str]:
    """Walk an element tree (ElementNode + ElementGroupNode), returning the
    flat list of leaf element names in declaration order."""
    out: List[str] = []
    stack = list(elements)
    while stack:
        item = stack.pop(0)
        if isinstance(item, nodes.ElementNode):
            out.append(item.name)
        elif isinstance(item, nodes.ElementGroupNode):
            stack[:0] = list(item.members)
    return out


def check_apply_scope_arg_shape(
    module: nodes.ModuleNode,
    registry: Optional[Mapping[str, nodes.StatuteNode]] = None,
) -> List[GraphLintWarning]:
    """Static type-check for ``apply_scope(<section>, ...)``.

    ``registry`` is the section-number → StatuteNode lookup. When omitted,
    statutes from the same module are used (sufficient for self-referential
    composition; library-wide coverage requires the caller to pass a
    populated registry built from the encoded library).

    Two diagnostics:

    * ``apply_scope_target_empty`` — calling apply_scope on a section that
      has no elements is structurally meaningless: nothing for the inner
      scope to evaluate. Often a typo on the section ref.
    * ``apply_scope_arg_missing_fields`` — when the first arg is a struct
      literal, every leaf element name on the target must be a field on
      the struct; missing fields would resolve to None at evaluation
      time and silently fail the inner predicate.

    Identifier args (the common case — ``apply_scope(s299, facts)``) are
    not statically checkable here; they're left to the runtime.
    """
    if registry is None:
        registry = {st.section_number: st for st in module.statutes}

    warnings: List[GraphLintWarning] = []
    for node in _walk_apply_scope(module):
        target = registry.get(node.section_ref)
        if target is None:
            # Resolution is the other check's responsibility; skip.
            continue
        element_names = _flatten_element_names(target.elements or ())
        if not element_names:
            warnings.append(
                GraphLintWarning(
                    code="apply_scope_target_empty",
                    sections=(node.section_ref,),
                    message=(
                        f"apply_scope(s{node.section_ref}, ...) targets a "
                        f"section with no top-level elements; the inner "
                        f"scope has nothing to evaluate"
                    ),
                    severity="warning",
                )
            )
            continue
        # Static struct-literal check: only fires when the first arg is a
        # struct literal (rare in practice, but the strongest signal we
        # can give without runtime info).
        if not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, nodes.StructLiteralNode):
            continue
        struct_fields = {fa.name for fa in first.field_values}
        missing = [n for n in element_names if n not in struct_fields]
        if missing:
            warnings.append(
                GraphLintWarning(
                    code="apply_scope_arg_missing_fields",
                    sections=(node.section_ref,),
                    message=(
                        f"apply_scope(s{node.section_ref}, ...) struct arg "
                        f"is missing fields the target's elements read: "
                        f"{', '.join(missing)}"
                    ),
                    severity="warning",
                )
            )
    return warnings


def check_is_infringed_resolution(
    module: nodes.ModuleNode,
    known_sections: Iterable[str],
) -> List[GraphLintWarning]:
    """Verify every ``is_infringed(<section>)`` references a known section.

    ``known_sections`` is the set of section numbers present in the
    library being lint-checked (typically ``graph.nodes`` from a
    :class:`ReferenceGraph`). Unknown section references emit
    ``is_infringed_unresolved`` warnings.
    """
    known = {str(s) for s in known_sections}
    warnings: List[GraphLintWarning] = []
    for node in _walk_is_infringed(module):
        if node.section_ref not in known:
            warnings.append(
                GraphLintWarning(
                    code="is_infringed_unresolved",
                    sections=(node.section_ref,),
                    message=(
                        f"is_infringed(s{node.section_ref}) does not resolve "
                        f"to any encoded section in the library"
                    ),
                    severity="warning",
                )
            )
    return warnings


def lint_reference_graph(
    graph: ReferenceGraph,
    *,
    kinds: Optional[Iterable[str]] = None,
    module: Optional[nodes.ModuleNode] = None,
) -> List[GraphLintWarning]:
    """Run all library-level diagnostics on a built reference graph.

    ``kinds`` defaults to ``("implicit", "subsumes")``; pass an explicit
    iterable to include or exclude further edge kinds.

    When ``module`` is supplied, also resolve ``is_infringed`` predicates
    against the graph's node set and surface ``is_infringed_unresolved``
    warnings for unknown section references.
    """
    edge_kinds = tuple(kinds) if kinds else _DEFAULT_KINDS
    warnings: List[GraphLintWarning] = []
    warnings.extend(_check_cross_section_cycles(graph, edge_kinds))
    if module is not None:
        warnings.extend(check_is_infringed_resolution(module, graph.nodes))
        warnings.extend(check_apply_scope_resolution(module, graph.nodes))
        warnings.extend(check_apply_scope_arg_shape(module))
    return warnings
