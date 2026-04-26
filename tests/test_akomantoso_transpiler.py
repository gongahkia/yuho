"""Tests for the Akoma Ntoso (LegalDocML) transpiler."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from yuho.services.analysis import analyze_source
from yuho.transpile import TranspileTarget, get_transpiler


_AKN_NS = "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}"


def _transpile(source: str) -> str:
    result = analyze_source(source, run_semantic=False)
    assert result.ast is not None, [str(e) for e in result.parse_errors]
    return get_transpiler(TranspileTarget.AKOMANTOSO).transpile(result.ast)


def test_target_string_aliases():
    assert TranspileTarget.from_string("akn") is TranspileTarget.AKOMANTOSO
    assert TranspileTarget.from_string("akomantoso") is TranspileTarget.AKOMANTOSO
    assert TranspileTarget.from_string("legaldocml") is TranspileTarget.AKOMANTOSO


def test_file_extension_is_xml():
    assert TranspileTarget.AKOMANTOSO.file_extension == ".xml"


def test_emits_well_formed_xml():
    source = '''
    statute 415 "Cheating" effective 1872-01-01 {
      elements { all_of {
        actus_reus deception := "Deceiving any person";
      } }
      penalty {
        imprisonment := 1 year .. 7 years;
      }
    }
    '''
    xml = _transpile(source)
    root = ET.fromstring(xml)
    assert root.tag == _AKN_NS + "akomaNtoso"


def test_act_section_structure():
    source = '''
    statute 300 "Murder" effective 1872-01-01 {
      elements { all_of {
        actus_reus killing := "Causing death";
        mens_rea intent := "Intent to kill";
      } }
    }
    '''
    root = ET.fromstring(_transpile(source))
    act = root.find(_AKN_NS + "act")
    assert act is not None
    assert act.attrib.get("name") == "penalCode"
    body = act.find(_AKN_NS + "body")
    sections = body.findall(_AKN_NS + "section")
    assert len(sections) == 1
    section = sections[0]
    assert section.attrib.get("eId") == "sec_300"
    num = section.find(_AKN_NS + "num")
    assert num.text == "300"
    heading = section.find(_AKN_NS + "heading")
    assert heading.text == "Murder"


def test_meta_frbr_block_present():
    source = 'statute 1 "Demo" effective 2020-01-01 { elements { all_of { actus_reus a := "x"; } } }'
    root = ET.fromstring(_transpile(source))
    frbr = root.find(f"{_AKN_NS}act/{_AKN_NS}meta/{_AKN_NS}identification/{_AKN_NS}FRBRWork")
    assert frbr is not None
    country = frbr.find(_AKN_NS + "FRBRcountry")
    assert country.attrib.get("value") == "sg"
    date = frbr.find(_AKN_NS + "FRBRdate")
    assert date.attrib.get("date") == "2020-01-01"


def test_elements_emitted_with_class_attr():
    source = '''
    statute 1 "Demo" {
      elements { all_of {
        actus_reus deception := "Deceives";
        mens_rea fraud := "Intent";
      } }
    }
    '''
    root = ET.fromstring(_transpile(source))
    items = root.findall(
        f".//{_AKN_NS}blockList[@class='elements']/{_AKN_NS}item"
    )
    assert len(items) == 2
    classes = {item.attrib.get("class") for item in items}
    assert classes == {"actus_reus", "mens_rea"}


def test_exception_block_emitted():
    """AKN has no first-class `<exception>`; emitted as `<hcontainer
    name="exception">`, the schema-canonical extension point."""
    source = '''
    statute 1 "Demo" {
      elements { all_of { actus_reus a := "x"; } }
      exception consent {
        "victim consents"
        "no offence is made out"
        when facts.consent == "true"
      }
    }
    '''
    root = ET.fromstring(_transpile(source))
    excs = [
        h for h in root.findall(f".//{_AKN_NS}hcontainer")
        if h.attrib.get("name") == "exception"
    ]
    assert len(excs) == 1
    num = excs[0].find(_AKN_NS + "num")
    assert num.text == "consent"


def test_meta_frbr_expression_and_manifestation_present():
    """OASIS XSD requires all three FRBR siblings inside `<identification>`."""
    source = 'statute 1 "Demo" effective 2020-01-01 { elements { all_of { actus_reus a := "x"; } } }'
    root = ET.fromstring(_transpile(source))
    ident = root.find(f"{_AKN_NS}act/{_AKN_NS}meta/{_AKN_NS}identification")
    assert ident is not None
    assert ident.find(_AKN_NS + "FRBRWork") is not None
    assert ident.find(_AKN_NS + "FRBRExpression") is not None
    assert ident.find(_AKN_NS + "FRBRManifestation") is not None


@pytest.mark.skipif(
    not Path("library/penal_code/s415_cheating/statute.yh").exists(),
    reason="library/penal_code not present in this checkout",
)
def test_s415_round_trip_well_formed():
    """End-to-end smoke: real s415 encoding -> AKN -> well-formed XML."""
    text = Path("library/penal_code/s415_cheating/statute.yh").read_text()
    xml = _transpile(text)
    # Must parse without raising
    ET.fromstring(xml)
