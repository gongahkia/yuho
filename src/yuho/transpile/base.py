"""
Transpiler base class and target enum.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto

from yuho.ast.nodes import ModuleNode


class TranspileTarget(Enum):
    """Supported transpilation targets."""

    JSON = auto()
    JSON_LD = auto()
    ENGLISH = auto()
    LATEX = auto()
    MERMAID = auto()
    ALLOY = auto()

    @classmethod
    def from_string(cls, name: str) -> "TranspileTarget":
        """Convert string to TranspileTarget."""
        mapping = {
            "json": cls.JSON,
            "jsonld": cls.JSON_LD,
            "json-ld": cls.JSON_LD,
            "english": cls.ENGLISH,
            "en": cls.ENGLISH,
            "latex": cls.LATEX,
            "tex": cls.LATEX,
            "mermaid": cls.MERMAID,
            "mmd": cls.MERMAID,
            "alloy": cls.ALLOY,
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
            TranspileTarget.JSON_LD: ".jsonld",
            TranspileTarget.ENGLISH: ".txt",
            TranspileTarget.LATEX: ".tex",
            TranspileTarget.MERMAID: ".mmd",
            TranspileTarget.ALLOY: ".als",
        }
        return extensions.get(self, ".txt")


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
    def transpile(self, ast: ModuleNode) -> str:
        """
        Transpile a Yuho AST to the target format.

        Args:
            ast: The root ModuleNode of the AST

        Returns:
            The transpiled output as a string
        """
        pass

    def transpile_to_file(self, ast: ModuleNode, path: str) -> None:
        """
        Transpile and write to a file.

        Args:
            ast: The root ModuleNode of the AST
            path: Output file path
        """
        output = self.transpile(ast)
        with open(path, "w", encoding="utf-8") as f:
            f.write(output)
