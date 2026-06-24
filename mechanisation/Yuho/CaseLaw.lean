/-
Executable case-law effect fragment.
-/

import Yuho.AST
import Yuho.Eval
import Yuho.Facts

namespace Yuho

def preferOption {α : Type} (preferred fallback : Option α) : Option α :=
  match preferred with
  | some value => some value
  | none => fallback

inductive CaseEffectKind where
  | requires : CaseEffectKind
  | satisfies : CaseEffectKind
  | excludes : CaseEffectKind
deriving Repr, DecidableEq, BEq

structure CaseBurdenShift where
  burden : String
  standard : Option String
deriving Repr, DecidableEq, BEq

abbrev CaseFactMetadata := FactMetadata

abbrev CaseFact := TypedFact

abbrev CaseFacts := TypedFacts

structure CaseEffect where
  target : String
  kind : CaseEffectKind
  fact : String
  burdenShift : Option CaseBurdenShift
  jurisdiction : Option String
deriving Repr, DecidableEq, BEq

inductive CourtLevel where
  | apex : CourtLevel
  | supreme : CourtLevel
  | courtOfAppeal : CourtLevel
  | appellate : CourtLevel
  | high : CourtLevel
  | district : CourtLevel
  | trial : CourtLevel
  | lower : CourtLevel
deriving Repr, DecidableEq, BEq

inductive DoctrineRole where
  | ratio : DoctrineRole
  | holding : DoctrineRole
  | obiter : DoctrineRole
deriving Repr, DecidableEq, BEq

structure CasePrecedence where
  jurisdictionRank : Nat
  courtRank : Nat
  doctrineRoleRank : Nat
  decisionDate : Nat
  declarationOrder : Nat
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
  burdenShift : Option CaseBurdenShift
  jurisdiction : Option String
  treatments : List (TreatmentKind × String)
  precedence : CasePrecedence
deriving Repr, DecidableEq, BEq

def CaseEffectKind.apply (kind : CaseEffectKind) (base fact : Bool) : Bool :=
  match kind with
  | .requires => base && fact
  | .satisfies => base || fact
  | .excludes => base && !fact

def CaseEffectKind.fromSurface (effect : String) : Option CaseEffectKind :=
  if effect = "require" || effect = "requires" ||
      effect = "narrow" || effect = "narrows" then
    some .requires
  else if effect = "satisfy" || effect = "satisfies" ||
      effect = "expand" || effect = "expands" then
    some .satisfies
  else if effect = "exclude" || effect = "excludes" then
    some .excludes
  else
    none

def CaseEffectKind.applySurface (effect : String) (base fact : Bool) :
    Option Bool :=
  (CaseEffectKind.fromSurface effect).map (fun kind => kind.apply base fact)

def CaseEffect.appliesTo (effect : CaseEffect) (name : String) : Bool :=
  decide (effect.target = name)

def CaseEffect.apply (effect : CaseEffect) (base : Bool) (F : Facts) : Bool :=
  effect.kind.apply base (F effect.fact)

def CaseBurdenShift.toRequirement (shift : CaseBurdenShift) :
    BurdenRequirement :=
  { burden := some shift.burden, standard := shift.standard }

def CaseFactMetadata.permitsBurden (metadata : CaseFactMetadata)
    (shift : CaseBurdenShift) : Bool :=
  metadata.satisfiesBurden shift.toRequirement

def CaseFact.truthWithBurden (fact : CaseFact) (shift : CaseBurdenShift) :
    Bool :=
  TypedFact.truthWithBurden fact shift.toRequirement

def CaseEffect.jurisdictionPermits (effect : CaseEffect)
    (statuteJurisdiction : Option String) : Bool :=
  match effect.jurisdiction, statuteJurisdiction with
  | some caseJurisdiction, some statuteJurisdiction =>
      decide (caseJurisdiction = statuteJurisdiction)
  | _, _ => true

