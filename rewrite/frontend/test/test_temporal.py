"""Synthetic civil-date selection over complete authored rule-expression graphs."""

from __future__ import annotations

from dataclasses import replace
from datetime import date as civil_date
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from rewrite.frontend import __main__ as frontend_cli
from rewrite.frontend import bundle, core, modules, temporal


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "rewrite/frontend/fixtures/temporal"
MODULES = FIXTURE / "modules"
ROOT_FILE = MODULES / "temporal_root.yh"
KERNEL = Path(os.environ.get("YUHO_KERNEL_BIN", "/missing-yuho-kernel"))
VALIDATOR = Path(os.environ.get("YUHO_BUNDLE_BIN", "/missing-yuho-model-bundle"))
INPUTS = (
    "f:entry",
    "f:no-authorization",
    "f:knowledge",
    "f:immediate-danger",
    "f:rescue-purpose",
)


def scenario(name: str) -> tuple[str, str]:
    path = FIXTURE / "scenarios" / f"{name}.yh"
    return path.read_text(encoding="utf-8"), str(path)


def status(values: tuple[str, ...]) -> str:
    text, _ = scenario("pre")
    for key, value in zip(INPUTS, values, strict=True):
        text, count = re.subn(
            rf"(?m)^([ \t]*{re.escape(key)} = )(proved|not_proved|unresolved\(not_determined\));$",
            rf"\g<1>{value};",
            text,
        )
        assert count == 1
    return text


def conjunction(values: tuple[str, ...]) -> str:
    if "not_proved" in values:
        return "not_satisfied"
    return "unresolved" if "unresolved(not_determined)" in values else "satisfied"


def disjunction(values: tuple[str, ...]) -> str:
    if "proved" in values:
        return "satisfied"
    return "unresolved" if "unresolved(not_determined)" in values else "not_satisfied"


class TemporalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resolved = temporal.resolve(ROOT_FILE, MODULES)

    def copy_tree(self, destination: str, *, reverse: bool = False) -> Path:
        target = Path(destination) / "modules"
        target.mkdir()
        names = sorted(path.name for path in MODULES.glob("*.yh"))
        for name in reversed(names) if reverse else names:
            (target / name).write_bytes((MODULES / name).read_bytes())
        return target

    def changed_root(self, before: str, after: str) -> temporal.Root:
        text = ROOT_FILE.read_text(encoding="utf-8")
        self.assertIn(before, text)
        return temporal.parse_root(
            text.replace(before, after, 1).encode(), "temporal_root.yh"
        )

    def assert_root_error(self, before: str, after: str, code: str) -> None:
        with self.assertRaises(core.FrontendError) as caught:
            self.changed_root(before, after)
        self.assertEqual(caught.exception.code, code)
        self.assertGreater(caught.exception.token.line, 0)
        self.assertGreater(caught.exception.token.column, 0)

    def test_complete_timeline_and_exact_boundary(self) -> None:
        root = self.resolved.root
        self.assertEqual(root.family.text, "fictional.restricted-entry")
        self.assertEqual(root.module_version.text, "1.0.0")
        self.assertEqual(
            [
                (
                    item.identifier.text,
                    item.version.text,
                    item.start.text,
                    item.end.text if item.end else None,
                )
                for item in root.expressions
            ],
            [
                ("pre-amendment", "1.0.0", "2030-01-01", "2031-01-01"),
                ("post-amendment", "2.0.0", "2031-01-01", None),
            ],
        )
        self.assertEqual(self.resolved.candidates[1][0].version.text, "2.0.0")
        self.assertEqual(self.resolved.candidates[1][1].root.version.text, "1.0.0")
        for name, expected in (
            ("pre", "pre-amendment"),
            ("boundary", "post-amendment"),
            ("post", "post-amendment"),
        ):
            with self.subTest(name=name):
                text, path = scenario(name)
                selected = temporal.select(
                    self.resolved, temporal.parse_scenario(text, path)
                )
                self.assertEqual(selected.expression.identifier.text, expected)
                self.assertEqual(
                    selected.record, core.canonical(json.loads(selected.record))
                )
                self.assertEqual(
                    json.loads(selected.record)["reason"],
                    "conduct_date_within_effective_interval",
                )
                self.assertEqual(
                    json.loads(selected.record)["module_lock_sha256"],
                    core.sha(self.resolved.lock),
                )
                chosen = next(
                    candidate
                    for expression, candidate in self.resolved.candidates
                    if expression.identifier.text == expected
                )
                self.assertEqual(
                    json.loads(selected.record)["selected_source_module_sha256"],
                    core.sha(chosen.root.source_bytes),
                )
                self.assertNotIn(str(ROOT), selected.record.decode())
        text, path = scenario("before")
        with self.assertRaises(core.FrontendError) as caught:
            temporal.select(self.resolved, temporal.parse_scenario(text, path))
        self.assertEqual(caught.exception.code, "SFE044")

    def test_dates_gaps_overlap_multiple_match_and_lineage(self) -> None:
        self.assert_root_error(
            "2030-01-01 until 2031-01-01", "2030-01-01 until 2030-01-01", "SFE042"
        )
        self.assert_root_error(
            "2030-01-01 until 2031-01-01", "2030-01-01 until 2029-01-01", "SFE042"
        )
        self.assert_root_error(
            "2030-01-01 until 2031-01-01", "2030-01-01 until 2031-06-01", "SFE043"
        )
        self.assert_root_error(
            "2030-01-01 until 2031-01-01", "2030-02-29 until 2031-01-01", "SFE040"
        )
        self.assert_root_error(
            "2030-01-01 until 2031-01-01", "2030-13-01 until 2031-01-01", "SFE040"
        )
        self.assert_root_error(
            "2030-01-01 until 2031-01-01", "2030/01/01 until 2031-01-01", "SFE040"
        )
        self.assert_root_error(
            "expression post-amendment version 2.0.0",
            "expression pre-amendment version 2.0.0",
            "SFE039",
        )
        self.assert_root_error(
            "expression post-amendment version 2.0.0",
            "expression post-amendment version 1.0.0",
            "SFE039",
        )
        self.assert_root_error(
            "supersedes pre-amendment;", "supersedes absent;", "SFE046"
        )
        self.assert_root_error(
            "supersedes pre-amendment;",
            "supersedes fictional.other::pre-amendment;",
            "SFE046",
        )
        self.assert_root_error(
            "rule-family fictional.restricted-entry;", "rule-family invalid;", "SFE038"
        )
        self.assert_root_error(
            "jurisdiction Fictional;", "jurisdiction Singapore;", "SFE021"
        )
        self.assert_root_error(
            "language YuhoSurface-v0.3;", "language YuhoSurface-v0.4;", "SFE049"
        )
        self.assert_root_error(
            "supersedes pre-amendment;",
            "supersedes pre-amendment;\n    supersedes pre-amendment;",
            "SFE038",
        )
        self.assert_root_error(
            "    model pre;", "    supersedes post-amendment;\n    model pre;", "SFE047"
        )
        text = (
            ROOT_FILE.read_text(encoding="utf-8")
            .replace("    supersedes pre-amendment;\n", "", 1)
            .replace(
                "    model pre;", "    supersedes post-amendment;\n    model pre;", 1
            )
        )
        with self.assertRaises(core.FrontendError) as caught:
            temporal.parse_root(text.encode(), "temporal_root.yh")
        self.assertEqual(caught.exception.code, "SFE048")
        with TemporaryDirectory() as temp:
            root = self.copy_tree(temp)
            file = root / "temporal_root.yh"
            file.write_text(
                file.read_text().replace(
                    "2031-01-01;\n    model pre", "2030-06-01;\n    model pre"
                )
            )
            resolved = temporal.resolve(file, root)
            pre, path = scenario("pre")
            with self.assertRaises(core.FrontendError) as caught:
                temporal.select(resolved, temporal.parse_scenario(pre, path))
            self.assertEqual(caught.exception.code, "SFE044")
        with TemporaryDirectory() as temp:
            root = self.copy_tree(temp)
            file = root / "exception_post.yh"
            file.write_text(
                file.read_text().replace("f:rescue-purpose", "f:other-purpose")
            )
            with self.assertRaises(core.FrontendError) as caught:
                temporal.resolve(root / "temporal_root.yh", root)
            self.assertEqual(caught.exception.code, "SFE038")
        original = self.resolved.candidates[1]
        overlap = replace(
            original[0], start=replace(original[0].start, text="2030-12-01")
        )
        corrupted = replace(
            self.resolved,
            candidates=(self.resolved.candidates[0], (overlap, original[1])),
        )
        pre, path = scenario("pre")
        with self.assertRaises(core.FrontendError) as caught:
            temporal.select(corrupted, temporal.parse_scenario(pre, path))
        self.assertEqual(caught.exception.code, "SFE045")

    def test_scenario_dates_and_status_validation(self) -> None:
        pre, path = scenario("pre")
        changes = [
            ("  conduct_date 2030-12-31;\n", "", "SFE041"),
            (
                "  conduct_date 2030-12-31;",
                "  conduct_date 2030-12-31;\n  conduct_date 2031-01-01;",
                "SFE041",
            ),
            ("2030-12-31", "2031-02-29", "SFE040"),
            ("2030-12-31", "2032-02-30", "SFE040"),
        ]
        for before, after, code in changes:
            with self.subTest(after=after):
                with self.assertRaises(core.FrontendError) as caught:
                    temporal.parse_scenario(pre.replace(before, after), path)
                self.assertEqual(caught.exception.code, code)
        leap = temporal.parse_scenario(pre.replace("2030-12-31", "2032-02-29"), path)
        self.assertEqual(
            temporal.select(self.resolved, leap).expression.identifier.text,
            "post-amendment",
        )
        absent = pre.replace("    f:entry = proved;\n", "")
        with self.assertRaises(core.FrontendError) as caught:
            temporal.select(self.resolved, temporal.parse_scenario(absent, path))
        self.assertEqual(caught.exception.code, "SFE009")
        duplicate = pre.replace(
            "    f:entry = proved;", "    f:entry = proved;\n    f:entry = proved;"
        )
        with self.assertRaises(core.FrontendError) as caught:
            temporal.select(self.resolved, temporal.parse_scenario(duplicate, path))
        self.assertEqual(caught.exception.code, "SFE002")
        bad = pre.replace("f:entry = proved;", "f:entry = perhaps;")
        with self.assertRaises(core.FrontendError) as caught:
            temporal.select(self.resolved, temporal.parse_scenario(bad, path))
        self.assertEqual(caught.exception.code, "SFE010")

    def test_lock_relocation_source_hash_and_context_inertness(self) -> None:
        self.assertEqual(
            self.resolved.lock, (FIXTURE / "MODULE-LOCK.json").read_bytes()
        )
        self.assertEqual(
            self.resolved.lock, core.canonical(json.loads(self.resolved.lock))
        )
        temporal.verify_lock(
            self.resolved.lock, (FIXTURE / "MODULE-LOCK.json").read_bytes(), "lock.json"
        )
        lock = json.loads(self.resolved.lock)
        self.assertEqual(lock["language_version"], temporal.LANGUAGE)
        self.assertEqual(len(lock["modules"]), 6)
        known_sources = {
            temporal.parse_root(
                ROOT_FILE.read_bytes(), "temporal_root.yh"
            ).module_id.text: ROOT_FILE.read_bytes()
        }
        for name in (
            "offence.yh",
            "exception_pre.yh",
            "exception_post.yh",
            "composition_pre.yh",
            "composition_post.yh",
        ):
            module = modules.parse_module((MODULES / name).read_bytes(), name)
            known_sources[module.identifier.text] = module.source_bytes
        for row in lock["modules"]:
            self.assertEqual(row["sha256"], core.sha(known_sources[row["id"]]))
            self.assertEqual(row["byte_length"], len(known_sources[row["id"]]))
        with TemporaryDirectory() as left, TemporaryDirectory() as right:
            first, second = self.copy_tree(left), self.copy_tree(right, reverse=True)
            a, b = (
                temporal.resolve(first / "temporal_root.yh", first),
                temporal.resolve(second / "temporal_root.yh", second),
            )
            self.assertEqual(a.lock, b.lock)
            pre, path = scenario("pre")
            self.assertEqual(
                temporal.select(a, temporal.parse_scenario(pre, path)).request,
                temporal.select(b, temporal.parse_scenario(pre, path)).request,
            )
            self.assertEqual(
                temporal.select(a, temporal.parse_scenario(pre, path)).record,
                temporal.select(b, temporal.parse_scenario(pre, path)).record,
            )
            file = first / "exception_pre.yh"
            file.write_bytes(file.read_bytes() + b"// changed exact source bytes\n")
            changed = temporal.resolve(first / "temporal_root.yh", first)
            with self.assertRaises(core.FrontendError) as caught:
                temporal.verify_lock(changed.lock, self.resolved.lock, "lock.json")
            self.assertEqual(caught.exception.code, "SFE051")

    def test_selection_never_reads_a_clock(self) -> None:
        class ClockTrap:
            @staticmethod
            def fromisoformat(value: str) -> civil_date:
                return civil_date.fromisoformat(value)

            @staticmethod
            def today() -> civil_date:
                raise AssertionError("system clock was consulted")

        pre, path = scenario("pre")
        expected = temporal.select(self.resolved, temporal.parse_scenario(pre, path))
        with patch.object(temporal, "date", ClockTrap):
            actual = temporal.select(self.resolved, temporal.parse_scenario(pre, path))
        self.assertEqual(actual.request, expected.request)
        self.assertEqual(actual.record, expected.record)
        with TemporaryDirectory() as temp:
            root = self.copy_tree(temp)
            file = root / "temporal_root.yh"
            file.write_text(
                file.read_text().replace("    supersedes pre-amendment;\n", "")
            )
            changed = temporal.resolve(file, root)
            pre, path = scenario("pre")
            selected = temporal.select(changed, temporal.parse_scenario(pre, path))
            original = temporal.select(
                self.resolved, temporal.parse_scenario(pre, path)
            )
            self.assertEqual(selected.request, original.request)
            self.assertNotEqual(selected.record, original.record)
            with self.assertRaises(core.FrontendError) as caught:
                temporal.verify_selection(
                    selected.record, original.record, "selection.json"
                )
            self.assertEqual(caught.exception.code, "SFE051")

    def test_cli_atomic_outputs_and_repeated_environment(self) -> None:
        base = [sys.executable, "-m", "rewrite.frontend"]
        args = [
            str(ROOT_FILE),
            "--module-root",
            str(MODULES),
            "--scenario",
            str(FIXTURE / "scenarios/pre.yh"),
        ]
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            outputs = []
            for number, tz, locale in (
                (1, "UTC", "C"),
                (2, "Pacific/Auckland", "C.UTF-8"),
            ):
                paths = (
                    directory / f"request{number}.json",
                    directory / f"lock{number}.json",
                    directory / f"selection{number}.json",
                )
                env = {
                    **os.environ,
                    "TZ": tz,
                    "LC_ALL": locale,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": str(ROOT),
                }
                run = subprocess.run(
                    base
                    + [
                        "compile",
                        *args,
                        "--output",
                        str(paths[0]),
                        "--lock-output",
                        str(paths[1]),
                        "--selection-output",
                        str(paths[2]),
                    ],
                    cwd=ROOT if number == 1 else directory,
                    env=env,
                    capture_output=True,
                )
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertFalse(run.stdout)
                outputs.append(tuple(path.read_bytes() for path in paths))
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[0][0], (FIXTURE / "pre-request.json").read_bytes())
            self.assertEqual(outputs[0][1], self.resolved.lock)
            self.assertEqual(
                outputs[0][2], (FIXTURE / "pre-selection.json").read_bytes()
            )
            invalid = directory / "invalid.yh"
            invalid.write_text(scenario("before")[0])
            paths = (
                directory / "failure-request.json",
                directory / "failure-lock.json",
                directory / "failure-selection.json",
            )
            run = subprocess.run(
                base
                + [
                    "compile",
                    str(ROOT_FILE),
                    "--module-root",
                    str(MODULES),
                    "--scenario",
                    str(invalid),
                    "--output",
                    str(paths[0]),
                    "--lock-output",
                    str(paths[1]),
                    "--selection-output",
                    str(paths[2]),
                ],
                cwd=ROOT,
                capture_output=True,
            )
            self.assertEqual(run.returncode, 1)
            self.assertEqual(json.loads(run.stderr)["code"], "SFE044")
            self.assertTrue(all(not path.exists() for path in paths))
            run = subprocess.run(
                base
                + [
                    "compile",
                    *args,
                    "--output",
                    str(paths[0]),
                    "--lock-output",
                    str(paths[1]),
                    "--selection-output",
                    str(paths[1]),
                ],
                cwd=ROOT,
                capture_output=True,
            )
            self.assertEqual(run.returncode, 1)
            self.assertEqual(json.loads(run.stderr)["code"], "SFE050")
            self.assertTrue(all(not path.exists() for path in paths))
            tampered = directory / "tampered-selection.json"
            tampered.write_bytes(outputs[0][2] + b" ")
            run = subprocess.run(
                base + ["check", *args, "--verify-selection", str(tampered)],
                cwd=ROOT,
                capture_output=True,
            )
            self.assertEqual(json.loads(run.stderr)["code"], "SFE051")
            check = subprocess.run(
                base + ["check", *args], cwd=ROOT, capture_output=True
            )
            self.assertEqual(
                json.loads(check.stdout)["language_version"], temporal.LANGUAGE
            )
            existing = directory / "existing-selection.json"
            existing.write_bytes(b"user data")
            run = subprocess.run(
                base
                + [
                    "compile",
                    *args,
                    "--output",
                    str(paths[0]),
                    "--lock-output",
                    str(paths[1]),
                    "--selection-output",
                    str(existing),
                ],
                cwd=ROOT,
                capture_output=True,
            )
            self.assertEqual(run.returncode, 1)
            self.assertEqual(existing.read_bytes(), b"user data")
            self.assertTrue(all(not path.exists() for path in paths))
            v02 = ROOT / "rewrite/frontend/fixtures/modules/composition.yh"
            v02_scenario = directory / "v02-temporal.yh"
            v02_scenario.write_text(
                (ROOT / "rewrite/frontend/fixtures/scenarios/module_all_proved.yh")
                .read_text()
                .replace(
                    "FictionalRestrictedEntryComposition-v0.2 {",
                    "FictionalRestrictedEntryComposition-v0.2 {\n  conduct_date 2030-12-31;",
                )
            )
            run = subprocess.run(
                base
                + [
                    "check",
                    str(v02),
                    "--module-root",
                    str(v02.parent),
                    "--scenario",
                    str(v02_scenario),
                ],
                cwd=ROOT,
                capture_output=True,
            )
            self.assertEqual(json.loads(run.stderr)["code"], "SFE049")
            v01 = ROOT / "rewrite/frontend/fixtures/synthetic/restricted_entry.yh"
            v01_scenario = directory / "v01-temporal.yh"
            v01_scenario.write_text(
                (ROOT / "rewrite/frontend/fixtures/synthetic/scenario_all_proved.yh")
                .read_text()
                .replace(
                    "FictionalRestrictedAreaEntry-v0.1 {",
                    "FictionalRestrictedAreaEntry-v0.1 {\n  conduct_date 2030-12-31;",
                )
            )
            run = subprocess.run(
                base + ["check", str(v01), "--scenario", str(v01_scenario)],
                cwd=ROOT,
                capture_output=True,
            )
            self.assertEqual(json.loads(run.stderr)["code"], "SFE049")

    def test_publish_failure_rolls_back_all_three_outputs(self) -> None:
        with TemporaryDirectory() as temp:
            paths = tuple(Path(temp) / f"part-{number}.json" for number in range(3))
            original = frontend_cli.os.link
            calls = 0

            def fail_second(
                source: Path, destination: Path, *, follow_symlinks: bool
            ) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("synthetic publish failure")
                original(source, destination, follow_symlinks=follow_symlinks)

            with patch.object(frontend_cli.os, "link", side_effect=fail_second):
                with self.assertRaises(OSError):
                    frontend_cli._publish_triple(
                        tuple((b"data", path) for path in paths)
                    )
            self.assertTrue(all(not path.exists() for path in paths))

    @unittest.skipUnless(KERNEL.is_file(), "kernel executable not configured")
    def test_486_status_matrix_and_snapshots(self) -> None:
        schema = json.loads(
            (ROOT / "rewrite/haskell/schema/request.schema.json").read_bytes()
        )
        for name, version in (("pre", "pre-amendment"), ("boundary", "post-amendment")):
            text, path = scenario(name)
            for values in itertools.product(
                ("proved", "not_proved", "unresolved(not_determined)"), repeat=5
            ):
                selected = temporal.select(
                    self.resolved,
                    temporal.parse_scenario(
                        status(values).replace("2030-12-31", "2031-01-01")
                        if name == "boundary"
                        else status(values),
                        path,
                    ),
                )
                self.assertEqual(selected.expression.identifier.text, version)
                Draft202012Validator(schema).validate(json.loads(selected.request))
                run = subprocess.run(
                    [str(KERNEL)],
                    input=selected.request + b"\n",
                    capture_output=True,
                    check=True,
                )
                result = json.loads(run.stdout)
                offence = conjunction(values[:3])
                exception = (
                    disjunction(values[3:])
                    if name == "pre"
                    else conjunction(values[3:])
                )
                expected = (
                    offence
                    if offence != "satisfied"
                    else (
                        "not_satisfied"
                        if exception == "satisfied"
                        else "satisfied"
                        if exception == "not_satisfied"
                        else "unresolved"
                    )
                )
                self.assertEqual(result["status"], expected)
                self.assertTrue(
                    {
                        "guilt",
                        "conviction",
                        "acquittal",
                        "liability",
                        "sentence",
                        "diagnosis",
                        "fitness",
                    }.isdisjoint(result)
                )
            snapshot = "pre" if name == "pre" else "post"
            selected = temporal.select(
                self.resolved, temporal.parse_scenario(text, path)
            )
            self.assertEqual(
                selected.request, (FIXTURE / f"{snapshot}-request.json").read_bytes()
            )
            self.assertEqual(
                selected.record, (FIXTURE / f"{snapshot}-selection.json").read_bytes()
            )
            run = subprocess.run(
                [str(KERNEL)],
                input=selected.request + b"\n",
                capture_output=True,
                check=True,
            )
            self.assertEqual(
                run.stdout, (FIXTURE / f"{snapshot}-response.json").read_bytes()
            )

    @unittest.skipUnless(VALIDATOR.is_file(), "bundle validator not configured")
    def test_double_bundles_and_structural_change_set(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            bundles = {}
            for name in ("pre", "boundary"):
                text, path = scenario(name)
                selected = temporal.select(
                    self.resolved, temporal.parse_scenario(text, path)
                )
                first, second = root / f"{name}-one", root / f"{name}-two"
                digest = bundle.build(selected.model, selected.request, first)
                self.assertEqual(
                    digest, bundle.build(selected.model, selected.request, second)
                )
                inventory = sorted(
                    path.relative_to(first).as_posix()
                    for path in first.rglob("*")
                    if path.is_file()
                )
                self.assertEqual(len(inventory), 4)
                self.assertEqual(
                    inventory,
                    sorted(
                        path.relative_to(second).as_posix()
                        for path in second.rglob("*")
                        if path.is_file()
                    ),
                )
                self.assertTrue(
                    all(
                        (first / path).read_bytes() == (second / path).read_bytes()
                        for path in inventory
                    )
                )
                validated = subprocess.run(
                    [str(VALIDATOR), "validate", str(first)], capture_output=True
                )
                self.assertEqual(validated.returncode, 0, validated.stdout)
                self.assertEqual(json.loads(validated.stdout)["bundle_digest"], digest)
                self.assertFalse((first / "reviews").exists())
                bundles[name] = first
            diff = subprocess.run(
                [str(VALIDATOR), "diff", str(bundles["pre"]), str(bundles["boundary"])],
                capture_output=True,
            )
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertEqual(diff.stdout, (FIXTURE / "change-set.json").read_bytes())
            self.assertNotIn(b"legal_amendment", diff.stdout)

    def test_path_and_utf8_rejection(self) -> None:
        with TemporaryDirectory() as temp:
            root = self.copy_tree(temp)
            (root / "escape.yh").symlink_to(MODULES / "offence.yh")
            with self.assertRaises(core.FrontendError) as caught:
                temporal.resolve(root / "temporal_root.yh", root)
            self.assertEqual(caught.exception.code, "SFE035")
            (root / "escape.yh").unlink()
            (root / "exception_pre.yh").write_bytes(b"\xff")
            with self.assertRaises(core.FrontendError) as caught:
                temporal.resolve(root / "temporal_root.yh", root)
            self.assertEqual(caught.exception.code, "SFE001")
        with self.assertRaises(core.FrontendError) as caught:
            temporal.resolve(ROOT_FILE, Path("/tmp"))
        self.assertEqual(caught.exception.code, "SFE035")
        with TemporaryDirectory() as temp:
            root = self.copy_tree(temp)
            file = root / "composition_pre.yh"
            file.write_text(
                file.read_text().replace("  export output final_rule;\n", "")
            )
            with self.assertRaises(core.FrontendError) as caught:
                temporal.resolve(root / "temporal_root.yh", root)
            self.assertEqual(caught.exception.code, "SFE030")
        with TemporaryDirectory() as temp:
            root = self.copy_tree(temp)
            file = root / "temporal_root.yh"
            file.write_text(
                file.read_text().replace(
                    "module fictional.restricted-entry-temporal version 1.0.0;",
                    "module fictional.restricted-entry-composition-pre version 1.0.0;",
                )
            )
            with self.assertRaises(core.FrontendError) as caught:
                temporal.resolve(file, root)
            self.assertEqual(caught.exception.code, "SFE027")
        root_text = ROOT_FILE.read_text(encoding="utf-8")
        extras = "".join(
            f"  expression extra-{number} version 3.{number}.0 {{\n"
            "    effective from 2040-01-01;\n    model post;\n  }\n"
            for number in range(temporal.MAX_EXPRESSIONS)
        )
        with self.assertRaises(core.FrontendError) as caught:
            temporal.parse_root(
                root_text.replace(
                    "  limitations {", extras + "  limitations {", 1
                ).encode(),
                "oversize-expressions.yh",
            )
        self.assertEqual(caught.exception.code, "SFE036")


if __name__ == "__main__":
    unittest.main()
