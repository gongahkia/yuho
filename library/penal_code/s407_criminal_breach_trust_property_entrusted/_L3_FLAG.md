# s407 — L3 flag

- failed: 7
- reason: The penalty block makes the fine optional by nesting it under `alternative {}` even though the canonical text requires imprisonment and fine cumulatively ("and shall also be liable to fine").
- suggested fix: Encode the fine as a direct cumulative penalty alongside the imprisonment term, without an `alternative {}` wrapper.
