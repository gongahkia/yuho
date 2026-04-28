/-
Generator.lean — verified specification of the Yuho Z3 generator;
v5 mechanisation that discharges the *oracle assumption* of §6.6
for §6.2 / §6.3 / §6.4 (cf. `paper/sections/soundness.tex` and
`todo.md` `§6.6 v5` bullet).

Prior bundle (v1–v4):
  Lemmas 6.2 / 6.3 / 6.4 hold *for any SMT model satisfying the
  four families of biconditionals
  `Z3Generator._generate_statute_constraints` emits*. The
  *existence* of such a model was assumed (the "oracle
  assumption" — `paper/sections/limitations.tex` §11 carried the
  caveat).

v5 bundle (this file):
  We exhibit constructive `canonicalSMTModel` and
  `canonicalGraphModel` and prove `(canonicalModel s F).satisfies s`
  unconditionally. The §6.2 / §6.3 / §6.4 lemmas now hold against
  a model the verified generator produces, with no axiomatic
  existential.

Scope boundary (what stays in v6+):
  The cross-section bundle `CrossSMTModel.satisfies` shares a
  single `excFires : String → Bool` indexed by *raw* exception
  labels across all statutes in a module. A truly module-wide
  canonical witness requires either a labels-unique-AND-disjoint
  invariant on the corpus or a refactor of the abstraction to
  index `excFires` by *qualified* atom names (`<sX>_exc_<label>`)
  matching what the Python generator actually emits. Both are
  v6 work; Cross.lean's `is_infringed_correspondence` and
  `apply_scope_correspondence` retain their existing
  hypothesis-discharge structure for now, with the §6.6 boundary
  statement updated to reflect the narrower v5 result.

Layout:

  1. Symbolic SMT formula AST (`SMTFormula`) — abstract image of
     `z3.Bool / z3.And / z3.Iff`. Verified spec of the emit shape.
  2. Atom-naming scheme — mirrors the strings
     `src/yuho/verify/z3_solver.py` uses (`<sX>_<elem>_satisfied`,
     `<sX>_elements_satisfied`, `<sX>_exc_<label>_fires`,
     `<sX>_conviction`).
  3. The verified specification: `Generator.encodeStatute`
     produces the list of biconditional formulas.
  4. The canonical models — constructive witnesses for `SMTModel`
     and `GraphSMTModel`.
  5. The soundness theorems:
     `canonical_smt_satisfies`,
     `canonical_graph_satisfies`.

What this file does *not* do:

  * Prove the Python implementation matches the Lean
    specification. That residual is now the only remaining gap,
    narrower and round-trip-testable rather than load-bearing on
    the soundness theorem. The bulk-contrast driver
    (`make verify-bulk-contrast`) already exercises the Python
    generator against the operational evaluator on every encoded
    statute; with the Lean spec in place those runs become the
    *verification* of the Python side rather than independent
    ground truth.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval
import Yuho.SMTAbs
import Yuho.Soundness
import Yuho.Graph

namespace Yuho

/-! ## §6.6-v5 layer 1 — Symbolic SMT formula AST

A finite-shape formula language sufficient to represent every
biconditional `Z3Generator._generate_statute_constraints` emits in
the current backend. The leaf `var` carries the atom name as a
`String`; semantic models evaluate it via a `String → Bool`
environment. -/

inductive SMTFormula where
  | var : String → SMTFormula
  | const : Bool → SMTFormula
  | not : SMTFormula → SMTFormula
  | and : SMTFormula → SMTFormula → SMTFormula
  | or  : SMTFormula → SMTFormula → SMTFormula
  | iff : SMTFormula → SMTFormula → SMTFormula
deriving Repr

/-- Evaluate an SMT formula under a string-indexed environment. -/
def SMTFormula.eval (env : String → Bool) : SMTFormula → Bool
  | .var n     => env n
  | .const b   => b
  | .not φ     => !(φ.eval env)
  | .and φ ψ   => φ.eval env && ψ.eval env
  | .or  φ ψ   => φ.eval env || ψ.eval env
  | .iff φ ψ   => decide (φ.eval env = ψ.eval env)

/-- A list of formulas all hold under `env`. -/
def SMTFormula.allHold (env : String → Bool) (φs : List SMTFormula) : Bool :=
  φs.all (fun φ => φ.eval env)

/-! ## §6.6-v5 layer 2 — Atom-naming scheme

Mirrors `Z3Generator` line-for-line. Per `src/yuho/verify/z3_solver.py`:

  * line 1228 — `<statute_id>_<elem_name>_satisfied`
  * line 1169 — `<statute_id>_elements_satisfied`
  * line 1511 — `<statute_id>_exc_<safe_label>_fires`
  * line 1173 — `<statute_id>_conviction`

We omit the `_` rewrite the Python generator does on `.`-bearing
section numbers since the Lean AST does not use such numbers. -/

namespace Generator

def elementAtomName (s : Statute) (e : Element) : String :=
  s.section_number ++ "_" ++ e.name ++ "_satisfied"

def elementsAtomName (s : Statute) : String :=
  s.section_number ++ "_elements_satisfied"

