"""Case-law treatment vocabulary."""

from __future__ import annotations


TREATMENT_KIND_ALIASES = {
    "follows": "followed",
    "distinguishes": "distinguished",
    "overrules": "overruled",
    "reverses": "reversed",
    "approves": "approved",
    "disapproves": "disapproved",
    "applies": "applied",
}

TREATMENT_KINDS = (
    "followed",
    "distinguished",
    "overruled",
    "reversed",
    "approved",
    "disapproved",
    "applied",
)

TREATMENT_EDGE_KINDS = tuple(f"treatment_{kind}" for kind in TREATMENT_KINDS)
INACTIVE_TREATMENT_KINDS = frozenset({"distinguished", "overruled", "reversed", "disapproved"})


def normalize_treatment_kind(kind: str) -> str:
    return TREATMENT_KIND_ALIASES.get(kind, kind)


def is_inactive_treatment(kind: str) -> bool:
    return normalize_treatment_kind(kind) in INACTIVE_TREATMENT_KINDS
