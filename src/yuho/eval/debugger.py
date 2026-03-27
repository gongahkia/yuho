"""GDB-style interactive debugger for Yuho interpreter."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

from yuho.ast import nodes
from yuho.eval.interpreter import (
    Environment,
    Interpreter,
    InterpreterError,
    ReturnSignal,
    Value,
)


# ---------------------------------------------------------------------------
# Debugger data types
# ---------------------------------------------------------------------------


class StepMode(Enum):
    """Debugger execution mode."""

    RUN = auto()  # Run until breakpoint
    STEP = auto()  # Step into (stop at next statement-level node)
    NEXT = auto()  # Step over (stop at next statement in same or parent frame)
    CONTINUE = auto()  # Continue until next breakpoint
    FINISH = auto()  # Run until current function returns


@dataclass
class Breakpoint:
    """A debugger breakpoint."""

    id: int
    file: str = ""
    line: int = 0
    function: str = ""
    condition: str = ""
    enabled: bool = True
    hit_count: int = 0

    def matches(self, file: str, line: int, fn_name: str = "") -> bool:
        if not self.enabled:
            return False
        if self.function and fn_name == self.function:
            return True
        if self.line and line == self.line:
            if not self.file or file.endswith(self.file):
                return True
        return False

    def __str__(self) -> str:
        parts = [f"#{self.id}"]
        if self.function:
            parts.append(f"fn {self.function}")
        elif self.line:
            loc = f"{self.file}:" if self.file else ""
            parts.append(f"{loc}{self.line}")
        if self.condition:
            parts.append(f"if {self.condition}")
        if not self.enabled:
            parts.append("(disabled)")
        if self.hit_count:
            parts.append(f"hit {self.hit_count}x")
        return " ".join(parts)


@dataclass
class StackFrame:
    """A call stack frame."""

    function_name: str
    source_file: str
    line: int
    env: Environment

    def __str__(self) -> str:
        loc = f"{self.source_file}:{self.line}" if self.source_file else f"line {self.line}"
        return f"{self.function_name} at {loc}"


class DebuggerPause(Exception):
    """Raised when the debugger needs to pause execution for user input."""

    def __init__(self, node: nodes.ASTNode, reason: str = ""):
        self.node = node
        self.reason = reason


# ---------------------------------------------------------------------------
# Node classification helpers
# ---------------------------------------------------------------------------

# Node types that represent "statements" -- things you'd want to step through.
# Excludes literals, types, patterns, and other non-steppable leaf nodes.
_STEPPABLE_TYPES = (
    nodes.VariableDecl,
    nodes.AssignmentStmt,
    nodes.ReturnStmt,
    nodes.AssertStmt,
    nodes.ExpressionStmt,
    nodes.FunctionCallNode,
    nodes.MatchExprNode,
    nodes.Block,
)


def _is_steppable(node: nodes.ASTNode) -> bool:
    """Check if a node represents a statement-level construct worth stopping at."""
    return isinstance(node, _STEPPABLE_TYPES)


def _node_line(node: nodes.ASTNode) -> int:
    """Get the source line for a node, or 0 if unknown."""
    if node.source_location:
        return node.source_location.line
    return 0


def _node_file(node: nodes.ASTNode) -> str:
    """Get the source file for a node."""
    if node.source_location:
        return node.source_location.file or ""
    return ""


# ---------------------------------------------------------------------------
# DebugInterpreter
# ---------------------------------------------------------------------------


class DebugInterpreter(Interpreter):
    """Interpreter subclass with breakpoint and stepping support.

    The debugger intercepts ``visit()`` calls. When a breakpoint or step
    condition is met, it raises ``DebuggerPause`` so the REPL can present
    the interactive debugger prompt.
    """

    def __init__(self, env: Optional[Environment] = None):
        super().__init__(env)
        self.env: Environment
        self.breakpoints: List[Breakpoint] = []
        self._bp_counter = 0
        self.call_stack: List[StackFrame] = []
        self.mode = StepMode.RUN
        self._step_frame_depth: int = 0  # depth when NEXT was issued
        self._source_lines: Dict[str, List[str]] = {}
        self._watchpoints: Dict[str, Optional[Value]] = {}  # var name -> last seen value
        self._paused_node: Optional[nodes.ASTNode] = None
        self._last_listed_line: int = 0  # for 'list' continuation

    # -- breakpoint management ----------------------------------------------

    def add_breakpoint(
        self,
        line: int = 0,
        function: str = "",
        file: str = "",
        condition: str = "",
    ) -> Breakpoint:
        self._bp_counter += 1
        bp = Breakpoint(
            id=self._bp_counter,
            file=file,
            line=line,
            function=function,
            condition=condition,
        )
        self.breakpoints.append(bp)
        return bp

    def delete_breakpoint(self, bp_id: int) -> bool:
        for i, bp in enumerate(self.breakpoints):
            if bp.id == bp_id:
                self.breakpoints.pop(i)
                return True
        return False

    def toggle_breakpoint(self, bp_id: int) -> Optional[Breakpoint]:
        for bp in self.breakpoints:
            if bp.id == bp_id:
                bp.enabled = not bp.enabled
                return bp
        return None

    # -- watchpoints --------------------------------------------------------

    def add_watch(self, var_name: str) -> None:
        val = self.env.get(var_name)
        self._watchpoints[var_name] = val

    def remove_watch(self, var_name: str) -> bool:
        return self._watchpoints.pop(var_name, None) is not None

    def _check_watchpoints(self, node: nodes.ASTNode) -> Optional[str]:
        for name, old_val in list(self._watchpoints.items()):
            cur = self.env.get(name)
            if cur is None and old_val is None:
                continue
            if cur is None or old_val is None or cur.raw != old_val.raw:
                self._watchpoints[name] = cur
                old_repr = repr(old_val.raw) if old_val else "undefined"
                new_repr = repr(cur.raw) if cur else "undefined"
                return f"watchpoint: {name} changed: {old_repr} -> {new_repr}"
        return None

    # -- source cache -------------------------------------------------------

    def load_source(self, file: str, source: str) -> None:
        self._source_lines[file] = source.splitlines()

    def get_source_lines(
        self, file: str, center: int, radius: int = 5
    ) -> List[Tuple[int, str, bool]]:
        """Return (line_number, text, is_current) tuples around *center*."""
        lines = self._source_lines.get(file, [])
        if not lines:
            return []
        start = max(0, center - 1 - radius)
        end = min(len(lines), center + radius)
        return [(i + 1, lines[i], (i + 1) == center) for i in range(start, end)]

    # -- core: intercept visit() -------------------------------------------

    def visit(self, node: nodes.ASTNode) -> Any:
        if _is_steppable(node):
            self._maybe_pause(node)
        return super().visit(node)

    def _maybe_pause(self, node: nodes.ASTNode) -> None:
        """Check if we should pause at this node."""
        line = _node_line(node)
        file = _node_file(node)

        # Check breakpoints
        for bp in self.breakpoints:
            fn_name = self.call_stack[-1].function_name if self.call_stack else "<module>"
            if bp.matches(file, line, fn_name):
                if bp.condition:
                    try:
                        val = self._eval_condition(bp.condition)
                        if not val.is_truthy():
                            continue
                    except Exception:
                        continue
                bp.hit_count += 1
                self._paused_node = node
                raise DebuggerPause(node, f"breakpoint #{bp.id}")

        # Check watchpoints
        watch_msg = self._check_watchpoints(node)
        if watch_msg:
            self._paused_node = node
            raise DebuggerPause(node, watch_msg)

        # Check stepping mode
        depth = len(self.call_stack)
        if self.mode == StepMode.STEP:
            self._paused_node = node
            raise DebuggerPause(node, "step")
        if self.mode == StepMode.NEXT and depth <= self._step_frame_depth:
            self._paused_node = node
            raise DebuggerPause(node, "next")
        if self.mode == StepMode.FINISH and depth < self._step_frame_depth:
            self._paused_node = node
            raise DebuggerPause(node, "finish")

    def _eval_condition(self, expr_str: str) -> Value:
        """Evaluate a simple expression string in current environment."""
        from yuho.parser import get_parser
        from yuho.ast import ASTBuilder

        parser = get_parser()
        # Wrap in an assert so it becomes a valid top-level statement,
        # then extract the condition expression.
        wrapped = f"int _cond := {expr_str};"
        result = parser.parse(wrapped, "<condition>")
        if result.errors:
            raise InterpreterError(f"Bad condition expression: {expr_str}")
        if result.root_node is None:
            raise InterpreterError(f"Cannot build condition AST: {expr_str}")
        builder = ASTBuilder(wrapped, "<condition>")
        module = builder.build(result.root_node)
        if module.variables:
            val_node = module.variables[0].value
            if val_node:
                return Interpreter.visit(self, val_node)
        raise InterpreterError(f"Cannot parse condition: {expr_str}")

    # -- override function call to track call stack -------------------------

    def visit_function_call(self, node: nodes.FunctionCallNode) -> Value:
        # resolve callee name (duplicated from parent to push frame)
        if isinstance(node.callee, nodes.IdentifierNode):
            fn_name = node.callee.name
        elif isinstance(node.callee, nodes.FieldAccessNode):
            fn_name = node.callee.field_name
        else:
            fn_name = "<unknown>"

        fn_def = self.env.get_function_def(fn_name)
        if fn_def is None:
            raise InterpreterError(f"Undefined function '{fn_name}'", node)

        arg_vals = [self.visit(a) for a in node.args]
        if len(arg_vals) != len(fn_def.params):
            raise InterpreterError(
                f"Function '{fn_name}' expects {len(fn_def.params)} args, got {len(arg_vals)}",
                node,
            )

        call_env = self.env.child()
        for param, val in zip(fn_def.params, arg_vals):
            call_env.set(param.name, val)

        # push stack frame
        frame = StackFrame(
            function_name=fn_name,
            source_file=_node_file(fn_def),
            line=_node_line(fn_def),
            env=call_env,
        )
        self.call_stack.append(frame)

        saved = self.env
        self.env = call_env
        try:
            self.visit(fn_def.body)
        except ReturnSignal as rs:
            self.env = saved
            self.call_stack.pop()
            return rs.value
        except DebuggerPause:
            # Re-raise without popping or restoring env -- the frame
            # is still active and user needs to inspect local scope.
            raise
        self.env = saved
        self.call_stack.pop()
        return Value(None, "none")

    # -- evaluate expression in current scope (for 'print' command) ---------

    def eval_expr(self, expr_str: str) -> Value:
        """Parse and evaluate an expression string in the current environment."""
        from yuho.parser import get_parser
        from yuho.ast import ASTBuilder

        parser = get_parser()
        # Try as a bare identifier first
        val = self.env.get(expr_str.strip())
        if val is not None:
            return val

        # Parse as an expression via variable declaration wrapper
        wrapped = f"int _dbg := {expr_str};"
        result = parser.parse(wrapped, "<debug>")
        if result.errors:
            raise InterpreterError(f"Cannot parse: {expr_str}")
        if result.root_node is None:
            raise InterpreterError(f"Cannot build debug AST: {expr_str}")
        builder = ASTBuilder(wrapped, "<debug>")
        module = builder.build(result.root_node)
        if module.variables and module.variables[0].value:
            return Interpreter.visit(self, module.variables[0].value)
        raise InterpreterError(f"Cannot evaluate: {expr_str}")

    # -- scope inspection ---------------------------------------------------

    def get_locals(self) -> Dict[str, Value]:
        """Return bindings in the current (innermost) scope only."""
        return dict(self.env.bindings)

    def get_all_bindings(self) -> Dict[str, Value]:
        """Walk the scope chain and collect all visible bindings."""
        result: Dict[str, Value] = {}
        env: Optional[Environment] = self.env
        while env is not None:
            for k, v in env.bindings.items():
                if k not in result:
                    result[k] = v
            env = env.parent
        return result
