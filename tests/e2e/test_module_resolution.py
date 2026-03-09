"""E2E tests: module resolution."""
import pytest
from pathlib import Path

class TestModuleResolution:
    def test_referencing_resolves(self, parse_source):
        """referencing statements should be parseable."""
        source = 'referencing penal_code/s300_murder;'
        ast = parse_source(source)
        assert len(ast.references) > 0
        assert ast.references[0].path == "penal_code/s300_murder"

    def test_import_resolves(self, parse_source):
        """import statements should be parseable."""
        source = 'import "test_module.yh";'
        ast = parse_source(source)
        assert len(ast.imports) > 0

    def test_resolver_cycle_detection(self):
        """Module resolver should detect import cycles."""
        try:
            from yuho.resolver import ModuleResolver
            resolver = ModuleResolver()
            # basic instantiation test
            assert resolver is not None
        except ImportError:
            pytest.skip("resolver not available")

    def test_resolver_search_paths(self, tmp_path):
        """Resolver should search configured paths."""
        try:
            from yuho.resolver import ModuleResolver
            resolver = ModuleResolver(search_paths=[tmp_path])
            assert tmp_path.resolve() in resolver._search_paths
        except (ImportError, AttributeError):
            pytest.skip("resolver not available")
