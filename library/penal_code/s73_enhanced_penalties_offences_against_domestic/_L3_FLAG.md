# s73 — L3 flag

- failed: 9
- reason: The encoding omits the 2019 commencement date even though the canonical entry carries a `[15/2019]` amendment marker, so `effective 1872-01-01` and `effective 2022-03-01` alone are not sane.
- suggested fix: Verify and add the section’s 2019 effective date, then retain the existing 2022 amendment date.
