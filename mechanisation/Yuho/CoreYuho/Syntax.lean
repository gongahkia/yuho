/-
Finite syntax and semantic domains for Core Yuho v0.1.

This namespace is deliberately separate from the older Boolean Yuho
mechanisation.  It models the normalized, three-valued Haskell Core described
in docs/rewrite/CORE-YUHO-LANGUAGE-REPORT-v0.1.md.
-/

import Std

namespace Yuho.CoreYuho

inductive Status where
  | satisfied
  | notSatisfied
  | unresolved
  deriving Repr, DecidableEq, BEq

abbrev Identifier := String
abbrev Actor := String
abbrev Role := String
abbrev ActContext := String
abbrev InstanceId := String

abbrev Environment := Identifier → Option Status
abbrev TotalEnvironment := Identifier → Status

inductive Permutation {alpha : Type} : List alpha → List alpha → Prop where
  | nil : Permutation [] []
  | cons (head : alpha) {left right : List alpha} :
      Permutation left right → Permutation (head :: left) (head :: right)
  | swap (first second : alpha) (tail : List alpha) :
      Permutation (second :: first :: tail) (first :: second :: tail)
  | trans {first second third : List alpha} :
      Permutation first second → Permutation second third →
        Permutation first third

inductive Requirement where
  | input (identifier : Identifier)
  | all (identifier : Identifier) (members : List Requirement)
  | any (identifier : Identifier) (members : List Requirement)
  deriving Repr

inductive DefinitionRequirement where
  | primitive (identifier : Identifier)
  | derived (identifier : Identifier)
  | all (members : List DefinitionRequirement)
  | any (members : List DefinitionRequirement)
  deriving Repr

structure Definition where
  identifier : Identifier
  requirement : DefinitionRequirement
  deriving Repr

abbrev DefinitionEnvironment := Identifier → Option Status

structure DefinitionInputs where
  primitive : Environment
  derived : DefinitionEnvironment

structure ScopedKey where
  actor : Actor
  role : Role
  context : ActContext
  instanceId : InstanceId
  deriving Repr, DecidableEq

abbrev ScopedEnvironment := ScopedKey → Identifier → Option Status

structure ExceptionInstance where
  key : ScopedKey
  guard : Requirement
  deriving Repr

structure CandidateBranch where
  identifier : Identifier
  ordinary : Requirement
  exception : Option ExceptionInstance
  deriving Repr

inductive PresumptionState where
  | active
  | inactive
  | rebutted
  | unresolved
  deriving Repr, DecidableEq, BEq

structure Allegation where
  identifier : Identifier
  requirement : Requirement
  deriving Repr

abbrev AllegationInputs := Identifier → Environment
abbrev CaseResult := List (Identifier × Option Status)

structure TemporalInterval where
  expression : Identifier
  effectiveFrom : Nat
  effectiveTo : Option Nat
  version : String
  supersedes : Option Identifier
  deriving Repr, DecidableEq

end Yuho.CoreYuho
