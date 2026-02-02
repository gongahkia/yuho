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


# Regex pattern for strict semver validation (based on semver.org spec)
SEMVER_PATTERN = re.compile(
    r"^v?"  # Optional 'v' prefix
    r"(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


class SemverValidationError(Exception):
    """Raised when a version string is not valid semver."""
    pass


@dataclass
class SemverValidation:
    """Result of semver validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate_semver(version_str: str, strict: bool = True) -> SemverValidation:
    """
    Validate a version string against semver specification.

    Args:
        version_str: Version string to validate
        strict: If True, requires full semver compliance. If False, allows
                partial versions like "1.0" or "1".

    Returns:
        SemverValidation result with validity and any errors/warnings
    """
    errors = []
    warnings = []

    if not version_str:
        return SemverValidation(False, ["Version string is empty"])

    version_str = version_str.strip()

    # Check for strict semver compliance
    match = SEMVER_PATTERN.match(version_str)

    if match:
        # Valid semver
        if version_str.startswith("v"):
            warnings.append("Version has 'v' prefix (valid but not recommended)")
        return SemverValidation(True, [], warnings)

    if strict:
        errors.append(f"'{version_str}' is not valid semver format (expected X.Y.Z)")

        # Provide helpful hints
        parts = version_str.lstrip("v").split(".")
        if len(parts) < 3:
            errors.append(f"Missing components: semver requires MAJOR.MINOR.PATCH")
        elif len(parts) > 3 and "-" not in version_str and "+" not in version_str:
            errors.append(f"Too many version components")

        # Check for invalid characters
        if re.search(r"[^0-9a-zA-Z.\-+]", version_str.lstrip("v")):
            errors.append("Contains invalid characters")

        return SemverValidation(False, errors)

    # Non-strict mode: allow partial versions
    partial_pattern = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?")
    if partial_pattern.match(version_str):
        warnings.append(f"'{version_str}' is a partial version (not strict semver)")
        return SemverValidation(True, [], warnings)

    return SemverValidation(False, [f"'{version_str}' cannot be parsed as a version"])


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
    """Semantic version representation with full semver 2.0 support."""
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""  # Build metadata (ignored in comparisons per semver spec)

    @classmethod
    def parse(cls, version_str: str, validate: bool = False) -> "Version":
        """
        Parse version string like '1.2.3' or 'v1.2.3-alpha+build.123'.

        Args:
            version_str: Version string to parse
            validate: If True, raises SemverValidationError for invalid versions

        Returns:
            Parsed Version object

        Raises:
            SemverValidationError: If validate=True and version is invalid
        """
        if validate:
            result = validate_semver(version_str, strict=True)
            if not result.valid:
                raise SemverValidationError("; ".join(result.errors))

        v = version_str.strip().lstrip("v")
        prerelease = ""
        build = ""

        # Extract build metadata (after +)
        if "+" in v:
            v, build = v.split("+", 1)

        # Extract prerelease (after -)
        if "-" in v:
            v, prerelease = v.split("-", 1)

        parts = v.split(".")
        major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

        return cls(major, minor, patch, prerelease, build)

    @classmethod
    def is_valid(cls, version_str: str, strict: bool = True) -> bool:
        """
        Check if a version string is valid semver.

        Args:
            version_str: Version string to check
            strict: If True, requires full semver compliance

        Returns:
            True if valid semver
        """
        return validate_semver(version_str, strict).valid

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base = f"{base}-{self.prerelease}"
        if self.build:
            base = f"{base}+{self.build}"
        return base

    def to_tuple(self) -> Tuple[int, int, int, str]:
        """Return version as comparable tuple (excludes build metadata)."""
        return (self.major, self.minor, self.patch, self.prerelease)

    def _compare_prerelease(self, other: "Version") -> int:
        """
        Compare prerelease versions per semver spec.

        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        # No prerelease > prerelease (1.0.0 > 1.0.0-alpha)
        if not self.prerelease and other.prerelease:
            return 1
        if self.prerelease and not other.prerelease:
            return -1
        if self.prerelease == other.prerelease:
            return 0

        # Compare prerelease identifiers
        self_parts = self.prerelease.split(".")
        other_parts = other.prerelease.split(".")

        for s, o in zip(self_parts, other_parts):
            # Numeric identifiers < alphanumeric
            s_num = s.isdigit()
            o_num = o.isdigit()

            if s_num and o_num:
                if int(s) < int(o):
                    return -1
                if int(s) > int(o):
                    return 1
            elif s_num:
                return -1  # numeric < alphanumeric
            elif o_num:
                return 1
            else:
                if s < o:
                    return -1
                if s > o:
                    return 1

        # Longer prerelease > shorter (1.0.0-alpha.1 > 1.0.0-alpha)
        if len(self_parts) < len(other_parts):
            return -1
        if len(self_parts) > len(other_parts):
            return 1
        return 0

    def __lt__(self, other: "Version") -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        return self._compare_prerelease(other) < 0

    def __le__(self, other: "Version") -> bool:
        return self == other or self < other

    def __gt__(self, other: "Version") -> bool:
        return other < self

    def __ge__(self, other: "Version") -> bool:
        return self == other or self > other

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return False
        # Build metadata is ignored in equality per semver spec
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.prerelease))

    def is_compatible_with(self, other: "Version") -> bool:
        """
        Check if this version is backwards-compatible with another version.

        Per semver rules:
        - Same major version (>0) = compatible
        - Major version 0 = unstable, only same minor is compatible

        Args:
            other: Version to check compatibility with

        Returns:
            True if self is backwards-compatible with other
        """
        if self.major == 0 and other.major == 0:
            # 0.x.y versions: only same minor is compatible
            return self.minor == other.minor
        return self.major == other.major

    def is_breaking_change_from(self, other: "Version") -> bool:
        """
        Check if upgrading from other to self is a breaking change.

        Args:
            other: Previous version

        Returns:
            True if this version introduces breaking changes
        """
        if self <= other:
            return False  # Downgrade or same version
        if self.major == 0 and other.major == 0:
            # 0.x.y: minor bumps can be breaking
            return self.minor > other.minor
        return self.major > other.major

    def next_major(self) -> "Version":
        """Return next major version."""
        return Version(self.major + 1, 0, 0)

    def next_minor(self) -> "Version":
        """Return next minor version."""
        return Version(self.major, self.minor + 1, 0)

    def next_patch(self) -> "Version":
        """Return next patch version."""
        return Version(self.major, self.minor, self.patch + 1)


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


