#!/usr/bin/env python3
"""Generate a Word add-in manifest pointing at a chosen host.

The checked-in ``manifest.xml`` defaults to ``https://localhost:3000``
for sideload-during-development. To ship to a real host, run::

    python3 build_manifest.py --host https://yuho.dev/word \\
                              --version 0.4.0.0 \\
                              --output manifest.prod.xml

The output is a sibling file with every ``https://localhost:3000``
swapped for the supplied host, optionally bumping ``<Version>`` and the
manifest ``<Id>`` (a fresh GUID is recommended for each public release
of an add-in to avoid AppSource cache collisions).

Usage:
    python3 build_manifest.py [--host URL] [--version V] [--id GUID]
                              [--output PATH]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "manifest.xml"
DEFAULT_OUT = HERE / "manifest.prod.xml"
LOCALHOST = "https://localhost:3000"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--host", required=True,
                    help="absolute base URL, no trailing slash (e.g. https://yuho.dev/word)")
    ap.add_argument("--version", default=None,
                    help="optional 4-part version override (e.g. 0.4.0.0)")
    ap.add_argument("--id", default=None, dest="addin_id",
                    help="optional GUID override for <Id>")
    ap.add_argument("--output", default=str(DEFAULT_OUT),
                    help=f"output path (default: {DEFAULT_OUT.name})")
    args = ap.parse_args()

    host = args.host.rstrip("/")
    text = SRC.read_text(encoding="utf-8")
    text = text.replace(LOCALHOST, host)

    if args.version:
        text = re.sub(r"<Version>[^<]+</Version>",
                      f"<Version>{args.version}</Version>", text, count=1)
    if args.addin_id:
        text = re.sub(r"<Id>[^<]+</Id>",
                      f"<Id>{args.addin_id}</Id>", text, count=1)

    Path(args.output).write_text(text, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
