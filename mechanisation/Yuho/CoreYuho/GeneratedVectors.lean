/- Generated input-only conformance vectors. Do not add expected results. -/
import Yuho.CoreYuho.Conformance

namespace Yuho.CoreYuho.Conformance

set_option maxHeartbeats 1000000

def vectorChunk0 : List Vector := [
  .aggregate "all-empty" .all [],
  .aggregate "all-satisfied-satisfied" .all [.satisfied, .satisfied],
  .aggregate "all-satisfied-not_satisfied" .all [.satisfied, .notSatisfied],
  .aggregate "all-satisfied-unresolved" .all [.satisfied, .unresolved],
  .aggregate "all-not_satisfied-satisfied" .all [.notSatisfied, .satisfied],
  .aggregate "all-not_satisfied-not_satisfied" .all [.notSatisfied, .notSatisfied],
  .aggregate "all-not_satisfied-unresolved" .all [.notSatisfied, .unresolved],
  .aggregate "all-unresolved-satisfied" .all [.unresolved, .satisfied],
  .aggregate "all-unresolved-not_satisfied" .all [.unresolved, .notSatisfied],
  .aggregate "all-unresolved-unresolved" .all [.unresolved, .unresolved],
  .aggregate "any-empty" .any [],
  .aggregate "any-satisfied-satisfied" .any [.satisfied, .satisfied]
]

def vectorChunk1 : List Vector := [
  .aggregate "any-satisfied-not_satisfied" .any [.satisfied, .notSatisfied],
  .aggregate "any-satisfied-unresolved" .any [.satisfied, .unresolved],
  .aggregate "any-not_satisfied-satisfied" .any [.notSatisfied, .satisfied],
  .aggregate "any-not_satisfied-not_satisfied" .any [.notSatisfied, .notSatisfied],
  .aggregate "any-not_satisfied-unresolved" .any [.notSatisfied, .unresolved],
  .aggregate "any-unresolved-satisfied" .any [.unresolved, .satisfied],
  .aggregate "any-unresolved-not_satisfied" .any [.unresolved, .notSatisfied],
  .aggregate "any-unresolved-unresolved" .any [.unresolved, .unresolved],
  .aggregate "branch-0" .branch [],
  .aggregate "branch-1" .branch [.notSatisfied],
  .aggregate "branch-2" .branch [.unresolved, .notSatisfied],
  .aggregate "branch-3" .branch [.satisfied, .unresolved]
]

def vectorChunk2 : List Vector := [
  .aggregate "guard-0" .guard [],
  .aggregate "guard-1" .guard [.notSatisfied],
  .aggregate "guard-2" .guard [.unresolved],
  .aggregate "guard-3" .guard [.satisfied, .unresolved],
  .requirement "tree-00" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .satisfied), ("f:c", .satisfied)],
  .requirement "tree-01" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .satisfied), ("f:c", .notSatisfied)],
  .requirement "tree-02" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .satisfied), ("f:c", .unresolved)],
  .requirement "tree-03" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .notSatisfied), ("f:c", .satisfied)],
  .requirement "tree-04" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .notSatisfied), ("f:c", .notSatisfied)],
  .requirement "tree-05" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .notSatisfied), ("f:c", .unresolved)],
  .requirement "tree-06" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .unresolved), ("f:c", .satisfied)],
  .requirement "tree-07" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .unresolved), ("f:c", .notSatisfied)]
]

def vectorChunk3 : List Vector := [
  .requirement "tree-08" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .unresolved), ("f:c", .unresolved)],
  .requirement "tree-09" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .satisfied), ("f:c", .satisfied)],
  .requirement "tree-10" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .satisfied), ("f:c", .notSatisfied)],
  .requirement "tree-11" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .satisfied), ("f:c", .unresolved)],
  .requirement "tree-12" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .notSatisfied), ("f:c", .satisfied)],
  .requirement "tree-13" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .notSatisfied), ("f:c", .notSatisfied)],
  .requirement "tree-14" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .notSatisfied), ("f:c", .unresolved)],
  .requirement "tree-15" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .unresolved), ("f:c", .satisfied)],
  .requirement "tree-16" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .unresolved), ("f:c", .notSatisfied)],
  .requirement "tree-17" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .unresolved), ("f:c", .unresolved)],
  .requirement "tree-18" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .unresolved), ("f:b", .satisfied), ("f:c", .satisfied)],
  .requirement "tree-19" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .unresolved), ("f:b", .satisfied), ("f:c", .notSatisfied)]
]

