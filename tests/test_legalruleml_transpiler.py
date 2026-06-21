"""Tests for the LegalRuleML transpiler."""

from __future__ import annotations

try:
    from lxml import etree as _ET

    _BACKEND = "lxml"
except ImportError:
    from xml.etree import ElementTree as _ET

    _BACKEND = "stdlib"

from yuho.ast import nodes
from yuho.transpile import TranspileTarget, get_transpiler
from yuho.transpile.legalruleml_transpiler import LegalRuleMLTranspiler


class ET:
    @staticmethod
    def fromstring(xml):
        if _BACKEND == "lxml" and isinstance(xml, str):
            return _ET.fromstring(xml.encode("utf-8"))
        return _ET.fromstring(xml)


_LRML = "{http://docs.oasis-open.org/legalruleml/ns/v1.0/}"


def _module() -> nodes.ModuleNode:
    base = nodes.ExceptionNode(
        label="base",
        condition=nodes.StringLit("base defence"),
        effect=nodes.StringLit("no conviction"),
        priority=1,
    )
    override = nodes.ExceptionNode(
        label="override",
        condition=nodes.StringLit("override defence"),
        effect=nodes.StringLit("no conviction"),
        priority=2,
        defeats="base",
    )
    statute = nodes.StatuteNode(
        section_number="1",
        title=nodes.StringLit("Demo"),
        definitions=(nodes.DefinitionEntry("property", nodes.StringLit("thing")),),
        elements=(
            nodes.ElementGroupNode(
                "all_of",
                (
                    nodes.ElementNode("actus_reus", "taking", nodes.StringLit("takes")),
                    nodes.ElementNode(
                        "obligation",
                        "report",
                        nodes.StringLit("reports"),
                        actor="offender",
                    ),
                    nodes.ElementNode("permission", "enter", nodes.StringLit("may enter")),
                    nodes.ElementNode(
                        "prohibition",
                        "retain",
                        nodes.StringLit("must not retain"),
                    ),
                ),
            ),
        ),
        penalty=nodes.PenaltyNode(
            imprisonment_max=nodes.DurationNode(years=2),
            fine_unlimited=True,
        ),
        illustrations=(),
        exceptions=(base, override),
    )
    return nodes.ModuleNode((), (), (), (statute,), ())


def _root():
    xml = LegalRuleMLTranspiler().transpile(_module())
    return ET.fromstring(xml)


def test_target_and_extension():
    transpiler = LegalRuleMLTranspiler()
    assert transpiler.target is TranspileTarget.LEGALRULEML
    assert TranspileTarget.LEGALRULEML.file_extension == ".lrml"
    assert TranspileTarget.from_string("lrml") is TranspileTarget.LEGALRULEML
    assert TranspileTarget.from_string("legalruleml") is TranspileTarget.LEGALRULEML
    assert isinstance(get_transpiler(TranspileTarget.LEGALRULEML), LegalRuleMLTranspiler)


def test_emits_well_formed_legalruleml_root():
    root = _root()
    assert root.tag == _LRML + "LegalRuleML"
    assert root.find(_LRML + "LegalSources") is not None
    assert root.find(_LRML + "Statements") is not None


def test_deontic_element_metadata_maps_to_lrml_nodes():
    root = _root()
    assert root.find(f".//{_LRML}Obligation") is not None
    assert root.find(f".//{_LRML}Permission") is not None
    assert root.find(f".//{_LRML}Prohibition") is not None


def test_defeats_metadata_maps_to_override_statement():
    root = _root()
    overrides = root.findall(f".//{_LRML}Override")
    pairs = {(node.attrib["over"], node.attrib["under"]) for node in overrides}
    assert ("#ps_s_x_1_exc_override", "#ps_s_x_1_exc_base") in pairs


def test_penalty_statement_links_to_prescriptive_statement():
    root = _root()
    penalty = root.find(f".//{_LRML}PenaltyStatement")
    reparation = root.find(f".//{_LRML}Reparation")
    assert penalty is not None
    assert reparation is not None
    assert reparation.find(_LRML + "appliesPenalty").attrib["keyref"] == "#pen_s_x_1_1"
    assert reparation.find(_LRML + "toPrescriptiveStatement").attrib["keyref"] == "#ps_s_x_1"
