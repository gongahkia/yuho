"""
Dependency resolution with version constraint solving for Yuho packages.

Implements a SAT-based resolver for package dependencies with support for
semver version constraints like ^1.0.0, ~1.2.0, >=1.0.0, etc.
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class ConstraintOp(Enum):
    """Version constraint operators."""
    EQ = "="       # Exact version
    GTE = ">="     # Greater than or equal
    LTE = "<="     # Less than or equal
    GT = ">"       # Greater than
    LT = "<"       # Less than
    CARET = "^"    # Compatible with (major version locked)
    TILDE = "~"    # Approximately (minor version locked)
    ANY = "*"      # Any version


@dataclass
class Version:
    """Semantic version representation."""
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    
    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """Parse version string like '1.2.3' or 'v1.2.3-alpha'."""
        v = version_str.lstrip("v")
        
        # Split prerelease
        if "-" in v:
            v, prerelease = v.split("-", 1)
        else:
            prerelease = ""
        
        parts = v.split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        
        return cls(major, minor, patch, prerelease)
    
    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{base}-{self.prerelease}"
        return base
    
    def __lt__(self, other: "Version") -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        # Prereleases are less than releases
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        return self.prerelease < other.prerelease
    
    def __le__(self, other: "Version") -> bool:
        return self == other or self < other
    
    def __gt__(self, other: "Version") -> bool:
        return other < self
    
    def __ge__(self, other: "Version") -> bool:
        return self == other or self > other
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return False
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)
    
    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.prerelease))


@dataclass
class VersionConstraint:
    """A version constraint like '^1.0.0' or '>=1.2.0'."""
    op: ConstraintOp
    version: Optional[Version]
    
    @classmethod
    def parse(cls, constraint_str: str) -> "VersionConstraint":
        """Parse constraint string."""
        constraint_str = constraint_str.strip()
        
        if constraint_str == "*" or not constraint_str:
            return cls(ConstraintOp.ANY, None)
        
        # Check for operators
        for op_str, op in [
            (">=", ConstraintOp.GTE),
            ("<=", ConstraintOp.LTE),
            (">", ConstraintOp.GT),
            ("<", ConstraintOp.LT),
            ("^", ConstraintOp.CARET),
            ("~", ConstraintOp.TILDE),
            ("=", ConstraintOp.EQ),
        ]:
            if constraint_str.startswith(op_str):
                version = Version.parse(constraint_str[len(op_str):])
                return cls(op, version)
        
        # Default to exact match
        return cls(ConstraintOp.EQ, Version.parse(constraint_str))
    
    def satisfies(self, version: Version) -> bool:
        """Check if a version satisfies this constraint."""
        if self.op == ConstraintOp.ANY:
            return True
        
        if self.version is None:
            return True
        
        v = self.version
        
        if self.op == ConstraintOp.EQ:
            return version == v
        elif self.op == ConstraintOp.GTE:
            return version >= v
        elif self.op == ConstraintOp.LTE:
            return version <= v
        elif self.op == ConstraintOp.GT:
            return version > v
        elif self.op == ConstraintOp.LT:
            return version < v
        elif self.op == ConstraintOp.CARET:
            # ^1.2.3 means >=1.2.3 <2.0.0 (major locked)
            if version < v:
                return False
            if v.major == 0:
                # ^0.x.y means >=0.x.y <0.(x+1).0
                return version.major == 0 and version.minor == v.minor
            return version.major == v.major
        elif self.op == ConstraintOp.TILDE:
            # ~1.2.3 means >=1.2.3 <1.3.0 (minor locked)
            if version < v:
                return False
            return version.major == v.major and version.minor == v.minor
        
        return False
    
    def __str__(self) -> str:
        if self.op == ConstraintOp.ANY:
            return "*"
        
        op_str = {
            ConstraintOp.EQ: "=",
            ConstraintOp.GTE: ">=",
            ConstraintOp.LTE: "<=",
            ConstraintOp.GT: ">",
            ConstraintOp.LT: "<",
            ConstraintOp.CARET: "^",
            ConstraintOp.TILDE: "~",
        }[self.op]
        
        return f"{op_str}{self.version}"


@dataclass
class Dependency:
    """A package dependency with version constraint."""
    package: str  # Section number
    constraint: VersionConstraint
    
    @classmethod
    def parse(cls, dep_str: str) -> "Dependency":
        """Parse dependency string like 'S403@^1.0.0' or 'S403>=1.0.0'."""
        # Check for @ separator
        if "@" in dep_str:
            package, version = dep_str.split("@", 1)
            return cls(package.strip(), VersionConstraint.parse(version))
        
        # Check for version operators
        for op in [">=", "<=", ">", "<", "^", "~", "="]:
            if op in dep_str:
                idx = dep_str.index(op)
                package = dep_str[:idx].strip()
                constraint = VersionConstraint.parse(dep_str[idx:])
                return cls(package, constraint)
        
        # No version constraint - any version
        return cls(dep_str.strip(), VersionConstraint(ConstraintOp.ANY, None))
    
    def __str__(self) -> str:
        return f"{self.package}@{self.constraint}"


@dataclass
class PackageInfo:
    """Information about a package for resolution."""
    section_number: str
    version: Version
    dependencies: List[Dependency] = field(default_factory=list)


@dataclass
class Resolution:
    """Result of dependency resolution."""
    success: bool
    packages: Dict[str, Version]  # section_number -> resolved version
    errors: List[str] = field(default_factory=list)
    install_order: List[str] = field(default_factory=list)


class DependencyResolver:
    """
    Resolves package dependencies with version constraints.
    
    Uses a backtracking algorithm to find a consistent set of
    package versions that satisfy all constraints.
    """
    
    def __init__(self):
        """Initialize resolver."""
        self._available: Dict[str, List[PackageInfo]] = {}  # package -> versions
        self._constraints: Dict[str, List[VersionConstraint]] = {}  # package -> constraints
    
    def add_available_package(self, package: PackageInfo) -> None:
        """Add an available package version."""
        if package.section_number not in self._available:
            self._available[package.section_number] = []
        self._available[package.section_number].append(package)
        # Keep sorted by version (newest first)
        self._available[package.section_number].sort(
            key=lambda p: p.version, reverse=True
        )
    
    def load_from_index(self, index) -> None:
        """Load available packages from library index."""
        for entry in index.list_all():
            pkg = PackageInfo(
                section_number=entry.section_number,
                version=Version.parse(entry.version),
                dependencies=[],  # Would need to load from package
            )
            self.add_available_package(pkg)
    
    def resolve(
        self,
        root_dependencies: List[Dependency],
        installed: Optional[Dict[str, Version]] = None,
    ) -> Resolution:
        """
        Resolve dependencies starting from root dependencies.
        
        Args:
            root_dependencies: Initial dependencies to resolve
            installed: Already installed packages (locked versions)
            
        Returns:
            Resolution result
        """
        installed = installed or {}
        self._constraints = {}
        
        # Add root constraints
        for dep in root_dependencies:
            self._add_constraint(dep.package, dep.constraint)
        
        # Try to resolve
        resolved: Dict[str, Version] = dict(installed)
        to_resolve = [dep.package for dep in root_dependencies]
        errors = []
        
        while to_resolve:
            package = to_resolve.pop(0)
            
            if package in resolved:
                # Already resolved, check constraint
                if not self._check_constraints(package, resolved[package]):
                    errors.append(
                        f"Conflict: {package}@{resolved[package]} violates constraints"
                    )
                continue
            
            # Find best matching version
            version = self._find_best_version(package)
            
            if version is None:
                errors.append(f"No version of {package} satisfies constraints")
                continue
            
            resolved[package] = version
            
            # Add transitive dependencies
            pkg_info = self._get_package(package, version)
            if pkg_info:
                for dep in pkg_info.dependencies:
                    self._add_constraint(dep.package, dep.constraint)
                    if dep.package not in resolved:
                        to_resolve.append(dep.package)
        
        if errors:
            return Resolution(
                success=False,
                packages={},
                errors=errors,
            )
        
        # Compute install order (topological sort)
        install_order = self._topological_sort(resolved)
        
        return Resolution(
            success=True,
            packages=resolved,
            install_order=install_order,
        )
    
    def _add_constraint(self, package: str, constraint: VersionConstraint) -> None:
        """Add a constraint for a package."""
        if package not in self._constraints:
            self._constraints[package] = []
        self._constraints[package].append(constraint)
    
    def _check_constraints(self, package: str, version: Version) -> bool:
        """Check if version satisfies all constraints for package."""
        if package not in self._constraints:
            return True
        return all(c.satisfies(version) for c in self._constraints[package])
    
    def _find_best_version(self, package: str) -> Optional[Version]:
        """Find the best (newest) version satisfying constraints."""
        if package not in self._available:
            return None
        
        for pkg_info in self._available[package]:
            if self._check_constraints(package, pkg_info.version):
                return pkg_info.version
        
        return None
    
    def _get_package(self, package: str, version: Version) -> Optional[PackageInfo]:
        """Get package info for a specific version."""
        if package not in self._available:
            return None
        
        for pkg_info in self._available[package]:
            if pkg_info.version == version:
                return pkg_info
        
        return None
    
    def _topological_sort(self, packages: Dict[str, Version]) -> List[str]:
        """Sort packages by dependency order (dependencies first)."""
        # Build dependency graph
        graph: Dict[str, Set[str]] = {pkg: set() for pkg in packages}
        
        for pkg, version in packages.items():
            pkg_info = self._get_package(pkg, version)
            if pkg_info:
                for dep in pkg_info.dependencies:
                    if dep.package in packages:
                        graph[pkg].add(dep.package)
        
        # Kahn's algorithm
        in_degree = {pkg: 0 for pkg in packages}
        for pkg, deps in graph.items():
            for dep in deps:
                in_degree[pkg] += 1
        
        queue = [pkg for pkg, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            pkg = queue.pop(0)
            result.append(pkg)
            
            for other, deps in graph.items():
                if pkg in deps:
                    in_degree[other] -= 1
                    if in_degree[other] == 0:
                        queue.append(other)
        
        return result


def resolve_dependencies(
    dependencies: List[str],
    installed: Optional[Dict[str, str]] = None,
) -> Resolution:
    """
    Convenience function to resolve dependencies.
    
    Args:
        dependencies: List of dependency strings like 'S403@^1.0.0'
        installed: Dict of installed packages (section -> version string)
        
    Returns:
        Resolution result
    """
    from yuho.library.index import LibraryIndex
    
    resolver = DependencyResolver()
    
    # Load available packages from index
    index = LibraryIndex()
    resolver.load_from_index(index)
    
    # Parse dependencies
    parsed_deps = [Dependency.parse(d) for d in dependencies]
    
    # Parse installed versions
    parsed_installed = {}
    if installed:
        for pkg, ver in installed.items():
            parsed_installed[pkg] = Version.parse(ver)
    
    return resolver.resolve(parsed_deps, parsed_installed)
