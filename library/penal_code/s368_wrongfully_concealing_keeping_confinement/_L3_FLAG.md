# s368 — L3 flag

- failed: 8
- reason: The encoding uses top-level `all_of` with freeform strings for "kidnapped or abducted" and "conceals or keeps such person in confinement" instead of preserving those disjunctive alternatives as structured `any_of` branches.
- suggested fix: Split the knowledge and actus reus limbs into explicit `any_of` alternatives while keeping the overall offence conjunctive.
