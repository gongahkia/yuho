#!/usr/bin/env python3
"""Build/test an sdist and an independent facade-only consumer outside its tree."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


GUIDES = ["authoring-quickstart", "authoring-sdk", "linked-definitions",
          "typed-authoring", "presumption-authoring", "temporal-authoring",
          "computed-input-bindings", "distribution"]
PAIRS = {
    "proof.document.json": "authoring-v0.1-experimental.schema.json",
    "linked.document.json": "authoring-v0.2-experimental.schema.json",
    "typed.document.json": "authoring-v0.3-experimental.schema.json",
    "active.document.json": "authoring-v0.4-experimental.schema.json",
    "rebutted.document.json": "authoring-v0.4-experimental.schema.json",
    "temporal.document.json": "authoring-v0.5-experimental.schema.json",
    "computed.document.json": "computed-input-v0.1-experimental.schema.json",
    "proof.projection.json": "analysis-projection-v0.1-experimental.schema.json",
    "linked-A.projection.json": "analysis-projection-v0.2-experimental.schema.json",
    "linked-B.projection.json": "analysis-projection-v0.2-experimental.schema.json",
    "typed.projection.json": "typed-analysis-projection-v0.3-experimental.schema.json",
    "active.projection.json": "presumption-projection-v0.4-experimental.schema.json",
    "rebutted.projection.json": "presumption-projection-v0.4-experimental.schema.json",
    "temporal-old.projection.json": "temporal-projection-v0.5-experimental.schema.json",
    "temporal-new.projection.json": "temporal-projection-v0.5-experimental.schema.json",
    "computed.projection.json": "computed-input-projection-v0.1-experimental.schema.json",
}


def verify(archive: Path, workspace: Path) -> None:
    checkout = Path(__file__).resolve().parents[1]
    if workspace.is_relative_to(checkout):
        raise SystemExit("work directory must be outside the source tree")
    workspace.mkdir(parents=True, exist_ok=False)
    commands = []

    def run(name: str, command: list[str], cwd: Path) -> bytes:
        print(name, "in", cwd, flush=True)
        started = time.monotonic()
        result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=900)
        (workspace / (name + ".log")).write_bytes(result.stdout + result.stderr)
        commands.append({"command": command, "cwd": str(cwd),
                         "exit_code": result.returncode,
                         "seconds": round(time.monotonic() - started, 3),
                         "log": name + ".log"})
        (workspace / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        if result.returncode:
            raise SystemExit((workspace / (name + ".log")).read_text()[-12000:])
        return result.stdout

    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        for member in members:
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isdir() or member.isfile()):
                raise SystemExit("unsafe source archive entry: " + member.name)
        roots = {Path(m.name).parts[0] for m in members}
        if len(roots) != 1:
            raise SystemExit("expected one package root")
        tar.extractall(workspace / "source", filter="data")
    source = workspace / "source" / roots.pop()
    files = sorted(str(p.relative_to(source)) for p in source.rglob("*") if p.is_file())
    required = ["LICENSE", "NOTICE", "README.md", "CHANGELOG.md", "cabal.project.sdk",
                "cabal.project.freeze", "test/SDKMain.hs",
                "test/fixtures/computed-input-repair/reviewer-rule0.document.json",
                "test/fixtures/computed-input-repair/reviewer-long-id.document.json"]
    required += ["docs/" + name + ".md" for name in GUIDES]
    for name in required:
        if name not in files:
            raise SystemExit("required SDK resource missing: " + name)
    unexpected = [p for p in files if any(x in Path(p).parts for x in
                  [".git", "dist-newstyle", "__pycache__", "research", "library"])]
    if unexpected:
        raise SystemExit("unexpected source-package content: " + repr(unexpected))
    (workspace / "files.json").write_text(json.dumps(files, indent=2) + "\n")
    deferred_links = []
    for name in GUIDES:
        document = source / "docs" / (name + ".md")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            relative = target.split("#", 1)[0].split("?", 1)[0]
            resolved = (document.parent / relative).resolve()
            if not resolved.exists():
                local = resolved.relative_to(source)
                if local.parts[0] in {"research", "library", "mechanisation"}:
                    deferred_links.append({"guide": name, "target": target})
                else:
                    raise SystemExit(f"broken packaged SDK link: {name}: {target}")
    shutil.copyfile(source / "cabal.project.sdk", source / "cabal.project")
    compiler = ["--offline", "-j1", "--with-compiler=ghc-9.8.4"]
    run("package-build", ["cabal", "v2-build", "all", *compiler], source)
    run("package-tests", ["cabal", "v2-test", "yuho-sdk-test", *compiler,
                          "--test-show-details=direct"], source)
    consumer = workspace / "consumer"
    consumer.mkdir()
    example = source / "examples/sdk-distribution-consumer"
    for p in example.iterdir():
        if p.suffix in {".hs", ".cabal"}:
            shutil.copyfile(p, consumer / p.name)
    imports = [line for line in (consumer / "Main.hs").read_text().splitlines()
               if line.startswith("import ") and "Yuho" in line]
    if imports != ["import Yuho.Authoring"]:
        raise SystemExit("consumer must use only Yuho.Authoring")
    shutil.copyfile(source / "cabal.project.freeze", consumer / "cabal.project.freeze")
    (consumer / "cabal.project").write_text(
        f'packages: . "{source}"\nwith-compiler: ghc-9.8.4\n'
        'index-state: 2026-09-12T03:17:42Z\njobs: 1\n'
        'package yuho\n  flags: +development -research-tests\n')
    target = "exe:yuho-sdk-distribution-consumer"
    run("consumer-build", ["cabal", "v2-build", target, *compiler], consumer)
    binary = run("consumer-bin", ["cabal", "list-bin", target,
                 "--offline", "--with-compiler=ghc-9.8.4"], consumer).decode().strip()
    output = consumer / "output"
    run("consumer-run", [binary, str(output)], consumer)
    schemas = {p.name: json.loads(p.read_bytes()) for p in (source / "schema").glob("*.schema.json")}
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s))
               for s in schemas.values() if "$id" in s)
    for artifact, schema in PAIRS.items():
        Draft202012Validator(schemas[schema], registry=registry,
            format_checker=FormatChecker()).validate(json.loads((output / artifact).read_bytes()))
    for artifact in ["proof.bindings.json", "computed.bindings.json"]:
        Draft202012Validator({"$ref": schemas["analysis-projection-v0.1-experimental.schema.json"]["$id"] + "#/$defs/view"},
            registry=registry).validate(json.loads((output / artifact).read_bytes()))
    if (source / "cabal.project.freeze").read_bytes() != (consumer / "cabal.project.freeze").read_bytes():
        raise SystemExit("consumer freeze differs from supplied freeze")
    report = {"archive": str(archive), "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
              "source": str(source), "consumer": str(consumer), "binary": binary,
              "file_count": len(files), "schema_count": len(schemas),
              "validated_artifacts": PAIRS, "deferred_research_links": deferred_links,
              "freeze_identical": True, "public_imports": imports, "status": "passed"}
    (workspace / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Extracted SDK package, packaged tests, independent consumer and schemas passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    args = parser.parse_args()
    verify(args.archive.resolve(), args.work_dir.resolve())


if __name__ == "__main__":
    main()
