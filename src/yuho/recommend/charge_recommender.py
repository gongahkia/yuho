"""Charge-recommender — surface candidate Penal Code sections for a fact pattern.

This is a thin orchestrator over Yuho's existing core tooling:

* corpus access via the canonical ``library/penal_code/_corpus`` JSON, the
  same data the simulator and the MCP server already use;
* per-element matching via ``simulator.evaluate``, which already does the
  fact-string-against-element-description structural trace;
* element / exception structure parsing reused from ``simulator``.

The recommender does **not** call any external LLM or scrape the web. It
does **not** decide whether an offence is made out. It is a structural
ranker: given a fact pattern without a known section, it searches the
encoded corpus for sections whose elements are plausibly satisfied by
the facts, and returns the top-k with the simulator's full per-element
trace attached so a human can verify each suggestion.

Every result carries an explicit ``not_legal_advice: True`` flag and the
disclaimer string defined in ``LEGAL_DISCLAIMER``. Callers MUST surface
this verbatim in any user-facing output.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REPO = Path(__file__).resolve().parent.parent.parent.parent
CORPUS = REPO / "library" / "penal_code" / "_corpus"
SIMULATOR_DIR = REPO / "simulator"


# ---------------------------------------------------------------------------
# Disclaimer — must accompany every recommendation surface
# ---------------------------------------------------------------------------


LEGAL_DISCLAIMER = (
    "This is a structural ranking over the encoded Penal Code, not legal "
    "advice. Recommendations are derived from keyword and element overlap "
    "between the supplied fact pattern and the encoded statute; they do "
    "NOT determine whether an offence is made out, do NOT account for "
    "prosecutorial discretion, and do NOT replace consultation with a "
    "qualified lawyer. Cross-reference the canonical text on Singapore "
    "Statutes Online (sso.agc.gov.sg) before acting on any output here."
)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    section: str
    title: str
    sso_url: str
    coverage: float                              # 0.0..1.0
    n_elements: int
    n_satisfied: int
    n_suggested: int
    n_unresolved: int
    n_contradicted: int
    satisfied:    List[str] = field(default_factory=list)
    suggested:    List[Dict[str, str]] = field(default_factory=list)
    unresolved:   List[str] = field(default_factory=list)
    contradicted: List[str] = field(default_factory=list)
    exceptions_matched: List[str] = field(default_factory=list)
    verdict:      str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Recommendation:
    candidates: List[Candidate] = field(default_factory=list)
    n_searched: int = 0
    n_simulated: int = 0
    not_legal_advice: bool = True
    disclaimer: str = LEGAL_DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidates":       [c.to_dict() for c in self.candidates],
            "n_searched":       self.n_searched,
            "n_simulated":      self.n_simulated,
            "not_legal_advice": self.not_legal_advice,
            "disclaimer":       self.disclaimer,
        }


# ---------------------------------------------------------------------------
# Recommender
# ---------------------------------------------------------------------------


class ChargeRecommender:
    """Stateful recommender that lazy-loads the slim corpus once."""

    def __init__(self, corpus_dir: Optional[Path] = None):
        self._corpus_dir = corpus_dir or CORPUS
        self._sections: Optional[Dict[str, Dict[str, Any]]] = None

    # -- public API --------------------------------------------------------

    def recommend(
        self,
        facts: Dict[str, Any],
        *,
        top_k: int = 5,
        max_candidates: int = 60,
        min_coverage: float = 0.0,
    ) -> Recommendation:
        """Rank Penal Code sections by structural fit to the supplied facts.

        Args:
            facts: a fact-pattern dict (same shape as the simulator's input,
                but ``section`` is optional — when present it is ignored
                and treated as a hint for diagnostic purposes).
            top_k: how many ranked candidates to return.
            max_candidates: cap on sections whose simulator trace gets run
                in the second stage. Larger = more thorough, slower.
            min_coverage: drop candidates whose coverage falls below this
                fraction. Default 0.0 keeps everything that simulated.

        Returns:
            A ``Recommendation`` whose ``candidates`` are sorted descending
            by ``coverage``. Always carries the disclaimer fields.
        """
        sections = self._load_sections()
        fact_strings = self._fact_strings(facts)
        if not fact_strings:
            return Recommendation(
                candidates=[], n_searched=len(sections), n_simulated=0,
            )

        # Stage 1: cheap keyword-overlap scoring to pick candidates.
        scored = self._prefilter(sections, fact_strings)
        candidates_to_simulate = [n for n, _ in scored[:max_candidates]]

        # Stage 2: run the simulator against each candidate.
        out: List[Candidate] = []
        for num in candidates_to_simulate:
            facts_for_section = dict(facts)
            facts_for_section["section"] = num
            trace = self._simulate(facts_for_section)
            if not trace or "error" in trace:
                continue
            n_elements = trace.get("n_elements", 0) or 0
            if n_elements == 0:
                continue
            n_sat = len(trace.get("satisfied", []))
            n_sug = len(trace.get("suggested", []))
            n_unres = len(trace.get("unresolved", []))
            n_contra = len(trace.get("contradicted", []))
            # Coverage: satisfied counts full, suggested at half-weight,
            # contradicted is a hard penalty.
            raw = (n_sat + 0.5 * n_sug - 0.5 * n_contra) / n_elements
            coverage = max(0.0, min(1.0, raw))
            if coverage < min_coverage:
                continue
            rec = sections.get(num, {})
            out.append(Candidate(
                section=num,
                title=rec.get("section_title") or trace.get("section_title") or "",
                sso_url=rec.get("sso_url", ""),
                coverage=round(coverage, 4),
                n_elements=n_elements,
                n_satisfied=n_sat,
                n_suggested=n_sug,
                n_unresolved=n_unres,
                n_contradicted=n_contra,
                satisfied=list(trace.get("satisfied", [])),
                suggested=list(trace.get("suggested", [])),
                unresolved=list(trace.get("unresolved", [])),
                contradicted=list(trace.get("contradicted", [])),
                exceptions_matched=list(trace.get("exceptions_matched", [])),
                verdict=trace.get("verdict", ""),
            ))

        # Sort by coverage desc; tie-break on n_satisfied desc, then section.
        out.sort(key=lambda c: (-c.coverage, -c.n_satisfied, c.section))
        return Recommendation(
            candidates=out[:top_k],
            n_searched=len(sections),
            n_simulated=len(candidates_to_simulate),
        )

    # -- internals ---------------------------------------------------------

    def _load_sections(self) -> Dict[str, Dict[str, Any]]:
        if self._sections is not None:
            return self._sections
        sec_dir = self._corpus_dir / "sections"
        if not sec_dir.exists():
            self._sections = {}
            return self._sections
        sections: Dict[str, Dict[str, Any]] = {}
        for p in sec_dir.glob("s*.json"):
            try:
                with p.open("r", encoding="utf-8") as f:
                    rec = json.load(f)
                num = rec.get("section_number")
                if num:
                    sections[num] = rec
            except Exception:
                continue
        self._sections = sections
        return sections

    @staticmethod
    def _fact_strings(facts: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        for key in ("description", "name"):
            v = facts.get(key)
            if isinstance(v, str) and v.strip():
                out.append(v.strip())
        for entry in facts.get("acts", []) or []:
            if isinstance(entry, dict) and entry.get("description"):
                out.append(str(entry["description"]).strip())
            elif isinstance(entry, str):
                out.append(entry.strip())
        ms = facts.get("mental_states") or {}
        if isinstance(ms, dict):
            for actor_states in ms.values():
                if isinstance(actor_states, dict):
                    for v in actor_states.values():
                        if isinstance(v, str):
                            out.append(v.strip())
                elif isinstance(actor_states, str):
                    out.append(actor_states.strip())
        for entry in facts.get("circumstances", []) or []:
            if isinstance(entry, str):
                out.append(entry.strip())
        for entry in facts.get("outcomes", []) or []:
            if isinstance(entry, dict) and entry.get("description"):
                out.append(str(entry["description"]).strip())
            elif isinstance(entry, str):
                out.append(entry.strip())
        return [s for s in out if s]

    @staticmethod
    def _tokenise(s: str) -> List[str]:
        return [w for w in re.split(r"[^a-zA-Z0-9]+", s.lower()) if len(w) > 2]

    def _prefilter(
        self,
        sections: Dict[str, Dict[str, Any]],
        fact_strings: List[str],
    ) -> List[Tuple[str, float]]:
        """Rank sections by token overlap with fact strings — cheap O(N)
        pass to pick candidates worth simulating."""
        # Stop words specific to legal-fact-pattern noise.
        STOP = {
            "the", "and", "for", "with", "into", "from", "this", "that",
            "any", "person", "his", "her", "their", "them", "him", "she",
            "have", "has", "was", "were", "are", "been", "actor", "victim",
            "accused", "such", "which", "would", "could", "shall",
        }
        fact_tokens = set()
        for s in fact_strings:
            fact_tokens.update(self._tokenise(s))
        fact_tokens -= STOP
        if not fact_tokens:
            return []
        scored: List[Tuple[str, float]] = []
        for num, rec in sections.items():
            haystack = " ".join([
                rec.get("section_title") or "",
                (rec.get("metadata") or {}).get("summary") or "",
                rec.get("encoded", {}).get("yh_source", "") or "",
                (rec.get("raw") or {}).get("text") or "",
            ]).lower()
            if not haystack:
                continue
            hits = sum(1 for t in fact_tokens if t in haystack)
            if hits == 0:
                continue
            # Normalise so longer haystacks don't dominate.
            score = hits / max(1.0, (len(haystack) ** 0.25))
            scored.append((num, score))
        scored.sort(key=lambda x: -x[1])
        return scored

    @staticmethod
    def _simulate(facts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Reuse the existing simulator. It expects to be importable from
        # the top-level `simulator/` directory, so we add it lazily.
        if str(SIMULATOR_DIR) not in sys.path:
            sys.path.insert(0, str(SIMULATOR_DIR))
        try:
            import simulator as sim_mod  # type: ignore
        except Exception:
            return None
        try:
            return sim_mod.evaluate(facts)
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Convenience entrypoint for CLI / MCP
# ---------------------------------------------------------------------------


def recommend(facts: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """One-shot helper used by the CLI command and the MCP tool.

    Always returns a dict carrying the disclaimer; the caller is expected
    to surface that verbatim.
    """
    rec = ChargeRecommender().recommend(facts, **kwargs)
    return rec.to_dict()


def render_recommendation_text(rec: Recommendation) -> str:
    """Pretty-print for terminal output. The disclaimer goes both at the
    top (so humans see it before scanning results) and at the bottom (so
    it's preserved if the output is truncated by a pager)."""
    lines: List[str] = []
    lines.append("⚠ NOT LEGAL ADVICE — structural ranking only.")
    lines.append("")
    if not rec.candidates:
        lines.append(f"No candidates found (searched {rec.n_searched}, simulated {rec.n_simulated}).")
        lines.append("")
        lines.append(LEGAL_DISCLAIMER)
        return "\n".join(lines)
    lines.append(f"Top {len(rec.candidates)} candidate sections "
                 f"(searched {rec.n_searched}, simulated {rec.n_simulated}):")
    lines.append("")
    for i, c in enumerate(rec.candidates, 1):
        lines.append(f"  {i}. s{c.section} — {c.title}")
        lines.append(f"     coverage: {c.coverage:.0%}  "
                     f"({c.n_satisfied} satisfied, {c.n_suggested} suggested, "
                     f"{c.n_unresolved} unresolved, {c.n_contradicted} contradicted "
                     f"of {c.n_elements} elements)")
        if c.satisfied:
            lines.append(f"     satisfied:    {', '.join(c.satisfied)}")
        if c.suggested:
            lines.append(f"     suggested:    {', '.join(s.get('element','') for s in c.suggested)}")
        if c.contradicted:
            lines.append(f"     contradicted: {', '.join(c.contradicted)}")
        if c.exceptions_matched:
            lines.append(f"     exceptions raised + matched: {', '.join(c.exceptions_matched)}")
        if c.verdict:
            lines.append(f"     verdict: {c.verdict}")
        if c.sso_url:
            lines.append(f"     SSO: {c.sso_url}")
        lines.append("")
    lines.append(LEGAL_DISCLAIMER)
    return "\n".join(lines)
