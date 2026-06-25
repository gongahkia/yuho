"""Corpus provenance ledger completeness checks."""

from __future__ import annotations

from scripts.verify_corpus_provenance import validate_corpus_provenance


def test_penal_code_corpus_provenance_is_complete() -> None:
    assert validate_corpus_provenance() == []
