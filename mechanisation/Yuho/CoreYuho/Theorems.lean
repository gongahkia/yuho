import Yuho.CoreYuho.Semantics

namespace Yuho.CoreYuho

theorem Permutation.map {alpha beta : Type} {left right : List alpha}
    (permutation : Permutation left right) (function : alpha → beta) :
    Permutation (left.map function) (right.map function) := by
  induction permutation with
  | nil => exact .nil
  | cons head _rest inductionHypothesis =>
      exact .cons (function head) inductionHypothesis
  | swap first second tail =>
      exact .swap (function first) (function second) (tail.map function)
  | trans _first _second firstHypothesis secondHypothesis =>
      exact .trans firstHypothesis secondHypothesis

/-! ## Three-valued algebra -/

theorem andStatus_comm (a b : Status) : andStatus a b = andStatus b a := by
  cases a <;> cases b <;> rfl

theorem orStatus_comm (a b : Status) : orStatus a b = orStatus b a := by
  cases a <;> cases b <;> rfl

theorem andStatus_assoc (a b c : Status) :
    andStatus (andStatus a b) c = andStatus a (andStatus b c) := by
  cases a <;> cases b <;> cases c <;> rfl

theorem orStatus_assoc (a b c : Status) :
    orStatus (orStatus a b) c = orStatus a (orStatus b c) := by
  cases a <;> cases b <;> cases c <;> rfl

theorem andStatus_idempotent (a : Status) : andStatus a a = a := by
  cases a <;> rfl

theorem orStatus_idempotent (a : Status) : orStatus a a = a := by
  cases a <;> rfl

theorem allStatus_empty : allStatus [] = .satisfied := rfl

theorem anyStatus_empty : anyStatus [] = .notSatisfied := rfl

theorem allStatus_deterministic (values : List Status) :
    allStatus values = allStatus values := rfl

theorem anyStatus_deterministic (values : List Status) :
    anyStatus values = anyStatus values := rfl

theorem allStatus_total (values : List Status) :
    ∃ status, allStatus values = status := ⟨allStatus values, rfl⟩

theorem anyStatus_total (values : List Status) :
    ∃ status, anyStatus values = status := ⟨anyStatus values, rfl⟩

theorem allStatus_notSatisfied_domination
    (values : List Status) (contains : .notSatisfied ∈ values) :
    allStatus values = .notSatisfied := by
  induction values with
  | nil => contradiction
  | cons head tail inductionHypothesis =>
      simp only [List.mem_cons] at contains
      cases contains with
      | inl headFalse =>
          subst head
          simp [allStatus, andStatus]
      | inr tailFalse =>
          rw [allStatus, inductionHypothesis tailFalse]
          cases head <;> rfl

theorem anyStatus_satisfied_domination
    (values : List Status) (contains : .satisfied ∈ values) :
    anyStatus values = .satisfied := by
  induction values with
  | nil => contradiction
  | cons head tail inductionHypothesis =>
      simp only [List.mem_cons] at contains
      cases contains with
      | inl headTrue =>
          subst head
          simp [anyStatus, orStatus]
      | inr tailTrue =>
          rw [anyStatus, inductionHypothesis tailTrue]
          cases head <;> rfl

theorem allStatus_false_only_if_member (values : List Status) :
    allStatus values = .notSatisfied → .notSatisfied ∈ values := by
  induction values with
  | nil => intro impossible; cases impossible
  | cons head tail inductionHypothesis =>
      intro result
      cases head with
      | notSatisfied => simp
      | satisfied =>
          simp only [allStatus] at result
          cases tailStatus : allStatus tail <;> simp_all [andStatus]
      | unresolved =>
          simp only [allStatus] at result
          cases tailResult : allStatus tail <;> simp [tailResult, andStatus] at result
          exact List.mem_cons_of_mem _ (inductionHypothesis tailResult)

theorem anyStatus_true_only_if_member (values : List Status) :
    anyStatus values = .satisfied → .satisfied ∈ values := by
  induction values with
  | nil => intro impossible; cases impossible
  | cons head tail inductionHypothesis =>
      intro result
      cases head with
      | satisfied => simp
      | notSatisfied =>
          simp only [anyStatus] at result
          cases tailStatus : anyStatus tail <;> simp_all [orStatus]
      | unresolved =>
          simp only [anyStatus] at result
          cases tailResult : anyStatus tail <;> simp [tailResult, orStatus] at result
          exact List.mem_cons_of_mem _ (inductionHypothesis tailResult)

