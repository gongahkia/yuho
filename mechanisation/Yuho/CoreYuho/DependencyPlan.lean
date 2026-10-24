/- Finite checked-plan semantics, additive to existing component evaluators.
   No parser, byte hash, legal interpretation or renderer refinement is assumed
   proved by this model. Component determinism/locality are explicit premises. -/
import Yuho.CoreYuho.TypedFinite

namespace Yuho.CoreYuho.DependencyPlan
open Yuho.CoreYuho

inductive Resolution where
  | established | defeated | notEstablished | unresolved | conflict
  deriving Repr, DecidableEq
inductive Evidence where
  | expression (value : Status)
  | proposition (value : Resolution)
  | unavailable (reason : String)
  deriving Repr, DecidableEq
structure Condition where
  value : Option Status
  conflictOrigin : Bool
  unavailableReason : Option String
  deriving Repr, DecidableEq

def convert : Evidence → Condition
  | .expression s => ⟨some s, false, none⟩
  | .proposition .established => ⟨some .satisfied, false, none⟩
  | .proposition .defeated | .proposition .notEstablished => ⟨some .notSatisfied, false, none⟩
  | .proposition .unresolved => ⟨some .unresolved, false, none⟩
  | .proposition .conflict => ⟨some .unresolved, true, none⟩
  | .unavailable r => ⟨none, false, some r⟩

theorem unavailable_has_no_value (r : String) : (convert (.unavailable r)).value = none := rfl
theorem conflict_origin_retained : (convert (.proposition .conflict)).conflictOrigin = true := rfl
theorem support_absence_is_technical_false :
    (convert (.proposition .notEstablished)).value = some .notSatisfied := rfl

inductive Availability where
  | eligible | ineligible | unresolved (conflictOrigin : Bool) | notEvaluated (reason : String)
  deriving Repr, DecidableEq

def availability (c : Condition) : Availability := match c.value with
  | some .satisfied => .eligible
  | some .notSatisfied => .ineligible
  | some .unresolved => .unresolved c.conflictOrigin
  | none => .notEvaluated (c.unavailableReason.getD "blocked")

theorem false_is_ineligible : availability (convert (.expression .notSatisfied)) = .ineligible := rfl
theorem unknown_is_unresolved : availability (convert (.expression .unresolved)) = .unresolved false := rfl
theorem skipped_is_not_evaluated (r : String) :
    availability (convert (.unavailable r)) = .notEvaluated r := rfl

structure Scope where
  actor : String
  context : String
  caseId : Option String
  allegation : Option String
  occurrence : String
  bindings : List (String × String)
  deriving Repr, DecidableEq
inductive Category where
  | expressionTruth | propositionResolution | technicalCondition
  deriving Repr, DecidableEq
structure Endpoint where
  component : String
  category : Category
  object : String
  scope : Scope
  deriving Repr, DecidableEq
structure Binding where
  source : Endpoint
  destination : Endpoint
  rationale : String
  deriving Repr, DecidableEq

def wellTyped (b : Binding) : Prop :=
  b.source.scope = b.destination.scope ∧
  b.destination.category = .technicalCondition ∧
  (b.source.category = .expressionTruth ∨ b.source.category = .propositionResolution)

theorem scope_preservation (b : Binding) (h : wellTyped b) :
    b.source.scope = b.destination.scope := h.1

def distinct {α : Type} : List α → Prop
  | [] => True
  | x::xs => x ∉ xs ∧ distinct xs

def singleWriter (bs : List Binding) : Prop := distinct (bs.map (·.destination))

theorem single_writer_destinations (bs : List Binding) (h : singleWriter bs) :
    distinct (bs.map (·.destination)) := h

-- A rank certificate validates a finite order independently of the scheduler.
-- Every edge must increase rank, including all possible guarded edges.
def ordered (edges : List (Nat × Nat)) (rank : Nat → Nat) : Prop :=
  ∀ e ∈ edges, rank e.1 < rank e.2

theorem no_self_edge (edges : List (Nat × Nat)) (rank : Nat → Nat)
    (h : ordered edges rank) (n : Nat) : (n,n) ∉ edges := by
  intro hm
  have hn := h (n,n) hm
  exact (Nat.lt_irrefl (rank n)) hn

