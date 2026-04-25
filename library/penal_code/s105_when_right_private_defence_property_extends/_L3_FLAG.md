# s105 — L3 flag

- failed: 6, 8
- reason: The encoding drops canonical limbs `(b)(i)`, `(b)(ii)`, and `(2)(a)` to `(2)(f)`, collapsing subsection `(2)` into a definition string and failing to preserve the statute's disjunctive structure.
- suggested fix: Re-encode subsection `(1)(b)` and subsection `(2)` with explicit nested items or `any_of` branches so every canonical limb is represented verbatim.
