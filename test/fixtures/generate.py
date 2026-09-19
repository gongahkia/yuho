"""Regenerate production-only hardening inputs from frozen spike examples."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SPIKE = ROOT / "experiments/language-spike/fixtures/requests"
OUT = HERE / "requests"
OUT.mkdir(exist_ok=True)


def base(name="B06"):
    return json.loads((SPIKE / f"{name}.json").read_bytes())


def put(name, value):
    value["request_id"] = name
    OUT.joinpath(f"{name}.json").write_text(
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    )


cases = {}


def add(name, label, data, status="rejected", code="KINV004", stage="validate"):
    put(name, data)
    cases[name] = {"label": label, "status": status, "code": code, "stage": stage}


x = base(); x["unknown"] = True
add("H01", "unknown top-level field", x)
x = base(); x["source"]["unknown"] = True
add("H02", "unknown source field", x)
x = base(); x["program"]["requirements"][0]["members"][0]["members"] = []
add("H03", "leaf contains members", x)
x = base(); x["program"]["requirements"][0]["members"] = []
add("H04", "empty All", x)
x = base(); x["program"]["requirements"][0]["members"][1]["members"] = []
add("H05", "empty Any", x)
x = base(); x["policy"]["reference_date"] = "2026-02-30"
add("H06", "impossible calendar date", x, code="KDEC001", stage="decode")
x = base("P02"); x["parser_result"]["accepted"] = True
add("H07", "parser accepted with error", x)
x = base("B05"); x["program"]["children"][0]["definitions"] = False
add("H08", "zero branches without definition", x)
x = base(); x["program"]["requirements"][0]["members"][1]["members"][1]["span"]["end"] = 99
add("H09", "span beyond source", x, code="KINV003")
x = base(); x["program"]["requirements"][0]["members"][1]["members"][0]["span"]["start_col"] = 2
add("H10", "byte/display position mismatch", x, code="KINV003")
x = base("R02")
add("H13", "duplicate semantic IDs", x, code="KINV002")
x = base("R03")
add("H14", "unsupported constructor", x, code="KCAP001", stage="capability")
x = base(); x["source"]["path"] = "fixtures/😀.yh"; x["source"]["text"] += "😀"
x["source"]["sha256"] = hashlib.sha256(x["source"]["text"].encode()).hexdigest()
add("H16", "valid non-BMP source and paired JSON surrogate", x, status="true", code="", stage="")
x["program"]["span"].update(end=7, end_line=4, end_col=2)
add("H19", "span ends inside a UTF-8 code point", x, code="KINV003")
x = base(); x["program"]["requirements"][0]["members"][0]["unknown"] = True
add("H18", "unknown requirement field", x)
x = base(); x["policy"]["max_nodes"] = 1
add("H20", "node limit before domain decoding", x)
x = base(); x["program"]["definitions"] = True
add("H21", "definitions marker with executable branch", x)

OUT.joinpath("H11.txt").write_bytes(b"[" * 65 + b"0" + b"]" * 65 + b"\n")
cases["H11"] = {"label": "excessive JSON nesting", "status": "rejected", "code": "KDEC001", "stage": "decode"}
OUT.joinpath("H12.txt").write_bytes(b" " * 1048577 + b"\n")
cases["H12"] = {"label": "excessive request and line size", "status": "rejected", "code": "KDEC002", "stage": "decode"}
original = (SPIKE / "B06.json").read_bytes()
OUT.joinpath("H15.txt").write_bytes(b'{"\\u0070rotocol":"x",' + original[1:])
cases["H15"] = {"label": "duplicate escaped JSON key", "status": "rejected", "code": "KDEC001", "stage": "decode"}
OUT.joinpath("H17.txt").write_bytes(original.replace(b"closed-boolean.yh", b"\\ud83d.yh"))
cases["H17"] = {"label": "malformed surrogate escape", "status": "rejected", "code": "KDEC001", "stage": "decode"}

HERE.joinpath("CASES.json").write_text(json.dumps(cases, indent=2, sort_keys=True) + "\n")
