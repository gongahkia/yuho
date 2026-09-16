import Yuho.CoreYuho.Syntax

namespace Yuho.CoreYuho

def andStatus : Status → Status → Status
  | .notSatisfied, _ => .notSatisfied
  | _, .notSatisfied => .notSatisfied
  | .unresolved, _ => .unresolved
  | _, .unresolved => .unresolved
  | .satisfied, .satisfied => .satisfied

def orStatus : Status → Status → Status
  | .satisfied, _ => .satisfied
  | _, .satisfied => .satisfied
  | .unresolved, _ => .unresolved
  | _, .unresolved => .unresolved
  | .notSatisfied, .notSatisfied => .notSatisfied

def allStatus : List Status → Status
  | [] => .satisfied
  | head :: tail => andStatus head (allStatus tail)

def anyStatus : List Status → Status
  | [] => .notSatisfied
  | head :: tail => orStatus head (anyStatus tail)

mutual
def Requirement.inputs : Requirement → List Identifier
  | .input identifier => [identifier]
  | .all _ members | .any _ members =>
      Requirement.inputsList members

def Requirement.inputsList : List Requirement → List Identifier
  | [] => []
  | head :: tail => Requirement.inputs head ++ Requirement.inputsList tail
end

mutual
def Requirement.evaluateTotal : Requirement → TotalEnvironment → Status
  | .input identifier, environment => environment identifier
  | .all _ members, environment =>
      allStatus (Requirement.evaluateTotalList members environment)
  | .any _ members, environment =>
      anyStatus (Requirement.evaluateTotalList members environment)

def Requirement.evaluateTotalList :
    List Requirement → TotalEnvironment → List Status
  | [], _ => []
  | head :: tail, environment =>
      Requirement.evaluateTotal head environment ::
        Requirement.evaluateTotalList tail environment
end

mutual
def Requirement.evaluate : Requirement → Environment → Option Status
  | .input identifier, environment => environment identifier
  | .all _ members, environment =>
      (Requirement.evaluateList members environment).map allStatus
  | .any _ members, environment =>
      (Requirement.evaluateList members environment).map anyStatus

def Requirement.evaluateList :
    List Requirement → Environment → Option (List Status)
  | [], _ => some []
  | head :: tail, environment => do
      let headStatus ← Requirement.evaluate head environment
      let tailStatuses ← Requirement.evaluateList tail environment
      pure (headStatus :: tailStatuses)
end

mutual
def DefinitionRequirement.primitiveInputs : DefinitionRequirement → List Identifier
  | .primitive identifier => [identifier]
  | .derived _ => []
  | .all members | .any members =>
      DefinitionRequirement.primitiveInputsList members

def DefinitionRequirement.primitiveInputsList :
    List DefinitionRequirement → List Identifier
  | [] => []
  | head :: tail =>
      DefinitionRequirement.primitiveInputs head ++
        DefinitionRequirement.primitiveInputsList tail
end

mutual
def DefinitionRequirement.dependencies : DefinitionRequirement → List Identifier
  | .primitive _ => []
  | .derived identifier => [identifier]
  | .all members | .any members =>
      DefinitionRequirement.dependenciesList members

def DefinitionRequirement.dependenciesList :
    List DefinitionRequirement → List Identifier
  | [] => []
  | head :: tail =>
      DefinitionRequirement.dependencies head ++
        DefinitionRequirement.dependenciesList tail
end

mutual
def DefinitionRequirement.evaluate :
    DefinitionRequirement → DefinitionInputs → Option Status
  | .primitive identifier, inputs => inputs.primitive identifier
  | .derived identifier, inputs => inputs.derived identifier
  | .all members, inputs =>
      (DefinitionRequirement.evaluateList members inputs).map allStatus
  | .any members, inputs =>
      (DefinitionRequirement.evaluateList members inputs).map anyStatus

def DefinitionRequirement.evaluateList :
    List DefinitionRequirement → DefinitionInputs → Option (List Status)
  | [], _ => some []
  | head :: tail, inputs => do
      let headStatus ← DefinitionRequirement.evaluate head inputs
      let tailStatuses ← DefinitionRequirement.evaluateList tail inputs
      pure (headStatus :: tailStatuses)
end

