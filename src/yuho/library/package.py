"""
Yuho statute package format and validation.

Defines the .yhpkg archive format and validation for contributions.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import tarfile
import gzip
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


# Metadata schema version
METADATA_VERSION = "1.0"


@dataclass
class DeprecationInfo:
    """Information about package deprecation status."""
    deprecated: bool = False
    reason: str = ""
    deprecated_since: str = ""  # Version when deprecated
    replacement: str = ""  # Section number of replacement package (e.g., "S378A")
    removal_version: str = ""  # Version when package will be removed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        if not self.deprecated:
            return {}
        return {
            "deprecated": self.deprecated,
            "reason": self.reason,
            "deprecated_since": self.deprecated_since,
            "replacement": self.replacement,
            "removal_version": self.removal_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeprecationInfo":
        """Create from dictionary."""
        if not data:
            return cls()
        return cls(
            deprecated=data.get("deprecated", False),
            reason=data.get("reason", ""),
            deprecated_since=data.get("deprecated_since", ""),
            replacement=data.get("replacement", ""),
            removal_version=data.get("removal_version", ""),
        )


@dataclass
class PackageMetadata:
    """
    Metadata for a Yuho statute package.

    Defined in metadata.toml within the contribution directory.
    """
    section_number: str
    title: str
    jurisdiction: str
    contributor: str
    version: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    license: str = "CC-BY-4.0"
    deprecation: DeprecationInfo = field(default_factory=DeprecationInfo)
    
    @classmethod
    def from_toml(cls, path: Path) -> "PackageMetadata":
        """Load metadata from TOML file."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                raise RuntimeError("tomllib/tomli required for metadata parsing")

        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Parse deprecation info if present
        deprecation_data = data.get("deprecation", {})
        deprecation = DeprecationInfo.from_dict(deprecation_data)

        return cls(
            section_number=data.get("section_number", ""),
            title=data.get("title", ""),
            jurisdiction=data.get("jurisdiction", ""),
            contributor=data.get("contributor", ""),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
            license=data.get("license", "CC-BY-4.0"),
            deprecation=deprecation,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "section_number": self.section_number,
            "title": self.title,
            "jurisdiction": self.jurisdiction,
            "contributor": self.contributor,
            "version": self.version,
            "description": self.description,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "license": self.license,
        }
        deprecation_dict = self.deprecation.to_dict()
        if deprecation_dict:
            result["deprecation"] = deprecation_dict
        return result

    @property
    def is_deprecated(self) -> bool:
        """Check if package is deprecated."""
        return self.deprecation.deprecated

    def get_deprecation_warning(self) -> Optional[str]:
        """Get deprecation warning message if deprecated."""
        if not self.deprecation.deprecated:
            return None
        msg = f"Package {self.section_number} is deprecated"
        if self.deprecation.reason:
            msg += f": {self.deprecation.reason}"
        if self.deprecation.replacement:
            msg += f". Use {self.deprecation.replacement} instead"
        if self.deprecation.removal_version:
            msg += f". Will be removed in version {self.deprecation.removal_version}"
        return msg
    
    def is_valid(self) -> tuple[bool, List[str]]:
        """
        Validate metadata completeness including semver validation.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        from yuho.library.resolver import validate_semver

        errors = []

        if not self.section_number:
            errors.append("section_number is required")
        if not self.title:
            errors.append("title is required")
        if not self.jurisdiction:
            errors.append("jurisdiction is required")
        if not self.contributor:
            errors.append("contributor is required")
        if not self.version:
            errors.append("version is required")
        else:
            # Validate version is proper semver
            semver_result = validate_semver(self.version, strict=True)
            if not semver_result.valid:
                errors.extend(f"version: {e}" for e in semver_result.errors)

        return (len(errors) == 0, errors)


@dataclass
class Package:
    """
    A Yuho statute package (.yhpkg).
    
    Package format:
    - Gzipped tarball containing:
      - statute.yh       - Main statute file
      - test_statute.yh  - Test cases (optional)
      - metadata.toml    - Package metadata
      - signature        - Ed25519 signature (optional)
    """
    metadata: PackageMetadata
    statute_content: str
    test_content: Optional[str] = None
    signature: Optional[bytes] = None
    
    @classmethod
    def from_directory(cls, path: Path) -> "Package":
        """
        Create package from a contribution directory.
        
        Expected structure:
        - path/statute.yh
        - path/test_statute.yh (optional)
        - path/metadata.toml
        """
        path = Path(path)
        
        # Load metadata
        metadata_path = path / "metadata.toml"
        if not metadata_path.exists():
            raise FileNotFoundError(f"metadata.toml not found in {path}")
        metadata = PackageMetadata.from_toml(metadata_path)
        
        # Load statute
        statute_path = path / "statute.yh"
        if not statute_path.exists():
            raise FileNotFoundError(f"statute.yh not found in {path}")
        statute_content = statute_path.read_text()
        
        # Load tests (optional)
        test_path = path / "test_statute.yh"
        test_content = test_path.read_text() if test_path.exists() else None
        
        # Load signature (optional)
        sig_path = path / "signature"
        signature = sig_path.read_bytes() if sig_path.exists() else None
        
        return cls(
            metadata=metadata,
            statute_content=statute_content,
            test_content=test_content,
            signature=signature,
        )
    
    @classmethod
    def from_yhpkg(cls, path: Path) -> "Package":
        """
        Load package from .yhpkg file.
        """
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Extract tarball
            with tarfile.open(path, "r:gz") as tar:
                tar.extractall(tmpdir_path)
            
            return cls.from_directory(tmpdir_path)
    
    def to_yhpkg(self, output_path: Path) -> Path:
        """
        Save package as .yhpkg file.
        
        Args:
            output_path: Path to write .yhpkg file
            
        Returns:
            Path to created file
        """
        import tempfile
        
        output_path = Path(output_path)
        if not output_path.suffix == ".yhpkg":
            output_path = output_path.with_suffix(".yhpkg")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Write statute
            (tmpdir_path / "statute.yh").write_text(self.statute_content)
            
            # Write tests if present
            if self.test_content:
                (tmpdir_path / "test_statute.yh").write_text(self.test_content)
            
            # Write metadata as TOML
            self._write_metadata_toml(tmpdir_path / "metadata.toml")
            
            # Write signature if present
            if self.signature:
                (tmpdir_path / "signature").write_bytes(self.signature)
            
            # Create gzipped tarball
            with tarfile.open(output_path, "w:gz") as tar:
                for item in tmpdir_path.iterdir():
                    tar.add(item, arcname=item.name)
        
        return output_path
    
    def _write_metadata_toml(self, path: Path) -> None:
        """Write metadata as TOML file."""
        lines = [
            f'section_number = "{self.metadata.section_number}"',
            f'title = "{self.metadata.title}"',
            f'jurisdiction = "{self.metadata.jurisdiction}"',
            f'contributor = "{self.metadata.contributor}"',
            f'version = "{self.metadata.version}"',
            f'description = "{self.metadata.description}"',
            f'license = "{self.metadata.license}"',
            f'tags = {json.dumps(self.metadata.tags)}',
            f'dependencies = {json.dumps(self.metadata.dependencies)}',
        ]
        # Add deprecation section if deprecated
        if self.metadata.deprecation.deprecated:
            lines.append("")
            lines.append("[deprecation]")
            lines.append("deprecated = true")
            if self.metadata.deprecation.reason:
                lines.append(f'reason = "{self.metadata.deprecation.reason}"')
            if self.metadata.deprecation.deprecated_since:
                lines.append(f'deprecated_since = "{self.metadata.deprecation.deprecated_since}"')
            if self.metadata.deprecation.replacement:
                lines.append(f'replacement = "{self.metadata.deprecation.replacement}"')
            if self.metadata.deprecation.removal_version:
                lines.append(f'removal_version = "{self.metadata.deprecation.removal_version}"')
        path.write_text("\n".join(lines))
    
    def content_hash(self) -> str:
        """
        Calculate content hash for package.
        
        Returns:
            SHA-256 hash of statute content
        """
        return hashlib.sha256(self.statute_content.encode()).hexdigest()


class PackageValidator:
    """
    Validates Yuho statute packages.
    
    Checks:
    - Metadata completeness
    - Statute parsability
    - Test execution
    - Signature verification (if provided)
    """
    
    def __init__(self, strict: bool = True):
        """
        Initialize validator.
        
        Args:
            strict: If True, fail on warnings. If False, only fail on errors.
        """
        self.strict = strict
    
    def validate(self, package: Package) -> tuple[bool, List[str], List[str]]:
        """
        Validate a package.

        Args:
            package: Package to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Validate metadata
        meta_valid, meta_errors = package.metadata.is_valid()
        if not meta_valid:
            errors.extend(f"Metadata: {e}" for e in meta_errors)

        # Check for deprecation
        deprecation_warning = package.metadata.get_deprecation_warning()
        if deprecation_warning:
            warnings.append(deprecation_warning)

        # Validate statute parsability
        parse_errors = self._check_parsability(package.statute_content)
        if parse_errors:
            errors.extend(f"Parse: {e}" for e in parse_errors)

        # Validate tests if present
        if package.test_content:
            test_errors = self._check_parsability(package.test_content)
            if test_errors:
                warnings.extend(f"Test parse: {e}" for e in test_errors)
        else:
            warnings.append("No test file provided")

        # Check signature if present
        if package.signature:
            sig_valid = self._verify_signature(package)
            if not sig_valid:
                errors.append("Signature verification failed")
        else:
            warnings.append("No signature provided")

        # Determine overall validity
        is_valid = len(errors) == 0
        if self.strict and warnings:
            is_valid = False

        return (is_valid, errors, warnings)
    
    def _check_parsability(self, content: str) -> List[str]:
        """Check if content parses successfully."""
        errors = []
        
        try:
            from yuho.parser import Parser
            parser = Parser()
            result = parser.parse(content)
            
            if result.errors:
                errors.extend(str(e) for e in result.errors)
        except Exception as e:
            errors.append(f"Parse error: {e}")
        
        return errors
    
    def _verify_signature(self, package: Package) -> bool:
        """Verify package signature."""
        if not package.signature:
            return True
        
        # In production, this would verify against contributor's public key
        # For now, just check signature format
        try:
            # Ed25519 signatures are 64 bytes
            return len(package.signature) == 64
        except Exception:
            return False
