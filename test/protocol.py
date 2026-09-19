"""Exercise the production executable as a persistent, line-oriented subprocess."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "test/kernel-fixtures/frozen"
HARDENING = ROOT / "test/fixtures"
FROZEN_IDS = [
    "B01", "B02", "B03", "B04", "B05", "B06", "B07",
    "P01", "P02", "P03", "P04", "R01", "R02", "R03", "R04",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    cases = json.loads((HARDENING / "CASES.json").read_text())
    inputs = [(name, (FROZEN / "requests" / f"{name}.json").read_bytes()) for name in FROZEN_IDS]
    for name in sorted(cases):
        extension = ".txt" if name in {"H11", "H12", "H15", "H17"} else ".json"
        inputs.append((name, (HARDENING / "requests" / f"{name}{extension}").read_bytes()))
    inputs.extend([inputs[0]] * 20)  # requests after the overlong line must still work
    inputs.append(next(item for item in inputs if item[0] == "H13"))

    payload = b"".join(request.rstrip(b"\n") + b"\n" for _, request in inputs)
    completed = subprocess.run(
        [str(args.executable.resolve())], input=payload, capture_output=True,
        check=True, timeout=30,
    )
    assert not completed.stderr, f"unexpected stderr: {completed.stderr!r}"
    lines = completed.stdout.splitlines(keepends=True)
    assert len(lines) == len(inputs), f"response count: {len(lines)} vs {len(inputs)}"
    assert all(line.endswith(b"\n") and line.count(b"\n") == 1 for line in lines)

    first_response: dict[str, bytes] = {}
    for (name, _), line in zip(inputs, lines, strict=True):
        assert line == first_response.setdefault(name, line), f"nondeterministic response: {name}"
        if name in FROZEN_IDS:
            expected = (FROZEN / "expected" / f"{name}.json").read_bytes()
            assert line == expected, f"frozen byte mismatch: {name}"
            continue
        expected = cases[name]
        response = json.loads(line)
        assert response["status"] == expected["status"], name
        diagnostics = response["diagnostics"]
        if expected["code"]:
            assert len(diagnostics) == 1, name
            assert diagnostics[0]["code"] == expected["code"], name
            assert diagnostics[0]["stage"] == expected["stage"], name
            assert response["status"] == "rejected", name
        else:
            assert diagnostics == [], name
        if name == "H16":
            request = json.loads((HARDENING / "requests/H16.json").read_bytes())
            digest_fields = ("input_schema", "fragment", "source", "program", "facts", "policy")
            canonical = json.dumps(
                {key: request[key] for key in digest_fields}, sort_keys=True,
                ensure_ascii=False, separators=(",", ":"),
            ).encode("utf-8")
            assert response["input_digest"] == hashlib.sha256(canonical).hexdigest(), name

    print(f"protocol: {len(FROZEN_IDS)} frozen goldens, {len(cases)} hardening cases, persistent recovery passed")


if __name__ == "__main__":
    main()
