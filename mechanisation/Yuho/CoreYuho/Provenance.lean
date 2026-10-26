import Std

/- Abstract projection invariants. Id includes the checked source/scope/occurrence
   tuple. This does not prove the Haskell resolver, parser or renderer refines it. -/
namespace Yuho.Provenance
inductive Category where
  | authored | supplied | occurrence | observation | derived | consequence
  deriving DecidableEq, Repr
structure Id where
  source : String
  scope : String
  occurrence : List Nat
  category : Category
  deriving DecidableEq, Repr
structure Edge where
  source : Id
  target : Id
  deriving DecidableEq, Repr

def endpoints (nodes : List Id) (e : Edge) : Prop := e.source ∈ nodes ∧ e.target ∈ nodes

def included (select : Id → Bool) (nodes : List Id) := nodes.filter select
def omitted (select : Id → Bool) (nodes : List Id) := nodes.filter (fun n => !select n)
def visible (select : Id → Bool) (edges : List Edge) := edges.filter (fun e => select e.source && select e.target)

theorem included_subset (s : Id → Bool) (ns : List Id) (n : Id)
    (h : n ∈ included s ns) : n ∈ ns := (List.mem_filter.mp h).1

theorem omitted_subset (s : Id → Bool) (ns : List Id) (n : Id)
    (h : n ∈ omitted s ns) : n ∈ ns := (List.mem_filter.mp h).1

theorem partition_complete (s : Id → Bool) (ns : List Id) (n : Id) (h : n ∈ ns) :
    n ∈ included s ns ∨ n ∈ omitted s ns := by
  cases hs : s n <;> simp [included, omitted, List.mem_filter, hs, h]

theorem partition_disjoint (s : Id → Bool) (ns : List Id) (n : Id) :
    ¬ (n ∈ included s ns ∧ n ∈ omitted s ns) := by
  cases hs : s n <;> simp [included, omitted, List.mem_filter, hs]

theorem visible_subset (s : Id → Bool) (es : List Edge) (e : Edge)
    (h : e ∈ visible s es) : e ∈ es := (List.mem_filter.mp h).1

theorem visible_endpoints (s : Id → Bool) (ns : List Id) (es : List Edge)
    (valid : ∀ e ∈ es, endpoints ns e) (e : Edge) (h : e ∈ visible s es) :
    endpoints (included s ns) e := by
  have he := List.mem_filter.mp h
  have hn := valid e he.1
  have hs : s e.source = true := by cases h₁ : s e.source <;> simp_all
  have ht : s e.target = true := by cases h₂ : s e.target <;> simp_all
  exact ⟨List.mem_filter.mpr ⟨hn.1, hs⟩, List.mem_filter.mpr ⟨hn.2, ht⟩⟩

theorem distinct_scope (a b : Id) (h : a.scope ≠ b.scope) : a ≠ b := by
  intro e
  exact h (congrArg Id.scope e)
theorem distinct_occurrence (a b : Id) (h : a.occurrence ≠ b.occurrence) : a ≠ b := by
  intro e
  exact h (congrArg Id.occurrence e)
theorem authored_not_observation (source scope : String) (path : List Nat) :
    (Id.mk source scope path .authored) ≠ (Id.mk source scope path .observation) := by
  intro h
  cases h

end Yuho.Provenance
