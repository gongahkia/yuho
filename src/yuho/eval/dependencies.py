"""Traceable cross-section dependency results for runtime evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from yuho.ir import CanonicalDependency


@dataclass(frozen=True)
class DependencyDiagnostic:
    """A dependency could not be evaluated in the active rule environment."""

    code: str
    message: str
    citation_path: Tuple[str, ...]
    target_section: Optional[str] = None


@dataclass(frozen=True)
class DependencySubresult:
    """The relevant, compact result of evaluating a dependency target."""

    statute_section: str
    statute_title: str
    overall_satisfied: Optional[bool]
    is_determinate: bool
    branch_paths: Tuple[Tuple[str, ...], ...]


@dataclass(frozen=True)
class DependencyResult:
    """One canonical edge and the target result that affected its guard."""

    edge: CanonicalDependency
    status: str
    subresult: Optional[DependencySubresult] = None
    diagnostic: Optional[DependencyDiagnostic] = None
