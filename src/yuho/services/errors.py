"""Typed boundary exceptions for parser, AST, and transpile interfaces."""

from __future__ import annotations

from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class ServiceBoundaryError(RuntimeError):
    """Base exception for failures crossing service boundaries."""

    boundary: str
    cause: Optional[BaseException]

    def __init__(
        self,
        boundary: str,
        message: str,
        *,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.boundary = boundary
        self.cause = cause


class ParserBoundaryError(ServiceBoundaryError):
    """Raised when parser operations fail at a boundary."""

    def __init__(self, message: str, *, cause: Optional[BaseException] = None) -> None:
        super().__init__("parser", message, cause=cause)


class ASTBoundaryError(ServiceBoundaryError):
    """Raised when AST builder operations fail at a boundary."""

    def __init__(self, message: str, *, cause: Optional[BaseException] = None) -> None:
        super().__init__("ast", message, cause=cause)


class TranspileBoundaryError(ServiceBoundaryError):
    """Raised when transpilation operations fail at a boundary."""

    def __init__(self, message: str, *, cause: Optional[BaseException] = None) -> None:
        super().__init__("transpile", message, cause=cause)


def run_parser_boundary(
    func: Callable[..., T],
    *args: Any,
    message: str = "Parser operation failed",
    **kwargs: Any,
) -> T:
    """Execute parser work and raise a typed boundary error on failure."""
    try:
        return func(*args, **kwargs)
    except ServiceBoundaryError:
        raise
    except Exception as exc:
        raise ParserBoundaryError(f"{message}: {exc}", cause=exc) from exc


def run_ast_boundary(
    func: Callable[..., T],
    *args: Any,
    message: str = "AST operation failed",
    **kwargs: Any,
) -> T:
    """Execute AST work and raise a typed boundary error on failure."""
    try:
        return func(*args, **kwargs)
    except ServiceBoundaryError:
        raise
    except Exception as exc:
        raise ASTBoundaryError(f"{message}: {exc}", cause=exc) from exc


def run_transpile_boundary(
    func: Callable[..., T],
    *args: Any,
    message: str = "Transpile operation failed",
    **kwargs: Any,
) -> T:
    """Execute transpile work and raise a typed boundary error on failure."""
    try:
        return func(*args, **kwargs)
    except ServiceBoundaryError:
        raise
    except Exception as exc:
        raise TranspileBoundaryError(f"{message}: {exc}", cause=exc) from exc
