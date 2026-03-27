"""Regression tests for related-statute penalty ordering checks."""

import pytest

from yuho.ast import ASTBuilder
from yuho.parser import get_parser
from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE


def _parse_source(source: str):
    parser = get_parser()
    result = parser.parse(source, "<test>")
    builder = ASTBuilder(result.source, "<test>")
    return builder.build(result.root_node)


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_z3_penalty_ordering_uses_explicit_subsumes_metadata() -> None:
    source = """
statute 100 "Base Offence" {
    elements {
        actus_reus act := "Base act";
    }
    penalty {
        imprisonment := 1 years .. 5 years;
    }
}

statute 200 "Aggravated Offence" subsumes 100 {
    elements {
        actus_reus act := "Aggravated act";
    }
    penalty {
        imprisonment := 1 years .. 5 years;
    }
}
"""

    ast = _parse_source(source)
    diagnostics = Z3Generator().generate_consistency_check(ast)

    penalty_diag = next(
        diag for diag in diagnostics if diag.check_name == "penalty_ordering_200_vs_100"
    )
    assert not penalty_diag.passed
    assert "imprisonment range is identical" in penalty_diag.message
    assert "no distinguishing penalty feature remains" in penalty_diag.message


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_z3_penalty_ordering_flags_weaker_subsuming_penalty() -> None:
    source = """
statute 101 "Base Offence" {
    elements {
        actus_reus act := "Base act";
    }
    penalty {
        imprisonment := 1 years .. 7 years;
    }
}

statute 201 "Aggravated Offence" subsumes 101 {
    elements {
        actus_reus act := "Aggravated act";
    }
    penalty {
        imprisonment := 1 years .. 5 years;
    }
}
"""

    ast = _parse_source(source)
    diagnostics = Z3Generator().generate_consistency_check(ast)

    penalty_diag = next(
        diag for diag in diagnostics if diag.check_name == "penalty_ordering_201_vs_101"
    )
    assert not penalty_diag.passed
    assert "below child max" in penalty_diag.message
