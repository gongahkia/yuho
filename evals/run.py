#!/usr/bin/env python3
"""Yuho LLM legal-reasoning benchmark runner.

Pipeline per fixture:

    fixture.scenario  →  LLM (3 tasks)  →  score against fixture.ground_truth

Tasks:

* T1 — section identification: "What Penal Code section best applies?"
* T2 — element-set recall: "Which encoded elements are satisfied?"
* T3 — exception citation: "Which defeating exception fires (if any)?"

Scoring:

* T1 — exact match on the canonical section string ("415", "300", "376AA").
* T2 — F1 over the predicted vs ground-truth element name set
        (precision = |intersection| / |predicted|;
         recall    = |intersection| / |ground-truth|).
* T3 — exact match (case-insensitive); "none" is canonicalised.

Usage::

    # Anthropic — needs ANTHROPIC_API_KEY:
    python evals/run.py --model claude-sonnet-4-6
    python evals/run.py --model claude-opus-4-7

    # OpenAI — needs OPENAI_API_KEY (org-scoped keys also pick up
    # OPENAI_ORGANIZATION / OPENAI_BASE_URL automatically):
    python evals/run.py --model gpt-4o
    python evals/run.py --provider openai --model gpt-4o-mini

    # Pin a smaller fixture slice:
    python evals/run.py --max-fixtures 5

    # Dry-run with a fake client (no API calls; useful for CI):
    python evals/run.py --fake

    # Machine-readable output:
    python evals/run.py --json --out evals/results.json

The runner is small and dependency-light by design. The scoring
logic, fixture loader, and report renderer are public so other
runners (different LLMs / different prompting strategies) can
reuse them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

REPO = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO / "evals" / "fixtures"


# =============================================================================
# Fixture loader
# =============================================================================


@dataclass(frozen=True)
class Fixture:
    """One benchmark item — scenario plus structural ground truth."""

    id: str
    section: str
    scenario: str
    truth_section: str
    truth_elements: Tuple[str, ...]
    truth_exception: Optional[str]
    fact_facts: Dict[str, bool] = field(default_factory=dict)
    tags: Tuple[str, ...] = ()


def load_fixtures(directory: Optional[Path] = None) -> List[Fixture]:
    """Load every YAML fixture under ``directory`` (default: evals/fixtures)."""
    directory = directory or FIXTURES_DIR
    if not directory.exists():
        raise FileNotFoundError(f"fixtures directory not found: {directory}")

    # Prefer PyYAML when available; fall back to the simulator's
    # bundled mini-YAML loader so the benchmark runner doesn't add
    # a new install dep on top of the existing toolchain.
    try:
        import yaml  # type: ignore

        def _load_one(text: str) -> Dict[str, Any]:
            return yaml.safe_load(text)
    except ImportError:
        sim_dir = REPO / "simulator"
        if str(sim_dir) not in sys.path:
            sys.path.insert(0, str(sim_dir))
        from simulator import _mini_yaml  # type: ignore

        def _load_one(text: str) -> Dict[str, Any]:
            return _mini_yaml(text)

    def _coerce_list(v: Any) -> List[str]:
        """Accept a list or an inline-list string (`[a, b, c]`)."""
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                inner = s[1:-1].strip()
                if not inner:
                    return []
                return [p.strip().strip("\"' ") for p in inner.split(",") if p.strip()]
            return [s]
        return [str(v)]

    out: List[Fixture] = []
    for fp in sorted(directory.glob("*.yaml")):
        raw = _load_one(fp.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"fixture {fp.name} is not a YAML mapping")
        gt = raw.get("ground_truth") or {}
        out.append(Fixture(
            id=raw["id"],
            section=raw.get("section", gt.get("section", "")),
            scenario=raw["scenario"].strip(),
            truth_section=str(gt["section"]),
            truth_elements=tuple(_coerce_list(gt.get("satisfied_elements"))),
            truth_exception=gt.get("fired_exception"),
            fact_facts=dict(raw.get("fact_facts") or {}),
            tags=tuple(_coerce_list(raw.get("tags"))),
        ))
    return out


# =============================================================================
# Client protocol — pluggable LLM backend
# =============================================================================


class BenchmarkClient(Protocol):
    """Minimal interface every backend must satisfy."""

    def query(self, prompt: str, *, system: str = "", task_kind: str = "") -> str: ...


@dataclass
class FakeClient:
    """A deterministic, dependency-free client for CI and local dev.

    Returns the structurally-correct answer for every task. Use
    ``--fake`` to validate the runner end-to-end without API access.
    """

    fixtures: List[Fixture]
    _by_scenario: Dict[str, Fixture] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._by_scenario = {fx.scenario: fx for fx in self.fixtures}

    def query(self, prompt: str, *, system: str = "", task_kind: str = "") -> str:
        # Match by full scenario text — short prefixes collide
        # across illustrations that share opening clauses (the
        # canonical Penal Code drafting style).
        match: Optional[Fixture] = None
        for scenario, fx in self._by_scenario.items():
            if scenario in prompt:
                if match is None or len(scenario) > len(match.scenario):
                    match = fx
        if match is None:
            return ""
        if task_kind == "section":
            return match.truth_section
        if task_kind == "elements":
            return json.dumps(list(match.truth_elements))
        if task_kind == "exception":
            return match.truth_exception or "none"
        return ""


@dataclass
class AnthropicClient:
    """Anthropic Claude API client. Requires ``ANTHROPIC_API_KEY`` and
    the ``anthropic`` SDK. Caches per-conversation prompt prefix so
    repeated calls inside one fixture share a cache hit."""

    model: str = "claude-sonnet-4-6"
    max_tokens: int = 512
    temperature: float = 0.0

    def __post_init__(self) -> None:
        try:
            import anthropic  # type: ignore  # noqa: F401
        except ImportError:
            raise ImportError(
                "anthropic SDK is required for AnthropicClient. "
                "Install with: pip install anthropic"
            )
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set; cannot run real LLM scoring"
            )

    def query(self, prompt: str, *, system: str = "", task_kind: str = "") -> str:
        import anthropic  # type: ignore
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system or "You are a concise legal-reasoning assistant for the Singapore Penal Code 1871. Reply with exactly the requested format and nothing else.",
            messages=[{"role": "user", "content": prompt}],
        )
        # Concatenate text blocks defensively.
        return "".join(
            getattr(block, "text", "") for block in response.content
        ).strip()


@dataclass
class OpenAIClient:
    """OpenAI Chat Completions client. Requires ``OPENAI_API_KEY`` and
    the ``openai`` SDK. Honours ``OPENAI_ORGANIZATION`` /
    ``OPENAI_ORG_ID`` (org-scoped keys) and ``OPENAI_BASE_URL`` (for
    Azure / proxy / open-weights endpoints that speak the OpenAI
    wire format)."""

    model: str = "gpt-4o"
    max_tokens: int = 512
    temperature: float = 0.0

    def __post_init__(self) -> None:
        try:
            import openai  # type: ignore  # noqa: F401
        except ImportError:
            raise ImportError(
                "openai SDK is required for OpenAIClient. "
                "Install with: pip install openai"
            )
        if not os.environ.get("OPENAI_API_KEY"):
            raise EnvironmentError(
                "OPENAI_API_KEY is not set; cannot run real LLM scoring"
            )

    def query(self, prompt: str, *, system: str = "", task_kind: str = "") -> str:
        import openai  # type: ignore
        # The OpenAI SDK auto-picks up OPENAI_API_KEY,
        # OPENAI_ORGANIZATION, and OPENAI_BASE_URL from the env.
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "system",
                 "content": system or "You are a concise legal-reasoning assistant for the Singapore Penal Code 1871. Reply with exactly the requested format and nothing else."},
                {"role": "user", "content": prompt},
            ],
        )
        choice = response.choices[0] if response.choices else None
        if choice is None or choice.message is None:
            return ""
        return (choice.message.content or "").strip()


# =============================================================================
# Prompt building
# =============================================================================


_SYSTEM_PROMPT = (
    "You are a concise structural-legal-reasoning assistant for the "
    "Singapore Penal Code 1871. You answer with EXACTLY the format the "
    "user asks for, nothing more. Do not add caveats, disclaimers, or "
    "prose explanations. The user is collecting structured ground "
    "truth for a benchmark — verbosity is wrong, not wise."
)


# Cheap regex/keyword classifier for null-answer cues. Used by the
# `polarity-conditional` variant to route per-fixture: scenarios that
# trip the classifier get the polarity-soft v2 prompts; those that do
# not get the baseline v1 prompts. Goal: capture the negative-slice
# gain of polarity-soft without paying its small positive-corpus cost.
# Patterns are case-insensitive substring matches on the scenario.
_NULL_CUE_PATTERNS = (
    r"\bno element\b",
    r"\bno offence\b",
    r"\bno mens rea\b",
    r"\bno intent\b",
    r"\bwithout intent\b",
    r"\bwithout knowledge\b",
    r"\bwithout dishonest\b",
    r"\bwithout fraudulent\b",
    r"\bdid not\b",
    r"\bdoes not\b",
    r"\bdoesn't\b",
    r"\bdidn't\b",
    r"\bnever\b",
    r"\bno deception\b",
    r"\bno fraud\b",
    r"\bnot guilty\b",
    r"\bno harm\b",
    r"\bno injury\b",
    r"\bnone fires?\b",
    r"\bno element fires\b",
)
_NULL_CUE_RE = re.compile("|".join(_NULL_CUE_PATTERNS), re.IGNORECASE)


def _classify_null_cue(scenario: str) -> bool:
    """Return True if scenario contains a null-answer keyword cue."""
    return bool(_NULL_CUE_RE.search(scenario or ""))


def _resolve_variant(variant: str, scenario: str) -> str:
    """Resolve `polarity-conditional` per-fixture; otherwise pass-through."""
    if variant == "polarity-conditional":
        return "polarity-soft" if _classify_null_cue(scenario) else "baseline"
    return variant


def _prompt_section(scenario: str, variant: str = "polarity") -> str:
    # Four prompt variants supported for §7.6 N-way comparison:
    #   - "baseline":     the original v1 closed-vocab prompt
    #   - "polarity":     adds `none` option + polarity priming +
    #                     `# ruled out:` CoT invitation on T2
    #   - "polarity-soft": polarity priming + `none` only, no CoT
    #                     invitation (tests whether the regression
    #                     under "polarity" comes from the CoT path
    #                     or from the priming itself)
    #   - "polarity-conditional": cheap regex classifier on scenario;
    #                     routes to polarity-soft on null-cue hits,
    #                     baseline otherwise (caller resolves via
    #                     _resolve_variant before calling here)
    # T1 prompt is identical between "polarity" and "polarity-soft"
    # — the variants only diverge on T2.
    # Scorer accepts either truth_section or `none` when truth
    # elements are empty (all variants), so the variants differ
    # only in what the model is *told* it can answer.
    if variant == "baseline":
        return (
            f"Scenario:\n{scenario}\n\n"
            "Task: Identify the Penal Code section that most directly applies. "
            "Reply with ONLY the section number (e.g. `415`, `300`, `376AA`). "
            "No prose, no `Section`, no period."
        )
    return (
        f"Scenario:\n{scenario}\n\n"
        "Task: Identify the Penal Code section that most directly applies. "
        "Reply with ONLY the section number (e.g. `415`, `300`, `376AA`), "
        "OR the literal word `none` if no Penal Code section applies "
        "to the scenario as stated (many scenarios are constructed so "
        "that no offence is made out). "
        "No prose, no `Section`, no period."
    )


def _prompt_elements(scenario: str, section: str,
                     vocabulary: Optional[List[str]] = None,
                     variant: str = "polarity") -> str:
    """Build the T2 prompt.

    When ``vocabulary`` is supplied, render T2 as a closed-set
    multi-label classification (pick a subset of the named elements).
    This is the structurally-honest framing: the LLM is being graded
    on whether the scenario satisfies *these specific* encoded
    elements, not on whether it can guess our private snake_case
    naming convention from scratch — which is unrelated to legal
    reasoning and explains the open-vocabulary T2 collapse on the
    initial gpt-4o-mini spot-check.

    The original open-vocabulary form is preserved as a fallback for
    callers that deliberately want to test naming-convention recall.
    """
    base = (
        f"Scenario:\n{scenario}\n\n"
        f"Assume Penal Code s{section} applies. "
    )
    if vocabulary:
        vocab_inline = ", ".join(vocabulary)
        if variant == "baseline":
            # Original v1 closed-vocab prompt.
            return (
                base
                + "The encoded section's structural elements are:\n"
                + f"  [{vocab_inline}]\n\n"
                + "Task: from the list above, return the subset of element "
                  "names that are SATISFIED by the scenario as stated. Reply "
                  'with ONLY a JSON array of strings (e.g. `["a", "b"]`); '
                  "use `[]` if no element is satisfied. Names must come "
                  "from the supplied list verbatim — no synonyms, no "
                  "additions, no prose."
            )
        if variant == "polarity-soft":
            # Polarity priming alone, no CoT invitation. Tests the
            # hypothesis that the "polarity"-variant regression on
            # the positive corpus (§7.6) comes from the
            # `# ruled out:` CoT path encouraging over-exclusion,
            # not from the priming itself.
            return (
                base
                + "The encoded section's structural elements are:\n"
                + f"  [{vocab_inline}]\n\n"
                + "IMPORTANT — many scenarios are constructed so that NO "
                  "element of this section is satisfied. The empty set `[]` "
                  "is a frequent and correct answer; do not feel obliged to "
                  "produce a non-empty subset.\n\n"
                  "Task: from the list above, return the subset of element "
                  "names that are SATISFIED by the scenario as stated. Reply "
                  'with ONLY a JSON array of strings (e.g. `["a", "b"]`); '
                  "use `[]` if no element is satisfied. Names must come "
                  "from the supplied list verbatim — no synonyms, no "
                  "additions, no prose."
            )
        # polarity priming + light CoT scaffold: explicitly call out
        # the empty-set case (the gpt-4o-mini polarity-negative
        # collapse from §7.6 motivated this) and invite a one-line
        # rule-out preamble before the final JSON array. Parser
        # tolerates the preamble: it extracts the LAST JSON array.
        return (
            base
            + "The encoded section's structural elements are:\n"
            + f"  [{vocab_inline}]\n\n"
            + "IMPORTANT — many scenarios are constructed so that NO "
              "element of this section is satisfied. The empty set `[]` "
              "is a frequent and correct answer; do not feel obliged to "
              "produce a non-empty subset.\n\n"
              "First, mentally walk through each element above and "
              "decide whether the scenario as stated establishes it. "
              "You may optionally output ONE short line beginning with "
              "`# ruled out:` listing element names you eliminated, "
              "before your final answer.\n\n"
              "Task: return the subset of element names from the list "
              "above that are SATISFIED by the scenario as stated. "
              'Final line must be ONLY a JSON array of strings (e.g. `["a", "b"]`); '
              "use `[]` if no element is satisfied. Names must come "
              "from the supplied list verbatim — no synonyms, no "
              "additions."
        )
    return (
        base
        + "Task: list the structural elements of that section that are "
          "SATISFIED by the scenario as stated. Reply with ONLY a JSON "
          'array of element name strings, e.g. `["deception", '
          '"fraudulent", "inducement"]`. No prose. Element names are '
          "short snake_case identifiers as they would appear in a "
          "structured statute encoding."
    )


def _prompt_exception(scenario: str, section: str) -> str:
    return (
        f"Scenario:\n{scenario}\n\n"
        f"Assume Penal Code s{section} applies. Task: name any defeating "
        "exception that fires from the scenario as stated. Reply with "
        "ONLY the exception name (snake_case identifier) or the literal "
        "word `none` if no exception fires. No prose."
    )


# =============================================================================
# Scoring
# =============================================================================


@dataclass
class TaskScore:
    correct: bool
    predicted: Any
    expected: Any
    f1: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None


@dataclass
class FixtureResult:
    fixture_id: str
    section: str
    t1_section: TaskScore
    t2_elements: TaskScore
    t3_exception: TaskScore
    elapsed_seconds: float


@dataclass
class BenchmarkResult:
    fixtures: List[FixtureResult] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.fixtures)

    def task_accuracy(self, task: str) -> float:
        if not self.fixtures:
            return 0.0
        correct = sum(1 for fr in self.fixtures
                      if getattr(fr, task).correct)
        return correct / len(self.fixtures)

    def mean_f1(self) -> float:
        scores = [fr.t2_elements.f1 for fr in self.fixtures
                  if fr.t2_elements.f1 is not None]
        return sum(scores) / len(scores) if scores else 0.0

    def stratified(self) -> Dict[str, Dict[str, Any]]:
        """Per-tag-prefix accuracy slices.

        Walks every fixture's ``tags`` field looking for ``key:value``
        pairs (e.g. ``chapter:xvi``, ``difficulty:basic``,
        ``category:property``). Returns a nested dict keyed by tag
        prefix → tag value → {n, t1, t2, t2_f1, t3}.
        """
        # Map each FixtureResult back to its source fixture for tag access.
        # We need fixture tags; recover them from the runtime store the
        # caller passes via `_attach_tags_to(result, fixtures)`.
        tags_by_id: Dict[str, Tuple[str, ...]] = getattr(self, "_tags_by_id", {})
        if not tags_by_id:
            return {}
        slices: Dict[str, Dict[str, List[FixtureResult]]] = {}
        for fr in self.fixtures:
            for tag in tags_by_id.get(fr.fixture_id, ()):
                if ":" not in tag:
                    continue
                prefix, _, value = tag.partition(":")
                slices.setdefault(prefix, {}).setdefault(value, []).append(fr)
        out: Dict[str, Dict[str, Any]] = {}
        for prefix, by_value in slices.items():
            out[prefix] = {}
            for value, frs in by_value.items():
                if not frs:
                    continue
                f1s = [fr.t2_elements.f1 for fr in frs if fr.t2_elements.f1 is not None]
                out[prefix][value] = {
                    "n": len(frs),
                    "t1_accuracy": sum(1 for fr in frs if fr.t1_section.correct) / len(frs),
                    "t2_accuracy": sum(1 for fr in frs if fr.t2_elements.correct) / len(frs),
                    "t2_mean_f1": (sum(f1s) / len(f1s)) if f1s else 0.0,
                    "t3_accuracy": sum(1 for fr in frs if fr.t3_exception.correct) / len(frs),
                }
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "t1_accuracy": self.task_accuracy("t1_section"),
            "t2_accuracy": self.task_accuracy("t2_elements"),
            "t2_mean_f1": self.mean_f1(),
            "t3_accuracy": self.task_accuracy("t3_exception"),
            "stratified": self.stratified(),
            "fixtures": [
                {
                    "id": fr.fixture_id,
                    "section": fr.section,
                    "t1": {"correct": fr.t1_section.correct,
                           "predicted": fr.t1_section.predicted,
                           "expected": fr.t1_section.expected},
                    "t2": {"correct": fr.t2_elements.correct,
                           "f1": fr.t2_elements.f1,
                           "predicted": list(fr.t2_elements.predicted)
                           if isinstance(fr.t2_elements.predicted, (list, tuple)) else fr.t2_elements.predicted,
                           "expected": list(fr.t2_elements.expected)
                           if isinstance(fr.t2_elements.expected, (list, tuple)) else fr.t2_elements.expected},
                    "t3": {"correct": fr.t3_exception.correct,
                           "predicted": fr.t3_exception.predicted,
                           "expected": fr.t3_exception.expected},
                    "elapsed_seconds": round(fr.elapsed_seconds, 3),
                }
                for fr in self.fixtures
            ],
            "not_legal_advice": True,
        }


def _canonical_section(s: str) -> str:
    """Strip leading `s` / `S.` / `Section`, surrounding whitespace, trailing
    punctuation. Returns the bare section number string."""
    raw = (s or "").strip().strip(".").strip()
    raw = re.sub(r"^(?:section|sec\.?|s\.?)\s*", "", raw, flags=re.IGNORECASE)
    return raw


def _canonical_exception(s: Optional[str]) -> str:
    if not s:
        return "none"
    return str(s).strip().lower().replace(" ", "_")


def _parse_elements(raw: str) -> List[str]:
    """Best-effort parse of an element-list LLM response.

    Tolerates a preceding ``# ruled out: …`` CoT preamble: extracts
    the LAST balanced JSON array from the response and parses that.
    """
    if not raw:
        return []
    raw = raw.strip()
    # Find the last balanced JSON array in the response.
    last_close = raw.rfind("]")
    if last_close >= 0:
        depth = 0
        last_open = -1
        for i in range(last_close, -1, -1):
            if raw[i] == "]":
                depth += 1
            elif raw[i] == "[":
                depth -= 1
                if depth == 0:
                    last_open = i
                    break
        if last_open >= 0:
            candidate = raw[last_open : last_close + 1]
            try:
                arr = json.loads(candidate)
                if isinstance(arr, list):
                    return [str(x).strip() for x in arr if str(x).strip()]
            except Exception:  # noqa: BLE001
                pass
    # Fall-back: split on commas / newlines, strip quotes / brackets.
    raw = raw.strip("[](){}")
    parts = re.split(r"[,\n]", raw)
    return [p.strip().strip("\"' `") for p in parts if p.strip()]


def _f1(predicted: List[str], expected: List[str]) -> Tuple[float, float, float]:
    pred_set = {x.lower() for x in predicted}
    exp_set = {x.lower() for x in expected}
    if not pred_set and not exp_set:
        return 1.0, 1.0, 1.0
    if not pred_set or not exp_set:
        return 0.0, 0.0, 0.0
    tp = len(pred_set & exp_set)
    precision = tp / len(pred_set)
    recall = tp / len(exp_set)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return f1, precision, recall


def score_fixture(
    fixture: Fixture, client: BenchmarkClient,
    *, variant: str = "polarity",
) -> FixtureResult:
    """Run all three tasks on a single fixture, return per-task scores."""
    t0 = time.monotonic()

    # `polarity-conditional` resolves per-fixture into polarity-soft or
    # baseline based on a cheap null-cue classifier on the scenario text.
    effective_variant = _resolve_variant(variant, fixture.scenario)

    # T1 — section. polarity-negative fixtures (truth_elements empty)
    # have an inherent ambiguity: the scenario is *about* a section
    # (e.g. an s100 illustration where no element fires), but a strict
    # reading is "no offence is made out, so no section applies". We
    # accept either the canonical section or `none` in that case; for
    # ordinary fixtures only the canonical section is correct.
    raw_section = client.query(_prompt_section(fixture.scenario, variant=effective_variant),
                               system=_SYSTEM_PROMPT, task_kind="section")
    pred_section = _canonical_section(raw_section)
    truth_canonical = _canonical_section(fixture.truth_section)
    is_polarity_negative = len(fixture.truth_elements) == 0
    t1_correct = pred_section == truth_canonical
    if is_polarity_negative and pred_section.lower() == "none":
        t1_correct = True
    t1 = TaskScore(
        correct=t1_correct,
        predicted=pred_section,
        expected=fixture.truth_section,
    )

    # T2 — elements. The encoded section's full element set lives on
    # `fact_facts`; passing it as the closed-set vocabulary turns T2
    # into honest multi-label classification rather than open-vocab
    # naming-convention recall (the latter conflates structural
    # reasoning with guessing our private snake_case names).
    vocabulary = sorted(fixture.fact_facts.keys()) if fixture.fact_facts else None
    raw_elements = client.query(
        _prompt_elements(fixture.scenario, fixture.truth_section,
                         vocabulary, variant=effective_variant),
        system=_SYSTEM_PROMPT, task_kind="elements",
    )
    pred_elements = _parse_elements(raw_elements)
    # When a vocabulary is in play, restrict the predicted set to it
    # — anything outside the vocab is hallucinated and grades as 0.
    if vocabulary:
        vocab_set = {v.lower() for v in vocabulary}
        pred_elements = [p for p in pred_elements if p.lower() in vocab_set]
    f1, precision, recall = _f1(pred_elements, list(fixture.truth_elements))
    t2 = TaskScore(
        correct=set(x.lower() for x in pred_elements) == set(x.lower() for x in fixture.truth_elements),
        predicted=pred_elements,
        expected=list(fixture.truth_elements),
        f1=f1, precision=precision, recall=recall,
    )

    # T3 — exception
    raw_exception = client.query(_prompt_exception(fixture.scenario, fixture.truth_section),
                                 system=_SYSTEM_PROMPT, task_kind="exception")
    pred_exception = _canonical_exception(raw_exception)
    expected_exception = _canonical_exception(fixture.truth_exception)
    t3 = TaskScore(
        correct=pred_exception == expected_exception,
        predicted=pred_exception,
        expected=expected_exception,
    )

    return FixtureResult(
        fixture_id=fixture.id,
        section=fixture.section,
        t1_section=t1,
        t2_elements=t2,
        t3_exception=t3,
        elapsed_seconds=time.monotonic() - t0,
    )


def run_benchmark(
    fixtures: List[Fixture], client: BenchmarkClient,
    *, progress: Optional[Callable[[int, int, FixtureResult], None]] = None,
    variant: str = "polarity",
) -> BenchmarkResult:
    """Score every fixture against the supplied client."""
    result = BenchmarkResult()
    # Attach a `fixture_id -> tags` map so `stratified()` can recover
    # per-tag slices without forcing the caller to manage that bookkeeping.
    result._tags_by_id = {fx.id: fx.tags for fx in fixtures}  # type: ignore[attr-defined]
    for i, fx in enumerate(fixtures, 1):
        try:
            fr = score_fixture(fx, client, variant=variant)
        except Exception as exc:  # noqa: BLE001 — keep run resilient
            fr = FixtureResult(
                fixture_id=fx.id, section=fx.section,
                t1_section=TaskScore(False, f"<error: {exc}>", fx.truth_section),
                t2_elements=TaskScore(False, [], list(fx.truth_elements), f1=0.0),
                t3_exception=TaskScore(False, f"<error: {exc}>",
                                       _canonical_exception(fx.truth_exception)),
                elapsed_seconds=0.0,
            )
        result.fixtures.append(fr)
        if progress is not None:
            progress(i, len(fixtures), fr)
    return result


def render_report(result: BenchmarkResult, *, show_per_fixture: bool = True) -> str:
    """Human-readable text report."""
    lines = [
        f"Yuho LLM legal-reasoning benchmark — n={result.n}",
        "",
        f"  T1 (section identification):  {result.task_accuracy('t1_section'):.1%}",
        f"  T2 (element-set recall):      {result.task_accuracy('t2_elements'):.1%}  (mean F1: {result.mean_f1():.3f})",
        f"  T3 (exception citation):      {result.task_accuracy('t3_exception'):.1%}",
    ]

    strat = result.stratified()
    if strat:
        for prefix in sorted(strat):
            lines.append("")
            lines.append(f"Stratified by `{prefix}`:")
            lines.append(f"  {'value':22s}  {'n':>4s}  {'T1':>6s}  {'T2-F1':>6s}  {'T3':>6s}")
            for value in sorted(strat[prefix]):
                row = strat[prefix][value]
                lines.append(
                    f"  {value:22s}  {row['n']:>4d}  "
                    f"{row['t1_accuracy']:>6.1%}  "
                    f"{row['t2_mean_f1']:>6.3f}  "
                    f"{row['t3_accuracy']:>6.1%}"
                )

    if show_per_fixture:
        lines.append("")
        lines.append("Per-fixture:")
        for fr in result.fixtures:
            lines.append(
                f"  [{fr.fixture_id:32s}] T1={'✓' if fr.t1_section.correct else '✗'}  "
                f"T2_F1={fr.t2_elements.f1 or 0:.2f}  "
                f"T3={'✓' if fr.t3_exception.correct else '✗'}  "
                f"({fr.elapsed_seconds:.2f}s)"
            )
    lines.append("")
    lines.append("Not legal advice — structural benchmark, not legal reasoning.")
    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--fixtures", type=Path, default=FIXTURES_DIR,
                   help="Override the fixtures directory")
    p.add_argument("--max-fixtures", type=int, default=0,
                   help="Cap number of fixtures (0 = no cap)")
    p.add_argument("--provider", choices=["anthropic", "openai"],
                   default=None,
                   help="LLM provider (default: inferred from --model: "
                        "claude-* → anthropic, gpt-* / o1-* / o3-* → openai)")
    p.add_argument("--model", default="claude-sonnet-4-6",
                   help="Model id. Anthropic: claude-sonnet-4-6, "
                        "claude-opus-4-7. OpenAI: gpt-4o, gpt-4o-mini, "
                        "o1, o3-mini, etc.")
    p.add_argument("--fake", action="store_true",
                   help="Use the deterministic fake client; no API calls")
    p.add_argument("--json", dest="json_out", action="store_true",
                   help="Emit JSON instead of human-readable text")
    p.add_argument("--out", type=Path, default=None,
                   help="Write report to this path (default: stdout)")
    p.add_argument("--no-per-fixture", action="store_true",
                   help="Hide the per-fixture table in the human report")
    p.add_argument("--prompt-variant",
                   choices=["baseline", "polarity", "polarity-soft",
                            "polarity-conditional"],
                   default="polarity",
                   help="Prompt variant. `baseline` = original v1 prompts; "
                        "`polarity` = adds polarity priming + optional "
                        "`# ruled out:` CoT preamble + `none` T1 option; "
                        "`polarity-soft` = same as `polarity` minus the "
                        "CoT invitation; `polarity-conditional` = cheap "
                        "regex classifier on scenario routes to "
                        "polarity-soft on null-cue hits, baseline "
                        "otherwise. Used for §7.6 N-way comparison.")
    args = p.parse_args()

    fixtures = load_fixtures(args.fixtures)
    if args.max_fixtures:
        fixtures = fixtures[: args.max_fixtures]
    if not fixtures:
        print("error: no fixtures loaded", file=sys.stderr)
        return 2

    if args.fake:
        client: BenchmarkClient = FakeClient(fixtures=fixtures)
    else:
        # Provider inference: --provider wins; else look at the model
        # prefix; else fall back to Anthropic for back-compat with the
        # original CLI default.
        provider = args.provider
        if provider is None:
            ml = args.model.lower()
            if ml.startswith("claude"):
                provider = "anthropic"
            elif ml.startswith(("gpt", "o1", "o3", "o4", "chatgpt")):
                provider = "openai"
            else:
                provider = "anthropic"
        try:
            if provider == "openai":
                client = OpenAIClient(model=args.model)
            else:
                client = AnthropicClient(model=args.model)
        except (ImportError, EnvironmentError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            print(
                "(use --fake to dry-run with a deterministic client)",
                file=sys.stderr,
            )
            return 2

    def _on_progress(i: int, n: int, fr: FixtureResult) -> None:
        print(
            f"  [{i}/{n}] {fr.fixture_id:32s} "
            f"T1={'✓' if fr.t1_section.correct else '✗'} "
            f"T2_F1={fr.t2_elements.f1 or 0:.2f} "
            f"T3={'✓' if fr.t3_exception.correct else '✗'}",
            file=sys.stderr,
        )

    if args.fake:
        client_label = "FakeClient"
    else:
        client_label = f"{type(client).__name__}({args.model})"
    print(f"Running {len(fixtures)} fixtures through {client_label} "
          f"(prompt-variant={args.prompt_variant})…",
          file=sys.stderr)
    result = run_benchmark(fixtures, client, progress=_on_progress,
                           variant=args.prompt_variant)

    output = (
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        if args.json_out else render_report(
            result, show_per_fixture=not args.no_per_fixture,
        )
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"wrote: {args.out}", file=sys.stderr)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
