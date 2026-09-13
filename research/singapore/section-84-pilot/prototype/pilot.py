"""Offline, bounded section 84 research-prototype artifacts and bundle recipe."""

from __future__ import annotations

import argparse
import copy
import ctypes
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
PILOT = HERE.parent
MODEL_ID = "SingaporePenalCodeSection84Post2022ResearchPrototype-v1"
FRAGMENT = "SuppliedProofStatus-v1"
SOURCE_ID = "src:pc84-excerpt"
STATUS_SOURCE_ID = "src:synthetic-status"
EXTRACTED = "extracted/penal-code-1871-section-84.txt"
HTML_NAME = "Penal Code 1871 - Singapore Statutes Online.html"
DOMAIN = b"yuho.model-bundle/v1\0"
QUOTES = (
    "at the time of doing it, by reason of unsoundness of mind",
    "incapable of knowing the nature of the act",
    "incapable of knowing that what he is doing is wrong",
    "completely deprived of any power to control his actions",
    "is wrong by the ordinary standards of reasonable and honest persons",
    "is wrong as contrary to law",
)
STATUS_TEXT = "synthetic proof classifications only\n"
BURDEN = {"holder": "defence", "kind": "legal"}
STANDARD = "balance_of_probabilities"
LEAF_QUOTE = {
    "f:unsoundness-time": 0,
    "f:nature-causation": 0,
    "f:nature-incapacity": 1,
    "f:wrong-causation": 0,
    "f:ordinary-wrongfulness-incapacity": 4,
    "f:contrary-law-incapacity": 5,
    "f:control-causation": 0,
    "f:control-incapacity": 3,
}
LEAF_PROPOSITION = {
    "f:unsoundness-time": "P84-02",
    "f:nature-causation": "P84-03",
    "f:nature-incapacity": "P84-04",
    "f:wrong-causation": "P84-03",
    "f:ordinary-wrongfulness-incapacity": "P84-06",
    "f:contrary-law-incapacity": "P84-07",
    "f:control-causation": "P84-03",
    "f:control-incapacity": "P84-09",
}
ROUTES = {
    "nature": ("f:nature-causation", "f:nature-incapacity"),
    "wrongfulness": (
        "f:wrong-causation",
        "f:ordinary-wrongfulness-incapacity",
        "f:contrary-law-incapacity",
    ),
    "control": ("f:control-causation", "f:control-incapacity"),
}


def canonical(value: object, *, line: bool = False) -> bytes:
    data = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return data + (b"\n" if line else b"")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def span(data: bytes, start: int, end: int) -> dict[str, int]:
    if not (0 <= start <= end <= len(data)):
        raise ValueError("span outside source")
    for offset in (start, end):
        if offset < len(data) and 0x80 <= data[offset] < 0xC0:
            raise ValueError("span inside UTF-8 sequence")

    def position(offset: int) -> tuple[int, int]:
        before = data[:offset]
        return before.count(b"\n") + 1, len(before.rsplit(b"\n", 1)[-1]) + 1

    first_line, first_col = position(start)
    last_line, last_col = position(end)
    return {
        "start": start,
        "end": end,
        "start_line": first_line,
        "start_col": first_col,
        "end_line": last_line,
        "end_col": last_col,
    }


def regular_bytes(path: Path, limit: int) -> bytes:
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise ValueError(f"expected regular file: {path.name}")
    if path.stat().st_size > limit:
        raise ValueError(f"input limit exceeded: {path.name}")
    data = path.read_bytes()
    if len(data) > limit:
        raise ValueError(f"input grew beyond limit: {path.name}")
    return data


