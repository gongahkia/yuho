"""
Yuho library module - user-contributed statute repository.

Provides:
- Package format definitions (.yhpkg)
- Contribution validation
- Library indexing and search
- Package installation and management
- Dependency resolution with version constraints
"""

from yuho.library.package import (
    Package,
    PackageMetadata,
    PackageValidator,
)
from yuho.library.index import (
    LibraryIndex,
    search_library,
)
from yuho.library.install import (
    install_package,
    uninstall_package,
    list_installed,
    update_package,
    check_updates,
    download_package,
    update_all_packages,
    publish_package,
)
from yuho.library.resolver import (
    DependencyResolver,
    Resolution,
    Dependency,
    Version,
    VersionConstraint,
    resolve_dependencies,
)
from yuho.library.lockfile import (
    LockFile,
    LockFileManager,
    LockedPackage,
    load_lock_file,
    create_lock_file,
)

__all__ = [
    "Package",
    "PackageMetadata",
    "PackageValidator",
    "LibraryIndex",
    "search_library",
    "install_package",
    "uninstall_package",
    "list_installed",
    "update_package",
    "check_updates",
    "download_package",
    "update_all_packages",
    "publish_package",
    "DependencyResolver",
    "Resolution",
    "Dependency",
    "Version",
    "VersionConstraint",
    "resolve_dependencies",
    "LockFile",
    "LockFileManager",
    "LockedPackage",
    "load_lock_file",
    "create_lock_file",
]
