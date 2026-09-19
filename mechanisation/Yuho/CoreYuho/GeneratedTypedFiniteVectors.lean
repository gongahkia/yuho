/- Generated input-only Core Yuho v0.2 vectors; no expected results. -/
import Yuho.CoreYuho.TypedFiniteConformance

namespace Yuho.CoreYuho.TypedFinite.Conformance

set_option maxHeartbeats 4000000

def vectorChunk0 : List Vector := [
  .negation "negation-satisfied" .satisfied,
  .negation "negation-not_satisfied" .notSatisfied,
  .negation "negation-unresolved" .unresolved,
  .quantifier "forall-0-empty" .forall [],
  .quantifier "exists-0-empty" .exists [],
  .cardinality "at-least-0-0-empty" .atLeast 0 [],
  .cardinality "at-least-1-0-empty" .atLeast 1 [],
  .cardinality "at-least-2-0-empty" .atLeast 2 [],
  .cardinality "at-least-3-0-empty" .atLeast 3 [],
  .cardinality "at-least-4-0-empty" .atLeast 4 [],
  .cardinality "at-least-5-0-empty" .atLeast 5 [],
  .cardinality "at-most-0-0-empty" .atMost 0 [],
  .cardinality "at-most-1-0-empty" .atMost 1 [],
  .cardinality "at-most-2-0-empty" .atMost 2 [],
  .cardinality "at-most-3-0-empty" .atMost 3 [],
  .cardinality "at-most-4-0-empty" .atMost 4 []
]

def vectorChunk1 : List Vector := [
  .cardinality "at-most-5-0-empty" .atMost 5 [],
  .cardinality "exactly-0-0-empty" .exactly 0 [],
  .cardinality "exactly-1-0-empty" .exactly 1 [],
  .cardinality "exactly-2-0-empty" .exactly 2 [],
  .cardinality "exactly-3-0-empty" .exactly 3 [],
  .cardinality "exactly-4-0-empty" .exactly 4 [],
  .cardinality "exactly-5-0-empty" .exactly 5 [],
  .quantifier "forall-1-satisfied" .forall [.satisfied],
  .quantifier "exists-1-satisfied" .exists [.satisfied],
  .cardinality "at-least-0-1-satisfied" .atLeast 0 [.satisfied],
  .cardinality "at-least-1-1-satisfied" .atLeast 1 [.satisfied],
  .cardinality "at-least-2-1-satisfied" .atLeast 2 [.satisfied],
  .cardinality "at-least-3-1-satisfied" .atLeast 3 [.satisfied],
  .cardinality "at-least-4-1-satisfied" .atLeast 4 [.satisfied],
  .cardinality "at-least-5-1-satisfied" .atLeast 5 [.satisfied],
  .cardinality "at-most-0-1-satisfied" .atMost 0 [.satisfied]
]

def vectorChunk2 : List Vector := [
  .cardinality "at-most-1-1-satisfied" .atMost 1 [.satisfied],
  .cardinality "at-most-2-1-satisfied" .atMost 2 [.satisfied],
  .cardinality "at-most-3-1-satisfied" .atMost 3 [.satisfied],
  .cardinality "at-most-4-1-satisfied" .atMost 4 [.satisfied],
  .cardinality "at-most-5-1-satisfied" .atMost 5 [.satisfied],
  .cardinality "exactly-0-1-satisfied" .exactly 0 [.satisfied],
  .cardinality "exactly-1-1-satisfied" .exactly 1 [.satisfied],
  .cardinality "exactly-2-1-satisfied" .exactly 2 [.satisfied],
  .cardinality "exactly-3-1-satisfied" .exactly 3 [.satisfied],
  .cardinality "exactly-4-1-satisfied" .exactly 4 [.satisfied],
  .cardinality "exactly-5-1-satisfied" .exactly 5 [.satisfied],
  .quantifier "forall-1-not_satisfied" .forall [.notSatisfied],
  .quantifier "exists-1-not_satisfied" .exists [.notSatisfied],
  .cardinality "at-least-0-1-not_satisfied" .atLeast 0 [.notSatisfied],
  .cardinality "at-least-1-1-not_satisfied" .atLeast 1 [.notSatisfied],
  .cardinality "at-least-2-1-not_satisfied" .atLeast 2 [.notSatisfied]
]

def vectorChunk3 : List Vector := [
  .cardinality "at-least-3-1-not_satisfied" .atLeast 3 [.notSatisfied],
  .cardinality "at-least-4-1-not_satisfied" .atLeast 4 [.notSatisfied],
  .cardinality "at-least-5-1-not_satisfied" .atLeast 5 [.notSatisfied],
  .cardinality "at-most-0-1-not_satisfied" .atMost 0 [.notSatisfied],
  .cardinality "at-most-1-1-not_satisfied" .atMost 1 [.notSatisfied],
  .cardinality "at-most-2-1-not_satisfied" .atMost 2 [.notSatisfied],
  .cardinality "at-most-3-1-not_satisfied" .atMost 3 [.notSatisfied],
  .cardinality "at-most-4-1-not_satisfied" .atMost 4 [.notSatisfied],
  .cardinality "at-most-5-1-not_satisfied" .atMost 5 [.notSatisfied],
  .cardinality "exactly-0-1-not_satisfied" .exactly 0 [.notSatisfied],
  .cardinality "exactly-1-1-not_satisfied" .exactly 1 [.notSatisfied],
  .cardinality "exactly-2-1-not_satisfied" .exactly 2 [.notSatisfied],
  .cardinality "exactly-3-1-not_satisfied" .exactly 3 [.notSatisfied],
  .cardinality "exactly-4-1-not_satisfied" .exactly 4 [.notSatisfied],
  .cardinality "exactly-5-1-not_satisfied" .exactly 5 [.notSatisfied],
  .quantifier "forall-1-unresolved" .forall [.unresolved]
]

def vectorChunk4 : List Vector := [
  .quantifier "exists-1-unresolved" .exists [.unresolved],
  .cardinality "at-least-0-1-unresolved" .atLeast 0 [.unresolved],
  .cardinality "at-least-1-1-unresolved" .atLeast 1 [.unresolved],
  .cardinality "at-least-2-1-unresolved" .atLeast 2 [.unresolved],
  .cardinality "at-least-3-1-unresolved" .atLeast 3 [.unresolved],
  .cardinality "at-least-4-1-unresolved" .atLeast 4 [.unresolved],
  .cardinality "at-least-5-1-unresolved" .atLeast 5 [.unresolved],
  .cardinality "at-most-0-1-unresolved" .atMost 0 [.unresolved],
  .cardinality "at-most-1-1-unresolved" .atMost 1 [.unresolved],
  .cardinality "at-most-2-1-unresolved" .atMost 2 [.unresolved],
  .cardinality "at-most-3-1-unresolved" .atMost 3 [.unresolved],
  .cardinality "at-most-4-1-unresolved" .atMost 4 [.unresolved],
  .cardinality "at-most-5-1-unresolved" .atMost 5 [.unresolved],
  .cardinality "exactly-0-1-unresolved" .exactly 0 [.unresolved],
  .cardinality "exactly-1-1-unresolved" .exactly 1 [.unresolved],
  .cardinality "exactly-2-1-unresolved" .exactly 2 [.unresolved]
]

def vectorChunk5 : List Vector := [
  .cardinality "exactly-3-1-unresolved" .exactly 3 [.unresolved],
  .cardinality "exactly-4-1-unresolved" .exactly 4 [.unresolved],
  .cardinality "exactly-5-1-unresolved" .exactly 5 [.unresolved],
  .quantifier "forall-2-satisfied-satisfied" .forall [.satisfied, .satisfied],
  .quantifier "exists-2-satisfied-satisfied" .exists [.satisfied, .satisfied],
  .cardinality "at-least-0-2-satisfied-satisfied" .atLeast 0 [.satisfied, .satisfied],
  .cardinality "at-least-1-2-satisfied-satisfied" .atLeast 1 [.satisfied, .satisfied],
  .cardinality "at-least-2-2-satisfied-satisfied" .atLeast 2 [.satisfied, .satisfied],
  .cardinality "at-least-3-2-satisfied-satisfied" .atLeast 3 [.satisfied, .satisfied],
  .cardinality "at-least-4-2-satisfied-satisfied" .atLeast 4 [.satisfied, .satisfied],
  .cardinality "at-least-5-2-satisfied-satisfied" .atLeast 5 [.satisfied, .satisfied],
  .cardinality "at-most-0-2-satisfied-satisfied" .atMost 0 [.satisfied, .satisfied],
  .cardinality "at-most-1-2-satisfied-satisfied" .atMost 1 [.satisfied, .satisfied],
  .cardinality "at-most-2-2-satisfied-satisfied" .atMost 2 [.satisfied, .satisfied],
  .cardinality "at-most-3-2-satisfied-satisfied" .atMost 3 [.satisfied, .satisfied],
  .cardinality "at-most-4-2-satisfied-satisfied" .atMost 4 [.satisfied, .satisfied]
]

def vectorChunk6 : List Vector := [
  .cardinality "at-most-5-2-satisfied-satisfied" .atMost 5 [.satisfied, .satisfied],
  .cardinality "exactly-0-2-satisfied-satisfied" .exactly 0 [.satisfied, .satisfied],
  .cardinality "exactly-1-2-satisfied-satisfied" .exactly 1 [.satisfied, .satisfied],
  .cardinality "exactly-2-2-satisfied-satisfied" .exactly 2 [.satisfied, .satisfied],
  .cardinality "exactly-3-2-satisfied-satisfied" .exactly 3 [.satisfied, .satisfied],
  .cardinality "exactly-4-2-satisfied-satisfied" .exactly 4 [.satisfied, .satisfied],
  .cardinality "exactly-5-2-satisfied-satisfied" .exactly 5 [.satisfied, .satisfied],
  .quantifier "forall-2-satisfied-not_satisfied" .forall [.satisfied, .notSatisfied],
  .quantifier "exists-2-satisfied-not_satisfied" .exists [.satisfied, .notSatisfied],
  .cardinality "at-least-0-2-satisfied-not_satisfied" .atLeast 0 [.satisfied, .notSatisfied],
  .cardinality "at-least-1-2-satisfied-not_satisfied" .atLeast 1 [.satisfied, .notSatisfied],
  .cardinality "at-least-2-2-satisfied-not_satisfied" .atLeast 2 [.satisfied, .notSatisfied],
  .cardinality "at-least-3-2-satisfied-not_satisfied" .atLeast 3 [.satisfied, .notSatisfied],
  .cardinality "at-least-4-2-satisfied-not_satisfied" .atLeast 4 [.satisfied, .notSatisfied],
  .cardinality "at-least-5-2-satisfied-not_satisfied" .atLeast 5 [.satisfied, .notSatisfied],
  .cardinality "at-most-0-2-satisfied-not_satisfied" .atMost 0 [.satisfied, .notSatisfied]
]

def vectorChunk7 : List Vector := [
  .cardinality "at-most-1-2-satisfied-not_satisfied" .atMost 1 [.satisfied, .notSatisfied],
  .cardinality "at-most-2-2-satisfied-not_satisfied" .atMost 2 [.satisfied, .notSatisfied],
  .cardinality "at-most-3-2-satisfied-not_satisfied" .atMost 3 [.satisfied, .notSatisfied],
  .cardinality "at-most-4-2-satisfied-not_satisfied" .atMost 4 [.satisfied, .notSatisfied],
  .cardinality "at-most-5-2-satisfied-not_satisfied" .atMost 5 [.satisfied, .notSatisfied],
  .cardinality "exactly-0-2-satisfied-not_satisfied" .exactly 0 [.satisfied, .notSatisfied],
  .cardinality "exactly-1-2-satisfied-not_satisfied" .exactly 1 [.satisfied, .notSatisfied],
  .cardinality "exactly-2-2-satisfied-not_satisfied" .exactly 2 [.satisfied, .notSatisfied],
  .cardinality "exactly-3-2-satisfied-not_satisfied" .exactly 3 [.satisfied, .notSatisfied],
  .cardinality "exactly-4-2-satisfied-not_satisfied" .exactly 4 [.satisfied, .notSatisfied],
  .cardinality "exactly-5-2-satisfied-not_satisfied" .exactly 5 [.satisfied, .notSatisfied],
  .quantifier "forall-2-satisfied-unresolved" .forall [.satisfied, .unresolved],
  .quantifier "exists-2-satisfied-unresolved" .exists [.satisfied, .unresolved],
  .cardinality "at-least-0-2-satisfied-unresolved" .atLeast 0 [.satisfied, .unresolved],
  .cardinality "at-least-1-2-satisfied-unresolved" .atLeast 1 [.satisfied, .unresolved],
  .cardinality "at-least-2-2-satisfied-unresolved" .atLeast 2 [.satisfied, .unresolved]
]

def vectorChunk8 : List Vector := [
  .cardinality "at-least-3-2-satisfied-unresolved" .atLeast 3 [.satisfied, .unresolved],
  .cardinality "at-least-4-2-satisfied-unresolved" .atLeast 4 [.satisfied, .unresolved],
  .cardinality "at-least-5-2-satisfied-unresolved" .atLeast 5 [.satisfied, .unresolved],
  .cardinality "at-most-0-2-satisfied-unresolved" .atMost 0 [.satisfied, .unresolved],
  .cardinality "at-most-1-2-satisfied-unresolved" .atMost 1 [.satisfied, .unresolved],
  .cardinality "at-most-2-2-satisfied-unresolved" .atMost 2 [.satisfied, .unresolved],
  .cardinality "at-most-3-2-satisfied-unresolved" .atMost 3 [.satisfied, .unresolved],
  .cardinality "at-most-4-2-satisfied-unresolved" .atMost 4 [.satisfied, .unresolved],
  .cardinality "at-most-5-2-satisfied-unresolved" .atMost 5 [.satisfied, .unresolved],
  .cardinality "exactly-0-2-satisfied-unresolved" .exactly 0 [.satisfied, .unresolved],
  .cardinality "exactly-1-2-satisfied-unresolved" .exactly 1 [.satisfied, .unresolved],
  .cardinality "exactly-2-2-satisfied-unresolved" .exactly 2 [.satisfied, .unresolved],
  .cardinality "exactly-3-2-satisfied-unresolved" .exactly 3 [.satisfied, .unresolved],
  .cardinality "exactly-4-2-satisfied-unresolved" .exactly 4 [.satisfied, .unresolved],
  .cardinality "exactly-5-2-satisfied-unresolved" .exactly 5 [.satisfied, .unresolved],
  .quantifier "forall-2-not_satisfied-satisfied" .forall [.notSatisfied, .satisfied]
]

def vectorChunk9 : List Vector := [
  .quantifier "exists-2-not_satisfied-satisfied" .exists [.notSatisfied, .satisfied],
  .cardinality "at-least-0-2-not_satisfied-satisfied" .atLeast 0 [.notSatisfied, .satisfied],
  .cardinality "at-least-1-2-not_satisfied-satisfied" .atLeast 1 [.notSatisfied, .satisfied],
  .cardinality "at-least-2-2-not_satisfied-satisfied" .atLeast 2 [.notSatisfied, .satisfied],
  .cardinality "at-least-3-2-not_satisfied-satisfied" .atLeast 3 [.notSatisfied, .satisfied],
  .cardinality "at-least-4-2-not_satisfied-satisfied" .atLeast 4 [.notSatisfied, .satisfied],
  .cardinality "at-least-5-2-not_satisfied-satisfied" .atLeast 5 [.notSatisfied, .satisfied],
  .cardinality "at-most-0-2-not_satisfied-satisfied" .atMost 0 [.notSatisfied, .satisfied],
  .cardinality "at-most-1-2-not_satisfied-satisfied" .atMost 1 [.notSatisfied, .satisfied],
  .cardinality "at-most-2-2-not_satisfied-satisfied" .atMost 2 [.notSatisfied, .satisfied],
  .cardinality "at-most-3-2-not_satisfied-satisfied" .atMost 3 [.notSatisfied, .satisfied],
  .cardinality "at-most-4-2-not_satisfied-satisfied" .atMost 4 [.notSatisfied, .satisfied],
  .cardinality "at-most-5-2-not_satisfied-satisfied" .atMost 5 [.notSatisfied, .satisfied],
  .cardinality "exactly-0-2-not_satisfied-satisfied" .exactly 0 [.notSatisfied, .satisfied],
  .cardinality "exactly-1-2-not_satisfied-satisfied" .exactly 1 [.notSatisfied, .satisfied],
  .cardinality "exactly-2-2-not_satisfied-satisfied" .exactly 2 [.notSatisfied, .satisfied]
]

def vectorChunk10 : List Vector := [
  .cardinality "exactly-3-2-not_satisfied-satisfied" .exactly 3 [.notSatisfied, .satisfied],
  .cardinality "exactly-4-2-not_satisfied-satisfied" .exactly 4 [.notSatisfied, .satisfied],
  .cardinality "exactly-5-2-not_satisfied-satisfied" .exactly 5 [.notSatisfied, .satisfied],
  .quantifier "forall-2-not_satisfied-not_satisfied" .forall [.notSatisfied, .notSatisfied],
  .quantifier "exists-2-not_satisfied-not_satisfied" .exists [.notSatisfied, .notSatisfied],
  .cardinality "at-least-0-2-not_satisfied-not_satisfied" .atLeast 0 [.notSatisfied, .notSatisfied],
  .cardinality "at-least-1-2-not_satisfied-not_satisfied" .atLeast 1 [.notSatisfied, .notSatisfied],
  .cardinality "at-least-2-2-not_satisfied-not_satisfied" .atLeast 2 [.notSatisfied, .notSatisfied],
  .cardinality "at-least-3-2-not_satisfied-not_satisfied" .atLeast 3 [.notSatisfied, .notSatisfied],
  .cardinality "at-least-4-2-not_satisfied-not_satisfied" .atLeast 4 [.notSatisfied, .notSatisfied],
  .cardinality "at-least-5-2-not_satisfied-not_satisfied" .atLeast 5 [.notSatisfied, .notSatisfied],
  .cardinality "at-most-0-2-not_satisfied-not_satisfied" .atMost 0 [.notSatisfied, .notSatisfied],
  .cardinality "at-most-1-2-not_satisfied-not_satisfied" .atMost 1 [.notSatisfied, .notSatisfied],
  .cardinality "at-most-2-2-not_satisfied-not_satisfied" .atMost 2 [.notSatisfied, .notSatisfied],
  .cardinality "at-most-3-2-not_satisfied-not_satisfied" .atMost 3 [.notSatisfied, .notSatisfied],
  .cardinality "at-most-4-2-not_satisfied-not_satisfied" .atMost 4 [.notSatisfied, .notSatisfied]
]

def vectorChunk11 : List Vector := [
  .cardinality "at-most-5-2-not_satisfied-not_satisfied" .atMost 5 [.notSatisfied, .notSatisfied],
  .cardinality "exactly-0-2-not_satisfied-not_satisfied" .exactly 0 [.notSatisfied, .notSatisfied],
  .cardinality "exactly-1-2-not_satisfied-not_satisfied" .exactly 1 [.notSatisfied, .notSatisfied],
  .cardinality "exactly-2-2-not_satisfied-not_satisfied" .exactly 2 [.notSatisfied, .notSatisfied],
  .cardinality "exactly-3-2-not_satisfied-not_satisfied" .exactly 3 [.notSatisfied, .notSatisfied],
  .cardinality "exactly-4-2-not_satisfied-not_satisfied" .exactly 4 [.notSatisfied, .notSatisfied],
  .cardinality "exactly-5-2-not_satisfied-not_satisfied" .exactly 5 [.notSatisfied, .notSatisfied],
  .quantifier "forall-2-not_satisfied-unresolved" .forall [.notSatisfied, .unresolved],
  .quantifier "exists-2-not_satisfied-unresolved" .exists [.notSatisfied, .unresolved],
  .cardinality "at-least-0-2-not_satisfied-unresolved" .atLeast 0 [.notSatisfied, .unresolved],
  .cardinality "at-least-1-2-not_satisfied-unresolved" .atLeast 1 [.notSatisfied, .unresolved],
  .cardinality "at-least-2-2-not_satisfied-unresolved" .atLeast 2 [.notSatisfied, .unresolved],
  .cardinality "at-least-3-2-not_satisfied-unresolved" .atLeast 3 [.notSatisfied, .unresolved],
  .cardinality "at-least-4-2-not_satisfied-unresolved" .atLeast 4 [.notSatisfied, .unresolved],
  .cardinality "at-least-5-2-not_satisfied-unresolved" .atLeast 5 [.notSatisfied, .unresolved],
  .cardinality "at-most-0-2-not_satisfied-unresolved" .atMost 0 [.notSatisfied, .unresolved]
]

def vectorChunk12 : List Vector := [
  .cardinality "at-most-1-2-not_satisfied-unresolved" .atMost 1 [.notSatisfied, .unresolved],
  .cardinality "at-most-2-2-not_satisfied-unresolved" .atMost 2 [.notSatisfied, .unresolved],
  .cardinality "at-most-3-2-not_satisfied-unresolved" .atMost 3 [.notSatisfied, .unresolved],
  .cardinality "at-most-4-2-not_satisfied-unresolved" .atMost 4 [.notSatisfied, .unresolved],
  .cardinality "at-most-5-2-not_satisfied-unresolved" .atMost 5 [.notSatisfied, .unresolved],
  .cardinality "exactly-0-2-not_satisfied-unresolved" .exactly 0 [.notSatisfied, .unresolved],
  .cardinality "exactly-1-2-not_satisfied-unresolved" .exactly 1 [.notSatisfied, .unresolved],
  .cardinality "exactly-2-2-not_satisfied-unresolved" .exactly 2 [.notSatisfied, .unresolved],
  .cardinality "exactly-3-2-not_satisfied-unresolved" .exactly 3 [.notSatisfied, .unresolved],
  .cardinality "exactly-4-2-not_satisfied-unresolved" .exactly 4 [.notSatisfied, .unresolved],
  .cardinality "exactly-5-2-not_satisfied-unresolved" .exactly 5 [.notSatisfied, .unresolved],
  .quantifier "forall-2-unresolved-satisfied" .forall [.unresolved, .satisfied],
  .quantifier "exists-2-unresolved-satisfied" .exists [.unresolved, .satisfied],
  .cardinality "at-least-0-2-unresolved-satisfied" .atLeast 0 [.unresolved, .satisfied],
  .cardinality "at-least-1-2-unresolved-satisfied" .atLeast 1 [.unresolved, .satisfied],
  .cardinality "at-least-2-2-unresolved-satisfied" .atLeast 2 [.unresolved, .satisfied]
]

def vectorChunk13 : List Vector := [
  .cardinality "at-least-3-2-unresolved-satisfied" .atLeast 3 [.unresolved, .satisfied],
  .cardinality "at-least-4-2-unresolved-satisfied" .atLeast 4 [.unresolved, .satisfied],
  .cardinality "at-least-5-2-unresolved-satisfied" .atLeast 5 [.unresolved, .satisfied],
  .cardinality "at-most-0-2-unresolved-satisfied" .atMost 0 [.unresolved, .satisfied],
  .cardinality "at-most-1-2-unresolved-satisfied" .atMost 1 [.unresolved, .satisfied],
  .cardinality "at-most-2-2-unresolved-satisfied" .atMost 2 [.unresolved, .satisfied],
  .cardinality "at-most-3-2-unresolved-satisfied" .atMost 3 [.unresolved, .satisfied],
  .cardinality "at-most-4-2-unresolved-satisfied" .atMost 4 [.unresolved, .satisfied],
  .cardinality "at-most-5-2-unresolved-satisfied" .atMost 5 [.unresolved, .satisfied],
  .cardinality "exactly-0-2-unresolved-satisfied" .exactly 0 [.unresolved, .satisfied],
  .cardinality "exactly-1-2-unresolved-satisfied" .exactly 1 [.unresolved, .satisfied],
  .cardinality "exactly-2-2-unresolved-satisfied" .exactly 2 [.unresolved, .satisfied],
  .cardinality "exactly-3-2-unresolved-satisfied" .exactly 3 [.unresolved, .satisfied],
  .cardinality "exactly-4-2-unresolved-satisfied" .exactly 4 [.unresolved, .satisfied],
  .cardinality "exactly-5-2-unresolved-satisfied" .exactly 5 [.unresolved, .satisfied],
  .quantifier "forall-2-unresolved-not_satisfied" .forall [.unresolved, .notSatisfied]
]

def vectorChunk14 : List Vector := [
  .quantifier "exists-2-unresolved-not_satisfied" .exists [.unresolved, .notSatisfied],
  .cardinality "at-least-0-2-unresolved-not_satisfied" .atLeast 0 [.unresolved, .notSatisfied],
  .cardinality "at-least-1-2-unresolved-not_satisfied" .atLeast 1 [.unresolved, .notSatisfied],
  .cardinality "at-least-2-2-unresolved-not_satisfied" .atLeast 2 [.unresolved, .notSatisfied],
  .cardinality "at-least-3-2-unresolved-not_satisfied" .atLeast 3 [.unresolved, .notSatisfied],
  .cardinality "at-least-4-2-unresolved-not_satisfied" .atLeast 4 [.unresolved, .notSatisfied],
  .cardinality "at-least-5-2-unresolved-not_satisfied" .atLeast 5 [.unresolved, .notSatisfied],
  .cardinality "at-most-0-2-unresolved-not_satisfied" .atMost 0 [.unresolved, .notSatisfied],
  .cardinality "at-most-1-2-unresolved-not_satisfied" .atMost 1 [.unresolved, .notSatisfied],
  .cardinality "at-most-2-2-unresolved-not_satisfied" .atMost 2 [.unresolved, .notSatisfied],
  .cardinality "at-most-3-2-unresolved-not_satisfied" .atMost 3 [.unresolved, .notSatisfied],
  .cardinality "at-most-4-2-unresolved-not_satisfied" .atMost 4 [.unresolved, .notSatisfied],
  .cardinality "at-most-5-2-unresolved-not_satisfied" .atMost 5 [.unresolved, .notSatisfied],
  .cardinality "exactly-0-2-unresolved-not_satisfied" .exactly 0 [.unresolved, .notSatisfied],
  .cardinality "exactly-1-2-unresolved-not_satisfied" .exactly 1 [.unresolved, .notSatisfied],
  .cardinality "exactly-2-2-unresolved-not_satisfied" .exactly 2 [.unresolved, .notSatisfied]
]

def vectorChunk15 : List Vector := [
  .cardinality "exactly-3-2-unresolved-not_satisfied" .exactly 3 [.unresolved, .notSatisfied],
  .cardinality "exactly-4-2-unresolved-not_satisfied" .exactly 4 [.unresolved, .notSatisfied],
  .cardinality "exactly-5-2-unresolved-not_satisfied" .exactly 5 [.unresolved, .notSatisfied],
  .quantifier "forall-2-unresolved-unresolved" .forall [.unresolved, .unresolved],
  .quantifier "exists-2-unresolved-unresolved" .exists [.unresolved, .unresolved],
  .cardinality "at-least-0-2-unresolved-unresolved" .atLeast 0 [.unresolved, .unresolved],
  .cardinality "at-least-1-2-unresolved-unresolved" .atLeast 1 [.unresolved, .unresolved],
  .cardinality "at-least-2-2-unresolved-unresolved" .atLeast 2 [.unresolved, .unresolved],
  .cardinality "at-least-3-2-unresolved-unresolved" .atLeast 3 [.unresolved, .unresolved],
  .cardinality "at-least-4-2-unresolved-unresolved" .atLeast 4 [.unresolved, .unresolved],
  .cardinality "at-least-5-2-unresolved-unresolved" .atLeast 5 [.unresolved, .unresolved],
  .cardinality "at-most-0-2-unresolved-unresolved" .atMost 0 [.unresolved, .unresolved],
  .cardinality "at-most-1-2-unresolved-unresolved" .atMost 1 [.unresolved, .unresolved],
  .cardinality "at-most-2-2-unresolved-unresolved" .atMost 2 [.unresolved, .unresolved],
  .cardinality "at-most-3-2-unresolved-unresolved" .atMost 3 [.unresolved, .unresolved],
  .cardinality "at-most-4-2-unresolved-unresolved" .atMost 4 [.unresolved, .unresolved]
]

def vectorChunk16 : List Vector := [
  .cardinality "at-most-5-2-unresolved-unresolved" .atMost 5 [.unresolved, .unresolved],
  .cardinality "exactly-0-2-unresolved-unresolved" .exactly 0 [.unresolved, .unresolved],
  .cardinality "exactly-1-2-unresolved-unresolved" .exactly 1 [.unresolved, .unresolved],
  .cardinality "exactly-2-2-unresolved-unresolved" .exactly 2 [.unresolved, .unresolved],
  .cardinality "exactly-3-2-unresolved-unresolved" .exactly 3 [.unresolved, .unresolved],
  .cardinality "exactly-4-2-unresolved-unresolved" .exactly 4 [.unresolved, .unresolved],
  .cardinality "exactly-5-2-unresolved-unresolved" .exactly 5 [.unresolved, .unresolved],
  .quantifier "forall-3-satisfied-satisfied-satisfied" .forall [.satisfied, .satisfied, .satisfied],
  .quantifier "exists-3-satisfied-satisfied-satisfied" .exists [.satisfied, .satisfied, .satisfied],
  .cardinality "at-least-0-3-satisfied-satisfied-satisfied" .atLeast 0 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-least-1-3-satisfied-satisfied-satisfied" .atLeast 1 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-least-2-3-satisfied-satisfied-satisfied" .atLeast 2 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-least-3-3-satisfied-satisfied-satisfied" .atLeast 3 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-least-4-3-satisfied-satisfied-satisfied" .atLeast 4 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-least-5-3-satisfied-satisfied-satisfied" .atLeast 5 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-most-0-3-satisfied-satisfied-satisfied" .atMost 0 [.satisfied, .satisfied, .satisfied]
]

