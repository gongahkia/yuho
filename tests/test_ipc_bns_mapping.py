"""IPC/BNS structural mapping coverage."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "library" / "_index" / "ipc_bns_mapping.json"


def _rows() -> dict[str, dict]:
    payload = json.loads(MAPPING.read_text(encoding="utf-8"))
    return {row["bns_number"]: row for row in payload["mappings"]}


def test_ipc_bns_mapping_has_one_row_per_bns_section():
    payload = json.loads(MAPPING.read_text(encoding="utf-8"))

    assert payload["method"] == "structural_title_body_token_overlap_v1"
    assert payload["stats"]["ipc_sections"] == 493
    assert payload["stats"]["bns_sections"] == 358
    assert len(payload["mappings"]) == 358


def test_ipc_bns_mapping_known_anchors():
    rows = _rows()
    expected = {
        "100": "299",
        "101": "300",
        "103": "302",
        "303": "378",
        "318": "415",
        "356": "499",
    }

    for bns_number, ipc_number in expected.items():
        assert rows[bns_number]["best_ipc"]["ipc_number"] == ipc_number
