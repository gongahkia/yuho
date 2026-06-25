"""PROV-compatible provenance sidecars for generated Yuho artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from yuho import __version__

PROVENANCE_SCHEMA_VERSION = "1.0.0"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_transpile_provenance(
    source_path: Path | str,
    source_text: str,
    output_path: Path | str,
    target: str,
    command: list[str] | None = None,
    tool_version: str = __version__,
) -> dict[str, Any]:
    source_id = "yuho:source"
    output = Path(output_path)
    output_id = "yuho:artifact"
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    entity: dict[str, dict[str, Any]] = {
        source_id: {
            "prov:type": "yuho:SourceFile",
            "prov:label": str(source_path),
            "yuho:sha256": sha256_text(source_text),
        },
        output_id: {
            "prov:type": "yuho:GeneratedArtifact",
            "prov:label": str(output),
            "yuho:target": target,
        },
    }
    if output.exists():
        entity[output_id]["yuho:sha256"] = sha256_file(output)

    activity: dict[str, dict[str, Any]] = {
        "yuho:transpile": {
            "prov:type": "yuho:Transpile",
            "prov:startedAtTime": generated_at,
            "prov:endedAtTime": generated_at,
            "prov:used": source_id,
            "yuho:target": target,
            "yuho:toolVersion": tool_version,
        }
    }
    if command:
        activity["yuho:transpile"]["yuho:command"] = command

    return {
        "@context": {
            "prov": "http://www.w3.org/ns/prov#",
            "yuho": "https://yuho.dev/ns#",
        },
        "_schema_version": PROVENANCE_SCHEMA_VERSION,
        "@type": "prov:Bundle",
        "entity": entity,
        "activity": activity,
        "wasGeneratedBy": {
            output_id: {
                "prov:activity": "yuho:transpile",
                "prov:time": generated_at,
            }
        },
        "used": {"yuho:transpile": {"prov:entity": source_id}},
    }


def write_transpile_provenance_sidecar(
    source_path: Path | str,
    source_text: str,
    output_path: Path | str,
    target: str,
    command: list[str] | None = None,
) -> str:
    out = Path(output_path)
    provenance = build_transpile_provenance(
        source_path=source_path,
        source_text=source_text,
        output_path=out,
        target=target,
        command=command,
    )
    sidecar = out.with_name(f"{out.name}.prov.json")
    sidecar.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return str(sidecar)