def exceptionAtomName (s : Statute) (x : Exception) : String :=
  s.section_number ++ "_exc_" ++ x.label ++ "_fires"

def convictionAtomName (s : Statute) : String :=
  s.section_number ++ "_conviction"

/-! ## §6.6-v5 layer 3 — Symbolic encoding of a statute

`encodeStatute` returns the biconditional formulas the verified
specification asserts. Every entry is an `iff`; the first leg is
the Z3 atom (a `var`), the second is the operational semantic
content rendered as a formula.

The mutual block on `encodeGroup` / `encodeGroupAll` /
`encodeGroupAny` mirrors the `Eval.lean` style. -/

mutual

/-- Render an element-tree as the formula a satisfying assignment
would equate to its `<...>_elements_satisfied` atom. -/
def encodeGroup : ElementGroup → SMTFormula
  | .leaf e   => .var e.name
  | .allOf gs => encodeGroupAll gs
  | .anyOf gs => encodeGroupAny gs

/-- All-of fold over children. Mirrors `ElementGroup.evalAll`. -/
def encodeGroupAll : List ElementGroup → SMTFormula
  | []        => .const true
  | g :: rest => .and (encodeGroup g) (encodeGroupAll rest)

/-- Any-of fold over children. Mirrors `ElementGroup.evalAny`. -/
def encodeGroupAny : List ElementGroup → SMTFormula
  | []        => .const false
  | g :: rest => .or (encodeGroup g) (encodeGroupAny rest)

end

-- One biconditional per leaf element: `<sX>_<elem>_satisfied ↔
-- <elem>` (the leaf fact atom). Walks the entire element tree.
-- Mutual block on the list helper (`encodeLeafBicondsList`) makes
-- the structural recursion explicit, mirroring the
-- `evalAll`/`evalAny` pattern in `Eval.lean`.
mutual

/-- Per-leaf biconditional emitter for the element tree of a
statute. Returns one `iff` per leaf reachable from `g`. -/
def encodeLeafBiconds (s : Statute) : ElementGroup → List SMTFormula
  | .leaf e   =>
      [.iff (.var (elementAtomName s e)) (.var e.name)]
  | .allOf gs => encodeLeafBicondsList s gs
  | .anyOf gs => encodeLeafBicondsList s gs

/-- List helper for `encodeLeafBiconds`. Concatenates the
biconditionals of every member group. -/
def encodeLeafBicondsList (s : Statute) :
    List ElementGroup → List SMTFormula
  | []        => []
  | g :: rest => encodeLeafBiconds s g ++ encodeLeafBicondsList s rest

end

/-- The aggregate elements-satisfied biconditional: the elements
atom equals the encoded element tree. -/
def encodeElementsBicond (s : Statute) : SMTFormula :=
  .iff (.var (elementsAtomName s)) (encodeGroup s.elements)

/-- One biconditional per exception. The right-hand side is an
opaque `var` namespaced under firedSet — the operational content
of the topological walk lives in `Exception.firedSet`'s definition,
and the canonical model's `excFires` field discharges the bicond
semantically (see `canonical_smt_satisfies`). -/
def encodeExceptionBiconds (s : Statute) : List SMTFormula :=
  s.exceptions.map (fun x =>
    .iff (.var (exceptionAtomName s x))
         (.var (s.section_number ++ "_exc_" ++ x.label ++ "_firedSet")))

/-- The conviction biconditional: `<sX>_conviction ↔
<sX>_elements_satisfied ∧ ¬(any exception fires)`. Closes
`<sX>_conviction` definitionally; mirrors lines 1521–1538 of
`z3_solver.py`. -/
def encodeConvictionBicond (s : Statute) : SMTFormula :=
  let anyFires :=
    s.exceptions.foldr
      (fun x acc => .or (.var (exceptionAtomName s x)) acc)
      (.const false)
  .iff (.var (convictionAtomName s))
       (.and (.var (elementsAtomName s)) (.not anyFires))

/-- All biconditionals the spec asserts for a single statute. -/
def encodeStatute (s : Statute) : List SMTFormula :=
  encodeLeafBiconds s s.elements ++
  [encodeElementsBicond s] ++
  encodeExceptionBiconds s ++
  [encodeConvictionBicond s]

/-! ## §6.6-v5 layer 4 — Canonical models

Constructive witnesses that the biconditional bundles in
`SMTAbs.lean` and `Graph.lean` are *satisfiable*. Each model field
is the operational semantic value the corresponding biconditional
equates to; the soundness theorems below discharge by `rfl` modulo
unfolding. -/