def CaseEffect.effectiveFact (effect : CaseEffect) (F : CaseFacts)
    (statuteJurisdiction : Option String) : Bool :=
  let fact := F effect.fact
  if effect.jurisdictionPermits statuteJurisdiction then
    match effect.burdenShift with
    | none => fact.truth
    | some shift => CaseFact.truthWithBurden fact shift
  else
    fact.truth

def CaseEffect.applyTyped (effect : CaseEffect) (base : Bool)
    (F : CaseFacts) (statuteJurisdiction : Option String) : Bool :=
  effect.kind.apply base (effect.effectiveFact F statuteJurisdiction)

def CaseEffect.applyAll (name : String) (base : Bool) (F : Facts) :
    List CaseEffect → Bool
  | [] => base
  | effect :: rest =>
      let next := if effect.appliesTo name then effect.apply base F else base
      CaseEffect.applyAll name next F rest

def CaseEffect.applyAllTyped (name : String) (base : Bool) (F : CaseFacts)
    (statuteJurisdiction : Option String) : List CaseEffect → Bool
  | [] => base
  | effect :: rest =>
      let next :=
        if effect.appliesTo name then
          effect.applyTyped base F statuteJurisdiction
        else
          base
      CaseEffect.applyAllTyped name next F statuteJurisdiction rest

def Element.evalWithCases (e : Element) (effects : List CaseEffect) (F : Facts) :
    Bool :=
  CaseEffect.applyAll e.name (e.eval F) F effects

def Element.evalWithTypedCases (e : Element) (effects : List CaseEffect)
    (F : Facts) (CF : CaseFacts) (statuteJurisdiction : Option String) : Bool :=
  CaseEffect.applyAllTyped e.name (e.eval F) CF statuteJurisdiction effects

def CourtLevel.rank : CourtLevel → Nat
  | .apex => 50
  | .supreme => 50
  | .courtOfAppeal => 50
  | .appellate => 40
  | .high => 30
  | .district => 20
  | .trial => 10
  | .lower => 10

def DoctrineRole.rank : DoctrineRole → Nat
  | .ratio => 20
  | .holding => 20
  | .obiter => 10

def CourtLevel.fromSurface (level : String) : Option CourtLevel :=
  if level = "apex" then
    some .apex
  else if level = "supreme" then
    some .supreme
  else if level = "court_of_appeal" then
    some .courtOfAppeal
  else if level = "appellate" then
    some .appellate
  else if level = "high" then
    some .high
  else if level = "district" then
    some .district
  else if level = "trial" then
    some .trial
  else if level = "lower" then
    some .lower
  else
    none

def CourtLevel.rankSurface (level : String) : Nat :=
  (CourtLevel.fromSurface level).map CourtLevel.rank |>.getD 0

def DoctrineRole.fromSurface (role : String) : Option DoctrineRole :=
  if role = "ratio" then
    some .ratio
  else if role = "holding" then
    some .holding
  else if role = "obiter" then
    some .obiter
  else
    none

def DoctrineRole.rankSurface (role : String) : Nat :=
  (DoctrineRole.fromSurface role).map DoctrineRole.rank |>.getD 0

def CasePrecedence.jurisdictionRankFor (caseJurisdiction : Option String)
    (statuteJurisdiction : Option String) : Nat :=
  match statuteJurisdiction, caseJurisdiction with
  | none, none => 1
  | none, some _ => 0
  | some _, none => 1
  | some statuteJurisdiction, some caseJurisdiction =>
      if caseJurisdiction = statuteJurisdiction then 2 else 0

def CasePrecedence.fromComponents
    (caseJurisdiction statuteJurisdiction : Option String)
    (courtLevel : Option CourtLevel) (doctrineRole : Option DoctrineRole)
    (decisionDate declarationOrder : Nat) : CasePrecedence :=
  { jurisdictionRank :=
      CasePrecedence.jurisdictionRankFor caseJurisdiction statuteJurisdiction
    courtRank := courtLevel.map CourtLevel.rank |>.getD 0
    doctrineRoleRank := doctrineRole.map DoctrineRole.rank |>.getD 0
    decisionDate := decisionDate
    declarationOrder := declarationOrder
  }

