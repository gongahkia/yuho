"""
Pytest fixtures for testing Yuho statute implementations.

Provides ready-to-use fixtures for parsing, AST building, and validating
Yuho code in user tests.

Usage:
    # In conftest.py
    pytest_plugins = ["yuho.testing.fixtures"]

    # In test files
    def test_my_statute(yuho_parser, yuho_ast, parse_statute):
        ast = parse_statute("statute 299 {...}")
        assert len(ast.statutes) == 1
"""

from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
import pytest


@pytest.fixture
def yuho_parser():
    """
    Fixture providing a Yuho parser instance.

    Usage:
        def test_parse(yuho_parser):
            result = yuho_parser.parse("statute 299 {...}")
            assert result.is_valid
    """
    from yuho.parser import Parser
    return Parser()


@pytest.fixture
def yuho_ast(yuho_parser):
    """
    Fixture providing an AST builder function.

    Usage:
        def test_ast(yuho_ast):
            ast = yuho_ast("statute 299 {...}")
            assert len(ast.statutes) == 1
    """
    from yuho.ast import ASTBuilder

    def build_ast(source: str):
        result = yuho_parser.parse(source)
        if not result.is_valid:
            raise ValueError(f"Parse error: {result.errors[0].message}")
        builder = ASTBuilder(source)
        return builder.build(result.root_node)

    return build_ast


@pytest.fixture
def parse_statute(yuho_ast):
    """
    Fixture providing a function to parse statute code and return the first statute.

    Usage:
        def test_theft(parse_statute):
            statute = parse_statute('''
                statute 378 "Theft" {
                    elements {
                        actus_reus taking: "takes property"
                    }
                }
            ''')
            assert statute.section_number == "378"
    """
    def _parse(source: str):
        ast = yuho_ast(source)
        if not ast.statutes:
            raise ValueError("No statute found in source")
        return ast.statutes[0]

    return _parse


@pytest.fixture
def parse_file(yuho_ast):
    """
    Fixture providing a function to parse a .yh file.

    Usage:
        def test_file(parse_file):
            ast = parse_file("path/to/statute.yh")
            assert len(ast.statutes) >= 1
    """
    def _parse_file(path: str):
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        source = file_path.read_text()
        return yuho_ast(source)

    return _parse_file


@pytest.fixture
def statute_validator():
    """
    Fixture providing a statute validator for checking statute completeness.

    Usage:
        def test_valid(statute_validator, parse_statute):
            statute = parse_statute("...")
            result = statute_validator(statute)
            assert result.valid
            assert not result.errors
    """
    @dataclass
    class ValidationResult:
        valid: bool
        errors: List[str] = field(default_factory=list)
        warnings: List[str] = field(default_factory=list)

    def _validate(statute) -> ValidationResult:
        errors = []
        warnings = []

        # Check required fields
        if not statute.section_number:
            errors.append("Missing section number")

        if not statute.title:
            warnings.append("Missing title")

        if not statute.elements:
            errors.append("No elements defined")
        else:
            # Check for at least one actus_reus
            has_actus = any(
                e.element_type == "actus_reus"
                for e in statute.elements
            )
            if not has_actus:
                warnings.append("No actus_reus element defined")

            # Check for mens_rea
            has_mens = any(
                e.element_type == "mens_rea"
                for e in statute.elements
            )
            if not has_mens:
                warnings.append("No mens_rea element defined")

        if not statute.penalty:
            warnings.append("No penalty section defined")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    return _validate


@dataclass
class StatuteTestCase:
    """
    Helper class for defining statute test cases.

    Usage:
        cases = [
            StatuteTestCase(
                name="theft_basic",
                source='''statute 378 "Theft" {...}''',
                expected_elements=["actus_reus:taking"],
                expected_penalty_max=7,  # years
            ),
        ]

        @pytest.mark.parametrize("case", cases, ids=lambda c: c.name)
        def test_statute(case, parse_statute):
            statute = parse_statute(case.source)
            case.verify(statute)
    """
    name: str
    source: str
    expected_section: Optional[str] = None
    expected_title: Optional[str] = None
    expected_elements: List[str] = field(default_factory=list)
    expected_penalty_max: Optional[int] = None  # years
    expected_fine_max: Optional[float] = None

    def verify(self, statute) -> None:
        """Verify statute against expected values. Raises AssertionError on mismatch."""
        if self.expected_section:
            assert statute.section_number == self.expected_section, \
                f"Section mismatch: expected {self.expected_section}, got {statute.section_number}"

        if self.expected_title:
            title = statute.title.value if statute.title else None
            assert title == self.expected_title, \
                f"Title mismatch: expected {self.expected_title}, got {title}"

        if self.expected_elements:
            actual_elements = [
                f"{e.element_type}:{e.name}"
                for e in (statute.elements or [])
            ]
            for expected in self.expected_elements:
                assert expected in actual_elements, \
                    f"Missing element: {expected}. Found: {actual_elements}"


def element_check(statute, element_type: str, name: str) -> bool:
    """
    Check if a statute has a specific element.

    Usage:
        def test_has_actus_reus(parse_statute):
            statute = parse_statute("...")
            assert element_check(statute, "actus_reus", "taking")
    """
    if not statute.elements:
        return False
    return any(
        e.element_type == element_type and e.name == name
        for e in statute.elements
    )


def penalty_check(statute, penalty_type: str, max_value: Any = None) -> bool:
    """
    Check if a statute has a specific penalty type.

    Usage:
        def test_has_imprisonment(parse_statute):
            statute = parse_statute("...")
            assert penalty_check(statute, "imprisonment")
    """
    if not statute.penalty:
        return False

    # Check penalty structure
    penalty = statute.penalty
    if hasattr(penalty, penalty_type):
        penalty_val = getattr(penalty, penalty_type)
        if penalty_val is None:
            return False
        if max_value is not None and hasattr(penalty_val, 'max'):
            return penalty_val.max is not None
        return True

    return False


# Register as pytest plugin
def pytest_configure(config):
    """Register Yuho markers."""
    config.addinivalue_line(
        "markers", "statute(section): mark test as testing a specific statute section"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
