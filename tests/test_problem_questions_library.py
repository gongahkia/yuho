"""Problem-question library coverage."""

from __future__ import annotations

from pathlib import Path

from yuho.services.analysis import analyze_file


ROOT = Path(__file__).resolve().parents[1]
PROBLEM_QUESTIONS = ROOT / "library" / "problem_questions"


def test_problem_questions_contains_ten_hypos():
    files = sorted(PROBLEM_QUESTIONS.glob("*.yh"))

    assert len(files) == 10


def test_problem_questions_parse():
    for path in sorted(PROBLEM_QUESTIONS.glob("*.yh")):
        result = analyze_file(path, run_semantic=False)

        assert result.parse_errors == [], path
        assert result.ast is not None, path

