"""TypedFiniteRules-v1 schemas, canonical bytes, refusals and persistent protocol."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from jsonschema import Draft202012Validator

WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = WORKSPACE.parents[1]
FIXTURES = ROOT / "examples/typed-finite"
INPUT_KEYS = ("input_schema", "fragment", "program", "policy")


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode()


def compile_request(yuho, model, scenario):
    completed = subprocess.run(
        [str(yuho), "compile", str(model), "--scenario", str(scenario)],
        cwd=ROOT, capture_output=True, check=True, timeout=30,
    )
    assert not completed.stderr
    request = json.loads(completed.stdout)
    assert completed.stdout == canonical(request).rstrip(b"\n")
    return request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("yuho", type=Path)
    parser.add_argument("kernel", type=Path)
    args = parser.parse_args()
    yuho = args.yuho.resolve()
    kernel = args.kernel.resolve()

    request_schema = json.loads((WORKSPACE / "schema/typed-finite-rules-request.schema.json").read_bytes())
    result_schema = json.loads((WORKSPACE / "schema/typed-finite-rules-result.schema.json").read_bytes())
    Draft202012Validator.check_schema(request_schema)
    Draft202012Validator.check_schema(result_schema)
    request_validator = Draft202012Validator(request_schema)
    result_validator = Draft202012Validator(result_schema)

    pairs = [
        ("fictional", "fictional-typed-rules.yh", "fictional-typed-rules-satisfied.yh"),
        ("property", "multi-person-property.yh", "multi-person-property-scenario.yh"),
        ("modular", "modular-typed-rules.yh", "modular-typed-rules-scenario.yh"),
        ("section82", ROOT / "research/singapore/research-release/typed-section82-showcase.yh",
         ROOT / "research/singapore/research-release/typed-section82-showcase-scenario.yh"),
    ]
    requests = {}
    for name, model_name, scenario_name in pairs:
        model = model_name if isinstance(model_name, Path) else FIXTURES / model_name
        scenario = scenario_name if isinstance(scenario_name, Path) else FIXTURES / scenario_name
        request = compile_request(yuho, model, scenario)
        request_validator.validate(request)
        requests[name] = request

    sequence = ["fictional", "property", "modular", "section82"] * 2
    wire = b"".join(canonical(requests[name]) for name in sequence)
    completed = subprocess.run([str(kernel)], input=wire, capture_output=True,
                               check=True, timeout=30)
    assert not completed.stderr
    lines = completed.stdout.splitlines(keepends=True)
    assert len(lines) == len(sequence)
    seen = {}
    for name, line in zip(sequence, lines, strict=True):
        result = json.loads(line)
        result_validator.validate(result)
        assert line == canonical(result)
        assert result["status"] == "evaluated"
        assert result["fragment"] == "TypedFiniteRules-v1"
        request = requests[name]
        digest = hashlib.sha256(canonical({key: request[key] for key in INPUT_KEYS}).rstrip(b"\n")).hexdigest()
        assert result["input_digest"] == digest
        assert seen.setdefault(name, line) == line

    malformed = []
    cycle = json.loads(canonical(requests["fictional"]))
    cycle["program"]["priorities"].append(
        {"higher": "r:general", "lower": "r:minor-exception"})
    malformed.append(cycle)
    wrong_type = json.loads(canonical(requests["fictional"]))
    wrong_type["program"]["facts"][0]["arguments"].reverse()
    malformed.append(wrong_type)
    unknown_kind = json.loads(canonical(requests["fictional"]))
    unknown_kind["program"]["requirements"][0]["expression"]["kind"] = "unbounded-exists"
    malformed.append(unknown_kind)
    completed = subprocess.run([str(kernel)], input=b"".join(map(canonical, malformed)),
                               capture_output=True, check=True, timeout=30)
    for line in completed.stdout.splitlines():
        result = json.loads(line)
        result_validator.validate(result)
        assert result["status"] == "rejected"
        assert result["diagnostics"][0]["code"] == "KTF001"

    with tempfile.TemporaryDirectory(prefix="yuho-typed-atomic-") as folder:
        destination = Path(folder) / "must-not-exist.json"
        missing_scenario = Path(folder) / "missing.yh"
        missing_scenario.write_text(
            "typed-rules-scenario Missing for FictionalTypedFiniteRules-v0.2 {\n}\n",
            encoding="utf-8",
        )
        failed = subprocess.run(
            [str(yuho), "compile", str(FIXTURES / "fictional-typed-rules.yh"),
             "--scenario", str(missing_scenario), "--output", str(destination)],
            cwd=ROOT, capture_output=True, timeout=30,
        )
        assert failed.returncode != 0 and not destination.exists()

    print("typed finite protocol: 4 compiled requests, 8 persistent evaluations, "
          "3 kernel refusals, schemas, canonical bytes and atomic failure passed")


if __name__ == "__main__":
    main()
