"""Offline ModelBundle CLI, schema, fixture and bounded integrity checks."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
FIXTURES = HERE / "model-bundle-fixtures"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode()


def tree_inventory(root: Path) -> dict[str, tuple[str, str]]:
    result = {}
    for path in root.rglob("*"):
        relative = str(path.relative_to(root))
        if path.is_symlink():
            result[relative] = ("symlink", os.readlink(path))
        elif path.is_file():
            result[relative] = ("file", hashlib.sha256(path.read_bytes()).hexdigest())
    return result


def main(executable: str) -> None:
    schemas = {}
    for name in ("core", "review", "validation"):
        path = WORKSPACE / f"schema/model-bundle-{name}.schema.json"
        schema = json.loads(path.read_bytes())
        Draft202012Validator.check_schema(schema)
        schemas[name] = Draft202012Validator(schema)
    cases = json.loads((FIXTURES / "CASES.json").read_bytes())
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_bytes())
    assert manifest["schema"] == "yuho.model-bundle-fixture-manifest/v1"
    assert manifest["base_request_sha256"] == hashlib.sha256(
        (HERE / "presumption-fixtures/requests/RD01.json").read_bytes()).hexdigest()
    expected_files = manifest["files"]
    actual_files = {str(path.relative_to(FIXTURES)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (FIXTURES / "bundles").rglob("*")
                    if path.is_file() and not path.is_symlink()}
    assert actual_files == expected_files, "fixture manifest differs from committed bytes"
    with tempfile.TemporaryDirectory(prefix="yuho-bundle-fixtures-") as temporary:
        regenerated = Path(temporary)
        subprocess.run([sys.executable, str(FIXTURES / "generate.py"),
                        str(regenerated / "bundles")], check=True)
        assert (regenerated / "CASES.json").read_bytes() == (FIXTURES / "CASES.json").read_bytes()
        assert (regenerated / "MANIFEST.json").read_bytes() == (FIXTURES / "MANIFEST.json").read_bytes()
        assert tree_inventory(regenerated / "bundles") == tree_inventory(FIXTURES / "bundles")
    outputs = {}
    for case in cases:
        path = FIXTURES / "bundles" / case["id"]
        args = [executable, "validate", str(path)]
        if case["policy"]:
            args.extend(["--require-asserted-review-purpose", case["policy"]])
        first = subprocess.run(args, capture_output=True, timeout=30)
        second = subprocess.run(args, capture_output=True, timeout=30)
        assert first.returncode == second.returncode == case["exit"], case["id"]
        assert first.stdout == second.stdout and first.stderr == second.stderr == b"", case["id"]
        assert first.stdout.endswith(b"\n") and first.stdout.count(b"\n") == 1, case["id"]
        result = json.loads(first.stdout)
        schemas["validation"].validate(result)
        assert first.stdout == canonical(result) + b"\n", case["id"]
        code = result["diagnostics"][0]["code"] if result["diagnostics"] else ""
        assert code == case["code"], (case["id"], code, case["code"])
        if case["bundle_digest"]:
            assert result["bundle_digest"] == case["bundle_digest"], case["id"]
        outputs[case["id"]] = result
        if case["exit"] in (0, 3):
            core = json.loads((path / "model-bundle.json").read_bytes())
            schemas["core"].validate(core)
            for review in (path / "reviews").glob("*.json") if (path / "reviews").exists() else []:
                schemas["review"].validate(json.loads(review.read_bytes()))
    assert outputs["MB01-minimal"]["bundle_digest"] == outputs["MB02-review"]["bundle_digest"]
    assert outputs["MB01-minimal"]["bundle_digest"] != outputs["MB07-core-change"]["bundle_digest"]
    assert outputs["MB01-minimal"]["bundle_digest"] != outputs["MB69-unverified-publisher-label"]["bundle_digest"]
    assert outputs["MB01-minimal"]["bundle_digest"] != outputs["MB70-wrong-but-valid-passage"]["bundle_digest"]
    assert outputs["MB04-stale-review"]["stale_reviews"] == ["review:1"]
    assert outputs["MB04-stale-review"]["applicable_asserted_reviews"] == []
    assert outputs["MB05-partial-review"]["partial_reviews"] == ["review:1"]
    assert outputs["MB64-stale-old-coverage"]["stale_reviews"] == ["review:1"]
    assert outputs["MB62-shared-locator-distinct-bytes"]["status"] == "valid"
    assert outputs["MB63-multiple-mappings"]["status"] == "valid"
    for name in ("MB08-unknown-field", "MB09-length-mismatch", "MB22-symlink",
                 "MB25-duplicate-key", "MB27-digest-mismatch"):
        assert outputs[name]["bundle_digest"] is None, name
    missing = subprocess.run([executable, "validate", str(FIXTURES / "does-not-exist")],
                             capture_output=True, timeout=30)
    assert missing.returncode == 2 and json.loads(missing.stdout)["status"] == "io_error"
    usage = subprocess.run([executable, "invalid"], capture_output=True, timeout=30)
    assert usage.returncode == 2 and json.loads(usage.stdout)["diagnostics"][0]["code"] == "MBUSAGE001"
    resource_checks(executable)
    print(f"model bundle: {len(cases)} fixtures, schemas, canonical bytes, "
          "regeneration, bounded resource checks, integrity and repeated-invocation recovery passed")


def resource_checks(executable: str) -> None:
    source = FIXTURES / "bundles/MB01-minimal"
    with tempfile.TemporaryDirectory(prefix="yuho-bundle-limits-") as temporary:
        root = Path(temporary)

        def run(name: str, mutate, expected: str = "MBRES001") -> None:
            package = root / name
            shutil.copytree(source, package)
            core = json.loads((package / "model-bundle.json").read_bytes())
            mutate(package, core)
            (package / "model-bundle.json").write_bytes(canonical(core))
            completed = subprocess.run([executable, "validate", str(package)],
                                       capture_output=True, timeout=30)
            assert completed.returncode == 1, (name, completed.stdout)
            result = json.loads(completed.stdout)
            assert result["diagnostics"][0]["code"] == expected, (name, result)

        run("source-count", lambda _p, c: c["legal_sources"].extend(
            [c["legal_sources"][0]] * 1025))
        run("derivation-count", lambda _p, c: c["derivations"].extend([{
            "child_digest": "0" * 64, "parent_digest": "1" * 64,
            "tool_name": "fixture", "tool_version": "1", "configuration": "none"}]
            * 4097))
        run("scope-id-count", lambda _p, c: c["scope"].update(
            semantic_ids=[f"x:{i:04}" for i in range(8193)]))
        run("artifact-size", lambda _p, c: c["artifacts"][0].update(byte_length=33554433))
        def large_file(package: Path, core: dict) -> None:
            target = package / "artifacts/sha256" / core["artifacts"][0]["sha256"]
            with target.open("r+b") as stream:
                stream.truncate(33554433)
        run("actual-artifact-size", large_file)
        def combined(_package: Path, core: dict) -> None:
            core["artifacts"].extend([{
                "sha256": f"{i + 10:064x}", "byte_length": 33554432,
                "media_type": "application/pdf", "role": "evidence"} for i in range(5)])
            core["artifacts"].sort(key=lambda item: item["sha256"])
        run("combined-size", combined)
        run("review-size", lambda p, _c: (
            (p / "reviews").mkdir(), (p / "reviews/review:large.json").write_bytes(b" " * 1048577)))
        run("metadata-depth", lambda _p, c: c["scope"].update(
            limitations=[[[[[[[[[[[[[[[[["deep"]]]]]]]]]]]]]]]]]), expected="MBRES001")
        def fifo(package: Path, core: dict) -> None:
            target = package / "artifacts/sha256" / core["artifacts"][0]["sha256"]
            target.unlink()
            os.mkfifo(target)
        run("special-file", fifo, expected="MBPKG001")


if __name__ == "__main__":
    main(sys.argv[1])
