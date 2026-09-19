"""Generate closed, synthetic GuardedPenaltySelection-v1 requests and vectors."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TYPED = HERE.parent / "typed-fixtures" / "requests"
REQUESTS = HERE / "requests"
REQUESTS.mkdir(exist_ok=True)
CASES: dict[str, dict] = {}
VECTORS: list[dict] = []


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode()


def provisions(provision: dict):
    yield provision
    for child in provision["children"]:
        yield from provisions(child)


def base(number: int, source: str = "T01") -> dict:
    request = json.loads((TYPED / f"{source}.json").read_bytes())
    request["request_id"] = f"G{number:02d}"
    request["fragment"] = "GuardedPenaltySelection-v1"
    for rule in request["registry"]:
        for provision in provisions(rule["program"]):
            provision["penalties"] = []
    return request


def rule(request: dict, identifier: str = "r:root") -> dict:
    return next(item for item in request["registry"] if item["id"] == identifier)


def provision(request: dict, identifier: str = "p:root", rule_id: str = "r:root") -> dict:
    return next(item for item in provisions(rule(request, rule_id)["program"])
                if item["id"] == identifier)


def penalty(request: dict, identifier: str, leaf: str | None = None,
            where: str = "p:root", rule_id: str = "r:root") -> dict:
    owner = provision(request, where, rule_id)
    declaration = {"penalty_id": identifier, "source_id": rule(request, rule_id)["source_id"],
                   "span": copy.deepcopy(owner["span"]),
                   "guard": {"kind": "leaf_true", "leaf_id": leaf} if leaf else
                            {"kind": "unguarded"}}
    owner["penalties"].append(declaration)
    return declaration


def declarations(request: dict) -> list[dict]:
    return [{"penalty_id": item["penalty_id"], "source_id": item.get("source_id"),
             "span": item.get("span"), "guard": item.get("guard"),
             "declaring_provision_path": owner["path"], "declaration_index": index,
             "rule_id": containing_rule["id"]}
            for containing_rule in request["registry"]
            for owner in provisions(containing_rule["program"])
            for index, item in enumerate(owner.get("penalties", []))
            if "penalty_id" in item]


def add(number: int, label: str, request: dict | bytes, status: str,
        selected: list[str] | None = None, supports: dict[str, list[list[str]]] | None = None,
        trace: list[list[str]] | None = None, warnings: list[list[str]] | None = None,
        code: str = "", stage: str = "") -> None:
    name = f"GP{number:02d}"
    data = request if isinstance(request, bytes) else canonical(request)
    suffix = ".txt" if isinstance(request, bytes) else ".json"
    (REQUESTS / f"{name}{suffix}").write_bytes(data)
    CASES[name] = {"label": label, "request_file": f"requests/{name}{suffix}",
                   "status": status, "code": code, "stage": stage,
                   "selected": selected or [], "supports": supports or {},
                   "trace": trace or [], "warnings": warnings or []}
    decoded = request if isinstance(request, dict) else None
    VECTORS.append({
        "case": name, "classification": "rejection" if status == "rejected" else
        "synthetic_selection", "fragment": "GuardedPenaltySelection-v1",
        "declarations": declarations(decoded) if decoded else [],
        "guard_edges": [{"penalty_id": item["penalty_id"],
                         "leaf_id": item["guard"]["leaf_id"]}
                        for item in declarations(decoded) if item.get("guard", {}).get(
                            "kind") == "leaf_true"] if decoded else [],
        "typed_bindings": decoded.get("facts", {}) if decoded else {},
        "boolean_projection": {key: value["value"] for key, value in decoded.get(
            "facts", {}).items() if isinstance(value, dict) and isinstance(
                value.get("value"), bool)} if decoded else {},
        "root_rule": decoded.get("root_rule") if decoded else None,
        "expected_status": status, "invalid_classification": code,
        "selected_id_order": selected or [], "supporting_paths": supports or {},
        "ordered_trace": trace or [], "warning_penalty_ids": warnings or []})


def rejection(number: int, label: str, request: dict | bytes,
              code: str = "KINV004", stage: str = "validate") -> None:
    add(number, label, request, "rejected", code=code, stage=stage)


def simple(number: int, source: str, leaf: str | None = None) -> dict:
    request = base(number, source)
    penalty(request, "pen:root:1", leaf)
    return request


x = simple(1, "T01"); add(1, "direct unguarded", x, "true", ["pen:root:1"],
    {"pen:root:1": [["root"]]}, [["pen:root:1", "p:root", "selected"]])
x = simple(2, "T02"); add(2, "false ordinary branch", x, "false", trace=[
    ["pen:root:1", "p:root", "branch_requirements_false"]])
x = simple(3, "T02", "f:root"); add(3, "failed requirements skip guard", x, "false",
    trace=[["pen:root:1", "p:root", "branch_requirements_false"]])
x = simple(4, "T17", "f:root"); add(4, "exception defeat skips guard", x, "false",
    trace=[["pen:root:1", "p:root", "branch_exception_defeated"]])
x = base(5, "T04"); penalty(x, "pen:first", where="p:first")
penalty(x, "pen:second", where="p:second")
add(5, "only satisfied alternative selects", x, "true", ["pen:second"],
    {"pen:second": [["second"]]}, [["pen:first", "p:first", "branch_exception_defeated"],
                                     ["pen:second", "p:second", "selected"]])
x = base(6, "T04"); penalty(x, "pen:root:1")
add(6, "root declaration inherited by eligible child", x, "true", ["pen:root:1"],
    {"pen:root:1": [["second"]]}, [["pen:root:1", "p:first", "branch_exception_defeated"],
                                     ["pen:root:1", "p:second", "selected"]])
x = base(7, "T04"); rule(x)["exceptions"] = []; penalty(x, "pen:root:1")
add(7, "one inherited ID, two supports", x, "true", ["pen:root:1"],
    {"pen:root:1": [["first"], ["second"]]},
    [["pen:root:1", "p:first", "selected"], ["pen:root:1", "p:second", "selected"]])
x = base(8, "T04"); penalty(x, "pen:first", where="p:first")
add(8, "sibling declaration does not leak", x, "true", trace=[
    ["pen:first", "p:first", "branch_exception_defeated"]])
x = simple(9, "T03", "f:third"); add(9, "true guard in recursive Any", x, "true",
    ["pen:root:1"], {"pen:root:1": [["root"]]},
    [["pen:root:1", "p:root", "selected"]])
x = simple(10, "T03", "f:second"); add(10, "false guard in true Any", x, "true",
    trace=[["pen:root:1", "p:root", "guard_false"]])
x = base(11); penalty(x, "pen:unguarded"); penalty(x, "pen:guarded", "f:root")
add(11, "unguarded and guarded accumulate", x, "true", ["pen:unguarded", "pen:guarded"],
    {"pen:unguarded": [["root"]], "pen:guarded": [["root"]]},
    [["pen:unguarded", "p:root", "selected"], ["pen:guarded", "p:root", "selected"]])
x = base(12); penalty(x, "pen:one", "f:root"); penalty(x, "pen:two", "f:root")
add(12, "same true guard accumulates without warning", x, "true", ["pen:one", "pen:two"],
    {"pen:one": [["root"]], "pen:two": [["root"]]},
    [["pen:one", "p:root", "selected"], ["pen:two", "p:root", "selected"]])
x = base(13, "T03"); penalty(x, "pen:one", "f:root")
penalty(x, "pen:two", "f:third")
add(13, "distinct true guards overlap on same path", x, "true", ["pen:one", "pen:two"],
    {"pen:one": [["root"]], "pen:two": [["root"]]},
    [["pen:one", "p:root", "selected"], ["pen:two", "p:root", "selected"]],
    [["pen:one", "pen:two"]])
x = base(14, "T03"); penalty(x, "pen:two", "f:third")
penalty(x, "pen:one", "f:root")
add(14, "declaration permutation changes presentation only", x, "true",
    ["pen:two", "pen:one"], {"pen:two": [["root"]], "pen:one": [["root"]]},
    [["pen:two", "p:root", "selected"], ["pen:one", "p:root", "selected"]],
    [["pen:two", "pen:one"]])
x = base(15, "T03"); child = copy.deepcopy(provision(x)); child.update(
    {"id": "p:child", "path": ["root", "child"], "requirements": [], "children": [],
     "penalties": []}); provision(x)["children"] = [child]
penalty(x, "pen:root", "f:root"); penalty(x, "pen:child", "f:third", where="p:child")
add(15, "distinct declaring provisions do not warn", x, "true",
    ["pen:root", "pen:child"], {"pen:root": [["root", "child"]],
                                  "pen:child": [["root", "child"]]},
    [["pen:root", "p:child", "selected"], ["pen:child", "p:child", "selected"]])
x = base(16, "T05"); penalty(x, "pen:inert")
add(16, "definition-only unguarded declaration is inert", x, "false")
x = base(17, "T05"); penalty(x, "pen:invalid", "f:absent")
rejection(17, "guarded definition-only declaration has no executable descendant", x,
          "KINV008")
x = base(18, "T18"); penalty(x, "pen:target", rule_id="r:target", where="p:target")
add(18, "target penalties are not selected for root", x, "true")
x = simple(19, "T01", "f:missing")
rejection(19, "missing exact guard leaf", x, "KINV008")
x = base(20, "T04"); penalty(x, "pen:wrong-scope", "f:first")
rejection(20, "sibling-only guard cannot scope root declaration", x, "KINV008")
x = simple(21, "T17", "f:target")
rejection(21, "dependency-target guard is not a root leaf", x, "KINV008")
x = base(22); item = penalty(x, "pen:invalid")
item["guard"] = {"kind": "leaf_false", "leaf_id": "f:root"}
rejection(22, "unsupported guard constructor", x, "KCAP001", "capability")
x = base(23); item = penalty(x, "pen:invalid"); item["fine"] = 100
rejection(23, "recognized punishment term", x, "KCAP001", "capability")
x = base(24); item = penalty(x, "pen:invalid"); item["other"] = 1
rejection(24, "unknown declaration field", x)
x = base(25); penalty(x, "pen:duplicate"); penalty(x, "pen:duplicate")
rejection(25, "duplicate global penalty ID", x, "KINV002")
x = base(26); item = penalty(x, "pen:bad-span"); item["span"]["end"] = 1000
rejection(26, "invalid declaration source span", x, "KINV003")
x = base(27); item = penalty(x, "pen:bad-source"); item["source_id"] = "src:absent"
rejection(27, "missing declaration source", x, "KINV005")
x = base(28, "T08"); penalty(x, "pen:typed", "f:root")
add(28, "typed matching metadata does not change selection", x, "true",
    ["pen:typed"], {"pen:typed": [["root"]]},
    [["pen:typed", "p:root", "selected"]])
x = base(29, "T11"); penalty(x, "pen:typed", "f:root")
add(29, "descriptive provenance does not change selection", x, "true",
    ["pen:typed"], {"pen:typed": [["root"]]},
    [["pen:typed", "p:root", "selected"]])


def migration(number: int, rash: bool, negligent: bool) -> None:
    request = base(number, "T03")
    program = provision(request)
    first = program["requirements"][0]["members"][0]
    alternatives = program["requirements"][0]["members"][1]
    first["id"] = "f:rash"
    alternatives["members"][0]["id"] = "f:negligent"
    alternatives["members"][1]["id"] = "f:other"
    request["facts"] = {"f:rash": {"type": "bool", "value": rash},
                        "f:negligent": {"type": "bool", "value": negligent},
                        "f:other": {"type": "bool", "value": True}}
    # The branch is satisfied independently of either guard, so neither is observable.
    program["requirements"] = [alternatives]
    alternatives["members"].append(first)
    penalty(request, "pen:rash", "f:rash")
    penalty(request, "pen:negligent", "f:negligent")
    chosen = (["pen:rash"] if rash else []) + (["pen:negligent"] if negligent else [])
    trace = [["pen:rash", "p:root", "selected" if rash else "guard_false"],
             ["pen:negligent", "p:root", "selected" if negligent else "guard_false"]]
    add(number, "synthetic s304A guard migration probe; no punishment terms", request,
        "true", chosen, {key: [["root"]] for key in chosen}, trace,
        [["pen:rash", "pen:negligent"]] if rash and negligent else [])


for number, rash, negligent in [(30, True, False), (31, False, True),
                                 (32, True, True), (33, False, False)]:
    migration(number, rash, negligent)

x = base(34); penalty(x, "pen:root:1")
raw = canonical(x).replace(b'"penalty_id":"pen:root:1"',
                           b'"penalty_id":"pen:root:1","penalty_id":"pen:root:1"', 1)
rejection(34, "duplicate JSON key", raw, "KDEC001", "decode")
x = base(35); penalty(x, "pen:root:1"); del provision(x)["penalties"]
rejection(35, "missing required penalties array", x, "KDEC001", "decode")
x = base(36); penalty(x, "pen:root:1", "f_root")
rejection(36, "exact ID does not normalize", x, "KINV008")
x = base(37, "T30"); penalty(x, "pen:root:1")
rejection(37, "typed metadata mismatch remains validation failure", x, "KINV007")


def occurrence_boundary(number: int, penalty_count: int) -> dict:
    request = base(number)
    program = provision(request)
    program["requirements"] = []
    program["children"] = []
    request["facts"] = {}
    template = copy.deepcopy(program)
    for index in range(64):
        child = copy.deepcopy(template)
        child["id"] = f"p:child-{index}"
        child["path"] = ["root", f"child-{index}"]
        child["penalties"] = []
        child["requirements"] = [{"id": f"f:child-{index}", "kind": "leaf",
                                  "path": child["path"],
                                  "span": copy.deepcopy(program["span"])}]
        program["children"].append(child)
        request["facts"][f"f:child-{index}"] = {"type": "bool", "value": True}
    for index in range(penalty_count):
        penalty(request, f"pen:boundary:{index}")
    return request


x = occurrence_boundary(38, 64)
add(38, "exactly 4096 expanded branch/declaration occurrences", x, "true",
    [f"pen:boundary:{index}" for index in range(64)],
    {f"pen:boundary:{index}": [["root", f"child-{child}"] for child in range(64)]
     for index in range(64)},
    [[f"pen:boundary:{declaration}", f"p:child-{child}", "selected"]
     for child in range(64) for declaration in range(64)])
x = occurrence_boundary(39, 65)
rejection(39, "4160 expanded occurrences exceed cap", x, "KDEC002", "decode")
x = base(40, "T04"); rule(x)["exceptions"] = []
penalty(x, "pen:second", where="p:second"); penalty(x, "pen:first", where="p:first")
add(40, "tree declaration order differs from branch trace order", x, "true",
    ["pen:first", "pen:second"], {"pen:first": [["first"]],
                                  "pen:second": [["second"]]},
    [["pen:first", "p:first", "selected"], ["pen:second", "p:second", "selected"]])
x = base(41); item = penalty(x, "pen:root:1")
item["guard"]["priority"] = 1
rejection(41, "priority field is not a selection control", x)
x = base(42); item = penalty(x, "pen:root:1")
item["guard"]["first_match"] = True
rejection(42, "first-match field is not a selection control", x)
x = base(43); penalty(x, "pen:root:1")
provision(x)["penalties"][0]["span"]["start_col"] = 2
rejection(43, "inconsistent source display position", x, "KINV003")
x = base(44, "T44"); penalty(x, "pen:unicode", "f:root")
add(44, "non-BMP descriptive provenance survives", x, "true", ["pen:unicode"],
    {"pen:unicode": [["root"]]}, [["pen:unicode", "p:root", "selected"]])
x = simple(45, "T01"); x["policy"]["max_nodes"] = 1
rejection(45, "penalties count against semantic-node cap before transformation", x)
x = base(46, "T17"); penalty(x, "pen:root:1")
x["registry"] = [rule(x)]; del x["facts"]["f:target"]
rejection(46, "missing exception dependency rejects before penalty selection", x, "KINV005")
x = base(47, "T17"); penalty(x, "pen:root:1")
x["registry"] = [rule(x)]; del x["facts"]["f:target"]
rule(x)["exceptions"][0]["guard"]["target"] = "r:root"
rejection(47, "self-cycle rejects before penalty selection", x, "KINV006")
x = base(48, "T17"); penalty(x, "pen:root:1")
rule(x)["exceptions"][0]["guard"] = {"kind": "call", "name": "unknown"}
rejection(48, "unsupported dependency guard rejects before selection", x,
          "KCAP001", "capability")
x = base(49); penalty(x, "pen:root:1")
unused = copy.deepcopy(rule(x)); unused["id"] = "r:unused"
unused["program"]["id"] = "p:unused"
unused["program"]["path"] = ["unused"]
unused["program"]["requirements"][0]["id"] = "f:unused"
unused["program"]["requirements"][0]["path"] = ["unused"]
unused["program"]["penalties"] = []
x["registry"].append(unused)
x["facts"]["f:unused"] = {"type": "bool", "value": True}
penalty(x, "pen:unused", "f:missing", "p:unused", "r:unused")
rejection(49, "unreachable registry rule penalty guard still validates", x, "KINV008")

# These are independent expected semantic statuses, not observations collected from Haskell.
BRANCH_EXPECTATIONS = {
    "GP01": [("p:root", "true", "satisfied")],
    "GP02": [("p:root", "false", "requirements_failed")],
    "GP03": [("p:root", "false", "requirements_failed")],
    "GP04": [("p:root", "false", "defeated")],
    "GP05": [("p:first", "false", "defeated"), ("p:second", "true", "satisfied")],
    "GP06": [("p:first", "false", "defeated"), ("p:second", "true", "satisfied")],
    "GP07": [("p:first", "true", "satisfied"), ("p:second", "true", "satisfied")],
    "GP08": [("p:first", "false", "defeated"), ("p:second", "true", "satisfied")],
    **{f"GP{number:02d}": [("p:root", "true", "satisfied")]
       for number in (9, 10, 11, 12, 13, 14, 28, 29, 30, 31, 32, 33, 44)},
    "GP15": [("p:child", "true", "satisfied")],
    "GP16": [],
    "GP18": [("p:root", "true", "satisfied")],
    "GP38": [(f"p:child-{index}", "true", "satisfied") for index in range(64)],
    "GP40": [("p:first", "true", "satisfied"), ("p:second", "true", "satisfied")],
}
WARNING_EXPECTATIONS = {
    "GP13": [{"paths": [["root"]], "guard_leaf_ids": ["f:root", "f:third"]}],
    "GP14": [{"paths": [["root"]], "guard_leaf_ids": ["f:third", "f:root"]}],
    "GP32": [{"paths": [["root"]], "guard_leaf_ids": ["f:rash", "f:negligent"]}],
}
for vector in VECTORS:
    name = vector["case"]
    request_file = REQUESTS / Path(CASES[name]["request_file"]).name
    if name in BRANCH_EXPECTATIONS:
        request = json.loads(request_file.read_bytes())
        paths = {item["id"]: item["path"] for item in provisions(
            rule(request)["program"])}
        vector["final_root_branches"] = [
            {"branch_id": identifier, "path": paths[identifier],
             "status": status, "reason": reason}
            for identifier, status, reason in BRANCH_EXPECTATIONS[name]]
    else:
        vector["final_root_branches"] = []
    vector["overlap_warnings"] = WARNING_EXPECTATIONS.get(name, [])

(HERE / "CASES.json").write_text(json.dumps(CASES, indent=2, sort_keys=True) + "\n")
(HERE / "PROOF-VECTORS.json").write_text(json.dumps(VECTORS, indent=2,
                                                     sort_keys=True) + "\n")
paths = [HERE / "CASES.json", HERE / "PROOF-VECTORS.json", HERE / "generate.py",
         HERE / "legacy_adapter.py",
         *sorted(REQUESTS.iterdir())]
manifest = {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}
(HERE / "MANIFEST.json").write_text(json.dumps(
    {"schema": "yuho.penalty-fixture-manifest/v1", "files": manifest},
    indent=2, sort_keys=True) + "\n")
