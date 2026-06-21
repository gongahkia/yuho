"""
Transpiler base class and target enum.
"""

from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence
from enum import Enum, auto

from yuho.ast.nodes import ModuleNode
from yuho.transpile.source_map import build_source_map


class TranspileTarget(Enum):
    """Supported transpilation targets."""

    JSON = auto()
    ENGLISH = auto()
    LATEX = auto()
    MERMAID = auto()
    MINDMAP = auto()
    ALLOY = auto()
    DOCX = auto()
    AKOMANTOSO = auto()
    LEGALRULEML = auto()

    @classmethod
    def from_string(cls, name: str) -> "TranspileTarget":
        """Convert string to TranspileTarget."""
        mapping = {
            "json": cls.JSON,
            "english": cls.ENGLISH,
            "en": cls.ENGLISH,
            "latex": cls.LATEX,
            "tex": cls.LATEX,
            "mermaid": cls.MERMAID,
            "mmd": cls.MERMAID,
            "mindmap": cls.MINDMAP,
            "mermaid-mindmap": cls.MINDMAP,
            "alloy": cls.ALLOY,
            "docx": cls.DOCX,
            "word": cls.DOCX,
            "akomantoso": cls.AKOMANTOSO,
            "akn": cls.AKOMANTOSO,
            "legaldocml": cls.AKOMANTOSO,
            "legalruleml": cls.LEGALRULEML,
            "lrml": cls.LEGALRULEML,
        }
        target = mapping.get(name.lower())
        if not target:
            raise ValueError(f"Unknown transpile target: {name}")
        return target

    @property
    def file_extension(self) -> str:
        """Return the file extension for this target."""
        extensions = {
            TranspileTarget.JSON: ".json",
            TranspileTarget.ENGLISH: ".txt",
            TranspileTarget.LATEX: ".tex",
            TranspileTarget.MERMAID: ".mmd",
            TranspileTarget.MINDMAP: ".mmd",
            TranspileTarget.ALLOY: ".als",
            TranspileTarget.DOCX: ".docx",
            TranspileTarget.AKOMANTOSO: ".xml",
            TranspileTarget.LEGALRULEML: ".lrml",
        }
        return extensions.get(self, ".txt")


class TranspileResult(str):
    """String-compatible transpilation result with diagnostics metadata."""

    output: str
    warnings: tuple[str, ...]
    manifest: dict[str, Any]
    source_map: dict[str, Any] | None

    def __new__(
        cls,
        output: str,
        warnings: Sequence[str] = (),
        manifest: Mapping[str, Any] | None = None,
        source_map: Mapping[str, Any] | None = None,
    ) -> "TranspileResult":
        obj = str.__new__(cls, output)
        obj.output = output
        obj.warnings = tuple(warnings)
        obj.manifest = dict(manifest or {})
        obj.source_map = dict(source_map) if source_map is not None else None
        return obj

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "output": self.output,
            "warnings": list(self.warnings),
            "manifest": self.manifest,
        }
        if self.source_map is not None:
            payload["source_map"] = self.source_map
        return payload


class TranspilerBase(ABC):
    """
    Abstract base class for transpilers.

    Subclasses must implement the transpile() method to convert
    a Yuho AST (ModuleNode) to the target format.
    """

    @property
    @abstractmethod
    def target(self) -> TranspileTarget:
        """Return the transpilation target."""
        pass

    @abstractmethod
    def transpile(self, ast: ModuleNode) -> TranspileResult:
        """
        Transpile a Yuho AST to the target format.

        Args:
            ast: The root ModuleNode of the AST

        Returns:
            String-compatible result with output, warnings, and manifest
        """
        pass

    def result(
        self,
        output: str,
        warnings: Sequence[str] = (),
        manifest: Mapping[str, Any] | None = None,
        source_ast: ModuleNode | None = None,
    ) -> TranspileResult:
        payload = {
            "target": self.target.name.lower(),
            "extension": self.target.file_extension,
        }
        if manifest:
            payload.update(manifest)
        source_map = None
        if source_ast is not None:
            source_map = build_source_map(output, source_ast)
            payload["source_map"] = {
                "version": source_map["version"],
                "sources": len(source_map["sources"]),
                "names": len(source_map["names"]),
                "spans": len(source_map["x_yuho_spans"]),
            }
        return TranspileResult(
            output,
            warnings=warnings,
            manifest=payload,
            source_map=source_map,
        )

    def transpile_to_file(self, ast: ModuleNode, path: str) -> None:
        """
        Transpile and write to a file.

        Args:
            ast: The root ModuleNode of the AST
            path: Output file path
        """
        output = self.transpile(ast).output
        with open(path, "w", encoding="utf-8") as f:
            f.write(output)
