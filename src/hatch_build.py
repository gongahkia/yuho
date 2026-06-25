"""Hatch build hook for compiling tree-sitter shared libraries into wheels."""

from __future__ import annotations

import hashlib
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Compile the tree-sitter grammar shared library before wheel packaging."""

    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        if self.target_name not in {"wheel", "editable"}:
            return

        root = Path(self.root)
        grammar_dir = root / "src" / "tree-sitter-yuho"
        package_dir = root / "src" / "tree_sitter_yuho"
        parser_c = grammar_dir / "src" / "parser.c"
        scanner_c = grammar_dir / "src" / "scanner.c"
        include_dir = grammar_dir / "src"

        if not parser_c.exists():
            raise RuntimeError(f"Missing parser source file: {parser_c}")

        if not scanner_c.exists():
            raise RuntimeError(f"Missing scanner source file: {scanner_c}")

        library_name = f"libtree-sitter-yuho.{_shared_library_suffix()}"
        output_path = Path(self.directory) / library_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        _compile_tree_sitter_library(
            parser_c=parser_c,
            scanner_c=scanner_c,
            include_dir=include_dir,
            output_path=output_path,
        )

        package_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output_path, package_dir / library_name)

        force_include = build_data.setdefault("force_include", {})
        if not isinstance(force_include, dict):
            raise RuntimeError("Unexpected build_data['force_include'] type")
        force_include[str(output_path)] = f"tree_sitter_yuho/{library_name}"


def _shared_library_suffix() -> str:
    if os.name == "nt":
        return "dll"
    if sys.platform == "darwin":
        return "dylib"
    return "so"


def _compile_tree_sitter_library(
    *, parser_c: Path, scanner_c: Path, include_dir: Path, output_path: Path
) -> None:
    compiler = _resolve_c_compiler()

    if os.name == "nt":
        linker_flags = ["-shared"]
    elif sys.platform == "darwin":
        library_name = output_path.name
        linker_flags = [
            "-dynamiclib",
            "-fPIC",
            f"-Wl,-install_name,@rpath/{library_name}",
        ]
    else:
        linker_flags = ["-shared", "-fPIC"]

    cmd = [
        compiler,
        *linker_flags,
        "-O2",
        "-I",
        str(include_dir),
        str(parser_c),
        str(scanner_c),
        "-o",
        str(output_path),
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Failed to compile tree-sitter shared library") from exc

    if sys.platform == "darwin":
        _normalize_macho_uuid(output_path)
        _adhoc_sign_macho(output_path)


def _normalize_macho_uuid(path: Path) -> None:
    data = bytearray(path.read_bytes())
    if len(data) < 32:
        raise RuntimeError(f"Invalid Mach-O file: {path}")

    magic = struct.unpack_from("<I", data, 0)[0]
    if magic != 0xFEEDFACF:
        raise RuntimeError(f"Unsupported Mach-O format for UUID normalization: {path}")

    ncmds = struct.unpack_from("<I", data, 16)[0]
    offset = 32
    for _ in range(ncmds):
        if offset + 8 > len(data):
            raise RuntimeError(f"Truncated Mach-O load commands: {path}")
        cmd, cmdsize = struct.unpack_from("<II", data, offset)
        if cmdsize < 8 or offset + cmdsize > len(data):
            raise RuntimeError(f"Invalid Mach-O load command: {path}")
        if cmd == 0x1B:
            if cmdsize < 24:
                raise RuntimeError(f"Invalid LC_UUID command: {path}")
            uuid_start = offset + 8
            data[uuid_start : uuid_start + 16] = bytes(16)
            digest = hashlib.sha256(data).digest()[:16]
            data[uuid_start : uuid_start + 16] = digest
            path.write_bytes(data)
            return
        offset += cmdsize

    raise RuntimeError(f"Missing LC_UUID command: {path}")


def _adhoc_sign_macho(path: Path) -> None:
    codesign = shutil.which("codesign")
    if not codesign:
        raise RuntimeError("codesign is required to build loadable macOS wheels")
    try:
        subprocess.run(
            [codesign, "--force", "--sign", "-", "--timestamp=none", str(path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip()
        raise RuntimeError(f"Failed to ad-hoc sign Mach-O library: {detail}") from exc


def _resolve_c_compiler() -> str:
    candidates = [os.environ.get("CC"), "cc", "clang", "gcc"]
    for candidate in candidates:
        if candidate and shutil.which(candidate):
            return candidate
    raise RuntimeError("No C compiler found. Set CC or install clang/gcc.")