def vectorChunk4 : List Vector := [
  .requirement "tree-20" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .unresolved), ("f:b", .satisfied), ("f:c", .unresolved)],
  .requirement "tree-21" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .unresolved), ("f:b", .notSatisfied), ("f:c", .satisfied)],
  .requirement "tree-22" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .unresolved), ("f:b", .notSatisfied), ("f:c", .notSatisfied)],
  .requirement "tree-23" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .unresolved), ("f:b", .notSatisfied), ("f:c", .unresolved)],
  .requirement "tree-24" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .unresolved), ("f:b", .unresolved), ("f:c", .satisfied)],
  .requirement "tree-25" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .unresolved), ("f:b", .unresolved), ("f:c", .notSatisfied)],
  .requirement "tree-26" "requirement" (.all "g:root" [.input "f:a", .any "g:choice" [.input "f:b", .input "f:c"]]) [("f:a", .unresolved), ("f:b", .unresolved), ("f:c", .unresolved)],
  .requirement "definition-chain-satisfied" "definition" (.all "d:chain" [.input "f:a", .input "f:b"]) [("f:a", .satisfied), ("f:b", .satisfied)],
  .requirement "definition-chain-unresolved" "definition" (.all "d:chain" [.input "f:a", .input "f:b"]) [("f:a", .satisfied), ("f:b", .unresolved)],
  .requirement "definition-diamond-satisfied" "definition" (.all "d:diamond" [.any "d:left" [.input "f:a", .input "f:b"], .any "d:right" [.input "f:a", .input "f:c"]]) [("f:a", .satisfied), ("f:b", .notSatisfied), ("f:c", .unresolved)],
  .requirement "definition-diamond-failed" "definition" (.all "d:diamond" [.any "d:left" [.input "f:a", .input "f:b"], .any "d:right" [.input "f:a", .input "f:c"]]) [("f:a", .notSatisfied), ("f:b", .satisfied), ("f:c", .notSatisfied)],
  .requirement "definition-release-rash" "definition" (.all "g:rash" [.input "f:act", .input "f:rashness", .input "f:endangerment"]) [("f:act", .satisfied), ("f:endangerment", .satisfied), ("f:rashness", .satisfied)]
]

def vectorChunk5 : List Vector := [
  .requirement "definition-release-s84" "definition" (.all "g:s84" [.input "f:unsoundness", .input "f:incapacity"]) [("f:incapacity", .unresolved), ("f:unsoundness", .satisfied)],
  .exception "exception-satisfied-satisfied" .satisfied [.satisfied],
  .exception "exception-satisfied-not_satisfied" .satisfied [.notSatisfied],
  .exception "exception-satisfied-unresolved" .satisfied [.unresolved],
  .exception "exception-not_satisfied-satisfied" .notSatisfied [.satisfied],
  .exception "exception-not_satisfied-not_satisfied" .notSatisfied [.notSatisfied],
  .exception "exception-not_satisfied-unresolved" .notSatisfied [.unresolved],
  .exception "exception-unresolved-satisfied" .unresolved [.satisfied],
  .exception "exception-unresolved-not_satisfied" .unresolved [.notSatisfied],
  .exception "exception-unresolved-unresolved" .unresolved [.unresolved],
  .exception "exception-no-guard" .satisfied [],
  .presumption "presumption-satisfied-satisfied" .satisfied .satisfied
]

def vectorChunk6 : List Vector := [
  .presumption "presumption-satisfied-not_satisfied" .satisfied .notSatisfied,
  .presumption "presumption-satisfied-unresolved" .satisfied .unresolved,
  .presumption "presumption-not_satisfied-satisfied" .notSatisfied .satisfied,
  .presumption "presumption-not_satisfied-not_satisfied" .notSatisfied .notSatisfied,
  .presumption "presumption-not_satisfied-unresolved" .notSatisfied .unresolved,
  .presumption "presumption-unresolved-satisfied" .unresolved .satisfied,
  .presumption "presumption-unresolved-not_satisfied" .unresolved .notSatisfied,
  .presumption "presumption-unresolved-unresolved" .unresolved .unresolved,
  .scope "scope-isolation-0" { actor := "actor:one", role := "principal", context := "principal-conduct", instanceId := "xi:one" } "f:guard" [{ key := { actor := "actor:two", role := "principal", context := "attempt-conduct", instanceId := "xi:two" }, input := "f:guard", status := .satisfied }, { key := { actor := "actor:one", role := "principal", context := "principal-conduct", instanceId := "xi:one" }, input := "f:guard", status := .satisfied }],
  .scope "scope-isolation-1" { actor := "actor:one", role := "principal", context := "principal-conduct", instanceId := "xi:one" } "f:guard" [{ key := { actor := "actor:two", role := "principal", context := "attempt-conduct", instanceId := "xi:two" }, input := "f:guard", status := .satisfied }, { key := { actor := "actor:one", role := "principal", context := "principal-conduct", instanceId := "xi:one" }, input := "f:guard", status := .notSatisfied }],
  .scope "scope-isolation-2" { actor := "actor:one", role := "principal", context := "principal-conduct", instanceId := "xi:one" } "f:guard" [{ key := { actor := "actor:two", role := "principal", context := "attempt-conduct", instanceId := "xi:two" }, input := "f:guard", status := .satisfied }, { key := { actor := "actor:one", role := "principal", context := "principal-conduct", instanceId := "xi:one" }, input := "f:guard", status := .unresolved }],
  .scope "scope-input-isolation" { actor := "actor:one", role := "principal", context := "principal-conduct", instanceId := "xi:one" } "f:guard" [{ key := { actor := "actor:one", role := "principal", context := "principal-conduct", instanceId := "xi:one" }, input := "f:guard", status := .notSatisfied }, { key := { actor := "actor:one", role := "principal", context := "principal-conduct", instanceId := "xi:one" }, input := "f:other", status := .satisfied }]
]