def CasePrecedence.fromSurfaceComponents
    (caseJurisdiction statuteJurisdiction : Option String)
    (courtLevel doctrineRole : Option String)
    (decisionDate declarationOrder : Nat) : CasePrecedence :=
  { jurisdictionRank :=
      CasePrecedence.jurisdictionRankFor caseJurisdiction statuteJurisdiction
    courtRank := courtLevel.map CourtLevel.rankSurface |>.getD 0
    doctrineRoleRank := doctrineRole.map DoctrineRole.rankSurface |>.getD 0
    decisionDate := decisionDate
    declarationOrder := declarationOrder
  }

def CasePrecedence.betterThan (left right : CasePrecedence) : Bool :=
  if left.jurisdictionRank = right.jurisdictionRank then
    if left.courtRank = right.courtRank then
      if left.doctrineRoleRank = right.doctrineRoleRank then
        if left.decisionDate = right.decisionDate then
          decide (right.declarationOrder < left.declarationOrder)
        else
          decide (right.decisionDate < left.decisionDate)
      else
        decide (right.doctrineRoleRank < left.doctrineRoleRank)
    else
      decide (right.courtRank < left.courtRank)
  else
    decide (right.jurisdictionRank < left.jurisdictionRank)

def TreatmentKind.adopts : TreatmentKind → Bool
  | .followed => true
  | .approved => true
  | .applied => true
  | .distinguished => false
  | .overruled => false
  | .reversed => false
  | .disapproved => false

def TreatmentKind.inactivates : TreatmentKind → Bool
  | .followed => false
  | .approved => false
  | .applied => false
  | .distinguished => true
  | .overruled => true
  | .reversed => true
  | .disapproved => true

def TreatmentKind.fromSurface (kind : String) : Option TreatmentKind :=
  if kind = "followed" || kind = "follows" then
    some .followed
  else if kind = "approved" || kind = "approves" then
    some .approved
  else if kind = "applied" || kind = "applies" then
    some .applied
  else if kind = "distinguished" || kind = "distinguishes" then
    some .distinguished
  else if kind = "overruled" || kind = "overrules" then
    some .overruled
  else if kind = "reversed" || kind = "reverses" then
    some .reversed
  else if kind = "disapproved" || kind = "disapproves" then
    some .disapproved
  else
    none

def TreatmentKind.adoptsSurface (kind : String) : Bool :=
  match TreatmentKind.fromSurface kind with
  | some treatment => treatment.adopts
  | none => false

def TreatmentKind.inactivatesSurface (kind : String) : Bool :=
  match TreatmentKind.fromSurface kind with
  | some treatment => treatment.inactivates
  | none => false

def CaseAuthority.adoptsCase (authority : CaseAuthority) (targetName : String) :
    Bool :=
  authority.treatments.any
    (fun treatment =>
      treatment.fst.adopts && decide (treatment.snd = targetName))

def CaseAuthority.inactivatesCase (authority : CaseAuthority)
    (targetName : String) : Bool :=
  authority.treatments.any
    (fun treatment =>
      treatment.fst.inactivates && decide (treatment.snd = targetName))

def CaseAuthority.isInactiveIn (authority : CaseAuthority)
    (cases : List CaseAuthority) : Bool :=
  cases.any (fun candidate => candidate.inactivatesCase authority.name)

def CaseAuthority.materializeEffect (authority : CaseAuthority)
    (effect : CaseEffect) : CaseEffect :=
  { effect with
    target := authority.element
    burdenShift := preferOption authority.burdenShift effect.burdenShift
    jurisdiction := preferOption authority.jurisdiction effect.jurisdiction
  }

