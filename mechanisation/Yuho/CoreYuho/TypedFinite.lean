/-
Core Yuho v0.2: finite typed values, quantifiers, cardinalities and explicit
two-rule priority resolution.  The filesystem/module surface is intentionally
outside this executable semantic core.
-/

import Yuho.CoreYuho.Theorems

namespace Yuho.CoreYuho.TypedFinite

open Yuho.CoreYuho

inductive Comparison where
  | equal | notEqual | lessThan | lessEqual | greaterThan | greaterEqual
  deriving Repr, DecidableEq

inductive ScalarValue where
  | integer (value : Int)
  | date (ordinal : Nat)
  | enumValue (typeName member : String)
  | money (currency : String) (minorUnits : Nat)
  | unresolved
  deriving Repr, DecidableEq

def compareOrdering (operation : Comparison) (ordering : Ordering) : Status :=
  let result := match operation with
    | .equal => ordering == .eq
    | .notEqual => ordering != .eq
    | .lessThan => ordering == .lt
    | .lessEqual => ordering != .gt
    | .greaterThan => ordering == .gt
    | .greaterEqual => ordering != .lt
  if result = true then .satisfied else .notSatisfied

def compareScalar (operation : Comparison) (left right : ScalarValue) : Status :=
  match left, right with
  | .unresolved, _ | _, .unresolved => .unresolved
  | .integer first, .integer second => compareOrdering operation (compare first second)
  | .date first, .date second => compareOrdering operation (compare first second)
  | .enumValue firstType first, .enumValue secondType second =>
      if firstType = secondType then compareOrdering operation (compare first second)
      else .unresolved
  | .money firstCurrency first, .money secondCurrency second =>
      if firstCurrency = secondCurrency then compareOrdering operation (compare first second)
      else .unresolved
  | _, _ => .unresolved

def negateStatus : Status → Status
  | .satisfied => .notSatisfied
  | .notSatisfied => .satisfied
  | .unresolved => .unresolved

def finiteForall (values : List Status) : Status := allStatus values
def finiteExists (values : List Status) : Status := anyStatus values

structure TypedTerm where
  identifier : Identifier
  typeName : Identifier
  deriving Repr, DecidableEq

structure PredicateSignature where
  identifier : Identifier
  argumentTypes : List Identifier
  deriving Repr, DecidableEq

structure PredicateApplication where
  predicate : Identifier
  arguments : List TypedTerm
  deriving Repr, DecidableEq

def PredicateApplication.wellTyped
    (application : PredicateApplication) (signature : PredicateSignature) : Prop :=
  application.predicate = signature.identifier ∧
    application.arguments.map (·.typeName) = signature.argumentTypes

def substituteTerm (binder replacement : TypedTerm) (term : TypedTerm) : TypedTerm :=
  if term.identifier = binder.identifier ∧ term.typeName = binder.typeName
    then replacement else term

def substituteApplication (binder replacement : TypedTerm)
    (application : PredicateApplication) : PredicateApplication :=
  { application with arguments := application.arguments.map (substituteTerm binder replacement) }

inductive CardinalityKind where
  | atLeast | atMost | exactly
  deriving Repr, DecidableEq

def countStatus (wanted : Status) : List Status → Nat
  | [] => 0
  | head :: tail => (if head = wanted then 1 else 0) + countStatus wanted tail

def cardinalityFromCounts (kind : CardinalityKind) (threshold satisfied unresolved : Nat) : Status :=
  match kind with
  | .atLeast =>
      if satisfied ≥ threshold then .satisfied
      else if satisfied + unresolved < threshold then .notSatisfied
      else .unresolved
  | .atMost =>
      if satisfied + unresolved ≤ threshold then .satisfied
      else if satisfied > threshold then .notSatisfied
      else .unresolved
  | .exactly =>
      if satisfied = threshold ∧ unresolved = 0 then .satisfied
      else if satisfied > threshold ∨ satisfied + unresolved < threshold
        then .notSatisfied else .unresolved

def cardinalityStatus (kind : CardinalityKind) (threshold : Nat)
    (values : List Status) : Status :=
  cardinalityFromCounts kind threshold
    (countStatus .satisfied values) (countStatus .unresolved values)

inductive Polarity where | establish | defeat deriving Repr, DecidableEq

