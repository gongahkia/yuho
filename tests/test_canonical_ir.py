"""Regression tests for the versioned canonical-IR boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from yuho.ast import ASTBuilder
from yuho.eval import StatuteEvaluator, StructInstance, Value
from yuho.ir import (
    CANONICAL_IR_SCHEMA,
    CANONICAL_IR_VERSION,
    canonical_hash,
    diagnose_capabilities,
    lower_module,
    lower_statute,
)
from yuho.parser import get_parser
from yuho.services.analysis import analyze_file, analyze_source
from yuho.verify.alloy import AlloyGenerator, AlloyUnsupportedFeature
from yuho.verify.z3_solver import Z3_AVAILABLE, Z3Generator


def _module(source: str):
    parsed = get_parser().parse(source)
    assert not parsed.errors, parsed.errors
    return ASTBuilder(source).build(parsed.root_node)


def test_canonical_ir_serialization_is_deterministic_and_semantic() -> None:
    compact = 'statute 1 "Example" { elements { actus_reus act := "act"; } }'
    spaced = """
        statute 1 "Example" {
            elements {
                actus_reus act := "act";
            }
        }
    """

    compact_ir = lower_module(_module(compact), source=compact)
    spaced_ir = lower_module(_module(spaced), source=spaced)

    assert compact_ir.schema == CANONICAL_IR_SCHEMA
    assert compact_ir.version == CANONICAL_IR_VERSION
    assert compact_ir.serialize() == compact_ir.serialize()
    assert compact_ir.digest == spaced_ir.digest
    assert compact_ir.source_hash != spaced_ir.source_hash
    assert compact_ir.artifact_digest != spaced_ir.artifact_digest


def test_lowering_preserves_scoped_subsection_paths_and_requirement_groups() -> None:
    source = """
        statute 84 "Scoped" {
            subsection (1) {
                elements {
                    all_of {
                        actus_reus act := "act";
                        any_of {
                            circumstance first_limb := "first";
                            circumstance second_limb := "second";
                        }
                    }
                }
            }
        }
    """

    ir = lower_module(_module(source), source=source)
    provision = ir.module.statutes[0].root.children[0]

    assert provision.citation == "s84(1)"
    assert provision.elements[0].to_dict()["combinator"] == "all_of"
    assert provision.elements[0].to_dict()["members"][1]["combinator"] == "any_of"


def test_analysis_exposes_canonical_ir_provenance() -> None:
    source = 'statute 1 "Example" { elements { actus_reus act := "act"; } }'

    result = analyze_source(source, file="<canonical-ir>", run_semantic=True)

    assert result.is_valid
    assert result.canonical_ir is not None
    payload = result.validation_payload()
    assert payload["canonical_ir"]["schema"] == CANONICAL_IR_SCHEMA
    assert payload["canonical_ir"]["hash"] == result.canonical_ir.digest


def test_checked_in_penal_code_corpus_lowers_to_canonical_ir() -> None:
    paths = sorted(Path("library/penal_code").glob("*/statute.yh"))

    assert len(paths) == 524
    for path in paths:
        result = analyze_file(path, run_semantic=False)
        assert result.ast_valid, path
        assert result.canonical_ir is not None, path


def test_runtime_uses_canonical_statute_adapter_and_records_provenance() -> None:
    source = 'statute 1 "Example" { elements { actus_reus act := "act"; } }'
    module = _module(source)
    statute = module.statutes[0]
    facts = StructInstance("Facts", {"act": Value(raw=True, type_tag="bool")})

    result = StatuteEvaluator().evaluate(statute, facts)

    assert result.overall_satisfied
    assert result.canonical_ir_version == CANONICAL_IR_VERSION
    assert result.canonical_ir_hash == canonical_hash(lower_statute(statute))
    assert result.diagnostics == ()


def test_nested_runtime_uses_its_canonical_ir_branch_semantics() -> None:
    source = """
        statute 84 "Scoped" {
            subsection (1) {
                elements { actus_reus act := "act"; }
            }
        }
    """
    statute = _module(source).statutes[0]
    facts = StructInstance("Facts", {"act": Value(raw=True, type_tag="bool")})

    result = StatuteEvaluator().evaluate(statute, facts)

    assert result.overall_satisfied
    assert result.branch_results[0].citation == "s84(1)"
    assert not any(diagnostic.feature == "subsection" for diagnostic in result.diagnostics)


def test_backend_capability_diagnostics_are_explicit() -> None:
    source = """
        statute 84 "Scoped" {
            subsection (1) {
                elements { actus_reus act := "act"; }
            }
        }
    """
    ir = lower_module(_module(source), source=source)

    diagnostics = diagnose_capabilities(ir, "alloy")

    assert any(diagnostic.feature == "subsection" for diagnostic in diagnostics)
    with pytest.raises(AlloyUnsupportedFeature, match="canonical-IR subsection"):
        AlloyGenerator().generate_canonical(ir, ast_adapter=_module(source))


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_z3_records_the_canonical_ir_artifact_it_lowered() -> None:
    source = 'statute 1 "Example" { elements { actus_reus act := "act"; } }'
    module = _module(source)
    ir = lower_module(module)
    generator = Z3Generator()

    solver, _ = generator.generate_canonical(ir, ast_adapter=module)

    assert solver is not None
    assert generator.canonical_ir_hash == ir.digest
