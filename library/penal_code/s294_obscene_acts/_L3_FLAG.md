# s294 — L3 flag

- failed: 9
- reason: The statute is tagged with amendment marker `[15/2019]` but the encoding uses only `effective 1872-01-01`, which fails the amended-section effective-date requirement.
- suggested fix: Add the amendment commencement date as an `effective` clause alongside any historical baseline date if the section remained in force through amendment.
