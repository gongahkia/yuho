"""migrate_g12_workaround.py — collapse the two-sibling-penalty G12 workaround
into the new nested-combinator form.

Pattern we collapse:

    penalty cumulative {
      imprisonment := X .. Y;
      supplementary := "...";
    }
    penalty or_both {
      fine := unlimited;
      caning := unspecified;
      supplementary := "...";
    }

becomes:

    penalty cumulative {
      imprisonment := X .. Y;
      or_both {
        fine := unlimited;
        caning := unspecified;
      }
    }

Conservative — only touches sections where:
  - The section has EXACTLY two penalty blocks at the same scope level
  - Neither block uses `when <ident>` (those are G9 branches, not G12)
  - Block 1 contains only imprisonment (+ optional supplementary)
  - Block 2 does NOT contain imprisonment; contains fine and/or caning

Dry-run by default; pass --write to apply. Runs `yuho check` before
writing and fails out if the migrated file doesn't parse.
"""
from __future__ import annotations
import argparse, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
YUHO = REPO / ".venv-scrape" / "bin" / "yuho"

PENALTY_RE = re.compile(
    r"""
    ^(?P<indent>[ \t]*)                    # leading indent
    penalty                                # keyword
    (?:\s+(?P<combinator>cumulative|alternative|or_both))?   # optional combinator
    (?!\s+when\s)                          # reject `penalty when ...` (G9)
    \s*\{                                  # open brace
    (?P<body>(?:[^{}]|\{[^{}]*\})*)        # body — allow one level of nesting inside
    \}
    """,
    re.MULTILINE | re.VERBOSE,
)

def find_penalty_blocks(text: str) -> list[re.Match]:
    """Return all matches of top-level penalty blocks."""
    return list(PENALTY_RE.finditer(text))

def has_clause(body: str, clause: str) -> bool:
    return bool(re.search(rf"^\s*{clause}\s*:=", body, re.MULTILINE))

def is_imprisonment_only(body: str) -> bool:
    """True if body has imprisonment and only supplementary as optional extra."""
    if not has_clause(body, "imprisonment"): return False
    if has_clause(body, "fine"): return False
    if has_clause(body, "caning"): return False
    if has_clause(body, "death"): return False
    return True

def is_fine_caning_only(body: str) -> bool:
    """True if body has fine and/or caning but no imprisonment."""
    if has_clause(body, "imprisonment"): return False
    return has_clause(body, "fine") or has_clause(body, "caning")

def indent_body(body: str, extra: str) -> str:
    """Re-indent every non-empty line by `extra` spaces."""
    out = []
    for line in body.splitlines():
        if line.strip(): out.append(extra + line)
        else: out.append(line)
    return "\n".join(out)

def migrate_file(yh: Path) -> tuple[bool, str, str]:
    """Return (changed, reason_if_not_changed, new_text)."""
    text = yh.read_text()
    matches = find_penalty_blocks(text)
    if len(matches) != 2: return False, f"{len(matches)} penalty blocks (need exactly 2)", text

    m1, m2 = matches
    b1, b2 = m1.group("body"), m2.group("body")
    c1, c2 = m1.group("combinator") or "cumulative", m2.group("combinator") or "cumulative"

    if not is_imprisonment_only(b1):
        return False, "first block is not imprisonment-only", text
    if not is_fine_caning_only(b2):
        return False, "second block is not fine/caning-only", text
    if c2 == "cumulative":
        return False, "second block has no clear combinator (was default cumulative)", text

    # Construct nested form. Keep the first block's indent scheme.
    outer_indent = m1.group("indent")
    inner_indent = outer_indent + "    "
    sub_indent = inner_indent + "    "

    # Strip the old trailing supplementary from block 2 — we move its content
    # into the nested block body verbatim.
    # Actually, preserve everything that was in block 2 (except its own braces).
    nested_body = b2.strip("\n")
    # body of b1 stays unchanged, just strip trailing whitespace
    imprisonment_body = b1.rstrip()

    new_block = (
        f"{outer_indent}penalty {c1} {{"
        f"\n{imprisonment_body}"
        f"\n"
        f"\n{inner_indent}{c2} {{"
        f"\n{indent_body(nested_body.strip('\n'), '    ')}"
        f"\n{inner_indent}}}"
        f"\n{outer_indent}}}"
    )

    # Replace matched text: from start of m1 to end of m2, spanning any
    # whitespace between them.
    start, end = m1.start(), m2.end()
    new_text = text[:start] + new_block + text[end:]
    return True, "", new_text

def check_yuho(yh: Path) -> bool:
    r = subprocess.run(
        [str(YUHO), "check", "--format", "json", str(yh)],
        capture_output=True, text=True, timeout=60,
    )
    try:
        import json as _j
        return _j.loads(r.stdout).get("valid", False)
    except Exception:
        return False

def main() -> None:
    p = argparse.ArgumentParser(prog="migrate_g12_workaround", description=__doc__)
    p.add_argument("--write", action="store_true", help="actually apply changes")
    p.add_argument("--limit", type=int, help="stop after N migrations (for smoke tests)")
    args = p.parse_args()

    changed = 0
    skipped = 0
    failed = 0
    for yh in sorted((REPO / "library" / "penal_code").glob("s*/statute.yh")):
        ok, reason, new_text = migrate_file(yh)
        if not ok:
            skipped += 1
            continue
        if args.limit and changed >= args.limit: break
        if args.write:
            original = yh.read_text()
            yh.write_text(new_text)
            if check_yuho(yh):
                changed += 1
                print(f"[migrated] {yh.parent.name}")
            else:
                yh.write_text(original)
                failed += 1
                print(f"[FAIL] {yh.parent.name} — migration broke yuho check, reverted")
        else:
            changed += 1
            print(f"[would migrate] {yh.parent.name}")
    print(f"\nsummary: {'wrote' if args.write else 'would write'} {changed}, skipped {skipped}, failed {failed}")

if __name__ == "__main__":
    main()
