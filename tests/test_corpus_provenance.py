"""Corpus provenance ledger completeness checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.verify_corpus_provenance import validate_corpus_provenance


def test_penal_code_corpus_provenance_is_complete() -> None:
    assert validate_corpus_provenance() == []


def test_provenance_recomputes_raw_and_encoded_hashes(tmp_path: Path) -> None:
    source = tmp_path / "library" / "penal_code" / "s1_example" / "statute.yh"
    source.parent.mkdir(parents=True)
    source.write_text('statute 1 "Example" {}\n', encoding="utf-8")
    raw = tmp_path / "raw.json"
    raw.write_text(
        json.dumps({"sections": [{"number": "1", "text": "Example source"}]}), encoding="utf-8"
    )
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps(
            {
                "n_sections": 1,
                "entries": [
                    {
                        "section_number": "1",
                        "sso_url": "https://example.test/s1",
                        "sso_anchor": "s1",
                        "raw": {"sha256": hashlib.sha256(b"Example source").hexdigest()},
                        "encoding": {
                            "yh_path": "library/penal_code/s1_example/statute.yh",
                            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                            "first_commit": {"sha": "first"},
                            "last_commit": {"sha": "last"},
                        },
                        "coverage": {"L1": True, "L2": True, "L3": "stamped"},
                        "provenance": {
                            "yuho_version": "5.1.0",
                            "scrape_date": "2026-01-01",
                            "encoding_commit": "commit",
                            "corpus_generated_at": "2026-01-01",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert validate_corpus_provenance(ledger, raw, tmp_path, expected_sections=1) == []
    source.write_text('statute 1 "Changed" {}\n', encoding="utf-8")
    assert validate_corpus_provenance(ledger, raw, tmp_path, expected_sections=1) == [
        "s1: encoded source hash does not match library/penal_code/s1_example/statute.yh"
    ]
