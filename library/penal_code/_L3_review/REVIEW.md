# L3 flag manual review

Generated review of all 126 flagged sections.

## Summary by verdict

| Verdict | Count | Meaning |
|---|--:|---|
| `STAMP_OVERRIDE` | 0 | Flag is likely spurious. Encoding addresses the concern; safe to override and stamp. |
| `FIX_NEEDED` | 2 | Flag is correct; mechanical fix is plausible. |
| `INVESTIGATE` | 124 | Needs a human read — the heuristic can't decide. |

## Summary by failed check

| Check | Description | Count |
|--:|---|--:|
| -1 | (no machine-readable failed-check code) | 23 |
| 3 | Illustrations complete | 1 |
| 4 | Explanations preserved | 2 |
| 5 | Exceptions preserved | 1 |
| 6 | Subsections preserved | 10 |
| 7 | No fabricated penalty facts | 31 |
| 8 | all_of vs any_of matches English | 20 |
| 9 | Effective date sane | 38 |

## Per-check files

- [check-1.md](./check-1.md) — (no machine-readable failed-check code) (23 sections)
- [check3.md](./check3.md) — Illustrations complete (1 sections)
- [check4.md](./check4.md) — Explanations preserved (2 sections)
- [check5.md](./check5.md) — Exceptions preserved (1 sections)
- [check6.md](./check6.md) — Subsections preserved (10 sections)
- [check7.md](./check7.md) — No fabricated penalty facts (31 sections)
- [check8.md](./check8.md) — all_of vs any_of matches English (20 sections)
- [check9.md](./check9.md) — Effective date sane (38 sections)

## How to use this review

1. For each `check<N>.md` file, scan the verdicts at the top of each block.
2. Group by verdict and act:
   - `STAMP_OVERRIDE` — manually stamp via metadata.toml (`last_verified = "YYYY-MM-DD"`).
   - `FIX_NEEDED` — apply the suggested fix to `statute.yh`, re-run `yuho check`, then stamp.
   - `INVESTIGATE` — open the section dir, read `_L3_FLAG.md` and the canonical SSO text together.
3. After resolving a flag, delete `_L3_FLAG.md` and add a `last_verified` line to `metadata.toml`.
4. Rebuild the corpus + ledger to reflect changes.
