"""Public claims must remain tied to explicit, inspectable evidence."""

from scripts import verify_capability_claims
from scripts.verify_capability_claims import validate_capability_claims


def test_capability_claims_match_coverage_and_release_evidence() -> None:
    assert validate_capability_claims() == []


def test_claim_boundary_scans_every_checked_in_document() -> None:
    assert verify_capability_claims.PUBLIC_BOUNDARY_DOCUMENTS == (
        verify_capability_claims.ROOT / "docs",
    )
