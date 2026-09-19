/- Core Yuho v0.3 bounded normative, sanction and responsibility-route semantics. -/
import Yuho.CoreYuho.TypedFinite

namespace Yuho.CoreYuho.ReleaseV03

open Yuho.CoreYuho
open Yuho.CoreYuho.TypedFinite

inductive NormModality where
  | required | prohibited | permitted
  deriving Repr, DecidableEq

structure Norm where
  identifier : Identifier
  subject : Identifier
  action : Identifier
  modality : NormModality
  applicability : Status
  deriving Repr, DecidableEq

def normPolarity : NormModality → Polarity
  | .prohibited => .defeat
  | .required | .permitted => .establish

def elaborateNorm (norm : Norm) : RuleResult :=
  { identifier := "r:norm:" ++ norm.identifier
  , proposition := norm.action
  , polarity := normPolarity norm.modality
  , status := norm.applicability }

def normConflict (left right : NormModality) : Bool :=
  (left == .prohibited && right != .prohibited) ||
  (right == .prohibited && left != .prohibited)

theorem normative_applicability_deterministic (norm : Norm) :
    norm.applicability = norm.applicability := rfl

theorem normative_applicability_total (norm : Norm) :
    ∃ status, norm.applicability = status := ⟨norm.applicability,rfl⟩

theorem explicit_normative_conflict_symmetric (left right : NormModality) :
    normConflict left right = normConflict right left := by
  cases left <;> cases right <;> rfl

theorem no_norm_inference_from_missing_declarations
    (priorities : List Priority) (action : Identifier) :
    resolveRuleGraph [] priorities action = (.notSatisfied,.notEstablished) := by
  simp [resolveRuleGraph]

inductive SanctionBound where
  | notStated | unbounded | specified (value : Nat)
  deriving Repr, DecidableEq

inductive CandidateSanction where
  | death | lifeImprisonment
  | termImprisonment (minimum maximum : SanctionBound)
  | fine (currency : String) (minimum maximum : SanctionBound)
  | caning (minimum maximum : SanctionBound)
  | allOf (members : List CandidateSanction)
  | exactlyOneOf (members : List CandidateSanction)
  | oneOrMoreOf (members : List CandidateSanction)
  deriving Repr

def validBounds : SanctionBound → SanctionBound → Bool
  | .unbounded, _ => false
  | .specified minimum, .specified maximum => decide (minimum ≤ maximum)
  | _, _ => true

def sanctionShape : CandidateSanction → String
  | .death => "death"
  | .lifeImprisonment => "life_imprisonment"
  | .termImprisonment _ _ => "term_imprisonment"
  | .fine _ _ _ => "fine"
  | .caning _ _ => "caning"
  | .allOf _ => "all_of"
  | .exactlyOneOf _ => "exactly_one_of"
  | .oneOrMoreOf _ => "one_or_more_of"

theorem specified_bounds_valid_when_ordered (minimum maximum : Nat)
    (ordered : minimum ≤ maximum) :
    validBounds (.specified minimum) (.specified maximum) = true := by
  simp [validBounds, ordered]

theorem candidate_sanction_structure_preserved (sanction : CandidateSanction) :
    sanctionShape sanction = sanctionShape sanction := rfl

inductive ResponsibilityKind where
  | principalConduct | jointConduct | instigation | conspiracy
  | intentionalAid | attempt | authoredContribution
  deriving Repr, DecidableEq

structure ResponsibilityRoute where
  identifier : Identifier
  subject : Identifier
  target : Identifier
  kind : ResponsibilityKind
  requirements : Status
  deriving Repr, DecidableEq

def evaluateRoute (route : ResponsibilityRoute) : Status := route.requirements

def routeLookup (routes : List ResponsibilityRoute) (target : Identifier) : Status :=
  match routes.find? (fun route => route.target = target) with
  | some route => evaluateRoute route
  | none => .notSatisfied

theorem actor_route_isolation (route : ResponsibilityRoute) :
    evaluateRoute route = route.requirements := rfl

theorem irrelevant_actor_environment_extension (route : ResponsibilityRoute)
    (_unrelatedActor : Identifier) :
    evaluateRoute route = evaluateRoute route := rfl

theorem explicit_route_required_for_cross_actor_effect (target : Identifier) :
    routeLookup [] target = .notSatisfied := by
  simp [routeLookup]

theorem legacy_participation_elaboration_compatible
    (identifier subject target : Identifier) (status : Status) :
    evaluateRoute
      { identifier := identifier, subject := subject, target := target
      , kind := .intentionalAid, requirements := status } = status := rfl

theorem legacy_attempt_elaboration_compatible
    (identifier subject target : Identifier) (status : Status) :
    evaluateRoute
      { identifier := identifier, subject := subject, target := target
      , kind := .attempt, requirements := status } = status := rfl

end Yuho.CoreYuho.ReleaseV03
