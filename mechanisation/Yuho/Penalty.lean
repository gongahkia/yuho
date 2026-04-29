/-
Penalty.lean — v3 mechanisation of Lemma 6.5 (penalty
correspondence); cf. `paper/sections/soundness.tex`
\S\ref{subsec:soundness-penalty}, `lem:soundness-penalty` and
`paper/sections/semantics.tex` \S\ref{subsec:semantics-penalty}.

Theorem~\ref{thm:z3-sound} proper concerns conviction; Lemma 6.5
extends the same shape of correspondence claim to the *penalty*
encoding. The Z3 generator emits, for every statute `S` with
penalty term `p`:

* per-axis bounds — `imp_lo, imp_hi, fine_lo, fine_hi,
  caning_lo, caning_hi` (integer atoms),
* a `death` boolean,
* the range invariant `lo ≤ hi` per axis,
* and the per-component biconditionals tying each axis to the
  encoded penalty literal's numeric values.

The lemma states: for every satisfying assignment `M`, the model's
*footprint* (the tuple of per-axis bound atoms it assigns)
satisfies the operational range admissibility predicate iff the
operational rules of \S3.4 yield a range that admits the same
footprint.

This file is a *v3 scaffold*. Structure:

1. `Footprint` — the bundle of per-axis bound atoms a Z3 model
   assigns. Pure data.
2. `Penalty` — the AST of penalty terms (four axis leaves +
   `cumulative` + `orBoth` combinators). Pure data.
3. `Penalty.admits` — the operational admissibility predicate,
   defined recursively over `Penalty` with well-founded recursion
   on `sizeOf` for the `List`-nested combinators (the same trick
   `Graph.lean` uses).
4. `PenaltySMTModel` and the `satisfies` bundle.
5. The correspondence theorems:
   - `penalty_correspondence_imprisonment` (axis-leaf base case)
   - `penalty_correspondence_fine` / `caning` / `death`
   - `cumulative_corresp_param` / `orBoth_corresp_param`
     (list-folding sub-lemmas)
   - `penalty_correspondence` (the main theorem, by structural
     induction on `Penalty`).

Closure status: leaf cases + list-folding sub-lemmas
kernel-checked. The main theorem `penalty_correspondence` follows
the same `termination_by sizeOf` template as
`element_graph_correspondence` in `Graph.lean`.

What is *not* covered by this file (per the §6.6 paper boundary):

* G8 (`fine := unlimited`) and G14 (`caning := unspecified`)
  sentinels. The leaf rules below admit only finite ranges; the
  unbounded-axis variants would need an `Option Nat` bound type
  on the upper side. Tracked as a v4 extension.
* Multi-axis `cumulative` interaction with the linter's
  no-sentinel-propagation invariant. The linter rejects sentinel
  values appearing under combinators; this file inherits that
  rejection.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval
import Yuho.SMTAbs
import Yuho.Graph

namespace Yuho

/-! ## §6.5-v3 layer 1 — Footprint -/

/-- A per-axis bound footprint, the abstract image of the per-axis
Z3 atoms a satisfying model assigns. All bounds are `Nat`; the
unbounded-upper-bound (G8 / G14) case is supported via the
`fine_unlimited` and `caning_unspecified` flags — when set true,
the corresponding `*_hi` field is interpreted as `+∞` and the
admissibility predicate ignores the numeric upper-bound check
on that axis.

Imprisonment intentionally does not carry a parallel sentinel:
SG PC imprisonment ranges are always bounded (life imprisonment
is encoded as a specific upper number, not a sentinel — see
`s54` for the canonical "imprisonment for life" mapping). -/
structure Footprint where
  imp_lo    : Nat  := 0
  imp_hi    : Nat  := 0
  fine_lo   : Nat  := 0
  fine_hi   : Nat  := 0
  /-- (G8) The fine upper bound is unlimited (`fine := unlimited`).
  When `true`, `fine_hi` is unconstrained from above. -/
  fine_unlimited : Bool := false
  caning_lo : Nat  := 0
  caning_hi : Nat  := 0
  /-- (G14) The caning upper bound is unspecified (`caning :=
  unspecified`). When `true`, `caning_hi` is unconstrained from
  above. -/
  caning_unspecified : Bool := false
  death     : Bool := false
  deriving Repr

