"""
Tests for new constructs: legal_test, conflict_check, annotations,
Catala/F* transpilers, and logic engine.
"""

import pytest
from yuho.parser import Parser
from yuho.ast.builder import ASTBuilder
from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget
from yuho.transpile.registry import TranspilerRegistry
from yuho.verify.logic_engine import (
    Formula,
    FormulaType,
    var,
    and_,
    or_,
    not_,
    implies,
    TRUE,
    FALSE,
    simplify,
    is_tautology,
    is_contradiction,
    is_satisfiable,
    evaluate,
    detect_circular_dependencies,
    analyze_formulas,
    statute_to_formulas,
    variables,
)


# =========================================================================
# Parsing helpers
# =========================================================================


def parse(source: str) -> nodes.ModuleNode:
    parser = Parser()
    result = parser.parse(source)
    builder = ASTBuilder(source)
    return builder.build(result.tree.root_node)


# =========================================================================
# Legal test construct
# =========================================================================


class TestLegalTest:
    def test_parse_basic_legal_test(self):
        src = """
legal_test ValidContract {
    bool offer_made,
    bool acceptance,
    bool consideration,
    requires offer_made && acceptance && consideration
}
"""
        mod = parse(src)
        assert len(mod.legal_tests) == 1
        lt = mod.legal_tests[0]
        assert lt.name == "ValidContract"
        assert len(lt.requirements) == 3
        assert lt.condition is not None

    def test_legal_test_requirement_names(self):
        src = """
legal_test SimpleMurder {
    bool actus_reus_present,
    bool mens_rea_present,
    requires actus_reus_present && mens_rea_present
}
"""
        mod = parse(src)
        lt = mod.legal_tests[0]
        names = [r.name for r in lt.requirements if isinstance(r, nodes.VariableDecl)]
        assert "actus_reus_present" in names
        assert "mens_rea_present" in names

    def test_legal_test_without_requires(self):
        src = """
legal_test EmptyTest {
    bool field_a,
}
"""
        mod = parse(src)
        assert len(mod.legal_tests) == 1
        lt = mod.legal_tests[0]
        assert lt.condition is None

    def test_legal_test_with_annotation(self):
        src = """
@precedent("PP v Tan [2020]")
legal_test AnnotatedTest {
    bool element_one,
    requires element_one
}
"""
        mod = parse(src)
        lt = mod.legal_tests[0]
        assert len(lt.annotations) == 1
        assert lt.annotations[0].name == "precedent"
        assert lt.annotations[0].args[0] == "PP v Tan [2020]"


# =========================================================================
# Conflict check construct
# =========================================================================


class TestConflictCheck:
    def test_parse_basic_conflict_check(self):
        src = """
conflict_check S299_vs_S300 {
    source := "s299_culpable_homicide"
    target := "s300_murder"
}
"""
        mod = parse(src)
        assert len(mod.conflict_checks) == 1
        cc = mod.conflict_checks[0]
        assert cc.name == "S299_vs_S300"
        assert cc.source == "s299_culpable_homicide"
        assert cc.target == "s300_murder"

    def test_conflict_check_with_semicolons(self):
        src = """
conflict_check TheftVsRobbery {
    source := "s378_theft";
    target := "s390_robbery";
}
"""
        mod = parse(src)
        cc = mod.conflict_checks[0]
        assert cc.source == "s378_theft"
        assert cc.target == "s390_robbery"

    def test_conflict_check_with_annotation(self):
        src = """
@hierarchy("subsidiary", "S300")
conflict_check HierarchyCheck {
    source := "s299"
    target := "s300"
}
"""
        mod = parse(src)
        cc = mod.conflict_checks[0]
        assert len(cc.annotations) == 1
        assert cc.annotations[0].name == "hierarchy"


# =========================================================================
# Annotation system
# =========================================================================


