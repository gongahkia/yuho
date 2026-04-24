## G1
Statute text: "Whoever shall be one of 5 or more persons assembled for the purpose of committing gang‑robbery, shall be punished with imprisonment for a term which may extend to 7 years, and shall also be punished with caning with not less than 4 strokes."

Current Yuho grammar requires `caning := ... strokes` to use either an exact stroke count or a closed range. Section 402 specifies only a minimum caning term, so encoding a numeric `caning :=` clause would either understate the statute or invent an upper bound. The minimum-only caning limb is therefore preserved verbatim in `supplementary`.
