"""Tests for jurisdiction-typed IPC proof-of-concept sections."""

from __future__ import annotations

from pathlib import Path

import pytest

from yuho.services.analysis import analyze_file


IPC_PROOF_SECTIONS = (
    "s300_murder",
    "s302_punishment_for_murder",
    "s375_rape",
    "s378_theft",
    "s420_cheating_inducing_delivery_property",
)


@pytest.mark.skipif(
    not Path("library/indian_penal_code").exists(),
    reason="library/indian_penal_code not present in this checkout",
)
def test_ipc_proof_sections_use_first_class_jurisdiction():
    for name in IPC_PROOF_SECTIONS:
        path = Path("library/indian_penal_code") / name / "statute.yh"
        source = path.read_text(encoding="utf-8")
        assert " jurisdiction india " in source
        assert "/// @jurisdiction india" not in source

        result = analyze_file(path, run_semantic=False)
        assert not result.parse_errors
        statute = result.ast.statutes[0]
        assert statute.jurisdiction == "india"
        assert statute.jurisdiction_node
        assert statute.jurisdiction_node.name == "india"
