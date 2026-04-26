/-
Fact patterns.

A fact pattern in §4 is a finite map from element identifiers to
truth values. We represent it as a total function `String → Bool`
and treat unsupplied keys as `false` (the prosecution-side
fail-closed reading of `Eval-Elem-Missing` in §4.2).

The total-function encoding makes the structural-induction proofs
in `Soundness.lean` cleaner — no `dom` tracking — at the cost of
giving up the prosecution/defence asymmetry (G11 burden). G11 is
elided from this mechanisation per the §4.6 scope statement.
-/

namespace Yuho

/-- A fact pattern: a total function from element identifiers to
booleans. Unsupplied keys default to `false`. -/
abbrev Facts := String → Bool

/-- The empty fact pattern: every element is unsatisfied. -/
def Facts.empty : Facts := fun _ => false

/-- Update a fact pattern at one key. -/
def Facts.set (F : Facts) (k : String) (v : Bool) : Facts :=
  fun k' => if k' = k then v else F k'

/-- Build a fact pattern from a list of (key, value) pairs. Later
entries override earlier ones. -/
def Facts.fromList : List (String × Bool) → Facts
  | [] => Facts.empty
  | (k, v) :: rest => (Facts.fromList rest).set k v

end Yuho
