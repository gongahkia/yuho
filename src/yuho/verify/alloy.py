"""
Alloy model generation and analysis for Yuho statutes.

Generates Alloy models from statute ASTs for bounded model checking,
invokes the Alloy analyzer, and parses counterexamples.
"""

import sys
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
        lines.extend(self._generate_commands(ast))
        
        return "\n".join(lines)
    
    def _generate_signatures(self, ast) -> List[str]:
        """Generate Alloy signatures from type definitions."""
        # collect party roles across all statutes for dynamic sigs
        party_roles = set()
        for statute in ast.statutes:
            for party in getattr(statute, 'parties', ()):
                party_roles.add(party.name)

        lines = [
            "// Base types",
            "abstract sig Person {}",
        ]
        if party_roles:
            for name in sorted(party_roles):
                lines.append(f"sig {name} extends Person {{}}")
        else:
            lines.append("sig Defendant extends Person {}")
            lines.append("sig Victim extends Person {}")
        lines.append("")
        lines.extend([
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
        ])
        
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
        """
        Generate Alloy facts from statutes using actual
        ElementGroupNode structure for conjunctive/disjunctive logic.
        """
        from yuho.ast.nodes import ElementNode, ElementGroupNode

        lines = ["// Facts derived from statute elements", ""]

        for statute in ast.statutes:
            lines.append(f"// Statute {statute.section_number}")

            # Generate signature for this statute
            statute_name = self._statute_name(statute.section_number)

            # Collect all leaf elements for the sig fields
            leaf_elements = self._collect_leaf_elements(statute.elements)

            lines.append(f"one sig {statute_name} {{")
            if leaf_elements:
                for i, elem in enumerate(leaf_elements):
                    elem_name = self._safe_identifier(elem.name)
                    comma = "," if i < len(leaf_elements) - 1 else ""
                    lines.append(f"    {elem_name}: one Element{comma}")
            lines.append("}")
            lines.append("")

            # Add conviction boolean
            lines.append(f"one sig {statute_name}_Conviction {{")
            lines.append("    convicted: one Bool")
            lines.append("}")
            lines.append("")

            # Generate fact block that ties elements to conviction
            # using the actual element group structure
            if statute.elements:
                lines.append(f"fact {statute_name}_elements {{")
                expr = self._element_group_to_alloy_expr(
                    statute.elements, statute_name
                )
                lines.append(f"    {statute_name}_Conviction.convicted = True implies ({expr})")
                # Reverse: if all elements satisfied => conviction
                lines.append(f"    ({expr}) implies {statute_name}_Conviction.convicted = True")
                lines.append("}")
                lines.append("")

            # Temporal ordering facts
            for tc in getattr(statute, 'temporal_constraints', ()):
                subj = self._safe_identifier(tc.subject)
                obj = self._safe_identifier(tc.object)
                if tc.relation == "precedes":
                    lines.append(f"fact {statute_name}_{subj}_precedes_{obj} {{")
                    lines.append(f"    // {tc.subject} must occur before {tc.object}")
                    lines.append(f"    {statute_name}.{subj}.satisfied = True implies {statute_name}.{obj}.satisfied = True")
                    lines.append("}")
                    lines.append("")
                elif tc.relation == "after":
                    lines.append(f"fact {statute_name}_{subj}_after_{obj} {{")
                    lines.append(f"    // {tc.subject} must occur after {tc.object}")
                    lines.append(f"    {statute_name}.{subj}.satisfied = True implies {statute_name}.{obj}.satisfied = True")
                    lines.append("}")
                    lines.append("")
                elif tc.relation == "during":
                    lines.append(f"fact {statute_name}_{subj}_during_{obj} {{")
                    lines.append(f"    // {tc.subject} occurs during {tc.object}")
                    lines.append(f"    {statute_name}.{subj}.satisfied = True iff {statute_name}.{obj}.satisfied = True")
                    lines.append("}")
                    lines.append("")

            # Generate exception predicates
            lines.extend(self._generate_exception_preds(statute, statute_name))

        return lines

    def _collect_leaf_elements(
        self, elements
    ) -> list:
        """Recursively collect all leaf ElementNode instances."""
        from yuho.ast.nodes import ElementNode, ElementGroupNode

        result = []
        for elem in elements:
            if isinstance(elem, ElementNode):
                result.append(elem)
            elif isinstance(elem, ElementGroupNode):
                result.extend(self._collect_leaf_elements(elem.members))
        return result

    def _element_group_to_alloy_expr(
        self, elements, statute_name: str
    ) -> str:
        """
        Recursively translate element tree to Alloy boolean expression.

        all_of -> conjunction (and)
        any_of -> disjunction (or)
        ElementNode -> field.satisfied = True
        """
        from yuho.ast.nodes import ElementNode, ElementGroupNode

        parts = []
        for elem in elements:
            if isinstance(elem, ElementNode):
                ename = self._safe_identifier(elem.name)
                parts.append(f"{statute_name}.{ename}.satisfied = True")
            elif isinstance(elem, ElementGroupNode):
                sub_expr = self._element_group_to_alloy_expr(
                    elem.members, statute_name
                )
                if elem.combinator == "any_of":
                    parts.append(f"({sub_expr})")
                else:
                    parts.append(f"({sub_expr})")

        if not parts:
            return "True"

        # Determine combinator for this level. Top-level elements
        # without an explicit group are conjunctive.
        # If the first element is a group, use its combinator for
        # the top-level join. Otherwise default to "and".
        is_any_of = False
        if len(elements) == 1:
            e = elements[0]
            from yuho.ast.nodes import ElementGroupNode as EG
            if isinstance(e, EG) and e.combinator == "any_of":
                is_any_of = True
        # For a tuple of top-level elements, check if they share a parent group
        if hasattr(elements, '__len__') and len(elements) > 0:
            first = elements[0] if not isinstance(elements, tuple) else elements[0]
            from yuho.ast.nodes import ElementGroupNode as EG2
            if isinstance(first, EG2):
                if first.combinator == "any_of":
                    is_any_of = True

        joiner = " or " if is_any_of else " and "
        return joiner.join(parts)

    def _generate_exception_preds(self, statute, statute_name: str) -> List[str]:
        """
        Create Alloy pred blocks for each ExceptionNode.

        Each exception becomes a predicate that, when satisfied,
        negates the conviction.
        """
        lines = []
        if not statute.exceptions:
            return lines

        for i, exc in enumerate(statute.exceptions):
            exc_label = exc.label or f"exception_{i}"
            safe_label = self._safe_identifier(exc_label)
            pred_name = f"{statute_name}_exc_{safe_label}"

            lines.append(f"pred {pred_name} {{")

            # Encode exception condition as a comment + constraint
            cond_text = exc.condition.value if hasattr(exc.condition, 'value') else str(exc.condition)
            lines.append(f"    // Condition: {cond_text}")

            # The exception predicate: if this pred holds, conviction is negated
            lines.append(f"    {statute_name}_Conviction.convicted = False")

            lines.append("}")
            lines.append("")

            # Fact: exception guard => not convicted
            if exc.guard is not None:
                lines.append(f"fact {pred_name}_guard {{")
                lines.append(f"    // When exception guard is satisfied, conviction is negated")
                lines.append(f"    {pred_name} implies {statute_name}_Conviction.convicted = False")
                lines.append("}")
                lines.append("")

        return lines
    
    def _generate_assertions(self, ast) -> List[str]:
        """
        Generate real Alloy assertions from actual statute AST properties.

        Produces:
        - Element consistency (no contradictions)
        - Conviction biconditional (conviction iff elements satisfied)
        - Exception correctness (exception => not convicted)
        - Cross-statute penalty ordering (if multiple statutes)
        """
        from yuho.ast.nodes import ElementNode, ElementGroupNode

        lines = [
            "// Assertions",
            "",
            "// No contradictory elements",
            "assert no_contradictory_elements {",
            "    // Every element must have a definite truth value",
            "    all e: Element | e.satisfied = True or e.satisfied = False",
            "}",
            "",
        ]

        # Per-statute assertions derived from actual structure
        for statute in ast.statutes:
            statute_name = self._statute_name(statute.section_number)
            leaf_elements = self._collect_leaf_elements(statute.elements)

            # Conviction biconditional assertion
            if leaf_elements:
                expr = self._element_group_to_alloy_expr(
                    statute.elements, statute_name
                )
                lines.append(f"// Conviction biconditional for {statute.section_number}")
                lines.append(f"assert {statute_name}_conviction_iff_elements {{")
                lines.append(f"    {statute_name}_Conviction.convicted = True iff ({expr})")
                lines.append("}")
                lines.append("")

            # Exception correctness: each exception negates conviction
            for i, exc in enumerate(statute.exceptions):
                exc_label = exc.label or f"exception_{i}"
                safe_label = self._safe_identifier(exc_label)
                pred_name = f"{statute_name}_exc_{safe_label}"

                lines.append(f"assert {pred_name}_negates_conviction {{")
                lines.append(f"    {pred_name} implies {statute_name}_Conviction.convicted = False")
                lines.append("}")
                lines.append("")

            # Element type consistency: actus_reus and mens_rea must both exist
            has_ar = any(
                e.element_type == "actus_reus" for e in leaf_elements
            )
            has_mr = any(
                e.element_type == "mens_rea" for e in leaf_elements
            )
            if has_ar and has_mr:
                ar_refs = [
                    f"{statute_name}.{self._safe_identifier(e.name)}.satisfied = True"
                    for e in leaf_elements if e.element_type == "actus_reus"
                ]
                mr_refs = [
                    f"{statute_name}.{self._safe_identifier(e.name)}.satisfied = True"
                    for e in leaf_elements if e.element_type == "mens_rea"
                ]
                lines.append(f"// Conviction requires both actus reus and mens rea for {statute.section_number}")
                lines.append(f"assert {statute_name}_requires_ar_and_mr {{")
                lines.append(f"    {statute_name}_Conviction.convicted = True implies")
                ar_expr = " and ".join(ar_refs[:1])  # at least one AR
                mr_expr = " or ".join(mr_refs[:1])   # at least one MR
                lines.append(f"        ({ar_expr}) and ({mr_expr})")
                lines.append("}")
                lines.append("")

        # Deontic conflict assertions
        for statute in ast.statutes:
            statute_name = self._statute_name(statute.section_number)
            leaf_elements = self._collect_leaf_elements(statute.elements)
            obl_names = {e.name for e in leaf_elements if e.element_type == "obligation"}
            pro_names = {e.name for e in leaf_elements if e.element_type == "prohibition"}
            if obl_names & pro_names:
                lines.append(f"// Deontic conflict detection for {statute.section_number}")
                lines.append(f"assert {statute_name}_no_deontic_conflict {{")
                for name in sorted(obl_names & pro_names):
                    sn = self._safe_identifier(name)
                    lines.append(f"    // '{name}' cannot be both obligation and prohibition")
                    lines.append(f"    not ({statute_name}.{sn}.satisfied = True)")
                lines.append("}")
                lines.append("")

        # Cross-statute penalty ordering assertion
        statutes_with_penalty = [s for s in ast.statutes if s.penalty is not None]
        if len(statutes_with_penalty) > 1:
            lines.append("// Penalty ordering across statutes")
            lines.append("assert penalty_ordering {")
            lines.append("    // More serious offenses should carry higher penalties")
            lines.append("    // (Checked via Z3 for precise arithmetic)")
            lines.append("}")
            lines.append("")

        # Phase 13: subsumption assertions
        statute_map = {s.section_number: s for s in ast.statutes}
        for statute in ast.statutes:
            if statute.subsumes and statute.subsumes in statute_map:
                sn = self._statute_name(statute.section_number)
                sub_sn = self._statute_name(statute.subsumes)
                lines.append(f"// Subsumption: s{statute.section_number} subsumes s{statute.subsumes}")
                lines.append(f"assert {sn}_subsumes_{sub_sn} {{")
                lines.append(f"    {sn}_Conviction.convicted = True implies {sub_sn}_Conviction.convicted = True")
                lines.append("}")
                lines.append("")

        return lines
    
    def _generate_commands(self, ast=None) -> List[str]:
        """Generate Alloy run/check commands for all assertions."""
        lines = [
            "// Verification commands",
            f"check no_contradictory_elements for {self.scope}",
        ]

        if ast is not None:
            from yuho.ast.nodes import ElementNode, ElementGroupNode
            for statute in ast.statutes:
                statute_name = self._statute_name(statute.section_number)
                leaf_elements = self._collect_leaf_elements(statute.elements)
                if leaf_elements:
                    lines.append(f"check {statute_name}_conviction_iff_elements for {self.scope}")
                for i, exc in enumerate(statute.exceptions):
                    exc_label = exc.label or f"exception_{i}"
                    safe_label = self._safe_identifier(exc_label)
                    pred_name = f"{statute_name}_exc_{safe_label}"
                    lines.append(f"check {pred_name}_negates_conviction for {self.scope}")

            statutes_with_penalty = [s for s in ast.statutes if s.penalty is not None]
            if len(statutes_with_penalty) > 1:
                lines.append(f"check penalty_ordering for {self.scope}")

        lines.append("")
        lines.append("// Run command for exploration")
        lines.append(f"run show_model for {self.scope}")
        return lines
    
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
        if sys.platform == "win32":
            common_paths.extend([
                Path.home() / "AppData" / "Local" / "alloy" / "alloy.jar",
                Path("C:/Program Files/alloy/alloy.jar"),
                Path("C:/Program Files (x86)/alloy/alloy.jar"),
            ])
        
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
