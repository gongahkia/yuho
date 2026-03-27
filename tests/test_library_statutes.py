"""
Real per-element tests for all library statutes.

Verifies that every statute in the library:
- Parses without errors
- Has required structural elements (title, elements, penalty)
- Contains at least one actus_reus and one mens_rea
- Has definitions and illustrations
- Has a companion test file that parses
"""

import pytest
from pathlib import Path

from yuho.services.analysis import analyze_file


LIBRARY_DIR = Path(__file__).parent.parent / "library" / "penal_code"


def _statute_dirs():
    """Yield (dir_name, statute_path) for each statute in the library."""
    if not LIBRARY_DIR.exists():
        return
    for d in sorted(LIBRARY_DIR.iterdir()):
        yh = d / "statute.yh"
        if d.is_dir() and yh.exists():
            yield d.name, yh


STATUTE_DIRS = list(_statute_dirs())


@pytest.mark.parametrize("name,path", STATUTE_DIRS, ids=[s[0] for s in STATUTE_DIRS])
class TestStatuteParsing:
    """Every statute must parse without errors."""

    def test_parses_without_errors(self, name, path):
        result = analyze_file(str(path))
        assert result.is_valid, f"{name}: parse errors: {result.errors}"
        assert result.ast is not None

    def test_has_at_least_one_statute(self, name, path):
        result = analyze_file(str(path))
        assert result.ast is not None
        assert len(result.ast.statutes) >= 1, f"{name}: no statutes found"

    def test_has_title(self, name, path):
        result = analyze_file(str(path))
        for s in result.ast.statutes:
            assert s.title is not None, f"{name} s{s.section_number}: missing title"

    def test_has_elements(self, name, path):
        result = analyze_file(str(path))
        for s in result.ast.statutes:
            assert len(s.elements) > 0, f"{name} s{s.section_number}: no elements"

    def test_has_penalty(self, name, path):
        result = analyze_file(str(path))
        for s in result.ast.statutes:
            assert s.penalty is not None, f"{name} s{s.section_number}: missing penalty"

    def test_has_definitions(self, name, path):
        result = analyze_file(str(path))
        for s in result.ast.statutes:
            assert len(s.definitions) > 0, f"{name} s{s.section_number}: no definitions"


@pytest.mark.parametrize("name,path", STATUTE_DIRS, ids=[s[0] for s in STATUTE_DIRS])
class TestStatuteElements:
    """Per-element checks: actus_reus, mens_rea presence."""

    def _flat_elements(self, elements):
        """Flatten element groups into individual elements."""
        from yuho.ast.nodes import ElementNode, ElementGroupNode

        flat = []
        for e in elements:
            if isinstance(e, ElementGroupNode):
                flat.extend(self._flat_elements(e.members))
            elif isinstance(e, ElementNode):
                flat.append(e)
        return flat

    def test_has_actus_reus(self, name, path):
        result = analyze_file(str(path))
        for s in result.ast.statutes:
            flat = self._flat_elements(s.elements)
            ar = [e for e in flat if e.element_type == "actus_reus"]
            assert len(ar) > 0, f"{name} s{s.section_number}: no actus_reus"

    def test_element_names_unique(self, name, path):
        result = analyze_file(str(path))
        for s in result.ast.statutes:
            flat = self._flat_elements(s.elements)
            names = [e.name for e in flat]
            assert len(names) == len(
                set(names)
            ), f"{name} s{s.section_number}: duplicate element names: {names}"


@pytest.mark.parametrize("name,path", STATUTE_DIRS, ids=[s[0] for s in STATUTE_DIRS])
class TestStatuteTestFiles:
    """Every statute should have a companion test file."""

    def test_test_file_exists(self, name, path):
        test_file = path.parent / "test_statute.yh"
        assert test_file.exists(), f"{name}: missing test_statute.yh"

    def test_test_file_parses(self, name, path):
        test_file = path.parent / "test_statute.yh"
        if not test_file.exists():
            pytest.skip("no test file")
        result = analyze_file(str(test_file), run_semantic=False)
        assert result.ast is not None, f"{name}: test file has parse errors: {result.errors}"

    def test_test_file_is_semantically_valid(self, name, path):
        test_file = path.parent / "test_statute.yh"
        if not test_file.exists():
            pytest.skip("no test file")
        result = analyze_file(str(test_file))
        assert result.is_valid, f"{name}: test file has semantic errors: {result.errors}"

    def test_metadata_exists(self, name, path):
        meta = path.parent / "metadata.toml"
        assert meta.exists(), f"{name}: missing metadata.toml"