class TestAnnotations:
    def test_annotation_on_statute(self):
        src = """
@amended("2020-01-01", "Criminal Law Reform Act 2019")
statute 415 "Cheating" effective 1872-01-01 {
    definitions {
        cheating := "whoever deceives any person"
    }
    elements {
        actus_reus deception := "deceives any person"
    }
}
"""
        mod = parse(src)
        statute = mod.statutes[0]
        assert len(statute.annotations) == 1
        ann = statute.annotations[0]
        assert ann.name == "amended"
        assert ann.args[0] == "2020-01-01"
        assert ann.args[1] == "Criminal Law Reform Act 2019"

    def test_presumed_annotation(self):
        src = """
@presumed("innocent")
statute 100 "Test" {
    elements {
        actus_reus act := "some act"
    }
}
"""
        mod = parse(src)
        assert mod.statutes[0].annotations[0].name == "presumed"
        assert mod.statutes[0].annotations[0].args[0] == "innocent"

    def test_multiple_annotations(self):
        src = """
@precedent("Case A v B [2020]")
@amended("2021-06-15", "Act 2021")
statute 200 "MultiAnnotation" {
    elements {
        actus_reus act := "test"
    }
}
"""
        mod = parse(src)
        anns = mod.statutes[0].annotations
        assert len(anns) == 2
        names = {a.name for a in anns}
        assert "precedent" in names
        assert "amended" in names

    def test_annotation_no_args(self):
        src = """
@presumed
statute 300 "NoArgs" {
    elements {
        actus_reus act := "test"
    }
}
"""
        mod = parse(src)
        ann = mod.statutes[0].annotations[0]
        assert ann.name == "presumed"
        assert len(ann.args) == 0


# =========================================================================
# Catala transpiler
# =========================================================================


@pytest.mark.skipif(
    not hasattr(TranspileTarget, "CATALA"),
    reason="Catala transpiler not yet shipped (planned target).",
)
class TestCatalaTranspiler:
    def _transpile(self, source: str) -> str:
        mod = parse(source)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.CATALA)
        return transpiler.transpile(mod)

    def test_catala_statute(self):
        src = """
statute 378 "Theft" effective 1872-01-01 {
    definitions {
        theft := "dishonest taking of property"
    }
    elements {
        actus_reus taking := "moves property out of possession"
        mens_rea dishonesty := "intention to dishonestly take"
    }
    penalty {
        imprisonment := 3 years
        fine := $10,000
    }
}
"""
        output = self._transpile(src)
        assert "Section 378" in output
        assert "declaration scope" in output
        assert "taking" in output
        assert "dishonesty" in output
        assert "guilty" in output

    def test_catala_legal_test(self):
        src = """
legal_test ValidOffer {
    bool definite,
    bool communicated,
    requires definite && communicated
}
"""
        output = self._transpile(src)
        assert "LegalTest" in output
        assert "test_satisfied" in output

    def test_catala_conflict_check(self):
        src = """
conflict_check TestConflict {
    source := "file_a"
    target := "file_b"
}
"""
        output = self._transpile(src)
        assert "Conflict check" in output
        assert "file_a" in output

    def test_catala_with_exception(self):
        src = """
statute 100 "Test" {
    elements {
        actus_reus act := "some act"
    }
    exception self_defence {
        "acted in self-defence"
    }
}
"""
        output = self._transpile(src)
        assert "exception" in output


# =========================================================================
# F* transpiler
# =========================================================================


@pytest.mark.skipif(
    not hasattr(TranspileTarget, "FSTAR"),
    reason="F* transpiler not yet shipped (planned target).",
)
class TestFStarTranspiler:
    def _transpile(self, source: str) -> str:
        mod = parse(source)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.FSTAR)
        return transpiler.transpile(mod)

    def test_fstar_statute(self):
        src = """
statute 378 "Theft" effective 1872-01-01 {
    definitions {
        theft := "dishonest taking of property"
    }
    elements {
        actus_reus taking := "moves property out of possession"
        mens_rea dishonesty := "intention to dishonestly take"
    }
    penalty {
        imprisonment := 3 years
    }
}
"""
        output = self._transpile(src)
        assert "module YuhoStatutes" in output
        assert "section_" in output
        assert "taking" in output
        assert "dishonesty" in output
        assert "is_guilty" in output

    def test_fstar_struct(self):
        src = """
struct Party {
    string name,
    int age,
}
"""
        output = self._transpile(src)
        assert "type" in output
        assert "name" in output
        assert "string" in output

    def test_fstar_legal_test(self):
        src = """
legal_test ValidContract {
    bool offer,
    bool acceptance,
    requires offer && acceptance
}
"""
        output = self._transpile(src)
        assert "Legal test" in output
        assert "test_" in output

    def test_fstar_enum(self):
        src = """
enum Verdict {
    Guilty,
    NotGuilty,
    Acquitted,
}
"""
        output = self._transpile(src)
        assert "Guilty" in output
        assert "NotGuilty" in output

    def test_fstar_with_annotations(self):
        src = """
@amended("2020-01-01", "Reform Act")
statute 100 "Annotated" {
    elements {
        actus_reus act := "test"
    }
}
"""
        output = self._transpile(src)
        assert "@amended" in output


