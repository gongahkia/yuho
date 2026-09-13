"""CLI for the bounded reusable YuhoSurface-v0.1 frontend."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile

from . import core


def _publish(data: bytes, destination: Path) -> None:
    core._safe_output(destination)
    with tempfile.TemporaryDirectory(
        prefix=".yuho-frontend-", dir=destination.parent
    ) as temp:
        temporary = Path(temp) / "request.json"
        temporary.write_bytes(data)
        os.link(temporary, destination, follow_symlinks=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "compile"])
    parser.add_argument("source", type=Path)
    parser.add_argument("--scenario", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--packet-dir", type=Path)
    args = parser.parse_args()
    try:
        source = core._regular_source(args.source)
        tokens = core.lex(source, str(args.source))
        if len(tokens) < 2 or tokens[0].text != "model":
            raise core.FrontendError(
                "SFE001", str(args.source), tokens[0], "expected model"
            )
        section84 = (
            tokens[1].text == "SingaporePenalCodeSection84Post2022ResearchPrototype-v1"
        )
        if section84:
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
                    {"status": "valid", "language_version": core.LANGUAGE_VERSION}
                )
                + b"\n"
            )
        elif args.output is None:
            sys.stdout.buffer.write(result)
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
