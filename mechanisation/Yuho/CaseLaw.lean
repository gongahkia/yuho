/-
Executable case-law effect fragment.
-/

import Yuho.AST
import Yuho.Eval
import Yuho.Facts

namespace Yuho

inductive CaseEffectKind where
  | requires : CaseEffectKind
  | satisfies : CaseEffectKind
  | excludes : CaseEffectKind
deriving Repr, DecidableEq, BEq

structure CaseEffect where
  target : String
  kind : CaseEffectKind
  fact : String
deriving Repr, DecidableEq, BEq

inductive TreatmentKind where
  | followed : TreatmentKind
  | approved : TreatmentKind
  | applied : TreatmentKind
  | distinguished : TreatmentKind
  | overruled : TreatmentKind
  | reversed : TreatmentKind
  | disapproved : TreatmentKind
deriving Repr, DecidableEq, BEq

structure CaseAuthority where
  name : String
  element : String
  effect : Option CaseEffect
  treatments : List (TreatmentKind × String)
deriving Repr

def CaseEffectKind.apply (kind : CaseEffectKind) (base fact : Bool) : Bool :=
  match kind with
  | .requires => base && fact
  | .satisfies => base || fact
  | .excludes => base && !fact

def CaseEffect.appliesTo (effect : CaseEffect) (name : String) : Bool :=
  decide (effect.target = name)

def CaseEffect.apply (effect : CaseEffect) (base : Bool) (F : Facts) : Bool :=
  effect.kind.apply base (F effect.fact)

def CaseEffect.applyAll (name : String) (base : Bool) (F : Facts) :
    List CaseEffect → Bool
  | [] => base
  | effect :: rest =>
      let next := if effect.appliesTo name then effect.apply base F else base
      CaseEffect.applyAll name next F rest

def Element.evalWithCases (e : Element) (effects : List CaseEffect) (F : Facts) :
    Bool :=
  CaseEffect.applyAll e.name (e.eval F) F effects

def TreatmentKind.adopts : TreatmentKind → Bool
  | .followed => true
  | .approved => true
  | .applied => true
  | .distinguished => false
  | .overruled => false
  | .reversed => false
  | .disapproved => false

def CaseAuthority.adoptsCase (authority : CaseAuthority) (targetName : String) :
    Bool :=
  authority.treatments.any
    (fun treatment =>
      treatment.fst.adopts && decide (treatment.snd = targetName))

def CaseAuthority.adoptedEffectFrom (authority target : CaseAuthority) :
    Option CaseEffect :=
  if authority.adoptsCase target.name then
    target.effect.map (fun effect => { effect with target := authority.element })
  else
    none

theorem CaseEffectKind.requires_false (base : Bool) :
    CaseEffectKind.apply .requires base false = false := by
  cases base <;> rfl

theorem CaseEffectKind.satisfies_true (base : Bool) :
    CaseEffectKind.apply .satisfies base true = true := by
  cases base <;> rfl

theorem CaseEffectKind.excludes_true (base : Bool) :
    CaseEffectKind.apply .excludes base true = false := by
  cases base <;> rfl

theorem CaseEffect.applyAll_nil (name : String) (base : Bool) (F : Facts) :
    CaseEffect.applyAll name base F [] = base := by
  rfl

theorem Element.evalWithCases_nil (e : Element) (F : Facts) :
    e.evalWithCases [] F = e.eval F := by
  rfl

theorem TreatmentKind.followed_adopts :
    TreatmentKind.followed.adopts = true := by
  rfl

theorem TreatmentKind.overruled_not_adopts :
    TreatmentKind.overruled.adopts = false := by
  rfl

end Yuho
