"""
TranspilerRegistry singleton for managing transpiler instances.

Provides a centralized registry mapping TranspileTarget to Transpiler
instances, supporting both built-in and user-registered transpilers.
"""

from typing import Dict, Optional, Type, Callable
import threading

from yuho.transpile.base import TranspileTarget, TranspilerBase


class TranspilerRegistry:
    """
    Singleton registry mapping TranspileTarget to Transpiler instances.

    Provides lazy instantiation of transpilers and supports registration
    of custom transpilers.

    Usage:
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.JSON)
        output = transpiler.transpile(ast)

        # Register custom transpiler
        registry.register(MyCustomTarget, MyCustomTranspiler)

    Thread Safety:
        The registry is thread-safe for both reading and registration.
    """

    _instance: Optional["TranspilerRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "TranspilerRegistry":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the registry with built-in transpilers."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            # Registry maps target -> transpiler class
            self._registry: Dict[TranspileTarget, Type[TranspilerBase]] = {}
            # Cache of instantiated transpilers
            self._instances: Dict[TranspileTarget, TranspilerBase] = {}
            # Factory functions for custom creation
            self._factories: Dict[TranspileTarget, Callable[[], TranspilerBase]] = {}

            # Register built-in transpilers lazily
            self._register_builtins()
            self._initialized = True

    def _register_builtins(self) -> None:
        """Register all built-in transpilers."""
        # Import lazily to avoid circular imports
        from yuho.transpile.json_transpiler import JSONTranspiler
        from yuho.transpile.jsonld_transpiler import JSONLDTranspiler
        from yuho.transpile.english_transpiler import EnglishTranspiler
        from yuho.transpile.latex_transpiler import LaTeXTranspiler
        from yuho.transpile.mermaid_transpiler import MermaidTranspiler
        from yuho.transpile.alloy_transpiler import AlloyTranspiler
        from yuho.transpile.graphql_transpiler import GraphQLTranspiler
        from yuho.transpile.blocks_transpiler import BlocksTranspiler

        self._registry[TranspileTarget.JSON] = JSONTranspiler
        self._registry[TranspileTarget.JSON_LD] = JSONLDTranspiler
        self._registry[TranspileTarget.ENGLISH] = EnglishTranspiler
        self._registry[TranspileTarget.LATEX] = LaTeXTranspiler
        self._registry[TranspileTarget.MERMAID] = MermaidTranspiler
        self._registry[TranspileTarget.ALLOY] = AlloyTranspiler
        self._registry[TranspileTarget.GRAPHQL] = GraphQLTranspiler
        self._registry[TranspileTarget.BLOCKS] = BlocksTranspiler

    @classmethod
    def instance(cls) -> "TranspilerRegistry":
        """
        Get the singleton instance of the registry.

        Returns:
            The global TranspilerRegistry instance.
        """
        return cls()

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance (primarily for testing).

        Clears all registered transpilers and cached instances.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance._registry.clear()
                cls._instance._instances.clear()
                cls._instance._factories.clear()
                cls._instance._initialized = False
                cls._instance = None

    def get(self, target: TranspileTarget) -> TranspilerBase:
        """
        Get a transpiler instance for the given target.

        Instances are cached for reuse. If no transpiler is registered
        for the target, raises KeyError.

        Args:
            target: The transpilation target.

        Returns:
            A transpiler instance for the target.

        Raises:
            KeyError: If no transpiler is registered for the target.
        """
        # Check cache first
        if target in self._instances:
            return self._instances[target]

        with self._lock:
            # Double-check after acquiring lock
            if target in self._instances:
                return self._instances[target]

            # Check for factory function
            if target in self._factories:
                instance = self._factories[target]()
                self._instances[target] = instance
                return instance

            # Check for registered class
            if target in self._registry:
                instance = self._registry[target]()
                self._instances[target] = instance
                return instance

            raise KeyError(f"No transpiler registered for target: {target}")

    def get_or_none(self, target: TranspileTarget) -> Optional[TranspilerBase]:
        """
        Get a transpiler instance, returning None if not registered.

        Args:
            target: The transpilation target.

        Returns:
            A transpiler instance, or None if not registered.
        """
        try:
            return self.get(target)
        except KeyError:
            return None

    def register(
        self,
        target: TranspileTarget,
        transpiler_class: Type[TranspilerBase],
    ) -> None:
        """
        Register a transpiler class for a target.

        Args:
            target: The transpilation target to register.
            transpiler_class: The transpiler class to instantiate.
        """
        with self._lock:
            self._registry[target] = transpiler_class
            # Clear cached instance to force re-creation
            self._instances.pop(target, None)

    def register_factory(
        self,
        target: TranspileTarget,
        factory: Callable[[], TranspilerBase],
    ) -> None:
        """
        Register a factory function for creating a transpiler.

        Useful when transpiler creation requires custom initialization.

        Args:
            target: The transpilation target to register.
            factory: A callable that returns a TranspilerBase instance.
        """
        with self._lock:
            self._factories[target] = factory
            # Clear cached instance to force re-creation
            self._instances.pop(target, None)

    def register_instance(
        self,
        target: TranspileTarget,
        instance: TranspilerBase,
    ) -> None:
        """
        Register a pre-created transpiler instance.

        Args:
            target: The transpilation target to register.
            instance: The transpiler instance to use.
        """
        with self._lock:
            self._instances[target] = instance

    def unregister(self, target: TranspileTarget) -> bool:
        """
        Remove a transpiler registration.

        Args:
            target: The target to unregister.

        Returns:
            True if a registration was removed, False otherwise.
        """
        with self._lock:
            removed = False
            if target in self._registry:
                del self._registry[target]
                removed = True
            if target in self._factories:
                del self._factories[target]
                removed = True
            if target in self._instances:
                del self._instances[target]
                removed = True
            return removed

    def is_registered(self, target: TranspileTarget) -> bool:
        """
        Check if a transpiler is registered for the target.

        Args:
            target: The target to check.

        Returns:
            True if a transpiler is registered.
        """
        return (
            target in self._registry
            or target in self._factories
            or target in self._instances
        )

    def registered_targets(self) -> list[TranspileTarget]:
        """
        Get all registered transpilation targets.

        Returns:
            List of registered TranspileTarget values.
        """
        targets = set(self._registry.keys())
        targets.update(self._factories.keys())
        targets.update(self._instances.keys())
        return list(targets)

    def clear_cache(self) -> None:
        """
        Clear all cached transpiler instances.

        Registered classes and factories are preserved.
        """
        with self._lock:
            self._instances.clear()
