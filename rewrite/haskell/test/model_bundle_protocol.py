"""Offline ModelBundle CLI, schema, fixture and bounded integrity checks."""

from __future__ import annotations

import hashlib
import json
import os
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
    assert outputs["MB04-stale-review"]["stale_reviews"] == ["review:1"]
    assert outputs["MB04-stale-review"]["applicable_asserted_reviews"] == []
    assert outputs["MB05-partial-review"]["partial_reviews"] == ["review:1"]
    for name in ("MB08-unknown-field", "MB09-length-mismatch", "MB22-symlink",
                 "MB25-duplicate-key", "MB27-digest-mismatch"):
        assert outputs[name]["bundle_digest"] is None, name
    missing = subprocess.run([executable, "validate", str(FIXTURES / "does-not-exist")],
                             capture_output=True, timeout=30)
    assert missing.returncode == 2 and json.loads(missing.stdout)["status"] == "io_error"
    usage = subprocess.run([executable, "invalid"], capture_output=True, timeout=30)
    assert usage.returncode == 2 and json.loads(usage.stdout)["diagnostics"][0]["code"] == "MBUSAGE001"
    print(f"model bundle: {len(cases)} fixtures, schemas, canonical bytes, "
          "regeneration, integrity and repeated-invocation recovery passed")


if __name__ == "__main__":
    main(sys.argv[1])
