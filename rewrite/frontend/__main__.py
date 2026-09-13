"""CLI for bounded YuhoSurface-v0.1, v0.2 and v0.3 frontends."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import os
from pathlib import Path
import sys
import tempfile

from . import core
from . import modules, temporal


def _publish(data: bytes, destination: Path) -> None:
    core._safe_output(destination)
    with tempfile.TemporaryDirectory(
        prefix=".yuho-frontend-", dir=destination.parent
    ) as temp:
        temporary = Path(temp) / "request.json"
        temporary.write_bytes(data)
        os.link(temporary, destination, follow_symlinks=False)


def _publish_pair(request: bytes, output: Path, lock: bytes, lock_output: Path) -> None:
    if output == lock_output:
        raise core.FrontendError(
            "SFE015",
            str(output),
            core.Token("error", "", 1, 1),
            "request and lock outputs must differ",
        )
    core._safe_output(output)
    core._safe_output(lock_output)
    with ExitStack() as stack:
        first_dir = Path(
            stack.enter_context(
                tempfile.TemporaryDirectory(prefix=".yuho-request-", dir=output.parent)
            )
        )
        second_dir = Path(
            stack.enter_context(
                tempfile.TemporaryDirectory(
                    prefix=".yuho-lock-", dir=lock_output.parent
                )
            )
        )
        first = first_dir / "request.json"
        second = second_dir / "lock.json"
        first.write_bytes(request)
        second.write_bytes(lock)
        published = False
        try:
            os.link(first, output, follow_symlinks=False)
            published = True
            os.link(second, lock_output, follow_symlinks=False)
        except OSError:
            if published:
                output.unlink()
            raise


def _publish_triple(items: tuple[tuple[bytes, Path], ...]) -> None:
    paths = [path for _, path in items]
    if len(set(paths)) != len(paths):
        raise core.FrontendError(
            "SFE050",
            str(paths[0]),
            core.Token("error", "", 1, 1),
            "temporal outputs must be distinct",
        )
    for path in paths:
        core._safe_output(path)
    with ExitStack() as stack:
        staged: list[tuple[Path, Path]] = []
        for number, (data, destination) in enumerate(items):
            directory = Path(
                stack.enter_context(
                    tempfile.TemporaryDirectory(
                        prefix=".yuho-temporal-", dir=destination.parent
                    )
                )
            )
            temporary = directory / f"artifact-{number}"
            temporary.write_bytes(data)
            staged.append((temporary, destination))
        published: list[Path] = []
        try:
            for temporary, destination in staged:
                os.link(temporary, destination, follow_symlinks=False)
                published.append(destination)
        except OSError:
            for destination in reversed(published):
                destination.unlink()
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "compile"])
    parser.add_argument("source", type=Path)
    parser.add_argument("--scenario", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--packet-dir", type=Path)
    parser.add_argument("--module-root", type=Path, action="append")
    parser.add_argument("--lock-output", type=Path)
    parser.add_argument("--verify-lock", type=Path)
    parser.add_argument("--selection-output", type=Path)
    parser.add_argument("--verify-selection", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "check" and (
            args.output is not None
            or args.lock_output is not None
            or args.selection_output is not None
        ):
            parser.error("check never writes compilation outputs")
        if args.module_root is not None and len(args.module_root) != 1:
            parser.error("exactly one --module-root is supported")
        source = core._regular_source(args.source)
        tokens = core.lex(source, str(args.source))
        if tokens[0].text == "model":
            temporal_token = next(
                (
                    token
                    for token in tokens
                    if token.kind == "word"
                    and token.text in {"rule-family", "effective", "conduct_date"}
                ),
                None,
            )
            if temporal_token is not None:
                raise core.FrontendError(
                    "SFE049",
                    str(args.source),
                    temporal_token,
                    "temporal constructs require YuhoSurface-v0.3",
                )
        selection = None
        if tokens[0].text == "language" and tokens[1].text == temporal.LANGUAGE:
            if args.module_root is None or args.scenario is None:
                parser.error("v0.3 selection requires --module-root and --scenario")
            if args.input_dir is not None or args.packet_dir is not None:
                parser.error("legacy source-packet flags do not apply to v0.3")
            if args.command == "compile" and any(
                path is None
                for path in (args.output, args.lock_output, args.selection_output)
            ):
                parser.error(
                    "v0.3 compilation requires --output, --lock-output and --selection-output"
                )
            resolved_temporal = temporal.resolve(args.source, args.module_root[0])
            scenario_source = core._regular_source(args.scenario)
            temporal_scenario = temporal.parse_scenario(
                scenario_source, str(args.scenario)
            )
            selected = temporal.select(resolved_temporal, temporal_scenario)
            result, lock, selection = (
                selected.request,
                resolved_temporal.lock,
                selected.record,
            )
            if args.verify_lock is not None:
                temporal.verify_lock(
                    lock,
                    core._regular_source(args.verify_lock).encode("utf-8"),
                    str(args.verify_lock),
                )
            if args.verify_selection is not None:
                temporal.verify_selection(
                    selection,
                    core._regular_source(args.verify_selection).encode("utf-8"),
                    str(args.verify_selection),
                )
            language_version = temporal.LANGUAGE
        elif tokens[0].text == "language":
            if args.module_root is None:
                parser.error("v0.2 modules require --module-root")
            if any(
                token.kind == "word"
                and token.text in {"rule-family", "effective", "conduct_date"}
                for token in tokens
            ):
                raise core.FrontendError(
                    "SFE049",
                    str(args.source),
                    next(
                        token
                        for token in tokens
                        if token.kind == "word"
                        and token.text in {"rule-family", "effective", "conduct_date"}
                    ),
                    "temporal constructs require YuhoSurface-v0.3",
                )
            if args.selection_output is not None or args.verify_selection is not None:
                parser.error("selection flags require a v0.3 temporal module")
            if args.input_dir is not None or args.packet_dir is not None:
                parser.error("legacy source-packet flags do not apply to v0.2 modules")
            resolved = modules.resolve(args.source, args.module_root[0])
            if args.verify_lock is not None:
                expected_lock = core._regular_source(args.verify_lock).encode("utf-8")
                modules.verify_lock(resolved, expected_lock, str(args.verify_lock))
            if args.scenario is not None:
                scenario_source = core._regular_source(args.scenario)
                scenario_tokens = core.lex(scenario_source, str(args.scenario))
                if any(
                    token.text == "conduct_date"
                    for token in scenario_tokens
                    if token.kind == "word"
                ):
                    token = next(
                        token
                        for token in scenario_tokens
                        if token.kind == "word" and token.text == "conduct_date"
                    )
                    raise core.FrontendError(
                        "SFE049",
                        str(args.scenario),
                        token,
                        "temporal scenarios require YuhoSurface-v0.3",
                    )
                scenario = core.parse_scenario(scenario_source, str(args.scenario))
                core.check_scenario(scenario, resolved.model, str(args.scenario))
            elif args.command == "compile":
                raise core.FrontendError(
                    "SFE009",
                    resolved.root.path,
                    resolved.root.identifier,
                    "scenario required",
                )
            if args.command == "compile":
                result = modules.compile_resolved(
                    resolved, scenario_source, str(args.scenario)
                )
            language_version = modules.LANGUAGE
            lock = resolved.lock
        else:
            if (
                args.module_root is not None
                or args.lock_output is not None
                or args.verify_lock is not None
                or args.selection_output is not None
                or args.verify_selection is not None
            ):
                parser.error("module and lock flags require a versioned module")
            language_version = core.LANGUAGE_VERSION
            lock = None
        if tokens[0].text not in {"model", "language"}:
            raise core.FrontendError(
                "SFE001", str(args.source), tokens[0], "expected model"
            )
        section84 = (
            tokens[0].text == "model"
            and tokens[1].text
            == "SingaporePenalCodeSection84Post2022ResearchPrototype-v1"
        )
        if tokens[0].text == "language":
            pass
        elif section84:
            if args.scenario is not None:
                raise core.FrontendError(
                    "SFE013",
                    str(args.source),
                    tokens[1],
                    "legacy model has embedded assignments",
                )
            model = core.parse_text(source, str(args.source))
            core.check(model, str(args.source))
            if args.command == "compile":
                if args.input_dir is None or args.packet_dir is None:
                    parser.error(
                        "section 84 compilation requires --input-dir and --packet-dir"
                    )
                result = core.lower(
                    model, args.input_dir, args.packet_dir, str(args.source)
                )
        else:
            model = core.parse_synthetic(source, str(args.source))
            core.check_synthetic(model, str(args.source))
            if args.scenario is not None:
                scenario_source = core._regular_source(args.scenario)
                scenario_token = next(
                    (
                        token
                        for token in core.lex(scenario_source, str(args.scenario))
                        if token.kind == "word" and token.text == "conduct_date"
                    ),
                    None,
                )
                if scenario_token is not None:
                    raise core.FrontendError(
                        "SFE049",
                        str(args.scenario),
                        scenario_token,
                        "temporal scenarios require YuhoSurface-v0.3",
                    )
                scenario = core.parse_scenario(scenario_source, str(args.scenario))
                core.check_scenario(scenario, model, str(args.scenario))
            elif args.command == "compile":
                raise core.FrontendError(
                    "SFE009", str(args.source), model.identifier, "scenario required"
                )
            if args.command == "compile":
                result = core.lower_synthetic(
                    model, scenario, str(args.source), str(args.scenario)
                )
        if args.command == "check":
            sys.stdout.buffer.write(
                core.canonical(
                    {"status": "valid", "language_version": language_version}
                )
                + b"\n"
            )
        elif args.output is None:
            if lock is not None and args.lock_output is not None:
                _publish(lock, args.lock_output)
            sys.stdout.buffer.write(result)
        elif selection is not None:
            _publish_triple(
                (
                    (result, args.output),
                    (lock, args.lock_output),
                    (selection, args.selection_output),
                )
            )
        elif lock is not None and args.lock_output is not None:
            _publish_pair(result, args.output, lock, args.lock_output)
        else:
            _publish(result, args.output)
    except core.FrontendError as error:
        sys.stderr.buffer.write(core.canonical(error.diagnostic()) + b"\n")
        return 1
    except (OSError, ValueError, KeyError) as error:
        diagnostic = {
            "code": "SFE015",
            "path": str(args.source),
            "line": 1,
            "column": 1,
            "message": str(error),
        }
        sys.stderr.buffer.write(core.canonical(diagnostic) + b"\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
