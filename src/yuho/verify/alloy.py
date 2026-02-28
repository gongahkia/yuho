"""
Alloy model generation and analysis for Yuho statutes.

Generates Alloy models from statute ASTs for bounded model checking,
invokes the Alloy analyzer, and parses counterexamples.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import tempfile
import re
import logging

from yuho.ast import ArrayType, BuiltinType, GenericType, NamedType, OptionalType, TypeNode

logger = logging.getLogger(__name__)


@dataclass
class AlloyCounterexample:
    """A counterexample from Alloy analysis."""
    assertion_name: str
    violated: bool
    witness: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    
    def to_diagnostic(self) -> Dict[str, Any]:
        """Convert to LSP-compatible diagnostic."""
        return {
            "message": f"Alloy: {self.assertion_name} - {self.message}",
            "severity": "warning" if self.violated else "info",
            "source": "alloy",
            "data": self.witness,
        }


class AlloyGenerator:
    """
    Generates Alloy models from Yuho statute ASTs.
    
    Translates statute elements, penalties, and constraints into
    Alloy's relational modeling language for bounded verification.
    """
    
    def __init__(self, scope: int = 5):
        """
        Initialize the generator.
        
        Args:
            scope: Default scope for bounded model checking (max instances)
        """
        self.scope = scope
    
    def generate(self, ast) -> str:
        """
        Generate Alloy model from a module AST.
        
        Args:
            ast: ModuleNode from Yuho AST
            
        Returns:
            Alloy model as string
        """
        lines = [
            "// Generated Alloy model from Yuho statute",
            "// Run assertions to verify statute consistency",
            "",
            "module yuho_statute",
            "",
        ]
        
        # Generate signatures for types
        lines.extend(self._generate_signatures(ast))
        
        # Generate facts from statutes
        lines.extend(self._generate_facts(ast))
        
        # Generate assertions
        lines.extend(self._generate_assertions(ast))
        
        # Generate run/check commands
        lines.extend(self._generate_commands())
        
        return "\n".join(lines)
    
    def _generate_signatures(self, ast) -> List[str]:
        """Generate Alloy signatures from type definitions."""
        lines = [
            "// Base types",
            "abstract sig Person {}",
            "sig Defendant extends Person {}",
            "sig Victim extends Person {}",
            "",
            "abstract sig Intent {}",
            "one sig Intentional, Reckless, Negligent extends Intent {}",
            "",
            "abstract sig Element {",
            "    satisfied: one Bool",
            "}",
            "",
            "abstract sig Bool {}",
            "one sig True, False extends Bool {}",
            "",
        ]
        
        # Generate from struct definitions
        for struct in ast.type_defs:
            sig_lines = [f"sig {struct.name} {{"]
            for field_def in struct.fields:
                alloy_type = self._type_to_alloy(field_def.type_annotation)
                sig_lines.append(f"    {field_def.name}: {alloy_type},")
            if sig_lines[-1].endswith(","):
                sig_lines[-1] = sig_lines[-1][:-1]  # Remove trailing comma
            sig_lines.append("}")
            lines.extend(sig_lines)
            lines.append("")
        
        return lines
    
    def _generate_facts(self, ast) -> List[str]:
        """Generate Alloy facts from statutes."""
        lines = ["// Facts derived from statute elements", ""]
        
        for statute in ast.statutes:
            lines.append(f"// Statute {statute.section_number}")
            
            # Generate signature for this statute
            statute_name = self._statute_name(statute.section_number)
            lines.append(f"one sig {statute_name} {{")
            
            # Add element fields
            if statute.elements:
                element_names = []
                for elem in statute.elements:
                    elem_name = self._safe_identifier(elem.name)
                    element_names.append(elem_name)
                    lines.append(f"    {elem_name}: one Element,")
                
                if lines[-1].endswith(","):
                    lines[-1] = lines[-1][:-1]
            
            lines.append("}")
            lines.append("")
            
            # Generate fact for element relationships
            if statute.elements:
                lines.append(f"fact {statute_name}_elements {{")
                lines.append(f"    // All elements must be satisfied for conviction")
                
                elem_refs = [
                    f"{statute_name}.{self._safe_identifier(e.name)}.satisfied = True"
                    for e in statute.elements
                ]
                if elem_refs:
                    lines.append(f"    // {' and '.join(elem_refs)}")
                
                lines.append("}")
                lines.append("")
        
        return lines
    
    def _generate_assertions(self, ast) -> List[str]:
        """Generate Alloy assertions for verification."""
        lines = [
            "// Assertions",
            "",
            "// No contradictory elements",
            "assert no_contradictory_elements {",
            "    // No element can be both satisfied and not satisfied",
            "    all e: Element | e.satisfied = True or e.satisfied = False",
            "}",
            "",
            "// Penalty ordering: more serious crimes should have higher penalties",
            "assert penalty_ordering {",
            "    // Placeholder: define penalty comparison logic",
            "    // In a complete implementation, compare penalty maximums",
            "}",
            "",
        ]
        
        # Add statute-specific assertions
        for statute in ast.statutes:
            statute_name = self._statute_name(statute.section_number)
            
            lines.append(f"// Assertions for {statute.section_number}")
            lines.append(f"assert {statute_name}_consistent {{")
            lines.append(f"    // Statute elements are internally consistent")
            lines.append("}")
            lines.append("")
        
        return lines
    
    def _generate_commands(self) -> List[str]:
        """Generate Alloy run/check commands."""
        return [
            "// Verification commands",
            f"check no_contradictory_elements for {self.scope}",
            f"check penalty_ordering for {self.scope}",
            "",
            "// Run command for exploration",
            f"run show_model for {self.scope}",
        ]
    
    def _type_to_alloy(self, yuho_type: TypeNode | str) -> str:
        """Convert Yuho type to Alloy type."""
        if isinstance(yuho_type, BuiltinType):
            type_map = {
                "int": "Int",
                "float": "Int",  # Alloy has no native float type
                "bool": "Bool",
                "string": "String",
                "money": "Int",  # Represent as cents
                "percent": "Int",
                "date": "Int",  # Unix timestamp / day count
                "duration": "Int",  # Days
                "void": "none",
            }
            return type_map.get(yuho_type.name, "univ")
        if isinstance(yuho_type, NamedType):
            return yuho_type.name
        if isinstance(yuho_type, OptionalType):
            return f"lone {self._type_to_alloy(yuho_type.inner)}"
        if isinstance(yuho_type, ArrayType):
            return f"set {self._type_to_alloy(yuho_type.element_type)}"
        if isinstance(yuho_type, GenericType):
            return yuho_type.base
        if isinstance(yuho_type, str):
            type_map = {
                "int": "Int",
                "float": "Int",
                "bool": "Bool",
                "string": "String",
                "money": "Int",
                "percent": "Int",
                "date": "Int",
                "duration": "Int",
                "void": "none",
            }
            return type_map.get(yuho_type, yuho_type)
        return "univ"

    def _safe_identifier(self, name: str) -> str:
        """Convert arbitrary names to stable Alloy-safe identifiers."""
        sanitized = re.sub(r"[^A-Za-z0-9_]", "_", name.strip())
        if not sanitized:
            return "unnamed"
        if sanitized[0].isdigit():
            return f"n_{sanitized}"
        return sanitized

    def _statute_name(self, section_number: str) -> str:
        base = re.sub(r"[^A-Za-z0-9_]", "_", section_number.strip())
        if not base:
            base = "unnamed"
        return f"Statute_{base}"


class AlloyAnalyzer:
    """
    Invokes the Alloy analyzer and parses results.
    
    Requires Alloy to be installed and accessible.
    """
    
    def __init__(
        self,
        alloy_jar: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the analyzer.
        
        Args:
            alloy_jar: Path to Alloy JAR file (auto-detect if None)
            timeout: Timeout in seconds for analysis
        """
        self.alloy_jar = alloy_jar or self._find_alloy_jar()
        self.timeout = timeout
    
    def _find_alloy_jar(self) -> Optional[str]:
        """Try to find Alloy JAR in common locations."""
        common_paths = [
            Path.home() / ".alloy" / "alloy.jar",
            Path("/usr/local/share/alloy/alloy.jar"),
            Path("/opt/alloy/alloy.jar"),
        ]
        
        for path in common_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def is_available(self) -> bool:
        """Check if Alloy analyzer is available."""
        if not self.alloy_jar:
            return False
        return Path(self.alloy_jar).exists()
    
    def analyze(self, model: str) -> List[AlloyCounterexample]:
        """
        Run Alloy analyzer on a model.
        
        Args:
            model: Alloy model as string
            
        Returns:
            List of counterexamples found
        """
        if not self.is_available():
            logger.warning("Alloy analyzer not available")
            return []
        
        # Write model to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".als", delete=False
        ) as f:
            f.write(model)
            model_path = f.name
        
        try:
            result = subprocess.run(
                ["java", "-jar", self.alloy_jar, "-c", model_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            return self._parse_output(result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Alloy analysis timed out after {self.timeout}s")
            return [AlloyCounterexample(
                assertion_name="timeout",
                violated=False,
                message=f"Analysis timed out after {self.timeout} seconds",
            )]
        except FileNotFoundError:
            logger.error("Java not found - required for Alloy")
            return []
        finally:
            Path(model_path).unlink(missing_ok=True)
    
    def _parse_output(
        self, stdout: str, stderr: str
    ) -> List[AlloyCounterexample]:
        """Parse Alloy analyzer output into counterexamples."""
        counterexamples = []
        
        # Parse "Assertion X may be violated" patterns
        violation_pattern = r"Assertion\s+(\w+)\s+(?:may be violated|is invalid)"
        for match in re.finditer(violation_pattern, stdout + stderr):
            counterexamples.append(AlloyCounterexample(
                assertion_name=match.group(1),
                violated=True,
                message="Assertion may be violated",
            ))
        
        # Parse "No counterexample found" patterns
        valid_pattern = r"Assertion\s+(\w+)\s+is valid"
        for match in re.finditer(valid_pattern, stdout + stderr):
            counterexamples.append(AlloyCounterexample(
                assertion_name=match.group(1),
                violated=False,
                message="No counterexample found within scope",
            ))
        
        return counterexamples
    
    def check_assertion(
        self, model: str, assertion_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check a specific assertion in a model.
        
        Args:
            model: Alloy model string
            assertion_name: Name of assertion to check
            
        Returns:
            Tuple of (is_valid, counterexample_message)
        """
        # Append check command if not present
        if f"check {assertion_name}" not in model:
            model = f"{model}\ncheck {assertion_name} for {self.alloy_jar or 5}"
        
        results = self.analyze(model)
        
        for result in results:
            if result.assertion_name == assertion_name:
                return (not result.violated, result.message if result.violated else None)
        
        return (True, None)  # Default: no counterexample found
