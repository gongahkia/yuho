"""
Library subcommand implementations for Yuho CLI.

Provides search, install, uninstall, list, update, publish, and info commands
for managing Yuho statute packages.
"""

from typing import Optional, List
from pathlib import Path
import json
import click


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
        # Registry install
        success, message = download_package(package)
    
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
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Uninstall an installed package.
    
    Args:
        package: Package section number
        json_output: Output as JSON
        verbose: Verbose output
    """
    from yuho.library import uninstall_package
    
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
    
    if package:
        # Update single package
        success, message = download_package(package)
        results = [(package, success, message)]
    else:
        # Check for updates first
        updates = check_updates()
        
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
        results = update_all_packages()
    
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
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Publish a package to the registry.
    
    Args:
        path: Path to package directory or .yhpkg
        registry: Registry URL
        token: Auth token
        json_output: Output as JSON
        verbose: Verbose output
    """
    from yuho.library import publish_package
    
    registry_url = registry or "https://registry.yuho.dev"
    
    success, message = publish_package(
        source=path,
        registry_url=registry_url,
        auth_token=token,
    )
    
    result = {"success": success, "message": message}
    
    if json_output:
        click.echo(json.dumps(result))
    elif success:
        click.echo(click.style("✓ ", fg="green") + message)
    else:
        click.echo(click.style("✗ ", fg="red") + message)
        raise SystemExit(1)


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
