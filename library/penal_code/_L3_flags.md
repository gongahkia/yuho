# Phase D L3 — flagged sections for human review

_Aggregated from per-section `_L3_FLAG.md` files. Regenerate by re-running `phase_d_l3_review.py`._

## s21 — L3 flag

- failed: 9
- reason: The encoding includes amendment markers for later 2016/2019 changes but does not include matching later `effective` clause(s), so the section’s amendment chronology is incomplete.
- suggested fix: Add the missing later effective date clause(s) that correspond to the 2016/2019 amendment markers before re-running L3 review.

## s73 — L3 flag

- failed: 9
- reason: The encoding omits the 2019 commencement date even though the canonical entry carries a `[15/2019]` amendment marker, so `effective 1872-01-01` and `effective 2022-03-01` alone are not sane.
- suggested fix: Verify and add the section’s 2019 effective date, then retain the existing 2022 amendment date.

## s304C — L3 flag

- failed: 7
- reason: Subsection (4) is not faithfully encoded because the statute makes imprisonment mandatory with additional liability to fine or to caning, but the `.yh` models only the fine branch machine-readably and leaves caning only in supplementary text.
- suggested fix: Encode both alternative supplementary punishments in subsection (4) without inventing a caning quantum that the statute does not state.

## s376 — L3 flag

- failed: 7
- reason: The encoding fabricates caning ranges (`0 .. 24` in subsection (3) and `12 .. 24` in subsection (4)) even though the canonical text states only liability to caning in subsection (3) and a minimum of 12 strokes in subsection (4).
- suggested fix: Remove the invented caning maxima and preserve the exact caning language only through faithful structured text or supplementary text without adding unstated numeric limits.

## s376H — L3 flag

- failed: 7
- reason: The encoding omits the canonical subsection `(2)(a)` penalty branch and therefore does not faithfully capture all conditional penalties in section 376H.
- suggested fix: Re-encode subsection `(2)` with both statutory penalty branches from the authoritative text, then rerun `yuho check`.

## s377 — L3 flag

- failed: 7
- reason: The canonical subsection (3) makes the offender liable to fine or to caning, but the encoding preserves only the fine branch and drops caning.
- suggested fix: Add the missing caning alternative to subsection (3) so the penalty structure fully matches the statute.

## s377BB — L3 flag

- failed: 7
- reason: The encoding drops the statute's express caning punishment in subsections (7) and (8) as structured penalty facts and leaves it only in supplementary text.
- suggested fix: Add explicit `caning :=` penalty clauses for subsections (7) and (8) so the punishment branches fully match the canonical text.

## s377BD — L3 flag

- failed: 7
- reason: Subsection (3) encodes only `fine := unlimited` for the “liable to fine or to caning” branch and omits any `caning :=` clause, so the penalty facts are incomplete.
- suggested fix: Model subsection (3)’s alternative branch with both fine and caning liability instead of leaving caning only in supplementary text.

## s377BG — L3 flag

- failed: 7
- reason: Subsection (2) in the encoding captures imprisonment and an unlimited fine but omits the alternative caning branch stated in the canonical text (“liable to fine or to caning”).
- suggested fix: Add a caning penalty branch for subsection (2) without inventing any unstated stroke count.

