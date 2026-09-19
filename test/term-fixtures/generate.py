"""Deterministically build synthetic PenaltyTerms-v1 requests from GP migration probes."""

import argparse
import copy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GP = HERE.parent / "penalty-fixtures"
BASE_CASES = json.loads((GP / "CASES.json").read_text(encoding="utf-8"))
OUT = HERE
CASES = {}
PROOF = {}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.name == "requests":
        path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(",", ":")) + "\n", encoding="utf-8")
    else:
        path.write_text(json.dumps(value, indent=2, sort_keys=True,
                                   ensure_ascii=False) + "\n", encoding="utf-8")


def unstated():
    return {"kind": "not_stated"}


def specified(value):
    return {"kind": "specified", "value": value}


def atom(kind, span, identifier="term:fixture", **fields):
    return {"term_id": identifier, "span": copy.deepcopy(span), "kind": kind, **fields}


def prison(span, lower=None, upper=None, unit="years"):
    return atom("term_imprisonment", span, unit=unit,
                minimum=unstated() if lower is None else specified(lower),
                maximum=unstated() if upper is None else specified(upper))


def fine(span, lower=None, upper=None):
    return atom("fine", span, currency="SGD",
                minimum=unstated() if lower is None else specified(lower),
                maximum=unstated() if upper is None else specified(upper))


def all_penalties(program):
    yield from program["penalties"]
    for child in program["children"]:
        yield from all_penalties(child)


def new_request(base, number):
    data = json.loads((GP / "requests" / f"{base}.json").read_text(encoding="utf-8"))
    data["fragment"] = "PenaltyTerms-v1"
    data["request_id"] = f"P{number:02d}"
    for rule in data["registry"]:
        for declaration in all_penalties(rule["program"]):
            declaration["term"] = prison(declaration["span"], upper=5)
            declaration["term"]["term_id"] = "term:" + declaration["penalty_id"][4:]
    return data


def first(data):
    return next(all_penalties(data["registry"][0]["program"]))


def group(kind, span, count=2):
    children = [atom("death", span, f"term:child:{index}") for index in range(count)]
    return atom(kind, span, "term:group", terms=children)


def nested(span, depth):
    current = atom("death", span, "term:bottom")
    for level in range(depth - 1):
        current = atom("all_of", span, f"term:level:{level}", terms=[
            current, atom("caning", span, f"term:sibling:{level}",
                          minimum=unstated(), maximum=unstated())])
    return current


def synthetic_migration_payloads(request):
    for rule in request["registry"]:
        for declaration in all_penalties(rule["program"]):
            span = declaration["span"]
            suffix = declaration["penalty_id"][4:]
            imprisonment = prison(span, upper=5)
            imprisonment["term_id"] = f"term:{suffix}:imprisonment"
            charge = fine(span)
            charge["term_id"] = f"term:{suffix}:fine"
            declaration["term"] = atom("one_or_more_of", span, f"term:{suffix}",
                                       terms=[imprisonment, charge])


def add(label, base="GP01", mutate=None, status=None, code=None):
    number = len(CASES) + 1
    name = f"PT{number:02d}"
    request = new_request(base, number)
    if mutate is not None:
        mutate(request)
    expectation = BASE_CASES[base]
    status = status if status is not None else expectation["status"]
    code = code if code is not None else ("" if status != "rejected" else expectation["code"])
    selected = expectation["selected"] if status != "rejected" else []
    CASES[name] = {"label": label, "request_file": f"requests/{name}.json",
                   "status": status, "code": code, "selected": selected,
                   "base_case": base}
    write(OUT / "requests" / f"{name}.json", request)
    return request


def set_term(transform):
    def apply(request):
        declaration = first(request)
        declaration["term"] = transform(declaration["span"])
    return apply


def term_nodes(term):
    yield term["term_id"]
    for child in term.get("terms", []):
        yield from term_nodes(child)


def term_edges(term):
    return [[term["term_id"], child["term_id"], index]
            for index, child in enumerate(term.get("terms", []))] + [edge
            for child in term.get("terms", []) for edge in term_edges(child)]


def canonical_term(term):
    result = copy.deepcopy(term)
    if result["kind"] == "fine":
        for bound in ("minimum", "maximum"):
            endpoint = result[bound]
            if endpoint["kind"] == "specified":
                amount = endpoint["value"]
                if "." not in amount:
                    amount += "."
                whole, fractional = amount.split(".")
                endpoint["value"] = whole + "." + fractional.ljust(2, "0")
    for index, child in enumerate(result.get("terms", [])):
        result["terms"][index] = canonical_term(child)
    return result


