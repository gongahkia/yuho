# s324 — L3 flag

- failed: 7
- reason: The encoding fabricates a caning range of `0 .. 24 strokes` even though the canonical text states only liability to caning without any numeric stroke count.
- suggested fix: Preserve the caning limb without inventing a stroke count, such as by moving the verbatim caning language into a supplementary penalty field.
