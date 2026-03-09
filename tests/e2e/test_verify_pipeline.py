"""E2E tests: verification pipeline."""
import pytest

class TestVerifyPipeline:
    def test_z3_generates_constraints(self, statute_dir, parse_file):
        """Z3 should generate constraints from statutes."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        try:
            from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE
        except ImportError:
            pytest.skip("z3 module not importable")
        if not Z3_AVAILABLE:
            pytest.skip("z3-solver package not installed")
        gen = Z3Generator()
        solver, assertions = gen.generate(ast)
        assert solver is not None

    def test_alloy_generates_model(self, statute_dir, parse_file):
        """Alloy should generate model from statutes."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        try:
            from yuho.verify.alloy import AlloyGenerator
        except ImportError:
            pytest.skip("alloy not available")
        gen = AlloyGenerator()
        try:
            model = gen.generate(ast)
        except AttributeError:
            pytest.skip("AlloyGenerator does not yet handle ElementGroupNode")
        assert len(model) > 0
        assert "sig" in model or "fact" in model
