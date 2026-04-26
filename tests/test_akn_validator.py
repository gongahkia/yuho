"""Tests for the Akoma Ntoso structural validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from yuho.services.analysis import analyze_source
from yuho.transpile import TranspileTarget, get_transpiler
from yuho.transpile.akn_validator import (
    AKNValidationResult,
    validate_akn,
    validate_akn_against_xsd,
)


def _emit_akn(yuho_source: str) -> str:
    result = analyze_source(yuho_source, run_semantic=False)
    assert result.ast is not None, [str(e) for e in result.parse_errors]
    return get_transpiler(TranspileTarget.AKOMANTOSO).transpile(result.ast)


# =============================================================================
# Happy paths
# =============================================================================


def test_emitted_akn_validates_clean():
    src = '''
    statute 415 "Cheating" effective 1872-01-01 {
      elements { all_of {
        actus_reus deception := "Deceiving any person";
        mens_rea fraud := "Fraudulent intent";
      } }
    }
    '''
    result = validate_akn(_emit_akn(src))
    assert result.ok, result.errors


def test_real_s415_encoding_validates():
    """End-to-end smoke: actual library s415 -> AKN -> structural valid."""
    yh = Path("library/penal_code/s415_cheating/statute.yh")
    if not yh.exists():
        pytest.skip("library not present in this checkout")
    result = validate_akn(_emit_akn(yh.read_text()))
    assert result.ok, result.errors


# =============================================================================
# Failure cases — hand-rolled invalid documents
# =============================================================================


def test_malformed_xml_reports_parse_error():
    result = validate_akn("<not-valid-xml>")
    assert not result.ok
    assert any("not well-formed" in e for e in result.errors)


def test_wrong_root_element_flagged():
    bad = '<?xml version="1.0"?><wrong xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'
    result = validate_akn(bad)
    assert not result.ok
    assert any("akomaNtoso" in e for e in result.errors)


def test_wrong_namespace_flagged():
    bad = '<?xml version="1.0"?><akomaNtoso xmlns="http://example.com/wrong"/>'
    result = validate_akn(bad)
    assert not result.ok


def test_missing_act_flagged():
    bad = (
        '<?xml version="1.0"?>'
        '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'
    )
    result = validate_akn(bad)
    assert not result.ok
    assert any("<act>" in e for e in result.errors)


def test_missing_meta_block_flagged():
    bad = (
        '<?xml version="1.0"?>'
        '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">'
        '<act name="penalCode"><body/></act></akomaNtoso>'
    )
    result = validate_akn(bad)
    assert not result.ok
    assert any("<meta>" in e for e in result.errors)


def test_section_missing_num_flagged():
    bad = (
        '<?xml version="1.0"?>'
        '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">'
        '<act name="x">'
        '<meta><identification source="#x"><FRBRWork>'
        '<FRBRthis value="/x"/><FRBRuri value="/x"/><FRBRdate date="2020-01-01" name="g"/>'
        '<FRBRauthor href="#x"/><FRBRcountry value="sg"/>'
        '</FRBRWork></identification></meta>'
        '<body><section eId="sec_415"></section></body>'
        '</act></akomaNtoso>'
    )
    result = validate_akn(bad)
    assert not result.ok
    assert any("<num>" in e for e in result.errors)


def test_invalid_eid_pattern_flagged():
    bad = (
        '<?xml version="1.0"?>'
        '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">'
        '<act name="x">'
        '<meta><identification source="#x"><FRBRWork>'
        '<FRBRthis value="/x"/><FRBRuri value="/x"/><FRBRdate date="2020-01-01" name="g"/>'
        '<FRBRauthor href="#x"/><FRBRcountry value="sg"/>'
        '</FRBRWork></identification></meta>'
        '<body><section eId="bad-id"><num>415</num></section></body>'
        '</act></akomaNtoso>'
    )
    result = validate_akn(bad)
    assert not result.ok
    assert any("eId" in e for e in result.errors)


def test_aggregates_all_errors_in_one_pass():
    """The validator should not short-circuit on the first failure."""
    bad = (
        '<?xml version="1.0"?>'
        '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">'
        '<act name="x">'
        # missing <meta>
        '<body>'
        '<section eId="bad-id"></section>'  # bad eId AND missing <num>
        '</body></act></akomaNtoso>'
    )
    result = validate_akn(bad)
    assert not result.ok
    assert len(result.errors) >= 3


# =============================================================================
# XSD optional path
# =============================================================================


def test_xsd_path_handles_missing_lxml_gracefully():
    """When lxml is not installed, validator returns a clear error rather
    than raising. (The CI environment may or may not have lxml; this test
    asserts the contract either way: result is a validation result.)"""
    result = validate_akn_against_xsd("<akomaNtoso/>", xsd_path="/nonexistent.xsd")
    assert isinstance(result, AKNValidationResult)
    assert not result.ok
    # Either lxml-missing or load-failed is acceptable.
    assert any(
        "lxml" in e or "failed to load XSD" in e or "XSD" in e
        for e in result.errors
    )
