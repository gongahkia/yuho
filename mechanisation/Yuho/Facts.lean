/-
Fact patterns.

A fact pattern in §4 is a finite map from element identifiers to
truth values. We represent it as a total function `String → Bool`
and treat unsupplied keys as `false` (the prosecution-side
fail-closed reading of `Eval-Elem-Missing` in §4.2).

The total-function encoding makes the structural-induction proofs
in `Soundness.lean` cleaner — no `dom` tracking. Typed facts below
mechanise the executable burden/proof-standard metadata guard used
by the runtime, without changing the structural conviction proofs.
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

structure BurdenRequirement where
  burden : Option String
  standard : Option String
deriving Repr, DecidableEq, BEq

structure FactMetadata where
  burden : Option String
  standard : Option String
deriving Repr, DecidableEq, BEq

structure TypedFact where
  truth : Bool
  metadata : Option FactMetadata
deriving Repr, DecidableEq, BEq

abbrev TypedFacts := String → TypedFact

def TypedFacts.empty : TypedFacts := fun _ => { truth := false, metadata := none }

def TypedFacts.set (F : TypedFacts) (k : String) (v : TypedFact) : TypedFacts :=
  fun k' => if k' = k then v else F k'

def TypedFacts.fromList : List (String × TypedFact) → TypedFacts
  | [] => TypedFacts.empty
  | (k, v) :: rest => (TypedFacts.fromList rest).set k v

def FactMetadata.satisfiesBurden (metadata : FactMetadata)
    (requirement : BurdenRequirement) : Bool :=
  let burdenOk :=
    match requirement.burden, metadata.burden with
    | some expected, some actual => decide (actual = expected)
    | _, _ => true
  let standardOk :=
    match requirement.standard, metadata.standard with
    | some expected, some actual => decide (actual = expected)
    | _, _ => true
  burdenOk && standardOk

def TypedFact.truthWithBurden (fact : TypedFact)
    (requirement : BurdenRequirement) : Bool :=
  if fact.truth then
    match fact.metadata with
    | none => true
    | some metadata => metadata.satisfiesBurden requirement
  else
    false

theorem TypedFact.truthWithBurden_untyped_true
    (requirement : BurdenRequirement) :
    ({ truth := true, metadata := none } : TypedFact).truthWithBurden
      requirement = true := by
  simp [TypedFact.truthWithBurden]

theorem TypedFact.truthWithBurden_false
    (requirement : BurdenRequirement) (metadata : Option FactMetadata) :
    ({ truth := false, metadata := metadata } : TypedFact).truthWithBurden
      requirement = false := by
  simp [TypedFact.truthWithBurden]

theorem TypedFact.truthWithBurden_matching
    (requirement : BurdenRequirement) :
    ({ truth := true
       metadata :=
        some { burden := requirement.burden
               standard := requirement.standard }
     } : TypedFact).truthWithBurden requirement = true := by
  cases requirement with
  | mk burden standard =>
      cases burden <;> cases standard <;>
        simp [TypedFact.truthWithBurden, FactMetadata.satisfiesBurden]

theorem TypedFact.truthWithBurden_wrong_burden
    (expected wrong : String) (standard factStandard : Option String)
    (h : wrong ≠ expected) :
    ({ truth := true
       metadata := some { burden := some wrong, standard := factStandard }
     } : TypedFact).truthWithBurden
      { burden := some expected, standard := standard } = false := by
  simp [TypedFact.truthWithBurden, FactMetadata.satisfiesBurden, h]

theorem TypedFact.truthWithBurden_wrong_standard
    (burden : Option String) (expected wrong : String)
    (h : wrong ≠ expected) :
    ({ truth := true
       metadata := some { burden := burden, standard := some wrong }
     } : TypedFact).truthWithBurden
      { burden := none, standard := some expected } = false := by
  simp [TypedFact.truthWithBurden, FactMetadata.satisfiesBurden, h]

end Yuho
