import json
from pathlib import Path

from click.testing import CliRunner

from yuho.ast import nodes
from yuho.ast.builder import ASTBuilder
from yuho.chronology import build_world, validate_world
from yuho.chronology.renderers import render_diff, render_world, world_to_dict
from yuho.cli import cli
from yuho.parser import Parser
from yuho.services.analysis import analyze_source
from yuho.transpile import JSONTranspiler


def parse(source: str) -> nodes.ModuleNode:
    result = Parser().parse(source)
    assert result.is_valid, [str(error) for error in result.errors]
    return ASTBuilder(source).build(result.tree.root_node)


CHRONO_SOURCE = """
source trial_transcript: transcript {
    citation := "Tr. 42";
}

source_bundle bundle_a {
    sources := [trial_transcript];
}

locator tr_42 {
    source_ref := trial_transcript;
    page := 42;
}

ruleset federal_rules {
    jurisdiction := federal;
    procedure := civil;
    source_ref := trial_transcript;
}

deadline_rule response_deadline {
    ruleset := federal_rules;
    rule := "response";
    jurisdiction := federal;
    source_ref := trial_transcript;
    authority := "Rule 12";
    trigger := service;
    offset := 21 days;
}

issue liability {
    summary := "liability issue";
}

issue_element breach_element {
    issue_ref := liability;
    entity_ref := admission_claim;
}

timeline main_case {
    start := 2024-01-01;
    end := 2024-12-31;
    jurisdiction := federal;
    procedure := civil;
}

entity transcript_excerpt: evidence {
    source_ref := trial_transcript;
    locator_ref := tr_42;
    citation := "Tr. 42:1";
    appears_on := main_case @ 2024-01-01..2024-01-31;
}

entity admission_claim: claim {
    source_ref := trial_transcript;
    citation := "Tr. 42:1";
    appears_on := main_case @ 2024-01-31..2024-01-31;
}

reltype supports {
    source := evidence;
    target := claim;
}

rel transcript_excerpt -["supports"]-> admission_claim @ 2024-01-01..2024-01-31;

scenario "alternate" from main_case {
    entity alternate_fact: fact {
        source_ref := trial_transcript;
        citation := "Tr. 99";
        appears_on := main_case @ 2024-02-01..2024-02-01;
    }
}

view trial_view {
    narrative := trial;
}

constraint "order" {
    rel transcript_excerpt --> admission_claim;
}
"""


def test_parser_ast_for_chronology_declarations_and_expressions() -> None:
    module = parse(CHRONO_SOURCE)
    assert module.sources[0].name == "trial_transcript"
    assert module.sources[0].kind == "transcript"
    assert len(module.source_bundles) == 1
    assert isinstance(module.source_bundles[0].fields[0].value, nodes.ListExprNode)
    assert len(module.locators) == 1
    assert len(module.rulesets) == 1
    assert len(module.deadline_rules) == 1
    assert len(module.issues) == 1
    assert len(module.issue_elements) == 1
    assert len(module.timelines) == 1
    assert isinstance(module.entities[0].fields[-1].value, nodes.TimelineAppearanceNode)
    assert module.relationships[0].label == "supports"
    assert isinstance(module.relationships[0].temporal_scope, nodes.RangeExprNode)
    assert module.scenarios[0].body[0].name == "alternate_fact"
    assert module.views[0].name == "trial_view"
    assert module.constraints[0].name == "order"


def test_world_validation_refs_bounds_relationships_and_warnings() -> None:
    source = """
timeline t { start := 2024-01-01; end := 2024-01-31; }
source s: record { citation := "A"; }
locator loc { source_ref := missing_source; }
entity orphan_claim: claim { appears_on := missing_t @ 2024-02-01..2024-02-02; }
entity bad_evidence: evidence { citation := "A"; appears_on := t @ 2023-12-31..2024-02-01; }
entity witness_a: witness { appears_on := t @ 2024-01-10..2024-01-10; }
rel bad_evidence -["impeaches"]-> orphan_claim;
rel orphan_claim -["contradicts"]-> witness_a;
rel bad_evidence -["contradicts"]-> witness_a;
"""
    diagnostics = validate_world(build_world(parse(source)))
    messages = [diagnostic.message for diagnostic in diagnostics]
    assert any("Unknown source_ref 'missing_source'" in message for message in messages)
    assert any("Unknown timeline 'missing_t'" in message for message in messages)
    assert any("appears before timeline start" in message for message in messages)
    assert any("appears after timeline end" in message for message in messages)
    assert any("missing source or source_ref" in message for message in messages)
    assert any("target should be ['witness']" in message for message in messages)
    assert any("Claim 'orphan_claim' has no source backing" in message for message in messages)
    assert any("Contradiction:" in message for message in messages)
    assert any("Witness 'witness_a' has no matching deposition" in message for message in messages)


