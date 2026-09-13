"""Compatibility entry point for the reviewed section 84 surface model."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rewrite.frontend.core import *  # noqa: E402,F403 - historical test API
from rewrite.frontend.core import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
