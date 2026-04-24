# Yuho — Outstanding Work

Tracking the Phase D re-encoding sweep and everything downstream of it.
Authoritative source for what's still undone once the current priority-
batch iteration settles.

## Full sweep (paused — to run after priority-batch iteration)

Re-encode every PC section that is not currently L3 using the Phase D
strict re-encoding prompt + new grammar primitives. Target ~490 sections.

Planned command (re-run when ready):

```bash
.venv-scrape/bin/python scripts/phase_d_reencode.py --all-remaining \
    --dispatch --parallel 8 --retries 1 --timeout 900 \
    --reasoning medium \
    --progress .phase_d_progress.jsonl --resume
```

- Uses Codex via ChatGPT subscription, `codex exec --full-auto`.
- Dispatcher: `scripts/phase_d_reencode.py`.
- Strict prompt: `doc/PHASE_D_REENCODING_PROMPT.md` — bans fabricated
  penalty caps, requires illustration preservation, mandates use of
  new primitives (subsection nesting, multi-effective, fine :=
  unlimited, penalty or_both / when, doc comments on element groups).
- `--resume` picks up from `.phase_d_progress.jsonl` so a killed /
  rate-limited run restarts cleanly.
- Estimated wall time: 1.5–3 h at parallel=8 on medium reasoning.
  Worst-case 5–6 h if Codex rate-limits kick in.

Pre-flight before launch:
- Confirm priority-batch sections (s350, s304A, s464, s511, s505, s420)
  passed a close human review. They are the fidelity benchmark.
- Decide whether to bump reasoning to `high` based on what priority-
  batch quality looks like. Lower reasoning is cheaper but may degrade
  fidelity on complex sections.
- Consider bumping parallel to 12 if priority batch shows no rate-limit
  errors on parallel=3.

Monitoring while it runs: the dispatcher prints one line per section
completion (`[done] sN (attempt K)` or `[failed] sN (attempt K)`), so
a Claude `Monitor` tailing the output file streams per-section events.

## After the sweep lands

1. Re-run coverage harness to confirm 524/524 L1+L2 green.
   ```bash
   .venv-scrape/bin/python scripts/coverage_report.py \
       --act-dir library/penal_code --yuho ./.venv-scrape/bin/yuho
   ```
2. Review `.phase_d_progress.jsonl` for `failed` entries; re-dispatch
   individually (or with `--retries 3`) and fix grammar gaps if the
   same section fails repeatedly.
3. Spot-check 20–30 random encodings against `_raw/act.json` for
   fidelity (illustrations present, no fabricated fine caps, correct
   subsection use).
4. Bulk-commit the sweep results with a clear message (e.g.
   `phase D wave 2 — bulk re-encoding of PC sections using new grammar`).
5. Update `doc/PHASE_C_GAPS.md` if new grammar gaps surface during the
   sweep.

## L3 review (deferred until after sweep)

499 sections are currently L1+L2 green, only 34 stamped L3. After the
sweep, do a structured L3 pass:

- Auto-stamp L3 on the trivial interpretation / definition sections
  where the encoding is a faithful mirror of one short sentence of
  statute text (lowest-risk bucket, ~60-80 sections).
- Manually review offence sections (elements + penalty present),
  prioritising the sections that still have ≥1 canonical illustration.
- Flag anything ambiguous to the human rather than stamping.

## Remaining grammar / tooling work (deferred)

- **G4**: illustration-count validation. Tooling check — fail lint when
  an encoded section has strictly fewer illustrations than
  `_raw/act.json` has canonical illustrations for that section.
- **G11**: `all_of` / `any_of` sanity check. Validation pass that
  cross-references the statute text's "or" / "and" connectives against
  the element-group combinator. Hard in general, approachable with an
  LLM judge or pattern match near element markers.
- **G10**: semantic hookup for cross-section references. The grammar
  already has `referencing`, `subsumes`, `amends`; semantic analyzer
  does not traverse them yet. Unblocks queries like "list sections that
  extend s415".
- Sub-linter for `fine := unlimited` omission: if raw statute text
  mentions "with fine" but no dollar amount, encoding must use
  `unlimited`. Prevents regressions.

## Phase 2 (still deferred from original roadmap)

- Historical versions — scrape pre-2020 revisions, thread `effective`
  dates through AST for temporal queries.
- Vision pivot — Evidence Act, Constitution, Contract Law once PC L3
  coverage is high.
