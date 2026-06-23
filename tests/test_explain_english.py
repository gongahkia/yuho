"""English rendering for explain traces."""

from __future__ import annotations

from yuho.explain import ElementTrace, JustificationTrace, PrecedentTrace
from yuho.transpile.english_transpiler import EnglishTranspiler


def test_english_transpiler_renders_explain_trace():
    trace = JustificationTrace(
        statute_section="1",
        overall_satisfied=False,
        elements=(
            ElementTrace(
                name="intent",
                element_type="mens_rea",
                satisfied=False,
                rule="satisfied(intent) :- fact(intent, true).",
                reason="fact 'intent' is missing or false",
            ),
        ),
        rules=("satisfied(intent) :- fact(intent, true).",),
    )

    rendered = EnglishTranspiler().render_explain_trace(trace)

    assert "Section 1 is not satisfied." in rendered
    assert (
        "The mens_rea element intent is not satisfied because " "fact 'intent' is missing or false."
    ) in rendered


def test_english_transpiler_renders_precedent_notes():
    trace = JustificationTrace(
        statute_section="1",
        overall_satisfied=True,
        elements=(
            ElementTrace(
                name="taking",
                element_type="actus_reus",
                satisfied=True,
                rule="satisfied(taking) :- fact(taking, true).",
                reason="fact 'taking' is truthy",
                precedents=(
                    PrecedentTrace(
                        case_name="New v PP",
                        citation="[2026] SGCA 1",
                        holding="Taking requires control plus deprivation",
                    ),
                ),
            ),
        ),
        rules=("satisfied(taking) :- fact(taking, true).",),
    )

    rendered = EnglishTranspiler().render_explain_trace(trace)

    assert "Case law New v PP [2026] SGCA 1 interprets element taking" in rendered