def CaseAuthority.betterThan (left right : CaseAuthority) : Bool :=
  left.precedence.betterThan right.precedence

def CaseAuthority.bestByPrecedence? : List CaseAuthority → Option CaseAuthority
  | [] => none
  | first :: rest =>
      some (rest.foldl
        (fun best candidate =>
          if candidate.betterThan best then candidate else best)
        first)

def CaseAuthority.effectsConflict (left right : CaseAuthority) : Bool :=
  match left.effect, right.effect with
  | some leftEffect, some rightEffect =>
      decide (leftEffect.fact = rightEffect.fact) &&
        decide (leftEffect.kind ≠ rightEffect.kind)
  | _, _ => false

def CaseAuthority.sameEffectFact (left right : CaseAuthority) : Bool :=
  match left.effect, right.effect with
  | some leftEffect, some rightEffect =>
      decide (leftEffect.fact = rightEffect.fact)
  | _, _ => false

def CaseAuthority.hasEffectConflictIn (authority : CaseAuthority)
    (cases : List CaseAuthority) : Bool :=
  cases.any (fun candidate => authority.effectsConflict candidate)

def CaseAuthority.bucketHasEffectConflict : List CaseAuthority → Bool
  | [] => false
  | authority :: rest =>
      authority.hasEffectConflictIn rest ||
        CaseAuthority.bucketHasEffectConflict rest

def CaseAuthority.resolveConflictBucket (cases : List CaseAuthority) :
    List CaseAuthority :=
  if CaseAuthority.bucketHasEffectConflict cases then
    match CaseAuthority.bestByPrecedence? cases with
    | some authority => [authority]
    | none => []
  else
    cases

def CaseAuthority.effectBucket (authority : CaseAuthority)
    (cases : List CaseAuthority) : List CaseAuthority :=
  cases.filter (fun candidate => authority.sameEffectFact candidate)

def CaseAuthority.keepAfterEffectConflicts (authority : CaseAuthority)
    (cases : List CaseAuthority) : Bool :=
  let bucket := authority.effectBucket cases
  if CaseAuthority.bucketHasEffectConflict bucket then
    match CaseAuthority.bestByPrecedence? bucket with
    | some best => decide (authority = best)
    | none => false
  else
    true

def CaseAuthority.resolveEffectConflicts
    (cases : List CaseAuthority) : List CaseAuthority :=
  cases.filter (fun authority => authority.keepAfterEffectConflicts cases)

def CaseAuthority.adoptedEffectFrom (authority target : CaseAuthority) :
    Option CaseEffect :=
  if authority.adoptsCase target.name then
    target.effect.map (fun effect => authority.materializeEffect effect)
  else
    none

def CaseAuthority.lookup (cases : List CaseAuthority) (name : String) :
    Option CaseAuthority :=
  cases.find? (fun authority => decide (authority.name = name))

def CaseAuthority.resolvedEffectIn (authority : CaseAuthority)
    (cases : List CaseAuthority) : Nat → Option CaseEffect
  | 0 => none
  | Nat.succ fuel =>
      if authority.isInactiveIn cases then
        none
      else
        match authority.effect with
        | some effect => some (authority.materializeEffect effect)
        | none =>
            let rec firstAdopted : List (TreatmentKind × String) → Option CaseEffect
              | [] => none
              | treatment :: rest =>
                  if treatment.fst.adopts then
                    match CaseAuthority.lookup cases treatment.snd with
                    | some target =>
                        match target.resolvedEffectIn cases fuel with
                        | some effect =>
                            some (authority.materializeEffect effect)
                        | none => firstAdopted rest
                    | none => firstAdopted rest
                  else
                    firstAdopted rest
            firstAdopted authority.treatments

theorem CaseEffectKind.requires_false (base : Bool) :
    CaseEffectKind.apply .requires base false = false := by
  cases base <;> rfl