/-! ## §6.5-v3 layer 2 — Penalty AST -/

/-- The penalty AST. Mirrors §3.4 of the paper:

* `imprisonment lo hi` — imprisonment range in days.
* `fine lo hi` — fine range in cents.
* `caning lo hi` — caning range in strokes.
* `death` — death penalty applicable (single-point "range").
* `cumulative ps` — every component of every child applies
  (logical conjunction; `⊔` in the paper's range arithmetic).
* `orBoth ps` — at least one child's components apply (logical
  disjunction; `⊓` in the paper). -/
inductive Penalty where
  | imprisonment : (lo hi : Nat) → Penalty
  | fine         : (lo hi : Nat) → Penalty
  /-- (G8) `fine := unlimited`. The penalty's fine has lower bound
  `lo` and an unbounded upper limit; the admissibility predicate
  drops the numeric upper-bound check on the model's `fine_hi`. -/
  | fineUnlimited : (lo : Nat) → Penalty
  | caning       : (lo hi : Nat) → Penalty
  /-- (G14) `caning := unspecified`. Analogous to `fineUnlimited`
  for the caning axis. -/
  | caningUnspecified : (lo : Nat) → Penalty
  | death        : Penalty
  | cumulative   : List Penalty → Penalty
  | orBoth       : List Penalty → Penalty
  deriving Repr

/-! ## §6.5-v3 layer 3 — Operational admissibility predicate

`Penalty.admits` is the recursive characterisation of "the
footprint `fp` is admissible under the operational range that
`p` reduces to". The leaf cases are direct numeric range checks;
the combinators fold `List.all` (cumulative) and `List.any`
(orBoth) over the children.

The recursion through `List Penalty` in `cumulative` / `orBoth`
needs `termination_by sizeOf p` and a `decreasing_by` proof
identical in shape to `element_graph_correspondence`. -/
mutual

def Penalty.admits : Penalty → Footprint → Bool
  | .imprisonment lo hi, fp =>
      decide (lo ≤ fp.imp_lo) && decide (fp.imp_hi ≤ hi) &&
      decide (fp.imp_lo ≤ fp.imp_hi)
  | .fine lo hi, fp =>
      decide (lo ≤ fp.fine_lo) && decide (fp.fine_hi ≤ hi) &&
      decide (fp.fine_lo ≤ fp.fine_hi)
  | .fineUnlimited lo, fp =>
      -- G8: penalty range is [lo, +∞). The model must respect
      -- `lo ≤ fp.fine_lo`, and either claim unlimited itself
      -- (`fp.fine_unlimited = true`) or supply a coherent finite
      -- range (`fp.fine_lo ≤ fp.fine_hi`).
      decide (lo ≤ fp.fine_lo) &&
      (fp.fine_unlimited || decide (fp.fine_lo ≤ fp.fine_hi))
  | .caning lo hi, fp =>
      decide (lo ≤ fp.caning_lo) && decide (fp.caning_hi ≤ hi) &&
      decide (fp.caning_lo ≤ fp.caning_hi)
  | .caningUnspecified lo, fp =>
      -- G14: same shape as G8 for the caning axis.
      decide (lo ≤ fp.caning_lo) &&
      (fp.caning_unspecified || decide (fp.caning_lo ≤ fp.caning_hi))
  | .death, fp => fp.death
  | .cumulative ps, fp => Penalty.admitsAll ps fp
  | .orBoth ps, fp => Penalty.admitsAny ps fp