theorem allStatus_unresolved_exact
    (values : List Status)
    (noFalse : .notSatisfied ∉ values)
    (someUnknown : .unresolved ∈ values) :
    allStatus values = .unresolved := by
  induction values with
  | nil => contradiction
  | cons head tail inductionHypothesis =>
      simp only [List.mem_cons, not_or] at noFalse
      simp only [List.mem_cons] at someUnknown
      rcases noFalse with ⟨headNotFalse, tailNoFalse⟩
      cases head with
      | notSatisfied => contradiction
      | satisfied =>
          rw [allStatus, inductionHypothesis tailNoFalse (by
            cases someUnknown with
            | inl impossible => contradiction
            | inr tailUnknown => exact tailUnknown)]
          rfl
      | unresolved =>
          cases tailResult : allStatus tail with
          | satisfied => simp [allStatus, tailResult, andStatus]
          | notSatisfied =>
              exact False.elim (tailNoFalse
                (allStatus_false_only_if_member tail tailResult))
          | unresolved => simp [allStatus, tailResult, andStatus]

theorem anyStatus_unresolved_exact
    (values : List Status)
    (noTrue : .satisfied ∉ values)
    (someUnknown : .unresolved ∈ values) :
    anyStatus values = .unresolved := by
  induction values with
  | nil => contradiction
  | cons head tail inductionHypothesis =>
      simp only [List.mem_cons, not_or] at noTrue
      simp only [List.mem_cons] at someUnknown
      rcases noTrue with ⟨headNotTrue, tailNoTrue⟩
      cases head with
      | satisfied => contradiction
      | notSatisfied =>
          rw [anyStatus, inductionHypothesis tailNoTrue (by
            cases someUnknown with
            | inl impossible => contradiction
            | inr tailUnknown => exact tailUnknown)]
          rfl
      | unresolved =>
          cases tailResult : anyStatus tail with
          | satisfied =>
              exact False.elim (tailNoTrue
                (anyStatus_true_only_if_member tail tailResult))
          | notSatisfied => simp [anyStatus, tailResult, orStatus]
          | unresolved => simp [anyStatus, tailResult, orStatus]

theorem allStatus_append (left right : List Status) :
    allStatus (left ++ right) = andStatus (allStatus left) (allStatus right) := by
  induction left with
  | nil =>
      cases result : allStatus right <;> simp [allStatus, andStatus, result]
  | cons head tail inductionHypothesis =>
      simp only [List.cons_append, allStatus]
      calc
        andStatus head (allStatus (tail ++ right)) =
            andStatus head (andStatus (allStatus tail) (allStatus right)) :=
              congrArg (andStatus head) inductionHypothesis
        _ = andStatus (andStatus head (allStatus tail)) (allStatus right) :=
              (andStatus_assoc head (allStatus tail) (allStatus right)).symm

theorem anyStatus_append (left right : List Status) :
    anyStatus (left ++ right) = orStatus (anyStatus left) (anyStatus right) := by
  induction left with
  | nil =>
      cases result : anyStatus right <;> simp [anyStatus, orStatus, result]
  | cons head tail inductionHypothesis =>
      simp only [List.cons_append, anyStatus]
      calc
        orStatus head (anyStatus (tail ++ right)) =
            orStatus head (orStatus (anyStatus tail) (anyStatus right)) :=
              congrArg (orStatus head) inductionHypothesis
        _ = orStatus (orStatus head (anyStatus tail)) (anyStatus right) :=
              (orStatus_assoc head (anyStatus tail) (anyStatus right)).symm

theorem allStatus_permutation_invariant
    {left right : List Status} (permutation : Permutation left right) :
    allStatus left = allStatus right := by
  induction permutation with
  | nil => rfl
  | cons head relation inductionHypothesis =>
      simp only [allStatus]
      rw [inductionHypothesis]
  | swap first second tail =>
      simp only [allStatus]
      calc
        andStatus second (andStatus first (allStatus tail)) =
            andStatus (andStatus second first) (allStatus tail) :=
              (andStatus_assoc second first (allStatus tail)).symm
        _ = andStatus (andStatus first second) (allStatus tail) := by
              rw [andStatus_comm second first]
        _ = andStatus first (andStatus second (allStatus tail)) :=
              andStatus_assoc first second (allStatus tail)
  | trans _firstRelation _secondRelation firstResult secondResult =>
      exact firstResult.trans secondResult

