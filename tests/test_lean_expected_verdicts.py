from __future__ import annotations

from scripts.verify_lean_expected_verdicts import compare_verdicts


def test_lean_expected_verdict_comparison_detects_smoke_agreement() -> None:
    rows = [
        {
            "name": "s299_true",
            "statute": "s299",
            "facts": "factsHomicide",
            "factValues": {"death": True, "intent": True},
            "expected": True,
        },
        {
            "name": "s299_missing_intent",
            "statute": "s299",
            "facts": "factsHomicideMissingIntent",
            "factValues": {"death": True},
            "expected": False,
        },
        {
            "name": "s300_consent_exception",
            "statute": "s300",
            "facts": "factsMurderConsent",
            "factValues": {"death": True, "intent_to_kill": True, "exc_consent": True},
            "expected": False,
        },
    ]

    assert compare_verdicts(rows) == []


def test_lean_expected_verdict_comparison_reports_mismatch() -> None:
    rows = [
        {
            "name": "s299_wrong",
            "statute": "s299",
            "facts": "factsHomicide",
            "factValues": {"death": True, "intent": True},
            "expected": False,
        }
    ]

    mismatches = compare_verdicts(rows)

    assert len(mismatches) == 1
    assert mismatches[0].name == "s299_wrong"
    assert mismatches[0].expected is False
    assert mismatches[0].actual is True
