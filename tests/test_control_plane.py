"""The published release workflow must reach the full release-audit plan."""

from scripts.verify_control_plane import verify_release_gate_wiring


def test_release_gate_wiring_matches_the_release_audit_plan() -> None:
    verify_release_gate_wiring()
