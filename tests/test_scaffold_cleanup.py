from pathlib import Path

import click
import pytest

from yuho.ast import ASTBuilder
from yuho.cli.commands.generate import (
    ScaffoldConfig,
    generate_full_scaffold,
    generate_minimal_scaffold,
    generate_standard_scaffold,
)
from yuho.cli.commands.init import run_init
from yuho.cli.commands.test import run_test
from yuho.parser import get_parser
from yuho.transpile.alloy_transpiler import AlloyTranspiler


def _parse_module(source: str, filename: str = "<test>"):
    parser = get_parser()
    result = parser.parse(source, filename)
    assert not result.errors
    builder = ASTBuilder(result.source, filename)
    return builder.build(result.root_node)


@pytest.mark.parametrize(
    "factory",
    [
        generate_standard_scaffold,
        generate_minimal_scaffold,
        generate_full_scaffold,
    ],
)
def test_generated_scaffolds_are_parseable_and_todo_free(factory) -> None:
    config = ScaffoldConfig(section="299", title="Sample Offence", template="standard")
    source = factory(config)

    assert "TODO" not in source
    assert 'statute "299"' not in source

    module = _parse_module(source)
    assert len(module.statutes) == 1
    assert module.statutes[0].section_number == "299"


def test_run_init_creates_runnable_todo_free_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(click, "prompt", lambda *_args, **_kwargs: "321")

    project_dir = tmp_path / "sample_offence"
    run_init(name="Sample Offence", directory=str(project_dir), verbose=False)

    statute_file = project_dir / "sample_offence.yh"
    test_file = project_dir / "tests" / "test_sample_offence.yh"

    statute_source = statute_file.read_text(encoding="utf-8")
    test_source = test_file.read_text(encoding="utf-8")

    assert "TODO" not in statute_source
    assert "TODO" not in test_source
    assert "assert scaffold_ready() == TRUE;" in test_source

    _parse_module(statute_source, str(statute_file))
    _parse_module(test_source, str(test_file))

    run_test(file=str(test_file), verbose=False)


def test_alloy_transpiler_replaces_placeholder_assertions() -> None:
    source = """
statute 390 "Robbery" effective 1872-01-01 subsumes 378 {
    elements {
        actus_reus taking := "Taking property by force";
        mens_rea intent := "Intentional use of force";
    }
    penalty {
        imprisonment := 3 years .. 14 years;
    }
}

statute 378 "Theft" effective 1872-01-01 {
    elements {
        actus_reus taking := "Taking property";
        mens_rea intent := "Dishonest intention";
    }
    penalty {
        fine := $0.00 .. $10,000.00;
    }
}
"""
    ast = _parse_module(source)
    output = AlloyTranspiler().transpile(ast)

    assert "placeholder" not in output.lower()
    assert "assert NoContradictoryElements {" in output
    assert "Subsumption annotations retained for downstream penalty analysis" in output
    assert "s390 subsumes s378" in output
    assert "check PenaltyOrdering" not in output
