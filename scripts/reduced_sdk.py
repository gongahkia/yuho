#!/usr/bin/env python3
"""Build/verify the exact private SDK proposal; no rights or publication grant."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "release/reduced-sdk-inventory.json"
INVENTORY_SHA256 = "810a2b5a71200dfeb2a9c3b037ccb4eb7e5ca9eaba3da9f43497e48bf1ab0fc3"


def canonical(name: str, directory: bool = False) -> str:
    value = name[:-1] if directory and name.endswith("/") else name
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or ".." in path.parts or "." in value.split("/")
            or "\\" in value or ":" in value or str(path) != value):
        raise ValueError("noncanonical/unsafe path: " + name)
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate inventory key: " + key)
        result[key] = value
    return result


def load_inventory(path: Path = INVENTORY) -> dict:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != INVENTORY_SHA256:
        raise ValueError("unreviewed inventory change; explicit inventory/pin review required")
    doc = json.loads(data, object_pairs_hook=unique_object)
    if doc["owner_approved"] is not False:
        raise ValueError("this tooling does not confer owner approval")
    canonical(doc["package_root"])
    names = [canonical(r["path"]) for r in doc["files"]]
    if names != sorted(set(names)) or len(set(n.casefold() for n in names)) != len(names):
        raise ValueError("duplicate/ambiguous inventory paths")
    for row in doc["files"]:
        canonical(row["source"])
        if row["type"] != "file" or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"]):
            raise ValueError("invalid inventory type/digest")
    return doc


def source_files(root: Path, inventory: dict) -> dict[str, bytes]:
    result = {}
    for row in inventory["files"]:
        path = root / row["source"]
        if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
            raise ValueError("source symlink refused: " + row["source"])
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("unreviewed source bytes: " + row["source"])
        result[row["path"]] = data
    return result


def checked_archive(archive: Path, inventory: dict) -> dict[str, bytes]:
    expected = {r["path"]: r["sha256"] for r in inventory["files"]}
    prefix = inventory["package_root"]
    directories = {prefix}
    for name in expected:
        directories.update(str(p) for p in PurePosixPath(prefix + "/" + name).parents if str(p) != ".")
    seen = set()
    folded = set()
    actual = {}
    with tarfile.open(archive) as tar:
        for member in tar:
            name = canonical(member.name, member.isdir())
            if name in seen or name.casefold() in folded:
                raise ValueError("duplicate/ambiguous archive path: " + name)
            seen.add(name)
            folded.add(name.casefold())
            if member.isdir():
                if name not in directories:
                    raise ValueError("unexpected directory: " + name)
                continue
            if not member.isfile() or member.sparse or member.mode & 0o7000:
                raise ValueError("nonregular/unsafe archive type: " + name)
            if not name.startswith(prefix + "/"):
                raise ValueError("unexpected package root: " + name)
            relative = name[len(prefix) + 1:]
            if relative not in expected:
                raise ValueError("unexpected archive member: " + relative)
            data = tar.extractfile(member).read()
            if hashlib.sha256(data).hexdigest() != expected[relative]:
                raise ValueError("archive digest mismatch: " + relative)
            actual[relative] = data
    missing = set(expected) - set(actual)
    if missing:
        raise ValueError("missing archive members: " + ", ".join(sorted(missing)))
    return actual


def stage(root: Path, destination: Path, inventory: dict) -> None:
    if destination.resolve().is_relative_to(root.resolve()):
        raise ValueError("stage must be a new directory outside the checkout")
    contents = source_files(root, inventory)
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in contents.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    verify_stage(destination, inventory)


def verify_stage(destination: Path, inventory: dict) -> None:
    expected = {r["path"]: r["sha256"] for r in inventory["files"]}
    files = {}
    for path in destination.rglob("*"):
        if path.is_symlink():
            raise ValueError("stage symlink refused")
        if path.is_file():
            files[str(path.relative_to(destination))] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif not path.is_dir():
            raise ValueError("nonregular stage entry")
    if files != expected:
        raise ValueError("stage path/digest inventory mismatch")


def build(root: Path, output: Path, inventory: dict) -> Path:
    if output.resolve().is_relative_to(root.resolve()):
        raise ValueError("output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    staged = output / "source"
    stage(root, staged, inventory)
    # This build helper is outside the archive's exact inventory.
    shutil.copyfile(staged / "cabal.project.sdk", staged / "cabal.project")
    check = subprocess.run(["cabal", "check"], cwd=staged, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(check.stdout, end="")
    if re.search(r"(?m)^Warning:", check.stdout):
        raise ValueError("Cabal packaging diagnostics require review")
    subprocess.run(["cabal", "v2-sdist", "all", "--output-directory=" + str(output.resolve())],
                   cwd=staged, check=True)
    archive = output / (inventory["package_root"] + ".tar.gz")
    checked_archive(archive, inventory)
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["build", "verify", "stage", "extract"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory", type=Path, default=INVENTORY)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    inventory = load_inventory(args.inventory)
    if args.operation == "build":
        archive = build(args.root, args.output, inventory)
    elif args.operation == "stage":
        stage(args.root, args.output, inventory)
        archive = None
    else:
        contents = checked_archive(args.archive, inventory)
        archive = args.archive
        if args.operation == "extract":
            if args.output.resolve().is_relative_to(args.root.resolve()):
                raise ValueError("extraction must be outside the checkout")
            args.output.mkdir(parents=True, exist_ok=False)
            for name, data in contents.items():
                path = args.output / inventory["package_root"] / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    print(json.dumps({"files": len(inventory["files"]), "owner_approved": False,
        "archive": str(archive) if archive else None,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest() if archive else None,
        "scope": "exact reduced SDK only; no research/repository/history clearance"}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, tarfile.TarError) as error:
        raise SystemExit(str(error))
