/-
Operational evaluation rules — §4.2 (elements) and §4.3 (exception
precedence) of the paper.

We encode the small-step rules as total Bool-valued functions over
the AST. This makes them computable (so we can `decide` smoke
goals) and gives `=`-based equational reasoning rather than the
relational `Downarrow` judgement form. The two presentations are
equivalent: a relational evaluation `e ⇓ b` corresponds to
`Element.eval e F = b` for the corresponding fact pattern.
-/

import Yuho.AST
import Yuho.Facts

namespace Yuho

/-- Evaluate a leaf element under a fact pattern.
Corresponds to the `Eval-Elem` / `Eval-Elem-Missing` rule pair of
§4.2: a fact-map lookup, with `Facts.empty`'s default `false` realising
the "Missing" case. -/
def Element.eval (e : Element) (F : Facts) : Bool :=
  F e.name

/-- Evaluate an element-tree under a fact pattern.
Corresponds to `Eval-AllOf` / `Eval-AnyOf` of §4.2 — the
combinators distribute over their member judgements. -/
def ElementGroup.eval : ElementGroup → Facts → Bool
  | .leaf e,  F => e.eval F
  | .allOf gs, F => gs.foldr (fun g acc => g.eval F && acc) true
  | .anyOf gs, F => gs.foldr (fun g acc => g.eval F || acc) false

/-- Walk an exception list in declaration order, building the set
of labels that fire. Each exception fires iff its guard holds AND
no defeating sibling already fired. The list-position ordering
serves as the topological sort the §4.3 well-foundedness invariant
guarantees (any cyclic `defeats` is rejected by the linter before
this function ever runs). -/
def Exception.firedSet (xs : List Exception) (F : Facts) : List String :=
  let go : List Exception → List String → List String
    | [], acc => acc
    | x :: rest, acc =>
      let suppressed := x.defeats.any (· ∈ acc)
      if x.guard F && !suppressed
        then go rest (x.label :: acc)
        else go rest acc
  go xs []

/-- Whether a specific exception fires under a fact pattern. -/
def Exception.fires (xs : List Exception) (F : Facts) (label : String) : Bool :=
  decide (label ∈ Exception.firedSet xs F)

/-- A statute convicts iff its elements are all satisfied AND no
exception fires. Corresponds to `Conviction` /
`NoConviction-Elements` / `NoConviction-Excused` in §4.3. -/
def Statute.elementsSatisfied (s : Statute) (F : Facts) : Bool :=
  s.elements.eval F

def Statute.anyExceptionFires (s : Statute) (F : Facts) : Bool :=
  !(Exception.firedSet s.exceptions F).isEmpty

def Statute.convicts (s : Statute) (F : Facts) : Bool :=
  s.elementsSatisfied F && !s.anyExceptionFires F

end Yuho
