"""Typed criminal outcomes and their traceable legal transitions.

These values describe the evaluator's result; they do not provide legal
advice or decide facts beyond the supported Yuho rule fragment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


class CriminalOutcomeKind(str, Enum):
    """The legal result of a supported charging-rule evaluation."""

    NOT_PROVED = "not_proved"
    ACQUITTED = "acquitted"
    REDUCED_TO = "reduced_to"
    CONVICTED = "convicted"
    SPECIAL_DISPOSITION = "special_disposition"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class OutcomeSource:
    """The statute/subsection declaration that caused an outcome transition."""

    citation_path: Tuple[str, ...]
    source_kind: str
    declaration_index: int
    outcome_kind: str
    target: Optional[str] = None
    source_version: Tuple[str, ...] = ()

    @property
    def citation(self) -> str:
        section, *subsections = self.citation_path
        return f"s{section}{''.join(subsections)}"


@dataclass(frozen=True)
class OutcomeTarget:
    """The resolved target of a lesser-offence transition."""

    section: str
    title: str
    outcome_kind: CriminalOutcomeKind
    overall_satisfied: Optional[bool]


@dataclass(frozen=True)
class SpecialDisposition:
    """A procedural consequence that accompanies a substantive outcome."""

    reference: str
    source: OutcomeSource


@dataclass(frozen=True)
class OutcomeDiagnostic:
    """A typed outcome could not be completed without losing legal meaning."""

    code: str
    message: str
    source: Optional[OutcomeSource] = None


@dataclass(frozen=True)
class CriminalOutcome:
    """A typed criminal outcome with its legal and factual provenance."""

    kind: CriminalOutcomeKind
    underlying_act_found: bool
    source: Optional[OutcomeSource] = None
    transition_sources: Tuple[OutcomeSource, ...] = ()
    target: Optional[OutcomeTarget] = None
    disposition: Optional[SpecialDisposition] = None
    facts_used: Tuple[str, ...] = ()
    diagnostics: Tuple[OutcomeDiagnostic, ...] = ()
    acquitted: bool = False

    @property
    def is_determinate(self) -> bool:
        return self.kind is not CriminalOutcomeKind.UNRESOLVED
