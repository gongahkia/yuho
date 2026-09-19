"""Deterministic synthetic sixth-fragment requests; prior fixtures are read only."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TERMS = HERE.parent / "term-fixtures" / "requests"
OUT = HERE
CASES = {}
VECTORS = {}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False,
                               indent=2 if path.parent.name != "requests" else None,
                               separators=None if path.parent.name != "requests" else (",", ":"))
                    + "\n", encoding="utf-8")


def source(span, number, index=0):
    return {"assignment_id": f"assignment:{number}:{index}",
            "source_id": "src:main", "span": copy.deepcopy(span),
            "origin": "synthetic_fixture", "issuer_label": "synthetic classification"}


def binding(status, number, index=0, span=None):
    if span is None:
        span = copy.deepcopy(BASE_SPAN)
    return {"proof_status": copy.deepcopy(status),
            "status_source": source(span, number, index)}


S = {"kind": "proved"}
N = {"kind": "not_proved"}
U = {"kind": "unresolved", "reason": "not_determined"}
PENDING = {"kind": "unresolved", "reason": "external_decision_pending"}
BASE_SPAN = json.loads((TERMS / "PT01.json").read_text())["registry"][0]["program"]["requirements"][0]["span"]


def load(number, base):
    request = json.loads((TERMS / f"{base}.json").read_text(encoding="utf-8"))
    request["fragment"] = "SuppliedProofStatus-v1"
    request["request_id"] = f"S{number:02d}"
    request["facts"] = {leaf: binding(S if item["value"] else N, number, index)
                        for index, (leaf, item) in enumerate(sorted(request["facts"].items()))}
    return request


def add(label, base="PT01", mutate=None, status="satisfied", code="", selected=None):
    number = len(CASES) + 1
    name = f"PS{number:02d}"
    request = load(number, base)
    if mutate:
        mutate(request)
    if selected is None:
        selected = ["pen:root:1"] if status == "satisfied" else []
    if status == "rejected":
        selected = []
    CASES[name] = {"label": label, "file": f"requests/{name}.json",
                   "status": status, "code": code, "selected": selected}
    write(OUT / "requests" / f"{name}.json", request)
    return request


def set_status(request, leaf, status):
    request["facts"][leaf]["proof_status"] = copy.deepcopy(status)


def second_leaf(request, status=S):
    program = request["registry"][0]["program"]
    second = copy.deepcopy(program["requirements"][0])
    second["id"] = "f:second"
    request["facts"]["f:second"] = binding(status, int(request["request_id"][1:]), 9)
    return second


def pair(request, left, right, kind):
    program = request["registry"][0]["program"]
    second = second_leaf(request, right)
    group = {"id": "group:pair", "kind": kind, "path": ["root"],
             "span": copy.deepcopy(program["span"]),
             "members": [program["requirements"][0], second]}
    program["requirements"] = [group]
    set_status(request, "f:root", left)


def nested_requirement(request):
    program = request["registry"][0]["program"]
    original = program["requirements"][0]
    second = second_leaf(request, U)
    third = copy.deepcopy(original)
    third["id"] = "f:third"
    request["facts"]["f:third"] = binding(S, int(request["request_id"][1:]), 10)
    any_group = {"id": "group:any", "kind": "any", "path": ["root"],
                 "span": copy.deepcopy(program["span"]), "members": [original, second]}
    program["requirements"] = [{"id": "group:all", "kind": "all", "path": ["root"],
                                "span": copy.deepcopy(program["span"]),
                                "members": [any_group, third]}]


def add_target(request, status):
    target = copy.deepcopy(request["registry"][1])
    target["id"] = "r:pending"
    target["program"]["id"] = "p:pending"
    target["program"]["path"] = ["pending"]
    target["program"]["requirements"][0]["id"] = "f:pending"
    target["program"]["requirements"][0]["path"] = ["pending"]
    target["exceptions"] = []
    target["program"]["penalties"] = []
    request["registry"].append(target)
    request["facts"]["f:pending"] = binding(status, int(request["request_id"][1:]), 9)
    extra = copy.deepcopy(request["registry"][0]["exceptions"][0])
    extra["id"] = "x:root:2"
    extra["guard"]["target"] = "r:pending"
    request["registry"][0]["exceptions"].append(extra)


def declare_both(request):
    declaration = {"burden": {"holder": "prosecution", "kind": "legal"},
                   "standard_of_proof": "beyond_reasonable_doubt"}
    request["registry"][0]["program"]["requirements"][0]["declared_metadata"] = declaration
    request["facts"]["f:root"].update(copy.deepcopy(declaration))


def raw_case(label, source_name, raw, code):
    name = f"PS{len(CASES) + 1:02d}"
    path = OUT / "requests" / f"{name}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    CASES[name] = {"label": label, "file": f"requests/{name}.txt",
                   "status": "rejected", "code": code, "selected": []}


def requirement_edges(node):
    return [[node["id"], child["id"], i]
            for i, child in enumerate(node.get("members", []))] + [edge
            for child in node.get("members", []) for edge in requirement_edges(child)]


def requirement_preorder(node):
    return [node["id"], *[identifier for child in node.get("members", [])
                          for identifier in requirement_preorder(child)]]


def executable_branches(program, inherited=()):
    direct = [*inherited, *program["requirements"]]
    descendants = [branch for child in program["children"]
                   for branch in executable_branches(child, direct)]
    if descendants:
        return descendants
    return [(program["id"], direct)] if direct else []


def walk(program):
    yield program
    for child in program["children"]:
        yield from walk(child)


def make_cases():
    add("proved classification")
    add("not proved is technical non-satisfaction", mutate=lambda r: set_status(r, "f:root", N), status="not_satisfied")
    add("unresolved not determined", mutate=lambda r: set_status(r, "f:root", U), status="unresolved")
    add("unresolved external decision pending", mutate=lambda r: set_status(r, "f:root", PENDING), status="unresolved")
    for kind in ("all", "any"):
        for left in (S, N, U):
            for right in (S, N, U):
                pair_status = ("not_satisfied" if N in (left, right) else
                               "unresolved" if U in (left, right) else "satisfied") if kind == "all" else (
                               "satisfied" if S in (left, right) else
                               "unresolved" if U in (left, right) else "not_satisfied")
                add(f"{kind} pair {left['kind']} / {right['kind']}",
                    mutate=lambda r, a=left, b=right, k=kind: pair(r, a, b, k),
                    status=pair_status)
    add("nested All/Any and full leaf traces", mutate=nested_requirement)
    add("alternative branch retains satisfied inherited support", "PT17",
        mutate=lambda r: set_status(r, "f:second", U))
    add("decisive All failure retains unresolved child", mutate=lambda r: pair(r, N, U, "all"), status="not_satisfied")
    add("decisive Any success retains unresolved child", mutate=lambda r: pair(r, S, U, "any"))
    add("definition-only is not vacuously satisfied", mutate=lambda r: (
        r["registry"][0]["program"].update({"requirements": [], "definitions": True}),
        r["facts"].clear()), status="not_satisfied")
    add("satisfied exception target defeats", "PT18", status="not_satisfied")
    add("not-proved target does not defeat", "PT18",
        mutate=lambda r: set_status(r, "f:target", N))
    add("unresolved exception target propagates", "PT18",
        mutate=lambda r: set_status(r, "f:target", U), status="unresolved")
    add("satisfied plus unresolved exceptions: all inspected", "PT18",
        mutate=lambda r: add_target(r, U), status="not_satisfied")
    add("unresolved ordinary requirements skip exceptions", "PT18",
        mutate=lambda r: set_status(r, "f:root", U), status="unresolved")
    def guarded_pair(r, guard_status):
        pair(r, S, guard_status, "any")
        r["registry"][0]["program"]["penalties"][0]["guard"] = {
            "kind": "leaf_true", "leaf_id": "f:second"}
    add("Any satisfied while penalty guard unresolved", mutate=lambda r: guarded_pair(r, U), selected=[])
    add("Any satisfied while penalty guard not proved", mutate=lambda r: guarded_pair(r, N), selected=[])
    add("Any satisfied and penalty guard proved", mutate=lambda r: guarded_pair(r, S))
    add("matching burden and standard", mutate=declare_both)
    add("mismatched burden holder", mutate=lambda r: (declare_both(r), r["facts"]["f:root"]["burden"].update(
        {"holder": "defence"})), status="rejected", code="KINV007")
    add("mismatched standard", mutate=lambda r: (declare_both(r), r["facts"]["f:root"].update(
        {"standard_of_proof": "balance_of_probabilities"})), status="rejected", code="KINV007")
    add("missing declared burden on unresolved status", mutate=lambda r: (declare_both(r),
        r["facts"]["f:root"].pop("burden"), set_status(r, "f:root", U)),
        status="rejected", code="KINV007")
    add("unreachable rule assignment metadata is checked", "PT20",
        mutate=lambda r: (r["registry"][1]["program"]["requirements"][0].update(
            {"declared_metadata": {"standard_of_proof": "beyond_reasonable_doubt"}}),
            r["facts"]["f:target"].update({"standard_of_proof": "balance_of_probabilities"})),
        status="rejected", code="KINV007")
    add("missing leaf binding", mutate=lambda r: r["facts"].pop("f:root"), status="rejected", code="KINV001")
    add("extra leaf binding", mutate=lambda r: r["facts"].update({"f:extra": binding(S, int(r["request_id"][1:]), 9)}),
        status="rejected", code="KINV004")
    add("normalized names do not match exact leaf IDs", mutate=lambda r: r["facts"].update(
        {"f_root": r["facts"].pop("f:root")}), status="rejected", code="KINV001")
    add("duplicate assignment IDs", mutate=lambda r: (pair(r, S, S, "all"),
        r["facts"]["f:second"]["status_source"].update({"assignment_id":
            r["facts"]["f:root"]["status_source"]["assignment_id"]})),
        status="rejected", code="KINV010")
    add("status source reference missing", mutate=lambda r: r["facts"]["f:root"]["status_source"].update(
        {"source_id": "src:missing"}), status="rejected", code="KINV010")
    add("status source span invalid", mutate=lambda r: r["facts"]["f:root"]["status_source"]["span"].update(
        {"end": 999}), status="rejected", code="KINV010")
    add("status source missing issuer", mutate=lambda r: r["facts"]["f:root"]["status_source"].pop(
        "issuer_label"), status="rejected", code="KDEC001")
    add("status source unknown origin", mutate=lambda r: r["facts"]["f:root"]["status_source"].update(
        {"origin": "court_verified"}), status="rejected", code="KDEC001")
    add("presumed is deferred capability", mutate=lambda r: set_status(r, "f:root", {"kind": "presumed"}),
        status="rejected", code="KCAP001")
    add("rebutted is deferred capability", mutate=lambda r: set_status(r, "f:root", {"kind": "rebutted"}),
        status="rejected", code="KCAP001")
    add("unknown proof constructor", mutate=lambda r: set_status(r, "f:root", {"kind": "unknown"}),
        status="rejected", code="KDEC001")
    add("bare status string rejected", mutate=lambda r: set_status(r, "f:root", "proved"),
        status="rejected", code="KDEC001")
    add("Boolean value excluded", mutate=lambda r: r["facts"]["f:root"].update({"value": True}),
        status="rejected", code="KINV004")
    add("Boolean type excluded", mutate=lambda r: r["facts"]["f:root"].update({"type": "bool"}),
        status="rejected", code="KINV004")
    add("confidence excluded", mutate=lambda r: r["facts"]["f:root"].update({"confidence": "0.9"}),
        status="rejected", code="KINV004")
    add("unknown request field", mutate=lambda r: r.update({"unknown": 1}), status="rejected", code="KINV004")
    add("non-BMP descriptive issuer and provenance", mutate=lambda r: (r["facts"]["f:root"]["status_source"].update(
        {"issuer_label": "synthetic 📜"}), r["facts"]["f:root"].update(
        {"provenance": {"source_label": "label 📜"}})))
    add("invalid term in dependency target rejects before evaluation", "PT20",
        mutate=lambda r: r["registry"][1]["program"]["penalties"][0]["term"]["maximum"].update(
            {"value": 0}), status="rejected", code="KINV009")
    add("missing exception target remains invariant rejection", "PT18",
        mutate=lambda r: r["registry"][0]["exceptions"][0]["guard"].update({"target": "r:missing"}),
        status="rejected", code="KINV005")
    add("cycle remains invariant rejection", "PT18", mutate=lambda r: r["registry"][1]["exceptions"].append(
        {**copy.deepcopy(r["registry"][0]["exceptions"][0]), "id": "x:target:1",
         "branch_id": "p:target", "guard": {"kind": "is_infringed", "target": "r:root"}}),
        status="rejected", code="KINV006")
    add("rejected malformed status reason", mutate=lambda r: set_status(r, "f:root",
        {"kind": "unresolved", "reason": "missing_target"}), status="rejected", code="KDEC001")
    add("unresolved provenance and metadata do not change projection", mutate=lambda r: (
        set_status(r, "f:root", U), r["facts"]["f:root"].update(
            {"provenance": {"recorded_date": "2024-02-29", "jurisdiction": "SG"}})),
        status="unresolved")
    original = (OUT / "requests" / "PS01.json").read_bytes()
    raw_case("duplicate JSON key in status", "PS01", original.replace(
        b'"kind":"proved"', b'"kind":"proved","kind":"proved"', 1), "KDEC001")
    raw_case("malformed JSON", "PS01", original[:-3] + b"\n", "KDEC001")
    raw_case("request byte limit", "PS01", original.replace(
        b'"request_id":"S01"', b'"request_id":"S01' + b'X' * 1048576 + b'"'), "KDEC002")
    raw_case("malformed surrogate", "PS01", original.replace(
        b'"issuer_label":"synthetic classification"', b'"issuer_label":"\\ud800"', 1), "KDEC001")
    add("missing required proof status", mutate=lambda r: r["facts"]["f:root"].pop(
        "proof_status"), status="rejected", code="KDEC001")
    add("assignment ID collides with leaf identity", mutate=lambda r: r["facts"]["f:root"][
        "status_source"].update({"assignment_id": "f:root"}), status="rejected", code="KINV010")
    add("empty descriptive issuer", mutate=lambda r: r["facts"]["f:root"]["status_source"].update(
        {"issuer_label": ""}), status="rejected", code="KDEC001")
    add("legacy evidential status excluded", mutate=lambda r: r["facts"]["f:root"].update(
        {"evidential_status": "proved"}), status="rejected", code="KINV004")
    add("unknown status-source field", mutate=lambda r: r["facts"]["f:root"]["status_source"].update(
        {"authority": "unverified"}), status="rejected", code="KINV004")
    add("inconsistent assignment byte and display positions", mutate=lambda r: r["facts"]["f:root"][
        "status_source"]["span"].update({"start": 1, "end": 2}), status="rejected", code="KINV010")


def vectors():
    for name, case in CASES.items():
        vector = {"expected_status": case["status"], "invalid_classification": case["code"],
                  "selected_ids": case["selected"], "bindings": {}, "projection": {},
                  "requirement_edges": [], "dependency_edges": [], "term_ids": [],
                  "declaration_order": [], "source_order": [], "expected_trace_order": {}}
        if case["file"].endswith(".json"):
            request = json.loads((OUT / case["file"]).read_text(encoding="utf-8"))
            vector["bindings"] = request["facts"]
            vector["projection"] = {leaf: {"proved": "satisfied", "not_proved": "not_satisfied",
                "unresolved": "unresolved"}.get(binding["proof_status"].get("kind"))
                for leaf, binding in request["facts"].items()
                if isinstance(binding, dict) and isinstance(binding.get("proof_status"), dict)}
            vector["source_order"] = [item["id"] for item in request["sources"]]
            for rule in request["registry"]:
                vector["expected_trace_order"][rule["id"]] = {branch_id:
                    [identifier for requirement in requirements
                     for identifier in requirement_preorder(requirement)]
                    for branch_id, requirements in executable_branches(rule["program"])}
                vector["dependency_edges"].extend([[rule["id"], ex["guard"].get("target"), ex["id"]]
                    for ex in rule["exceptions"] if isinstance(ex.get("guard"), dict)])
                for provision in walk(rule["program"]):
                    vector["requirement_edges"].extend(edge for item in provision["requirements"]
                        for edge in requirement_edges(item))
                    for penalty in provision["penalties"]:
                        vector["declaration_order"].append(penalty["penalty_id"])
                        def term_ids(term):
                            if "term_id" in term:
                                yield term["term_id"]
                            for child in term.get("terms", []):
                                yield from term_ids(child)
                        if "term" in penalty:
                            vector["term_ids"].extend(term_ids(penalty["term"]))
        VECTORS[name] = vector
    VECTORS["PS24"]["expected_branch_statuses"] = [
        ["p:first", "satisfied"], ["p:second", "unresolved"]]
    VECTORS["PS28"]["expected_exception_statuses"] = ["satisfied"]
    VECTORS["PS29"]["expected_exception_statuses"] = ["not_satisfied"]
    VECTORS["PS30"]["expected_exception_statuses"] = ["unresolved"]
    VECTORS["PS31"]["expected_exception_statuses"] = ["satisfied", "unresolved"]
    VECTORS["PS01"]["expected_selection_trace"] = [
        ["pen:root:1", "p:root", "selected"]]
    VECTORS["PS28"]["expected_selection_trace"] = [
        ["pen:root:1", "p:root", "branch_exception_defeated"]]
    VECTORS["PS33"]["expected_selection_trace"] = [
        ["pen:root:1", "p:root", "guard_unresolved"]]


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    OUT = args.output
    make_cases()
    vectors()
    write(OUT / "CASES.json", CASES)
    write(OUT / "PROOF-VECTORS.json", VECTORS)
    paths = [OUT / "CASES.json", OUT / "PROOF-VECTORS.json", *sorted((OUT / "requests").iterdir())]
    files = {str(path.relative_to(OUT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    files["generate.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write(OUT / "MANIFEST.json", {"format": "yuho.ps-fixtures/v1", "files": files})


if __name__ == "__main__":
    main()
