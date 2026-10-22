#!/usr/bin/env python3
"""Create a deterministic private research candidate from Git sources and sdist.

Rights clearance/publication is a separate owner decision. No Git metadata,
untracked local files, caches, compiler binaries or downloaded tools are included.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile

from extract_reproducibility_bundle import NEGATIVE_LINKS


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT) or output.exists():
        raise SystemExit("output must be a new path outside the checkout")
    version = re.search(r"^version:\s*(\S+)", (ROOT / "yuho.cabal").read_text(), re.M).group(1)
    prefix = "yuho-reproducibility-" + version
    sdk = args.sdk_archive.resolve()
    names = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")) - {""}
    with tarfile.open(sdk) as tar:
        for member in tar.getmembers():
            if not member.isfile():
                if not member.isdir():
                    raise SystemExit("nonregular SDK archive entry")
                continue
            relative = Path(member.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise SystemExit("unsafe SDK archive path")
            relative = Path(*relative.parts[1:])
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != tar.extractfile(member).read():
                raise SystemExit("SDK archive differs from candidate: " + str(relative))
            names.add(str(relative))
    # This release script is a source resource, never an arbitrary untracked glob.
    names.add("scripts/generate_reproducibility_bundle.py")
    spec = importlib.util.spec_from_file_location("prior_bytes", ROOT / "test/prior_bytes.py")
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    historical = prior.baseline_archive()
    digest = hashlib.sha256(historical).hexdigest()
    if digest != prior.BASELINE_ARCHIVE_SHA256:
        raise SystemExit("historical Git archive differs from pinned distribution digest")
    info = {"source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "source_state": "working-tree release candidate; not an independently accepted commit",
            "sdk_archive_sha256": hashlib.sha256(sdk.read_bytes()).hexdigest(),
            "historical_commit": prior.BASELINE, "historical_archive_sha256": digest,
            "rights": "Third-party statutory/research redistribution requires separate clearance"}
    contents = {}
    links = {}
    for name in sorted(names):
        path = ROOT / name
        if path.is_symlink():
            target = os.readlink(path)
            if NEGATIVE_LINKS.get(name) != target:
                raise SystemExit("unexpected source symlink: " + name)
            links[name] = target
            continue
        if not path.is_file():
            raise SystemExit("nonregular source path: " + name)
        contents[name] = (path.read_bytes(), 0o755 if path.stat().st_mode & 0o111 else 0o644)
    if set(links) != set(NEGATIVE_LINKS):
        raise SystemExit("negative symlink fixture inventory differs")
    contents["reproducibility/prior-kernel.tar"] = (historical, 0o644)
    contents["reproducibility/BUILD-INFO.json"] = ((json.dumps(info, sort_keys=True, indent=2) + "\n").encode(), 0o644)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for name in sorted(set(contents) | set(links)):
                    data, mode = contents.get(name, (b"", 0o777))
                    member = tarfile.TarInfo(prefix + "/" + name)
                    member.size = len(data)
                    member.mode = mode
                    member.mtime = 0
                    member.uid = member.gid = 0
                    member.uname = member.gname = ""
                    if name in links:
                        member.type = tarfile.SYMTYPE
                        member.linkname = links[name]
                    tar.addfile(member, io.BytesIO(data))
    print(json.dumps({"output": str(output), "files": len(contents), "negative_symlinks": len(links),
                      "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
