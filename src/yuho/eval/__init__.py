"""Interpreter/evaluator engine for Yuho."""

from yuho.eval.interpreter import Interpreter, Environment, Value, StructInstance
from yuho.eval.statute_evaluator import (
    ApplicablePenalty,
    EvaluationResult,
    PenaltyDiagnostic,
    StatuteEvaluator,
)
from yuho.eval.defeasible import DefeasibleReasoner, DefeasibleResult
from yuho.eval.dependencies import DependencyDiagnostic, DependencyResult, DependencySubresult
from yuho.eval.outcomes import (
    CriminalOutcome,
    CriminalOutcomeKind,
    OutcomeDiagnostic,
    OutcomeSource,
    OutcomeTarget,
    SpecialDisposition,
)

__all__ = [
    "Interpreter",
    "Environment",
    "Value",
    "StructInstance",
    "StatuteEvaluator",
    "EvaluationResult",
    "ApplicablePenalty",
    "PenaltyDiagnostic",
    "DefeasibleReasoner",
    "DefeasibleResult",
    "DependencyDiagnostic",
    "DependencyResult",
    "DependencySubresult",
    "CriminalOutcome",
    "CriminalOutcomeKind",
    "OutcomeDiagnostic",
    "OutcomeSource",
    "OutcomeTarget",
    "SpecialDisposition",
]
