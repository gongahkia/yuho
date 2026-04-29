"""Run `yuho test` across every behavioural-test fixture in
`library/penal_code/*/test_statute.yh` and assert all pass.

Companion to `tests/test_library_statutes.py` (which only enforces
parse + lint validity, not runtime assertion truth). This script
closes the contract gap surfaced 2026-04-29: with the comment-strip
sweep applied, every rich test's `assert` lines are evaluable
end-to-end by the interpreter, and the runtime sweep becomes a
load-bearing CI claim.

Exit codes:
  0 — all 90/90 rich tests pass
  1 — at least one fixture fails or errors (full breakdown to stderr)
  2 — internal error (file-system / yuho CLI not importable)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LIBRARY = REPO / "library" / "penal_code"


def main() -> int:
    if not LIBRARY.is_dir():
        print(f"library not found: {LIBRARY}", file=sys.stderr)
        return 2

    files = sorted(LIBRARY.glob("*/test_statute.yh"))
    rich = [p for p in files if "assert" in p.read_text(encoding="utf-8")]

    print(f"→ runtime-sweeping {len(rich)} rich test_statute.yh files…")

    passed = 0
    failed: list[tuple[str, str]] = []
    errored: list[tuple[str, str]] = []
    for p in rich:
        statute_path = p.parent / "statute.yh"
        result = subprocess.run(
            [sys.executable, "-m", "yuho.cli.main", "test", str(statute_path)],
            capture_output=True, text=True, timeout=60,
        )
        out = (result.stdout + result.stderr).strip()
        if result.returncode == 0 and ("PASS" in out or "All" in out):
            passed += 1
            continue
        last_line = out.splitlines()[-1] if out else "<no output>"
        if "Assertion failed" in out or "FAIL" in out:
            failed.append((p.parent.name, last_line[:160]))
        else:
            errored.append((p.parent.name, last_line[:160]))

    print(f"runtime sweep: PASS={passed}/{len(rich)}  FAIL={len(failed)}  ERR={len(errored)}")
    if failed:
        print("Assertion failures:", file=sys.stderr)
        for name, msg in failed:
            print(f"  {name}: {msg}", file=sys.stderr)
    if errored:
        print("Errors:", file=sys.stderr)
        for name, msg in errored:
            print(f"  {name}: {msg}", file=sys.stderr)

    return 0 if not (failed or errored) else 1


if __name__ == "__main__":
    sys.exit(main())
