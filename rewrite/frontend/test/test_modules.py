"""YuhoSurface-v0.2 offline module composition and regression tests."""

from __future__ import annotations

from dataclasses import asdict, replace
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from rewrite.frontend import bundle, core, modules


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "rewrite/frontend/fixtures/modules"
SCENARIO = ROOT / "rewrite/frontend/fixtures/scenarios/module_all_proved.yh"
KERNEL = Path(os.environ.get("YUHO_KERNEL_BIN", "/missing-yuho-kernel"))
VALIDATOR = Path(os.environ.get("YUHO_BUNDLE_BIN", "/missing-yuho-model-bundle"))
LEAVES = (
    "f:fictional.restricted-entry.version-1-0-0.entry",
    "f:fictional.restricted-entry.version-1-0-0.no-authorization",
    "f:fictional.restricted-entry.version-1-0-0.knowledge",
    "f:fictional.emergency-rescue.version-1-0-0.immediate-danger",
    "f:fictional.emergency-rescue.version-1-0-0.rescue-purpose",
)


def statuses(values: tuple[str, ...]) -> str:
    source = SCENARIO.read_text(encoding="utf-8")
    for leaf, status in zip(LEAVES, values, strict=True):
        source, count = re.subn(
            rf"(?m)^([ \t]*{re.escape(leaf)} = )proved;$", rf"\g<1>{status};", source
        )
        assert count == 1
    return source


def all_status(values: tuple[str, ...]) -> str:
    if "not_proved" in values:
        return "not_satisfied"
    if any(value.startswith("unresolved") for value in values):
        return "unresolved"
    return "satisfied"


class ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resolved = modules.resolve(FIXTURE / "composition.yh", FIXTURE)
        cls.scenario = SCENARIO.read_text(encoding="utf-8")
        cls.request = modules.compile_resolved(
            cls.resolved, cls.scenario, str(SCENARIO)
        )

    def copy_modules(self, temp: str) -> Path:
        target = Path(temp) / "modules"
        target.mkdir()
        for name in ("composition.yh", "offence.yh", "exception.yh"):
            (target / name).write_bytes((FIXTURE / name).read_bytes())
        return target

    def assert_error(self, root: Path, code: str) -> core.FrontendError:
        with self.assertRaises(core.FrontendError) as caught:
            modules.resolve(root / "composition.yh", root)
        error = caught.exception
        self.assertEqual(error.code, code)
        self.assertTrue(error.path)
        self.assertGreaterEqual(error.token.line, 1)
        self.assertGreaterEqual(error.token.column, 1)
        return error

    def test_independent_ast_exports_and_explicit_composition(self) -> None:
        for name, kind in (
            ("offence.yh", "offence"),
            ("exception.yh", "exception"),
            ("composition.yh", "composition"),
        ):
            with self.subTest(module=name):
                raw = (FIXTURE / name).read_bytes()
                parsed = modules.parse_module(raw, name)
                self.assertEqual(parsed.kind.text, kind)
                self.assertEqual(
                    asdict(parsed), asdict(modules.parse_module(raw, name))
                )
                self.assertEqual(parsed.language.text, modules.LANGUAGE)
                self.assertEqual(parsed.jurisdiction.text, "Fictional")
        root = self.resolved.root
        self.assertEqual(
            [item.alias.text for item in root.imports], ["entry", "rescue"]
        )
        self.assertEqual(
            root.composition.attached_exception.text, "rescue::x:emergency-rescue"
        )
        self.assertEqual(root.composition.attached_offence.text, "entry::o:entry")
        self.assertEqual(
            [module.identifier.text for module in self.resolved.ordered],
            [
                "fictional.emergency-rescue",
                "fictional.restricted-entry",
                "fictional.restricted-entry-composition",
            ],
        )
        self.assertEqual(len(self.resolved.model.offence.elements), 3)
        self.assertEqual(len(self.resolved.model.exception.elements), 2)
        self.assertEqual(len(set(LEAVES)), 5)
        self.assertTrue(all("version-1-0-0" in leaf for leaf in LEAVES))

    def test_lock_canonical_exact_hashes_and_relocation(self) -> None:
        expected = (FIXTURE / "MODULE-LOCK.json").read_bytes()
        self.assertEqual(self.resolved.lock, expected)
        lock = json.loads(expected)
        self.assertEqual(expected, core.canonical(lock))
        self.assertEqual(lock["schema"], modules.LOCK_SCHEMA)
        self.assertEqual(lock["compiler"], modules.COMPILER)
        self.assertEqual(
            core.sha(expected),
            "badac18187f709389a8ae8d16e5adde77d94d9d151d922dc5d3564b20415a845",
        )
        self.assertNotIn(str(ROOT), expected.decode("utf-8"))
        modules.verify_lock(self.resolved, expected, str(FIXTURE / "MODULE-LOCK.json"))
        for row in lock["modules"]:
            source = next(
                module.source_bytes
                for module in self.resolved.ordered
                if module.identifier.text == row["id"]
            )
            self.assertEqual(row["byte_length"], len(source))
            self.assertEqual(row["sha256"], core.sha(source))
        with TemporaryDirectory() as left, TemporaryDirectory() as right:
            first = self.copy_modules(left)
            relocated = modules.resolve(first / "composition.yh", first)
            reversed_copy = Path(right) / "modules"
            reversed_copy.mkdir()
            for name in ("exception.yh", "offence.yh", "composition.yh"):
                (reversed_copy / name).write_bytes((FIXTURE / name).read_bytes())
            other = modules.resolve(reversed_copy / "composition.yh", reversed_copy)
            self.assertEqual(relocated.lock, other.lock)
            self.assertEqual(
                self.request,
                modules.compile_resolved(relocated, self.scenario, str(SCENARIO)),
            )
            self.assertEqual(
                self.request,
                modules.compile_resolved(other, self.scenario, str(SCENARIO)),
            )
            (first / "offence.yh").write_bytes(
                (first / "offence.yh").read_bytes() + b"// byte change\n"
            )
            changed = modules.resolve(first / "composition.yh", first)
            with self.assertRaises(core.FrontendError) as caught:
                modules.verify_lock(changed, expected, "locked.json")
            self.assertEqual(caught.exception.code, "SFE037")

    def test_request_schema_and_golden(self) -> None:
        self.assertEqual(self.request, (FIXTURE / "request.json").read_bytes())
        self.assertEqual(self.request, core.canonical(json.loads(self.request)))
        self.assertEqual(
            core.sha(self.request),
            "2d2d46fb5cb05d004a9ec1beef7bef233e8c70e83e0af6bd506135c0852cae2a",
        )
        self.assertFalse(self.request.endswith(b"\n"))
        schema = json.loads(
            (ROOT / "rewrite/haskell/schema/request.schema.json").read_bytes()
        )
        Draft202012Validator(schema).validate(json.loads(self.request))
        original = self.resolved.root.source_bytes.decode("utf-8")
        self.assertNotIn("proof_assignments", original)
        self.assertNotIn("offence o:entry", self.scenario)
        self.assertEqual(set(json.loads(self.request)["facts"]), set(LEAVES))

    def test_context_and_unused_imports_do_not_execute(self) -> None:
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            offence = root / "offence.yh"
            offence.write_text(
                offence.read_text(encoding="utf-8").replace(
                    "burden none none none not_applicable;",
                    "burden synthetic_context none none not_applicable;",
                ),
                encoding="utf-8",
            )
            modified = modules.resolve(root / "composition.yh", root)
            self.assertEqual(
                self.request,
                modules.compile_resolved(modified, self.scenario, str(SCENARIO)),
            )
            self.assertNotEqual(self.resolved.lock, modified.lock)
            extra = root / "extra.yh"
            extra.write_text(
                (FIXTURE / "offence.yh")
                .read_text(encoding="utf-8")
                .replace(
                    "fictional.restricted-entry version",
                    "fictional.unused-entry version",
                ),
                encoding="utf-8",
            )
            composition = root / "composition.yh"
            composition.write_text(
                composition.read_text(encoding="utf-8").replace(
                    "  import fictional.restricted-entry version 1.0.0 as entry;",
                    "  import fictional.restricted-entry version 1.0.0 as entry;\n"
                    "  import fictional.unused-entry version 1.0.0 as unused;",
                ),
                encoding="utf-8",
            )
            unused = modules.resolve(composition, root)
            self.assertEqual(
                self.request,
                modules.compile_resolved(unused, self.scenario, str(SCENARIO)),
            )
            self.assertIn(
                "fictional.unused-entry@1.0.0",
                json.loads(unused.lock)["topological_order"],
            )

    def test_cli_check_compile_atomic_and_lock_verification(self) -> None:
        command = [sys.executable, "-m", "rewrite.frontend"]
        base = [str(FIXTURE / "composition.yh"), "--module-root", str(FIXTURE)]
        check = subprocess.run(
            command
            + ["check", *base, "--verify-lock", str(FIXTURE / "MODULE-LOCK.json")],
            capture_output=True,
            check=True,
            cwd=ROOT,
        )
        self.assertEqual(
            json.loads(check.stdout),
            {"status": "valid", "language_version": modules.LANGUAGE},
        )
        with TemporaryDirectory() as temp:
            root = Path(temp)
            requests = []
            locks = []
            for number in (1, 2):
                output, lock = (
                    root / f"request{number}.json",
                    root / f"lock{number}.json",
                )
                run = subprocess.run(
                    command
                    + [
                        "compile",
                        *base,
                        "--scenario",
                        str(SCENARIO),
                        "--output",
                        str(output),
                        "--lock-output",
                        str(lock),
                    ],
                    capture_output=True,
                    check=True,
                    cwd=ROOT,
                )
                self.assertFalse(run.stdout)
                requests.append(output.read_bytes())
                locks.append(lock.read_bytes())
            self.assertEqual(requests, [self.request, self.request])
            self.assertEqual(locks, [self.resolved.lock, self.resolved.lock])
            failure = subprocess.run(
                command
                + [
                    "compile",
                    *base,
                    "--scenario",
                    str(SCENARIO),
                    "--output",
                    str(root / "unwritten.json"),
                    "--lock-output",
                    str(root / "lock1.json"),
                ],
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(failure.returncode, 1)
            self.assertFalse((root / "unwritten.json").exists())
            wrong = root / "wrong-scenario.yh"
            wrong.write_text(
                self.scenario.replace(
                    "f:fictional.restricted-entry.version-1-0-0.entry = proved;", ""
                ),
                encoding="utf-8",
            )
            failure = subprocess.run(
                command
                + [
                    "compile",
                    *base,
                    "--scenario",
                    str(wrong),
                    "--output",
                    str(root / "unwritten.json"),
                    "--lock-output",
                    str(root / "unwritten-lock.json"),
                ],
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(failure.returncode, 1)
            self.assertEqual(json.loads(failure.stderr)["code"], "SFE009")
            self.assertFalse((root / "unwritten.json").exists())
            self.assertFalse((root / "unwritten-lock.json").exists())
            repeated = subprocess.run(
                command + ["check", *base, "--module-root", str(FIXTURE)],
                capture_output=True,
                cwd=ROOT,
            )
            self.assertEqual(repeated.returncode, 2)
            self.assertFalse(repeated.stdout)

    def test_module_diagnostics(self) -> None:
        cases = [
            (
                "composition.yh",
                "module fictional.restricted-entry-composition",
                "module unsafe/../entry",
                "SFE022",
            ),
            (
                "composition.yh",
                "language YuhoSurface-v0.2",
                "language YuhoSurface-v0.3",
                "SFE023",
            ),
            ("composition.yh", "version 1.0.0; {", "version latest; {", "SFE024"),
            (
                "composition.yh",
                "import fictional.emergency-rescue version 1.0.0",
                "import fictional.absent version 1.0.0",
                "SFE025",
            ),
            (
                "composition.yh",
                "import fictional.emergency-rescue version 1.0.0",
                "import fictional.emergency-rescue version 1.0.1",
                "SFE026",
            ),
            ("composition.yh", "as rescue;", "as entry;", "SFE028"),
            (
                "composition.yh",
                "entry::g:offence-requirements",
                "entry::g:missing",
                "SFE031",
            ),
            (
                "composition.yh",
                "entry::g:offence-requirements",
                "g:offence-requirements",
                "SFE032",
            ),
            (
                "composition.yh",
                "offence entry::o:entry;",
                "offence entry::r:entry;",
                "SFE033",
            ),
            ("composition.yh", "entry::o:entry;", "absent::o:entry;", "SFE031"),
            (
                "composition.yh",
                "import fictional.restricted-entry version 1.0.0",
                "import ../restricted-entry version 1.0.0",
                "SFE035",
            ),
            (
                "composition.yh",
                "jurisdiction Fictional;",
                "jurisdiction Singapore;",
                "SFE021",
            ),
            (
                "offence.yh",
                "element fault f:knowledge",
                "element danger f:knowledge",
                "SFE017",
            ),
            (
                "composition.yh",
                "final_rule entry::r:entry;",
                "final_rule rescue::x:emergency-rescue;",
                "SFE033",
            ),
        ]
        for name, old, new, code in cases:
            with self.subTest(name=name, code=code, change=new):
                with TemporaryDirectory() as temp:
                    root = self.copy_modules(temp)
                    file = root / name
                    text = file.read_text(encoding="utf-8")
                    self.assertIn(old, text)
                    file.write_text(text.replace(old, new, 1), encoding="utf-8")
                    self.assert_error(root, code)
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            file = root / "offence.yh"
            file.write_bytes(file.read_bytes() + b"// distinct duplicate bytes\n")
            shutil.copyfile(file, root / "duplicate.yh")
            self.assert_error(root, "SFE027")
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            file = root / "offence.yh"
            text = file.read_text(encoding="utf-8")
            file.write_text(
                text.replace("export proposition g:offence-requirements;", ""),
                encoding="utf-8",
            )
            self.assert_error(root, "SFE030")
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            file = root / "offence.yh"
            text = file.read_text(encoding="utf-8")
            file.write_text(
                text.replace(
                    "  export offence o:entry;",
                    "  import fictional.restricted-entry-composition version 1.0.0 as parent;\n  export offence o:entry;",
                ),
                encoding="utf-8",
            )
            error = self.assert_error(root, "SFE029")
            self.assertIn("import cycle", error.message)
            self.assertIn("fictional.restricted-entry-composition", error.message)
        with patch.object(
            modules,
            "_namespace",
            side_effect=lambda _module, token: replace(token, text="x:clash"),
        ):
            with self.assertRaises(core.FrontendError) as caught:
                modules._compose(
                    self.resolved.root,
                    {
                        (module.identifier.text, module.version.text): module
                        for module in self.resolved.ordered
                    },
                )
            self.assertEqual(caught.exception.code, "SFE034")

    def test_unsafe_paths_utf8_and_limits(self) -> None:
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            (root / "escape.yh").symlink_to(FIXTURE / "offence.yh")
            self.assert_error(root, "SFE035")
            (root / "escape.yh").unlink()
            with self.assertRaises(core.FrontendError) as caught:
                modules.resolve(FIXTURE / "composition.yh", root)
            self.assertEqual(caught.exception.code, "SFE035")
            (root / "offence.yh").write_bytes(b"\xff")
            self.assert_error(root, "SFE001")
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            for number in range(modules.MAX_MODULES):
                file = root / f"extra{number}.yh"
                file.write_bytes((FIXTURE / "offence.yh").read_bytes())
            self.assert_error(root, "SFE036")
        with self.assertRaises(core.FrontendError) as caught:
            modules.parse_module(
                b"// padding\n" * (core.MAX_SOURCE_BYTES // 11 + 1), "oversize.yh"
            )
        self.assertEqual(caught.exception.code, "SFE036")
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            body = (root / "offence.yh").read_text(encoding="utf-8")
            for number in range(20):
                name = f"fictional.chain-{number}"
                next_import = (
                    f"  import fictional.chain-{number + 1} version 1.0.0 as next;\n"
                    if number < 19
                    else ""
                )
                text = body.replace(
                    "fictional.restricted-entry version", f"{name} version"
                )
                text = text.replace(
                    "  export offence o:entry;",
                    next_import + "  export offence o:entry;",
                )
                (root / f"chain-{number}.yh").write_text(text, encoding="utf-8")
            composition = root / "composition.yh"
            composition.write_text(
                composition.read_text(encoding="utf-8").replace(
                    "  import fictional.restricted-entry version 1.0.0 as entry;",
                    "  import fictional.restricted-entry version 1.0.0 as entry;\n"
                    "  import fictional.chain-0 version 1.0.0 as chain;",
                ),
                encoding="utf-8",
            )
            self.assert_error(root, "SFE036")
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            filler = b"// aggregate bytes\n" * 3000
            for number in range(22):
                source = (
                    (FIXTURE / "offence.yh")
                    .read_bytes()
                    .replace(
                        b"fictional.restricted-entry version",
                        f"fictional.large-{number} version".encode(),
                    )
                )
                (root / f"large-{number}.yh").write_bytes(source + filler)
            self.assert_error(root, "SFE036")
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            for number in range(modules.MAX_ROOT_ENTRIES):
                (root / f"asset-{number}.txt").write_bytes(b"")
            self.assert_error(root, "SFE036")
        with TemporaryDirectory() as temp:
            root = self.copy_modules(temp)
            nested = root
            for _ in range(modules.MAX_IMPORT_DEPTH + 1):
                nested = nested / "nested"
                nested.mkdir()
            self.assert_error(root, "SFE036")

    @unittest.skipUnless(KERNEL.is_file(), "kernel executable not configured")
    def test_golden_and_exhaustive_243_status_matrix(self) -> None:
        first = subprocess.run(
            [str(KERNEL)], input=self.request + b"\n", capture_output=True, check=True
        )
        self.assertEqual(first.stdout, (FIXTURE / "response.json").read_bytes())
        result_schema = json.loads(
            (ROOT / "rewrite/haskell/schema/result.schema.json").read_bytes()
        )
        Draft202012Validator(result_schema).validate(json.loads(first.stdout))
        for values in itertools.product(
            ("proved", "not_proved", "unresolved(not_determined)"), repeat=5
        ):
            request = modules.compile_resolved(
                self.resolved, statuses(values), "scenario.yh"
            )
            run = subprocess.run(
                [str(KERNEL)], input=request + b"\n", capture_output=True, check=True
            )
            result = json.loads(run.stdout)
            offence = all_status(values[:3])
            rescue = all_status(values[3:])
            root = result["rules"][0]
            self.assertEqual(root["trace"][0]["value"], offence)
            self.assertEqual(len(root["trace"]), 4)
            self.assertEqual(len(result["rules"]) == 2, offence == "satisfied")
            if len(result["rules"]) == 2:
                self.assertEqual(result["rules"][1]["trace"][0]["value"], rescue)
                self.assertEqual(len(result["rules"][1]["trace"]), 3)
            expected = (
                offence
                if offence != "satisfied"
                else (
                    "not_satisfied"
                    if rescue == "satisfied"
                    else "satisfied"
                    if rescue == "not_satisfied"
                    else "unresolved"
                )
            )
            self.assertEqual(result["status"], expected)
            if offence == rescue == "satisfied":
                self.assertEqual(root["branches"][0]["reason"], "defeated")
            self.assertTrue(
                {
                    "guilt",
                    "conviction",
                    "acquittal",
                    "sentence",
                    "fitness",
                    "court_disposition",
                }.isdisjoint(result)
            )

    @unittest.skipUnless(VALIDATOR.is_file(), "bundle validator not configured")
    def test_two_fresh_bundles_valid_and_v01_unchanged(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = root / "first", root / "second"
            digest = bundle.build(self.resolved.model, self.request, first)
            self.assertEqual(
                digest, bundle.build(self.resolved.model, self.request, second)
            )
            self.assertEqual(
                digest,
                "d2a6c48b02883ca0fd06810fd8d60a21773c7e8b73be07a05f61e754371f675d",
            )
            names = sorted(
                str(path.relative_to(first))
                for path in first.rglob("*")
                if path.is_file()
            )
            self.assertEqual(len(names), 4)
            self.assertEqual(
                names,
                sorted(
                    str(path.relative_to(second))
                    for path in second.rglob("*")
                    if path.is_file()
                ),
            )
            for name in names:
                self.assertEqual(
                    (first / name).read_bytes(), (second / name).read_bytes()
                )
            validated = subprocess.run(
                [str(VALIDATOR), "validate", str(first)], capture_output=True
            )
            self.assertEqual(validated.returncode, 0, validated.stdout)
            result = json.loads(validated.stdout)
            self.assertEqual(result["bundle_digest"], digest)
            self.assertEqual(result["applicable_asserted_reviews"], [])
            self.assertFalse((first / "reviews").exists())


if __name__ == "__main__":
    unittest.main()
