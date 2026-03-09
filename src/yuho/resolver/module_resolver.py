"""
Module resolution for Yuho cross-file imports and references.

Resolves ImportNode and ReferencingStmt to parsed ModuleNode ASTs,
with caching, cycle detection, and exported symbol extraction.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional
import logging

from yuho.ast.nodes import (
    ModuleNode,
    ImportNode,
    ReferencingStmt,
    ASTNode,
    StructDefNode,
    FunctionDefNode,
    StatuteNode,
    VariableDecl,
)
from yuho.ast.builder import ASTBuilder
from yuho.parser import get_parser

logger = logging.getLogger(__name__)


class ModuleResolutionError(Exception):
    """Raised when a module cannot be resolved."""

    def __init__(self, message: str, path: str = "", from_file: str = ""):
        self.path = path
        self.from_file = from_file
        super().__init__(message)


class CycleError(ModuleResolutionError):
    """Raised when a circular import is detected."""

    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        cycle_str = " -> ".join(cycle_path)
        super().__init__(
            f"Circular import detected: {cycle_str}",
            path=cycle_path[-1] if cycle_path else "",
            from_file=cycle_path[0] if cycle_path else "",
        )


class ModuleResolver:
    """
    Resolves Yuho module imports and references to parsed ASTs.

    Handles:
    - ImportNode resolution (relative/absolute .yh file paths)
    - ReferencingStmt resolution (library statute paths)
    - Module caching to avoid re-parsing
    - Cycle detection to prevent infinite loops
    - Exported symbol extraction for scope injection

    Usage:
        resolver = ModuleResolver(search_paths=[Path("library")])
        module = resolver.resolve(import_node, from_file=Path("main.yh"))
        symbols = resolver.get_exported_symbols(module)
    """

    def __init__(self, search_paths: Optional[List[Path]] = None):
        """
        Initialize the resolver.

        Args:
            search_paths: directories to search for modules.
                          Defaults to [cwd] if not provided.
        """
        if search_paths is not None:
            self._search_paths = [Path(p).resolve() for p in search_paths]
        else:
            self._search_paths = [Path.cwd()]
        self._cache: Dict[str, ModuleNode] = {} # abs path str -> ModuleNode
        self._currently_resolving: Set[str] = set()
        self._parser = None # lazily initialized on first resolve

    @property
    def search_paths(self) -> List[Path]:
        """Return the configured search paths."""
        return list(self._search_paths)

    # =========================================================================
    # Public API
    # =========================================================================

    def resolve(self, import_node: ImportNode, from_file: Path) -> ModuleNode:
        """
        Resolve an ImportNode to its parsed ModuleNode.

        Tries the following in order:
        1. import_path relative to the importing file's directory
        2. import_path + .yh extension relative to importing file
        3. import_path relative to each search path
        4. import_path + .yh relative to each search path

        Args:
            import_node: the import statement AST node
            from_file: path of the file containing the import

        Returns:
            Parsed ModuleNode for the imported file

        Raises:
            ModuleResolutionError: if the file cannot be found
            CycleError: if a circular import is detected
        """
        from_dir = Path(from_file).resolve().parent
        candidates = self._import_candidates(import_node.path, from_dir)
        return self._resolve_from_candidates(
            candidates,
            import_node.path,
            str(from_file),
        )

    def resolve_reference(
        self, ref: ReferencingStmt, from_file: Path
    ) -> ModuleNode:
        """
        Resolve a ReferencingStmt (e.g. referencing penal_code/s300_murder).

        Search order:
        1. library/{path}/statute.yh relative to each search path
        2. {path}.yh relative to each search path
        3. {path}/statute.yh relative to each search path
        4. {path}.yh relative to importing file
        5. {path}/statute.yh relative to importing file

        Args:
            ref: the referencing statement AST node
            from_file: path of the file containing the reference

        Returns:
            Parsed ModuleNode for the referenced statute

        Raises:
            ModuleResolutionError: if the statute cannot be found
            CycleError: if a circular reference is detected
        """
        from_dir = Path(from_file).resolve().parent
        candidates = self._reference_candidates(ref.path, from_dir)
        return self._resolve_from_candidates(
            candidates,
            ref.path,
            str(from_file),
        )

    def get_exported_symbols(self, module: ModuleNode) -> Dict[str, ASTNode]:
        """
        Extract exported symbols from a module.

        Returns a dict mapping symbol name to its defining AST node.
        Exports include:
        - struct names -> StructDefNode
        - function names -> FunctionDefNode
        - statute section numbers -> StatuteNode
        - top-level variable names -> VariableDecl

        Args:
            module: a parsed ModuleNode

        Returns:
            Dict mapping name strings to their defining ASTNode
        """
        symbols: Dict[str, ASTNode] = {}
        for struct_def in module.type_defs:
            symbols[struct_def.name] = struct_def
        for func_def in module.function_defs:
            symbols[func_def.name] = func_def
        for statute in module.statutes:
            symbols[statute.section_number] = statute
        for var_decl in module.variables:
            symbols[var_decl.name] = var_decl
        return symbols

    def resolve_and_get_symbols(
        self,
        import_node: ImportNode,
        from_file: Path,
    ) -> Dict[str, ASTNode]:
        """
        Convenience: resolve an import and return its exported symbols,
        filtered by the imported_names list if specified.

        Args:
            import_node: the import statement
            from_file: path of the importing file

        Returns:
            Dict of symbol name -> ASTNode to inject into scope
        """
        module = self.resolve(import_node, from_file)
        all_symbols = self.get_exported_symbols(module)
        if not import_node.imported_names or import_node.is_wildcard:
            return all_symbols # import all
        return {
            name: node
            for name, node in all_symbols.items()
            if name in import_node.imported_names
        }

    def clear_cache(self) -> None:
        """Clear the module cache."""
        self._cache.clear()

    @property
    def cached_modules(self) -> Dict[str, ModuleNode]:
        """Return a read-only view of the module cache."""
        return dict(self._cache)

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _get_parser(self):
        """Lazily initialize and return the tree-sitter parser."""
        if self._parser is None:
            self._parser = get_parser()
        return self._parser

    def _import_candidates(
        self, import_path: str, from_dir: Path
    ) -> List[Path]:
        """Generate candidate file paths for an import statement."""
        candidates: List[Path] = []
        raw = Path(import_path)
        # relative to importing file
        candidates.append(from_dir / raw)
        if not import_path.endswith(".yh"):
            candidates.append(from_dir / f"{import_path}.yh")
        # relative to each search path
        for sp in self._search_paths:
            candidates.append(sp / raw)
            if not import_path.endswith(".yh"):
                candidates.append(sp / f"{import_path}.yh")
        return candidates

    def _reference_candidates(
        self, ref_path: str, from_dir: Path
    ) -> List[Path]:
        """Generate candidate file paths for a referencing statement."""
        candidates: List[Path] = []
        # library/{path}/statute.yh relative to search paths
        for sp in self._search_paths:
            candidates.append(sp / "library" / ref_path / "statute.yh")
        # {path}.yh and {path}/statute.yh relative to search paths
        for sp in self._search_paths:
            candidates.append(sp / f"{ref_path}.yh")
            candidates.append(sp / ref_path / "statute.yh")
        # relative to importing file
        candidates.append(from_dir / f"{ref_path}.yh")
        candidates.append(from_dir / ref_path / "statute.yh")
        return candidates

    def _resolve_from_candidates(
        self,
        candidates: List[Path],
        original_path: str,
        from_file: str,
    ) -> ModuleNode:
        """
        Try each candidate path and return the first that resolves.

        Raises ModuleResolutionError if none work.
        """
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_file():
                return self._parse_module(resolved, original_path, from_file)
        tried = "\n  ".join(str(c.resolve()) for c in candidates)
        raise ModuleResolutionError(
            f"Cannot resolve '{original_path}' from '{from_file}'. "
            f"Tried:\n  {tried}",
            path=original_path,
            from_file=from_file,
        )

    def _parse_module(
        self, file_path: Path, original_path: str, from_file: str
    ) -> ModuleNode:
        """
        Parse a .yh file into a ModuleNode, with caching and cycle detection.
        """
        key = str(file_path)
        # cache hit
        if key in self._cache:
            return self._cache[key]
        # cycle detection
        if key in self._currently_resolving:
            cycle = list(self._currently_resolving) + [key]
            raise CycleError(cycle)
        self._currently_resolving.add(key)
        try:
            source = file_path.read_text(encoding="utf-8")
            parse_result = self._get_parser().parse(source, file=str(file_path))
            if parse_result.root_node is None:
                raise ModuleResolutionError(
                    f"Failed to parse '{file_path}': no parse tree produced",
                    path=original_path,
                    from_file=from_file,
                )
            builder = ASTBuilder(source, file=str(file_path))
            module = builder.build(parse_result.root_node)
            self._cache[key] = module
            # recursively resolve nested imports
            self._resolve_nested(module, file_path)
            return module
        except (OSError, UnicodeDecodeError) as exc:
            raise ModuleResolutionError(
                f"Cannot read '{file_path}': {exc}",
                path=original_path,
                from_file=from_file,
            ) from exc
        finally:
            self._currently_resolving.discard(key)

    def _resolve_nested(self, module: ModuleNode, file_path: Path) -> None:
        """Recursively resolve imports and references inside a module."""
        for imp in module.imports:
            try:
                self.resolve(imp, file_path)
            except ModuleResolutionError as exc:
                logger.warning("nested import resolution failed: %s", exc)
        for ref in module.references:
            try:
                self.resolve_reference(ref, file_path)
            except ModuleResolutionError as exc:
                logger.warning("nested reference resolution failed: %s", exc)