def test_existing_check_path_runs_chronology_validation() -> None:
    source = """
timeline t { start := 2024-01-31; end := 2024-01-01; }
"""
    result = analyze_source(source, run_semantic=True)
    payload = result.validation_payload()
    assert not payload["valid"]
    assert any("Chronology: Timeline 't' start is after end" in item["message"] for item in payload["errors"])


def test_exports_json_markdown_mermaid_svg_html_and_diff() -> None:
    source = """
source s: record { citation := "A"; }
timeline t { start := 2024-01-01; end := 2024-01-31; }
entity evidence_a: evidence { source_ref := s; citation := "A1"; appears_on := t @ 2024-01-01..2024-01-02; }
entity claim_a: claim { source_ref := s; citation := "A2"; appears_on := t @ 2024-01-03..2024-01-03; }
rel evidence_a -["cites"]-> claim_a;
rel evidence_a -["contradicts"]-> claim_a;
"""
    world = build_world(parse(source))
    assert "evidence_a" in render_world(world, "json")
    assert "## Entities" in render_world(world, "markdown")
    assert "gantt" in render_world(world, "mermaid")
    assert "#c1121f" in render_world(world, "svg")
    assert "<html>" in render_world(world, "html")

    right = build_world(parse(source + '\nentity extra_fact: fact { source_ref := s; citation := "A3"; }\n'))
    assert "+ entities.extra_fact" in render_diff(world, right, "text")


def test_json_transpiler_serializes_chronology_ast() -> None:
    module = parse(CHRONO_SOURCE)
    payload = json.loads(JSONTranspiler(include_locations=False).transpile(module))
    assert payload["sources"][0]["name"] == "trial_transcript"
    assert payload["entities"][0]["type_name"] == "evidence"
    assert payload["relationships"][0]["label"] == "supports"


