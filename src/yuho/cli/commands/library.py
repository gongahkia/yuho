"""
Library subcommand implementations for Yuho CLI.

Provides search, install, uninstall, list, update, publish, and info commands
for managing Yuho statute packages.
"""

from typing import Optional, List
from pathlib import Path
import json
import click


def _get_library_network_config(
    registry_url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> tuple[str, Optional[str], int, bool]:
    """Resolve network options from CLI overrides and config defaults."""
    from yuho.config.loader import get_config

    library_config = get_config().library
    return (
        registry_url or library_config.registry_url,
        auth_token if auth_token is not None else library_config.auth_token,
        library_config.timeout,
        library_config.verify_ssl,
    )


def _is_offline_mode() -> bool:
    """Check whether CLI global offline mode is enabled."""
    ctx = click.get_current_context(silent=True)
    while ctx and ctx.parent:
        ctx = ctx.parent
    if ctx and isinstance(ctx.obj, dict):
        return bool(ctx.obj.get("offline", False))
    return False


def _offline_block_message(operation: str) -> str:
    return (
        f"Offline mode enabled: '{operation}' requires registry/network access. "
        "Disable --offline to proceed."
    )


def _abort_offline(operation: str, json_output: bool) -> None:
    """Exit with a consistent offline-blocked error message."""
    message = _offline_block_message(operation)
    if json_output:
        click.echo(json.dumps({"success": False, "message": message}))
    else:
        click.echo(click.style("✗ ", fg="red") + message)
    raise SystemExit(1)


def run_library_search(
    query: str,
    jurisdiction: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Search the library for packages matching query.
    
    Args:
        query: Search query (keyword, section number, or title)
        jurisdiction: Filter by jurisdiction
        tags: Filter by tags
        limit: Maximum results to return
        json_output: Output as JSON
        verbose: Verbose output
    """
    from yuho.library import search_library
    
    results = search_library(
        keyword=query,
        jurisdiction=jurisdiction,
        tags=tags,
    )[:limit]
    
    if json_output:
        click.echo(json.dumps(results, indent=2))
        return
    
    if not results:
        click.echo(f"No packages found for '{query}'")
        return
    
    click.echo(f"Found {len(results)} package(s):\n")
    
    for pkg in results:
        section = pkg.get("section_number", "")
        title = pkg.get("title", "")
        version = pkg.get("version", "")
        jurisdiction_val = pkg.get("jurisdiction", "")
        description = pkg.get("description", "")
        
        click.echo(click.style(f"  {section}", fg="cyan", bold=True) + 
                   click.style(f" v{version}", fg="yellow"))
        click.echo(f"    {title}")
        if jurisdiction_val:
            click.echo(f"    Jurisdiction: {jurisdiction_val}")
        if description and verbose:
            click.echo(f"    {description[:80]}...")
        click.echo()


def run_library_install(
    package: str,
    force: bool = False,
    no_deps: bool = False,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Install a package from registry or local path.
    
    Args:
        package: Package section number or path to .yhpkg
        force: Overwrite existing package
        no_deps: Don't install dependencies
        json_output: Output as JSON
        verbose: Verbose output
    """
    from yuho.library import install_package, download_package
    
    path = Path(package)
    
    if path.exists():
        # Local install
        success, message = install_package(str(path), force=force)
    else:
        if _is_offline_mode():
            _abort_offline("library install", json_output)
        # Registry install
        registry_url, auth_token, timeout, verify_ssl = _get_library_network_config()
        success, message = download_package(
            package,
            registry_url=registry_url,
            auth_token=auth_token,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )
    
    result = {"success": success, "message": message}
    
    if json_output:
        click.echo(json.dumps(result))
    elif success:
        click.echo(click.style("✓ ", fg="green") + message)
    else:
        click.echo(click.style("✗ ", fg="red") + message)
        raise SystemExit(1)


def run_library_uninstall(
    package: str,
    dry_run: bool = False,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Uninstall an installed package.

    Args:
        package: Package section number
        dry_run: Show what would be done without doing it
        json_output: Output as JSON
        verbose: Verbose output
    """
    from yuho.library import uninstall_package, list_installed

    if dry_run:
        # Check if package is installed
        installed = list_installed()
        pkg_info = next((p for p in installed if p.get("section_number") == package), None)

        if pkg_info:
            result = {
                "dry_run": True,
                "would_uninstall": package,
                "version": pkg_info.get("version", "unknown"),
                "title": pkg_info.get("title", ""),
            }
            if json_output:
                click.echo(json.dumps(result, indent=2))
            else:
                click.echo(click.style("[DRY RUN] ", fg="yellow") +
                          f"Would uninstall {package} v{pkg_info.get('version', '?')}")
                if verbose:
                    click.echo(f"  Title: {pkg_info.get('title', 'N/A')}")
        else:
            result = {"dry_run": True, "error": f"Package not found: {package}"}
            if json_output:
                click.echo(json.dumps(result))
            else:
                click.echo(click.style("[DRY RUN] ", fg="yellow") +
                          f"Package not installed: {package}")
        return

    success, message = uninstall_package(package)

    result = {"success": success, "message": message}

    if json_output:
        click.echo(json.dumps(result))
    elif success:
        click.echo(click.style("✓ ", fg="green") + message)
    else:
        click.echo(click.style("✗ ", fg="red") + message)
        raise SystemExit(1)


def run_library_list(
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    List all installed packages.
    
    Args:
        json_output: Output as JSON
        verbose: Verbose output
    """
    from yuho.library import list_installed
    
    packages = list_installed()
    
    if json_output:
        click.echo(json.dumps(packages, indent=2))
        return
    
    if not packages:
        click.echo("No packages installed")
        return
    
    click.echo(f"Installed packages ({len(packages)}):\n")
    
    for pkg in packages:
        section = pkg.get("section_number", "")
        title = pkg.get("title", "")
        version = pkg.get("version", "")
        
        click.echo(f"  {click.style(section, fg='cyan', bold=True)} " +
                   f"{click.style(f'v{version}', fg='yellow')}")
        if verbose:
            click.echo(f"    {title}")


def run_library_update(
    package: Optional[str] = None,
    all_packages: bool = False,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Update one or all packages.
    
    Args:
        package: Specific package to update (None for all)
        all_packages: Update all packages
        json_output: Output as JSON
        verbose: Verbose output
    """
    from yuho.library import update_all_packages, check_updates, download_package
    if _is_offline_mode():
        _abort_offline("library update", json_output)

    registry_url, auth_token, timeout, verify_ssl = _get_library_network_config()
    
    if package:
        # Update single package
        success, message = download_package(
            package,
            registry_url=registry_url,
            auth_token=auth_token,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )
        results = [(package, success, message)]
    else:
        # Check for updates first
        updates = check_updates(
            registry_url=registry_url,
            auth_token=auth_token,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )
        
        if not updates:
            if json_output:
                click.echo(json.dumps({"updates": []}))
            else:
                click.echo("All packages are up to date")
            return
        
        if not all_packages:
            # Just show available updates
            if json_output:
                click.echo(json.dumps({"updates": updates}))
            else:
                click.echo("Updates available:\n")
                for u in updates:
                    section = u["section_number"]
                    current = u["current_version"]
                    available = u["available_version"]
                    click.echo(f"  {section}: {current} -> {available}")
                click.echo("\nRun 'yuho library update --all' to update all")
            return
        
        # Update all
        results = update_all_packages(
            registry_url=registry_url,
            auth_token=auth_token,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )
    
    if json_output:
        click.echo(json.dumps([
            {"package": r[0], "success": r[1], "message": r[2]}
            for r in results
        ], indent=2))
    else:
        for section, success, message in results:
            if success:
                click.echo(click.style("✓ ", fg="green") + message)
            else:
                click.echo(click.style("✗ ", fg="red") + f"{section}: {message}")


def run_library_publish(
    path: str,
    registry: Optional[str] = None,
    token: Optional[str] = None,
    dry_run: bool = False,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Publish a package to the registry.

    Args:
        path: Path to package directory or .yhpkg
        registry: Registry URL
        token: Auth token
        dry_run: Validate package without actually publishing
        json_output: Output as JSON
        verbose: Verbose output
    """
    from yuho.library import publish_package, Package
    from pathlib import Path as PathLib

    if _is_offline_mode() and not dry_run:
        _abort_offline("library publish", json_output)

    registry_url, auth_token, timeout, verify_ssl = _get_library_network_config(
        registry,
        token,
    )
    pkg_path = PathLib(path)

    if dry_run:
        # Validate the package without publishing
        errors = []
        warnings = []
        pkg_info = {}

        try:
            # Try to load and validate the package
            if pkg_path.is_file() and pkg_path.suffix == ".yhpkg":
                pkg = Package.from_yhpkg(pkg_path)
            elif pkg_path.is_dir():
                # Look for metadata.toml
                meta_file = pkg_path / "metadata.toml"
                if not meta_file.exists():
                    errors.append("Missing metadata.toml")
                else:
                    import tomllib
                    with open(meta_file, "rb") as f:
                        pkg_info = tomllib.load(f)

                # Check for statute.yh
                statute_file = pkg_path / "statute.yh"
                if not statute_file.exists():
                    errors.append("Missing statute.yh")

                # Validate with parser
                if statute_file.exists():
                    from yuho.parser import get_parser
                    parser = get_parser()
                    result = parser.parse_file(statute_file)
                    if result.errors:
                        errors.extend(f"Parse error: {e.message}" for e in result.errors)
            else:
                errors.append(f"Invalid package path: {path}")

            if not auth_token and not dry_run:
                warnings.append("No auth token provided")

        except Exception as e:
            errors.append(f"Validation error: {e}")

        result = {
            "dry_run": True,
            "path": str(pkg_path),
            "registry": registry_url,
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "package_info": pkg_info,
        }

        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(click.style("[DRY RUN] ", fg="yellow") + f"Validating {path}")
            if pkg_info.get("section_number"):
                click.echo(f"  Section: {pkg_info.get('section_number')}")
            if pkg_info.get("title"):
                click.echo(f"  Title: {pkg_info.get('title')}")
            if pkg_info.get("version"):
                click.echo(f"  Version: {pkg_info.get('version')}")
            click.echo(f"  Registry: {registry_url}")

            if errors:
                click.echo(click.style("\nErrors:", fg="red"))
                for err in errors:
                    click.echo(f"  - {err}")
            if warnings:
                click.echo(click.style("\nWarnings:", fg="yellow"))
                for warn in warnings:
                    click.echo(f"  - {warn}")

            if not errors:
                click.echo(click.style("\n✓ Package is valid and ready to publish", fg="green"))
            else:
                click.echo(click.style("\n✗ Package validation failed", fg="red"))
                raise SystemExit(1)
        return

    success, message = publish_package(
        source=path,
        registry_url=registry_url,
        auth_token=auth_token,
        timeout=timeout,
        verify_ssl=verify_ssl,
    )

    result = {"success": success, "message": message}

    if json_output:
        click.echo(json.dumps(result))
    elif success:
        click.echo(click.style("✓ ", fg="green") + message)
    else:
        click.echo(click.style("✗ ", fg="red") + message)
        raise SystemExit(1)


def run_library_outdated(
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Show packages with updates available.

    Args:
        json_output: Output as JSON
        verbose: Verbose output including deprecation info
    """
    from yuho.library import check_updates, list_installed, LibraryIndex
    from yuho.library.resolver import Version

    offline_mode = _is_offline_mode()

    if offline_mode:
        updates = []
    else:
        registry_url, auth_token, timeout, verify_ssl = _get_library_network_config()
        # Get update info from registry
        updates = check_updates(
            registry_url=registry_url,
            auth_token=auth_token,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )
    installed = list_installed()

    # Build installed lookup
    installed_map = {
        pkg.get("section_number"): pkg
        for pkg in installed
    }

    # Check for deprecated packages
    index = LibraryIndex()
    deprecated_warnings = []
    for pkg in installed:
        section = pkg.get("section_number")
        entry = index.get(section)
        if entry and hasattr(entry, 'deprecation') and getattr(entry, 'is_deprecated', False):
            deprecated_warnings.append({
                "section_number": section,
                "message": f"Package {section} is deprecated",
            })

    if json_output:
        result = {
            "outdated": updates,
            "deprecated": deprecated_warnings,
            "total_installed": len(installed),
            "total_outdated": len(updates),
            "offline": offline_mode,
        }
        click.echo(json.dumps(result, indent=2))
        return

    if offline_mode:
        click.echo(click.style("[offline] ", fg="yellow") + "Skipped registry update check; showing local data only.")

    if not updates and not deprecated_warnings:
        click.echo(click.style("All packages are up to date!", fg="green"))
        return

    if updates:
        click.echo(click.style(f"\nOutdated packages ({len(updates)}):\n", bold=True))

        for u in updates:
            section = u["section_number"]
            current = u["current_version"]
            available = u["available_version"]

            # Determine upgrade type
            try:
                curr_v = Version.parse(current)
                avail_v = Version.parse(available)
                if avail_v.major > curr_v.major:
                    change_type = click.style("MAJOR", fg="red", bold=True)
                elif avail_v.minor > curr_v.minor:
                    change_type = click.style("minor", fg="yellow")
                else:
                    change_type = click.style("patch", fg="green")
            except Exception:
                change_type = ""

            click.echo(
                f"  {click.style(section, fg='cyan', bold=True)}  "
                f"{click.style(current, fg='yellow')} -> "
                f"{click.style(available, fg='green')}  {change_type}"
            )

            if verbose:
                pkg = installed_map.get(section, {})
                title = pkg.get("title", "")
                if title:
                    click.echo(f"      {title}")

        click.echo()

    if deprecated_warnings:
        click.echo(click.style(f"\nDeprecated packages ({len(deprecated_warnings)}):\n", fg="yellow", bold=True))
        for d in deprecated_warnings:
            click.echo(f"  {click.style('⚠', fg='yellow')} {d['message']}")
        click.echo()

    click.echo(f"Run 'yuho library update --all' to update outdated packages")


def run_library_tree(
    package: Optional[str] = None,
    depth: int = 10,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Show dependency tree for packages.

    Args:
        package: Specific package to show tree for (None for all installed)
        depth: Maximum depth to display
        json_output: Output as JSON
        verbose: Verbose output including versions
    """
    from yuho.library import list_installed, LibraryIndex, Package
    from yuho.library.resolver import Dependency
    from pathlib import Path

    index = LibraryIndex()

    def get_dependencies(section: str) -> List[str]:
        """Get dependencies for a package from its metadata."""
        entry = index.get(section)
        if not entry:
            return []
        # Load package to get dependencies
        pkg_path = Path(entry.package_path) if hasattr(entry, 'package_path') else None
        if pkg_path and pkg_path.exists():
            try:
                pkg = Package.from_yhpkg(pkg_path)
                return pkg.metadata.dependencies
            except Exception:
                pass
        return []

    def build_tree(section: str, seen: set, current_depth: int) -> dict:
        """Build dependency tree recursively."""
        if current_depth > depth or section in seen:
            return {"section": section, "circular": section in seen, "children": []}

        seen = seen | {section}
        entry = index.get(section)
        version = entry.version if entry else "?"

        deps = get_dependencies(section)
        children = []

        for dep_str in deps:
            try:
                dep = Dependency.parse(dep_str)
                child_tree = build_tree(dep.package, seen, current_depth + 1)
                child_tree["constraint"] = str(dep.constraint)
                children.append(child_tree)
            except Exception:
                children.append({"section": dep_str, "error": True, "children": []})

        return {
            "section": section,
            "version": version,
            "children": children,
        }

    def print_tree(node: dict, prefix: str = "", is_last: bool = True) -> None:
        """Print tree with ASCII art."""
        connector = "└── " if is_last else "├── "
        section = node.get("section", "?")
        version = node.get("version", "")
        constraint = node.get("constraint", "")

        # Format the node
        label = click.style(section, fg="cyan", bold=True)
        if verbose and version:
            label += click.style(f" v{version}", fg="yellow")
        if constraint:
            label += click.style(f" ({constraint})", fg="white", dim=True)
        if node.get("circular"):
            label += click.style(" (circular)", fg="red")
        if node.get("error"):
            label += click.style(" (not found)", fg="red")

        click.echo(prefix + connector + label)

        children = node.get("children", [])
        child_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(children):
            print_tree(child, child_prefix, i == len(children) - 1)

    # Get packages to display
    if package:
        packages = [package]
    else:
        installed = list_installed()
        packages = [pkg.get("section_number") for pkg in installed if pkg.get("section_number")]

    if not packages:
        if json_output:
            click.echo(json.dumps({"trees": [], "message": "No packages installed"}))
        else:
            click.echo("No packages installed")
        return

    # Build trees
    trees = []
    for pkg in packages:
        tree = build_tree(pkg, set(), 0)
        trees.append(tree)

    if json_output:
        click.echo(json.dumps({"trees": trees}, indent=2))
        return

    click.echo()
    for i, tree in enumerate(trees):
        section = tree.get("section", "?")
        version = tree.get("version", "")
        children = tree.get("children", [])

        # Root node
        root_label = click.style(section, fg="cyan", bold=True)
        if verbose and version:
            root_label += click.style(f" v{version}", fg="yellow")

        if not children:
            click.echo(f"{root_label} (no dependencies)")
        else:
            click.echo(root_label)
            for j, child in enumerate(children):
                print_tree(child, "", j == len(children) - 1)

        if i < len(trees) - 1:
            click.echo()


def run_library_info(
    package: str,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Show detailed package information.

    Args:
        package: Package section number
        json_output: Output as JSON
        verbose: Verbose output
    """
    from yuho.library import LibraryIndex

    index = LibraryIndex()
    entry = index.get(package)

    if not entry:
        if json_output:
            click.echo(json.dumps({"error": f"Package not found: {package}"}))
        else:
            click.echo(f"Package not found: {package}")
        raise SystemExit(1)

    info = entry.to_dict()

    if json_output:
        click.echo(json.dumps(info, indent=2))
        return

    click.echo(click.style(f"\n{info['section_number']}", fg="cyan", bold=True) +
               click.style(f" v{info['version']}", fg="yellow"))
    click.echo(f"\n  Title:        {info['title']}")
    click.echo(f"  Jurisdiction: {info['jurisdiction']}")
    click.echo(f"  Contributor:  {info['contributor']}")

    if info.get("description"):
        click.echo(f"  Description:  {info['description']}")

    if info.get("tags"):
        click.echo(f"  Tags:         {', '.join(info['tags'])}")

    click.echo()
