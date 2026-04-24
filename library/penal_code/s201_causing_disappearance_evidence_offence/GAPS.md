## GA

Statute text:

> "( c ) if the offence is punishable with imprisonment for any term not extending to 20 years, shall be punished with imprisonment for a term which may extend to one‑fourth part of the longest term of the imprisonment provided for the offence, or with fine, or with both."

Gap:

The grammar accepts only concrete `duration_literal` or `duration_range` values for `imprisonment := ...` and cannot express a sentence that is defined as a fraction of another offence's maximum imprisonment term. The limb is therefore preserved verbatim in `supplementary` inside `penalty or_both when below_20_year_offence`.
