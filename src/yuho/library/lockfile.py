"""
Version locking for reproducible Yuho package installs.

Manages yuho.lock file that records exact resolved versions
for reproducible installations across environments.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json
import hashlib
import logging
import os
import tempfile

from yuho.library.resolver import Version, Resolution

logger = logging.getLogger(__name__)


# Default lock file name
LOCK_FILE_NAME = "yuho.lock"


@dataclass
class LockedPackage:
    """A locked package version with integrity hash."""
    section_number: str
    version: str
    content_hash: str
    source: str  # "registry" or local path
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "content_hash": self.content_hash,
            "source": self.source,
            "dependencies": self.dependencies,
        }
    
    @classmethod
    def from_dict(cls, section: str, data: Dict[str, Any]) -> "LockedPackage":
        """Create from dictionary."""
        return cls(
            section_number=section,
            version=data["version"],
            content_hash=data.get("content_hash", ""),
            source=data.get("source", "registry"),
            dependencies=data.get("dependencies", []),
        )


@dataclass
class LockFile:
    """
    Lock file for reproducible installs.
    
    Format (JSON):
    {
        "lock_version": "1",
        "generated_at": "2024-01-15T10:30:00Z",
        "packages": {
            "S403": {
                "version": "1.2.3",
                "content_hash": "sha256:abc123...",
                "source": "registry",
                "dependencies": ["S400@^1.0.0"]
            }
        }
    }
    """
    lock_version: str = "1"
    generated_at: str = ""
    packages: Dict[str, LockedPackage] = field(default_factory=dict)
    
    @classmethod
    def from_file(cls, path: Path) -> "LockFile":
        """Load lock file from path."""
        if not path.exists():
            return cls()
        
        with open(path) as f:
            data = json.load(f)
        
        packages = {}
        for section, pkg_data in data.get("packages", {}).items():
            packages[section] = LockedPackage.from_dict(section, pkg_data)
        
        return cls(
            lock_version=data.get("lock_version", "1"),
            generated_at=data.get("generated_at", ""),
            packages=packages,
        )
    
    def to_file(self, path: Path) -> None:
        """Save lock file to path."""
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "lock_version": self.lock_version,
            "generated_at": self.generated_at or datetime.utcnow().isoformat() + "Z",
            "packages": {
                section: pkg.to_dict()
                for section, pkg in sorted(self.packages.items())
            },
        }

        fd, temp_path_str = tempfile.mkstemp(
            prefix=f"{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
        )
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
    
    def add_package(
        self,
        section: str,
        version: str,
        content_hash: str,
        source: str = "registry",
        dependencies: Optional[List[str]] = None,
    ) -> None:
        """Add or update a locked package."""
        self.packages[section] = LockedPackage(
            section_number=section,
            version=version,
            content_hash=content_hash,
            source=source,
            dependencies=dependencies or [],
        )
    
    def remove_package(self, section: str) -> bool:
        """Remove a package from lock file."""
        if section in self.packages:
            del self.packages[section]
            return True
        return False
    
    def get_version(self, section: str) -> Optional[str]:
        """Get locked version for a package."""
        if section in self.packages:
            return self.packages[section].version
        return None
    
    def get_hash(self, section: str) -> Optional[str]:
        """Get content hash for a package."""
        if section in self.packages:
            return self.packages[section].content_hash
        return None
    
    def verify_integrity(self, section: str, content_hash: str) -> bool:
        """Verify package integrity against lock file."""
        locked_hash = self.get_hash(section)
        if not locked_hash:
            return True  # No hash recorded
        return locked_hash == content_hash
    
    def get_locked_versions(self) -> Dict[str, str]:
        """Get all locked versions as dict."""
        return {
            section: pkg.version
            for section, pkg in self.packages.items()
        }


class LockFileManager:
    """
    Manages lock file operations for a project.
    
    Handles creating, updating, and using lock files for
    reproducible package installations.
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize manager for a project directory.
        
        Args:
            project_dir: Project root directory
        """
        self.project_dir = Path(project_dir)
        self.lock_path = self.project_dir / LOCK_FILE_NAME
        self._lock_file: Optional[LockFile] = None
    
    @property
    def lock_file(self) -> LockFile:
        """Get or load the lock file."""
        if self._lock_file is None:
            self._lock_file = LockFile.from_file(self.lock_path)
        return self._lock_file
    
    def exists(self) -> bool:
        """Check if lock file exists."""
        return self.lock_path.exists()
    
    def create_from_resolution(self, resolution: Resolution) -> LockFile:
        """
        Create lock file from dependency resolution.
        
        Args:
            resolution: Resolved dependencies
            
        Returns:
            Created lock file
        """
        lock = LockFile(
            generated_at=datetime.utcnow().isoformat() + "Z",
        )
        
        for section, version in resolution.packages.items():
            lock.add_package(
                section=section,
                version=str(version),
                content_hash="",  # Will be filled on install
                source="registry",
            )
        
        lock.to_file(self.lock_path)
        self._lock_file = lock
        
        return lock
    
    def update_hash(self, section: str, content_hash: str) -> None:
        """Update content hash after installation."""
        if section in self.lock_file.packages:
            self.lock_file.packages[section].content_hash = content_hash
            self.lock_file.to_file(self.lock_path)
    
    def get_locked_for_install(self) -> Dict[str, str]:
        """
        Get locked versions for installation.
        
        Returns:
            Dict of section -> version
        """
        return self.lock_file.get_locked_versions()
    
    def refresh(self, new_resolution: Resolution) -> LockFile:
        """
        Refresh lock file with new resolution.
        
        Preserves content hashes for unchanged versions.
        
        Args:
            new_resolution: New resolution to lock
            
        Returns:
            Updated lock file
        """
        old_lock = self.lock_file
        new_lock = LockFile(
            generated_at=datetime.utcnow().isoformat() + "Z",
        )
        
        for section, version in new_resolution.packages.items():
            # Preserve hash if version unchanged
            old_hash = ""
            if section in old_lock.packages:
                old_pkg = old_lock.packages[section]
                if old_pkg.version == str(version):
                    old_hash = old_pkg.content_hash
            
            new_lock.add_package(
                section=section,
                version=str(version),
                content_hash=old_hash,
                source="registry",
            )
        
        new_lock.to_file(self.lock_path)
        self._lock_file = new_lock
        
        return new_lock
    
    def check_outdated(self) -> List[str]:
        """
        Check for packages that may be outdated.
        
        Returns:
            List of section numbers with potential updates
        """
        from yuho.library.install import check_updates
        
        updates = check_updates()
        outdated = []
        
        for update in updates:
            section = update["section_number"]
            if section in self.lock_file.packages:
                outdated.append(section)
        
        return outdated


def load_lock_file(project_dir: Optional[Path] = None) -> LockFile:
    """
    Load lock file from project directory.
    
    Args:
        project_dir: Project directory (default: current)
        
    Returns:
        Lock file instance
    """
    project_dir = project_dir or Path.cwd()
    return LockFile.from_file(project_dir / LOCK_FILE_NAME)


def create_lock_file(
    dependencies: List[str],
    project_dir: Optional[Path] = None,
) -> LockFile:
    """
    Create lock file from dependencies.
    
    Args:
        dependencies: List of dependency strings
        project_dir: Project directory
        
    Returns:
        Created lock file
    """
    from yuho.library.resolver import resolve_dependencies
    
    project_dir = project_dir or Path.cwd()
    
    resolution = resolve_dependencies(dependencies)
    
    if not resolution.success:
        raise ValueError(f"Resolution failed: {'; '.join(resolution.errors)}")
    
    manager = LockFileManager(project_dir)
    return manager.create_from_resolution(resolution)
