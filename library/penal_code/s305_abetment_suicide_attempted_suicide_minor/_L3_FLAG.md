# s305 — L3 flag

- failed: 7
- reason: The encoded penalties for subsection (1)(a) and subsection (1)(c) collapse conditional sentencing branches into generic `penalty cumulative` blocks and leave the death/life contingencies only in supplementary text, so the machine-readable penalty structure is not faithful to the statute.
- suggested fix: Re-express subsection (1)(a) and subsection (1)(c) as explicit sibling penalty branches, using conditional `penalty when <ident>` blocks for the fine-if-not-death/life or fine-if-not-life limbs and preserving the life-imprisonment alternatives structurally.
