# s414 — L3 flag

- failed: 7, 9
- reason: The encoding uses an unsound `[15/2019]` effective date (`2019-12-31` instead of repo-local `2020-01-01`) and alters subsection (2)(b) by substituting `Road Traffic Act (Cap. 276)` for the canonical `Road Traffic Act 1961`.
- suggested fix: Update the amendment effective date to the verified commencement date and restore subsection (2)(b) to the canonical Road Traffic Act wording before rerunning L3 review.
