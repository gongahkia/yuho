"""Offline diff CLI snapshots, schema and rejection checks."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "model-bundle-diff-fixtures"
EXISTING = HERE / "model-bundle-fixtures/bundles"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def location(name: str, root: Path = FIXTURES / "bundles") -> Path:
    return (EXISTING if name.startswith("MB") else root) / name


def run(executable: str, old: str, new: str, root: Path = FIXTURES / "bundles"):
    return subprocess.run([executable, "diff", str(location(old, root)),
                           str(location(new, root))], capture_output=True, timeout=60)


def main(executable: str, update: bool = False) -> None:
    cases = json.loads((FIXTURES / "CASES.json").read_bytes())
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_bytes())
    assert manifest["schema"] == "yuho.model-bundle-diff-fixture-manifest/v1"
    actual = {str(path.relative_to(FIXTURES)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (FIXTURES / "bundles").rglob("*") if path.is_file()}
    assert manifest["files"] == actual, "committed fixture manifest differs"
    with tempfile.TemporaryDirectory(prefix="yuho-diff-fixtures-") as temporary:
        regenerated = Path(temporary)
        subprocess.run([sys.executable, str(FIXTURES / "generate.py"),
                        str(regenerated / "bundles")], check=True)
        assert (regenerated / "CASES.json").read_bytes() == (FIXTURES / "CASES.json").read_bytes()
        assert (regenerated / "MANIFEST.json").read_bytes() == (FIXTURES / "MANIFEST.json").read_bytes()
    schema = json.loads((HERE.parent / "schema/model-bundle-change-set.schema.json").read_bytes())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    snapshots = FIXTURES / "snapshots"
    if update:
        snapshots.mkdir(exist_ok=True)
    outputs = {}
    for case in cases:
        first = run(executable, case["old"], case["new"])
        second = run(executable, case["old"], case["new"])
        assert first.returncode == second.returncode == case["exit"], (case["id"], first.stderr)
        assert (first.stdout, first.stderr) == (second.stdout, second.stderr), case["id"]
        selected = first.stdout if first.returncode == 0 else first.stderr
        other = first.stderr if first.returncode == 0 else first.stdout
        assert selected.endswith(b"\n") and selected.count(b"\n") == 1 and not other, case["id"]
        parsed = json.loads(selected)
        assert selected == canonical(parsed) + b"\n", case["id"]
        if first.returncode == 0:
            validator.validate(parsed)
            assert parsed["summary"]["total"] == len(parsed["changes"]), case["id"]
            for classification in ("added", "removed", "unchanged", "modified", "unknown-relationship"):
                assert parsed["summary"][classification] == sum(
                    row["classification"] == classification for row in parsed["changes"]), case["id"]
        else:
            assert parsed["diagnostics"], case["id"]
        snapshot = snapshots / f"{case['id']}.json"
        if update:
            snapshot.write_bytes(selected)
        else:
            assert selected == snapshot.read_bytes(), case["id"]
        outputs[case["id"]] = parsed
    assert outputs["DC01-identical"]["core_relation"] == "identical"
    assert outputs["DC01-identical"]["summary"]["total"] == outputs["DC01-identical"]["summary"]["unchanged"]
    assert outputs["DC02-review-only"]["core_relation"] == "identical"
    assert outputs["DC25-reordered-authoring"]["core_relation"] == "identical"
    assert outputs["DC02-review-only"]["review_impact"]["old_reviews_non_applicable_to_new"] == []
    assert outputs["DC10-old-review-nontransfer"]["review_impact"]["old_reviews_non_applicable_to_new"] == ["review:1"]
    assert outputs["DC07-scope-added"]["summary"]["added"] == outputs["DC08-scope-removed"]["summary"]["removed"]
    assert any(row["category"] == "legal_sources" and row["classification"] == "modified"
               for row in outputs["DC03-metadata"]["changes"])
    assert any(row["category"] == "semantic_mappings" and row["classification"] == "modified"
               for row in outputs["DC05-span"]["changes"])
    assert any(row["category"] == "artifacts" and row["classification"] == "added"
               for row in outputs["DC09-source-bytes"]["changes"])
    assert "f:root" in outputs["DC09-source-bytes"]["directly_affected_ids"]
    assert any(row["classification"] == "unknown-relationship" for row in outputs["DC06-model"]["changes"])
    assert any(row["category"] == "semantic_mappings" and row["classification"] == "unknown-relationship"
               for row in outputs["DC23-ambiguous-mapping"]["changes"])
    assert all(row["classification"] == "unchanged" for row in outputs["DC24-equal-multiple-mappings"]["changes"])
    assert outputs["DC06-model"]["wider_downstream_impact"] == "unknown"
    missing = subprocess.run([executable, "diff", str(FIXTURES / "absent"),
                              str(location("DX01-base"))], capture_output=True, timeout=30)
    assert missing.returncode == 2 and not missing.stdout
    usage = subprocess.run([executable, "diff"], capture_output=True, timeout=30)
    assert usage.returncode == 2 and not usage.stdout
    unsupported_version_check(executable)
    output_limit_check(executable)
    good = run(executable, "DX01-base", "DX03-source-metadata")
    assert good.returncode == 0, good.stderr
    assert good.stdout == run(executable, "DX01-base", "DX03-source-metadata").stdout
    print(f"model bundle diff: {len(cases)} snapshot cases, schema, deterministic bytes, "
          "fixture regeneration, direction, reviews, output limit and rejection recovery passed")


def output_limit_check(executable: str) -> None:
    with tempfile.TemporaryDirectory(prefix="yuho-diff-limit-") as temporary:
        roots = []
        for label in ("a", "b"):
            target = Path(temporary) / label
            shutil.copytree(location("DX01-base"), target)
            core = json.loads((target / "model-bundle.json").read_bytes())
            template = core["legal_sources"][0]
            for index in range(1000):
                item = dict(template)
                item["source_id"] = f"src:{label}{'x' * 108}{index:04}"
                item["manifestation_id"] = f"manifestation:{label}{'x' * 98}{index:04}"
                core["legal_sources"].append(item)
            core["legal_sources"].sort(key=lambda item: item["source_id"])
            core["scope"]["source_ids"] = sorted(item["source_id"] for item in core["legal_sources"])
            (target / "model-bundle.json").write_bytes(canonical(core))
            roots.append(target)
        completed = subprocess.run([executable, "diff", str(roots[0]), str(roots[1])],
                                   capture_output=True, timeout=90)
        assert completed.returncode == 4 and not completed.stdout, completed.stderr
        diagnostic = json.loads(completed.stderr)
        assert diagnostic["diagnostics"][0]["code"] == "MBCDRES001", diagnostic


def unsupported_version_check(executable: str) -> None:
    with tempfile.TemporaryDirectory(prefix="yuho-diff-version-") as temporary:
        target = Path(temporary) / "future"
        shutil.copytree(location("DX01-base"), target)
        core = json.loads((target / "model-bundle.json").read_bytes())
        core["schema"] = "yuho.model-bundle/v2"
        (target / "model-bundle.json").write_bytes(canonical(core))
        completed = subprocess.run([executable, "diff", str(location("DX01-base")), str(target)],
                                   capture_output=True, timeout=30)
        assert completed.returncode == 1 and not completed.stdout
        assert json.loads(completed.stderr)["diagnostics"][0]["code"] == "MBCAP001"


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], update=len(args) == 2 and args[1] == "--update-snapshots")
