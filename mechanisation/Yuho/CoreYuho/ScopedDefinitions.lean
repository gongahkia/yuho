/- Scoped typed definition use: abstract substitution and assessment locality.
   Finite first-order body only; this does not prove parser/resolver/serialization
   refinement. Production expansion is independently tested against actual reads. -/
import Yuho.CoreYuho.DependencyPlan

namespace Yuho.CoreYuho.ScopedDefinitions
open Yuho.CoreYuho
open Yuho.CoreYuho.TypedFinite

structure DefinitionId where
  owner : String
  version : String
  declaration : String
  source : String
  deriving Repr, DecidableEq

structure Occurrence where
  definition : DefinitionId
  useSite : String
  component : String
  scope : DependencyPlan.Scope
  arguments : List TypedTerm
  selection : String
  deriving Repr, DecidableEq

-- Role variables and their typed replacements are separate from display text.
structure Substitution where
  role : TypedTerm
  entity : TypedTerm
  compatible : role.typeName = entity.typeName

theorem substitution_preserves_type (s : Substitution) (t : TypedTerm) :
    (substituteTerm s.role s.entity t).typeName = t.typeName := by
  unfold substituteTerm
  split
  next h => exact s.compatible.symm.trans h.2.symm
  next => rfl

def selectApplication (signature : PredicateSignature) (arguments : List TypedTerm) :
    PredicateApplication := ⟨signature.identifier, arguments⟩

theorem instantiated_application_well_typed (signature : PredicateSignature)
    (arguments : List TypedTerm) (h : arguments.map (·.typeName) = signature.argumentTypes) :
    (selectApplication signature arguments).wellTyped signature := ⟨rfl, h⟩

theorem distinct_scope_distinct_occurrence (a b : Occurrence) (h : a.scope ≠ b.scope) : a ≠ b := by
  intro eq
  exact h (congrArg Occurrence.scope eq)

theorem distinct_use_distinct_occurrence (a b : Occurrence) (h : a.useSite ≠ b.useSite) : a ≠ b := by
  intro eq
  exact h (congrArg Occurrence.useSite eq)

theorem distinct_selection_distinct_occurrence (a b : Occurrence) (h : a.selection ≠ b.selection) : a ≠ b := by
  intro eq
  exact h (congrArg Occurrence.selection eq)

-- A finite grounded body delegates all truth functions to existing semantics.
inductive Body where
  | atom (predicate : String) (arguments : List TypedTerm)
  | conjunction (a b : Body)
  | disjunction (a b : Body)
  | negation (a : Body)
  deriving Repr, DecidableEq

abbrev AssessmentEnvironment := Occurrence → String → List TypedTerm → Status

def evaluate (env : AssessmentEnvironment) (occurrence : Occurrence) : Body → Status
  | .atom p args => env occurrence p args
  | .conjunction a b => allStatus [evaluate env occurrence a, evaluate env occurrence b]
  | .disjunction a b => anyStatus [evaluate env occurrence a, evaluate env occurrence b]
  | .negation a => negateStatus (evaluate env occurrence a)

-- No global definition-result cache is part of the semantics. Equal definition
-- bodies do not imply equal assessment environments or equal occurrence results.
theorem assessment_noninterference (first second : AssessmentEnvironment)
    (occurrence : Occurrence) (h : ∀ p args, first occurrence p args = second occurrence p args)
    (body : Body) : evaluate first occurrence body = evaluate second occurrence body := by
  induction body with
  | atom p args => exact h p args
  | conjunction a b ha hb => simp only [evaluate, ha, hb]
  | disjunction a b ha hb => simp only [evaluate, ha, hb]
  | negation a ha => simp only [evaluate, ha]

-- Source identity is retained as a structural value, independent of its body
-- expansion and environment. Finite structural evaluation terminates in Lean.
def instantiate (definition : DefinitionId) (useSite component : String)
    (scope : DependencyPlan.Scope) (args : List TypedTerm) (selection : String) : Occurrence :=
  ⟨definition, useSite, component, scope, args, selection⟩

theorem authored_identity_retained (definition : DefinitionId) (useSite component : String)
    (scope : DependencyPlan.Scope) (args : List TypedTerm) (selection : String) :
    (instantiate definition useSite component scope args selection).definition = definition := rfl

end Yuho.CoreYuho.ScopedDefinitions
