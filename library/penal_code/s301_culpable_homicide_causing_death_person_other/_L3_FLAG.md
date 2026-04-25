# s301 — L3 flag

- failed: 9
- reason: The section is marked `[15/2019]` but the encoding uses `effective 2019-12-31`, while the Criminal Law Reform Act 2019 (Act 15 of 2019) entered into force on 2020-01-01, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later `effective` clause with the verified commencement date `2020-01-01`, then rerun L3 review.
