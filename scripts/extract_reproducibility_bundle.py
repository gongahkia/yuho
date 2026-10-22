#!/usr/bin/env python3
"""Extract a research bundle, preserving its two exact negative symlink fixtures."""

from __future__ import annotations

import argparse
import os
from pathlib import Path, PurePosixPath
import tarfile


NEGATIVE_LINKS = {
    "test/model-bundle-fixtures/bundles/MB22-symlink/artifacts/sha256/2408d0a51cd717a8734137f246be3eb4331a9955a312fd24ce5a778393c27821": "/etc/passwd",
    "test/model-bundle-fixtures/bundles/MB32-review-symlink/reviews/review:1.json": "/etc/passwd",
}


def extract_bundle(archive: Path, destination: Path) -> Path:
    with tarfile.open(archive) as tar:
        regular = []
        links = {}
        roots = set()
        names = set()
        for member in tar.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError("unsafe bundle path: " + member.name)
            if member.name.rstrip("/") != str(path) or str(path) in names:
                raise ValueError("noncanonical or duplicate bundle path")
            names.add(str(path))
            roots.add(path.parts[0])
            relative = str(PurePosixPath(*path.parts[1:]))
            if member.issym():
                if NEGATIVE_LINKS.get(relative) != member.linkname:
                    raise ValueError("unexpected symlink: " + member.name)
                links[relative] = member.linkname
            elif member.isfile() or member.isdir():
                regular.append(member)
            else:
                raise ValueError("unsupported bundle entry type")
        if len(roots) != 1 or set(links) != set(NEGATIVE_LINKS):
            raise ValueError("bundle root or exact negative-fixture set differs")
        destination.mkdir(parents=True, exist_ok=False)
        # No symlinks exist during regular extraction; data filtering remains on.
        tar.extractall(destination, members=regular, filter="data")
    source = destination / roots.pop()
    for relative, target in links.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        # Preserve the original lstat rejection fixtures; never open their target.
        os.symlink(target, path)
    return source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(extract_bundle(args.archive.resolve(), args.output_dir.resolve()))


if __name__ == "__main__":
    main()
