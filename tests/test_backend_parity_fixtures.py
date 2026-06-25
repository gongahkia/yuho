"""Generated backend parity claim fixture contract."""

from __future__ import annotations

from pathlib import Path

from scripts.verify_backend_parity import PARITY_CLAIMS_REL, build_summary, load_claims
from yuho.cli.commands.verify import BACKEND_METADATA
from yuho.services.analysis import analyze_source
from yuho.verify.z3_solver import Z3Solver, Z3UnsupportedFeature


def test_backend_parity_fixture_schema_and_evidence_paths() -> None:
    claims = load_claims()

    assert claims["schema_version"] == 1
    assert claims["generated_from"]
    assert claims["parity_links"]
    assert claims["feature_coverage"]
    for source in claims["generated_from"]:
        assert Path(source).exists(), source
    for link in claims["parity_links"]:
        assert link["name"]
        evidence = link["evidence"]
        if evidence.endswith(".py"):
            assert Path(evidence).exists(), evidence


def test_backend_parity_summary_is_generated_from_fixture_rows() -> None:
    claims = load_claims()
    summary = build_summary()

    for link in claims["parity_links"]:
        assert f"{link['name']}: {link['evidence']}" in summary
    for row in claims["feature_coverage"]:
        assert f"- {row['feature']}: {row['status']}" in summary


def test_backend_parity_fixture_tracks_backend_metadata_boundaries() -> None:
    summary = build_summary()

    assert BACKEND_METADATA["alloy"]["status"] == "secondary-explicit-unsupported"
    assert "penalty semantics" in BACKEND_METADATA["alloy"]["unsupported_features"]
    assert "typed fact burden/proof-standard metadata" in BACKEND_METADATA["alloy"]["unsupported_features"]
    assert any(
        "case-law semantics" in feature
        for feature in BACKEND_METADATA["z3"]["unsupported_features"]
    )
    assert any(
        "typed fact burden/proof-standard metadata" in feature
        for feature in BACKEND_METADATA["z3"]["unsupported_features"]
    )
    assert "alloy (secondary-explicit-unsupported)" in summary


def test_backend_parity_docs_reference_generated_fixture() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    status = Path("docs/positioning/status-matrix.md").read_text(encoding="utf-8")
    canonical = Path("docs/researcher/canonical-semantics.md").read_text(encoding="utf-8")

    fixture_path = PARITY_CLAIMS_REL.as_posix()
    assert "secondary bounded-shape smoke backend" in readme
    assert fixture_path in status
    assert "scripts/verify_backend_parity.py" in status
    assert fixture_path in canonical


def test_z3_consistency_rejects_case_law_explicitly() -> None:
    result = analyze_source(
        """
        statute 1 "Case" {
            elements { actus_reus act := "Act"; }
            caselaw "A v B" "2026 SGCA 1" {
                "Narrow reading"
                element act
            }
        }
        """,
        file="<z3-unsupported>",
        run_semantic=False,
    )
    assert result.ast is not None

    try:
        Z3Solver().check_statute_consistency(result.ast)
    except Z3UnsupportedFeature as exc:
        assert "s1: case-law semantics" in exc.features
    else:
        raise AssertionError("Z3 consistency check accepted unsupported case-law")


def test_z3_consistency_rejects_typed_fact_burdens_explicitly() -> None:
    result = analyze_source(
        """
        statute 1 "Burden" {
            elements {
                actus_reus act := "Act" burden prosecution beyond_reasonable_doubt;
            }
        }
        """,
        file="<z3-unsupported>",
        run_semantic=False,
    )
    assert result.ast is not None

    try:
        Z3Solver().check_statute_consistency(result.ast)
    except Z3UnsupportedFeature as exc:
        assert "s1.act: typed fact burden/proof standard" in exc.features
    else:
        raise AssertionError("Z3 consistency check accepted unsupported burden metadata")
