"""
Package installation and management for Yuho library.

Handles downloading, verifying, and installing statute packages.
"""

from typing import Optional, List, Tuple
from pathlib import Path
import shutil
import logging
import json
import tempfile
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin

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


def _compare_versions(v1: str, v2: str) -> int:
    """
    Compare semantic version strings.

    Returns:
        -1 if v1 < v2, 0 if equal, 1 if v1 > v2
    """
    def parse_version(v: str) -> Tuple[int, ...]:
        parts = v.lstrip("v").split(".")
        result = []
        for p in parts:
            # Handle pre-release suffixes like -alpha, -beta
            num = p.split("-")[0]
            try:
                result.append(int(num))
            except ValueError:
                result.append(0)
        return tuple(result)

    p1 = parse_version(v1)
    p2 = parse_version(v2)

    # Pad to equal length
    max_len = max(len(p1), len(p2))
    p1 = p1 + (0,) * (max_len - len(p1))
    p2 = p2 + (0,) * (max_len - len(p2))

    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    return 0


def check_updates(
    registry_url: Optional[str] = None,
    auth_token: Optional[str] = None,
    timeout: int = 30,
    verify_ssl: bool = True,
) -> List[dict]:
    """
    Check for package updates from registry.

    Args:
        registry_url: Registry URL to check (default: https://registry.yuho.dev)
        auth_token: Optional authentication token
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates

    Returns:
        List of packages with updates available, each containing:
        - section_number: Package section number
        - current_version: Currently installed version
        - available_version: Version available in registry
        - title: Package title
    """
    if not registry_url:
        registry_url = "https://registry.yuho.dev"

    index = LibraryIndex()
    installed = index.list_all()

    if not installed:
        logger.info("No packages installed")
        return []

    updates = []

    try:
        # Fetch registry index
        api_url = urljoin(registry_url.rstrip("/") + "/", "api/v1/packages")

        headers = {
            "Accept": "application/json",
            "User-Agent": "yuho-library/2.0",
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        request = Request(api_url, headers=headers, method="GET")

        import ssl
        context = None
        if not verify_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        with urlopen(request, timeout=timeout, context=context) as response:
            registry_data = json.loads(response.read().decode("utf-8"))

        # Build registry lookup
        registry_packages = {}
        for pkg in registry_data.get("packages", []):
            section = pkg.get("section_number")
            if section:
                registry_packages[section] = pkg

        # Compare versions
        for entry in installed:
            section = entry.section_number
            if section in registry_packages:
                registry_pkg = registry_packages[section]
                registry_version = registry_pkg.get("version", "0.0.0")

                if _compare_versions(entry.version, registry_version) < 0:
                    updates.append({
                        "section_number": section,
                        "current_version": entry.version,
                        "available_version": registry_version,
                        "title": entry.title,
                    })

        return updates

    except HTTPError as e:
        logger.error(f"Registry request failed: HTTP {e.code}")
        return []
    except URLError as e:
        logger.error(f"Registry connection failed: {e.reason}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid registry response: {e}")
        return []
    except Exception as e:
        logger.exception(f"Update check failed: {e}")
        return []


def download_package(
    section_number: str,
    registry_url: Optional[str] = None,
    auth_token: Optional[str] = None,
    timeout: int = 30,
    verify_ssl: bool = True,
    library_dir: Optional[Path] = None,
) -> Tuple[bool, str]:
    """
    Download and install a package from the registry.

    Args:
        section_number: Section number to download
        registry_url: Registry URL
        auth_token: Optional authentication token
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        library_dir: Library directory

    Returns:
        Tuple of (success, message)
    """
    if not registry_url:
        registry_url = "https://registry.yuho.dev"

    try:
        # Fetch package
        api_url = urljoin(
            registry_url.rstrip("/") + "/",
            f"api/v1/packages/{section_number}/download"
        )

        headers = {
            "Accept": "application/octet-stream",
            "User-Agent": "yuho-library/2.0",
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        request = Request(api_url, headers=headers, method="GET")

        import ssl
        context = None
        if not verify_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        with urlopen(request, timeout=timeout, context=context) as response:
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".yhpkg", delete=False) as tmp:
                tmp.write(response.read())
                tmp_path = tmp.name

        # Install the package
        success, message = install_package(tmp_path, library_dir, force=True)

        # Cleanup temp file
        Path(tmp_path).unlink(missing_ok=True)

        return (success, message)

    except HTTPError as e:
        if e.code == 404:
            return (False, f"Package not found: {section_number}")
        return (False, f"Download failed: HTTP {e.code}")
    except URLError as e:
        return (False, f"Connection failed: {e.reason}")
    except Exception as e:
        return (False, f"Download failed: {e}")


def update_all_packages(
    registry_url: Optional[str] = None,
    auth_token: Optional[str] = None,
    timeout: int = 30,
    verify_ssl: bool = True,
    library_dir: Optional[Path] = None,
) -> List[Tuple[str, bool, str]]:
    """
    Update all installed packages to latest versions.

    Args:
        registry_url: Registry URL
        auth_token: Optional authentication token
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        library_dir: Library directory

    Returns:
        List of (section_number, success, message) tuples
    """
    updates = check_updates(registry_url, auth_token, timeout, verify_ssl)

    if not updates:
        logger.info("All packages are up to date")
        return []

    results = []
    for update in updates:
        section = update["section_number"]
        success, message = download_package(
            section,
            registry_url,
            auth_token,
            timeout,
            verify_ssl,
            library_dir,
        )
        results.append((section, success, message))

    return results


def publish_package(
    source: str,
    registry_url: str,
    auth_token: Optional[str] = None,
    timeout: int = 60,
    verify_ssl: bool = True,
) -> Tuple[bool, str]:
    """
    Publish a package to a registry.

    Args:
        source: Path to package source (.yhpkg file or directory)
        registry_url: Registry URL to publish to
        auth_token: Authentication token (required for publishing)
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates

    Returns:
        Tuple of (success, message)
    """
    source_path = Path(source)

    try:
        # Load and validate package
        if source_path.suffix == ".yhpkg":
            package = Package.from_yhpkg(source_path)
            pkg_path = source_path
        elif source_path.is_dir():
            package = Package.from_directory(source_path)
            # Create temporary .yhpkg
            with tempfile.NamedTemporaryFile(suffix=".yhpkg", delete=False) as tmp:
                pkg_path = Path(tmp.name)
            package.to_yhpkg(pkg_path)
        else:
            return (False, f"Invalid source: {source}")

        # Validate strictly for publishing
        validator = PackageValidator(strict=True)
        is_valid, errors, warnings = validator.validate(package)

        if not is_valid:
            return (False, f"Package validation failed: {'; '.join(errors)}")

        if warnings:
            logger.warning(f"Package warnings: {'; '.join(warnings)}")

        # Require authentication for publishing
        if not auth_token:
            return (False, "Authentication token required for publishing. Set via --auth-token or config.")

        # Upload to registry
        api_url = urljoin(registry_url.rstrip("/") + "/", "api/v1/packages")

        # Read package data
        with open(pkg_path, "rb") as f:
            pkg_data = f.read()

        # Cleanup temp file if created
        if source_path.is_dir():
            pkg_path.unlink(missing_ok=True)

        # Prepare multipart form data
        boundary = "----YuhoPackageBoundary"
        body_parts = []

        # Add package file
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="package"; filename="{package.metadata.section_number}.yhpkg"'.encode()
        )
        body_parts.append(b"Content-Type: application/octet-stream")
        body_parts.append(b"")
        body_parts.append(pkg_data)

        # Add metadata
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="metadata"')
        body_parts.append(b"Content-Type: application/json")
        body_parts.append(b"")
        body_parts.append(json.dumps(package.metadata.to_dict()).encode())

        body_parts.append(f"--{boundary}--".encode())

        body = b"\r\n".join(body_parts)

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {auth_token}",
            "User-Agent": "yuho-library/2.0",
        }

        request = Request(api_url, data=body, headers=headers, method="POST")

        import ssl
        context = None
        if not verify_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        with urlopen(request, timeout=timeout, context=context) as response:
            result = json.loads(response.read().decode("utf-8"))

        if result.get("success"):
            return (True, f"Published {package.metadata.section_number} v{package.metadata.version}")
        else:
            return (False, result.get("error", "Unknown error"))

    except HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
            error_data = json.loads(error_body)
            error_msg = error_data.get("error", f"HTTP {e.code}")
        except Exception:
            error_msg = f"HTTP {e.code}: {error_body or e.reason}"
        return (False, f"Publish failed: {error_msg}")
    except URLError as e:
        return (False, f"Connection failed: {e.reason}")
    except Exception as e:
        logger.exception(f"Publish failed: {e}")
        return (False, f"Publish failed: {e}")