def vectorChunk17 : List Vector := [
  .cardinality "at-most-1-3-satisfied-satisfied-satisfied" .atMost 1 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-most-2-3-satisfied-satisfied-satisfied" .atMost 2 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-most-3-3-satisfied-satisfied-satisfied" .atMost 3 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-most-4-3-satisfied-satisfied-satisfied" .atMost 4 [.satisfied, .satisfied, .satisfied],
  .cardinality "at-most-5-3-satisfied-satisfied-satisfied" .atMost 5 [.satisfied, .satisfied, .satisfied],
  .cardinality "exactly-0-3-satisfied-satisfied-satisfied" .exactly 0 [.satisfied, .satisfied, .satisfied],
  .cardinality "exactly-1-3-satisfied-satisfied-satisfied" .exactly 1 [.satisfied, .satisfied, .satisfied],
  .cardinality "exactly-2-3-satisfied-satisfied-satisfied" .exactly 2 [.satisfied, .satisfied, .satisfied],
  .cardinality "exactly-3-3-satisfied-satisfied-satisfied" .exactly 3 [.satisfied, .satisfied, .satisfied],
  .cardinality "exactly-4-3-satisfied-satisfied-satisfied" .exactly 4 [.satisfied, .satisfied, .satisfied],
  .cardinality "exactly-5-3-satisfied-satisfied-satisfied" .exactly 5 [.satisfied, .satisfied, .satisfied],
  .quantifier "forall-3-satisfied-satisfied-not_satisfied" .forall [.satisfied, .satisfied, .notSatisfied],
  .quantifier "exists-3-satisfied-satisfied-not_satisfied" .exists [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-0-3-satisfied-satisfied-not_satisfied" .atLeast 0 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-1-3-satisfied-satisfied-not_satisfied" .atLeast 1 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-2-3-satisfied-satisfied-not_satisfied" .atLeast 2 [.satisfied, .satisfied, .notSatisfied]
]

def vectorChunk18 : List Vector := [
  .cardinality "at-least-3-3-satisfied-satisfied-not_satisfied" .atLeast 3 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-4-3-satisfied-satisfied-not_satisfied" .atLeast 4 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-5-3-satisfied-satisfied-not_satisfied" .atLeast 5 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-0-3-satisfied-satisfied-not_satisfied" .atMost 0 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-1-3-satisfied-satisfied-not_satisfied" .atMost 1 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-2-3-satisfied-satisfied-not_satisfied" .atMost 2 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-3-3-satisfied-satisfied-not_satisfied" .atMost 3 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-4-3-satisfied-satisfied-not_satisfied" .atMost 4 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-5-3-satisfied-satisfied-not_satisfied" .atMost 5 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-0-3-satisfied-satisfied-not_satisfied" .exactly 0 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-1-3-satisfied-satisfied-not_satisfied" .exactly 1 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-2-3-satisfied-satisfied-not_satisfied" .exactly 2 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-3-3-satisfied-satisfied-not_satisfied" .exactly 3 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-4-3-satisfied-satisfied-not_satisfied" .exactly 4 [.satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-5-3-satisfied-satisfied-not_satisfied" .exactly 5 [.satisfied, .satisfied, .notSatisfied],
  .quantifier "forall-3-satisfied-satisfied-unresolved" .forall [.satisfied, .satisfied, .unresolved]
]

def vectorChunk19 : List Vector := [
  .quantifier "exists-3-satisfied-satisfied-unresolved" .exists [.satisfied, .satisfied, .unresolved],
  .cardinality "at-least-0-3-satisfied-satisfied-unresolved" .atLeast 0 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-least-1-3-satisfied-satisfied-unresolved" .atLeast 1 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-least-2-3-satisfied-satisfied-unresolved" .atLeast 2 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-least-3-3-satisfied-satisfied-unresolved" .atLeast 3 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-least-4-3-satisfied-satisfied-unresolved" .atLeast 4 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-least-5-3-satisfied-satisfied-unresolved" .atLeast 5 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-most-0-3-satisfied-satisfied-unresolved" .atMost 0 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-most-1-3-satisfied-satisfied-unresolved" .atMost 1 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-most-2-3-satisfied-satisfied-unresolved" .atMost 2 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-most-3-3-satisfied-satisfied-unresolved" .atMost 3 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-most-4-3-satisfied-satisfied-unresolved" .atMost 4 [.satisfied, .satisfied, .unresolved],
  .cardinality "at-most-5-3-satisfied-satisfied-unresolved" .atMost 5 [.satisfied, .satisfied, .unresolved],
  .cardinality "exactly-0-3-satisfied-satisfied-unresolved" .exactly 0 [.satisfied, .satisfied, .unresolved],
  .cardinality "exactly-1-3-satisfied-satisfied-unresolved" .exactly 1 [.satisfied, .satisfied, .unresolved],
  .cardinality "exactly-2-3-satisfied-satisfied-unresolved" .exactly 2 [.satisfied, .satisfied, .unresolved]
]

def vectorChunk20 : List Vector := [
  .cardinality "exactly-3-3-satisfied-satisfied-unresolved" .exactly 3 [.satisfied, .satisfied, .unresolved],
  .cardinality "exactly-4-3-satisfied-satisfied-unresolved" .exactly 4 [.satisfied, .satisfied, .unresolved],
  .cardinality "exactly-5-3-satisfied-satisfied-unresolved" .exactly 5 [.satisfied, .satisfied, .unresolved],
  .quantifier "forall-3-satisfied-not_satisfied-satisfied" .forall [.satisfied, .notSatisfied, .satisfied],
  .quantifier "exists-3-satisfied-not_satisfied-satisfied" .exists [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-0-3-satisfied-not_satisfied-satisfied" .atLeast 0 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-1-3-satisfied-not_satisfied-satisfied" .atLeast 1 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-2-3-satisfied-not_satisfied-satisfied" .atLeast 2 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-3-3-satisfied-not_satisfied-satisfied" .atLeast 3 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-4-3-satisfied-not_satisfied-satisfied" .atLeast 4 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-5-3-satisfied-not_satisfied-satisfied" .atLeast 5 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-0-3-satisfied-not_satisfied-satisfied" .atMost 0 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-1-3-satisfied-not_satisfied-satisfied" .atMost 1 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-2-3-satisfied-not_satisfied-satisfied" .atMost 2 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-3-3-satisfied-not_satisfied-satisfied" .atMost 3 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-4-3-satisfied-not_satisfied-satisfied" .atMost 4 [.satisfied, .notSatisfied, .satisfied]
]

def vectorChunk21 : List Vector := [
  .cardinality "at-most-5-3-satisfied-not_satisfied-satisfied" .atMost 5 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-0-3-satisfied-not_satisfied-satisfied" .exactly 0 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-1-3-satisfied-not_satisfied-satisfied" .exactly 1 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-2-3-satisfied-not_satisfied-satisfied" .exactly 2 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-3-3-satisfied-not_satisfied-satisfied" .exactly 3 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-4-3-satisfied-not_satisfied-satisfied" .exactly 4 [.satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-5-3-satisfied-not_satisfied-satisfied" .exactly 5 [.satisfied, .notSatisfied, .satisfied],
  .quantifier "forall-3-satisfied-not_satisfied-not_satisfied" .forall [.satisfied, .notSatisfied, .notSatisfied],
  .quantifier "exists-3-satisfied-not_satisfied-not_satisfied" .exists [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-3-satisfied-not_satisfied-not_satisfied" .atLeast 0 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-3-satisfied-not_satisfied-not_satisfied" .atLeast 1 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-3-satisfied-not_satisfied-not_satisfied" .atLeast 2 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-3-3-satisfied-not_satisfied-not_satisfied" .atLeast 3 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-3-satisfied-not_satisfied-not_satisfied" .atLeast 4 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-3-satisfied-not_satisfied-not_satisfied" .atLeast 5 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-3-satisfied-not_satisfied-not_satisfied" .atMost 0 [.satisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk22 : List Vector := [
  .cardinality "at-most-1-3-satisfied-not_satisfied-not_satisfied" .atMost 1 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-3-satisfied-not_satisfied-not_satisfied" .atMost 2 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-3-satisfied-not_satisfied-not_satisfied" .atMost 3 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-3-satisfied-not_satisfied-not_satisfied" .atMost 4 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-5-3-satisfied-not_satisfied-not_satisfied" .atMost 5 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-3-satisfied-not_satisfied-not_satisfied" .exactly 0 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-3-satisfied-not_satisfied-not_satisfied" .exactly 1 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-3-satisfied-not_satisfied-not_satisfied" .exactly 2 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-3-3-satisfied-not_satisfied-not_satisfied" .exactly 3 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-3-satisfied-not_satisfied-not_satisfied" .exactly 4 [.satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-3-satisfied-not_satisfied-not_satisfied" .exactly 5 [.satisfied, .notSatisfied, .notSatisfied],
  .quantifier "forall-3-satisfied-not_satisfied-unresolved" .forall [.satisfied, .notSatisfied, .unresolved],
  .quantifier "exists-3-satisfied-not_satisfied-unresolved" .exists [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-0-3-satisfied-not_satisfied-unresolved" .atLeast 0 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-1-3-satisfied-not_satisfied-unresolved" .atLeast 1 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-2-3-satisfied-not_satisfied-unresolved" .atLeast 2 [.satisfied, .notSatisfied, .unresolved]
]

def vectorChunk23 : List Vector := [
  .cardinality "at-least-3-3-satisfied-not_satisfied-unresolved" .atLeast 3 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-4-3-satisfied-not_satisfied-unresolved" .atLeast 4 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-5-3-satisfied-not_satisfied-unresolved" .atLeast 5 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-0-3-satisfied-not_satisfied-unresolved" .atMost 0 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-1-3-satisfied-not_satisfied-unresolved" .atMost 1 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-2-3-satisfied-not_satisfied-unresolved" .atMost 2 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-3-3-satisfied-not_satisfied-unresolved" .atMost 3 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-4-3-satisfied-not_satisfied-unresolved" .atMost 4 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-5-3-satisfied-not_satisfied-unresolved" .atMost 5 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-0-3-satisfied-not_satisfied-unresolved" .exactly 0 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-1-3-satisfied-not_satisfied-unresolved" .exactly 1 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-2-3-satisfied-not_satisfied-unresolved" .exactly 2 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-3-3-satisfied-not_satisfied-unresolved" .exactly 3 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-4-3-satisfied-not_satisfied-unresolved" .exactly 4 [.satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-5-3-satisfied-not_satisfied-unresolved" .exactly 5 [.satisfied, .notSatisfied, .unresolved],
  .quantifier "forall-3-satisfied-unresolved-satisfied" .forall [.satisfied, .unresolved, .satisfied]
]

def vectorChunk24 : List Vector := [
  .quantifier "exists-3-satisfied-unresolved-satisfied" .exists [.satisfied, .unresolved, .satisfied],
  .cardinality "at-least-0-3-satisfied-unresolved-satisfied" .atLeast 0 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-least-1-3-satisfied-unresolved-satisfied" .atLeast 1 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-least-2-3-satisfied-unresolved-satisfied" .atLeast 2 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-least-3-3-satisfied-unresolved-satisfied" .atLeast 3 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-least-4-3-satisfied-unresolved-satisfied" .atLeast 4 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-least-5-3-satisfied-unresolved-satisfied" .atLeast 5 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-most-0-3-satisfied-unresolved-satisfied" .atMost 0 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-most-1-3-satisfied-unresolved-satisfied" .atMost 1 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-most-2-3-satisfied-unresolved-satisfied" .atMost 2 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-most-3-3-satisfied-unresolved-satisfied" .atMost 3 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-most-4-3-satisfied-unresolved-satisfied" .atMost 4 [.satisfied, .unresolved, .satisfied],
  .cardinality "at-most-5-3-satisfied-unresolved-satisfied" .atMost 5 [.satisfied, .unresolved, .satisfied],
  .cardinality "exactly-0-3-satisfied-unresolved-satisfied" .exactly 0 [.satisfied, .unresolved, .satisfied],
  .cardinality "exactly-1-3-satisfied-unresolved-satisfied" .exactly 1 [.satisfied, .unresolved, .satisfied],
  .cardinality "exactly-2-3-satisfied-unresolved-satisfied" .exactly 2 [.satisfied, .unresolved, .satisfied]
]

def vectorChunk25 : List Vector := [
  .cardinality "exactly-3-3-satisfied-unresolved-satisfied" .exactly 3 [.satisfied, .unresolved, .satisfied],
  .cardinality "exactly-4-3-satisfied-unresolved-satisfied" .exactly 4 [.satisfied, .unresolved, .satisfied],
  .cardinality "exactly-5-3-satisfied-unresolved-satisfied" .exactly 5 [.satisfied, .unresolved, .satisfied],
  .quantifier "forall-3-satisfied-unresolved-not_satisfied" .forall [.satisfied, .unresolved, .notSatisfied],
  .quantifier "exists-3-satisfied-unresolved-not_satisfied" .exists [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-0-3-satisfied-unresolved-not_satisfied" .atLeast 0 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-1-3-satisfied-unresolved-not_satisfied" .atLeast 1 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-2-3-satisfied-unresolved-not_satisfied" .atLeast 2 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-3-3-satisfied-unresolved-not_satisfied" .atLeast 3 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-4-3-satisfied-unresolved-not_satisfied" .atLeast 4 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-5-3-satisfied-unresolved-not_satisfied" .atLeast 5 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-0-3-satisfied-unresolved-not_satisfied" .atMost 0 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-1-3-satisfied-unresolved-not_satisfied" .atMost 1 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-2-3-satisfied-unresolved-not_satisfied" .atMost 2 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-3-3-satisfied-unresolved-not_satisfied" .atMost 3 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-4-3-satisfied-unresolved-not_satisfied" .atMost 4 [.satisfied, .unresolved, .notSatisfied]
]

def vectorChunk26 : List Vector := [
  .cardinality "at-most-5-3-satisfied-unresolved-not_satisfied" .atMost 5 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-0-3-satisfied-unresolved-not_satisfied" .exactly 0 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-1-3-satisfied-unresolved-not_satisfied" .exactly 1 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-2-3-satisfied-unresolved-not_satisfied" .exactly 2 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-3-3-satisfied-unresolved-not_satisfied" .exactly 3 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-4-3-satisfied-unresolved-not_satisfied" .exactly 4 [.satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-5-3-satisfied-unresolved-not_satisfied" .exactly 5 [.satisfied, .unresolved, .notSatisfied],
  .quantifier "forall-3-satisfied-unresolved-unresolved" .forall [.satisfied, .unresolved, .unresolved],
  .quantifier "exists-3-satisfied-unresolved-unresolved" .exists [.satisfied, .unresolved, .unresolved],
  .cardinality "at-least-0-3-satisfied-unresolved-unresolved" .atLeast 0 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-least-1-3-satisfied-unresolved-unresolved" .atLeast 1 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-least-2-3-satisfied-unresolved-unresolved" .atLeast 2 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-least-3-3-satisfied-unresolved-unresolved" .atLeast 3 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-least-4-3-satisfied-unresolved-unresolved" .atLeast 4 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-least-5-3-satisfied-unresolved-unresolved" .atLeast 5 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-most-0-3-satisfied-unresolved-unresolved" .atMost 0 [.satisfied, .unresolved, .unresolved]
]

def vectorChunk27 : List Vector := [
  .cardinality "at-most-1-3-satisfied-unresolved-unresolved" .atMost 1 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-most-2-3-satisfied-unresolved-unresolved" .atMost 2 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-most-3-3-satisfied-unresolved-unresolved" .atMost 3 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-most-4-3-satisfied-unresolved-unresolved" .atMost 4 [.satisfied, .unresolved, .unresolved],
  .cardinality "at-most-5-3-satisfied-unresolved-unresolved" .atMost 5 [.satisfied, .unresolved, .unresolved],
  .cardinality "exactly-0-3-satisfied-unresolved-unresolved" .exactly 0 [.satisfied, .unresolved, .unresolved],
  .cardinality "exactly-1-3-satisfied-unresolved-unresolved" .exactly 1 [.satisfied, .unresolved, .unresolved],
  .cardinality "exactly-2-3-satisfied-unresolved-unresolved" .exactly 2 [.satisfied, .unresolved, .unresolved],
  .cardinality "exactly-3-3-satisfied-unresolved-unresolved" .exactly 3 [.satisfied, .unresolved, .unresolved],
  .cardinality "exactly-4-3-satisfied-unresolved-unresolved" .exactly 4 [.satisfied, .unresolved, .unresolved],
  .cardinality "exactly-5-3-satisfied-unresolved-unresolved" .exactly 5 [.satisfied, .unresolved, .unresolved],
  .quantifier "forall-3-not_satisfied-satisfied-satisfied" .forall [.notSatisfied, .satisfied, .satisfied],
  .quantifier "exists-3-not_satisfied-satisfied-satisfied" .exists [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-0-3-not_satisfied-satisfied-satisfied" .atLeast 0 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-1-3-not_satisfied-satisfied-satisfied" .atLeast 1 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-2-3-not_satisfied-satisfied-satisfied" .atLeast 2 [.notSatisfied, .satisfied, .satisfied]
]

def vectorChunk28 : List Vector := [
  .cardinality "at-least-3-3-not_satisfied-satisfied-satisfied" .atLeast 3 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-4-3-not_satisfied-satisfied-satisfied" .atLeast 4 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-5-3-not_satisfied-satisfied-satisfied" .atLeast 5 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-0-3-not_satisfied-satisfied-satisfied" .atMost 0 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-1-3-not_satisfied-satisfied-satisfied" .atMost 1 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-2-3-not_satisfied-satisfied-satisfied" .atMost 2 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-3-3-not_satisfied-satisfied-satisfied" .atMost 3 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-4-3-not_satisfied-satisfied-satisfied" .atMost 4 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-5-3-not_satisfied-satisfied-satisfied" .atMost 5 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-0-3-not_satisfied-satisfied-satisfied" .exactly 0 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-1-3-not_satisfied-satisfied-satisfied" .exactly 1 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-2-3-not_satisfied-satisfied-satisfied" .exactly 2 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-3-3-not_satisfied-satisfied-satisfied" .exactly 3 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-4-3-not_satisfied-satisfied-satisfied" .exactly 4 [.notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-5-3-not_satisfied-satisfied-satisfied" .exactly 5 [.notSatisfied, .satisfied, .satisfied],
  .quantifier "forall-3-not_satisfied-satisfied-not_satisfied" .forall [.notSatisfied, .satisfied, .notSatisfied]
]

def vectorChunk29 : List Vector := [
  .quantifier "exists-3-not_satisfied-satisfied-not_satisfied" .exists [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-0-3-not_satisfied-satisfied-not_satisfied" .atLeast 0 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-1-3-not_satisfied-satisfied-not_satisfied" .atLeast 1 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-2-3-not_satisfied-satisfied-not_satisfied" .atLeast 2 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-3-3-not_satisfied-satisfied-not_satisfied" .atLeast 3 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-4-3-not_satisfied-satisfied-not_satisfied" .atLeast 4 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-5-3-not_satisfied-satisfied-not_satisfied" .atLeast 5 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-0-3-not_satisfied-satisfied-not_satisfied" .atMost 0 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-1-3-not_satisfied-satisfied-not_satisfied" .atMost 1 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-2-3-not_satisfied-satisfied-not_satisfied" .atMost 2 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-3-3-not_satisfied-satisfied-not_satisfied" .atMost 3 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-4-3-not_satisfied-satisfied-not_satisfied" .atMost 4 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-5-3-not_satisfied-satisfied-not_satisfied" .atMost 5 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-0-3-not_satisfied-satisfied-not_satisfied" .exactly 0 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-1-3-not_satisfied-satisfied-not_satisfied" .exactly 1 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-2-3-not_satisfied-satisfied-not_satisfied" .exactly 2 [.notSatisfied, .satisfied, .notSatisfied]
]

def vectorChunk30 : List Vector := [
  .cardinality "exactly-3-3-not_satisfied-satisfied-not_satisfied" .exactly 3 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-4-3-not_satisfied-satisfied-not_satisfied" .exactly 4 [.notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-5-3-not_satisfied-satisfied-not_satisfied" .exactly 5 [.notSatisfied, .satisfied, .notSatisfied],
  .quantifier "forall-3-not_satisfied-satisfied-unresolved" .forall [.notSatisfied, .satisfied, .unresolved],
  .quantifier "exists-3-not_satisfied-satisfied-unresolved" .exists [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-0-3-not_satisfied-satisfied-unresolved" .atLeast 0 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-1-3-not_satisfied-satisfied-unresolved" .atLeast 1 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-2-3-not_satisfied-satisfied-unresolved" .atLeast 2 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-3-3-not_satisfied-satisfied-unresolved" .atLeast 3 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-4-3-not_satisfied-satisfied-unresolved" .atLeast 4 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-5-3-not_satisfied-satisfied-unresolved" .atLeast 5 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-0-3-not_satisfied-satisfied-unresolved" .atMost 0 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-1-3-not_satisfied-satisfied-unresolved" .atMost 1 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-2-3-not_satisfied-satisfied-unresolved" .atMost 2 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-3-3-not_satisfied-satisfied-unresolved" .atMost 3 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-4-3-not_satisfied-satisfied-unresolved" .atMost 4 [.notSatisfied, .satisfied, .unresolved]
]

def vectorChunk31 : List Vector := [
  .cardinality "at-most-5-3-not_satisfied-satisfied-unresolved" .atMost 5 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-0-3-not_satisfied-satisfied-unresolved" .exactly 0 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-1-3-not_satisfied-satisfied-unresolved" .exactly 1 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-2-3-not_satisfied-satisfied-unresolved" .exactly 2 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-3-3-not_satisfied-satisfied-unresolved" .exactly 3 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-4-3-not_satisfied-satisfied-unresolved" .exactly 4 [.notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-5-3-not_satisfied-satisfied-unresolved" .exactly 5 [.notSatisfied, .satisfied, .unresolved],
  .quantifier "forall-3-not_satisfied-not_satisfied-satisfied" .forall [.notSatisfied, .notSatisfied, .satisfied],
  .quantifier "exists-3-not_satisfied-not_satisfied-satisfied" .exists [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-0-3-not_satisfied-not_satisfied-satisfied" .atLeast 0 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-1-3-not_satisfied-not_satisfied-satisfied" .atLeast 1 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-2-3-not_satisfied-not_satisfied-satisfied" .atLeast 2 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-3-3-not_satisfied-not_satisfied-satisfied" .atLeast 3 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-4-3-not_satisfied-not_satisfied-satisfied" .atLeast 4 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-5-3-not_satisfied-not_satisfied-satisfied" .atLeast 5 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-0-3-not_satisfied-not_satisfied-satisfied" .atMost 0 [.notSatisfied, .notSatisfied, .satisfied]
]

def vectorChunk32 : List Vector := [
  .cardinality "at-most-1-3-not_satisfied-not_satisfied-satisfied" .atMost 1 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-2-3-not_satisfied-not_satisfied-satisfied" .atMost 2 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-3-3-not_satisfied-not_satisfied-satisfied" .atMost 3 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-4-3-not_satisfied-not_satisfied-satisfied" .atMost 4 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-5-3-not_satisfied-not_satisfied-satisfied" .atMost 5 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-0-3-not_satisfied-not_satisfied-satisfied" .exactly 0 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-1-3-not_satisfied-not_satisfied-satisfied" .exactly 1 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-2-3-not_satisfied-not_satisfied-satisfied" .exactly 2 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-3-3-not_satisfied-not_satisfied-satisfied" .exactly 3 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-4-3-not_satisfied-not_satisfied-satisfied" .exactly 4 [.notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-5-3-not_satisfied-not_satisfied-satisfied" .exactly 5 [.notSatisfied, .notSatisfied, .satisfied],
  .quantifier "forall-3-not_satisfied-not_satisfied-not_satisfied" .forall [.notSatisfied, .notSatisfied, .notSatisfied],
  .quantifier "exists-3-not_satisfied-not_satisfied-not_satisfied" .exists [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-3-not_satisfied-not_satisfied-not_satisfied" .atLeast 0 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-3-not_satisfied-not_satisfied-not_satisfied" .atLeast 1 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-3-not_satisfied-not_satisfied-not_satisfied" .atLeast 2 [.notSatisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk33 : List Vector := [
  .cardinality "at-least-3-3-not_satisfied-not_satisfied-not_satisfied" .atLeast 3 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-3-not_satisfied-not_satisfied-not_satisfied" .atLeast 4 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-3-not_satisfied-not_satisfied-not_satisfied" .atLeast 5 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-3-not_satisfied-not_satisfied-not_satisfied" .atMost 0 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-1-3-not_satisfied-not_satisfied-not_satisfied" .atMost 1 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-3-not_satisfied-not_satisfied-not_satisfied" .atMost 2 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-3-not_satisfied-not_satisfied-not_satisfied" .atMost 3 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-3-not_satisfied-not_satisfied-not_satisfied" .atMost 4 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-5-3-not_satisfied-not_satisfied-not_satisfied" .atMost 5 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-3-not_satisfied-not_satisfied-not_satisfied" .exactly 0 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-3-not_satisfied-not_satisfied-not_satisfied" .exactly 1 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-3-not_satisfied-not_satisfied-not_satisfied" .exactly 2 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-3-3-not_satisfied-not_satisfied-not_satisfied" .exactly 3 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-3-not_satisfied-not_satisfied-not_satisfied" .exactly 4 [.notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-3-not_satisfied-not_satisfied-not_satisfied" .exactly 5 [.notSatisfied, .notSatisfied, .notSatisfied],
  .quantifier "forall-3-not_satisfied-not_satisfied-unresolved" .forall [.notSatisfied, .notSatisfied, .unresolved]
]

def vectorChunk34 : List Vector := [
  .quantifier "exists-3-not_satisfied-not_satisfied-unresolved" .exists [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-0-3-not_satisfied-not_satisfied-unresolved" .atLeast 0 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-1-3-not_satisfied-not_satisfied-unresolved" .atLeast 1 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-2-3-not_satisfied-not_satisfied-unresolved" .atLeast 2 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-3-3-not_satisfied-not_satisfied-unresolved" .atLeast 3 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-4-3-not_satisfied-not_satisfied-unresolved" .atLeast 4 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-5-3-not_satisfied-not_satisfied-unresolved" .atLeast 5 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-0-3-not_satisfied-not_satisfied-unresolved" .atMost 0 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-1-3-not_satisfied-not_satisfied-unresolved" .atMost 1 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-2-3-not_satisfied-not_satisfied-unresolved" .atMost 2 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-3-3-not_satisfied-not_satisfied-unresolved" .atMost 3 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-4-3-not_satisfied-not_satisfied-unresolved" .atMost 4 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-5-3-not_satisfied-not_satisfied-unresolved" .atMost 5 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-0-3-not_satisfied-not_satisfied-unresolved" .exactly 0 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-1-3-not_satisfied-not_satisfied-unresolved" .exactly 1 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-2-3-not_satisfied-not_satisfied-unresolved" .exactly 2 [.notSatisfied, .notSatisfied, .unresolved]
]

def vectorChunk35 : List Vector := [
  .cardinality "exactly-3-3-not_satisfied-not_satisfied-unresolved" .exactly 3 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-4-3-not_satisfied-not_satisfied-unresolved" .exactly 4 [.notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-5-3-not_satisfied-not_satisfied-unresolved" .exactly 5 [.notSatisfied, .notSatisfied, .unresolved],
  .quantifier "forall-3-not_satisfied-unresolved-satisfied" .forall [.notSatisfied, .unresolved, .satisfied],
  .quantifier "exists-3-not_satisfied-unresolved-satisfied" .exists [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-0-3-not_satisfied-unresolved-satisfied" .atLeast 0 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-1-3-not_satisfied-unresolved-satisfied" .atLeast 1 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-2-3-not_satisfied-unresolved-satisfied" .atLeast 2 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-3-3-not_satisfied-unresolved-satisfied" .atLeast 3 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-4-3-not_satisfied-unresolved-satisfied" .atLeast 4 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-5-3-not_satisfied-unresolved-satisfied" .atLeast 5 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-0-3-not_satisfied-unresolved-satisfied" .atMost 0 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-1-3-not_satisfied-unresolved-satisfied" .atMost 1 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-2-3-not_satisfied-unresolved-satisfied" .atMost 2 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-3-3-not_satisfied-unresolved-satisfied" .atMost 3 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-4-3-not_satisfied-unresolved-satisfied" .atMost 4 [.notSatisfied, .unresolved, .satisfied]
]

def vectorChunk36 : List Vector := [
  .cardinality "at-most-5-3-not_satisfied-unresolved-satisfied" .atMost 5 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-0-3-not_satisfied-unresolved-satisfied" .exactly 0 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-1-3-not_satisfied-unresolved-satisfied" .exactly 1 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-2-3-not_satisfied-unresolved-satisfied" .exactly 2 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-3-3-not_satisfied-unresolved-satisfied" .exactly 3 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-4-3-not_satisfied-unresolved-satisfied" .exactly 4 [.notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-5-3-not_satisfied-unresolved-satisfied" .exactly 5 [.notSatisfied, .unresolved, .satisfied],
  .quantifier "forall-3-not_satisfied-unresolved-not_satisfied" .forall [.notSatisfied, .unresolved, .notSatisfied],
  .quantifier "exists-3-not_satisfied-unresolved-not_satisfied" .exists [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-0-3-not_satisfied-unresolved-not_satisfied" .atLeast 0 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-1-3-not_satisfied-unresolved-not_satisfied" .atLeast 1 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-2-3-not_satisfied-unresolved-not_satisfied" .atLeast 2 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-3-3-not_satisfied-unresolved-not_satisfied" .atLeast 3 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-4-3-not_satisfied-unresolved-not_satisfied" .atLeast 4 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-5-3-not_satisfied-unresolved-not_satisfied" .atLeast 5 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-0-3-not_satisfied-unresolved-not_satisfied" .atMost 0 [.notSatisfied, .unresolved, .notSatisfied]
]

def vectorChunk37 : List Vector := [
  .cardinality "at-most-1-3-not_satisfied-unresolved-not_satisfied" .atMost 1 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-2-3-not_satisfied-unresolved-not_satisfied" .atMost 2 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-3-3-not_satisfied-unresolved-not_satisfied" .atMost 3 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-4-3-not_satisfied-unresolved-not_satisfied" .atMost 4 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-5-3-not_satisfied-unresolved-not_satisfied" .atMost 5 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-0-3-not_satisfied-unresolved-not_satisfied" .exactly 0 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-1-3-not_satisfied-unresolved-not_satisfied" .exactly 1 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-2-3-not_satisfied-unresolved-not_satisfied" .exactly 2 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-3-3-not_satisfied-unresolved-not_satisfied" .exactly 3 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-4-3-not_satisfied-unresolved-not_satisfied" .exactly 4 [.notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-5-3-not_satisfied-unresolved-not_satisfied" .exactly 5 [.notSatisfied, .unresolved, .notSatisfied],
  .quantifier "forall-3-not_satisfied-unresolved-unresolved" .forall [.notSatisfied, .unresolved, .unresolved],
  .quantifier "exists-3-not_satisfied-unresolved-unresolved" .exists [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-0-3-not_satisfied-unresolved-unresolved" .atLeast 0 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-1-3-not_satisfied-unresolved-unresolved" .atLeast 1 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-2-3-not_satisfied-unresolved-unresolved" .atLeast 2 [.notSatisfied, .unresolved, .unresolved]
]

def vectorChunk38 : List Vector := [
  .cardinality "at-least-3-3-not_satisfied-unresolved-unresolved" .atLeast 3 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-4-3-not_satisfied-unresolved-unresolved" .atLeast 4 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-5-3-not_satisfied-unresolved-unresolved" .atLeast 5 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-0-3-not_satisfied-unresolved-unresolved" .atMost 0 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-1-3-not_satisfied-unresolved-unresolved" .atMost 1 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-2-3-not_satisfied-unresolved-unresolved" .atMost 2 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-3-3-not_satisfied-unresolved-unresolved" .atMost 3 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-4-3-not_satisfied-unresolved-unresolved" .atMost 4 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-5-3-not_satisfied-unresolved-unresolved" .atMost 5 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-0-3-not_satisfied-unresolved-unresolved" .exactly 0 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-1-3-not_satisfied-unresolved-unresolved" .exactly 1 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-2-3-not_satisfied-unresolved-unresolved" .exactly 2 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-3-3-not_satisfied-unresolved-unresolved" .exactly 3 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-4-3-not_satisfied-unresolved-unresolved" .exactly 4 [.notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-5-3-not_satisfied-unresolved-unresolved" .exactly 5 [.notSatisfied, .unresolved, .unresolved],
  .quantifier "forall-3-unresolved-satisfied-satisfied" .forall [.unresolved, .satisfied, .satisfied]
]

def vectorChunk39 : List Vector := [
  .quantifier "exists-3-unresolved-satisfied-satisfied" .exists [.unresolved, .satisfied, .satisfied],
  .cardinality "at-least-0-3-unresolved-satisfied-satisfied" .atLeast 0 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-least-1-3-unresolved-satisfied-satisfied" .atLeast 1 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-least-2-3-unresolved-satisfied-satisfied" .atLeast 2 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-least-3-3-unresolved-satisfied-satisfied" .atLeast 3 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-least-4-3-unresolved-satisfied-satisfied" .atLeast 4 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-least-5-3-unresolved-satisfied-satisfied" .atLeast 5 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-most-0-3-unresolved-satisfied-satisfied" .atMost 0 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-most-1-3-unresolved-satisfied-satisfied" .atMost 1 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-most-2-3-unresolved-satisfied-satisfied" .atMost 2 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-most-3-3-unresolved-satisfied-satisfied" .atMost 3 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-most-4-3-unresolved-satisfied-satisfied" .atMost 4 [.unresolved, .satisfied, .satisfied],
  .cardinality "at-most-5-3-unresolved-satisfied-satisfied" .atMost 5 [.unresolved, .satisfied, .satisfied],
  .cardinality "exactly-0-3-unresolved-satisfied-satisfied" .exactly 0 [.unresolved, .satisfied, .satisfied],
  .cardinality "exactly-1-3-unresolved-satisfied-satisfied" .exactly 1 [.unresolved, .satisfied, .satisfied],
  .cardinality "exactly-2-3-unresolved-satisfied-satisfied" .exactly 2 [.unresolved, .satisfied, .satisfied]
]

def vectorChunk40 : List Vector := [
  .cardinality "exactly-3-3-unresolved-satisfied-satisfied" .exactly 3 [.unresolved, .satisfied, .satisfied],
  .cardinality "exactly-4-3-unresolved-satisfied-satisfied" .exactly 4 [.unresolved, .satisfied, .satisfied],
  .cardinality "exactly-5-3-unresolved-satisfied-satisfied" .exactly 5 [.unresolved, .satisfied, .satisfied],
  .quantifier "forall-3-unresolved-satisfied-not_satisfied" .forall [.unresolved, .satisfied, .notSatisfied],
  .quantifier "exists-3-unresolved-satisfied-not_satisfied" .exists [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-0-3-unresolved-satisfied-not_satisfied" .atLeast 0 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-1-3-unresolved-satisfied-not_satisfied" .atLeast 1 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-2-3-unresolved-satisfied-not_satisfied" .atLeast 2 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-3-3-unresolved-satisfied-not_satisfied" .atLeast 3 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-4-3-unresolved-satisfied-not_satisfied" .atLeast 4 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-5-3-unresolved-satisfied-not_satisfied" .atLeast 5 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-0-3-unresolved-satisfied-not_satisfied" .atMost 0 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-1-3-unresolved-satisfied-not_satisfied" .atMost 1 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-2-3-unresolved-satisfied-not_satisfied" .atMost 2 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-3-3-unresolved-satisfied-not_satisfied" .atMost 3 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-4-3-unresolved-satisfied-not_satisfied" .atMost 4 [.unresolved, .satisfied, .notSatisfied]
]

def vectorChunk41 : List Vector := [
  .cardinality "at-most-5-3-unresolved-satisfied-not_satisfied" .atMost 5 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-0-3-unresolved-satisfied-not_satisfied" .exactly 0 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-1-3-unresolved-satisfied-not_satisfied" .exactly 1 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-2-3-unresolved-satisfied-not_satisfied" .exactly 2 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-3-3-unresolved-satisfied-not_satisfied" .exactly 3 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-4-3-unresolved-satisfied-not_satisfied" .exactly 4 [.unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-5-3-unresolved-satisfied-not_satisfied" .exactly 5 [.unresolved, .satisfied, .notSatisfied],
  .quantifier "forall-3-unresolved-satisfied-unresolved" .forall [.unresolved, .satisfied, .unresolved],
  .quantifier "exists-3-unresolved-satisfied-unresolved" .exists [.unresolved, .satisfied, .unresolved],
  .cardinality "at-least-0-3-unresolved-satisfied-unresolved" .atLeast 0 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-least-1-3-unresolved-satisfied-unresolved" .atLeast 1 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-least-2-3-unresolved-satisfied-unresolved" .atLeast 2 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-least-3-3-unresolved-satisfied-unresolved" .atLeast 3 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-least-4-3-unresolved-satisfied-unresolved" .atLeast 4 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-least-5-3-unresolved-satisfied-unresolved" .atLeast 5 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-most-0-3-unresolved-satisfied-unresolved" .atMost 0 [.unresolved, .satisfied, .unresolved]
]

def vectorChunk42 : List Vector := [
  .cardinality "at-most-1-3-unresolved-satisfied-unresolved" .atMost 1 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-most-2-3-unresolved-satisfied-unresolved" .atMost 2 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-most-3-3-unresolved-satisfied-unresolved" .atMost 3 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-most-4-3-unresolved-satisfied-unresolved" .atMost 4 [.unresolved, .satisfied, .unresolved],
  .cardinality "at-most-5-3-unresolved-satisfied-unresolved" .atMost 5 [.unresolved, .satisfied, .unresolved],
  .cardinality "exactly-0-3-unresolved-satisfied-unresolved" .exactly 0 [.unresolved, .satisfied, .unresolved],
  .cardinality "exactly-1-3-unresolved-satisfied-unresolved" .exactly 1 [.unresolved, .satisfied, .unresolved],
  .cardinality "exactly-2-3-unresolved-satisfied-unresolved" .exactly 2 [.unresolved, .satisfied, .unresolved],
  .cardinality "exactly-3-3-unresolved-satisfied-unresolved" .exactly 3 [.unresolved, .satisfied, .unresolved],
  .cardinality "exactly-4-3-unresolved-satisfied-unresolved" .exactly 4 [.unresolved, .satisfied, .unresolved],
  .cardinality "exactly-5-3-unresolved-satisfied-unresolved" .exactly 5 [.unresolved, .satisfied, .unresolved],
  .quantifier "forall-3-unresolved-not_satisfied-satisfied" .forall [.unresolved, .notSatisfied, .satisfied],
  .quantifier "exists-3-unresolved-not_satisfied-satisfied" .exists [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-0-3-unresolved-not_satisfied-satisfied" .atLeast 0 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-1-3-unresolved-not_satisfied-satisfied" .atLeast 1 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-2-3-unresolved-not_satisfied-satisfied" .atLeast 2 [.unresolved, .notSatisfied, .satisfied]
]

def vectorChunk43 : List Vector := [
  .cardinality "at-least-3-3-unresolved-not_satisfied-satisfied" .atLeast 3 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-4-3-unresolved-not_satisfied-satisfied" .atLeast 4 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-5-3-unresolved-not_satisfied-satisfied" .atLeast 5 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-0-3-unresolved-not_satisfied-satisfied" .atMost 0 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-1-3-unresolved-not_satisfied-satisfied" .atMost 1 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-2-3-unresolved-not_satisfied-satisfied" .atMost 2 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-3-3-unresolved-not_satisfied-satisfied" .atMost 3 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-4-3-unresolved-not_satisfied-satisfied" .atMost 4 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-5-3-unresolved-not_satisfied-satisfied" .atMost 5 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-0-3-unresolved-not_satisfied-satisfied" .exactly 0 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-1-3-unresolved-not_satisfied-satisfied" .exactly 1 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-2-3-unresolved-not_satisfied-satisfied" .exactly 2 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-3-3-unresolved-not_satisfied-satisfied" .exactly 3 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-4-3-unresolved-not_satisfied-satisfied" .exactly 4 [.unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-5-3-unresolved-not_satisfied-satisfied" .exactly 5 [.unresolved, .notSatisfied, .satisfied],
  .quantifier "forall-3-unresolved-not_satisfied-not_satisfied" .forall [.unresolved, .notSatisfied, .notSatisfied]
]

def vectorChunk44 : List Vector := [
  .quantifier "exists-3-unresolved-not_satisfied-not_satisfied" .exists [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-3-unresolved-not_satisfied-not_satisfied" .atLeast 0 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-3-unresolved-not_satisfied-not_satisfied" .atLeast 1 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-3-unresolved-not_satisfied-not_satisfied" .atLeast 2 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-3-3-unresolved-not_satisfied-not_satisfied" .atLeast 3 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-3-unresolved-not_satisfied-not_satisfied" .atLeast 4 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-3-unresolved-not_satisfied-not_satisfied" .atLeast 5 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-3-unresolved-not_satisfied-not_satisfied" .atMost 0 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-1-3-unresolved-not_satisfied-not_satisfied" .atMost 1 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-3-unresolved-not_satisfied-not_satisfied" .atMost 2 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-3-unresolved-not_satisfied-not_satisfied" .atMost 3 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-3-unresolved-not_satisfied-not_satisfied" .atMost 4 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-5-3-unresolved-not_satisfied-not_satisfied" .atMost 5 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-3-unresolved-not_satisfied-not_satisfied" .exactly 0 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-3-unresolved-not_satisfied-not_satisfied" .exactly 1 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-3-unresolved-not_satisfied-not_satisfied" .exactly 2 [.unresolved, .notSatisfied, .notSatisfied]
]

def vectorChunk45 : List Vector := [
  .cardinality "exactly-3-3-unresolved-not_satisfied-not_satisfied" .exactly 3 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-3-unresolved-not_satisfied-not_satisfied" .exactly 4 [.unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-3-unresolved-not_satisfied-not_satisfied" .exactly 5 [.unresolved, .notSatisfied, .notSatisfied],
  .quantifier "forall-3-unresolved-not_satisfied-unresolved" .forall [.unresolved, .notSatisfied, .unresolved],
  .quantifier "exists-3-unresolved-not_satisfied-unresolved" .exists [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-0-3-unresolved-not_satisfied-unresolved" .atLeast 0 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-1-3-unresolved-not_satisfied-unresolved" .atLeast 1 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-2-3-unresolved-not_satisfied-unresolved" .atLeast 2 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-3-3-unresolved-not_satisfied-unresolved" .atLeast 3 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-4-3-unresolved-not_satisfied-unresolved" .atLeast 4 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-5-3-unresolved-not_satisfied-unresolved" .atLeast 5 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-0-3-unresolved-not_satisfied-unresolved" .atMost 0 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-1-3-unresolved-not_satisfied-unresolved" .atMost 1 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-2-3-unresolved-not_satisfied-unresolved" .atMost 2 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-3-3-unresolved-not_satisfied-unresolved" .atMost 3 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-4-3-unresolved-not_satisfied-unresolved" .atMost 4 [.unresolved, .notSatisfied, .unresolved]
]

def vectorChunk46 : List Vector := [
  .cardinality "at-most-5-3-unresolved-not_satisfied-unresolved" .atMost 5 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-0-3-unresolved-not_satisfied-unresolved" .exactly 0 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-1-3-unresolved-not_satisfied-unresolved" .exactly 1 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-2-3-unresolved-not_satisfied-unresolved" .exactly 2 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-3-3-unresolved-not_satisfied-unresolved" .exactly 3 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-4-3-unresolved-not_satisfied-unresolved" .exactly 4 [.unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-5-3-unresolved-not_satisfied-unresolved" .exactly 5 [.unresolved, .notSatisfied, .unresolved],
  .quantifier "forall-3-unresolved-unresolved-satisfied" .forall [.unresolved, .unresolved, .satisfied],
  .quantifier "exists-3-unresolved-unresolved-satisfied" .exists [.unresolved, .unresolved, .satisfied],
  .cardinality "at-least-0-3-unresolved-unresolved-satisfied" .atLeast 0 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-least-1-3-unresolved-unresolved-satisfied" .atLeast 1 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-least-2-3-unresolved-unresolved-satisfied" .atLeast 2 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-least-3-3-unresolved-unresolved-satisfied" .atLeast 3 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-least-4-3-unresolved-unresolved-satisfied" .atLeast 4 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-least-5-3-unresolved-unresolved-satisfied" .atLeast 5 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-most-0-3-unresolved-unresolved-satisfied" .atMost 0 [.unresolved, .unresolved, .satisfied]
]

def vectorChunk47 : List Vector := [
  .cardinality "at-most-1-3-unresolved-unresolved-satisfied" .atMost 1 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-most-2-3-unresolved-unresolved-satisfied" .atMost 2 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-most-3-3-unresolved-unresolved-satisfied" .atMost 3 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-most-4-3-unresolved-unresolved-satisfied" .atMost 4 [.unresolved, .unresolved, .satisfied],
  .cardinality "at-most-5-3-unresolved-unresolved-satisfied" .atMost 5 [.unresolved, .unresolved, .satisfied],
  .cardinality "exactly-0-3-unresolved-unresolved-satisfied" .exactly 0 [.unresolved, .unresolved, .satisfied],
  .cardinality "exactly-1-3-unresolved-unresolved-satisfied" .exactly 1 [.unresolved, .unresolved, .satisfied],
  .cardinality "exactly-2-3-unresolved-unresolved-satisfied" .exactly 2 [.unresolved, .unresolved, .satisfied],
  .cardinality "exactly-3-3-unresolved-unresolved-satisfied" .exactly 3 [.unresolved, .unresolved, .satisfied],
  .cardinality "exactly-4-3-unresolved-unresolved-satisfied" .exactly 4 [.unresolved, .unresolved, .satisfied],
  .cardinality "exactly-5-3-unresolved-unresolved-satisfied" .exactly 5 [.unresolved, .unresolved, .satisfied],
  .quantifier "forall-3-unresolved-unresolved-not_satisfied" .forall [.unresolved, .unresolved, .notSatisfied],
  .quantifier "exists-3-unresolved-unresolved-not_satisfied" .exists [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-0-3-unresolved-unresolved-not_satisfied" .atLeast 0 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-1-3-unresolved-unresolved-not_satisfied" .atLeast 1 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-2-3-unresolved-unresolved-not_satisfied" .atLeast 2 [.unresolved, .unresolved, .notSatisfied]
]

def vectorChunk48 : List Vector := [
  .cardinality "at-least-3-3-unresolved-unresolved-not_satisfied" .atLeast 3 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-4-3-unresolved-unresolved-not_satisfied" .atLeast 4 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-5-3-unresolved-unresolved-not_satisfied" .atLeast 5 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-0-3-unresolved-unresolved-not_satisfied" .atMost 0 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-1-3-unresolved-unresolved-not_satisfied" .atMost 1 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-2-3-unresolved-unresolved-not_satisfied" .atMost 2 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-3-3-unresolved-unresolved-not_satisfied" .atMost 3 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-4-3-unresolved-unresolved-not_satisfied" .atMost 4 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-5-3-unresolved-unresolved-not_satisfied" .atMost 5 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-0-3-unresolved-unresolved-not_satisfied" .exactly 0 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-1-3-unresolved-unresolved-not_satisfied" .exactly 1 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-2-3-unresolved-unresolved-not_satisfied" .exactly 2 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-3-3-unresolved-unresolved-not_satisfied" .exactly 3 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-4-3-unresolved-unresolved-not_satisfied" .exactly 4 [.unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-5-3-unresolved-unresolved-not_satisfied" .exactly 5 [.unresolved, .unresolved, .notSatisfied],
  .quantifier "forall-3-unresolved-unresolved-unresolved" .forall [.unresolved, .unresolved, .unresolved]
]

def vectorChunk49 : List Vector := [
  .quantifier "exists-3-unresolved-unresolved-unresolved" .exists [.unresolved, .unresolved, .unresolved],
  .cardinality "at-least-0-3-unresolved-unresolved-unresolved" .atLeast 0 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-least-1-3-unresolved-unresolved-unresolved" .atLeast 1 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-least-2-3-unresolved-unresolved-unresolved" .atLeast 2 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-least-3-3-unresolved-unresolved-unresolved" .atLeast 3 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-least-4-3-unresolved-unresolved-unresolved" .atLeast 4 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-least-5-3-unresolved-unresolved-unresolved" .atLeast 5 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-most-0-3-unresolved-unresolved-unresolved" .atMost 0 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-most-1-3-unresolved-unresolved-unresolved" .atMost 1 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-most-2-3-unresolved-unresolved-unresolved" .atMost 2 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-most-3-3-unresolved-unresolved-unresolved" .atMost 3 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-most-4-3-unresolved-unresolved-unresolved" .atMost 4 [.unresolved, .unresolved, .unresolved],
  .cardinality "at-most-5-3-unresolved-unresolved-unresolved" .atMost 5 [.unresolved, .unresolved, .unresolved],
  .cardinality "exactly-0-3-unresolved-unresolved-unresolved" .exactly 0 [.unresolved, .unresolved, .unresolved],
  .cardinality "exactly-1-3-unresolved-unresolved-unresolved" .exactly 1 [.unresolved, .unresolved, .unresolved],
  .cardinality "exactly-2-3-unresolved-unresolved-unresolved" .exactly 2 [.unresolved, .unresolved, .unresolved]
]

def vectorChunk50 : List Vector := [
  .cardinality "exactly-3-3-unresolved-unresolved-unresolved" .exactly 3 [.unresolved, .unresolved, .unresolved],
  .cardinality "exactly-4-3-unresolved-unresolved-unresolved" .exactly 4 [.unresolved, .unresolved, .unresolved],
  .cardinality "exactly-5-3-unresolved-unresolved-unresolved" .exactly 5 [.unresolved, .unresolved, .unresolved],
  .quantifier "forall-4-satisfied-satisfied-satisfied-satisfied" .forall [.satisfied, .satisfied, .satisfied, .satisfied],
  .quantifier "exists-4-satisfied-satisfied-satisfied-satisfied" .exists [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-0-4-satisfied-satisfied-satisfied-satisfied" .atLeast 0 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-1-4-satisfied-satisfied-satisfied-satisfied" .atLeast 1 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-2-4-satisfied-satisfied-satisfied-satisfied" .atLeast 2 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-3-4-satisfied-satisfied-satisfied-satisfied" .atLeast 3 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-4-4-satisfied-satisfied-satisfied-satisfied" .atLeast 4 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-5-4-satisfied-satisfied-satisfied-satisfied" .atLeast 5 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-0-4-satisfied-satisfied-satisfied-satisfied" .atMost 0 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-1-4-satisfied-satisfied-satisfied-satisfied" .atMost 1 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-2-4-satisfied-satisfied-satisfied-satisfied" .atMost 2 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-3-4-satisfied-satisfied-satisfied-satisfied" .atMost 3 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-4-4-satisfied-satisfied-satisfied-satisfied" .atMost 4 [.satisfied, .satisfied, .satisfied, .satisfied]
]

def vectorChunk51 : List Vector := [
  .cardinality "at-most-5-4-satisfied-satisfied-satisfied-satisfied" .atMost 5 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-0-4-satisfied-satisfied-satisfied-satisfied" .exactly 0 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-1-4-satisfied-satisfied-satisfied-satisfied" .exactly 1 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-2-4-satisfied-satisfied-satisfied-satisfied" .exactly 2 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-3-4-satisfied-satisfied-satisfied-satisfied" .exactly 3 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-4-4-satisfied-satisfied-satisfied-satisfied" .exactly 4 [.satisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-5-4-satisfied-satisfied-satisfied-satisfied" .exactly 5 [.satisfied, .satisfied, .satisfied, .satisfied],
  .quantifier "forall-4-satisfied-satisfied-satisfied-not_satisfied" .forall [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .quantifier "exists-4-satisfied-satisfied-satisfied-not_satisfied" .exists [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-0-4-satisfied-satisfied-satisfied-not_satisfied" .atLeast 0 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-1-4-satisfied-satisfied-satisfied-not_satisfied" .atLeast 1 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-2-4-satisfied-satisfied-satisfied-not_satisfied" .atLeast 2 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-3-4-satisfied-satisfied-satisfied-not_satisfied" .atLeast 3 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-4-4-satisfied-satisfied-satisfied-not_satisfied" .atLeast 4 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-5-4-satisfied-satisfied-satisfied-not_satisfied" .atLeast 5 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-0-4-satisfied-satisfied-satisfied-not_satisfied" .atMost 0 [.satisfied, .satisfied, .satisfied, .notSatisfied]
]

def vectorChunk52 : List Vector := [
  .cardinality "at-most-1-4-satisfied-satisfied-satisfied-not_satisfied" .atMost 1 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-2-4-satisfied-satisfied-satisfied-not_satisfied" .atMost 2 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-3-4-satisfied-satisfied-satisfied-not_satisfied" .atMost 3 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-4-4-satisfied-satisfied-satisfied-not_satisfied" .atMost 4 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-5-4-satisfied-satisfied-satisfied-not_satisfied" .atMost 5 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-0-4-satisfied-satisfied-satisfied-not_satisfied" .exactly 0 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-1-4-satisfied-satisfied-satisfied-not_satisfied" .exactly 1 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-2-4-satisfied-satisfied-satisfied-not_satisfied" .exactly 2 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-3-4-satisfied-satisfied-satisfied-not_satisfied" .exactly 3 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-4-4-satisfied-satisfied-satisfied-not_satisfied" .exactly 4 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-5-4-satisfied-satisfied-satisfied-not_satisfied" .exactly 5 [.satisfied, .satisfied, .satisfied, .notSatisfied],
  .quantifier "forall-4-satisfied-satisfied-satisfied-unresolved" .forall [.satisfied, .satisfied, .satisfied, .unresolved],
  .quantifier "exists-4-satisfied-satisfied-satisfied-unresolved" .exists [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-0-4-satisfied-satisfied-satisfied-unresolved" .atLeast 0 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-1-4-satisfied-satisfied-satisfied-unresolved" .atLeast 1 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-2-4-satisfied-satisfied-satisfied-unresolved" .atLeast 2 [.satisfied, .satisfied, .satisfied, .unresolved]
]

def vectorChunk53 : List Vector := [
  .cardinality "at-least-3-4-satisfied-satisfied-satisfied-unresolved" .atLeast 3 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-4-4-satisfied-satisfied-satisfied-unresolved" .atLeast 4 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-5-4-satisfied-satisfied-satisfied-unresolved" .atLeast 5 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-0-4-satisfied-satisfied-satisfied-unresolved" .atMost 0 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-1-4-satisfied-satisfied-satisfied-unresolved" .atMost 1 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-2-4-satisfied-satisfied-satisfied-unresolved" .atMost 2 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-3-4-satisfied-satisfied-satisfied-unresolved" .atMost 3 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-4-4-satisfied-satisfied-satisfied-unresolved" .atMost 4 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-5-4-satisfied-satisfied-satisfied-unresolved" .atMost 5 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-0-4-satisfied-satisfied-satisfied-unresolved" .exactly 0 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-1-4-satisfied-satisfied-satisfied-unresolved" .exactly 1 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-2-4-satisfied-satisfied-satisfied-unresolved" .exactly 2 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-3-4-satisfied-satisfied-satisfied-unresolved" .exactly 3 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-4-4-satisfied-satisfied-satisfied-unresolved" .exactly 4 [.satisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-5-4-satisfied-satisfied-satisfied-unresolved" .exactly 5 [.satisfied, .satisfied, .satisfied, .unresolved],
  .quantifier "forall-4-satisfied-satisfied-not_satisfied-satisfied" .forall [.satisfied, .satisfied, .notSatisfied, .satisfied]
]

def vectorChunk54 : List Vector := [
  .quantifier "exists-4-satisfied-satisfied-not_satisfied-satisfied" .exists [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-0-4-satisfied-satisfied-not_satisfied-satisfied" .atLeast 0 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-1-4-satisfied-satisfied-not_satisfied-satisfied" .atLeast 1 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-2-4-satisfied-satisfied-not_satisfied-satisfied" .atLeast 2 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-3-4-satisfied-satisfied-not_satisfied-satisfied" .atLeast 3 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-4-4-satisfied-satisfied-not_satisfied-satisfied" .atLeast 4 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-5-4-satisfied-satisfied-not_satisfied-satisfied" .atLeast 5 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-0-4-satisfied-satisfied-not_satisfied-satisfied" .atMost 0 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-1-4-satisfied-satisfied-not_satisfied-satisfied" .atMost 1 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-2-4-satisfied-satisfied-not_satisfied-satisfied" .atMost 2 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-3-4-satisfied-satisfied-not_satisfied-satisfied" .atMost 3 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-4-4-satisfied-satisfied-not_satisfied-satisfied" .atMost 4 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-5-4-satisfied-satisfied-not_satisfied-satisfied" .atMost 5 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-0-4-satisfied-satisfied-not_satisfied-satisfied" .exactly 0 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-1-4-satisfied-satisfied-not_satisfied-satisfied" .exactly 1 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-2-4-satisfied-satisfied-not_satisfied-satisfied" .exactly 2 [.satisfied, .satisfied, .notSatisfied, .satisfied]
]

def vectorChunk55 : List Vector := [
  .cardinality "exactly-3-4-satisfied-satisfied-not_satisfied-satisfied" .exactly 3 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-4-4-satisfied-satisfied-not_satisfied-satisfied" .exactly 4 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-5-4-satisfied-satisfied-not_satisfied-satisfied" .exactly 5 [.satisfied, .satisfied, .notSatisfied, .satisfied],
  .quantifier "forall-4-satisfied-satisfied-not_satisfied-not_satisfied" .forall [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .quantifier "exists-4-satisfied-satisfied-not_satisfied-not_satisfied" .exists [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-4-satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 0 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-4-satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 1 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-4-satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 2 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-3-4-satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 3 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-4-satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 4 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-4-satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 5 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-4-satisfied-satisfied-not_satisfied-not_satisfied" .atMost 0 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-1-4-satisfied-satisfied-not_satisfied-not_satisfied" .atMost 1 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-4-satisfied-satisfied-not_satisfied-not_satisfied" .atMost 2 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-4-satisfied-satisfied-not_satisfied-not_satisfied" .atMost 3 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-4-satisfied-satisfied-not_satisfied-not_satisfied" .atMost 4 [.satisfied, .satisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk56 : List Vector := [
  .cardinality "at-most-5-4-satisfied-satisfied-not_satisfied-not_satisfied" .atMost 5 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-4-satisfied-satisfied-not_satisfied-not_satisfied" .exactly 0 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-4-satisfied-satisfied-not_satisfied-not_satisfied" .exactly 1 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-4-satisfied-satisfied-not_satisfied-not_satisfied" .exactly 2 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-3-4-satisfied-satisfied-not_satisfied-not_satisfied" .exactly 3 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-4-satisfied-satisfied-not_satisfied-not_satisfied" .exactly 4 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-4-satisfied-satisfied-not_satisfied-not_satisfied" .exactly 5 [.satisfied, .satisfied, .notSatisfied, .notSatisfied],
  .quantifier "forall-4-satisfied-satisfied-not_satisfied-unresolved" .forall [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .quantifier "exists-4-satisfied-satisfied-not_satisfied-unresolved" .exists [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-0-4-satisfied-satisfied-not_satisfied-unresolved" .atLeast 0 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-1-4-satisfied-satisfied-not_satisfied-unresolved" .atLeast 1 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-2-4-satisfied-satisfied-not_satisfied-unresolved" .atLeast 2 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-3-4-satisfied-satisfied-not_satisfied-unresolved" .atLeast 3 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-4-4-satisfied-satisfied-not_satisfied-unresolved" .atLeast 4 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-5-4-satisfied-satisfied-not_satisfied-unresolved" .atLeast 5 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-0-4-satisfied-satisfied-not_satisfied-unresolved" .atMost 0 [.satisfied, .satisfied, .notSatisfied, .unresolved]
]

def vectorChunk57 : List Vector := [
  .cardinality "at-most-1-4-satisfied-satisfied-not_satisfied-unresolved" .atMost 1 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-2-4-satisfied-satisfied-not_satisfied-unresolved" .atMost 2 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-3-4-satisfied-satisfied-not_satisfied-unresolved" .atMost 3 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-4-4-satisfied-satisfied-not_satisfied-unresolved" .atMost 4 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-5-4-satisfied-satisfied-not_satisfied-unresolved" .atMost 5 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-0-4-satisfied-satisfied-not_satisfied-unresolved" .exactly 0 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-1-4-satisfied-satisfied-not_satisfied-unresolved" .exactly 1 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-2-4-satisfied-satisfied-not_satisfied-unresolved" .exactly 2 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-3-4-satisfied-satisfied-not_satisfied-unresolved" .exactly 3 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-4-4-satisfied-satisfied-not_satisfied-unresolved" .exactly 4 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-5-4-satisfied-satisfied-not_satisfied-unresolved" .exactly 5 [.satisfied, .satisfied, .notSatisfied, .unresolved],
  .quantifier "forall-4-satisfied-satisfied-unresolved-satisfied" .forall [.satisfied, .satisfied, .unresolved, .satisfied],
  .quantifier "exists-4-satisfied-satisfied-unresolved-satisfied" .exists [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-0-4-satisfied-satisfied-unresolved-satisfied" .atLeast 0 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-1-4-satisfied-satisfied-unresolved-satisfied" .atLeast 1 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-2-4-satisfied-satisfied-unresolved-satisfied" .atLeast 2 [.satisfied, .satisfied, .unresolved, .satisfied]
]

def vectorChunk58 : List Vector := [
  .cardinality "at-least-3-4-satisfied-satisfied-unresolved-satisfied" .atLeast 3 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-4-4-satisfied-satisfied-unresolved-satisfied" .atLeast 4 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-5-4-satisfied-satisfied-unresolved-satisfied" .atLeast 5 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-0-4-satisfied-satisfied-unresolved-satisfied" .atMost 0 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-1-4-satisfied-satisfied-unresolved-satisfied" .atMost 1 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-2-4-satisfied-satisfied-unresolved-satisfied" .atMost 2 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-3-4-satisfied-satisfied-unresolved-satisfied" .atMost 3 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-4-4-satisfied-satisfied-unresolved-satisfied" .atMost 4 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-5-4-satisfied-satisfied-unresolved-satisfied" .atMost 5 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-0-4-satisfied-satisfied-unresolved-satisfied" .exactly 0 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-1-4-satisfied-satisfied-unresolved-satisfied" .exactly 1 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-2-4-satisfied-satisfied-unresolved-satisfied" .exactly 2 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-3-4-satisfied-satisfied-unresolved-satisfied" .exactly 3 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-4-4-satisfied-satisfied-unresolved-satisfied" .exactly 4 [.satisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-5-4-satisfied-satisfied-unresolved-satisfied" .exactly 5 [.satisfied, .satisfied, .unresolved, .satisfied],
  .quantifier "forall-4-satisfied-satisfied-unresolved-not_satisfied" .forall [.satisfied, .satisfied, .unresolved, .notSatisfied]
]

def vectorChunk59 : List Vector := [
  .quantifier "exists-4-satisfied-satisfied-unresolved-not_satisfied" .exists [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-0-4-satisfied-satisfied-unresolved-not_satisfied" .atLeast 0 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-1-4-satisfied-satisfied-unresolved-not_satisfied" .atLeast 1 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-2-4-satisfied-satisfied-unresolved-not_satisfied" .atLeast 2 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-3-4-satisfied-satisfied-unresolved-not_satisfied" .atLeast 3 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-4-4-satisfied-satisfied-unresolved-not_satisfied" .atLeast 4 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-5-4-satisfied-satisfied-unresolved-not_satisfied" .atLeast 5 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-0-4-satisfied-satisfied-unresolved-not_satisfied" .atMost 0 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-1-4-satisfied-satisfied-unresolved-not_satisfied" .atMost 1 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-2-4-satisfied-satisfied-unresolved-not_satisfied" .atMost 2 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-3-4-satisfied-satisfied-unresolved-not_satisfied" .atMost 3 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-4-4-satisfied-satisfied-unresolved-not_satisfied" .atMost 4 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-5-4-satisfied-satisfied-unresolved-not_satisfied" .atMost 5 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-0-4-satisfied-satisfied-unresolved-not_satisfied" .exactly 0 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-1-4-satisfied-satisfied-unresolved-not_satisfied" .exactly 1 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-2-4-satisfied-satisfied-unresolved-not_satisfied" .exactly 2 [.satisfied, .satisfied, .unresolved, .notSatisfied]
]

def vectorChunk60 : List Vector := [
  .cardinality "exactly-3-4-satisfied-satisfied-unresolved-not_satisfied" .exactly 3 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-4-4-satisfied-satisfied-unresolved-not_satisfied" .exactly 4 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-5-4-satisfied-satisfied-unresolved-not_satisfied" .exactly 5 [.satisfied, .satisfied, .unresolved, .notSatisfied],
  .quantifier "forall-4-satisfied-satisfied-unresolved-unresolved" .forall [.satisfied, .satisfied, .unresolved, .unresolved],
  .quantifier "exists-4-satisfied-satisfied-unresolved-unresolved" .exists [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-0-4-satisfied-satisfied-unresolved-unresolved" .atLeast 0 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-1-4-satisfied-satisfied-unresolved-unresolved" .atLeast 1 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-2-4-satisfied-satisfied-unresolved-unresolved" .atLeast 2 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-3-4-satisfied-satisfied-unresolved-unresolved" .atLeast 3 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-4-4-satisfied-satisfied-unresolved-unresolved" .atLeast 4 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-5-4-satisfied-satisfied-unresolved-unresolved" .atLeast 5 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-0-4-satisfied-satisfied-unresolved-unresolved" .atMost 0 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-1-4-satisfied-satisfied-unresolved-unresolved" .atMost 1 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-2-4-satisfied-satisfied-unresolved-unresolved" .atMost 2 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-3-4-satisfied-satisfied-unresolved-unresolved" .atMost 3 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-4-4-satisfied-satisfied-unresolved-unresolved" .atMost 4 [.satisfied, .satisfied, .unresolved, .unresolved]
]

def vectorChunk61 : List Vector := [
  .cardinality "at-most-5-4-satisfied-satisfied-unresolved-unresolved" .atMost 5 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-0-4-satisfied-satisfied-unresolved-unresolved" .exactly 0 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-1-4-satisfied-satisfied-unresolved-unresolved" .exactly 1 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-2-4-satisfied-satisfied-unresolved-unresolved" .exactly 2 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-3-4-satisfied-satisfied-unresolved-unresolved" .exactly 3 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-4-4-satisfied-satisfied-unresolved-unresolved" .exactly 4 [.satisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-5-4-satisfied-satisfied-unresolved-unresolved" .exactly 5 [.satisfied, .satisfied, .unresolved, .unresolved],
  .quantifier "forall-4-satisfied-not_satisfied-satisfied-satisfied" .forall [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .quantifier "exists-4-satisfied-not_satisfied-satisfied-satisfied" .exists [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-0-4-satisfied-not_satisfied-satisfied-satisfied" .atLeast 0 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-1-4-satisfied-not_satisfied-satisfied-satisfied" .atLeast 1 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-2-4-satisfied-not_satisfied-satisfied-satisfied" .atLeast 2 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-3-4-satisfied-not_satisfied-satisfied-satisfied" .atLeast 3 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-4-4-satisfied-not_satisfied-satisfied-satisfied" .atLeast 4 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-5-4-satisfied-not_satisfied-satisfied-satisfied" .atLeast 5 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-0-4-satisfied-not_satisfied-satisfied-satisfied" .atMost 0 [.satisfied, .notSatisfied, .satisfied, .satisfied]
]

def vectorChunk62 : List Vector := [
  .cardinality "at-most-1-4-satisfied-not_satisfied-satisfied-satisfied" .atMost 1 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-2-4-satisfied-not_satisfied-satisfied-satisfied" .atMost 2 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-3-4-satisfied-not_satisfied-satisfied-satisfied" .atMost 3 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-4-4-satisfied-not_satisfied-satisfied-satisfied" .atMost 4 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-5-4-satisfied-not_satisfied-satisfied-satisfied" .atMost 5 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-0-4-satisfied-not_satisfied-satisfied-satisfied" .exactly 0 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-1-4-satisfied-not_satisfied-satisfied-satisfied" .exactly 1 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-2-4-satisfied-not_satisfied-satisfied-satisfied" .exactly 2 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-3-4-satisfied-not_satisfied-satisfied-satisfied" .exactly 3 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-4-4-satisfied-not_satisfied-satisfied-satisfied" .exactly 4 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-5-4-satisfied-not_satisfied-satisfied-satisfied" .exactly 5 [.satisfied, .notSatisfied, .satisfied, .satisfied],
  .quantifier "forall-4-satisfied-not_satisfied-satisfied-not_satisfied" .forall [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .quantifier "exists-4-satisfied-not_satisfied-satisfied-not_satisfied" .exists [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-0-4-satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 0 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-1-4-satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 1 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-2-4-satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 2 [.satisfied, .notSatisfied, .satisfied, .notSatisfied]
]

def vectorChunk63 : List Vector := [
  .cardinality "at-least-3-4-satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 3 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-4-4-satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 4 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-5-4-satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 5 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-0-4-satisfied-not_satisfied-satisfied-not_satisfied" .atMost 0 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-1-4-satisfied-not_satisfied-satisfied-not_satisfied" .atMost 1 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-2-4-satisfied-not_satisfied-satisfied-not_satisfied" .atMost 2 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-3-4-satisfied-not_satisfied-satisfied-not_satisfied" .atMost 3 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-4-4-satisfied-not_satisfied-satisfied-not_satisfied" .atMost 4 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-5-4-satisfied-not_satisfied-satisfied-not_satisfied" .atMost 5 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-0-4-satisfied-not_satisfied-satisfied-not_satisfied" .exactly 0 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-1-4-satisfied-not_satisfied-satisfied-not_satisfied" .exactly 1 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-2-4-satisfied-not_satisfied-satisfied-not_satisfied" .exactly 2 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-3-4-satisfied-not_satisfied-satisfied-not_satisfied" .exactly 3 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-4-4-satisfied-not_satisfied-satisfied-not_satisfied" .exactly 4 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-5-4-satisfied-not_satisfied-satisfied-not_satisfied" .exactly 5 [.satisfied, .notSatisfied, .satisfied, .notSatisfied],
  .quantifier "forall-4-satisfied-not_satisfied-satisfied-unresolved" .forall [.satisfied, .notSatisfied, .satisfied, .unresolved]
]

def vectorChunk64 : List Vector := [
  .quantifier "exists-4-satisfied-not_satisfied-satisfied-unresolved" .exists [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-0-4-satisfied-not_satisfied-satisfied-unresolved" .atLeast 0 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-1-4-satisfied-not_satisfied-satisfied-unresolved" .atLeast 1 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-2-4-satisfied-not_satisfied-satisfied-unresolved" .atLeast 2 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-3-4-satisfied-not_satisfied-satisfied-unresolved" .atLeast 3 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-4-4-satisfied-not_satisfied-satisfied-unresolved" .atLeast 4 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-5-4-satisfied-not_satisfied-satisfied-unresolved" .atLeast 5 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-0-4-satisfied-not_satisfied-satisfied-unresolved" .atMost 0 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-1-4-satisfied-not_satisfied-satisfied-unresolved" .atMost 1 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-2-4-satisfied-not_satisfied-satisfied-unresolved" .atMost 2 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-3-4-satisfied-not_satisfied-satisfied-unresolved" .atMost 3 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-4-4-satisfied-not_satisfied-satisfied-unresolved" .atMost 4 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-5-4-satisfied-not_satisfied-satisfied-unresolved" .atMost 5 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-0-4-satisfied-not_satisfied-satisfied-unresolved" .exactly 0 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-1-4-satisfied-not_satisfied-satisfied-unresolved" .exactly 1 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-2-4-satisfied-not_satisfied-satisfied-unresolved" .exactly 2 [.satisfied, .notSatisfied, .satisfied, .unresolved]
]

def vectorChunk65 : List Vector := [
  .cardinality "exactly-3-4-satisfied-not_satisfied-satisfied-unresolved" .exactly 3 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-4-4-satisfied-not_satisfied-satisfied-unresolved" .exactly 4 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-5-4-satisfied-not_satisfied-satisfied-unresolved" .exactly 5 [.satisfied, .notSatisfied, .satisfied, .unresolved],
  .quantifier "forall-4-satisfied-not_satisfied-not_satisfied-satisfied" .forall [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .quantifier "exists-4-satisfied-not_satisfied-not_satisfied-satisfied" .exists [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-0-4-satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 0 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-1-4-satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 1 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-2-4-satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 2 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-3-4-satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 3 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-4-4-satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 4 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-5-4-satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 5 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-0-4-satisfied-not_satisfied-not_satisfied-satisfied" .atMost 0 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-1-4-satisfied-not_satisfied-not_satisfied-satisfied" .atMost 1 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-2-4-satisfied-not_satisfied-not_satisfied-satisfied" .atMost 2 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-3-4-satisfied-not_satisfied-not_satisfied-satisfied" .atMost 3 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-4-4-satisfied-not_satisfied-not_satisfied-satisfied" .atMost 4 [.satisfied, .notSatisfied, .notSatisfied, .satisfied]
]

def vectorChunk66 : List Vector := [
  .cardinality "at-most-5-4-satisfied-not_satisfied-not_satisfied-satisfied" .atMost 5 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-0-4-satisfied-not_satisfied-not_satisfied-satisfied" .exactly 0 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-1-4-satisfied-not_satisfied-not_satisfied-satisfied" .exactly 1 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-2-4-satisfied-not_satisfied-not_satisfied-satisfied" .exactly 2 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-3-4-satisfied-not_satisfied-not_satisfied-satisfied" .exactly 3 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-4-4-satisfied-not_satisfied-not_satisfied-satisfied" .exactly 4 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-5-4-satisfied-not_satisfied-not_satisfied-satisfied" .exactly 5 [.satisfied, .notSatisfied, .notSatisfied, .satisfied],
  .quantifier "forall-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .forall [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .quantifier "exists-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .exists [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 0 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 1 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 2 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-3-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 3 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 4 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 5 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 0 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk67 : List Vector := [
  .cardinality "at-most-1-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 1 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 2 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 3 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 4 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-5-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 5 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 0 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 1 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 2 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-3-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 3 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 4 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-4-satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 5 [.satisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .quantifier "forall-4-satisfied-not_satisfied-not_satisfied-unresolved" .forall [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .quantifier "exists-4-satisfied-not_satisfied-not_satisfied-unresolved" .exists [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-0-4-satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 0 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-1-4-satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 1 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-2-4-satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 2 [.satisfied, .notSatisfied, .notSatisfied, .unresolved]
]

def vectorChunk68 : List Vector := [
  .cardinality "at-least-3-4-satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 3 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-4-4-satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 4 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-5-4-satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 5 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-0-4-satisfied-not_satisfied-not_satisfied-unresolved" .atMost 0 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-1-4-satisfied-not_satisfied-not_satisfied-unresolved" .atMost 1 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-2-4-satisfied-not_satisfied-not_satisfied-unresolved" .atMost 2 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-3-4-satisfied-not_satisfied-not_satisfied-unresolved" .atMost 3 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-4-4-satisfied-not_satisfied-not_satisfied-unresolved" .atMost 4 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-5-4-satisfied-not_satisfied-not_satisfied-unresolved" .atMost 5 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-0-4-satisfied-not_satisfied-not_satisfied-unresolved" .exactly 0 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-1-4-satisfied-not_satisfied-not_satisfied-unresolved" .exactly 1 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-2-4-satisfied-not_satisfied-not_satisfied-unresolved" .exactly 2 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-3-4-satisfied-not_satisfied-not_satisfied-unresolved" .exactly 3 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-4-4-satisfied-not_satisfied-not_satisfied-unresolved" .exactly 4 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-5-4-satisfied-not_satisfied-not_satisfied-unresolved" .exactly 5 [.satisfied, .notSatisfied, .notSatisfied, .unresolved],
  .quantifier "forall-4-satisfied-not_satisfied-unresolved-satisfied" .forall [.satisfied, .notSatisfied, .unresolved, .satisfied]
]

def vectorChunk69 : List Vector := [
  .quantifier "exists-4-satisfied-not_satisfied-unresolved-satisfied" .exists [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-0-4-satisfied-not_satisfied-unresolved-satisfied" .atLeast 0 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-1-4-satisfied-not_satisfied-unresolved-satisfied" .atLeast 1 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-2-4-satisfied-not_satisfied-unresolved-satisfied" .atLeast 2 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-3-4-satisfied-not_satisfied-unresolved-satisfied" .atLeast 3 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-4-4-satisfied-not_satisfied-unresolved-satisfied" .atLeast 4 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-5-4-satisfied-not_satisfied-unresolved-satisfied" .atLeast 5 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-0-4-satisfied-not_satisfied-unresolved-satisfied" .atMost 0 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-1-4-satisfied-not_satisfied-unresolved-satisfied" .atMost 1 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-2-4-satisfied-not_satisfied-unresolved-satisfied" .atMost 2 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-3-4-satisfied-not_satisfied-unresolved-satisfied" .atMost 3 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-4-4-satisfied-not_satisfied-unresolved-satisfied" .atMost 4 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-5-4-satisfied-not_satisfied-unresolved-satisfied" .atMost 5 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-0-4-satisfied-not_satisfied-unresolved-satisfied" .exactly 0 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-1-4-satisfied-not_satisfied-unresolved-satisfied" .exactly 1 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-2-4-satisfied-not_satisfied-unresolved-satisfied" .exactly 2 [.satisfied, .notSatisfied, .unresolved, .satisfied]
]

def vectorChunk70 : List Vector := [
  .cardinality "exactly-3-4-satisfied-not_satisfied-unresolved-satisfied" .exactly 3 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-4-4-satisfied-not_satisfied-unresolved-satisfied" .exactly 4 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-5-4-satisfied-not_satisfied-unresolved-satisfied" .exactly 5 [.satisfied, .notSatisfied, .unresolved, .satisfied],
  .quantifier "forall-4-satisfied-not_satisfied-unresolved-not_satisfied" .forall [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .quantifier "exists-4-satisfied-not_satisfied-unresolved-not_satisfied" .exists [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-0-4-satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 0 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-1-4-satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 1 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-2-4-satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 2 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-3-4-satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 3 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-4-4-satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 4 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-5-4-satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 5 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-0-4-satisfied-not_satisfied-unresolved-not_satisfied" .atMost 0 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-1-4-satisfied-not_satisfied-unresolved-not_satisfied" .atMost 1 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-2-4-satisfied-not_satisfied-unresolved-not_satisfied" .atMost 2 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-3-4-satisfied-not_satisfied-unresolved-not_satisfied" .atMost 3 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-4-4-satisfied-not_satisfied-unresolved-not_satisfied" .atMost 4 [.satisfied, .notSatisfied, .unresolved, .notSatisfied]
]

def vectorChunk71 : List Vector := [
  .cardinality "at-most-5-4-satisfied-not_satisfied-unresolved-not_satisfied" .atMost 5 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-0-4-satisfied-not_satisfied-unresolved-not_satisfied" .exactly 0 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-1-4-satisfied-not_satisfied-unresolved-not_satisfied" .exactly 1 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-2-4-satisfied-not_satisfied-unresolved-not_satisfied" .exactly 2 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-3-4-satisfied-not_satisfied-unresolved-not_satisfied" .exactly 3 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-4-4-satisfied-not_satisfied-unresolved-not_satisfied" .exactly 4 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-5-4-satisfied-not_satisfied-unresolved-not_satisfied" .exactly 5 [.satisfied, .notSatisfied, .unresolved, .notSatisfied],
  .quantifier "forall-4-satisfied-not_satisfied-unresolved-unresolved" .forall [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .quantifier "exists-4-satisfied-not_satisfied-unresolved-unresolved" .exists [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-0-4-satisfied-not_satisfied-unresolved-unresolved" .atLeast 0 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-1-4-satisfied-not_satisfied-unresolved-unresolved" .atLeast 1 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-2-4-satisfied-not_satisfied-unresolved-unresolved" .atLeast 2 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-3-4-satisfied-not_satisfied-unresolved-unresolved" .atLeast 3 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-4-4-satisfied-not_satisfied-unresolved-unresolved" .atLeast 4 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-5-4-satisfied-not_satisfied-unresolved-unresolved" .atLeast 5 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-0-4-satisfied-not_satisfied-unresolved-unresolved" .atMost 0 [.satisfied, .notSatisfied, .unresolved, .unresolved]
]

def vectorChunk72 : List Vector := [
  .cardinality "at-most-1-4-satisfied-not_satisfied-unresolved-unresolved" .atMost 1 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-2-4-satisfied-not_satisfied-unresolved-unresolved" .atMost 2 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-3-4-satisfied-not_satisfied-unresolved-unresolved" .atMost 3 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-4-4-satisfied-not_satisfied-unresolved-unresolved" .atMost 4 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-5-4-satisfied-not_satisfied-unresolved-unresolved" .atMost 5 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-0-4-satisfied-not_satisfied-unresolved-unresolved" .exactly 0 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-1-4-satisfied-not_satisfied-unresolved-unresolved" .exactly 1 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-2-4-satisfied-not_satisfied-unresolved-unresolved" .exactly 2 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-3-4-satisfied-not_satisfied-unresolved-unresolved" .exactly 3 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-4-4-satisfied-not_satisfied-unresolved-unresolved" .exactly 4 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-5-4-satisfied-not_satisfied-unresolved-unresolved" .exactly 5 [.satisfied, .notSatisfied, .unresolved, .unresolved],
  .quantifier "forall-4-satisfied-unresolved-satisfied-satisfied" .forall [.satisfied, .unresolved, .satisfied, .satisfied],
  .quantifier "exists-4-satisfied-unresolved-satisfied-satisfied" .exists [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-0-4-satisfied-unresolved-satisfied-satisfied" .atLeast 0 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-1-4-satisfied-unresolved-satisfied-satisfied" .atLeast 1 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-2-4-satisfied-unresolved-satisfied-satisfied" .atLeast 2 [.satisfied, .unresolved, .satisfied, .satisfied]
]

def vectorChunk73 : List Vector := [
  .cardinality "at-least-3-4-satisfied-unresolved-satisfied-satisfied" .atLeast 3 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-4-4-satisfied-unresolved-satisfied-satisfied" .atLeast 4 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-5-4-satisfied-unresolved-satisfied-satisfied" .atLeast 5 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-0-4-satisfied-unresolved-satisfied-satisfied" .atMost 0 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-1-4-satisfied-unresolved-satisfied-satisfied" .atMost 1 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-2-4-satisfied-unresolved-satisfied-satisfied" .atMost 2 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-3-4-satisfied-unresolved-satisfied-satisfied" .atMost 3 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-4-4-satisfied-unresolved-satisfied-satisfied" .atMost 4 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-5-4-satisfied-unresolved-satisfied-satisfied" .atMost 5 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-0-4-satisfied-unresolved-satisfied-satisfied" .exactly 0 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-1-4-satisfied-unresolved-satisfied-satisfied" .exactly 1 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-2-4-satisfied-unresolved-satisfied-satisfied" .exactly 2 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-3-4-satisfied-unresolved-satisfied-satisfied" .exactly 3 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-4-4-satisfied-unresolved-satisfied-satisfied" .exactly 4 [.satisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-5-4-satisfied-unresolved-satisfied-satisfied" .exactly 5 [.satisfied, .unresolved, .satisfied, .satisfied],
  .quantifier "forall-4-satisfied-unresolved-satisfied-not_satisfied" .forall [.satisfied, .unresolved, .satisfied, .notSatisfied]
]

def vectorChunk74 : List Vector := [
  .quantifier "exists-4-satisfied-unresolved-satisfied-not_satisfied" .exists [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-0-4-satisfied-unresolved-satisfied-not_satisfied" .atLeast 0 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-1-4-satisfied-unresolved-satisfied-not_satisfied" .atLeast 1 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-2-4-satisfied-unresolved-satisfied-not_satisfied" .atLeast 2 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-3-4-satisfied-unresolved-satisfied-not_satisfied" .atLeast 3 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-4-4-satisfied-unresolved-satisfied-not_satisfied" .atLeast 4 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-5-4-satisfied-unresolved-satisfied-not_satisfied" .atLeast 5 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-0-4-satisfied-unresolved-satisfied-not_satisfied" .atMost 0 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-1-4-satisfied-unresolved-satisfied-not_satisfied" .atMost 1 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-2-4-satisfied-unresolved-satisfied-not_satisfied" .atMost 2 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-3-4-satisfied-unresolved-satisfied-not_satisfied" .atMost 3 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-4-4-satisfied-unresolved-satisfied-not_satisfied" .atMost 4 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-5-4-satisfied-unresolved-satisfied-not_satisfied" .atMost 5 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-0-4-satisfied-unresolved-satisfied-not_satisfied" .exactly 0 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-1-4-satisfied-unresolved-satisfied-not_satisfied" .exactly 1 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-2-4-satisfied-unresolved-satisfied-not_satisfied" .exactly 2 [.satisfied, .unresolved, .satisfied, .notSatisfied]
]

def vectorChunk75 : List Vector := [
  .cardinality "exactly-3-4-satisfied-unresolved-satisfied-not_satisfied" .exactly 3 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-4-4-satisfied-unresolved-satisfied-not_satisfied" .exactly 4 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-5-4-satisfied-unresolved-satisfied-not_satisfied" .exactly 5 [.satisfied, .unresolved, .satisfied, .notSatisfied],
  .quantifier "forall-4-satisfied-unresolved-satisfied-unresolved" .forall [.satisfied, .unresolved, .satisfied, .unresolved],
  .quantifier "exists-4-satisfied-unresolved-satisfied-unresolved" .exists [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-0-4-satisfied-unresolved-satisfied-unresolved" .atLeast 0 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-1-4-satisfied-unresolved-satisfied-unresolved" .atLeast 1 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-2-4-satisfied-unresolved-satisfied-unresolved" .atLeast 2 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-3-4-satisfied-unresolved-satisfied-unresolved" .atLeast 3 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-4-4-satisfied-unresolved-satisfied-unresolved" .atLeast 4 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-5-4-satisfied-unresolved-satisfied-unresolved" .atLeast 5 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-0-4-satisfied-unresolved-satisfied-unresolved" .atMost 0 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-1-4-satisfied-unresolved-satisfied-unresolved" .atMost 1 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-2-4-satisfied-unresolved-satisfied-unresolved" .atMost 2 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-3-4-satisfied-unresolved-satisfied-unresolved" .atMost 3 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-4-4-satisfied-unresolved-satisfied-unresolved" .atMost 4 [.satisfied, .unresolved, .satisfied, .unresolved]
]

def vectorChunk76 : List Vector := [
  .cardinality "at-most-5-4-satisfied-unresolved-satisfied-unresolved" .atMost 5 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-0-4-satisfied-unresolved-satisfied-unresolved" .exactly 0 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-1-4-satisfied-unresolved-satisfied-unresolved" .exactly 1 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-2-4-satisfied-unresolved-satisfied-unresolved" .exactly 2 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-3-4-satisfied-unresolved-satisfied-unresolved" .exactly 3 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-4-4-satisfied-unresolved-satisfied-unresolved" .exactly 4 [.satisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-5-4-satisfied-unresolved-satisfied-unresolved" .exactly 5 [.satisfied, .unresolved, .satisfied, .unresolved],
  .quantifier "forall-4-satisfied-unresolved-not_satisfied-satisfied" .forall [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .quantifier "exists-4-satisfied-unresolved-not_satisfied-satisfied" .exists [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-0-4-satisfied-unresolved-not_satisfied-satisfied" .atLeast 0 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-1-4-satisfied-unresolved-not_satisfied-satisfied" .atLeast 1 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-2-4-satisfied-unresolved-not_satisfied-satisfied" .atLeast 2 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-3-4-satisfied-unresolved-not_satisfied-satisfied" .atLeast 3 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-4-4-satisfied-unresolved-not_satisfied-satisfied" .atLeast 4 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-5-4-satisfied-unresolved-not_satisfied-satisfied" .atLeast 5 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-0-4-satisfied-unresolved-not_satisfied-satisfied" .atMost 0 [.satisfied, .unresolved, .notSatisfied, .satisfied]
]

def vectorChunk77 : List Vector := [
  .cardinality "at-most-1-4-satisfied-unresolved-not_satisfied-satisfied" .atMost 1 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-2-4-satisfied-unresolved-not_satisfied-satisfied" .atMost 2 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-3-4-satisfied-unresolved-not_satisfied-satisfied" .atMost 3 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-4-4-satisfied-unresolved-not_satisfied-satisfied" .atMost 4 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-5-4-satisfied-unresolved-not_satisfied-satisfied" .atMost 5 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-0-4-satisfied-unresolved-not_satisfied-satisfied" .exactly 0 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-1-4-satisfied-unresolved-not_satisfied-satisfied" .exactly 1 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-2-4-satisfied-unresolved-not_satisfied-satisfied" .exactly 2 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-3-4-satisfied-unresolved-not_satisfied-satisfied" .exactly 3 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-4-4-satisfied-unresolved-not_satisfied-satisfied" .exactly 4 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-5-4-satisfied-unresolved-not_satisfied-satisfied" .exactly 5 [.satisfied, .unresolved, .notSatisfied, .satisfied],
  .quantifier "forall-4-satisfied-unresolved-not_satisfied-not_satisfied" .forall [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .quantifier "exists-4-satisfied-unresolved-not_satisfied-not_satisfied" .exists [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-4-satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 0 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-4-satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 1 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-4-satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 2 [.satisfied, .unresolved, .notSatisfied, .notSatisfied]
]

def vectorChunk78 : List Vector := [
  .cardinality "at-least-3-4-satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 3 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-4-satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 4 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-4-satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 5 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-4-satisfied-unresolved-not_satisfied-not_satisfied" .atMost 0 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-1-4-satisfied-unresolved-not_satisfied-not_satisfied" .atMost 1 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-4-satisfied-unresolved-not_satisfied-not_satisfied" .atMost 2 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-4-satisfied-unresolved-not_satisfied-not_satisfied" .atMost 3 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-4-satisfied-unresolved-not_satisfied-not_satisfied" .atMost 4 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-5-4-satisfied-unresolved-not_satisfied-not_satisfied" .atMost 5 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-4-satisfied-unresolved-not_satisfied-not_satisfied" .exactly 0 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-4-satisfied-unresolved-not_satisfied-not_satisfied" .exactly 1 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-4-satisfied-unresolved-not_satisfied-not_satisfied" .exactly 2 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-3-4-satisfied-unresolved-not_satisfied-not_satisfied" .exactly 3 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-4-satisfied-unresolved-not_satisfied-not_satisfied" .exactly 4 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-4-satisfied-unresolved-not_satisfied-not_satisfied" .exactly 5 [.satisfied, .unresolved, .notSatisfied, .notSatisfied],
  .quantifier "forall-4-satisfied-unresolved-not_satisfied-unresolved" .forall [.satisfied, .unresolved, .notSatisfied, .unresolved]
]

def vectorChunk79 : List Vector := [
  .quantifier "exists-4-satisfied-unresolved-not_satisfied-unresolved" .exists [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-0-4-satisfied-unresolved-not_satisfied-unresolved" .atLeast 0 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-1-4-satisfied-unresolved-not_satisfied-unresolved" .atLeast 1 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-2-4-satisfied-unresolved-not_satisfied-unresolved" .atLeast 2 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-3-4-satisfied-unresolved-not_satisfied-unresolved" .atLeast 3 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-4-4-satisfied-unresolved-not_satisfied-unresolved" .atLeast 4 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-5-4-satisfied-unresolved-not_satisfied-unresolved" .atLeast 5 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-0-4-satisfied-unresolved-not_satisfied-unresolved" .atMost 0 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-1-4-satisfied-unresolved-not_satisfied-unresolved" .atMost 1 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-2-4-satisfied-unresolved-not_satisfied-unresolved" .atMost 2 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-3-4-satisfied-unresolved-not_satisfied-unresolved" .atMost 3 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-4-4-satisfied-unresolved-not_satisfied-unresolved" .atMost 4 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-5-4-satisfied-unresolved-not_satisfied-unresolved" .atMost 5 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-0-4-satisfied-unresolved-not_satisfied-unresolved" .exactly 0 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-1-4-satisfied-unresolved-not_satisfied-unresolved" .exactly 1 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-2-4-satisfied-unresolved-not_satisfied-unresolved" .exactly 2 [.satisfied, .unresolved, .notSatisfied, .unresolved]
]

def vectorChunk80 : List Vector := [
  .cardinality "exactly-3-4-satisfied-unresolved-not_satisfied-unresolved" .exactly 3 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-4-4-satisfied-unresolved-not_satisfied-unresolved" .exactly 4 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-5-4-satisfied-unresolved-not_satisfied-unresolved" .exactly 5 [.satisfied, .unresolved, .notSatisfied, .unresolved],
  .quantifier "forall-4-satisfied-unresolved-unresolved-satisfied" .forall [.satisfied, .unresolved, .unresolved, .satisfied],
  .quantifier "exists-4-satisfied-unresolved-unresolved-satisfied" .exists [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-0-4-satisfied-unresolved-unresolved-satisfied" .atLeast 0 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-1-4-satisfied-unresolved-unresolved-satisfied" .atLeast 1 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-2-4-satisfied-unresolved-unresolved-satisfied" .atLeast 2 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-3-4-satisfied-unresolved-unresolved-satisfied" .atLeast 3 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-4-4-satisfied-unresolved-unresolved-satisfied" .atLeast 4 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-5-4-satisfied-unresolved-unresolved-satisfied" .atLeast 5 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-0-4-satisfied-unresolved-unresolved-satisfied" .atMost 0 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-1-4-satisfied-unresolved-unresolved-satisfied" .atMost 1 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-2-4-satisfied-unresolved-unresolved-satisfied" .atMost 2 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-3-4-satisfied-unresolved-unresolved-satisfied" .atMost 3 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-4-4-satisfied-unresolved-unresolved-satisfied" .atMost 4 [.satisfied, .unresolved, .unresolved, .satisfied]
]

def vectorChunk81 : List Vector := [
  .cardinality "at-most-5-4-satisfied-unresolved-unresolved-satisfied" .atMost 5 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-0-4-satisfied-unresolved-unresolved-satisfied" .exactly 0 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-1-4-satisfied-unresolved-unresolved-satisfied" .exactly 1 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-2-4-satisfied-unresolved-unresolved-satisfied" .exactly 2 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-3-4-satisfied-unresolved-unresolved-satisfied" .exactly 3 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-4-4-satisfied-unresolved-unresolved-satisfied" .exactly 4 [.satisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-5-4-satisfied-unresolved-unresolved-satisfied" .exactly 5 [.satisfied, .unresolved, .unresolved, .satisfied],
  .quantifier "forall-4-satisfied-unresolved-unresolved-not_satisfied" .forall [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .quantifier "exists-4-satisfied-unresolved-unresolved-not_satisfied" .exists [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-0-4-satisfied-unresolved-unresolved-not_satisfied" .atLeast 0 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-1-4-satisfied-unresolved-unresolved-not_satisfied" .atLeast 1 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-2-4-satisfied-unresolved-unresolved-not_satisfied" .atLeast 2 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-3-4-satisfied-unresolved-unresolved-not_satisfied" .atLeast 3 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-4-4-satisfied-unresolved-unresolved-not_satisfied" .atLeast 4 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-5-4-satisfied-unresolved-unresolved-not_satisfied" .atLeast 5 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-0-4-satisfied-unresolved-unresolved-not_satisfied" .atMost 0 [.satisfied, .unresolved, .unresolved, .notSatisfied]
]

def vectorChunk82 : List Vector := [
  .cardinality "at-most-1-4-satisfied-unresolved-unresolved-not_satisfied" .atMost 1 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-2-4-satisfied-unresolved-unresolved-not_satisfied" .atMost 2 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-3-4-satisfied-unresolved-unresolved-not_satisfied" .atMost 3 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-4-4-satisfied-unresolved-unresolved-not_satisfied" .atMost 4 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-5-4-satisfied-unresolved-unresolved-not_satisfied" .atMost 5 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-0-4-satisfied-unresolved-unresolved-not_satisfied" .exactly 0 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-1-4-satisfied-unresolved-unresolved-not_satisfied" .exactly 1 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-2-4-satisfied-unresolved-unresolved-not_satisfied" .exactly 2 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-3-4-satisfied-unresolved-unresolved-not_satisfied" .exactly 3 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-4-4-satisfied-unresolved-unresolved-not_satisfied" .exactly 4 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-5-4-satisfied-unresolved-unresolved-not_satisfied" .exactly 5 [.satisfied, .unresolved, .unresolved, .notSatisfied],
  .quantifier "forall-4-satisfied-unresolved-unresolved-unresolved" .forall [.satisfied, .unresolved, .unresolved, .unresolved],
  .quantifier "exists-4-satisfied-unresolved-unresolved-unresolved" .exists [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-0-4-satisfied-unresolved-unresolved-unresolved" .atLeast 0 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-1-4-satisfied-unresolved-unresolved-unresolved" .atLeast 1 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-2-4-satisfied-unresolved-unresolved-unresolved" .atLeast 2 [.satisfied, .unresolved, .unresolved, .unresolved]
]

def vectorChunk83 : List Vector := [
  .cardinality "at-least-3-4-satisfied-unresolved-unresolved-unresolved" .atLeast 3 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-4-4-satisfied-unresolved-unresolved-unresolved" .atLeast 4 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-5-4-satisfied-unresolved-unresolved-unresolved" .atLeast 5 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-0-4-satisfied-unresolved-unresolved-unresolved" .atMost 0 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-1-4-satisfied-unresolved-unresolved-unresolved" .atMost 1 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-2-4-satisfied-unresolved-unresolved-unresolved" .atMost 2 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-3-4-satisfied-unresolved-unresolved-unresolved" .atMost 3 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-4-4-satisfied-unresolved-unresolved-unresolved" .atMost 4 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-5-4-satisfied-unresolved-unresolved-unresolved" .atMost 5 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-0-4-satisfied-unresolved-unresolved-unresolved" .exactly 0 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-1-4-satisfied-unresolved-unresolved-unresolved" .exactly 1 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-2-4-satisfied-unresolved-unresolved-unresolved" .exactly 2 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-3-4-satisfied-unresolved-unresolved-unresolved" .exactly 3 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-4-4-satisfied-unresolved-unresolved-unresolved" .exactly 4 [.satisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-5-4-satisfied-unresolved-unresolved-unresolved" .exactly 5 [.satisfied, .unresolved, .unresolved, .unresolved],
  .quantifier "forall-4-not_satisfied-satisfied-satisfied-satisfied" .forall [.notSatisfied, .satisfied, .satisfied, .satisfied]
]

def vectorChunk84 : List Vector := [
  .quantifier "exists-4-not_satisfied-satisfied-satisfied-satisfied" .exists [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-0-4-not_satisfied-satisfied-satisfied-satisfied" .atLeast 0 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-1-4-not_satisfied-satisfied-satisfied-satisfied" .atLeast 1 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-2-4-not_satisfied-satisfied-satisfied-satisfied" .atLeast 2 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-3-4-not_satisfied-satisfied-satisfied-satisfied" .atLeast 3 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-4-4-not_satisfied-satisfied-satisfied-satisfied" .atLeast 4 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-5-4-not_satisfied-satisfied-satisfied-satisfied" .atLeast 5 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-0-4-not_satisfied-satisfied-satisfied-satisfied" .atMost 0 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-1-4-not_satisfied-satisfied-satisfied-satisfied" .atMost 1 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-2-4-not_satisfied-satisfied-satisfied-satisfied" .atMost 2 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-3-4-not_satisfied-satisfied-satisfied-satisfied" .atMost 3 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-4-4-not_satisfied-satisfied-satisfied-satisfied" .atMost 4 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-5-4-not_satisfied-satisfied-satisfied-satisfied" .atMost 5 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-0-4-not_satisfied-satisfied-satisfied-satisfied" .exactly 0 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-1-4-not_satisfied-satisfied-satisfied-satisfied" .exactly 1 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-2-4-not_satisfied-satisfied-satisfied-satisfied" .exactly 2 [.notSatisfied, .satisfied, .satisfied, .satisfied]
]

def vectorChunk85 : List Vector := [
  .cardinality "exactly-3-4-not_satisfied-satisfied-satisfied-satisfied" .exactly 3 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-4-4-not_satisfied-satisfied-satisfied-satisfied" .exactly 4 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-5-4-not_satisfied-satisfied-satisfied-satisfied" .exactly 5 [.notSatisfied, .satisfied, .satisfied, .satisfied],
  .quantifier "forall-4-not_satisfied-satisfied-satisfied-not_satisfied" .forall [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .quantifier "exists-4-not_satisfied-satisfied-satisfied-not_satisfied" .exists [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-0-4-not_satisfied-satisfied-satisfied-not_satisfied" .atLeast 0 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-1-4-not_satisfied-satisfied-satisfied-not_satisfied" .atLeast 1 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-2-4-not_satisfied-satisfied-satisfied-not_satisfied" .atLeast 2 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-3-4-not_satisfied-satisfied-satisfied-not_satisfied" .atLeast 3 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-4-4-not_satisfied-satisfied-satisfied-not_satisfied" .atLeast 4 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-5-4-not_satisfied-satisfied-satisfied-not_satisfied" .atLeast 5 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-0-4-not_satisfied-satisfied-satisfied-not_satisfied" .atMost 0 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-1-4-not_satisfied-satisfied-satisfied-not_satisfied" .atMost 1 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-2-4-not_satisfied-satisfied-satisfied-not_satisfied" .atMost 2 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-3-4-not_satisfied-satisfied-satisfied-not_satisfied" .atMost 3 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-4-4-not_satisfied-satisfied-satisfied-not_satisfied" .atMost 4 [.notSatisfied, .satisfied, .satisfied, .notSatisfied]
]

def vectorChunk86 : List Vector := [
  .cardinality "at-most-5-4-not_satisfied-satisfied-satisfied-not_satisfied" .atMost 5 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-0-4-not_satisfied-satisfied-satisfied-not_satisfied" .exactly 0 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-1-4-not_satisfied-satisfied-satisfied-not_satisfied" .exactly 1 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-2-4-not_satisfied-satisfied-satisfied-not_satisfied" .exactly 2 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-3-4-not_satisfied-satisfied-satisfied-not_satisfied" .exactly 3 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-4-4-not_satisfied-satisfied-satisfied-not_satisfied" .exactly 4 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-5-4-not_satisfied-satisfied-satisfied-not_satisfied" .exactly 5 [.notSatisfied, .satisfied, .satisfied, .notSatisfied],
  .quantifier "forall-4-not_satisfied-satisfied-satisfied-unresolved" .forall [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .quantifier "exists-4-not_satisfied-satisfied-satisfied-unresolved" .exists [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-0-4-not_satisfied-satisfied-satisfied-unresolved" .atLeast 0 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-1-4-not_satisfied-satisfied-satisfied-unresolved" .atLeast 1 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-2-4-not_satisfied-satisfied-satisfied-unresolved" .atLeast 2 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-3-4-not_satisfied-satisfied-satisfied-unresolved" .atLeast 3 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-4-4-not_satisfied-satisfied-satisfied-unresolved" .atLeast 4 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-5-4-not_satisfied-satisfied-satisfied-unresolved" .atLeast 5 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-0-4-not_satisfied-satisfied-satisfied-unresolved" .atMost 0 [.notSatisfied, .satisfied, .satisfied, .unresolved]
]

def vectorChunk87 : List Vector := [
  .cardinality "at-most-1-4-not_satisfied-satisfied-satisfied-unresolved" .atMost 1 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-2-4-not_satisfied-satisfied-satisfied-unresolved" .atMost 2 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-3-4-not_satisfied-satisfied-satisfied-unresolved" .atMost 3 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-4-4-not_satisfied-satisfied-satisfied-unresolved" .atMost 4 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-5-4-not_satisfied-satisfied-satisfied-unresolved" .atMost 5 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-0-4-not_satisfied-satisfied-satisfied-unresolved" .exactly 0 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-1-4-not_satisfied-satisfied-satisfied-unresolved" .exactly 1 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-2-4-not_satisfied-satisfied-satisfied-unresolved" .exactly 2 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-3-4-not_satisfied-satisfied-satisfied-unresolved" .exactly 3 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-4-4-not_satisfied-satisfied-satisfied-unresolved" .exactly 4 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-5-4-not_satisfied-satisfied-satisfied-unresolved" .exactly 5 [.notSatisfied, .satisfied, .satisfied, .unresolved],
  .quantifier "forall-4-not_satisfied-satisfied-not_satisfied-satisfied" .forall [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .quantifier "exists-4-not_satisfied-satisfied-not_satisfied-satisfied" .exists [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-0-4-not_satisfied-satisfied-not_satisfied-satisfied" .atLeast 0 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-1-4-not_satisfied-satisfied-not_satisfied-satisfied" .atLeast 1 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-2-4-not_satisfied-satisfied-not_satisfied-satisfied" .atLeast 2 [.notSatisfied, .satisfied, .notSatisfied, .satisfied]
]

def vectorChunk88 : List Vector := [
  .cardinality "at-least-3-4-not_satisfied-satisfied-not_satisfied-satisfied" .atLeast 3 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-4-4-not_satisfied-satisfied-not_satisfied-satisfied" .atLeast 4 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-5-4-not_satisfied-satisfied-not_satisfied-satisfied" .atLeast 5 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-0-4-not_satisfied-satisfied-not_satisfied-satisfied" .atMost 0 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-1-4-not_satisfied-satisfied-not_satisfied-satisfied" .atMost 1 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-2-4-not_satisfied-satisfied-not_satisfied-satisfied" .atMost 2 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-3-4-not_satisfied-satisfied-not_satisfied-satisfied" .atMost 3 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-4-4-not_satisfied-satisfied-not_satisfied-satisfied" .atMost 4 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-5-4-not_satisfied-satisfied-not_satisfied-satisfied" .atMost 5 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-0-4-not_satisfied-satisfied-not_satisfied-satisfied" .exactly 0 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-1-4-not_satisfied-satisfied-not_satisfied-satisfied" .exactly 1 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-2-4-not_satisfied-satisfied-not_satisfied-satisfied" .exactly 2 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-3-4-not_satisfied-satisfied-not_satisfied-satisfied" .exactly 3 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-4-4-not_satisfied-satisfied-not_satisfied-satisfied" .exactly 4 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-5-4-not_satisfied-satisfied-not_satisfied-satisfied" .exactly 5 [.notSatisfied, .satisfied, .notSatisfied, .satisfied],
  .quantifier "forall-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .forall [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk89 : List Vector := [
  .quantifier "exists-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .exists [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 0 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 1 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 2 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-3-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 3 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 4 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atLeast 5 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atMost 0 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-1-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atMost 1 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atMost 2 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atMost 3 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atMost 4 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-5-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .atMost 5 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .exactly 0 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .exactly 1 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .exactly 2 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk90 : List Vector := [
  .cardinality "exactly-3-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .exactly 3 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .exactly 4 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-4-not_satisfied-satisfied-not_satisfied-not_satisfied" .exactly 5 [.notSatisfied, .satisfied, .notSatisfied, .notSatisfied],
  .quantifier "forall-4-not_satisfied-satisfied-not_satisfied-unresolved" .forall [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .quantifier "exists-4-not_satisfied-satisfied-not_satisfied-unresolved" .exists [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-0-4-not_satisfied-satisfied-not_satisfied-unresolved" .atLeast 0 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-1-4-not_satisfied-satisfied-not_satisfied-unresolved" .atLeast 1 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-2-4-not_satisfied-satisfied-not_satisfied-unresolved" .atLeast 2 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-3-4-not_satisfied-satisfied-not_satisfied-unresolved" .atLeast 3 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-4-4-not_satisfied-satisfied-not_satisfied-unresolved" .atLeast 4 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-5-4-not_satisfied-satisfied-not_satisfied-unresolved" .atLeast 5 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-0-4-not_satisfied-satisfied-not_satisfied-unresolved" .atMost 0 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-1-4-not_satisfied-satisfied-not_satisfied-unresolved" .atMost 1 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-2-4-not_satisfied-satisfied-not_satisfied-unresolved" .atMost 2 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-3-4-not_satisfied-satisfied-not_satisfied-unresolved" .atMost 3 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-4-4-not_satisfied-satisfied-not_satisfied-unresolved" .atMost 4 [.notSatisfied, .satisfied, .notSatisfied, .unresolved]
]

def vectorChunk91 : List Vector := [
  .cardinality "at-most-5-4-not_satisfied-satisfied-not_satisfied-unresolved" .atMost 5 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-0-4-not_satisfied-satisfied-not_satisfied-unresolved" .exactly 0 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-1-4-not_satisfied-satisfied-not_satisfied-unresolved" .exactly 1 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-2-4-not_satisfied-satisfied-not_satisfied-unresolved" .exactly 2 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-3-4-not_satisfied-satisfied-not_satisfied-unresolved" .exactly 3 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-4-4-not_satisfied-satisfied-not_satisfied-unresolved" .exactly 4 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-5-4-not_satisfied-satisfied-not_satisfied-unresolved" .exactly 5 [.notSatisfied, .satisfied, .notSatisfied, .unresolved],
  .quantifier "forall-4-not_satisfied-satisfied-unresolved-satisfied" .forall [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .quantifier "exists-4-not_satisfied-satisfied-unresolved-satisfied" .exists [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-0-4-not_satisfied-satisfied-unresolved-satisfied" .atLeast 0 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-1-4-not_satisfied-satisfied-unresolved-satisfied" .atLeast 1 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-2-4-not_satisfied-satisfied-unresolved-satisfied" .atLeast 2 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-3-4-not_satisfied-satisfied-unresolved-satisfied" .atLeast 3 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-4-4-not_satisfied-satisfied-unresolved-satisfied" .atLeast 4 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-5-4-not_satisfied-satisfied-unresolved-satisfied" .atLeast 5 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-0-4-not_satisfied-satisfied-unresolved-satisfied" .atMost 0 [.notSatisfied, .satisfied, .unresolved, .satisfied]
]

def vectorChunk92 : List Vector := [
  .cardinality "at-most-1-4-not_satisfied-satisfied-unresolved-satisfied" .atMost 1 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-2-4-not_satisfied-satisfied-unresolved-satisfied" .atMost 2 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-3-4-not_satisfied-satisfied-unresolved-satisfied" .atMost 3 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-4-4-not_satisfied-satisfied-unresolved-satisfied" .atMost 4 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-5-4-not_satisfied-satisfied-unresolved-satisfied" .atMost 5 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-0-4-not_satisfied-satisfied-unresolved-satisfied" .exactly 0 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-1-4-not_satisfied-satisfied-unresolved-satisfied" .exactly 1 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-2-4-not_satisfied-satisfied-unresolved-satisfied" .exactly 2 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-3-4-not_satisfied-satisfied-unresolved-satisfied" .exactly 3 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-4-4-not_satisfied-satisfied-unresolved-satisfied" .exactly 4 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-5-4-not_satisfied-satisfied-unresolved-satisfied" .exactly 5 [.notSatisfied, .satisfied, .unresolved, .satisfied],
  .quantifier "forall-4-not_satisfied-satisfied-unresolved-not_satisfied" .forall [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .quantifier "exists-4-not_satisfied-satisfied-unresolved-not_satisfied" .exists [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-0-4-not_satisfied-satisfied-unresolved-not_satisfied" .atLeast 0 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-1-4-not_satisfied-satisfied-unresolved-not_satisfied" .atLeast 1 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-2-4-not_satisfied-satisfied-unresolved-not_satisfied" .atLeast 2 [.notSatisfied, .satisfied, .unresolved, .notSatisfied]
]

def vectorChunk93 : List Vector := [
  .cardinality "at-least-3-4-not_satisfied-satisfied-unresolved-not_satisfied" .atLeast 3 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-4-4-not_satisfied-satisfied-unresolved-not_satisfied" .atLeast 4 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-5-4-not_satisfied-satisfied-unresolved-not_satisfied" .atLeast 5 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-0-4-not_satisfied-satisfied-unresolved-not_satisfied" .atMost 0 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-1-4-not_satisfied-satisfied-unresolved-not_satisfied" .atMost 1 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-2-4-not_satisfied-satisfied-unresolved-not_satisfied" .atMost 2 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-3-4-not_satisfied-satisfied-unresolved-not_satisfied" .atMost 3 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-4-4-not_satisfied-satisfied-unresolved-not_satisfied" .atMost 4 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-5-4-not_satisfied-satisfied-unresolved-not_satisfied" .atMost 5 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-0-4-not_satisfied-satisfied-unresolved-not_satisfied" .exactly 0 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-1-4-not_satisfied-satisfied-unresolved-not_satisfied" .exactly 1 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-2-4-not_satisfied-satisfied-unresolved-not_satisfied" .exactly 2 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-3-4-not_satisfied-satisfied-unresolved-not_satisfied" .exactly 3 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-4-4-not_satisfied-satisfied-unresolved-not_satisfied" .exactly 4 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-5-4-not_satisfied-satisfied-unresolved-not_satisfied" .exactly 5 [.notSatisfied, .satisfied, .unresolved, .notSatisfied],
  .quantifier "forall-4-not_satisfied-satisfied-unresolved-unresolved" .forall [.notSatisfied, .satisfied, .unresolved, .unresolved]
]

def vectorChunk94 : List Vector := [
  .quantifier "exists-4-not_satisfied-satisfied-unresolved-unresolved" .exists [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-0-4-not_satisfied-satisfied-unresolved-unresolved" .atLeast 0 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-1-4-not_satisfied-satisfied-unresolved-unresolved" .atLeast 1 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-2-4-not_satisfied-satisfied-unresolved-unresolved" .atLeast 2 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-3-4-not_satisfied-satisfied-unresolved-unresolved" .atLeast 3 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-4-4-not_satisfied-satisfied-unresolved-unresolved" .atLeast 4 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-5-4-not_satisfied-satisfied-unresolved-unresolved" .atLeast 5 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-0-4-not_satisfied-satisfied-unresolved-unresolved" .atMost 0 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-1-4-not_satisfied-satisfied-unresolved-unresolved" .atMost 1 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-2-4-not_satisfied-satisfied-unresolved-unresolved" .atMost 2 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-3-4-not_satisfied-satisfied-unresolved-unresolved" .atMost 3 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-4-4-not_satisfied-satisfied-unresolved-unresolved" .atMost 4 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-5-4-not_satisfied-satisfied-unresolved-unresolved" .atMost 5 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-0-4-not_satisfied-satisfied-unresolved-unresolved" .exactly 0 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-1-4-not_satisfied-satisfied-unresolved-unresolved" .exactly 1 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-2-4-not_satisfied-satisfied-unresolved-unresolved" .exactly 2 [.notSatisfied, .satisfied, .unresolved, .unresolved]
]

def vectorChunk95 : List Vector := [
  .cardinality "exactly-3-4-not_satisfied-satisfied-unresolved-unresolved" .exactly 3 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-4-4-not_satisfied-satisfied-unresolved-unresolved" .exactly 4 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-5-4-not_satisfied-satisfied-unresolved-unresolved" .exactly 5 [.notSatisfied, .satisfied, .unresolved, .unresolved],
  .quantifier "forall-4-not_satisfied-not_satisfied-satisfied-satisfied" .forall [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .quantifier "exists-4-not_satisfied-not_satisfied-satisfied-satisfied" .exists [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-0-4-not_satisfied-not_satisfied-satisfied-satisfied" .atLeast 0 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-1-4-not_satisfied-not_satisfied-satisfied-satisfied" .atLeast 1 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-2-4-not_satisfied-not_satisfied-satisfied-satisfied" .atLeast 2 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-3-4-not_satisfied-not_satisfied-satisfied-satisfied" .atLeast 3 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-4-4-not_satisfied-not_satisfied-satisfied-satisfied" .atLeast 4 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-5-4-not_satisfied-not_satisfied-satisfied-satisfied" .atLeast 5 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-0-4-not_satisfied-not_satisfied-satisfied-satisfied" .atMost 0 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-1-4-not_satisfied-not_satisfied-satisfied-satisfied" .atMost 1 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-2-4-not_satisfied-not_satisfied-satisfied-satisfied" .atMost 2 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-3-4-not_satisfied-not_satisfied-satisfied-satisfied" .atMost 3 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-4-4-not_satisfied-not_satisfied-satisfied-satisfied" .atMost 4 [.notSatisfied, .notSatisfied, .satisfied, .satisfied]
]

def vectorChunk96 : List Vector := [
  .cardinality "at-most-5-4-not_satisfied-not_satisfied-satisfied-satisfied" .atMost 5 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-0-4-not_satisfied-not_satisfied-satisfied-satisfied" .exactly 0 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-1-4-not_satisfied-not_satisfied-satisfied-satisfied" .exactly 1 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-2-4-not_satisfied-not_satisfied-satisfied-satisfied" .exactly 2 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-3-4-not_satisfied-not_satisfied-satisfied-satisfied" .exactly 3 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-4-4-not_satisfied-not_satisfied-satisfied-satisfied" .exactly 4 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-5-4-not_satisfied-not_satisfied-satisfied-satisfied" .exactly 5 [.notSatisfied, .notSatisfied, .satisfied, .satisfied],
  .quantifier "forall-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .forall [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .quantifier "exists-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .exists [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-0-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 0 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-1-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 1 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-2-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 2 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-3-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 3 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-4-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 4 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-5-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atLeast 5 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-0-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atMost 0 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied]
]

def vectorChunk97 : List Vector := [
  .cardinality "at-most-1-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atMost 1 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-2-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atMost 2 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-3-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atMost 3 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-4-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atMost 4 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-5-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .atMost 5 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-0-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .exactly 0 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-1-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .exactly 1 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-2-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .exactly 2 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-3-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .exactly 3 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-4-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .exactly 4 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-5-4-not_satisfied-not_satisfied-satisfied-not_satisfied" .exactly 5 [.notSatisfied, .notSatisfied, .satisfied, .notSatisfied],
  .quantifier "forall-4-not_satisfied-not_satisfied-satisfied-unresolved" .forall [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .quantifier "exists-4-not_satisfied-not_satisfied-satisfied-unresolved" .exists [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-0-4-not_satisfied-not_satisfied-satisfied-unresolved" .atLeast 0 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-1-4-not_satisfied-not_satisfied-satisfied-unresolved" .atLeast 1 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-2-4-not_satisfied-not_satisfied-satisfied-unresolved" .atLeast 2 [.notSatisfied, .notSatisfied, .satisfied, .unresolved]
]

def vectorChunk98 : List Vector := [
  .cardinality "at-least-3-4-not_satisfied-not_satisfied-satisfied-unresolved" .atLeast 3 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-4-4-not_satisfied-not_satisfied-satisfied-unresolved" .atLeast 4 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-5-4-not_satisfied-not_satisfied-satisfied-unresolved" .atLeast 5 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-0-4-not_satisfied-not_satisfied-satisfied-unresolved" .atMost 0 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-1-4-not_satisfied-not_satisfied-satisfied-unresolved" .atMost 1 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-2-4-not_satisfied-not_satisfied-satisfied-unresolved" .atMost 2 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-3-4-not_satisfied-not_satisfied-satisfied-unresolved" .atMost 3 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-4-4-not_satisfied-not_satisfied-satisfied-unresolved" .atMost 4 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-5-4-not_satisfied-not_satisfied-satisfied-unresolved" .atMost 5 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-0-4-not_satisfied-not_satisfied-satisfied-unresolved" .exactly 0 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-1-4-not_satisfied-not_satisfied-satisfied-unresolved" .exactly 1 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-2-4-not_satisfied-not_satisfied-satisfied-unresolved" .exactly 2 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-3-4-not_satisfied-not_satisfied-satisfied-unresolved" .exactly 3 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-4-4-not_satisfied-not_satisfied-satisfied-unresolved" .exactly 4 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-5-4-not_satisfied-not_satisfied-satisfied-unresolved" .exactly 5 [.notSatisfied, .notSatisfied, .satisfied, .unresolved],
  .quantifier "forall-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .forall [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied]
]

def vectorChunk99 : List Vector := [
  .quantifier "exists-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .exists [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-0-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 0 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-1-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 1 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-2-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 2 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-3-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 3 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-4-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 4 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-5-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atLeast 5 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-0-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atMost 0 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-1-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atMost 1 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-2-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atMost 2 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-3-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atMost 3 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-4-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atMost 4 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-5-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .atMost 5 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-0-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .exactly 0 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-1-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .exactly 1 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-2-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .exactly 2 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied]
]

def vectorChunk100 : List Vector := [
  .cardinality "exactly-3-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .exactly 3 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-4-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .exactly 4 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-5-4-not_satisfied-not_satisfied-not_satisfied-satisfied" .exactly 5 [.notSatisfied, .notSatisfied, .notSatisfied, .satisfied],
  .quantifier "forall-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .forall [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .quantifier "exists-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .exists [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 0 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 1 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 2 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-3-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 3 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 4 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atLeast 5 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 0 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-1-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 1 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 2 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 3 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 4 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk101 : List Vector := [
  .cardinality "at-most-5-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .atMost 5 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 0 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 1 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 2 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-3-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 3 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 4 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-4-not_satisfied-not_satisfied-not_satisfied-not_satisfied" .exactly 5 [.notSatisfied, .notSatisfied, .notSatisfied, .notSatisfied],
  .quantifier "forall-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .forall [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .quantifier "exists-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .exists [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-0-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 0 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-1-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 1 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-2-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 2 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-3-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 3 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-4-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 4 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-5-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atLeast 5 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-0-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atMost 0 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved]
]

def vectorChunk102 : List Vector := [
  .cardinality "at-most-1-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atMost 1 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-2-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atMost 2 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-3-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atMost 3 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-4-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atMost 4 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-5-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .atMost 5 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-0-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .exactly 0 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-1-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .exactly 1 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-2-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .exactly 2 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-3-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .exactly 3 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-4-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .exactly 4 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-5-4-not_satisfied-not_satisfied-not_satisfied-unresolved" .exactly 5 [.notSatisfied, .notSatisfied, .notSatisfied, .unresolved],
  .quantifier "forall-4-not_satisfied-not_satisfied-unresolved-satisfied" .forall [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .quantifier "exists-4-not_satisfied-not_satisfied-unresolved-satisfied" .exists [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-0-4-not_satisfied-not_satisfied-unresolved-satisfied" .atLeast 0 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-1-4-not_satisfied-not_satisfied-unresolved-satisfied" .atLeast 1 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-2-4-not_satisfied-not_satisfied-unresolved-satisfied" .atLeast 2 [.notSatisfied, .notSatisfied, .unresolved, .satisfied]
]

def vectorChunk103 : List Vector := [
  .cardinality "at-least-3-4-not_satisfied-not_satisfied-unresolved-satisfied" .atLeast 3 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-4-4-not_satisfied-not_satisfied-unresolved-satisfied" .atLeast 4 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-5-4-not_satisfied-not_satisfied-unresolved-satisfied" .atLeast 5 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-0-4-not_satisfied-not_satisfied-unresolved-satisfied" .atMost 0 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-1-4-not_satisfied-not_satisfied-unresolved-satisfied" .atMost 1 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-2-4-not_satisfied-not_satisfied-unresolved-satisfied" .atMost 2 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-3-4-not_satisfied-not_satisfied-unresolved-satisfied" .atMost 3 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-4-4-not_satisfied-not_satisfied-unresolved-satisfied" .atMost 4 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-5-4-not_satisfied-not_satisfied-unresolved-satisfied" .atMost 5 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-0-4-not_satisfied-not_satisfied-unresolved-satisfied" .exactly 0 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-1-4-not_satisfied-not_satisfied-unresolved-satisfied" .exactly 1 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-2-4-not_satisfied-not_satisfied-unresolved-satisfied" .exactly 2 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-3-4-not_satisfied-not_satisfied-unresolved-satisfied" .exactly 3 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-4-4-not_satisfied-not_satisfied-unresolved-satisfied" .exactly 4 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-5-4-not_satisfied-not_satisfied-unresolved-satisfied" .exactly 5 [.notSatisfied, .notSatisfied, .unresolved, .satisfied],
  .quantifier "forall-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .forall [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied]
]

def vectorChunk104 : List Vector := [
  .quantifier "exists-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .exists [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-0-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 0 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-1-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 1 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-2-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 2 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-3-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 3 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-4-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 4 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-5-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atLeast 5 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-0-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atMost 0 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-1-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atMost 1 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-2-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atMost 2 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-3-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atMost 3 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-4-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atMost 4 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-5-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .atMost 5 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-0-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .exactly 0 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-1-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .exactly 1 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-2-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .exactly 2 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied]
]

def vectorChunk105 : List Vector := [
  .cardinality "exactly-3-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .exactly 3 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-4-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .exactly 4 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-5-4-not_satisfied-not_satisfied-unresolved-not_satisfied" .exactly 5 [.notSatisfied, .notSatisfied, .unresolved, .notSatisfied],
  .quantifier "forall-4-not_satisfied-not_satisfied-unresolved-unresolved" .forall [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .quantifier "exists-4-not_satisfied-not_satisfied-unresolved-unresolved" .exists [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-0-4-not_satisfied-not_satisfied-unresolved-unresolved" .atLeast 0 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-1-4-not_satisfied-not_satisfied-unresolved-unresolved" .atLeast 1 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-2-4-not_satisfied-not_satisfied-unresolved-unresolved" .atLeast 2 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-3-4-not_satisfied-not_satisfied-unresolved-unresolved" .atLeast 3 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-4-4-not_satisfied-not_satisfied-unresolved-unresolved" .atLeast 4 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-5-4-not_satisfied-not_satisfied-unresolved-unresolved" .atLeast 5 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-0-4-not_satisfied-not_satisfied-unresolved-unresolved" .atMost 0 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-1-4-not_satisfied-not_satisfied-unresolved-unresolved" .atMost 1 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-2-4-not_satisfied-not_satisfied-unresolved-unresolved" .atMost 2 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-3-4-not_satisfied-not_satisfied-unresolved-unresolved" .atMost 3 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-4-4-not_satisfied-not_satisfied-unresolved-unresolved" .atMost 4 [.notSatisfied, .notSatisfied, .unresolved, .unresolved]
]

def vectorChunk106 : List Vector := [
  .cardinality "at-most-5-4-not_satisfied-not_satisfied-unresolved-unresolved" .atMost 5 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-0-4-not_satisfied-not_satisfied-unresolved-unresolved" .exactly 0 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-1-4-not_satisfied-not_satisfied-unresolved-unresolved" .exactly 1 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-2-4-not_satisfied-not_satisfied-unresolved-unresolved" .exactly 2 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-3-4-not_satisfied-not_satisfied-unresolved-unresolved" .exactly 3 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-4-4-not_satisfied-not_satisfied-unresolved-unresolved" .exactly 4 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-5-4-not_satisfied-not_satisfied-unresolved-unresolved" .exactly 5 [.notSatisfied, .notSatisfied, .unresolved, .unresolved],
  .quantifier "forall-4-not_satisfied-unresolved-satisfied-satisfied" .forall [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .quantifier "exists-4-not_satisfied-unresolved-satisfied-satisfied" .exists [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-0-4-not_satisfied-unresolved-satisfied-satisfied" .atLeast 0 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-1-4-not_satisfied-unresolved-satisfied-satisfied" .atLeast 1 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-2-4-not_satisfied-unresolved-satisfied-satisfied" .atLeast 2 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-3-4-not_satisfied-unresolved-satisfied-satisfied" .atLeast 3 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-4-4-not_satisfied-unresolved-satisfied-satisfied" .atLeast 4 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-5-4-not_satisfied-unresolved-satisfied-satisfied" .atLeast 5 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-0-4-not_satisfied-unresolved-satisfied-satisfied" .atMost 0 [.notSatisfied, .unresolved, .satisfied, .satisfied]
]

def vectorChunk107 : List Vector := [
  .cardinality "at-most-1-4-not_satisfied-unresolved-satisfied-satisfied" .atMost 1 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-2-4-not_satisfied-unresolved-satisfied-satisfied" .atMost 2 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-3-4-not_satisfied-unresolved-satisfied-satisfied" .atMost 3 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-4-4-not_satisfied-unresolved-satisfied-satisfied" .atMost 4 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-5-4-not_satisfied-unresolved-satisfied-satisfied" .atMost 5 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-0-4-not_satisfied-unresolved-satisfied-satisfied" .exactly 0 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-1-4-not_satisfied-unresolved-satisfied-satisfied" .exactly 1 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-2-4-not_satisfied-unresolved-satisfied-satisfied" .exactly 2 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-3-4-not_satisfied-unresolved-satisfied-satisfied" .exactly 3 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-4-4-not_satisfied-unresolved-satisfied-satisfied" .exactly 4 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-5-4-not_satisfied-unresolved-satisfied-satisfied" .exactly 5 [.notSatisfied, .unresolved, .satisfied, .satisfied],
  .quantifier "forall-4-not_satisfied-unresolved-satisfied-not_satisfied" .forall [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .quantifier "exists-4-not_satisfied-unresolved-satisfied-not_satisfied" .exists [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-0-4-not_satisfied-unresolved-satisfied-not_satisfied" .atLeast 0 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-1-4-not_satisfied-unresolved-satisfied-not_satisfied" .atLeast 1 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-2-4-not_satisfied-unresolved-satisfied-not_satisfied" .atLeast 2 [.notSatisfied, .unresolved, .satisfied, .notSatisfied]
]

def vectorChunk108 : List Vector := [
  .cardinality "at-least-3-4-not_satisfied-unresolved-satisfied-not_satisfied" .atLeast 3 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-4-4-not_satisfied-unresolved-satisfied-not_satisfied" .atLeast 4 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-5-4-not_satisfied-unresolved-satisfied-not_satisfied" .atLeast 5 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-0-4-not_satisfied-unresolved-satisfied-not_satisfied" .atMost 0 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-1-4-not_satisfied-unresolved-satisfied-not_satisfied" .atMost 1 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-2-4-not_satisfied-unresolved-satisfied-not_satisfied" .atMost 2 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-3-4-not_satisfied-unresolved-satisfied-not_satisfied" .atMost 3 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-4-4-not_satisfied-unresolved-satisfied-not_satisfied" .atMost 4 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-5-4-not_satisfied-unresolved-satisfied-not_satisfied" .atMost 5 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-0-4-not_satisfied-unresolved-satisfied-not_satisfied" .exactly 0 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-1-4-not_satisfied-unresolved-satisfied-not_satisfied" .exactly 1 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-2-4-not_satisfied-unresolved-satisfied-not_satisfied" .exactly 2 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-3-4-not_satisfied-unresolved-satisfied-not_satisfied" .exactly 3 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-4-4-not_satisfied-unresolved-satisfied-not_satisfied" .exactly 4 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-5-4-not_satisfied-unresolved-satisfied-not_satisfied" .exactly 5 [.notSatisfied, .unresolved, .satisfied, .notSatisfied],
  .quantifier "forall-4-not_satisfied-unresolved-satisfied-unresolved" .forall [.notSatisfied, .unresolved, .satisfied, .unresolved]
]

def vectorChunk109 : List Vector := [
  .quantifier "exists-4-not_satisfied-unresolved-satisfied-unresolved" .exists [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-0-4-not_satisfied-unresolved-satisfied-unresolved" .atLeast 0 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-1-4-not_satisfied-unresolved-satisfied-unresolved" .atLeast 1 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-2-4-not_satisfied-unresolved-satisfied-unresolved" .atLeast 2 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-3-4-not_satisfied-unresolved-satisfied-unresolved" .atLeast 3 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-4-4-not_satisfied-unresolved-satisfied-unresolved" .atLeast 4 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-5-4-not_satisfied-unresolved-satisfied-unresolved" .atLeast 5 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-0-4-not_satisfied-unresolved-satisfied-unresolved" .atMost 0 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-1-4-not_satisfied-unresolved-satisfied-unresolved" .atMost 1 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-2-4-not_satisfied-unresolved-satisfied-unresolved" .atMost 2 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-3-4-not_satisfied-unresolved-satisfied-unresolved" .atMost 3 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-4-4-not_satisfied-unresolved-satisfied-unresolved" .atMost 4 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-5-4-not_satisfied-unresolved-satisfied-unresolved" .atMost 5 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-0-4-not_satisfied-unresolved-satisfied-unresolved" .exactly 0 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-1-4-not_satisfied-unresolved-satisfied-unresolved" .exactly 1 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-2-4-not_satisfied-unresolved-satisfied-unresolved" .exactly 2 [.notSatisfied, .unresolved, .satisfied, .unresolved]
]

def vectorChunk110 : List Vector := [
  .cardinality "exactly-3-4-not_satisfied-unresolved-satisfied-unresolved" .exactly 3 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-4-4-not_satisfied-unresolved-satisfied-unresolved" .exactly 4 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-5-4-not_satisfied-unresolved-satisfied-unresolved" .exactly 5 [.notSatisfied, .unresolved, .satisfied, .unresolved],
  .quantifier "forall-4-not_satisfied-unresolved-not_satisfied-satisfied" .forall [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .quantifier "exists-4-not_satisfied-unresolved-not_satisfied-satisfied" .exists [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-0-4-not_satisfied-unresolved-not_satisfied-satisfied" .atLeast 0 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-1-4-not_satisfied-unresolved-not_satisfied-satisfied" .atLeast 1 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-2-4-not_satisfied-unresolved-not_satisfied-satisfied" .atLeast 2 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-3-4-not_satisfied-unresolved-not_satisfied-satisfied" .atLeast 3 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-4-4-not_satisfied-unresolved-not_satisfied-satisfied" .atLeast 4 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-5-4-not_satisfied-unresolved-not_satisfied-satisfied" .atLeast 5 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-0-4-not_satisfied-unresolved-not_satisfied-satisfied" .atMost 0 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-1-4-not_satisfied-unresolved-not_satisfied-satisfied" .atMost 1 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-2-4-not_satisfied-unresolved-not_satisfied-satisfied" .atMost 2 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-3-4-not_satisfied-unresolved-not_satisfied-satisfied" .atMost 3 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-4-4-not_satisfied-unresolved-not_satisfied-satisfied" .atMost 4 [.notSatisfied, .unresolved, .notSatisfied, .satisfied]
]

def vectorChunk111 : List Vector := [
  .cardinality "at-most-5-4-not_satisfied-unresolved-not_satisfied-satisfied" .atMost 5 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-0-4-not_satisfied-unresolved-not_satisfied-satisfied" .exactly 0 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-1-4-not_satisfied-unresolved-not_satisfied-satisfied" .exactly 1 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-2-4-not_satisfied-unresolved-not_satisfied-satisfied" .exactly 2 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-3-4-not_satisfied-unresolved-not_satisfied-satisfied" .exactly 3 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-4-4-not_satisfied-unresolved-not_satisfied-satisfied" .exactly 4 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-5-4-not_satisfied-unresolved-not_satisfied-satisfied" .exactly 5 [.notSatisfied, .unresolved, .notSatisfied, .satisfied],
  .quantifier "forall-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .forall [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .quantifier "exists-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .exists [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 0 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 1 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 2 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-3-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 3 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 4 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atLeast 5 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atMost 0 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied]
]

def vectorChunk112 : List Vector := [
  .cardinality "at-most-1-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atMost 1 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atMost 2 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atMost 3 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atMost 4 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-5-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .atMost 5 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .exactly 0 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .exactly 1 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .exactly 2 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-3-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .exactly 3 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .exactly 4 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-4-not_satisfied-unresolved-not_satisfied-not_satisfied" .exactly 5 [.notSatisfied, .unresolved, .notSatisfied, .notSatisfied],
  .quantifier "forall-4-not_satisfied-unresolved-not_satisfied-unresolved" .forall [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .quantifier "exists-4-not_satisfied-unresolved-not_satisfied-unresolved" .exists [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-0-4-not_satisfied-unresolved-not_satisfied-unresolved" .atLeast 0 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-1-4-not_satisfied-unresolved-not_satisfied-unresolved" .atLeast 1 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-2-4-not_satisfied-unresolved-not_satisfied-unresolved" .atLeast 2 [.notSatisfied, .unresolved, .notSatisfied, .unresolved]
]

def vectorChunk113 : List Vector := [
  .cardinality "at-least-3-4-not_satisfied-unresolved-not_satisfied-unresolved" .atLeast 3 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-4-4-not_satisfied-unresolved-not_satisfied-unresolved" .atLeast 4 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-5-4-not_satisfied-unresolved-not_satisfied-unresolved" .atLeast 5 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-0-4-not_satisfied-unresolved-not_satisfied-unresolved" .atMost 0 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-1-4-not_satisfied-unresolved-not_satisfied-unresolved" .atMost 1 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-2-4-not_satisfied-unresolved-not_satisfied-unresolved" .atMost 2 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-3-4-not_satisfied-unresolved-not_satisfied-unresolved" .atMost 3 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-4-4-not_satisfied-unresolved-not_satisfied-unresolved" .atMost 4 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-5-4-not_satisfied-unresolved-not_satisfied-unresolved" .atMost 5 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-0-4-not_satisfied-unresolved-not_satisfied-unresolved" .exactly 0 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-1-4-not_satisfied-unresolved-not_satisfied-unresolved" .exactly 1 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-2-4-not_satisfied-unresolved-not_satisfied-unresolved" .exactly 2 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-3-4-not_satisfied-unresolved-not_satisfied-unresolved" .exactly 3 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-4-4-not_satisfied-unresolved-not_satisfied-unresolved" .exactly 4 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-5-4-not_satisfied-unresolved-not_satisfied-unresolved" .exactly 5 [.notSatisfied, .unresolved, .notSatisfied, .unresolved],
  .quantifier "forall-4-not_satisfied-unresolved-unresolved-satisfied" .forall [.notSatisfied, .unresolved, .unresolved, .satisfied]
]

def vectorChunk114 : List Vector := [
  .quantifier "exists-4-not_satisfied-unresolved-unresolved-satisfied" .exists [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-0-4-not_satisfied-unresolved-unresolved-satisfied" .atLeast 0 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-1-4-not_satisfied-unresolved-unresolved-satisfied" .atLeast 1 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-2-4-not_satisfied-unresolved-unresolved-satisfied" .atLeast 2 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-3-4-not_satisfied-unresolved-unresolved-satisfied" .atLeast 3 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-4-4-not_satisfied-unresolved-unresolved-satisfied" .atLeast 4 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-5-4-not_satisfied-unresolved-unresolved-satisfied" .atLeast 5 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-0-4-not_satisfied-unresolved-unresolved-satisfied" .atMost 0 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-1-4-not_satisfied-unresolved-unresolved-satisfied" .atMost 1 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-2-4-not_satisfied-unresolved-unresolved-satisfied" .atMost 2 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-3-4-not_satisfied-unresolved-unresolved-satisfied" .atMost 3 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-4-4-not_satisfied-unresolved-unresolved-satisfied" .atMost 4 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-5-4-not_satisfied-unresolved-unresolved-satisfied" .atMost 5 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-0-4-not_satisfied-unresolved-unresolved-satisfied" .exactly 0 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-1-4-not_satisfied-unresolved-unresolved-satisfied" .exactly 1 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-2-4-not_satisfied-unresolved-unresolved-satisfied" .exactly 2 [.notSatisfied, .unresolved, .unresolved, .satisfied]
]

def vectorChunk115 : List Vector := [
  .cardinality "exactly-3-4-not_satisfied-unresolved-unresolved-satisfied" .exactly 3 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-4-4-not_satisfied-unresolved-unresolved-satisfied" .exactly 4 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-5-4-not_satisfied-unresolved-unresolved-satisfied" .exactly 5 [.notSatisfied, .unresolved, .unresolved, .satisfied],
  .quantifier "forall-4-not_satisfied-unresolved-unresolved-not_satisfied" .forall [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .quantifier "exists-4-not_satisfied-unresolved-unresolved-not_satisfied" .exists [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-0-4-not_satisfied-unresolved-unresolved-not_satisfied" .atLeast 0 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-1-4-not_satisfied-unresolved-unresolved-not_satisfied" .atLeast 1 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-2-4-not_satisfied-unresolved-unresolved-not_satisfied" .atLeast 2 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-3-4-not_satisfied-unresolved-unresolved-not_satisfied" .atLeast 3 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-4-4-not_satisfied-unresolved-unresolved-not_satisfied" .atLeast 4 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-5-4-not_satisfied-unresolved-unresolved-not_satisfied" .atLeast 5 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-0-4-not_satisfied-unresolved-unresolved-not_satisfied" .atMost 0 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-1-4-not_satisfied-unresolved-unresolved-not_satisfied" .atMost 1 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-2-4-not_satisfied-unresolved-unresolved-not_satisfied" .atMost 2 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-3-4-not_satisfied-unresolved-unresolved-not_satisfied" .atMost 3 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-4-4-not_satisfied-unresolved-unresolved-not_satisfied" .atMost 4 [.notSatisfied, .unresolved, .unresolved, .notSatisfied]
]

def vectorChunk116 : List Vector := [
  .cardinality "at-most-5-4-not_satisfied-unresolved-unresolved-not_satisfied" .atMost 5 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-0-4-not_satisfied-unresolved-unresolved-not_satisfied" .exactly 0 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-1-4-not_satisfied-unresolved-unresolved-not_satisfied" .exactly 1 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-2-4-not_satisfied-unresolved-unresolved-not_satisfied" .exactly 2 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-3-4-not_satisfied-unresolved-unresolved-not_satisfied" .exactly 3 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-4-4-not_satisfied-unresolved-unresolved-not_satisfied" .exactly 4 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-5-4-not_satisfied-unresolved-unresolved-not_satisfied" .exactly 5 [.notSatisfied, .unresolved, .unresolved, .notSatisfied],
  .quantifier "forall-4-not_satisfied-unresolved-unresolved-unresolved" .forall [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .quantifier "exists-4-not_satisfied-unresolved-unresolved-unresolved" .exists [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-0-4-not_satisfied-unresolved-unresolved-unresolved" .atLeast 0 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-1-4-not_satisfied-unresolved-unresolved-unresolved" .atLeast 1 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-2-4-not_satisfied-unresolved-unresolved-unresolved" .atLeast 2 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-3-4-not_satisfied-unresolved-unresolved-unresolved" .atLeast 3 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-4-4-not_satisfied-unresolved-unresolved-unresolved" .atLeast 4 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-5-4-not_satisfied-unresolved-unresolved-unresolved" .atLeast 5 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-0-4-not_satisfied-unresolved-unresolved-unresolved" .atMost 0 [.notSatisfied, .unresolved, .unresolved, .unresolved]
]

def vectorChunk117 : List Vector := [
  .cardinality "at-most-1-4-not_satisfied-unresolved-unresolved-unresolved" .atMost 1 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-2-4-not_satisfied-unresolved-unresolved-unresolved" .atMost 2 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-3-4-not_satisfied-unresolved-unresolved-unresolved" .atMost 3 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-4-4-not_satisfied-unresolved-unresolved-unresolved" .atMost 4 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-5-4-not_satisfied-unresolved-unresolved-unresolved" .atMost 5 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-0-4-not_satisfied-unresolved-unresolved-unresolved" .exactly 0 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-1-4-not_satisfied-unresolved-unresolved-unresolved" .exactly 1 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-2-4-not_satisfied-unresolved-unresolved-unresolved" .exactly 2 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-3-4-not_satisfied-unresolved-unresolved-unresolved" .exactly 3 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-4-4-not_satisfied-unresolved-unresolved-unresolved" .exactly 4 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-5-4-not_satisfied-unresolved-unresolved-unresolved" .exactly 5 [.notSatisfied, .unresolved, .unresolved, .unresolved],
  .quantifier "forall-4-unresolved-satisfied-satisfied-satisfied" .forall [.unresolved, .satisfied, .satisfied, .satisfied],
  .quantifier "exists-4-unresolved-satisfied-satisfied-satisfied" .exists [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-0-4-unresolved-satisfied-satisfied-satisfied" .atLeast 0 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-1-4-unresolved-satisfied-satisfied-satisfied" .atLeast 1 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-2-4-unresolved-satisfied-satisfied-satisfied" .atLeast 2 [.unresolved, .satisfied, .satisfied, .satisfied]
]

def vectorChunk118 : List Vector := [
  .cardinality "at-least-3-4-unresolved-satisfied-satisfied-satisfied" .atLeast 3 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-4-4-unresolved-satisfied-satisfied-satisfied" .atLeast 4 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-least-5-4-unresolved-satisfied-satisfied-satisfied" .atLeast 5 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-0-4-unresolved-satisfied-satisfied-satisfied" .atMost 0 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-1-4-unresolved-satisfied-satisfied-satisfied" .atMost 1 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-2-4-unresolved-satisfied-satisfied-satisfied" .atMost 2 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-3-4-unresolved-satisfied-satisfied-satisfied" .atMost 3 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-4-4-unresolved-satisfied-satisfied-satisfied" .atMost 4 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "at-most-5-4-unresolved-satisfied-satisfied-satisfied" .atMost 5 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-0-4-unresolved-satisfied-satisfied-satisfied" .exactly 0 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-1-4-unresolved-satisfied-satisfied-satisfied" .exactly 1 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-2-4-unresolved-satisfied-satisfied-satisfied" .exactly 2 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-3-4-unresolved-satisfied-satisfied-satisfied" .exactly 3 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-4-4-unresolved-satisfied-satisfied-satisfied" .exactly 4 [.unresolved, .satisfied, .satisfied, .satisfied],
  .cardinality "exactly-5-4-unresolved-satisfied-satisfied-satisfied" .exactly 5 [.unresolved, .satisfied, .satisfied, .satisfied],
  .quantifier "forall-4-unresolved-satisfied-satisfied-not_satisfied" .forall [.unresolved, .satisfied, .satisfied, .notSatisfied]
]

def vectorChunk119 : List Vector := [
  .quantifier "exists-4-unresolved-satisfied-satisfied-not_satisfied" .exists [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-0-4-unresolved-satisfied-satisfied-not_satisfied" .atLeast 0 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-1-4-unresolved-satisfied-satisfied-not_satisfied" .atLeast 1 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-2-4-unresolved-satisfied-satisfied-not_satisfied" .atLeast 2 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-3-4-unresolved-satisfied-satisfied-not_satisfied" .atLeast 3 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-4-4-unresolved-satisfied-satisfied-not_satisfied" .atLeast 4 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-5-4-unresolved-satisfied-satisfied-not_satisfied" .atLeast 5 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-0-4-unresolved-satisfied-satisfied-not_satisfied" .atMost 0 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-1-4-unresolved-satisfied-satisfied-not_satisfied" .atMost 1 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-2-4-unresolved-satisfied-satisfied-not_satisfied" .atMost 2 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-3-4-unresolved-satisfied-satisfied-not_satisfied" .atMost 3 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-4-4-unresolved-satisfied-satisfied-not_satisfied" .atMost 4 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-5-4-unresolved-satisfied-satisfied-not_satisfied" .atMost 5 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-0-4-unresolved-satisfied-satisfied-not_satisfied" .exactly 0 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-1-4-unresolved-satisfied-satisfied-not_satisfied" .exactly 1 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-2-4-unresolved-satisfied-satisfied-not_satisfied" .exactly 2 [.unresolved, .satisfied, .satisfied, .notSatisfied]
]

def vectorChunk120 : List Vector := [
  .cardinality "exactly-3-4-unresolved-satisfied-satisfied-not_satisfied" .exactly 3 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-4-4-unresolved-satisfied-satisfied-not_satisfied" .exactly 4 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-5-4-unresolved-satisfied-satisfied-not_satisfied" .exactly 5 [.unresolved, .satisfied, .satisfied, .notSatisfied],
  .quantifier "forall-4-unresolved-satisfied-satisfied-unresolved" .forall [.unresolved, .satisfied, .satisfied, .unresolved],
  .quantifier "exists-4-unresolved-satisfied-satisfied-unresolved" .exists [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-0-4-unresolved-satisfied-satisfied-unresolved" .atLeast 0 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-1-4-unresolved-satisfied-satisfied-unresolved" .atLeast 1 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-2-4-unresolved-satisfied-satisfied-unresolved" .atLeast 2 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-3-4-unresolved-satisfied-satisfied-unresolved" .atLeast 3 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-4-4-unresolved-satisfied-satisfied-unresolved" .atLeast 4 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-least-5-4-unresolved-satisfied-satisfied-unresolved" .atLeast 5 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-0-4-unresolved-satisfied-satisfied-unresolved" .atMost 0 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-1-4-unresolved-satisfied-satisfied-unresolved" .atMost 1 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-2-4-unresolved-satisfied-satisfied-unresolved" .atMost 2 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-3-4-unresolved-satisfied-satisfied-unresolved" .atMost 3 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "at-most-4-4-unresolved-satisfied-satisfied-unresolved" .atMost 4 [.unresolved, .satisfied, .satisfied, .unresolved]
]

def vectorChunk121 : List Vector := [
  .cardinality "at-most-5-4-unresolved-satisfied-satisfied-unresolved" .atMost 5 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-0-4-unresolved-satisfied-satisfied-unresolved" .exactly 0 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-1-4-unresolved-satisfied-satisfied-unresolved" .exactly 1 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-2-4-unresolved-satisfied-satisfied-unresolved" .exactly 2 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-3-4-unresolved-satisfied-satisfied-unresolved" .exactly 3 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-4-4-unresolved-satisfied-satisfied-unresolved" .exactly 4 [.unresolved, .satisfied, .satisfied, .unresolved],
  .cardinality "exactly-5-4-unresolved-satisfied-satisfied-unresolved" .exactly 5 [.unresolved, .satisfied, .satisfied, .unresolved],
  .quantifier "forall-4-unresolved-satisfied-not_satisfied-satisfied" .forall [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .quantifier "exists-4-unresolved-satisfied-not_satisfied-satisfied" .exists [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-0-4-unresolved-satisfied-not_satisfied-satisfied" .atLeast 0 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-1-4-unresolved-satisfied-not_satisfied-satisfied" .atLeast 1 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-2-4-unresolved-satisfied-not_satisfied-satisfied" .atLeast 2 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-3-4-unresolved-satisfied-not_satisfied-satisfied" .atLeast 3 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-4-4-unresolved-satisfied-not_satisfied-satisfied" .atLeast 4 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-5-4-unresolved-satisfied-not_satisfied-satisfied" .atLeast 5 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-0-4-unresolved-satisfied-not_satisfied-satisfied" .atMost 0 [.unresolved, .satisfied, .notSatisfied, .satisfied]
]

def vectorChunk122 : List Vector := [
  .cardinality "at-most-1-4-unresolved-satisfied-not_satisfied-satisfied" .atMost 1 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-2-4-unresolved-satisfied-not_satisfied-satisfied" .atMost 2 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-3-4-unresolved-satisfied-not_satisfied-satisfied" .atMost 3 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-4-4-unresolved-satisfied-not_satisfied-satisfied" .atMost 4 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-5-4-unresolved-satisfied-not_satisfied-satisfied" .atMost 5 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-0-4-unresolved-satisfied-not_satisfied-satisfied" .exactly 0 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-1-4-unresolved-satisfied-not_satisfied-satisfied" .exactly 1 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-2-4-unresolved-satisfied-not_satisfied-satisfied" .exactly 2 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-3-4-unresolved-satisfied-not_satisfied-satisfied" .exactly 3 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-4-4-unresolved-satisfied-not_satisfied-satisfied" .exactly 4 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-5-4-unresolved-satisfied-not_satisfied-satisfied" .exactly 5 [.unresolved, .satisfied, .notSatisfied, .satisfied],
  .quantifier "forall-4-unresolved-satisfied-not_satisfied-not_satisfied" .forall [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .quantifier "exists-4-unresolved-satisfied-not_satisfied-not_satisfied" .exists [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-4-unresolved-satisfied-not_satisfied-not_satisfied" .atLeast 0 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-4-unresolved-satisfied-not_satisfied-not_satisfied" .atLeast 1 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-4-unresolved-satisfied-not_satisfied-not_satisfied" .atLeast 2 [.unresolved, .satisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk123 : List Vector := [
  .cardinality "at-least-3-4-unresolved-satisfied-not_satisfied-not_satisfied" .atLeast 3 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-4-unresolved-satisfied-not_satisfied-not_satisfied" .atLeast 4 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-4-unresolved-satisfied-not_satisfied-not_satisfied" .atLeast 5 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-4-unresolved-satisfied-not_satisfied-not_satisfied" .atMost 0 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-1-4-unresolved-satisfied-not_satisfied-not_satisfied" .atMost 1 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-4-unresolved-satisfied-not_satisfied-not_satisfied" .atMost 2 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-4-unresolved-satisfied-not_satisfied-not_satisfied" .atMost 3 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-4-unresolved-satisfied-not_satisfied-not_satisfied" .atMost 4 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-5-4-unresolved-satisfied-not_satisfied-not_satisfied" .atMost 5 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-4-unresolved-satisfied-not_satisfied-not_satisfied" .exactly 0 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-4-unresolved-satisfied-not_satisfied-not_satisfied" .exactly 1 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-4-unresolved-satisfied-not_satisfied-not_satisfied" .exactly 2 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-3-4-unresolved-satisfied-not_satisfied-not_satisfied" .exactly 3 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-4-unresolved-satisfied-not_satisfied-not_satisfied" .exactly 4 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-4-unresolved-satisfied-not_satisfied-not_satisfied" .exactly 5 [.unresolved, .satisfied, .notSatisfied, .notSatisfied],
  .quantifier "forall-4-unresolved-satisfied-not_satisfied-unresolved" .forall [.unresolved, .satisfied, .notSatisfied, .unresolved]
]

def vectorChunk124 : List Vector := [
  .quantifier "exists-4-unresolved-satisfied-not_satisfied-unresolved" .exists [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-0-4-unresolved-satisfied-not_satisfied-unresolved" .atLeast 0 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-1-4-unresolved-satisfied-not_satisfied-unresolved" .atLeast 1 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-2-4-unresolved-satisfied-not_satisfied-unresolved" .atLeast 2 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-3-4-unresolved-satisfied-not_satisfied-unresolved" .atLeast 3 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-4-4-unresolved-satisfied-not_satisfied-unresolved" .atLeast 4 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-5-4-unresolved-satisfied-not_satisfied-unresolved" .atLeast 5 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-0-4-unresolved-satisfied-not_satisfied-unresolved" .atMost 0 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-1-4-unresolved-satisfied-not_satisfied-unresolved" .atMost 1 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-2-4-unresolved-satisfied-not_satisfied-unresolved" .atMost 2 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-3-4-unresolved-satisfied-not_satisfied-unresolved" .atMost 3 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-4-4-unresolved-satisfied-not_satisfied-unresolved" .atMost 4 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-5-4-unresolved-satisfied-not_satisfied-unresolved" .atMost 5 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-0-4-unresolved-satisfied-not_satisfied-unresolved" .exactly 0 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-1-4-unresolved-satisfied-not_satisfied-unresolved" .exactly 1 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-2-4-unresolved-satisfied-not_satisfied-unresolved" .exactly 2 [.unresolved, .satisfied, .notSatisfied, .unresolved]
]

def vectorChunk125 : List Vector := [
  .cardinality "exactly-3-4-unresolved-satisfied-not_satisfied-unresolved" .exactly 3 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-4-4-unresolved-satisfied-not_satisfied-unresolved" .exactly 4 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-5-4-unresolved-satisfied-not_satisfied-unresolved" .exactly 5 [.unresolved, .satisfied, .notSatisfied, .unresolved],
  .quantifier "forall-4-unresolved-satisfied-unresolved-satisfied" .forall [.unresolved, .satisfied, .unresolved, .satisfied],
  .quantifier "exists-4-unresolved-satisfied-unresolved-satisfied" .exists [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-0-4-unresolved-satisfied-unresolved-satisfied" .atLeast 0 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-1-4-unresolved-satisfied-unresolved-satisfied" .atLeast 1 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-2-4-unresolved-satisfied-unresolved-satisfied" .atLeast 2 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-3-4-unresolved-satisfied-unresolved-satisfied" .atLeast 3 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-4-4-unresolved-satisfied-unresolved-satisfied" .atLeast 4 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-least-5-4-unresolved-satisfied-unresolved-satisfied" .atLeast 5 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-0-4-unresolved-satisfied-unresolved-satisfied" .atMost 0 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-1-4-unresolved-satisfied-unresolved-satisfied" .atMost 1 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-2-4-unresolved-satisfied-unresolved-satisfied" .atMost 2 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-3-4-unresolved-satisfied-unresolved-satisfied" .atMost 3 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "at-most-4-4-unresolved-satisfied-unresolved-satisfied" .atMost 4 [.unresolved, .satisfied, .unresolved, .satisfied]
]

def vectorChunk126 : List Vector := [
  .cardinality "at-most-5-4-unresolved-satisfied-unresolved-satisfied" .atMost 5 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-0-4-unresolved-satisfied-unresolved-satisfied" .exactly 0 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-1-4-unresolved-satisfied-unresolved-satisfied" .exactly 1 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-2-4-unresolved-satisfied-unresolved-satisfied" .exactly 2 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-3-4-unresolved-satisfied-unresolved-satisfied" .exactly 3 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-4-4-unresolved-satisfied-unresolved-satisfied" .exactly 4 [.unresolved, .satisfied, .unresolved, .satisfied],
  .cardinality "exactly-5-4-unresolved-satisfied-unresolved-satisfied" .exactly 5 [.unresolved, .satisfied, .unresolved, .satisfied],
  .quantifier "forall-4-unresolved-satisfied-unresolved-not_satisfied" .forall [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .quantifier "exists-4-unresolved-satisfied-unresolved-not_satisfied" .exists [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-0-4-unresolved-satisfied-unresolved-not_satisfied" .atLeast 0 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-1-4-unresolved-satisfied-unresolved-not_satisfied" .atLeast 1 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-2-4-unresolved-satisfied-unresolved-not_satisfied" .atLeast 2 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-3-4-unresolved-satisfied-unresolved-not_satisfied" .atLeast 3 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-4-4-unresolved-satisfied-unresolved-not_satisfied" .atLeast 4 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-5-4-unresolved-satisfied-unresolved-not_satisfied" .atLeast 5 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-0-4-unresolved-satisfied-unresolved-not_satisfied" .atMost 0 [.unresolved, .satisfied, .unresolved, .notSatisfied]
]

def vectorChunk127 : List Vector := [
  .cardinality "at-most-1-4-unresolved-satisfied-unresolved-not_satisfied" .atMost 1 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-2-4-unresolved-satisfied-unresolved-not_satisfied" .atMost 2 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-3-4-unresolved-satisfied-unresolved-not_satisfied" .atMost 3 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-4-4-unresolved-satisfied-unresolved-not_satisfied" .atMost 4 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-5-4-unresolved-satisfied-unresolved-not_satisfied" .atMost 5 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-0-4-unresolved-satisfied-unresolved-not_satisfied" .exactly 0 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-1-4-unresolved-satisfied-unresolved-not_satisfied" .exactly 1 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-2-4-unresolved-satisfied-unresolved-not_satisfied" .exactly 2 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-3-4-unresolved-satisfied-unresolved-not_satisfied" .exactly 3 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-4-4-unresolved-satisfied-unresolved-not_satisfied" .exactly 4 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-5-4-unresolved-satisfied-unresolved-not_satisfied" .exactly 5 [.unresolved, .satisfied, .unresolved, .notSatisfied],
  .quantifier "forall-4-unresolved-satisfied-unresolved-unresolved" .forall [.unresolved, .satisfied, .unresolved, .unresolved],
  .quantifier "exists-4-unresolved-satisfied-unresolved-unresolved" .exists [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-0-4-unresolved-satisfied-unresolved-unresolved" .atLeast 0 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-1-4-unresolved-satisfied-unresolved-unresolved" .atLeast 1 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-2-4-unresolved-satisfied-unresolved-unresolved" .atLeast 2 [.unresolved, .satisfied, .unresolved, .unresolved]
]

def vectorChunk128 : List Vector := [
  .cardinality "at-least-3-4-unresolved-satisfied-unresolved-unresolved" .atLeast 3 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-4-4-unresolved-satisfied-unresolved-unresolved" .atLeast 4 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-least-5-4-unresolved-satisfied-unresolved-unresolved" .atLeast 5 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-0-4-unresolved-satisfied-unresolved-unresolved" .atMost 0 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-1-4-unresolved-satisfied-unresolved-unresolved" .atMost 1 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-2-4-unresolved-satisfied-unresolved-unresolved" .atMost 2 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-3-4-unresolved-satisfied-unresolved-unresolved" .atMost 3 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-4-4-unresolved-satisfied-unresolved-unresolved" .atMost 4 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "at-most-5-4-unresolved-satisfied-unresolved-unresolved" .atMost 5 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-0-4-unresolved-satisfied-unresolved-unresolved" .exactly 0 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-1-4-unresolved-satisfied-unresolved-unresolved" .exactly 1 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-2-4-unresolved-satisfied-unresolved-unresolved" .exactly 2 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-3-4-unresolved-satisfied-unresolved-unresolved" .exactly 3 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-4-4-unresolved-satisfied-unresolved-unresolved" .exactly 4 [.unresolved, .satisfied, .unresolved, .unresolved],
  .cardinality "exactly-5-4-unresolved-satisfied-unresolved-unresolved" .exactly 5 [.unresolved, .satisfied, .unresolved, .unresolved],
  .quantifier "forall-4-unresolved-not_satisfied-satisfied-satisfied" .forall [.unresolved, .notSatisfied, .satisfied, .satisfied]
]

def vectorChunk129 : List Vector := [
  .quantifier "exists-4-unresolved-not_satisfied-satisfied-satisfied" .exists [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-0-4-unresolved-not_satisfied-satisfied-satisfied" .atLeast 0 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-1-4-unresolved-not_satisfied-satisfied-satisfied" .atLeast 1 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-2-4-unresolved-not_satisfied-satisfied-satisfied" .atLeast 2 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-3-4-unresolved-not_satisfied-satisfied-satisfied" .atLeast 3 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-4-4-unresolved-not_satisfied-satisfied-satisfied" .atLeast 4 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-least-5-4-unresolved-not_satisfied-satisfied-satisfied" .atLeast 5 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-0-4-unresolved-not_satisfied-satisfied-satisfied" .atMost 0 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-1-4-unresolved-not_satisfied-satisfied-satisfied" .atMost 1 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-2-4-unresolved-not_satisfied-satisfied-satisfied" .atMost 2 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-3-4-unresolved-not_satisfied-satisfied-satisfied" .atMost 3 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-4-4-unresolved-not_satisfied-satisfied-satisfied" .atMost 4 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "at-most-5-4-unresolved-not_satisfied-satisfied-satisfied" .atMost 5 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-0-4-unresolved-not_satisfied-satisfied-satisfied" .exactly 0 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-1-4-unresolved-not_satisfied-satisfied-satisfied" .exactly 1 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-2-4-unresolved-not_satisfied-satisfied-satisfied" .exactly 2 [.unresolved, .notSatisfied, .satisfied, .satisfied]
]

def vectorChunk130 : List Vector := [
  .cardinality "exactly-3-4-unresolved-not_satisfied-satisfied-satisfied" .exactly 3 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-4-4-unresolved-not_satisfied-satisfied-satisfied" .exactly 4 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .cardinality "exactly-5-4-unresolved-not_satisfied-satisfied-satisfied" .exactly 5 [.unresolved, .notSatisfied, .satisfied, .satisfied],
  .quantifier "forall-4-unresolved-not_satisfied-satisfied-not_satisfied" .forall [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .quantifier "exists-4-unresolved-not_satisfied-satisfied-not_satisfied" .exists [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-0-4-unresolved-not_satisfied-satisfied-not_satisfied" .atLeast 0 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-1-4-unresolved-not_satisfied-satisfied-not_satisfied" .atLeast 1 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-2-4-unresolved-not_satisfied-satisfied-not_satisfied" .atLeast 2 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-3-4-unresolved-not_satisfied-satisfied-not_satisfied" .atLeast 3 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-4-4-unresolved-not_satisfied-satisfied-not_satisfied" .atLeast 4 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-least-5-4-unresolved-not_satisfied-satisfied-not_satisfied" .atLeast 5 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-0-4-unresolved-not_satisfied-satisfied-not_satisfied" .atMost 0 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-1-4-unresolved-not_satisfied-satisfied-not_satisfied" .atMost 1 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-2-4-unresolved-not_satisfied-satisfied-not_satisfied" .atMost 2 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-3-4-unresolved-not_satisfied-satisfied-not_satisfied" .atMost 3 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "at-most-4-4-unresolved-not_satisfied-satisfied-not_satisfied" .atMost 4 [.unresolved, .notSatisfied, .satisfied, .notSatisfied]
]

def vectorChunk131 : List Vector := [
  .cardinality "at-most-5-4-unresolved-not_satisfied-satisfied-not_satisfied" .atMost 5 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-0-4-unresolved-not_satisfied-satisfied-not_satisfied" .exactly 0 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-1-4-unresolved-not_satisfied-satisfied-not_satisfied" .exactly 1 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-2-4-unresolved-not_satisfied-satisfied-not_satisfied" .exactly 2 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-3-4-unresolved-not_satisfied-satisfied-not_satisfied" .exactly 3 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-4-4-unresolved-not_satisfied-satisfied-not_satisfied" .exactly 4 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .cardinality "exactly-5-4-unresolved-not_satisfied-satisfied-not_satisfied" .exactly 5 [.unresolved, .notSatisfied, .satisfied, .notSatisfied],
  .quantifier "forall-4-unresolved-not_satisfied-satisfied-unresolved" .forall [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .quantifier "exists-4-unresolved-not_satisfied-satisfied-unresolved" .exists [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-0-4-unresolved-not_satisfied-satisfied-unresolved" .atLeast 0 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-1-4-unresolved-not_satisfied-satisfied-unresolved" .atLeast 1 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-2-4-unresolved-not_satisfied-satisfied-unresolved" .atLeast 2 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-3-4-unresolved-not_satisfied-satisfied-unresolved" .atLeast 3 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-4-4-unresolved-not_satisfied-satisfied-unresolved" .atLeast 4 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-least-5-4-unresolved-not_satisfied-satisfied-unresolved" .atLeast 5 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-0-4-unresolved-not_satisfied-satisfied-unresolved" .atMost 0 [.unresolved, .notSatisfied, .satisfied, .unresolved]
]

def vectorChunk132 : List Vector := [
  .cardinality "at-most-1-4-unresolved-not_satisfied-satisfied-unresolved" .atMost 1 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-2-4-unresolved-not_satisfied-satisfied-unresolved" .atMost 2 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-3-4-unresolved-not_satisfied-satisfied-unresolved" .atMost 3 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-4-4-unresolved-not_satisfied-satisfied-unresolved" .atMost 4 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "at-most-5-4-unresolved-not_satisfied-satisfied-unresolved" .atMost 5 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-0-4-unresolved-not_satisfied-satisfied-unresolved" .exactly 0 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-1-4-unresolved-not_satisfied-satisfied-unresolved" .exactly 1 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-2-4-unresolved-not_satisfied-satisfied-unresolved" .exactly 2 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-3-4-unresolved-not_satisfied-satisfied-unresolved" .exactly 3 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-4-4-unresolved-not_satisfied-satisfied-unresolved" .exactly 4 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .cardinality "exactly-5-4-unresolved-not_satisfied-satisfied-unresolved" .exactly 5 [.unresolved, .notSatisfied, .satisfied, .unresolved],
  .quantifier "forall-4-unresolved-not_satisfied-not_satisfied-satisfied" .forall [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .quantifier "exists-4-unresolved-not_satisfied-not_satisfied-satisfied" .exists [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-0-4-unresolved-not_satisfied-not_satisfied-satisfied" .atLeast 0 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-1-4-unresolved-not_satisfied-not_satisfied-satisfied" .atLeast 1 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-2-4-unresolved-not_satisfied-not_satisfied-satisfied" .atLeast 2 [.unresolved, .notSatisfied, .notSatisfied, .satisfied]
]

def vectorChunk133 : List Vector := [
  .cardinality "at-least-3-4-unresolved-not_satisfied-not_satisfied-satisfied" .atLeast 3 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-4-4-unresolved-not_satisfied-not_satisfied-satisfied" .atLeast 4 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-least-5-4-unresolved-not_satisfied-not_satisfied-satisfied" .atLeast 5 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-0-4-unresolved-not_satisfied-not_satisfied-satisfied" .atMost 0 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-1-4-unresolved-not_satisfied-not_satisfied-satisfied" .atMost 1 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-2-4-unresolved-not_satisfied-not_satisfied-satisfied" .atMost 2 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-3-4-unresolved-not_satisfied-not_satisfied-satisfied" .atMost 3 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-4-4-unresolved-not_satisfied-not_satisfied-satisfied" .atMost 4 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "at-most-5-4-unresolved-not_satisfied-not_satisfied-satisfied" .atMost 5 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-0-4-unresolved-not_satisfied-not_satisfied-satisfied" .exactly 0 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-1-4-unresolved-not_satisfied-not_satisfied-satisfied" .exactly 1 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-2-4-unresolved-not_satisfied-not_satisfied-satisfied" .exactly 2 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-3-4-unresolved-not_satisfied-not_satisfied-satisfied" .exactly 3 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-4-4-unresolved-not_satisfied-not_satisfied-satisfied" .exactly 4 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .cardinality "exactly-5-4-unresolved-not_satisfied-not_satisfied-satisfied" .exactly 5 [.unresolved, .notSatisfied, .notSatisfied, .satisfied],
  .quantifier "forall-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .forall [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk134 : List Vector := [
  .quantifier "exists-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .exists [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atLeast 0 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atLeast 1 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atLeast 2 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-3-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atLeast 3 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atLeast 4 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atLeast 5 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atMost 0 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-1-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atMost 1 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atMost 2 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atMost 3 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atMost 4 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "at-most-5-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .atMost 5 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .exactly 0 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .exactly 1 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .exactly 2 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied]
]

def vectorChunk135 : List Vector := [
  .cardinality "exactly-3-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .exactly 3 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .exactly 4 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-4-unresolved-not_satisfied-not_satisfied-not_satisfied" .exactly 5 [.unresolved, .notSatisfied, .notSatisfied, .notSatisfied],
  .quantifier "forall-4-unresolved-not_satisfied-not_satisfied-unresolved" .forall [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .quantifier "exists-4-unresolved-not_satisfied-not_satisfied-unresolved" .exists [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-0-4-unresolved-not_satisfied-not_satisfied-unresolved" .atLeast 0 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-1-4-unresolved-not_satisfied-not_satisfied-unresolved" .atLeast 1 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-2-4-unresolved-not_satisfied-not_satisfied-unresolved" .atLeast 2 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-3-4-unresolved-not_satisfied-not_satisfied-unresolved" .atLeast 3 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-4-4-unresolved-not_satisfied-not_satisfied-unresolved" .atLeast 4 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-least-5-4-unresolved-not_satisfied-not_satisfied-unresolved" .atLeast 5 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-0-4-unresolved-not_satisfied-not_satisfied-unresolved" .atMost 0 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-1-4-unresolved-not_satisfied-not_satisfied-unresolved" .atMost 1 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-2-4-unresolved-not_satisfied-not_satisfied-unresolved" .atMost 2 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-3-4-unresolved-not_satisfied-not_satisfied-unresolved" .atMost 3 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "at-most-4-4-unresolved-not_satisfied-not_satisfied-unresolved" .atMost 4 [.unresolved, .notSatisfied, .notSatisfied, .unresolved]
]

def vectorChunk136 : List Vector := [
  .cardinality "at-most-5-4-unresolved-not_satisfied-not_satisfied-unresolved" .atMost 5 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-0-4-unresolved-not_satisfied-not_satisfied-unresolved" .exactly 0 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-1-4-unresolved-not_satisfied-not_satisfied-unresolved" .exactly 1 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-2-4-unresolved-not_satisfied-not_satisfied-unresolved" .exactly 2 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-3-4-unresolved-not_satisfied-not_satisfied-unresolved" .exactly 3 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-4-4-unresolved-not_satisfied-not_satisfied-unresolved" .exactly 4 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .cardinality "exactly-5-4-unresolved-not_satisfied-not_satisfied-unresolved" .exactly 5 [.unresolved, .notSatisfied, .notSatisfied, .unresolved],
  .quantifier "forall-4-unresolved-not_satisfied-unresolved-satisfied" .forall [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .quantifier "exists-4-unresolved-not_satisfied-unresolved-satisfied" .exists [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-0-4-unresolved-not_satisfied-unresolved-satisfied" .atLeast 0 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-1-4-unresolved-not_satisfied-unresolved-satisfied" .atLeast 1 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-2-4-unresolved-not_satisfied-unresolved-satisfied" .atLeast 2 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-3-4-unresolved-not_satisfied-unresolved-satisfied" .atLeast 3 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-4-4-unresolved-not_satisfied-unresolved-satisfied" .atLeast 4 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-least-5-4-unresolved-not_satisfied-unresolved-satisfied" .atLeast 5 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-0-4-unresolved-not_satisfied-unresolved-satisfied" .atMost 0 [.unresolved, .notSatisfied, .unresolved, .satisfied]
]

def vectorChunk137 : List Vector := [
  .cardinality "at-most-1-4-unresolved-not_satisfied-unresolved-satisfied" .atMost 1 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-2-4-unresolved-not_satisfied-unresolved-satisfied" .atMost 2 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-3-4-unresolved-not_satisfied-unresolved-satisfied" .atMost 3 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-4-4-unresolved-not_satisfied-unresolved-satisfied" .atMost 4 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "at-most-5-4-unresolved-not_satisfied-unresolved-satisfied" .atMost 5 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-0-4-unresolved-not_satisfied-unresolved-satisfied" .exactly 0 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-1-4-unresolved-not_satisfied-unresolved-satisfied" .exactly 1 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-2-4-unresolved-not_satisfied-unresolved-satisfied" .exactly 2 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-3-4-unresolved-not_satisfied-unresolved-satisfied" .exactly 3 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-4-4-unresolved-not_satisfied-unresolved-satisfied" .exactly 4 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .cardinality "exactly-5-4-unresolved-not_satisfied-unresolved-satisfied" .exactly 5 [.unresolved, .notSatisfied, .unresolved, .satisfied],
  .quantifier "forall-4-unresolved-not_satisfied-unresolved-not_satisfied" .forall [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .quantifier "exists-4-unresolved-not_satisfied-unresolved-not_satisfied" .exists [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-0-4-unresolved-not_satisfied-unresolved-not_satisfied" .atLeast 0 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-1-4-unresolved-not_satisfied-unresolved-not_satisfied" .atLeast 1 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-2-4-unresolved-not_satisfied-unresolved-not_satisfied" .atLeast 2 [.unresolved, .notSatisfied, .unresolved, .notSatisfied]
]

def vectorChunk138 : List Vector := [
  .cardinality "at-least-3-4-unresolved-not_satisfied-unresolved-not_satisfied" .atLeast 3 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-4-4-unresolved-not_satisfied-unresolved-not_satisfied" .atLeast 4 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-least-5-4-unresolved-not_satisfied-unresolved-not_satisfied" .atLeast 5 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-0-4-unresolved-not_satisfied-unresolved-not_satisfied" .atMost 0 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-1-4-unresolved-not_satisfied-unresolved-not_satisfied" .atMost 1 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-2-4-unresolved-not_satisfied-unresolved-not_satisfied" .atMost 2 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-3-4-unresolved-not_satisfied-unresolved-not_satisfied" .atMost 3 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-4-4-unresolved-not_satisfied-unresolved-not_satisfied" .atMost 4 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "at-most-5-4-unresolved-not_satisfied-unresolved-not_satisfied" .atMost 5 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-0-4-unresolved-not_satisfied-unresolved-not_satisfied" .exactly 0 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-1-4-unresolved-not_satisfied-unresolved-not_satisfied" .exactly 1 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-2-4-unresolved-not_satisfied-unresolved-not_satisfied" .exactly 2 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-3-4-unresolved-not_satisfied-unresolved-not_satisfied" .exactly 3 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-4-4-unresolved-not_satisfied-unresolved-not_satisfied" .exactly 4 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .cardinality "exactly-5-4-unresolved-not_satisfied-unresolved-not_satisfied" .exactly 5 [.unresolved, .notSatisfied, .unresolved, .notSatisfied],
  .quantifier "forall-4-unresolved-not_satisfied-unresolved-unresolved" .forall [.unresolved, .notSatisfied, .unresolved, .unresolved]
]

def vectorChunk139 : List Vector := [
  .quantifier "exists-4-unresolved-not_satisfied-unresolved-unresolved" .exists [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-0-4-unresolved-not_satisfied-unresolved-unresolved" .atLeast 0 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-1-4-unresolved-not_satisfied-unresolved-unresolved" .atLeast 1 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-2-4-unresolved-not_satisfied-unresolved-unresolved" .atLeast 2 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-3-4-unresolved-not_satisfied-unresolved-unresolved" .atLeast 3 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-4-4-unresolved-not_satisfied-unresolved-unresolved" .atLeast 4 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-least-5-4-unresolved-not_satisfied-unresolved-unresolved" .atLeast 5 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-0-4-unresolved-not_satisfied-unresolved-unresolved" .atMost 0 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-1-4-unresolved-not_satisfied-unresolved-unresolved" .atMost 1 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-2-4-unresolved-not_satisfied-unresolved-unresolved" .atMost 2 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-3-4-unresolved-not_satisfied-unresolved-unresolved" .atMost 3 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-4-4-unresolved-not_satisfied-unresolved-unresolved" .atMost 4 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "at-most-5-4-unresolved-not_satisfied-unresolved-unresolved" .atMost 5 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-0-4-unresolved-not_satisfied-unresolved-unresolved" .exactly 0 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-1-4-unresolved-not_satisfied-unresolved-unresolved" .exactly 1 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-2-4-unresolved-not_satisfied-unresolved-unresolved" .exactly 2 [.unresolved, .notSatisfied, .unresolved, .unresolved]
]

def vectorChunk140 : List Vector := [
  .cardinality "exactly-3-4-unresolved-not_satisfied-unresolved-unresolved" .exactly 3 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-4-4-unresolved-not_satisfied-unresolved-unresolved" .exactly 4 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .cardinality "exactly-5-4-unresolved-not_satisfied-unresolved-unresolved" .exactly 5 [.unresolved, .notSatisfied, .unresolved, .unresolved],
  .quantifier "forall-4-unresolved-unresolved-satisfied-satisfied" .forall [.unresolved, .unresolved, .satisfied, .satisfied],
  .quantifier "exists-4-unresolved-unresolved-satisfied-satisfied" .exists [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-0-4-unresolved-unresolved-satisfied-satisfied" .atLeast 0 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-1-4-unresolved-unresolved-satisfied-satisfied" .atLeast 1 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-2-4-unresolved-unresolved-satisfied-satisfied" .atLeast 2 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-3-4-unresolved-unresolved-satisfied-satisfied" .atLeast 3 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-4-4-unresolved-unresolved-satisfied-satisfied" .atLeast 4 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-least-5-4-unresolved-unresolved-satisfied-satisfied" .atLeast 5 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-0-4-unresolved-unresolved-satisfied-satisfied" .atMost 0 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-1-4-unresolved-unresolved-satisfied-satisfied" .atMost 1 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-2-4-unresolved-unresolved-satisfied-satisfied" .atMost 2 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-3-4-unresolved-unresolved-satisfied-satisfied" .atMost 3 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "at-most-4-4-unresolved-unresolved-satisfied-satisfied" .atMost 4 [.unresolved, .unresolved, .satisfied, .satisfied]
]

def vectorChunk141 : List Vector := [
  .cardinality "at-most-5-4-unresolved-unresolved-satisfied-satisfied" .atMost 5 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-0-4-unresolved-unresolved-satisfied-satisfied" .exactly 0 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-1-4-unresolved-unresolved-satisfied-satisfied" .exactly 1 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-2-4-unresolved-unresolved-satisfied-satisfied" .exactly 2 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-3-4-unresolved-unresolved-satisfied-satisfied" .exactly 3 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-4-4-unresolved-unresolved-satisfied-satisfied" .exactly 4 [.unresolved, .unresolved, .satisfied, .satisfied],
  .cardinality "exactly-5-4-unresolved-unresolved-satisfied-satisfied" .exactly 5 [.unresolved, .unresolved, .satisfied, .satisfied],
  .quantifier "forall-4-unresolved-unresolved-satisfied-not_satisfied" .forall [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .quantifier "exists-4-unresolved-unresolved-satisfied-not_satisfied" .exists [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-0-4-unresolved-unresolved-satisfied-not_satisfied" .atLeast 0 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-1-4-unresolved-unresolved-satisfied-not_satisfied" .atLeast 1 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-2-4-unresolved-unresolved-satisfied-not_satisfied" .atLeast 2 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-3-4-unresolved-unresolved-satisfied-not_satisfied" .atLeast 3 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-4-4-unresolved-unresolved-satisfied-not_satisfied" .atLeast 4 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-least-5-4-unresolved-unresolved-satisfied-not_satisfied" .atLeast 5 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-0-4-unresolved-unresolved-satisfied-not_satisfied" .atMost 0 [.unresolved, .unresolved, .satisfied, .notSatisfied]
]

def vectorChunk142 : List Vector := [
  .cardinality "at-most-1-4-unresolved-unresolved-satisfied-not_satisfied" .atMost 1 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-2-4-unresolved-unresolved-satisfied-not_satisfied" .atMost 2 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-3-4-unresolved-unresolved-satisfied-not_satisfied" .atMost 3 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-4-4-unresolved-unresolved-satisfied-not_satisfied" .atMost 4 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "at-most-5-4-unresolved-unresolved-satisfied-not_satisfied" .atMost 5 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-0-4-unresolved-unresolved-satisfied-not_satisfied" .exactly 0 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-1-4-unresolved-unresolved-satisfied-not_satisfied" .exactly 1 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-2-4-unresolved-unresolved-satisfied-not_satisfied" .exactly 2 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-3-4-unresolved-unresolved-satisfied-not_satisfied" .exactly 3 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-4-4-unresolved-unresolved-satisfied-not_satisfied" .exactly 4 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .cardinality "exactly-5-4-unresolved-unresolved-satisfied-not_satisfied" .exactly 5 [.unresolved, .unresolved, .satisfied, .notSatisfied],
  .quantifier "forall-4-unresolved-unresolved-satisfied-unresolved" .forall [.unresolved, .unresolved, .satisfied, .unresolved],
  .quantifier "exists-4-unresolved-unresolved-satisfied-unresolved" .exists [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-0-4-unresolved-unresolved-satisfied-unresolved" .atLeast 0 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-1-4-unresolved-unresolved-satisfied-unresolved" .atLeast 1 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-2-4-unresolved-unresolved-satisfied-unresolved" .atLeast 2 [.unresolved, .unresolved, .satisfied, .unresolved]
]

def vectorChunk143 : List Vector := [
  .cardinality "at-least-3-4-unresolved-unresolved-satisfied-unresolved" .atLeast 3 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-4-4-unresolved-unresolved-satisfied-unresolved" .atLeast 4 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-least-5-4-unresolved-unresolved-satisfied-unresolved" .atLeast 5 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-0-4-unresolved-unresolved-satisfied-unresolved" .atMost 0 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-1-4-unresolved-unresolved-satisfied-unresolved" .atMost 1 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-2-4-unresolved-unresolved-satisfied-unresolved" .atMost 2 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-3-4-unresolved-unresolved-satisfied-unresolved" .atMost 3 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-4-4-unresolved-unresolved-satisfied-unresolved" .atMost 4 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "at-most-5-4-unresolved-unresolved-satisfied-unresolved" .atMost 5 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-0-4-unresolved-unresolved-satisfied-unresolved" .exactly 0 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-1-4-unresolved-unresolved-satisfied-unresolved" .exactly 1 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-2-4-unresolved-unresolved-satisfied-unresolved" .exactly 2 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-3-4-unresolved-unresolved-satisfied-unresolved" .exactly 3 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-4-4-unresolved-unresolved-satisfied-unresolved" .exactly 4 [.unresolved, .unresolved, .satisfied, .unresolved],
  .cardinality "exactly-5-4-unresolved-unresolved-satisfied-unresolved" .exactly 5 [.unresolved, .unresolved, .satisfied, .unresolved],
  .quantifier "forall-4-unresolved-unresolved-not_satisfied-satisfied" .forall [.unresolved, .unresolved, .notSatisfied, .satisfied]
]

def vectorChunk144 : List Vector := [
  .quantifier "exists-4-unresolved-unresolved-not_satisfied-satisfied" .exists [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-0-4-unresolved-unresolved-not_satisfied-satisfied" .atLeast 0 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-1-4-unresolved-unresolved-not_satisfied-satisfied" .atLeast 1 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-2-4-unresolved-unresolved-not_satisfied-satisfied" .atLeast 2 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-3-4-unresolved-unresolved-not_satisfied-satisfied" .atLeast 3 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-4-4-unresolved-unresolved-not_satisfied-satisfied" .atLeast 4 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-least-5-4-unresolved-unresolved-not_satisfied-satisfied" .atLeast 5 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-0-4-unresolved-unresolved-not_satisfied-satisfied" .atMost 0 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-1-4-unresolved-unresolved-not_satisfied-satisfied" .atMost 1 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-2-4-unresolved-unresolved-not_satisfied-satisfied" .atMost 2 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-3-4-unresolved-unresolved-not_satisfied-satisfied" .atMost 3 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-4-4-unresolved-unresolved-not_satisfied-satisfied" .atMost 4 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "at-most-5-4-unresolved-unresolved-not_satisfied-satisfied" .atMost 5 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-0-4-unresolved-unresolved-not_satisfied-satisfied" .exactly 0 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-1-4-unresolved-unresolved-not_satisfied-satisfied" .exactly 1 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-2-4-unresolved-unresolved-not_satisfied-satisfied" .exactly 2 [.unresolved, .unresolved, .notSatisfied, .satisfied]
]

def vectorChunk145 : List Vector := [
  .cardinality "exactly-3-4-unresolved-unresolved-not_satisfied-satisfied" .exactly 3 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-4-4-unresolved-unresolved-not_satisfied-satisfied" .exactly 4 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .cardinality "exactly-5-4-unresolved-unresolved-not_satisfied-satisfied" .exactly 5 [.unresolved, .unresolved, .notSatisfied, .satisfied],
  .quantifier "forall-4-unresolved-unresolved-not_satisfied-not_satisfied" .forall [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .quantifier "exists-4-unresolved-unresolved-not_satisfied-not_satisfied" .exists [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-0-4-unresolved-unresolved-not_satisfied-not_satisfied" .atLeast 0 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-1-4-unresolved-unresolved-not_satisfied-not_satisfied" .atLeast 1 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-2-4-unresolved-unresolved-not_satisfied-not_satisfied" .atLeast 2 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-3-4-unresolved-unresolved-not_satisfied-not_satisfied" .atLeast 3 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-4-4-unresolved-unresolved-not_satisfied-not_satisfied" .atLeast 4 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-least-5-4-unresolved-unresolved-not_satisfied-not_satisfied" .atLeast 5 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-0-4-unresolved-unresolved-not_satisfied-not_satisfied" .atMost 0 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-1-4-unresolved-unresolved-not_satisfied-not_satisfied" .atMost 1 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-2-4-unresolved-unresolved-not_satisfied-not_satisfied" .atMost 2 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-3-4-unresolved-unresolved-not_satisfied-not_satisfied" .atMost 3 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "at-most-4-4-unresolved-unresolved-not_satisfied-not_satisfied" .atMost 4 [.unresolved, .unresolved, .notSatisfied, .notSatisfied]
]

def vectorChunk146 : List Vector := [
  .cardinality "at-most-5-4-unresolved-unresolved-not_satisfied-not_satisfied" .atMost 5 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-0-4-unresolved-unresolved-not_satisfied-not_satisfied" .exactly 0 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-1-4-unresolved-unresolved-not_satisfied-not_satisfied" .exactly 1 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-2-4-unresolved-unresolved-not_satisfied-not_satisfied" .exactly 2 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-3-4-unresolved-unresolved-not_satisfied-not_satisfied" .exactly 3 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-4-4-unresolved-unresolved-not_satisfied-not_satisfied" .exactly 4 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .cardinality "exactly-5-4-unresolved-unresolved-not_satisfied-not_satisfied" .exactly 5 [.unresolved, .unresolved, .notSatisfied, .notSatisfied],
  .quantifier "forall-4-unresolved-unresolved-not_satisfied-unresolved" .forall [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .quantifier "exists-4-unresolved-unresolved-not_satisfied-unresolved" .exists [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-0-4-unresolved-unresolved-not_satisfied-unresolved" .atLeast 0 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-1-4-unresolved-unresolved-not_satisfied-unresolved" .atLeast 1 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-2-4-unresolved-unresolved-not_satisfied-unresolved" .atLeast 2 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-3-4-unresolved-unresolved-not_satisfied-unresolved" .atLeast 3 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-4-4-unresolved-unresolved-not_satisfied-unresolved" .atLeast 4 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-least-5-4-unresolved-unresolved-not_satisfied-unresolved" .atLeast 5 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-0-4-unresolved-unresolved-not_satisfied-unresolved" .atMost 0 [.unresolved, .unresolved, .notSatisfied, .unresolved]
]

def vectorChunk147 : List Vector := [
  .cardinality "at-most-1-4-unresolved-unresolved-not_satisfied-unresolved" .atMost 1 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-2-4-unresolved-unresolved-not_satisfied-unresolved" .atMost 2 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-3-4-unresolved-unresolved-not_satisfied-unresolved" .atMost 3 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-4-4-unresolved-unresolved-not_satisfied-unresolved" .atMost 4 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "at-most-5-4-unresolved-unresolved-not_satisfied-unresolved" .atMost 5 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-0-4-unresolved-unresolved-not_satisfied-unresolved" .exactly 0 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-1-4-unresolved-unresolved-not_satisfied-unresolved" .exactly 1 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-2-4-unresolved-unresolved-not_satisfied-unresolved" .exactly 2 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-3-4-unresolved-unresolved-not_satisfied-unresolved" .exactly 3 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-4-4-unresolved-unresolved-not_satisfied-unresolved" .exactly 4 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .cardinality "exactly-5-4-unresolved-unresolved-not_satisfied-unresolved" .exactly 5 [.unresolved, .unresolved, .notSatisfied, .unresolved],
  .quantifier "forall-4-unresolved-unresolved-unresolved-satisfied" .forall [.unresolved, .unresolved, .unresolved, .satisfied],
  .quantifier "exists-4-unresolved-unresolved-unresolved-satisfied" .exists [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-0-4-unresolved-unresolved-unresolved-satisfied" .atLeast 0 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-1-4-unresolved-unresolved-unresolved-satisfied" .atLeast 1 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-2-4-unresolved-unresolved-unresolved-satisfied" .atLeast 2 [.unresolved, .unresolved, .unresolved, .satisfied]
]

def vectorChunk148 : List Vector := [
  .cardinality "at-least-3-4-unresolved-unresolved-unresolved-satisfied" .atLeast 3 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-4-4-unresolved-unresolved-unresolved-satisfied" .atLeast 4 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-least-5-4-unresolved-unresolved-unresolved-satisfied" .atLeast 5 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-0-4-unresolved-unresolved-unresolved-satisfied" .atMost 0 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-1-4-unresolved-unresolved-unresolved-satisfied" .atMost 1 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-2-4-unresolved-unresolved-unresolved-satisfied" .atMost 2 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-3-4-unresolved-unresolved-unresolved-satisfied" .atMost 3 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-4-4-unresolved-unresolved-unresolved-satisfied" .atMost 4 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "at-most-5-4-unresolved-unresolved-unresolved-satisfied" .atMost 5 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-0-4-unresolved-unresolved-unresolved-satisfied" .exactly 0 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-1-4-unresolved-unresolved-unresolved-satisfied" .exactly 1 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-2-4-unresolved-unresolved-unresolved-satisfied" .exactly 2 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-3-4-unresolved-unresolved-unresolved-satisfied" .exactly 3 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-4-4-unresolved-unresolved-unresolved-satisfied" .exactly 4 [.unresolved, .unresolved, .unresolved, .satisfied],
  .cardinality "exactly-5-4-unresolved-unresolved-unresolved-satisfied" .exactly 5 [.unresolved, .unresolved, .unresolved, .satisfied],
  .quantifier "forall-4-unresolved-unresolved-unresolved-not_satisfied" .forall [.unresolved, .unresolved, .unresolved, .notSatisfied]
]

def vectorChunk149 : List Vector := [
  .quantifier "exists-4-unresolved-unresolved-unresolved-not_satisfied" .exists [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-0-4-unresolved-unresolved-unresolved-not_satisfied" .atLeast 0 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-1-4-unresolved-unresolved-unresolved-not_satisfied" .atLeast 1 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-2-4-unresolved-unresolved-unresolved-not_satisfied" .atLeast 2 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-3-4-unresolved-unresolved-unresolved-not_satisfied" .atLeast 3 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-4-4-unresolved-unresolved-unresolved-not_satisfied" .atLeast 4 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-least-5-4-unresolved-unresolved-unresolved-not_satisfied" .atLeast 5 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-0-4-unresolved-unresolved-unresolved-not_satisfied" .atMost 0 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-1-4-unresolved-unresolved-unresolved-not_satisfied" .atMost 1 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-2-4-unresolved-unresolved-unresolved-not_satisfied" .atMost 2 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-3-4-unresolved-unresolved-unresolved-not_satisfied" .atMost 3 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-4-4-unresolved-unresolved-unresolved-not_satisfied" .atMost 4 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "at-most-5-4-unresolved-unresolved-unresolved-not_satisfied" .atMost 5 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-0-4-unresolved-unresolved-unresolved-not_satisfied" .exactly 0 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-1-4-unresolved-unresolved-unresolved-not_satisfied" .exactly 1 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-2-4-unresolved-unresolved-unresolved-not_satisfied" .exactly 2 [.unresolved, .unresolved, .unresolved, .notSatisfied]
]

def vectorChunk150 : List Vector := [
  .cardinality "exactly-3-4-unresolved-unresolved-unresolved-not_satisfied" .exactly 3 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-4-4-unresolved-unresolved-unresolved-not_satisfied" .exactly 4 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .cardinality "exactly-5-4-unresolved-unresolved-unresolved-not_satisfied" .exactly 5 [.unresolved, .unresolved, .unresolved, .notSatisfied],
  .quantifier "forall-4-unresolved-unresolved-unresolved-unresolved" .forall [.unresolved, .unresolved, .unresolved, .unresolved],
  .quantifier "exists-4-unresolved-unresolved-unresolved-unresolved" .exists [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-0-4-unresolved-unresolved-unresolved-unresolved" .atLeast 0 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-1-4-unresolved-unresolved-unresolved-unresolved" .atLeast 1 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-2-4-unresolved-unresolved-unresolved-unresolved" .atLeast 2 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-3-4-unresolved-unresolved-unresolved-unresolved" .atLeast 3 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-4-4-unresolved-unresolved-unresolved-unresolved" .atLeast 4 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-least-5-4-unresolved-unresolved-unresolved-unresolved" .atLeast 5 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-0-4-unresolved-unresolved-unresolved-unresolved" .atMost 0 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-1-4-unresolved-unresolved-unresolved-unresolved" .atMost 1 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-2-4-unresolved-unresolved-unresolved-unresolved" .atMost 2 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-3-4-unresolved-unresolved-unresolved-unresolved" .atMost 3 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "at-most-4-4-unresolved-unresolved-unresolved-unresolved" .atMost 4 [.unresolved, .unresolved, .unresolved, .unresolved]
]

def vectorChunk151 : List Vector := [
  .cardinality "at-most-5-4-unresolved-unresolved-unresolved-unresolved" .atMost 5 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-0-4-unresolved-unresolved-unresolved-unresolved" .exactly 0 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-1-4-unresolved-unresolved-unresolved-unresolved" .exactly 1 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-2-4-unresolved-unresolved-unresolved-unresolved" .exactly 2 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-3-4-unresolved-unresolved-unresolved-unresolved" .exactly 3 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-4-4-unresolved-unresolved-unresolved-unresolved" .exactly 4 [.unresolved, .unresolved, .unresolved, .unresolved],
  .cardinality "exactly-5-4-unresolved-unresolved-unresolved-unresolved" .exactly 5 [.unresolved, .unresolved, .unresolved, .unresolved],
  .comparison "integer-eq-0-0" .equal (.integer 0) (.integer 0),
  .comparison "integer-eq-0-1" .equal (.integer 0) (.integer 1),
  .comparison "integer-eq-0-2" .equal (.integer 0) (.integer 2),
  .comparison "integer-eq-1-0" .equal (.integer 1) (.integer 0),
  .comparison "integer-eq-1-1" .equal (.integer 1) (.integer 1),
  .comparison "integer-eq-1-2" .equal (.integer 1) (.integer 2),
  .comparison "integer-eq-2-0" .equal (.integer 2) (.integer 0),
  .comparison "integer-eq-2-1" .equal (.integer 2) (.integer 1),
  .comparison "integer-eq-2-2" .equal (.integer 2) (.integer 2)
]

def vectorChunk152 : List Vector := [
  .comparison "unresolved-eq" .equal (.unresolved) (.integer 1),
  .comparison "integer-neq-0-0" .notEqual (.integer 0) (.integer 0),
  .comparison "integer-neq-0-1" .notEqual (.integer 0) (.integer 1),
  .comparison "integer-neq-0-2" .notEqual (.integer 0) (.integer 2),
  .comparison "integer-neq-1-0" .notEqual (.integer 1) (.integer 0),
  .comparison "integer-neq-1-1" .notEqual (.integer 1) (.integer 1),
  .comparison "integer-neq-1-2" .notEqual (.integer 1) (.integer 2),
  .comparison "integer-neq-2-0" .notEqual (.integer 2) (.integer 0),
  .comparison "integer-neq-2-1" .notEqual (.integer 2) (.integer 1),
  .comparison "integer-neq-2-2" .notEqual (.integer 2) (.integer 2),
  .comparison "unresolved-neq" .notEqual (.unresolved) (.integer 1),
  .comparison "integer-lt-0-0" .lessThan (.integer 0) (.integer 0),
  .comparison "integer-lt-0-1" .lessThan (.integer 0) (.integer 1),
  .comparison "integer-lt-0-2" .lessThan (.integer 0) (.integer 2),
  .comparison "integer-lt-1-0" .lessThan (.integer 1) (.integer 0),
  .comparison "integer-lt-1-1" .lessThan (.integer 1) (.integer 1)
]

def vectorChunk153 : List Vector := [
  .comparison "integer-lt-1-2" .lessThan (.integer 1) (.integer 2),
  .comparison "integer-lt-2-0" .lessThan (.integer 2) (.integer 0),
  .comparison "integer-lt-2-1" .lessThan (.integer 2) (.integer 1),
  .comparison "integer-lt-2-2" .lessThan (.integer 2) (.integer 2),
  .comparison "unresolved-lt" .lessThan (.unresolved) (.integer 1),
  .comparison "integer-lte-0-0" .lessEqual (.integer 0) (.integer 0),
  .comparison "integer-lte-0-1" .lessEqual (.integer 0) (.integer 1),
  .comparison "integer-lte-0-2" .lessEqual (.integer 0) (.integer 2),
  .comparison "integer-lte-1-0" .lessEqual (.integer 1) (.integer 0),
  .comparison "integer-lte-1-1" .lessEqual (.integer 1) (.integer 1),
  .comparison "integer-lte-1-2" .lessEqual (.integer 1) (.integer 2),
  .comparison "integer-lte-2-0" .lessEqual (.integer 2) (.integer 0),
  .comparison "integer-lte-2-1" .lessEqual (.integer 2) (.integer 1),
  .comparison "integer-lte-2-2" .lessEqual (.integer 2) (.integer 2),
  .comparison "unresolved-lte" .lessEqual (.unresolved) (.integer 1),
  .comparison "integer-gt-0-0" .greaterThan (.integer 0) (.integer 0)
]

def vectorChunk154 : List Vector := [
  .comparison "integer-gt-0-1" .greaterThan (.integer 0) (.integer 1),
  .comparison "integer-gt-0-2" .greaterThan (.integer 0) (.integer 2),
  .comparison "integer-gt-1-0" .greaterThan (.integer 1) (.integer 0),
  .comparison "integer-gt-1-1" .greaterThan (.integer 1) (.integer 1),
  .comparison "integer-gt-1-2" .greaterThan (.integer 1) (.integer 2),
  .comparison "integer-gt-2-0" .greaterThan (.integer 2) (.integer 0),
  .comparison "integer-gt-2-1" .greaterThan (.integer 2) (.integer 1),
  .comparison "integer-gt-2-2" .greaterThan (.integer 2) (.integer 2),
  .comparison "unresolved-gt" .greaterThan (.unresolved) (.integer 1),
  .comparison "integer-gte-0-0" .greaterEqual (.integer 0) (.integer 0),
  .comparison "integer-gte-0-1" .greaterEqual (.integer 0) (.integer 1),
  .comparison "integer-gte-0-2" .greaterEqual (.integer 0) (.integer 2),
  .comparison "integer-gte-1-0" .greaterEqual (.integer 1) (.integer 0),
  .comparison "integer-gte-1-1" .greaterEqual (.integer 1) (.integer 1),
  .comparison "integer-gte-1-2" .greaterEqual (.integer 1) (.integer 2),
  .comparison "integer-gte-2-0" .greaterEqual (.integer 2) (.integer 0)
]

def vectorChunk155 : List Vector := [
  .comparison "integer-gte-2-1" .greaterEqual (.integer 2) (.integer 1),
  .comparison "integer-gte-2-2" .greaterEqual (.integer 2) (.integer 2),
  .comparison "unresolved-gte" .greaterEqual (.unresolved) (.integer 1),
  .comparison "date-eq" .equal (.date 20000) (.date 20001),
  .comparison "money-eq" .equal (.money "SGD" 5000) (.money "SGD" 5001),
  .comparison "date-neq" .notEqual (.date 20000) (.date 20001),
  .comparison "money-neq" .notEqual (.money "SGD" 5000) (.money "SGD" 5001),
  .comparison "date-lt" .lessThan (.date 20000) (.date 20001),
  .comparison "money-lt" .lessThan (.money "SGD" 5000) (.money "SGD" 5001),
  .comparison "date-lte" .lessEqual (.date 20000) (.date 20001),
  .comparison "money-lte" .lessEqual (.money "SGD" 5000) (.money "SGD" 5001),
  .comparison "date-gt" .greaterThan (.date 20000) (.date 20001),
  .comparison "money-gt" .greaterThan (.money "SGD" 5000) (.money "SGD" 5001),
  .comparison "date-gte" .greaterEqual (.date 20000) (.date 20001),
  .comparison "money-gte" .greaterEqual (.money "SGD" 5000) (.money "SGD" 5001),
  .comparison "enum-eq" .equal (.enumValue "risk" "high") (.enumValue "risk" "low")
]

def vectorChunk156 : List Vector := [
  .comparison "enum-neq" .notEqual (.enumValue "risk" "high") (.enumValue "risk" "low"),
  .priority "priority-higher-defeat" ({ identifier := "r:high", proposition := "p:target", polarity := .defeat, status := .satisfied }) ({ identifier := "r:low", proposition := "p:target", polarity := .establish, status := .satisfied }) true,
  .priority "priority-higher-establish" ({ identifier := "r:high", proposition := "p:target", polarity := .establish, status := .satisfied }) ({ identifier := "r:low", proposition := "p:target", polarity := .defeat, status := .satisfied }) true,
  .priority "priority-higher-unresolved" ({ identifier := "r:high", proposition := "p:target", polarity := .defeat, status := .unresolved }) ({ identifier := "r:low", proposition := "p:target", polarity := .establish, status := .satisfied }) true,
  .priority "priority-higher-fails" ({ identifier := "r:high", proposition := "p:target", polarity := .defeat, status := .notSatisfied }) ({ identifier := "r:low", proposition := "p:target", polarity := .establish, status := .satisfied }) true,
  .priority "priority-incomparable-conflict" ({ identifier := "r:left", proposition := "p:target", polarity := .establish, status := .satisfied }) ({ identifier := "r:right", proposition := "p:target", polarity := .defeat, status := .satisfied }) false,
  .priority "priority-diamond-left-edge" ({ identifier := "r:top-left", proposition := "p:target", polarity := .defeat, status := .satisfied }) ({ identifier := "r:base", proposition := "p:target", polarity := .establish, status := .satisfied }) true,
  .priority "priority-diamond-right-edge" ({ identifier := "r:top-right", proposition := "p:target", polarity := .defeat, status := .unresolved }) ({ identifier := "r:base", proposition := "p:target", polarity := .establish, status := .satisfied }) true,
  .priority "priority-chain-top-edge" ({ identifier := "r:top", proposition := "p:target", polarity := .defeat, status := .satisfied }) ({ identifier := "r:middle", proposition := "p:target", polarity := .establish, status := .satisfied }) true,
  .priority "priority-chain-middle-edge" ({ identifier := "r:middle", proposition := "p:target", polarity := .establish, status := .satisfied }) ({ identifier := "r:bottom", proposition := "p:target", polarity := .defeat, status := .satisfied }) true,
  .substitution "substitution-variable" "var:item" "item:laptop" { identifier := "var:item", typeName := "property" },
  .substitution "substitution-entity" "var:item" "item:laptop" { identifier := "item:fixed", typeName := "property" },
  .isolation "actor-isolation-satisfied" "actor:one/p:fact" [("actor:one/p:fact", .satisfied), ("actor:two/p:fact", .satisfied)],
  .isolation "allegation-isolation-satisfied" "a:one/p:fact" [("a:one/p:fact", .satisfied), ("a:two/p:fact", .notSatisfied)],
  .isolation "actor-isolation-not_satisfied" "actor:one/p:fact" [("actor:one/p:fact", .notSatisfied), ("actor:two/p:fact", .satisfied)],
  .isolation "allegation-isolation-not_satisfied" "a:one/p:fact" [("a:one/p:fact", .notSatisfied), ("a:two/p:fact", .notSatisfied)]
]

def vectorChunk157 : List Vector := [
  .isolation "actor-isolation-unresolved" "actor:one/p:fact" [("actor:one/p:fact", .unresolved), ("actor:two/p:fact", .satisfied)],
  .isolation "allegation-isolation-unresolved" "a:one/p:fact" [("a:one/p:fact", .unresolved), ("a:two/p:fact", .notSatisfied)]
]

def vectors : List Vector := vectorChunk0 ++ vectorChunk1 ++ vectorChunk2 ++ vectorChunk3 ++ vectorChunk4 ++ vectorChunk5 ++ vectorChunk6 ++ vectorChunk7 ++ vectorChunk8 ++ vectorChunk9 ++ vectorChunk10 ++ vectorChunk11 ++ vectorChunk12 ++ vectorChunk13 ++ vectorChunk14 ++ vectorChunk15 ++ vectorChunk16 ++ vectorChunk17 ++ vectorChunk18 ++ vectorChunk19 ++ vectorChunk20 ++ vectorChunk21 ++ vectorChunk22 ++ vectorChunk23 ++ vectorChunk24 ++ vectorChunk25 ++ vectorChunk26 ++ vectorChunk27 ++ vectorChunk28 ++ vectorChunk29 ++ vectorChunk30 ++ vectorChunk31 ++ vectorChunk32 ++ vectorChunk33 ++ vectorChunk34 ++ vectorChunk35 ++ vectorChunk36 ++ vectorChunk37 ++ vectorChunk38 ++ vectorChunk39 ++ vectorChunk40 ++ vectorChunk41 ++ vectorChunk42 ++ vectorChunk43 ++ vectorChunk44 ++ vectorChunk45 ++ vectorChunk46 ++ vectorChunk47 ++ vectorChunk48 ++ vectorChunk49 ++ vectorChunk50 ++ vectorChunk51 ++ vectorChunk52 ++ vectorChunk53 ++ vectorChunk54 ++ vectorChunk55 ++ vectorChunk56 ++ vectorChunk57 ++ vectorChunk58 ++ vectorChunk59 ++ vectorChunk60 ++ vectorChunk61 ++ vectorChunk62 ++ vectorChunk63 ++ vectorChunk64 ++ vectorChunk65 ++ vectorChunk66 ++ vectorChunk67 ++ vectorChunk68 ++ vectorChunk69 ++ vectorChunk70 ++ vectorChunk71 ++ vectorChunk72 ++ vectorChunk73 ++ vectorChunk74 ++ vectorChunk75 ++ vectorChunk76 ++ vectorChunk77 ++ vectorChunk78 ++ vectorChunk79 ++ vectorChunk80 ++ vectorChunk81 ++ vectorChunk82 ++ vectorChunk83 ++ vectorChunk84 ++ vectorChunk85 ++ vectorChunk86 ++ vectorChunk87 ++ vectorChunk88 ++ vectorChunk89 ++ vectorChunk90 ++ vectorChunk91 ++ vectorChunk92 ++ vectorChunk93 ++ vectorChunk94 ++ vectorChunk95 ++ vectorChunk96 ++ vectorChunk97 ++ vectorChunk98 ++ vectorChunk99 ++ vectorChunk100 ++ vectorChunk101 ++ vectorChunk102 ++ vectorChunk103 ++ vectorChunk104 ++ vectorChunk105 ++ vectorChunk106 ++ vectorChunk107 ++ vectorChunk108 ++ vectorChunk109 ++ vectorChunk110 ++ vectorChunk111 ++ vectorChunk112 ++ vectorChunk113 ++ vectorChunk114 ++ vectorChunk115 ++ vectorChunk116 ++ vectorChunk117 ++ vectorChunk118 ++ vectorChunk119 ++ vectorChunk120 ++ vectorChunk121 ++ vectorChunk122 ++ vectorChunk123 ++ vectorChunk124 ++ vectorChunk125 ++ vectorChunk126 ++ vectorChunk127 ++ vectorChunk128 ++ vectorChunk129 ++ vectorChunk130 ++ vectorChunk131 ++ vectorChunk132 ++ vectorChunk133 ++ vectorChunk134 ++ vectorChunk135 ++ vectorChunk136 ++ vectorChunk137 ++ vectorChunk138 ++ vectorChunk139 ++ vectorChunk140 ++ vectorChunk141 ++ vectorChunk142 ++ vectorChunk143 ++ vectorChunk144 ++ vectorChunk145 ++ vectorChunk146 ++ vectorChunk147 ++ vectorChunk148 ++ vectorChunk149 ++ vectorChunk150 ++ vectorChunk151 ++ vectorChunk152 ++ vectorChunk153 ++ vectorChunk154 ++ vectorChunk155 ++ vectorChunk156 ++ vectorChunk157

end Yuho.CoreYuho.TypedFinite.Conformance
