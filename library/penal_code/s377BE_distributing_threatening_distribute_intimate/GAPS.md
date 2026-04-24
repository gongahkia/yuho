## GA
"Subject to subsection (4), a person who is guilty of an offence under subsection (1) or (2) shall on conviction be punished with imprisonment for a term which may extend to 5 years, or with fine, or with caning, or with any combination of such punishments. [15/2019]"

"A person who commits an offence under subsection (1) or (2) against a person ( B ) who is below 14 years of age shall on conviction be punished with imprisonment for a term which may extend to 5 years and shall also be liable to fine or to caning. [15/2019]"

The current Yuho grammar supports `fine := unlimited`, but `caning` still requires a numeric stroke count or range. Section 377BE states liability to caning without specifying any number of strokes, so the encoding preserves the caning limb verbatim in `supplementary` text and does not invent a `caning := ... strokes` clause.