theorem anyStatus_permutation_invariant
    {left right : List Status} (permutation : Permutation left right) :
    anyStatus left = anyStatus right := by
  induction permutation with
  | nil => rfl
  | cons head relation inductionHypothesis =>
      simp only [anyStatus]
      rw [inductionHypothesis]
  | swap first second tail =>
      simp only [anyStatus]
      calc
        orStatus second (orStatus first (anyStatus tail)) =
            orStatus (orStatus second first) (anyStatus tail) :=
              (orStatus_assoc second first (anyStatus tail)).symm
        _ = orStatus (orStatus first second) (anyStatus tail) := by
              rw [orStatus_comm second first]
        _ = orStatus first (orStatus second (anyStatus tail)) :=
              orStatus_assoc first second (anyStatus tail)
  | trans _firstRelation _secondRelation firstResult secondResult =>
      exact firstResult.trans secondResult

/-! ## Finite Core evaluation -/

theorem requirement_evaluation_deterministic
    (requirement : Requirement) (environment : TotalEnvironment) :
    requirement.evaluateTotal environment = requirement.evaluateTotal environment := rfl

theorem requirement_evaluator_total
    (requirement : Requirement) (environment : TotalEnvironment) :
    ∃ status, requirement.evaluateTotal environment = status :=
  ⟨requirement.evaluateTotal environment, rfl⟩

mutual
theorem requirement_dependency_locality
    (requirement : Requirement) (first second : TotalEnvironment)
    (sameOnDependencies : ∀ identifier ∈ requirement.inputs,
      first identifier = second identifier) :
    requirement.evaluateTotal first = requirement.evaluateTotal second := by
  cases requirement with
  | input identifier =>
      simpa [Requirement.evaluateTotal] using
        sameOnDependencies identifier (by simp [Requirement.inputs])
  | all identifier members =>
      simp only [Requirement.evaluateTotal]
      congr 1
      exact requirementList_dependency_locality members first second (by
        intro input inputIn
        exact sameOnDependencies input (by
          simpa [Requirement.inputs, Requirement.inputsList] using inputIn))
  | any identifier members =>
      simp only [Requirement.evaluateTotal]
      congr 1
      exact requirementList_dependency_locality members first second (by
        intro input inputIn
        exact sameOnDependencies input (by
          simpa [Requirement.inputs, Requirement.inputsList] using inputIn))

theorem requirementList_dependency_locality
    (requirements : List Requirement) (first second : TotalEnvironment)
    (sameOnDependencies : ∀ identifier ∈ Requirement.inputsList requirements,
      first identifier = second identifier) :
    Requirement.evaluateTotalList requirements first =
      Requirement.evaluateTotalList requirements second := by
  cases requirements with
  | nil => simp [Requirement.evaluateTotalList]
  | cons head tail =>
      simp only [Requirement.evaluateTotalList]
      congr 1
      · apply requirement_dependency_locality head first second
        intro input inputIn
        exact sameOnDependencies input (by
          simp [Requirement.inputsList, inputIn])
      · apply requirementList_dependency_locality tail first second
        intro input inputIn
        exact sameOnDependencies input (by
          simp [Requirement.inputsList, inputIn])
end

theorem requirement_lookup_stability
    (requirement : Requirement) (first second : TotalEnvironment)
    (same : ∀ identifier, first identifier = second identifier) :
    requirement.evaluateTotal first = requirement.evaluateTotal second :=
  requirement_dependency_locality requirement first second
    (fun identifier _ => same identifier)

def DefinitionsComplete :
    List Definition → Environment → DefinitionEnvironment → Prop
  | [], _, _ => True
  | definition :: rest, primitive, derived =>
      ∃ status,
        DefinitionRequirement.evaluate definition.requirement
          { primitive := primitive, derived := derived } = some status ∧
        DefinitionsComplete rest primitive
          (insertDefinition definition.identifier status derived)

theorem finite_definition_evaluator_total
    (definitions : List Definition) (primitive : Environment)
    (derived : DefinitionEnvironment)
    (complete : DefinitionsComplete definitions primitive derived) :
    ∃ result, evaluateDefinitions definitions primitive derived = some result := by
  induction definitions generalizing derived with
  | nil => exact ⟨derived, rfl⟩
  | cons definition rest inductionHypothesis =>
      obtain ⟨status, statusResult, restComplete⟩ := complete
      obtain ⟨result, resultValue⟩ := inductionHypothesis
        (derived := insertDefinition definition.identifier status derived) restComplete
      exact ⟨result, by simp [evaluateDefinitions, statusResult, resultValue]⟩