structure RuleResult where
  identifier : Identifier
  proposition : Identifier
  polarity : Polarity
  status : Status
  deriving Repr, DecidableEq

structure Priority where
  higher : Identifier
  lower : Identifier
  deriving Repr, DecidableEq

inductive PropositionState where
  | established | defeated | conflict | unresolved | notEstablished
  deriving Repr, DecidableEq

def resolveCompetingRules (higher lower : RuleResult)
    (priority : Option Priority) : Status × PropositionState :=
  if higher.proposition != lower.proposition then (.unresolved,.unresolved)
  else if higher.polarity = lower.polarity then
    if higher.status = .satisfied ∨ lower.status = .satisfied
      then (if higher.polarity = .establish then (.satisfied,.established)
        else (.notSatisfied,.defeated))
      else if higher.status = .unresolved ∨ lower.status = .unresolved
        then (.unresolved,.unresolved) else (.notSatisfied,.notEstablished)
  else match priority with
    | some edge =>
        if edge.higher = higher.identifier ∧ edge.lower = lower.identifier then
          match higher.status with
          | .satisfied => if higher.polarity = .establish
              then (.satisfied,.established) else (.notSatisfied,.defeated)
          | .unresolved => (.unresolved,.unresolved)
          | .notSatisfied => match lower.status with
              | .satisfied => if lower.polarity = .establish
                  then (.satisfied,.established) else (.notSatisfied,.defeated)
              | .unresolved => (.unresolved,.unresolved)
              | .notSatisfied => (.notSatisfied,.notEstablished)
        else (.unresolved,.conflict)
    | none => if higher.status = .satisfied ∧ lower.status = .satisfied
        then (.unresolved,.conflict)
      else if higher.status = .unresolved ∨ lower.status = .unresolved
        then (.unresolved,.unresolved)
      else if higher.status = .satisfied then
        if higher.polarity = .establish then (.satisfied,.established)
        else (.notSatisfied,.defeated)
      else if lower.status = .satisfied then
        if lower.polarity = .establish then (.satisfied,.established)
        else (.notSatisfied,.defeated)
      else (.notSatisfied,.notEstablished)

theorem comparison_deterministic (operation : Comparison) (left right : ScalarValue) :
    compareScalar operation left right = compareScalar operation left right := rfl

theorem comparison_total (operation : Comparison) (left right : ScalarValue) :
    ∃ result, compareScalar operation left right = result :=
  ⟨compareScalar operation left right, rfl⟩

theorem negation_involution (status : Status) :
    negateStatus (negateStatus status) = status := by cases status <;> rfl

theorem forall_deterministic (values : List Status) :
    finiteForall values = finiteForall values := rfl

theorem exists_deterministic (values : List Status) :
    finiteExists values = finiteExists values := rfl

theorem forall_expansion_agrees (values : List Status) :
    finiteForall values = allStatus values := rfl

theorem exists_expansion_agrees (values : List Status) :
    finiteExists values = anyStatus values := rfl

theorem forall_permutation_invariant {left right : List Status}
    (permutation : Permutation left right) : finiteForall left = finiteForall right :=
  allStatus_permutation_invariant permutation

theorem exists_permutation_invariant {left right : List Status}
    (permutation : Permutation left right) : finiteExists left = finiteExists right :=
  anyStatus_permutation_invariant permutation

theorem substituteTerm_type_preserved (binder replacement term : TypedTerm)
    (sameType : replacement.typeName = binder.typeName) :
    (substituteTerm binder replacement term).typeName = term.typeName := by
  unfold substituteTerm
  split
  · next selected =>
      have termType : term.typeName = binder.typeName := selected.right
      exact sameType.trans termType.symm
  · rfl

theorem substitution_preserves_well_typed_application
    (application : PredicateApplication) (signature : PredicateSignature)
    (binder replacement : TypedTerm)
    (typed : application.wellTyped signature)
    (sameType : replacement.typeName = binder.typeName) :
    (substituteApplication binder replacement application).wellTyped signature := by
  unfold substituteApplication
  unfold PredicateApplication.wellTyped at typed ⊢
  constructor
  · exact typed.left
  · rw [List.map_map]
    have pointwise : ∀ term : TypedTerm,
        (substituteTerm binder replacement term).typeName = term.typeName :=
      fun term => substituteTerm_type_preserved binder replacement term sameType
    have mapped : application.arguments.map
        (fun term => (substituteTerm binder replacement term).typeName) =
        application.arguments.map (·.typeName) := by
      apply List.map_congr_left
      intro term _
      exact pointwise term
    exact mapped.trans typed.right

