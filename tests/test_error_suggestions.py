"""Regression tests for the parse-error suggestion engine."""

from __future__ import annotations

from yuho.cli.error_formatter import format_suggestions, suggest_keyword
from yuho.parser.wrapper import ParseError
from yuho.parser.source_location import SourceLocation


def _err(msg: str, line: int = 1, col: int = 1, end_col: int = 1) -> ParseError:
    return ParseError(
        message=msg,
        location=SourceLocation(file="test.yh", line=line, col=col, end_line=line, end_col=end_col),
    )


class TestSuggestKeyword:
    def test_close_typo(self):
        assert "actus_reus" in suggest_keyword("actu_reus")

    def test_distance_2(self):
        assert "elements" in suggest_keyword("elemnts")

    def test_unknown_returns_empty(self):
        assert suggest_keyword("xyzzy12345") == []

    def test_g14_keyword_in_set(self):
        assert "unspecified" in suggest_keyword("unspecifed")

    def test_g8_or_both_in_set(self):
        assert "or_both" in suggest_keyword("orboth")


class TestStructuralHints:
    def test_assignment_operator(self):
        src = 'actus_reus deception = "..."'
        e = _err("Unexpected syntax: 'actus_reus deception = ...'")
        hints = format_suggestions(e, src)
        assert any("`:=`" in h for h in hints), hints

    def test_missing_close_brace(self):
        src = "statute 1 \"x\" effective 1872-01-01 {\n"
        e = _err("Missing closing brace '}'")
        hints = format_suggestions(e, src)
        assert any("never closed" in h for h in hints), hints

    def test_missing_semicolon(self):
        src = "fine := unlimited"
        e = _err("Missing semicolon")
        hints = format_suggestions(e, src)
        assert any("`;`" in h for h in hints), hints

    def test_fabricated_fine_cap(self):
        # Source has fabricated fine but no canonical "with fine"
        src = "penalty {\n    fine := $0.00 .. $50,000.00;\n}\n"
        e = _err("Unexpected syntax: '$0.00 ..'", line=2, col=12)
        hints = format_suggestions(e, src)
        assert any("unlimited" in h.lower() for h in hints), hints

    def test_fabricated_caning_range(self):
        src = "penalty {\n    caning := 0 .. 24 strokes;\n}\n"
        e = _err("Unexpected syntax: 'caning := 0 ..'", line=2, col=12)
        hints = format_suggestions(e, src)
        assert any("unspecified" in h.lower() for h in hints), hints


class TestDidYouMean:
    def test_typo_in_unexpected(self):
        e = _err("Unexpected syntax: 'elemnts'")
        hints = format_suggestions(e, "elemnts {")
        assert any("elements" in h for h in hints), hints

    def test_no_suggestion_for_short_token(self):
        e = _err("Unexpected syntax: 'a'")
        hints = format_suggestions(e, "a")
        # token shorter than 3 chars -> no Levenshtein hint
        assert not any("mean" in h for h in hints)

    def test_no_suggestion_for_unknown(self):
        e = _err("Unexpected syntax: 'completelyfabricated'")
        hints = format_suggestions(e, "completelyfabricated")
        assert not any("mean" in h for h in hints)


class TestNoFalsePositives:
    def test_valid_source_yields_no_hints(self):
        # An empty error gives empty hints.
        e = _err("Some unrelated error")
        assert format_suggestions(e, "") == []

    def test_dedupe(self):
        # Same hint shouldn't appear twice.
        src = 'actus_reus x = "y"'
        e = _err("Unexpected syntax: 'x'")
        hints = format_suggestions(e, src)
        assert len(set(hints)) == len(hints)
