## GA
Statute text: "shall be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine, or to caning. [15/2019]"

Current Yuho grammar can encode the uncapped fine limb as `fine := unlimited`, but it cannot directly encode a caning liability where the statute gives no numeric stroke count because `caning :=` requires a number or range. The exact caning language is therefore preserved in `supplementary` text in `penalty when caning_liability` to avoid inventing a stroke count.