def rename_without_replace(source: Path, destination: Path) -> None:
    # Linux renameat2 closes the race between checking the destination and publishing it.
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
    if renameat2(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def locked_inputs(input_dir: Path, packet_dir: Path) -> tuple[bytes, bytes]:
    for directory in (input_dir, packet_dir, packet_dir / "extracted"):
        if not stat.S_ISDIR(directory.lstat().st_mode):
            raise ValueError(f"expected real directory: {directory.name}")
    lock = json.loads((PILOT / "SOURCE-LOCK.json").read_bytes())
    for row in lock["sources"]:
        data = regular_bytes(input_dir / row["original_filename"], 8 * 1024 * 1024)
        if len(data) != row["byte_length"] or sha(data) != row["sha256"]:
            raise ValueError(f"source lock mismatch: {row['source_id']}")
    for row in lock["generated_artifacts"]:
        data = regular_bytes(packet_dir / row["path"], 8 * 1024 * 1024)
        if len(data) != row["byte_length"] or sha(data) != row["sha256"]:
            raise ValueError(f"generated packet lock mismatch: {row['path']}")
    html = regular_bytes(input_dir / HTML_NAME, 8 * 1024 * 1024)
    extracted = regular_bytes(packet_dir / EXTRACTED, 2 * 1024 * 1024)
    extracted.decode("utf-8", errors="strict")
    return html, extracted


def excerpt(extracted: bytes) -> tuple[bytes, dict[int, dict[str, int]]]:
    locations = {}
    for index, quote in enumerate(QUOTES):
        needle = quote.encode("utf-8")
        if extracted.count(needle) != 1:
            raise ValueError(f"statutory excerpt is absent or ambiguous: {index}")
        start = extracted.index(needle)
        locations[index] = span(extracted, start, start + len(needle))
    return ("\n".join(QUOTES) + "\n").encode("utf-8"), locations


def excerpt_span(text: bytes, index: int) -> dict[str, int]:
    needle = QUOTES[index].encode("utf-8")
    start = text.index(needle)
    return span(text, start, start + len(needle))


def leaf(identifier: str, text: bytes) -> dict:
    return {
        "id": identifier,
        "kind": "leaf",
        "path": ["section84"],
        "span": excerpt_span(text, LEAF_QUOTE[identifier]),
        "declared_metadata": {
            "burden": copy.deepcopy(BURDEN),
            "standard_of_proof": STANDARD,
        },
    }


def group(identifier: str, kind: str, members: list[dict], text: bytes) -> dict:
    return {
        "id": identifier,
        "kind": kind,
        "path": ["section84"],
        "span": span(text, 0, len(text)),
        "members": members,
    }


def request(extracted: bytes) -> dict:
    text, _ = excerpt(extracted)
    branches = [
        group(f"g:{name}", "all", [leaf(item, text) for item in ids], text)
        for name, ids in ROUTES.items()
    ]
    structure = group(
        "g:premise-and-routes",
        "all",
        [
            leaf("f:unsoundness-time", text),
            group("g:alternative-routes", "any", branches, text),
        ],
        text,
    )
    facts = {}
    for identifier in sorted(LEAF_QUOTE):
        facts[identifier] = {
            "proof_status": {"kind": "unresolved", "reason": "not_determined"},
            "burden": copy.deepcopy(BURDEN),
            "standard_of_proof": STANDARD,
            "status_source": {
                "assignment_id": "assignment:" + identifier.removeprefix("f:"),
                "issuer_label": "synthetic research fixture",
                "origin": "synthetic_fixture",
                "source_id": STATUS_SOURCE_ID,
                "span": span(STATUS_TEXT.encode(), 0, len(STATUS_TEXT.encode())),
            },
        }
    return {
        "protocol": "yuho.kernel-protocol/v1",
        "request_id": "X00",
        "operation": "evaluate",
        "input_schema": "yuho.kernel-input/v1",
        "fragment": FRAGMENT,
        "root_rule": "r:section84",
        "policy": {"max_nodes": 1024, "reference_date": "2026-09-13"},
        "sources": [
            {
                "id": SOURCE_ID,
                "path": "research/section84/excerpt.txt",
                "text": text.decode(),
                "sha256": sha(text),
            },
            {
                "id": STATUS_SOURCE_ID,
                "path": "research/section84/synthetic-status.txt",
                "text": STATUS_TEXT,
                "sha256": sha(STATUS_TEXT.encode()),
            },
        ],
        "registry": [
            {
                "id": "r:section84",
                "source_id": SOURCE_ID,
                "program": {
                    "id": "p:section84",
                    "path": ["section84"],
                    "span": span(text, 0, len(text)),
                    "definitions": False,
                    "requirements": [structure],
                    "children": [],
                    "penalties": [],
                },
                "exceptions": [],
            }
        ],
        "facts": facts,
    }


def semantic_inventory(value: object) -> list[str]:
    ids = []
    if isinstance(value, list):
        for item in value:
            ids.extend(semantic_inventory(item))
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in {"id", "exception_id", "penalty_id", "term_id", "presumption_id"}:
                ids.append(item)
            ids.extend(semantic_inventory(item))
    return ids


def model_mapping(extracted: bytes) -> dict:
    _, locations = excerpt(extracted)
    entries = []
    for identifier in sorted(LEAF_QUOTE):
        support = [locations[LEAF_QUOTE[identifier]]]
        if identifier in {
            "f:ordinary-wrongfulness-incapacity",
            "f:contrary-law-incapacity",
        }:
            support.append(locations[2])  # s 84(1)(b) supplies the incapacity operator.
        entries.append(
            {
                "semantic_id": identifier,
                "proposition_id": LEAF_PROPOSITION[identifier],
                "source_id": "src:pc84-extracted",
                "supporting_spans": sorted(support, key=lambda item: item["start"]),
                "external_classification_required": True,
            }
        )
    return {
        "schema": "yuho.sg-section-84-prototype-mapping/v1",
        "leaf_mappings": entries,
        "group_mappings": [
            {
                "semantic_id": identifier,
                "source_id": "src:pc84-extracted",
                "span": span(extracted, 0, len(extracted)),
                "role": role,
            }
            for identifier, role in sorted(
                [
                    ("g:premise-and-routes", "requirement"),
                    ("g:alternative-routes", "requirement"),
                    ("g:nature", "requirement"),
                    ("g:wrongfulness", "requirement"),
                    ("g:control", "requirement"),
                    ("p:section84", "provision"),
                    ("r:section84", "rule"),
                ]
            )
        ],
        "source_text_sha256": sha(extracted),
    }


def model_scope() -> dict:
    return {
        "schema": "yuho.sg-section-84-executable-research-scope/v1",
        "model_id": MODEL_ID,
        "model_version": "v1",
        "jurisdiction": "Singapore",
        "instrument": "Penal Code 1871",
        "provision": "section 84",
        "expression": "reviewed post-2022 structure",
        "expression_effective_from": "2022-03-01",
        "research_cutoff": "2026-09-13",
        "intended_use": "research_prototype",
        "anchor_offence": "absent",
        "case_specific_temporal_selection": "not_performed",
        "evidence_assessment": "not_performed",
        "diagnosis": "not_performed",
        "offence_determination": "excluded",
        "court_outcomes": "excluded",
        "legal_advice": "excluded",
        "digest_bound_implementation_confirmation": "implementation_conformance_review_pending",
        "reviewed_baseline_commit": "c057fb84000265b412d1b6ca3d050e7b2a1d5eca",
        "technical_result_only": True,
    }


def fixtures(base: dict) -> list[tuple[str, dict, str]]:
    all_ids = list(LEAF_QUOTE)
    # Every accepted scenario is a complete externally supplied classification.
    cases = [
        ("X01-nature", {"f:unsoundness-time", *ROUTES["nature"]}, {}, "satisfied"),
        (
            "X02-wrongfulness",
            {"f:unsoundness-time", *ROUTES["wrongfulness"]},
            {},
            "satisfied",
        ),
        (
            "X03-moral-not-proved",
            {"f:unsoundness-time", "f:wrong-causation", "f:contrary-law-incapacity"},
            {},
            "not_satisfied",
        ),
        ("X04-control", {"f:unsoundness-time", *ROUTES["control"]}, {}, "satisfied"),
        (
            "X05-unsoundness-not-proved",
            set(all_ids) - {"f:unsoundness-time"},
            {},
            "not_satisfied",
        ),
        (
            "X06-causation-not-proved",
            {"f:unsoundness-time", "f:nature-incapacity"},
            {},
            "not_satisfied",
        ),
        ("X07-no-route", set(), {}, "not_satisfied"),
        (
            "X08-unresolved-premise",
            set(ROUTES["nature"]),
            {"f:unsoundness-time": "not_determined"},
            "unresolved",
        ),
        (
            "X09-multiple-unresolved",
            {"f:unsoundness-time", "f:nature-causation", "f:control-causation"},
            {
                "f:nature-incapacity": "external_decision_pending",
                "f:control-incapacity": "not_determined",
            },
            "unresolved",
        ),
        (
            "X10-proved-plus-unresolved",
            {"f:unsoundness-time", *ROUTES["nature"]},
            {"f:control-incapacity": "not_determined"},
            "satisfied",
        ),
        (
            "X11-one-wrongfulness-component",
            {
                "f:unsoundness-time",
                "f:wrong-causation",
                "f:ordinary-wrongfulness-incapacity",
            },
            {},
            "not_satisfied",
        ),
    ]
    rows = []
    for name, proved, unresolved, expected in cases:
        item = copy.deepcopy(base)
        item["request_id"] = name[:3]
        for identifier in all_ids:
            status = (
                {"kind": "proved"}
                if identifier in proved
                else {"kind": "unresolved", "reason": unresolved[identifier]}
                if identifier in unresolved
                else {"kind": "not_proved"}
            )
            item["facts"][identifier]["proof_status"] = status
        rows.append((name, item, expected))
    return rows


def rejected_fixtures(base: dict) -> list[tuple[str, dict, str]]:
    rows = []

    def add(name: str, mutate, code: str) -> None:
        item = copy.deepcopy(base)
        item["request_id"] = "Y" + f"{len(rows) + 1:02d}"
        mutate(item)
        rows.append((name, item, code))

    add(
        "Y01-wrong-burden",
        lambda x: x["facts"]["f:nature-incapacity"]["burden"].update(
            holder="prosecution"
        ),
        "KINV007",
    )
    add(
        "Y02-wrong-standard",
        lambda x: x["facts"]["f:nature-incapacity"].update(
            standard_of_proof="beyond_reasonable_doubt"
        ),
        "KINV007",
    )
    add(
        "Y03-malformed-proof",
        lambda x: x["facts"]["f:nature-incapacity"].update(proof_status="proved"),
        "KDEC001",
    )
    add(
        "Y04-bad-reason",
        lambda x: x["facts"]["f:nature-incapacity"]["proof_status"].update(
            reason="not_reviewed"
        ),
        "KDEC001",
    )
    add("Y05-missing-leaf", lambda x: x["facts"].pop("f:nature-incapacity"), "KINV001")
    add(
        "Y06-duplicate-leaf",
        lambda x: x["registry"][0]["program"]["requirements"][0]["members"][1][
            "members"
        ][0]["members"][1].update(id="f:unsoundness-time"),
        "KINV002",
    )
    add(
        "Y07-narrative-evidence",
        lambda x: x["facts"]["f:nature-incapacity"].update(
            narrative_evidence="a fictional story"
        ),
        "KINV004",
    )
    add(
        "Y08-real-case-temporal",
        lambda x: x.update(case_conduct_date="2024-01-01"),
        "KINV004",
    )
    add(
        "Y09-unregistered-model-id", lambda x: x.update(model_id="different"), "KINV004"
    )
    add(
        "Y10-unregistered-model-version",
        lambda x: x.update(model_version="v2"),
        "KINV004",
    )
    add(
        "Y11-deferred-status",
        lambda x: x["facts"]["f:nature-incapacity"].update(
            proof_status={"kind": "presumed"}
        ),
        "KCAP001",
    )
    add(
        "Y12-missing-assignment",
        lambda x: x["facts"]["f:nature-incapacity"].pop("status_source"),
        "KDEC001",
    )
    return rows


def bundle_core(
    model: dict, mapping: dict, scope: dict, html: bytes, extracted: bytes
) -> tuple[dict, dict[str, bytes]]:
    text, _ = excerpt(extracted)
    model_bytes = canonical(model)
    source_bytes = STATUS_TEXT.encode()
    artifacts = {
        sha(data): data for data in (model_bytes, html, extracted, text, source_bytes)
    }
    records = [
        {
            "source_id": "src:pc84-html",
            "work_id": "work:pc1871",
            "expression_id": "expression:pc84:post2022",
            "manifestation_id": "manifestation:pc84:html",
            "artifact_digest": sha(html),
            "source_type": "legislation",
            "language": "en",
            "jurisdiction": "Singapore",
            "identifiers": ["Penal Code 1871 s 84"],
            "publisher_label": "SSO label in unverified browser snapshot",
            "locator": "https://sso.agc.gov.sg/Act/PC1871",
            "dates": {},
        },
        {
            "source_id": "src:pc84-extracted",
            "work_id": "work:pc1871",
            "expression_id": "expression:pc84:post2022",
            "manifestation_id": "manifestation:pc84:extracted",
            "artifact_digest": sha(extracted),
            "source_type": "legislation",
            "language": "en",
            "jurisdiction": "Singapore",
            "identifiers": ["Penal Code 1871 s 84"],
            "publisher_label": "derived from unverified browser snapshot",
            "locator": "research:locked-extraction",
            "dates": {"effective_from": "2022-03-01"},
        },
        {
            "source_id": SOURCE_ID,
            "work_id": "work:pc1871",
            "expression_id": "expression:pc84:post2022",
            "manifestation_id": "manifestation:pc84:excerpt",
            "artifact_digest": sha(text),
            "source_type": "legislation",
            "language": "en",
            "jurisdiction": "Singapore",
            "identifiers": ["Penal Code 1871 s 84"],
            "publisher_label": "selected exact excerpts from locked extraction",
            "locator": "research:prototype-excerpt",
            "dates": {"effective_from": "2022-03-01"},
        },
        {
            "source_id": STATUS_SOURCE_ID,
            "work_id": "work:synthetic-status",
            "expression_id": "expression:synthetic-status:v1",
            "manifestation_id": "manifestation:synthetic-status:text",
            "artifact_digest": sha(source_bytes),
            "source_type": "synthetic",
            "language": "en",
            "jurisdiction": "SYN",
            "identifiers": [],
            "publisher_label": "Yuho synthetic research fixture",
            "locator": "research:synthetic-status",
            "dates": {},
        },
    ]
    semantic_mappings = []
    for item in mapping["leaf_mappings"]:
        for support_span in item["supporting_spans"]:
            semantic_mappings.append(
                {
                    "semantic_id": item["semantic_id"],
                    "artifact_digest": sha(extracted),
                    "source_id": item["source_id"],
                    "role": "requirement",
                    "span": support_span,
                }
            )
    for item in mapping["group_mappings"]:
        semantic_mappings.append(
            {
                "semantic_id": item["semantic_id"],
                "artifact_digest": sha(extracted),
                "source_id": item["source_id"],
                "role": item["role"],
                "span": item["span"],
            }
        )
    semantic_mappings.sort(
        key=lambda item: (
            item["semantic_id"],
            item["artifact_digest"],
            item["span"]["start"],
            item["span"]["end"],
        )
    )
    semantic_ids = sorted(semantic_inventory(model["registry"]))
    if sorted({item["semantic_id"] for item in semantic_mappings}) != semantic_ids:
        raise ValueError("mapping and executable semantic inventories differ")
    core = {
        "schema": "yuho.model-bundle/v1",
        "canonical_profile": "yuho.sorted-json/v1",
        "hash_algorithm": "sha256",
        "model_id": MODEL_ID,
        "artifacts": sorted(
            [
                {
                    "sha256": sha(data),
                    "byte_length": len(data),
                    "media_type": (
                        "application/json"
                        if data is model_bytes
                        else "text/html"
                        if data is html
                        else "text/plain; charset=utf-8"
                    ),
                    "role": (
                        "executable_model"
                        if data is model_bytes
                        else "evidence"
                        if data is html
                        else "source_text"
                    ),
                }
                for data in (model_bytes, html, extracted, text, source_bytes)
            ],
            key=lambda item: item["sha256"],
        ),
        "legal_sources": sorted(records, key=lambda item: item["source_id"]),
        "derivations": sorted(
            [
                {
                    "child_digest": sha(extracted),
                    "parent_digest": sha(html),
                    "tool_name": "yuho.sg-legislation-html-extraction",
                    "tool_version": "v1",
                    "configuration": "locked section-84 extraction",
                },
                {
                    "child_digest": sha(text),
                    "parent_digest": sha(extracted),
                    "tool_name": "yuho.sg-section-84-excerpt",
                    "tool_version": "v1",
                    "configuration": "six exact substrings in declared order",
                },
            ],
            key=lambda item: (item["child_digest"], item["parent_digest"]),
        ),
        "semantic_mappings": semantic_mappings,
        "scope": {
            "coverage_mode": "enumerated_only",
            "semantic_ids": semantic_ids,
            "source_ids": sorted(item["source_id"] for item in records),
            "expression_ids": [
                "expression:pc84:post2022",
                "expression:synthetic-status:v1",
            ],
            "exclusions": sorted(
                [
                    {"exclusion_id": eid, "reason": reason}
                    for eid, reason in [
                        ("ex:anchor", "no anchor offence or section 323"),
                        ("ex:case-time", "no case-specific expression selection"),
                        ("ex:cpc", "no fitness or CPC disposition"),
                        ("ex:evidence", "no evidence assessment or diagnosis"),
                        ("ex:outcome", "no guilt, conviction, acquittal or sentence"),
                    ]
                ],
                key=lambda item: item["exclusion_id"],
            ),
            "limitations": sorted(
                [
                    "Externally supplied synthetic proof statuses only",
                    "Research prototype, not legal advice",
                    "Research review predates executable bytes and bundle digest",
                    "Source hashes identify bytes and do not authenticate authority",
                ]
            ),
            "unsupported_capabilities": sorted(
                [
                    "case-specific legal applicability",
                    "court outcome",
                    "evidence assessment",
                    "section 107 burden adjudication",
                ]
            ),
            "jurisdictions": ["Singapore"],
            "subject_matters": ["section 84 exception structure"],
            "temporal_context": {"kind": "unspecified"},
        },
        "executable_model": {
            "artifact_digest": sha(model_bytes),
            "format": "yuho.kernel-input/v1",
            "fragment": FRAGMENT,
        },
    }
    if (
        scope["model_id"] != core["model_id"]
        or scope["model_version"] != "v1"
        or scope["expression_effective_from"] != "2022-03-01"
    ):
        raise ValueError("sidecar model scope differs from bundle core")
    return core, artifacts


def verify_committed(extracted: bytes) -> tuple[dict, dict, dict]:
    model = request(extracted)
    mapping = model_mapping(extracted)
    scope = model_scope()
    for name, item in (
        ("request.json", model),
        ("mapping.json", mapping),
        ("scope.json", scope),
    ):
        if (HERE / name).read_bytes() != canonical(item, line=name != "request.json"):
            raise ValueError(f"committed prototype artifact differs: {name}")
    return model, mapping, scope


def validate_synthetic_scenario(raw: bytes, baseline: dict) -> dict:
    if len(raw) > 1048576:
        raise ValueError("synthetic request exceeds kernel byte limit")
    candidate = json.loads(raw.decode("utf-8", errors="strict"))
    if raw != canonical(candidate):
        raise ValueError("synthetic request is not canonical JSON")
    if not isinstance(candidate, dict) or not re.fullmatch(
        r"[A-Z][0-9]{2}", str(candidate.get("request_id", ""))
    ):
        raise ValueError("invalid synthetic request ID")
    facts = candidate.get("facts")
    if not isinstance(facts, dict) or set(facts) != set(baseline["facts"]):
        raise ValueError("synthetic request must classify every exact model leaf")
    expected = copy.deepcopy(baseline)
    expected["request_id"] = candidate["request_id"]
    for identifier in facts:
        if not isinstance(facts[identifier], dict):
            raise ValueError("synthetic fact binding is not an object")
        status = facts[identifier].get("proof_status")
        if status not in (
            {"kind": "proved"},
            {"kind": "not_proved"},
            {"kind": "unresolved", "reason": "not_determined"},
            {"kind": "unresolved", "reason": "external_decision_pending"},
        ):
            raise ValueError("unsupported synthetic proof classification")
        expected["facts"][identifier]["proof_status"] = status
    if candidate != expected:
        raise ValueError("request exceeds the bounded synthetic model scope")
    return candidate


def build_bundle(
    input_dir: Path, packet_dir: Path, destination: Path, validator: Path
) -> str:
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination already exists")
    html, extracted = locked_inputs(input_dir, packet_dir)
    model, mapping, scope = verify_committed(extracted)
    core, artifacts = bundle_core(model, mapping, scope, html, extracted)
    parent = destination.parent
    if not parent.is_dir():
        raise ValueError("destination parent missing")
    with tempfile.TemporaryDirectory(
        prefix=".yuho-s84-bundle-", dir=parent
    ) as temporary:
        temporary_path = Path(temporary)
        store = temporary_path / "artifacts" / "sha256"
        store.mkdir(parents=True)
        (temporary_path / "model-bundle.json").write_bytes(canonical(core))
        for digest, data in artifacts.items():
            (store / digest).write_bytes(data)
        result = subprocess.run(
            [str(validator), "validate", str(temporary_path)],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError(
                "ModelBundle validator rejected built package: "
                + result.stdout.decode("utf-8", "replace")
            )
        validation = json.loads(result.stdout)
        digest = sha(DOMAIN + canonical(core))
        if validation["status"] != "valid" or validation["bundle_digest"] != digest:
            raise ValueError("validator digest or status differs")
        rename_without_replace(temporary_path, destination)
    return digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["build-bundle", "verify-artifacts", "run-synthetic"]
    )
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--validator", type=Path)
    parser.add_argument("--request-path", type=Path)
    parser.add_argument("--kernel", type=Path)
    args = parser.parse_args()
    if args.command == "build-bundle" and (
        args.destination is None or args.validator is None
    ):
        parser.error("build-bundle requires --destination and --validator")
    if args.command == "run-synthetic" and (
        args.request_path is None or args.kernel is None
    ):
        parser.error("run-synthetic requires --request-path and --kernel")
    _, extracted = locked_inputs(args.input_dir, args.packet_dir)
    model, _, _ = verify_committed(extracted)
    if args.command == "build-bundle":
        print(
            build_bundle(
                args.input_dir,
                args.packet_dir,
                args.destination,
                args.validator.resolve(),
            )
        )
    elif args.command == "run-synthetic":
        raw = regular_bytes(args.request_path, 1048576)
        validate_synthetic_scenario(raw, model)
        result = subprocess.run(
            [str(args.kernel.resolve())],
            input=raw + b"\n",
            capture_output=True,
            check=True,
        )
        if result.stderr or len(result.stdout.splitlines()) != 1:
            raise ValueError("kernel did not return one clean protocol response")
        sys.stdout.buffer.write(result.stdout)
    else:
        print("locked inputs and committed prototype artifacts match")


if __name__ == "__main__":
    main()
