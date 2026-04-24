## G1
Statute text: "A person who is guilty of an offence under subsection (1) shall ... be punished on conviction with imprisonment for a term which may extend to 10 years, or with fine, or with caning, or any combination of such punishments"

Current Yuho grammar can encode `or_both` and `fine := unlimited`, but it cannot directly encode an uncapped caning limb because `caning :=` requires a numeric stroke count or range. The exact caning language is therefore preserved in `supplementary` text in subsection `(2)` to avoid inventing a number of strokes.
