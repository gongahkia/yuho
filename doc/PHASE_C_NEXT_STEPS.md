# Phase C — Next Steps After Codex Finishes

Follow these in order. Each step is independent; pause anywhere.

## Step 1 — verify Codex's output

After Codex Cloud reports done, run the coverage harness to confirm all 524
sections are now encoded and pass L1+L2:

```bash
cd /Users/gongahkia/Desktop/coding/projects/yuho
./.venv-scrape/bin/python scripts/coverage_report.py \
    --act-dir library/penal_code \
    --yuho ./.venv-scrape/bin/yuho
```

Expected final line:

```
encoded=524/524 L1=524 L2=524 L3=25 → library/penal_code/_coverage
```

If any number is short, inspect the new `library/penal_code/_coverage/COVERAGE.md`
"Unencoded sections" table or the "Errors" section at the bottom.

## Step 2 — sanity-check a handful of encodings by eye

Agents produce encodings that pass the checker, but the checker does not
know legal correctness. Spot-check 5–10 at random before committing:

```bash
shuf -n 10 <(ls library/penal_code | grep -E '^s[0-9]') | while read d; do
    echo "=== $d ==="; cat "library/penal_code/$d/statute.yh"; echo
done | less
```

What to look for:

- **Right shape**: offence sections have `elements {}` + `penalty {}`; pure
  punishment sections cross-ref their target offence in a doc comment.
- **No placeholders**: search for `TODO`, `lorem`, `xxx`, `placeholder`.
- **No hollow encodings**: an `actus_reus` that's just `"does the thing"` is
  a fail; the agent should have captured the statute's actual elements.
- **Multi-letter suffix workaround**: sections like s376AA, s377BA are
  encoded as `statute <num>.<n>` with a `/// @section <original>` doc
  comment. That's the agreed-upon workaround until the grammar is fixed in
  Phase D. Do not "fix" those now.

If a sample looks thin or wrong, log it in `doc/PHASE_C_REVIEW.md` (create
if missing) with the section number and a one-line note. Don't block the
commit on it — corrections can be per-section edits later.

```bash
grep -rlE 'TODO|lorem|placeholder' library/penal_code/s*_*/statute.yh
```

## Step 3 — commit the bulk encoding

One commit for the whole phase, not per-section. Too noisy otherwise.

```bash
git status --short | head
git add library/penal_code/ scripts/coverage_report.py
git commit -m "$(cat <<'EOF'
encode remaining PC sections via phase C agents

Bulk encoding of the Singapore Penal Code 1871 by parallel Claude
subagents in two waves, then Codex Cloud for the final sections.

- library/penal_code/s*_*/statute.yh: ~473 newly encoded sections,
  each with metadata.toml. All pass yuho check (L1 parse + L2
  semantic). Total coverage: 524/524 L1+L2 green, 25 L3 verified
  (originals only; new encodings require human review before L3).
- scripts/coverage_report.py: fix regex so multi-letter section
  suffixes (376AA, 377BA-BO, 377CA, 377CB) are recognised.
- library/penal_code/_coverage/: regenerated dashboard.

Three Phase D expressiveness gaps surfaced during encoding — see
doc/PHASE_C_GAPS.md.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

## Step 4 — capture Phase D gap findings

Phase C's whole point is to surface grammar/AST gaps for the Phase D
refactor. Three concrete gaps surfaced during mass encoding:

Create `doc/PHASE_C_GAPS.md` with:

```markdown
# Phase C — Expressiveness Gaps

Surfaced during bulk encoding of the Singapore Penal Code. Each gap is a
concrete input to Phase D (AST/grammar refactor).

## G1 — element_group rejects preceding doc comments

`all_of { ... }` and `any_of { ... }` blocks cannot be preceded by a
`///` doc comment. Agents had to omit group-level rationale.

**Workaround:** attach doc comments only to `element_entry` siblings.

**Fix:** extend the grammar to allow `doc_comment*` before
`element_group`.

## G2 — colons break /// doc comments

A `:` anywhere inside a `///` doc comment causes a parse error.

