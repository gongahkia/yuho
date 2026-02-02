"""
Package installation and management for Yuho library.

Handles downloading, verifying, and installing statute packages.
"""

from typing import Optional, List, Tuple
from pathlib import Path
import shutil
import logging

from yuho.library.package import Package, PackageValidator
from yuho.library.index import LibraryIndex, IndexEntry, DEFAULT_LIBRARY_DIR

logger = logging.getLogger(__name__)


def install_package(
    source: str,
    library_dir: Optional[Path] = None,
    verify_signature: bool = True,
    force: bool = False,
) -> Tuple[bool, str]:
    """
    Install a statute package to the library.
    
    Args:
        source: Path to .yhpkg file or contribution directory
        library_dir: Library directory (default: ~/.yuho/library/packages)
        verify_signature: Whether to verify package signature
        force: Overwrite existing package
        
    Returns:
        Tuple of (success, message)
    """
    library_dir = library_dir or DEFAULT_LIBRARY_DIR
    library_dir.mkdir(parents=True, exist_ok=True)
    
    source_path = Path(source)
    
    try:
        # Load package
        if source_path.suffix == ".yhpkg":
            package = Package.from_yhpkg(source_path)
        elif source_path.is_dir():
            package = Package.from_directory(source_path)
        else:
            return (False, f"Invalid source: {source}")
        
        # Validate
        validator = PackageValidator(strict=False)
        is_valid, errors, warnings = validator.validate(package)
        
        if not is_valid:
            return (False, f"Validation failed: {'; '.join(errors)}")
        
        if warnings:
            logger.warning(f"Package warnings: {'; '.join(warnings)}")
        
        # Check signature if required
        if verify_signature and not package.signature:
            logger.warning("Package has no signature, proceeding anyway")
        
        # Check for existing package
        section_safe = package.metadata.section_number.replace("/", "_").replace(".", "_")
        dest_path = library_dir / f"{section_safe}.yhpkg"
        
        if dest_path.exists() and not force:
            return (False, f"Package already installed: {package.metadata.section_number}. Use --force to overwrite.")
        
        # Create .yhpkg if from directory
        if source_path.is_dir():
            package.to_yhpkg(dest_path)
        else:
            shutil.copy2(source_path, dest_path)
        
        # Update index
        index = LibraryIndex()
        entry = IndexEntry.from_metadata(
            package.metadata,
            dest_path.name,
            package.content_hash(),
        )
        index.add(entry)
        
        return (True, f"Installed {package.metadata.section_number} v{package.metadata.version}")
        
    except FileNotFoundError as e:
        return (False, f"File not found: {e}")
    except Exception as e:
        logger.exception(f"Installation failed: {e}")
        return (False, f"Installation failed: {e}")


def uninstall_package(
    section_number: str,
    library_dir: Optional[Path] = None,
) -> Tuple[bool, str]:
    """
    Uninstall a statute package from the library.
    
    Args:
        section_number: Section number of package to remove
        library_dir: Library directory
        
    Returns:
        Tuple of (success, message)
    """
    library_dir = library_dir or DEFAULT_LIBRARY_DIR
    index = LibraryIndex()
    
    entry = index.get(section_number)
    if not entry:
        return (False, f"Package not found: {section_number}")
    
    # Remove package file
    pkg_path = library_dir / entry.package_path
    if pkg_path.exists():
        pkg_path.unlink()
    
    # Remove from index
    index.remove(section_number)
    
    return (True, f"Uninstalled {section_number}")


def list_installed(library_dir: Optional[Path] = None) -> List[dict]:
    """
    List all installed packages.
    
    Args:
        library_dir: Library directory
        
    Returns:
        List of package metadata dictionaries
    """
    index = LibraryIndex()
    return [e.to_dict() for e in index.list_all()]


def update_package(
    section_number: str,
    new_source: str,
    library_dir: Optional[Path] = None,
) -> Tuple[bool, str]:
    """
    Update an installed package.
    
    Args:
        section_number: Section number to update
        new_source: Path to new version
        library_dir: Library directory
        
    Returns:
        Tuple of (success, message)
    """
    index = LibraryIndex()
    
    current = index.get(section_number)
    if not current:
        return (False, f"Package not found: {section_number}")
    
    # Install new version (force overwrite)
    success, message = install_package(new_source, library_dir, force=True)
    
    if success:
        # Get new version info
        new_entry = index.get(section_number)
        if new_entry:
            message = f"Updated {section_number}: {current.version} -> {new_entry.version}"
    
    return (success, message)


def check_updates(
    registry_url: Optional[str] = None,
) -> List[dict]:
    """
    Check for package updates from registry.
    
    Args:
        registry_url: Registry URL to check
        
    Returns:
        List of packages with updates available
    """
    # In a full implementation, this would fetch the registry index
    # and compare versions with installed packages
    logger.warning("Registry update check not implemented")
    return []


def publish_package(
    source: str,
    registry_url: str,
) -> Tuple[bool, str]:
    """
    Publish a package to a registry.
    
    Args:
        source: Path to package source
        registry_url: Registry URL to publish to
        
    Returns:
        Tuple of (success, message)
    """
    source_path = Path(source)
    
    try:
        # Load and validate
        if source_path.suffix == ".yhpkg":
            package = Package.from_yhpkg(source_path)
        elif source_path.is_dir():
            package = Package.from_directory(source_path)
        else:
            return (False, f"Invalid source: {source}")
        
        validator = PackageValidator(strict=True)
        is_valid, errors, warnings = validator.validate(package)
        
        if not is_valid:
            return (False, f"Package invalid: {'; '.join(errors + warnings)}")
        
        if not package.signature:
            return (False, "Package must be signed for publishing")
        
        # In a full implementation, this would upload to the registry
        logger.warning(f"Would publish to {registry_url}")
        return (False, "Publishing not yet implemented")
        
    except Exception as e:
        return (False, f"Publish failed: {e}")
