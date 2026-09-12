"""Generate production-only, specification-derived exception requests and vectors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUESTS = HERE / "requests"
REQUESTS.mkdir(exist_ok=True)
TEXT = "a\nb\nc\nd\ne\nf\ng\nh\n"
FRAGMENT = "AcyclicGuardedExceptions-v1"
SPAN = {"start": 0, "end": 15, "start_line": 1, "start_col": 1,
        "end_line": 8, "end_col": 2}
SMALL = {"start": 0, "end": 1, "start_line": 1, "start_col": 1,
         "end_line": 1, "end_col": 2}
CASES: dict[str, dict] = {}
VECTORS: list[dict] = []


def source(text: str = TEXT) -> dict:
    return {"id": "src:main", "path": "synthetic/exception.yh", "text": text,
            "sha256": hashlib.sha256(text.encode()).hexdigest()}


def leaf(name: str, line: int = 1) -> dict:
    start = 2 * (line - 1)
    return {"id": f"f:{name}", "kind": "leaf", "path": [name],
            "span": {"start": start, "end": start + 1, "start_line": line,
                     "start_col": 1, "end_line": line, "end_col": 2}}


def provision(name: str, with_leaf: bool = True, children: list[dict] | None = None) -> dict:
    return {"id": f"p:{name}", "path": [name], "span": dict(SPAN),
            "definitions": False, "requirements": [leaf(name)] if with_leaf else [],
            "children": children or []}


def exception(name: str, number: int, target: str, branch: str | None = None) -> dict:
    return {"id": f"x:{name}:{number}", "branch_id": branch or f"p:{name}",
            "source_id": "src:main", "span": dict(SMALL),
            "guard": {"kind": "is_infringed", "target": f"r:{target}"},
            "effect": "defeat"}


def rule(name: str, targets: list[str] | None = None,
         alternatives: list[str] | None = None) -> dict:
    children = [provision(child) for child in alternatives or []]
    program = provision(name, with_leaf=not bool(alternatives), children=children)
    return {"id": f"r:{name}", "source_id": "src:main", "program": program,
            "exceptions": [exception(name, i + 1, target)
                           for i, target in enumerate(targets or [])]}


def all_leaves(program: dict):
    for requirement in program["requirements"]:
        yield requirement["id"]
    for child in program["children"]:
        yield from all_leaves(child)


def request(name: str, registry: list[dict], false_facts: tuple[str, ...] = ()) -> dict:
    facts = {identifier: identifier not in false_facts
             for item in registry for identifier in all_leaves(item["program"])}
    return {"protocol": "yuho.kernel-protocol/v1", "request_id": name,
            "operation": "evaluate", "input_schema": "yuho.kernel-input/v1",
            "fragment": FRAGMENT, "sources": [source()],
            "policy": {"reference_date": "2026-09-12", "max_nodes": 1024},
            "root_rule": "r:root", "registry": registry, "facts": facts}


def add(name: str, label: str, value: dict, status: str, *, code: str = "",
        stage: str = "", branches: list[str] | None = None,
        reasons: list[str] | None = None, fired: list[str] | None = None,
        rules: dict[str, str] | None = None) -> None:
    REQUESTS.joinpath(f"{name}.json").write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n")
    expected = {"label": label, "status": status, "code": code, "stage": stage,
                "branches": branches or [], "reasons": reasons or [],
                "fired": fired or [], "rules": rules or {}}
    CASES[name] = expected
    VECTORS.append(vector(name, value, expected))


def vector(name: str, value: dict | None, expected: dict) -> dict:
    edges = [] if value is None else [
        {"rule": item["id"], "branch": ex["branch_id"], "exception": ex["id"],
         "target": ex["guard"].get("target", ""), "source_id": ex["source_id"]}
        for item in value["registry"] for ex in item["exceptions"]]
    root_paths = []
    rule_paths = {}
    observations = []
    if value is not None:
        for item in value["registry"]:
            if item["id"] not in expected["rules"]:
                continue
            provision_by_id = {}

            def register_provision(node: dict) -> None:
                provision_by_id[node["id"]] = node
                for child in node["children"]:
                    register_provision(child)

            register_provision(item["program"])
            rule_paths[item["id"]] = [branch["path"] for branch in provision_by_id.values()
                                       if branch["requirements"]]
            if item["id"] == value["root_rule"]:
                root_paths = rule_paths[item["id"]]
            for ex in item["exceptions"]:
                branch = provision_by_id.get(ex["branch_id"])
                if branch is None or not all(value["facts"].get(identifier, False)
                                             for identifier in all_leaves(branch)):
                    continue
                target = ex["guard"].get("target")
                target_status = expected["rules"].get(target)
                if target_status is not None:
                    observations.append({"rule": item["id"], "branch": ex["branch_id"],
                                         "branch_path": branch["path"], "exception": ex["id"],
                                         "source_id": ex["source_id"], "target": target,
                                         "target_status": target_status,
                                         "guard_status": target_status,
                                         "applicable": target_status == "true"})
    diagnostic_class = ("none" if not expected["code"] else
                        "capability" if expected["code"].startswith("KCAP") else
                        "decode" if expected["code"].startswith("KDEC") else
                        "invariant")
    return {"case": name, "fragment": FRAGMENT, "classification":
            "rejection" if expected["code"] else "synthetic_semantic",
            "root_rule": None if value is None else value["root_rule"],
            "facts": {} if value is None else value["facts"],
            "reference_date": None if value is None else value["policy"]["reference_date"],
            "dependency_edges": edges, "expected_status": expected["status"],
            "expected_root_branch_paths": root_paths,
            "expected_rule_branch_paths": rule_paths,
            "expected_branch_statuses": expected["branches"],
            "expected_fired_exception_ids": expected["fired"],
            "expected_rule_statuses": expected["rules"],
            "expected_guard_observations": observations,
            "expected_trace_order": {rule_id: [entry["exception"] for entry in observations
                                                if entry["rule"] == rule_id]
                                     for rule_id in expected["rules"]},
            "expected_diagnostic_class": diagnostic_class,
            "expected_diagnostic_code": expected["code"]}


add("E01", "satisfied without exceptions", request("E01", [rule("root")]), "true",
    branches=["true"], reasons=["satisfied"], rules={"r:root": "true"})
add("E02", "true target defeats", request("E02", [rule("root", ["target"]), rule("target")]),
    "false", branches=["false"], reasons=["defeated"], fired=["x:root:1"],
    rules={"r:root": "false", "r:target": "true"})
add("E03", "false target preserves", request("E03", [rule("root", ["target"]), rule("target")],
    ("f:target",)), "true", branches=["true"], reasons=["satisfied"],
    rules={"r:root": "true", "r:target": "false"})
add("E04", "two true guards both fire", request("E04", [rule("root", ["a", "b"]),
    rule("a"), rule("b")]), "false", branches=["false"], reasons=["defeated"],
    fired=["x:root:1", "x:root:2"], rules={"r:root": "false", "r:a": "true", "r:b": "true"})
add("E05", "multi-level chain", request("E05", [rule("root", ["mid"]),
    rule("mid", ["leaf"]), rule("leaf")]), "true", branches=["true"],
    reasons=["satisfied"], rules={"r:root": "true", "r:mid": "false", "r:leaf": "true"})
add("E06", "diamond graph", request("E06", [rule("root", ["left", "right"]),
    rule("left", ["leaf"]), rule("right", ["leaf"]), rule("leaf")]), "true",
    branches=["true"], reasons=["satisfied"],
    rules={"r:root": "true", "r:left": "false", "r:right": "false", "r:leaf": "true"})
add("E07", "same total facts for caller and target", request("E07", [rule("root", ["target"]),
    rule("target")], ("f:target",)), "true", branches=["true"],
    reasons=["satisfied"], rules={"r:root": "true", "r:target": "false"})

x = request("E08", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["guard"]["facts"] = {}
add("E08", "guard-local fact override", x, "rejected", code="KINV004", stage="validate")
x = request("E09", [rule("root", ["missing"])]); add("E09", "missing target", x,
    "rejected", code="KINV005", stage="validate")
x = request("E10", [rule("root", ["root"])]); add("E10", "self cycle", x,
    "rejected", code="KINV006", stage="validate")
x = request("E11", [rule("root", ["a"]), rule("a", ["b"]), rule("b", ["root"])]);
add("E11", "multi-rule cycle", x, "rejected", code="KINV006", stage="validate")
x = request("E12", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["guard"]["kind"] = "arbitrary_call"
add("E12", "unsupported guard", x, "rejected", code="KCAP001", stage="capability")
x = request("E13", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["priority"] = 1
add("E13", "priority field", x, "rejected", code="KINV004", stage="validate")
add("E14", "unsatisfied branch skips guards", request("E14", [rule("root", ["target"]),
    rule("target")], ("f:root",)), "false", branches=["false"],
    reasons=["requirements_failed"], rules={"r:root": "false"})

def alternative_rule() -> dict:
    item = rule("root", alternatives=["first", "second"])
    item["exceptions"] = [exception("root", 1, "target", "p:first")]
    return item

add("E15", "defeated alternative plus satisfied alternative",
    request("E15", [alternative_rule(), rule("target")]), "true",
    branches=["false", "true"], reasons=["defeated", "satisfied"],
    fired=["x:root:1"], rules={"r:root": "true", "r:target": "true"})
x = request("E16", [alternative_rule(), rule("target")]);
x["registry"][0]["exceptions"].append(exception("root", 2, "target", "p:second"))
add("E16", "all alternatives defeated", x, "false", branches=["false", "false"],
    reasons=["defeated", "defeated"], fired=["x:root:1", "x:root:2"],
    rules={"r:root": "false", "r:target": "true"})
add("E17", "source-order exception trace", request("E17", [rule("root", ["a", "b"]),
    rule("a"), rule("b")]), "false", branches=["false"], reasons=["defeated"],
    fired=["x:root:1", "x:root:2"], rules={"r:root": "false", "r:a": "true", "r:b": "true"})
x = request("E18", [rule("root", ["a", "b"]), rule("a"), rule("b")]);
x["registry"][0]["exceptions"].reverse()
add("E18", "reordered trace without priority", x, "false", branches=["false"],
    reasons=["defeated"], fired=["x:root:2", "x:root:1"],
    rules={"r:root": "false", "r:a": "true", "r:b": "true"})
x = request("E19", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["span"]["end"] = 17
add("E19", "exception span beyond source", x, "rejected", code="KINV003", stage="validate")
x = request("E20", [rule("root", ["target"]), rule("target")]); x["policy"]["max_nodes"] = 1
add("E20", "semantic node limit", x, "rejected", code="KINV004", stage="validate")
x = request("E21", [rule("root"), rule("target")]); x["registry"][1]["id"] = "r:root"
add("E21", "duplicate rule ID", x, "rejected", code="KINV002", stage="validate")
x = request("E22", [rule("root"), rule("target")]); x["registry"][1]["program"]["requirements"][0]["id"] = "f:root"
add("E22", "duplicate element ID", x, "rejected", code="KINV002", stage="validate")
x = request("E23", [rule("root"), rule("unreachable", ["missing"])])
add("E23", "unreachable missing target still rejects", x, "rejected", code="KINV005", stage="validate")
x = request("E24", [rule("root"), rule("left", ["right"]), rule("right", ["left"])])
add("E24", "unreachable cycle still rejects", x, "rejected", code="KINV006", stage="validate")
x = request("E25", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["effect"] = "reduce"
add("E25", "unsupported exception effect", x, "rejected", code="KCAP001", stage="capability")
x = request("E26", [rule("root")]); x["unknown"] = True
add("E26", "unknown top-level field", x, "rejected", code="KINV004", stage="validate")
x = request("E27", [rule("root")]); x["registry"][0]["unknown"] = True
add("E27", "unknown rule field", x, "rejected", code="KINV004", stage="validate")
x = request("E28", [rule("root")]); x["sources"].append(dict(x["sources"][0]))
add("E28", "duplicate source ID", x, "rejected", code="KINV002", stage="validate")
x = request("E29", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["source_id"] = "src:missing"
add("E29", "missing exception source", x, "rejected", code="KINV005", stage="validate")
x = request("E30", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["branch_id"] = "p:missing"
add("E30", "missing branch", x, "rejected", code="KINV005", stage="validate")
x = request("E31", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["facts"] = {"f:target": False}
add("E31", "target-specific fact map", x, "rejected", code="KINV004", stage="validate")
x = request("E34", [rule("root")]); x["sources"][0] = source(TEXT + "😀")
add("E34", "valid non-BMP source", x, "true", branches=["true"],
    reasons=["satisfied"], rules={"r:root": "true"})
x = request("E36", [rule("root")]); x["source"] = x["sources"][0]
add("E36", "mixed fragment fields", x, "rejected", code="KINV004", stage="validate")
x = request("E37", [rule("root", ["a", "b"]), rule("a"), rule("b")]); x["registry"][0]["exceptions"][1]["id"] = "x:root:1"
add("E37", "duplicate exception ID", x, "rejected", code="KINV002", stage="validate")
x = request("E38", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["guard"]["target"] = "target"
add("E38", "unqualified target", x, "rejected", code="KINV004", stage="validate")
x = request("E39", [rule("root", ["target"]), rule("target")]); x["registry"][0]["exceptions"][0]["guard"].update({"kind": "arbitrary_call", "arguments": []})
add("E39", "unsupported guard with arguments", x, "rejected", code="KCAP001", stage="capability")
x = request("E40", [rule("root", alternatives=["first", "second"])]); x["registry"][0]["program"]["children"][1]["id"] = "p:first"
add("E40", "duplicate executable branch provision ID", x, "rejected", code="KINV002", stage="validate")

base = REQUESTS.joinpath("E01.json").read_bytes()
REQUESTS.joinpath("E32.txt").write_bytes(b'{"\\u0070rotocol":"x",' + base[1:])
CASES["E32"] = {"label": "duplicate escaped JSON key", "status": "rejected",
                "code": "KDEC001", "stage": "decode", "branches": [], "reasons": [],
                "fired": [], "rules": {}}
VECTORS.append(vector("E32", None, CASES["E32"]))
REQUESTS.joinpath("E33.txt").write_bytes(base.replace(b"synthetic/exception.yh", b"\\ud83d.yh"))
CASES["E33"] = {"label": "malformed surrogate", "status": "rejected",
                "code": "KDEC001", "stage": "decode", "branches": [], "reasons": [],
                "fired": [], "rules": {}}
VECTORS.append(vector("E33", None, CASES["E33"]))
REQUESTS.joinpath("E35.txt").write_bytes(b" " * 1048577 + b"\n")
CASES["E35"] = {"label": "overlong line", "status": "rejected",
                "code": "KDEC002", "stage": "decode", "branches": [], "reasons": [],
                "fired": [], "rules": {}}
VECTORS.append(vector("E35", None, CASES["E35"]))

HERE.joinpath("CASES.json").write_text(json.dumps(CASES, sort_keys=True, indent=2) + "\n")
HERE.joinpath("PROOF-VECTORS.json").write_text(
    json.dumps(sorted(VECTORS, key=lambda item: item["case"]), sort_keys=True,
               ensure_ascii=False, indent=2) + "\n")
files = [HERE / "CASES.json", HERE / "PROOF-VECTORS.json", *sorted(REQUESTS.iterdir())]
HERE.joinpath("MANIFEST.json").write_text(json.dumps({
    "schema": "yuho.exception-fixture-manifest/v1",
    "files": {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in files},
}, sort_keys=True, indent=2) + "\n")
