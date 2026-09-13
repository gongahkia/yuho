"""Generate compact synthetic comparison bundles; snapshots need an explicit flag."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST = HERE.parent
sys.path.insert(0, str(TEST / "model-bundle-fixtures"))
from generate import base, canon, review, sha, write_bundle  # noqa: E402


def replace_blob(core: dict, blobs: dict[str, bytes], old: str, data: bytes) -> str:
    new = sha(data)
    blobs.pop(old)
    blobs[new] = data
    for artifact in core["artifacts"]:
        if artifact["sha256"] == old:
            artifact["sha256"] = new
            artifact["byte_length"] = len(data)
    core["artifacts"].sort(key=lambda item: item["sha256"])
    return new


def make(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    core, blobs = base()
    write_bundle(output / "DX01-base", core, blobs)
    write_bundle(output / "DX02-same-core-review", core, blobs,
                 {"review:1.json": review(core)})

    changed = copy.deepcopy(core)
    changed["legal_sources"][0]["publisher_label"] = "different descriptive label"
    write_bundle(output / "DX03-source-metadata", changed, blobs)

    changed = copy.deepcopy(core)
    changed["scope"]["exclusions"] = [{"exclusion_id": "excluded:1", "reason": "synthetic omission"}]
    write_bundle(output / "DX04-scope", changed, blobs)

    changed = copy.deepcopy(core)
    changed["semantic_mappings"][0]["span"] = {
        "start": 2, "end": 3, "start_line": 2, "start_col": 1,
        "end_line": 2, "end_col": 2,
    }
    write_bundle(output / "DX05-span", changed, blobs)

    changed, payload = copy.deepcopy(core), dict(blobs)
    model_digest = changed["executable_model"]["artifact_digest"]
    request = json.loads(payload[model_digest])
    request["request_id"] = "D99"
    changed["executable_model"]["artifact_digest"] = replace_blob(
        changed, payload, model_digest, canon(request))
    write_bundle(output / "DX06-model-artifact", changed, payload)

    changed, payload = copy.deepcopy(core), dict(blobs)
    model_digest = changed["executable_model"]["artifact_digest"]
    request = json.loads(payload[model_digest])
    extra = copy.deepcopy(request["registry"][0]["program"]["penalties"][0])
    extra["penalty_id"] = "pen:root:2"
    extra["term"]["term_id"] = "term:fixture:2"
    request["registry"][0]["program"]["penalties"].append(extra)
    changed["executable_model"]["artifact_digest"] = replace_blob(
        changed, payload, model_digest, canon(request))
    changed["scope"]["semantic_ids"] = sorted(changed["scope"]["semantic_ids"]
                                              + ["pen:root:2", "term:fixture:2"])
    template = changed["semantic_mappings"][0]
    for sid in ("pen:root:2", "term:fixture:2"):
        mapping = copy.deepcopy(template)
        mapping["semantic_id"] = sid
        changed["semantic_mappings"].append(mapping)
    changed["semantic_mappings"].sort(key=lambda item: (item["semantic_id"],
        item["artifact_digest"], item["span"]["start"], item["span"]["end"]))
    write_bundle(output / "DX07-positive-scope", changed, payload)

    changed, payload = copy.deepcopy(core), dict(blobs)
    old_text = changed["legal_sources"][0]["artifact_digest"]
    new_text = blobs[old_text] + b"extra\n"
    new_digest = replace_blob(changed, payload, old_text, new_text)
    changed["legal_sources"][0]["artifact_digest"] = new_digest
    for mapping in changed["semantic_mappings"]:
        mapping["artifact_digest"] = new_digest
    model_digest = changed["executable_model"]["artifact_digest"]
    request = json.loads(payload[model_digest])
    request["sources"][0]["text"] = new_text.decode()
    request["sources"][0]["sha256"] = new_digest
    changed["executable_model"]["artifact_digest"] = replace_blob(
        changed, payload, model_digest, canon(request))
    write_bundle(output / "DX08-source-bytes", changed, payload)

    changed = copy.deepcopy(core)
    write_bundle(output / "DX09-fresh-review", changed, blobs,
                 {"review:1.json": review(changed)})
    changed = copy.deepcopy(core)
    changed["model_id"] = "model:changed"
    write_bundle(output / "DX10-stale-review", changed, blobs,
                 {"review:1.json": review(core)})

    cases = [
        ("DC01-identical", "DX01-base", "DX01-base", 0),
        ("DC02-review-only", "DX01-base", "DX02-same-core-review", 0),
        ("DC03-metadata", "DX01-base", "DX03-source-metadata", 0),
        ("DC04-scope", "DX01-base", "DX04-scope", 0),
        ("DC05-span", "DX01-base", "DX05-span", 0),
        ("DC06-model", "DX01-base", "DX06-model-artifact", 0),
        ("DC07-scope-added", "DX01-base", "DX07-positive-scope", 0),
        ("DC08-scope-removed", "DX07-positive-scope", "DX01-base", 0),
        ("DC09-source-bytes", "DX01-base", "DX08-source-bytes", 0),
        ("DC10-old-review-nontransfer", "DX02-same-core-review", "DX03-source-metadata", 0),
        ("DC11-fresh-review", "DX03-source-metadata", "DX09-fresh-review", 0),
        ("DC12-stale-review", "DX01-base", "DX10-stale-review", 0),
        ("DC13-added-source", "DX01-base", "MB36-two-manifestations", 0),
        ("DC14-removed-source", "MB36-two-manifestations", "DX01-base", 0),
        ("DC15-extraction", "DX01-base", "MB37-extracted-text", 0),
        ("DC16-expressions", "DX01-base", "MB38-two-expressions", 0),
        ("DC17-multiple-mappings", "DX01-base", "MB63-multiple-mappings", 0),
        ("DC18-reverse", "DX03-source-metadata", "DX01-base", 0),
        ("DC19-invalid-old", "MB08-unknown-field", "DX01-base", 1),
        ("DC20-invalid-new", "DX01-base", "MB09-length-mismatch", 1),
        ("DC21-invalid-both", "MB08-unknown-field", "MB09-length-mismatch", 1),
        ("DC22-resource-invalid", "MB31-oversize-manifest", "DX01-base", 1),
    ]
    (output.parent / "CASES.json").write_bytes(canon([
        {"id": name, "old": old, "new": new, "exit": code}
        for name, old, new, code in cases]) + b"\n")
    inventory = {str(path.relative_to(output.parent)): sha(path.read_bytes())
                 for path in output.rglob("*") if path.is_file()}
    (output.parent / "MANIFEST.json").write_bytes(canon({
        "schema": "yuho.model-bundle-diff-fixture-manifest/v1",
        "files": dict(sorted(inventory.items())),
    }) + b"\n")


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "bundles"
    make(destination)