theorem CaseEffectKind.satisfies_true (base : Bool) :
    CaseEffectKind.apply .satisfies base true = true := by
  cases base <;> rfl

theorem CaseEffectKind.excludes_true (base : Bool) :
    CaseEffectKind.apply .excludes base true = false := by
  cases base <;> rfl

theorem CaseEffectKind.narrows_fromSurface :
    CaseEffectKind.fromSurface "narrows" = some .requires := by
  rfl

theorem CaseEffectKind.expands_fromSurface :
    CaseEffectKind.fromSurface "expands" = some .satisfies := by
  rfl

theorem CaseEffectKind.unknown_fromSurface :
    CaseEffectKind.fromSurface "persuades" = none := by
  rfl

theorem CaseEffectKind.narrow_surface_false (base : Bool) :
    CaseEffectKind.applySurface "narrow" base false = some false := by
  cases base <;> rfl

theorem CaseEffectKind.expand_surface_true (base : Bool) :
    CaseEffectKind.applySurface "expand" base true = some true := by
  cases base <;> rfl

theorem CaseEffect.applyAll_nil (name : String) (base : Bool) (F : Facts) :
    CaseEffect.applyAll name base F [] = base := by
  rfl

theorem Element.evalWithCases_nil (e : Element) (F : Facts) :
    e.evalWithCases [] F = e.eval F := by
  rfl

theorem Element.evalWithTypedCases_nil
    (e : Element) (F : Facts) (CF : CaseFacts)
    (statuteJurisdiction : Option String) :
    e.evalWithTypedCases [] F CF statuteJurisdiction = e.eval F := by
  rfl

theorem CaseFact.truthWithBurden_matching
    (shift : CaseBurdenShift) :
    CaseFact.truthWithBurden
      ({ truth := true
         metadata :=
          some { burden := some shift.burden, standard := shift.standard }
       } : CaseFact) shift = true := by
  cases shift with
  | mk burden standard =>
  cases standard <;>
    simp [CaseFact.truthWithBurden, CaseFactMetadata.permitsBurden,
      CaseBurdenShift.toRequirement, TypedFact.truthWithBurden,
      FactMetadata.satisfiesBurden]

theorem CaseFact.truthWithBurden_wrong_burden
    (shift : CaseBurdenShift) (wrongBurden : String)
    (h : wrongBurden ≠ shift.burden) :
    CaseFact.truthWithBurden
      ({ truth := true
         metadata := some { burden := some wrongBurden, standard := none }
       } : CaseFact) shift = false := by
  simp [CaseFact.truthWithBurden, CaseFactMetadata.permitsBurden,
    CaseBurdenShift.toRequirement, TypedFact.truthWithBurden,
    FactMetadata.satisfiesBurden, h]

theorem CaseEffect.effectiveFact_local_jurisdiction_uses_burden
    (effect : CaseEffect) (F : CaseFacts) (shift : CaseBurdenShift)
    (statuteJurisdiction : String)
    (hShift : effect.burdenShift = some shift)
    (hJurisdiction : effect.jurisdiction = some statuteJurisdiction) :
    effect.effectiveFact F (some statuteJurisdiction) =
      CaseFact.truthWithBurden (F effect.fact) shift := by
  simp [CaseEffect.effectiveFact, CaseEffect.jurisdictionPermits,
    hShift, hJurisdiction]

theorem CaseEffect.effectiveFact_foreign_jurisdiction_ignores_burden
    (effect : CaseEffect) (F : CaseFacts) (shift : CaseBurdenShift)
    (caseJurisdiction statuteJurisdiction : String)
    (hShift : effect.burdenShift = some shift)
    (hJurisdiction : effect.jurisdiction = some caseJurisdiction)
    (hMismatch : caseJurisdiction ≠ statuteJurisdiction) :
    effect.effectiveFact F (some statuteJurisdiction) =
      (F effect.fact).truth := by
  simp [CaseEffect.effectiveFact, CaseEffect.jurisdictionPermits,
    hShift, hJurisdiction, hMismatch]

