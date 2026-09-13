"""Bounded synthetic YuhoSurface-v0.1 compiler and kernel conformance."""

from __future__ import annotations

from dataclasses import asdict
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator

from rewrite.frontend import bundle, core


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "rewrite/frontend/fixtures/synthetic"
MODEL = FIXTURE / "restricted_entry.yh"
SCENARIO = FIXTURE / "scenario_all_proved.yh"
KERNEL = Path(os.environ.get("YUHO_KERNEL_BIN", "/missing-yuho-kernel"))
VALIDATOR = Path(os.environ.get("YUHO_BUNDLE_BIN", "/missing-yuho-model-bundle"))
LEAVES = (
    "f:entry",
    "f:no-authorization",
    "f:knowledge",
    "f:immediate-danger",
    "f:rescue-purpose",
)


def all_status(values: tuple[str, ...]) -> str:
    if "not_proved" in values:
        return "not_satisfied"
    if any(value.startswith("unresolved") for value in values):
        return "unresolved"
    return "satisfied"


def run_kernel(data: bytes) -> dict:
    completed = subprocess.run(
        [str(KERNEL)], input=data + b"\n", capture_output=True, check=True
    )
    assert not completed.stderr
    return json.loads(completed.stdout)


def scenario_with(values: tuple[str, ...]) -> str:
    text = SCENARIO.read_text(encoding="utf-8")
    for identifier, status in zip(LEAVES, values, strict=True):
        text, count = re.subn(
            rf"(?m)^([ \t]*{re.escape(identifier)} = )proved;$",
            rf"\g<1>{status};",
            text,
        )
        assert count == 1
    return text


class FrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = MODEL.read_text(encoding="utf-8")
        cls.scenario = SCENARIO.read_text(encoding="utf-8")
        cls.model = core.parse_synthetic(cls.source, str(MODEL))
        cls.default = core.compile_synthetic_text(
            cls.source, cls.scenario, str(MODEL), str(SCENARIO)
        )

    def diagnostic(self, source: str, scenario: str, code: str) -> None:
        with self.assertRaises(core.FrontendError) as caught:
            core.compile_synthetic_text(source, scenario, str(MODEL), str(SCENARIO))
        error = caught.exception
        self.assertEqual(error.code, code)
        self.assertIn(error.path, {str(MODEL), str(SCENARIO)})
        self.assertGreaterEqual(error.token.line, 1)
        self.assertGreaterEqual(error.token.column, 1)

    def test_parse_resolution_types_canonical_golden(self) -> None:
        self.assertEqual(
            asdict(self.model), asdict(core.parse_synthetic(self.source, str(MODEL)))
        )
        self.assertEqual(self.model.identifier.line, 2)
        checked = core.check_synthetic(self.model, str(MODEL))
        self.assertEqual(len(checked["rules"]), 2)
        self.assertEqual(
            {x.category.text for x in self.model.offence.elements},
            {"conduct", "circumstance", "fault"},
        )
        self.assertEqual(
            {x.category.text for x in self.model.exception.elements},
            {"circumstance", "purpose"},
        )
        self.assertEqual(self.default, (FIXTURE / "request.json").read_bytes())
        self.assertEqual(self.default, core.canonical(json.loads(self.default)))
        request_schema = json.loads(
            (ROOT / "rewrite/haskell/schema/request.schema.json").read_bytes()
        )
        Draft202012Validator(request_schema).validate(json.loads(self.default))
        self.assertEqual(
            core.sha(self.default),
            "2c46977bbb855fac477d85f4d8dc2581d992bb87253cc1372146fb679212a535",
        )
        self.assertFalse(self.default.endswith(b"\n"))
        self.assertEqual(core.LANGUAGE_VERSION, "yuho.surface/v0.1")

    def test_model_and_scenario_are_separate_and_annotations_inert(self) -> None:
        self.assertNotIn("proof_assignments", self.source)
        self.assertNotIn("offence o:entry", self.scenario)
        changed = self.source.replace(
            "burden none none none", "burden synthetic_context none none"
        )
        changed = changed.replace(
            "Fictional, non-authoritative compiler",
            "Synthetic, non-authoritative compiler",
        )
        self.assertEqual(
            self.default,
            core.compile_synthetic_text(
                changed, self.scenario, str(MODEL), str(SCENARIO)
            ),
        )
        alternative = self.source.replace(
            "all g:emergency-requirements", "any g:emergency-requirements"
        )
        compiled = json.loads(
            core.compile_synthetic_text(
                alternative, self.scenario, str(MODEL), str(SCENARIO)
            )
        )
        self.assertEqual(
            compiled["registry"][1]["program"]["requirements"][0]["kind"], "any"
        )

    def test_cli_check_compile_stdout_and_atomic_path(self) -> None:
        command = [sys.executable, "-m", "rewrite.frontend"]
        checked = subprocess.run(
            command + ["check", str(MODEL)], capture_output=True, check=True, cwd=ROOT
        )
        self.assertEqual(json.loads(checked.stdout)["status"], "valid")
        emitted = subprocess.run(
            command + ["compile", str(MODEL), "--scenario", str(SCENARIO)],
            capture_output=True,
            check=True,
            cwd=ROOT,
        )
        self.assertEqual(emitted.stdout, self.default)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("one.json", "two.json"):
                output = root / name
                result = subprocess.run(
                    command
                    + [
                        "compile",
                        str(MODEL),
                        "--scenario",
                        str(SCENARIO),
                        "--output",
                        str(output),
                    ],
                    capture_output=True,
                    check=True,
                    cwd=ROOT,
                )
                self.assertFalse(result.stdout)
                self.assertEqual(output.read_bytes(), self.default)
            self.assertEqual(
                (root / "one.json").read_bytes(), (root / "two.json").read_bytes()
            )
            forbidden = subprocess.run(
                command
                + [
                    "compile",
                    str(MODEL),
                    "--scenario",
                    str(SCENARIO),
                    "--output",
                    str(root / "one.json"),
                ],
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(forbidden.returncode, 1)
            self.assertEqual(json.loads(forbidden.stderr)["code"], "SFE015")
            (root / "link").symlink_to(root, target_is_directory=True)
            forbidden = subprocess.run(
                command
                + [
                    "compile",
                    str(MODEL),
                    "--scenario",
                    str(SCENARIO),
                    "--output",
                    str(root / "link/new.json"),
                ],
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(forbidden.returncode, 1)
            self.assertFalse((root / "new.json").exists())

    def test_negative_diagnostics(self) -> None:
        cases = [
            (
                self.source.replace(
                    "variant SuppliedProofStatus-v1;", "variant SuppliedProofStatus-v1"
                ),
                self.scenario,
                "SFE001",
            ),
            (
                self.source.replace("jurisdiction Fictional", "jurisdiction Singapore"),
                self.scenario,
                "SFE021",
            ),
            (
                self.source.replace(
                    "variant SuppliedProofStatus-v1", "variant ClosedBooleanBranches-v1"
                ),
                self.scenario,
                "SFE004",
            ),
            (
                self.source.replace(
                    "element conduct f:entry", "element conduct f:no-authorization"
                ),
                self.scenario,
                "SFE002",
            ),
            (
                self.source.replace(
                    "element conduct f:entry", "element unknown f:entry"
                ),
                self.scenario,
                "SFE017",
            ),
            (
                self.source.replace("to o:entry", "to o:missing"),
                self.scenario,
                "SFE018",
            ),
            (
                self.source.replace(
                    "f:entry, f:no-authorization", "f:missing, f:no-authorization"
                ),
                self.scenario,
                "SFE003",
            ),
            (
                self.source.replace(
                    "f:entry, f:no-authorization", "ann:none, f:no-authorization"
                ),
                self.scenario,
                "SFE012",
            ),
            (
                self.source.replace(
                    "f:entry, f:no-authorization",
                    "f:immediate-danger, f:no-authorization",
                ),
                self.scenario,
                "SFE019",
            ),
            (
                self.source.replace(
                    "f:entry, f:no-authorization",
                    "g:offence-requirements, f:no-authorization",
                ),
                self.scenario,
                "SFE008",
            ),
            (
                self.source.replace(
                    "offence_requirements g:offence-requirements",
                    "offence_requirements f:entry",
                ),
                self.scenario,
                "SFE020",
            ),
            (
                self.source.replace(
                    "all g:offence-requirements", "any g:offence-requirements"
                ),
                self.scenario.replace("f:entry = proved;", "f:entry = unknown;"),
                "SFE010",
            ),
            (
                self.source.replace(
                    "burden none none none", "burden section107 defence legal"
                ),
                self.scenario,
                "SFE011",
            ),
            (
                self.source.replace(
                    "source src:fictional-rule source_text",
                    "source src:fictional-rule official",
                ),
                self.scenario,
                "SFE014",
            ),
            (
                self.source.replace(
                    "fictional/restricted-entry.txt", "../untrusted.txt"
                ),
                self.scenario,
                "SFE015",
            ),
            (
                self.source.replace(
                    "source src:fictional-rule source_text",
                    "source src:fictional-rule source_text",
                ),
                self.scenario.replace("f:entry = proved;", "f:undeclared = proved;"),
                "SFE009",
            ),
            (self.source, self.scenario.replace("f:entry = proved;", ""), "SFE009"),
            (
                self.source,
                self.scenario.replace("f:entry = proved;", "f:entry = unresolved;"),
                "SFE010",
            ),
            (
                self.source.replace("f:entry quote q:entry", "f:entry quote q:missing"),
                self.scenario,
                "SFE003",
            ),
            (
                self.source.replace("element conduct", "sentence conduct"),
                self.scenario,
                "SFE013",
            ),
            (
                self.source.replace("purpose compiler_fixture", "purpose official_law"),
                self.scenario,
                "SFE021",
            ),
            (self.source + "\nmodel Duplicate-v0.1 {}", self.scenario, "SFE002"),
        ]
        for source, scenario, code in cases:
            with self.subTest(code=code, source=source[:30]):
                self.diagnostic(source, scenario, code)
        self.diagnostic(
            self.source,
            self.scenario.replace(
                "f:entry = proved;", "f:entry = proved;\n f:entry = proved;"
            ),
            "SFE002",
        )
        self.diagnostic(
            self.source.replace(
                "policy 2026-09-13 1024", "policy 2026-09-13 1024 extra"
            ),
            self.scenario,
            "SFE001",
        )

    def test_strict_utf8_lf_limits_and_no_partial_output(self) -> None:
        self.diagnostic(self.source.replace("\n", "\r\n", 1), self.scenario, "SFE001")
        self.diagnostic(self.source + "// trailing comment\r", self.scenario, "SFE001")
        self.diagnostic(
            self.source + "x" * (core.MAX_SOURCE_BYTES + 1), self.scenario, "SFE016"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            invalid = root / "invalid.yh"
            invalid.write_bytes(b"model \xff")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "rewrite.frontend",
                    "compile",
                    str(invalid),
                    "--scenario",
                    str(SCENARIO),
                    "--output",
                    str(root / "result.json"),
                ],
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stderr)["code"], "SFE001")
            self.assertFalse((root / "result.json").exists())
            invalid.write_text(
                self.source.replace("to o:entry", "to o:missing"), encoding="utf-8"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "rewrite.frontend",
                    "compile",
                    str(invalid),
                    "--scenario",
                    str(SCENARIO),
                    "--output",
                    str(root / "result.json"),
                ],
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stderr)["code"], "SFE018")
            self.assertFalse((root / "result.json").exists())
            (root / "link.yh").symlink_to(MODEL)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "rewrite.frontend",
                    "check",
                    str(root / "link.yh"),
                ],
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(json.loads(result.stderr)["code"], "SFE015")
        unicode_source = self.source.replace(
            "Immediate danger to another person",
            "Immediate danger to another person 🌐",
        )
        unicode_request = json.loads(
            core.compile_synthetic_text(
                unicode_source, self.scenario, str(MODEL), str(SCENARIO)
            )
        )
        text = unicode_request["sources"][0]["text"].encode("utf-8")
        self.assertIn("🌐".encode("utf-8"), text)
        leaf = unicode_request["registry"][1]["program"]["requirements"][0]["members"][
            0
        ]
        self.assertEqual(
            text[leaf["span"]["start"] : leaf["span"]["end"]].decode("utf-8"),
            "Immediate danger to another person 🌐",
        )

    @unittest.skipUnless(KERNEL.is_file(), "kernel executable not configured")
    def test_golden_and_exhaustive_243_status_matrix(self) -> None:
        completed = subprocess.run(
            [str(KERNEL)], input=self.default + b"\n", capture_output=True, check=True
        )
        self.assertEqual(completed.stdout, (FIXTURE / "response.json").read_bytes())
        result_schema = json.loads(
            (ROOT / "rewrite/haskell/schema/result.schema.json").read_bytes()
        )
        Draft202012Validator(result_schema).validate(json.loads(completed.stdout))
        for values in itertools.product(
            ("proved", "not_proved", "unresolved(not_determined)"), repeat=5
        ):
            scenario = scenario_with(values)
            request = core.compile_synthetic_text(
                self.source, scenario, str(MODEL), "<scenario>"
            )
            result = run_kernel(request)
            root = result["rules"][0]
            rescue = result["rules"][1] if len(result["rules"]) == 2 else None
            observations = [
                item for rule in result["rules"] for item in rule["proof_observations"]
            ]
            self.assertEqual(len(observations), 5 if rescue is not None else 3)
            self.assertEqual(
                [item["proof_status"]["kind"] for item in observations],
                [value.split("(")[0] for value in values[: len(observations)]],
            )
            self.assertEqual(len(root["trace"]), 4)
            offence_status = all_status(values[:3])
            rescue_status = all_status(values[3:])
            self.assertEqual(root["trace"][0]["value"], offence_status)
            if rescue is not None:
                self.assertEqual(len(rescue["trace"]), 3)
                self.assertEqual(rescue["trace"][0]["value"], rescue_status)
            self.assertEqual(rescue is not None, offence_status == "satisfied")
            expected_final = (
                offence_status
                if offence_status != "satisfied"
                else "not_satisfied"
                if rescue_status == "satisfied"
                else "satisfied"
                if rescue_status == "not_satisfied"
                else "unresolved"
            )
            self.assertEqual(root["status"], expected_final)
            offence_all = all(value == "proved" for value in values[:3])
            rescue_all = all(value == "proved" for value in values[3:])
            if offence_all and rescue_all:
                self.assertEqual(root["branches"][0]["reason"], "defeated")
                self.assertEqual(root["status"], "not_satisfied")
            if offence_all and all(value == "not_proved" for value in values[3:]):
                self.assertEqual(root["status"], "satisfied")
            if any(value == "not_proved" for value in values[:3]):
                self.assertEqual(root["status"], "not_satisfied")
            self.assertTrue(
                {
                    "guilt",
                    "conviction",
                    "acquittal",
                    "sentence",
                    "court_disposition",
                }.isdisjoint(result)
            )

    @unittest.skipUnless(VALIDATOR.is_file(), "bundle validator not configured")
    def test_deterministic_bundle_and_rejections(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = root / "first", root / "second"
            digest1 = bundle.build(self.model, self.default, first)
            digest2 = bundle.build(self.model, self.default, second)
            with self.assertRaises(ValueError):
                bundle.build(self.model, self.default + b" ", root / "rejected")
            self.assertFalse((root / "rejected").exists())
            self.assertEqual(digest1, digest2)
            self.assertEqual(
                digest1,
                "091cb0f9286dd8dd67cbd686d92a410d7a928fe8fa2d03396821e814ca4976db",
            )
            inventory = sorted(
                str(item.relative_to(first))
                for item in first.rglob("*")
                if item.is_file()
            )
            self.assertEqual(len(inventory), 4)
            self.assertEqual(
                inventory,
                sorted(
                    str(item.relative_to(second))
                    for item in second.rglob("*")
                    if item.is_file()
                ),
            )
            for name in inventory:
                self.assertEqual(
                    (first / name).read_bytes(), (second / name).read_bytes()
                )
            good = subprocess.run(
                [str(VALIDATOR), "validate", str(first)], capture_output=True
            )
            self.assertEqual(good.returncode, 0, good.stdout)
            self.assertEqual(json.loads(good.stdout)["bundle_digest"], digest1)
            self.assertFalse((first / "reviews").exists())
            artifact = first / "artifacts/sha256" / core.sha(self.default)
            artifact.write_bytes(self.default + b" ")
            self.assertEqual(
                subprocess.run(
                    [str(VALIDATOR), "validate", str(first)], capture_output=True
                ).returncode,
                1,
            )
            extra = second / "unexpected"
            extra.write_text("x")
            self.assertEqual(
                subprocess.run(
                    [str(VALIDATOR), "validate", str(second)], capture_output=True
                ).returncode,
                1,
            )
            extra.unlink()
            source_digest = core.sha(
                json.loads(self.default)["sources"][0]["text"].encode("utf-8")
            )
            source_artifact = second / "artifacts/sha256" / source_digest
            source_original = source_artifact.read_bytes()
            source_artifact.write_bytes(source_original + b"x")
            self.assertEqual(
                subprocess.run(
                    [str(VALIDATOR), "validate", str(second)], capture_output=True
                ).returncode,
                1,
            )
            source_artifact.write_bytes(source_original)
            manifest_path = second / "model-bundle.json"
            manifest_original = manifest_path.read_bytes()
            manifest = json.loads(manifest_original)
            manifest["semantic_mappings"][0]["span"]["end"] = len(source_original) + 1
            manifest_path.write_bytes(core.canonical(manifest))
            self.assertEqual(
                subprocess.run(
                    [str(VALIDATOR), "validate", str(second)], capture_output=True
                ).returncode,
                1,
            )
            manifest_path.write_bytes(manifest_original)
            source_artifact.unlink()
            self.assertEqual(
                subprocess.run(
                    [str(VALIDATOR), "validate", str(second)], capture_output=True
                ).returncode,
                1,
            )
            source_artifact.write_bytes(source_original)
            (second / "link").symlink_to(first)
            self.assertEqual(
                subprocess.run(
                    [str(VALIDATOR), "validate", str(second)], capture_output=True
                ).returncode,
                1,
            )
            with self.assertRaises(core.FrontendError):
                bundle.build(self.model, self.default, root / "link/new")
            self.assertFalse((root / "link/new").exists())


if __name__ == "__main__":
    unittest.main()
