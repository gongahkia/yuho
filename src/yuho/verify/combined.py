"""
Combined Alloy + Z3 verifier for cross-validation.

Runs both Alloy and Z3 verification and compares results
to provide higher confidence in verification outcomes.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import logging

from yuho.verify.alloy import AlloyGenerator, AlloyAnalyzer, AlloyCounterexample
from yuho.verify.z3_solver import Z3Solver, Z3Diagnostic

logger = logging.getLogger(__name__)


@dataclass
class CombinedVerificationResult:
    """Result of combined Alloy+Z3 verification."""
    
    alloy_available: bool
    z3_available: bool
    
    alloy_results: List[AlloyCounterexample]
    z3_results: List[Z3Diagnostic]
    
    agreement: bool  # True if both agree on consistency
    confidence: str  # "high", "medium", "low"
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "alloy_available": self.alloy_available,
            "z3_available": self.z3_available,
            "alloy_results": [r.__dict__ for r in self.alloy_results],
            "z3_results": [r.__dict__ for r in self.z3_results],
            "agreement": self.agreement,
            "confidence": self.confidence,
            "message": self.message,
        }


class CombinedVerifier:
    """
    Combined verifier using both Alloy and Z3.
    
    Provides higher confidence verification by running both
    solvers and comparing their results. Disagreements are
    flagged for manual review.
    """
    
    def __init__(
        self,
        alloy_jar: str | None = None,
        alloy_timeout: int = 30,
        z3_timeout_ms: int = 5000,
    ):
        """
        Initialize the combined verifier.
        
        Args:
            alloy_jar: Path to Alloy JAR (None to auto-detect)
            alloy_timeout: Alloy timeout in seconds
            z3_timeout_ms: Z3 timeout in milliseconds
        """
        self.alloy_analyzer = AlloyAnalyzer(alloy_jar, alloy_timeout)
        self.z3_solver = Z3Solver(z3_timeout_ms)
    
    def verify(self, ast) -> CombinedVerificationResult:
        """
        Run combined verification on AST.
        
        Args:
            ast: ModuleNode from Yuho AST
            
        Returns:
            CombinedVerificationResult with comparison
        """
        alloy_available = self.alloy_analyzer.is_available()
        z3_available = self.z3_solver.is_available()
        
        alloy_results = []
        z3_results = []
        
        # Run Alloy verification if available
        if alloy_available:
            try:
                alloy_gen = AlloyGenerator()
                alloy_model = alloy_gen.generate(ast)
                alloy_results = self.alloy_analyzer.analyze(alloy_model)
            except Exception as e:
                logger.error(f"Alloy verification failed: {e}")
                alloy_available = False
        
        # Run Z3 verification if available
        if z3_available:
            try:
                is_consistent, z3_diags = self.z3_solver.check_statute_consistency(ast)
                z3_results = z3_diags
            except Exception as e:
                logger.error(f"Z3 verification failed: {e}")
                z3_available = False
        
        # Compare results
        agreement, confidence, message = self._compare_results(
            alloy_available, z3_available,
            alloy_results, z3_results
        )
        
        return CombinedVerificationResult(
            alloy_available=alloy_available,
            z3_available=z3_available,
            alloy_results=alloy_results,
            z3_results=z3_results,
            agreement=agreement,
            confidence=confidence,
            message=message,
        )
    
    def _compare_results(
        self,
        alloy_available: bool,
        z3_available: bool,
        alloy_results: List[AlloyCounterexample],
        z3_results: List[Z3Diagnostic],
    ) -> Tuple[bool, str, str]:
        """
        Compare Alloy and Z3 results.
        
        Returns:
            Tuple of (agreement, confidence, message)
        """
        # If neither available
        if not alloy_available and not z3_available:
            return (False, "low", "Neither Alloy nor Z3 available")
        
        # If only one available
        if not alloy_available:
            z3_passed = all(d.passed for d in z3_results)
            return (
                True,
                "medium",
                f"Z3 only: {'PASS' if z3_passed else 'FAIL'} ({len(z3_results)} checks)"
            )
        
        if not z3_available:
            alloy_failed = any(r.violated for r in alloy_results)
            return (
                True,
                "medium",
                f"Alloy only: {'FAIL' if alloy_failed else 'PASS'} ({len(alloy_results)} checks)"
            )
        
        # Both available - compare
        alloy_failed = any(r.violated for r in alloy_results)
        z3_failed = any(not d.passed for d in z3_results)
        
        if alloy_failed == z3_failed:
            # Agreement
            status = "FAIL" if alloy_failed else "PASS"
            return (
                True,
                "high",
                f"Alloy and Z3 agree: {status} (Alloy: {len(alloy_results)}, Z3: {len(z3_results)} checks)"
            )
        else:
            # Disagreement
            return (
                False,
                "low",
                f"DISAGREEMENT: Alloy {'FAIL' if alloy_failed else 'PASS'}, "
                f"Z3 {'FAIL' if z3_failed else 'PASS'} - manual review required"
            )
    
    def verify_with_details(self, ast) -> Dict[str, Any]:
        """
        Run verification and return detailed results.
        
        Args:
            ast: ModuleNode from Yuho AST
            
        Returns:
            Detailed results dictionary
        """
        result = self.verify(ast)
        
        return {
            "summary": {
                "agreement": result.agreement,
                "confidence": result.confidence,
                "message": result.message,
            },
            "alloy": {
                "available": result.alloy_available,
                "results": [
                    {
                        "assertion": r.assertion_name,
                        "violated": r.violated,
                        "message": r.message,
                    }
                    for r in result.alloy_results
                ],
            },
            "z3": {
                "available": result.z3_available,
                "results": [
                    {
                        "check": r.check_name,
                        "passed": r.passed,
                        "message": r.message,
                        "counterexample": r.counterexample,
                    }
                    for r in result.z3_results
                ],
            },
        }