def vectorChunk7 : List Vector := [
  .caseAnalysis "case-two" [{ identifier := "a:first", requirement := .input "f:a", assignments := [("f:a", .satisfied)] }, { identifier := "a:second", requirement := .input "f:b", assignments := [("f:b", .unresolved)] }],
  .caseAnalysis "case-reordered" [{ identifier := "a:second", requirement := .input "f:b", assignments := [("f:b", .unresolved)] }, { identifier := "a:first", requirement := .input "f:a", assignments := [("f:a", .satisfied)] }],
  .caseAnalysis "case-three" [{ identifier := "a:first", requirement := .input "f:a", assignments := [("f:a", .satisfied)] }, { identifier := "a:second", requirement := .input "f:b", assignments := [("f:b", .unresolved)] }, { identifier := "a:third", requirement := .input "f:c", assignments := [("f:c", .notSatisfied)] }],
  .temporal "temporal-lower" 10 [{ expression := "e:old", effectiveFrom := 10, effectiveTo := some 20, version := "1.0.0", supersedes := none }, { expression := "e:new", effectiveFrom := 20, effectiveTo := none, version := "9.9.9", supersedes := some "e:old" }],
  .temporal "temporal-before-boundary" 19 [{ expression := "e:old", effectiveFrom := 10, effectiveTo := some 20, version := "1.0.0", supersedes := none }, { expression := "e:new", effectiveFrom := 20, effectiveTo := none, version := "9.9.9", supersedes := some "e:old" }],
  .temporal "temporal-boundary" 20 [{ expression := "e:old", effectiveFrom := 10, effectiveTo := some 20, version := "1.0.0", supersedes := none }, { expression := "e:new", effectiveFrom := 20, effectiveTo := none, version := "9.9.9", supersedes := some "e:old" }],
  .temporal "temporal-open-end" 200 [{ expression := "e:old", effectiveFrom := 10, effectiveTo := some 20, version := "1.0.0", supersedes := none }, { expression := "e:new", effectiveFrom := 20, effectiveTo := none, version := "9.9.9", supersedes := some "e:old" }],
  .temporal "temporal-before-all" 9 [{ expression := "e:old", effectiveFrom := 10, effectiveTo := some 20, version := "1.0.0", supersedes := none }, { expression := "e:new", effectiveFrom := 20, effectiveTo := none, version := "9.9.9", supersedes := some "e:old" }],
  .temporal "temporal-gap" 25 [{ expression := "e:left", effectiveFrom := 10, effectiveTo := some 20, version := "2.0.0", supersedes := none }, { expression := "e:right", effectiveFrom := 30, effectiveTo := some 40, version := "1.0.0", supersedes := some "e:left" }],
  .temporal "temporal-overlap" 25 [{ expression := "e:first", effectiveFrom := 10, effectiveTo := some 30, version := "1.0.0", supersedes := none }, { expression := "e:second", effectiveFrom := 20, effectiveTo := some 40, version := "99.0.0", supersedes := some "e:first" }],
  .temporal "temporal-version-ignored" 20 [{ expression := "e:old", effectiveFrom := 10, effectiveTo := some 20, version := "1.0.0", supersedes := none }, { expression := "e:new", effectiveFrom := 20, effectiveTo := none, version := "9.9.9", supersedes := some "e:old" }]
]

def vectors : List Vector := vectorChunk0 ++ vectorChunk1 ++ vectorChunk2 ++ vectorChunk3 ++ vectorChunk4 ++ vectorChunk5 ++ vectorChunk6 ++ vectorChunk7

end Yuho.CoreYuho.Conformance
