"""Computable statute definition support."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.ast import nodes
from yuho.cli.main import cli
from yuho.eval.facts import struct_from_facts
from yuho.eval.statute_evaluator import StatuteEvaluator
from yuho.explain import DatalogExplainer
from yuho.resolver import ModuleResolver
from yuho.services.analysis import analyze_file, analyze_source
from yuho.transpile.english_transpiler import EnglishTranspiler
from yuho.transpile.latex_transpiler import LaTeXTranspiler


SOURCE = """
statute 1 "Computed" {
  definitions {
    deceptive := facts.representation.falsehood;
  }
  elements {
    actus_reus deception := deceptive;
    circumstance harm := deceptive;
  }
  penalty {
    fine := $0.00 .. $1.00;
  }
}
"""


def _fact_path(*parts: str) -> nodes.ASTNode:
    expr: nodes.ASTNode = nodes.IdentifierNode("facts")
    for part in parts:
        expr = nodes.FieldAccessNode(base=expr, field_name=part)
    return expr


def _statute() -> nodes.StatuteNode:
    definition = nodes.DefinitionEntry(
        term="deceptive",
        definition=_fact_path("representation", "falsehood"),
    )
    return nodes.StatuteNode(
        section_number="1",
        title=nodes.StringLit("Computed"),
        definitions=(definition,),
        elements=(
            nodes.ElementNode(
                element_type="actus_reus",
                name="deception",
                description=nodes.IdentifierNode("deceptive"),
            ),
            nodes.ElementNode(
                element_type="circumstance",
                name="harm",
                description=nodes.IdentifierNode("deceptive"),
            ),
        ),
        penalty=None,
        illustrations=(),
    )


def test_runtime_elements_can_reference_computable_definition() -> None:
    result = StatuteEvaluator().evaluate(
        _statute(),
        struct_from_facts({"representation": {"falsehood": True}}),
    )

    assert result.overall_satisfied is True
    assert result.bindings() == {"deception": True, "harm": True}


def test_runtime_computable_definition_can_fail() -> None:
    result = StatuteEvaluator().evaluate(
        _statute(),
        struct_from_facts({"representation": {"falsehood": False}}),
    )

    assert result.overall_satisfied is False
    assert result.bindings() == {"deception": False, "harm": False}


def test_explainer_uses_computable_definition() -> None:
    trace = DatalogExplainer().explain(
        _statute(),
        {"representation": {"falsehood": True}},
    )

    assert trace.overall_satisfied is True
    assert [element.satisfied for element in trace.elements] == [True, True]


def test_source_level_computable_definition_evaluates() -> None:
    analysis = analyze_source(SOURCE, file="<computed>", run_semantic=False)
    assert not analysis.parse_errors
    statute = analysis.ast.statutes[0]

    result = StatuteEvaluator().evaluate(
        statute,
        struct_from_facts({"representation": {"falsehood": True}}),
    )

    assert result.overall_satisfied is True
    assert result.bindings() == {"deception": True, "harm": True}


def test_source_level_computable_definition_explains() -> None:
    statute = analyze_source(SOURCE, file="<computed>", run_semantic=False).ast.statutes[0]

    trace = DatalogExplainer().explain(statute, {"representation": {"falsehood": True}})

    assert trace.overall_satisfied is True
    assert [element.satisfied for element in trace.elements] == [True, True]


def test_source_level_computable_definition_tooling(tmp_path: Path) -> None:
    statute_path = tmp_path / "computed.yh"
    statute_path.write_text(SOURCE, encoding="utf-8")
    runner = CliRunner()

    lint = runner.invoke(cli, ["lint", "--mode", "executable", str(statute_path)])
    assert lint.exit_code == 0
    assert "opaque-executable-meaning" not in lint.output

    formatted = runner.invoke(cli, ["fmt", str(statute_path)])
    assert formatted.exit_code == 0
    assert "deceptive := facts.representation.falsehood;" in formatted.output

    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"representation": {"falsehood": True}}), encoding="utf-8")
    explained = runner.invoke(cli, ["explain", "--facts", str(facts), str(statute_path)])
    assert explained.exit_code == 0
    assert "Section 1 is satisfied." in explained.output


def test_computable_definition_exports_do_not_assume_string_values() -> None:
    statute = analyze_source(SOURCE, file="<computed>", run_semantic=False).ast

    english = EnglishTranspiler().transpile(statute)
    latex = LaTeXTranspiler().transpile(statute)

    assert "facts's representation's falsehood" in english.output
    assert r"\textit{facts}.representation.falsehood" in latex.output


def test_named_imported_computable_definition_evaluates(tmp_path: Path) -> None:
    helper = tmp_path / "defs.yh"
    helper.write_text(
        """
