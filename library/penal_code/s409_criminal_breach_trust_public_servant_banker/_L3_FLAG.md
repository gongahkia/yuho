# s409 — L3 flag

- failed: 6
- reason: Subsection (2) in `statute.yh` adds director/officer definition detail and changes the partnership citation beyond what appears in the canonical `library/penal_code/_raw/act.json` entry, so the subsection is not a faithful encoding of the review source.
- suggested fix: Rewrite subsection (2) to match the canonical `act.json` text exactly and avoid injecting definition detail not present in that source.
