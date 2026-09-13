"""Deterministic fictional ModelBundle-v1 recipe for frontend conformance tests."""

from __future__ import annotations

import json
from pathlib import Path

from . import core


def _inventory(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        if isinstance(value.get("id"), str):
            found.add(value["id"])
        for child in value.values():
            found.update(_inventory(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_inventory(child))
    return found


def core_and_artifacts(
    model: core.SyntheticModel, request_bytes: bytes
) -> tuple[dict, dict[str, bytes]]:
    core.check_synthetic(model, "<bundle-model>")
    request = json.loads(request_bytes)
    if not isinstance(request, dict):
        raise ValueError("executable artifact must be a JSON object")
    registry = request.get("registry")
    facts = request.get("facts")
    declared_sources = request.get("sources")
    if (
        not isinstance(registry, list)
        or not all(isinstance(item, dict) for item in registry)
        or not isinstance(facts, dict)
        or not isinstance(declared_sources, list)
        or not all(isinstance(item, dict) for item in declared_sources)
    ):
        raise ValueError("executable artifact has invalid structure")
    expected_text = "\n".join(value.text for _, value in model.quotes) + "\n"
    expected_leaves = {
        item.identifier.text
        for rule in (model.offence, model.exception)
        for item in rule.elements
    }
    if (
        core.canonical(request) != request_bytes
        or request.get("fragment") != model.variant.text
        or request.get("request_id") != model.request_id.text
        or request.get("root_rule") != model.offence.rule.text
        or [item.get("id") for item in registry]
        != [model.offence.rule.text, model.exception.rule.text]
        or set(facts) != expected_leaves
    ):
        raise ValueError("executable artifact does not match the authored model")
    source_id = next(
        identifier.text
        for identifier, role, _ in model.sources
        if role.text == "source_text"
    )
    status_id = next(
        identifier.text
        for identifier, role, _ in model.sources
        if role.text == "synthetic_status"
    )
    sources = {item.get("id"): item for item in declared_sources}
    if len(sources) != len(declared_sources) or set(sources) != {source_id, status_id}:
        raise ValueError("source declarations differ from the authored model")
    source, status = sources[source_id], sources[status_id]
    if source["text"] != expected_text or status["text"] != core.SYNTHETIC_STATUS_TEXT:
        raise ValueError("executable source bytes differ from the authored model")
    source_bytes = source["text"].encode("utf-8")
    status_bytes = status["text"].encode("utf-8")
    artifacts = {
        core.sha(data): data for data in (request_bytes, source_bytes, status_bytes)
    }
    descriptions = [
        {
            "sha256": core.sha(data),
            "byte_length": len(data),
            "media_type": "application/json"
            if data is request_bytes
            else "text/plain; charset=utf-8",
            "role": "executable_model" if data is request_bytes else "source_text",
        }
        for data in (request_bytes, source_bytes, status_bytes)
    ]
    records = [
        {
            "source_id": source["id"],
            "work_id": "work:fictional-rule",
            "expression_id": "expression:fictional-rule:v0.1",
            "manifestation_id": "manifestation:fictional-rule:text",
            "artifact_digest": core.sha(source_bytes),
            "source_type": "synthetic",
            "language": "en",
            "jurisdiction": "Fictional",
            "identifiers": [],
            "publisher_label": "Yuho fictional compiler fixture",
            "locator": "research:fictional-rule",
            "dates": {},
        },
        {
            "source_id": status["id"],
            "work_id": "work:fictional-status",
            "expression_id": "expression:fictional-status:v0.1",
            "manifestation_id": "manifestation:fictional-status:text",
            "artifact_digest": core.sha(status_bytes),
            "source_type": "synthetic",
            "language": "en",
            "jurisdiction": "Fictional",
            "identifiers": [],
            "publisher_label": "Yuho fictional compiler fixture",
            "locator": "research:fictional-status",
            "dates": {},
        },
    ]
    mappings: list[dict] = []

    def add(identifier: str, role: str, item_span: dict) -> None:
        mappings.append(
            {
                "semantic_id": identifier,
                "artifact_digest": core.sha(source_bytes),
                "source_id": source["id"],
                "role": role,
                "span": item_span,
            }
        )

    def requirements(node: dict) -> None:
        add(node["id"], "requirement", node["span"])
        for member in node.get("members", []):
            requirements(member)

    for rule in request["registry"]:
        add(rule["id"], "rule", rule["program"]["span"])
        add(rule["program"]["id"], "provision", rule["program"]["span"])
        for node in rule["program"]["requirements"]:
            requirements(node)
        for exception in rule["exceptions"]:
            add(exception["id"], "exception", exception["span"])
    mappings.sort(
        key=lambda item: (
            item["semantic_id"],
            item["artifact_digest"],
            item["span"]["start"],
            item["span"]["end"],
        )
    )
    semantic_ids = sorted({item["semantic_id"] for item in mappings})
    if semantic_ids != sorted(_inventory(request["registry"])):
        raise ValueError("model mapping inventory mismatch")
    manifest = {
        "schema": "yuho.model-bundle/v1",
        "canonical_profile": "yuho.sorted-json/v1",
        "hash_algorithm": "sha256",
        "model_id": model.identifier.text,
        "artifacts": sorted(descriptions, key=lambda item: item["sha256"]),
        "legal_sources": sorted(records, key=lambda item: item["source_id"]),
        "derivations": [],
        "semantic_mappings": mappings,
        "scope": {
            "coverage_mode": "enumerated_only",
            "semantic_ids": semantic_ids,
            "source_ids": sorted(item["source_id"] for item in records),
            "expression_ids": sorted(item["expression_id"] for item in records),
            "exclusions": [
                {
                    "exclusion_id": "ex:court-outcome",
                    "reason": "no judicial disposition",
                },
                {"exclusion_id": "ex:evidence", "reason": "no evidence assessment"},
                {"exclusion_id": "ex:real-law", "reason": "wholly fictional rule"},
            ],
            "limitations": sorted(item.text for item in model.limitations),
            "unsupported_capabilities": [
                "court outcome",
                "evidence assessment",
                "real jurisdiction applicability",
            ],
            "jurisdictions": ["Fictional"],
            "subject_matters": ["synthetic restricted area entry"],
            "temporal_context": {"kind": "unspecified"},
        },
        "executable_model": {
            "artifact_digest": core.sha(request_bytes),
            "format": "yuho.kernel-input/v1",
            "fragment": "SuppliedProofStatus-v1",
        },
    }
    return manifest, artifacts


def build(model: core.SyntheticModel, request_bytes: bytes, destination: Path) -> str:
    core._safe_output(destination)
    manifest, artifacts = core_and_artifacts(model, request_bytes)
    manifest_bytes = core.canonical(manifest)
    digest = core.sha(b"yuho.model-bundle/v1\0" + manifest_bytes)
    import tempfile
    import ctypes
    import os

    with tempfile.TemporaryDirectory(
        prefix=".yuho-bundle-", dir=destination.parent
    ) as temp:
        temporary = Path(temp) / "bundle"
        store = temporary / "artifacts/sha256"
        store.mkdir(parents=True)
        (temporary / "model-bundle.json").write_bytes(manifest_bytes)
        for artifact_digest, data in artifacts.items():
            (store / artifact_digest).write_bytes(data)
        libc = ctypes.CDLL(None, use_errno=True)
        renameat2 = libc.renameat2
        renameat2.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameat2.restype = ctypes.c_int
        if renameat2(-100, os.fsencode(temporary), -100, os.fsencode(destination), 1):
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno), str(destination))
    return digest
