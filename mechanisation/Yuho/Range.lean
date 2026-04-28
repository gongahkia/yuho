/-
Range.lean — algebraic-style alternative surface to `Penalty.admits`.

Per `paper/sections/soundness.tex` §6.5 footnote and the §6.5-v4
"v5 follow-ups" entry in `Penalty.lean`, the paper writes
`R₁ ⊔ ⋯ ⊔ Rₖ` for cumulative penalties and `R₁ ⊓ ⋯ ⊓ Rₖ` for
or-both penalties. The current `Penalty.cumulative` / `Penalty.orBoth`
constructors capture the same operational shape via the
`Penalty.admits` predicate but use list-of-children syntax rather
than infix algebra.

This file exposes:

  * `Range` — a thin alias for `Penalty` so users can talk about
    "ranges" without leaving the `Penalty` AST.
  * `Range.cumulativeJoin` / `Range.orBothMeet` — n-ary algebraic
    constructors, sugar for `Penalty.cumulative` / `Penalty.orBoth`.
  * `Range.cumulativeJoin_admits_iff` /
    `Range.orBothMeet_admits_iff` — correspondence theorems
    pinning the algebraic surface to the operational
    `Penalty.admits` predicate.

Nothing semantically new lives here; the §6.5 lemma is unchanged.
The file is a usability layer for downstream proofs and tutorials
that prefer the paper's algebraic notation. -/

import Yuho.Penalty

namespace Yuho

/-- A `Range` is a `Penalty` viewed under its range-arithmetic
surface. The alias keeps `Penalty.admits` available unchanged. -/
abbrev Range := Penalty

namespace Range

/-- **Cumulative join.** `cumulativeJoin [R₁, …, Rₖ]` is the range
that admits a footprint iff every component admits it. Sugar for
`Penalty.cumulative`. -/
abbrev cumulativeJoin (rs : List Range) : Range :=
  Penalty.cumulative rs

/-- **Or-both meet.** `orBothMeet [R₁, …, Rₖ]` is the range that
admits a footprint iff at least one component admits it. Sugar
for `Penalty.orBoth`. -/
abbrev orBothMeet (rs : List Range) : Range :=
  Penalty.orBoth rs

/-! ### Correspondence theorems

These pin the algebraic surface to the operational `Penalty.admits`
predicate, so users phrasing penalties in `cumulativeJoin` /
`orBothMeet` notation can immediately appeal to the §6.5
soundness lemma. -/

/-- **`cumulativeJoin` admits `fp` iff every component admits.**
Forward direction reuses `penalty_correspondence_cumulative`. -/
theorem cumulativeJoin_admits_iff (rs : List Range) (fp : Footprint) :
    (cumulativeJoin rs).admits fp = true ↔ ∀ r ∈ rs, r.admits fp = true := by
  constructor
  · intro h
    exact penalty_correspondence_cumulative rs fp h
  · intro h
    simp only [cumulativeJoin, Penalty.admits]
    induction rs with
    | nil => simp [Penalty.admitsAll]
    | cons q rest ih =>
      rw [Penalty.admitsAll, Bool.and_eq_true]
      refine ⟨?_, ?_⟩
      · exact h q (List.mem_cons_self _ _)
      · exact ih (fun r hmem => h r (List.mem_cons_of_mem _ hmem))

/-- **`orBothMeet` admits `fp` iff some component admits.**
Forward direction reuses `penalty_correspondence_orBoth`. -/
theorem orBothMeet_admits_iff (rs : List Range) (fp : Footprint) :
    (orBothMeet rs).admits fp = true ↔ ∃ r ∈ rs, r.admits fp = true := by
  constructor
  · intro h
    exact penalty_correspondence_orBoth rs fp h
  · intro ⟨r, hmem, hadmits⟩
    simp only [orBothMeet, Penalty.admits]
    induction rs with
    | nil => cases hmem
    | cons q rest ih =>
      rw [Penalty.admitsAny, Bool.or_eq_true]
      cases hmem with
      | head =>
        exact Or.inl hadmits
      | tail _ hmem' =>
        exact Or.inr (ih hmem')

/-- **Identity: cumulativeJoin of a singleton.** -/
theorem cumulativeJoin_singleton (r : Range) (fp : Footprint) :
    (cumulativeJoin [r]).admits fp = r.admits fp := by
  simp [cumulativeJoin, Penalty.admits, Penalty.admitsAll]

/-- **Identity: orBothMeet of a singleton.** -/
theorem orBothMeet_singleton (r : Range) (fp : Footprint) :
    (orBothMeet [r]).admits fp = r.admits fp := by
  simp [orBothMeet, Penalty.admits, Penalty.admitsAny]

/-- **Empty cumulative is vacuously admissible.** -/
theorem cumulativeJoin_nil (fp : Footprint) :
    (cumulativeJoin []).admits fp = true := by
  simp [cumulativeJoin, Penalty.admits, Penalty.admitsAll]

/-- **Empty or-both admits nothing.** -/
theorem orBothMeet_nil (fp : Footprint) :
    (orBothMeet []).admits fp = false := by
  simp [orBothMeet, Penalty.admits, Penalty.admitsAny]

end Range
end Yuho
