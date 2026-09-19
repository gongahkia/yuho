/- Generated input-only Core Yuho v0.3 vectors; no expected results. -/
import Yuho.CoreYuho.ReleaseV03Conformance

namespace Yuho.CoreYuho.ReleaseV03.Conformance

open Yuho.CoreYuho
open Yuho.CoreYuho.TypedFinite
open Yuho.CoreYuho.ReleaseV03

def rule (identifier : String) (polarity : Polarity) (status : Status) : RuleResult :=
  { identifier := identifier, proposition := "p:target", polarity := polarity, status := status }

def vectors : List Vector := [
  .normApplicability "norm-satisfied" .satisfied,
  .normApplicability "norm-not-satisfied" .notSatisfied,
  .normApplicability "norm-unresolved" .unresolved,
  .normConflictVector "conflict-required-required" .required .required,
  .normConflictVector "conflict-required-prohibited" .required .prohibited,
  .normConflictVector "conflict-required-permitted" .required .permitted,
  .normConflictVector "conflict-prohibited-required" .prohibited .required,
  .normConflictVector "conflict-prohibited-prohibited" .prohibited .prohibited,
  .normConflictVector "conflict-prohibited-permitted" .prohibited .permitted,
  .normConflictVector "conflict-permitted-required" .permitted .required,
  .normConflictVector "conflict-permitted-prohibited" .permitted .prohibited,
  .normConflictVector "conflict-permitted-permitted" .permitted .permitted,
  .sanctionBounds "bounds-unspecified" .notStated .unbounded,
  .sanctionBounds "bounds-invalid-minimum" .unbounded (.specified 10),
  .sanctionBounds "bounds-ordered" (.specified 2) (.specified 5),
  .sanctionBounds "bounds-reversed" (.specified 5) (.specified 2),
  .sanctionBounds "bounds-open-maximum" (.specified 2) .unbounded,
  .sanctionBounds "bounds-stated-maximum" .notStated (.specified 5),
  .sanctionShapeVector "shape-death" .death,
  .sanctionShapeVector "shape-life" .lifeImprisonment,
  .sanctionShapeVector "shape-imprisonment" (.termImprisonment .notStated (.specified 5)),
  .sanctionShapeVector "shape-fine" (.fine "SGD" .notStated (.specified 100)),
  .sanctionShapeVector "shape-caning" (.caning (.specified 3) (.specified 6)),
  .sanctionShapeVector "shape-all" (.allOf [.death,.lifeImprisonment]),
  .sanctionShapeVector "shape-exactly-one" (.exactlyOneOf [.death,.lifeImprisonment]),
  .sanctionShapeVector "shape-one-or-more" (.oneOrMoreOf [.death,.lifeImprisonment]),
  .responsibilityRoute "route-satisfied" .satisfied,
  .responsibilityRoute "route-not-satisfied" .notSatisfied,
  .responsibilityRoute "route-unresolved" .unresolved,
  .missingRoute "route-missing",
  .priority "norm-priority-defeat" (rule "r:high" .defeat .satisfied)
    (rule "r:low" .establish .satisfied) true,
  .priority "norm-priority-unresolved" (rule "r:high" .defeat .unresolved)
    (rule "r:low" .establish .satisfied) true,
  .priority "norm-priority-conflict" (rule "r:left" .defeat .satisfied)
    (rule "r:right" .establish .satisfied) false
]

end Yuho.CoreYuho.ReleaseV03.Conformance
