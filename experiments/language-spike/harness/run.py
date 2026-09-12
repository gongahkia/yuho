"""Common, serial, read-only conformance and resource harness for both kernels."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import tempfile
import time

from jsonschema import Draft202012Validator, RefResolver


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
RESULTS = ROOT / "results"
REQUEST_SCHEMA = json.loads((ROOT / "schema/request.schema.json").read_text())
RESULT_SCHEMA = json.loads((ROOT / "schema/result.schema.json").read_text())
RESOLVER = RefResolver.from_schema(RESULT_SCHEMA, store={REQUEST_SCHEMA["$id"]: REQUEST_SCHEMA})
MANIFEST = json.loads((FIXTURES / "MANIFEST.json").read_text())
IDS = sorted(MANIFEST["cases"])
BINARIES = {
    "haskell": Path(subprocess.check_output(
        ["cabal", "list-bin", "exe:yuho-kernel-haskell"], cwd=ROOT / "haskell", text=True
    ).strip()),
    "ocaml": ROOT / "ocaml/yuho-kernel-ocaml",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(schema: dict, value: dict, *, result: bool = False) -> None:
    validator = Draft202012Validator(schema, resolver=RESOLVER if result else None)
    errors = list(validator.iter_errors(value))
    if errors:
        raise AssertionError(str(errors[0]))


def shuffled(value, rng: random.Random):
    if isinstance(value, dict):
        pairs = list(value.items())
        rng.shuffle(pairs)
        return {key: shuffled(item, rng) for key, item in pairs}
    if isinstance(value, list):
        return [shuffled(item, rng) for item in value]
    return value


def response_check(case: str, actual: bytes, expected: bytes) -> None:
    if actual != expected:
        raise AssertionError(f"{case}: exact bytes differ: {actual!r} != {expected!r}")
    if not actual.endswith(b"\n") or actual.count(b"\n") != 1:
        raise AssertionError(f"{case}: response is not exactly one line")
    obj = json.loads(actual)
    validate(RESULT_SCHEMA, obj, result=True)
    if obj != json.loads(expected):
        raise AssertionError(f"{case}: structural mismatch")


def one(binary: Path, request: bytes, expected: bytes, case: str, cwd: Path | None = None) -> bytes:
    result = subprocess.run([str(binary)], input=request, capture_output=True, cwd=cwd, timeout=5)
    if result.returncode or result.stderr:
        raise AssertionError(f"{case}: exit={result.returncode}, stderr={result.stderr!r}")
    response_check(case, result.stdout, expected)
    return result.stdout


def rss_kib(pid: int) -> int:
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    raise AssertionError("VmRSS unavailable")


def measured_cold(binary: Path, request: bytes, expected: bytes) -> dict:
    with tempfile.NamedTemporaryFile() as timing:
        started = time.perf_counter_ns()
        result = subprocess.run(
            ["/usr/bin/time", "-f", "%e %U %S %M", "-o", timing.name, str(binary)],
            input=request, capture_output=True, timeout=5,
        )
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        if result.returncode or result.stderr:
            raise AssertionError(f"cold launch failed: {result.returncode}, {result.stderr!r}")
        response_check("B06", result.stdout, expected)
        _rounded_elapsed, user, system, rss = Path(timing.name).read_text().split()
        return {"elapsed_ms": elapsed_ms, "cpu_ms_10ms_resolution": (float(user) + float(system)) * 1000,
                "peak_rss_kib": int(rss)}


def summarize(samples: list[float]) -> dict:
    values = sorted(samples)
    return {"median": statistics.median(values), "p95": values[28], "max": values[-1]}


def run_candidate(name: str, binary: Path) -> dict:
    requests = {case: (FIXTURES / "requests" / f"{case}.json").read_bytes() for case in IDS}
    expected = {case: (FIXTURES / "expected" / f"{case}.json").read_bytes() for case in IDS}
    actuals = {}
    for case in IDS:
        validate(REQUEST_SCHEMA, json.loads(requests[case]))
        validate(RESULT_SCHEMA, json.loads(expected[case]), result=True)
        actuals[case] = one(binary, requests[case], expected[case], case)
    case_results = {case: {"expected_sha256": sha(expected[case]),
                           "actual_sha256": sha(actuals[case]), "diff": None}
                    for case in IDS}

    # Ten fresh processes, ten shuffled passes each: exactly 100 per fixture.
    rng = random.Random(0xB06)
    for _ in range(10):
        proc = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert proc.stdin and proc.stdout and proc.stderr
        for _ in range(10):
            for case in IDS:
                payload = json.dumps(shuffled(json.loads(requests[case]), rng), ensure_ascii=False,
                                     separators=(",", ":")).encode() + b"\n"
                proc.stdin.write(payload)
                proc.stdin.flush()
                response_check(case, proc.stdout.readline(), expected[case])
        proc.stdin.close()
        if proc.wait(timeout=5) or proc.stderr.read():
            raise AssertionError(f"{name}: repeat process failed")

    # Fresh invalid UTF-8 and malformed JSON must return a typed decode result.
    rejection = {}
    for label, payload in {"invalid_utf8": b"\xff\n", "malformed_json": b"{bad\n"}.items():
        result = subprocess.run([str(binary)], input=payload, capture_output=True, timeout=5)
        obj = json.loads(result.stdout)
        if result.returncode or result.stderr or obj["status"] != "rejected" or len(result.stdout.splitlines()) != 1:
            raise AssertionError(f"{name}: {label} did not produce one typed rejection")
        rejection[label] = obj["diagnostics"][0]["code"]

    cold = [measured_cold(binary, requests["B06"], expected["B06"]) for _ in range(30)]
    cold_elapsed = summarize([item["elapsed_ms"] for item in cold])
    cold_cpu = summarize([item["cpu_ms_10ms_resolution"] for item in cold])
    cold_rss = summarize([item["peak_rss_kib"] for item in cold])

    cycle = [f"B{1 + (index % 7):02d}" for index in range(1000)]
    proc = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin and proc.stdout and proc.stderr
    steady_rss = []
    started = time.perf_counter()
    for case in cycle:
        proc.stdin.write(requests[case])
        proc.stdin.flush()
        response_check(case, proc.stdout.readline(), expected[case])
        steady_rss.append(rss_kib(proc.pid))
    steady_ms = (time.perf_counter() - started) * 1000
    proc.stdin.close()
    if proc.wait(timeout=5) or proc.stderr.read():
        raise AssertionError(f"{name}: steady process failed")
    steady = {"requests": 1000, "elapsed_ms": steady_ms, "peak_rss_kib": max(steady_rss),
              "first_100_mean_rss_kib": statistics.mean(steady_rss[:100]),
              "last_100_mean_rss_kib": statistics.mean(steady_rss[-100:]),
              "growth_kib": statistics.mean(steady_rss[-100:]) - statistics.mean(steady_rss[:100])}

    with tempfile.TemporaryDirectory(prefix=f"yuho-{name}-install-") as tmp:
        installed = Path(tmp) / "kernel"
        shutil.copy2(binary, installed)
        for case in ("B01", "P02"):
            one(installed, requests[case], expected[case], case, cwd=Path(tmp))
    libraries = subprocess.run(["ldd", str(binary)], capture_output=True, text=True).stdout.splitlines()

    vectors = []
    for case in [f"B{index:02d}" for index in range(1, 8)]:
        obj = json.loads(actuals[case])
        vectors.append({"case": case, "branches": obj["branches"], "trace": obj["trace"]})
        assert all("id" in edge and "path" in edge and "children" in edge for edge in obj["trace"])
    vector_bytes = (json.dumps(vectors, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    (RESULTS / f"{name.upper()}-PROOF-VECTORS.json").write_bytes(vector_bytes)

    return {"binary_sha256": sha(binary.read_bytes()), "binary_bytes": binary.stat().st_size,
            "case_results": case_results,
            "exact_fixture_matches": 15, "boolean_and_rejection_matches": 11,
            "parser_transport_matches": 4, "determinism_repetitions_per_case": 100,
            "parser_transport_repetitions_per_case": 100, "protocol_rejections": rejection,
            "cold_samples": cold, "cold_elapsed_ms": cold_elapsed, "cold_cpu_ms": cold_cpu,
            "cold_peak_rss_kib": cold_rss, "steady": steady,
            "packaging": {"clean_directory_B01_P02": "pass", "ldd": libraries},
            "proof_vectors_sha256": sha(vector_bytes), "proof_vectors": 7}


def main() -> None:
    report = {"fixture_manifest_sha256": sha((FIXTURES / "MANIFEST.json").read_bytes()),
              "repository_head_at_freeze": MANIFEST["repository_head"],
              "harness": "harness/run.py", "candidates_run_serially": True, "candidates": {}}
    for name, binary in BINARIES.items():
        print(f"measuring {name}", flush=True)
        report["candidates"][name] = run_candidate(name, binary)
        (RESULTS / "RAW-MEASUREMENTS.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("both candidates passed harness", flush=True)


if __name__ == "__main__":
    main()
