"""Migration-only projection; never silently discard old penalty payloads."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Projection:
    declarations: tuple[dict, ...]
    notices: tuple[str, ...]
    rejections: tuple[str, ...]


def project(legacy: list[dict], provision_path: tuple[str, ...],
            leaf_ids: dict[str, str]) -> Projection:
    declarations: list[dict] = []
    notices: list[str] = []
    rejections: list[str] = []
    for index, item in enumerate(legacy):
        if set(item) - {"guard", "source_id", "span"}:
            rejections.append(f"declaration {index}: punishment terms or unknown fields excluded")
            continue
        if not isinstance(item.get("source_id"), str) or "span" not in item:
            rejections.append(f"declaration {index}: source and span required")
            continue
        guard = item.get("guard")
        if guard is None:
            resolved = {"kind": "unguarded"}
        elif isinstance(guard, str) and guard in leaf_ids:
            resolved = {"kind": "leaf_true", "leaf_id": leaf_ids[guard]}
            notices.append(f"declaration {index}: mapped legacy guard {guard} by adapter")
        else:
            rejections.append(f"declaration {index}: unmappable legacy guard")
            continue
        identity = ":".join(provision_path)
        declarations.append({"penalty_id": f"pen:{identity}:{index}",
                             "source_id": item["source_id"], "span": item["span"],
                             "guard": resolved})
        notices.append(f"declaration {index}: assigned migration penalty ID from path/index")
    return Projection(tuple(declarations) if not rejections else (),
                      tuple(notices), tuple(rejections))