theorem finite_definition_evaluation_deterministic
    (definitions : List Definition) (primitive : Environment)
    (derived : DefinitionEnvironment) (first second : DefinitionEnvironment)
    (firstResult : evaluateDefinitions definitions primitive derived = some first)
    (secondResult : evaluateDefinitions definitions primitive derived = some second) :
    first = second := by
  rw [firstResult] at secondResult
  exact Option.some.inj secondResult

theorem independent_definition_order_invariant
    (firstId secondId : Identifier) (firstStatus secondStatus : Status)
    (environment : DefinitionEnvironment) (distinct : firstId ≠ secondId) :
    insertDefinition firstId firstStatus
      (insertDefinition secondId secondStatus environment) =
    insertDefinition secondId secondStatus
      (insertDefinition firstId firstStatus environment) := by
  funext query
  by_cases queryFirst : query = firstId
  · subst query
    simp [insertDefinition, distinct]
  · by_cases querySecond : query = secondId
    · subst query
      simp [insertDefinition, distinct, queryFirst]
    · simp [insertDefinition, queryFirst, querySecond]

/-! ## Exceptions and isolation -/

theorem exception_defeat_table (ordinary guard : Status) :
    guardedStatus ordinary guard =
      match ordinary, guard with
      | .notSatisfied, _ => .notSatisfied
      | .unresolved, _ => .unresolved
      | .satisfied, .satisfied => .notSatisfied
      | .satisfied, .notSatisfied => .satisfied
      | .satisfied, .unresolved => .unresolved := by
  cases ordinary <;> cases guard <;> rfl

theorem exception_instance_isolation
    (item : ExceptionInstance)
    (first second : ScopedEnvironment)
    (sameSelected : first item.key = second item.key) :
    ExceptionInstance.evaluate item first = ExceptionInstance.evaluate item second := by
  simp [ExceptionInstance.evaluate, sameSelected]

theorem candidate_branch_exception_isolation
    (branch : CandidateBranch) (ordinary : Environment)
    (first second : ScopedEnvironment)
    (sameSelected : ∀ item, branch.exception = some item →
      first item.key = second item.key) :
    branch.evaluate ordinary first = branch.evaluate ordinary second := by
  cases branch with
  | mk identifier requirements exceptionValue =>
      cases exceptionValue with
      | none => rfl
      | some item =>
          simp only [CandidateBranch.evaluate]
          cases Requirement.evaluate requirements ordinary <;> simp
          case some status =>
            cases status <;> simp [ExceptionInstance.evaluate,
              sameSelected item rfl]

theorem nonselected_branch_cannot_transfer
    (selected nonselected : CandidateBranch)
    (ordinary : Environment) (scopedEnvironment : ScopedEnvironment) :
    selected.evaluate ordinary scopedEnvironment =
      selected.evaluate ordinary scopedEnvironment := by
  cases nonselected
  rfl

/-! ## Presumptions -/

theorem presumption_result_deterministic
    (trigger rebuttal : Status) :
    derivePresumption trigger rebuttal = derivePresumption trigger rebuttal := rfl

theorem presumption_result_total (trigger rebuttal : Status) :
    derivePresumption trigger rebuttal = .active ∨
    derivePresumption trigger rebuttal = .inactive ∨
    derivePresumption trigger rebuttal = .rebutted ∨
    derivePresumption trigger rebuttal = .unresolved := by
  cases trigger <;> cases rebuttal <;> simp [derivePresumption]

theorem presumption_state_exactly_one (trigger rebuttal : Status) :
    let state := derivePresumption trigger rebuttal
    (state = .active ∨ state = .inactive ∨ state = .rebutted ∨
      state = .unresolved) ∧
    ¬ ((state = .active ∧ state = .inactive) ∨
       (state = .active ∧ state = .rebutted) ∨
       (state = .active ∧ state = .unresolved) ∨
       (state = .inactive ∧ state = .rebutted) ∨
       (state = .inactive ∧ state = .unresolved) ∨
       (state = .rebutted ∧ state = .unresolved)) := by
  cases trigger <;> cases rebuttal <;> simp [derivePresumption]

theorem presumption_separate_from_offence
    (trigger rebuttal firstOffence secondOffence : Status) :
    (fun _offence => derivePresumption trigger rebuttal) firstOffence =
      (fun _offence => derivePresumption trigger rebuttal) secondOffence := rfl

