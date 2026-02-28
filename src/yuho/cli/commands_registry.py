"""
CLI command registration helpers.
"""

from typing import Optional

import click


def register_group_commands(cli: click.Group) -> None:
    """Register grouped subcommands for the Yuho CLI."""

    # =========================================================================
    # Config command
    # =========================================================================

    @cli.group()
    @click.pass_context
    def config(ctx: click.Context) -> None:
        """
        Manage Yuho configuration.

        View and modify configuration settings for all Yuho components.
        """
        pass

    @config.command("show")
    @click.option("-s", "--section", type=click.Choice(["llm", "transpile", "lsp", "mcp"]),
                  help="Show only specific section")
    @click.option("-f", "--format", "fmt", type=click.Choice(["toml", "json"]),
                  default="toml", help="Output format")
    @click.pass_context
    def config_show(ctx: click.Context, section: Optional[str], fmt: str) -> None:
        """
        Display current configuration.

        Shows all configuration values from file and environment.

        Examples:
            yuho config show
            yuho config show -s llm
            yuho config show -f json
        """
        from yuho.cli.commands.config import run_config_show
        run_config_show(section=section, format=fmt, verbose=ctx.obj["verbose"])

    @config.command("set")
    @click.argument("key")
    @click.argument("value")
    @click.pass_context
    def config_set(ctx: click.Context, key: str, value: str) -> None:
        """
        Set a configuration value.

        KEY must be in format 'section.key' (e.g., 'llm.provider').

        Examples:
            yuho config set llm.provider ollama
            yuho config set llm.model llama3
            yuho config set mcp.port 9000
        """
        from yuho.cli.commands.config import run_config_set
        run_config_set(key, value, verbose=ctx.obj["verbose"])

    @config.command("init")
    @click.option("--force", is_flag=True, help="Overwrite existing config file")
    @click.pass_context
    def config_init(ctx: click.Context, force: bool) -> None:
        """
        Create a default configuration file.

        Creates ~/.config/yuho/config.toml with sensible defaults.
        """
        from yuho.cli.commands.config import run_config_init
        run_config_init(force=force, verbose=ctx.obj["verbose"])

    # =========================================================================
    # Library command
    # =========================================================================

    @cli.group()
    @click.pass_context
    def library(ctx: click.Context) -> None:
        """
        Manage Yuho statute packages.

        Search, install, update, and manage statute packages from the library.
        """
        pass

    @library.command("search")
    @click.argument("query")
    @click.option("-j", "--jurisdiction", help="Filter by jurisdiction")
    @click.option("-t", "--tag", "tags", multiple=True, help="Filter by tag")
    @click.option("-n", "--limit", type=int, default=20, help="Max results")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @click.pass_context
    def library_search(
        ctx: click.Context,
        query: str,
        jurisdiction: Optional[str],
        tags: tuple,
        limit: int,
        json_output: bool,
    ) -> None:
        """
        Search for packages in the library.

        Examples:
            yuho library search theft
            yuho library search S403 --jurisdiction singapore
        """
        from yuho.cli.commands.library import run_library_search
        run_library_search(
            query,
            jurisdiction=jurisdiction,
            tags=list(tags) if tags else None,
            limit=limit,
            json_output=json_output,
            verbose=ctx.obj["verbose"],
        )

    @library.command("install")
    @click.argument("package")
    @click.option("-f", "--force", is_flag=True, help="Overwrite existing")
    @click.option("--no-deps", is_flag=True, help="Skip dependencies")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @click.pass_context
    def library_install(
        ctx: click.Context,
        package: str,
        force: bool,
        no_deps: bool,
        json_output: bool,
    ) -> None:
        """
        Install a package.

        Examples:
            yuho library install S403
            yuho library install ./my-package.yhpkg
        """
        from yuho.cli.commands.library import run_library_install
        run_library_install(
            package,
            force=force,
            no_deps=no_deps,
            json_output=json_output,
            verbose=ctx.obj["verbose"],
        )

    @library.command("uninstall")
    @click.argument("package")
    @click.option("--dry-run", is_flag=True, help="Show what would be done")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @click.pass_context
    def library_uninstall(
        ctx: click.Context,
        package: str,
        dry_run: bool,
        json_output: bool,
    ) -> None:
        """
        Uninstall a package.

        Examples:
            yuho library uninstall S403
        """
        from yuho.cli.commands.library import run_library_uninstall
        run_library_uninstall(
            package,
            dry_run=dry_run,
            json_output=json_output,
            verbose=ctx.obj["verbose"],
        )

    @library.command("list")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @click.pass_context
    def library_list(ctx: click.Context, json_output: bool) -> None:
        """
        List all installed packages.
        """
        from yuho.cli.commands.library import run_library_list
        run_library_list(json_output=json_output, verbose=ctx.obj["verbose"])

    @library.command("update")
    @click.argument("package", required=False)
    @click.option("--all", "all_packages", is_flag=True, help="Update all packages")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @click.pass_context
    def library_update(
        ctx: click.Context,
        package: Optional[str],
        all_packages: bool,
        json_output: bool,
    ) -> None:
        """
        Update one or all packages.

        Without arguments, shows available updates.
        Use --all to apply all updates.

        Examples:
            yuho library update           # Show updates
            yuho library update --all     # Apply all updates
            yuho library update S403      # Update specific package
        """
        from yuho.cli.commands.library import run_library_update
        run_library_update(
            package,
            all_packages=all_packages,
            json_output=json_output,
            verbose=ctx.obj["verbose"],
        )

    @library.command("publish")
    @click.argument("path", type=click.Path(exists=True))
    @click.option("--registry", help="Registry URL")
    @click.option("--token", help="Auth token")
    @click.option("--dry-run", is_flag=True, help="Validate package without publishing")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @click.pass_context
    def library_publish(
        ctx: click.Context,
        path: str,
        registry: Optional[str],
        token: Optional[str],
        dry_run: bool,
        json_output: bool,
    ) -> None:
        """
        Publish a package to the registry.

        Examples:
            yuho library publish ./my-statute --token $YUHO_TOKEN
            yuho library publish ./my-statute --dry-run
        """
        from yuho.cli.commands.library import run_library_publish
        run_library_publish(
            path,
            registry=registry,
            token=token,
            dry_run=dry_run,
            json_output=json_output,
            verbose=ctx.obj["verbose"],
        )

    @library.command("info")
    @click.argument("package")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @click.pass_context
    def library_info(
        ctx: click.Context,
        package: str,
        json_output: bool,
    ) -> None:
        """
        Show detailed package information.

        Examples:
            yuho library info S403
        """
        from yuho.cli.commands.library import run_library_info
        run_library_info(
            package,
            json_output=json_output,
            verbose=ctx.obj["verbose"],
        )

    @library.command("outdated")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @click.pass_context
    def library_outdated(
        ctx: click.Context,
        json_output: bool,
    ) -> None:
        """
        Show packages with updates available.

        Displays installed packages that have newer versions in the registry,
        along with the type of update (major, minor, patch) and deprecation warnings.

        Examples:
            yuho library outdated
            yuho library outdated --json
        """
        from yuho.cli.commands.library import run_library_outdated
        run_library_outdated(
            json_output=json_output,
            verbose=ctx.obj["verbose"],
        )

    @library.command("tree")
    @click.argument("package", required=False)
    @click.option("--depth", "-d", default=10, help="Maximum depth to display")
    @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
    @click.pass_context
    def library_tree(
        ctx: click.Context,
        package: Optional[str],
        depth: int,
        json_output: bool,
    ) -> None:
        """
        Show dependency tree for packages.

        Displays a tree visualization of package dependencies. If no package
        is specified, shows trees for all installed packages.

        Examples:
            yuho library tree
            yuho library tree S403
            yuho library tree --depth 3
        """
        from yuho.cli.commands.library import run_library_tree
        run_library_tree(
            package=package,
            depth=depth,
            json_output=json_output,
            verbose=ctx.obj["verbose"],
        )
