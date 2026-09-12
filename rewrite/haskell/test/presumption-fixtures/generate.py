"""Deterministic synthetic seventh-fragment fixtures and proof-neutral vectors."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROOF = HERE.parent / "proof-fixtures" / "requests"
S = {"kind": "proved"}
N = {"kind": "not_proved"}
U = {"kind": "unresolved", "reason": "not_determined"}
SPAN = {"start": 0, "end": 1, "start_line": 1, "start_col": 1,
        "end_line": 1, "end_col": 2}
CASES = {}
VECTORS = {}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":") if path.parent.name == "requests" else None,
                               indent=None if path.parent.name == "requests" else 2) + "\n",
                    encoding="utf-8")


def leaf(identifier):
    return {"kind": "leaf_effective", "span": copy.deepcopy(SPAN),
            "leaf_id": identifier}


def group(kind, *children):
    return {"kind": kind, "span": copy.deepcopy(SPAN),
            "members": list(children)}


def route(identifier="pres:one", target="f:root", trigger="f:trigger",
          rebuttal="f:rebuttal"):
    return {"presumption_id": identifier, "target_leaf_id": target,
            "source_id": "src:main", "span": copy.deepcopy(SPAN),
            "trigger": leaf(trigger) if isinstance(trigger, str) else trigger,
            "rebuttal": leaf(rebuttal) if isinstance(rebuttal, str) else rebuttal}


def binding(status, number, index):
    return {"proof_status": copy.deepcopy(status), "status_source": {
        "assignment_id": f"assignment:rd:{number}:{index}",
        "source_id": "src:main", "span": copy.deepcopy(SPAN),
        "origin": "synthetic_fixture", "issuer_label": "synthetic classification"}}


def base(number, proof="PS01"):
    request = json.loads((PROOF / f"{proof}.json").read_text(encoding="utf-8"))
    request["fragment"] = "RegisteredPresumptionDerivations-v1"
    request["request_id"] = f"D{number:02d}"
    request["presumptions"] = []
    return request


def add_leaf(request, identifier, status):
    if identifier in request["facts"]:
        request["facts"][identifier]["proof_status"] = copy.deepcopy(status)
        return
    suffix = identifier.split(":")[-1]
    rule = copy.deepcopy(request["registry"][0])
    rule["id"] = "r:fixture_" + suffix
    rule["program"]["id"] = "p:fixture_" + suffix
    rule["program"]["path"] = ["fixture", suffix]
    requirement = rule["program"]["requirements"][0]
    if requirement["kind"] != "leaf":
        requirement = copy.deepcopy(request["registry"][0]["program"]["requirements"][0])
        if requirement["kind"] != "leaf":
            requirement = {"id": identifier, "kind": "leaf", "path": ["fixture", suffix],
                           "span": copy.deepcopy(SPAN)}
    requirement["id"] = identifier
    requirement["path"] = ["fixture", suffix]
    rule["program"]["requirements"] = [requirement]
    rule["program"]["children"] = []
    rule["program"]["penalties"] = []
    rule["exceptions"] = []
    request["registry"].append(rule)
    request["facts"][identifier] = binding(status, int(request["request_id"][1:]),
                                     len(request["facts"]))


def standard(request, direct=N, trigger=S, rebuttal=N):
    request["facts"]["f:root"]["proof_status"] = copy.deepcopy(direct)
    add_leaf(request, "f:trigger", trigger)
    add_leaf(request, "f:rebuttal", rebuttal)
    request["presumptions"] = [route()]


def add(label, mutation=None, status="satisfied", code="", states=None,
        proof="PS01", selected=None):
    number = len(CASES) + 1
    name = f"RD{number:02d}"
    request = base(number, proof)
    if mutation:
        mutation(request)
    if selected is None:
        selected = ["pen:root:1"] if status == "satisfied" else []
    if status == "rejected":
        selected = []
    CASES[name] = {"label": label, "file": f"requests/{name}.json",
                   "status": status, "code": code, "selected": selected,
                   "route_states": states or []}
    write(OUT / "requests" / f"{name}.json", request)
    return request


def add_raw(label, payload, code):
    name = f"RD{len(CASES) + 1:02d}"
    path = OUT / "requests" / f"{name}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    CASES[name] = {"label": label, "file": f"requests/{name}.txt",
                   "status": "rejected", "code": code, "selected": [],
                   "route_states": []}


def state(trigger, rebuttal):
    if trigger == "not_satisfied":
        return "inactive"
    if rebuttal == "satisfied":
        return "rebutted"
    if trigger == "satisfied" and rebuttal == "not_satisfied":
        return "active"
    return "unresolved"


def value(status):
    return {"proved": "satisfied", "not_proved": "not_satisfied",
            "unresolved": "unresolved"}[status["kind"]]


def all_of(values):
    return ("not_satisfied" if "not_satisfied" in values else
            "unresolved" if "unresolved" in values else "satisfied")


def any_of(values):
    return ("satisfied" if "satisfied" in values else
            "unresolved" if "unresolved" in values else "not_satisfied")


def simple_status(trigger, rebuttal, direct=N):
    route_state = state(value(trigger), value(rebuttal))
    return ("satisfied" if direct == S or route_state == "active" else
            "unresolved" if direct == U or route_state == "unresolved" else
            "not_satisfied")


def cases():
    add("empty registry preserves supplied projection")
    for trigger, rebuttal in ((N,N),(N,U),(N,S),(U,N),(U,U),(U,S),(S,N),(S,U),(S,S)):
        add(f"table trigger {value(trigger)} rebuttal {value(rebuttal)}",
            lambda r, t=trigger, b=rebuttal: standard(r, N, t, b),
            status=simple_status(trigger, rebuttal),
            states=[state(value(trigger), value(rebuttal))])
    for kind, operator in (("all_of", all_of), ("any_of", any_of)):
        for left in (S,N,U):
            for right in (S,N,U):
                combined = operator([value(left), value(right)])
                route_state = state(combined, "not_satisfied")
                expected = ("satisfied" if route_state == "active" else
                            "unresolved" if route_state == "unresolved" else "not_satisfied")
                def mutate(r, a=left, b=right, k=kind):
                    standard(r, N, a, b)
                    add_leaf(r, "f:third", N)
                    r["presumptions"][0]["trigger"] = group(k, leaf("f:trigger"),
                                                                 leaf("f:rebuttal"))
                    r["presumptions"][0]["rebuttal"] = leaf("f:third")
                add(f"{kind} pair {value(left)} {value(right)}", mutate,
                    status=expected, states=[route_state])
    add("direct satisfaction and active route coexist",
        lambda r: standard(r, S,S,N), states=["active"])
    add("direct unresolved with active route", lambda r: standard(r,U,S,N),
        states=["active"])
    add("direct unresolved without active route", lambda r: standard(r,U,N,N),
        status="unresolved", states=["inactive"])
    add("multiple active routes remain separate", lambda r: (
        standard(r), r["presumptions"].append(route("pres:two"))),
        states=["active","active"])
    add("active dominates unresolved route", lambda r: (
        standard(r), add_leaf(r,"f:pending",U),
        r["presumptions"].append(route("pres:two",trigger="f:pending"))),
        states=["active","unresolved"])
    add("rebutted and inactive routes do not negate", lambda r: (
        standard(r,N,S,S), add_leaf(r,"f:inactive",N),
        r["presumptions"].append(route("pres:two",trigger="f:inactive"))),
        status="not_satisfied", states=["rebutted","inactive"])
    add("one-step chained support", lambda r: (
        standard(r,N,N,N), add_leaf(r,"f:seed",S),
        r["presumptions"].append(route("pres:two",target="f:trigger",
                                         trigger="f:seed"))),
        states=["active","active"])
    add("multi-step acyclic chain in reverse declaration order", lambda r: (
        standard(r,N,N,N), add_leaf(r,"f:seed",S),
        add_leaf(r,"f:middle",N),
        r["presumptions"].append(route("pres:two",target="f:trigger",
                                         trigger="f:middle")),
        r["presumptions"].append(route("pres:three",target="f:middle",
                                         trigger="f:seed"))),
        states=["active","active","active"])
    add("chain through rebuttal disables root route", lambda r: (
        standard(r,N,S,N), add_leaf(r,"f:seed",S),
        add_leaf(r,"f:other",N),
        r["presumptions"].append(route("pres:two",target="f:rebuttal",
                                         trigger="f:seed",rebuttal="f:other"))),
        status="not_satisfied", states=["rebutted","active"])
    add("identical registrations with different IDs are distinct modeling routes",
        lambda r: (standard(r), r["presumptions"].append(route("pres:two"))),
        states=["active","active"])
    add("effective target satisfies exception and defeats root", lambda r: (
        add_leaf(r,"f:rebuttal",N),
        r["facts"]["f:target"].update({"proof_status": N}),
        r["presumptions"].append(route(target="f:target",trigger="f:root"))),
        status="not_satisfied", states=["active"], proof="PS28")
    add("effective guard selects penalty", lambda r: (
        add_leaf(r,"f:rebuttal",N),
        r["presumptions"].append(route(target="f:second",trigger="f:root"))),
        states=["active"], proof="PS33")
    add("unresolved effective guard skips penalty", lambda r: (
        add_leaf(r,"f:rebuttal",N), add_leaf(r,"f:trigger",U),
        r["presumptions"].append(route(target="f:second"))),
        states=["unresolved"], proof="PS33", selected=[])
    add("source order differs from dependency resolution", lambda r: (
        standard(r,N,N,N), add_leaf(r,"f:seed",S),
        r["presumptions"].append(route("pres:two",target="f:trigger",trigger="f:seed"))),
        states=["active","active"])
    add("non-BMP descriptive issuer survives canonical encoding", lambda r: (
        standard(r), r["facts"]["f:root"]["status_source"].update(
            {"issuer_label":"synthetic 📜"})), states=["active"])
    add("unreachable target registration is evaluated", lambda r: (
        standard(r), r["presumptions"].append(route("pres:two",target="f:rebuttal",
                                         trigger="f:trigger",rebuttal="f:trigger"))),
        states=["active","rebutted"])
    add("no short-circuit in decisive all and rebuttal", lambda r: (
        standard(r,N,N,S), add_leaf(r,"f:third",U),
        r["presumptions"][0].update({"trigger":group("all_of",leaf("f:trigger"),
                                                        leaf("f:third"))})),
        status="not_satisfied", states=["inactive"])

    def bad(label, mutation, code="KINV005"):
        add(label, lambda r: (standard(r), mutation(r)),
            status="rejected", code=code)
    bad("missing target leaf", lambda r: r["presumptions"][0].update(
        {"target_leaf_id":"f:missing"}))
    bad("missing trigger leaf", lambda r: r["presumptions"][0]["trigger"].update(
        {"leaf_id":"f:missing"}))
    bad("missing rebuttal leaf", lambda r: r["presumptions"][0]["rebuttal"].update(
        {"leaf_id":"f:missing"}))
    bad("missing rebuttal condition", lambda r: r["presumptions"][0].pop("rebuttal"),
        "KDEC001")
    bad("duplicate presumption ID", lambda r: r["presumptions"].append(route()),
        "KINV002")
    bad("presumption ID collides with leaf", lambda r: r["presumptions"][0].update(
        {"presumption_id":"f:root"}), "KINV002")
    bad("invalid registration span", lambda r: r["presumptions"][0]["span"].update(
        {"end":99}), "KINV003")
    bad("condition outside owning span", lambda r: r["presumptions"][0]["trigger"]["span"].update(
        {"end":3,"end_col":2,"end_line":2}), "KINV003")
    bad("empty all group", lambda r: r["presumptions"][0].update(
        {"trigger":group("all_of")}), "KINV004")
    bad("singleton any group", lambda r: r["presumptions"][0].update(
        {"trigger":group("any_of",leaf("f:trigger"))}), "KINV004")
    def deep(r):
        node = leaf("f:trigger")
        for _ in range(16):
            node = group("all_of",node,leaf("f:rebuttal"))
        r["presumptions"][0]["trigger"] = node
    bad("condition depth 17", deep, "KINV004")
    bad("semantic node limit", lambda r: r["policy"].update({"max_nodes":5}),
        "KINV004")
    bad("self-cycle", lambda r: r["presumptions"][0]["trigger"].update(
        {"leaf_id":"f:root"}), "KINV006")
    bad("two-target cycle", lambda r: r["presumptions"].append(
        route("pres:two",target="f:trigger",trigger="f:root")), "KINV006")
    bad("longer cycle", lambda r: (
        add_leaf(r,"f:middle",N),
        r["presumptions"].extend([
            route("pres:two",target="f:trigger",trigger="f:middle"),
            route("pres:three",target="f:middle",trigger="f:root")])), "KINV006")
    bad("cycle through rebuttal", lambda r: (
        r["presumptions"][0]["rebuttal"].update({"leaf_id":"f:middle"}),
        add_leaf(r,"f:middle",N),
        r["presumptions"].append(route("pres:two",target="f:middle",
                                         trigger="f:root"))), "KINV006")
    bad("unknown registration field", lambda r: r["presumptions"][0].update(
        {"unreviewed":True}), "KINV004")
    bad("unknown condition field", lambda r: r["presumptions"][0]["trigger"].update(
        {"unreviewed":True}), "KINV004")
    bad("irrebuttable is unsupported", lambda r: r["presumptions"][0].update(
        {"irrebuttable":True}), "KCAP001")
    bad("burden shift is unsupported", lambda r: r["presumptions"][0].update(
        {"burden_shift":"defence"}), "KCAP001")
    bad("negation is unsupported", lambda r: r["presumptions"][0]["trigger"].update(
        {"kind":"not"}), "KCAP001")
    bad("direct status predicate is unsupported", lambda r: r["presumptions"][0]["trigger"].update(
        {"kind":"leaf_direct"}), "KCAP001")
    bad("missing source reference", lambda r: r["presumptions"][0].update(
        {"source_id":"src:missing"}), "KINV005")
    bad("unknown top-level field", lambda r: r.update({"unreviewed":True}), "KINV004")
    original = (OUT / "requests/RD02.json").read_bytes()
    add_raw("malformed JSON", original[:-3] + b"\n", "KDEC001")
    add_raw("duplicate JSON key", original.replace(
        b'"presumption_id":"pres:one"',
        b'"presumption_id":"pres:one","presumption_id":"pres:one"',1), "KDEC001")
    add_raw("malformed surrogate escape", original.replace(
        b'"issuer_label":"synthetic classification"',
        b'"issuer_label":"\\ud800"',1), "KDEC001")
    add_raw("oversized request", original.replace(
        b'"request_id":"D02"', b'"request_id":"D02' + b'X' * 1048576 + b'"'),
        "KDEC002")
    def at_limit(r):
        standard(r)
        node = leaf("f:trigger")
        for _ in range(15):
            node = group("any_of", node, leaf("f:rebuttal"))
        r["presumptions"][0]["trigger"] = node
    add("condition nesting at depth 16", at_limit, states=["active"])
    bad("recognized direct-status predicate without a span is a capability",
        lambda r: r["presumptions"][0].update({"trigger":{"kind":"leaf_direct"}}),
        "KCAP001")
    add("direct unresolved plus unresolved route retains route without causal attribution",
        lambda r: standard(r,U,U,N), status="unresolved", states=["unresolved"])
    add("rebutting one route preserves another active route", lambda r: (
        standard(r), r["presumptions"].append(route("pres:two",
          trigger="f:trigger", rebuttal="f:trigger"))),
        states=["active","rebutted"])


def make_vectors():
    for name, case in CASES.items():
        vector = {"expected_status":case["status"], "invalid_classification":case["code"],
                  "selected_ids":case["selected"], "route_states":case["route_states"],
                  "registrations":[], "dependency_edges":[], "direct_bindings":{},
                  "condition_edges":[], "expected_effective":{}, "source_order":[],
                  "exception_edges":[], "penalty_guard_edges":[], "term_roots":[],
                  "selected_support_paths":{},
                  "graph_kind":"effective_leaf" if case["code"] == "KINV006" else ""}
        if case["file"].endswith(".json"):
            request = json.loads((OUT / case["file"]).read_text(encoding="utf-8"))
            vector["direct_bindings"] = request["facts"]
            vector["source_order"] = [source["id"] for source in request["sources"]]
            for rule in request["registry"]:
                for exception in rule["exceptions"]:
                    vector["exception_edges"].append([rule["id"],
                        exception["guard"].get("target"), exception["id"]])
                def provisions(node):
                    yield node
                    for child in node["children"]:
                        yield from provisions(child)
                for provision in provisions(rule["program"]):
                    for penalty in provision["penalties"]:
                        if penalty["guard"].get("kind") == "leaf_true":
                            vector["penalty_guard_edges"].append([
                                penalty["penalty_id"], penalty["guard"]["leaf_id"]])
                        if "term" in penalty:
                            vector["term_roots"].append([penalty["penalty_id"],
                                penalty["term"]["term_id"]])
            for registration in request["presumptions"]:
                vector["registrations"].append(registration)
                def walk(node, parent, path):
                    if node.get("kind") == "leaf_effective":
                        vector["dependency_edges"].append([
                            registration.get("target_leaf_id"), node.get("leaf_id"),
                            registration.get("presumption_id"), path])
                    for index, child in enumerate(node.get("members",[])):
                        vector["condition_edges"].append([parent,path,index])
                        walk(child,parent,path+f"/{index}")
                for field in ("trigger","rebuttal"):
                    if field in registration:
                        walk(registration[field], registration.get("presumption_id"),field)
            by_target = {}
            for registration,state_name in zip(request["presumptions"],
                                               case["route_states"]):
                by_target.setdefault(registration["target_leaf_id"],[]).append(state_name)
            for leaf_id,bound in request["facts"].items():
                direct = value(bound["proof_status"])
                states = by_target.get(leaf_id,[])
                vector["expected_effective"][leaf_id] = (
                    "satisfied" if direct == "satisfied" or "active" in states else
                    "unresolved" if direct == "unresolved" or "unresolved" in states else
                    "not_satisfied")
            vector["selected_support_paths"] = {identifier:[["root"]]
                for identifier in case["selected"]}
        VECTORS[name] = vector


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE)
    OUT = parser.parse_args().output
    cases()
    make_vectors()
    write(OUT / "CASES.json", CASES)
    write(OUT / "PROOF-VECTORS.json", VECTORS)
    paths = [OUT / "CASES.json",OUT / "PROOF-VECTORS.json",
             *sorted((OUT / "requests").iterdir())]
    files = {str(path.relative_to(OUT)):hashlib.sha256(path.read_bytes()).hexdigest()
             for path in paths}
    files["generate.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write(OUT / "MANIFEST.json", {"format":"yuho.rd-fixtures/v1","files":files})


if __name__ == "__main__":
    main()
