"""
Yuho testing module - pytest fixtures and utilities for testing Yuho statute implementations.

Usage in your tests:
    from yuho.testing import yuho_parser, yuho_ast, parse_statute

Or import fixtures directly in conftest.py:
    pytest_plugins = ["yuho.testing.fixtures"]

For coverage tracking:
    from yuho.testing import CoverageTracker, analyze_test_coverage
"""

from yuho.testing.fixtures import (
    yuho_parser,
    yuho_ast,
    parse_statute,
    parse_file,
    statute_validator,
    StatuteTestCase,
    element_check,
    penalty_check,
)
from yuho.testing.coverage import (
    CoverageTracker,
    CoverageReport,
    StatuteCoverage,
    ElementCoverage,
    analyze_test_coverage,
)

__all__ = [
    # Fixtures
    "yuho_parser",
    "yuho_ast",
    "parse_statute",
    "parse_file",
    "statute_validator",
    "StatuteTestCase",
    "element_check",
    "penalty_check",
    # Coverage
    "CoverageTracker",
    "CoverageReport",
    "StatuteCoverage",
    "ElementCoverage",
    "analyze_test_coverage",
]
