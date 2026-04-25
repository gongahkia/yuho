# s410 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.