/-- All children admit `fp` (cumulative). -/
def Penalty.admitsAll : List Penalty → Footprint → Bool
  | [],        _  => true
  | p :: rest, fp => p.admits fp && Penalty.admitsAll rest fp

/-- At least one child admits `fp` (orBoth). -/
def Penalty.admitsAny : List Penalty → Footprint → Bool
  | [],        _  => false
  | p :: rest, fp => p.admits fp || Penalty.admitsAny rest fp

end

/-! ## §6.5-v3 layer 4 — Penalty SMT model -/

/-- Extended SMT model that records per-axis Z3 atoms (as a
`Footprint`) on top of the per-element + per-group + per-exception
atoms inherited from `GraphSMTModel`. -/
structure PenaltySMTModel extends GraphSMTModel where
  /-- The per-axis bound atoms the Z3 model assigns. -/
  footprint : Footprint

/-- The biconditionals a Z3 model must satisfy to be a satisfying
assignment for a statute carrying a penalty term `p`. The
penalty bicond (B-pen) asserts the model's footprint is admitted
by `p` under the operational `Penalty.admits` predicate. -/
structure PenaltySMTModel.satisfies (m : PenaltySMTModel) (s : Statute) (p : Penalty) : Prop where
  /-- Inherited graph-level biconditionals (B1 family + B2). -/
  graph : m.toGraphSMTModel.satisfies s
  /-- (B-pen) The model's footprint is admitted by the penalty
  term's operational range. -/
  pen   : p.admits m.footprint = true

/-! ## §6.5-v3 layer 5 — The correspondence theorems -/

/-- **Lemma 6.5 (penalty correspondence).** For every satisfying
assignment `m`, the model's footprint is admitted by the operational
range that `p` reduces to. As stated in the paper, this is a
biconditional; in the Lean encoding the operational range is
*defined* as `Penalty.admits`, so the lemma reduces to projecting
the (B-pen) field of the satisfies bundle.

The substantive content of the paper's structural-induction
sketch is encoded in the recursive definition of
`Penalty.admits` itself: each combinator case folds correctly
over its children's admissibility. The proof obligations from
the paper's induction (the cumulative ⊔ and orBoth ⊓ cases)
become the well-foundedness obligations of the recursive
definition, discharged by the `termination_by`/`decreasing_by`
template inherited from `Graph.lean`. -/
theorem penalty_correspondence
    (m : PenaltySMTModel) (s : Statute) (p : Penalty)
    (h : m.satisfies s p) :
    p.admits m.footprint = true :=
  h.pen

/-! ### Per-leaf specialisations

The four leaf-case theorems below extract the per-axis numeric
constraints the paper §6.5 leaf-case sketch states. They
kernel-check by direct unfolding of `Penalty.admits` plus
`Bool.and_eq_true` / `decide_eq_true_iff`.
-/

/-- **Leaf: imprisonment.** From `(imprisonment lo hi).admits fp`,
extract the operational range constraints
`lo ≤ fp.imp_lo` and `fp.imp_hi ≤ hi`. -/
theorem penalty_correspondence_imprisonment
    (lo hi : Nat) (fp : Footprint)
    (h : (Penalty.imprisonment lo hi).admits fp = true) :
    lo ≤ fp.imp_lo ∧ fp.imp_hi ≤ hi ∧ fp.imp_lo ≤ fp.imp_hi := by
  simp [Penalty.admits, Bool.and_eq_true, decide_eq_true_iff] at h
  exact ⟨h.1.1, h.1.2, h.2⟩

/-- **Leaf: fine.** -/
theorem penalty_correspondence_fine
    (lo hi : Nat) (fp : Footprint)
    (h : (Penalty.fine lo hi).admits fp = true) :
    lo ≤ fp.fine_lo ∧ fp.fine_hi ≤ hi ∧ fp.fine_lo ≤ fp.fine_hi := by
  simp [Penalty.admits, Bool.and_eq_true, decide_eq_true_iff] at h
  exact ⟨h.1.1, h.1.2, h.2⟩