theorem CasePrecedence.local_beats_foreign_same_court :
    ({ jurisdictionRank := 2, courtRank := 30, doctrineRoleRank := 0,
       decisionDate := 20200101, declarationOrder := 1 } :
      CasePrecedence).betterThan
      ({ jurisdictionRank := 0, courtRank := 30, doctrineRoleRank := 0,
         decisionDate := 20260101, declarationOrder := 0 } :
        CasePrecedence) = true := by
  rfl

theorem CasePrecedence.higher_court_beats_newer_date :
    ({ jurisdictionRank := 2, courtRank := 50, doctrineRoleRank := 0,
       decisionDate := 20200101, declarationOrder := 0 } :
      CasePrecedence).betterThan
      ({ jurisdictionRank := 2, courtRank := 30, doctrineRoleRank := 0,
         decisionDate := 20260101, declarationOrder := 1 } :
        CasePrecedence) = true := by
  rfl

theorem CasePrecedence.newer_date_breaks_same_court_tie :
    ({ jurisdictionRank := 2, courtRank := 50, doctrineRoleRank := 0,
       decisionDate := 20260101, declarationOrder := 1 } :
      CasePrecedence).betterThan
      ({ jurisdictionRank := 2, courtRank := 50, doctrineRoleRank := 0,
         decisionDate := 20200101, declarationOrder := 0 } :
        CasePrecedence) = true := by
  rfl

theorem CourtLevel.apex_rank : CourtLevel.apex.rank = 50 := by
  rfl

theorem DoctrineRole.obiter_rank : DoctrineRole.obiter.rank = 10 := by
  rfl

theorem CourtLevel.courtOfAppeal_surface_rank :
    CourtLevel.rankSurface "court_of_appeal" = 50 := by
  rfl

theorem CourtLevel.unknown_surface_rank :
    CourtLevel.rankSurface "magistrate" = 0 := by
  rfl

theorem DoctrineRole.holding_surface_rank :
    DoctrineRole.rankSurface "holding" = 20 := by
  rfl

theorem DoctrineRole.unknown_surface_rank :
    DoctrineRole.rankSurface "commentary" = 0 := by
  rfl

theorem CasePrecedence.local_jurisdiction_rank :
    CasePrecedence.jurisdictionRankFor (some "singapore")
      (some "singapore") = 2 := by
  rfl

theorem CasePrecedence.surface_components_rank :
    CasePrecedence.fromSurfaceComponents (some "singapore") (some "singapore")
      (some "high") (some "obiter") 20260101 3 =
      { jurisdictionRank := 2
        courtRank := 30
        doctrineRoleRank := 10
        decisionDate := 20260101
        declarationOrder := 3 } := by
  rfl

theorem CaseAuthority.resolveConflictBucket_nil :
    CaseAuthority.resolveConflictBucket [] = [] := by
  rfl

theorem CaseAuthority.resolveEffectConflicts_nil :
    CaseAuthority.resolveEffectConflicts [] = [] := by
  rfl

theorem CaseAuthority.keepAfterEffectConflicts_no_bucket_conflict
    (authority : CaseAuthority) (cases : List CaseAuthority)
    (h : CaseAuthority.bucketHasEffectConflict
      (authority.effectBucket cases) = false) :
    authority.keepAfterEffectConflicts cases = true := by
  simp [CaseAuthority.keepAfterEffectConflicts, h]

theorem CaseAuthority.resolveEffectConflicts_keeps_pair
    (left right : CaseAuthority)
    (hLeft : left.keepAfterEffectConflicts [left, right] = true)
    (hRight : right.keepAfterEffectConflicts [left, right] = true) :
    CaseAuthority.resolveEffectConflicts [left, right] = [left, right] := by
  simp [CaseAuthority.resolveEffectConflicts, hLeft, hRight]

