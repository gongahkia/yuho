# Phase C Orchestration — running Codex + Claude agents in parallel

This doc is for the human dispatching agents. The agent-facing prompt lives
in `PHASE_C_ENCODING_PROMPT.md`; the dispatcher is `scripts/phase_c_prompt.py`.

## Typical loop

```bash
# 1. Refresh coverage so --list / --next reflect current state
.venv-scrape/bin/python scripts/coverage_report.py \
    --act-dir library/penal_code --yuho ./.venv-scrape/bin/yuho

# 2. See what's unencoded
.venv-scrape/bin/python scripts/phase_c_prompt.py --list | head -20

# 3. Dispatch a batch — one prompt per agent. Copy-paste into each:
.venv-scrape/bin/python scripts/phase_c_prompt.py 34 | pbcopy   # → Codex tab 1
.venv-scrape/bin/python scripts/phase_c_prompt.py 35 | pbcopy   # → Claude tab 1
.venv-scrape/bin/python scripts/phase_c_prompt.py 36 | pbcopy   # → Codex tab 2
# ...

# 4. After agents finish, recompute coverage and review diffs
.venv-scrape/bin/python scripts/coverage_report.py \
    --act-dir library/penal_code --yuho ./.venv-scrape/bin/yuho
git status --short library/penal_code/
```

## Dispatch patterns

### Sequential (safe, slow)

One agent at a time:

```bash
.venv-scrape/bin/python scripts/phase_c_prompt.py --next 1 | pbcopy
```

### Batched parallel (recommended)

Copy multiple prompts at once, split by sentinel:

```bash
.venv-scrape/bin/python scripts/phase_c_prompt.py --next 10 --stdout-split \
    > /tmp/batch.txt
csplit -z -f /tmp/batch_ -b '%02d.md' /tmp/batch.txt \
    '/<<<---NEXT_SECTION--->>>/' '{*}'
# each /tmp/batch_NN.md is a standalone prompt for one section
```

Hand each file to a separate agent session.

## Codex vs Claude — soft allocation heuristic

Not a hard rule. Both models can handle any section. But in practice:

| Send to Codex | Send to Claude |
|---|---|
| pure punishment sections ("Whoever commits X shall be punished…") | sections with nuanced legal doctrine (defences, exceptions) |
| straightforward offences with clear actus reus / mens rea | mens rea gradients (rashness / negligence / knowledge) |
| interpretation sections (definitions only) | cross-section scope modifiers (s511 attempt, s107 abetment) |
| mechanical template application | sections where the legal meaning is genuinely contested |

Don't over-optimize. If Codex is busy, give the section to Claude and vice versa.

## Quality gating before commit

After a batch finishes and agents have written to their directories:

1. **Re-run coverage harness** — any L1- or L2-red section is broken; re-dispatch or fix by hand.
2. **Eyeball each encoding** — open two or three `.yh` files from the batch. Look for:
   - Legal-logic shortcuts (`actus_reus act := "does the thing"` type placeholders)
   - Wrong classification (an offence encoded as interpretation, etc.)
   - Free-form string wraps where a `match` / element group would fit better
3. **Collect GAPS** — run:
   ```bash
   find library/penal_code -name GAPS.md -newer library/penal_code/_coverage/coverage.json
   ```
   Append each agent's gaps to a running `doc/PHASE_C_GAPS.md` (create when first gap lands). This is the input to Phase D.

## Commit strategy

Per-section commits generate too much noise during mass ingest. Use batched commits:

```bash
# stage everything in a batch
git add library/penal_code/s34_* library/penal_code/s35_* library/penal_code/s36_*
git commit -m "encode PC sections 34-36"  # ≤5 words
```

Revert to per-file commits once mass-ingest is done and you're doing surgical edits.

## Duplicate-dispatch protection

The dispatcher already filters by `coverage.json`, so `--next K` will never emit a section that's already encoded. But if two agents somehow race on the same number and both write files:

```bash
# see if any section has duplicate dirs
ls library/penal_code | grep -E '^s[0-9]+[A-Z]?_' | \
    sed -E 's/^(s[0-9]+[A-Z]?)_.*/\1/' | sort | uniq -d
```

Keep the better one; `rm -rf` the other.

## Scale limits

- **Git merge risk**: near zero — each agent writes to a disjoint directory.
- **Yuho check contention**: none — check is a short-lived subprocess per file; 100 concurrent runs is fine on any modern laptop.
- **Your attention bandwidth**: the real limit. 10–15 agents in flight at once is the sweet spot; beyond that you can't meaningfully QA the output.

## Failure modes to watch for

| Symptom | Likely cause | Fix |
|---|---|---|
| agent emits a `.yh` that parses but encodes nothing meaningful (just text strings in definitions) | section doesn't fit Yuho's offence shape and agent didn't write `GAPS.md` | reject; re-dispatch with instruction to classify first |
| agent uses placeholder text ("TODO", "scaffolded") despite prompt ban | prompt not fully read | reject; re-dispatch |
| L2 fails with a semantic error the agent didn't catch | agent didn't have shell access and couldn't iterate | fix by hand, or re-dispatch to a shell-capable agent |
| two sections with wildly different encoding styles | different models, different idioms | acceptable initially; normalize in Phase C2 review |
| GAPS.md accumulates but no one reads it | orchestration oversight | set a weekly review of `doc/PHASE_C_GAPS.md` |
