## G1
Statute text: "Subject to subsection (4), a person who is guilty of an offence under this section shall be punished with imprisonment for a term which may extend to 20 years, and shall also be liable to fine or to caning."

Current Yuho grammar can encode `fine := unlimited`, but it cannot directly encode an uncapped "liable to caning" clause with no stroke count. The exact caning language is therefore preserved in `supplementary` text to avoid inventing a number of strokes.

## G2
Statute text: "Whoever ... shall be punished with imprisonment for a term of not less than 8 years and not more than 20 years and shall also be punished with caning with not less than 12 strokes."

Current Yuho grammar can encode the mandatory minimum imprisonment term, but it cannot directly encode a minimum-only caning clause without inventing an upper bound. The exact caning language is therefore preserved in `supplementary` text to avoid fabricating a stroke range.
