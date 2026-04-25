# s311 — L3 flag

- failed: 9
- reason: The section carries amendment markers `[15/2019]` and `[Act 23 of 2021 wef 01/03/2022]` but the encoding uses only `effective 1872-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Add later `effective` clauses for the post-1872 amendments, including `2022-03-01` and the verified commencement date for Act 15 of 2019, then rerun L3 review.
