#!/usr/bin/env python3
"""Refine/validate evidence-scoped rights; never a licence or publication grant."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "release/rights-content-evidence.json"
POLICY_SHA256 = "0f2823b4b400a7dfbd964e9bc6af87ebd36d653388ecd0ac15a0de2d353db69d"
ORIGINAL = "Original and covered by approved Apache-2.0"
MIXED = "Mixed content; see per-content evidence and permission scopes"
UNRESOLVED = "Permission or provenance unresolved"
CATEGORIES = {"original", "synthetic", "conditional_legislation", "third_party_permission", "unresolved"}
FIELDS = ("category", "content_locator", "source_reference", "evidence", "status")
NAMESPACES = {"owner_authorisation", "challenge_evidence", "retained_evidence", "synthetic_authorship", "project_authorship", "unknown"}
UNKNOWN_REFERENCES = {None, "unknown", "unknown third-party source"}
PROJECT_FILES = {
    "scripts/reduced_sdk.py", "scripts/rights_inventory.py", "test/reduced_sdk.py",
    "test/rights_inventory.py", "docs/reduced-sdk-boundary.md",
    "release/reduced-sdk-inventory.json", "release/rights-content-evidence.json",
    "release/reduced-sdk/yuho.cabal", "release/reduced-sdk/cabal.project.sdk",
    "release/reduced-sdk/NOTICE", "release/reduced-sdk/docs/sdk-only-inspection.md",
}


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON key: " + name)
        result[name] = value
    return result


def read_json(path: Path) -> dict:
    return json.loads(path.read_bytes(), object_pairs_hook=unique_object)


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def load_policy(path: Path = POLICY) -> dict:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != POLICY_SHA256:
        raise ValueError("rights evidence policy changed; explicit review/pin update required")
    policy = json.loads(data, object_pairs_hook=unique_object)
    authoritative(policy)  # Check the authored input itself before using it.
    return policy


def key(row: dict) -> tuple[str, str]:
    return row["origin"], row["repository_path"]


def scope(category: str, locator: str, source: str | None, evidence: str, status: str) -> dict:
    return dict(zip(FIELDS, (category, locator, source, evidence, status)))


def body(value: dict) -> dict:
    return {field: value[field] for field in FIELDS}


def identity(owner: tuple[str, str], role: str) -> str:
    return "yuho.rights-scope/" + hashlib.sha256(encoded([*owner, role])).hexdigest()


def identified(owner, role, value, namespace) -> dict:
    return {**body(value), "scope_id": identity(owner, role), "reference_namespace": namespace}


def original_scope() -> dict:
    return scope("original", "authored code/representation/analysis only; external portions separately scoped",
                 "release/owner-apache-authorisation.json", "retained owner grant for authorised original portions",
                 "not proof of universal ownership or full-file clearance")


def classification(scopes: list[dict]) -> str:
    categories = {s["category"] for s in scopes}
    if len(categories) > 1:
        return MIXED
    return {"original": ORIGINAL, "synthetic": "Original synthetic example; Apache-2.0 scope",
            "conditional_legislation": "Potentially covered by conditional legislative reproduction permission",
            "third_party_permission": "Third-party with verified permission", "unresolved": UNRESOLVED}[next(iter(categories))]


def clearance_summary(scopes: list[dict]) -> str:
    if any(s["category"] in {"conditional_legislation", "unresolved"} for s in scopes):
        return "Conditional or unresolved portions remain; no full-file clearance"
    return "Identified original/permission scopes only; public boundary remains unapproved"


def check_scope(value: dict) -> None:
    if value.get("category") not in CATEGORIES:
        raise ValueError("unsupported rights category")
    for field in ("content_locator", "evidence", "status"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError("missing supported scope " + field)
    namespace = value.get("reference_namespace")
    reference = value.get("source_reference")
    if namespace not in NAMESPACES:
        raise ValueError("unsupported source reference namespace")
    if namespace == "unknown":
        if value["category"] != "unresolved" or reference not in UNKNOWN_REFERENCES:
            raise ValueError("unknown provenance must be explicitly unresolved with an unknown/missing source")
    elif not isinstance(reference, str) or not reference.strip():
        raise ValueError("blank source reference")
    if not isinstance(value.get("scope_id"), str) or not value["scope_id"].startswith("yuho.rights-scope/"):
        raise ValueError("missing stable scope identity")


def authoritative(policy: dict) -> dict:
    """Existing policy lists, not the submitted matrix, define required identities."""
    result = {}

    def put(record, scopes):
        owner = record["origin"], record["path"]
        if not all(isinstance(v, str) and v.strip() for v in owner):
            raise ValueError("invalid reviewed owner identity")
        path = Path(owner[1])
        if path.is_absolute() or ".." in path.parts or "\\" in owner[1] or path.as_posix() != owner[1]:
            raise ValueError("unsupported reviewed file path")
        if owner in result:
            raise ValueError("ambiguous authoritative row: " + record["path"])
        result[owner] = {"sha256": record["sha256"], "scopes": scopes}

    for record in policy["challenged_original_files"]:
        owner = record["origin"], record["path"]
        put(record, [identified(owner, "original", original_scope(), "owner_authorisation"),
            identified(owner, "challenge", scope(record["external_category"], record["content_locator"],
                record["source_reference"], record["evidence_reference"], record["qualification"]), "challenge_evidence")])
    for record in policy["retained_external_or_unresolved"]:
        owner = record["origin"], record["path"]
        # Explicit reviewed roles are stored in policy, never array-index identities.
        scopes = [identified(owner, s["review_key"], s, s["reference_namespace"]) for s in record["reviewed_scopes"]]
        put(record, scopes)
    for record in policy["original_assets"]:
        owner = record["origin"], record["path"]
        put(record, [identified(owner, "asset", scope("original", "identified owner-drawn mascot rendition only",
            record["authorisation_reference"], "retained owner creator statement and explicit four-file Apache-2.0 approval",
            "original authorisation resolved; publication remains separately gated"), "owner_authorisation")])
    for record in policy["synthetic_portions"]:
        owner = record["origin"], record["path"]
        value = identified(owner, "synthetic", scope("synthetic", record["content_locator"], "project-authored synthetic source",
            record["evidence"], "not a statutory quotation or proof classification"), "synthetic_authorship")
        if owner not in result:
            put(record, [identified(owner, "original", original_scope(), "owner_authorisation"), value])
        else:
            if result[owner]["sha256"] != record["sha256"]:
                raise ValueError("conflicting synthetic source attachment")
            existing = [s for s in result[owner]["scopes"] if s["category"] == "synthetic"]
            if not existing:
                result[owner]["scopes"].append(value)
            elif len(existing) != 1 or body(existing[0]) != body(value):
                raise ValueError("conflicting authored synthetic scope evidence")
    for record in policy.get("additional_reviewed_scopes", []):
        owner = record["origin"], record["path"]
        value = identified(owner, record["review_key"], record["scope"], record["reference_namespace"])
        if value["category"] != "unresolved" or value["reference_namespace"] != "unknown":
            raise ValueError("additional unknown-source review cannot assert permission")
        if owner not in result:
            # The record stores the already-reviewed base scopes too, for exact completeness.
            put(record, [identified(owner, s["review_key"], s, s["reference_namespace"]) for s in record["base_scopes"]])
        if result[owner]["sha256"] != record["sha256"]:
            raise ValueError("conflicting reviewed source attachment: " + record["path"])
        result[owner]["scopes"].append(value)
    for owner, record in result.items():
        ids = [s["scope_id"] for s in record["scopes"]]
        if len(set(ids)) != len(ids) or len({encoded(body(s)) for s in record["scopes"]}) != len(ids):
            raise ValueError("duplicate authoritative scope identity: " + owner[1])
        for value in record["scopes"]:
            check_scope(value)
        record["scopes"].sort(key=lambda s: s["scope_id"])
    return result


def default_scopes(row: dict) -> list[dict]:
    owner = key(row)
    if owner[0] == "current checkout" and owner[1] in PROJECT_FILES:
        value = scope("original", "new release-engineering material", "this bounded implementation",
                      "explicit authored release-engineering file list", "not a legal clearance")
        return [identified(owner, "project-file", value, "project_authorship")]
    if (row.get("previous_classification", row["classification"]).startswith("Original")
            and row.get("evidence_locations") and row.get("source_and_acquisition_provenance")):
        return [identified(owner, "original", original_scope(), "owner_authorisation")]
    value = scope("unresolved", "whole source; no established rights provenance", "unknown",
                  "absence of rights evidence in supplied record", "unresolved")
    return [identified(owner, "unknown", value, "unknown")]


def expected_scopes(row, registry):
    return registry[key(row)]["scopes"] if key(row) in registry else default_scopes(row)


def match_scopes(row: dict, expected: list[dict], legacy: bool = False) -> None:
    scopes = row.get("rights_scopes", [])
    if not scopes:
        raise ValueError("missing supported content scope: " + row["repository_path"])
    ids = [s.get("scope_id") for s in scopes]
    if not legacy and len(set(ids)) != len(ids):
        raise ValueError("duplicate scope identity: " + row["repository_path"])
    remaining = list(expected)
    for value in scopes:
        matches = [s for s in remaining if value == s or
            (legacy and set(value) == set(FIELDS) and body(value) == body(s))]
        if len(matches) != 1:
            raise ValueError("scope/source correspondence conflict or unrecorded scope; preserve input and record/review explicitly: " + row["repository_path"])
        remaining.remove(matches[0])
    if remaining:
        raise ValueError("required reviewed scope omitted: " + row["repository_path"])


def check_coverage(rows, registry, partial):
    owners = [key(r) for r in rows]
    if len(set(owners)) != len(owners):
        raise ValueError("duplicate rights row")
    if not partial:
        missing = set(registry) - set(owners)
        if missing:
            raise ValueError("required reviewed/challenged row missing: " + sorted(missing)[0][1])


def check_attachments(rows, registry, policy, root):
    if root is None:
        return
    for row in rows:
        owner = key(row)
        if owner in registry and owner[0] == "current checkout":
            path = root / owner[1]
            if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != registry[owner]["sha256"]:
                raise ValueError("stale/missing reviewed source; evidence retained, review required: " + owner[1])
    for name, digest in policy.get("reference_attachments", {}).items():
        attachment = root / name
        if not attachment.is_file() or attachment.is_symlink() or hashlib.sha256(attachment.read_bytes()).hexdigest() != digest:
            raise ValueError("stale/missing source-reference evidence: " + name)
    source = root / policy["source_export"]
    if not source.is_file() or source.is_symlink() or hashlib.sha256(source.read_bytes()).hexdigest() != policy["source_export_sha256"]:
        raise ValueError("stale/missing legislative evidence source")


def validate(document: dict, policy: dict, *, partial: bool = False, root: Path | None = None) -> None:
    if document.get("public_release_cleared", False) is not False:
        raise ValueError("inventory cannot grant public release clearance")
    if not partial and document.get("inventory_mode") == "partial":
        raise ValueError("partial inventory requires explicit partial validation")
    registry = authoritative(policy)
    check_coverage(document["rows"], registry, partial)
    for row in document["rows"]:
        if row.get("fully_cleared") is not False or row.get("cleared", False) is not False:
            raise ValueError("inventory is not a clearance grant: " + row["repository_path"])
        scopes = row.get("rights_scopes", [])
        for value in scopes:
            check_scope(value)
        match_scopes(row, expected_scopes(row, registry))
        if key(row) in registry and row["sha256"] != registry[key(row)]["sha256"]:
            raise ValueError("reviewed source digest changed: " + row["repository_path"])
        if row["classification"] != classification(scopes) or row.get("clearance_status") != clearance_summary(scopes):
            raise ValueError("classification/clearance summary contradicts reviewed scopes: " + row["repository_path"])
    check_attachments(document["rows"], registry, policy, root)


def refine(document: dict, policy: dict, root: Path | None = None, *, partial: bool = False) -> dict:
    if document.get("public_release_cleared", False) is not False:
        raise ValueError("inventory cannot grant public release clearance")
    if not partial and document.get("inventory_mode") == "partial":
        raise ValueError("partial inventory requires explicit partial generation")
    result = copy.deepcopy(document)
    registry = authoritative(policy)
    check_coverage(result["rows"], registry, partial)
    for row in result["rows"]:
        if row.get("cleared", False) is not False or row.get("fully_cleared", False) is not False:
            raise ValueError("unapproved clearance promotion: " + row["repository_path"])
        expected = expected_scopes(row, registry)
        if key(row) in registry and row["sha256"] != registry[key(row)]["sha256"]:
            raise ValueError("stale reviewed inventory source attachment: " + row["repository_path"])
        if "rights_scopes" in row:
            # Never replace a recorded extra/conflicting scope with generated defaults.
            match_scopes(row, expected, legacy=True)
        row["previous_classification"] = row.get("previous_classification", row["classification"])
        row["rights_scopes"] = copy.deepcopy(expected)
        row["classification"] = classification(expected)
        row["fully_cleared"] = False
        row["clearance_status"] = clearance_summary(expected)
    check_attachments(result["rows"], registry, policy, root)
    if root is not None and not partial:
        existing = {key(r): r for r in result["rows"]}
        paths = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")) - {""}
        paths |= set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=root).decode().split("\0")) - {""}
        for path in sorted(paths):
            file = root / path
            digest = None if file.is_symlink() else hashlib.sha256(file.read_bytes()).hexdigest()
            row = existing.get(("current checkout", path))
            if row:
                row["sha256"] = digest
            else:
                row = {"origin": "current checkout", "repository_path": path, "sha256": digest,
                       "classification": UNRESOLVED, "fully_cleared": False,
                       "release_surfaces": {"current_proposed_tree": True, "reduced_sdk": False,
                                            "public_bytes": "not inferred from local working tree"}}
                row["rights_scopes"] = default_scopes(row)
                row["classification"] = classification(row["rights_scopes"])
                row["clearance_status"] = clearance_summary(row["rights_scopes"])
                row["previous_classification"] = row["classification"]
                result["rows"].append(row)
    result["rows"].sort(key=key)
    result["counts"] = dict(sorted(Counter(r["classification"] for r in result["rows"]).items()))
    result["inventory_mode"] = "partial" if partial else "full"
    result["public_release_cleared"] = False
    result["content_scope_policy"] = "Authorised original portions only; source-bound reviewed scopes and explicit unknown provenance; no licence or public clearance grant."
    result["archive_membership_basis"] = "Inherited ordinary-SDK/full-bundle booleans refer to Remediation 02 snapshots; reduced candidate uses its unchanged separate exact inventory."
    validate(result, policy, partial=partial, root=root)
    return result


def record_unresolved(document: dict, policy: dict) -> dict:
    """Propose additions to this same policy; never silently activate them."""
    if document.get("public_release_cleared", False) is not False:
        raise ValueError("inventory cannot grant public release clearance")
    proposed = copy.deepcopy(policy)
    registry = authoritative(policy)
    check_coverage(document["rows"], registry, True)
    added = 0
    for row in document["rows"]:
        if row.get("cleared", False) is not False or row.get("fully_cleared", False) is not False:
            raise ValueError("unapproved clearance promotion")
        expected = expected_scopes(row, registry)
        remaining = list(expected)
        extras = []
        for value in row.get("rights_scopes", []):
            match = next((s for s in remaining if value == s or
                          (set(value) == set(FIELDS) and body(value) == body(s))), None)
            if match is not None:
                remaining.remove(match)
            else:
                extras.append(value)
        if remaining:
            raise ValueError("cannot record additions while reviewed scopes are absent/conflicting: " + row["repository_path"])
        for value in extras:
            if (value["category"] != "unresolved" or value["source_reference"] not in UNKNOWN_REFERENCES
                    or value.get("reference_namespace", "unknown") != "unknown"):
                raise ValueError("record-unresolved accepts explicit unknown provenance only; separately review other sources")
            review_key = "review-" + hashlib.sha256(encoded(body(value))).hexdigest()
            bound = identified(key(row), review_key, value, "unknown")
            check_scope(bound)
            if value.get("scope_id", bound["scope_id"]) != bound["scope_id"]:
                raise ValueError("conflicting additional scope identity")
            if key(row) in registry and row["sha256"] != registry[key(row)]["sha256"]:
                raise ValueError("stale additional review source attachment")
            proposed["additional_reviewed_scopes"].append({"origin": row["origin"], "path": row["repository_path"],
                "sha256": row["sha256"], "review_key": review_key, "scope": body(value), "reference_namespace": "unknown",
                "base_scopes": [{**s, "review_key": next((role for role in ("original", "unknown", "project-file")
                    if identity(key(row), role) == s["scope_id"]), "retained-base-" + s["scope_id"].split("/")[-1])} for s in expected]})
            added += 1
    if not added:
        raise ValueError("no new unresolved review input to record")
    authoritative(proposed)
    return proposed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--partial", action="store_true", help="explicit subset fixture; never full-inventory certification")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--record-unresolved", action="store_true", help="write proposed existing-policy additions outside checkout; review/pin activation required")
    args = parser.parse_args()
    policy = load_policy()
    document = read_json(args.input)
    if args.validate_only:
        validate(document, policy, partial=args.partial, root=args.root)
    else:
        if args.output is None:
            parser.error("--output is required for generation or review proposal")
        if args.record_unresolved:
            if args.output.resolve() == args.input.resolve():
                raise ValueError("review proposal must not overwrite its input evidence")
            if args.output.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError("review proposal must be outside checkout; deliberate review/pin activation required")
            result = record_unresolved(document, policy)
            check_attachments(document["rows"], authoritative(result), result, args.root)
        else:
            result = refine(document, policy, args.root, partial=args.partial)
        args.output.write_bytes(encoded(result))
    print("Content-scoped rights evidence checked; no licence grant or redistribution clearance" +
          ("; proposed policy requires explicit review/pin activation" if args.record_unresolved else ""))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(str(error))