@dataclass
class CompatibilityResult:
    """Result of compatibility check between package versions."""
    compatible: bool
    breaking_changes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    upgrade_type: str = ""  # "major", "minor", "patch", "prerelease", "downgrade"


class CompatibilityChecker:
    """
    Checks version compatibility between packages.

    Enforces semver compatibility rules and detects breaking changes.
    """

    @staticmethod
    def check_upgrade(
        from_version: Version,
        to_version: Version,
        allow_major: bool = False,
    ) -> CompatibilityResult:
        """
        Check if upgrading between versions is compatible.

        Args:
            from_version: Current version
            to_version: Target version
            allow_major: If True, allow major version upgrades

        Returns:
            CompatibilityResult with compatibility status
        """
        breaking = []
        warnings = []

        # Determine upgrade type
        if to_version < from_version:
            upgrade_type = "downgrade"
            warnings.append(f"Downgrade from {from_version} to {to_version}")
        elif to_version.major > from_version.major:
            upgrade_type = "major"
        elif to_version.minor > from_version.minor:
            upgrade_type = "minor"
        elif to_version.patch > from_version.patch:
            upgrade_type = "patch"
        elif to_version.prerelease != from_version.prerelease:
            upgrade_type = "prerelease"
        else:
            upgrade_type = "none"

        # Check for breaking changes
        is_breaking = to_version.is_breaking_change_from(from_version)
        if is_breaking:
            if from_version.major == 0:
                breaking.append(
                    f"Minor version bump in 0.x series ({from_version} -> {to_version}) "
                    "may contain breaking changes"
                )
            else:
                breaking.append(
                    f"Major version bump ({from_version} -> {to_version}) "
                    "indicates breaking API changes"
                )

        compatible = not is_breaking or allow_major

        return CompatibilityResult(
            compatible=compatible,
            breaking_changes=breaking,
            warnings=warnings,
            upgrade_type=upgrade_type,
        )

    @staticmethod
    def check_constraint_compatibility(
        constraint1: VersionConstraint,
        constraint2: VersionConstraint,
    ) -> Tuple[bool, Optional[VersionConstraint]]:
        """
        Check if two version constraints can be satisfied simultaneously.

        Args:
            constraint1: First constraint
            constraint2: Second constraint

        Returns:
            Tuple of (compatible, merged_constraint or None if incompatible)
        """
        # ANY matches everything
        if constraint1.op == ConstraintOp.ANY:
            return (True, constraint2)
        if constraint2.op == ConstraintOp.ANY:
            return (True, constraint1)

        # For exact matches, check if they're the same
        if constraint1.op == ConstraintOp.EQ and constraint2.op == ConstraintOp.EQ:
            if constraint1.version == constraint2.version:
                return (True, constraint1)
            return (False, None)

        # For one exact and one range, check if exact satisfies range
        if constraint1.op == ConstraintOp.EQ:
            if constraint2.satisfies(constraint1.version):
                return (True, constraint1)
            return (False, None)
        if constraint2.op == ConstraintOp.EQ:
            if constraint1.satisfies(constraint2.version):
                return (True, constraint2)
            return (False, None)

        # For two ranges, find intersection
        # This is a simplified check - returns the more restrictive constraint
        # A full implementation would compute the actual intersection
        v1, v2 = constraint1.version, constraint2.version

        # Check if there's any overlap by testing boundary versions
        test_versions = [v1, v2]
        if v1:
            test_versions.extend([v1.next_patch(), v1.next_minor(), v1.next_major()])
        if v2:
            test_versions.extend([v2.next_patch(), v2.next_minor(), v2.next_major()])

        for v in test_versions:
            if v and constraint1.satisfies(v) and constraint2.satisfies(v):
                # There's at least one satisfying version
                # Return the constraint with higher minimum
                if constraint1.version and constraint2.version:
                    if constraint1.version >= constraint2.version:
                        return (True, constraint1)
                    return (True, constraint2)
                return (True, constraint1)

        return (False, None)

    @staticmethod
    def find_compatible_versions(
        available: List[Version],
        constraints: List[VersionConstraint],
    ) -> List[Version]:
        """
        Find all versions that satisfy all constraints.

        Args:
            available: List of available versions
            constraints: List of constraints to satisfy

        Returns:
            List of compatible versions (sorted newest first)
        """
        compatible = []
        for v in available:
            if all(c.satisfies(v) for c in constraints):
                compatible.append(v)
        return sorted(compatible, reverse=True)


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
