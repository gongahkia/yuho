"""Tests for `scripts/bulk_contrast.py` — the bulk Z3-contrast driver.

Pins:
- The pair collector returns at least the canonical doctrinal
  pairs (s299↔s300 via subsumes).
- A capped run produces the expected output layout: per-pair JSON
  files + a top-level `index.json` summary.
- Per-pair failures (sections with no elements) are logged in the
  index without aborting the run.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LIBRARY = REPO / "library" / "penal_code"
SCRIPT = REPO / "scripts" / "bulk_contrast.py"


@pytest.mark.skipif(
    not (LIBRARY / "s299_culpable_homicide" / "statute.yh").exists()
    or not (LIBRARY / "s300_murder" / "statute.yh").exists(),
    reason="Penal Code library not present",
)
def test_pair_collector_includes_subsumes_canonical_pair():
    sys.path.insert(0, str(REPO / "scripts"))
    sys.path.insert(0, str(REPO / "src"))
    import bulk_contrast
    pairs = bulk_contrast._collect_pairs(LIBRARY)
    assert any(
        a == "300" and b == "299" and kind == "subsumes"
        for (a, b, kind) in pairs
    ), "expected (300, 299, subsumes) — s300 subsumes s299"


@pytest.mark.skipif(
    not (LIBRARY / "s299_culpable_homicide" / "statute.yh").exists()
    or not (LIBRARY / "s300_murder" / "statute.yh").exists(),
    reason="Penal Code library not present",
)
def test_bulk_run_capped_produces_index_and_pairs(tmp_path):
    out_dir = tmp_path / "contrast"
    r = subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--out-dir", str(out_dir),
            "--max-pairs", "5",
            "--kinds", "subsumes",
            "--timeout-ms", "10000",
        ],
        capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert (out_dir / "index.json").exists()
    summary = json.loads((out_dir / "index.json").read_text())
    assert summary["n_pairs"] >= 1
    assert summary["n_ok"] >= 1
    assert summary["not_legal_advice"] is True
    # Every per-pair file declared in the index should land on disk.
    landed_pairs = [k for k, v in summary["pairs"].items() if v["ok"]]
    for slug in landed_pairs:
        assert (out_dir / slug).exists()
        payload = json.loads((out_dir / slug).read_text())
        assert payload["contrast"] is True
        assert payload["a_conviction"] is True
        assert payload["b_conviction"] is False
        assert "pair_kind" in payload
