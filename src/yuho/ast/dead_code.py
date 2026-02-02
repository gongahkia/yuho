"""
Dead code elimination for Yuho AST.

Removes provably unreachable code branches:
- Match arms that can never be reached (covered by earlier patterns)
- Branches guarded by constant FALSE conditions
- Entire match expressions that reduce to a single arm
"""

from dataclasses import dataclass
from typing import List, Optional, Set

from yuho.ast import nodes
from yuho.ast.transformer import Transformer
from yuho.ast.constant_folder import ConstantFolder
from yuho.ast.reachability import ReachabilityChecker, ReachabilityResult
from yuho.ast.type_inference import TypeInferenceResult


@dataclass
class EliminationStats:
    """Statistics about eliminated dead code."""

    removed_match_arms: int = 0
    removed_true_guards: int = 0
    simplified_matches: int = 0

    @property
    def total_eliminations(self) -> int:
        return self.removed_match_arms + self.removed_true_guards + self.simplified_matches


class DeadCodeEliminator(Transformer):
    """
    AST transformer that removes provably unreachable branches.

    Performs the following optimizations:
    1. Removes match arms that are unreachable (covered by earlier patterns)
    2. Removes guards that are constant TRUE (simplifies to unguarded arm)
    3. Removes entire match expressions that have only one reachable arm
    4. Removes branches guarded by FALSE conditions (not yet if-exprs exist)

    Usage:
        eliminator = DeadCodeEliminator()
        optimized_ast = eliminator.transform(ast)
        print(f"Removed {eliminator.stats.total_eliminations} dead code items")

    Note:
        This transformer should typically be run after constant folding
        to maximize dead code detection.
    """

    def __init__(
        self,
        type_info: Optional[TypeInferenceResult] = None,
        *,
        fold_constants_first: bool = True,
    ):
        """
        Initialize the dead code eliminator.

        Args:
            type_info: Type inference result for better reachability analysis.
            fold_constants_first: If True, fold constants before elimination
                to maximize dead code detection.
        """
        self.type_info = type_info
        self.fold_constants_first = fold_constants_first
        self.stats = EliminationStats()
        self._constant_folder = ConstantFolder() if fold_constants_first else None

    def transform(self, node: nodes.ASTNode) -> nodes.ASTNode:
        """
        Transform the AST, eliminating dead code.

        If fold_constants_first is True, runs constant folding pass first.
        """
        if self._constant_folder:
            node = self._constant_folder.transform(node)
        return super().transform(node)

    def transform_match_expr(self, node: nodes.MatchExprNode) -> nodes.ASTNode:
        """
        Transform match expression, removing unreachable arms.

        1. Transform children first (recurse into arm bodies)
        2. Run reachability analysis
        3. Filter out unreachable arms
        4. If only one arm remains and it's a wildcard, simplify
        """
        # First, transform children (arm bodies, guards, etc.)
        node = super().transform_match_expr(node)

        # Run reachability check on this match
        checker = ReachabilityChecker(self.type_info)
        result = checker._check_match_reachability(node)

        # Get indices of unreachable arms
        unreachable_indices: Set[int] = {
            arm.arm_index for arm in result.unreachable_arms
        }

        # Filter and transform arms
        new_arms = []
        for i, arm in enumerate(node.arms):
            if i in unreachable_indices:
                self.stats.removed_match_arms += 1
                continue

            # Check if guard is constant TRUE - can remove guard
            new_arm = self._simplify_arm_guard(arm)
            new_arms.append(new_arm)

        # If no arms remain (shouldn't happen in valid code), return unchanged
        if not new_arms:
            return node

        # If only one arm remains and it's a wildcard, simplify to just the body
        if len(new_arms) == 1:
            single_arm = new_arms[0]
            if self._is_catch_all_arm(single_arm):
                self.stats.simplified_matches += 1
                # Return the body directly
                return single_arm.body

        # Check if arms changed
        if len(new_arms) != len(node.arms):
            return nodes.MatchExprNode(
                scrutinee=node.scrutinee,
                arms=tuple(new_arms),
                ensure_exhaustiveness=node.ensure_exhaustiveness,
                source_location=node.source_location,
            )

        return node

    def _simplify_arm_guard(self, arm: nodes.MatchArm) -> nodes.MatchArm:
        """
        Simplify arm guard if it's a constant TRUE.

        A guard that's always TRUE can be removed entirely.
        """
        if arm.guard is None:
            return arm

        # Check if guard is constant TRUE
        guard = arm.guard
        if self._constant_folder:
            guard = self._constant_folder.transform(guard)

        if isinstance(guard, nodes.BoolLit) and guard.value is True:
            self.stats.removed_true_guards += 1
            return nodes.MatchArm(
                pattern=arm.pattern,
                guard=None,  # Remove the always-true guard
                body=arm.body,
                source_location=arm.source_location,
            )

        # Guard is constant FALSE - this arm is dead
        # (but ReachabilityChecker should have caught this)

        return arm

    def _is_catch_all_arm(self, arm: nodes.MatchArm) -> bool:
        """
        Check if an arm is a catch-all (wildcard with no guard).

        A catch-all arm matches any value unconditionally.
        """
        if arm.guard is not None:
            return False

        pattern = arm.pattern
        return isinstance(pattern, (nodes.WildcardPattern, nodes.BindingPattern))


def eliminate_dead_code(
    ast: nodes.ASTNode,
    type_info: Optional[TypeInferenceResult] = None,
    **kwargs,
) -> nodes.ASTNode:
    """
    Convenience function to eliminate dead code from an AST.

    Args:
        ast: The AST to transform.
        type_info: Optional type inference result for better analysis.
        **kwargs: Options passed to DeadCodeEliminator constructor.

    Returns:
        A new AST with dead code eliminated.

    Example:
        from yuho.ast.dead_code import eliminate_dead_code
        optimized = eliminate_dead_code(parsed_ast)
    """
    eliminator = DeadCodeEliminator(type_info, **kwargs)
    return eliminator.transform(ast)
