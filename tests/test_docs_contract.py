"""Documentation contract tests for shipped CLI and DSL surfaces."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from yuho.cli.main import cli
from yuho.services.analysis import analyze_source
from yuho.transpile.json_transpiler import JSONTranspiler


DOC_ROOTS = [
    Path(".github"),
    Path("docs"),
    Path("library"),
]

CONSTRUCT_TERMS = ["legal_test", "conflict_check", "annotation"]

DOC_SYNTAX_FEATURE_SNIPPETS = {
    "types_and_data": """
type MaybeInt = int?;

struct LegalFact {
    string citation,
}

struct Person : LegalFact {
    string name,
    int age,
    money wealth,
    date dob,
    duration sentence,
    [string] tags,
}

enum Fruit { apple, orange, pear }
enum Verdict { guilty(bool), not_guilty }
""",
    "operators_match_and_functions": """
fn classify(int count, bool serious) : string {
    bool threshold := count >= 3 && !FALSE;
    return match {
        case TRUE if threshold && serious := consequence "serious";
        case TRUE if threshold := consequence "ordinary";
        case _ := consequence "none";
    };
}

assert classify(3, TRUE) == "serious";
""",
    "statute_groups_exceptions_case_law_penalties": """
statute 299 "Base" {
    elements { actus_reus death := "death"; }
}

statute 300 "Murder" effective 1872-01-01 effective 2012-12-31 subsumes 299 {
    elements {
        all_of {
            actus_reus death := "death";
            any_of {
                mens_rea intent := "intent";
                mens_rea knowledge := "knowledge";
            }
        }
    }

    exception general_exception {
        "general defence"
        "no conviction"
    }

    exception narrow_exception {
        "narrow defence"
        "no conviction"
        priority 2
        defeats general_exception
    }

    penalty cumulative {
        imprisonment := 1 year .. 7 years;
        fine := $0.00 .. $50,000.00;
    }

    penalty or_both {
        fine := unlimited;
        caning := unspecified;
    }

    caselaw "PP v Tan" "[2026] SGCA 1" {
        "death means biological death"
        element death
    }

    subsection (1) {
        elements { actus_reus act := "act"; }
    }
}
""",
    "cross_section_contracts": """
struct Facts {
    bool death,
    bool intent,
}

/// @input Facts
/// @output bool
statute 1 "Base" {
    elements { actus_reus death := "death"; }
}

fn check(Facts facts) : bool {
    return is_infringed(s1) && apply_scope(s1, facts, { intent := TRUE });
}
""",
    "annotations_tests_conflicts_and_imports": """
import "penal_code/s415_cheating";
import { dishonestly as imported_dishonestly } from "penal_code/s24_definitions";
import * from "penal_code/s415_cheating";
referencing penal_code/s415_cheating

@presumed("innocent")
@amended("2021-06-15", "Criminal Law Reform Act 2021")
statute 200 "Annotated Offence" {
    elements { actus_reus act := "act"; }
}

@precedent("PP v Tan [2020]")
legal_test ValidOffer {
    bool definite,
    bool communicated,
    requires definite && communicated
}

@hierarchy("subsidiary", "S300")
conflict_check S299_vs_S300 {
    source := "s299_culpable_homicide";
    target := "s300_murder";
}
""",
}


def _local_markdown_links(markdown_text: str) -> list[str]:
    """Return local markdown link targets from a markdown document."""
    targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown_text)
    return [
        target
        for target in targets
        if not target.startswith(("http://", "https://", "#", "mailto:"))
    ]


def test_documented_cli_commands_exist() -> None:
    """Every CLI command documented in the reference should be implemented."""
    actual = set(cli.commands.keys())
    reference = Path("docs/user/cli-reference.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"`yuho\s+([a-zA-Z0-9_-]+)", reference))

    assert documented
    assert documented.issubset(actual), sorted(documented - actual)


def test_dsl_docs_cover_new_constructs() -> None:
    """Syntax and semantics docs should mention the shipped advanced constructs."""
    syntax = Path("docs/researcher/syntax.md").read_text(encoding="utf-8")
    semantics = Path("docs/researcher/formal-semantics.md").read_text(encoding="utf-8")

    for term in CONSTRUCT_TERMS:
        assert term in syntax
        assert term in semantics


def test_local_markdown_links_resolve() -> None:
    """All non-README local markdown links in docs should resolve."""
    missing: list[tuple[str, str]] = []

    for root in DOC_ROOTS:
        for md_path in root.rglob("*.md"):
            content = md_path.read_text(encoding="utf-8", errors="ignore")
            for target in _local_markdown_links(content):
                clean_target = target.split("#", 1)[0]
                if not clean_target:
                    continue
                resolved = (md_path.parent / clean_target).resolve()
                if not resolved.exists():
                    missing.append((str(md_path), target))

    assert not missing, missing


def test_positioning_docs_are_linked() -> None:
    """Public honesty docs should stay discoverable."""
    readme = Path("README.md").read_text(encoding="utf-8")
    index = Path("docs/INDEX.md").read_text(encoding="utf-8")

    assert "docs/positioning/status-matrix.md" in readme
    assert "docs/researcher/canonical-semantics.md" in readme
    assert "researcher/canonical-semantics.md" in index
    assert "positioning/status-matrix.md" in index
    assert "positioning/comparisons.md" in index
    assert "contributor/expert-review-checklist.md" in index
    assert "faithful executable law" not in readme.lower()


def test_mechanisation_readme_states_claim_boundary() -> None:
    """Lean mechanisation docs should separate proof evidence from trust boundaries."""
    readme = Path("mechanisation/README.md").read_text(encoding="utf-8")

    for term in ("Proved", "Tested", "Trusted", "Out of scope"):
        assert f"| {term} |" in readme


def test_generic_docs_do_not_overstate_type_support() -> None:
    """Generic syntax docs should match the current erased implementation."""
    syntax = Path("docs/researcher/syntax.md").read_text(encoding="utf-8").lower()
    semantics = Path("docs/researcher/formal-semantics.md").read_text(encoding="utf-8").lower()

    assert "surface-only" in syntax
    assert "does not yet substitute" in syntax
    assert "runtime and export layers may erase" in syntax
    assert "generic type syntax is represented in the ast" in semantics
    assert "not fully" in semantics
    assert "erase or simplify type arguments" in semantics
    assert "strongly, statically-typed" not in syntax


def test_boolean_literal_docs_match_parser_spelling() -> None:
    """The parser accepts uppercase TRUE/FALSE boolean literals."""
    syntax = Path("docs/researcher/syntax.md").read_text(encoding="utf-8")
    semantics = Path("docs/researcher/formal-semantics.md").read_text(encoding="utf-8")

    assert "bool — TRUE or FALSE" in syntax
    assert "| TRUE | FALSE" in semantics


@pytest.mark.parametrize("feature, source", sorted(DOC_SYNTAX_FEATURE_SNIPPETS.items()))
def test_documented_syntax_feature_snippets_parse_and_transpile(
    feature: str,
    source: str,
) -> None:
    """Representative syntax-doc features should parse and survive JSON export."""
    result = analyze_source(source, file=f"<docs:{feature}>", run_semantic=False)

    assert not result.parse_errors, [str(e) for e in result.parse_errors]
    assert result.ast is not None
    JSONTranspiler(include_locations=False).transpile(result.ast)
