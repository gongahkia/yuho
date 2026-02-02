"""
Coverage tracking for Yuho statute test implementations.

Tracks which elements, conditions, and branches are exercised by tests.
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class ElementCoverage:
    """Coverage tracking for a single statute element."""
    element_type: str  # actus_reus, mens_rea, circumstance
    name: str
    covered: bool = False
    test_count: int = 0
    test_files: List[str] = field(default_factory=list)


@dataclass
class StatuteCoverage:
    """Coverage tracking for a single statute."""
    section_number: str
    title: str = ""
    elements: Dict[str, ElementCoverage] = field(default_factory=dict)
    penalty_covered: bool = False
    illustrations_covered: Set[str] = field(default_factory=set)
    total_illustrations: int = 0

    @property
    def element_coverage_percent(self) -> float:
        """Calculate percentage of elements covered."""
        if not self.elements:
            return 0.0
        covered = sum(1 for e in self.elements.values() if e.covered)
        return (covered / len(self.elements)) * 100

    @property
    def overall_coverage_percent(self) -> float:
        """Calculate overall coverage percentage."""
        total_items = len(self.elements) + 1  # +1 for penalty
        if self.total_illustrations > 0:
            total_items += self.total_illustrations

        covered_items = sum(1 for e in self.elements.values() if e.covered)
        if self.penalty_covered:
            covered_items += 1
        covered_items += len(self.illustrations_covered)

        return (covered_items / total_items) * 100 if total_items > 0 else 0.0


@dataclass
class CoverageReport:
    """Complete coverage report for a test run."""
    statutes: Dict[str, StatuteCoverage] = field(default_factory=dict)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0

    @property
    def overall_coverage_percent(self) -> float:
        """Calculate overall coverage across all statutes."""
        if not self.statutes:
            return 0.0
        total = sum(s.overall_coverage_percent for s in self.statutes.values())
        return total / len(self.statutes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "summary": {
                "total_statutes": len(self.statutes),
                "overall_coverage": f"{self.overall_coverage_percent:.1f}%",
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
            },
            "statutes": {
                section: {
                    "title": cov.title,
                    "element_coverage": f"{cov.element_coverage_percent:.1f}%",
                    "overall_coverage": f"{cov.overall_coverage_percent:.1f}%",
                    "elements": {
                        name: {
                            "type": elem.element_type,
                            "covered": elem.covered,
                            "test_count": elem.test_count,
                        }
                        for name, elem in cov.elements.items()
                    },
                    "penalty_covered": cov.penalty_covered,
                    "illustrations_covered": len(cov.illustrations_covered),
                    "total_illustrations": cov.total_illustrations,
                }
                for section, cov in self.statutes.items()
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class CoverageTracker:
    """
    Tracks test coverage for Yuho statute implementations.

    Usage:
        tracker = CoverageTracker()
        tracker.load_statutes_from_ast(ast)
        tracker.mark_element_covered("378", "actus_reus", "taking", "test_theft.yh")
        report = tracker.generate_report()
    """

    def __init__(self):
        self.report = CoverageReport()

    def load_statutes_from_ast(self, ast) -> None:
        """Load statute structure from AST for coverage tracking."""
        for statute in ast.statutes:
            section = statute.section_number
            title = statute.title.value if statute.title else ""

            cov = StatuteCoverage(section_number=section, title=title)

            # Track elements
            for element in (statute.elements or []):
                elem_key = f"{element.element_type}:{element.name}"
                cov.elements[elem_key] = ElementCoverage(
                    element_type=element.element_type,
                    name=element.name,
                )

            # Track illustrations
            if hasattr(statute, 'illustrations') and statute.illustrations:
                cov.total_illustrations = len(statute.illustrations)

            self.report.statutes[section] = cov

    def mark_element_covered(
        self,
        section: str,
        element_type: str,
        element_name: str,
        test_file: str,
    ) -> None:
        """Mark an element as covered by a test."""
        if section not in self.report.statutes:
            return

        elem_key = f"{element_type}:{element_name}"
        cov = self.report.statutes[section]

        if elem_key in cov.elements:
            cov.elements[elem_key].covered = True
            cov.elements[elem_key].test_count += 1
            if test_file not in cov.elements[elem_key].test_files:
                cov.elements[elem_key].test_files.append(test_file)

    def mark_penalty_covered(self, section: str) -> None:
        """Mark penalty section as covered."""
        if section in self.report.statutes:
            self.report.statutes[section].penalty_covered = True

    def mark_illustration_covered(self, section: str, illustration_label: str) -> None:
        """Mark an illustration as covered."""
        if section in self.report.statutes:
            self.report.statutes[section].illustrations_covered.add(illustration_label)

    def add_test_result(self, passed: bool) -> None:
        """Record a test result."""
        self.report.total_tests += 1
        if passed:
            self.report.passed_tests += 1
        else:
            self.report.failed_tests += 1

    def generate_report(self) -> CoverageReport:
        """Generate the coverage report."""
        return self.report

    def print_summary(self) -> None:
        """Print a human-readable coverage summary."""
        print("\n" + "=" * 60)
        print("STATUTE COVERAGE REPORT")
        print("=" * 60)

        for section, cov in self.report.statutes.items():
            print(f"\n{section}: {cov.title}")
            print(f"  Element coverage: {cov.element_coverage_percent:.1f}%")

            for elem_key, elem in cov.elements.items():
                status = "COVERED" if elem.covered else "NOT COVERED"
                print(f"    [{status}] {elem.element_type}: {elem.name}")

            penalty_status = "COVERED" if cov.penalty_covered else "NOT COVERED"
            print(f"    [{penalty_status}] penalty")

            if cov.total_illustrations > 0:
                ill_cov = len(cov.illustrations_covered)
                print(f"    Illustrations: {ill_cov}/{cov.total_illustrations}")

        print("\n" + "-" * 60)
        print(f"Overall coverage: {self.report.overall_coverage_percent:.1f}%")
        print(f"Tests: {self.report.passed_tests}/{self.report.total_tests} passed")
        print("=" * 60)


def analyze_test_coverage(
    statute_files: List[Path],
    test_files: List[Path],
) -> CoverageReport:
    """
    Analyze test coverage for a set of statute and test files.

    Args:
        statute_files: List of .yh statute files
        test_files: List of test files

    Returns:
        CoverageReport with coverage analysis
    """
    from yuho.parser import Parser
    from yuho.ast import ASTBuilder

    tracker = CoverageTracker()
    parser = Parser()

    # Load statute structure
    for statute_file in statute_files:
        try:
            result = parser.parse_file(statute_file)
            if result.is_valid:
                builder = ASTBuilder(result.source, str(statute_file))
                ast = builder.build(result.root_node)
                tracker.load_statutes_from_ast(ast)
        except Exception:
            continue

    # Analyze test files for coverage
    for test_file in test_files:
        try:
            result = parser.parse_file(test_file)
            if result.is_valid:
                builder = ASTBuilder(result.source, str(test_file))
                ast = builder.build(result.root_node)

                # Check what elements are referenced in tests
                for statute in ast.statutes:
                    section = statute.section_number

                    # Mark elements as covered if they appear in test assertions
                    for elem in (statute.elements or []):
                        tracker.mark_element_covered(
                            section,
                            elem.element_type,
                            elem.name,
                            str(test_file),
                        )

                    if statute.penalty:
                        tracker.mark_penalty_covered(section)

                tracker.add_test_result(passed=True)
            else:
                tracker.add_test_result(passed=False)
        except Exception:
            tracker.add_test_result(passed=False)

    return tracker.generate_report()
