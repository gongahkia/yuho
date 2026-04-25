#!/usr/bin/env python3
"""Generate manifest.firefox.json from manifest.json for Firefox MV3.

Firefox MV3 is mostly compatible with Chrome's MV3, with two key
differences:

1. ``background.service_worker`` is supported (Firefox 121+) but the
   ``scripts`` form has wider compatibility (115+); for the broadest
   reach we emit ``scripts: ["..."]`` instead of ``service_worker``.
2. ``browser_specific_settings.gecko`` is required for AMO submission
   and gates the minimum Firefox version we target.

Other manifest fields (action, content_scripts, host_permissions,
permissions, web_accessible_resources, icons) work as-is.

Usage:
    python3 build_firefox_manifest.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "manifest.json"
DEST = HERE / "manifest.firefox.json"


def main() -> int:
    with SRC.open("r", encoding="utf-8") as f:
        chrome = json.load(f)

    firefox = dict(chrome)

    # Background: use scripts form for Firefox 115+ compatibility.
    bg = firefox.get("background", {})
    if "service_worker" in bg:
        firefox["background"] = {
            "scripts": [bg["service_worker"]],
            "type": bg.get("type", "module"),
        }

    # Required for AMO.
    firefox["browser_specific_settings"] = {
        "gecko": {
            "id": "yuho@gabrielongzm.com",
            "strict_min_version": "115.0",
        }
    }

    DEST.write_text(json.dumps(firefox, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"wrote {DEST.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