def test_chronology_cli_check_export_reports_and_import(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.yh"
    source_path.write_text(
        """
source s: record { citation := "A"; }
timeline t { start := 2024-01-01; end := 2024-01-31; }
entity e: evidence { source_ref := s; citation := "A1"; appears_on := t @ 2024-01-01..2024-01-02; }
entity c: claim { source_ref := s; citation := "A2"; appears_on := t @ 2024-01-03..2024-01-03; }
entity x: exhibit { number := "X1"; description := "register"; source_ref := s; }
rel e -["cites"]-> c;
""",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["chronology", "check", str(source_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["valid"] is True

    result = runner.invoke(cli, ["chronology", "export", str(source_path), "-t", "mermaid"])
    assert result.exit_code == 0, result.output
    assert "gantt" in result.output

    result = runner.invoke(cli, ["chronology", "sources", str(source_path)])
    assert result.exit_code == 0
    assert "Sources" in result.output

    result = runner.invoke(cli, ["chronology", "exhibits", str(source_path)])
    assert result.exit_code == 0
    assert "X1" in result.output

    csv_path = tmp_path / "import.csv"
    csv_path.write_text(
        "declaration,name,type,summary,source_ref,citation,timeline,start,end\n"
        "entity,imported_fact,fact,imported,s,A3,t,2024-01-04,2024-01-04\n",
        encoding="utf-8",
    )
    result = runner.invoke(cli, ["chronology", "import", str(csv_path), "--from", "csv"])
    assert result.exit_code == 0
    assert "entity imported_fact: fact" in result.output


def test_parity_validation_deadlines_reltypes_continuous_recurrence_and_state() -> None:
    source = """
source s: record { citation := "A"; url := "not-a-url"; }
source_bundle b { sources := [s, s]; }
locator loc { source_ref := s; }
ruleset rs { jurisdiction := federal; procedure := civil; source_ref := s; }
deadline_rule dr { ruleset := rs; rule := "R"; trigger := service; offset := 0 days; source_ref := s; direction := sideways; }
timeline parent { start := 2024-01-01; end := 2024-01-31; jurisdiction := federal; procedure := civil; }
timeline child { kind := branch; parent := parent; start := 2024-01-01; end := 2024-01-31; jurisdiction := state; loop_count := 0; }
entity e: evidence { citation := "A"; source := "paper"; appears_on := parent @ 2024-01-01..2024-01-01; }
entity f: fact { source_ref := s; citation := "B"; continuous := TRUE; recurrence := 0 days; skip := ["bad"]; state := [{ at := "bad", status := "filed" }]; appears_on := parent @ 2024-01-01..2024-01-02; }
entity g: fact { source_ref := s; citation := "C"; appears_on := parent @ 2024-01-10..2024-01-10; }
reltype supports { source := evidence; target := fact; required := TRUE; min_inbound := 2; max_inbound := 1; temporal := before; }
rel e -["supports"]-> f @ 2024-01-02..2024-01-01;
entity d: deadline { rule := dr; rule_ref := dr; jurisdiction := state; trigger := 2024-01-10; due := 2024-01-09; source_ref := s; appears_on := parent @ 2024-01-09..2024-01-09; }
"""
    diagnostics = validate_world(build_world(parse(source)))
    messages = [diagnostic.message for diagnostic in diagnostics]
    assert any("invalid url" in message for message in messages)
    assert any("Duplicate source 's' in bundle" in message for message in messages)
    assert any("no concrete locator field" in message for message in messages)
    assert any("offset must be positive" in message for message in messages)
    assert any("invalid direction" in message for message in messages)
    assert any("jurisdiction differs" in message for message in messages)
    assert any("loop_count must be positive" in message for message in messages)
    assert any("temporal scope starts after it ends" in message for message in messages)
    assert any("min_inbound exceeds max_inbound" in message for message in messages)
    assert any("recurrence must be a positive duration" in message for message in messages)
    assert any("skip values must be dates" in message for message in messages)
    assert any("state at must be a time point" in message for message in messages)
    assert any("due before its trigger" in message for message in messages)


def test_struct_schema_inheritance_and_constraints() -> None:
    source = """
struct LegalFact {
    string citation,
}
struct ProvenFact : LegalFact {
    source source_ref,
    string status,
}
source s: record { citation := "A"; }
timeline t { start := 2024-01-01; end := 2024-01-31; }
entity e: evidence { citation := "E"; source_ref := s; appears_on := t @ 2024-01-01..2024-01-01; }
entity f: ProvenFact { citation := "F"; source_ref := s; status := "filed"; state := [{ at := 2024-01-02, status := "served" }]; appears_on := t @ 2024-01-02..2024-01-02; }
rel e -["cites"]-> f;
constraint "facts are supported" {
    assert type_of(f) == "ProvenFact", "schema type";
    assert has_inbound(f, "cites"), "cites edge";
    assert before(e, f), "temporal";
    assert field_at(f, "status", 2024-01-03) == "served", "state";
    len(inbound(f, "cites")) == 1;
}
"""
    diagnostics = validate_world(build_world(parse(source)))
    assert [diag.message for diag in diagnostics if diag.severity == "error"] == []


def test_cli_scenario_commands_and_exhibit_formats(tmp_path: Path) -> None:
    source_path = tmp_path / "scenario.yh"
    source_path.write_text(
        """
source s: record { citation := "A"; }
timeline t { start := 2024-01-01; end := 2024-01-31; }
entity e: evidence { source_ref := s; citation := "A1"; appears_on := t @ 2024-01-01..2024-01-01; }
entity c: claim { source_ref := s; citation := "A2"; appears_on := t @ 2024-01-02..2024-01-02; }
entity x: exhibit { number := "X1"; description := "register"; source_ref := s; appears_on := t @ 2024-01-03..2024-01-03; }
rel e -["cites"]-> c;
scenario "alt" from t {
    entity alt_fact: fact { source_ref := s; citation := "A3"; appears_on := t @ 2024-01-04..2024-01-04; }
}
""",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["chronology", "scenario-report", str(source_path)])
    assert result.exit_code == 0, result.output
    assert "alt" in result.output
    result = runner.invoke(cli, ["chronology", "scenario-diff", str(source_path), "alt"])
    assert result.exit_code == 0, result.output
    assert "+ entities.alt_fact" in result.output
    result = runner.invoke(cli, ["chronology", "exhibits", str(source_path), "--format", "csv"])
    assert result.exit_code == 0, result.output
    assert "number,entity,description" in result.output
    result = runner.invoke(cli, ["chronology", "exhibits", str(source_path), "--format", "json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)[0]["number"] == "X1"


def test_relationship_csv_and_jsonld_imports(tmp_path: Path) -> None:
    csv_path = tmp_path / "rels.csv"
    csv_path.write_text(
        "declaration,name,type,summary,source_ref,citation,timeline,start,end,source,target,label\n"
        "entity,a,fact,A,s,A1,t,2024-01-01,2024-01-01,,,\n"
        "entity,b,claim,B,s,A2,t,2024-01-02,2024-01-02,,,\n"
        "relationship,,,,,,,,,a,b,cites\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["chronology", "import", str(csv_path), "--from", "csv"])
    assert result.exit_code == 0, result.output
    assert "timeline t" in result.output
    assert 'rel a -["cites"]-> b;' in result.output

    jsonld_path = tmp_path / "graph.jsonld"
    jsonld_path.write_text(
        json.dumps(
            {
                "@graph": [
                    {"@id": "a", "@type": "Fact", "name": "A", "supports": {"@id": "b"}},
                    {"@id": "b", "@type": "Claim", "name": "B"},
                ]
            }
        ),
        encoding="utf-8",
    )
    result = runner.invoke(cli, ["chronology", "import", str(jsonld_path), "--from", "jsonld"])
    assert result.exit_code == 0, result.output
    assert 'rel a -["supports"]-> b;' in result.output
