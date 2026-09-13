"""Synthetic v0.4 typed plan conformance and trust-boundary tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from rewrite.frontend import core, plan


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "rewrite/frontend/fixtures/plan"
KERNEL = Path(os.environ.get("YUHO_KERNEL_BIN", "/missing-yuho-kernel"))
VALIDATOR = Path(os.environ.get("YUHO_BUNDLE_BIN", "/missing-yuho-model-bundle"))
PLAN = FIXTURE / "plan.yh"
SCENARIO = FIXTURE / "scenarios/basic.yh"


class PlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authored = plan.parse_plan(PLAN.read_bytes(), str(PLAN))

    def scenario(self, *changes: tuple[str, str]) -> plan.Scenario:
        source = SCENARIO.read_text(encoding="utf-8")
        for old, new in changes:
            self.assertIn(old, source)
            source = source.replace(old, new, 1)
        return plan.parse_scenario(source.encode(), str(SCENARIO))

    def run_case(self, *changes: tuple[str, str]) -> tuple[dict, dict, dict, dict]:
        with TemporaryDirectory() as temp:
            compiled, lock, trace, digests = plan.execute(
                self.authored,
                self.scenario(*changes),
                FIXTURE,
                KERNEL,
                VALIDATOR,
                Path(temp),
            )
            return json.loads(trace), json.loads(compiled), json.loads(lock), digests

    def assert_plan_error(self, old: str, new: str, code: str) -> None:
        source = PLAN.read_text(encoding="utf-8")
        self.assertIn(old, source)
        with self.assertRaises(core.FrontendError) as caught:
            plan.parse_plan(source.replace(old, new, 1).encode(), str(PLAN))
        self.assertEqual(caught.exception.code, code)
        self.assertGreater(caught.exception.token.line, 0)
        self.assertGreater(caught.exception.token.column, 0)

    def test_authored_dag_and_fragment_models(self) -> None:
        self.assertEqual(
            [step.identifier.text for step in self.authored.steps],
            ["assessment", "choice", "basic_terms", "enhanced_terms"],
        )
        requests, models, lock = plan._prepare(self.authored, self.scenario(), FIXTURE)
        self.assertEqual(
            [
                json.loads(requests[step.identifier.text])["fragment"]
                for step in self.authored.steps
            ],
            [step.variant.text for step in self.authored.steps],
        )
        self.assertEqual(json.loads(lock)["schema"], "yuho.execution-module-lock/v0.1")
        self.assertEqual(len(json.loads(lock)["modules"]), 7)
        for sid in ("choice", "basic_terms", "enhanced_terms"):
            self.assertEqual(
                models[sid].identifier.text,
                f"fictional.{('candidate-selection' if sid == 'choice' else sid.replace('_', '-'))}",
            )

    @unittest.skipUnless(
        KERNEL.is_file() and VALIDATOR.is_file(), "offline Haskell binaries required"
    )
    def test_decision_covering_matrix(self) -> None:
        cases = [
            ("basic", (), "satisfied", ["pen:basic"], "completed", "skipped"),
            (
                "enhanced",
                (
                    ("f:basic = true", "f:basic = false"),
                    ("f:enhanced = false", "f:enhanced = true"),
                ),
                "satisfied",
                ["pen:enhanced"],
                "skipped",
                "completed",
            ),
            (
                "exception",
                (
                    (
                        "f:fictional.emergency-rescue.version-1-0-0.immediate-danger = not_proved",
                        "f:fictional.emergency-rescue.version-1-0-0.immediate-danger = proved",
                    ),
                    (
                        "f:fictional.emergency-rescue.version-1-0-0.rescue-purpose = not_proved",
                        "f:fictional.emergency-rescue.version-1-0-0.rescue-purpose = proved",
                    ),
                ),
                "not_satisfied",
                None,
                "skipped",
                "skipped",
            ),
            (
                "requirements_not_proved",
                (
                    (
                        "f:fictional.restricted-entry.version-1-0-0.entry = proved",
                        "f:fictional.restricted-entry.version-1-0-0.entry = not_proved",
                    ),
                ),
                "not_satisfied",
                None,
                "skipped",
                "skipped",
            ),
            (
                "unresolved",
                (
                    (
                        "f:fictional.restricted-entry.version-1-0-0.entry = proved",
                        "f:fictional.restricted-entry.version-1-0-0.entry = unresolved(not_determined)",
                    ),
                ),
                "unresolved",
                None,
                "skipped",
                "skipped",
            ),
            (
                "selection_guard_false",
                (("f:eligible = true", "f:eligible = false"),),
                "satisfied",
                [],
                "skipped",
                "skipped",
            ),
            (
                "no_candidate",
                (("f:basic = true", "f:basic = false"),),
                "satisfied",
                [],
                "skipped",
                "skipped",
            ),
        ]
        for name, changes, root_status, selected, basic, enhanced in cases:
            with self.subTest(name=name):
                trace, compiled, lock, digests = self.run_case(*changes)
                self.assertEqual(trace["schema"], plan.TRACE_SCHEMA)
                self.assertEqual(compiled["schema"], plan.PLAN_SCHEMA)
                self.assertEqual(lock["schema"], "yuho.execution-module-lock/v0.1")
                self.assertEqual(len(digests), 4)
                steps = {item["id"]: item for item in trace["steps"]}
                self.assertEqual(
                    steps["assessment"]["outputs"]["root-status"], root_status
                )
                self.assertEqual(steps["basic_terms"]["state"], basic)
                self.assertEqual(steps["enhanced_terms"]["state"], enhanced)
                if selected is None:
                    self.assertEqual(steps["choice"]["state"], "skipped")
                    self.assertEqual(steps["choice"]["response_sha256"], None)
                    expected = (
                        "upstream_unresolved"
                        if name == "unresolved"
                        else "upstream_defeated"
                        if name == "exception"
                        else "upstream_not_proved"
                    )
                    self.assertEqual(steps["choice"]["reason"], expected)
                    self.assertEqual(steps["basic_terms"]["reason"], expected)
                    self.assertEqual(steps["enhanced_terms"]["reason"], expected)
                else:
                    self.assertEqual(
                        steps["choice"]["outputs"]["selected-penalties"], selected
                    )
                    if name == "basic":
                        self.assertEqual(
                            steps["enhanced_terms"]["reason"],
                            "alternate_candidate_selected",
                        )
                    if name == "enhanced":
                        self.assertEqual(
                            steps["basic_terms"]["reason"],
                            "alternate_candidate_selected",
                        )
                    if name in {"selection_guard_false", "no_candidate"}:
                        self.assertEqual(
                            steps["basic_terms"]["reason"], "candidate_not_selected"
                        )
                self.assertEqual(trace["scope"]["court_outcome"], "excluded")
                self.assertNotIn("guilty", json.dumps(trace))
                self.assertNotIn("acquitted", json.dumps(trace))

    @unittest.skipUnless(
        KERNEL.is_file() and VALIDATOR.is_file(), "offline Haskell binaries required"
    )
    def test_ambiguous_candidate_and_kernel_failure(self) -> None:
        with TemporaryDirectory() as temp:
            ambiguous = self.scenario(("f:enhanced = false", "f:enhanced = true"))
            with self.assertRaises(core.FrontendError) as caught:
                plan.execute(
                    self.authored, ambiguous, FIXTURE, KERNEL, VALIDATOR, Path(temp)
                )
            self.assertEqual(caught.exception.code, "SFE060")
        with TemporaryDirectory() as temp:
            with self.assertRaises(core.FrontendError) as caught:
                plan.execute(
                    self.authored,
                    self.scenario(),
                    FIXTURE,
                    Path("/bin/false"),
                    VALIDATOR,
                    Path(temp),
                )
            self.assertEqual(caught.exception.code, "SFE065")

    @unittest.skipUnless(
        KERNEL.is_file() and VALIDATOR.is_file(), "offline Haskell binaries required"
    )
    def test_determinism_relocation_and_hash_binding(self) -> None:
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            a = plan.execute(
                self.authored, self.scenario(), FIXTURE, KERNEL, VALIDATOR, Path(first)
            )
            b = plan.execute(
                self.authored, self.scenario(), FIXTURE, KERNEL, VALIDATOR, Path(second)
            )
            self.assertEqual(a, b)
            for name, data in (
                ("plan.json", a[0]),
                ("module-lock.json", a[1]),
                ("basic-trace.json", a[2]),
            ):
                self.assertEqual((FIXTURE / "snapshots" / name).read_bytes(), data)
            for name, data in (
                ("execution-plan-v0.1.schema.json", a[0]),
                ("execution-trace-v0.1.schema.json", a[2]),
            ):
                schema = json.loads(
                    (ROOT / "rewrite/frontend/schema" / name).read_bytes()
                )
                Draft202012Validator.check_schema(schema)
                Draft202012Validator(schema).validate(json.loads(data))
            tree = Path(second) / "relocated"
            shutil.copytree(FIXTURE, tree)
            relocated_plan = plan.parse_plan(
                (tree / "plan.yh").read_bytes(), str(tree / "plan.yh")
            )
            relocated = plan.parse_scenario(
                (tree / "scenarios/basic.yh").read_bytes(),
                str(tree / "scenarios/basic.yh"),
            )
            with TemporaryDirectory() as third:
                c = plan.execute(
                    relocated_plan, relocated, tree, KERNEL, VALIDATOR, Path(third)
                )
            self.assertEqual(a, c)
            requests, _, _ = plan._prepare(self.authored, self.scenario(), FIXTURE)
            plan.verify_compiled(a[0], requests, a[3], str(PLAN))
            tampered = dict(requests)
            tampered["choice"] += b" "
            with self.assertRaises(core.FrontendError) as caught:
                plan.verify_compiled(a[0], tampered, a[3], str(PLAN))
            self.assertEqual(caught.exception.code, "SFE064")
            tampered_digests = {**a[3], "choice": "0" * 64}
            with self.assertRaises(core.FrontendError) as caught:
                plan.verify_compiled(a[0], requests, tampered_digests, str(PLAN))
            self.assertEqual(caught.exception.code, "SFE064")

    def test_plan_diagnostics(self) -> None:
        self.assert_plan_error("step choice uses", "step assessment uses", "SFE053")
        self.assert_plan_error(
            "assessment::root-status", "missing::root-status", "SFE054"
        )
        self.assert_plan_error(
            "assessment::root-status", "assessment::bad-output", "SFE058"
        )
        self.assert_plan_error("is satisfied", "is unresolved", "SFE059")
        self.assert_plan_error(
            "GuardedPenaltySelection-v1", "PenaltyTerms-v1", "SFE058"
        )
        self.assert_plan_error(
            "output assessment::root-status;", "output bad::root-status;", "SFE063"
        )
        self.assert_plan_error(
            "step assessment uses SuppliedProofStatus-v1 module fictional.restricted-entry-composition version 1.0.0;",
            "step assessment uses SuppliedProofStatus-v1 module fictional.restricted-entry-composition version 1.0.0 when choice::selected-penalties contains pen:basic;",
            "SFE055",
        )
        self.assert_plan_error("step choice uses", "step choice when", "SFE001")
        self.assert_plan_error(
            "step basic_terms uses PenaltyTerms-v1 module fictional.basic-terms version 1.0.0 when choice::selected-penalties contains pen:basic;",
            "step basic_terms uses PenaltyTerms-v1 module fictional.basic-terms version 1.0.0;",
            "SFE062",
        )
        self.assert_plan_error(
            "  outputs {",
            "  execution-plan fictional.duplicate version 1.0.0;\n  outputs {",
            "SFE053",
        )

    def test_stable_order_for_ready_steps(self) -> None:
        source = PLAN.read_text(encoding="utf-8")
        basic = next(
            line
            for line in source.splitlines(keepends=True)
            if "step basic_terms" in line
        )
        enhanced = next(
            line
            for line in source.splitlines(keepends=True)
            if "step enhanced_terms" in line
        )
        reordered = source.replace(basic + enhanced, enhanced + basic)
        self.assertNotEqual(reordered, source)
        result = plan.parse_plan(reordered.encode(), str(PLAN))
        self.assertEqual(
            [step.identifier.text for step in result.steps],
            ["assessment", "choice", "basic_terms", "enhanced_terms"],
        )

    def test_fragment_and_scenario_diagnostics(self) -> None:
        model_file = FIXTURE / "fragments/fictional.candidate-selection.yh"
        source = model_file.read_bytes()
        changed = source.replace(b"candidate pen:enhanced", b"candidate pen:basic")
        with self.assertRaises(core.FrontendError) as caught:
            plan.parse_fragment(changed, str(model_file))
        self.assertEqual(caught.exception.code, "SFE053")
        with self.assertRaises(core.FrontendError) as caught:
            plan._prepare(
                self.authored,
                self.scenario(("f:basic = true", "f:basic = undecided")),
                FIXTURE,
            )
        self.assertEqual(caught.exception.code, "SFE059")
        with self.assertRaises(core.FrontendError) as caught:
            plan._prepare(
                self.authored, self.scenario(("f:basic = true;", "")), FIXTURE
            )
        self.assertEqual(caught.exception.code, "SFE059")
        with self.assertRaises(core.FrontendError) as caught:
            plan.parse_fragment(
                source.replace(b"candidate pen:basic", b"candidate pen:unknown"),
                str(model_file),
            )
        self.assertEqual(caught.exception.code, "SFE059")

    def test_missing_module_symlink_and_resource_limit(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp) / "modules"
            shutil.copytree(FIXTURE, root)
            (root / "fragments/fictional.basic-terms.yh").unlink()
            with self.assertRaises(core.FrontendError) as caught:
                plan.check_modules(self.authored, root)
            self.assertEqual(caught.exception.code, "SFE057")
            (root / "fragments/fictional.basic-terms.yh").symlink_to(
                FIXTURE / "fragments/fictional.basic-terms.yh"
            )
            with self.assertRaises(core.FrontendError) as caught:
                plan.check_modules(self.authored, root)
            self.assertEqual(caught.exception.code, "SFE015")
        source = PLAN.read_bytes().replace(
            b"  outputs {",
            b"  step extra uses PenaltyTerms-v1 module fictional.basic-terms version 1.0.0 when choice::selected-penalties contains pen:basic;\n  outputs {",
        )
        with self.assertRaises(core.FrontendError) as caught:
            plan.parse_plan(source, str(PLAN))
        self.assertEqual(caught.exception.code, "SFE067")
        with patch.object(plan, "MAX_TOTAL_REQUEST_BYTES", 10):
            with self.assertRaises(core.FrontendError) as caught:
                plan._prepare(self.authored, self.scenario(), FIXTURE)
            self.assertEqual(caught.exception.code, "SFE067")

    def test_closed_schema_rejects_unknown_fields(self) -> None:
        for name in (
            "execution-plan-v0.1.schema.json",
            "execution-trace-v0.1.schema.json",
        ):
            schema = json.loads((ROOT / "rewrite/frontend/schema" / name).read_bytes())
            record = json.loads(
                (
                    FIXTURE
                    / "snapshots"
                    / ("plan.json" if "plan-" in name else "basic-trace.json")
                ).read_bytes()
            )
            Draft202012Validator(schema).validate(record)
            with self.assertRaises(Exception):
                Draft202012Validator(schema).validate({**record, "unexpected": True})

    @unittest.skipUnless(
        KERNEL.is_file() and VALIDATOR.is_file(), "offline Haskell binaries required"
    )
    def test_cli_atomic_failure_and_canonical_outputs(self) -> None:
        with TemporaryDirectory() as temp:
            trace = Path(temp) / "trace.json"
            output_plan = Path(temp) / "plan.json"
            output_lock = Path(temp) / "lock.json"
            command = [
                sys.executable,
                "-m",
                "rewrite.frontend",
                "plan-run",
                str(PLAN),
                "--module-root",
                str(FIXTURE),
                "--scenario",
                str(SCENARIO),
                "--trace-output",
                str(trace),
                "--plan-output",
                str(output_plan),
                "--lock-output",
                str(output_lock),
                "--kernel-bin",
                "/bin/false",
                "--bundle-bin",
                str(VALIDATOR),
            ]
            failed = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
            self.assertEqual(failed.returncode, 1)
            self.assertFalse(trace.exists())
            self.assertFalse(output_plan.exists())
            self.assertFalse(output_lock.exists())
            command[command.index("/bin/false")] = str(KERNEL)
            passed = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertEqual(
                trace.read_bytes(), core.canonical(json.loads(trace.read_bytes()))
            )
            self.assertEqual(
                json.loads(trace.read_bytes())["schema"], plan.TRACE_SCHEMA
            )
            self.assertEqual(
                output_plan.read_bytes(), (FIXTURE / "snapshots/plan.json").read_bytes()
            )
            self.assertEqual(
                output_lock.read_bytes(),
                (FIXTURE / "snapshots/module-lock.json").read_bytes(),
            )

    @unittest.skipUnless(
        KERNEL.is_file() and VALIDATOR.is_file(), "offline Haskell binaries required"
    )
    def test_protocol_and_response_resource_failure(self) -> None:
        with TemporaryDirectory() as temp:
            executable = Path(temp) / "bad-kernel"
            executable.write_text("#!/bin/sh\nprintf 'not-json\\n'\n", encoding="utf-8")
            executable.chmod(0o700)
            bundles = Path(temp) / "bundles"
            bundles.mkdir()
            with self.assertRaises(core.FrontendError) as caught:
                plan.execute(
                    self.authored,
                    self.scenario(),
                    FIXTURE,
                    executable,
                    VALIDATOR,
                    bundles,
                )
            self.assertEqual(caught.exception.code, "SFE065")
        with TemporaryDirectory() as temp:
            with patch.object(plan, "MAX_RESPONSE_BYTES", 16):
                with self.assertRaises(core.FrontendError) as caught:
                    plan.execute(
                        self.authored,
                        self.scenario(),
                        FIXTURE,
                        KERNEL,
                        VALIDATOR,
                        Path(temp),
                    )
                self.assertEqual(caught.exception.code, "SFE065")


if __name__ == "__main__":
    unittest.main()
