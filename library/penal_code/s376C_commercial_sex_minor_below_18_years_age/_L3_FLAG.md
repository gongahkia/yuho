# s376C — L3 flag

- failed: 9
- reason: The encoded statute uses `effective 2020-01-01` even though comparable Penal Code sections introduced by the same `[15/2019]` amendment in this codebase use `2019-12-31`, so the amendment effective date is not sane enough to stamp.
- suggested fix: Verify the commencement date for Act 15 of 2019 for section 376C and update the `effective` clause to the correct date before rerunning L3 review.