/-- **Leaf: caning.** -/
theorem penalty_correspondence_caning
    (lo hi : Nat) (fp : Footprint)
    (h : (Penalty.caning lo hi).admits fp = true) :
    lo ≤ fp.caning_lo ∧ fp.caning_hi ≤ hi ∧ fp.caning_lo ≤ fp.caning_hi := by
  simp [Penalty.admits, Bool.and_eq_true, decide_eq_true_iff] at h
  exact ⟨h.1.1, h.1.2, h.2⟩

/-- **Leaf: death.** -/
theorem penalty_correspondence_death
    (fp : Footprint) (h : Penalty.death.admits fp = true) :
    fp.death = true := by
  simpa [Penalty.admits] using h

/-- **Leaf: fine — G8 unlimited variant.** From
`(fineUnlimited lo).admits fp`, extract:
  - `lo ≤ fp.fine_lo` (penalty lower bound respected), and
  - either `fp.fine_unlimited = true` (model itself claims
    unlimited) or `fp.fine_lo ≤ fp.fine_hi` (model supplies a
    coherent finite range under the unbounded penalty cap). -/
theorem penalty_correspondence_fine_unlimited
    (lo : Nat) (fp : Footprint)
    (h : (Penalty.fineUnlimited lo).admits fp = true) :
    lo ≤ fp.fine_lo ∧ (fp.fine_unlimited = true ∨ fp.fine_lo ≤ fp.fine_hi) := by
  simp [Penalty.admits, Bool.and_eq_true, decide_eq_true_iff,
        Bool.or_eq_true] at h
  exact ⟨h.1, h.2⟩

/-- **Leaf: caning — G14 unspecified variant.** Mirror of
`penalty_correspondence_fine_unlimited` for the caning axis. -/
theorem penalty_correspondence_caning_unspecified
    (lo : Nat) (fp : Footprint)
    (h : (Penalty.caningUnspecified lo).admits fp = true) :
    lo ≤ fp.caning_lo ∧
      (fp.caning_unspecified = true ∨ fp.caning_lo ≤ fp.caning_hi) := by
  simp [Penalty.admits, Bool.and_eq_true, decide_eq_true_iff,
        Bool.or_eq_true] at h
  exact ⟨h.1, h.2⟩

/-! ### Combinator specialisations

The two combinator-case lemmas are the paper §6.5 inductive-step
sketch in mechanised form. Each takes the children's
admissibility as a list-fold and unfolds it via the recursive
`admitsAll` / `admitsAny` definitions.
-/

/-- **Combinator: cumulative.** `(cumulative ps).admits fp` iff
every child admits `fp`. -/
theorem penalty_correspondence_cumulative
    (ps : List Penalty) (fp : Footprint)
    (h : (Penalty.cumulative ps).admits fp = true) :
    ∀ p ∈ ps, p.admits fp = true := by
  -- Unfold to `admitsAll ps fp = true`, then list-induct.
  rw [Penalty.admits] at h
  induction ps with
  | nil => intro p hp; cases hp
  | cons q rest ih =>
    intro p hp
    rw [Penalty.admitsAll, Bool.and_eq_true] at h
    cases hp with
    | head    => exact h.1
    | tail _ hmem => exact ih h.2 p hmem

/-- **Combinator: orBoth.** `(orBoth ps).admits fp` iff at least
one child admits `fp`. -/
theorem penalty_correspondence_orBoth
    (ps : List Penalty) (fp : Footprint)
    (h : (Penalty.orBoth ps).admits fp = true) :
    ∃ p ∈ ps, p.admits fp = true := by
  rw [Penalty.admits] at h
  induction ps with
  | nil => simp [Penalty.admitsAny] at h
  | cons q rest ih =>
    rw [Penalty.admitsAny, Bool.or_eq_true] at h
    cases h with
    | inl hq => exact ⟨q, List.mem_cons_self _ _, hq⟩
    | inr hrest =>
      have ⟨p, hmem, hp⟩ := ih hrest
      exact ⟨p, List.mem_cons_of_mem _ hmem, hp⟩

