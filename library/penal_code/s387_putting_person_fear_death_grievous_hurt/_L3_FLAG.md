# s387 — L3 flag

- failed: 7
- reason: The encoding omits a structured caning punishment even though the canonical text expressly requires punishment "with caning", and the repo now supports `caning := unspecified` for non-numeric caning terms.
- suggested fix: Add an explicit `caning := unspecified` punishment entry so the mandatory caning limb is preserved structurally instead of only in supplementary prose.