theorem CaseAuthority.materializeEffect_burden_override
    (authority : CaseAuthority) (effect : CaseEffect)
    (shift : CaseBurdenShift)
    (h : authority.burdenShift = some shift) :
    (authority.materializeEffect effect).burdenShift = some shift := by
  simp [CaseAuthority.materializeEffect, preferOption, h]

theorem CaseAuthority.materializeEffect_target_override
    (authority : CaseAuthority) (effect : CaseEffect) :
    (authority.materializeEffect effect).target = authority.element := by
  rfl

theorem CaseAuthority.materializeEffect_kind_preserved
    (authority : CaseAuthority) (effect : CaseEffect) :
    (authority.materializeEffect effect).kind = effect.kind := by
  rfl

theorem CaseAuthority.materializeEffect_fact_preserved
    (authority : CaseAuthority) (effect : CaseEffect) :
    (authority.materializeEffect effect).fact = effect.fact := by
  rfl

theorem TreatmentKind.followed_adopts :
    TreatmentKind.followed.adopts = true := by
  rfl

theorem TreatmentKind.overruled_not_adopts :
    TreatmentKind.overruled.adopts = false := by
  rfl

theorem TreatmentKind.overruled_inactivates :
    TreatmentKind.overruled.inactivates = true := by
  rfl

theorem TreatmentKind.followed_not_inactivates :
    TreatmentKind.followed.inactivates = false := by
  rfl

theorem TreatmentKind.follows_surface_adopts :
    TreatmentKind.adoptsSurface "follows" = true := by
  rfl

theorem TreatmentKind.approves_surface_adopts :
    TreatmentKind.adoptsSurface "approves" = true := by
  rfl

theorem TreatmentKind.overrules_surface_inactivates :
    TreatmentKind.inactivatesSurface "overrules" = true := by
  rfl

theorem TreatmentKind.distinguishes_surface_inactivates :
    TreatmentKind.inactivatesSurface "distinguishes" = true := by
  rfl

theorem TreatmentKind.unknown_surface_not_adopting :
    TreatmentKind.adoptsSurface "mentions" = false := by
  rfl

theorem CaseAuthority.resolvedEffectIn_zero
    (authority : CaseAuthority) (cases : List CaseAuthority) :
    authority.resolvedEffectIn cases 0 = none := by
  simp [CaseAuthority.resolvedEffectIn]

theorem CaseAuthority.resolvedEffectIn_own
    (authority : CaseAuthority) (cases : List CaseAuthority)
    (fuel : Nat) (effect : CaseEffect)
    (hActive : authority.isInactiveIn cases = false)
    (h : authority.effect = some effect) :
    authority.resolvedEffectIn cases (Nat.succ fuel) =
      some (authority.materializeEffect effect) := by
  simp [CaseAuthority.resolvedEffectIn, hActive, h]

theorem CaseAuthority.resolvedEffectIn_inactive
    (authority : CaseAuthority) (cases : List CaseAuthority)
    (fuel : Nat)
    (hInactive : authority.isInactiveIn cases = true) :
    authority.resolvedEffectIn cases (Nat.succ fuel) = none := by
  simp [CaseAuthority.resolvedEffectIn, hInactive]

theorem CaseAuthority.resolvedEffectIn_missing_followed_target
    (authority : CaseAuthority) (cases : List CaseAuthority)
    (fuel : Nat) (targetName : String)
    (hNoEffect : authority.effect = none)
    (hMissing : CaseAuthority.lookup cases targetName = none) :
    ({ authority with treatments := [(.followed, targetName)] } :
      CaseAuthority).resolvedEffectIn cases (Nat.succ fuel) = none := by
  simp [CaseAuthority.resolvedEffectIn,
    CaseAuthority.resolvedEffectIn.firstAdopted, hNoEffect]
  intro _
  simp [CaseAuthority.resolvedEffectIn.firstAdopted, hMissing]

end Yuho
