"""
Yuho verify module - formal verification with Alloy and Z3.

Provides:
- Alloy model generation from statute AST
- Alloy analyzer integration for bounded model checking
- Z3 constraint generation and satisfiability checking
- Z3 constraint generation from AST (parallel to Alloy)
- Combined Alloy+Z3 verification with cross-validation
- Counterexample parsing and diagnostic generation
"""

from yuho.verify.alloy import (
    AlloyGenerator,
    AlloyAnalyzer,
    AlloyCounterexample,
)
from yuho.verify.z3_solver import (
    Z3Solver,
    Z3Generator,
    Z3Diagnostic,
    Z3CounterexampleExtractor,
    ConstraintGenerator,
    SatisfiabilityResult,
)
from yuho.verify.combined import (
    CombinedVerifier,
    CombinedVerificationResult,
)

__all__ = [
    "AlloyGenerator",
    "AlloyAnalyzer",
    "AlloyCounterexample",
    "Z3Solver",
    "Z3Generator",
    "Z3Diagnostic",
    "Z3CounterexampleExtractor",
    "ConstraintGenerator",
    "SatisfiabilityResult",
    "CombinedVerifier",
    "CombinedVerificationResult",
]
