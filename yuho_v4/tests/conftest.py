"""
Pytest Configuration and Shared Fixtures

This file contains shared pytest configuration and fixtures used across test modules.
"""

import pytest
import sys
import os
from pathlib import Path

# Add yuho_v4 to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def sample_yuho_code():
    """Fixture providing sample Yuho code snippets"""
    return {
        'simple_struct': """
            struct Person {
                string name,
                int age
            }
        """,
        'struct_with_declaration': """
            struct Person {
                string name,
                int age
            }
            Person p := {
                name := "John",
                age := 30
            }
        """,
        'match_case': """
            match {
                case TRUE := consequence TRUE;
                case _ := consequence pass;
            }
        """,
        'arithmetic': """
            int x := 1 + 2 * 3;
        """,
        'logical': """
            bool result := TRUE && FALSE || TRUE;
        """,
    }


@pytest.fixture
def invalid_yuho_code():
    """Fixture providing invalid Yuho code for error testing"""
    return {
        'wrong_assignment': 'int x = 42;',  # Should use :=
        'unclosed_brace': 'struct Test {',
        'type_mismatch': 'int x := "string";',
        'undefined_var': 'int y := x;',
    }


@pytest.fixture
def legal_example_code():
    """Fixture providing legal statute representation examples"""
    return {
        'cheating': """
            struct Cheating {
                string accused,
                string action,
                string victim,
                bool deception,
                bool dishonest,
                bool harm
            }
            
            match {
                case deception && dishonest && harm := consequence "guilty of cheating";
                case _ := consequence "not guilty";
            }
        """,
        'theft': """
            struct Theft {
                string accused,
                string property,
                bool dishonest,
                bool movable,
                bool withoutConsent
            }
            
            match {
                case dishonest && movable && withoutConsent := consequence "guilty of theft";
                case _ := consequence "not guilty";
            }
        """,
    }


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

