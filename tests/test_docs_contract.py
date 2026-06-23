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
    "comments_variables_literals": """
// single-line comment
/*
multi-line comment
*/
int count := 200;
float ratio := 400.00;
string label := "example";
bool flag := TRUE;
money amount := $10.56;
percent share := 25%;
date started := 2020-01-12;
duration term := 2 years, 6 months;
int? maybe_count := pass;

/// doc comment
statute 900 "Comment Host" {
    elements {
        actus_reus act := "act";
        mens_rea intent := "intent";
    }
    penalty { fine := $0.00 .. $1.00; }
}
""",
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
    elements { actus_reus death := "death" burden prosecution beyond_reasonable_doubt; }
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

    /// @role ratio
    /// @jurisdiction singapore
    /// @court_level apex
    /// @date 2026-01-01
    /// @effect requires active_misleading
    caselaw "PP v Tan" "[2026] SGCA 1" {
        "death means biological death"
        element death
    }

    caselaw "Appeal v Tan" "[2026] SGCA 2" {
        "earlier holding distinguished"
        element death
        treatment distinguished "PP v Tan" "[2026] SGCA 1"
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
    "testing_and_ambiguity": """
fn add(int a, int b) : int {
    return a + b;
}

assert add(1, 2) == 3;
assert add(3, 4) == 7, "expected arithmetic";

fn evaluate_strict(string deception_type, bool causes_damage_harm) : string {
    return match {
        case TRUE if deception_type == "active" && causes_damage_harm := consequence "said to cheat";
        case _ := consequence "not said to cheat";
    };
}

fn evaluate_liberal(string deception_type, bool causes_damage_harm) : string {
    return match {
        case TRUE if deception_type != "none" && causes_damage_harm := consequence "said to cheat";
        case _ := consequence "not said to cheat";
    };
}

assert evaluate_strict("passive", TRUE) == "not said to cheat";
assert evaluate_liberal("passive", TRUE) == "said to cheat";
""",
}

SYNTAX_HEADING_CONTRACTS = {
    "Comments": "comments_variables_literals",
    "Variable Declaration": "comments_variables_literals",
    "Types": "comments_variables_literals",
    "Data Structures": "types_and_data",
    "Operators": "operators_match_and_functions",
    "Control Structures": "operators_match_and_functions",
    "Functions": "operators_match_and_functions",
    "Statute Blocks": "statute_groups_exceptions_case_law_penalties",
    "Element Groups (AND/OR relationships)": "statute_groups_exceptions_case_law_penalties",
    "Exception Blocks": "statute_groups_exceptions_case_law_penalties",
    "Case Law Blocks": "statute_groups_exceptions_case_law_penalties",
    "Extended Penalty": "statute_groups_exceptions_case_law_penalties",
    "Penalty combinators (`cumulative` / `alternative` / `or_both`)": "statute_groups_exceptions_case_law_penalties",
    "Exception priority + `defeats`": "statute_groups_exceptions_case_law_penalties",
    "Effective dates, amends, subsumes": "statute_groups_exceptions_case_law_penalties",
    "Subsections": "statute_groups_exceptions_case_law_penalties",
    "Cross-section predicates: `is_infringed` and `apply_scope`": "cross_section_contracts",
    "Annotations": "annotations_tests_conflicts_and_imports",
    "Legal Tests": "annotations_tests_conflicts_and_imports",
    "Conflict Checks": "annotations_tests_conflicts_and_imports",
    "Imports": "annotations_tests_conflicts_and_imports",
    "Testing": "testing_and_ambiguity",
    "Modelling Ambiguity": "testing_and_ambiguity",
    "Doc comments for competing interpretations": "testing_and_ambiguity",
    "Separate evaluation functions for alternative interpretations": "testing_and_ambiguity",
    "Cross-referencing statutes": "annotations_tests_conflicts_and_imports",
}

NON_FEATURE_SYNTAX_HEADINGS = {"Table Of Contents", "Introduction"}


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


def test_formal_semantics_caselaw_contract_matches_runtime_metadata() -> None:
    """Case-law formal syntax should cover executable metadata and treatments."""
    semantics = Path("docs/researcher/formal-semantics.md").read_text(encoding="utf-8")

    for term in (
        "CaseTreatment ::= 'treatment' TreatmentKind StringLit StringLit?",
        "EffectOp    ::= 'requires' | 'satisfies' | 'excludes'",
        "| 'overrules' | 'overruled'",
        "Sat_case(requires f, e, F)",
    ):
        assert term in semantics


def test_documented_syntax_headings_have_executable_contracts() -> None:
    """Each syntax-reference feature heading should map to an executable sample."""
    syntax = Path("docs/researcher/syntax.md").read_text(encoding="utf-8")
    headings = {
        match.group(1).strip()
        for match in re.finditer(r"^#{2,3}\s+(.+)$", syntax, re.MULTILINE)
    }
    feature_headings = headings - NON_FEATURE_SYNTAX_HEADINGS

    assert feature_headings == set(SYNTAX_HEADING_CONTRACTS)
    assert set(SYNTAX_HEADING_CONTRACTS.values()).issubset(DOC_SYNTAX_FEATURE_SNIPPETS)


@pytest.mark.parametrize("feature, source", sorted(DOC_SYNTAX_FEATURE_SNIPPETS.items()))
def test_documented_syntax_feature_snippets_analyze_and_transpile(
    feature: str,
    source: str,
) -> None:
    """Representative syntax-doc features should pass parser, semantic, lint, and JSON export phases."""
    result = analyze_source(source, file=f"<docs:{feature}>", run_semantic=True)

    assert not result.parse_errors, [str(e) for e in result.parse_errors]
    assert result.semantic_valid is True, result.diagnostics()
    assert result.lint_checked is True
    assert result.ast is not None
    JSONTranspiler(include_locations=False).transpile(result.ast)
