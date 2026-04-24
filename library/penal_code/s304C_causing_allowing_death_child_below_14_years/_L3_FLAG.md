# s304C — L3 flag

- failed: 9
- reason: The encoding includes a generic `effective 1872-01-01` clause even though canonical section 304C was introduced by amendment `[15/2019]`, so the effective-date metadata is not sane.
- suggested fix: Remove the generic 1872 effective date and retain the amendment-era effective date that corresponds to the section's introduction.
