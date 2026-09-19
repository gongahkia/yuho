"""Explicit migration-only projection; never evaluates legacy Python truthiness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Projection:
    bindings: dict[str, dict[str, Any]]
    notices: tuple[str, ...]
    rejections: tuple[str, ...]


def project(payload: Mapping[str, Any], leaf_ids: Mapping[str, str]) -> Projection:
    if "facts" in payload and set(payload) != {"facts"}:
        return Projection({}, (), ("unsupported outer fields beside facts",))
    raw = payload.get("facts", payload)
    if not isinstance(raw, Mapping):
        return Projection({}, (), ("facts object required",))
    bindings: dict[str, dict[str, Any]] = {}
    notices: list[str] = []
    rejections: list[str] = []
    for legacy_name, raw_value in raw.items():
        if not isinstance(legacy_name, str):
            rejections.append("non-string legacy fact key")
            continue
        if legacy_name not in leaf_ids:
            rejections.append(f"{legacy_name}: no explicit leaf-ID mapping")
            continue
        leaf_id = leaf_ids[legacy_name]
        if leaf_id in bindings:
            rejections.append(f"{legacy_name}: duplicate leaf-ID binding {leaf_id}")
            continue
        if isinstance(raw_value, bool):
            bindings[leaf_id] = {"type": "bool", "value": raw_value}
            notices.append(f"{legacy_name}: primitive Boolean shorthand projected explicitly")
            continue
        if not isinstance(raw_value, Mapping):
            rejections.append(f"{legacy_name}: non-Boolean legacy truthiness unsupported")
            continue
        allowed = {"type", "value", "burden", "standard_of_proof", "source", "date",
                   "jurisdiction"}
        unsupported = sorted(set(raw_value) - allowed)
        if unsupported:
            rejections.append(f"{legacy_name}: unsupported metadata {','.join(unsupported)}")
            continue
        if raw_value.get("type", "bool") != "bool" or not isinstance(raw_value.get("value"), bool):
            rejections.append(f"{legacy_name}: Boolean type and value required")
            continue
        projected: dict[str, Any] = {"type": "bool", "value": raw_value["value"]}
        if "burden" in raw_value:
            holder = raw_value["burden"]
            if holder not in ("prosecution", "defence"):
                rejections.append(f"{legacy_name}: unsupported burden label")
                continue
            projected["burden"] = {"holder": holder, "kind": "unspecified"}
            notices.append(f"{legacy_name}: burden kind unclassified; no legal/evidential inference")
        if "standard_of_proof" in raw_value:
            standard = raw_value["standard_of_proof"]
            if standard not in ("beyond_reasonable_doubt", "balance_of_probabilities"):
                rejections.append(f"{legacy_name}: unsupported proof-standard label")
                continue
            projected["standard_of_proof"] = standard
        provenance = {new: raw_value[old] for old, new in
                      (("source", "source_label"), ("date", "recorded_date"),
                       ("jurisdiction", "jurisdiction")) if old in raw_value}
        if provenance:
            projected["provenance"] = provenance
            notices.append(f"{legacy_name}: provenance labels are descriptive only")
        bindings[leaf_id] = projected
    return Projection(bindings, tuple(notices), tuple(rejections))