def insertDefinition
    (identifier : Identifier) (status : Status)
    (environment : DefinitionEnvironment) : DefinitionEnvironment :=
  fun query => if query = identifier then some status else environment query

def evaluateDefinitions :
    List Definition → Environment → DefinitionEnvironment →
      Option DefinitionEnvironment
  | [], _, derived => some derived
  | definition :: rest, primitive, derived => do
      let status ← DefinitionRequirement.evaluate definition.requirement
        { primitive := primitive, derived := derived }
      evaluateDefinitions rest primitive
        (insertDefinition definition.identifier status derived)

def dependenciesAvailable
    (available : List Identifier) (definition : Definition) : Prop :=
  ∀ dependency ∈ definition.requirement.dependencies, dependency ∈ available

def orderedAcyclicFrom : List Identifier → List Definition → Prop
  | _, [] => True
  | available, definition :: rest =>
      dependenciesAvailable available definition ∧
      definition.identifier ∉ available ∧
      orderedAcyclicFrom (definition.identifier :: available) rest

def orderedAcyclic (definitions : List Definition) : Prop :=
  orderedAcyclicFrom [] definitions

def guardedStatus (ordinary guard : Status) : Status :=
  match ordinary with
  | .notSatisfied => .notSatisfied
  | .unresolved => .unresolved
  | .satisfied =>
      match guard with
      | .satisfied => .notSatisfied
      | .notSatisfied => .satisfied
      | .unresolved => .unresolved

def ExceptionInstance.evaluate
    (item : ExceptionInstance) (environment : ScopedEnvironment) : Option Status :=
  Requirement.evaluate item.guard (environment item.key)

def CandidateBranch.evaluate
    (branch : CandidateBranch) (ordinaryEnvironment : Environment)
    (scopedEnvironment : ScopedEnvironment) : Option Status := do
  let ordinary ← branch.ordinary.evaluate ordinaryEnvironment
  match branch.exception with
  | none => pure ordinary
  | some item =>
      match ordinary with
      | .notSatisfied => pure .notSatisfied
      | .unresolved => pure .unresolved
      | .satisfied => do
          let guard ← ExceptionInstance.evaluate item scopedEnvironment
          pure (guardedStatus ordinary guard)

def derivePresumption (trigger rebuttal : Status) : PresumptionState :=
  match trigger, rebuttal with
  | .notSatisfied, _ => .inactive
  | _, .satisfied => .rebutted
  | .satisfied, .notSatisfied => .active
  | _, _ => .unresolved

def applyPresumptions
    (direct : Status) (states : List PresumptionState) : Status :=
  if direct == Status.satisfied || states.any (· == PresumptionState.active)
    then .satisfied
  else if direct == Status.unresolved || states.any (· == PresumptionState.unresolved)
    then .unresolved
  else .notSatisfied

def evaluateAllegation
    (allegation : Allegation) (inputs : AllegationInputs) : Identifier × Option Status :=
  (allegation.identifier,
    Requirement.evaluate allegation.requirement (inputs allegation.identifier))

def evaluateCase (allegations : List Allegation) (inputs : AllegationInputs) : CaseResult :=
  allegations.map (fun allegation => evaluateAllegation allegation inputs)

def TemporalInterval.contains (interval : TemporalInterval) (date : Nat) : Prop :=
  interval.effectiveFrom ≤ date ∧
    match interval.effectiveTo with
    | none => True
    | some upper => date < upper

instance (interval : TemporalInterval) (date : Nat) :
    Decidable (interval.contains date) := by
  unfold TemporalInterval.contains
  cases interval.effectiveTo <;> infer_instance

def SuccessfulSelection
    (intervals : List TemporalInterval) (date : Nat)
    (selected : TemporalInterval) : Prop :=
  selected ∈ intervals ∧ selected.contains date ∧
    ∀ candidate ∈ intervals, candidate.contains date → candidate = selected

def PairwiseNonoverlapping (intervals : List TemporalInterval) : Prop :=
  ∀ first ∈ intervals, ∀ second ∈ intervals,
    first ≠ second → ∀ date, ¬ (first.contains date ∧ second.contains date)

def selectTemporal
    (intervals : List TemporalInterval) (date : Nat) : Option TemporalInterval :=
  match intervals.filter (·.contains date) with
  | [selected] => some selected
  | _ => none

end Yuho.CoreYuho
