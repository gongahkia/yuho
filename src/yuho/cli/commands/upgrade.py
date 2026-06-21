"""Upgrade Yuho source files between grammar versions."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click

from yuho.parser.wrapper import CURRENT_GRAMMAR_VERSION, GRAMMAR_PRAGMA_RE


@dataclass(frozen=True)
class UpgradeResult:
    source: str
    changed: bool
    from_version: Optional[str]
    to_version: str


def run_upgrade(
    file: str,
    *,
    in_place: bool = False,
    check: bool = False,
    from_version: Optional[str] = None,
    to_version: str = CURRENT_GRAMMAR_VERSION,
    quiet: bool = False,
) -> None:
    if file == "-" and in_place:
        click.echo("error: --in-place cannot be used with stdin", err=True)
        sys.exit(2)

    if file == "-":
        source = sys.stdin.read()
        path = None
    else:
        path = Path(file)
        source = path.read_text(encoding="utf-8")

    try:
        result = upgrade_source(source, from_version=from_version, to_version=to_version)
    except ValueError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)

    if check:
        if result.changed:
            click.echo(
                f"upgrade required: v{result.from_version or 'none'} -> v{result.to_version}",
                err=True,
            )
            sys.exit(1)
        if not quiet:
            click.echo(f"up to date: v{result.to_version}")
        sys.exit(0)

    if in_place:
        assert path is not None
        path.write_text(result.source, encoding="utf-8")
        if not quiet:
            action = "updated" if result.changed else "unchanged"
            click.echo(f"{action}: {path}")
        sys.exit(0)

    print(result.source, end="")
    sys.exit(0)


def upgrade_source(
    source: str,
    *,
    from_version: Optional[str] = None,
    to_version: str = CURRENT_GRAMMAR_VERSION,
) -> UpgradeResult:
    from_version = _normalize_version(from_version) if from_version else None
    to_version = _normalize_version(to_version)
    first_line, rest = _split_first_line(source)
    detected_version = _detect_version(first_line)

    if from_version and detected_version and detected_version != from_version:
        raise ValueError(f"--from v{from_version} does not match file pragma v{detected_version}")

    effective_from = detected_version or from_version
    target_line = f"#yuho v{to_version}"
    if first_line.startswith("#yuho"):
        new_source = target_line + rest
    else:
        new_source = target_line + "\n" + source

    return UpgradeResult(
        source=new_source,
        changed=new_source != source,
        from_version=effective_from,
        to_version=to_version,
    )


def _split_first_line(source: str) -> tuple[str, str]:
    line_end = source.find("\n")
    if line_end == -1:
        return source.rstrip("\r"), ""
    return source[:line_end].rstrip("\r"), source[line_end:]


def _detect_version(first_line: str) -> Optional[str]:
    match = GRAMMAR_PRAGMA_RE.fullmatch(first_line)
    return match.group("version") if match else None


def _normalize_version(version: str) -> str:
    return version[1:] if version.startswith("v") else version
