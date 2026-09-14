"""Offline synthetic program integration over temporal selection and typed plans."""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import tempfile

from . import core, plan, temporal


RECEIPT_SCHEMA = "yuho.program-receipt/v0.1"


def _source(path: Path) -> bytes:
    return core._regular_source(path).encode("utf-8")


def _checked(
    plan_path: Path, module_root: Path, scenario_path: Path
) -> tuple[plan.PlanSource, plan.Scenario, plan.TemporalAssessment]:
    authored = plan.parse_plan(_source(plan_path), str(plan_path))
    scenario = plan.parse_scenario(_source(scenario_path), str(scenario_path))
    if authored.steps[0].source_kind != "temporal" or scenario.conduct_date is None:
        plan.fail("SFE041", scenario.path, scenario.identifier, "temporal assessment and conduct date required")
    plan.check_modules(authored, module_root)
    resolved = temporal.resolve(module_root / "proof/temporal_root.yh", module_root / "proof")
    temporal_scenario = temporal.Scenario(
        scenario.path, scenario.identifier, resolved.root.family,
        scenario.conduct_date, scenario.proof,
    )
    selected = temporal.select(resolved, temporal_scenario)
    return authored, scenario, plan.TemporalAssessment(resolved, selected, scenario.conduct_date)


def check(plan_path: Path, module_root: Path, scenario_path: Path) -> bytes:
    authored, scenario, assessment = _checked(plan_path, module_root, scenario_path)
    plan._prepare(authored, scenario, module_root, assessment)
    return assessment.selected.record


def _publish_directory(source: Path, destination: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = libc.renameat2
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    if renameat2(-100, os.fsencode(source), -100, os.fsencode(destination), 1):
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), str(destination))


def run(
    plan_path: Path,
    module_root: Path,
    scenario_path: Path,
    destination: Path,
    kernel: Path,
    validator: Path,
) -> bytes:
    core._safe_output(destination)
    source_root = module_root.resolve(strict=True)
    if destination.parent.resolve().is_relative_to(source_root):
        plan.fail("SFE066", str(destination), core.Token("error", "", 1, 1), "output must be outside module root")
    authored, scenario, assessment = _checked(plan_path, module_root, scenario_path)
    with tempfile.TemporaryDirectory(prefix=".yuho-program-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "packet"
        staging.mkdir()
        bundles = staging / "step-bundles"
        bundles.mkdir()
        plan_bytes, lock, trace, digests = plan.execute(
            authored, scenario, module_root, kernel, validator, bundles, assessment
        )
        requests, _, recomputed_lock = plan._prepare(authored, scenario, module_root, assessment)
        if lock != recomputed_lock:
            plan.fail("SFE064", authored.path, authored.identifier, "execution module lock changed")
        plan_record = json.loads(plan_bytes)
        trace_record = json.loads(trace)
        if (
            plan_record["temporal"]["selection_sha256"] != core.sha(assessment.selected.record)
            or trace_record["temporal_selection_sha256"] != core.sha(assessment.selected.record)
            or trace_record["plan_sha256"] != core.sha(plan_bytes)
            or trace_record["module_lock_sha256"] != core.sha(lock)
            or trace_record["scenario_sha256"] != core.sha(scenario.source)
        ):
            plan.fail("SFE064", authored.path, authored.identifier, "temporal plan or trace binding differs")
        (staging / "requests").mkdir()
        for step in plan_record["steps"]:
            sid = step["id"]
            if step["request_sha256"] != core.sha(requests[sid]) or step["bundle_digest"] != digests[sid]:
                plan.fail("SFE064", authored.path, authored.identifier, "step binding differs")
            (staging / "requests" / f"{sid}.json").write_bytes(requests[sid])
        artifacts = {
            "module-lock.json": lock,
            "temporal-module-lock.json": assessment.resolved.lock,
            "temporal-selection.json": assessment.selected.record,
            "plan.json": plan_bytes,
            "trace.json": trace,
        }
        for name, data in artifacts.items():
            (staging / name).write_bytes(data)
        receipt = core.canonical({
            "schema": RECEIPT_SCHEMA,
            "package_id": authored.identifier.text,
            "scope": {"jurisdiction": "Fictional", "authority": "none", "review": "none", "court_outcome": "excluded", "use": "compiler_fixture"},
            "source_inventory": json.loads(lock)["modules"],
            "scenario_id": scenario.identifier.text,
            "scenario_sha256": core.sha(scenario.source),
            "module_lock_sha256": core.sha(lock),
            "temporal_module_lock_sha256": core.sha(assessment.resolved.lock),
            "conduct_date": scenario.conduct_date.text,
            "temporal_selection_sha256": core.sha(assessment.selected.record),
            "selected_expression": {
                "id": assessment.selected.expression.identifier.text,
                "version": assessment.selected.expression.version.text,
            },
            "plan_sha256": core.sha(plan_bytes),
            "steps": [
                {"id": step["id"], "request_sha256": step["request_sha256"], "bundle_digest": step["bundle_digest"]}
                for step in plan_record["steps"]
            ],
            "trace_sha256": core.sha(trace),
            "final_technical_state": trace_record["outputs"]["assessment::root-status"],
        })
        (staging / "receipt.json").write_bytes(receipt)
        _publish_directory(staging, destination)
    return receipt


def verify(
    packet: Path,
    plan_path: Path,
    module_root: Path,
    scenario_path: Path,
    kernel: Path,
    validator: Path,
) -> None:
    if not packet.is_dir() or packet.is_symlink():
        raise ValueError("program packet must be a regular directory")
    with tempfile.TemporaryDirectory(prefix=".yuho-program-verify-") as temporary:
        expected = Path(temporary) / "packet"
        run(plan_path, module_root, scenario_path, expected, kernel, validator)
        def inventory(root: Path) -> dict[str, bytes]:
            result = {}
            for directory, subdirectories, filenames in os.walk(root, followlinks=False):
                for name in (*subdirectories, *filenames):
                    item = Path(directory) / name
                    if item.is_symlink():
                        raise ValueError("symlink in program packet")
                for name in filenames:
                    item = Path(directory) / name
                    if not item.is_file():
                        raise ValueError("unexpected packet object")
                    result[item.relative_to(root).as_posix()] = item.read_bytes()
            return result
        if inventory(packet) != inventory(expected):
            raise ValueError("program packet differs from exact authored-source replay")
