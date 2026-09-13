"""Generate synthetic, content-addressed ModelBundle v1 package fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
BASE_REQUEST = WORKSPACE / "test/presumption-fixtures/requests/RD01.json"
DOMAIN = b"yuho.model-bundle/v1\0"
SCOPE_DOMAIN = b"yuho.model-scope/v1\0"


def canon(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def semantic_ids(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, list):
        for item in value:
            found.extend(semantic_ids(item))
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"id", "exception_id", "penalty_id", "term_id", "presumption_id"} \
                    and isinstance(item, str):
                found.append(item)
            found.extend(semantic_ids(item))
    return found


def base() -> tuple[dict, dict[str, bytes]]:
    request = json.loads(BASE_REQUEST.read_bytes())
    model_bytes = canon(request)
    text_bytes = request["sources"][0]["text"].encode()
    model_digest, text_digest = sha(model_bytes), sha(text_bytes)
    ids = sorted(semantic_ids(request["registry"]) + semantic_ids(request["presumptions"]))
    span = {"start": 0, "end": 1, "start_line": 1, "start_col": 1,
            "end_line": 1, "end_col": 2}
    core = {
        "schema": "yuho.model-bundle/v1",
        "canonical_profile": "yuho.sorted-json/v1",
        "hash_algorithm": "sha256",
        "model_id": "model:synthetic",
        "artifacts": [
            {"sha256": model_digest, "byte_length": len(model_bytes),
             "media_type": "application/json", "role": "executable_model"},
            {"sha256": text_digest, "byte_length": len(text_bytes),
             "media_type": "text/plain; charset=utf-8", "role": "source_text"},
        ],
        "legal_sources": [{
            "source_id": "src:main", "work_id": "work:synthetic",
            "expression_id": "expression:synthetic:1",
            "manifestation_id": "manifestation:text:1",
            "artifact_digest": text_digest, "source_type": "synthetic",
            "language": "en", "jurisdiction": "SYN", "identifiers": [], "dates": {},
            "publisher_label": "synthetic fixture author",
            "locator": "fixture:synthetic:1",
        }],
        "derivations": [],
        "semantic_mappings": [{
            "semantic_id": sid, "artifact_digest": text_digest,
            "source_id": "src:main", "role": "supporting_context", "span": span,
        } for sid in ids],
        "scope": {
            "coverage_mode": "enumerated_only", "semantic_ids": ids,
            "source_ids": ["src:main"],
            "expression_ids": ["expression:synthetic:1"],
            "exclusions": [], "limitations": ["synthetic technical fixture"],
            "unsupported_capabilities": [], "jurisdictions": ["SYN"],
            "subject_matters": ["synthetic"],
            "temporal_context": {"kind": "unspecified"},
        },
        "executable_model": {"artifact_digest": model_digest,
                             "format": "yuho.kernel-input/v1",
                             "fragment": request["fragment"]},
    }
    core["artifacts"].sort(key=lambda x: x["sha256"])
    return core, {model_digest: model_bytes, text_digest: text_bytes}


def review(core: dict, *, stale: bool = False, coverage: str = "scope_digest",
           purpose: str = "semantic_fidelity", review_id: str = "review:1") -> dict:
    bundle_digest = sha(DOMAIN + canon(core))
    scope_digest = sha(SCOPE_DOMAIN + canon(core["scope"]))
    if stale:
        bundle_digest = "0" * 64
    if coverage == "scope_digest":
        coverage_value = {"kind": "scope_digest", "scope_digest": scope_digest}
    elif coverage == "semantic_ids":
        coverage_value = {"kind": "semantic_ids",
                          "semantic_ids": core["scope"]["semantic_ids"][:1]}
    else:
        coverage_value = {"kind": "source_ids", "source_ids": ["src:main"]}
    return {
        "schema": "yuho.review-assertion/v1", "review_id": review_id,
        "bundle_digest": bundle_digest, "scope_digest": scope_digest,
        "purposes": [purpose], "coverage": coverage_value,
        "limitations": ["synthetic test review; no authority"],
        "outcome": "asserted_acceptable", "reviewed_at": "2026-09-13T00:00:00Z",
        "reviewer": {"reviewer_id": "reviewer:synthetic", "name": "Synthetic Reviewer",
                     "role": "fixture", "organisation": "none"},
    }


def write_bundle(path: Path, core: dict, blobs: dict[str, bytes],
                 reviews: dict[str, dict] | None = None) -> None:
    if path.exists():
        shutil.rmtree(path)
    store = path / "artifacts/sha256"
    store.mkdir(parents=True)
    (path / "model-bundle.json").write_bytes(canon(core))
    for name, data in blobs.items():
        (store / name).write_bytes(data)
    for name, value in (reviews or {}).items():
        target = path / "reviews"
        target.mkdir(exist_ok=True)
        (target / name).write_bytes(canon(value))


def make(output: Path) -> list[dict]:
    output.mkdir(parents=True, exist_ok=True)
    cases: list[dict] = []

    def add(name: str, core: dict, blobs: dict[str, bytes],
            expected: int, code: str = "", reviews: dict[str, dict] | None = None,
            policy: str | None = None) -> Path:
        path = output / name
        write_bundle(path, core, blobs, reviews)
        cases.append({"id": name, "exit": expected, "code": code,
                      "policy": policy,
                      "bundle_digest": sha(DOMAIN + canon(core)) if expected in (0, 3) else None})
        return path

    core, blobs = base()
    add("MB01-minimal", core, blobs, 0)
    add("MB02-review", core, blobs, 0, reviews={"review:1.json": review(core)},
        policy="semantic_fidelity")
    add("MB03-unmet-policy", core, blobs, 3, policy="source_fidelity")
    add("MB04-stale-review", core, blobs, 3,
        reviews={"review:1.json": review(core, stale=True)}, policy="semantic_fidelity")
    add("MB05-partial-review", core, blobs, 3,
        reviews={"review:1.json": review(core, coverage="semantic_ids")},
        policy="semantic_fidelity")
    changed = copy.deepcopy(core)
    changed["scope"]["exclusions"] = [{"exclusion_id": "excluded:1", "reason": "outside synthetic slice"}]
    add("MB06-exclusion", changed, blobs, 0)
    changed = copy.deepcopy(core)
    changed["model_id"] = "model:changed"
    add("MB07-core-change", changed, blobs, 0)
    changed = copy.deepcopy(core)
    changed["extra"] = 1
    add("MB08-unknown-field", changed, blobs, 1, "MBDEC001")
    changed = copy.deepcopy(core)
    changed["artifacts"][0]["byte_length"] += 1
    add("MB09-length-mismatch", changed, blobs, 1, "MBINV001")
    changed = copy.deepcopy(core)
    changed["scope"]["semantic_ids"] = changed["scope"]["semantic_ids"][:-1]
    add("MB10-unmapped-id", changed, blobs, 1, "MBINV001")
    changed = copy.deepcopy(core)
    changed["semantic_mappings"][0]["span"]["end"] = 100
    add("MB11-span-past-end", changed, blobs, 1, "MBINV001")
    changed = copy.deepcopy(core)
    changed["legal_sources"][0]["dates"] = {"effective_from": "2026-12-31", "effective_to": "2026-01-01"}
    add("MB12-date-conflict", changed, blobs, 1, "MBINV001")
    changed = copy.deepcopy(core)
    changed["legal_sources"].append(copy.deepcopy(changed["legal_sources"][0]))
    add("MB13-duplicate-source", changed, blobs, 1, "MBINV001")
    changed = copy.deepcopy(core)
    changed["semantic_mappings"].append(copy.deepcopy(changed["semantic_mappings"][0]))
    add("MB14-duplicate-mapping", changed, blobs, 1, "MBINV001")
    changed = copy.deepcopy(core)
    changed["artifacts"][0]["role"] = "wrong"
    add("MB15-unsupported-role", changed, blobs, 1, "MBCAP001")
    changed = copy.deepcopy(core)
    changed["hash_algorithm"] = "sha512"
    add("MB16-unsupported-algorithm", changed, blobs, 1, "MBCAP001")
    changed = copy.deepcopy(core)
    changed["scope"]["coverage_mode"] = "complete_instrument"
    add("MB17-unsupported-coverage", changed, blobs, 1, "MBCAP001")
    changed = copy.deepcopy(core)
    changed["derivations"] = [{"child_digest": core["artifacts"][0]["sha256"],
        "parent_digest": core["artifacts"][0]["sha256"], "tool_name": "fixture",
        "tool_version": "1", "configuration": "none"}]
    add("MB18-derivation-cycle", changed, blobs, 1, "MBINV001")
    path = add("MB19-missing-blob", core, blobs, 1, "MBPKG001")
    sorted((path / "artifacts/sha256").iterdir())[0].unlink()
    path = add("MB20-unreferenced-blob", core, blobs, 1, "MBPKG001")
    (path / "artifacts/sha256" / ("f" * 64)).write_bytes(b"unreferenced")
    path = add("MB21-invalid-filename", core, blobs, 1, "MBPKG001")
    (path / "artifacts/sha256" / "not-a-digest").write_bytes(b"x")
    path = add("MB22-symlink", core, blobs, 1, "MBPKG001")
    target = sorted((path / "artifacts/sha256").iterdir())[0]
    target.unlink()
    target.symlink_to("/etc/passwd")
    path = add("MB23-extra-file", core, blobs, 1, "MBPKG001")
    (path / "unexpected").write_bytes(b"x")
    path = add("MB24-noncanonical", core, blobs, 1, "MBDEC002")
    (path / "model-bundle.json").write_bytes(json.dumps(core).encode())
    path = add("MB25-duplicate-key", core, blobs, 1, "MBDEC001")
    raw = canon(core)
    (path / "model-bundle.json").write_bytes(raw[:-1] + b',"schema":"yuho.model-bundle/v1"}')
    path = add("MB26-malformed-unicode", core, blobs, 1, "MBDEC001")
    (path / "model-bundle.json").write_bytes(raw.replace(b"synthetic", b"\\uD800", 1))
    path = add("MB27-digest-mismatch", core, blobs, 1, "MBINV001")
    target = sorted((path / "artifacts/sha256").iterdir())[0]
    target.write_bytes(b"different bytes")
    path = add("MB28-malformed-review", core, blobs, 1, "MBDEC001",
               reviews={"review:1.json": review(core)})
    (path / "reviews/review:1.json").write_bytes(b'{"wrong":true}')
    path = add("MB29-review-unknown-id", core, blobs, 1, "MBINV001",
               reviews={"review:1.json": review(core, coverage="semantic_ids")})
    value = json.loads((path / "reviews/review:1.json").read_bytes())
    value["coverage"]["semantic_ids"] = ["unknown:id"]
    (path / "reviews/review:1.json").write_bytes(canon(value))
    path = add("MB30-review-wildcard", core, blobs, 1, "MBINV001",
               reviews={"review:1.json": review(core, coverage="semantic_ids")})
    value = json.loads((path / "reviews/review:1.json").read_bytes())
    value["coverage"]["semantic_ids"] = ["*"]
    (path / "reviews/review:1.json").write_bytes(canon(value))
    path = add("MB31-oversize-manifest", core, blobs, 1, "MBRES001")
    (path / "model-bundle.json").write_bytes(b"x" * 1048577)
    path = add("MB32-review-symlink", core, blobs, 1, "MBPKG001",
               reviews={"review:1.json": review(core)})
    (path / "reviews/review:1.json").unlink()
    (path / "reviews/review:1.json").symlink_to("/etc/passwd")
    path = add("MB33-path-traversal", core, blobs, 1, "MBPKG001")
    (path / "artifacts/sha256" / "..").resolve()  # package names are never trusted as paths
    (path / "artifacts/sha256" / "..x").write_bytes(b"x")
    path = add("MB34-absolute-path", core, blobs, 1, "MBDEC001")
    value = json.loads((path / "model-bundle.json").read_bytes())
    value["absolute_path"] = "/etc/passwd"
    (path / "model-bundle.json").write_bytes(canon(value))
    path = add("MB35-invalid-utf8-text", core, blobs, 1, "MBINV001")
    text_digest = next(a["sha256"] for a in core["artifacts"] if a["role"] == "source_text")
    (path / "artifacts/sha256" / text_digest).write_bytes(b"\xff")

    def extra_source(core: dict, blobs: dict[str, bytes], content: bytes,
                     media: str, role: str, sid: str, expression: str) -> str:
        digest = sha(content)
        blobs[digest] = content
        core["artifacts"].append({"sha256": digest, "byte_length": len(content),
                                  "media_type": media, "role": role})
        core["artifacts"].sort(key=lambda x: x["sha256"])
        core["legal_sources"].append({
            "source_id": sid, "work_id": "work:synthetic", "expression_id": expression,
            "manifestation_id": f"manifestation:{sid}", "artifact_digest": digest,
            "source_type": "synthetic", "language": "en", "jurisdiction": "SYN",
            "identifiers": [], "dates": {}, "locator": "fixture:shared-locator",
        })
        core["legal_sources"].sort(key=lambda x: x["source_id"])
        core["scope"]["source_ids"] = sorted(x["source_id"] for x in core["legal_sources"])
        core["scope"]["expression_ids"] = sorted({x["expression_id"] for x in core["legal_sources"]})
        return digest

    changed, payload = copy.deepcopy(core), dict(blobs)
    pdf = extra_source(changed, payload, b"%PDF-1.7\nsynthetic\n", "application/pdf",
                       "evidence", "src:pdf", "expression:synthetic:1")
    add("MB36-two-manifestations", changed, payload, 0)
    changed["derivations"] = [{"child_digest": text_digest, "parent_digest": pdf,
                               "tool_name": "fixture-extractor", "tool_version": "1",
                               "configuration": "exact fixture bytes"}]
    add("MB37-extracted-text", changed, payload, 0)
    changed, payload = copy.deepcopy(core), dict(blobs)
    extra_source(changed, payload, b"revised synthetic text\n", "text/plain; charset=utf-8",
                 "source_text", "src:revision", "expression:synthetic:2")
    add("MB38-two-expressions", changed, payload, 0)
    changed, payload = copy.deepcopy(core), dict(blobs)
    unicode_digest = extra_source(changed, payload, "A😀\r\nB".encode(),
        "text/plain; charset=utf-8", "source_text", "src:unicode", "expression:synthetic:1")
    add("MB39-non-bmp-crlf", changed, payload, 0)
    changed["semantic_mappings"][0]["artifact_digest"] = unicode_digest
    changed["semantic_mappings"][0]["source_id"] = "src:unicode"
    changed["semantic_mappings"][0]["span"] = {
        "start": 1, "end": 5, "start_line": 1, "start_col": 2,
        "end_line": 1, "end_col": 6}
    changed["semantic_mappings"].sort(key=lambda x: (x["semantic_id"],
        x["artifact_digest"], x["span"]["start"], x["span"]["end"]))
    add("MB40-unicode-byte-span", changed, payload, 0)
    invalid = copy.deepcopy(changed)
    invalid["semantic_mappings"][0]["span"]["start"] = 2
    add("MB41-continuation-span", invalid, payload, 1, "MBINV001")
    invalid = copy.deepcopy(core)
    invalid["semantic_mappings"][0]["span"]["start_col"] = 2
    add("MB42-line-column-mismatch", invalid, blobs, 1, "MBINV001")
    invalid = copy.deepcopy(core)
    invalid["semantic_mappings"][0]["source_id"] = "src:missing"
    add("MB43-missing-source", invalid, blobs, 1, "MBINV001")
    invalid = copy.deepcopy(core)
    invalid["scope"]["expression_ids"] = ["expression:missing"]
    add("MB44-missing-expression", invalid, blobs, 1, "MBINV001")
    invalid = copy.deepcopy(core)
    invalid["scope"]["exclusions"] = [{"exclusion_id": invalid["scope"]["semantic_ids"][0],
                                        "reason": "cannot exclude a positive ID"}]
    add("MB45-scope-exclusion-overlap", invalid, blobs, 1, "MBINV001")
    invalid, payload = copy.deepcopy(core), dict(blobs)
    pdf = extra_source(invalid, payload, b"%PDF-1.7\n", "application/pdf", "evidence",
                       "src:pdf", "expression:synthetic:1")
    invalid["semantic_mappings"][0]["artifact_digest"] = pdf
    invalid["semantic_mappings"][0]["source_id"] = "src:pdf"
    add("MB46-pdf-span", invalid, payload, 1, "MBINV001")
    invalid, payload = copy.deepcopy(core), dict(blobs)
    extra_source(invalid, payload, b"\xff", "text/plain; charset=utf-8", "source_text",
                 "src:invalid", "expression:synthetic:1")
    add("MB47-invalid-utf8-artifact", invalid, payload, 1, "MBINV001")
    invalid = copy.deepcopy(core)
    invalid["artifacts"][0]["media_type"] = "application/x-unknown"
    add("MB48-unsupported-media", invalid, blobs, 1, "MBCAP001")
    invalid = copy.deepcopy(core)
    invalid["artifacts"].append({"sha256": "f" * 64, "byte_length": 0,
                                 "media_type": "application/pdf", "role": "evidence"})
    invalid["artifacts"].sort(key=lambda x: x["sha256"])
    add("MB49-unreferenced-artifact", invalid, blobs, 1, "MBINV001")
    invalid = copy.deepcopy(core)
    invalid["derivations"] = [{"child_digest": text_digest, "parent_digest": "f" * 64,
                               "tool_name": "fixture", "tool_version": "1", "configuration": "none"}]
    add("MB50-missing-derivation-parent", invalid, blobs, 1, "MBINV001")
    invalid = copy.deepcopy(core)
    invalid["legal_sources"][0]["manifestation_id"] = "manifestation:duplicate"
    duplicate = copy.deepcopy(invalid["legal_sources"][0])
    duplicate["source_id"] = "src:other"
    invalid["legal_sources"].append(duplicate)
    invalid["scope"]["source_ids"] = ["src:main", "src:other"]
    add("MB51-duplicate-manifestation", invalid, blobs, 1, "MBINV001")
    invalid = copy.deepcopy(core)
    invalid["legal_sources"][0]["dates"] = {"publication": "2026-02-30"}
    add("MB52-impossible-date", invalid, blobs, 1, "MBINV001")
    invalid = copy.deepcopy(core)
    invalid["scope"]["temporal_context"] = {"kind": "asserted_point_in_time",
                                               "date": "2026-13-01"}
    add("MB53-invalid-point-in-time", invalid, blobs, 1, "MBINV001")
    add("MB54-review-two-purposes", core, blobs, 0,
        reviews={"review:1.json": {**review(core), "purposes": ["semantic_fidelity", "source_fidelity"]}},
        policy="source_fidelity")
    add("MB55-review-source-coverage", core, blobs, 0,
        reviews={"review:1.json": review(core, coverage="source_ids", purpose="source_fidelity")},
        policy="source_fidelity")
    add("MB56-source-coverage-not-semantic", core, blobs, 3,
        reviews={"review:1.json": review(core, coverage="source_ids")},
        policy="semantic_fidelity")
    path = add("MB57-review-unknown-field", core, blobs, 1, "MBDEC001",
               reviews={"review:1.json": review(core)})
    value = json.loads((path / "reviews/review:1.json").read_bytes())
    value["authenticated"] = True
    (path / "reviews/review:1.json").write_bytes(canon(value))
    path = add("MB58-duplicate-review-key", core, blobs, 1, "MBDEC001",
               reviews={"review:1.json": review(core)})
    raw = (path / "reviews/review:1.json").read_bytes()
    (path / "reviews/review:1.json").write_bytes(raw[:-1] + b',"review_id":"review:1"}')
    path = add("MB59-review-limit", core, blobs, 1, "MBRES001")
    (path / "reviews").mkdir()
    for i in range(65):
        (path / "reviews" / f"review:{i:02}.json").write_bytes(b"{}")
    invalid = copy.deepcopy(core)
    invalid["artifacts"] += [{"sha256": f"{i:064x}", "byte_length": 0,
                               "media_type": "application/pdf", "role": "evidence"}
                              for i in range(257)]
    add("MB60-artifact-count-limit", invalid, blobs, 1, "MBRES001")
    invalid = copy.deepcopy(core)
    invalid["scope"]["exclusions"] = [
        {"exclusion_id": f"excluded:{i:04}", "reason": "synthetic omitted unit"}
        for i in range(1025)]
    add("MB61-exclusion-count-limit", invalid, blobs, 1, "MBRES001")
    changed, payload = copy.deepcopy(core), dict(blobs)
    extra_source(changed, payload, b"first rendering\n", "text/plain; charset=utf-8",
                 "source_text", "src:first", "expression:synthetic:1")
    extra_source(changed, payload, b"second rendering\n", "text/plain; charset=utf-8",
                 "source_text", "src:second", "expression:synthetic:1")
    add("MB62-shared-locator-distinct-bytes", changed, payload, 0)
    changed, payload = copy.deepcopy(core), dict(blobs)
    second = extra_source(changed, payload, b"second supporting passage\n",
                          "text/plain; charset=utf-8", "source_text", "src:second",
                          "expression:synthetic:1")
    extra_mapping = copy.deepcopy(changed["semantic_mappings"][0])
    extra_mapping["artifact_digest"] = second
    extra_mapping["source_id"] = "src:second"
    changed["semantic_mappings"].append(extra_mapping)
    changed["semantic_mappings"].sort(key=lambda x: (x["semantic_id"],
        x["artifact_digest"], x["span"]["start"], x["span"]["end"]))
    add("MB63-multiple-mappings", changed, payload, 0)
    stale = review(core, stale=True, coverage="semantic_ids")
    stale["coverage"]["semantic_ids"] = ["old:removed"]
    add("MB64-stale-old-coverage", core, blobs, 3,
        reviews={"review:1.json": stale}, policy="semantic_fidelity")
    changed = copy.deepcopy(core)
    changed["legal_sources"][0]["verified_official"] = True
    add("MB65-untrusted-authority-claim", changed, blobs, 1, "MBDEC001")

    def altered_model(request: dict) -> tuple[dict, dict[str, bytes]]:
        altered_core, altered_payload = copy.deepcopy(core), dict(blobs)
        old = altered_core["executable_model"]["artifact_digest"]
        data = canon(request)
        new = sha(data)
        altered_payload.pop(old)
        altered_payload[new] = data
        altered_core["executable_model"]["artifact_digest"] = new
        for artifact in altered_core["artifacts"]:
            if artifact["sha256"] == old:
                artifact["sha256"] = new
                artifact["byte_length"] = len(data)
        altered_core["artifacts"].sort(key=lambda x: x["sha256"])
        return altered_core, altered_payload

    duplicate_request = json.loads(BASE_REQUEST.read_bytes())
    duplicate_request["registry"].append(copy.deepcopy(duplicate_request["registry"][0]))
    changed, payload = altered_model(duplicate_request)
    add("MB66-duplicate-model-semantic-id", changed, payload, 1, "MBINV001")
    extra_fact_request = json.loads(BASE_REQUEST.read_bytes())
    extra_fact_request["facts"]["not:a:leaf"] = extra_fact_request["facts"]["f:root"]
    changed, payload = altered_model(extra_fact_request)
    add("MB67-invalid-model-facts", changed, payload, 1, "MBINV001")
    changed_source_request = json.loads(BASE_REQUEST.read_bytes())
    changed_source_request["sources"][0]["text"] += "extra\n"
    changed_source_request["sources"][0]["sha256"] = sha(
        changed_source_request["sources"][0]["text"].encode())
    changed, payload = altered_model(changed_source_request)
    add("MB68-model-source-mismatch", changed, payload, 1, "MBINV001")
    changed = copy.deepcopy(core)
    changed["legal_sources"][0]["publisher_label"] = "unverified official-looking label"
    add("MB69-unverified-publisher-label", changed, blobs, 0)
    changed = copy.deepcopy(core)
    changed["semantic_mappings"][0]["span"] = {
        "start": 2, "end": 3, "start_line": 2, "start_col": 1,
        "end_line": 2, "end_col": 2}
    add("MB70-wrong-but-valid-passage", changed, blobs, 0)
    changed = copy.deepcopy(core)
    changed["derivations"] = [{"child_digest": text_digest,
                               "parent_digest": changed["executable_model"]["artifact_digest"],
                               "tool_name": "fixture", "tool_version": "1",
                               "configuration": "invalid parent role"}]
    add("MB71-model-as-extraction-parent", changed, blobs, 1, "MBINV001")
    changed = copy.deepcopy(core)
    changed["artifacts"].insert(0, copy.deepcopy(changed["artifacts"][0]))
    add("MB72-duplicate-artifact-entry", changed, blobs, 1, "MBINV001")
    return cases


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "bundles"
    if destination.exists():
        shutil.rmtree(destination)
    cases = make(destination)
    (destination.parent / "CASES.json").write_bytes(canon(cases) + b"\n")
    entries = {str(p.relative_to(destination.parent)): sha(p.read_bytes())
               for p in destination.rglob("*") if p.is_file() and not p.is_symlink()}
    manifest = {"schema": "yuho.model-bundle-fixture-manifest/v1",
                "base_request_sha256": sha(BASE_REQUEST.read_bytes()),
                "files": dict(sorted(entries.items()))}
    (destination.parent / "MANIFEST.json").write_bytes(canon(manifest) + b"\n")
