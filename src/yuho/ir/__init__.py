"""Versioned canonical intermediate representation for Yuho."""

from yuho.ir.canonical import (
    CANONICAL_IR_SCHEMA,
    CANONICAL_IR_VERSION,
    CapabilityDiagnostic,
    CapabilityStatus,
    CanonicalElement,
    CanonicalElementGroup,
    CanonicalIR,
    CanonicalModule,
    CanonicalProvision,
    CanonicalStatute,
    canonical_hash,
    diagnose_capabilities,
    diagnose_statute_capabilities,
    lower_module,
    lower_statute,
)

__all__ = [
    "CANONICAL_IR_SCHEMA",
    "CANONICAL_IR_VERSION",
    "CapabilityDiagnostic",
    "CapabilityStatus",
    "CanonicalElement",
    "CanonicalElementGroup",
    "CanonicalIR",
    "CanonicalModule",
    "CanonicalProvision",
    "CanonicalStatute",
    "canonical_hash",
    "diagnose_capabilities",
    "diagnose_statute_capabilities",
    "lower_module",
    "lower_statute",
]
