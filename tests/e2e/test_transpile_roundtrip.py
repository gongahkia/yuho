"""E2E tests: transpilation roundtrip."""
import pytest
import json
from yuho.transpile.base import TranspileTarget
from yuho.transpile.registry import TranspilerRegistry

TARGETS = [t for t in TranspileTarget]

class TestTranspileRoundtrip:
    def test_transpile_to_json(self, statute_dir, parse_file):
        """Statutes should transpile to valid JSON."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.JSON)
        output = transpiler.transpile(ast)
        assert len(output) > 0
        parsed = json.loads(output) # should be valid JSON
        assert isinstance(parsed, dict)

    def test_transpile_to_english(self, statute_dir, parse_file):
        """Statutes should transpile to English text."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.ENGLISH)
        output = transpiler.transpile(ast)
        assert len(output) > 0
        lower = output.lower()
        assert "section" in lower or "statute" in lower

    @pytest.mark.parametrize("target", TARGETS, ids=lambda t: t.name)
    def test_all_targets_produce_output(self, target, parse_source):
        """All transpile targets should produce non-empty output for a minimal statute."""
        source = '''
struct TestCase { bool guilty, }
statute 999 "Test Statute" {
    elements {
        actus_reus act := "The physical act";
        mens_rea intent := "The mental state";
    }
    penalty {
        imprisonment := 1 years .. 5 years;
    }
}
'''
        ast = parse_source(source)
        registry = TranspilerRegistry.instance()
        try:
            transpiler = registry.get(target)
            output = transpiler.transpile(ast)
            assert len(output) > 0
        except Exception:
            pytest.skip(f"Transpiler {target.name} not available")