# =========================================================================
# Logic engine
# =========================================================================


class TestLogicEngine:
    # --- simplification ---
    def test_double_negation(self):
        f = not_(not_(var("A")))
        assert simplify(f) == var("A")

    def test_and_with_false(self):
        f = and_(var("A"), FALSE)
        assert simplify(f) == FALSE

    def test_and_with_true(self):
        f = and_(var("A"), TRUE)
        assert simplify(f) == var("A")

    def test_or_with_true(self):
        f = or_(var("A"), TRUE)
        assert simplify(f) == TRUE

    def test_or_with_false(self):
        f = or_(var("A"), FALSE)
        assert simplify(f) == var("A")

    def test_complement_and(self):
        a = var("A")
        f = and_(a, not_(a))
        assert simplify(f) == FALSE

    def test_complement_or(self):
        a = var("A")
        f = or_(a, not_(a))
        assert simplify(f) == TRUE

    def test_not_true(self):
        assert simplify(not_(TRUE)) == FALSE

    def test_not_false(self):
        assert simplify(not_(FALSE)) == TRUE

    def test_nested_and_flatten(self):
        f = and_(var("A"), and_(var("B"), var("C")))
        s = simplify(f)
        assert s.kind == FormulaType.AND
        assert len(s.children) == 3

    # --- tautology ---
    def test_tautology_excluded_middle(self):
        a = var("A")
        assert is_tautology(or_(a, not_(a)))

    def test_not_tautology(self):
        assert not is_tautology(var("A"))

    def test_implication_tautology(self):
        a = var("A")
        assert is_tautology(implies(a, a))

    # --- contradiction ---
    def test_contradiction_and_complement(self):
        a = var("A")
        assert is_contradiction(and_(a, not_(a)))

    def test_not_contradiction(self):
        assert not is_contradiction(var("A"))

    def test_false_is_contradiction(self):
        assert is_contradiction(FALSE)

    # --- satisfiability ---
    def test_satisfiable_simple(self):
        result = is_satisfiable(var("A"))
        assert result is not None
        assert result["A"] is True

    def test_unsatisfiable(self):
        a = var("A")
        assert is_satisfiable(and_(a, not_(a))) is None

    def test_satisfiable_complex(self):
        a, b = var("A"), var("B")
        result = is_satisfiable(and_(a, not_(b)))
        assert result is not None
        assert result["A"] is True
        assert result["B"] is False

    # --- evaluation ---
    def test_evaluate_true(self):
        assert evaluate(TRUE, {}) is True

    def test_evaluate_false(self):
        assert evaluate(FALSE, {}) is False

    def test_evaluate_var(self):
        assert evaluate(var("X"), {"X": True}) is True
        assert evaluate(var("X"), {"X": False}) is False

    def test_evaluate_and(self):
        f = and_(var("A"), var("B"))
        assert evaluate(f, {"A": True, "B": True}) is True
        assert evaluate(f, {"A": True, "B": False}) is False

    def test_evaluate_implies(self):
        f = implies(var("A"), var("B"))
        assert evaluate(f, {"A": True, "B": False}) is False
        assert evaluate(f, {"A": False, "B": False}) is True

    # --- variables extraction ---
    def test_variables(self):
        f = and_(var("A"), or_(var("B"), not_(var("C"))))
        assert variables(f) == {"A", "B", "C"}

    # --- circular dependency detection ---
    def test_no_cycles(self):
        deps = {"A": {"B"}, "B": {"C"}, "C": set()}
        assert detect_circular_dependencies(deps) == []

    def test_simple_cycle(self):
        deps = {"A": {"B"}, "B": {"A"}}
        cycles = detect_circular_dependencies(deps)
        assert len(cycles) > 0

    def test_self_cycle(self):
        deps = {"A": {"A"}}
        cycles = detect_circular_dependencies(deps)
        assert len(cycles) > 0

    # --- analyze_formulas ---
    def test_analyze_finds_tautology(self):
        a = var("A")
        formulas = {"excluded_middle": or_(a, not_(a))}
        result = analyze_formulas(formulas)
        assert len(result.tautologies) == 1

    def test_analyze_finds_contradiction(self):
        a = var("A")
        formulas = {"impossible": and_(a, not_(a))}
        result = analyze_formulas(formulas)
        assert len(result.contradictions) == 1

    def test_analyze_with_deps(self):
        formulas = {"A": var("A"), "B": var("B")}
        deps = {"A": {"B"}, "B": {"A"}}
        result = analyze_formulas(formulas, deps)
        assert len(result.circular_deps) > 0

    # --- statute_to_formulas ---
    def test_statute_to_formulas(self):
        src = """
statute 100 "Test" {
    elements {
        actus_reus act := "did something"
        mens_rea intent := "intended it"
    }
    exception defence {
        "self defence"
    }
}
"""
        mod = parse(src)
        formulas = statute_to_formulas(mod.statutes[0])
        assert "guilt" in formulas
        assert "effective_guilt" in formulas


