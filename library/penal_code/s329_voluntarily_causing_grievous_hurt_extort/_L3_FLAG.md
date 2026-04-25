# s329 — L3 flag

- failed: 7
- reason: The encoding hard-codes `caning := 0 .. 24 strokes` even though the canonical text only says the offender is liable to caning without specifying any stroke count.
- suggested fix: Preserve the caning limb without inventing a numeric range, consistent with the repo's handling of uncapped caning provisions.
