# s450 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent treats Act 15 of 2019 commencement as `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the unsound 2019 amendment effective date with the correct commencement date used consistently for Act 15 of 2019 in this repo, then re-run L3 review.