def child(request):
    return first(request)["term"]["terms"][0]


def make_cases():
    add("term imprisonment maximum", mutate=set_term(lambda s: prison(s, upper=5)))
    add("life imprisonment", mutate=set_term(lambda s: atom("life_imprisonment", s)))
    add("fine decimal canonicalization", mutate=set_term(lambda s: fine(s, "1.2", "10")))
    add("caning", mutate=set_term(lambda s: atom("caning", s, minimum=unstated(), maximum=specified(3))))
    add("death", mutate=set_term(lambda s: atom("death", s)))
    add("imprisonment minimum only", mutate=set_term(lambda s: prison(s, lower=1)))
    add("imprisonment maximum only", mutate=set_term(lambda s: prison(s, upper=1)))
    add("fixed equal bounds", mutate=set_term(lambda s: prison(s, 3, 3)))
    add("both bounds not stated", mutate=set_term(lambda s: fine(s)))
    add("explicitly unbounded fine maximum", mutate=set_term(lambda s: {**fine(s, "1"), "maximum": {"kind": "unbounded"}}))
    add("all_of source tree", mutate=set_term(lambda s: group("all_of", s)))
    add("exactly_one_of source tree", mutate=set_term(lambda s: group("exactly_one_of", s)))
    add("one_or_more_of source tree", mutate=set_term(lambda s: group("one_or_more_of", s)))
    add("nested combinations", mutate=set_term(lambda s: nested(s, 4)))
    add("authored child order", mutate=set_term(lambda s: {**group("all_of", s), "terms": list(reversed(group("all_of", s)["terms"]))}))
    add("unselected false branch still validates terms", "GP02")
    add("inherited selected term with two supports", "GP07")
    add("exception defeated branch omits term", "GP04")
    add("overlap warning unchanged", "GP13")
    add("dependency target term validated, not selected", "GP18")
    add("zero imprisonment bound", mutate=set_term(lambda s: prison(s, lower=0)), status="rejected", code="KINV009")
    add("negative caning bound", mutate=set_term(lambda s: atom("caning", s, minimum=specified(-1), maximum=unstated())), status="rejected", code="KINV009")
    add("reversed imprisonment bounds", mutate=set_term(lambda s: prison(s, 5, 2)), status="rejected", code="KINV009")
    add("excessive integer magnitude", mutate=set_term(lambda s: prison(s, upper=1000001)), status="rejected", code="KINV009")
    add("unsupported duration unit", mutate=set_term(lambda s: prison(s, unit="hours")), status="rejected", code="KCAP001")
    add("mixed duration components", mutate=lambda r: first(r)["term"].update({"duration": [1, 2]}), status="rejected", code="KCAP001")
    add("malformed fine decimal", mutate=set_term(lambda s: fine(s, "1,000")), status="rejected", code="KDEC001")
    add("excess fine precision", mutate=set_term(lambda s: fine(s, "1.234")), status="rejected", code="KDEC001")
    add("fine exponent rejected", mutate=set_term(lambda s: fine(s, "1e2")), status="rejected", code="KDEC001")
    add("fine leading zero rejected", mutate=set_term(lambda s: fine(s, "01.00")), status="rejected", code="KDEC001")
    add("non-SGD currency", mutate=set_term(lambda s: {**fine(s), "currency": "USD"}), status="rejected", code="KCAP001")
    add("life with numeric field", mutate=set_term(lambda s: {**atom("life_imprisonment", s), "maximum": specified(99)}), status="rejected", code="KINV004")
    add("death with numerical field", mutate=set_term(lambda s: {**atom("death", s), "minimum": specified(1)}), status="rejected", code="KINV004")
    add("empty combinator", mutate=set_term(lambda s: group("all_of", s, 0)), status="rejected", code="KINV009")
    add("singleton combinator", mutate=set_term(lambda s: group("exactly_one_of", s, 1)), status="rejected", code="KINV009")
    add("duplicate child term IDs", mutate=lambda r: (set_term(lambda s: group("all_of", s))(r), child(r).update({"term_id": "term:child:1"})), status="rejected", code="KINV009")
    add("duplicate term IDs across declarations", "GP13", mutate=lambda r: [p["term"].update({"term_id": "term:duplicate"}) for p in all_penalties(r["registry"][0]["program"])], status="rejected", code="KINV009")
    add("invalid source span", mutate=lambda r: first(r)["term"]["span"].update({"end": 999}), status="rejected", code="KINV003")
    add("term outside declaration span", mutate=lambda r: first(r)["span"].update({"start": 1, "start_col": 2}), status="rejected", code="KINV009")
    add("unsupported punishment atom", mutate=set_term(lambda s: atom("forfeiture", s)), status="rejected", code="KCAP001")
    add("unsupported sentencing metadata", mutate=lambda r: first(r)["term"].update({"sentencing_mode": "mandatory"}), status="rejected", code="KCAP001")
    add("depth 16 boundary", mutate=set_term(lambda s: nested(s, 16)))
    add("depth 17 overflow", mutate=set_term(lambda s: nested(s, 17)), status="rejected", code="KDEC002")
    add("semantic node budget rejects terms", mutate=lambda r: r["policy"].update({"max_nodes": 4}), status="rejected", code="KINV004")
    add("missing required term", mutate=lambda r: first(r).pop("term"), status="rejected", code="KDEC001")
    add("unknown term field", mutate=lambda r: first(r)["term"].update({"mystery": True}), status="rejected", code="KINV004")
    add("fine zero rejected", mutate=set_term(lambda s: fine(s, "0")), status="rejected", code="KINV009")
    add("reversed fine bounds", mutate=set_term(lambda s: fine(s, "5", "2")), status="rejected", code="KINV009")
    add("unbounded fine minimum rejected", mutate=set_term(lambda s: {**fine(s), "minimum": {"kind": "unbounded"}}), status="rejected", code="KINV009")
    add("unbounded imprisonment maximum rejected", mutate=set_term(lambda s: {**prison(s), "maximum": {"kind": "unbounded"}}), status="rejected", code="KINV009")
    add("fine 18 integer digits", mutate=set_term(lambda s: fine(s, "999999999999999999")))
    add("fine 19 integer digits rejected", mutate=set_term(lambda s: fine(s, "9999999999999999999")), status="rejected", code="KDEC001")
    add("source order permutation leaves selection unchanged", "GP14")
    add("definition-only term valid but inert", "GP16")
    add("migration probe: rash s304A imprisonment/fine shape, not doctrine", "GP30",
        mutate=synthetic_migration_payloads)
    add("migration probe: negligent s304A imprisonment/fine shape, not doctrine", "GP31",
        mutate=synthetic_migration_payloads)
    add("migration probe: both s304A imprisonment/fine shapes, not doctrine", "GP32",
        mutate=synthetic_migration_payloads)
    add("migration probe: neither s304A imprisonment/fine shape, not doctrine", "GP33",
        mutate=synthetic_migration_payloads)
    add("valid non-BMP descriptive provenance", mutate=lambda r: r["facts"]["f:root"].update(
        {"provenance": {"source_label": "source 📜"}}))
    add("invalid dependency-target term rejects whole registry", "GP18",
        mutate=lambda r: next(all_penalties(r["registry"][1]["program"]))["term"].update(
            {"maximum": specified(0)}), status="rejected", code="KINV009")
    add("invalid empty term ID segment", mutate=lambda r: first(r)["term"].update(
        {"term_id": "term:bad:"}), status="rejected", code="KINV009")
    add("recognized legacy punishment payload rejects as capability", mutate=lambda r:
        first(r).update({"fine": 100}), status="rejected", code="KCAP001")
    add("unknown penalty declaration field", mutate=lambda r: first(r).update(
        {"unknown": 1}), status="rejected", code="KINV004")
    add("canonical fine with two fractional digits", mutate=set_term(
        lambda s: fine(s, "1.20", "100.00")))


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    OUT = args.output
    make_cases()
    raw = (OUT / "requests" / "PT01.json").read_text(encoding="utf-8").replace('"request_id":"P01"', '"request_id":"P65"')
    raw = raw.replace('"kind":"term_imprisonment"', '"kind":"term_imprisonment","kind":"term_imprisonment"', 1)
    (OUT / "requests" / "PT65.txt").write_text(raw, encoding="utf-8")
    CASES["PT65"] = {"label": "duplicate JSON key in term", "request_file": "requests/PT65.txt",
                     "status": "rejected", "code": "KDEC001", "selected": []}
    raw = (OUT / "requests" / "PT01.json").read_text(encoding="utf-8").replace('"request_id":"P01"', '"request_id":"P66"')
    raw = raw.replace('"request_id":"P66"', '"request_id":"P66' + 'X' * 1048576 + '"')
    (OUT / "requests" / "PT66.txt").write_text(raw, encoding="utf-8")
    CASES["PT66"] = {"label": "line and request byte limit", "request_file": "requests/PT66.txt",
                     "status": "rejected", "code": "KDEC002", "selected": []}
    raw = (OUT / "requests" / "PT01.json").read_text(encoding="utf-8").replace(
        '"request_id":"P01"', '"request_id":"P67"').replace(
            '"term:fixture"', '"\\ud800"', 1)
    (OUT / "requests" / "PT67.txt").write_text(raw, encoding="utf-8")
    CASES["PT67"] = {"label": "malformed surrogate escape", "request_file": "requests/PT67.txt",
                     "status": "rejected", "code": "KDEC001", "selected": []}
    raw = (OUT / "requests" / "PT01.json").read_text(encoding="utf-8").replace(
        '"request_id":"P01"', '"request_id":"P68"').replace(
            '"kind":"specified"', '"kind":"specified","kind":"specified"', 1)
    (OUT / "requests" / "PT68.txt").write_text(raw, encoding="utf-8")
    CASES["PT68"] = {"label": "duplicate JSON key in endpoint", "request_file": "requests/PT68.txt",
                     "status": "rejected", "code": "KDEC001", "selected": []}
    write(OUT / "CASES.json", CASES)
    previous = {row["case"]: row for row in json.loads(
        (GP / "PROOF-VECTORS.json").read_text(encoding="utf-8"))}
    for name, case in CASES.items():
        vector = {"status": case["status"], "invalid_classification": case["code"],
                  "selected_ids": case["selected"], "declaration_order": [],
                  "term_preorder": [], "combinator_edges": [], "declarations": []}
        if name not in ("PT65", "PT66", "PT67", "PT68"):
            request = json.loads((OUT / case["request_file"]).read_text(encoding="utf-8"))
            declarations = [p for rule in request["registry"]
                            for p in all_penalties(rule["program"])]
            vector["declaration_order"] = [p["penalty_id"] for p in declarations]
            for declaration in declarations:
                if "term" not in declaration:
                    continue
                term = declaration["term"]
                vector["declarations"].append({"penalty_id": declaration["penalty_id"],
                                               "span": declaration["span"],
                                               "term": term,
                                               "canonical_term": canonical_term(term)
                                               if case["status"] != "rejected" else None,
                                               "canonical_json": json.dumps(
                                                   canonical_term(term), sort_keys=True,
                                                   ensure_ascii=False, separators=(",", ":"))
                                               if case["status"] != "rejected" else None})
                if "term_id" in term:
                    vector["term_preorder"].extend(term_nodes(term))
                    vector["combinator_edges"].extend(term_edges(term))
            if case["status"] != "rejected":
                gp = previous[case["base_case"]]
                vector["branch_statuses"] = gp["final_root_branches"]
                vector["supporting_paths"] = gp["supporting_paths"]
                vector["selection_trace"] = gp["ordered_trace"]
                vector["warnings"] = gp["warning_penalty_ids"]
                vector["selected_term_ids"] = {p["penalty_id"]: p["term"]["term_id"]
                    for p in declarations if p["penalty_id"] in case["selected"]}
        PROOF[name] = vector
    write(OUT / "PROOF-VECTORS.json", PROOF)
    write(OUT / "MIGRATION-PROBES.json", {
        "s304A": "PT55-PT58 use synthetic imprisonment/fine shapes and an arbitrary five-year bound; no term or verdict is a doctrinal claim",
        "zero_minimum": "legacy zero is ambiguous; PT21 rejects specified zero",
        "or_both": "PT13 encodes source order without choosing a child",
        "fine_without_amount": "PT09 retains two not_stated endpoints",
        "life_and_death": "PT02 and PT05 use categorical atoms, no numeric proxy",
        "mandatory_minimum": "the adapter must report any legal interpretation or lossy mapping",
    })
    paths = [OUT / "CASES.json", OUT / "PROOF-VECTORS.json",
             OUT / "MIGRATION-PROBES.json", *sorted((OUT / "requests").glob("PT*.json")),
             *sorted((OUT / "requests").glob("PT*.txt"))]
    files = {str(path.relative_to(OUT)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in paths}
    files["generate.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write(OUT / "MANIFEST.json", {"files": files, "format": "yuho.pt-fixtures/v1"})


if __name__ == "__main__":
    main()
