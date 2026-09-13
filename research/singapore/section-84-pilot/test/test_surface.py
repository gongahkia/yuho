"""The authored section 84 surface slice must preserve the reviewed bytes."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


PILOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = PILOT / "surface/section84.yh"
FRONTEND_FILE = PILOT / "surface/frontend.py"
PROTOTYPE = PILOT / "prototype"
SOURCE = Path(os.environ.get("YUHO_S84_INPUT_DIR", "/missing-s84-source"))
PACKET = Path(os.environ.get("YUHO_S84_PACKET_DIR", "/missing-s84-packet"))
KERNEL = Path(os.environ.get("YUHO_KERNEL_BIN", "/missing-yuho-kernel"))
VALIDATOR = Path(os.environ.get("YUHO_BUNDLE_BIN", "/missing-yuho-model-bundle"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


surface = load_module("s84_surface_test", FRONTEND_FILE)
pilot = load_module("s84_pilot_surface_test", PROTOTYPE / "pilot.py")


@unittest.skipUnless(
    SOURCE.is_dir() and PACKET.is_dir(), "locked external source packet not configured"
)
class SurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE_FILE.read_text(encoding="utf-8")
        cls.expected = (PROTOTYPE / "request.json").read_bytes()

    def compiled(self, text: str) -> bytes:
        return surface.compile_text(text, str(SOURCE_FILE), SOURCE, PACKET)

    def assert_code(self, text: str, code: str) -> None:
        with self.assertRaises(surface.FrontendError) as caught:
            self.compiled(text)
        self.assertEqual(caught.exception.code, code)
        diagnostic = caught.exception.diagnostic()
        self.assertEqual(diagnostic["path"], str(SOURCE_FILE))
        self.assertGreaterEqual(diagnostic["line"], 1)
        self.assertGreaterEqual(diagnostic["column"], 1)

    def test_parse_ast_resolution_and_exact_request(self) -> None:
        ast = surface.parse_text(self.source, str(SOURCE_FILE))
        again = surface.parse_text(self.source, str(SOURCE_FILE))
        self.assertEqual(asdict(ast), asdict(again))
        self.assertEqual(ast.identifier.line, 1)
        self.assertEqual(ast.root_requirement.text, "g:premise-and-routes")
        self.assertEqual(len(ast.propositions), 13)
        declarations, assignments = surface.check(ast, str(SOURCE_FILE))
        self.assertEqual(len(declarations), 13)
        self.assertEqual(len(assignments), 8)
        result = self.compiled(self.source)
        self.assertEqual(result, self.expected)
        self.assertEqual(
            hashlib.sha256(result).hexdigest(),
            "1ebe4d4fdd3de643e938c512fafd1c68ed437728b1249d32b6a236639a58d6e2",
        )
        self.assertFalse(result.endswith(b"\n"))
        self.assertEqual(result, pilot.canonical(json.loads(result)))

    def test_repeat_compile_and_atomic_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuho-s84-surface-") as temp:
            root = Path(temp)
            first, second = root / "first.json", root / "second.json"
            self.assertEqual(
                surface.compile_file(SOURCE_FILE, first, SOURCE, PACKET), self.expected
            )
            self.assertEqual(
                surface.compile_file(SOURCE_FILE, second, SOURCE, PACKET), self.expected
            )
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first.read_bytes(), self.expected)
            with self.assertRaises(surface.FrontendError) as caught:
                surface.compile_file(SOURCE_FILE, first, SOURCE, PACKET)
            self.assertEqual(caught.exception.code, "SFE015")
            self.assertEqual(first.read_bytes(), self.expected)

    @unittest.skipUnless(KERNEL.is_file(), "kernel executable not configured")
    def test_all_accepted_fixture_assignments_and_kernel_snapshots(self) -> None:
        for request_path in sorted((PROTOTYPE / "fixtures/requests").glob("X*.json")):
            with self.subTest(request=request_path.name):
                expected_request = json.loads(request_path.read_bytes())
                source = self.source.replace(
                    "request X00;", f"request {expected_request['request_id']};"
                )
                for identifier, fact in expected_request["facts"].items():
                    status = fact["proof_status"]
                    expression = status["kind"]
                    if "reason" in status:
                        expression += f"({status['reason']})"
                    pattern = rf"(?m)^([ \t]*{re.escape(identifier)} = )unresolved\(not_determined\);$"
                    source, count = re.subn(pattern, rf"\g<1>{expression};", source)
                    self.assertEqual(count, 1)
                compiled = self.compiled(source)
                self.assertEqual(compiled, request_path.read_bytes())
                completed = subprocess.run(
                    [str(KERNEL)],
                    input=compiled + b"\n",
                    capture_output=True,
                    check=True,
                )
                snapshot = (
                    PROTOTYPE / "fixtures/snapshots" / request_path.name
                ).read_bytes()
                self.assertEqual(completed.stdout, snapshot)
                self.assertFalse(completed.stderr)
                result = json.loads(completed.stdout)
                self.assertTrue(
                    {
                        "guilt",
                        "conviction",
                        "acquittal",
                        "sentence",
                        "diagnosis",
                        "fitness",
                        "cpc_disposition",
                    }.isdisjoint(result)
                )

    @unittest.skipUnless(VALIDATOR.is_file(), "bundle validator not configured")
    def test_compiled_request_builds_identical_reviewed_bundle(self) -> None:
        compiled = self.compiled(self.source)
        html, extracted = pilot.locked_inputs(SOURCE, PACKET)
        _, mapping, scope = pilot.verify_committed(extracted)
        core, artifacts = pilot.bundle_core(
            json.loads(compiled), mapping, scope, html, extracted
        )
        with tempfile.TemporaryDirectory(prefix="yuho-s84-surface-bundle-") as temp:
            root = Path(temp)
            from_surface = root / "surface"
            store = from_surface / "artifacts/sha256"
            store.mkdir(parents=True)
            (from_surface / "model-bundle.json").write_bytes(pilot.canonical(core))
            for digest, data in artifacts.items():
                (store / digest).write_bytes(data)
            validation = subprocess.run(
                [str(VALIDATOR), "validate", str(from_surface)],
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout)
            result = json.loads(validation.stdout)
            digest = "02e51da9fa1bf285eec7cca8b55494c1d6a8e82b9b7e7e300a30b338ecbd404a"
            self.assertEqual(result["bundle_digest"], digest)
            self.assertEqual(result["status"], "valid")
            self.assertEqual(result["applicable_asserted_reviews"], [])
            original = root / "original"
            self.assertEqual(
                pilot.build_bundle(SOURCE, PACKET, original, VALIDATOR), digest
            )
            names = sorted(
                str(p.relative_to(from_surface))
                for p in from_surface.rglob("*")
                if p.is_file()
            )
            self.assertEqual(len(names), 6)
            self.assertEqual(
                names,
                sorted(
                    str(p.relative_to(original))
                    for p in original.rglob("*")
                    if p.is_file()
                ),
            )
            for name in names:
                self.assertEqual(
                    (from_surface / name).read_bytes(), (original / name).read_bytes()
                )
            self.assertEqual(
                (store / hashlib.sha256(compiled).hexdigest()).read_bytes(), compiled
            )
            self.assertFalse((from_surface / "reviews").exists())

    def test_negative_diagnostic_categories(self) -> None:
        cases = [
            (
                self.source.replace(
                    "variant SuppliedProofStatus-v1;", "variant SuppliedProofStatus-v1"
                ),
                "SFE001",
            ),
            (
                self.source.replace(
                    "leaf f:nature-incapacity proposition P84-04 quote q:nature;",
                    "leaf f:unsoundness-time proposition P84-04 quote q:nature;",
                ),
                "SFE002",
            ),
            (
                self.source.replace(
                    "f:wrong-causation, f:ordinary", "f:missing, f:ordinary"
                ),
                "SFE003",
            ),
            (
                self.source.replace(
                    "variant SuppliedProofStatus-v1;",
                    "variant RegisteredPresumptionDerivations-v1;",
                ),
                "SFE004",
            ),
            (
                self.source.replace(
                    "leaf f:nature-incapacity", "leaf g:nature-incapacity"
                ),
                "SFE005",
            ),
            (
                self.source.replace(
                    "all g:nature (f:nature-causation, f:nature-incapacity);",
                    "all g:nature (f:nature-causation);",
                ),
                "SFE006",
            ),
            (
                self.source.replace("root r:section84", "missing_root r:section84"),
                "SFE007",
            ),
            (
                self.source.replace(
                    "any g:alternative-routes (g:nature, g:wrongfulness, g:control);",
                    "any g:alternative-routes (g:nature, g:premise-and-routes, g:control);",
                ),
                "SFE008",
            ),
            (
                self.source.replace(
                    "    f:nature-incapacity = unresolved(not_determined);\n", ""
                ),
                "SFE009",
            ),
            (
                self.source.replace(
                    "f:nature-incapacity = unresolved(not_determined);",
                    "f:nature-incapacity = presumed;",
                ),
                "SFE010",
            ),
            (
                self.source.replace(
                    "burden section107 defence legal balance_of_probabilities;",
                    "burden section107 defence legal beyond_reasonable_doubt;",
                ),
                "SFE011",
            ),
            (
                self.source.replace(
                    "g:nature, g:wrongfulness, g:control",
                    "g:nature, section107, g:control",
                ),
                "SFE012",
            ),
            (self.source.replace("all g:nature", "exception g:nature"), "SFE013"),
            (
                self.source.replace(
                    "mapping_source src:pc84-extracted;", "mapping_source src:wrong;"
                ),
                "SFE014",
            ),
            (
                self.source.replace(
                    "quote q:ordinary support q:wrong_operator;",
                    "quote q:ordinary;",
                ),
                "SFE014",
            ),
        ]
        for changed, code in cases:
            with self.subTest(code=code):
                self.assertNotEqual(changed, self.source)
                self.assert_code(changed, code)

    def test_assignment_provenance_and_non_executable_limitations(self) -> None:
        changed = self.source.replace(
            "technical rule status only", "technical support status only"
        )
        self.assertEqual(self.compiled(changed), self.expected)
        self.assert_code(
            self.source.replace(
                "f:nature-incapacity = unresolved(not_determined);",
                "f:nature-incapacity = unresolved(unsupported_reason);",
            ),
            "SFE010",
        )
        self.assert_code(
            self.source.replace(
                "f:nature-incapacity = unresolved(not_determined);",
                "f:nature-incapacity = unresolved(not_determined);\n"
                "    f:extra = proved;",
            ),
            "SFE009",
        )
        self.assert_code(
            self.source.replace(
                "f:nature-incapacity = unresolved(not_determined);",
                "f:nature-incapacity = unresolved(not_determined);\n"
                "    f:nature-incapacity = proved;",
            ),
            "SFE002",
        )

    def test_lf_utf8_and_failed_output_safety(self) -> None:
        self.assert_code(self.source.replace("\n", "\r\n"), "SFE001")
        self.assertEqual(self.compiled("// 🧪\n" + self.source), self.expected)
        self.assert_code(self.source + (" " * surface.MAX_SOURCE_BYTES), "SFE016")
        with tempfile.TemporaryDirectory(prefix="yuho-s84-surface-negative-") as temp:
            root = Path(temp)
            invalid = root / "invalid.yh"
            invalid.write_bytes(b"model \xff")
            output = root / "out.json"
            with self.assertRaises(surface.FrontendError) as caught:
                surface.compile_file(invalid, output, SOURCE, PACKET)
            self.assertEqual(caught.exception.code, "SFE001")
            self.assertFalse(output.exists())
            invalid.write_text(self.source.replace("variant", "wrong_variant", 1))
            with self.assertRaises(surface.FrontendError):
                surface.compile_file(invalid, output, SOURCE, PACKET)
            self.assertFalse(output.exists())
            symlink = root / "link.yh"
            symlink.symlink_to(SOURCE_FILE)
            with self.assertRaises(surface.FrontendError) as caught:
                surface.compile_file(symlink, output, SOURCE, PACKET)
            self.assertEqual(caught.exception.code, "SFE015")
            output.symlink_to(SOURCE_FILE)
            with self.assertRaises(surface.FrontendError) as caught:
                surface.compile_file(SOURCE_FILE, output, SOURCE, PACKET)
            self.assertEqual(caught.exception.code, "SFE015")
            output.unlink()
            parent_link = root / "parent-link"
            parent_link.symlink_to(root, target_is_directory=True)
            with self.assertRaises(surface.FrontendError) as caught:
                surface.compile_file(
                    SOURCE_FILE, parent_link / "request.json", SOURCE, PACKET
                )
            self.assertEqual(caught.exception.code, "SFE015")


if __name__ == "__main__":
    unittest.main()