theorem countStatus_permutation_invariant (wanted : Status)
    {left right : List Status} (permutation : Permutation left right) :
    countStatus wanted left = countStatus wanted right := by
  induction permutation with
  | nil => rfl
  | cons head _rest induction =>
      simp [countStatus, induction]
  | swap first second tail =>
      simp [countStatus, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]
  | trans _firstRelation _secondRelation firstResult secondResult =>
      exact firstResult.trans secondResult

theorem cardinality_permutation_invariant (kind : CardinalityKind) (threshold : Nat)
    {left right : List Status} (permutation : Permutation left right) :
    cardinalityStatus kind threshold left = cardinalityStatus kind threshold right := by
  unfold cardinalityStatus
  rw [countStatus_permutation_invariant .satisfied permutation]
  rw [countStatus_permutation_invariant .unresolved permutation]

theorem cardinality_deterministic (kind : CardinalityKind) (threshold : Nat)
    (values : List Status) :
    cardinalityStatus kind threshold values = cardinalityStatus kind threshold values := rfl

theorem cardinality_total (kind : CardinalityKind) (threshold : Nat)
    (values : List Status) : ∃ result, cardinalityStatus kind threshold values = result :=
  ⟨cardinalityStatus kind threshold values, rfl⟩

theorem cardinality_mutually_exclusive (kind : CardinalityKind) (threshold : Nat)
    (values : List Status) :
    cardinalityStatus kind threshold values = .satisfied ∨
    cardinalityStatus kind threshold values = .notSatisfied ∨
    cardinalityStatus kind threshold values = .unresolved := by
  cases cardinalityStatus kind threshold values <;> simp

theorem atLeast_satisfied_boundary (threshold satisfied unresolved : Nat)
    (boundary : satisfied ≥ threshold) :
    cardinalityFromCounts .atLeast threshold satisfied unresolved = .satisfied := by
  simp [cardinalityFromCounts, boundary]

theorem atMost_satisfied_boundary (threshold satisfied unresolved : Nat)
    (boundary : satisfied + unresolved ≤ threshold) :
    cardinalityFromCounts .atMost threshold satisfied unresolved = .satisfied := by
  simp [cardinalityFromCounts, boundary]

theorem priority_resolution_deterministic (higher lower : RuleResult)
    (priority : Option Priority) :
    resolveCompetingRules higher lower priority =
      resolveCompetingRules higher lower priority := rfl

theorem higher_satisfied_defeat_wins
    (highId lowId proposition : Identifier) :
    resolveCompetingRules
      { identifier := highId, proposition := proposition, polarity := .defeat,
        status := .satisfied }
      { identifier := lowId, proposition := proposition, polarity := .establish,
        status := .satisfied }
      (some { higher := highId, lower := lowId }) = (.notSatisfied,.defeated) := by
  simp [resolveCompetingRules]

theorem unresolved_higher_blocks_lower
    (highId lowId proposition : Identifier) :
    resolveCompetingRules
      { identifier := highId, proposition := proposition, polarity := .defeat,
        status := .unresolved }
      { identifier := lowId, proposition := proposition, polarity := .establish,
        status := .satisfied }
      (some { higher := highId, lower := lowId }) = (.unresolved,.unresolved) := by
  simp [resolveCompetingRules]

theorem incomparable_satisfied_conflict
    (firstId secondId proposition : Identifier) :
    resolveCompetingRules
      { identifier := firstId, proposition := proposition, polarity := .establish,
        status := .satisfied }
      { identifier := secondId, proposition := proposition, polarity := .defeat,
        status := .satisfied }
      none = (.unresolved,.conflict) := by
  simp [resolveCompetingRules]

theorem unrelated_proposition_is_irrelevant
    (first second : RuleResult) (different : first.proposition ≠ second.proposition)
    (priority : Option Priority) :
    resolveCompetingRules first second priority = (.unresolved,.unresolved) := by
  simp [resolveCompetingRules, different]

end Yuho.CoreYuho.TypedFinite
