"""Generate synthetic TypedBooleanFacts-v1 requests and proof-neutral vectors."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXCEPTIONS = HERE.parent / "exception-fixtures" / "requests"
REQUESTS = HERE / "requests"
REQUESTS.mkdir(exist_ok=True)
CASES: dict[str, dict] = {}
VECTORS: list[dict] = []
MANIFEST: dict[str, str] = {}
BURDEN = {"holder": "prosecution", "kind": "legal"}
STANDARD = "beyond_reasonable_doubt"


def base(name: str, source: str = "E01") -> dict:
    request = json.loads((EXCEPTIONS / f"{source}.json").read_text())
    request["fragment"] = "TypedBooleanFacts-v1"
    request["request_id"] = name
    request["facts"] = {key: {"type": "bool", "value": value}
                        for key, value in request["facts"].items()}
    return request


def leaf(request: dict) -> dict:
    return request["registry"][0]["program"]["requirements"][0]


def fact(request: dict, key: str = "f:root") -> dict:
    return request["facts"][key]


def declarations(request: dict) -> dict:
    found = {}

    def requirement(item: dict) -> None:
        if item["kind"] == "leaf":
            found[item["id"]] = item.get("declared_metadata", {})
        else:
            for member in item["members"]:
                requirement(member)

    def provision(item: dict) -> None:
        for member in item["requirements"]:
            requirement(member)
        for child in item["children"]:
            provision(child)

    for rule in request["registry"]:
        provision(rule["program"])
    return found


def add(name: str, label: str, request: dict | bytes, status: str,
        code: str = "", stage: str = "", rules: dict | None = None,
        branches: list[str] | None = None, checks: dict | None = None) -> None:
    raw = isinstance(request, bytes)
    data = request if raw else (json.dumps(request, sort_keys=True, separators=(",", ":"),
                                           ensure_ascii=True) + "\n").encode()
    suffix = ".txt" if raw else ".json"
    (REQUESTS / f"{name}{suffix}").write_bytes(data)
    MANIFEST[name] = hashlib.sha256(data).hexdigest()
    CASES[name] = {"label": label, "status": status, "code": code, "stage": stage,
                   "rules": rules or {}, "branches": branches or [],
                   "checks": checks or {}, "request_file": f"requests/{name}{suffix}"}
    if raw:
        VECTORS.append({"case": name, "fragment": "TypedBooleanFacts-v1",
                        "classification": "rejection", "expected_status": status,
                        "expected_diagnostic_code": code, "leaf_bindings": {},
                        "leaf_declarations": {}, "boolean_projection": {},
                        "dependency_edges": []})
    else:
        VECTORS.append({
            "case": name, "fragment": "TypedBooleanFacts-v1",
            "classification": "rejection" if code else "synthetic_semantic",
            "leaf_bindings": request["facts"],
            "leaf_declarations": declarations(request),
            "boolean_projection": {key: value["value"] for key, value in
                                   request["facts"].items() if isinstance(value, dict)
                                   and isinstance(value.get("value"), bool)},
            "dependency_edges": [{"rule": rule["id"], "exception": ex["id"],
                                  "branch": ex["branch_id"],
                                  "target": ex["guard"].get("target")}
                                 for rule in request["registry"]
                                 for ex in rule["exceptions"]],
            "root_rule": request["root_rule"],
            "reference_date": request["policy"]["reference_date"],
            "expected_status": status, "expected_diagnostic_code": code,
            "expected_rule_statuses": rules or {},
            "expected_root_branch_statuses": branches or [],
            "expected_binding_checks": checks or {},
        })


x = base("T01"); add("T01", "typed true", x, "true", rules={"r:root": "true"}, branches=["true"])
x = base("T02"); fact(x)["value"] = False
add("T02", "typed false", x, "false", rules={"r:root": "false"}, branches=["false"])
x = base("T03")
first = leaf(x)
second = copy.deepcopy(first); second["id"] = "f:second"
third = copy.deepcopy(first); third["id"] = "f:third"
group = {"id": "g:any", "kind": "any", "path": ["root"],
         "span": copy.deepcopy(first["span"]), "members": [second, third]}
x["registry"][0]["program"]["requirements"] = [
    {"id": "g:all", "kind": "all", "path": ["root"],
     "span": copy.deepcopy(first["span"]), "members": [first, group]}]
x["facts"]["f:second"] = {"type": "bool", "value": False}
x["facts"]["f:third"] = {"type": "bool", "value": True}
add("T03", "recursive all any", x, "true", rules={"r:root": "true"}, branches=["true"])
x = base("T04", "E15")
add("T04", "alternative branch with defeat", x, "true",
    rules={"r:root": "true", "r:target": "true"}, branches=["false", "true"])
x = base("T05"); x["registry"][0]["program"]["requirements"] = []
x["registry"][0]["program"]["definitions"] = True; x["facts"] = {}
add("T05", "definition only", x, "false", rules={"r:root": "false"})
x = base("T06"); leaf(x)["declared_metadata"] = {"burden": BURDEN}; fact(x)["burden"] = BURDEN
add("T06", "matching burden", x, "true", rules={"r:root": "true"}, branches=["true"],
    checks={"f:root": ["matched", "not_declared"]})
x = base("T07"); leaf(x)["declared_metadata"] = {"standard_of_proof": STANDARD}
fact(x)["standard_of_proof"] = STANDARD
add("T07", "matching standard", x, "true", rules={"r:root": "true"}, branches=["true"],
    checks={"f:root": ["not_declared", "matched"]})
x = base("T08"); leaf(x)["declared_metadata"] = {"burden": BURDEN, "standard_of_proof": STANDARD}
fact(x).update({"burden": BURDEN, "standard_of_proof": STANDARD})
add("T08", "both matching", x, "true", rules={"r:root": "true"}, branches=["true"],
    checks={"f:root": ["matched", "matched"]})
x = base("T09"); fact(x).update({"burden": BURDEN, "standard_of_proof": STANDARD})
add("T09", "supplied metadata without declaration", x, "true", rules={"r:root": "true"}, branches=["true"])
x = base("T10"); add("T10", "neither side has metadata", x, "true",
    rules={"r:root": "true"}, branches=["true"])
x = base("T11"); fact(x)["provenance"] = {"source_label": "descriptive witness label"}
add("T11", "descriptive source label", x, "true", rules={"r:root": "true"}, branches=["true"])
x = base("T12"); fact(x)["provenance"] = {"recorded_date": "2024-02-29"}
add("T12", "valid leap day", x, "true", rules={"r:root": "true"}, branches=["true"])
x = base("T13"); fact(x)["provenance"] = {"source_label": "another label", "jurisdiction": "SG"}
add("T13", "provenance invariant verdict", x, "true", rules={"r:root": "true"}, branches=["true"])
x = base("T14"); fact(x)["provenance"] = {"recorded_date": "2026-09-12", "jurisdiction": "SG"}
add("T14", "ordinary valid date", x, "true", rules={"r:root": "true"}, branches=["true"])
x = base("T15", "E02"); fact(x, "f:target")["provenance"] = {"source_label": "shared"}
add("T15", "typed target context", x, "false",
    rules={"r:root": "false", "r:target": "true"}, branches=["false"])
x = base("T16", "E06"); add("T16", "diamond dependency", x, "true",
    rules={"r:root": "true", "r:left": "false", "r:right": "false", "r:leaf": "true"}, branches=["true"])
x = base("T17", "E02"); add("T17", "true target defeats", x, "false",
    rules={"r:root": "false", "r:target": "true"}, branches=["false"])
x = base("T18", "E03"); add("T18", "false target preserves", x, "true",
    rules={"r:root": "true", "r:target": "false"}, branches=["true"])

def reject(name: str, label: str, request: dict, code: str = "KINV004",
           stage: str = "validate") -> None:
    add(name, label, request, "rejected", code, stage)

x = base("T19"); del x["facts"]["f:root"]; reject("T19", "missing leaf binding", x, "KINV001")
x = base("T20"); x["facts"]["f:extra"] = {"type": "bool", "value": True}
reject("T20", "extra leaf binding", x)
x = base("T21"); x["facts"]["f:root"] = True; reject("T21", "primitive shorthand", x, "KDEC001", "decode")
x = base("T22"); fact(x)["value"] = "true"; reject("T22", "string is not Boolean", x, "KDEC001", "decode")
x = base("T23"); fact(x)["type"] = "int"; reject("T23", "unsupported typed value", x, "KCAP001", "capability")
x = base("T24"); fact(x)["unknown"] = True; reject("T24", "unknown fact field", x)
x = base("T25")
raw = json.dumps(x, sort_keys=True, separators=(",", ":")).replace('"type":"bool"', '"type":"bool","\\u0074ype":"bool"', 1).encode() + b"\n"
add("T25", "duplicate escaped field", raw, "rejected", "KDEC001", "decode")
x = base("T26"); leaf(x)["declared_metadata"] = {}; reject("T26", "empty declaration", x, "KDEC001", "decode")
x = base("T27"); fact(x)["provenance"] = {}; reject("T27", "empty provenance", x, "KDEC001", "decode")
x = base("T28"); fact(x)["provenance"] = {"recorded_date": "2025-02-29"}
reject("T28", "impossible calendar date", x, "KDEC001", "decode")
x = base("T29"); leaf(x)["declared_metadata"] = {"burden": BURDEN}
reject("T29", "missing declared burden", x, "KINV007")
x = base("T30"); leaf(x)["declared_metadata"] = {"burden": BURDEN}
fact(x)["burden"] = {"holder": "defence", "kind": "legal"}
reject("T30", "mismatched burden holder", x, "KINV007")
x = base("T31"); leaf(x)["declared_metadata"] = {"burden": BURDEN}
fact(x)["burden"] = {"holder": "prosecution", "kind": "evidential"}
reject("T31", "mismatched burden kind", x, "KINV007")
x = base("T32"); leaf(x)["declared_metadata"] = {"standard_of_proof": STANDARD}
reject("T32", "missing declared standard", x, "KINV007")
x = base("T33"); leaf(x)["declared_metadata"] = {"standard_of_proof": STANDARD}
fact(x)["standard_of_proof"] = "balance_of_probabilities"
reject("T33", "mismatched standard", x, "KINV007")
x = base("T34"); fact(x)["standard_of_proof"] = "prima_facie"
reject("T34", "unsupported prima facie label", x, "KCAP001", "capability")
x = base("T35"); fact(x)["confidence"] = 1
reject("T35", "confidence unsupported", x)
x = base("T36"); fact(x)["evidential_status"] = "admitted"
reject("T36", "proof status unsupported", x)
x = base("T37"); fact(x)["type"] = "proof_status"
reject("T37", "proof-state constructor unsupported", x, "KCAP001", "capability")
x = base("T38"); leaf(x)["id"] = "f root"; x["facts"] = {
    "f_root": {"type": "bool", "value": True}, "f-root": {"type": "bool", "value": False}}
reject("T38", "normalized-name collision cannot bind", x, "KINV001")
x = base("T39"); leaf(x)["declared_metadata"] = {"burden": BURDEN, "unknown": 1}
reject("T39", "unknown declaration field", x)
x = base("T40"); leaf(x)["declared_metadata"] = {"burden": BURDEN}
fact(x)["burden"] = {"holder": "defence", "kind": "legal"}; fact(x)["value"] = False
reject("T40", "false binding still rejects mismatch", x, "KINV007")
x = base("T41"); x["registry"].append(copy.deepcopy(x["registry"][0]))
x["registry"][1]["id"] = "r:unreachable"; x["registry"][1]["program"]["id"] = "p:unreachable"
x["registry"][1]["program"]["requirements"][0]["id"] = "f:unreachable"
x["registry"][1]["program"]["requirements"][0]["declared_metadata"] = {"burden": BURDEN}
x["facts"]["f:unreachable"] = {"type": "bool", "value": True}
reject("T41", "unreachable rule mismatch", x, "KINV007")
x = base("T42", "E15"); x["facts"]["f:first"]["value"] = False
x["registry"][0]["program"]["children"][0]["requirements"][0]["declared_metadata"] = {"burden": BURDEN}
reject("T42", "unevaluated branch mismatch", x, "KINV007")
x = base("T43"); fact(x)["provenance"] = {"source_label": "label", "authority": True}
reject("T43", "unknown provenance field", x)
x = base("T44"); fact(x)["provenance"] = {"source_label": "𠜎 witness"}
add("T44", "non-BMP descriptive label", x, "true", rules={"r:root": "true"}, branches=["true"])
x = base("T45"); fact(x)["provenance"] = {"source_label": "x" * 257}
reject("T45", "overlong label", x, "KDEC001", "decode")
x = base("T46"); fact(x)["burden"] = {"holder": "prosecution"}
reject("T46", "incomplete burden", x, "KDEC001", "decode")
x = base("T47"); fact(x)["provenance"] = {"recorded_date": "2026-09-12", "jurisdiction": "MY"}
add("T47", "jurisdiction annotation inert", x, "true", rules={"r:root": "true"}, branches=["true"])
x = base("T48")
raw = json.dumps(x, sort_keys=True, separators=(",", ":")).replace(
    '"type":"bool"', '"type":"bool","provenance":{"source_label":"\\ud800"}', 1).encode() + b"\n"
add("T48", "malformed surrogate", raw, "rejected", "KDEC001", "decode")
x = base("T49"); fact(x)["provenance"] = {"source_label": "x" * 1048576}
add("T49", "request-byte resource limit",
    (json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n").encode(),
    "rejected", "KDEC002", "decode")
x = base("T50"); fact(x)["burden"] = {}
reject("T50", "empty burden object", x, "KDEC001", "decode")
x = base("T51"); fact(x)["provenance"] = {"source_label": ""}
reject("T51", "empty source label", x, "KDEC001", "decode")
x = base("T52"); leaf(x)["declared_metadata"] = {"burden": {"holder": "prosecution", "kind": "legal", "extra": True}}
reject("T52", "unknown nested burden field", x)
x = base("T53")
first = leaf(x); first["id"] = "f-root"
second = copy.deepcopy(first); second["id"] = "f_root"
x["registry"][0]["program"]["requirements"].append(second)
x["facts"] = {"f-root": {"type": "bool", "value": True},
              "f_root": {"type": "bool", "value": False}}
add("T53", "distinct similar leaf IDs retain independent bindings", x, "false",
    rules={"r:root": "false"}, branches=["false"])

# Expected semantic lists are specified independently of the Haskell evaluator.
for item in VECTORS:
    name = item["case"]
    if item["classification"] == "rejection":
        continue
    order = {rule_id: ["f:" + rule_id[2:]] for rule_id in item["expected_rule_statuses"]}
    paths = {rule_id: [[rule_id[2:]]] for rule_id in item["expected_rule_statuses"]}
    guards: dict[str, list[list[str]]] = {}
    fired: dict[str, list[str]] = {}
    if name == "T03":
        order["r:root"] = ["f:root", "f:second", "f:third"]
    if name == "T53":
        order["r:root"] = ["f-root", "f_root"]
    if name == "T04":
        order["r:root"] = ["f:first", "f:second"]
        paths["r:root"] = [["first"], ["second"]]
        guards = {"r:root": [["x:root:1", "true"]]}
        fired = {"r:root": ["x:root:1"]}
    if name == "T05":
        order["r:root"] = []
        paths["r:root"] = []
    if name in ("T15", "T17"):
        guards = {"r:root": [["x:root:1", "true"]]}
        fired = {"r:root": ["x:root:1"]}
    if name == "T16":
        guards = {"r:root": [["x:root:1", "false"], ["x:root:2", "false"]],
                  "r:left": [["x:left:1", "true"]],
                  "r:right": [["x:right:1", "true"]]}
        fired = {"r:left": ["x:left:1"], "r:right": ["x:right:1"]}
    if name == "T18":
        guards = {"r:root": [["x:root:1", "false"]]}
    item["expected_fact_observation_order"] = order
    item["expected_rule_branch_paths"] = paths
    item["expected_guard_trace_order"] = guards
    item["expected_fired_exception_ids"] = fired

binding_errors = {
    "T29": ("r:root", "f:root", "burden", "prosecution:legal", "absent"),
    "T30": ("r:root", "f:root", "burden", "prosecution:legal", "defence:legal"),
    "T31": ("r:root", "f:root", "burden", "prosecution:legal", "prosecution:evidential"),
    "T32": ("r:root", "f:root", "standard_of_proof", STANDARD, "absent"),
    "T33": ("r:root", "f:root", "standard_of_proof", STANDARD,
            "balance_of_probabilities"),
    "T40": ("r:root", "f:root", "burden", "prosecution:legal", "defence:legal"),
    "T41": ("r:unreachable", "f:unreachable", "burden", "prosecution:legal", "absent"),
    "T42": ("r:root", "f:first", "burden", "prosecution:legal", "absent"),
}
for item in VECTORS:
    if item["case"] in binding_errors:
        rule_id, leaf_id, field, expected, supplied = binding_errors[item["case"]]
        item["expected_binding_error"] = {
            "rule": rule_id, "leaf": leaf_id, "field": field,
            "expected": expected, "supplied": supplied,
            "source_path": "synthetic/exception.yh"}

(HERE / "CASES.json").write_text(json.dumps(CASES, indent=2, sort_keys=True) + "\n")
(HERE / "PROOF-VECTORS.json").write_text(json.dumps(VECTORS, indent=2, sort_keys=True) + "\n")
files = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
         for name in ("CASES.json", "PROOF-VECTORS.json", "MIGRATION-PROBES.json",
                      "legacy_adapter.py", "generate.py")}
files.update({CASES[name]["request_file"]: digest
              for name, digest in MANIFEST.items()})
(HERE / "MANIFEST.json").write_text(json.dumps(
    {"schema": "yuho.typed-fixture-manifest/v1", "files": files},
    indent=2, sort_keys=True) + "\n")