theorem no_back_edge (a b : Nat) (rank : Nat → Nat)
    (ab : rank a < rank b) : ¬ rank b < rank a := Nat.not_lt_of_ge (Nat.le_of_lt ab)

inductive Reach (edges : List (Nat × Nat)) : Nat → Nat → Prop where
  | edge {a b : Nat} : (a,b) ∈ edges → Reach edges a b
  | trans {a b c : Nat} : Reach edges a b → Reach edges b c → Reach edges a c

theorem reachable_increases (edges : List (Nat × Nat)) (rank : Nat → Nat)
    (h : ordered edges rank) {a b : Nat} (path : Reach edges a b) : rank a < rank b := by
  induction path with
  | edge hm => exact h _ hm
  | trans _ _ ih₁ ih₂ => exact Nat.lt_trans ih₁ ih₂

theorem acyclic (edges : List (Nat × Nat)) (rank : Nat → Nat)
    (h : ordered edges rank) (n : Nat) : ¬ Reach edges n n := by
  intro path
  exact Nat.lt_irrefl (rank n) (reachable_increases edges rank h path)

-- Evaluation is structural recursion over a checked finite, duplicate-free
-- order. At-most-once is the order's independently checked Nodup certificate.
def execute (f : Nat → Status) : List Nat → List (Nat × Status)
  | [] => []
  | n::ns => (n,f n)::execute f ns

theorem execute_length (f : Nat → Status) (ns : List Nat) :
    (execute f ns).length = ns.length := by
  induction ns with
  | nil => rfl
  | cons n ns ih => simp [execute, ih]

theorem execute_keys (f : Nat → Status) (ns : List Nat) :
    (execute f ns).map Prod.fst = ns := by
  induction ns with
  | nil => rfl
  | cons n ns ih => simp [execute, ih]

theorem at_most_once (f : Nat → Status) (ns : List Nat) (h : distinct ns) :
    distinct ((execute f ns).map Prod.fst) := by
  rw [execute_keys]
  exact h

-- Any two completed valuations of a finite ranked dependency system agree,
-- provided each deterministic component depends only on lower ranks. This
-- proves order independence under those explicit component premises; it is not
-- a proof of production parsing/adapters or the scheduler implementation.
theorem valuation_unique
    (f : Nat → (Nat → Status) → Status)
    (locality : ∀ n v w, (∀ m, m < n → v m = w m) → f n v = f n w)
    (v w : Nat → Status)
    (hv : ∀ n, v n = f n v) (hw : ∀ n, w n = f n w) : v = w := by
  funext n
  induction n using Nat.strongInductionOn with
  | ind n ih =>
      calc v n = f n v := hv n
           _ = f n w := locality n v w (fun m hm => ih m hm)
           _ = w n := (hw n).symm

-- A private generated leaf carries exactly the converted technical value.
-- The template is retained unchanged alongside its execution-only overlay.
def lower (template : List String) (binding : String) (s : Status) :=
  (template, (binding,s))
theorem lowering_preserves_template (t : List String) (b : String) (s : Status) :
    (lower t b s).1 = t := rfl
theorem lowering_leaf_value (t : List String) (b : String) (s : Status) :
    (lower t b s).2.2 = s := rfl

structure Candidate where
  identity : String
  term : List String
  scope : Scope
  deriving Repr, DecidableEq

def guardedCandidate (c : Candidate) (e : Evidence) := (c, availability (convert e))
theorem candidate_term_and_scope_retained (c : Candidate) (e : Evidence) :
    (guardedCandidate c e).1 = c := rfl

-- Actual conversions retain the source endpoint; equality of status/labels is
-- never used as a source-to-destination identity proof.
structure ProjectionRecord where
  binding : Binding
  evidence : Evidence
  condition : Condition

def project (b : Binding) (e : Evidence) : ProjectionRecord := ⟨b,e,convert e⟩
theorem projection_retains_source (b : Binding) (e : Evidence) :
    (project b e).binding.source = b.source := rfl

end Yuho.CoreYuho.DependencyPlan