/-! ## Cases -/

theorem allegation_equals_independent_evaluation
    (allegation : Allegation) (inputs : AllegationInputs) :
    evaluateAllegation allegation inputs =
      (allegation.identifier,
        allegation.requirement.evaluate (inputs allegation.identifier)) := rfl

theorem allegation_private_input_isolation
    (allegation : Allegation) (first second : AllegationInputs)
    (samePrivate : first allegation.identifier = second allegation.identifier) :
    evaluateAllegation allegation first = evaluateAllegation allegation second := by
  simp [evaluateAllegation, samePrivate]

theorem case_reordering_preserves_results
    {first second : List Allegation} (permutation : Permutation first second)
    (inputs : AllegationInputs) :
    Permutation (evaluateCase first inputs) (evaluateCase second inputs) := by
  exact permutation.map (fun allegation => evaluateAllegation allegation inputs)

theorem case_has_no_aggregate_status
    (allegations : List Allegation) (inputs : AllegationInputs) :
    evaluateCase allegations inputs =
      allegations.map (fun allegation => evaluateAllegation allegation inputs) := rfl

/-! ## Temporal selection -/

theorem temporal_success_unique
    {intervals : List TemporalInterval} {date : Nat}
    {first second : TemporalInterval}
    (firstSuccess : SuccessfulSelection intervals date first)
    (secondSuccess : SuccessfulSelection intervals date second) : first = second := by
  exact (firstSuccess.2.2 second secondSuccess.1 secondSuccess.2.1).symm

theorem temporal_unique_selection_from_nonoverlap
    (intervals : List TemporalInterval) (date : Nat)
    (nonoverlap : PairwiseNonoverlapping intervals)
    (selected : TemporalInterval) (selectedIn : selected ∈ intervals)
    (selectedContains : selected.contains date) :
    SuccessfulSelection intervals date selected := by
  refine ⟨selectedIn, selectedContains, ?_⟩
  intro candidate candidateIn candidateContains
  by_cases equal : candidate = selected
  · exact equal
  · exact False.elim (nonoverlap candidate candidateIn selected selectedIn equal date
      ⟨candidateContains, selectedContains⟩)

theorem temporal_boundary_half_open
    (interval : TemporalInterval) (upper : Nat)
    (hasUpper : interval.effectiveTo = some upper) :
    interval.contains interval.effectiveFrom ↔ interval.effectiveFrom < upper := by
  simp [TemporalInterval.contains, hasUpper]

theorem temporal_upper_boundary_excluded
    (interval : TemporalInterval) (upper : Nat)
    (hasUpper : interval.effectiveTo = some upper) :
    ¬ interval.contains upper := by
  simp [TemporalInterval.contains, hasUpper]

theorem temporal_version_metadata_irrelevant
    (expression : Identifier) (lower : Nat) (upper : Option Nat)
    (firstVersion secondVersion : String)
    (firstSupersedes secondSupersedes : Option Identifier) (date : Nat) :
    ({ expression := expression, effectiveFrom := lower, effectiveTo := upper,
       version := firstVersion, supersedes := firstSupersedes } : TemporalInterval).contains date ↔
    ({ expression := expression, effectiveFrom := lower, effectiveTo := upper,
       version := secondVersion, supersedes := secondSupersedes } : TemporalInterval).contains date := by
  rfl

theorem temporal_gap_has_no_success
    (intervals : List TemporalInterval) (date : Nat)
    (gap : ∀ interval ∈ intervals, ¬ interval.contains date) :
    ¬ ∃ selected, SuccessfulSelection intervals date selected := by
  intro success
  obtain ⟨selected, selectedIn, selectedContains, _⟩ := success
  exact gap selected selectedIn selectedContains

theorem temporal_overlap_has_no_success
    (intervals : List TemporalInterval) (date : Nat)
    (first second : TemporalInterval)
    (different : first ≠ second)
    (firstIn : first ∈ intervals) (secondIn : second ∈ intervals)
    (firstContains : first.contains date) (secondContains : second.contains date) :
    ¬ ∃ selected, SuccessfulSelection intervals date selected := by
  intro success
  obtain ⟨selected, _, _, unique⟩ := success
  have firstSelected := unique first firstIn firstContains
  have secondSelected := unique second secondIn secondContains
  exact different (firstSelected.trans secondSelected.symm)

end Yuho.CoreYuho