statute 24 "Shared Definitions" {
  definitions {
    deceptive := facts.representation.falsehood;
  }
  elements {
    actus_reus placeholder := "placeholder";
  }
}
""",
        encoding="utf-8",
    )
    main = tmp_path / "main.yh"
    main.write_text(
        """
import { deceptive } from "defs.yh";

statute 1 "Uses Imported Definition" {
  elements {
    actus_reus deception := deceptive;
  }
}
""",
        encoding="utf-8",
    )

    analysis = analyze_file(main, run_semantic=True)
    assert not analysis.errors
    ast = ModuleResolver(search_paths=[tmp_path]).module_with_imported_definitions(
        analysis.ast,
        main,
    )
    result = StatuteEvaluator().evaluate(
        ast.statutes[0],
        struct_from_facts({"representation": {"falsehood": True}}),
    )

    assert result.overall_satisfied is True
    assert result.bindings() == {"deception": True}


def test_explain_uses_imported_computable_definition(tmp_path: Path) -> None:
    (tmp_path / "defs.yh").write_text(
        """
statute 24 "Shared Definitions" {
  definitions {
    deceptive := facts.representation.falsehood;
  }
  elements {
    actus_reus placeholder := "placeholder";
  }
}
""",
        encoding="utf-8",
    )
    statute = tmp_path / "main.yh"
    statute.write_text(
        """
import { deceptive } from "defs.yh";

statute 1 "Uses Imported Definition" {
  elements {
    actus_reus deception := deceptive;
  }
}
""",
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(
        json.dumps({"representation": {"falsehood": True}}),
        encoding="utf-8",
    )

    explained = CliRunner().invoke(cli, ["explain", "--facts", str(facts), str(statute)])

    assert explained.exit_code == 0
    assert "Section 1 is satisfied." in explained.output
    assert "predicate expression is truthy" in explained.output


def test_local_definition_overrides_imported_definition(tmp_path: Path) -> None:
    (tmp_path / "defs.yh").write_text(
        """
statute 24 "Shared Definitions" {
  definitions {
    deceptive := facts.representation.falsehood;
  }
  elements {
    actus_reus placeholder := "placeholder";
  }
}
""",
        encoding="utf-8",
    )
    statute = tmp_path / "main.yh"
    statute.write_text(
        """
import { deceptive } from "defs.yh";

statute 1 "Local Override" {
  definitions {
    deceptive := FALSE;
  }
  elements {
    actus_reus deception := deceptive;
  }
}
""",
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(
        json.dumps({"representation": {"falsehood": True}}),
        encoding="utf-8",
    )

    explained = CliRunner().invoke(cli, ["explain", "--facts", str(facts), str(statute)])

    assert explained.exit_code == 0
    assert "Section 1 is not satisfied." in explained.output


def test_duplicate_imported_definitions_emit_semantic_warning(tmp_path: Path) -> None:
    for filename, fact_name in (("defs_a.yh", "a"), ("defs_b.yh", "b")):
        (tmp_path / filename).write_text(
            f"""
statute 24 "{filename}" {{
  definitions {{
    shared := facts.{fact_name};
  }}
  elements {{
    actus_reus placeholder := "placeholder";
  }}
}}
""",
            encoding="utf-8",
        )
    main = tmp_path / "main.yh"
    main.write_text(
        """
import { shared } from "defs_a.yh";
import { shared } from "defs_b.yh";

statute 1 "Duplicate Imports" {
  elements {
    actus_reus overlap := shared;
  }
}
""",
        encoding="utf-8",
    )

    analysis = analyze_file(main, run_semantic=True)
    warnings = [
        issue.message for issue in analysis.semantic_summary.issues
        if issue.severity == "warning"
    ]

    assert any("Duplicate imported definition 'shared'" in warning for warning in warnings)


def test_named_import_carries_transitive_definition_dependencies(tmp_path: Path) -> None:
    (tmp_path / "base.yh").write_text(
        """
statute 10 "Base" {
  definitions {
    base := facts.base;
  }
  elements {
    actus_reus placeholder := "placeholder";
  }
}
""",
        encoding="utf-8",
    )
    (tmp_path / "derived.yh").write_text(
        """
import { base } from "base.yh";

statute 11 "Derived" {
  definitions {
    derived := base;
  }
  elements {
    actus_reus placeholder := "placeholder";
  }
}
""",
        encoding="utf-8",
    )
    statute = tmp_path / "main.yh"
    statute.write_text(
        """
import { derived } from "derived.yh";

statute 1 "Transitive Import" {
  elements {
    actus_reus result := derived;
  }
}
""",
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"base": True}), encoding="utf-8")

    explained = CliRunner().invoke(cli, ["explain", "--facts", str(facts), str(statute)])

    assert explained.exit_code == 0
    assert "Section 1 is satisfied." in explained.output