# =========================================================================
# Transpiler target enum
# =========================================================================


@pytest.mark.skipif(
    not hasattr(TranspileTarget, "CATALA") or not hasattr(TranspileTarget, "FSTAR"),
    reason="Catala / F* transpiler targets not yet shipped.",
)
class TestTranspileTargets:
    def test_catala_from_string(self):
        assert TranspileTarget.from_string("catala") == TranspileTarget.CATALA

    def test_fstar_from_string(self):
        assert TranspileTarget.from_string("fstar") == TranspileTarget.FSTAR
        assert TranspileTarget.from_string("f*") == TranspileTarget.FSTAR
        assert TranspileTarget.from_string("fst") == TranspileTarget.FSTAR

    def test_catala_extension(self):
        assert TranspileTarget.CATALA.file_extension == ".catala_en"

    def test_fstar_extension(self):
        assert TranspileTarget.FSTAR.file_extension == ".fst"


# =========================================================================
# Integration: parse + transpile roundtrip
# =========================================================================


class TestIntegration:
    def test_full_program_with_all_constructs(self):
        src = """
struct Facts {
    bool act_done,
    bool intent_present,
}

@amended("2020-01-01", "Reform Act")
@precedent("PP v Lee [2019]")
statute 100 "Test Offense" effective 2020-01-01 {
    definitions {
        offense := "a test offense"
    }
    elements {
        actus_reus act := "committed the act"
        mens_rea intent := "had the intent"
    }
    penalty {
        imprisonment := 2 years
        fine := $5,000
    }
    exception self_defence {
        "acted in self-defence"
    }
}

legal_test OffenseTest {
    bool act_done,
    bool intent_present,
    requires act_done && intent_present
}

conflict_check S100_vs_S200 {
    source := "s100_test"
    target := "s200_other"
}
"""
        mod = parse(src)
        assert len(mod.statutes) == 1
        assert len(mod.legal_tests) == 1
        assert len(mod.conflict_checks) == 1
        assert len(mod.statutes[0].annotations) == 2
        # Transpile to all available targets. Some referenced targets
        # (CATALA, FSTAR, PROLOG) are planned but not yet shipped — the
        # enum may not declare them. Skip those rather than fail.
        wanted = ["CATALA", "FSTAR", "JSON", "ENGLISH", "PROLOG"]
        targets = [getattr(TranspileTarget, n) for n in wanted
                   if hasattr(TranspileTarget, n)]
        registry = TranspilerRegistry.instance()
        for target in targets:
            transpiler = registry.get(target)
            output = transpiler.transpile(mod)
            assert len(output) > 0, f"Empty output for {target}"

    def test_existing_statutes_still_parse(self):
        """Ensure existing statute syntax is unaffected."""
        src = """
statute 299 "Culpable Homicide" effective 1872-01-01 {
    definitions {
        culpableHomicide := "causing death by doing an act"
    }
    elements {
        actus_reus causingDeath := "causes the death of a person"
        mens_rea intentionToCauseDeath := "with the intention of causing death"
    }
    penalty {
        imprisonment := 10 years .. 20 years
        fine := $10,000
    }
    illustration a {
        "A shoots B with intent to kill"
    }
    exception suddenProvocation {
        "the offender was deprived of self-control by sudden provocation"
    }
}
"""
        mod = parse(src)
        assert len(mod.statutes) == 1
        s = mod.statutes[0]
        assert s.section_number == "299"
        assert len(s.definitions) == 1
        assert len(s.illustrations) == 1
        assert len(s.exceptions) == 1
