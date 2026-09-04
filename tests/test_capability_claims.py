"""Public claims must remain tied to explicit, inspectable evidence."""

from scripts.verify_capability_claims import validate_capability_claims


def test_capability_claims_match_coverage_and_release_evidence() -> None:
    assert validate_capability_claims() == []