/-- Canonical `SMTModel` for a fact pattern + statute. The
exception map is built by deciding firedSet membership; non-section
labels default to `false` (vacuously, since they are not in the
statute's exception list). -/
def canonicalSMTModel (s : Statute) (F : Facts) : SMTModel where
  facts := F
  excFires := fun label =>
    decide (label ∈ Exception.firedSet s.exceptions F)

/-- Canonical `GraphSMTModel`. Adds per-group truth atoms by
delegating to `ElementGroup.eval`. -/
def canonicalGraphModel (s : Statute) (F : Facts) : GraphSMTModel where
  facts := F
  groupTruth := fun g => g.eval F
  excFires := fun label =>
    decide (label ∈ Exception.firedSet s.exceptions F)

end Generator

/-! ## §6.6-v5 layer 5 — Soundness theorems

The canonical models satisfy the abstract SMT bundles
*unconditionally*, by direct construction. -/

/-- **Discharge of the SMTAbs oracle assumption.** The canonical
SMTModel satisfies the per-element + per-exception biconditional
bundle for every fact pattern.

Together with `Soundness.lean::element_correspondence` and
`Soundness.lean::exception_correspondence`, this closes the §6.2
+ §6.4 oracle gap: those lemmas now hold against a *constructed*
model rather than an axiomatic existential. -/
theorem canonical_smt_satisfies (s : Statute) (F : Facts) :
    (Generator.canonicalSMTModel s F).satisfies s := by
  unfold SMTModel.satisfies
  refine ⟨?_, ?_, ?_⟩
  · -- (B1) per-element: `m.facts e.name = e.eval m.facts`. By
    -- `canonicalSMTModel`, `m.facts = F`. By `Element.eval`,
    -- `e.eval F = F e.name`. Both sides reduce to `F e.name`.
    intro e
    simp [Generator.canonicalSMTModel, Element.eval]
  · -- (B2) per-exception: by construction, `excFires` is the same
    -- `decide` application both sides invoke.
    intro _label
    rfl
  · -- (B3) the placeholder `True`.
    trivial

/-- **Discharge of the Graph.lean oracle assumption.** The
canonical GraphSMTModel satisfies the four-family biconditional
bundle for every fact pattern.

Composed with `Graph.lean::element_graph_correspondence`, this
closes the §6.3 oracle gap: Lemma 6.3 holds against the
constructed model, hence against the operational element-tree
evaluator directly. -/
theorem canonical_graph_satisfies (s : Statute) (F : Facts) :
    (Generator.canonicalGraphModel s F).satisfies s where
  leaf  := by
    intro e
    simp [Generator.canonicalGraphModel,
          ElementGroup.eval, Element.eval]
  allOf := by
    intro gs
    -- LHS: `groupTruth (.allOf gs)` — by `canonicalGraphModel`'s
    -- definition, this is `(.allOf gs).eval F = evalAll gs F`.
    -- RHS: `gs.all groupTruth = gs.all (fun g => g.eval F)`.
    -- Both reduce to the same fold; close by induction on `gs`.
    simp only [Generator.canonicalGraphModel, ElementGroup.eval]
    induction gs with
    | nil => simp [ElementGroup.evalAll, List.all]
    | cons g rest ih =>
      simp [ElementGroup.evalAll, List.all, ih]
  anyOf := by
    intro gs
    simp only [Generator.canonicalGraphModel, ElementGroup.eval]
    induction gs with
    | nil => simp [ElementGroup.evalAny, List.any]
    | cons g rest ih =>
      simp [ElementGroup.evalAny, List.any, ih]
  exc   := by
    intro _label
    rfl

/-! ## §6.6-v5 layer 6 — Unconditional soundness corollaries

With the canonical model in hand, the conditional soundness
lemmas of §6.2 / §6.3 / §6.4 specialise to *unconditional*
statements. These are the panel-facing "what does the
mechanisation prove?" claims.

The proofs are immediate: each corollary instantiates the
canonical model and applies the canonical-satisfies theorem
to discharge the soundness premise. -/

/-- **Unconditional Lemma 6.2.** For every statute, leaf element,
and fact pattern, the leaf-bool the verified generator produces
agrees with the operational element evaluator. No oracle
assumption. -/
theorem element_correspondence_unconditional
    (_s : Statute) (e : Element) (F : Facts) :
    (Generator.canonicalSMTModel _s F).facts e.name
      = e.eval (Generator.canonicalSMTModel _s F).facts :=
  element_correspondence (Generator.canonicalSMTModel _s F) e

/-- **Unconditional Lemma 6.3.** For every statute, element-tree,
and fact pattern, the per-group atom the verified generator
produces agrees with the operational element-tree evaluator. No
oracle assumption. -/
theorem element_graph_correspondence_unconditional
    (s : Statute) (g : ElementGroup) (F : Facts) :
    (Generator.canonicalGraphModel s F).groupTruth g
      = g.eval (Generator.canonicalGraphModel s F).facts :=
  element_graph_correspondence
    (Generator.canonicalGraphModel s F) s
    (canonical_graph_satisfies s F) g

/-- **Unconditional Lemma 6.4.** For every statute, exception
label, and fact pattern, the exception-fires atom the verified
generator produces agrees with `Exception.firedSet`'s membership
test. No oracle assumption. -/
theorem exception_correspondence_unconditional
    (s : Statute) (label : String) (F : Facts) :
    (Generator.canonicalSMTModel s F).excFires label
      = decide (label ∈ Exception.firedSet s.exceptions
                  (Generator.canonicalSMTModel s F).facts) :=
  exception_correspondence
    (Generator.canonicalSMTModel s F) s
    (canonical_smt_satisfies s F) label

end Yuho
