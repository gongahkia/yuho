/-
Operational evaluation rules — §4.2 (elements) and §4.3 (exception
precedence) of the paper.

We encode the small-step rules as total Bool-valued functions over
the AST. This makes them computable (so we can `decide` smoke
goals) and gives `=`-based equational reasoning rather than the
relational `Downarrow` judgement form. The two presentations are
equivalent: a relational evaluation `e ⇓ b` corresponds to
`Element.eval e F = b` for the corresponding fact pattern.

Lean 4's structural-recursion checker can't see through the nested
`List` recursion in `ElementGroup.eval` directly, so we split it
into a mutual block (`evalAll` / `evalAny`) where the recursion is
explicitly on the list. Equivalent semantically to a list-fold.
-/

import Yuho.AST
import Yuho.Facts

namespace Yuho

/-- Evaluate a leaf element under a fact pattern.
Corresponds to the `Eval-Elem` / `Eval-Elem-Missing` rule pair of
§4.2: a fact-map lookup, with `Facts.empty`'s default `false`
realising the "Missing" case. -/
def Element.eval (e : Element) (F : Facts) : Bool :=
  F e.name

-- ElementGroup.eval and the two list helpers share a mutual-recursion
-- block. `evalAll` / `evalAny` handle the list recursion explicitly so
-- the structural-recursion checker is satisfied (foldr-via-lambda
-- doesn't expose `g.eval` to the checker).
mutual

/-- Evaluate an element-tree under a fact pattern.
Corresponds to `Eval-AllOf` / `Eval-AnyOf` of §4.2 — the combinators
distribute over their member judgements. -/
def ElementGroup.eval : ElementGroup → Facts → Bool
  | .leaf e,  F => e.eval F
  | .allOf gs, F => ElementGroup.evalAll gs F
  | .anyOf gs, F => ElementGroup.evalAny gs F

/-- All-of: every member group must hold under `F`. -/
def ElementGroup.evalAll : List ElementGroup → Facts → Bool
  | [],         _ => true
  | g :: rest,  F => g.eval F && ElementGroup.evalAll rest F

/-- Any-of: at least one member group must hold under `F`. -/
def ElementGroup.evalAny : List ElementGroup → Facts → Bool
  | [],         _ => false
  | g :: rest,  F => g.eval F || ElementGroup.evalAny rest F

end

/-- Auxiliary: walk the exception list in declaration order with an
accumulator of labels already fired. Each exception fires iff its
guard holds AND no defeating sibling already fired. The list-position
ordering serves as the topological sort the §4.3 well-foundedness
invariant guarantees (any cyclic `defeats` is rejected by the
linter before this function ever runs). -/
def Exception.firedSetAux :
    List Exception → List String → Facts → List String
  | [],        acc, _ => acc
  | x :: rest, acc, F =>
      let suppressed := x.defeats.any (fun lbl => decide (lbl ∈ acc))
      if x.guard F && !suppressed
        then Exception.firedSetAux rest (x.label :: acc) F
        else Exception.firedSetAux rest acc F

/-- The set of exception labels that fire under the supplied
fact pattern. -/
def Exception.firedSet (xs : List Exception) (F : Facts) : List String :=
  Exception.firedSetAux xs [] F

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
