import Yuho.CoreYuho.DependencyPlan

/-! Exact scalar reductions. These mathematical definitions do not prove the
production parser, origin mapping, bounds checker or lowering implementation.
Missing inputs are errors; an explicit unknown is a value-state, not zero. -/
namespace Yuho.CoreYuho.Quantitative

inductive Unit where
  | integer | money (currency : String) | count (domain : String)
  deriving Repr, DecidableEq
inductive Filter where
  | yes | no | unknown
  deriving Repr, DecidableEq
inductive Input where
  | missing | unknown | known (value : Int)
  deriving Repr, DecidableEq
abbrev Value := Option Int

def resolve : Input → Except String Value
  | .missing => .error "missing input"
  | .unknown => .ok none
  | .known n => .ok (some n)
def add (a b : Value) : Value := do
  let x ← a
  let y ← b
  pure (x + y)
def sumValues : List Value → Value
  | [] => some 0
  | x :: xs => add x (sumValues xs)
def inclusion (condition : Filter) (value : Value) : Value :=
  match condition with
  | .yes => value
  | .no => some 0
  | .unknown => none
def filteredSum (items : List (Filter × Value)) : Value :=
  sumValues (items.map fun (condition, value) => inclusion condition value)
def scale (factor : Int) (value : Value) : Value := value.map (factor * ·)
def count (conditions : List Filter) : Value :=
  filteredSum (conditions.map fun condition => (condition, some 1))

structure TypedValue where
  unit : Unit
  value : Value
  deriving Repr, DecidableEq
def checkedAdd (a b : TypedValue) : Option TypedValue :=
  if a.unit = b.unit then some ⟨a.unit, add a.value b.value⟩ else none

theorem missing_refused : resolve .missing = .error "missing input" := rfl
theorem explicit_unknown_preserved : resolve .unknown = .ok none := rfl
theorem empty_sum : sumValues [] = some 0 := rfl
theorem exact_integer_sum (a b : Int) : sumValues [some a, some b] = some (a+b) := by
  simp [sumValues, add]
theorem exact_integer_factor (factor value : Int) :
    scale factor (some value) = some (factor * value) := rfl
theorem factor_unknown (factor : Int) : scale factor none = none := rfl
theorem false_excludes_unknown : inclusion .no none = some 0 := rfl
theorem unknown_inclusion_even_zero : inclusion .unknown (some 0) = none := rfl
theorem different_units_refused (a b : TypedValue) (h : a.unit ≠ b.unit) :
    checkedAdd a b = none := by simp [checkedAdd, h]
theorem accepted_result_type (a b result : TypedValue)
    (h : checkedAdd a b = some result) : result.unit = a.unit := by
  unfold checkedAdd at h
  split at h
  next => exact (Option.some.inj h).symm ▸ rfl
  next => contradiction

theorem sum_swap (a b : Value) (rest : List Value) :
    sumValues (a :: b :: rest) = sumValues (b :: a :: rest) := by
  cases a <;> cases b <;> simp [sumValues, add]
  cases sumValues rest <;> simp [add, Int.add_comm, Int.add_left_comm, Int.add_assoc]

abbrev Environment := String → String → Input
def write (env : Environment) (scope output : String) (value : Input) : Environment :=
  fun other name => if other = scope ∧ name = output then value else env other name
theorem other_scope_unchanged (env : Environment) (scope other output name : String)
    (value : Input) (h : other ≠ scope) :
    write env scope output value other name = env other name := by
  simp [write, h]

-- The finite plan folds structurally over a checked order. Production's DAG
-- extraction/certificate checking and numeric bounds are separate obligations.
def runOrdered (env : Environment) (scope : String) :
    List (String × (Environment → Except String Input)) → Except String Environment
  | [] => .ok env
  | (output, computation) :: rest => do
      let result ← computation env
      runOrdered (write env scope output result) scope rest
theorem deterministic_ordered_execution (env : Environment) (scope : String)
    (plan : List (String × (Environment → Except String Input)))
    (left right : Environment)
    (h₁ : runOrdered env scope plan = .ok left)
    (h₂ : runOrdered env scope plan = .ok right) : left = right := by
  exact Except.ok.inj (h₁.symm.trans h₂)

theorem ordered_preserves_other_scope (env result : Environment)
    (scope other name : String) (different : other ≠ scope)
    (plan : List (String × (Environment → Except String Input)))
    (evaluated : runOrdered env scope plan = .ok result) :
    result other name = env other name := by
  induction plan generalizing env with
  | nil =>
      simp only [runOrdered] at evaluated
      cases evaluated
      rfl
  | cons item rest ih =>
      rcases item with ⟨output, computation⟩
      cases step : computation env with
      | error message =>
          simp only [runOrdered, step] at evaluated
          cases evaluated
      | ok value =>
          simp [runOrdered, step] at evaluated
          rw [ih (write env scope output value) evaluated]
          exact other_scope_unchanged env scope other output name value different

end Yuho.CoreYuho.Quantitative