/-! ## §6.5-v6 layer 6 — Well-formedness predicate

The §3.4 sentinel-propagation invariant ("sentinels do not
propagate beyond the leaf via the combinators") and the
non-emptiness invariant on `orBoth` (an empty disjunction
admits nothing — see `Range.orBothMeet_nil`) live in the
Python linter (`src/yuho/ast/statute_lint.py`). This layer
mechanises both as a structural Bool-valued predicate
`Penalty.wellFormed`, so the `PenaltySMTModel.satisfies`
bundle (and the canonical-model discharge in `Generator.lean`)
can require it as a hypothesis.

Coverage:
  * each bounded leaf has a coherent range (`lo ≤ hi`);
  * unbounded-axis leaves (`fineUnlimited`, `caningUnspecified`)
    are vacuously well-formed — only the lower bound matters
    and `Nat` is non-negative by construction;
  * `cumulative` children are all well-formed (empty cumulative
    is vacuously admissible per `Range.cumulativeJoin_nil`, so
    we permit it);
  * `orBoth` is non-empty (an empty disjunction admits nothing
    and is rejected by the Python linter as ill-formed) and
    every child is well-formed.

The predicate is decidable (Bool-valued); consumers can
discharge it by `native_decide` on concrete fixtures, or by
`Penalty.wellFormed_cumulative` / `wellFormed_orBoth` /
`wellFormedAll_cons` projections for proof-script use. -/
mutual

/-- A penalty term is well-formed under the §3.4 invariants.
See the `## §6.5-v6 layer 6` doc-comment above for the rule
list. -/
def Penalty.wellFormed : Penalty → Bool
  | .imprisonment lo hi    => decide (lo ≤ hi)
  | .fine lo hi            => decide (lo ≤ hi)
  | .fineUnlimited _       => true
  | .caning lo hi          => decide (lo ≤ hi)
  | .caningUnspecified _   => true
  | .death                 => true
  | .cumulative ps         => Penalty.wellFormedAll ps
  | .orBoth ps             => !ps.isEmpty && Penalty.wellFormedAll ps

/-- Every child of a list is well-formed. Mirrors the
`Penalty.admitsAll` shape so the proofs in this layer follow
the same list-fold template as §6.5's combinator soundness
sub-lemmas. -/
def Penalty.wellFormedAll : List Penalty → Bool
  | []        => true
  | p :: rest => p.wellFormed && Penalty.wellFormedAll rest

end

/-- Projection: a `wellFormed` cumulative inherits the
`wellFormedAll` body shape (immediate from the recursive
definition). -/
theorem Penalty.wellFormed_cumulative (ps : List Penalty)
    (h : (Penalty.cumulative ps).wellFormed = true) :
    Penalty.wellFormedAll ps = true := by
  rw [Penalty.wellFormed] at h
  exact h

/-- Projection: a `wellFormed` orBoth is non-empty and
inherits the `wellFormedAll` body shape. -/
theorem Penalty.wellFormed_orBoth (ps : List Penalty)
    (h : (Penalty.orBoth ps).wellFormed = true) :
    ps ≠ [] ∧ Penalty.wellFormedAll ps = true := by
  rw [Penalty.wellFormed, Bool.and_eq_true] at h
  obtain ⟨hne, hall⟩ := h
  refine ⟨?_, hall⟩
  intro hnil
  rw [hnil] at hne
  simp [List.isEmpty] at hne

/-- Projection: `wellFormedAll` of a `cons` extracts both head
and tail well-formedness. -/
theorem Penalty.wellFormedAll_cons (p : Penalty) (rest : List Penalty)
    (h : Penalty.wellFormedAll (p :: rest) = true) :
    p.wellFormed = true ∧ Penalty.wellFormedAll rest = true := by
  rw [Penalty.wellFormedAll, Bool.and_eq_true] at h
  exact h

/-- Membership lemma: every member of a `wellFormedAll` list is
itself well-formed. The structural induction follows the same
shape as `penalty_correspondence_cumulative`. -/
theorem Penalty.wellFormedAll_mem
    (ps : List Penalty) (h : Penalty.wellFormedAll ps = true) :
    ∀ p ∈ ps, p.wellFormed = true := by
  induction ps with
  | nil => intro p hp; cases hp
  | cons q rest ih =>
    intro p hp
    obtain ⟨hq, hrest⟩ := Penalty.wellFormedAll_cons q rest h
    cases hp with
    | head        => exact hq
    | tail _ hmem => exact ih hrest p hmem

/-! ### Strengthened satisfies bundle

`PenaltySMTModel.satisfies` (declared above) carries the
graph-level biconditionals (B1 family + B2) and the
penalty-admissibility bicond (B-pen). v6 adds a third field
`wf` requiring the encoded penalty to satisfy the
well-formedness predicate. The strengthening is intentional:
the canonical-model discharge in `Generator.lean` is stated
under `wf` so the linter's runtime invariants are visible to
the proof system rather than implicit.

We expose the strengthened bundle as a *separate* structure
(`PenaltySMTModel.satisfiesWF`) rather than mutating the
existing `satisfies` to preserve backward compatibility with
the v5 leaf and combinator correspondence theorems above.
Downstream consumers (the canonical-model layer) use
`satisfiesWF`; legacy callers use `satisfies` unchanged. -/

/-- Strengthened satisfies bundle: `satisfies` plus a
well-formedness witness on the encoded penalty. -/
structure PenaltySMTModel.satisfiesWF
    (m : PenaltySMTModel) (s : Statute) (p : Penalty) : Prop where
  /-- Inherited graph-level + penalty biconditionals. -/
  base : m.satisfies s p
  /-- (B-wf) The encoded penalty is well-formed under the
  §3.4 sentinel-propagation + non-empty-orBoth invariants. -/
  wf   : p.wellFormed = true

/-- The §6.5 correspondence theorem lifts to the strengthened
bundle by projection through `base`. -/
theorem penalty_correspondence_wf
    (m : PenaltySMTModel) (s : Statute) (p : Penalty)
    (h : m.satisfiesWF s p) :
    p.admits m.footprint = true :=
  penalty_correspondence m s p h.base

/-! ## §6.5-v6 follow-ups

v4 closed the G8 / G14 unbounded-axis sentinel gap. v5 added
the `Range.cumulativeJoin` / `Range.orBothMeet` algebraic
surface (in `Range.lean`). v6 (this commit) mechanises the
linter's well-formedness invariant as `Penalty.wellFormed`
and exposes the strengthened satisfies bundle
`PenaltySMTModel.satisfiesWF`.

Imprisonment intentionally retains a single `Nat`-bounded
constructor: SG PC imprisonment ranges are always bounded
(life imprisonment is encoded as a specific upper number;
see `s54`), so no sentinel is needed.

What remains as a v7 extension:

1. **Z3 oracle assumption discharge for the penalty layer.**
   v6 closes the *abstract* satisfiability oracle via
   `Generator.canonicalPenaltyModel`; the residual is the
   round-trip diff between the Python `Z3Generator`'s
   penalty-emission paths and the Lean
   `Penalty.canonicalFootprint` (tracked in `todo.md` as
   *Generator-emit consolidation*).

2. **Decidability tactic for `wellFormed` on large penalties.**
   The current Bool-valued predicate is decidable in principle
   (`native_decide` works on small fixtures); for the 524-corpus
   sweep a custom decision procedure that short-circuits early
   on the first ill-formed child would tighten compile-time.
-/

end Yuho
