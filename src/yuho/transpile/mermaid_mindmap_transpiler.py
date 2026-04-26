"""Mermaid mindmap transpiler — statute-shape mindmap rendering.

Companion to :class:`yuho.transpile.mermaid_transpiler.MermaidTranspiler`.
The flowchart transpiler shows the *evaluation* shape of a statute (how
elements compose, where exceptions fire, what penalty fires when); this
transpiler shows the *structural* shape — the same hierarchy a human
reader sees on Singapore Statutes Online: title → definitions → elements
(nested by combinator) → penalty → illustrations → exceptions → caselaw.

Why a separate class rather than a flag on the flowchart transpiler:
mindmap and flowchart syntaxes are unrelated dialects of Mermaid, and
the rendering invariants (no edges, indentation-driven hierarchy, no
node IDs) make the codepath sufficiently distinct that one shared
class would be more confusing than two specialised ones.

Output shape::

    mindmap
      s415 Cheating
        Definitions
          deceive
          fraudulently
          dishonestly
        Elements [ALL OF]
          actus_reus deception
          mens_rea [ANY OF]
            fraudulent
            dishonest
          actus_reus inducement
          circumstance harm
        Penalty
          Imprisonment 1y..7y
          Fine ≤ $50000
        Illustrations
          example1
          example2

Mermaid mindmap syntax: each indented line is a child of the line above
it at lesser indentation. No explicit edges. Two-space indent per level
is the convention rendered by the live Mermaid renderer; we follow it
strictly.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase


_INDENT = "  "  # mermaid mindmap parser is whitespace-sensitive; keep at 2.


class MermaidMindmapTranspiler(TranspilerBase):
    """Emit a Mermaid mindmap describing a statute's structural shape."""

    def __init__(self, max_label_chars: int = 80) -> None:
        self.max_label_chars = max_label_chars
        self._lines: List[str] = []

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.MINDMAP

    # ------------------------------------------------------------------
    # Top level
    # ------------------------------------------------------------------

    def transpile(self, ast: nodes.ModuleNode) -> str:
        self._lines = ["mindmap"]
        statutes = list(ast.statutes)
        if not statutes:
            self._lines.append(f"{_INDENT}No statutes")
            return "\n".join(self._lines)
        if len(statutes) == 1:
            self._render_statute(statutes[0], depth=1)
        else:
            # Multi-statute module: synthesise a wrapper root so each statute
            # surfaces as a child branch.
            module_label = "Module"
            self._lines.append(f"{_INDENT}{module_label}")
            for s in statutes:
                self._render_statute(s, depth=2)
        return "\n".join(self._lines)

    # ------------------------------------------------------------------
    # Per-statute hierarchy
    # ------------------------------------------------------------------

    def _render_statute(self, stat: nodes.StatuteNode, depth: int) -> None:
        title = stat.title.value if stat.title else "(untitled)"
        # Mermaid mindmap supports `((round))` for the root node visual; we
        # use it for the root statute label only.
        label = f"s{stat.section_number} {title}"
        self._emit(depth, label, decorator="round")

        if stat.effective_dates:
            self._emit(depth + 1, "Effective dates")
            for d in stat.effective_dates:
                self._emit(depth + 2, d)

        if stat.definitions:
            self._emit(depth + 1, "Definitions")
            for d in stat.definitions:
                term = getattr(d, "term", None) or getattr(d, "name", "")
                self._emit(depth + 2, str(term) or "(unnamed)")

        if stat.elements:
            # The statute-level element block is implicitly an `all_of`; we
            # surface that explicitly so the mindmap reflects the doctrinal
            # combinator structure.
            self._emit(depth + 1, "Elements [ALL OF]")
            for member in stat.elements:
                self._render_element_member(member, depth + 2)

        # Penalty (primary + multi-penalty G12 siblings).
        all_penalties: List[nodes.PenaltyNode] = []
        if stat.penalty is not None:
            all_penalties.append(stat.penalty)
        all_penalties.extend(getattr(stat, "additional_penalties", ()) or ())
        for i, pen in enumerate(all_penalties, 1):
            label = "Penalty" if len(all_penalties) == 1 else f"Penalty ({i})"
            combinator = getattr(pen, "combinator", None)
            if combinator and combinator != "cumulative":
                label = f"{label} [{combinator}]"
            self._emit(depth + 1, label)
            for line in self._penalty_components(pen):
                self._emit(depth + 2, line)

        if stat.illustrations:
            self._emit(depth + 1, "Illustrations")
            for ill in stat.illustrations:
                ill_label = getattr(ill, "label", None) or getattr(ill, "name", "") or "ill"
                desc_node = getattr(ill, "description", None)
                desc = desc_node.value if hasattr(desc_node, "value") else str(desc_node or "")
                child_label = self._truncate(f"{ill_label}: {desc}") if desc else ill_label
                self._emit(depth + 2, child_label)

        if stat.exceptions:
            self._emit(depth + 1, "Exceptions")
            for exc in stat.exceptions:
                exc_label = getattr(exc, "label", None) or "(unlabeled)"
                priority = getattr(exc, "priority", None)
                if priority is not None:
                    exc_label = f"{exc_label} (priority {priority})"
                self._emit(depth + 2, exc_label)

        if stat.case_law:
            self._emit(depth + 1, "Case law")
            for cl in stat.case_law:
                name = cl.case_name.value if getattr(cl, "case_name", None) else "(unnamed)"
                self._emit(depth + 2, name)

        if stat.subsections:
            self._emit(depth + 1, "Subsections")
            for sub in stat.subsections:
                self._emit(depth + 2, f"({sub.number})")

    # ------------------------------------------------------------------
    # Element / penalty helpers
    # ------------------------------------------------------------------

    def _render_element_member(self, member, depth: int) -> None:
        """Render one element node or one element group + its members."""
        if isinstance(member, nodes.ElementNode):
            label = f"{member.element_type} {member.name}"
            self._emit(depth, label)
        elif isinstance(member, nodes.ElementGroupNode):
            combinator = (member.combinator or "all_of").upper()
            tag = {"ALL_OF": "ALL OF", "ANY_OF": "ANY OF"}.get(combinator, combinator)
            self._emit(depth, f"[{tag}]")
            for child in member.members:
                self._render_element_member(child, depth + 1)

    def _penalty_components(self, pen: nodes.PenaltyNode) -> List[str]:
        out: List[str] = []
        if pen.death_penalty:
            out.append("Death")
        if pen.imprisonment_max:
            if pen.imprisonment_min:
                out.append(f"Imprisonment {pen.imprisonment_min}..{pen.imprisonment_max}")
            else:
                out.append(f"Imprisonment up to {pen.imprisonment_max}")
        if pen.fine_max:
            if pen.fine_min:
                out.append(f"Fine ${pen.fine_min.amount}..${pen.fine_max.amount}")
            else:
                out.append(f"Fine up to ${pen.fine_max.amount}")
        elif getattr(pen, "fine_unlimited", False):
            out.append("Fine (unlimited)")
        if pen.caning_max:
            if pen.caning_min:
                out.append(f"Caning {pen.caning_min}-{pen.caning_max} strokes")
            else:
                out.append(f"Caning up to {pen.caning_max} strokes")
        elif getattr(pen, "caning_unspecified", False):
            out.append("Caning (unspecified)")
        if pen.supplementary:
            out.append(self._truncate(pen.supplementary.value))
        return out or ["(no penalty fields)"]

    # ------------------------------------------------------------------
    # Plumbing
    # ------------------------------------------------------------------

    def _emit(self, depth: int, label: str, *, decorator: Optional[str] = None) -> None:
        text = self._sanitise(label)
        if decorator == "round":
            text = f"(({text}))"
        self._lines.append(f"{_INDENT * depth}{text}")

    def _sanitise(self, text: str) -> str:
        """Mindmap labels do not tolerate raw parens / brackets / quotes well.

        Strip the worst offenders, replace structural brackets with safer
        Unicode markers, and truncate length so the rendered diagram does
        not overflow the page.
        """
        s = (text or "").replace("\n", " ").strip()
        # Mindmap parser treats trailing parens like `name(args)` as a node
        # decorator; rewriting `(x)` to `[x]` keeps the visual hint without
        # confusing the parser.
        s = s.replace("(", "[").replace(")", "]")
        s = s.replace('"', "'")
        return self._truncate(s)

    def _truncate(self, text: str) -> str:
        if len(text) <= self.max_label_chars:
            return text
        return text[: self.max_label_chars - 1].rstrip() + "…"