**Workaround:** use `--` (em-dash) or commas instead.

**Fix:** lex `///` as opaque-until-EOL, or escape `:` inside doc
comments explicitly.

## G3 — section_number token only accepts single trailing letter

Grammar rule `section_number = \d+[A-Z]?` rejects multi-letter suffixes
like `376AA`, `377BA..377BO`, `377CA`, `377CB`. Affected ~25 real PC
sections.

**Workaround:** encode as `statute <num>.<n> "<title>"` with
`/// @section <original>` doc comment for traceability.

**Fix:** change token to `\d+[A-Z]*`. Also audit downstream consumers
(LSP, transpilers, CLI) that may assume single-letter suffix.

## Further findings to add as you review

- (blank for now; add as you find them during L3 review)
```

Commit this separately:

```bash
git add doc/PHASE_C_GAPS.md
git commit -m "$(cat <<'EOF'
document phase C expressiveness gaps

Three concrete AST/grammar gaps surfaced by parallel agents during
mass encoding of the Penal Code. These are the direct inputs to the
Phase D refactor.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

## Step 5 — update the roadmap

```bash
# mark Phase C as complete in roadmap.md
```

Open `roadmap.md`. Under "Phase C — Expressiveness probes", change the
section to note that mass encoding replaced the selective probe plan.
Reference `doc/PHASE_C_GAPS.md` as the finding log. Commit:

```bash
git add roadmap.md
git commit -m "mark phase C complete, phase D ready"
```

## Step 6 — L3 human review (longest step, optional in bulk)

L3 verification is the only remaining layer. All 499 new sections have
L3 = ✗ (no `last_verified` in metadata.toml). This is intentional —
machine-drafted encodings need human eyes before they count as authoritative.

Strategy options, in order of rigour:

**Option A — bulk scan, batch L3 (fastest, lowest fidelity)**
Read each `statute.yh` against the SSO URL in its `metadata.toml`
(already pre-filled). If it looks right, stamp L3 by setting in
`metadata.toml`:
```toml
[verification]
last_verified = "2026-04-24"
verified_by = "Your Name"
```
Estimate: ~2 min per section → ~17 hours for all 499.

**Option B — prioritized (recommended)**
L3 only the sections that matter for your use cases first (e.g. high-
frequency offences: theft, cheating, hurt, CBT — many already L3).
Leave rare/technical sections unverified until a user actually queries
them. Estimate: ~2–4 hours for a useful prioritized set.

**Option C — skip for now**
Accept L2-green as sufficient for Phase D planning. The 25 hand-
verified encodings remain the gold standard against which Phase D can
regression-test. Revisit L3 after the grammar refactor so you're not
double-reviewing pre- and post-refactor encodings.

I recommend **Option C → B → A**. Don't spend lunch breaks L3-ing
sections that may need regrammar'ing in Phase D anyway.

## Step 7 — Phase D kickoff

Once Phase C is committed and gaps are documented, Phase D planning is
the next conversation. Not a single-command step — it's a design session
driven by `doc/PHASE_C_GAPS.md` + any further findings from Step 6.

When you're ready to start Phase D, open a fresh Claude session and
open it with:

> Phase D of the Yuho revamp roadmap. Read `roadmap.md`,
> `doc/PHASE_C_GAPS.md`, and `doc/PHASE_C_NEXT_STEPS.md` to see
> Phase C's outputs. I want to scope the AST/grammar refactor.

---

## Quick reference — commands summary

```bash
# step 1: verify coverage
./.venv-scrape/bin/python scripts/coverage_report.py \
    --act-dir library/penal_code --yuho ./.venv-scrape/bin/yuho

# step 2: spot-check random encodings
shuf -n 10 <(ls library/penal_code | grep -E '^s[0-9]') | while read d; do
    echo "=== $d ==="; cat "library/penal_code/$d/statute.yh"; echo
done | less

# step 2 sanity: look for placeholder text
grep -rlE 'TODO|lorem|placeholder' library/penal_code/s*_*/statute.yh

# step 3 and onward: see body above
```
