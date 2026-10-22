#!/usr/bin/env python3
"""Check retained notice evidence and archive inclusion, not legal clearance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


REQUIRED = ["LICENSE", "NOTICE", "docs/third-party-notices.md",
            "docs/legislation-notice.md", "docs/owner-authorisation.md",
            "docs/distribution-boundaries.md", "release/owner-apache-authorisation.json"]
LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
ANSWER = "Approve Apache-2.0 for authorised original materials"
ITEM = '["request_user_input_async","call_c84fdd68b28a476aadf4b1fb155ea0f8",0]'


def check_notices(files: dict[str, bytes]) -> list[str]:
    errors = ["missing notice resource: " + p for p in REQUIRED if p not in files]
    if errors:
        return errors
    if hashlib.sha256(files["LICENSE"]).hexdigest() != LICENSE_SHA256:
        errors.append("standard Apache text differs")
    for p in ["NOTICE", "docs/legislation-notice.md"]:
        text = " ".join(files[p].decode().lower().split())
        for phrase in ["copyright of the singapore government", "permission of agc",
                       "https://sso.agc.gov.sg/", "responsible for ensuring the accuracy",
                       "not associated or affiliated", "do not endorse", "conditions"]:
            if phrase not in text:
                errors.append(p + ": missing " + phrase)
    notice = " ".join(files["NOTICE"].decode().lower().split())
    if "acquisition and accuracy review remain outstanding" not in notice:
        errors.append("NOTICE: clearance limitation absent")
    try:
        record = json.loads(files["release/owner-apache-authorisation.json"])
        if (record.get("license") != "Apache-2.0" or record.get("answer") != ANSWER
                or record.get("question_item_id") != ITEM
                or "third-party statutory text" not in record.get("exclusions", [])
                or record.get("approval_timestamp") is not None):
            errors.append("owner evidence differs from supplied approval")
    except (ValueError, AttributeError):
        errors.append("invalid owner evidence")
    return errors


def archive_files(path: Path) -> dict[str, bytes]:
    files = {}
    names = set()
    roots = set()
    with tarfile.open(path) as tar:
        for member in tar:
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or len(name.parts) < 2:
                if member.isdir() and len(name.parts) == 1:
                    continue
                raise ValueError("unsafe archive path")
            if str(name) in names:
                raise ValueError("duplicate archive path")
            names.add(str(name))
            roots.add(name.parts[0])
            if member.isfile():
                files[str(PurePosixPath(*name.parts[1:]))] = tar.extractfile(member).read()
        if len(roots) != 1:
            raise ValueError("expected one archive root")
    return files


def check_archive(path: Path, expected: dict[str, bytes]) -> list[str]:
    files = archive_files(path)
    errors = check_notices(files)
    errors += ["archive notice differs: " + p for p in REQUIRED
               if p in files and files[p] != expected[p]]
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--archive", type=Path, action="append", default=[])
    args = parser.parse_args()
    files = {p: (args.root / p).read_bytes() for p in REQUIRED if (args.root / p).is_file()}
    errors = check_notices(files)
    if not errors:
        for archive in args.archive:
            errors.extend(check_archive(archive, files))
    if errors:
        raise SystemExit("\n".join(errors))
    print("Notice/evidence inclusion verified; redistribution clearance is not established")


if __name__ == "__main__":
    main()
